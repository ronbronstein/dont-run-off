"""The PR chip: state in the GitHub colors, then only the signal that matters most."""
from __future__ import annotations

from typing import List, Optional, Tuple

from . import fmt, theme
from .layout import Segment
from .prstate import PrFacts, PrView
from .theme import DOT, label, paint, value

PRIORITY = 85


def _tag(f: PrFacts) -> str:
    text = f"MR !{f.number}" if f.kind == "mr" else f"PR #{f.number}"
    return theme.link(value(text), f.url)


def _state_word(f: PrFacts, now: float) -> str:
    if f.state in ("MERGED", "CLOSED"):
        word, color = ("merged", theme.PR_MERGED) if f.state == "MERGED" else ("closed", theme.PR_CLOSED)
        when = f" {fmt.age(now - f.ended_at)}" if f.ended_at is not None else ""
        return paint(word + when, fg=color, bold=True)
    if f.draft:
        return paint("draft", fg=theme.PR_DRAFT, bold=True)
    return paint("open", fg=theme.PR_OPEN, bold=True)


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("s" if n != 1 else "")


def _signals(f: PrFacts) -> Tuple[List[str], Optional[str]]:
    """Return (the signals in words, the short word of an alarm, if any)."""
    signals: List[str] = []
    alarm = None
    if f.conflicting:
        signals.append("✗ conflicts")
        alarm = "✗ conflicts"
    if f.failed:
        signals.append(f"✗ {_plural(f.failed, 'check')} failed")
        alarm = "✗ checks"
    if f.review == "CHANGES_REQUESTED":
        signals.append("changes requested")
        alarm = alarm or "✗ changes"
    if alarm:
        return signals, alarm
    if f.review == "APPROVED":
        signals.append(paint("approved", fg=theme.OK, bold=True))
    elif f.review == "REVIEW_REQUIRED":
        signals.append(paint("needs review", fg=theme.INFO, bold=True))
    if f.pending:
        signals.append(paint(f"◌ {_plural(f.pending, 'check')} running", fg=theme.INFO, bold=True))
    elif f.passed:
        signals.append(paint("✓ checks", fg=theme.OK, bold=True))
    return signals, None


def _pr(f: PrFacts, now: float) -> Segment:
    head = _tag(f) + " " + _state_word(f, now)
    if f.state != "OPEN":
        return Segment(head, priority=PRIORITY)
    signals, alarm = _signals(f)
    text = DOT.join([head] + signals)
    if alarm:
        return Segment(text, priority=PRIORITY, tone="bad", short=_tag(f) + " " + alarm)
    return Segment(text, priority=PRIORITY, short=head if signals else None)


def build(view: Optional[PrView], now: float) -> Optional[Segment]:
    if view is None:
        return None
    if view.kind == "none":
        return Segment(label("no PR"), priority=40)
    if view.kind == "unknown" or view.facts is None:
        return Segment(label("PR ?"), priority=40)
    return _pr(view.facts, now)
