import json
import os
import unittest

from sl import seg_context, theme
from sl.payload import Cache, Context, parse

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
NOW = 1791633000


def plain(seg):
    return theme.strip(seg.text), theme.strip(seg.short) if seg.short else None


def load(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return parse(f.read())


def cache(**over):
    base = dict(warm=True, observed=True, ttl="1h", expires_at=NOW + 3192, recache_tokens=388_000,
                last_miss_at=None, last_miss_causes=())
    base.update(over)
    return Cache(**base)


def ctx(used, window=1_000_000):
    return Context(used, window, round(used * 100 / window))


class ContextChip(unittest.TestCase):
    def test_big_window_shows_tokens_not_percent(self):
        text = plain(seg_context.context(ctx(161_000), "wide"))[0]
        self.assertTrue(text.startswith("ctx "))
        self.assertTrue(text.endswith(" 161k"))
        self.assertNotIn("%", text)
        self.assertNotIn("/1M", text)

    def test_small_window_shows_the_limit_too(self):
        self.assertTrue(plain(seg_context.context(ctx(90_000, 200_000), "wide"))[0]
                        .endswith(" 90k/200k"))

    def test_level_1_is_orange_with_no_hint(self):
        seg = seg_context.context(ctx(210_000), "wide")
        self.assertEqual(seg.tone, "calm")
        self.assertNotIn("wrap", plain(seg)[0])
        self.assertIn("38;2;%d;%d;%d" % theme.HOT, seg.text)

    def test_level_2_says_wrap_soon_in_red(self):
        seg = seg_context.context(ctx(260_000), "wide")
        self.assertEqual(seg.tone, "calm")
        self.assertIn("260k · wrap soon", plain(seg)[0])
        self.assertIn("38;2;%d;%d;%d" % theme.BAD, seg.text)

    def test_level_3_is_the_seriously_pill(self):
        seg = seg_context.context(ctx(310_000), "wide")
        self.assertEqual(seg.tone, "bad")
        self.assertIn("Seriously? 310k · wrap now", plain(seg)[0])

    def test_the_bar_is_a_tank_that_fills(self):
        text = plain(seg_context.context(ctx(0), "wide"))[0]
        self.assertIn("▱" * 10, text)
        self.assertNotIn("▰", text)
        self.assertIn("▰", plain(seg_context.context(ctx(161_000), "wide"))[0])

    def test_short_form_has_no_bar(self):
        self.assertEqual(plain(seg_context.context(ctx(161_000), "wide"))[1], "ctx 161k")
        self.assertEqual(plain(seg_context.context(ctx(310_000), "wide"))[1], "Seriously? 310k")


class CacheChip(unittest.TestCase):
    def test_countdown_is_a_draining_bar_and_minutes_and_seconds(self):
        seg = seg_context.cache(cache(), NOW)
        self.assertEqual(plain(seg)[0][1:], " cache ⣿⣿⣿⣿⣿⣀ 53:12")
        self.assertEqual(seg.tone, "calm")
        self.assertIn("38;2;%d;%d;%d" % theme.OK, seg.text)

    def test_the_hourglass_turns_at_each_tick_and_keeps_its_width(self):
        a, b = (seg_context.cache(cache(expires_at=NOW + 3000), t) for t in (NOW, NOW + seg_context.TICK_S))
        self.assertNotEqual(plain(a)[0][0], plain(b)[0][0])
        self.assertEqual(theme.width(a.text), theme.width(b.text))

    def test_the_bar_drains_with_the_time_left_of_each_ttl(self):
        half_1h = plain(seg_context.cache(cache(expires_at=NOW + 1800), NOW))[0]
        half_5m = plain(seg_context.cache(cache(ttl="5m", expires_at=NOW + 150), NOW))[0]
        self.assertIn("⣿⣿⣿⣀⣀⣀ 30:00", half_1h)
        self.assertIn("⣿⣿⣿⣀⣀⣀ 2:30", half_5m)

    def test_an_unknown_ttl_has_no_bar(self):
        self.assertNotIn("⣀", plain(seg_context.cache(cache(ttl=None), NOW))[0])

    def test_near_expiry_with_a_big_context_is_solid_amber_and_names_the_cost(self):
        seg = seg_context.cache(cache(expires_at=NOW + 252), NOW)
        self.assertEqual(seg.tone, "warn")
        self.assertEqual([p[1:] for p in plain(seg)], [" cache ⣀⣀⣀⣀⣀⣀ 4:12 → re-reads 388k", " 4:12"])

    def test_near_expiry_with_a_small_context_stays_calm(self):
        seg = seg_context.cache(cache(expires_at=NOW + 252, recache_tokens=20_000), NOW)
        self.assertEqual(seg.tone, "calm")
        self.assertEqual(plain(seg)[0][1:], " cache ⣀⣀⣀⣀⣀⣀ 4:12")
        self.assertIn("38;2;%d;%d;%d" % theme.WARN, seg.text)

    def test_a_5_minute_cache_warns_in_its_last_minute_only(self):
        self.assertEqual(seg_context.cache(cache(ttl="5m", expires_at=NOW + 90), NOW).tone, "calm")
        self.assertEqual(seg_context.cache(cache(ttl="5m", expires_at=NOW + 50), NOW).tone, "warn")

    def test_cold_with_a_big_context_names_the_cost(self):
        seg = seg_context.cache(cache(warm=False, expires_at=None), NOW)
        self.assertEqual(seg.tone, "warn")
        self.assertEqual(plain(seg), ("⌛ cache cold · next reply re-reads 388k", "⌛ cache cold"))

    def test_cold_with_a_small_context_is_calm(self):
        seg = seg_context.cache(cache(warm=False, expires_at=None, recache_tokens=20_000), NOW)
        self.assertEqual(seg.tone, "calm")
        self.assertEqual(plain(seg)[0], "⌛ cache cold · next reply re-reads 20k")

    def test_warm_flag_past_expiry_is_cold(self):
        self.assertIn("cold", plain(seg_context.cache(cache(expires_at=NOW - 5), NOW))[0])

    def test_recent_miss_names_the_reason(self):
        seg = seg_context.cache(cache(last_miss_at=NOW - 60, last_miss_causes=("ttl_expired_1h",)), NOW)
        self.assertTrue(plain(seg)[0].endswith(" 53:12 · miss: idle >1h"))

    def test_old_miss_is_gone(self):
        seg = seg_context.cache(cache(last_miss_at=NOW - 700, last_miss_causes=("ttl_expired_1h",)), NOW)
        self.assertNotIn("miss", plain(seg)[0])

    def test_no_chip_when_caching_is_not_observed(self):
        self.assertIsNone(seg_context.cache(cache(observed=False), NOW))

    def test_warm_with_no_expiry(self):
        self.assertEqual(plain(seg_context.cache(cache(expires_at=None), NOW))[0], "cache warm")

    def test_reason_words(self):
        cases = {("ttl_expired_5m",): "idle >5m", ("messages_rewritten",): "history changed",
                 ("tools_changed",): "tools changed", ("model_changed",): "model changed",
                 ("something_new",): "something new",
                 ("ttl_expired_1h", "tools_changed"): "idle >1h, tools changed"}
        for causes, words in cases.items():
            self.assertEqual(seg_context.miss_reason(causes), words)

    def test_real_miss_fixture(self):
        s = load("payload_cache_miss.json")
        seg = seg_context.cache(s.cache, s.cache.last_miss_at + 30)
        self.assertIn("miss: idle >1h", plain(seg)[0])


class Build(unittest.TestCase):
    def test_order(self):
        s = load("payload_real.json")
        texts = [plain(x)[0] for x in seg_context.build(s, NOW, "wide")]
        self.assertTrue(texts[0].startswith("ctx "))
        self.assertIn(texts[1][0], "⏳⌛")
        self.assertEqual(len(texts), 2)

    def test_empty(self):
        self.assertEqual(seg_context.build(parse(json.dumps({})), NOW, "wide"), [])


if __name__ == "__main__":
    unittest.main()
