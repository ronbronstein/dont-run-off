import json
import os
import shutil
import tempfile
import time
import unittest

from sl import monthcost

NOW = time.mktime((2026, 11, 7, 12, 0, 0, 0, 0, -1))
NOV_2 = "2026-11-02T10:00:00Z"
OCT_30 = "2026-10-30T10:00:00Z"


def entry(model="claude-opus-5-5", ts=NOV_2, mid="m1", rid="r1", **usage):
    u = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
         "cache_creation_input_tokens": 0}
    u.update(usage)
    return {"type": "assistant", "timestamp": ts, "requestId": rid,
            "message": {"id": mid, "model": model, "usage": u}}


class Prices(unittest.TestCase):
    def test_one_million_output_tokens_on_opus_costs_the_list_price(self):
        self.assertAlmostEqual(monthcost.cost_of("claude-opus-5-5", {"output_tokens": 1_000_000}), 20)

    def test_cache_writes_cost_more_than_input_and_reads_cost_less(self):
        usage = {"cache_creation_input_tokens": 3_000_000, "cache_read_input_tokens": 1_000_000,
                 "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000}}
        # 2M at 5m (1.25 x $4) + 1M at 1h (2 x $4) + 1M read ($0.20)
        self.assertAlmostEqual(monthcost.cost_of("claude-opus-5-5", usage), 10 + 8 + 0.2)

    def test_fast_mode_costs_double(self):
        self.assertAlmostEqual(
            monthcost.cost_of("claude-opus-5-5", {"output_tokens": 1_000_000, "speed": "fast"}), 40)

    def test_a_context_suffix_does_not_hide_the_model(self):
        self.assertAlmostEqual(monthcost.cost_of("claude-opus-5-5[1m]", {"input_tokens": 1_000_000}), 4)

    def test_an_unknown_model_has_no_price(self):
        self.assertIsNone(monthcost.cost_of("gpt-9", {"input_tokens": 1}))

    def test_bad_numbers_count_as_zero(self):
        self.assertEqual(monthcost.cost_of("claude-opus-5-5", {"input_tokens": "lots"}), 0)


class Scan(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def write(self, name, rows, extra=""):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            f.write(extra)
        return path

    def test_sums_this_month_only_and_counts_a_streamed_message_once(self):
        self.write("p/a.jsonl", [entry(output_tokens=1_000_000),
                                 entry(output_tokens=1_000_000),            # same message again
                                 entry(mid="m2", rid="r2", output_tokens=500_000),
                                 entry(mid="m3", rid="r3", ts=OCT_30, output_tokens=9_000_000)])
        self.write("p/sub/agents/b.jsonl", [entry(model="claude-haiku-5-5", mid="h", rid="h",
                                                  output_tokens=2_000_000)])
        result = monthcost.scan(self.dir, monthcost.month_start(NOW))
        self.assertAlmostEqual(result["usd"], 20 + 10 + 1)
        self.assertEqual(result["unknown"], 0)

    def test_bad_lines_and_unknown_models_do_not_stop_the_scan(self):
        self.write("p/a.jsonl", [entry(output_tokens=1_000_000),
                                 entry(model="mystery", mid="x", rid="x", output_tokens=5),
                                 entry(model="<synthetic>", mid="s", rid="s"),
                                 {"type": "user", "message": "hi"}],
                   extra='{"broken json "usage"\n')
        result = monthcost.scan(self.dir, monthcost.month_start(NOW))
        self.assertAlmostEqual(result["usd"], 20)
        self.assertEqual(result["unknown"], 1)

    def test_skips_files_last_changed_before_the_month(self):
        path = self.write("p/old.jsonl", [entry(output_tokens=1_000_000)])
        old = monthcost.month_start(NOW) - 86400
        os.utime(path, (old, old))
        self.assertEqual(monthcost.scan(self.dir, monthcost.month_start(NOW))["usd"], 0)

    def test_no_projects_folder_is_zero(self):
        self.assertEqual(monthcost.scan(os.path.join(self.dir, "none"), 0)["usd"], 0)


class Get(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.mkdtemp()
        self.spawned = []

    def tearDown(self):
        shutil.rmtree(self.cache)

    def spawn(self, job, lock):
        self.spawned.append(lock)
        return True

    def get(self, now=NOW):
        return monthcost.get(self.cache, now, os.path.join(self.cache, "errors.log"),
                             "/nowhere", spawn=self.spawn)

    def save(self, **entry):
        monthcost.save(monthcost.cache_path(self.cache), entry)

    def test_no_cache_starts_a_job_and_shows_nothing(self):
        self.assertIsNone(self.get())
        self.assertEqual(len(self.spawned), 1)

    def test_a_fresh_cache_answers_without_a_job(self):
        self.save(ts=NOW - 60, month="2026-11", usd=731.0)
        self.assertEqual(self.get(), 731.0)
        self.assertEqual(self.spawned, [])

    def test_a_stale_cache_answers_and_starts_a_job(self):
        self.save(ts=NOW - monthcost.TTL_S, month="2026-11", usd=731.0)
        self.assertEqual(self.get(), 731.0)
        self.assertEqual(len(self.spawned), 1)

    def test_last_months_total_is_never_shown(self):
        self.save(ts=NOW - 60, month="2026-10", usd=999.0)
        self.assertIsNone(self.get())
        self.assertEqual(len(self.spawned), 1)

    def test_the_job_writes_the_cache(self):
        jobs = []
        monthcost.get(self.cache, NOW, "/dev/null", "/nowhere",
                      spawn=lambda job, lock: jobs.append(job) or True)
        jobs[0]()
        self.assertEqual(self.get(), 0)


class Folder(unittest.TestCase):
    def test_default_and_config_dir(self):
        self.assertEqual(monthcost.projects_dir({}, "/h"), os.path.join("/h", ".claude", "projects"))
        self.assertEqual(monthcost.projects_dir({"CLAUDE_CONFIG_DIR": "/c"}, "/h"),
                         os.path.join("/c", "projects"))


if __name__ == "__main__":
    unittest.main()
