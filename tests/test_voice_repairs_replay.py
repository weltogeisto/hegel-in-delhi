"""tools/voice_repairs_replay.py on a small day written here: what it rebuilds, what it counts, what it leaves out."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import voice_repairs_replay as vr  # noqa: E402

HEGDE, RAMESH = "Shri G. Hegde", "Ramesh, the caretaker"
DAY = {
    "n": 47, "date": "2026-11-17",
    "segments": [{"from": "09:00", "to": "12:00", "at": "home"}, {"from": "12:00", "to": "13:00", "mode": "walk", "a": "home", "b": "iic"},
                 {"from": "13:00", "to": "15:00", "at": "iic"}],
    "entries": [{"k": "said", "by": "Shri G. Hegde", "to": "Hegel", "text": "Hegde ji?", "t": "09:47"}],
    "steps": [
        {"t": "09:47", "present": [RAMESH, HEGDE], "decision": {"says": "Good morning.", "speaks_to": None},
         "voice": {"by": "Ramesh", "says": "Ji.", "does": None}},                                    # off: Ramesh (first present); on: the greeter
        {"t": "10:02", "present": [RAMESH, HEGDE], "decision": {"says": "Ramesh, thank you. Shri Hegde, a word about the vouchers."},
         "voice": {"by": "Ramesh", "says": "Ji.", "does": "I wipe the table."}},                      # named: Hegde has the longer stretch
        {"t": "10:17", "present": [RAMESH, HEGDE], "decision": {"says": "Ramesh, tea."},
         "voice": {"by": "Shri G. Hegde", "says": "No.", "does": "She sighs."}},                      # off gives Ramesh: not reproducible
        {"t": "13:04", "present": ["the guard at the library", "the programme officer"], "decision": {"says": "Thank you."},
         "voice": {"by": "The guard at the library", "says": "Sir.", "does": None}},
    ],
}


class Replay(unittest.TestCase):
    def setUp(self):
        self.res = vr.Replay().run([DAY])

    def test_counts(self):
        d = self.res["days"][0]
        self.assertEqual((d["replies"], d["reproducible"], d["changed"], d["dropped"], d["greetings"]), (4, 3, 2, 2, 1))
        self.assertEqual([x["t"] for x in self.res["unreproducible"]], ["10:17"])

    def test_greeting_inferred_from_the_entries(self):
        r = self.res["changed"][0]
        self.assertEqual((r["t"], r["recorded"], r["new"], r["rule"], r["greeting_held"]), ("09:47", "Ramesh", "hegde", "greeting", False))
        self.assertFalse(r["names_a_present"])

    def test_named_move_is_marked(self):
        r = self.res["changed"][1]
        self.assertEqual((r["t"], r["new"], r["rule"]), ("10:02", "hegde", "named"))
        self.assertTrue(r["names_a_present"] and r["new_is_named"] and r["recorded_is_named"])

    def test_dropped_does(self):
        self.assertEqual([(x["t"], x["kind"]) for x in self.res["dropped"]], [("10:02", "first person"), ("10:17", "wrong pronoun")])

    def test_last_spoken_is_read_from_earlier_entries_only(self):
        f = vr.Replay().facts(DAY, 0)
        self.assertEqual(f["entries"], [])
        self.assertEqual(vr.Replay().facts(DAY, 1)["entries"][0]["by"], "Shri G. Hegde")

    def test_cli_writes_json_and_table_from_a_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs, out = Path(tmp, "docs"), Path(tmp, "out")
            docs.mkdir()
            (docs / "2026-11-17.json").write_text(json.dumps(DAY), encoding="utf-8")
            vr.main(["--docs", str(docs), "--days", "47", "--out", str(out)])
            res = json.loads((out / "replay.json").read_text(encoding="utf-8"))
            self.assertEqual(res["days"][0]["changed"], 2)
            self.assertIn("| 47 | 2026-11-17 | 4 | 1 | 3 | 2 | 2 |", (out / "replay.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
