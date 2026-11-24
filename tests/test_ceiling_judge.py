"""tools/ceiling_judge.py: blind pairs in two sheets, sealed ballots, calibration pairs, and the reads declared before the run."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import ceiling_judge as cj

ARMS = ("A", "A2", "B", "C", "D", "F")
N = 40


def reply(arm, brief):
    return json.dumps({"title": f"On the matter {brief}", "kind": "essay", "to": None, "continues": False, "text": f"PIECE-{arm}-{brief} argues."})


class Books:
    """A stand-in for his shelf: the same two passages for every search, one of them German."""
    def search(self, parts, n=40):
        return [{"label": "Philosophy of Right §63", "text": "Money represents things. " * 60, "lang": "en"},
                {"label": "Philosophie des Rechts §63", "text": "Das Geld.", "lang": "de"},
                {"label": "Philosophy of History, India", "text": "India.", "lang": "en"},
                {"label": "A third", "text": "x", "lang": "en"}]


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.f, self.k = Path(self.td.name) / "F", Path(self.td.name) / "keys"
        self.f.mkdir()
        self.ids = [f"b{i:02d}" for i in range(1, N + 1)]
        (self.f / "BRIEFS.json").write_text(json.dumps([{"id": b, "date": f"2026-11-{1 + i // 2:02d}", "headline": f"Headline {b}", "object": "a thing"}
                                                        for i, b in enumerate(self.ids)]))                      # twenty mornings, two briefs each
        (self.f / "TEXTS.json").write_text(json.dumps({b: {"title": f"Article {b}", "text": f"The article on {b}."} for b in self.ids}))
        local = [{"id": f"{a}|{b}", "reply": reply(a, b)} for b in self.ids for a in ARMS[:5]]
        (self.f / "REPLIES-ceiling-1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in local))
        (self.f / "REPLIES-F.jsonl").write_text("".join(json.dumps({"id": f"F|{b}", "reply": reply("F", b)}) + "\n" for b in self.ids))

    def tearDown(self):
        self.td.cleanup()

    def sheet(self, controls=0):
        if controls:
            rows = [{"id": f"c{i:02d}", "type": "inference" if i % 2 else "invention", "brief": self.ids[i], "good": f"GOOD-{i}", "bad": f"BAD-{i}"} for i in range(controls)]
            (self.f / "CONTROLS.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.res = cj.cmd_sheet(self.f, self.k, books=Books())
        self.key = json.loads((self.k / "KEY.json").read_text())
        self.sheets = [cj.rows(self.f / "SHEET-1.jsonl"), cj.rows(self.f / "SHEET-2.jsonl")]
        return self.res

    def ballots(self, family, pick, ways=(1, 2), invented=lambda k: "neither"):
        """Ballot files of one family, a file a sheet: pick(key row) -> "first" | "second" | "both" | "neither"."""
        files = []
        for n in ways:
            out = []
            for r in self.sheets[n - 1]:
                k = self.key[r["pair"]]
                want = pick(k)
                arm = {"first": k["first"], "second": k["second"]}.get(want)
                q1 = want if want in ("both", "neither") else "X" if k["X"] == arm else "Y"
                out.append({"pair": r["pair"], "q1": q1, "claim": "" if q1 == "neither" else "the claim", "warrant": "" if q1 == "neither" else "its warrant",
                            "invented": invented(k), "fidelity": "both", "stance_X": "defence", "stance_Y": "revision"})
            p = Path(self.td.name) / f"{family}-{n}.jsonl"
            p.write_text("".join(json.dumps(x) + "\n" for x in out))
            files.append(p)
        return files

    def score(self, **families):
        cj.cmd_seal(self.f, [p for files in families.values() for p in files])
        return cj.cmd_score(self.f, self.k, families)

    def test_every_pair_is_in_both_sheets_once_and_the_other_way_round(self):
        self.sheet()
        self.assertEqual(self.res["rows_a_sheet"], N * len(cj.PAIRS))
        self.assertEqual(len(cj.PAIRS), 8)                                            # B with D and C with D are there too
        both = {}
        for pid, k in self.key.items():
            both.setdefault((k["brief"], k["first"], k["second"]), {})[k["sheet"]] = (k["X"], k["Y"])
        self.assertTrue(all(set(v) == {1, 2} and v[1] == v[2][::-1] for v in both.values()))
        self.assertEqual({r["pair"] for r in self.sheets[0]} & {r["pair"] for r in self.sheets[1]}, set())      # fresh ids in each sheet
        first_is_x = sum(k["X"] == k["first"] for k in self.key.values() if k["sheet"] == 1)
        self.assertTrue(0.3 < first_is_x / (N * 8) < 0.7)                             # which way goes into the first sheet is a draw

    def test_a_row_shows_the_brief_his_books_and_two_pieces_and_nothing_else(self):
        self.sheet()
        row = self.sheets[0][0]
        self.assertEqual(set(row), {"pair", "headline", "about", "text", "his_books", "X", "Y"})
        self.assertEqual([b["from"] for b in row["his_books"]], ["Philosophy of Right §63", "Philosophy of History, India"])      # English, the two nearest
        self.assertLessEqual(len(row["his_books"][0]["text"]), cj.BOOK_CHARS)
        self.assertFalse(any(p.name in ("KEY.json", "SALT") for p in self.f.iterdir()))                      # key and salt are outside the folder
        packet = json.loads((self.f / "PACKET.json").read_text())
        self.assertEqual(set(packet["sha256"]), {"SHEET-1.jsonl", "SHEET-2.jsonl", "WELT-24.jsonl", "KEY.json"})

    def test_the_ids_cannot_be_worked_out_from_the_repository(self):
        self.sheet()
        again = cj.cmd_sheet(self.f, self.k, books=Books())
        self.assertEqual(again["sha256"], self.res["sha256"])                         # the same salt gives the same packet
        other = Path(self.td.name) / "other-keys"
        self.assertNotEqual(cj.cmd_sheet(self.f, other, books=Books())["sha256"]["SHEET-1.jsonl"], self.res["sha256"]["SHEET-1.jsonl"])
        self.assertNotEqual((other / "SALT").read_text(), (self.k / "SALT").read_text())

    def test_welts_rows_are_three_a_comparison_from_one_sheet_without_controls(self):
        self.sheet(controls=8)
        welt = cj.rows(self.f / "WELT-24.jsonl")
        self.assertEqual(len(welt), 24)
        ks = [self.key[r["pair"]] for r in welt]
        self.assertTrue(all(k["sheet"] == 1 and "control" not in k for k in ks))
        self.assertEqual({(k["first"], k["second"]) for k in ks}, set(cj.PAIRS))

    def test_a_sheet_is_read_in_parts_and_each_part_is_all_a_reader_gets(self):
        self.sheet()
        out = Path(self.td.name) / "parts"
        got = cj.cmd_parts(self.f, out)
        self.assertEqual(sum(n for name, n in got.items() if name.startswith("s1-")), len(self.sheets[0]))
        self.assertTrue(all(n <= cj.PART for n in got.values()))
        d = out / "s2-01"
        self.assertEqual(sorted(x.name for x in d.iterdir()), ["PROMPT.md", "check.py", "s2-01.pairs", "s2-01.txt"])
        text, prompt = (d / "s2-01.txt").read_text(), (d / "PROMPT.md").read_text()
        first = self.sheets[1][0]
        self.assertIn(f"pair: {first['pair']}", text)
        self.assertIn(first["X"], text)
        self.assertEqual((d / "s2-01.pairs").read_text().split(), [r["pair"] for r in self.sheets[1][:cj.PART]])
        self.assertIn("`s2-01.txt`", prompt)
        self.assertIn("python3 check.py s2-01", prompt)
        for arm in ARMS:                                                    # nothing a reader gets names an arm
            self.assertNotIn(f'"{arm}"', text + prompt)

    def test_a_changed_sheet_is_not_cut(self):
        self.sheet()
        (self.f / "SHEET-1.jsonl").write_text((self.f / "SHEET-1.jsonl").read_text().replace("PIECE-A-", "PIECE-Z-", 1))
        with self.assertRaises(ValueError):
            cj.cmd_parts(self.f, Path(self.td.name) / "parts")

    def test_the_parts_join_into_a_sheets_ballots_and_a_wrong_part_stops_it(self):
        self.sheet()
        out = Path(self.td.name) / "parts"
        cj.cmd_parts(self.f, out)
        answer = lambda pid: {"pair": pid, "q1": "neither", "claim": "", "warrant": "", "invented": "neither", "fidelity": "both", "stance_X": "none", "stance_Y": "none"}
        for d in out.iterdir():
            (d / f"{d.name}.out.jsonl").write_text("".join(json.dumps(answer(pid)) + "\n" for pid in (d / f"{d.name}.pairs").read_text().split()))
        res = cj.cmd_join(out, "astra")
        self.assertEqual([a["pair"] for a in cj.rows(out / "astra-2.jsonl")], [r["pair"] for r in self.sheets[1]])
        self.assertEqual(res["astra-1.jsonl"]["rows"], len(self.sheets[0]))
        self.score(astra=[out / "astra-1.jsonl", out / "astra-2.jsonl"])
        last = out / "s1-02" / "s1-02.out.jsonl"
        last.write_text("".join(last.read_text().splitlines(True)[:-1]))                # a part one row short
        with self.assertRaises(ValueError):
            cj.cmd_join(out, "astra")

    def test_the_arms_are_counted_beside_the_ballots(self):
        import re
        rows = [{"id": "A|b01", "reply": json.dumps({"title": "Notes", "text": "21 October 2026, 06:16. Delhi. The airport and the internet."})},
                {"id": "A|b02", "reply": json.dumps({"title": "On the thing", "text": "The concept moves."})},
                {"id": "B|b01", "reply": json.dumps({"title": "On it", "text": "The airport serves the city."})}]
        (self.f / "REPLIES-ceiling-1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        (self.f / "REPLIES-F.jsonl").write_text("")
        (self.f / "TEXTS.json").write_text(json.dumps({"b01": {"title": "An airport", "text": "The airport."}, "b02": {"title": "A thing", "text": "A thing."}}))
        got = cj.cmd_counts(self.f, rx=re.compile(r"\b(airport|internet)s?\b", re.I))
        self.assertEqual(got["A"]["pieces"], 2)
        self.assertEqual(got["A"]["opens_like_a_diary"], 1)
        self.assertEqual(got["A"]["century_terms_mean"], 1.0)                 # two terms in one piece, none in the other
        self.assertEqual(got["A"]["pieces_with_a_term_not_shown"], 1)         # "internet": the text gave him only the airport
        self.assertEqual(got["B"]["century_terms_not_shown_mean"], 0.0)

    def test_a_ballot_must_be_sealed_and_is_not_changed_after(self):
        self.sheet()
        files = self.ballots("claude", lambda k: "second")
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, {"claude": files})
        self.score(claude=files)
        files[0].write_text(files[0].read_text().replace('"fidelity": "both"', '"fidelity": "neither"', 1))
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, {"claude": files})
        with self.assertRaises(ValueError):
            cj.cmd_seal(self.f, files)

    def test_a_row_outside_the_form_is_refused(self):
        self.sheet()
        files = self.ballots("claude", lambda k: "second")
        files[0].write_text(files[0].read_text().replace('"claim": "the claim"', '"claim": ""', 1))        # a piece named, and no claim quoted
        cj.cmd_seal(self.f, files)
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, {"claude": files})

    def test_the_outcomes_are_told_apart(self):
        self.sheet()
        how = {0: "second", 1: "first", 2: "both", 3: "neither"}
        def pick(k):
            if (k["first"], k["second"]) != ("A", "D"):
                return "neither"
            i = int(k["brief"][1:]) % 6
            if i == 4:
                return "first" if k["sheet"] == 1 else "second"           # another piece each way round
            if i == 5:
                return "both" if k["sheet"] == 1 else "second"
            return how[i]
        t = self.score(claude=self.ballots("claude", pick))["families"]["claude"]["tally"]["A-D"]
        self.assertEqual((t["eligible"], t["second"], t["first"], t["both"], t["neither"], t["reversal"], t["mixed"]), (40, 6, 7, 7, 7, 7, 6))
        self.assertEqual(t["bar"], 27)

    def test_one_way_round_alone_is_not_eligible_and_under_forty_nothing_is_declared(self):
        self.sheet()
        files = self.ballots("claude", lambda k: "second")
        keep = [r for r in cj.rows(files[1]) if int(self.key[r["pair"]]["brief"][1:]) > 5]                  # five briefs judged one way round only
        files[1].write_text("".join(json.dumps(r) + "\n" for r in keep))
        res = self.score(claude=files)
        t = res["families"]["claude"]["tally"]["A-D"]
        self.assertEqual((t["eligible"], t["second"], t["bar"]), (35, 35, None))
        self.assertIsNone(res["families"]["claude"]["reads"]["bundle_lifts_him"])
        self.assertTrue(any(s.startswith("Not declared (fewer than 40 eligible briefs)") for s in res["statements"]))

    def test_the_band_is_the_larger_of_the_two_ways_and_the_bundle_must_clear_it(self):
        self.sheet()
        def pick(k):
            pair, i = (k["first"], k["second"]), int(k["brief"][1:])
            if pair == ("A", "A2"):
                return "first" if i <= 30 else "second"                   # A over A2 in 30 briefs: the band is 30
            if pair == ("A", "D"):
                return "second" if i <= 29 else "neither"                 # D over A in 29: over the bar of 27, inside the band
            if pair == ("A", "B"):
                return "second" if i <= 35 else "neither"                 # B over A in 35: outside
            return "second" if "F" in pair else "neither"
        res = self.score(claude=self.ballots("claude", pick))
        r = res["families"]["claude"]["reads"]
        self.assertEqual(r["band"], {"A2_over_A": 10, "A_over_A2": 30, "taken": 30})
        self.assertEqual((r["bundle_lifts_him"], r["text_lifts_him"], r["cloud_over_his_best"], r["cloud_over_his_live"]), (False, True, True, True))
        self.assertIn("A short Wikipedia introduction, assigned to him, lifts what he writes.", res["statements"])
        self.assertIn("The bundle does not win outside the band.", res["statements"])
        self.assertIn("The cloud model, as it was configured, beats his best arm on these briefs.", res["statements"])

    def test_families_that_disagree_leave_it_unresolved(self):
        self.sheet()
        yes = self.ballots("claude", lambda k: "second" if (k["first"], k["second"]) != ("A", "A2") else "neither")
        no = self.ballots("astra", lambda k: "neither")
        res = self.score(claude=yes, astra=no)
        self.assertTrue(any(s.startswith("The families disagree on this, so it is unresolved: With the text, the fuller instructions") for s in res["statements"]))
        self.assertEqual(res["agreement"]["astra / claude"], {"compared": 320, "same": 40})                  # they agree on A with A2 only

    def test_the_calibration_pairs_can_fail_a_family(self):
        self.sheet(controls=8)
        self.assertEqual((self.res["controls"], self.res["rows_a_sheet"]), (8, N * 8 + 8))
        good = lambda k: "first" if "control" in k else "second" if (k["first"], k["second"]) != ("A", "A2") else "neither"
        fooled = lambda k: "second"                                                   # names the bad piece of every control
        flags = lambda k: ("X" if k["X"] == "bad" else "Y") if k.get("control") == "invention" else "neither"
        res = self.score(claude=self.ballots("claude", good, invented=flags), astra=self.ballots("astra", fooled))
        c = res["families"]["claude"]["calibration"]
        self.assertEqual((c["controls"], c["right"], c["inventions_flagged"], c["passed"]), (8, 8, 4, True))
        self.assertIs(res["families"]["astra"]["calibration"]["passed"], False)
        self.assertTrue(res["statements"][0].startswith("astra failed the calibration pairs"))
        self.assertIn("With the text, the fuller instructions and time to think together, he wins outside the band: this bundle lifts what he writes on an assigned headline.", res["statements"])
        self.assertEqual(res["families"]["claude"]["tally"]["A-D"]["eligible"], 40)   # the controls are not counted among the briefs
        md = (self.f / "RESULT.md").read_text()
        self.assertIn("Calibration: 8 of 8 controls right, 4 inventions flagged: passed.", md)

    def test_the_arms_table_counts_stances_fidelity_and_inventions(self):
        self.sheet()
        res = self.score(claude=self.ballots("claude", lambda k: "second", invented=lambda k: "X"))
        a = res["families"]["claude"]["arms"]
        self.assertEqual(sum(t["shown"] for t in a.values()), 2 * 2 * N * 8)
        self.assertEqual(a["A"]["shown"], a["A"]["kept_1831"])                        # "both" keeps both
        self.assertEqual(a["A"]["defence"] + a["A"]["revision"], a["A"]["shown"])
        self.assertEqual(sum(t["invented"] for t in a.values()), 2 * N * 8)           # one side of every row

    def test_welts_rows_stand_beside_the_families(self):
        self.sheet()
        fam = self.ballots("claude", lambda k: "second")
        mine = []
        for r in cj.rows(self.f / "WELT-24.jsonl"):
            k = self.key[r["pair"]]
            mine.append({"pair": r["pair"], "q1": ("X" if k["X"] == "D" else "Y") if (k["first"], k["second"]) == ("A", "D") else "neither"})
        w = Path(self.td.name) / "welt.jsonl"
        w.write_text("".join(json.dumps(x) + "\n" for x in mine))
        cj.cmd_seal(self.f, fam + [w])
        res = cj.cmd_score(self.f, self.k, {"claude": fam}, welt=w)
        self.assertEqual(res["welt"]["A-D"], {"read": 3, "first": 0, "second": 3, "both": 0, "neither": 0})
        self.assertEqual(res["welt"]["A-B"], {"read": 3, "first": 0, "second": 0, "both": 0, "neither": 3})
        self.assertIn("## Welt's rows", (self.f / "RESULT.md").read_text())
        w.write_text(w.read_text().replace("neither", "X", 1))
        with self.assertRaises(ValueError):
            cj.cmd_score(self.f, self.k, {"claude": fam}, welt=w)             # changed after its seal

    def test_the_interval_is_taken_over_mornings(self):
        lo, hi = cj.interval([True] * 20 + [False] * 20, [f"m{i // 2}" for i in range(40)])
        self.assertTrue(0.25 < lo < 0.5 < hi < 0.75)
        self.assertEqual(cj.interval([True] * 6, ["m"] * 6), [1.0, 1.0])
        self.assertIsNone(cj.interval([], []))


if __name__ == "__main__":
    unittest.main()
