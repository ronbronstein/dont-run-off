import json
import unittest

from sl import seg_session, theme
from sl.payload import parse
from sl.tasks import TaskSummary


def plain(seg):
    return theme.strip(seg.text), theme.strip(seg.short) if seg.short else None


def session(**extra):
    return parse(json.dumps(extra))


MODEL = {"display_name": "Opus 5.5"}


class Model(unittest.TestCase):
    def test_name_and_effort(self):
        seg = seg_session.model(session(model=MODEL, effort={"level": "xhigh"}))
        self.assertEqual(plain(seg), ("◆ Opus 5.5 ●●●●○ xhigh", "◆ Opus 5.5 ●●●●○"))

    def test_each_model_family_has_its_own_icon_and_color(self):
        seen = set()
        for name, icon in (("Fable 5.1", "❦"), ("Opus 5.5", "◆"), ("Sonnet 5.5", "♪"),
                           ("Haiku 5.5", "✿")):
            seg = seg_session.model(session(model={"display_name": name}))
            self.assertEqual(plain(seg)[0], f"{icon} {name}")
            self.assertEqual(theme.width(icon), 1, "a wide icon breaks the line width")
            seen.add(seg_session.family_style(name, None)[1])
        self.assertEqual(len(seen), 4)

    def test_family_comes_from_the_id_when_the_name_does_not_say(self):
        seg = seg_session.model(session(model={"display_name": "Custom", "id": "claude-haiku-5-5"}))
        self.assertEqual(plain(seg)[0], "✿ Custom")

    def test_unknown_model_keeps_the_name_with_a_plain_icon(self):
        seg = seg_session.model(session(model={"display_name": "Mystery 9"}))
        self.assertEqual(plain(seg)[0], "◇ Mystery 9")

    def test_each_effort_level_has_its_dots(self):
        for level, dots in (("low", "●○○○○"), ("medium", "●●○○○"), ("high", "●●●○○"),
                            ("xhigh", "●●●●○"), ("max", "●●●●●"), ("MAX", "●●●●●")):
            seg = seg_session.model(session(model=MODEL, effort={"level": level}))
            self.assertEqual(plain(seg)[0], f"◆ Opus 5.5 {dots} {level}")

    def test_unknown_effort_shows_the_word_with_no_dots(self):
        seg = seg_session.model(session(model=MODEL, effort={"level": "turbo"}))
        self.assertEqual(plain(seg), ("◆ Opus 5.5 turbo", "◆ Opus 5.5 turbo"))

    def test_short_form_keeps_the_effort_and_drops_the_badges(self):
        seg = seg_session.model(session(model=MODEL, effort={"level": "high"},
                                        agent={"name": "rev"}))
        self.assertEqual(plain(seg)[1], "◆ Opus 5.5 ●●●○○")

    def test_badges_only_for_exceptions(self):
        seg = seg_session.model(session(model=MODEL, fast_mode=True, thinking={"enabled": False},
                                        agent={"name": "rev"}, output_style={"name": "terse"}))
        for word in ("fast", "no-think", "agent rev", "style terse"):
            self.assertIn(word, plain(seg)[0])

    def test_defaults_show_no_badges(self):
        seg = seg_session.model(session(model=MODEL, thinking={"enabled": True},
                                        output_style={"name": "default"}))
        self.assertEqual(plain(seg)[0], "◆ Opus 5.5")

    def test_no_model(self):
        self.assertIsNone(seg_session.model(session()))


class SessionChip(unittest.TestCase):
    def test_name_and_age(self):
        seg = seg_session.session_chip(session(session_name="Mod research",
                                               cost={"total_duration_ms": 3_480_000}))
        self.assertEqual(plain(seg), ("“Mod research” 58m", "58m"))

    def test_age_with_no_name(self):
        seg = seg_session.session_chip(session(cost={"total_duration_ms": 3_480_000}))
        self.assertEqual(plain(seg)[0], "session 58m")

    def test_long_name_is_cut(self):
        seg = seg_session.session_chip(session(session_name="x" * 80))
        self.assertLess(theme.width(seg.text), 40)

    def test_nothing_to_show(self):
        self.assertIsNone(seg_session.session_chip(session()))


class TaskChip(unittest.TestCase):
    def summary(self, **over):
        base = dict(namespace="a", pending=30, overdue=0, due_today=0, active_count=0, active=None)
        base.update(over)
        return TaskSummary(**base)

    def test_a_plain_backlog_shows_nothing(self):
        self.assertIsNone(seg_session.task_chip(self.summary()))

    def test_active_task(self):
        seg = seg_session.task_chip(self.summary(active="Ship it", active_count=1))
        self.assertEqual(plain(seg)[0], "▶ Ship it")

    def test_more_than_one_active(self):
        seg = seg_session.task_chip(self.summary(active="Ship it", active_count=3))
        self.assertEqual(plain(seg)[0], "▶ Ship it +2")

    def test_overdue_and_due_today(self):
        seg = seg_session.task_chip(self.summary(overdue=2, due_today=1))
        self.assertEqual(plain(seg)[0], "2 overdue · 1 due today")


if __name__ == "__main__":
    unittest.main()
