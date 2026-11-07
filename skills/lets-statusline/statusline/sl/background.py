"""Run slow work (gh, a slow git) after the status line has already answered.

Claude Code reads the script's stdout until EOF, and it cancels a script that is
still running when the next update arrives. So the job runs in a detached child
that holds none of the parent's pipes, and a lock file stops a pile-up when
several sessions want the same data.
"""
from __future__ import annotations

import os
import time
from typing import Callable

LOCK_TTL_S = 30  # a job that died leaves a lock; do not let it block for ever


def _take_lock(path: str) -> bool:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for _ in range(2):
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(path) < LOCK_TTL_S:
                    return False
                os.unlink(path)
            except FileNotFoundError:
                pass  # the other job finished in between: try again
    return False


def _detach() -> None:
    os.setsid()
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    if devnull > 2:
        os.close(devnull)


def spawn(job: Callable[[], None], lock_path: str) -> bool:
    """Start `job` in a detached child. Return False when one is already running."""
    if not _take_lock(lock_path):
        return False
    try:
        pid = os.fork()
    except OSError:
        os.unlink(lock_path)
        return False
    if pid:
        return True
    try:
        _detach()
        job()
    finally:
        try:
            os.unlink(lock_path)
        finally:
            os._exit(0)  # never run the parent's exit code or flush its buffers
