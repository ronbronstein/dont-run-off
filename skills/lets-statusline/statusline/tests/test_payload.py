import json
import os
import unittest

from sl.payload import PayloadError, parse

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name="payload_real.json"):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()


class ParseRealPayload(unittest.TestCase):
    def setUp(self):
        self.s = parse(load_fixture())

    def test_identity_fields(self):
        self.assertEqual(self.s.model_name, "Opus 5.5")
        self.assertEqual(self.s.model_id, "claude-opus-5-5")
        self.assertEqual(self.s.effort, "xhigh")
        self.assertEqual(self.s.session_name, "demo site rebuild")
        self.assertEqual(self.s.cwd, "/fake-home/Code/demo-theme/_migration")
        self.assertEqual(self.s.project_dir, "/fake-home/Code/demo-theme")
        self.assertTrue(self.s.thinking)
        self.assertFalse(self.s.fast_mode)
        self.assertEqual(self.s.output_style, "default")

    def test_context(self):
        ctx = self.s.context
        self.assertEqual(ctx.used_tokens, 208191)
        self.assertEqual(ctx.window, 1_000_000)
        self.assertEqual(ctx.used_pct, 21)

    def test_session_age(self):
        self.assertEqual(self.s.duration_s, 1187)

    def test_cache(self):
        c = self.s.cache
        self.assertTrue(c.warm)
        self.assertEqual(c.ttl, "1h")
        self.assertEqual(c.expires_at, 1791636250)
        self.assertTrue(c.observed)
        self.assertIsNone(c.last_miss_at)
        self.assertEqual(c.recache_tokens, 208191)
        self.assertEqual(c.last_miss_causes, ())

    def test_cost(self):
        self.assertAlmostEqual(self.s.cost_usd, 7.7808866)

    def test_limits(self):
        labels = [(l.label, l.used_pct, l.resets_at, l.window_s) for l in self.s.limits]
        self.assertEqual(labels, [
            ("5h", 26, 1791642600, 5 * 3600),
            ("7d", 8, 1792220400, 7 * 86400),
        ])

    def test_absent_optional_blocks(self):
        self.assertIsNone(self.s.pr)
        self.assertIsNone(self.s.agent_name)


class ParseEdgeCases(unittest.TestCase):
    def test_rejects_non_object(self):
        with self.assertRaises(PayloadError):
            parse("[]")

    def test_rejects_bad_json(self):
        with self.assertRaises(PayloadError):
            parse("{not json")

    def test_empty_object_is_safe(self):
        s = parse("{}")
        self.assertIsNone(s.context)
        self.assertEqual(s.limits, ())
        self.assertEqual(s.cwd, "")

    def test_context_derives_tokens_from_percent(self):
        s = parse(json.dumps({"context_window": {"used_percentage": 30, "context_window_size": 200000}}))
        self.assertEqual(s.context.used_tokens, 60000)

    def test_context_guesses_window_from_model_id(self):
        s = parse(json.dumps({"model": {"id": "claude-x[1m]"},
                              "context_window": {"total_input_tokens": 1000}}))
        self.assertEqual(s.context.window, 1_000_000)

    def test_null_percentage_early_in_session(self):
        s = parse(json.dumps({"context_window": {"used_percentage": None, "total_input_tokens": 0,
                                                 "context_window_size": 1000000}}))
        self.assertEqual(s.context.used_tokens, 0)
        self.assertEqual(s.context.used_pct, 0)

    def test_wrong_types_are_ignored(self):
        s = parse(json.dumps({"model": {"display_name": 5}, "fast_mode": "yes",
                              "rate_limits": {"five_hour": {"used_percentage": "lots"}}}))
        self.assertIsNone(s.model_name)
        self.assertFalse(s.fast_mode)
        self.assertEqual(s.limits, ())

    def test_pr_and_worktree(self):
        s = parse(json.dumps({
            "pr": {"number": 42, "url": "https://x/pull/42", "review_state": "changes_requested"},
            "workspace": {"repo": {"host": "github.com", "name": "demo", "owner": "someone"}},
        }))
        self.assertEqual(s.pr.number, 42)
        self.assertEqual(s.pr.review_state, "changes_requested")
        self.assertIsNone(s.pr.kind)
        self.assertEqual(s.repo.slug, "someone/demo")
        self.assertEqual(s.repo.host, "github.com")

    def test_partial_repo_is_ignored(self):
        s = parse(json.dumps({"workspace": {"repo": {"name": "demo"}}}))
        self.assertIsNone(s.repo)

    def test_real_worktree_payload(self):
        s = parse(load_fixture("payload_worktree.json"))
        self.assertEqual(s.repo.slug, "someone/some-repo")
        self.assertEqual(s.cache.last_miss_causes, ("ttl_expired_1h",))
        self.assertFalse(s.cache.warm)

    def test_cache_miss_causes(self):
        s = parse(json.dumps({"prompt_cache": {
            "warm": False, "last_miss_at": 123, "last_miss_cause": {"causes": ["tools_changed", "ttl"]}}}))
        self.assertFalse(s.cache.warm)
        self.assertEqual(s.cache.last_miss_at, 123)
        self.assertEqual(s.cache.last_miss_causes, ("tools_changed", "ttl"))


if __name__ == "__main__":
    unittest.main()
