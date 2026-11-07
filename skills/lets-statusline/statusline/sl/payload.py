"""Parse the JSON that Claude Code sends on stdin into frozen dataclasses.

This is the system boundary: every field is type-checked here, so the rest of
the code can trust what it gets. Unknown or wrongly typed fields become None.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional, Tuple

FIVE_HOURS = 5 * 3600
SEVEN_DAYS = 7 * 86400


class PayloadError(ValueError):
    """The stdin payload is not a JSON object."""


@dataclass(frozen=True)
class Context:
    used_tokens: int
    window: int
    used_pct: float


@dataclass(frozen=True)
class Cache:
    warm: bool
    observed: bool                    # False: this provider reports no caching at all
    ttl: Optional[str]
    expires_at: Optional[float]
    recache_tokens: Optional[int]
    last_miss_at: Optional[float]
    last_miss_causes: Tuple[str, ...]


@dataclass(frozen=True)
class Limit:
    label: str
    used_pct: float
    resets_at: Optional[float]
    window_s: int


@dataclass(frozen=True)
class PullRequest:
    number: int
    url: Optional[str]
    review_state: Optional[str]
    kind: Optional[str]


@dataclass(frozen=True)
class Repo:
    host: str
    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True)
class Session:
    cwd: str
    project_dir: Optional[str]
    session_name: Optional[str]
    model_name: Optional[str]
    model_id: Optional[str]
    effort: Optional[str]
    thinking: Optional[bool]
    fast_mode: bool
    agent_name: Optional[str]
    output_style: Optional[str]
    duration_s: Optional[int]
    context: Optional[Context]
    cache: Optional[Cache]
    limits: Tuple[Limit, ...]
    pr: Optional[PullRequest]
    repo: Optional[Repo]


def _get(d: Any, *path: str) -> Any:
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v


def _int(v: Any) -> Optional[int]:
    n = _num(v)
    return None if n is None else int(n)


def _str(v: Any) -> Optional[str]:
    return v if isinstance(v, str) and v else None


def _bool(v: Any) -> Optional[bool]:
    return v if isinstance(v, bool) else None


def _context(d: dict, model_id: Optional[str]) -> Optional[Context]:
    cw = _get(d, "context_window")
    if not isinstance(cw, dict):
        return None
    window = _int(cw.get("context_window_size"))
    if not window:
        window = 1_000_000 if model_id and "1m" in model_id.lower() else 200_000
    used = _int(cw.get("total_input_tokens"))
    pct = _num(cw.get("used_percentage"))
    if used is None and pct is not None:
        used = int(window * pct / 100)
    if used is None:
        return None
    if pct is None:
        pct = round(used * 100 / window) if window else 0
    return Context(used_tokens=used, window=window, used_pct=pct)


def _cache(d: dict) -> Optional[Cache]:
    pc = _get(d, "prompt_cache")
    if not isinstance(pc, dict):
        return None
    causes = _get(pc, "last_miss_cause", "causes")
    causes = tuple(c for c in causes if isinstance(c, str)) if isinstance(causes, list) else ()
    return Cache(
        warm=bool(_bool(pc.get("warm"))),
        observed=_bool(pc.get("caching_observed")) is not False,
        ttl=_str(pc.get("ttl")),
        expires_at=_num(pc.get("expires_at")),
        recache_tokens=_int(pc.get("recache_tokens_if_cold")),
        last_miss_at=_num(pc.get("last_miss_at")),
        last_miss_causes=causes,
    )


def _limits(d: dict) -> Tuple[Limit, ...]:
    out = []
    for key, label, span in (("five_hour", "5h", FIVE_HOURS), ("seven_day", "7d", SEVEN_DAYS)):
        pct = _num(_get(d, "rate_limits", key, "used_percentage"))
        if pct is None:
            continue
        out.append(Limit(label, pct, _num(_get(d, "rate_limits", key, "resets_at")), span))
    return tuple(out)


def _pr(d: dict) -> Optional[PullRequest]:
    number = _int(_get(d, "pr", "number"))
    if number is None:
        return None
    return PullRequest(number, _str(_get(d, "pr", "url")),
                       _str(_get(d, "pr", "review_state")), _str(_get(d, "pr", "kind")))


def _repo(d: dict) -> Optional[Repo]:
    host, owner, name = (_str(_get(d, "workspace", "repo", key)) for key in ("host", "owner", "name"))
    return Repo(host, owner, name) if host and owner and name else None


def _duration(d: dict) -> Optional[int]:
    ms = _num(_get(d, "cost", "total_duration_ms"))
    return None if ms is None else int(ms / 1000)


def parse(raw: str) -> Session:
    try:
        d = json.loads(raw)
    except ValueError as e:
        raise PayloadError(f"stdin is not valid JSON: {e}") from e
    if not isinstance(d, dict):
        raise PayloadError(f"stdin JSON is a {type(d).__name__}, expected an object")

    model_id = _str(_get(d, "model", "id"))
    return Session(
        cwd=_str(d.get("cwd")) or _str(_get(d, "workspace", "current_dir")) or "",
        project_dir=_str(_get(d, "workspace", "project_dir")),
        session_name=_str(d.get("session_name")),
        model_name=_str(_get(d, "model", "display_name")),
        model_id=model_id,
        effort=_str(_get(d, "effort", "level")),
        thinking=_bool(_get(d, "thinking", "enabled")),
        fast_mode=bool(_bool(d.get("fast_mode"))),
        agent_name=_str(_get(d, "agent", "name")),
        output_style=_str(_get(d, "output_style", "name")),
        duration_s=_duration(d),
        context=_context(d, model_id),
        cache=_cache(d),
        limits=_limits(d),
        pr=_pr(d),
        repo=_repo(d),
    )
