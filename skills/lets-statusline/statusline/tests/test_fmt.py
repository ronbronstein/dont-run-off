import unittest

from sl import fmt


class Tokens(unittest.TestCase):
    def test_values(self):
        cases = {0: "0", 999: "999", 1000: "1k", 167851: "168k", 999_499: "999k",
                 1_000_000: "1M", 1_500_000: "1.5M", 200_000: "200k"}
        for n, want in cases.items():
            self.assertEqual(fmt.tokens(n), want, n)


class Duration(unittest.TestCase):
    def test_values(self):
        cases = {-5: "0m", 0: "0m", 59: "<1m", 60: "1m", 3599: "59m", 3600: "1h",
                 6420: "1h47m", 86400: "1d", 4 * 86400 + 3 * 3600 + 59: "4d3h"}
        for s, want in cases.items():
            self.assertEqual(fmt.duration(s), want, s)


class Age(unittest.TestCase):
    def test_values(self):
        self.assertEqual(fmt.age(30), "just now")
        self.assertEqual(fmt.age(720), "12m ago")
        self.assertEqual(fmt.age(3 * 3600), "3h ago")
        self.assertEqual(fmt.age(5 * 86400), "5d ago")


class Clock(unittest.TestCase):
    def test_values(self):
        cases = {-5: "0:00", 0: "0:00", 9: "0:09", 252: "4:12", 3192: "53:12", 3600: "60:00"}
        for s, want in cases.items():
            self.assertEqual(fmt.clock(s), want, s)


class Truncate(unittest.TestCase):
    def test_short_text_unchanged(self):
        self.assertEqual(fmt.truncate("abc", 5), "abc")

    def test_long_text_gets_ellipsis(self):
        self.assertEqual(fmt.truncate("abcdefgh", 5), "abcd…")

    def test_zero_width(self):
        self.assertEqual(fmt.truncate("abc", 0), "")


if __name__ == "__main__":
    unittest.main()
