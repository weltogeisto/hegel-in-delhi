"""HEGEL_KEEP_TIME (Day 53): an appointment at another place ends what he is doing in time to walk there, his mind says how
long is left, and a talk at the IIC he missed is offered once more the next day. Off, nothing of it happens."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import D, There, fresh, look  # noqa: E402  (this also keeps the tests off the Pi's env file)
from test_world import answer  # noqa: E402

from world.world import LEAVE_SPARE, World, at_dt  # noqa: E402

TALK = {"date": "2026-10-14", "t": "18:30", "what": "your talk at the IIC", "beat": "iic_talk_day"}


def booked():
    st = fresh()
    st["beats"].append("iic_talk")
    st["appointments"].append(dict(TALK))
    return st


def rest(w, t, st, minutes=60):
    """A rest at home from t, as Day 53's 17:55: returns the step."""
    st["place"], day = "home", {"segments": [], "entries": [], "steps": []}
    sit, ctx = w.situation(t, st, day, None)
    errors, _, rep = w.check(answer(action="rest", place="home", minutes=minutes), sit, ctx, st)
    assert not errors, errors
    return w.apply(rep[0], rep[1], sit, ctx, st, day), sit


class KeepTime(unittest.TestCase):
    def setUp(self):
        self.on, self.off = World(keep_time=True), World()
        self.walk = self.on.walk("home", "iic")

    def test_a_rest_at_home_ends_in_time_to_walk_to_the_talk(self):
        step, _ = rest(self.on, at_dt(D(14), 17 * 60 + 55), booked())
        self.assertEqual(step["end"], f"{(18 * 60 + 30 - self.walk - LEAVE_SPARE) // 60:02d}:{(18 * 60 + 30 - self.walk - LEAVE_SPARE) % 60:02d}")

    def test_off_the_rest_runs_its_hour_as_on_day_53(self):
        step, _ = rest(self.off, at_dt(D(14), 17 * 60 + 55), booked())
        self.assertEqual(step["end"], "18:55")

    def test_a_rest_that_ends_before_he_must_leave_is_not_cut(self):
        step, _ = rest(self.on, at_dt(D(14), 15 * 60), booked())
        self.assertEqual(step["end"], "16:00")

    def test_he_is_told_the_time_when_he_must_set_out(self):
        st = booked()
        leave = 18 * 60 + 30 - self.walk - LEAVE_SPARE
        sit, ctx = look(self.on, at_dt(D(14), leave), st, "home")
        self.assertIn(f"Your talk at the IIC begins at 18:30, at the IIC; the walk from here takes about {self.walk} minutes.",
                      sit["event"])
        self.assertIn("time", ctx["opened"])
        sit, _ = look(self.on, at_dt(D(14), leave - 30), booked(), "home")
        self.assertNotIn("begins at 18:30", sit["event"])                                   # not before
        sit, _ = look(self.off, at_dt(D(14), leave), booked(), "home")
        self.assertNotIn("begins at 18:30", sit["event"])                                   # nor with the switch off

    def test_his_mind_says_how_long_is_left_on_the_day(self):
        line = lambda w, t: next(x for x in look(w, t, booked(), "home")[0]["on_mind"] if "your talk at the IIC" in x)
        self.assertEqual(line(self.on, at_dt(D(14), 16 * 60 + 55)), "Today, Wednesday 14 October 18:30: your talk at the IIC, in 95 minutes.")
        self.assertEqual(line(self.on, at_dt(D(14), 10 * 60)), "Today, Wednesday 14 October 18:30: your talk at the IIC.")   # hours away
        self.assertEqual(line(self.on, at_dt(D(13), 17 * 60)), "Tomorrow, Wednesday 14 October 18:30: your talk at the IIC.")   # Day 53's mistake
        self.assertEqual(line(self.on, at_dt(D(12), 17 * 60)), "Wednesday 14 October 18:30: your talk at the IIC.")   # further off
        self.assertEqual(line(self.off, at_dt(D(14), 16 * 60 + 55)), "Wednesday 14 October 18:30: your talk at the IIC.")

    def test_at_the_iic_itself_nothing_cuts_or_reminds(self):
        st = booked()
        self.assertEqual(self.on.due_elsewhere(at_dt(D(14), 18 * 60), st, "iic"), [])

    def test_a_missed_talk_is_offered_again_the_next_morning_and_given_that_evening(self):
        w, st = self.on, booked()
        look(w, at_dt(D(14), 19 * 60 + 20), st, "iic")                                        # 19:20: the window has closed
        self.assertIn("iic_talk_day", st["missed"])
        with There(home=[]):
            self.assertIsNone(look(w, at_dt(D(15), 10 * 60), st, "home")[1]["beat"])         # nobody to bring the note
        with There(home=["ramesh"]):
            self.assertIsNone(look(w, at_dt(D(15), 8 * 60), st, "home")[1]["beat"])          # not before nine
            sit, ctx = look(w, at_dt(D(15), 10 * 60), st, "home")
            self.assertEqual(ctx["beat"]["id"], "iic_talk_again")
            self.assertIn("offers the hall again this evening at half past six", sit["event"])
            self.assertIn("offer:iic_talk_again", ctx["opened"])
            w.fire(ctx["beat"], at_dt(D(15), 10 * 60), st)
            w.settle_choice(ctx["beat"], True, st, at_dt(D(15), 10 * 60))
        self.assertEqual(st["appointments"], [{"date": "2026-10-15", "t": "18:30", "what": "your talk at the IIC, offered a second time",
                                               "beat": "iic_talk_day2"}])
        step, _ = rest(w, at_dt(D(15), 17 * 60 + 30), st, 120)                             # and this time he is woken in time
        self.assertEqual(step["end"], f"{(18 * 60 + 30 - self.walk - LEAVE_SPARE) // 60:02d}:{(18 * 60 + 30 - self.walk - LEAVE_SPARE) % 60:02d}")
        with There(iic=["officer"]):
            sit, ctx = look(w, at_dt(D(15), 18 * 60 + 30), st, "iic")
            self.assertEqual(ctx["beat"]["id"], "iic_talk_day2")
            w.fire(ctx["beat"], at_dt(D(15), 18 * 60 + 30), st)
            look(w, at_dt(D(15), 19 * 60 + 35), st, "iic")
        self.assertEqual(st["cheques"], [{"from": "the India International Centre", "amount": 10000, "since": "2026-10-15"}])
        with There(home=["ramesh"]):
            self.assertIsNone(look(w, at_dt(D(16), 10 * 60), st, "home")[1]["beat"])        # offered once only

    def test_a_second_refusal_ends_it(self):
        w, st = self.on, booked()
        look(w, at_dt(D(14), 19 * 60 + 20), st, "iic")
        with There(home=["ramesh"]):
            ctx = look(w, at_dt(D(15), 10 * 60), st, "home")[1]
            w.fire(ctx["beat"], at_dt(D(15), 10 * 60), st)
            w.settle_choice(ctx["beat"], False, st, at_dt(D(15), 10 * 60))
            self.assertEqual(st["appointments"], [])
            self.assertIsNone(look(w, at_dt(D(16), 10 * 60), st, "home")[1]["beat"])

    def test_off_the_note_never_comes(self):
        w, st = self.off, booked()
        look(w, at_dt(D(14), 19 * 60 + 20), st, "iic")
        with There(home=["ramesh"]):
            self.assertIsNone(look(w, at_dt(D(15), 10 * 60), st, "home")[1]["beat"])
        self.assertNotIn("iic_talk_again", {b["id"] for b in w.beats})

    def test_a_talk_he_gave_is_not_offered_again(self):
        w, st = self.on, booked()
        with There(iic=["officer"]):
            ctx = look(w, at_dt(D(14), 18 * 60 + 30), st, "iic")[1]
            w.fire(ctx["beat"], at_dt(D(14), 18 * 60 + 30), st)
        with There(home=["ramesh"]):
            self.assertIsNone(look(w, at_dt(D(15), 10 * 60), st, "home")[1]["beat"])


class KeepTimeAsOnThePi(KeepTime):
    """The same, with the switches the Pi runs: the world repairs and the culture."""
    def setUp(self):
        self.on, self.off = World(keep_time=True, repairs=True, culture=True), World(repairs=True, culture=True)
        self.walk = self.on.walk("home", "iic")


if __name__ == "__main__":
    unittest.main()
