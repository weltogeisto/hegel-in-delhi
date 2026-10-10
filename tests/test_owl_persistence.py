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
        self.day.update(complete=True, entries=[dict(k="diary", t="10:35", text="This difficulty shakes my judgment.")],
                        segments=[dict(mode="stand", at="home", **{"from": "00:00", "to": "24:00"})])
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
