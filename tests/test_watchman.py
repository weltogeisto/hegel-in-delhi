"""The watchman (T17) on Day 13's real record: the morning the PC restarted and the mind went away."""
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("watchman", REPO / "tools" / "watchman.py")
watchman = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchman)

DAY13 = json.loads((REPO / "tests/data/day13-2026-10-14.json").read_text(encoding="utf-8"))
SHIFT = 300


class WatchmanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-watch-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def published_to(self, t):
        """Day 13 as the Pi had published it when the step at t was the latest, and a moment on his clock just before it ran out."""
        day = copy.deepcopy(DAY13)
        cut = next(i for i, s in enumerate(day["steps"]) if s.get("t") == t)
        day["steps"] = day["steps"][:cut + 1]
        end = day["steps"][-1]["end"]
        day["state"]["until"] = f"{day['date']}T{end}+05:30" if end != "24:00" else f"{day['date']}T23:59+05:30"
        day["state"]["asleep"] = day["steps"][-1]["decision"]["action"] == "sleep"
        (self.tmp / f"{day['date']}.json").write_text(json.dumps(day), encoding="utf-8")
        (self.tmp / "index.json").write_text(json.dumps({"format": 1, "clock_shift_min": SHIFT,
                                                         "days": [{"date": day["date"], "n": day["n"]}]}), encoding="utf-8")
        his_now = watchman.until_of(day) - timedelta(minutes=10)
        return (his_now - timedelta(minutes=SHIFT)).astimezone(timezone.utc)

    def test_day13_morning_raises_the_alarm_at_the_third_step_without_a_mind(self):
        self.assertEqual(watchman.check(self.tmp, self.published_to("08:11"))["state"], "ok")       # a walk, decided by the mind
        self.assertEqual(watchman.check(self.tmp, self.published_to("09:01"))["state"], "ok")       # two steps away: not yet
        alarm = watchman.check(self.tmp, self.published_to("09:31"))
        self.assertEqual(alarm["state"], "mind_away")
        self.assertIn("08:31, 09:01, 09:31", alarm["detail"])
        self.assertNotIn("192.168", alarm["detail"])                    # the PC's address stays out of a public issue
        self.assertNotIn("http", alarm["detail"])

    def test_asleep_he_needs_no_mind(self):
        now = self.published_to("22:20")                                 # Day 13 ends: away all afternoon, then to bed
        self.assertEqual(watchman.check(self.tmp, now)["state"], "ok")

    def test_a_published_day_that_ran_out_an_hour_ago_means_the_world_stopped(self):
        now = self.published_to("09:31") + timedelta(minutes=10 + 61)
        quiet = watchman.check(self.tmp, now)
        self.assertEqual(quiet["state"], "pi_quiet")
        self.assertIn("61 minutes", quiet["detail"])
        self.assertEqual(watchman.check(self.tmp, now - timedelta(minutes=2))["state"], "mind_away")

    def test_the_hourly_workflow_runs_it_on_the_shadow_branch(self):
        wf = (REPO / ".github/workflows/watchman.yml").read_text(encoding="utf-8")
        self.assertIn("ref: shadow", wf)
        self.assertIn("python3 tools/watchman.py shadow/docs/days", wf)
        self.assertIn("issues: write", wf)


if __name__ == "__main__":
    unittest.main()
