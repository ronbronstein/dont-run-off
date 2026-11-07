"""Append status line errors to a small rotating log file.

The status line must never crash (a non-zero exit blanks it), so data sources
catch their errors. They are not swallowed: each one lands here with context,
and the line shows a ⚠ marker.
"""
from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime

MAX_BYTES = 256 * 1024


def log(path: str, where: str, exc: BaseException, **context: object) -> None:
    ctx = " ".join(f"{k}={v}" for k, v in context.items())
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)[-3:])
    entry = f"{datetime.now().isoformat(timespec='seconds')} [{where}] " \
            f"{type(exc).__name__}: {exc} | {ctx}\n{tb}\n"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and os.path.getsize(path) > MAX_BYTES:
            os.replace(path, path + ".1")
        with open(path, "a") as f:
            f.write(entry)
    except OSError as e:
        # Last resort: stderr is visible with `claude --debug`.
        sys.stderr.write(f"statusline: cannot write {path}: {e}\n{entry}")
