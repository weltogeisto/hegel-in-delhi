"""A rehearsal may run his clock ahead of Delhi; the page follows the published shift."""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from world.clock import IST, now_ist
from world.config import Config
from world.engine import Days

REPO = Path(__file__).resolve().parents[1]


class ClockShiftTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-shift-")
        self.day = json.loads((REPO / "docs/days/2026-10-02.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def index(self, shift):
        days = Days(Path(self.tmp.name), shift)
        days.save(copy.deepcopy(self.day))
        return days.index()

    def test_config_reads_the_shift_and_defaults_to_zero(self):
        env = {k: v for k, v in os.environ.items() if k != "HEGEL_CLOCK_SHIFT_MIN"}
        env["HEGEL_ENV"] = str(Path(self.tmp.name) / "no-env")          # not the machine's own env file
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(Config({"HEGEL_CLOCK_SHIFT_MIN": "300"}).clock_shift_min, 300)
            self.assertEqual(Config().clock_shift_min, 0)

    def test_now_runs_ahead_by_the_shift(self):
        gap = now_ist(300) - datetime.now(IST)
        self.assertLess(abs(gap - timedelta(minutes=300)), timedelta(seconds=5))
        self.assertLess(abs(now_ist() - datetime.now(IST)), timedelta(seconds=5))

    def test_index_publishes_clears_or_keeps_the_shift(self):
        self.assertEqual(self.index(300)["clock_shift_min"], 300)
        self.assertEqual(self.index(None)["clock_shift_min"], 300)       # a Days without the config leaves it
        self.assertNotIn("clock_shift_min", self.index(0))

    def test_page_reads_its_clock_from_the_index(self):
        page = (REPO / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn("new Date(Date.now() + (330 + SHIFT)*60000)", page)
        self.assertIn("SHIFT = Number.isFinite(+ix.clock_shift_min)", page)


if __name__ == "__main__":
    unittest.main()
