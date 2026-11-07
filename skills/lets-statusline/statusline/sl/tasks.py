"""Taskwarrior counts for the namespace bound to the current repo.

Read-only: the export runs with gc, recurrence and hooks off, so it never
changes the task data. The raw rows are cached for TTL_S seconds; the counts
are computed fresh each time because "overdue" depends on the clock.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

TTL_S = 30
TIMEOUT_S = 2.0
_NAME = r"([a-z0-9][a-z0-9._-]*[a-z0-9])"
# "Namespace: `x`", "**Namespace (this repo):** `x`", "namespace ...: **`project:x`**"
_LABEL = re.compile(r"namespace[^:\n`]*:\W*?`(?:project:)?" + _NAME + "`", re.I)
_PROJECT = re.compile(r"project:" + _NAME)
_MULTI = re.compile(r"multi-namespace", re.I)
_KEEP = ("description", "due", "wait", "start")
_ARGS = ("rc.gc=off", "rc.recurrence=off", "rc.hooks=off", "rc.verbose=nothing",
         "rc.confirmation=off", "rc.json.array=on")


class TaskError(RuntimeError):
    """The Taskwarrior export failed or returned something unreadable."""


@dataclass(frozen=True)
class TaskSummary:
    namespace: str
    pending: int
    overdue: int
    due_today: int
    active_count: int
    active: Optional[str]


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(20_000)
    except OSError:
        return ""


def find_namespace(cwd: str, boundary: str) -> Optional[str]:
    """Look in cwd and its parents, up to and including `boundary` (the repo root).

    In each folder TASKS.md wins over .taskproject, as in the taskwarrior rule.
    A TASKS.md that says "MULTI-namespace" stops the search with no answer.
    """
    cur = os.path.realpath(cwd)
    stop = os.path.realpath(boundary)
    if os.path.commonpath([cur, stop]) != stop:
        return None
    while True:
        text = _read(os.path.join(cur, "TASKS.md"))
        if _MULTI.search(text):
            return None                    # the namespace depends on the folder: do not guess
        m = _LABEL.search(text) or _PROJECT.search(text)
        if m:
            return m.group(1)
        line = _read(os.path.join(cur, ".taskproject")).strip().splitlines()
        if line and re.fullmatch(_NAME, line[0].strip()):
            return line[0].strip()
        if cur == stop or os.path.dirname(cur) == cur:
            return None
        cur = os.path.dirname(cur)


def _ts(value: object) -> Optional[float]:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def summarize(rows: List[dict], now: float, namespace: str = "") -> TaskSummary:
    today = datetime.fromtimestamp(now).date()
    visible = [r for r in rows if not ((_ts(r.get("wait")) or 0) > now)]
    overdue = due_today = 0
    started = []
    for r in visible:
        due = _ts(r.get("due"))
        if due is not None and due < now:
            overdue += 1
        elif due is not None and datetime.fromtimestamp(due).date() == today:
            due_today += 1
        start = _ts(r.get("start"))
        if start is not None:
            started.append((start, str(r.get("description", ""))))
    started.sort(reverse=True)
    return TaskSummary(namespace, len(visible), overdue, due_today, len(started),
                       started[0][1] if started else None)


def _export(ns: str, runner: Callable[..., subprocess.CompletedProcess]) -> Optional[List[dict]]:
    """The pending rows, or None when Taskwarrior is not installed (it is optional)."""
    try:
        r = runner(["task", *_ARGS, f"project:{ns}", "status:pending", "export"],
                   capture_output=True, text=True, timeout=TIMEOUT_S, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        return None
    except (OSError, subprocess.TimeoutExpired) as e:
        raise TaskError(f"task export for {ns} failed: {e}") from e
    if r.returncode != 0:
        raise TaskError(f"task export for {ns} exited {r.returncode}: {r.stderr.strip()[:200]}")
    try:
        rows = json.loads(r.stdout or "[]")
    except ValueError as e:
        raise TaskError(f"task export for {ns} returned bad JSON: {e}") from e
    return [{k: row[k] for k in _KEEP if k in row} for row in rows if isinstance(row, dict)]


def load(ns: str, cache_dir: str, now: float,
         runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> Optional[TaskSummary]:
    path = os.path.join(cache_dir, f"tasks-{ns}.json")
    try:
        with open(path) as f:
            cached = json.load(f)
        if now - float(cached["ts"]) < TTL_S:
            return summarize(cached["rows"], now, ns)
    except (OSError, ValueError, KeyError, TypeError):
        pass  # no usable cache: fetch below
    rows = _export(ns, runner)
    if rows is None:
        return None
    os.makedirs(cache_dir, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump({"ts": now, "rows": rows}, f)
    os.replace(tmp, path)
    return summarize(rows, now, ns)
