import json
import unittest
from dataclasses import replace

from sl import seg_place, theme
from sl.gitstate import GitState
from sl.payload import parse

HOME = "/fake-home"
NOW = 1_800_000_000


def plain(seg):
    return theme.strip(seg.text), theme.strip(seg.short) if seg.short else None


def fg(c):
    return "38;2;%d;%d;%d" % c


def state(**over):
    g = GitState(toplevel=HOME + "/Code/acme/demo", branch="main", oid="abc1234",
                 upstream="origin/main", ahead=0, behind=0, staged=0, modified=0, untracked=0,
                 conflicts=0, stash=0, last_commit_ts=NOW - 600, operation=None,
                 linked_worktree=False, main_repo="demo", has_remote=True, base="origin/main",
                 ahead_base=None, behind_base=None)
    return replace(g, **over)


def session(cwd=HOME + "/Code/acme/demo", **extra):
    return parse(json.dumps(dict(cwd=cwd, **extra)))


class SplitPath(unittest.TestCase):
    def test_under_code(self):
        self.assertEqual(seg_place.split_path(HOME + "/Code/acme/demo", HOME), ("acme/", "demo"))

    def test_under_home(self):
        self.assertEqual(seg_place.split_path(HOME + "/.claude", HOME), ("~/", ".claude"))

    def test_home_itself(self):
        self.assertEqual(seg_place.split_path(HOME, HOME), ("", "~"))

    def test_outside_home(self):
        self.assertEqual(seg_place.split_path("/opt/thing", HOME), ("/opt/", "thing"))


class Where(unittest.TestCase):
    def test_on_the_base_branch(self):
        seg = seg_place.where(session(), state(), HOME)
        self.assertEqual(plain(seg), ("acme/demo  ⎇ main", "demo  ⎇ main"))
        self.assertIn(fg(theme.REPO) + "m" + "main", seg.text)

    def test_on_a_feature_branch_the_name_changes_color(self):
        seg = seg_place.where(session(), state(branch="feat/x"), HOME)
        self.assertEqual(plain(seg)[0], "acme/demo  ⎇ feat/x")
        self.assertIn(fg(theme.INFO) + "m" + "feat/x", seg.text)

    def test_subdir_is_shown(self):
        seg = seg_place.where(session(cwd=HOME + "/Code/acme/demo/src/app"), state(), HOME)
        self.assertEqual(plain(seg)[0], "acme/demo/src/app  ⎇ main")

    def test_long_subdir_keeps_the_tail(self):
        cwd = HOME + "/Code/acme/demo/" + "/".join(["abcdefgh"] * 5)
        text, _ = plain(seg_place.where(session(cwd=cwd), state(), HOME))
        self.assertTrue(text.startswith("acme/demo/…"))
        self.assertTrue(text.endswith("abcdefgh  ⎇ main"))

    def test_linked_worktree_says_worktree_in_words(self):
        g = state(toplevel="/x/worktrees/review-posts", linked_worktree=True,
                  branch="feat/review-posts")
        seg = seg_place.where(session(cwd=g.toplevel), g, HOME)
        self.assertEqual(plain(seg)[0], "demo  ⑂ worktree review-posts  ⎇ feat/review-posts")
        self.assertIn(fg(theme.WORKTREE), seg.text)

    def test_worktree_named_as_its_branch_does_not_repeat(self):
        g = state(toplevel="/x/worktrees/feat-x", linked_worktree=True, branch="feat-x")
        seg = seg_place.where(session(cwd=g.toplevel), g, HOME)
        self.assertEqual(plain(seg)[0], "demo  ⑂ worktree  ⎇ feat-x")

    def test_detached_head_is_amber(self):
        seg = seg_place.where(session(), state(branch=None), HOME)
        self.assertEqual(plain(seg)[0], "acme/demo  ⎇ detached @abc1234")
        self.assertIn(fg(theme.WARN), seg.text)

    def test_no_commits_yet(self):
        self.assertEqual(plain(seg_place.where(session(), state(oid=None), HOME))[0],
                         "acme/demo  ⎇ main (no commits)")

    def test_not_a_repo(self):
        self.assertEqual(plain(seg_place.where(session(cwd=HOME + "/notes"), None, HOME))[0],
                         "~/notes  no git")

    def test_failed_git_does_not_claim_no_git(self):
        seg = seg_place.where(session(), None, HOME, git_failed=True)
        self.assertNotIn("no git", plain(seg)[0])


class Changes(unittest.TestCase):
    def test_clean_is_a_short_green_word(self):
        seg = seg_place.changes(state(), NOW)
        self.assertEqual((plain(seg)[0], seg.tone), ("✓ clean", "calm"))
        self.assertIn(fg(theme.OK), seg.text)

    def test_dirty_names_each_count_and_the_last_commit(self):
        seg = seg_place.changes(state(staged=1, modified=2, untracked=3), NOW)
        self.assertEqual(plain(seg), ("1 staged · 2 changed · 3 new · last commit 10m ago",
                                      "+1 ~2 ?3"))
        self.assertEqual(seg.tone, "calm")

    def test_uncommitted_for_over_an_hour_is_solid_amber(self):
        seg = seg_place.changes(state(modified=1, last_commit_ts=NOW - 7200), NOW)
        self.assertEqual(seg.tone, "warn")
        self.assertEqual(plain(seg)[0], "1 changed · last commit 2h ago")

    def test_conflict_is_solid_red(self):
        seg = seg_place.changes(state(conflicts=1, modified=1), NOW)
        self.assertEqual(seg.tone, "bad")
        self.assertEqual(plain(seg)[0], "1 conflict · 1 changed")

    def test_dirty_with_no_commits_yet(self):
        seg = seg_place.changes(state(untracked=2, last_commit_ts=None), NOW)
        self.assertEqual(plain(seg)[0], "2 new")


class Commits(unittest.TestCase):
    def test_in_sync_shows_nothing(self):
        self.assertIsNone(seg_place.commits(state()))

    def test_states(self):
        cases = [
            (state(has_remote=False, upstream=None), "no remote"),
            (state(branch="feat/x", upstream=None), "branch not pushed"),
            (state(ahead=2), "↑2 not pushed"),
            (state(behind=3), "↓3 to pull"),
            (state(ahead=2, behind=3), "↑2 not pushed · ↓3 to pull"),
            (state(stash=2), "≡2 stashed"),
            (state(branch="feat/x", ahead_base=5, behind_base=0), "5 ahead of main"),
            (state(branch="feat/x", ahead_base=0, behind_base=2), "2 behind main"),
            (state(branch="feat/x", ahead=1, ahead_base=5, behind_base=2),
             "↑1 not pushed · 5 ahead of main · 2 behind main"),
        ]
        for g, want in cases:
            self.assertEqual(plain(seg_place.commits(g))[0], want)

    def test_short_form_uses_symbols(self):
        seg = seg_place.commits(state(branch="feat/x", ahead=1, behind=2, ahead_base=5,
                                      behind_base=3))
        self.assertEqual(plain(seg)[1], "↑1 ↓2 +5 -3")

    def test_base_on_a_local_only_repo_keeps_its_name(self):
        seg = seg_place.commits(state(branch="feat/x", base="main", has_remote=False, upstream=None,
                                      ahead_base=1, behind_base=0))
        self.assertEqual(plain(seg)[0], "no remote · 1 ahead of main")


class Build(unittest.TestCase):
    def texts(self, segs):
        return [plain(s)[0] for s in segs]

    def test_calm_repo_is_two_chips(self):
        segs = seg_place.build(session(), state(), HOME, NOW)
        self.assertEqual(self.texts(segs), ["acme/demo  ⎇ main", "✓ clean"])

    def test_operation_is_solid_red_and_comes_after_the_location(self):
        segs = seg_place.build(session(), state(operation="rebase 2/5", branch=None), HOME, NOW)
        self.assertEqual(self.texts(segs)[1], "⚑ rebase 2/5")
        self.assertEqual(segs[1].tone, "bad")

    def test_errors_are_marked(self):
        segs = seg_place.build(session(), state(), HOME, NOW, errors=("tasks",))
        self.assertIn("⚠ tasks", self.texts(segs))

    def test_stale_git_data_says_its_age(self):
        segs = seg_place.build(session(), state(), HOME, NOW, git_age=150)
        self.assertIn("git data 2m old", self.texts(segs))

    def test_recent_git_data_says_nothing(self):
        segs = seg_place.build(session(), state(), HOME, NOW, git_age=4)
        self.assertNotIn("git data", " ".join(self.texts(segs)))

    def test_slow_repo_with_no_data_yet(self):
        segs = seg_place.build(session(), None, HOME, NOW, git_pending=True)
        self.assertIn("reading git…", self.texts(segs))
        self.assertNotIn("no git", " ".join(self.texts(segs)))


if __name__ == "__main__":
    unittest.main()
