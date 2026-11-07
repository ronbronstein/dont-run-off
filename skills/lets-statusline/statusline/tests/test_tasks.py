import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone

from sl import tasks

NOON = datetime(2026, 10, 10, 12, 0).timestamp()  # local noon


def tw(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


class FindNamespace(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.repo = os.path.join(self.root, "repo")
        self.sub = os.path.join(self.repo, "a", "b")
        os.makedirs(self.sub)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_namespace_line_bold_style(self):
        write(os.path.join(self.repo, "TASKS.md"), "# T\n\n**Namespace:** `acme.one`\n")
        self.assertEqual(tasks.find_namespace(self.sub, self.repo), "acme.one")

    def test_lowercase_and_bold_backticks(self):
        write(os.path.join(self.repo, "TASKS.md"), "namespace: **`acme.marketing.website`**\n")
        self.assertEqual(tasks.find_namespace(self.repo, self.repo), "acme.marketing.website")

    def test_project_form_with_trailing_dot(self):
        write(os.path.join(self.repo, "TASKS.md"), "Scope: `project:acme.tools.` and children\n")
        self.assertEqual(tasks.find_namespace(self.sub, self.repo), "acme.tools")

    def test_label_with_words_before_the_colon(self):
        write(os.path.join(self.repo, "TASKS.md"),
              "**Namespace (this repo): `acme.clients.example.website`**\n")
        self.assertEqual(tasks.find_namespace(self.repo, self.repo),
                         "acme.clients.example.website")

    def test_label_with_project_prefix(self):
        write(os.path.join(self.repo, "TASKS.md"),
              "Taskwarrior namespace for this repo: **`project:acme.two`**\n")
        self.assertEqual(tasks.find_namespace(self.repo, self.repo), "acme.two")

    def test_example_in_prose_is_not_a_namespace(self):
        write(os.path.join(self.repo, "TASKS.md"),
              "# T\n- Folder slug (e.g. `some-client`) ↔ namespace slug (flat, e.g. `someclient`).\n"
              "Scope: `project:real.one`\n")
        self.assertEqual(tasks.find_namespace(self.repo, self.repo), "real.one")

    def test_multi_namespace_file_gives_no_namespace(self):
        write(os.path.join(self.repo, "TASKS.md"),
              "# TASKS — x (MULTI-namespace)\n> Tasks: `task project:acme.marketing list`\n")
        self.assertIsNone(tasks.find_namespace(self.sub, self.repo))

    def test_deeper_taskproject_wins_in_a_multi_namespace_repo(self):
        write(os.path.join(self.repo, "TASKS.md"), "# TASKS (MULTI-namespace)\n")
        write(os.path.join(self.sub, ".taskproject"), "client.x\n")
        self.assertEqual(tasks.find_namespace(self.sub, self.repo), "client.x")

    def test_taskproject_file(self):
        write(os.path.join(self.repo, ".taskproject"), "acme.admin\n")
        self.assertEqual(tasks.find_namespace(self.sub, self.repo), "acme.admin")

    def test_tasks_md_wins_over_taskproject(self):
        write(os.path.join(self.repo, ".taskproject"), "b.b\n")
        write(os.path.join(self.repo, "TASKS.md"), "Namespace: `a.a`\n")
        self.assertEqual(tasks.find_namespace(self.repo, self.repo), "a.a")

    def test_stops_at_the_boundary(self):
        write(os.path.join(self.root, "TASKS.md"), "Namespace: `outside.repo`\n")
        self.assertIsNone(tasks.find_namespace(self.sub, self.repo))


class Summarize(unittest.TestCase):
    def test_counts(self):
        rows = [
            {"description": "plain"},
            {"description": "late", "due": tw(NOON - 3600)},
            {"description": "today", "due": tw(NOON + 3600)},
            {"description": "tomorrow", "due": tw(NOON + 86400)},
            {"description": "hidden", "wait": tw(NOON + 86400)},
            {"description": "doing it", "start": tw(NOON - 600)},
        ]
        s = tasks.summarize(rows, NOON)
        self.assertEqual(s.pending, 5)
        self.assertEqual(s.overdue, 1)
        self.assertEqual(s.due_today, 1)
        self.assertEqual(s.active_count, 1)
        self.assertEqual(s.active, "doing it")

    def test_latest_started_task_is_shown(self):
        rows = [{"description": "old", "start": tw(NOON - 9000)},
                {"description": "new", "start": tw(NOON - 60)}]
        s = tasks.summarize(rows, NOON)
        self.assertEqual((s.active, s.active_count), ("new", 2))

    def test_bad_dates_are_ignored(self):
        s = tasks.summarize([{"description": "x", "due": "garbage"}], NOON)
        self.assertEqual((s.pending, s.overdue), (1, 0))


class Load(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.mkdtemp()
        self.calls = 0

    def tearDown(self):
        shutil.rmtree(self.cache)

    def runner(self, args, **kw):
        self.calls += 1
        self.assertIn("rc.gc=off", args)
        self.assertIn("rc.recurrence=off", args)
        self.assertIn("project:demo.ns", args)
        return subprocess.CompletedProcess(args, 0, json.dumps([{"description": "a"}]), "")

    def test_uses_cache_within_ttl(self):
        tasks.load("demo.ns", self.cache, NOON, runner=self.runner)
        s = tasks.load("demo.ns", self.cache, NOON + 10, runner=self.runner)
        self.assertEqual(self.calls, 1)
        self.assertEqual(s.pending, 1)

    def test_refreshes_after_ttl(self):
        tasks.load("demo.ns", self.cache, NOON, runner=self.runner)
        tasks.load("demo.ns", self.cache, NOON + tasks.TTL_S + 1, runner=self.runner)
        self.assertEqual(self.calls, 2)

    def test_no_taskwarrior_is_normal_and_gives_no_summary(self):
        def missing(args, **kw):
            raise FileNotFoundError("task")
        self.assertIsNone(tasks.load("demo.ns", self.cache, NOON, runner=missing))

    def test_failure_raises_typed_error(self):
        def broken(args, **kw):
            return subprocess.CompletedProcess(args, 2, "", "boom")
        with self.assertRaises(tasks.TaskError) as cm:
            tasks.load("demo.ns", self.cache, NOON, runner=broken)
        self.assertIn("demo.ns", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
