#!/usr/bin/env python3
"""Install, update, or undo the status line. The lets-statusline skill runs this.

    python3 install.py status    what is there now, as JSON; changes nothing
    python3 install.py install   back up, copy the code, write statusLine
    python3 install.py undo      put the earlier statusLine back

Standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "statusline")
RECORD = ".install.json"
REFRESH_SECONDS = 10  # sl/seg_context.py TICK_S must match this
SKIP_DIRS = {"__pycache__"}
SKIP_FILES = {".DS_Store", RECORD}
SKIP_SUFFIXES = (".pyc",)


class InstallError(Exception):
    """A problem that the user must fix. The message says what and where."""


def claude_dir() -> str:
    return os.path.join(os.path.expanduser("~"), ".claude")


def settings_path() -> str:
    return os.path.join(claude_dir(), "settings.json")


def target_dir() -> str:
    return os.path.join(claude_dir(), "statusline")


def record_path() -> str:
    return os.path.join(target_dir(), RECORD)


def hash_tree(root: str) -> Dict[str, str]:
    """Relative path -> sha256, for every file that belongs to the line."""
    hashes = {}
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name in SKIP_FILES or name.endswith(SKIP_SUFFIXES):
                continue
            path = os.path.join(folder, name)
            with open(path, "rb") as f:
                hashes[os.path.relpath(path, root).replace(os.sep, "/")] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def read_settings() -> dict:
    path = settings_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        raise InstallError(f"{path} is not valid JSON ({e}). Fix it, then run this again. Nothing changed.") from e
    if not isinstance(data, dict):
        raise InstallError(f"{path} does not hold a JSON object. Fix it, then run this again. Nothing changed.")
    return data


def write_settings(new: dict, expected_keys: set) -> None:
    """Replace the file in one step, after a check that no other key was lost or added."""
    if set(new) != expected_keys:
        raise InstallError(f"Stopped before the write: the keys in {settings_path()} would change. Nothing changed.")
    text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
    real = os.path.realpath(settings_path())  # a link stays a link
    os.makedirs(os.path.dirname(real), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(real), prefix=".settings-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        with open(tmp, encoding="utf-8") as f:
            if json.load(f) != new:
                raise InstallError("Stopped before the write: the new settings did not read back the same.")
        if os.path.exists(real):
            shutil.copymode(real, tmp)
        os.replace(tmp, real)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def free_path(base: str) -> str:
    """base, or base-2, base-3, when two runs land in the same second."""
    path, n = base, 2
    while os.path.exists(path):
        path, n = f"{base}-{n}", n + 1
    return path


def read_record() -> Optional[dict]:
    try:
        with open(record_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def changed_files(reference: Dict[str, str]) -> List[str]:
    installed = hash_tree(target_dir())
    return sorted(p for p in set(installed) | set(reference) if installed.get(p) != reference.get(p))


def status() -> dict:
    source = hash_tree(SOURCE)
    record = read_record()
    settings = read_settings()
    if not os.path.isdir(target_dir()):
        state, changed = "not-installed", []
    elif record is None:
        state, changed = "no-record", changed_files(source)
    else:
        changed = changed_files(record.get("files", {}))
        state = "up-to-date" if record.get("files") == source else "update-available"
    return {
        "state": state,
        "changed_by_user": changed,
        "current_status_line": settings.get("statusLine"),
        "theme": settings.get("theme"),
        "python": platform.python_version(),
        "platform": sys.platform,
        "tools": {t: shutil.which(t) is not None for t in ("git", "gh", "task")},
        "target": target_dir(),
    }


def is_ours(line: object) -> bool:
    """Exact on the quoted entry path: a user's ~/.claude/statusline.sh is not ours."""
    entry = os.path.join(target_dir(), "statusline.py")
    return isinstance(line, dict) and str(line.get("command", "")).endswith(f'"{entry}"')


def install() -> dict:
    settings = read_settings()  # first: broken settings must stop everything
    os.makedirs(claude_dir(), exist_ok=True)
    backup_settings = None
    if os.path.exists(settings_path()):
        backup_settings = free_path(f"{settings_path()}.{stamp()}.bak")
        shutil.copy2(os.path.realpath(settings_path()), backup_settings)

    old_record = read_record() or {}
    current = settings.get("statusLine")
    # A second install must not record its own line as the one to go back to.
    previous = old_record.get("previous_status_line") if is_ours(current) else current

    staging = tempfile.mkdtemp(dir=claude_dir(), prefix=".statusline-new-")
    new_code = os.path.join(staging, "statusline")
    backup_code = None
    try:
        shutil.copytree(SOURCE, new_code, ignore=shutil.ignore_patterns(*SKIP_DIRS, *SKIP_FILES, "*.pyc"))
        with open(os.path.join(new_code, RECORD), "w", encoding="utf-8") as f:
            json.dump({"files": hash_tree(SOURCE), "previous_status_line": previous}, f, indent=2)
        if os.path.exists(target_dir()):
            backup_code = free_path(f"{target_dir()}.backup-{stamp()}")
            os.rename(target_dir(), backup_code)
        os.rename(new_code, target_dir())
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    entry = os.path.join(target_dir(), "statusline.py")
    line = {"type": "command", "command": f'"{sys.executable}" "{entry}"', "refreshInterval": REFRESH_SECONDS}
    write_settings(dict(settings, statusLine=line), set(settings) | {"statusLine"})
    return {"installed": target_dir(), "command": line["command"], "settings_backup": backup_settings,
            "code_backup": backup_code, "previous_status_line": previous}


def undo() -> dict:
    record = read_record()
    if record is None:
        raise InstallError(f"The status line is not installed by this skill: no {record_path()}.")
    settings = read_settings()
    previous = record.get("previous_status_line")
    new = {k: v for k, v in settings.items() if k != "statusLine"}
    if previous is not None:
        new = dict(settings, statusLine=previous)
    backup = free_path(f"{settings_path()}.{stamp()}.bak")
    shutil.copy2(os.path.realpath(settings_path()), backup)
    write_settings(new, set(new))
    return {"restored_status_line": previous, "settings_backup": backup, "code_left_in": target_dir()}


def main(argv: List[str]) -> int:
    commands = {"status": status, "install": install, "undo": undo}
    if len(argv) != 2 or argv[1] not in commands:
        sys.stderr.write(f"Usage: install.py {'|'.join(commands)}\n")
        return 2
    try:
        print(json.dumps(commands[argv[1]](), indent=2, ensure_ascii=False))
    except (InstallError, OSError) as e:
        sys.stderr.write(f"{e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
