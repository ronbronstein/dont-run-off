import unittest

from sl import layout, theme
from sl.layout import Segment


def plain(s):
    return theme.strip(s)


def bg_code(c):
    return "48;2;%d;%d;%d" % c


class Fit(unittest.TestCase):
    """Each chip is its text + 2 columns of padding. One separator column between chips."""

    def setUp(self):
        self.segs = (
            Segment("AAAAAAAAAA", priority=100, short="AA"),
            Segment("BBBBBBBBBB", priority=50, short="BB"),
            Segment("CCCCCCCCCC", priority=10, short="CC"),
        )

    def texts(self, segs):
        return [plain(s.text) for s in segs]

    def test_everything_fits(self):
        self.assertEqual(self.texts(layout.fit(self.segs, 100)), ["A" * 10, "B" * 10, "C" * 10])

    def test_shortens_lowest_priority_first(self):
        # 12 + 12 + 12 + 2 separators = 38. Budget 26 forces two short forms: 12 + 4 + 4 + 2 = 22.
        self.assertEqual(self.texts(layout.fit(self.segs, 26)), ["A" * 10, "BB", "CC"])

    def test_shortens_only_as_much_as_needed(self):
        self.assertEqual(self.texts(layout.fit(self.segs, 30)), ["A" * 10, "B" * 10, "CC"])

    def test_restores_full_text_after_a_drop_frees_space(self):
        segs = (Segment("A" * 10, priority=100, short="A"), Segment("Z" * 40, priority=1))
        self.assertEqual(self.texts(layout.fit(segs, 14)), ["A" * 10])

    def test_drops_lowest_priority_when_short_is_not_enough(self):
        self.assertEqual(self.texts(layout.fit(self.segs, 9)), ["AA", "BB"])

    def test_keeps_the_top_segment_even_if_too_wide(self):
        self.assertEqual(self.texts(layout.fit(self.segs, 1)), ["AA"])

    def test_order_is_preserved(self):
        segs = (Segment("low", priority=1), Segment("high", priority=99))
        self.assertEqual(self.texts(layout.fit(segs, 100)), ["low", "high"])

    def test_input_is_not_mutated(self):
        before = tuple(self.segs)
        layout.fit(self.segs, 8)
        self.assertEqual(self.segs, before)


class Line(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(layout.line((), 80), "")

    def test_chips_are_separated_by_a_thin_line(self):
        out = layout.line((Segment("a"), Segment("b")), 80)
        self.assertEqual(plain(out), " a │ b ")

    def test_the_separator_sits_on_the_same_background_as_the_chips(self):
        out = layout.line((Segment("a"), Segment("b")), 80)
        self.assertIn(theme.paint("│", fg=theme.SEPARATOR, bg=theme.CHIP_BG), out)

    def test_a_chip_apart_gets_a_heavy_wide_separator(self):
        out = layout.line((Segment("a"), Segment("b", apart=True)), 80)
        self.assertEqual(plain(out), " a  ┃  b ")
        self.assertEqual(theme.width(out), 9)

    def test_fit_counts_the_wide_separator(self):
        segs = (Segment("a" * 10, priority=90), Segment("b" * 10, priority=10, apart=True))
        # 12 + 12 for the chips, 3 for " ┃ "
        self.assertEqual(len(layout.fit(segs, 26)), 1)
        self.assertEqual(len(layout.fit(segs, 27)), 2)

    def test_calm_chip_has_the_slate_background(self):
        self.assertIn(bg_code(theme.CHIP_BG), layout.line((Segment("a"),), 80))

    def test_warn_chip_is_solid_amber(self):
        self.assertIn(bg_code(theme.WARN), layout.line((Segment("a", tone="warn"),), 80))

    def test_bad_chip_is_solid_red(self):
        self.assertIn(bg_code(theme.ALARM_BG), layout.line((Segment("a", tone="bad"),), 80))

    def test_a_short_form_keeps_the_tone(self):
        segs = (Segment("A" * 30, short="A", tone="bad"),)
        self.assertIn(bg_code(theme.ALARM_BG), layout.line(segs, 10))

    def test_line_fits_budget(self):
        segs = tuple(Segment("x" * 20, priority=p) for p in (90, 50, 10))
        self.assertLessEqual(theme.width(layout.line(segs, 50)), 50)


class Block(unittest.TestCase):
    def test_rows_get_the_same_width_on_the_same_background(self):
        rows = layout.block([layout.line((Segment("a"),), 80), layout.line((Segment("long text"),), 80)])
        self.assertEqual(theme.width(rows[0]), theme.width(rows[1]))
        self.assertTrue(rows[0].endswith(theme.chip_fill(8)))

    def test_the_widest_row_does_not_change(self):
        row = layout.line((Segment("long text"),), 80)
        self.assertEqual(layout.block([row])[0], row)

    def test_an_empty_row_stays_empty(self):
        self.assertEqual(layout.block(["", layout.line((Segment("a"),), 80)])[0], "")


class Compose(unittest.TestCase):
    def test_skips_empty_lines(self):
        self.assertEqual(layout.compose(["a", "", "b"]), "a\nb")


if __name__ == "__main__":
    unittest.main()
