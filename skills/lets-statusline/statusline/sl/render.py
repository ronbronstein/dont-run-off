"""Turn one stdin payload into the status line text."""
from __future__ import annotations

import json
import os
import subprocess
from typing import Callable, List, Mapping, Optional, TypeVar

from . import (background, errlog, gitcache, gitstate, ladder, layout, prstate, seg_budget,
               seg_context, seg_place, seg_pr, seg_session, tasks, theme)
from .payload import parse

MARGIN = 4            # columns Claude Code keeps for its own spacing
DEFAULT_COLUMNS = 120
T = TypeVar("T")


def default_cache_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".claude", "cache", "statusline")


def debug_dump(raw: str, cache_dir: str) -> None:
    """Save the raw payload per session while the DEBUG flag file exists.

    Turn on:  touch ~/.claude/cache/statusline/DEBUG
    Read:     ~/.claude/cache/statusline/payloads/<session id, 8 chars>.json
    Turn off: rm ~/.claude/cache/statusline/DEBUG
    """
    if not os.path.exists(os.path.join(cache_dir, "DEBUG")):
        return
    sid = str(json.loads(raw).get("session_id") or "unknown")[:8]
    folder = os.path.join(cache_dir, "payloads")
    os.makedirs(folder, exist_ok=True)
    tmp = os.path.join(folder, f"{sid}.json.{os.getpid()}.tmp")
    with open(tmp, "w") as f:
        f.write(raw)
    os.replace(tmp, os.path.join(folder, f"{sid}.json"))


def tier(columns: int) -> str:
    return "wide" if columns >= 120 else "normal" if columns >= 90 else "narrow"


def _columns(env: Mapping[str, str]) -> int:
    try:
        columns = int(env.get("COLUMNS") or DEFAULT_COLUMNS)
    except ValueError:
        return DEFAULT_COLUMNS
    return columns if columns > 0 else DEFAULT_COLUMNS


def _safe(name: str, fn: Callable[[], T], errors: List[str], log_path: str,
          **context: object) -> Optional[T]:
    """Run one data source. On failure: log it with context, mark it, go on."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 - one bad source must not blank the line
        errors.append(name)
        errlog.log(log_path, name, e, **context)
        return None


def render(raw: str, env: Mapping[str, str], now: float, home: Optional[str] = None,
           cache_dir: Optional[str] = None,
           task_runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
           collect_git: Callable[..., Optional[gitstate.GitState]] = gitstate.collect,
           spawn: Callable[..., bool] = background.spawn,
           get_pr: Optional[Callable[..., Optional[prstate.PrView]]] = None) -> str:
    home = home or os.path.expanduser("~")
    cache_dir = cache_dir or default_cache_dir()
    log_path = os.path.join(cache_dir, "errors.log")
    session = parse(raw)
    columns = _columns(env)
    budget = max(1, columns - MARGIN)
    size = tier(columns)
    errors: List[str] = []
    _safe("debug", lambda: debug_dump(raw, cache_dir), errors, log_path)

    view = _safe("git", lambda: gitcache.get(session.cwd, cache_dir, now, log_path,
                                             collect=collect_git, spawn=spawn),
                 errors, log_path, cwd=session.cwd) if session.cwd else None
    git = view.state if view else None
    boundary = git.toplevel if git else (session.project_dir or session.cwd)
    ns = _safe("tasks", lambda: tasks.find_namespace(session.cwd, boundary), errors, log_path,
               cwd=session.cwd) if session.cwd else None
    summary = _safe("tasks", lambda: tasks.load(ns, cache_dir, now, runner=task_runner),
                    errors, log_path, namespace=ns) if ns else None
    pr_source = get_pr or (lambda s, g: prstate.get(s, g, cache_dir, now, log_path, spawn=spawn))
    pr = _safe("pr", lambda: pr_source(session, git), errors, log_path, cwd=session.cwd)

    banners = ladder.banner_lines(session.context, budget) if session.context else []
    lines = [theme.truncate_visible(b, budget) for b in banners]
    named = seg_session.session_chip(session)
    model = seg_session.model(session)
    task = seg_session.task_chip(summary)
    cost = seg_session.cost_chip(session.cost_usd)
    lines += layout.block([
        layout.line(seg_place.build(session, git, home, now, errors,
                                    git_age=view.age if view else 0,
                                    git_pending=bool(view and view.pending),
                                    pr=seg_pr.build(pr, now))
                    + ([named] if named else []), budget),
        layout.line(([model] if model else []) + seg_context.build(session, now, size)
                    + ([task] if task else []) + ([cost] if cost else []), budget),
        layout.line(seg_budget.build(session, now, size), budget),
    ])
    return layout.compose(lines)
