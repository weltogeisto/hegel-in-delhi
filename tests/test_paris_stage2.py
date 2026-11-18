"""Paris stage 2 (tools/paris_stage2.py, DECISIONS.md 55): the travel version of his instructions carries nothing of
Delhi or of his death, and the frozen requests are what the declaration says."""
import json
import sys
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "tools"))
import paris_stage2  # noqa: E402

F = R / "pc/exports/paris-stage2-20261118"


class Stage2Test(unittest.TestCase):
    def test_the_travel_instructions_hold_nothing_of_delhi_or_his_death(self):
        text = paris_stage2.SOUL.read_text(encoding="utf-8")
        for journey, year in paris_stage2.YEAR.items():
            with self.subTest(journey=journey):
                soul = paris_stage2.travel_soul(text, journey)
                for word in ("Delhi", "Hindi", "2026", "bungalow", "died", "1831", "Hegde"):
                    self.assertNotIn(word, soul)
                self.assertIn(f"It is {year}", soul)
                self.assertIn("Marie", soul)
                self.assertEqual(soul, (F / f"soul-{year}.md").read_text(encoding="utf-8"))

    def test_the_frozen_requests_are_three_letters_and_a_translation_per_card(self):
        cards = [json.loads(l) for l in (F / "CARDS.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        reqs = [json.loads(l) for l in (F / "REQUESTS.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(cards), 24)
        self.assertEqual(sum(1 for c in cards if c["journey"] == "Paris 1827"), 8)
        self.assertEqual(len(reqs), 96)
        for c in cards:
            with self.subTest(card=c["id"]):
                self.assertLessEqual(len(c["card"].split()), 60)
                self.assertEqual(sorted(r["params"]["seed"] for r in reqs if r["id"].startswith(f"letter|{c['id']}|")), [1831, 2718, 3141])
                self.assertEqual(sum(1 for r in reqs if r["id"] == f"translate|{c['id']}"), 1)
        self.assertTrue(all(r["params"]["cache_prompt"] is False for r in reqs))


if __name__ == "__main__":
    unittest.main()
