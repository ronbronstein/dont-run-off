"""Small text formatters: token counts, durations, ages, the cache clock."""
from __future__ import annotations

import time

_HEAVY = str.maketrans("0123456789dhm", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝗱𝗵𝗺")


def tokens(n: float) -> str:
    n = int(n)
    if n >= 999_500:                       # never "1000k"
        return f"{round(n / 1_000_000, 1):g}M"
    if n >= 1000:
        return f"{round(n / 1000)}k"
    return str(n)


def duration(seconds: float) -> str:
    """Compact time span: 1h47m, 4d3h, 12m."""
    s = int(seconds)
    if s <= 0:
        return "0m"
    if s < 60:
        return "<1m"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        h, m = divmod(s // 60, 60)
        return f"{h}h{m}m" if m else f"{h}h"
    d, h = divmod(s // 3600, 24)
    return f"{d}d{h}h" if h else f"{d}d"


def money(usd: float) -> str:
    """Dollars: cents below $100, whole dollars from there ($7.78, $123, $1,235)."""
    return f"${usd:,.2f}" if usd < 99.995 else f"${usd:,.0f}"


def clock(seconds: float) -> str:
    """A countdown: 53:12, 4:07, 0:09."""
    minutes, secs = divmod(max(0, int(seconds)), 60)
    return f"{minutes}:{secs:02d}"


def age(seconds: float) -> str:
    if seconds < 60:
        return "just now"
    return f"{duration(seconds)} ago"


def truncate(text: str, max_width: int) -> str:
    if max_width <= 0:
        return ""
    if len(text) <= max_width:
        return text
    return text[: max_width - 1] + "…"


def heavy(text: str) -> str:
    """Heavy digits. A terminal has one font size, so this is the nearest thing to "bigger"."""
    return text.translate(_HEAVY)


def when(ts: float) -> str:
    """A local day and time: Thu 08:00."""
    return time.strftime("%a %H:%M", time.localtime(ts))
