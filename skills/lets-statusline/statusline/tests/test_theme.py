import unittest

from sl import theme


class Paint(unittest.TestCase):
    def test_plain_text_has_no_codes(self):
        self.assertEqual(theme.paint("x"), "x")

    def test_color_and_reset(self):
        out = theme.paint("x", fg=(1, 2, 3), bold=True)
        self.assertTrue(out.startswith("\x1b["))
        self.assertIn("38;2;1;2;3", out)
        self.assertIn("1", out.split("m")[0])
        self.assertTrue(out.endswith("x\x1b[0m"))

    def test_background(self):
        self.assertIn("48;2;9;8;7", theme.paint("x", bg=(9, 8, 7)))


class Width(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(theme.strip(theme.paint("héllo", fg=(1, 1, 1))), "héllo")

    def test_ascii(self):
        self.assertEqual(theme.width(theme.paint("hello", fg=(1, 1, 1), bold=True)), 5)

    def test_box_drawing_is_single(self):
        self.assertEqual(theme.width("━━─╾▌│↻⎇"), 8)

    def test_emoji_is_double(self):
        self.assertEqual(theme.width("🚨x"), 3)


class TextColors(unittest.TestCase):
    def test_labels_are_white_not_gray(self):
        self.assertTrue(all(c >= 200 for c in theme.LABEL), theme.LABEL)

    def test_values_are_white_and_bold(self):
        out = theme.value("42")
        self.assertIn("38;2;%d;%d;%d" % theme.TEXT, out)
        self.assertTrue(out.startswith("\x1b[1;"))

    def test_inner_dot_is_light_gray(self):
        self.assertTrue(all(150 <= c < 200 for c in theme.MUTED), theme.MUTED)


class Chip(unittest.TestCase):
    def test_calm_keeps_inner_colors_with_no_background(self):
        inner = theme.paint("a", fg=theme.OK) + theme.paint("b", fg=theme.BAD)
        out = theme.chip(inner)
        self.assertEqual(theme.strip(out), " ab ")
        self.assertNotIn("\x1b[48;", out)
        self.assertIn("38;2;%d;%d;%d" % theme.OK, out)

    def test_solid_tones_flatten_the_inner_colors(self):
        inner = theme.paint("a", fg=theme.OK)
        for tone, bg in (("warn", theme.WARN), ("bad", theme.ALARM_BG)):
            out = theme.chip(inner, tone)
            self.assertEqual(theme.strip(out), " a ")
            self.assertIn("48;2;%d;%d;%d" % bg, out)
            self.assertNotIn("38;2;%d;%d;%d" % theme.OK, out)

    def test_ink_on_amber_is_readable(self):
        self.assertTrue(all(c < 60 for c in theme.INK))


class Link(unittest.TestCase):
    def test_link_has_no_width(self):
        out = theme.link("PR #1", "https://x/1")
        self.assertEqual(theme.width(out), 5)
        self.assertIn("https://x/1", out)

    def test_no_url(self):
        self.assertEqual(theme.link("PR #1", None), "PR #1")

    def test_link_refuses_anything_but_a_clean_https_url(self):
        for url in ("http://x/1", "file:///etc/passwd", "https://x/1\x07\x1b[31mgotcha",
                    "https://x/1\x1b]8;;https://evil", "https://x/1 y", "https://x/1\x9c"):
            self.assertEqual(theme.link("PR #1", url), "PR #1")


class Mix(unittest.TestCase):
    def test_mix_endpoints(self):
        self.assertEqual(theme.mix((200, 100, 0), (0, 0, 0), 1.0), (200, 100, 0))
        self.assertEqual(theme.mix((200, 100, 0), (0, 0, 0), 0.0), (0, 0, 0))
        self.assertEqual(theme.mix((200, 100, 0), (0, 0, 0), 0.5), (100, 50, 0))


if __name__ == "__main__":
    unittest.main()
