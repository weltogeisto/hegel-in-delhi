"""A pause for his world when the PC is away (HEGEL_PAUSE_AWAY, world/pause.py, pc/PAUSE.md)."""
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox  # noqa: E402

from world import pause  # noqa: E402
from world.clock import IST, at_dt  # noqa: E402
from world.config import Config  # noqa: E402
from world.mind import MindAway, StubMind  # noqa: E402

DAY1 = date(2026, 10, 3)


class Away(StubMind):
    def ensure_awake(self):
        raise MindAway("no answer from the PC")


class Pause(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.box.cfg.base_shift_min = 0
        self.engine = self.box.engine()
        self.box.run_day(DAY1, self.engine)                      # a full first day; the next begins asleep

    def at(self, d, minute):
        return at_dt(d, minute).astimezone(IST)

    def test_the_switch_is_off_until_set_and_keeps_no_trail_until_it_holds(self):
        self.assertFalse(Config({}).pause_away)
        self.assertTrue(Config({"HEGEL_PAUSE_AWAY": "1"}).pause_away)
        self.assertEqual(pause.lag_min(self.box.cfg), 0)

    def test_only_his_waking_asks_for_the_pc(self):
        d2 = DAY1 + timedelta(days=1)
        self.assertFalse(pause.needs_wake(self.engine, self.at(d2, 120)))            # the night: nothing is due
        wake = self.engine.world.wake_time(d2)
        self.assertTrue(pause.needs_wake(self.engine, self.at(d2, wake)))

    def test_held_at_waking_then_resumed_on_the_held_day_with_whole_days_of_trail(self):
        d2 = DAY1 + timedelta(days=1)
        wake = self.engine.world.wake_time(d2)
        cfg = self.box.cfg
        self.assertIsNone(pause.gate(cfg, self.engine, Away(), self.at(d2, wake)))
        held = pause.load(cfg)
        self.assertEqual(held["held"], d2.isoformat())
        self.assertIsNone(pause.gate(cfg, self.engine, Away(), self.at(d2 + timedelta(days=2), 600)))
        self.assertEqual(self.engine.days.latest()["date"], d2.isoformat())        # nothing ran while it was held
        now = pause.gate(cfg, self.engine, StubMind(), self.at(d2 + timedelta(days=3), 480))
        self.assertEqual(now.date(), d2)
        self.assertEqual((now.hour, now.minute), (8, 0))                         # the same hour as Delhi's, three days back
        data = pause.load(cfg)
        self.assertEqual((data["lag_days"], data["held"]), (3, None))
        self.assertEqual(data["history"][0]["lag_days"], 3)
        self.assertEqual(self.engine.days.shift_min, -3 * 1440)
        self.engine.tick(self.at(d2, wake + 30))
        day = self.engine.days.load(d2)
        self.assertTrue(any("decision" in s and s["t"] >= f"{wake // 60:02d}" for s in day["steps"]))
        self.assertEqual(json.loads((self.box.cfg.docs / "days/index.json").read_text())["clock_shift_min"], -3 * 1440)

    def test_back_the_same_morning_he_wakes_late_and_nothing_trails(self):
        d2 = DAY1 + timedelta(days=1)
        wake = self.engine.world.wake_time(d2)
        cfg = self.box.cfg
        self.assertIsNone(pause.gate(cfg, self.engine, Away(), self.at(d2, wake)))
        now = pause.gate(cfg, self.engine, StubMind(), self.at(d2, 660))
        self.assertEqual(now, self.at(d2, 660))
        self.assertEqual(pause.load(cfg)["lag_days"], 0)
        self.engine.tick(now)
        day = self.engine.days.load(d2)
        self.assertTrue(any(s.get("resumed") for s in day["steps"]))

    def test_with_the_pc_there_the_gate_is_only_the_clock(self):
        d2 = DAY1 + timedelta(days=1)
        wake = self.engine.world.wake_time(d2)
        self.assertEqual(pause.gate(self.box.cfg, self.engine, StubMind(), self.at(d2, wake)), self.at(d2, wake))
        self.assertFalse(pause.path(self.box.cfg).exists())

    def test_apply_reads_the_trail_into_the_clock_shift(self):
        cfg = self.box.cfg
        cfg.clock_shift_min = 15
        pause.save(cfg, {"lag_days": 2, "held": None, "since": None, "history": []})
        pause.apply(cfg)
        self.assertEqual((cfg.base_shift_min, cfg.clock_shift_min), (15, 15 - 2 * 1440))


if __name__ == "__main__":
    unittest.main()
