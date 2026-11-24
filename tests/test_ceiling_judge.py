"""tools/ceiling_judge.py: blind pairs both ways round, sealed judgments, and the reads declared before the run."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import ceiling_judge as cj

ARMS = ("A", "A2", "B", "C", "D", "F")
N = 6


def reply(arm, brief):
    return json.dumps({"title": f"On the matter {brief}", "kind": "essay", "to": None, "continues": False, "text": f"PIECE-{arm}-{brief} argues."})


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.f, self.k = Path(self.td.name) / "F", Path(self.td.name) / "keys"
        self.f.mkdir()
        ids = [f"b{i:02d}" for i in range(1, N + 1)]
        (self.f / "BRIEFS.json").write_text(json.dumps([{"id": b, "date": "2026-11-20", "headline": f"Headline {b}"} for b in ids]))
        (self.f / "TEXTS.json").write_text(json.dumps({b: {"title": f"Article {b}", "text": f"The article on {b}."} for b in ids}))
        local = [{"id": f"{a}|{b}", "reply": reply(a, b)} for b in ids for a in ARMS[:5]]
        local[0]["reply"] = "not the writing object"                                  # A|b01 is unusable
        (self.f / "REPLIES-ceiling-1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in local))
        (self.f / "REPLIES-F.jsonl").write_text("".join(json.dumps({"id": f"F|{b}", "reply": reply("F", b)}) + "\n" for b in ids))
        self.res = cj.cmd_sheet(self.f, self.k)
        self.key = json.loads((self.k / "KEY.json").read_text())
        self.sheet = cj.rows(self.f / "SHEET.jsonl")

    def tearDown(self):
        self.td.cleanup()

    def judge(self, name, pick):
        """A reader who answers each row by pick(key row) -> the arm it names on q1, or None."""
        out = []
        for r in self.sheet:
            k = self.key[r["pair"]]
            arm = pick(k)
            out.append({"pair": r["pair"], "q1": "X" if k["X"] == arm else "Y" if k["Y"] == arm else "neither", "q2": "both"})
        p = Path(self.td.name) / name
        p.write_text("".join(json.dumps(x) + "\n" for x in out))
        return p

    def test_every_pair_is_there_twice_and_a_brief_without_a_piece_is_left_out_of_its_pairs(self):
        self.assertEqual(self.res["rows"], 2 * (N * len(cj.PAIRS) - 5))               # b01 has no A: its five pairs with A are gone
        self.assertEqual(sorted(self.res["pairs_lacking_a_piece"]), sorted(f"A-{x}|b01" for x in ("A2", "B", "C", "D", "F")))
        ways = {}
        for pid, k in self.key.items():
            ways.setdefault((k["brief"], k["first"], k["second"]), []).append((k["X"], k["Y"]))
        self.assertTrue(all(len(v) == 2 and v[0] == v[1][::-1] for v in ways.values()))
        row = self.sheet[0]
        self.assertEqual(set(row), {"pair", "headline", "about", "text", "X", "Y"})   # nothing in a row says which arm is which
        self.assertTrue(row["X"].startswith("On the matter"))
        self.assertFalse(any(p.name.startswith("KEY") for p in self.f.iterdir()))     # the key is outside the folder

    def test_welts_rows_are_a_fixed_draw_one_way_round(self):
        welt = cj.rows(self.f / "WELT-24.jsonl")
        self.assertEqual(len(welt), 24)
        self.assertTrue(all(self.key[r["pair"]]["X"] == self.key[r["pair"]]["first"] for r in welt))
        again = cj.cmd_sheet(self.f, self.k)
        self.assertEqual((again["sheet_sha256"], again["welt_sha256"], again["key_sha256"]),
                         (self.res["sheet_sha256"], self.res["welt_sha256"], self.res["key_sha256"]))

    def test_a_judgment_must_be_sealed_before_it_is_scored_and_is_not_changed_after(self):
        j = self.judge("reader-1.jsonl", lambda k: k["second"])
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, [j])
        cj.cmd_seal(self.f, [j])
        cj.cmd_score(self.f, self.k, [j])
        j.write_text(j.read_text().replace('"q2": "both"', '"q2": "neither"', 1))
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, [j])
        with self.assertRaises(ValueError):
            cj.cmd_seal(self.f, [j])

    def test_a_win_needs_the_same_arm_both_ways_round(self):
        first_way_only = lambda k: k["second"] if k["X"] == k["first"] else None       # names the second arm one way round only
        j = self.judge("reader-1.jsonl", first_way_only)
        cj.cmd_seal(self.f, [j])
        t = cj.cmd_score(self.f, self.k, [j])["readers"]["reader-1.jsonl"]["tally"]
        self.assertEqual((t["A-D"]["D"], t["A-D"]["A"], t["A-D"]["none"], t["A-D"]["briefs"]), (0, 0, 5, 5))

    def test_the_pipeline_is_the_ceiling_when_d_wins_outside_the_band(self):
        pick = lambda k: {("A", "A2"): None, ("A", "B"): "B", ("A", "C"): None, ("A", "D"): "D", ("D", "F"): "F", ("A", "F"): "F"}[(k["first"], k["second"])]
        j1, j2 = self.judge("reader-1.jsonl", pick), self.judge("reader-2.jsonl", pick)
        cj.cmd_seal(self.f, [j1, j2])
        res = cj.cmd_score(self.f, self.k, [j1, j2])
        r = res["readers"]["reader-1.jsonl"]
        self.assertEqual((r["tally"]["A-D"]["D"], r["reads"]["needed"]["A-D"], r["reads"]["band_A2_over_A"]), (5, 4, 0))
        self.assertTrue(r["reads"]["D_over_A_outside_the_band"] and r["reads"]["B_over_A_outside_the_band"])
        self.assertFalse(r["reads"]["C_over_A_outside_the_band"])
        self.assertTrue(res["verdict"].startswith("The pipeline is the ceiling"))
        self.assertEqual(res["agreement"]["reader-1.jsonl / reader-2.jsonl"], {"compared": 31, "same": 31})
        self.assertEqual(r["kept_1831"]["A"], {"shown": 50, "named": 50})             # five pairs with A, five briefs, both ways round
        self.assertIn("| A and D | 5 | 0 | 5 | 0 | 4 |", (self.f / "RESULT.md").read_text())

    def test_the_model_is_the_ceiling_when_d_stays_in_the_band_and_f_wins(self):
        pick = lambda k: "F" if "F" in (k["first"], k["second"]) else "A2" if k["second"] == "A2" else k["second"]
        j = self.judge("reader-1.jsonl", pick)                                        # every second arm wins, A2 too: D is inside the band
        cj.cmd_seal(self.f, [j])
        res = cj.cmd_score(self.f, self.k, [j])
        self.assertFalse(res["readers"]["reader-1.jsonl"]["reads"]["D_over_A_outside_the_band"])
        self.assertTrue(res["verdict"].startswith("The 27B is the ceiling"))

    def test_the_measure_is_the_ceiling_when_readers_disagree_or_f_does_not_win(self):
        a = self.judge("reader-1.jsonl", lambda k: "D" if (k["first"], k["second"]) == ("A", "D") else "F" if k["second"] == "F" else None)
        b = self.judge("reader-2.jsonl", lambda k: "F" if k["second"] == "F" else None)
        cj.cmd_seal(self.f, [a, b])
        self.assertTrue(cj.cmd_score(self.f, self.k, [a, b])["verdict"].startswith("The measure is the ceiling"))
        c = self.judge("reader-3.jsonl", lambda k: None)                              # nobody ever wins
        cj.cmd_seal(self.f, [c])
        self.assertTrue(cj.cmd_score(self.f, self.k, [c])["verdict"].startswith("The measure is the ceiling"))

    def test_an_answer_outside_the_form_is_refused(self):
        j = self.judge("reader-1.jsonl", lambda k: k["second"])
        j.write_text(j.read_text().replace('"q1": "X"', '"q1": "the first"', 1))
        cj.cmd_seal(self.f, [j])
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, [j])


if __name__ == "__main__":
    unittest.main()
