"""Memories retain the place where a thought occurred, before a requested trip."""
import copy
import json
import unittest
from datetime import date
from pathlib import Path
from world.memory import Memory
from world.world import World, at_dt

class ThoughtLocationTest(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(None, World())

    def day(self, action="walk", segments=None):
        return dict(n=8, date="2026-10-09", entries=[], steps=[
            dict(t="09:00", end="09:10", decision=dict(action=action, place="lodhi",
                 thought="I have not yet left home; the walk is still ahead of me."))],
            segments=segments if segments is not None else [
                dict(**{"from":"09:00", "to":"09:10"}, mode="walk", a="home", b="lodhi")])

    def test_walk_destination_does_not_become_where_he_thought(self):
        day = self.day()
        self.assertEqual(self.memory.place_line("lodhi", [day]), [])
        got = self.memory.place_line("home", [day])
        self.assertEqual(len(got), 1)
        self.assertIn("I have not yet left home", got[0])

    def test_a_reading_decision_can_also_include_a_trip(self):
        day = self.day(action="read")
        day["segments"].append(dict(**{"from":"09:10","to":"09:40"}, mode="inside", at="lodhi"))
        self.assertEqual(self.memory.place_line("lodhi", [day]), [])
        self.assertEqual(len(self.memory.place_line("home", [day])), 1)

    def test_arrival_boundary_uses_the_next_step_location(self):
        day = self.day()
        day["steps"].append(dict(t="09:10", end="09:40",
            decision=dict(action="stay", place="lodhi", thought="Now I am actually beside the bench.")))
        day["segments"].append(dict(**{"from":"09:10","to":"09:40"}, mode="stand", at="lodhi"))
        got = self.memory.place_line("lodhi", [day])
        self.assertEqual(len(got), 1)
        self.assertIn("09:10", got[0])
        self.assertIn("actually beside the bench", got[0])
        self.assertEqual(len(self.memory.place_line("home", [day])), 1)

    def test_an_old_walk_without_location_evidence_is_not_a_visit(self):
        self.assertEqual(self.memory.place_line("lodhi", [self.day(segments=[])]), [])

    def test_legacy_stationary_steps_remain_usable(self):
        day = self.day(action="stay", segments=[])
        self.assertEqual(len(self.memory.place_line("lodhi", [day])), 1)

    def test_checked_world_actions_record_the_thought_before_the_move(self):
        root = Path(__file__).resolve().parents[1]
        original = json.loads((root / "docs/days/2026-10-02.json").read_text())
        for action in ("walk", "read"):
            with self.subTest(action=action):
                world = World()
                st = copy.deepcopy(original["state"])
                st.update(place="home", asleep=False, today={})
                day = dict(n=2, date="2026-10-03", entries=[], steps=[], segments=[])
                sit, ctx = world.situation(at_dt(date(2026, 10, 3), 540), st, day)
                ans = dict(thought="I have not yet left home; the walk is still ahead of me.",
                           action=action, place="lodhi", minutes=30, says=None, buys=[], revision=None)
                errors, warnings, checked = world.check(ans, sit, ctx, st)
                self.assertEqual(errors, [])
                step = world.apply(checked[0], checked[1], sit, ctx, st, day)
                day["steps"].append(step)
                self.assertEqual(st["place"], "lodhi")
                self.assertEqual(day["segments"][0]["a"], "home")
                self.assertEqual(self.memory.place_line("lodhi", [day]), [])
                self.assertEqual(len(self.memory.place_line("home", [day])), 1)

if __name__ == "__main__":
    unittest.main()
