"""A short-lived snapshot of the git state.

Why it exists: the line refreshes on a fast timer for the cache countdown, and
most ticks do not need new git data. In a slow repo the last good state shows
at once, and a background job reads git with a long timeout.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from . import background, errlog, gitstate
from .gitstate import GitError, GitState, GitTimeout

FRESH_S = 3.0                # a snapshot this young needs no git call
SLOW_FACTOR = 5              # a repo that takes 2 s is read at most every 10 s
BACKGROUND_TIMEOUT_S = 10.0


@dataclass(frozen=True)
class GitView:
    state: Optional[GitState]
    age: float        # seconds since the snapshot
    pending: bool     # no data yet: the first read is still running in the background


def fresh_for(took: float) -> float:
    return max(FRESH_S, took * SLOW_FACTOR)


def cache_path(cache_dir: str, cwd: str) -> str:
    key = hashlib.sha1(cwd.encode("utf-8", "replace")).hexdigest()[:16]
    return os.path.join(cache_dir, f"git-{key}.json")


def _load(path: str):
    try:
        with open(path) as f:
            d = json.load(f)
        state = None if d["state"] is None else gitstate.from_dict(d["state"])
        return float(d["ts"]), float(d["took"]), state
    except (OSError, ValueError, KeyError, TypeError, GitError):
        return None


def _save(path: str, ts: float, took: float, state: Optional[GitState]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump({"ts": ts, "took": took,
                   "state": None if state is None else gitstate.to_dict(state)}, f)
    os.replace(tmp, path)


def _read_and_save(cwd: str, path: str, now: float, read: Callable[[], Optional[GitState]]):
    start = time.monotonic()
    state = read()
    took = time.monotonic() - start
    _save(path, now + took, took, state)
    return state


def refresh_job(cwd: str, cache_dir: str, now: float, log_path: str,
                collect: Callable[..., Optional[GitState]]) -> Callable[[], None]:
    def job() -> None:
        try:
            _read_and_save(cwd, cache_path(cache_dir, cwd), now,
                           lambda: collect(cwd, timeout=BACKGROUND_TIMEOUT_S))
        except Exception as e:  # noqa: BLE001 - nobody else can see this job fail
            errlog.log(log_path, "git", e, cwd=cwd)
    return job


def get(cwd: str, cache_dir: str, now: float, log_path: str,
        collect: Callable[..., Optional[GitState]] = gitstate.collect,
        spawn: Callable[..., bool] = background.spawn) -> GitView:
    path = cache_path(cache_dir, cwd)
    snapshot = _load(path)
    if snapshot:
        ts, took, state = snapshot
        if now - ts < fresh_for(took):
            return GitView(state, max(0.0, now - ts), False)
    try:
        return GitView(_read_and_save(cwd, path, now, lambda: collect(cwd)), 0, False)
    except GitTimeout:
        spawn(refresh_job(cwd, cache_dir, now, log_path, collect), path + ".lock")
    if snapshot:
        return GitView(snapshot[2], max(0.0, now - snapshot[0]), False)
    return GitView(None, 0, True)
