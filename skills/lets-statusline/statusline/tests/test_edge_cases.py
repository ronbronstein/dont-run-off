"""Edge cases found in the 2026-10-10 code review, kept through the 2026-11 redesign."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from sl import fmt, gitstate, layout, render, tasks, theme
from sl.layout import Segment
from tests.test_gitstate import ENV
from tests.test_seg_place import HOME

NOW = 1_800_000_000


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


class NonUtf8Files(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_latin1_tasks_md_does_not_crash(self):
        write_bytes(os.path.join(self.d, "TASKS.md"), b"Caf\xe9\nNamespace: `a.b`\n")
        self.assertEqual(tasks.find_namespace(self.d, self.d), "a.b")

    def test_namespace_errors_do_not_blank_the_line(self):
        def boom(*a, **k):
            raise OSError("disk on fire")
        original = tasks.find_namespace
        tasks.find_namespace = boom
        try:
            out = render.render(json.dumps({"cwd": self.d}), {"COLUMNS": "120"}, NOW, home=HOME,
                                cache_dir=os.path.join(self.d, "c"))
        finally:
            tasks.find_namespace = original
        self.assertIn("⚠", theme.strip(out))


class TaskprojectValidation(unittest.TestCase):
    def test_bad_value_is_ignored(self):
        d = tempfile.mkdtemp()
        try:
            write_bytes(os.path.join(d, ".taskproject"), b"acme/sessions\n")
            self.assertIsNone(tasks.find_namespace(d, d))
        finally:
            shutil.rmtree(d)


class Width(unittest.TestCase):
    def test_single_wide_segment_is_truncated(self):
        out = layout.line((Segment(theme.paint("x" * 80, fg=theme.REPO, bold=True)),), 30)
        self.assertLessEqual(theme.width(out), 30)
        self.assertIn("…", theme.strip(out))
        self.assertTrue(out.endswith(theme.RESET))

    def test_truncate_visible_keeps_codes(self):
        s = theme.paint("abcdef", fg=theme.OK) + theme.paint("ghij", fg=theme.BAD)
        cut = theme.truncate_visible(s, 7)
        self.assertEqual(theme.strip(cut), "abcdef…")
        self.assertEqual(theme.truncate_visible(s, 50), s)

    def test_tiny_terminal_stays_in_budget(self):
        d = tempfile.mkdtemp()
        try:
            p = json.dumps({"cwd": "/tmp", "model": {"display_name": "Opus 5.5"},
                            "context_window": {"total_input_tokens": 650000,
                                               "context_window_size": 1000000}})
            out = render.render(p, {"COLUMNS": "24"}, NOW, home=HOME, cache_dir=d)
            for row in out.split("\n"):
                self.assertLessEqual(theme.width(row), 24 - render.MARGIN, theme.strip(row))
        finally:
            shutil.rmtree(d)


class BareRepoWorktree(unittest.TestCase):
    def test_repo_name_from_bare_common_dir(self):
        self.assertEqual(gitstate.repo_name("/x/bare.git", "/x/wt", linked=True), "bare")
        self.assertEqual(gitstate.repo_name("/x/demo/.git", "/x/wt", linked=True), "demo")
        self.assertEqual(gitstate.repo_name("/x/demo/.git", "/x/demo", linked=False), "demo")


class Tokens(unittest.TestCase):
    def test_no_1000k(self):
        self.assertEqual(fmt.tokens(999_600), "1M")
        self.assertEqual(fmt.tokens(1_250_000), "1.2M")


class EntryPointEncoding(unittest.TestCase):
    def test_non_utf8_locale_still_prints(self):
        home = tempfile.mkdtemp()
        try:
            script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "statusline.py")
            p = b'{"cwd": "/tmp", "context_window": {"total_input_tokens": 1000}}'
            r = subprocess.run([sys.executable, script], input=p, capture_output=True,
                               env=dict(ENV, HOME=home, LC_ALL="en_US.ISO8859-1",
                                        PYTHONIOENCODING="latin-1"))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("▱".encode("utf-8"), r.stdout)
        finally:
            shutil.rmtree(home)


if __name__ == "__main__":
    unittest.main()
