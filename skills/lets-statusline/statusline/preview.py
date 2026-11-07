#!/usr/bin/env python3
"""Show the status line in many states, in your real terminal and font.

    python3 ~/.claude/statusline/preview.py            # every scenario
    python3 ~/.claude/statusline/preview.py pr         # scenarios whose title has "pr"
    python3 ~/.claude/statusline/preview.py 100        # one scenario group at 100 columns

Uses the real renderer with made-up git state, PR state, tasks and payloads.
Nothing here touches your repos, your tasks, GitHub or the real cache.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sl import render, theme  # noqa: E402
from sl.gitstate import GitState  # noqa: E402
from sl.prstate import PrFacts, PrView  # noqa: E402

NOW = time.time()
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "fixtures",
                       "payload_real.json")
ACTIVE = [{"description": "Ship the status line redesign", "start": "20261010T080000Z"},
          {"description": "a"}, {"description": "b"}]
OVERDUE = [{"description": "late", "due": "20200101T000000Z"}, {"description": "a"}]


def base_payload(**over):
    with open(FIXTURE) as f:
        d = json.load(f)
    d["prompt_cache"]["expires_at"] = NOW + 53 * 60 + 12
    d["rate_limits"]["five_hour"]["resets_at"] = NOW + 2 * 3600 + 40 * 60
    d["rate_limits"]["seven_day"]["resets_at"] = NOW + 6 * 86400
    d["context_window"]["total_input_tokens"] = 120_000
    d["context_window"]["used_percentage"] = 12
    d["cost"]["total_duration_ms"] = 58 * 60_000
    d["session_name"] = "Status line redesign"
    d.update(over)
    return d


def ctx(d, used):
    d["context_window"] = dict(d["context_window"], total_input_tokens=used,
                               used_percentage=used / 10_000)
    d["prompt_cache"] = dict(d["prompt_cache"], recache_tokens_if_cold=used)
    return d


def cache(d, **over):
    d["prompt_cache"] = dict(d["prompt_cache"], **over)
    return d


def git(top, **over):
    g = GitState(toplevel=top, branch="main", oid="6b56a0a", upstream="origin/main", ahead=0,
                 behind=0, staged=0, modified=0, untracked=0, conflicts=0, stash=0,
                 last_commit_ts=int(NOW - 12 * 60), operation=None, linked_worktree=False,
                 main_repo=os.path.basename(top), has_remote=True, base="origin/main",
                 ahead_base=None, behind_base=None)
    return replace(g, **over)


def pr(**over):
    base = dict(number=42, state="OPEN", draft=False, review=None, conflicting=False, failed=0,
                pending=0, passed=0, url="https://github.com/o/r/pull/42", ended_at=None)
    base.update(over)
    return PrView("pr", PrFacts(**base))


def scenarios(top):
    wt = top + "-wt"
    feat = dict(branch="feat/statusline", upstream="origin/feat/statusline", ahead_base=5, behind_base=0)
    burn = {"five_hour": {"used_percentage": 80, "resets_at": NOW + 2.5 * 3600},
            "seven_day": {"used_percentage": 41, "resets_at": NOW + 3 * 86400}}
    week = {"five_hour": {"used_percentage": 12, "resets_at": NOW + 4 * 3600},
            "seven_day": {"used_percentage": 82, "resets_at": NOW + 1 * 86400}}
    room = {"five_hour": {"used_percentage": 15, "resets_at": NOW + 2.5 * 3600},
            "seven_day": {"used_percentage": 20, "resets_at": NOW + 3.5 * 86400}}
    good = {"five_hour": {"used_percentage": 45, "resets_at": NOW + 2.5 * 3600},
            "seven_day": {"used_percentage": 50, "resets_at": NOW + 3 * 86400}}
    week_out = {"five_hour": {"used_percentage": 30, "resets_at": NOW + 2.5 * 3600},
                "seven_day": {"used_percentage": 80, "resets_at": NOW + 3.5 * 86400}}
    return [
        ("WHERE — on main, clean and in sync", base_payload(), git(top), None, []),
        ("WHERE — on main, work in progress", base_payload(),
         git(top, staged=2, modified=3, untracked=1, ahead=2), None, []),
        ("WHERE — on main, uncommitted for 3 hours", base_payload(),
         git(top, modified=4, ahead=1, last_commit_ts=int(NOW - 3 * 3600)), None, []),
        ("WHERE — behind the remote", base_payload(), git(top, behind=3), None, []),
        ("WHERE — on a branch, not pushed yet", base_payload(),
         git(top, branch="feat/statusline", upstream=None, ahead_base=3, behind_base=0), None, []),
        ("WHERE — on a branch that fell behind main", base_payload(),
         git(top, branch="feat/statusline", upstream="origin/feat/statusline", ahead_base=5,
             behind_base=12, ahead=1), None, []),
        ("WHERE — in a worktree", base_payload(),
         git(wt, linked_worktree=True, main_repo="demo", branch="feat/review-posts",
             upstream="origin/feat/review-posts", ahead_base=2, behind_base=0, modified=3),
         None, []),
        ("WHERE — rebase stopped on a conflict", base_payload(),
         git(top, branch=None, operation="rebase 2/5", conflicts=1, modified=1, upstream=None), None, []),
        ("WHERE — a repo with no remote", base_payload(),
         git(top, has_remote=False, upstream=None, base="main"), None, []),
        ("PR — none yet on a pushed branch", base_payload(), git(top, **feat), PrView("none", None), []),
        ("PR — draft", base_payload(), git(top, **feat), pr(draft=True, passed=3), []),
        ("PR — open, checks running", base_payload(), git(top, **feat), pr(passed=1, pending=2), []),
        ("PR — open, checks passed", base_payload(), git(top, **feat), pr(passed=3), []),
        ("PR — open, approved", base_payload(), git(top, **feat), pr(passed=3, review="APPROVED"), []),
        ("PR — open, needs review", base_payload(), git(top, **feat), pr(review="REVIEW_REQUIRED"), []),
        ("PR — checks failed", base_payload(), git(top, **feat), pr(failed=2, passed=1), []),
        ("PR — merge conflicts", base_payload(), git(top, **feat), pr(conflicting=True), []),
        ("PR — changes requested", base_payload(), git(top, **feat), pr(review="CHANGES_REQUESTED"), []),
        ("PR — merged", base_payload(), git(top, **dict(feat, ahead_base=0, behind_base=3)),
         pr(state="MERGED", ended_at=NOW - 2 * 3600), []),
        ("PR — closed", base_payload(), git(top, **feat), pr(state="CLOSED", ended_at=NOW - 3 * 86400), []),
        ("CACHE — about to expire, big context", cache(ctx(base_payload(), 180_000), expires_at=NOW + 252),
         git(top), None, []),
        ("CACHE — about to expire, small context",
         cache(ctx(base_payload(), 40_000), expires_at=NOW + 252), git(top), None, []),
        ("CACHE — cold, big context", cache(ctx(base_payload(), 180_000), warm=False, expires_at=None),
         git(top), None, []),
        ("CACHE — just missed, and why",
         cache(base_payload(), last_miss_at=NOW - 60, last_miss_cause={"causes": ["ttl_expired_1h"]}),
         git(top), None, []),
        ("USAGE — 5h runs out before the reset", base_payload(rate_limits=burn), git(top), None, []),
        ("USAGE — 7d is getting high", base_payload(rate_limits=week), git(top), None, []),
        ("USAGE — room to push: much of both limits will go unused (amber)",
         base_payload(rate_limits=room), git(top), None, []),
        ("USAGE — good use: both limits land near 100% at the reset (green)",
         base_payload(rate_limits=good), git(top), None, []),
        ("USAGE — 7d runs out before the reset (red)", base_payload(rate_limits=week_out), git(top), None, []),
        ("USAGE — an API key: no limits, only the cost",
         {k: v for k, v in base_payload().items() if k != "rate_limits"}, git(top), None, []),
        ("MODEL — Fable, max effort", base_payload(model={"display_name": "Fable 5.1"},
                                                   effort={"level": "max"}), git(top), None, []),
        ("MODEL — Opus, xhigh effort", base_payload(), git(top), None, []),
        ("MODEL — Opus, high effort", base_payload(effort={"level": "high"}), git(top), None, []),
        ("MODEL — Sonnet, medium effort", base_payload(model={"display_name": "Sonnet 5.5"},
                                                       effort={"level": "medium"}), git(top), None, []),
        ("MODEL — Haiku, low effort", base_payload(model={"display_name": "Haiku 5.5"},
                                                   effort={"level": "low"}), git(top), None, []),
        ("MODEL — an unknown model", base_payload(model={"display_name": "Mystery 9"},
                                                  effort={"level": "high"}), git(top), None, []),
        ("SESSION — an active task and an overdue task", base_payload(), git(top), None,
         ACTIVE + OVERDUE),
        ("SESSION — fast mode, an agent, thinking off",
         base_payload(fast_mode=True, thinking={"enabled": False}, agent={"name": "reviewer"}),
         git(top), None, []),
        ("CONTEXT — level 1, 210k", ctx(base_payload(), 210_000), git(top), None, []),
        ("CONTEXT — level 2, 260k", ctx(base_payload(), 260_000), git(top), None, []),
        ("CONTEXT — level 3, 310k", ctx(base_payload(), 310_000), git(top), None, []),
        ("CONTEXT — level 4, 420k: a banner on top", ctx(base_payload(), 420_000), git(top), None, []),
        ("CONTEXT — level 5, 530k", ctx(base_payload(), 530_000), git(top), None, []),
        ("CONTEXT — level 6, 640k: two banners", ctx(base_payload(), 640_000), git(top), None, []),
    ]


def wide_and_narrow(top):
    busy = base_payload()
    state = git(top, branch="feat/statusline", upstream="origin/feat/statusline", modified=3, ahead=2,
                ahead_base=5, behind_base=1)
    return [(f"WIDTH — {w} columns, the same busy state", busy, state, pr(failed=1, passed=2), [], w)
            for w in (180, 140, 100, 70, 50)]


def main(argv):
    pick = argv[1].lower() if len(argv) > 1 else ""
    tmp = tempfile.mkdtemp()
    try:
        home = os.path.join(tmp, "home")
        top = os.path.realpath(os.path.join(home, "Code", "acme", "demo"))
        os.makedirs(top)
        os.makedirs(top + "-wt")
        for folder in (top, top + "-wt"):
            with open(os.path.join(folder, "TASKS.md"), "w") as f:
                f.write("Namespace: `demo.preview`\n")
        rows = [s + (150,) for s in scenarios(top)] + wide_and_narrow(top)
        for i, (title, payload, state, view, tasks, columns) in enumerate(rows):
            if pick and pick not in title.lower():
                continue

            def runner(args, rows=tasks, **kw):
                return subprocess.CompletedProcess(args, 0, json.dumps(rows), "")
            payload = dict(payload, cwd=state.toplevel)
            text = render.render(json.dumps(payload), {"COLUMNS": str(columns)}, NOW, home=home,
                                 cache_dir=os.path.join(tmp, f"cache-{i}"), task_runner=runner,
                                 collect_git=lambda cwd, timeout=None, s=state: s,
                                 spawn=lambda job, lock: False,
                                 get_pr=lambda s, g, v=view: v)
            print(theme.paint(title, fg=theme.MUTED))
            print(text)
            print()
    finally:
        shutil.rmtree(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
