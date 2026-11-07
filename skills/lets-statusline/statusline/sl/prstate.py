"""The pull request for the current branch: draft, open, merged, closed, checks.

Claude Code's payload reports a PR only while it is open (docs: "removed once it
merges or closes"), so merged, closed, and CI come from `gh`. `gh` takes about
0.5 s, which is too slow for the line: it runs in a background job, and the line
reads the job's cache file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Callable, Optional

from . import background, errlog
from .gitstate import GitState
from .payload import PullRequest, Session

GH_TIMEOUT_S = 15
_FIELDS = "number,state,isDraft,reviewDecision,mergeable,statusCheckRollup,url,mergedAt,closedAt"
_STATES = ("OPEN", "MERGED", "CLOSED")
_REVIEWS = ("APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED")
_PASSED = ("SUCCESS", "NEUTRAL", "SKIPPED")
_RUNNING = ("PENDING", "EXPECTED")
_PAYLOAD_REVIEWS = {"approved": "APPROVED", "changes_requested": "CHANGES_REQUESTED"}
_SLUG_PART = re.compile(r"[A-Za-z0-9_.][A-Za-z0-9_.-]*\Z")  # one path segment, no leading dash


class PrError(RuntimeError):
    """`gh` failed, or its answer cannot be read."""


@dataclass(frozen=True)
class PrFacts:
    number: int
    state: str                # OPEN, MERGED, CLOSED
    draft: bool
    review: Optional[str]     # APPROVED, CHANGES_REQUESTED, REVIEW_REQUIRED
    conflicting: bool
    failed: int
    pending: int
    passed: int
    url: Optional[str]
    ended_at: Optional[float]  # when it merged or closed
    kind: Optional[str] = None  # "mr" for a GitLab merge request


@dataclass(frozen=True)
class PrView:
    kind: str                  # "pr", "none" (no PR for this branch), "unknown" (lookup failed)
    facts: Optional[PrFacts]


def _timestamp(value: object) -> Optional[float]:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def _count_checks(rollup: object):
    failed = pending = passed = 0
    for check in rollup if isinstance(rollup, list) else ():
        if not isinstance(check, dict):
            continue
        if check.get("__typename") == "StatusContext":
            result = check.get("state")
        elif check.get("status") != "COMPLETED":
            result = "PENDING"
        else:
            result = check.get("conclusion")
        if result in _RUNNING:
            pending += 1
        elif result in _PASSED:
            passed += 1
        else:
            failed += 1
    return failed, pending, passed


def parse_view(d: object) -> PrFacts:
    """Check one `gh pr view --json` answer. This is a system boundary."""
    if not isinstance(d, dict):
        raise PrError(f"gh answer is a {type(d).__name__}, expected an object")
    number, state = d.get("number"), d.get("state")
    if not isinstance(number, int) or isinstance(number, bool) or state not in _STATES:
        raise PrError(f"gh answer has number={number!r} state={state!r}")
    failed, pending, passed = _count_checks(d.get("statusCheckRollup"))
    review = d.get("reviewDecision")
    url = d.get("url")
    return PrFacts(number=number, state=state, draft=d.get("isDraft") is True,
                   review=review if review in _REVIEWS else None,
                   conflicting=d.get("mergeable") == "CONFLICTING",
                   failed=failed, pending=pending, passed=passed,
                   url=url if isinstance(url, str) else None,
                   ended_at=_timestamp(d.get("mergedAt")) or _timestamp(d.get("closedAt")))


def to_dict(facts: PrFacts) -> dict:
    return asdict(facts)


def _from_dict(d: object) -> Optional[PrFacts]:
    try:
        return PrFacts(**d)  # type: ignore[arg-type]
    except TypeError:
        return None


def fetch(slug: str, branch: str, run: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict:
    """Ask GitHub about the PR for a branch. "No PR" is a normal answer, not an error."""
    try:
        r = run(["gh", "pr", "view", branch, "-R", slug, "--json", _FIELDS], capture_output=True,
                text=True, timeout=GH_TIMEOUT_S, stdin=subprocess.DEVNULL,
                env=dict(os.environ, GH_PROMPT_DISABLED="1", NO_COLOR="1"))
    except FileNotFoundError:
        return {"status": "no-gh"}  # gh is optional: the payload still gives the live PR
    except (OSError, subprocess.TimeoutExpired) as e:
        raise PrError(f"gh pr view {branch} -R {slug} failed: {e}") from e
    if r.returncode != 0:
        if "no pull requests found" in r.stderr:
            return {"status": "none"}
        raise PrError(f"gh pr view {branch} -R {slug} exited {r.returncode}: {r.stderr.strip()[:200]}")
    try:
        return {"status": "ok", "pr": to_dict(parse_view(json.loads(r.stdout)))}
    except ValueError as e:
        raise PrError(f"gh pr view {branch} -R {slug} returned bad JSON: {e}") from e


def ttl(entry: dict) -> int:
    """Seconds an answer stays good. A finished PR rarely changes; running checks do."""
    if entry.get("status") == "no-gh":
        return 3600
    if entry.get("status") == "error":
        return 300
    if entry.get("status") == "none":
        return 120
    pr = entry.get("pr") or {}
    if pr.get("state") != "OPEN":
        return 1800
    return 30 if pr.get("pending") else 60


def cache_path(cache_dir: str, slug: str, branch: str) -> str:
    key = hashlib.sha1(f"{slug}#{branch}".encode("utf-8", "replace")).hexdigest()[:16]
    return os.path.join(cache_dir, f"pr-{key}.json")


def save(path: str, entry: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(entry, f)
    os.replace(tmp, path)


def load(path: str) -> Optional[dict]:
    try:
        with open(path) as f:
            d = json.load(f)
        float(d["ts"])
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def refresh_job(slug: str, branch: str, cache_dir: str, now: float, log_path: str,
                run: Callable[..., subprocess.CompletedProcess]) -> Callable[[], None]:
    path = cache_path(cache_dir, slug, branch)

    def job() -> None:
        try:
            entry = fetch(slug, branch, run=run)
        except PrError as e:
            errlog.log(log_path, "pr", e, repo=slug, branch=branch)
            old = load(path) or {}
            entry = {"status": "error", "pr": old.get("pr")}
        save(path, dict(entry, ts=now))
    return job


def _from_payload(pr: PullRequest) -> PrFacts:
    return PrFacts(number=pr.number, state="OPEN", draft=pr.review_state == "draft",
                   review=_PAYLOAD_REVIEWS.get(pr.review_state or ""), conflicting=False,
                   failed=0, pending=0, passed=0, url=pr.url, ended_at=None, kind=pr.kind)


def _gh_can_ask(owner: str, name: str, branch: str) -> bool:
    """These values come from the repo, and `gh` reads them as arguments.

    A leading dash is an option. A number or a URL is a PR, not a branch. A slug
    with an extra segment names another host.
    """
    return bool(_SLUG_PART.match(owner) and _SLUG_PART.match(name)
                and not branch.startswith("-") and not branch.isdigit() and "://" not in branch)


def _eligible(session: Session, git: Optional[GitState]) -> bool:
    return bool(git and git.branch and git.upstream and not git.is_base
                and session.repo and session.repo.host == "github.com"
                and _gh_can_ask(session.repo.owner, session.repo.name, git.branch))


def _merge(payload: Optional[PrFacts], entry: Optional[dict]) -> Optional[PrView]:
    """The payload is live, so it wins on number, state, and review. The cache adds the rest."""
    cached = _from_dict(entry["pr"]) if entry and entry.get("pr") else None
    if payload:
        if cached and cached.number == payload.number and cached.state == "OPEN":
            return PrView("pr", replace(payload, review=payload.review or cached.review,
                                        conflicting=cached.conflicting, failed=cached.failed,
                                        pending=cached.pending, passed=cached.passed,
                                        url=payload.url or cached.url))
        return PrView("pr", payload)
    if cached:
        return PrView("pr", cached)
    if entry is None or entry.get("status") == "no-gh":
        return None
    return PrView("none" if entry.get("status") == "none" else "unknown", None)


def get(session: Session, git: Optional[GitState], cache_dir: str, now: float, log_path: str,
        spawn: Callable[..., bool] = background.spawn,
        run: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> Optional[PrView]:
    payload = _from_payload(session.pr) if session.pr else None
    if not _eligible(session, git):
        return PrView("pr", payload) if payload else None
    slug, branch = session.repo.slug, git.branch  # type: ignore[union-attr]
    path = cache_path(cache_dir, slug, branch)
    entry = load(path)
    if entry is None or now - float(entry["ts"]) >= ttl(entry):
        spawn(refresh_job(slug, branch, cache_dir, now, log_path, run), path + ".lock")
    return _merge(payload, entry)
