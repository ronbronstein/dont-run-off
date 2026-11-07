import json
import os
import shutil
import subprocess
import tempfile
import unittest

from sl import prstate
from sl.payload import parse
from tests.test_seg_place import state

NOW = 1_800_000_000

# Cut down from a real `gh pr view` answer (a public PR).
MERGED = {"closedAt": "2026-09-27T08:12:16Z", "isDraft": False, "mergeable": "UNKNOWN",
          "mergedAt": "2026-09-27T08:12:16Z", "number": 5, "reviewDecision": "", "state": "MERGED",
          "statusCheckRollup": [{"__typename": "CheckRun", "conclusion": "SUCCESS",
                                 "status": "COMPLETED", "name": "validate"}],
          "url": "https://github.com/o/r/pull/5"}


def run_json(data):
    def run(args, **kw):
        return subprocess.CompletedProcess(args, 0, json.dumps(data), "")
    return run


def session(**extra):
    d = dict(cwd="/x", workspace={"repo": {"host": "github.com", "owner": "o", "name": "r"}})
    d.update(extra)
    return parse(json.dumps(d))


def feature(**over):
    return state(branch="feat/x", upstream="origin/feat/x", **over)


class ParseView(unittest.TestCase):
    def test_real_merged_answer(self):
        f = prstate.parse_view(MERGED)
        self.assertEqual((f.number, f.state, f.draft, f.review), (5, "MERGED", False, None))
        self.assertEqual((f.failed, f.pending, f.passed), (0, 0, 1))
        self.assertEqual(f.url, "https://github.com/o/r/pull/5")
        self.assertIsNotNone(f.ended_at)

    def test_closed_uses_closed_at(self):
        f = prstate.parse_view(dict(MERGED, state="CLOSED", mergedAt=None))
        self.assertEqual(f.state, "CLOSED")
        self.assertIsNotNone(f.ended_at)

    def test_conflicting(self):
        self.assertTrue(prstate.parse_view(dict(MERGED, mergeable="CONFLICTING")).conflicting)

    def test_check_counts(self):
        rollup = [
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "NEUTRAL"},
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SKIPPED"},
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"},
            {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "TIMED_OUT"},
            {"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": ""},
            {"__typename": "StatusContext", "state": "SUCCESS"},
            {"__typename": "StatusContext", "state": "PENDING"},
            {"__typename": "StatusContext", "state": "ERROR"},
        ]
        f = prstate.parse_view(dict(MERGED, statusCheckRollup=rollup))
        self.assertEqual((f.failed, f.pending, f.passed), (3, 2, 4))

    def test_bad_answer_raises_with_context(self):
        with self.assertRaises(prstate.PrError):
            prstate.parse_view({"state": "OPEN"})
        with self.assertRaises(prstate.PrError):
            prstate.parse_view({"number": 1, "state": "WEIRD"})


class Fetch(unittest.TestCase):
    def test_ok(self):
        out = prstate.fetch("o/r", "feat/x", run=run_json(MERGED))
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["pr"]["number"], 5)

    def test_asks_gh_for_the_branch_in_the_repo(self):
        seen = {}

        def run(args, **kw):
            seen["args"] = args
            return subprocess.CompletedProcess(args, 0, json.dumps(MERGED), "")
        prstate.fetch("o/r", "feat/x", run=run)
        self.assertEqual(seen["args"][:6], ["gh", "pr", "view", "feat/x", "-R", "o/r"])

    def test_no_pr_is_a_normal_answer(self):
        def run(args, **kw):
            return subprocess.CompletedProcess(args, 1, "", 'no pull requests found for branch "x"')
        self.assertEqual(prstate.fetch("o/r", "x", run=run), {"status": "none"})

    def test_other_failure_raises(self):
        def run(args, **kw):
            return subprocess.CompletedProcess(args, 1, "", "HTTP 502")
        with self.assertRaises(prstate.PrError) as e:
            prstate.fetch("o/r", "x", run=run)
        self.assertIn("HTTP 502", str(e.exception))

    def test_gh_missing_is_a_normal_answer(self):
        def run(args, **kw):
            raise FileNotFoundError("gh")
        self.assertEqual(prstate.fetch("o/r", "x", run=run), {"status": "no-gh"})

    def test_gh_missing_shows_no_pr_chip_and_asks_rarely(self):
        self.assertIsNone(prstate._merge(None, {"status": "no-gh", "ts": NOW}))
        self.assertEqual(prstate.ttl({"status": "no-gh"}), 3600)

    def test_timeout_raises(self):
        def run(args, **kw):
            raise subprocess.TimeoutExpired(args, 15)
        with self.assertRaises(prstate.PrError):
            prstate.fetch("o/r", "x", run=run)

    def test_not_json_raises(self):
        def run(args, **kw):
            return subprocess.CompletedProcess(args, 0, "oops", "")
        with self.assertRaises(prstate.PrError):
            prstate.fetch("o/r", "x", run=run)


class Ttl(unittest.TestCase):
    def test_values(self):
        cases = [({"status": "none"}, 120), ({"status": "error"}, 300),
                 ({"status": "ok", "pr": {"state": "MERGED"}}, 1800),
                 ({"status": "ok", "pr": {"state": "CLOSED"}}, 1800),
                 ({"status": "ok", "pr": {"state": "OPEN", "pending": 0}}, 60),
                 ({"status": "ok", "pr": {"state": "OPEN", "pending": 2}}, 30)]
        for entry, want in cases:
            self.assertEqual(prstate.ttl(entry), want, entry)


class Get(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.log = os.path.join(self.d, "errors.log")
        self.spawned = []

    def tearDown(self):
        shutil.rmtree(self.d)

    def spawn(self, job, lock):
        self.spawned.append(job)
        return True

    def get(self, s, g, now=NOW, run=None):
        return prstate.get(s, g, self.d, now, self.log, spawn=self.spawn,
                           run=run or run_json(MERGED))

    def seed(self, entry, age=0):
        prstate.save(prstate.cache_path(self.d, "o/r", "feat/x"), dict(entry, ts=NOW - age))

    def test_no_lookup_on_the_base_branch(self):
        self.assertIsNone(self.get(session(), state()))
        self.assertEqual(self.spawned, [])

    def test_no_lookup_on_a_detached_head(self):
        self.get(session(), state(branch=None))
        self.assertEqual(self.spawned, [])

    def test_no_lookup_with_no_upstream(self):
        self.get(session(), state(branch="feat/x", upstream=None))
        self.assertEqual(self.spawned, [])

    def test_no_lookup_for_a_branch_that_gh_reads_as_something_else(self):
        for branch in ("--web", "-R", "42", "https://github.com/o/r/pull/1"):
            self.assertFalse(prstate._eligible(session(), state(branch=branch, upstream="origin/x")), branch)

    def test_no_lookup_for_a_repo_name_that_is_not_one_segment(self):
        for owner, name in (("-x", "r"), ("o", "--web"), ("evil.example", "o/r"), ("o/r", "x"), ("o", "r\n"), ("o", "")):
            s = parse(json.dumps({"cwd": "/x", "workspace": {"repo": {"host": "github.com", "owner": owner, "name": name}}}))
            self.assertFalse(prstate._eligible(s, state(branch="feat/x", upstream="origin/feat/x")), (owner, name))

    def test_a_normal_branch_and_repo_can_ask(self):
        s = parse(json.dumps({"cwd": "/x", "workspace": {"repo": {"host": "github.com", "owner": "my-org", "name": "my.repo_1"}}}))
        self.assertTrue(prstate._eligible(s, state(branch="feat/x-1", upstream="origin/feat/x-1")))

    def test_no_lookup_off_github(self):
        s = session(workspace={"repo": {"host": "gitlab.com", "owner": "o", "name": "r"}})
        self.assertIsNone(self.get(s, feature()))
        self.assertEqual(self.spawned, [])

    def test_no_lookup_when_the_payload_has_no_repo(self):
        self.get(parse(json.dumps({"cwd": "/x"})), feature())
        self.assertEqual(self.spawned, [])

    def test_gitlab_payload_still_shows(self):
        s = session(workspace={"repo": {"host": "gitlab.com", "owner": "o", "name": "r"}},
                    pr={"number": 9, "kind": "mr", "review_state": "pending"})
        view = self.get(s, feature())
        self.assertEqual((view.facts.number, view.facts.kind), (9, "mr"))

    def test_first_run_starts_a_refresh_and_returns_at_once(self):
        self.assertIsNone(self.get(session(), feature()))
        self.assertEqual(len(self.spawned), 1)

    def test_the_refresh_job_writes_the_cache(self):
        self.get(session(), feature())
        self.spawned[0]()
        view = self.get(session(), feature())
        self.assertEqual(view.facts.state, "MERGED")

    def test_fresh_cache_starts_no_refresh(self):
        self.seed({"status": "none"})
        view = self.get(session(), feature())
        self.assertEqual(view.kind, "none")
        self.assertEqual(self.spawned, [])

    def test_stale_cache_shows_and_refreshes(self):
        self.seed({"status": "none"}, age=500)
        self.assertEqual(self.get(session(), feature()).kind, "none")
        self.assertEqual(len(self.spawned), 1)

    def test_payload_wins_over_an_old_merged_answer(self):
        self.seed({"status": "ok", "pr": prstate.to_dict(prstate.parse_view(MERGED))})
        view = self.get(session(pr={"number": 7, "review_state": "draft"}), feature())
        self.assertEqual((view.facts.number, view.facts.state, view.facts.draft), (7, "OPEN", True))

    def test_payload_review_with_cached_checks_of_the_same_pr(self):
        open_pr = dict(MERGED, state="OPEN", mergedAt=None, closedAt=None, number=7,
                       mergeable="CONFLICTING", statusCheckRollup=[
                           {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"}])
        self.seed({"status": "ok", "pr": prstate.to_dict(prstate.parse_view(open_pr))})
        view = self.get(session(pr={"number": 7, "review_state": "approved"}), feature())
        f = view.facts
        self.assertEqual((f.review, f.failed, f.conflicting), ("APPROVED", 1, True))

    def test_failed_lookup_is_logged_and_keeps_the_old_answer(self):
        self.seed({"status": "ok", "pr": prstate.to_dict(prstate.parse_view(MERGED))}, age=5000)

        def broken(args, **kw):
            return subprocess.CompletedProcess(args, 1, "", "HTTP 502")
        self.get(session(), feature(), run=broken)
        self.spawned[0]()
        view = self.get(session(), feature())
        self.assertEqual(view.facts.state, "MERGED")
        with open(self.log) as f:
            self.assertIn("HTTP 502", f.read())

    def test_failed_lookup_with_no_old_answer_is_unknown(self):
        def broken(args, **kw):
            return subprocess.CompletedProcess(args, 1, "", "HTTP 502")
        self.get(session(), feature(), run=broken)
        self.spawned[0]()
        self.assertEqual(self.get(session(), feature()).kind, "unknown")

    def test_a_broken_cache_file_counts_as_no_cache(self):
        with open(prstate.cache_path(self.d, "o/r", "feat/x"), "w") as f:
            f.write("{nope")
        self.assertIsNone(self.get(session(), feature()))
        self.assertEqual(len(self.spawned), 1)


if __name__ == "__main__":
    unittest.main()
