"""Chips, width fitting, and line composition."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, List, Optional, Sequence, Tuple

from . import theme

CHIP_PAD = 2  # one space on each side of a chip's text
GAP = 1       # the width of the separator between chips


@dataclass(frozen=True)
class Segment:
    """One chip on a line.

    priority: higher stays longer when the line is too wide.
    tone:     "calm" (slate), "warn" (solid amber: act soon), "bad" (solid red: act now).
    short:    optional compact form, used before the chip is dropped.
    """
    text: str
    priority: int = 50
    tone: str = "calm"
    short: Optional[str] = None


def _total(segs: Sequence[Segment]) -> int:
    if not segs:
        return 0
    return sum(theme.width(s.text) + CHIP_PAD for s in segs) + GAP * (len(segs) - 1)


def fit(segments: Sequence[Segment], budget: int) -> Tuple[Segment, ...]:
    """Return the chips that fit in `budget` columns, in their original order.

    1. Use short forms, lowest priority first, until the line fits.
    2. Drop chips, lowest priority first (always keep one).
    3. Give the full form back to any shortened chip that now fits.
    """
    segs: List[Segment] = list(segments)
    by_priority = sorted(range(len(segs)), key=lambda i: segs[i].priority)
    full = list(segs)

    for i in by_priority:
        if _total(segs) <= budget:
            break
        if segs[i].short is not None:
            segs[i] = replace(segs[i], text=segs[i].short)

    alive = [True] * len(segs)
    for i in by_priority:
        kept = [s for s, a in zip(segs, alive) if a]
        if _total(kept) <= budget or len(kept) == 1:
            break
        alive[i] = False

    for i in reversed(by_priority):
        if alive[i] and segs[i].text != full[i].text:
            trial = list(segs)
            trial[i] = full[i]
            if _total([s for s, a in zip(trial, alive) if a]) <= budget:
                segs = trial

    return tuple(s for s, a in zip(segs, alive) if a)


def line(segments: Iterable[Segment], budget: int) -> str:
    segs = tuple(segments)
    if not segs:
        return ""
    kept = fit(segs, budget)
    separator = theme.paint("│", fg=theme.SEPARATOR, bg=theme.CHIP_BG)
    return theme.truncate_visible(separator.join(theme.chip(s.text, s.tone) for s in kept), budget)


def block(rows: Sequence[str]) -> List[str]:
    """Pad the rows to one width, so that they read as one even band."""
    widest = max((theme.width(r) for r in rows), default=0)
    return [r + theme.chip_fill(widest - theme.width(r)) if r and theme.width(r) < widest else r
            for r in rows]


def compose(lines: Iterable[str]) -> str:
    return "\n".join(l for l in lines if l)
