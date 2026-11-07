"""The context ladder: how loud the context warning is.

The line gives an early warning that grows until it cannot be ignored. On a big
window (1M) the steps are absolute tokens, because quality drops with tokens
read, not with percent of the window. On a small window (200k) the steps are
percent, because the hard limit comes first.
"""
from __future__ import annotations

from typing import List, Tuple

from . import fmt, theme
from .payload import Context
from .theme import RGB

TOKEN_STEPS = (200_000, 250_000, 300_000, 400_000, 500_000, 600_000)
PCT_STEPS = (50, 60, 70, 80, 85, 90)
BIG_WINDOW = 500_000
# 20% orange, 25% red, 30% "Seriously?" (red starts at 25%)
LEVEL_COLORS = (theme.OK, theme.HOT, theme.BAD, theme.BAD, theme.BAD, theme.BAD, theme.BAD)


def thresholds(window: int) -> Tuple[int, ...]:
    if window >= BIG_WINDOW:
        return TOKEN_STEPS
    return tuple(window * p // 100 for p in PCT_STEPS)


def level(used: int, window: int) -> int:
    return sum(1 for t in thresholds(window) if used >= t)


def horizon(window: int) -> int:
    return thresholds(window)[-1]


def color_for(used: float, window: int) -> RGB:
    return LEVEL_COLORS[level(int(used), window)]


def _messages(lvl: int, tok: str) -> Tuple[str, ...]:
    """Banner text variants for a level, longest first."""
    if lvl == 4:
        return (f"Seriously?! Context is at {tok}. Wrap up, then start fresh.",
                f"Seriously?! {tok}. Wrap up", f"Seriously?! {tok}")
    if lvl == 5:
        return (f"SERIOUSLY. {tok} OF CONTEXT. Wrap up NOW, then start fresh.",
                f"SERIOUSLY. {tok}. Wrap up NOW", f"SERIOUSLY. {tok}")
    return (f"STOP. {tok} of context. Every reply re-reads all of it: slower, costlier, sloppier.",
            f"STOP. {tok} of context. Every reply re-reads all of it.",
            f"STOP. {tok}")


def _bar(text: str, width: int) -> str:
    pad = max(0, width - theme.width(text) - 1)
    return theme.paint(" " + text + " " * pad, fg=theme.ALARM_FG, bg=theme.ALARM_BG, bold=True)


def _pick(variants: Tuple[str, ...], budget: int) -> str:
    for v in variants:
        if theme.width(v) + 2 <= budget:
            return v
    return variants[-1]


def banner_lines(ctx: Context, budget: int) -> List[str]:
    """Banner lines shown above the status line from level 4 up.

    Levels 4-5: one line whose red width grows with the context.
    Level 6: two full-width lines.
    """
    lvl = level(ctx.used_tokens, ctx.window)
    if lvl < 4:
        return []
    text = _pick(_messages(lvl, fmt.tokens(ctx.used_tokens)), budget)
    if lvl == 6:
        second = _pick(("Wrap up now with /dont-run-off:lets-wrap, then /clear.",
                        "Wrap up, then /clear"), budget)
        return [_bar(text, budget), _bar(second, budget)]
    grow = round(budget * min(1.0, ctx.used_tokens / horizon(ctx.window)))
    return [_bar(text, max(theme.width(text) + 2, grow))]
