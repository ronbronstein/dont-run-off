"""This month's usage of all sessions at API list prices, from Claude Code's local session logs.

Claude Code gives the line the cost of one session only. The month total comes from the logs in
`~/.claude/projects` (or `$CLAUDE_CONFIG_DIR/projects`). A scan takes about a second, which is too
slow for the line: it runs in a background job, and the line reads the job's cache file.

It counts only the sessions of this computer that wrote logs. A subscriber does not pay this
amount; it shows the value of the usage.
"""
from __future__ import annotations

import calendar
import glob
import json
import os
import time
from typing import Callable, Mapping, Optional, Tuple

from . import background, errlog

TTL_S = 300  # the total moves slowly; one scan in 5 minutes is enough

# US dollars per million tokens: input, output, cache read. Update these when the prices change.
# A cache write costs 1.25 x input (5-minute cache) or 2 x input (1-hour cache). Fast mode: 2 x.
PRICES_AS_OF = "2026-10-06"
PRICES = {
    "claude-fable-5-1": (10.0, 50.0, 0.25),
    "claude-fable-5": (10.0, 50.0, 1.0),
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-opus-5": (5.0, 25.0, 0.50),
    "claude-opus-4-8": (5.0, 25.0, 0.50),
    "claude-opus-4-7": (5.0, 25.0, 0.50),
    "claude-opus-4-6": (5.0, 25.0, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20),
    "claude-sonnet-5": (2.0, 10.0, 0.20),
    "claude-sonnet-4-6": (3.0, 15.0, 0.30),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-haiku-4-5": (1.0, 5.0, 0.10),
}


def _n(value: object) -> float:
    """A token count from the log. The log is external data: anything else counts as 0."""
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def cost_of(model: str, usage: Mapping) -> Optional[float]:
    """The list price of one API call. None for a model with no price."""
    price = PRICES.get(model.split("[")[0])
    if price is None:
        return None
    inp, out, read = price
    cache = usage.get("cache_creation")
    hour = _n(cache.get("ephemeral_1h_input_tokens")) if isinstance(cache, dict) else 0.0
    five = max(0.0, _n(usage.get("cache_creation_input_tokens")) - hour)
    usd = (_n(usage.get("input_tokens")) * inp + _n(usage.get("output_tokens")) * out
           + _n(usage.get("cache_read_input_tokens")) * read + five * inp * 1.25 + hour * inp * 2) / 1e6
    return usd * 2 if usage.get("speed") == "fast" else usd


def month_start(now: float) -> float:
    t = time.localtime(now)
    return time.mktime((t.tm_year, t.tm_mon, 1, 0, 0, 0, 0, 0, -1))


def month_key(now: float) -> str:
    return time.strftime("%Y-%m", time.localtime(now))


def _when(stamp: object) -> Optional[float]:
    if not isinstance(stamp, str):
        return None
    try:
        return float(calendar.timegm(time.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S"))) \
            if stamp.endswith("Z") else None
    except ValueError:
        return None


def _call(line: str) -> Optional[Tuple[Tuple, str, dict, float]]:
    """One log line as (call id, model, usage, time). None for any other line."""
    try:
        d = json.loads(line)
    except ValueError:
        return None
    message = d.get("message") if isinstance(d, dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("usage"), dict):
        return None
    when = _when(d.get("timestamp"))
    model = message.get("model")
    if when is None or not isinstance(model, str):
        return None
    return (message.get("id"), d.get("requestId")), model, message["usage"], when


def scan(projects: str, since: float) -> dict:
    """Sum every API call since `since`. A streamed reply repeats its usage: count each call once."""
    seen = set()
    usd = 0.0
    unknown = 0
    for path in glob.glob(os.path.join(glob.escape(projects), "**", "*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(path) < since:
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = [line for line in f if '"usage"' in line]
        except OSError:
            continue  # a session can delete its log while we read
        for line in lines:
            call = _call(line)
            if call is None or call[3] < since or call[1] == "<synthetic>" or call[0] in seen:
                continue
            seen.add(call[0])
            cost = cost_of(call[1], call[2])
            if cost is None:
                unknown += 1
            else:
                usd += cost
    return {"usd": usd, "unknown": unknown}


def projects_dir(env: Mapping[str, str], home: str) -> str:
    base = env.get("CLAUDE_CONFIG_DIR") or os.path.join(home, ".claude")
    return os.path.join(base, "projects")


def cache_path(cache_dir: str) -> str:
    return os.path.join(cache_dir, "month-cost.json")


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
        return d if isinstance(d, dict) and float(d["ts"]) >= 0 and float(d["usd"]) >= 0 else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def refresh_job(cache_dir: str, now: float, log_path: str, projects: str) -> Callable[[], None]:
    def job() -> None:
        try:
            result = scan(projects, month_start(now))
        except Exception as e:  # noqa: BLE001 - keep the old total; the log says why
            errlog.log(log_path, "month-cost", e, projects=projects)
            return
        save(cache_path(cache_dir), dict(result, ts=now, month=month_key(now)))
    return job


def get(cache_dir: str, now: float, log_path: str, projects: str,
        spawn: Callable[..., bool] = background.spawn) -> Optional[float]:
    """This month's total from the cache. Starts a scan when the cache is old or from last month."""
    path = cache_path(cache_dir)
    entry = load(path)
    current = entry is not None and entry.get("month") == month_key(now)
    if not current or now - float(entry["ts"]) >= TTL_S:  # type: ignore[index]
        spawn(refresh_job(cache_dir, now, log_path, projects), path + ".lock")
    return float(entry["usd"]) if current else None  # type: ignore[index]
