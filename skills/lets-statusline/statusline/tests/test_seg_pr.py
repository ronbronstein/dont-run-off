import unittest

from sl import seg_pr, theme
from sl.prstate import PrFacts, PrView

NOW = 1_800_000_000


def facts(**over):
    base = dict(number=42, state="OPEN", draft=False, review=None, conflicting=False, failed=0,
                pending=0, passed=0, url="https://github.com/o/r/pull/42", ended_at=None, kind=None)
    base.update(over)
    return PrFacts(**base)


def chip(**over):
    return seg_pr.build(PrView("pr", facts(**over)), NOW)


def text(seg):
    return theme.strip(seg.text)


def fg(c):
    return "38;2;%d;%d;%d" % c


class States(unittest.TestCase):
    def test_open_is_green(self):
        seg = chip()
        self.assertEqual(text(seg), "PR #42 open")
        self.assertIn(fg(theme.PR_OPEN), seg.text)
        self.assertEqual(seg.tone, "calm")

    def test_draft_is_gray(self):
        seg = chip(draft=True)
        self.assertEqual(text(seg), "PR #42 draft")
        self.assertIn(fg(theme.PR_DRAFT), seg.text)

    def test_merged_is_purple_with_its_age(self):
        seg = chip(state="MERGED", ended_at=NOW - 7200)
        self.assertEqual(text(seg), "PR #42 merged 2h ago")
        self.assertIn(fg(theme.PR_MERGED), seg.text)

    def test_closed_is_red_text_and_not_an_alarm(self):
        seg = chip(state="CLOSED", ended_at=NOW - 3 * 86400)
        self.assertEqual(text(seg), "PR #42 closed 3d ago")
        self.assertIn(fg(theme.PR_CLOSED), seg.text)
        self.assertEqual(seg.tone, "calm")

    def test_merged_ignores_checks_and_conflicts(self):
        seg = chip(state="MERGED", ended_at=NOW - 60, failed=2, conflicting=True)
        self.assertEqual(text(seg), "PR #42 merged 1m ago")
        self.assertEqual(seg.tone, "calm")


class Signals(unittest.TestCase):
    def test_approved(self):
        self.assertEqual(text(chip(review="APPROVED")), "PR #42 open · approved")

    def test_needs_review(self):
        self.assertEqual(text(chip(review="REVIEW_REQUIRED")), "PR #42 open · needs review")

    def test_changes_requested_is_solid_red(self):
        seg = chip(review="CHANGES_REQUESTED")
        self.assertEqual((text(seg), seg.tone), ("PR #42 open · changes requested", "bad"))

    def test_checks_passing(self):
        self.assertEqual(text(chip(passed=3)), "PR #42 open · ✓ checks")

    def test_checks_running(self):
        seg = chip(passed=1, pending=2)
        self.assertEqual(text(seg), "PR #42 open · ◌ 2 checks running")
        self.assertEqual(seg.tone, "calm")

    def test_checks_failed_is_solid_red(self):
        seg = chip(failed=1, passed=2)
        self.assertEqual((text(seg), seg.tone), ("PR #42 open · ✗ 1 check failed", "bad"))

    def test_conflicts_are_solid_red(self):
        seg = chip(conflicting=True)
        self.assertEqual((text(seg), seg.tone), ("PR #42 open · ✗ conflicts", "bad"))

    def test_a_draft_with_failed_checks_is_still_an_alarm(self):
        seg = chip(draft=True, failed=2)
        self.assertEqual((text(seg), seg.tone), ("PR #42 draft · ✗ 2 checks failed", "bad"))

    def test_short_form_keeps_the_state_and_the_alarm(self):
        self.assertEqual(theme.strip(chip(passed=1).short), "PR #42 open")
        self.assertEqual(theme.strip(chip(failed=1).short), "PR #42 ✗ checks")

    def test_link_to_the_pr(self):
        self.assertIn("\x1b]8;;https://github.com/o/r/pull/42", chip().text)

    def test_link_survives_a_solid_chip(self):
        self.assertIn("\x1b]8;;https://github.com/o/r/pull/42",
                      theme.chip(chip(failed=1).text, "bad"))

    def test_no_url_means_no_link(self):
        self.assertNotIn("\x1b]8", chip(url=None).text)


class Others(unittest.TestCase):
    def test_gitlab(self):
        self.assertEqual(text(chip(kind="mr", number=9)), "MR !9 open")

    def test_no_pr_on_a_pushed_branch(self):
        self.assertEqual(text(seg_pr.build(PrView("none", None), NOW)), "no PR")

    def test_unknown_after_a_failed_lookup(self):
        self.assertEqual(text(seg_pr.build(PrView("unknown", None), NOW)), "PR ?")

    def test_nothing_to_show(self):
        self.assertIsNone(seg_pr.build(None, NOW))


if __name__ == "__main__":
    unittest.main()
