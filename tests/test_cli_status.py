"""CLI compatibility with the handwritten prologue and an explicit live start."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from world.__main__ import cmd_start, cmd_status
from world.engine import Days, until_of
from world.world import at_dt

REPO = Path(__file__).resolve().parents[1]


class CLIStatusTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-cli-")
        self.cfg = SimpleNamespace(docs=Path(self.tmp.name) / "docs", mind_url=None)
        self.days = Days(self.cfg.docs)
        self.day = json.loads((REPO / "docs/days/2026-10-02.json").read_text(encoding="utf-8"))
        self.days.save(copy.deepcopy(self.day))

    def tearDown(self):
        self.tmp.cleanup()

    def status(self):
        output = io.StringIO()
        with patch("world.__main__.now_ist", return_value=at_dt(date(2026, 10, 12), 12 * 60)), redirect_stdout(output):
            result = cmd_status(self.cfg, SimpleNamespace())
        self.assertEqual(result, 0)
        return output.getvalue()

    def test_status_accepts_handwritten_day_without_steps(self):
        self.assertNotIn("steps", self.day)
        output = self.status()
        self.assertIn("latest day     1 (2026-10-02), 0 steps", output)
        self.assertIn("quiet steps    0 today", output)
        self.assertNotIn("last step", output)

    def test_status_preserves_decision_counts_for_engine_days(self):
        day = copy.deepcopy(self.day)
        day["steps"] = [
            {"resumed": True},
            {"t": "09:00", "end": "09:30", "decision": {"action": "rest", "place": "home"},
             "mind": {"source": "quiet", "latency_s": 1.0, "attempts": 3}},
        ]
        self.days.save(day)
        output = self.status()
        self.assertIn("1 steps", output)
        self.assertIn("quiet steps    1 today", output)
        self.assertIn("last step      09:00–09:30 rest → home", output)

    def test_status_counts_refusals_and_flags_a_loop(self):
        day = copy.deepcopy(self.day)
        meal = "No household meal is available now; the next service is dinner from 19:30. Choose an available activity"
        day["steps"] = [{"t": f"{h}:00", "end": f"{h}:30", "decision": {"action": "rest", "place": "home"},
                         "mind": {"source": "mind", "latency_s": 1.0, "attempts": 2, "refused": [[meal]]}} for h in (14, 15, 16, 17)]
        day["steps"][0]["mind"]["refused"].append(["nothing is sold at home"])
        self.days.save(day)
        output = self.status()
        self.assertIn("refusals       5 today; most often (4×): No household meal is available now", output)
        self.assertIn("← a loop?", output)
        day["steps"] = day["steps"][:2]
        self.days.save(day)
        output = self.status()
        self.assertIn("refusals       3 today; most often (2×)", output)
        self.assertNotIn("a loop", output)

    def test_status_without_refusals(self):
        self.assertIn("refusals       0 today", self.status())

    def test_explicit_start_schedules_midnight_without_inventing_steps(self):
        args = SimpleNamespace(date="2026-10-13", no_git=True)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cmd_start(self.cfg, args), 0)
        day = self.days.latest()
        assert day is not None
        self.assertEqual(until_of(day), at_dt(date(2026, 10, 13), 0))
        self.assertTrue(day["state"]["asleep"])
        self.assertEqual(day["entries"], self.day["entries"])
        self.assertEqual(day["segments"], self.day["segments"])
        self.assertNotIn("steps", day)
        self.assertIn("published to   2026-10-13 00:00", self.status())


if __name__ == "__main__":
    unittest.main()
