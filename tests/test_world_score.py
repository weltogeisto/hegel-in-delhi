"""tools/world_score.py: the six measures by week, on small synthetic futures."""
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from tools import world_score as ws

START = date(2026, 11, 25)


def step(act, place="home", thought="A thought.", opened=("reply",), t="10:00"):
    return {"t": t, "event": "x", "opened": list(opened),
            "decision": {"thought": thought, "action": act, "place": place, "minutes": 30}, "mind": {"source": "mind"}}


def day(i, acts=("read", "walk"), moments=8, beats=(), file="line", meals=(), entries=(), funnel=None, complete=True,
        thoughts=None, opened=("reply",)):
    d = START + timedelta(days=i)
    steps = [step(acts[k % len(acts)], "home" if k % 2 else "lodhi", (thoughts or {}).get(k, "A thought."), opened) for k in range(moments)]
    return {"n": 55 + i, "date": d.isoformat(), "steps": steps, "entries": list(entries), "complete": complete,
            "funnel": funnel or {}, "owl": {"diary": "x"},
            "state": {"imprest": 1000, "beats": list(beats), "file": file, "cheques": [], "owed": [], "account": {"vouchers": []},
                      "today": {m: True for m in meals}}}


def varied(i, **kw):
    """A day unlike the one before: the acts alternate with the day's parity."""
    return day(i, acts=(("read",) if i % 2 else ("walk",)), **kw)


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name) / "futures"

    def tearDown(self):
        self.td.cleanup()

    def write(self, seed, days, root=None):
        f = (root or self.root) / seed / "days"
        f.mkdir(parents=True, exist_ok=True)
        for d in days:
            (f / f"{d['date']}.json").write_text(json.dumps(d))

    def score(self, seed="1831"):
        rows, raw, fb = ws.load(self.root / seed, START.isoformat())
        return ws.score_future(rows, raw, fb)

    def base(self, **kw):
        d = day(-1, **kw)
        return d

    def test_weeks_are_cut_and_a_short_last_week_is_marked(self):
        self.write("1831", [self.base()] + [varied(i) for i in range(9)] + [varied(9, complete=False)])
        w = self.score()
        self.assertEqual([x["days"] for x in w], [7, 2])
        self.assertEqual([x["short"] for x in w], [False, True])
        self.assertEqual((w[0]["from"], w[1]["from"]), ("2026-11-25", "2026-12-02"))

    def test_brought_is_the_weekly_mean_and_ok_at_six(self):
        self.write("1831", [self.base()] + [varied(i, opened=("papers",) if i < 7 else ("reply",)) for i in range(8)])
        w = self.score()
        self.assertEqual(w[0]["brought"]["mean"], 8.0)   # every moment of a day opened by a brought kind
        self.assertTrue(w[0]["brought"]["ok"])
        self.assertFalse(w[1]["brought"]["ok"])

    def test_alike_counts_a_run_that_crosses_the_week_boundary(self):
        # days 0-4 differ day to day; days 5..8 repeat day 4 (same acts); the run of alike days spans the boundary at day 7
        days = [self.base()] + [varied(i) for i in range(5)] + [varied(4) | {"date": (START + timedelta(days=i)).isoformat()} for i in range(5, 9)]
        self.write("1831", days)
        w = self.score()
        self.assertEqual(w[0]["alike"]["longest_run"], 2)       # days 5 and 6 alike
        self.assertTrue(w[0]["alike"]["ok"])
        self.assertEqual(w[1]["alike"]["longest_run"], 4)       # the run reaches 4 on day 8, counting the week before
        self.assertFalse(w[1]["alike"]["ok"])

    def test_threads_count_the_file_and_new_beats_but_not_repeat_sessions(self):
        days = [self.base(beats=["a"], file="one")]
        days.append(varied(0, beats=["a", "b"], file="two"))                       # file moved, beat b is new
        days.append(day(1, beats=["a", "b", "session:x", "talk@ramesh"], file="two"))  # repeats only
        self.write("1831", days)
        t = self.score()[0]["threads"]
        self.assertEqual(t["count"], 2)
        self.assertEqual(t["moved"], ["file: two", "beat: b"])
        self.assertTrue(t["ok"])

    def test_thread_kinds_count_when_opened(self):
        self.write("1831", [self.base(), day(0, opened=("story",)), varied(1)])
        self.assertEqual(self.score()[0]["threads"]["count"], 8)    # one per moment of the day, all opened by a story

    def test_meals_are_counted(self):
        self.write("1831", [self.base(), day(0, meals=("breakfast", "dinner")), varied(1, meals=("breakfast", "lunch", "dinner")), varied(2)])
        f = self.score()[0]["fed"]
        self.assertEqual((f["meals"], f["of"], f["share"]), (5, 9, 0.556))
        self.assertEqual((f["days_nothing"], f["nothing_on"]), (1, ["2026-11-27"]))         # the third day: no meal at all

    def test_food_he_bought_is_not_a_day_without_food(self):
        bought = varied(1)
        bought["state"]["today"]["bought_food"] = {"place": "habitat", "t": "2026-11-26T15:36+05:30"}
        self.write("1831", [self.base(), day(0, meals=("lunch",)), bought, varied(2)])
        f = self.score()[0]["fed"]
        self.assertEqual((f["meals"], f["days_nothing"]), (1, 1))                           # one meal in three days; he ate on two of them

    def read_entry(self, title, t="09:00"):
        return {"k": "read", "title": title, "t": t}

    def test_a_reading_is_used_with_two_shared_title_words_and_not_with_one(self):
        entries = [self.read_entry("Phenomenology of Spirit and Recognition"), self.read_entry("Lectures on Aesthetics and Gardens")]
        later = {2: "He turned the spirit over; recognition is the matter of the phenomenology.", 3: "Aesthetics came to mind, nothing more."}
        self.write("1831", [self.base(), day(0, entries=entries), varied(1), varied(2, thoughts=later), varied(3)])
        c = self.score()[0]["came_back"]
        self.assertEqual((c["readings"], c["used"], c["used_share"]), (2, 1, 0.5))

    def test_a_reading_used_after_fourteen_days_is_not_used(self):
        late = {0: "Phenomenology of spirit again."}
        days = [self.base(), day(0, entries=[self.read_entry("Phenomenology of Spirit")])] + [varied(i) for i in range(1, 15)]
        days.append(varied(15, thoughts=late))
        self.write("1831", days)
        c = self.score()[0]["came_back"]
        self.assertEqual((c["readings"], c["used"]), (1, 0))

    def test_no_readings_gives_none_and_return_kinds_count_moments(self):
        self.write("1831", [self.base(), day(0, opened=("trace",)), varied(1)])
        c = self.score()[0]["came_back"]
        self.assertEqual((c["readings"], c["used_share"], c["returns"]), (0, None, 8))

    def test_funnel_counts_and_the_same_answer_every_time(self):
        f = lambda s, y, n: {"shown": s, "yes": y, "no": n}
        days = [self.base(), day(0, funnel={"bank": f(1, 0, 1), "session:g": f(3, 3, 0), "loan": f(1, 1, 0)}),
                varied(1, funnel={"bank": f(2, 0, 2), "loan": f(1, 0, 1)})]
        self.write("1831", days)
        c = self.score()[0]["chose"]
        self.assertEqual((c["shown"], c["taken"], c["declined"]), (5, 1, 4))
        self.assertEqual(c["same_answer_ids"], ["bank"])     # loan was shown twice but answered both ways

    def test_what_he_wrote_is_counted_by_week(self):
        w1 = {"k": "writing", "title": "On the Republic", "work": "on-the-republic", "sitting": 1, "words": 500, "text": "x " * 500, "t": "11:00"}
        w2 = dict(w1, sitting=2, words=None, text="y " * 300)
        w3 = {"k": "writing", "title": "A letter", "work": "a-letter", "sitting": 1, "words": 200, "text": "z " * 200, "t": "12:00"}
        self.write("1831", [self.base()] + [varied(0, entries=[w1]), varied(1, entries=[w2, w3])] + [varied(i) for i in range(2, 8)])
        w = self.score()
        self.assertEqual(w[0]["wrote"], {"sittings": 3, "words": 1000, "manuscripts": 2})
        self.assertEqual(w[1]["wrote"], {"sittings": 0, "words": 0, "manuscripts": 0})
        self.assertIn("Wrote, by week: 3 sittings, 1,000 words; 0 sittings, 0 words.", ws.render({"1831": w}))

    def test_compare_matches_futures_by_name_and_gives_b_minus_a(self):
        a, b = Path(self.td.name) / "a", Path(self.td.name) / "b"
        self.write("1831", [self.base(), varied(0, meals=("breakfast",)), varied(1)], a / "futures")
        self.write("1831", [self.base(), varied(0, meals=("breakfast", "lunch", "dinner")), varied(1)], b / "futures")
        self.write("2718", [self.base(), varied(0)], b / "futures")
        arms = [ws.score_folder(x / "futures", START.isoformat()) for x in (a, b)]
        res = ws.compare(*arms)
        self.assertEqual(res["matched"], ["1831"])
        fed = res["measures"]["fed (meals)"][0]
        self.assertEqual((fed["A"], fed["B"], fed["B_minus_A"]), (1, 3, 2))

    def test_the_command_line_writes_the_files(self):
        self.write("1831", [self.base(), varied(0), varied(1)])
        out = Path(self.td.name) / "out"
        self.assertEqual(ws.main(["--futures", str(self.root), "--from", START.isoformat(), "--out", str(out)]), 0)
        self.assertIn("## Future 1831", (out / "SCORE.md").read_text())
        self.assertIn("Week 1:", (out / "SCORE.md").read_text())
        self.assertEqual(set(json.loads((out / "score.json").read_text())), {"1831"})

    def test_the_compare_command_line_writes_both_arms_and_the_comparison(self):
        a, b = Path(self.td.name) / "a", Path(self.td.name) / "b"
        for x in (a, b):
            self.write("1831", [self.base(), varied(0), varied(1)], x / "futures")
        out = Path(self.td.name) / "out"
        self.assertEqual(ws.main(["--compare", str(a), str(b), "--from", START.isoformat(), "--out", str(out)]), 0)
        for p in ("A/SCORE.md", "B/score.json", "COMPARE.md", "score.json"):
            self.assertTrue((out / p).exists(), p)
        self.assertIn("1 futures matched", (out / "COMPARE.md").read_text())


if __name__ == "__main__":
    unittest.main()
