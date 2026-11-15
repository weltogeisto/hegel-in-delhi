"""An answer to what he said as he left stays with that step: it does not follow him to where he arrives.

At 38:25 and 45:25 a bookseller's line reached him at home, after he had walked there from Khan Market."""
import json
import unittest
from datetime import date
from pathlib import Path

from world import voices
from world.world import World, at_dt

R = Path(__file__).resolve().parents[1]
LINE = {"by": "The bookseller", "says": "Just move your bag, the queue is forming.", "does": "She wipes the table."}


def answer(**kw):
    a = dict(thought="The tea is finished.", action="talk", place="khan", minutes=15,
             says="Thank you for the tea.", speaks_to="bookseller", buys=[], revision=None)
    a.update(kw)
    return a


class ReplyLeftTests(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def fixture(self):
        day = json.loads((R / "docs/days/2026-10-02.json").read_text())
        day.update(date="2026-10-03", n=2, steps=[], entries=[], segments=[], complete=False)
        st = day["state"]
        st.update(place="khan", asleep=False, today={}, people=list(self.w.cast), beats=[b["id"] for b in self.w.beats])
        self.w.ledger(st)
        t = at_dt(date(2026, 10, 3), 17 * 60 + 56)
        st["until"] = t.isoformat(timespec="minutes")
        sit = dict(day="Saturday 3 October", time="17:56", place="khan", weather="23 °C, clear", aqi="unknown",
                   outfit="white cotton kurta", imprest_left=st["imprest"], present=["the bookseller"],
                   open_now=["home", "khan", "iic"], event="The bookseller is here.")
        ctx = dict(t=t, present=["bookseller"], beat=None, public=[], recent=[], known_text="The bookseller has met him.")
        return day, st, sit, ctx

    def run_step(self, a):
        """Apply one step in which he speaks and gets LINE back; then build the situation at the step's end."""
        day, st, sit, ctx = self.fixture()
        errors, _, rep = self.w.check(a, sit, ctx, st)
        self.assertFalse(errors)
        ctx["reply"] = LINE
        step = self.w.apply(*rep, sit, ctx, st, day)
        day["steps"].append(step)
        h, m = map(int, step["end"].split(":"))
        end = at_dt(date(2026, 10, 3), h * 60 + m)
        nxt, _ = self.w.situation(end, st, day, step)
        return step, nxt

    def test_walking_away_leaves_the_answer_behind(self):
        step, nxt = self.run_step(answer(action="walk", place="home"))
        self.assertEqual(step["left"], "khan")
        self.assertEqual(step["voice"], LINE)                                  # the record keeps the answer
        self.assertEqual(nxt["place"], "home")
        self.assertNotIn(LINE["says"], nxt["event"])

    def test_going_elsewhere_to_do_something_leaves_it_too(self):
        step, nxt = self.run_step(answer(action="read", place="iic", minutes=30))
        self.assertEqual(step["left"], "khan")
        self.assertNotIn(LINE["says"], nxt["event"])

    def test_staying_hears_the_answer_as_before(self):
        step, nxt = self.run_step(answer())
        self.assertNotIn("left", step)
        self.assertEqual(step["voice"], LINE)
        self.assertIn(voices.heard(LINE), nxt["event"])

    def test_the_answer_is_in_the_record_either_way(self):
        for a in (answer(), answer(action="walk", place="home")):
            with self.subTest(action=a["action"]):
                day, st, sit, ctx = self.fixture()
                _, _, rep = self.w.check(a, sit, ctx, st)
                ctx["reply"] = LINE
                self.w.apply(*rep, sit, ctx, st, day)
                self.assertTrue(any(LINE["says"] in json.dumps(e, ensure_ascii=False) for e in day["entries"]))


if __name__ == "__main__":
    unittest.main()
