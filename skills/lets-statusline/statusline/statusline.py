#!/usr/bin/env python3
"""Claude Code status line. Reads the session JSON on stdin, prints 3 rows (more at high context).

The /lets-statusline skill installs it. Read README.md to change it.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sl import errlog, render, theme  # noqa: E402


def main() -> int:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        out = render.render(raw, os.environ, time.time())
    except Exception as e:  # noqa: BLE001 - last line of defense: never blank the line
        errlog.log(os.path.join(render.default_cache_dir(), "errors.log"), "fatal", e)
        out = theme.chip("statusline error: see ~/.claude/cache/statusline/errors.log", "bad")
    # Bytes, not text: a non-UTF-8 locale must not break the output.
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
