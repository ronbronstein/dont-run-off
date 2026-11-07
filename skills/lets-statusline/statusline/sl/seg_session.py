"""The model and effort, the active task (line 2), and the session name (end of line 1)."""
from __future__ import annotations

from typing import Optional, Tuple

from . import fmt, theme
from .layout import Segment
from .payload import Session
from .tasks import TaskSummary
from .theme import DOT, label, paint, value


# One-column text symbols, not emoji: an emoji glyph can break the line width.
FAMILIES = (("fable", "❦", theme.MODEL_FABLE), ("opus", "◆", theme.MODEL_OPUS),
            ("sonnet", "♪", theme.MODEL_SONNET), ("haiku", "✿", theme.MODEL_HAIKU))
EFFORT_DOTS = {"low": 1, "medium": 2, "high": 3, "xhigh": 4, "max": 5}
EFFORT_CELLS = 5


def family_style(name: str, model_id: Optional[str]) -> Tuple[str, theme.RGB]:
    """The icon and color of a model. The name decides; the id is the fallback."""
    for text in (name, model_id or ""):
        for family, icon, color in FAMILIES:
            if family in text.lower():
                return icon, color
    return "◇", theme.TEXT


def effort_mark(level: str, color: theme.RGB) -> Optional[str]:
    filled = EFFORT_DOTS.get(level.lower())
    if filled is None:
        return None
    return (paint("●" * filled, fg=color)
            + paint("○" * (EFFORT_CELLS - filled), fg=theme.mix(color, theme.CHIP_BG, 0.55)))


def model(s: Session) -> Optional[Segment]:
    if not s.model_name:
        return None
    icon, color = family_style(s.model_name, s.model_id)
    name = paint(f"{icon} {s.model_name}", fg=color, bold=True)
    parts = [name]
    short = name
    if s.effort:
        dots = effort_mark(s.effort, color)
        word = value(s.effort)
        parts += [dots, word] if dots else [word]
        short = f"{name} {dots or word}"
    if s.fast_mode:
        parts.append(paint("fast", fg=theme.WARN, bold=True))
    if s.thinking is False:
        parts.append(label("no-think"))
    if s.agent_name:
        parts.append(paint(f"agent {s.agent_name}", fg=theme.WORKTREE, bold=True))
    if s.output_style and s.output_style != "default":
        parts.append(label(f"style {s.output_style}"))
    return Segment(" ".join(parts), priority=92, short=short)


def session_chip(s: Session) -> Optional[Segment]:
    age = fmt.duration(s.duration_s) if s.duration_s else None
    if not s.session_name:
        return Segment(label("session ") + value(age), priority=30) if age else None
    name = paint(f"“{fmt.truncate(s.session_name, 32)}”", fg=theme.LABEL, italic=True)
    if not age:
        return Segment(name, priority=30)
    return Segment(name + " " + value(age), priority=30, short=value(age))


COINS = "⛁"  # the session cost at API prices


def cost_chip(usd: Optional[float]) -> Optional[Segment]:
    """The session cost at API prices. A subscriber does not pay it, so it stays white."""
    if usd is None:
        return None
    return Segment(label(f"{COINS} ") + value(fmt.money(usd)), priority=60)


def task_chip(t: Optional[TaskSummary]) -> Optional[Segment]:
    """Only what needs attention. A backlog count is noise."""
    if t is None:
        return None
    parts = []
    short = None
    if t.active:
        more = f" +{t.active_count - 1}" if t.active_count > 1 else ""
        parts.append(paint("▶ " + fmt.truncate(t.active, 34) + more, fg=theme.INFO, bold=True))
        short = paint("▶ " + fmt.truncate(t.active, 14), fg=theme.INFO, bold=True)
    if t.overdue:
        parts.append(paint(f"{t.overdue} overdue", fg=theme.BAD, bold=True))
    if t.due_today:
        parts.append(paint(f"{t.due_today} due today", fg=theme.WARN, bold=True))
    if not parts:
        return None
    return Segment(DOT.join(parts), priority=55, short=short)
