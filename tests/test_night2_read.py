"""tools/night2_read.py: night 2's futures read day by day, and the first day each shows what was named."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import night2_read as n2


def step(place, act):
    return {"t": "10:00", "event": "x", "opened": ["reply"],
            "decision": {"thought": "A thought.", "action": act, "place": place, "minutes": 30}, "mind": {"source": "mind"}}


def day(n, date, moments=25, cash=10000, beats=(), acts=("read", "walk"), owl=True, complete=True):
    steps = [step("home" if i % 2 else "lodhi", acts[i % len(acts)]) for i in range(moments)]
    d = {"n": n, "date": date, "steps": steps, "entries": [], "complete": complete,
         "state": {"imprest": cash, "beats": list(beats), "file": f"file on {date}", "cheques": [{"amount": 10000}], "owed": [{"amount": 290}],
                   "account": {"vouchers": []}}}
    if owl:
        d["owl"] = {"diary": "He walked and read."}
    return d


class Night2Test(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name) / "futures"

    def tearDown(self):
        self.td.cleanup()

    def write(self, seed, days):
        f = self.root / seed / "days"
        f.mkdir(parents=True)
        for d in days:
            (f / f"{d['date']}.json").write_text(json.dumps(d))

    def test_days_before_the_start_only_give_the_state_to_count_from(self):
        self.write("1831", [day(54, "2026-11-24", cash=15000, beats=["a"]), day(55, "2026-11-25", cash=14200, beats=["a", "b"]),
                            day(56, "2026-11-26", cash=14200, beats=["a", "b"])])
        rows = n2.day_rows(self.root / "1831", "2026-11-25")
        self.assertEqual([r["n"] for r in rows], [55, 56])
        self.assertEqual((rows[0]["change"], rows[0]["beats"], rows[1]["beats"]), (-800, ["b"], []))
        self.assertEqual((rows[0]["cheques"], rows[0]["owed"], rows[0]["file"]), (10000, 290, "file on 2026-11-25"))
        self.assertEqual(rows[1]["variation"], 0.0)                    # the same day again

    def test_the_first_day_of_each_thing_named(self):
        days = [day(54, "2026-11-24", cash=9000, beats=["a"])]
        for i in range(10):
            days.append(day(55 + i, f"2026-11-{25 + i:02d}" if i < 6 else f"2026-12-{i - 5:02d}", cash=9000 - 800 * (i + 1),
                            beats=["a", "b"] if i >= 1 else ["a"], moments=25 if i != 4 else 12, owl=i != 6))
        self.write("2718", days)
        m = n2.milestones(n2.day_rows(self.root / "2718", "2026-11-25"))
        self.assertEqual(m["days"], 10)
        self.assertEqual(m["cash_under"], "2026-12-03")                # 9000 - 800 * 9 = 1800
        self.assertEqual(m["under_floor"], "2026-11-29")
        self.assertEqual(m["owl_silent"], "2026-12-01")
        self.assertEqual(m["no_beat_for_a_week"], "2026-12-03")        # no beat since the second day, for seven days
        self.assertEqual(m["same_day_again"], "2026-11-28")            # days 2, 3 and 4 repeat the first

    def test_a_cut_day_is_shown_and_not_counted(self):
        self.write("1831", [day(55, "2026-11-25"), day(56, "2026-11-26", complete=False, owl=False)])
        rows = n2.day_rows(self.root / "1831", "2026-11-25")
        m = n2.milestones(rows)
        self.assertEqual((m["days"], m["owl_silent"]), (1, None))
        text, _ = n2.report({"1831": rows})
        self.assertIn("(cut)", text)

    def test_the_command_line_writes_both_futures(self):
        self.write("1831", [day(55, "2026-11-25"), day(56, "2026-11-26")])
        self.write("2718", [day(55, "2026-11-25", cash=500)])
        out = Path(self.td.name) / "out"
        self.assertEqual(n2.main(["--futures", str(self.root), "--from", "2026-11-25", "--out", str(out)]), 0)
        res = json.loads((out / "result.json").read_text())
        self.assertEqual(set(res), {"1831", "2718"})
        self.assertEqual(res["2718"]["milestones"]["cash_under"], "2026-11-25")
        self.assertIn("## Seed 2718: 1 days", (out / "RESULT.md").read_text())


if __name__ == "__main__":
    unittest.main()
