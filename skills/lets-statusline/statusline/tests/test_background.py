import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from sl import background

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def wait_for(path, seconds=5.0):
    end = time.time() + seconds
    while time.time() < end:
        if os.path.exists(path):
            return True
        time.sleep(0.02)
    return False


class Spawn(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.lock = os.path.join(self.d, "x.lock")
        self.out = os.path.join(self.d, "out")

    def tearDown(self):
        # A detached job can still remove its lock while this runs.
        shutil.rmtree(self.d, ignore_errors=True)

    def touch(self):
        open(self.out, "w").close()

    def test_runs_the_job_and_removes_the_lock(self):
        self.assertTrue(background.spawn(self.touch, self.lock))
        self.assertTrue(wait_for(self.out))
        end = time.time() + 5
        while os.path.exists(self.lock) and time.time() < end:
            time.sleep(0.02)
        self.assertFalse(os.path.exists(self.lock))

    def test_a_held_lock_stops_a_second_job(self):
        open(self.lock, "w").close()
        self.assertFalse(background.spawn(self.touch, self.lock))
        time.sleep(0.1)
        self.assertFalse(os.path.exists(self.out))

    def test_an_old_lock_does_not_block_for_ever(self):
        open(self.lock, "w").close()
        old = time.time() - background.LOCK_TTL_S - 5
        os.utime(self.lock, (old, old))
        self.assertTrue(background.spawn(self.touch, self.lock))
        self.assertTrue(wait_for(self.out))

    def test_the_parent_exits_at_once_and_releases_the_pipes(self):
        # Claude Code reads stdout until EOF. A child that keeps the pipe open blocks the line.
        script = (
            "import sys, time\n"
            f"sys.path.insert(0, {ROOT!r})\n"
            "from sl import background\n"
            f"background.spawn(lambda: (time.sleep(3), open({self.out!r}, 'w').close()), {self.lock!r})\n"
            "print('done')\n"
        )
        start = time.time()
        r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=10)
        self.assertLess(time.time() - start, 1.5)
        self.assertEqual(r.stdout.strip(), "done")
        self.assertTrue(wait_for(self.out, 6))


if __name__ == "__main__":
    unittest.main()
