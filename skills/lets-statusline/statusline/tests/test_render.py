import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from sl import gitstate, render, theme
from sl.prstate import PrView
from tests.test_gitstate import ENV, git, write
from tests.test_seg_pr import facts

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
NOW = 1791633000  # cache expires in 54m10s, 5h resets in 2h40m


def payload(**overrides):
    with open(os.path.join(FIXTURES, "payload_real.json")) as f:
        d = json.load(f)
    for key, value in overrides.items():
        d[key] = value
    return d


def no_tasks(args, **kw):
    return subprocess.CompletedProcess(args, 0, "[]", "")


def no_spawn(job, lock):
    return False


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        cls.home = os.path.join(cls.root, "home")
        cls.repo = os.path.join(cls.home, "Code", "acme", "demo")
        os.makedirs(cls.repo)
        git(cls.repo, "init", "-q", "-b", "main")
        write(os.path.join(cls.repo, "a.txt"))
        git(cls.repo, "add", "a.txt")
        git(cls.repo, "commit", "-q", "-m", "one")
        cls.cache = os.path.join(cls.root, "cache")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root)

    def setUp(self):
        shutil.rmtree(self.cache, ignore_errors=True)

    def run_render(self, d, columns=140, runner=no_tasks, collect_git=None, cwd=None, get_pr=None):
        d = dict(d)
        d["cwd"] = cwd or self.repo
        kw = {"collect_git": collect_git} if collect_git else {}
        out = render.render(json.dumps(d), {"COLUMNS": str(columns)}, NOW, home=self.home,
                            cache_dir=self.cache, task_runner=runner, spawn=no_spawn,
                            get_pr=get_pr or (lambda s, g: None), **kw)
        return out, [theme.strip(l) for l in out.split("\n")]


class Layout(Base):
    def test_two_lines_with_the_main_facts(self):
        _, lines = self.run_render(payload())
        self.assertEqual(len(lines), 3)
        place, session, usage = lines
        for text in ("acme/demo", "⎇ main", "✓ clean", "no remote"):
            self.assertIn(text, place)
        for text in ("ctx", "208k", "54:10", "cache", "Opus 5.5", "xhigh"):
            self.assertIn(text, session)
        for text in ("5h", "26%", "◷ 𝟮𝗵𝟰𝟬𝗺", "7d", "8%", "▦ "):
            self.assertIn(text, usage)
            self.assertNotIn(text, session)
        self.assertTrue(place.rstrip().endswith("“demo site rebuild” 19m"), place)
        self.assertNotIn("demo site rebuild", session)

    def test_a_thin_line_separates_the_chips(self):
        _, lines = self.run_render(payload())
        self.assertIn("xhigh │ ctx", lines[1])

    def test_the_three_rows_make_one_even_block(self):
        out, _ = self.run_render(payload())
        self.assertEqual(len({theme.width(row) for row in out.split("\n")}), 1)

    def test_banners_stay_outside_the_block(self):
        d = payload()
        d["context_window"] = dict(d["context_window"], total_input_tokens=650_000,
                                   used_percentage=65)
        out, _ = self.run_render(d)
        rows = out.split("\n")
        self.assertEqual(len({theme.width(row) for row in rows[-3:]}), 1)
        self.assertNotIn(theme.chip_fill(1), rows[0])

    def test_no_limits_means_no_empty_row(self):
        d = payload()
        del d["rate_limits"]
        _, lines = self.run_render(d)
        self.assertEqual(len(lines), 2)

    def test_the_session_cost_ends_row_two(self):
        # It is about the session, not the limits.
        _, lines = self.run_render(payload())
        self.assertTrue(theme.strip(lines[1]).rstrip().endswith("│ ⛁ $7.78"), lines[1])
        self.assertNotIn("⛁", theme.strip(lines[2]))

    def test_model_comes_first_on_the_second_line(self):
        _, lines = self.run_render(payload())
        self.assertTrue(lines[1].lstrip().startswith("◆ Opus 5.5 ●●●●○ xhigh"), lines[1])

    def test_model_and_effort_stay_on_a_narrow_line(self):
        _, lines = self.run_render(payload(), columns=60)
        self.assertIn("◆ Opus 5.5 ●●●●○", lines[1])

    def test_vanity_stats_are_gone(self):
        out, _ = self.run_render(payload())
        text = theme.strip(out)
        # The API cost came back on purpose (2026-11-07), on row 3 only.
        for word in ("+151", "% hit", "cached", "next warning", "all pushed", "tasks", "▌"):
            self.assertNotIn(word, text)

    def test_narrow_terminal_fits(self):
        out, lines = self.run_render(payload(), columns=60)
        for raw in out.split("\n"):
            self.assertLessEqual(theme.width(raw), 60 - render.MARGIN)
        self.assertIn("ctx", lines[1])
        self.assertRegex(lines[1], r"[⏳⌛] \d+:\d\d")

    def test_not_a_git_folder(self):
        plain = os.path.join(self.home, "notes")
        os.makedirs(plain, exist_ok=True)
        _, lines = self.run_render(payload(), cwd=plain)
        self.assertIn("~/notes", lines[0])
        self.assertIn("no git", lines[0])

    def test_columns_of_zero_use_the_default(self):
        self.assertEqual(render._columns({"COLUMNS": "0"}), render.DEFAULT_COLUMNS)


class EmptyPayload(Base):
    def test_no_cwd_shows_no_folder(self):
        out = render.render("{}", {"COLUMNS": "120"}, NOW, home=self.home, cache_dir=self.cache,
                            task_runner=no_tasks, spawn=no_spawn)
        self.assertNotIn("no git", theme.strip(out))


class ContextLadder(Base):
    def ctx(self, used):
        d = payload()
        d["context_window"] = dict(d["context_window"], total_input_tokens=used,
                                   used_percentage=used / 10_000)
        return d

    def test_level_3_pill(self):
        _, lines = self.run_render(self.ctx(310_000))
        self.assertIn("Seriously? 310k", lines[1])
        self.assertEqual(len(lines), 3)

    def test_level_4_adds_a_banner_on_top(self):
        _, lines = self.run_render(self.ctx(420_000))
        self.assertEqual(len(lines), 4)
        self.assertIn("Seriously?!", lines[0])

    def test_level_6_adds_two_banners(self):
        _, lines = self.run_render(self.ctx(650_000))
        self.assertEqual(len(lines), 5)
        self.assertIn("STOP.", lines[0])


class Signals(Base):
    def test_pr_chip_is_on_the_first_line(self):
        view = PrView("pr", facts(number=7, state="MERGED", ended_at=NOW - 3600))
        _, lines = self.run_render(payload(), get_pr=lambda s, g: view)
        self.assertIn("PR #7 merged 1h ago", lines[0])

    def test_tasks_show_only_what_matters(self):
        write(os.path.join(self.repo, "TASKS.md"), "Namespace: `demo.ns`\n")
        try:
            rows = [{"description": "ship the status line", "start": "20261010T080000Z"},
                    {"description": "late", "due": "20200101T000000Z"}, {"description": "x"}]

            def runner(args, **kw):
                return subprocess.CompletedProcess(args, 0, json.dumps(rows), "")
            _, lines = self.run_render(payload(), runner=runner, columns=200)
            self.assertIn("▶ ship the status line", lines[1])
            self.assertIn("1 overdue", lines[1])
            self.assertNotIn("open", lines[1])
        finally:
            os.remove(os.path.join(self.repo, "TASKS.md"))


class Errors(Base):
    def test_collector_error_is_logged_and_marked(self):
        def broken(cwd, timeout=None):
            raise RuntimeError("git exploded")
        _, lines = self.run_render(payload(), collect_git=broken)
        self.assertIn("⚠", lines[0])
        with open(os.path.join(self.cache, "errors.log")) as f:
            self.assertIn("git exploded", f.read())

    def test_slow_git_is_not_an_error(self):
        def slow(cwd, timeout=None):
            raise gitstate.GitTimeout("git status timed out")
        _, lines = self.run_render(payload(), collect_git=slow)
        self.assertIn("reading git…", lines[0])
        self.assertNotIn("⚠", lines[0])
        self.assertFalse(os.path.exists(os.path.join(self.cache, "errors.log")))

    def test_a_pr_failure_does_not_blank_the_line(self):
        def broken(s, g):
            raise RuntimeError("pr exploded")
        _, lines = self.run_render(payload(), get_pr=broken)
        self.assertIn("⚠ pr", lines[0])

    def test_entry_point_never_fails(self):
        home = tempfile.mkdtemp()
        try:
            script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "statusline.py")
            r = subprocess.run([sys.executable, script], input="not json", capture_output=True,
                               text=True, env=dict(ENV, HOME=home))
            self.assertEqual(r.returncode, 0)
            self.assertIn("statusline error", r.stdout)
            log = os.path.join(home, ".claude", "cache", "statusline", "errors.log")
            self.assertTrue(os.path.exists(log))
        finally:
            shutil.rmtree(home)


class DebugDump(Base):
    def test_no_dump_without_the_flag(self):
        self.run_render(payload())
        self.assertFalse(os.path.exists(os.path.join(self.cache, "payloads")))

    def test_dump_with_the_flag(self):
        os.makedirs(self.cache, exist_ok=True)
        flag = os.path.join(self.cache, "DEBUG")
        open(flag, "w").close()
        self.run_render(payload())
        path = os.path.join(self.cache, "payloads", "00000000.json")
        with open(path) as f:
            self.assertEqual(json.load(f)["session_name"], "demo site rebuild")


if __name__ == "__main__":
    unittest.main()
