import os
import shutil
import tempfile
import unittest

from sl import errlog


class ErrLog(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "deep", "errors.log")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_writes_context(self):
        try:
            raise ValueError("bad thing")
        except ValueError as e:
            errlog.log(self.path, "git", e, cwd="/x")
        with open(self.path) as f:
            text = f.read()
        self.assertIn("[git] ValueError: bad thing", text)
        self.assertIn("cwd=/x", text)

    def test_rotates_when_big(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as f:
            f.write("x" * (errlog.MAX_BYTES + 1))
        errlog.log(self.path, "tasks", RuntimeError("again"))
        self.assertTrue(os.path.exists(self.path + ".1"))
        self.assertLess(os.path.getsize(self.path), 2000)


if __name__ == "__main__":
    unittest.main()
