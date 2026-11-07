"""The context bar, built from box-drawing characters.

Filled cells use a heavy line (━), a half cell uses ╾, and empty cells use a
light line (─). The shape differs as well as the color, so the bar still reads
for color-blind users and on terminals with poor color.
"""
from __future__ import annotations

from typing import Callable, List, Tuple

from . import theme
from .theme import RGB

FULL, HALF, EMPTY = "━", "╾", "─"
SAND_FULL, SAND_HALF, SAND_EMPTY = "⣿", "⣤", "⣀"


def _cells(fraction: float, cells: int) -> Tuple[int, bool]:
    fill = max(0.0, min(1.0, fraction)) * cells
    full = int(fill)
    half = full < cells and fill - full >= 0.5
    return full, half


def _paint_runs(chars: List[Tuple[str, RGB]]) -> str:
    """Paint runs of equal color together to keep the output short."""
    out, run, color = [], "", None
    for ch, c in chars:
        if c != color and run:
            out.append(theme.paint(run, fg=color))
            run = ""
        run, color = run + ch, c
    if run:
        out.append(theme.paint(run, fg=color))
    return "".join(out)


def sand_bar(fraction: float, cells: int, color: RGB) -> str:
    """Braille sand in one color, for a level that runs down, such as the time left."""
    full, half = _cells(fraction, cells)
    bright = SAND_FULL * full + (SAND_HALF if half else "")
    return theme.paint(bright, fg=color) + theme.paint(SAND_EMPTY * (cells - len(bright)), fg=theme.dim(color))


def zone_bar(used: float, horizon: float, cells: int, color_at: Callable[[float], RGB],
             glyphs: Tuple[str, str, str] = (FULL, HALF, EMPTY)) -> str:
    """A bar whose cells take the color of the zone they cover.

    Filled cells are bright. Empty cells are a dim tint of their zone color, so
    the bar shows where the amber and red zones start before you reach them.
    """
    filled, partial, empty = glyphs
    full, half = _cells(used / horizon if horizon else 1.0, cells)
    step = horizon / cells
    chars = []
    for i in range(cells):
        zone = color_at(i * step + step / 2)
        if i < full:
            chars.append((filled, zone))
        elif i == full and half:
            chars.append((partial, zone))
        else:
            chars.append((empty, theme.dim(zone)))
    return _paint_runs(chars)
