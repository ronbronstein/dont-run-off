"""Line 2, first part — how long can this session go on? The context, and the cache countdown."""
from __future__ import annotations

from typing import List, Optional, Sequence

from . import bars, fmt, ladder, theme
from .layout import Segment
from .payload import Cache, Context, Session
from .theme import DOT, label, paint, value

CTX_CELLS = {"wide": 10, "normal": 8, "narrow": 6}
TANK = ("▰", "▰", "▱")  # filled, partial (rounds up), empty: the context fills like a tank
CACHE_WARN_1H_S = 300
CACHE_WARN_5M_S = 60
CACHE_CELLS = {"wide": 6, "normal": 5, "narrow": 4}
TTL_S = {"5m": 300, "1h": 3600}
TICK_S = 10             # refreshInterval in settings.json: the hourglass turns once per tick
SAND = "⏳"             # both are 2 columns wide, so the turn does not move the line
EMPTY_GLASS = "⌛"
BIG_RECACHE = 100_000   # below this, a cold cache is not worth a warning
MISS_SHOW_S = 600       # the reason for a miss stays this long, then it is noise
_REASONS = {"ttl_expired_1h": "idle >1h", "ttl_expired_5m": "idle >5m",
            "messages_rewritten": "history changed", "tools_changed": "tools changed",
            "tools_added": "tools changed", "tools_removed": "tools changed",
            "system_changed": "system prompt changed", "model_changed": "model changed"}


def _amount(ctx: Context) -> str:
    """On a big window the ladder counts tokens, so percent of 1M only misleads."""
    used = fmt.tokens(ctx.used_tokens)
    return used if ctx.window >= ladder.BIG_WINDOW else f"{used}/{fmt.tokens(ctx.window)}"


def context(ctx: Context, tier: str) -> Segment:
    lvl = ladder.level(ctx.used_tokens, ctx.window)
    color = ladder.LEVEL_COLORS[lvl]
    amount = _amount(ctx)
    bar = bars.zone_bar(ctx.used_tokens, ladder.horizon(ctx.window), CTX_CELLS[tier],
                        lambda v: ladder.color_for(v, ctx.window), TANK)
    head = label("ctx ") + bar + " "
    if lvl >= 3:
        return Segment(head + f"Seriously? {amount} · wrap now", priority=100, tone="bad",
                       short=f"Seriously? {amount}")
    shown = paint(amount, fg=color, bold=True)
    hint = DOT + paint("wrap soon", fg=color, bold=True) if lvl == 2 else ""
    return Segment(head + shown + hint, priority=100, short=label("ctx ") + shown)


def miss_reason(causes: Sequence[str]) -> str:
    words = []
    for cause in causes:
        word = _REASONS.get(cause, cause.replace("_", " "))
        if word not in words:
            words.append(word)
    return ", ".join(words[:2])


def _miss_note(c: Cache, now: float) -> str:
    if c.last_miss_at is None or now - c.last_miss_at > MISS_SHOW_S:
        return ""
    reason = miss_reason(c.last_miss_causes)
    return DOT + paint(f"miss: {reason}" if reason else "miss", fg=theme.WARN, bold=True)


def _glass(now: float) -> str:
    return SAND if int(now // TICK_S) % 2 == 0 else EMPTY_GLASS


def _drain(left: float, ttl: Optional[str], color: theme.RGB, cells: int) -> str:
    total = TTL_S.get(ttl or "")
    return label("cache ") + bars.sand_bar(left / total, cells, color) + " " if total else ""


def cache(c: Cache, now: float, cells: int = CACHE_CELLS["wide"]) -> Optional[Segment]:
    if not c.observed:
        return None
    rebuild = c.recache_tokens or 0
    big = rebuild >= BIG_RECACHE
    note = _miss_note(c, now)
    if not c.warm or (c.expires_at is not None and c.expires_at <= now):
        text = EMPTY_GLASS + label(" cache ") + paint("cold", fg=theme.WARN if big else theme.LABEL, bold=True)
        cost = DOT + label("next reply re-reads ") + value(fmt.tokens(rebuild)) if rebuild else ""
        return Segment(text + cost + note, priority=95, tone="warn" if big else "calm",
                       short=EMPTY_GLASS + " cache cold" if big else text)
    if c.expires_at is None:
        return Segment(label("cache ") + paint("warm", fg=theme.OK, bold=True) + note, priority=95)
    left = c.expires_at - now
    soon = left <= (CACHE_WARN_5M_S if c.ttl == "5m" else CACHE_WARN_1H_S)
    color = theme.WARN if soon else theme.OK
    shown = paint(fmt.clock(left), fg=color, bold=True)
    glass = _glass(now) + " "
    short = glass + shown
    full = glass + _drain(left, c.ttl, color, cells) + shown
    if soon and big:
        return Segment(full + label(" → re-reads ") + value(fmt.tokens(rebuild)) + note,
                       priority=95, tone="warn", short=short)
    return Segment(full + note, priority=95, short=short)


def build(s: Session, now: float, tier: str) -> List[Segment]:
    segs: List[Optional[Segment]] = [context(s.context, tier) if s.context else None,
                                     cache(s.cache, now, CACHE_CELLS[tier]) if s.cache else None]
    return [x for x in segs if x is not None]
