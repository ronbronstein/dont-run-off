import os
import time
import unittest

from sl import fmt, seg_budget, theme
from sl.payload import Limit

NOW = 1_800_000_000
FIVE = 5 * 3600
WEEK = 7 * 86400


def plain(seg):
    return theme.strip(seg.text), theme.strip(seg.short) if seg.short else None


def limit(pct, left, label="5h", span=FIVE):
    return Limit(label, pct, NOW + left, span)


def week(pct, left):
    return limit(pct, left, "7d", WEEK)


class Utc(unittest.TestCase):
    """NOW is Friday 2027-01-15 08:00 UTC. Pin the zone so the day and time are stable."""

    def setUp(self):
        self.old = os.environ.get("TZ")
        os.environ["TZ"] = "UTC"
        time.tzset()

    def tearDown(self):
        if self.old is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = self.old
        time.tzset()


class FiveHourChip(unittest.TestCase):
    def test_a_meter_a_clock_icon_and_heavy_digits(self):
        seg = seg_budget.limit_segment(limit(30, 9600), NOW, 100)
        self.assertEqual(plain(seg), ("5h ▮▮▮▯▯▯▯▯▯▯ 30%  ↯ ~5h26m  ◷ 𝟮𝗵𝟰𝟬𝗺", "5h 30%  ↯ ~5h26m  ◷ 𝟮𝗵𝟰𝟬𝗺"))
        self.assertEqual(seg.tone, "calm")

    def test_the_heavy_digits_count_one_column_each(self):
        self.assertEqual(theme.width(fmt.heavy("2h40m")), 5)
        self.assertEqual(fmt.heavy("<1m"), "<𝟭𝗺")

    def test_the_meter_gets_narrower_with_the_terminal(self):
        seg = seg_budget.limit_segment(limit(50, 3000), NOW, 100, "narrow")
        self.assertEqual(plain(seg)[0], "5h ▮▮▮▯▯▯ 50%  ↯ ~4h9m  ◷ 𝟱𝟬𝗺")

    def test_running_out_before_the_reset_is_solid_red(self):
        # 80% used, halfway through the 5h window: at this pace it runs out early.
        seg = seg_budget.limit_segment(limit(80, 9000), NOW, 100)
        self.assertEqual(seg.tone, "bad")
        self.assertIn("↯ ~37m", plain(seg)[0])
        self.assertIn("↯ ~37m", plain(seg)[1])

    def test_limit_after_reset_is_neutral(self):
        seg = seg_budget.limit_segment(limit(95, -2400), NOW, 100)
        self.assertEqual(seg.tone, "calm")
        self.assertEqual(plain(seg)[0], "5h reset")

    def test_early_in_the_window_the_pace_is_not_judged(self):
        seg = seg_budget.limit_segment(limit(5, FIVE - 300), NOW, 100)
        self.assertEqual(seg.tone, "calm")
        self.assertNotIn("↯", plain(seg)[0])


class Pace(Utc):
    """The pace is a time, never a second percent. It always shows after the first 10% of a window."""

    def test_room_to_spare_says_how_long_the_limit_lasts_in_the_nudge_color(self):
        # 10% used, halfway through: at this pace it lasts 22h30m, far past the reset.
        seg = seg_budget.limit_segment(limit(10, 9000), NOW, 100)
        self.assertIn("↯ ~22h30m", plain(seg)[0])
        self.assertIn("↯ ~22h30m", plain(seg)[1])
        self.assertIn(theme.paint("  ↯ ~22h30m", fg=theme.POOR, bold=True), seg.text)
        self.assertNotIn("at reset", plain(seg)[0])

    def test_good_use_is_green(self):
        # 45% used, halfway through: projected 90% at the reset.
        seg = seg_budget.limit_segment(limit(45, 9000), NOW, 100)
        self.assertIn(theme.paint("  ↯ ~3h3m", fg=theme.GOOD, bold=True), seg.text)

    def test_the_week_gets_a_pace_too(self):
        # 30% used, halfway through the week: projected 60%.
        seg = seg_budget.limit_segment(week(30, WEEK // 2), NOW, 80)
        self.assertIn("↯ ~8d4h", plain(seg)[0])
        self.assertIn(theme.paint("  ↯ ~8d4h", fg=theme.FAIR, bold=True), seg.text)

    def test_the_week_says_when_it_runs_out(self):
        seg = seg_budget.limit_segment(week(80, WEEK // 2), NOW, 80)
        self.assertIn("↯ ~21h", plain(seg)[0])
        self.assertEqual(seg.tone, "bad")

    def test_pace_colors_nudge_to_use_the_limit(self):
        for projected, color in ((10, theme.POOR), (59, theme.POOR), (60, theme.FAIR),
                                 (84, theme.FAIR), (85, theme.GOOD), (99, theme.GOOD),
                                 (100, theme.BADLY), (150, theme.BADLY)):
            self.assertEqual(seg_budget.pace_color(projected), color, projected)


class Cost(unittest.TestCase):
    def test_the_api_cost_has_its_label_and_stands_apart(self):
        seg = seg_budget.cost_segment(7.7808866)
        self.assertEqual(theme.strip(seg.text), "⛁ $7.78")
        self.assertTrue(seg.apart)

    def test_money_formats(self):
        for usd, text in ((0, "$0.00"), (0.004, "$0.00"), (7.7808866, "$7.78"), (99.99, "$99.99"),
                          (123.4, "$123"), (1234.6, "$1,235")):
            self.assertEqual(fmt.money(usd), text, usd)

    def test_no_cost_in_the_payload_gives_no_chip(self):
        self.assertIsNone(seg_budget.cost_segment(None))


class SevenDayChip(Utc):
    def test_one_square_per_day_and_the_day_and_time_of_the_reset(self):
        seg = seg_budget.limit_segment(week(8, 6 * 86400), NOW, 80)
        self.assertEqual(plain(seg), ("7d ■□□□□□□ 8%  ↯ ~11d12h  ▦ Thu 08:00", "7d 8%  ↯ ~11d12h  ▦ Thu 08:00"))

    def test_the_squares_stay_seven_on_every_width(self):
        for tier in ("wide", "normal", "narrow"):
            text = plain(seg_budget.limit_segment(week(75, 86400), NOW, 80, tier))[0]
            self.assertIn("■■■■■□□ 75%", text)

    def test_the_reset_date_is_calm_white_because_it_is_not_a_countdown(self):
        seg = seg_budget.limit_segment(week(8, 6 * 86400), NOW, 80)
        self.assertIn(theme.value("Thu 08:00"), seg.text)


class Colors(unittest.TestCase):
    def test_low_percent_is_positive_and_high_percent_is_negative(self):
        for pct, color in ((0, theme.GOOD), (49, theme.GOOD), (50, theme.FAIR), (69, theme.FAIR),
                           (70, theme.POOR), (89, theme.POOR), (90, theme.BADLY)):
            self.assertEqual(seg_budget.used_color(pct), color, pct)

    def test_long_time_to_the_reset_is_negative_and_short_time_is_positive(self):
        for share, color in ((0.0, theme.GOOD), (0.24, theme.GOOD), (0.25, theme.FAIR),
                             (0.49, theme.FAIR), (0.5, theme.POOR), (0.74, theme.POOR),
                             (0.75, theme.BADLY), (1.0, theme.BADLY)):
            self.assertEqual(seg_budget.left_color(share), color, share)

    def test_the_countdown_uses_the_negative_color_for_a_long_wait(self):
        seg = seg_budget.limit_segment(limit(5, FIVE - 2400), NOW, 100)
        self.assertIn(theme.paint("5%", fg=theme.GOOD, bold=True), seg.text)
        self.assertIn(theme.paint(fmt.heavy("4h20m"), fg=theme.BADLY, bold=True), seg.text)

    def test_the_countdown_uses_the_positive_color_for_a_short_wait(self):
        seg = seg_budget.limit_segment(limit(5, 1800), NOW, 100)
        self.assertIn(theme.paint(fmt.heavy("30m"), fg=theme.GOOD, bold=True), seg.text)

    def test_a_low_percent_stays_positive_when_the_pace_is_only_high(self):
        # 45% used, halfway through the window: projected 90%, near the limit but not over it.
        seg = seg_budget.limit_segment(limit(45, 9000), NOW, 100)
        self.assertEqual(seg.tone, "calm")
        self.assertIn(theme.paint("45%", fg=theme.GOOD, bold=True), seg.text)

    def test_amber_stays_a_colored_number(self):
        seg = seg_budget.limit_segment(limit(72, 3600), NOW, 100)
        self.assertEqual(seg.tone, "calm")
        self.assertIn(theme.paint("72%", fg=theme.POOR, bold=True), seg.text)

    def test_the_meter_shows_where_amber_and_red_start_before_you_reach_them(self):
        seg = seg_budget.limit_segment(limit(10, 9600), NOW, 100)
        self.assertIn("38;2;%d;%d;%d" % theme.dim(theme.BADLY), seg.text)


if __name__ == "__main__":
    unittest.main()
