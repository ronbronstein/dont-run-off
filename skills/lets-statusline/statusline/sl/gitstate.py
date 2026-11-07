"""Collect git facts for the cwd with parallel, read-only git calls."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

TIMEOUT_S = 0.5   # the status line must stay fast; gitcache retries in the background
_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", LC_ALL="C")


class GitError(RuntimeError):
    """A git call failed in a way that is not 'this is not a repo'."""


class GitTimeout(GitError):
    """A git call took too long. Normal in a big repo; not worth a log line."""


def short_base(base: Optional[str]) -> Optional[str]:
    """origin/main -> main. A local base keeps its name."""
    if base is None:
        return None
    return base[len("origin/"):] if base.startswith("origin/") else base


@dataclass(frozen=True)
class GitState:
    toplevel: str
    branch: Optional[str]        # None when detached
    oid: Optional[str]           # short commit id; None before the first commit
    upstream: Optional[str]
    ahead: int
    behind: int
    staged: int
    modified: int
    untracked: int
    conflicts: int
    stash: int
    last_commit_ts: Optional[int]
    operation: Optional[str]     # "rebase 2/5", "merge", ...
    linked_worktree: bool
    main_repo: str
    has_remote: bool
    base: Optional[str]          # the branch work merges into: origin/main, main, ...
    ahead_base: Optional[int]    # None on the base branch or when unknown
    behind_base: Optional[int]

    @property
    def is_base(self) -> bool:
        return self.branch is not None and self.branch == short_base(self.base)


def to_dict(state: GitState) -> dict:
    return asdict(state)


def from_dict(d: dict) -> GitState:
    try:
        return GitState(**d)
    except TypeError as e:
        raise GitError(f"snapshot has an unknown shape: {e}") from e


def parse_status(text: str) -> Dict[str, object]:
    """Parse `git status --porcelain=v2 --branch --show-stash`."""
    s: Dict[str, object] = dict(branch=None, oid=None, upstream=None, ahead=0, behind=0,
                                stash=0, staged=0, modified=0, untracked=0, conflicts=0)
    for row in text.splitlines():
        if row.startswith("# branch.oid "):
            oid = row[13:].strip()
            s["oid"] = None if oid == "(initial)" else oid[:7]
        elif row.startswith("# branch.head "):
            head = row[14:].strip()
            s["branch"] = None if head == "(detached)" else head
        elif row.startswith("# branch.upstream "):
            s["upstream"] = row[18:].strip()
        elif row.startswith("# branch.ab "):
            m = re.match(r"# branch\.ab \+(\d+) -(\d+)", row)
            if m:
                s["ahead"], s["behind"] = int(m.group(1)), int(m.group(2))
        elif row.startswith("# stash "):
            s["stash"] = int(row[8:].strip() or 0)
        elif row[:2] in ("1 ", "2 "):
            xy = row[2:4]
            s["staged"] += xy[0] != "."      # type: ignore[operator]
            s["modified"] += xy[1] != "."    # type: ignore[operator]
        elif row.startswith("u "):
            s["conflicts"] += 1              # type: ignore[operator]
        elif row.startswith("? "):
            s["untracked"] += 1              # type: ignore[operator]
    return s


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""


def operation(git_dir: str) -> Optional[str]:
    """Name the operation in progress (rebase, merge, ...), if any."""
    for sub, num, end in (("rebase-merge", "msgnum", "end"), ("rebase-apply", "next", "last")):
        d = os.path.join(git_dir, sub)
        if os.path.isdir(d):
            n, total = _read(os.path.join(d, num)), _read(os.path.join(d, end))
            return f"rebase {n}/{total}" if n and total else "rebase"
    for marker, name in (("MERGE_HEAD", "merge"), ("CHERRY_PICK_HEAD", "cherry-pick"),
                         ("REVERT_HEAD", "revert"), ("BISECT_LOG", "bisect")):
        if os.path.exists(os.path.join(git_dir, marker)):
            return name
    return None


def repo_name(common_dir: str, toplevel: str, linked: bool) -> str:
    """The main repo's name. A linked worktree names its main repo, not itself."""
    if not linked:
        return os.path.basename(toplevel)
    base = os.path.basename(common_dir)
    if base == ".git":
        return os.path.basename(os.path.dirname(common_dir))
    return base[:-4] if base.endswith(".git") else base    # a bare repo: demo.git


def has_remote(common_dir: str) -> bool:
    return bool(re.search(r'^\s*\[remote "', _read(os.path.join(common_dir, "config")), re.M))


def base_branch(common_dir: str) -> Optional[str]:
    """The branch work merges into. It differs per repo, so read it from origin/HEAD first."""
    m = re.match(r"ref: refs/remotes/(.+)",
                 _read(os.path.join(common_dir, "refs", "remotes", "origin", "HEAD")))
    if m:
        return m.group(1)
    packed = _read(os.path.join(common_dir, "packed-refs"))
    for name in ("main", "master"):
        if os.path.exists(os.path.join(common_dir, "refs", "heads", name)) \
                or re.search(rf" refs/heads/{name}$", packed, re.M):
            return name
    return None


def _start(cwd: str, *args: str) -> subprocess.Popen:
    return subprocess.Popen(["git", "-C", cwd, *args], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=_ENV)


def _finish(p: subprocess.Popen, what: str, timeout: float) -> subprocess.CompletedProcess:
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise GitTimeout(f"git {what} timed out after {timeout}s") from e
    return subprocess.CompletedProcess(p.args, p.returncode, out, err)


def _reap(procs: List[subprocess.Popen]) -> None:
    """Stop any git call still running and close every pipe."""
    for p in procs:
        if p.poll() is None:
            p.kill()
        for stream in (p.stdout, p.stderr):
            if stream:
                stream.close()
        p.wait()


def _base_counts(cwd: str, base: str, timeout: float) -> Tuple[Optional[int], Optional[int]]:
    """(ahead of base, behind base). A failure here is not worth losing the line for."""
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-list", "--left-right", "--count", f"{base}...HEAD"],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, env=_ENV,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, None
    m = re.fullmatch(r"(\d+)\s+(\d+)", r.stdout.strip()) if r.returncode == 0 else None
    return (int(m.group(2)), int(m.group(1))) if m else (None, None)


def collect(cwd: str, timeout: float = TIMEOUT_S) -> Optional[GitState]:
    """Return the git state for `cwd`, or None when it is not inside a work tree."""
    if not cwd or not os.path.isdir(cwd):
        return None
    procs: List[subprocess.Popen] = [
        _start(cwd, "rev-parse", "--path-format=absolute", "--show-toplevel",
               "--absolute-git-dir", "--git-common-dir"),
        _start(cwd, "--no-optional-locks", "status", "--porcelain=v2", "--branch",
               "--show-stash", "--untracked-files=normal"),
        _start(cwd, "log", "-1", "--format=%ct"),
    ]
    try:
        rev = _finish(procs[0], "rev-parse", timeout)
        if rev.returncode != 0:
            return None                           # not a work tree: not an error
        status = _finish(procs[1], "status", timeout)
        log = _finish(procs[2], "log", timeout)
    finally:
        _reap(procs)
    if status.returncode != 0:
        raise GitError(f"git status failed in {cwd}: {status.stderr.strip()[:200]}")

    toplevel, git_dir, common_dir = (rev.stdout.splitlines() + ["", "", ""])[:3]
    common_dir = os.path.normpath(common_dir or git_dir)
    linked = os.path.normpath(git_dir) != common_dir
    last = log.stdout.strip()
    s = parse_status(status.stdout)
    base = base_branch(common_dir)
    counts: Tuple[Optional[int], Optional[int]] = (None, None)
    if s["branch"] and s["oid"] and base and s["branch"] != short_base(base):
        counts = _base_counts(cwd, base, timeout)
    return GitState(
        toplevel=toplevel, branch=s["branch"], oid=s["oid"], upstream=s["upstream"],  # type: ignore[arg-type]
        ahead=s["ahead"], behind=s["behind"], staged=s["staged"],  # type: ignore[arg-type]
        modified=s["modified"], untracked=s["untracked"], conflicts=s["conflicts"],  # type: ignore[arg-type]
        stash=s["stash"],  # type: ignore[arg-type]
        last_commit_ts=int(last) if log.returncode == 0 and last.isdigit() else None,
        operation=operation(git_dir),
        linked_worktree=linked, main_repo=repo_name(common_dir, toplevel, linked),
        has_remote=has_remote(common_dir), base=base, ahead_base=counts[0], behind_base=counts[1],
    )
