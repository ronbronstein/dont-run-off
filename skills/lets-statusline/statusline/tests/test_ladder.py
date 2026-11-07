import unittest

from sl import ladder, theme
from sl.payload import Context


def ctx(used, window=1_000_000):
    return Context(used_tokens=used, window=window, used_pct=round(used * 100 / window))


class Levels(unittest.TestCase):
    def test_big_window_uses_tokens(self):
        cases = {0: 0, 199_999: 0, 200_000: 1, 250_000: 2, 300_000: 3,
                 400_000: 4, 500_000: 5, 600_000: 6, 900_000: 6}
        for used, want in cases.items():
            self.assertEqual(ladder.level(used, 1_000_000), want, used)

    def test_small_window_uses_percent(self):
        cases = {99_999: 0, 100_000: 1, 120_000: 2, 140_000: 3,
                 160_000: 4, 170_000: 5, 180_000: 6}
        for used, want in cases.items():
            self.assertEqual(ladder.level(used, 200_000), want, used)

    def test_horizon(self):
        self.assertEqual(ladder.horizon(1_000_000), 600_000)
        self.assertEqual(ladder.horizon(200_000), 180_000)


class Colors(unittest.TestCase):
    def test_orange_at_20_red_at_25(self):
        self.assertEqual(ladder.color_for(199_000, 1_000_000), theme.OK)
        self.assertEqual(ladder.color_for(210_000, 1_000_000), theme.HOT)
        self.assertEqual(ladder.color_for(260_000, 1_000_000), theme.BAD)


class Banner(unittest.TestCase):
    def test_banners_say_wrap_up_and_the_tokens(self):
        for used in (420_000, 520_000, 610_000):
            text = " ".join(theme.strip(l) for l in ladder.banner_lines(ctx(used), 120)).lower()
            self.assertIn("wrap", text)
            self.assertIn(f"{used // 1000}k", text)
            self.assertNotIn("%", text)

    def test_no_banner_below_level_4(self):
        self.assertEqual(ladder.banner_lines(ctx(399_999), 120), [])

    def test_level_4_banner_grows_with_context(self):
        small = ladder.banner_lines(ctx(400_000), 120)
        big = ladder.banner_lines(ctx(450_000), 120)
        self.assertEqual(len(small), 1)
        self.assertIn("Seriously?!", theme.strip(small[0]))
        self.assertEqual(theme.width(small[0]), 80)
        self.assertEqual(theme.width(big[0]), 90)

    def test_level_5_is_capitals(self):
        lines = ladder.banner_lines(ctx(520_000), 120)
        self.assertIn("SERIOUSLY.", theme.strip(lines[0]))

    def test_level_6_is_two_full_lines(self):
        lines = ladder.banner_lines(ctx(610_000), 120)
        self.assertEqual(len(lines), 2)
        self.assertIn("STOP.", theme.strip(lines[0]))
        self.assertEqual([theme.width(l) for l in lines], [120, 120])

    def test_banner_never_narrower_than_its_text(self):
        line = ladder.banner_lines(ctx(400_000), 30)[0]
        self.assertGreaterEqual(theme.width(line), len("Seriously?!"))


if __name__ == "__main__":
    unittest.main()
