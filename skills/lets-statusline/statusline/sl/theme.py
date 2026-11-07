"""Palette, ANSI styling, chips, and visible-width helpers.

Colors are 24-bit for a dark terminal background.

The rule of the line: everything sits on one slate band. Only what needs you gets
a solid color: amber = act soon, red = act now. So a calm line has no solid block.

Text: white = labels, white bold = values.
Green/amber/orange/red = state. Teal/blue/magenta = where you are.
PR states use the GitHub colors: green open, gray draft, purple merged, red closed.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, Tuple

RGB = Tuple[int, int, int]

BG = (30, 33, 39)          # assumed terminal background, used to make dim tints
CHIP_BG = (52, 57, 68)     # slate: the background of a calm chip
INK = (30, 33, 39)         # dark text on a solid amber chip
TEXT = (238, 240, 244)     # white: values (bold)
LABEL = (212, 216, 223)    # white: labels
MUTED = (165, 170, 180)    # light gray: the · inside a chip
SEPARATOR = (120, 127, 142)  # the thin line between chips
FAINT = (75, 82, 99)       # darker gray: rule lines in the preview
OK = (152, 195, 121)       # green
WARN = (229, 192, 123)     # amber
HOT = (209, 154, 102)      # orange
BAD = (224, 108, 117)      # red
ALARM_BG = (190, 38, 52)   # solid red chips and banners
ALARM_FG = (255, 255, 255)
REPO = (86, 182, 194)      # teal: the repo and the base branch
INFO = (97, 175, 239)      # blue: a feature branch, unpushed commits, running checks
WORKTREE = (198, 120, 221)  # magenta: a linked worktree
PR_OPEN = (63, 185, 80)
PR_DRAFT = (150, 158, 170)
PR_MERGED = (163, 113, 247)
PR_CLOSED = (248, 81, 73)
GOOD = (126, 203, 138)     # usage limits, from positive to negative: soft green
FAIR = (196, 208, 120)     # soft lime
POOR = (232, 176, 98)      # soft amber
BADLY = (232, 112, 112)    # soft red
MODEL_FABLE = (240, 128, 180)   # rose
MODEL_OPUS = (177, 140, 255)    # violet
MODEL_SONNET = (90, 190, 250)   # sky blue
MODEL_HAIKU = (110, 220, 170)   # mint

HEALTH_COLORS = {0: OK, 1: WARN, 2: BAD}

RESET = "\x1b[0m"
_ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\]8;;[^\x07\x1b]*(?:\x07|\x1b\\)")
_SGR = re.compile(r"\x1b\[[0-9;]*m")
_SAFE_URL = re.compile(r"https://[^\x00-\x20\x7f-\x9f]+\Z")  # a control character ends the link early


def mix(color: RGB, base: RGB, amount: float) -> RGB:
    """Blend `color` into `base`; amount=1 gives color, 0 gives base."""
    return tuple(round(b + (c - b) * amount) for c, b in zip(color, base))  # type: ignore[return-value]


def dim(color: RGB, amount: float = 0.38) -> RGB:
    return mix(color, BG, amount)


def paint(text: str, fg: Optional[RGB] = None, bg: Optional[RGB] = None,
          bold: bool = False, italic: bool = False) -> str:
    codes = []
    if bold:
        codes.append("1")
    if italic:
        codes.append("3")
    if fg:
        codes.append("38;2;%d;%d;%d" % fg)
    if bg:
        codes.append("48;2;%d;%d;%d" % bg)
    if not codes:
        return text
    return f"\x1b[{';'.join(codes)}m{text}{RESET}"


DOT = paint(" · ", fg=MUTED)   # muted separator inside a chip


def label(text: str) -> str:
    return paint(text, fg=LABEL)


def value(text: str) -> str:
    return paint(text, fg=TEXT, bold=True)


def link(text: str, url: Optional[str]) -> str:
    """A clickable link (OSC 8). A terminal that does not support it shows plain text."""
    if not url or not _SAFE_URL.match(url):
        return text
    return f"\x1b]8;;{url}\x07{text}\x1b]8;;\x07"


def chip(text: str, tone: str = "calm") -> str:
    """One group on the line. Calm keeps its inner colors; warn and bad are solid."""
    if tone in ("warn", "bad"):
        flat = _SGR.sub("", text)
        fg, bg = (INK, WARN) if tone == "warn" else (ALARM_FG, ALARM_BG)
        return paint(f" {flat} ", fg=fg, bg=bg, bold=True)
    background = "\x1b[48;2;%d;%d;%dm" % CHIP_BG
    return background + " " + text.replace(RESET, RESET + background) + " " + RESET


def chip_fill(columns: int) -> str:
    """Empty columns on the chip background, to even out the rows."""
    return paint(" " * columns, bg=CHIP_BG)


def strip(s: str) -> str:
    return _ANSI.sub("", s)


def _char_width(ch: str) -> int:
    if unicodedata.combining(ch) or ch in "‍️":   # zero-width joiner, emoji style
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def width(s: str) -> int:
    """Terminal columns used by `s` (ANSI codes ignored, wide chars count 2)."""
    return sum(_char_width(ch) for ch in strip(s))


def truncate_visible(s: str, max_width: int) -> str:
    """Cut `s` to `max_width` columns. Keep the ANSI codes; end with … and a reset."""
    if width(s) <= max_width:
        return s
    if max_width <= 0:
        return ""
    out, used, i = [], 0, 0
    while i < len(s):
        m = _ANSI.match(s, i)
        if m:
            out.append(m.group(0))
            i = m.end()
            continue
        w = _char_width(s[i])
        if used + w > max_width - 1:
            break
        out.append(s[i])
        used += w
        i += 1
    return "".join(out) + "…" + RESET
