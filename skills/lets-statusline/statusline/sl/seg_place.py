"""Line 1 — where am I? Repo, worktree, branch, uncommitted work, commits."""
from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

from . import fmt, gitstate, theme
from .gitstate import GitState
from .layout import Segment
from .payload import Session
from .theme import DOT, label, paint, value

NUDGE_AFTER_S = 3600   # dirty tree and no commit for an hour: solid amber
STALE_NOTE_S = 30      # git data older than this says its age


def split_path(path: str, home: str) -> Tuple[str, str]:
    """Return (prefix, name) for a folder, relative to ~/Code or ~ when possible."""
    path, home = os.path.realpath(path), os.path.realpath(home)
    code = os.path.join(home, "Code")
    if path.startswith(code + os.sep):
        rel = os.path.relpath(path, code)
    elif path == home:
        return "", "~"
    elif path.startswith(home + os.sep):
        rel = "~/" + os.path.relpath(path, home)
    else:
        rel = path
    head, _, name = rel.rpartition("/")
    return (head + "/" if head else ""), name


def _subdir(cwd: str, top: str) -> str:
    rel = os.path.relpath(os.path.realpath(cwd), os.path.realpath(top))
    if rel == "." or rel.startswith(".."):
        return ""
    return "/" + (rel if len(rel) <= 24 else "…" + rel[-23:])


def _branch_name(git: GitState) -> str:
    """The color says where you are: teal = base branch, blue = a branch, amber = detached."""
    if git.branch is None:
        return paint(f"detached @{git.oid or '?'}", fg=theme.WARN, bold=True)
    color = theme.REPO if git.is_base else theme.INFO
    name = paint(git.branch, fg=color, bold=True)
    return name + (label(" (no commits)") if git.oid is None else "")


def where(session: Session, git: Optional[GitState], home: str, git_failed: bool = False) -> Segment:
    if git is None:
        head, name = split_path(session.cwd, home)
        text = label(head) + paint(name, fg=theme.REPO, bold=True)
        return Segment(text + ("" if git_failed else label("  no git")), priority=100,
                       short=paint(name, fg=theme.REPO, bold=True))
    arrow = label("  ⎇ ")
    branch = _branch_name(git)
    sub = label(_subdir(session.cwd, git.toplevel))
    if git.linked_worktree:
        repo = paint(git.main_repo, fg=theme.REPO, bold=True)
        folder = os.path.basename(git.toplevel)
        name = "worktree" if folder == git.branch else f"worktree {folder}"
        tree = label("  ⑂ ") + paint(name, fg=theme.WORKTREE, bold=True) + sub
        return Segment(repo + tree + arrow + branch, priority=100,
                       short=repo + label(" ⑂ ") + branch)
    head, plain = split_path(git.toplevel, home)
    repo = paint(plain, fg=theme.REPO, bold=True)
    return Segment(label(head) + repo + sub + arrow + branch, priority=100,
                   short=repo + arrow + branch)


def changes(git: GitState, now: float) -> Segment:
    """Uncommitted work. Full form in words, short form in git symbols (+ ~ ? ✖)."""
    counts = ((git.conflicts, "conflict", "✖", theme.BAD), (git.staged, "staged", "+", theme.OK),
              (git.modified, "changed", "~", theme.WARN), (git.untracked, "new", "?", theme.LABEL))
    shown = [c for c in counts if c[0]]
    if not shown:
        return Segment(paint("✓ clean", fg=theme.OK, bold=True), priority=90)
    parts = [paint(f"{n} {word}", fg=color, bold=True) for n, word, _, color in shown]
    age = None if git.last_commit_ts is None else max(0, now - git.last_commit_ts)
    if age is not None and not git.conflicts:
        parts.append(label("last commit ") + value(fmt.age(age)))
    tone = "bad" if git.conflicts else "warn" if age is not None and age > NUDGE_AFTER_S else "calm"
    short = " ".join(paint(f"{sym}{n}", fg=color, bold=True) for n, _, sym, color in shown)
    return Segment(DOT.join(parts), priority=90, tone=tone, short=short)


def commits(git: GitState) -> Optional[Segment]:
    """Only what differs from "all in sync". In sync shows nothing."""
    base = gitstate.short_base(git.base)
    rows = []
    if not git.has_remote:
        rows.append((label("no remote"), label("local")))
    elif not git.upstream and git.branch:
        rows.append((paint("branch not pushed", fg=theme.WARN, bold=True),
                     paint("no ↑", fg=theme.WARN, bold=True)))
    if git.ahead:
        rows.append((paint(f"↑{git.ahead} not pushed", fg=theme.INFO, bold=True),
                     paint(f"↑{git.ahead}", fg=theme.INFO, bold=True)))
    if git.behind:
        rows.append((paint(f"↓{git.behind} to pull", fg=theme.WARN, bold=True),
                     paint(f"↓{git.behind}", fg=theme.WARN, bold=True)))
    if git.ahead_base:
        rows.append((value(str(git.ahead_base)) + label(f" ahead of {base}"),
                     value(f"+{git.ahead_base}")))
    if git.behind_base:
        rows.append((paint(f"{git.behind_base} behind {base}", fg=theme.WARN, bold=True),
                     paint(f"-{git.behind_base}", fg=theme.WARN, bold=True)))
    if git.stash:
        rows.append((label(f"≡{git.stash} stashed"), label(f"≡{git.stash}")))
    if not rows:
        return None
    return Segment(DOT.join(full for full, _ in rows), priority=80,
                   short=" ".join(short for _, short in rows))


def build(session: Session, git: Optional[GitState], home: str, now: float,
          errors: Sequence[str] = (), git_age: float = 0, git_pending: bool = False,
          pr: Optional[Segment] = None) -> List[Segment]:
    git_failed = "git" in errors or git_pending
    segs = [where(session, git, home, git_failed)] if session.cwd else []
    if git is not None:
        if git.operation:
            segs.append(Segment(f"⚑ {git.operation}", priority=99, tone="bad"))
        segs.append(changes(git, now))
        extra = commits(git)
        if extra:
            segs.append(extra)
    if pr:
        segs.append(pr)
    if git_age > STALE_NOTE_S:
        segs.append(Segment(label(f"git data {fmt.duration(git_age)} old"), priority=70))
    if git_pending:
        segs.append(Segment(label("reading git…"), priority=70))
    if errors:
        segs.append(Segment("⚠ " + ",".join(errors), priority=98, tone="warn", short="⚠"))
    return segs
