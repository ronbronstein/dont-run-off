"""Line 3 — how much usage is left? The 5-hour and 7-day limits, with pace."""
from __future__ import annotations

from typing import List, Optional

from . import bars, fmt, theme
from .layout import Segment
from .payload import Limit, Session
from .theme import label, paint, value

MIN_ELAPSED = 0.10  # below 10% of the window, the pace is too noisy to judge
PRIORITY = {"5h": 90, "7d": 75}
METER_CELLS = {"wide": 10, "normal": 8, "narrow": 6}
WEEK_CELLS = 7                  # one square per day
METER = ("▮", "▮", "▯")         # filled, partial (rounds up), empty
SQUARES = ("■", "■", "□")
CLOCK = "◷"                     # one-column text symbols, not emoji
CALENDAR = "▦"


def pace(limit: Limit, now: float):
    """Return (projected % at reset, seconds until 100% at this pace, seconds to reset).

    The first two are None early in the window or before any use: the pace is noise then.
    """
    if limit.resets_at is None:
        return None, None, None
    left = max(0.0, limit.resets_at - now)
    elapsed = limit.window_s - left
    if elapsed < limit.window_s * MIN_ELAPSED or limit.used_pct <= 0:
        return None, None, left
    rate = limit.used_pct / elapsed                 # percent per second
    projected = limit.used_pct + rate * left
    lasts = max(0.0, 100 - limit.used_pct) / rate
    return projected, lasts, left


def pace_color(projected: float) -> theme.RGB:
    """Use it or lose it: room left unused at the reset is a nudge, running out is the alarm."""
    if projected >= 100:
        return theme.BADLY
    if projected >= 85:
        return theme.GOOD
    return theme.FAIR if projected >= 60 else theme.POOR


def _pace_text(projected: Optional[float], lasts: Optional[float], left: Optional[float]) -> str:
    if projected is None or lasts is None or left is None:
        return ""
    words = f"  out in ~{fmt.duration(lasts)}" if lasts < left else f"  lasts ~{fmt.duration(lasts)}"
    return paint(words, fg=pace_color(projected), bold=True)


def cost_segment(usd: Optional[float]) -> Optional[Segment]:
    """The session cost at API prices. A subscriber does not pay it, so it stays white."""
    if usd is None:
        return None
    return Segment(label("In API costs: ") + value(fmt.money(usd)), priority=60, apart=True)


def state(limit: Limit, projected: Optional[float]) -> int:
    p = projected if projected is not None else limit.used_pct
    if limit.used_pct >= 90 or p >= 110:
        return 2
    if limit.used_pct >= 70 or p >= 90:
        return 1
    return 0


def used_color(used_pct: float) -> theme.RGB:
    """A low percent is positive. The amber and red zones start at the state() limits."""
    if used_pct >= 90:
        return theme.BADLY
    if used_pct >= 70:
        return theme.POOR
    return theme.FAIR if used_pct >= 50 else theme.GOOD


def left_color(share_left: float) -> theme.RGB:
    """A long wait for the reset is negative; a short wait is positive."""
    if share_left >= 0.75:
        return theme.BADLY
    if share_left >= 0.5:
        return theme.POOR
    return theme.FAIR if share_left >= 0.25 else theme.GOOD


def _reset(limit: Limit, left: Optional[float]) -> str:
    """The 5h limit counts down. The 7d limit names its day and time: a date is not a warning."""
    if left is None:
        return ""
    if limit.label == "7d":
        return label(f"  {CALENDAR} ") + value(fmt.when(limit.resets_at))
    wait = paint(fmt.heavy(fmt.duration(left)), fg=left_color(left / limit.window_s), bold=True)
    return label(f"  {CLOCK} ") + wait


def limit_segment(limit: Limit, now: float, priority: int, tier: str = "wide") -> Segment:
    if limit.resets_at is not None and limit.resets_at <= now:
        # The window has reset but the payload is older than the clock (idle timer refresh).
        return Segment(label(f"{limit.label} reset"), priority=priority)
    projected, lasts, left = pace(limit, now)
    health = state(limit, projected)
    pct = paint(f"{limit.used_pct:.0f}%", fg=used_color(limit.used_pct), bold=True)
    head = label(limit.label + " ") + pct
    is_week = limit.label == "7d"
    bar = bars.zone_bar(limit.used_pct, 100, WEEK_CELLS if is_week else METER_CELLS[tier],
                        used_color, SQUARES if is_week else METER)
    speed = _pace_text(projected, lasts, left)
    reset = _reset(limit, left)
    return Segment(label(limit.label + " ") + bar + " " + pct + speed + reset, priority=priority,
                   tone="bad" if health == 2 else "calm",
                   short=head + speed + reset)


def build(s: Session, now: float, tier: str = "wide") -> List[Segment]:
    segs = [limit_segment(l, now, PRIORITY.get(l.label, 70), tier) for l in s.limits]
    cost = cost_segment(s.cost_usd)
    return segs + ([cost] if cost else [])
