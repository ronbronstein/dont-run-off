"""Tests for skills/lets-statusline/install.py. Each test runs it as a user does, in a temp home."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL = os.path.join(ROOT, "skills", "lets-statusline", "install.py")


class Installer(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="sl-install-")
        self.claude = os.path.join(self.home, ".claude")
        os.makedirs(self.claude)
        self.settings = os.path.join(self.claude, "settings.json")
        self.target = os.path.join(self.claude, "statusline")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def run_it(self, *args, ok=True):
        env = dict(os.environ, HOME=self.home)
        r = subprocess.run([sys.executable, INSTALL, *args], env=env, capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def status(self):
        return json.loads(self.run_it("status").stdout)

    def write_settings(self, data):
        with open(self.settings, "w") as f:
            json.dump(data, f)

    def read_settings(self):
        with open(self.settings) as f:
            return json.load(f)

    def backups(self, prefix):
        return [n for n in os.listdir(self.claude) if n.startswith(prefix)]

    def edit_installed(self, rel="sl/theme.py"):
        with open(os.path.join(self.target, rel), "a") as f:
            f.write("# my change\n")

    def test_status_on_a_new_machine(self):
        s = self.status()
        self.assertEqual(s["state"], "not-installed")
        self.assertIsNone(s["current_status_line"])
        self.assertIn("python", s)
        self.assertIn("git", s["tools"])

    def test_status_reads_the_theme_and_an_existing_line(self):
        self.write_settings({"theme": "light", "statusLine": {"type": "command", "command": "x"}})
        s = self.status()
        self.assertEqual(s["theme"], "light")
        self.assertEqual(s["current_status_line"]["command"], "x")

    def test_install_copies_the_code_and_writes_only_the_status_line(self):
        self.write_settings({"theme": "dark", "model": "m", "hooks": {"a": 1}})
        self.run_it("install")
        s = self.read_settings()
        self.assertEqual(s["theme"], "dark")
        self.assertEqual(s["model"], "m")
        self.assertEqual(s["hooks"], {"a": 1})
        self.assertEqual(s["statusLine"]["type"], "command")
        self.assertEqual(s["statusLine"]["refreshInterval"], 10)
        self.assertIn(self.target, s["statusLine"]["command"])
        self.assertTrue(os.path.exists(os.path.join(self.target, "statusline.py")))
        self.assertFalse(any("__pycache__" in d for d, _, _ in os.walk(self.target)))

    def test_install_backs_up_settings_first(self):
        self.write_settings({"model": "m"})
        self.run_it("install")
        names = self.backups("settings.json.")
        self.assertEqual(len(names), 1)
        with open(os.path.join(self.claude, names[0])) as f:
            self.assertEqual(json.load(f), {"model": "m"})

    def test_install_with_no_settings_file_creates_one(self):
        self.run_it("install")
        self.assertIn("statusLine", self.read_settings())

    def test_the_written_command_runs(self):
        self.run_it("install")
        command = self.read_settings()["statusLine"]["command"]
        r = subprocess.run(command, shell=True, input="{}", capture_output=True, text=True,
                           env=dict(os.environ, HOME=self.home))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("statusline error", r.stdout)

    def test_broken_settings_stop_the_install_and_change_nothing(self):
        with open(self.settings, "w") as f:
            f.write("{not json")
        r = self.run_it("install", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("settings.json", r.stderr)
        with open(self.settings) as f:
            self.assertEqual(f.read(), "{not json")
        self.assertFalse(os.path.exists(self.target))

    def test_settings_that_are_a_link_stay_a_link(self):
        real = os.path.join(self.home, "real-settings.json")
        with open(real, "w") as f:
            json.dump({"model": "m"}, f)
        os.symlink(real, self.settings)
        self.run_it("install")
        self.assertTrue(os.path.islink(self.settings))
        with open(real) as f:
            self.assertIn("statusLine", json.load(f))

    def test_after_install_the_state_is_up_to_date(self):
        self.run_it("install")
        s = self.status()
        self.assertEqual(s["state"], "up-to-date")
        self.assertEqual(s["changed_by_user"], [])

    def test_status_names_the_files_that_the_user_changed(self):
        self.run_it("install")
        self.edit_installed()
        s = self.status()
        self.assertEqual(s["changed_by_user"], ["sl/theme.py"])

    def test_an_older_install_with_no_record_compares_with_the_new_code(self):
        self.run_it("install")
        os.remove(os.path.join(self.target, ".install.json"))
        self.edit_installed()
        s = self.status()
        self.assertEqual(s["state"], "no-record")
        self.assertEqual(s["changed_by_user"], ["sl/theme.py"])

    def test_a_new_file_of_the_user_counts_as_changed(self):
        self.run_it("install")
        with open(os.path.join(self.target, "mine.py"), "w") as f:
            f.write("x = 1\n")
        self.assertEqual(self.status()["changed_by_user"], ["mine.py"])

    def test_reinstall_keeps_a_backup_with_the_user_edit(self):
        self.run_it("install")
        self.edit_installed()
        self.run_it("install")
        names = self.backups("statusline.backup-")
        self.assertEqual(len(names), 1)
        with open(os.path.join(self.claude, names[0], "sl", "theme.py")) as f:
            self.assertIn("# my change", f.read())
        with open(os.path.join(self.target, "sl", "theme.py")) as f:
            self.assertNotIn("# my change", f.read())
        self.assertEqual(self.status()["changed_by_user"], [])

    def test_undo_restores_the_earlier_line_and_keeps_later_settings(self):
        old = {"type": "command", "command": "mine"}
        self.write_settings({"statusLine": old})
        self.run_it("install")
        s = self.read_settings()
        s["model"] = "set later"
        self.write_settings(s)
        self.run_it("undo")
        self.assertEqual(self.read_settings(), {"statusLine": old, "model": "set later"})

    def test_undo_after_two_installs_goes_back_to_the_first_line(self):
        old = {"type": "command", "command": "mine"}
        self.write_settings({"statusLine": old})
        self.run_it("install")
        self.run_it("install")
        self.run_it("undo")
        self.assertEqual(self.read_settings()["statusLine"], old)

    def test_undo_restores_a_user_line_with_a_similar_path(self):
        old = {"type": "command", "command": f"{self.claude}/statusline.sh"}
        self.write_settings({"statusLine": old})
        self.run_it("install")
        self.run_it("undo")
        self.assertEqual(self.read_settings()["statusLine"], old)

    def test_undo_with_no_earlier_line_removes_the_key(self):
        self.write_settings({"model": "m"})
        self.run_it("install")
        self.run_it("undo")
        self.assertEqual(self.read_settings(), {"model": "m"})

    def test_undo_with_no_install_says_so(self):
        r = self.run_it("undo", ok=False)
        self.assertIn("not installed", r.stderr)


if __name__ == "__main__":
    unittest.main()
