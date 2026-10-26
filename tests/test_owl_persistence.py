"""Persist nightly changes in the authoritative day file, including same-day writes."""
import copy
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox
from world.world import at_dt

SAT = date(2026, 10, 3)


class RevisingOwl:
    def __init__(self, times=("10:35",)):
        self.times = times

    def chat(self, messages, schema=None, **kwargs):
        out = dict(diary="I considered the morning's difficulty, and it left my judgment less certain than before. " * 2,
                   revision_log="The India thesis was shaken by the recorded difficulty.",
                   theses=[dict(id="india", status="shaken", evidence=list(self.times))])
        if "depesche" in (schema or {}).get("properties", {}):
            out["depesche"] = "Readers in Berlin,\nI record the difficulty without pretending it is settled.\nG. W. F. Hegel"
        return json.dumps(out)


class OwlPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.engine = self.box.engine()
        self.engine.owl_mind = RevisingOwl()
        self.day = self.engine.new_day(self.box.days.load(date(2026, 10, 2)), SAT)
        thoughts = [dict(k="diary", t=f"{5 + i // 6:02d}:{(i % 6) * 10 + 1:02d}", text=f"A thought of the morning, number {i}.") for i in range(30)]
        self.day.update(complete=True, entries=[dict(k="diary", t="10:35", text="This difficulty shakes my judgment.")] + thoughts,
                        segments=[dict(mode="stand", at="home", **{"from": "00:00", "to": "24:00"})])            # a full day: above the floor
        self.day["state"]["until"] = at_dt(SAT + timedelta(days=1), 0).isoformat(timespec="minutes")
        self.day["state"]["theses"][0]["status"] = "unshaken"
        self.day["state"]["depesche_n"] = 0
        self.box.days.save(self.day)

    def tearDown(self):
        self.box.close()

    def write(self):
        self.engine.run_owl(self.box.days.load(SAT), at_dt(SAT + timedelta(days=1), 90))

    def test_same_day_revision_survives_reload(self):
        self.write()
        saved = self.box.days.load(SAT)
        self.assertEqual(saved["owl"]["theses"][0]["to"], "shaken")
        self.assertEqual(saved["state"]["theses"][0]["status"], "shaken")

    def test_same_day_depesche_number_survives_reload(self):
        self.write()
        saved = self.box.days.load(SAT)
        self.assertEqual(saved["owl"]["depesche"]["n"], 1)
        self.assertEqual(saved["state"]["depesche_n"], 1)

    def test_next_day_inherits_nightly_revision_and_number(self):
        self.write()
        next_day = self.box.engine().new_day(self.box.days.load(SAT), SAT + timedelta(days=1))
        self.assertEqual(next_day["state"]["theses"][0]["status"], "shaken")
        self.assertEqual(next_day["state"]["depesche_n"], 1)

    def test_later_day_owns_revision_without_rewriting_historical_state(self):
        later = self.engine.new_day(self.box.days.load(SAT), SAT + timedelta(days=1))
        self.box.days.save(later)
        self.write()
        historical, latest = self.box.days.load(SAT), self.box.days.load(SAT + timedelta(days=1))
        self.assertEqual(historical["state"]["theses"][0]["status"], "unshaken")
        self.assertEqual(latest["state"]["theses"][0]["status"], "shaken")
        self.assertEqual(latest["state"]["depesche_n"], 1)
        self.assertIn("owl", historical)
        self.assertFalse(latest.get("owl"))

    def test_missing_evidence_does_not_change_status(self):
        self.engine.owl_mind = RevisingOwl(("18:00",))
        self.write()
        saved = self.box.days.load(SAT)
        self.assertEqual(saved["state"]["theses"][0]["status"], "unshaken")
        self.assertEqual(saved["owl"]["theses"], [])


if __name__ == "__main__":
    unittest.main()


class ThesisFloorTest(unittest.TestCase):
    """Day 24 (25 October) had 5 thoughts and 29 steps without a mind, and its owl moved 'state' to shaken.
    A day with fewer of his own thoughts than T10 measures (20) moves no thesis; the owl is told so."""

    def setUp(self):
        self.box = Sandbox()
        self.engine = self.box.engine()
        self.owl = RevisingOwl()
        self.asked = []
        chat = self.owl.chat
        self.owl.chat = lambda messages, schema=None, **kw: (self.asked.append(messages[-1]["content"]), chat(messages, schema, **kw))[1]
        self.engine.owl_mind = self.owl

    def tearDown(self):
        self.box.close()

    def night(self, n_thoughts):
        day = self.engine.new_day(self.box.days.load(date(2026, 10, 2)), SAT)
        entries = [dict(k="diary", t="10:35", text="This difficulty shakes my judgment.")]
        entries += [dict(k="diary", t=f"{5 + i // 6:02d}:{(i % 6) * 10 + 1:02d}", text=f"Thought {i}.") for i in range(n_thoughts - 1)]
        day.update(complete=True, entries=entries, segments=[dict(mode="stand", at="home", **{"from": "00:00", "to": "24:00"})])
        day["state"]["until"] = at_dt(SAT + timedelta(days=1), 0).isoformat(timespec="minutes")
        day["state"]["theses"][0]["status"] = "unshaken"
        self.box.days.save(day)
        self.engine.run_owl(self.box.days.load(SAT), at_dt(SAT + timedelta(days=1), 90))
        return self.box.days.load(SAT)

    def test_a_thin_day_moves_no_thesis_and_the_owl_is_told(self):
        with self.assertLogs("world", "WARNING") as logs:
            saved = self.night(5)
        self.assertEqual(saved["owl"]["theses"], [])
        self.assertEqual(saved["state"]["theses"][0]["status"], "unshaken")
        self.assertEqual(saved["owl"]["theses_held"], {"thoughts": 5, "floor": 20})
        self.assertIn("moves no thesis", " ".join(logs.output))
        self.assertIn("Today he had 5 thoughts of his own, fewer than 20: tonight no thesis changes its status.", self.asked[-1])
        self.assertTrue(saved["owl"]["diary"])                                        # the night is still written up

    def test_a_full_day_moves_a_thesis_on_evidence(self):
        saved = self.night(30)
        self.assertEqual([(c["id"], c["from"], c["to"]) for c in saved["owl"]["theses"]], [("india", "unshaken", "shaken")])
        self.assertNotIn("theses_held", saved["owl"])
        self.assertNotIn("fewer than 20", self.asked[-1])
