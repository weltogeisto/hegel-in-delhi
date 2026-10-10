"""Synthetic fixtures only: never exported to training data."""
import copy
import unittest
from datetime import date

from world.memory import Memory, encountered_text, record_text
from world import contract
from world.world import World
from test_world import Sandbox


class EvidenceMemoryTest(unittest.TestCase):
    def test_self_generated_claims_do_not_grant_exposure(self):
        day = {"entries": [
            {"k": "diary", "text": "Marx told me about Freud."},
            {"k": "writing", "text": "A television is in my room."},
            {"k": "plan", "items": [{"intention": "Study Darwin"}]},
            {"k": "said", "text": "I already know the internet."},
        ], "steps": [{"decision": {"thought": "Einstein"}, "mind": {"raw": "Hitler"}}],
            "owl": {"diary": "I met Gandhi."}}
        before = copy.deepcopy(day)
        self.assertIn("Marx", record_text(day))
        self.assertEqual(encountered_text(day).strip(), "")
        self.assertEqual(day, before)

    def test_observed_received_and_shown_material_counts(self):
        day = {"entries": [
            {"k": "world", "text": "A sign says television."},
            {"k": "said", "by": "Nidhi", "to": "Hegel", "text": "Marx studied your work."},
            {"k": "read", "title": "Darwin", "text": "A dated article."},
        ], "steps": [{"event": "A visitor mentions Gandhi.", "shelf_exposure": [{"text": "An actual excerpt."}]}]}
        for text in ("television", "Marx", "Darwin", "Gandhi", "actual excerpt"):
            self.assertIn(text, encountered_text(day))

    def test_recalled_thought_cannot_bypass_gate_but_current_event_can(self):
        box = Sandbox()
        try:
            mem = Memory(box.days, World())
            sit = {"day": "Monday", "time": "10:00", "place": "home", "weather": "hot", "aqi": 70,
                   "outfit": "coat", "imprest_left": 100, "present": [], "open_now": ["home"],
                   "event": "A quiet morning.", "remember": ["I thought of Marx."],
                   "earlier": ["Marx came yesterday."], "on_mind": ["My thesis concerns Marx."]}
            day = {"date": "2026-10-03", "entries": [], "steps": []}
            self.assertNotIn("Marx", mem.known_text(day, sit))
            sit["event"] = "Nidhi mentions Marx in conversation."
            self.assertIn("Marx", mem.known_text(day, sit))
        finally:
            box.close()

    def test_source_corrections_refresh_cache_and_deletion_drops_exposure(self):
        box = Sandbox()
        try:
            day = box.days.load(date(2026, 10, 2))
            mem = Memory(box.days, World())
            self.assertNotIn("Darwin", mem.known_before("2026-10-03"))
            day["entries"].append({"k": "read", "t": "20:00", "text": "Darwin"})
            box.days.save(day)
            self.assertIn("Darwin", mem.known_before("2026-10-03"))
            day["entries"].pop()
            box.days.save(day)
            self.assertNotIn("Darwin", mem.known_before("2026-10-03"))
        finally:
            box.close()


if __name__ == '__main__':
    unittest.main()
