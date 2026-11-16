"""tools/voice_claims.py: a deterministic sample, each item with its context, the right count, no empty `says`."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import voice_claims as vc  # noqa: E402


def step(t, says, voice=None, place="home"):
    s = {"t": t, "end": t, "event": f"Event at {t}.", "present": ["Ramesh"],
         "decision": {"thought": "x", "action": "talk", "place": place, "minutes": 10, "says": says}}
    if voice:
        s["voice"] = voice
    return s


DAY1 = {"format": 1, "n": 1, "date": "2026-10-13",
        "entries": [{"k": "world", "text": "Morning papers.", "t": "06:00"}, {"k": "diary", "text": "PRIVATE", "t": "06:05"},
                    {"k": "said", "by": "Ramesh", "to": "Hegel", "text": "Tea is ready, sir.", "t": "06:10"},
                    {"k": "bag", "item": "Chai", "price": 20, "t": "06:30"}],
        "steps": [step("06:10", "Thank you.", {"by": "Ramesh", "says": "Tea is ready, sir.", "does": None}),
                  step("06:30", "Chai please.", {"by": "Ramesh", "says": "Twenty rupees, sir.", "does": "Ramesh nods."}),
                  step("07:00", "Nothing.")],
        "state": {"imprest": 100, "file": "Open.", "owed": [{"to": "Ramesh", "amount": 8000, "why": "wage", "since": "2026-10-01"}],
                  "people": ["ramesh"], "flags": {"a": 1}, "appointments": [], "engagements": [], "wardrobe": []}}
DAY2 = {"format": 1, "n": 2, "date": "2026-10-14",
        "entries": [{"k": "said", "by": "Sunil", "to": "Hegel", "text": "Oh, it is you.", "t": "08:00"}],
        "steps": [{**step("08:00", "A cup.", {"by": "Sunil", "says": "Ten rupees.", "does": None}),
                   "event": "You arrive. Sunil says: “Oh, it is you.” Sunil grins."},
                  step("09:00", "Hello.", {"by": "Ramesh", "says": "", "does": None})],
        "state": {"imprest": 80}}


class VoiceClaimsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.days = Path(self.tmp.name) / "days"
        self.days.mkdir()
        for d in (DAY1, DAY2):
            (self.days / f"{d['date']}.json").write_text(json.dumps(d), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, name, n=100, seed=1831):
        out = Path(self.tmp.name) / name
        vc.main(["--days", str(self.days), "--n", str(n), "--seed", seed.__str__(), "--out", str(out)])
        return out, [json.loads(l) for l in (out / "sample.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_deterministic(self):
        _, a = self.run_tool("a", n=2)
        _, b = self.run_tool("b", n=2)
        self.assertEqual(a, b)

    def test_item_carries_context(self):
        _, items = self.run_tool("c")
        tea = next(i for i in items if i["says"] == "Twenty rupees, sir.")
        self.assertEqual((tea["date"], tea["day"], tea["t"], tea["place"], tea["by"], tea["kind"]), ("2026-10-13", 1, "06:30", "home", "Ramesh", "reply"))
        self.assertEqual(tea["he_said"], "Chai please.")
        ctx = json.dumps(tea["context"], ensure_ascii=False)
        self.assertIn("Morning papers.", ctx)
        self.assertIn("bought Chai", ctx)
        self.assertNotIn("PRIVATE", ctx)                       # his diary is not the record
        self.assertEqual(tea["context"]["earlier_exchanges"][0]["they_said"], "Tea is ready, sir.")
        later = next(i for i in items if i["says"] == "Ten rupees.")
        self.assertEqual(later["context"]["state_of"], "2026-10-13")
        self.assertIn("owed", later["context"]["state"])

    def test_greeting_found_with_its_does(self):
        _, items = self.run_tool("g")
        g = [i for i in items if i["kind"] == "greeting"]
        self.assertEqual([(i["by"], i["says"], i["does"], i["he_said"]) for i in g], [("Sunil", "Oh, it is you.", "Sunil grins.", None)])

    def test_count_and_no_empty_says(self):
        out, items = self.run_tool("n", n=2)
        self.assertEqual(len(items), 2)
        out, items = self.run_tool("m", n=100)
        pop = json.loads((out / "population.json").read_text(encoding="utf-8"))
        self.assertEqual(len(items), pop["population"])        # n larger than the population: all of it
        self.assertEqual(pop["population"], 4)                 # two greetings/replies per day, the empty `says` left out
        self.assertEqual(pop["replies_recorded"], 5)
        self.assertTrue(all(i["says"].strip() for i in items))
        self.assertEqual([i["id"] for i in items], ["VC001", "VC002", "VC003", "VC004"])
        self.assertTrue((out / "sheet.md").read_text(encoding="utf-8").count("VC00") >= 4)
        self.assertIn("follow-up: yes|no|unknown", (out / "LABELS-TEMPLATE.md").read_text(encoding="utf-8"))

    def test_context_is_compact_and_cuts_are_named(self):
        day = json.loads(json.dumps(DAY1))
        day["entries"] = [{"k": "world", "text": "word " * 40, "t": "05:00"} for _ in range(30)]
        item = {"date": day["date"], "t": "06:10", "by": "Ramesh"}
        c = vc.build_context(item, {day["date"]: day}, [day], [])
        self.assertEqual(c["entries_cut"], 22)
        vc.fit(c)
        self.assertLessEqual(vc.words(vc.context_text(c)), vc.BUDGET_WORDS)
        self.assertIn("more", vc.context_text(c))


if __name__ == "__main__":
    unittest.main()
