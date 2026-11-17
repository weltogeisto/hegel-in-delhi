"""Museums, concerts and plays (HEGEL_CULTURE, world/data/culture.json, pc/CULTURE.md)."""
import json
import sys
import unittest
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox  # noqa: E402

from world import contract  # noqa: E402
from world.clock import at_dt  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World  # noqa: E402

MON, SAT = date(2026, 11, 16), date(2026, 11, 21)
VENUES = ["national_museum", "ngma", "habitat", "kamani"]


class Off(unittest.TestCase):
    def test_the_switch_is_off_until_set(self):
        self.assertFalse(Config({}).culture)
        self.assertTrue(Config({"HEGEL_CULTURE": "1"}).culture)

    def test_without_it_the_world_and_the_schema_are_what_they_were(self):
        w = World()
        self.assertEqual(list(w.places), contract.PLACES)
        self.assertIs(contract.decision_schema(None), contract.SCHEMA)
        self.assertIs(contract.decision_schema({"places": contract.PLACES}), contract.SCHEMA)
        self.assertIs(contract.decision_schema({"id": "x", "time": "09:00"}), contract.SCHEMA)
        ans = {"thought": "A thought long enough to pass the check.", "action": "walk", "place": "habitat", "minutes": 30,
               "says": None, "buys": [], "revision": None}
        self.assertIn("unknown place 'habitat'", contract.check_shape(ans)[0])

    def test_a_day_renders_byte_for_byte_with_the_switch_off(self):
        a, b = Sandbox(), Sandbox()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        e1 = a.engine()
        e2 = Engine(b.cfg, World(culture=False), StubMind())
        e2.lookup = e1.lookup
        d1, d2 = a.run_day(date(2026, 10, 3), e1), b.run_day(date(2026, 10, 3), e2)
        self.assertEqual(json.dumps(d1["steps"], sort_keys=True), json.dumps(d2["steps"], sort_keys=True))
        self.assertTrue(all("places" not in (s.get("situation") or {}) for s in d1["steps"]))


class On(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = World(culture=True)

    def test_the_venues_join_the_places_and_every_pair_has_a_walk(self):
        self.assertEqual(list(self.w.places)[:8], contract.PLACES)
        self.assertEqual(list(self.w.places)[8:], VENUES)
        for a, b in combinations(self.w.places, 2):
            self.assertGreaterEqual(self.w.walk(a, b), 5, (a, b))
        self.assertEqual(self.w.walk("home", "habitat"), 24)
        self.assertEqual(self.w.walk("lodhi", "habitat"), 12)

    def test_the_schema_and_the_check_take_the_venues(self):
        schema = contract.decision_schema({"places": list(self.w.places)})
        self.assertEqual(schema["properties"]["place"]["enum"][-4:], VENUES)
        self.assertEqual(contract.SCHEMA["properties"]["place"]["enum"], contract.PLACES)      # the original is untouched
        ans = {"thought": "A thought long enough to pass the check.", "action": "walk", "place": "ngma", "minutes": 30,
               "says": None, "buys": [], "revision": None}
        self.assertEqual(contract.check_shape(ans, list(self.w.places))[0], [])

    def test_the_listings_say_what_is_on_and_when_the_museums_open(self):
        mon, sat = self.w.listings(MON), self.w.listings(SAT)
        self.assertIn("raga Yaman, free", mon)
        self.assertNotIn("Open today", mon)                 # the museums are closed on Mondays
        self.assertIn("Kathak", sat)
        self.assertIn("Rossini", sat)
        self.assertIn("₹300", sat)
        self.assertIn("the National Museum 10:00 to 18:00", sat)
        self.assertLess(sat.index("17:00"), sat.index("18:30"))

    def test_sights_come_one_at_a_time_in_an_order_fixed_for_the_day(self):
        n = len(self.w.places["national_museum"]["sights"])
        today = {}
        seen = [self.w.sight("national_museum", SAT, today) for _ in range(n)]
        self.assertEqual(len(set(seen)), n)
        self.assertIsNone(self.w.sight("national_museum", SAT, today))
        again = {}
        self.assertEqual(self.w.sight("national_museum", SAT, again), seen[0])
        self.assertNotEqual([self.w.sight("national_museum", SAT + timedelta(days=7), {}) for _ in range(1)], [None])

    def test_a_performance_announces_itself_then_runs_part_by_part(self):
        today = {}
        before = self.w.on_stage("habitat", at_dt(MON, 18 * 60), today)
        self.assertIn("Tonight here", before)
        first = self.w.on_stage("habitat", at_dt(MON, 18 * 60 + 30), today)
        self.assertTrue(first.startswith("The recital begins"))
        self.assertIn("goes on", self.w.on_stage("habitat", at_dt(MON, 18 * 60 + 35), today))
        last = self.w.on_stage("habitat", at_dt(MON, 19 * 60 + 50), today)
        self.assertTrue(last.startswith("The recital ends"))
        self.assertIsNone(self.w.on_stage("habitat", at_dt(MON, 20 * 60 + 5), today))
        self.assertIsNone(self.w.on_stage("kamani", at_dt(MON, 18 * 60 + 40), {}))

    def test_every_performance_ends_before_bedtime_and_names_no_living_person(self):
        for pid in VENUES:
            for e in self.w.places[pid].get("programme", []):
                self.assertLessEqual(e["to"], "20:30", e["title"])
                self.assertEqual(len(e["parts"]), 4)
        text = json.dumps(json.loads((Path(__file__).resolve().parents[1] / "world/data/culture.json").read_text(encoding="utf-8")))
        for name in ("Pandit", "Ustad", "Shrimati", "Smt."):
            self.assertNotIn(name, text)


class Visit(unittest.TestCase):
    """A mind that goes to the museum, buys a ticket, and looks."""

    def test_a_day_at_the_museum(self):
        box = Sandbox()
        self.addCleanup(box.close)

        class Museum(StubMind):
            def decide(self, messages, sit):
                if "national_museum" in sit["open_now"] and sit["place"] != "national_museum" and sit["time"] < "15:00":
                    return json.dumps({"thought": "I shall go and see the museum on Janpath this morning.", "action": "walk",
                                       "place": "national_museum", "minutes": 30, "says": None, "buys": [], "revision": None})
                if sit["place"] == "national_museum" and sit["time"] < "15:00":
                    buys = [] if any("Entry ticket" in x for x in sit["on_mind"]) else \
                        [{"item": "Entry ticket, foreign visitors", "price_inr": 650}]
                    return json.dumps({"thought": "I walk on through the galleries and look at what is in front of me.",
                                       "action": "stay", "place": "national_museum", "minutes": 20, "says": None,
                                       "buys": buys, "revision": None})
                return super().decide(messages, sit)

        engine = Engine(box.cfg, World(culture=True), Museum())
        engine.lookup = box.engine().lookup
        day = box.run_day(SAT, engine)
        there = [s for s in day["steps"] if (s.get("decision") or {}).get("place") == "national_museum"]
        self.assertTrue(there)
        self.assertTrue(any("gallery" in s["event"] or "courtyard" in s["event"] for s in day["steps"]))
        self.assertTrue(any(e.get("k") == "world" and str(e.get("text", "")).startswith("Today's listings") for e in day["entries"]))


if __name__ == "__main__":
    unittest.main()
