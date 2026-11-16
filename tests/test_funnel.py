"""A2: the day file counts, for each offer and beat, whether it was live, eligible, shown, and the answer to its choice."""
import copy
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_opened  # noqa: E402
from test_world import Sandbox, state  # noqa: E402

from world.world import World, at_dt  # noqa: E402

KEYS = {"live", "eligible", "shown", "yes", "no"}


class FunnelTest(unittest.TestCase):
    def test_a_fired_offer_with_a_yes(self):
        found = [(day["date"], i, f) for day in test_opened.run() for i, f in day["funnel"].items() if f["yes"]]
        self.assertTrue(found, "no offer was answered yes in ten days")
        for d, i, f in found:
            self.assertEqual((f["live"], f["shown"], f["yes"], f["no"]), (1, 1, 1, 0), (d, i, f))
            self.assertGreaterEqual(f["eligible"], 1, (d, i, f))
        self.assertIn("sell_frock", {i for _, i, _ in found})

    def test_counts_are_consistent(self):
        for day in test_opened.run():
            fired = {s["beat"] for s in day["steps"] if s.get("beat")}
            for i, f in day["funnel"].items():
                self.assertEqual(set(f), KEYS)
                self.assertTrue(any(f.values()), (day["date"], i))
                self.assertIn(f["live"], (0, 1))
                self.assertLessEqual(f["shown"], 1)
                self.assertLessEqual(f["yes"] + f["no"], f["shown"])
                self.assertLessEqual(f["shown"], f["eligible"])
                if f["eligible"]:
                    self.assertEqual(f["live"], 1)
                self.assertEqual(bool(f["shown"]), any(b.split("@")[0] == i for b in fired), (day["date"], i, fired))

    def test_a_beat_that_never_could_is_not_there(self):
        for day in test_opened.run():
            for i in day["funnel"]:
                self.assertNotIn(i, ("sell_frock",) if day["date"] < "2026-10-06" else ())

    def test_eligible_changes_nothing(self):
        """eligible() makes the books on first need (ledger) and nothing else: a state read by it is the state it was."""
        w = World()
        st = state()
        t = at_dt(date(2026, 10, 12), 600)
        w.ledger(st)                                   # the books, made once
        before = copy.deepcopy(st)
        for b in w.beats:
            for pid in (None, "home", "khan"):
                w.eligible(b, t, st, pid)
                w.eligible(b, t, st, pid, timed=False, placed=False)
        self.assertEqual(st, before)

    def test_a_month_is_not_slower(self):
        """Counting reads each offer once a moment: a thirty-day rehearsal stays in the seconds it was."""
        import time
        box = Sandbox()
        try:
            e, t0 = box.engine(), time.time()
            for i in range(30):
                box.run_day(date(2026, 10, 3) + timedelta(days=i), e)
            took = time.time() - t0
        finally:
            box.close()
        self.assertLess(took, 120, f"thirty days took {took:.0f}s")


if __name__ == "__main__":
    unittest.main()
