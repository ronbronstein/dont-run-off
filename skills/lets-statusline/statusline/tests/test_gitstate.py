import os
import shutil
import subprocess
import tempfile
import unittest

from sl import gitstate

STATUS = """\
# branch.oid 6b56a0ae0cda948cd5d05667f4c7359558ffbac3
# branch.head main
# branch.upstream origin/main
# branch.ab +3 -1
# stash 2
1 M. N... 100644 100644 100644 aaa bbb staged.txt
1 .M N... 100644 100644 100644 aaa bbb modified.txt
1 MM N... 100644 100644 100644 aaa bbb both.txt
2 R. N... 100644 100644 100644 aaa bbb R100 new.txt\told.txt
u UU N... 100644 100644 100644 100644 aaa bbb ccc conflict.txt
? untracked-1.txt
? untracked-2.txt
"""

ENV = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@t")


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, env=ENV,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write(path, text="x\n"):
    with open(path, "w") as f:
        f.write(text)


class ParseStatus(unittest.TestCase):
    def test_counts(self):
        s = gitstate.parse_status(STATUS)
        self.assertEqual(s["branch"], "main")
        self.assertEqual(s["oid"], "6b56a0a")
        self.assertEqual(s["upstream"], "origin/main")
        self.assertEqual((s["ahead"], s["behind"]), (3, 1))
        self.assertEqual(s["stash"], 2)
        self.assertEqual(s["staged"], 3)      # M., MM, R.
        self.assertEqual(s["modified"], 2)    # .M, MM
        self.assertEqual(s["conflicts"], 1)
        self.assertEqual(s["untracked"], 2)

    def test_detached_and_initial(self):
        s = gitstate.parse_status("# branch.oid (initial)\n# branch.head (detached)\n")
        self.assertIsNone(s["branch"])
        self.assertIsNone(s["oid"])
        self.assertIsNone(s["upstream"])


class Operation(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_none(self):
        self.assertIsNone(gitstate.operation(self.d))

    def test_rebase_progress(self):
        os.mkdir(os.path.join(self.d, "rebase-merge"))
        write(os.path.join(self.d, "rebase-merge", "msgnum"), "2\n")
        write(os.path.join(self.d, "rebase-merge", "end"), "5\n")
        self.assertEqual(gitstate.operation(self.d), "rebase 2/5")

    def test_merge(self):
        write(os.path.join(self.d, "MERGE_HEAD"))
        self.assertEqual(gitstate.operation(self.d), "merge")

    def test_cherry_pick(self):
        write(os.path.join(self.d, "CHERRY_PICK_HEAD"))
        self.assertEqual(gitstate.operation(self.d), "cherry-pick")


class HasRemote(unittest.TestCase):
    def test_reads_config(self):
        d = tempfile.mkdtemp()
        try:
            write(os.path.join(d, "config"), '[core]\n\tbare = false\n')
            self.assertFalse(gitstate.has_remote(d))
            write(os.path.join(d, "config"), '[core]\n[remote "origin"]\n\turl = x\n')
            self.assertTrue(gitstate.has_remote(d))
        finally:
            shutil.rmtree(d)


class BaseBranch(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_origin_head_wins(self):
        os.makedirs(os.path.join(self.d, "refs", "remotes", "origin"))
        write(os.path.join(self.d, "refs", "remotes", "origin", "HEAD"),
              "ref: refs/remotes/origin/staging\n")
        os.makedirs(os.path.join(self.d, "refs", "heads"))
        write(os.path.join(self.d, "refs", "heads", "main"))
        self.assertEqual(gitstate.base_branch(self.d), "origin/staging")

    def test_local_main_then_master(self):
        os.makedirs(os.path.join(self.d, "refs", "heads"))
        self.assertIsNone(gitstate.base_branch(self.d))
        write(os.path.join(self.d, "refs", "heads", "master"))
        self.assertEqual(gitstate.base_branch(self.d), "master")
        write(os.path.join(self.d, "refs", "heads", "main"))
        self.assertEqual(gitstate.base_branch(self.d), "main")

    def test_a_packed_local_branch_counts(self):
        write(os.path.join(self.d, "packed-refs"),
              "# pack-refs with: peeled\nabc123 refs/heads/main\n")
        self.assertEqual(gitstate.base_branch(self.d), "main")

    def test_short_name(self):
        self.assertEqual(gitstate.short_base("origin/main"), "main")
        self.assertEqual(gitstate.short_base("origin/release/2.0"), "release/2.0")
        self.assertEqual(gitstate.short_base("main"), "main")
        self.assertIsNone(gitstate.short_base(None))


class Snapshot(unittest.TestCase):
    def test_round_trip(self):
        d = tempfile.mkdtemp()
        try:
            git(d, "init", "-q", "-b", "main")
            g = gitstate.collect(d)
            self.assertEqual(gitstate.from_dict(gitstate.to_dict(g)), g)
        finally:
            shutil.rmtree(d)

    def test_unknown_shape_raises(self):
        with self.assertRaises(gitstate.GitError):
            gitstate.from_dict({"branch": "old"})


class CollectRealRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        cls.remote = os.path.join(cls.root, "origin.git")
        cls.repo = os.path.join(cls.root, "demo")
        git(cls.root, "init", "-q", "--bare", cls.remote)
        git(cls.root, "init", "-q", "-b", "main", cls.repo)
        write(os.path.join(cls.repo, "a.txt"))
        git(cls.repo, "add", "a.txt")
        git(cls.repo, "commit", "-q", "-m", "one")
        git(cls.repo, "remote", "add", "origin", cls.remote)
        git(cls.repo, "push", "-q", "-u", "origin", "main")
        write(os.path.join(cls.repo, "a.txt"), "stashed\n")
        git(cls.repo, "stash", "-q")
        write(os.path.join(cls.repo, "b.txt"))
        git(cls.repo, "add", "b.txt")
        git(cls.repo, "commit", "-q", "-m", "two")       # ahead 1
        write(os.path.join(cls.repo, "a.txt"), "changed\n")  # modified
        write(os.path.join(cls.repo, "c.txt"))
        git(cls.repo, "add", "c.txt")                      # staged
        write(os.path.join(cls.repo, "d.txt"))             # untracked
        os.mkdir(os.path.join(cls.repo, "sub"))
        cls.wt = os.path.join(cls.root, "wt-feature")
        git(cls.repo, "worktree", "add", "-q", "-b", "feature", cls.wt)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root)

    def test_main_checkout(self):
        g = gitstate.collect(os.path.join(self.repo, "sub"))
        self.assertEqual(os.path.realpath(g.toplevel), os.path.realpath(self.repo))
        self.assertEqual(g.branch, "main")
        self.assertEqual(g.upstream, "origin/main")
        self.assertEqual((g.ahead, g.behind), (1, 0))
        self.assertEqual((g.staged, g.modified, g.untracked, g.conflicts), (1, 1, 1, 0))
        self.assertEqual(g.stash, 1)
        self.assertTrue(g.has_remote)
        self.assertFalse(g.linked_worktree)
        self.assertEqual(g.main_repo, "demo")
        self.assertIsNotNone(g.last_commit_ts)
        self.assertIsNone(g.operation)

    def test_linked_worktree(self):
        g = gitstate.collect(self.wt)
        self.assertTrue(g.linked_worktree)
        self.assertEqual(g.main_repo, "demo")
        self.assertEqual(g.branch, "feature")
        self.assertIsNone(g.upstream)

    def test_on_the_base_branch_no_base_counts(self):
        g = gitstate.collect(self.repo)
        self.assertTrue(g.is_base)
        self.assertEqual(g.base, "main")
        self.assertIsNone(g.ahead_base)

    def test_a_branch_counts_commits_against_the_base(self):
        g = gitstate.collect(self.wt)
        self.assertFalse(g.is_base)
        self.assertEqual(g.base, "main")
        self.assertEqual((g.ahead_base, g.behind_base), (0, 0))
        write(os.path.join(self.wt, "e.txt"))
        git(self.wt, "add", "e.txt")
        git(self.wt, "commit", "-q", "-m", "on feature")
        g = gitstate.collect(self.wt)
        self.assertEqual((g.ahead_base, g.behind_base), (1, 0))
        git(self.wt, "reset", "-q", "--hard", "HEAD~1")

    def test_detached_head_has_no_base_counts(self):
        d = os.path.join(self.root, "wt-detached")
        git(self.repo, "worktree", "add", "-q", "--detach", d)
        g = gitstate.collect(d)
        self.assertIsNone(g.branch)
        self.assertFalse(g.is_base)
        self.assertIsNone(g.ahead_base)

    def test_timeout_raises_the_timeout_error(self):
        with self.assertRaises(gitstate.GitTimeout):
            gitstate.collect(self.repo, timeout=0)

    def test_not_a_repo(self):
        d = tempfile.mkdtemp()
        try:
            self.assertIsNone(gitstate.collect(d))
        finally:
            shutil.rmtree(d)

    def test_missing_dir(self):
        self.assertIsNone(gitstate.collect(os.path.join(self.root, "nope")))


if __name__ == "__main__":
    unittest.main()
