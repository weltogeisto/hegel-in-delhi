"""tools/works_score.py: what the manuscripts do, counted sitting by sitting. Synthetic day files only."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import works_score as ws


def writing(text, work="w1", sitting=1, title="Work One", kind="notes", t="10:00"):
    return {"k": "writing", "title": title, "kind": kind, "to": None, "sitting": sitting, "text": text, "work": work,
            "words": len(text.split()), "t": t}


def day(date, *entries, complete=True):
    return {"date": date, "complete": complete, "steps": [], "entries": list(entries), "state": {}}


def sit(days, **kw):
    return ws.score(days, **kw)


A = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima"


class CountsTest(unittest.TestCase):
    def test_opens_dated(self):
        self.assertTrue(ws.opens_dated("24 November 2026. Delhi. The sun."))
        self.assertTrue(ws.opens_dated("Tonight at 15:44 I sat down."))
        self.assertTrue(ws.opens_dated("The air quality index stood high."))
        self.assertTrue(ws.opens_dated("AQI is bad today, and I write."))
        self.assertFalse(ws.opens_dated("The Idea is what it is. " * 6 + "13 October 2026"))     # the date comes after 30 words
        self.assertFalse(ws.opens_dated("Spirit comes to itself in the state."))

    def test_century_whole_word_any_case_plural_not_inside_another_word(self):
        r = sit([day("2026-11-01", writing("Then MARX spoke, and darwins ideas, but the marxists and Marxology and Darwinian came too."))])
        self.assertEqual(r[0]["century"]["terms"], ["MARX", "darwin", "marxist"])
        self.assertEqual(r[0]["century"]["count"], 3)
        self.assertEqual(sit([day("2026-11-01", writing("Nothing of the kind, only Hegel."))])[0]["century"]["count"], 0)

    def test_said_before_across_two_manuscripts(self):
        d1 = day("2026-11-01", writing(A, work="w1"))
        d2 = day("2026-11-02", writing("alpha bravo charlie delta echo foxtrot zulu yankee xray whiskey", work="w2", title="Two"))
        r = sit([d1, d2])
        self.assertEqual(r[0]["said_before"], 0.0)
        self.assertEqual(r[1]["said_before"], 0.2)         # five runs, only the first stands in the first sitting

    def test_stock_needs_three_earlier_sittings(self):
        f = "the state is the actuality"
        days = [day("2026-11-0%d" % i, writing(w + " " + f + " " + e)) for i, (w, e) in enumerate((("one", "ant"), ("two", "bee"), ("three", "cat"), ("four", "dog")), 1)]
        days.append(day("2026-11-05", writing("five different sentence entirely")))
        r = sit(days)
        self.assertEqual(r[2]["stock"], 0.0)               # only two earlier sittings held the formula
        self.assertEqual(r[3]["stock"], 0.5)               # of four runs, "the state is the" and "state is the actuality" stood in three
        self.assertEqual(r[4]["stock"], 0.0)

    def test_new_words(self):
        d1 = day("2026-11-01", writing("substance substance dialectic wandering"))
        d2 = day("2026-11-02", writing("substance dialectic wandering marketplace nothing monument because it"))
        r = sit([d1, d2])
        self.assertEqual(r[0]["new_words"]["count"], 3)
        n = r[1]["new_words"]
        self.assertEqual((n["count"], n["share"], n["sample"]), (2, 0.4, ["marketplace", "monument"]))

    def test_reading_used_by_two_title_words_and_the_fourteen_days(self):
        reads = day("2026-11-10", {"k": "read", "title": "Nietzsche on Genealogy and Morality"},
                    {"k": "read", "title": "Gazette of Railway Timetables"})
        old = day("2026-10-20", {"k": "read", "title": "Ancient Treatise on Sovereignty"})
        s = day("2026-11-24", writing("I thought of genealogy and morality at length, and of sovereignty, and railway nothing."))
        r = sit([old, reads, s])[0]["read_used"]
        self.assertEqual((r["available"], r["used"]), (2, 1))       # the treatise is 35 days old; the gazette shares only one word
        self.assertEqual(r["titles"], ["Nietzsche on Genealogy and Morality"])
        edge = day("2026-11-10", writing("sovereignty ancient treatise"))
        r = sit([day("2026-10-27", {"k": "read", "title": "Ancient Treatise on Sovereignty"}), edge])[0]["read_used"]
        self.assertEqual((r["available"], r["used"]), (1, 1))       # 14 days back still counts
        r = sit([day("2026-10-26", {"k": "read", "title": "Ancient Treatise on Sovereignty"}), edge])[0]["read_used"]
        self.assertEqual(r["available"], 0)

    def test_before_and_from_change_what_counts_as_earlier_not_what_is_scored(self):
        d1, d2, d3 = (day("2026-11-0%d" % i, writing(A, work="w%d" % i)) for i in (1, 2, 3))
        self.assertEqual([x["said_before"] for x in sit([d1, d2, d3])], [0.0, 1.0, 1.0])
        r = sit([d2, d3], before_days=[d1])
        self.assertEqual([x["date"] for x in r], ["2026-11-02", "2026-11-03"])
        self.assertEqual(r[0]["said_before"], 1.0)
        r = sit([d1, d2, d3], start="2026-11-03")
        self.assertEqual([x["date"] for x in r], ["2026-11-03"])
        self.assertEqual(r[0]["said_before"], 1.0)
        self.assertEqual(sit([d1, d2], before_days=[d1])[0]["date"], "2026-11-02")       # the same day in both is counted once

    def test_incomplete_days_and_empty_sittings_are_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "2026-11-01.json").write_text(json.dumps(day("2026-11-01", writing(A), complete=False)))
            Path(td, "2026-11-02.json").write_text(json.dumps(day("2026-11-02", writing("  "), writing(A))))
            days = ws.load_days(td)
        self.assertEqual(len(sit(days)), 1)

    def test_summaries(self):
        days = [day("2026-11-01", writing("1 November 2026. Marx and substance wandering.", work="a", title="A")),
                day("2026-11-02", writing("Plain beginning of another monument.", work="a", sitting=2, title="A")),
                day("2026-11-03", writing("15:44 Darwin and Marx again, marketplace.", work="b", title="B", kind="letter"))]
        res = ws.summarize(sit(days))
        o = res["overall"]
        self.assertEqual((o["sittings"], o["manuscripts"], o["open_dated_share"]), (3, 2, round(2 / 3, 4)))
        self.assertEqual((o["sittings_with_century"], o["century_terms_distinct"], o["century_terms"]), (2, 2, ["darwin", "marx"]))
        self.assertEqual((o["readings_available"], o["readings_used"]), (0, 0))
        a, b = res["works"]
        self.assertEqual((a["work"], a["sittings"], a["first"], a["last"], a["opens_dated"], a["century_terms"]),
                         ("a", 2, "2026-11-01", "2026-11-02", 1, 1))
        self.assertEqual(len(a["new_words_per_sitting"]), 2)
        self.assertEqual((b["sittings"], b["century_terms"], b["kind"]), (1, 2, "letter"))


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def put(self, folder, d):
        f = self.root / folder
        f.mkdir(parents=True, exist_ok=True)
        (f / f"{d['date']}.json").write_text(json.dumps(d))

    def test_days(self):
        for i in (1, 2, 3):
            self.put("days", day("2026-11-0%d" % i, writing("%d November 2026. %s" % (i, A), sitting=i)))
        self.assertEqual(ws.main(["--days", str(self.root / "days"), "--out", str(self.root / "out")]), 0)
        text = (self.root / "out" / "WORKS.md").read_text()
        self.assertIn("Sittings: 3", text)
        self.assertIn("### Work One", text)                      # three sittings: a table of its own
        data = json.loads((self.root / "out" / "works.json").read_text())
        self.assertEqual(data["overall"]["sittings"], 3)

    def test_futures_with_before_and_from(self):
        self.put("live", day("2026-11-24", writing(A, work="w0", title="Live")))
        for seed in ("1831", "2718"):
            self.put(f"futures/{seed}/days", day("2026-11-25", writing(A, work="w1")))
            self.put(f"futures/{seed}/days", day("2026-11-26", writing("fresh words here, wandering monument marketplace", work="w1", sitting=2)))
        out = self.root / "out"
        self.assertEqual(ws.main(["--futures", str(self.root / "futures"), "--before", str(self.root / "live"), "--from", "2026-11-25",
                                  "--out", str(out)]), 0)
        text = (out / "WORKS.md").read_text()
        self.assertIn("## Future 1831", text)
        self.assertIn("## Future 2718", text)
        self.assertLess(text.index("| Future |"), text.index("## Future 1831"))
        data = json.loads((out / "works.json").read_text())
        self.assertEqual(sorted(data), ["1831", "2718"])
        self.assertEqual([s["said_before"] for s in data["1831"]["sittings"]], [1.0, 0.0])    # said in the live record first
        for line in text.splitlines():
            if line.startswith("|"):
                self.assertLessEqual(line.count("|") - 1, 7)


if __name__ == "__main__":
    unittest.main()
