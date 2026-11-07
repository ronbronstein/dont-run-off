import os
import shutil
import tempfile
import unittest

from sl import gitcache, gitstate
from tests.test_seg_place import state

NOW = 1_800_000_000


class Get(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.calls = 0
        self.spawned = []
        self.log = os.path.join(self.d, "errors.log")

    def tearDown(self):
        shutil.rmtree(self.d)

    def collect(self, cwd, timeout=None):
        self.calls += 1
        return state()

    def slow(self, cwd, timeout=None):
        self.calls += 1
        raise gitstate.GitTimeout("git status timed out")

    def spawn(self, job, lock):
        self.spawned.append(job)
        return True

    def get(self, collect=None, now=NOW):
        return gitcache.get("/repo", self.d, now, self.log, collect=collect or self.collect,
                            spawn=self.spawn)

    def test_first_read_runs_git(self):
        view = self.get()
        self.assertEqual((view.state.branch, view.age, view.pending), ("main", 0, False))
        self.assertEqual(self.calls, 1)

    def test_a_fresh_snapshot_runs_no_git(self):
        self.get()
        view = self.get(now=NOW + 2)
        self.assertEqual(self.calls, 1)
        self.assertEqual(view.state.branch, "main")

    def test_an_old_snapshot_runs_git_again(self):
        self.get()
        self.get(now=NOW + gitcache.FRESH_S + 1)
        self.assertEqual(self.calls, 2)

    def test_a_timeout_shows_the_last_good_state_and_refreshes_in_the_background(self):
        self.get()
        view = self.get(collect=self.slow, now=NOW + 100)
        self.assertEqual(view.state.branch, "main")
        self.assertAlmostEqual(view.age, 100, delta=0.5)
        self.assertEqual(len(self.spawned), 1)

    def test_a_timeout_writes_no_error(self):
        self.get(collect=self.slow)
        self.assertFalse(os.path.exists(self.log))

    def test_a_timeout_with_no_snapshot_is_pending(self):
        view = self.get(collect=self.slow)
        self.assertIsNone(view.state)
        self.assertTrue(view.pending)

    def test_the_background_job_saves_a_snapshot(self):
        calls = []

        def patient(cwd, timeout=None):
            calls.append(timeout)
            return state(branch="feat/x")
        job = gitcache.refresh_job("/repo", self.d, NOW, self.log, patient)
        job()
        self.assertEqual(calls, [gitcache.BACKGROUND_TIMEOUT_S])
        self.assertEqual(self.get(now=NOW + 1).state.branch, "feat/x")

    def test_a_failed_background_job_logs_its_error(self):
        def broken(cwd, timeout=None):
            raise gitstate.GitError("git status failed in /repo")
        gitcache.refresh_job("/repo", self.d, NOW, self.log, broken)()
        with open(self.log) as f:
            self.assertIn("git status failed", f.read())

    def test_a_slow_repo_is_read_less_often(self):
        self.assertEqual(gitcache.fresh_for(0.02), gitcache.FRESH_S)
        self.assertEqual(gitcache.fresh_for(2.0), 10.0)

    def test_not_a_repo_is_remembered_too(self):
        def none(cwd, timeout=None):
            self.calls += 1
            return None
        self.assertIsNone(self.get(collect=none).state)
        self.assertIsNone(self.get(collect=none, now=NOW + 1).state)
        self.assertEqual(self.calls, 1)

    def test_a_snapshot_from_an_older_version_counts_as_no_snapshot(self):
        with open(gitcache.cache_path(self.d, "/repo"), "w") as f:
            f.write('{"ts": %d, "took": 0.01, "state": {"branch": "old"}}' % NOW)
        self.assertEqual(self.get().state.branch, "main")
        self.assertEqual(self.calls, 1)

    def test_a_broken_snapshot_counts_as_no_snapshot(self):
        with open(gitcache.cache_path(self.d, "/repo"), "w") as f:
            f.write("{nope")
        self.assertEqual(self.get().state.branch, "main")


if __name__ == "__main__":
    unittest.main()
