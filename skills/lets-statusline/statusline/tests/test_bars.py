import unittest

from sl import bars, theme


def rgb_code(c):
    return "38;2;%d;%d;%d" % c


class ZoneBar(unittest.TestCase):
    def color_at(self, value):
        return theme.OK if value < 300_000 else theme.BAD

    def test_fill(self):
        self.assertEqual(theme.strip(bars.zone_bar(0, 600_000, 12, self.color_at)), "─" * 12)
        self.assertEqual(theme.strip(bars.zone_bar(300_000, 600_000, 12, self.color_at)),
                         "━" * 6 + "─" * 6)
        self.assertEqual(theme.strip(bars.zone_bar(325_000, 600_000, 12, self.color_at)),
                         "━" * 6 + "╾" + "─" * 5)
        self.assertEqual(theme.strip(bars.zone_bar(900_000, 600_000, 12, self.color_at)), "━" * 12)

    def test_empty_cells_show_the_zone_ahead(self):
        out = bars.zone_bar(0, 600_000, 12, self.color_at)
        self.assertIn(rgb_code(theme.dim(theme.OK)), out)
        self.assertIn(rgb_code(theme.dim(theme.BAD)), out)

    def test_filled_cells_are_bright(self):
        out = bars.zone_bar(600_000, 600_000, 12, self.color_at)
        self.assertIn(rgb_code(theme.OK), out)
        self.assertIn(rgb_code(theme.BAD), out)


if __name__ == "__main__":
    unittest.main()
