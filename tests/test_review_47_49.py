"""Five world defects from the review of Days 47–49 (18 November), each fixed in world/world.py:
the plate redrawn every hour, a snack counted from an old meal, eating where nothing is sold, an answer from someone
whose hours have ended, and a change of clothes at the place he leaves. All behind HEGEL_WORLD_REPAIRS (DECISIONS 57): off, the day is the day it was."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import answer, state  # noqa: E402

from world.config import Config  # noqa: E402
from world.world import World, at_dt  # noqa: E402

SAT = date(2026, 10, 3)


def at(h, m=0, d=SAT):
    return at_dt(d, h * 60 + m)


def play(w, st, when, prev=None, **kw):
    day = st.setdefault("_day", {"segments": [], "entries": [], "steps": []})
    sit, ctx = w.situation(when, st, day, prev)
    errors, _, rep = w.check(answer(**kw), sit, ctx, st)
    assert not errors, errors
    w.apply(rep[0], rep[1], sit, ctx, st, day)
    return day


class PlateTest(unittest.TestCase):
    def test_the_plate_is_one_dish_until_he_eats_a_meal(self):
        w, st = World(repairs=True), state()
        st["last_meal"] = "2026-10-03T08:00+05:30"
        dishes = {w.plate(at(h, 10), st) for h in range(15, 19)}
        self.assertEqual(len(dishes), 1)                                   # was drawn again each hour
        self.assertIsNotNone(dishes.pop())

    def test_the_promised_plate_is_the_dish_offered(self):
        w, st = World(promises=True, repairs=True), state()
        st["last_meal"] = "2026-10-03T08:00+05:30"
        offered = w.plate(at(15, 10), st)
        st["promises"] = [{"id": "p1", "by": "ramesh", "what": "plate", "said": "I will bring it.", "made": "2026-10-03T15:10+05:30",
                           "due": "2026-10-03T15:40+05:30", "place": "home", "status": "open"}]
        w.promise_round(at(16, 5), st, "home", [])                         # due at 15:40, kept an hour later
        self.assertEqual(st["today"]["laid"]["dish"], offered)


class SnackTest(unittest.TestCase):
    def setUp(self):
        self.w, self.st = World(repairs=True), state()
        self.st["today"] = {"woke": "06:00"}

    def test_a_snack_long_after_the_meal_holds_hunger_off_from_when_it_is_eaten(self):
        self.st["last_meal"] = "2026-10-03T07:00+05:30"
        self.w.feed(self.st, at(15), "snack")
        self.assertEqual(self.w.needs(at(16, 30), self.st)[1], [])          # was "You are hungry.": counted from 07:00
        self.assertIn("You are hungry.", self.w.needs(at(17, 30), self.st)[1])

    def test_a_snack_after_the_meal_still_pushes_hunger_back_two_hours(self):
        self.st["last_meal"] = "2026-10-03T12:00+05:30"
        self.w.feed(self.st, at(14, 30), "snack")
        self.assertEqual(self.w.fed_at(at(18), self.st), at(14))

    def test_eight_samosas_are_a_meal_and_no_more(self):
        self.st["last_meal"] = "2026-09-25T13:00+05:30"                   # the review's case: a meal nine days old
        for _ in range(8):
            self.w.feed(self.st, at(12), "snack")
        self.assertEqual(self.w.fed_at(at(20), self.st), at(12))
        self.assertEqual(self.w.needs(at(12, 40), self.st)[1], [])          # was "You are very hungry."

    def test_a_meal_clears_the_snacks(self):
        self.st["last_meal"] = "2026-10-03T07:00+05:30"
        self.w.feed(self.st, at(15), "snack")
        self.w.feed(self.st, at(19), "meal")
        self.assertNotIn("fed_at", self.st)
        self.assertEqual(self.w.fed_at(at(20), self.st), at(19))

    def test_a_state_from_before_the_fix_is_read_as_it_was(self):
        self.st.update(last_meal="2026-10-03T12:00+05:30", snacks=1)
        self.assertEqual(self.w.fed_at(at(18), self.st), at(14))


class EatAwayTest(unittest.TestCase):
    def setUp(self):
        self.w, self.st = World(repairs=True), state()
        self.st["place"] = "khan"

    def errors(self, when, **kw):
        sit, ctx = self.w.situation(when, self.st, {"segments": [], "entries": [], "steps": []}, None)
        return self.w.check(answer(**kw), sit, ctx, self.st)[0]

    def test_eating_where_nothing_is_bought_is_refused(self):
        errors = self.errors(at(13), action="eat", place="khan")
        self.assertTrue(any("nothing to eat at Khan Market" in e for e in errors), errors)

    def test_eating_what_he_buys_is_not(self):
        self.assertEqual(self.errors(at(13), action="eat", place="khan", buys=[{"item": "chole bhature", "price_inr": 180}]), [])

    def test_eating_what_he_has_just_bought_there_is_not(self):
        play(self.w, self.st, at(13), action="buy", place="khan", buys=[{"item": "chole bhature", "price_inr": 180}], minutes=15)
        self.assertEqual(self.errors(at(13, 15), action="eat", place="khan"), [])
        self.assertTrue(self.errors(at(15, 30), action="eat", place="khan"))             # not two hours later

    def test_the_habitat_centre_has_its_cafe_and_food_court(self):
        self.w = World(repairs=True, culture=True)                       # its own sights show a café; it sold nothing before
        self.st["place"] = "habitat"
        errors = self.errors(at(13), action="eat", place="habitat")
        self.assertTrue(any("A thali at the food court" in e for e in errors), errors)
        self.assertEqual(self.errors(at(13), action="eat", place="habitat", buys=[{"item": "a thali", "price_inr": 450}]), [])

    def test_a_place_that_sells_no_food(self):
        self.st["place"] = "iic"
        errors = self.errors(at(13), action="eat", place="iic")
        self.assertTrue(any("no food is sold here" in e for e in errors), errors)


class GoneTest(unittest.TestCase):
    def test_an_answer_from_someone_whose_hours_have_ended_says_so(self):
        w, st = World(repairs=True), state()
        name = w.cast["ramesh"]["name"]
        here = w.present_ids("home", at(10), st)
        self.assertIn("ramesh", here)
        voice = {"by": name, "says": "The tea is ready, sahib."}
        sit, _ = w.situation(at(10), st, {"segments": [], "entries": [], "steps": []}, {"end": "10:00", "voice": voice})
        self.assertIn("The tea is ready, sahib.", sit["event"])
        self.assertNotIn("has gone", sit["event"])
        late = next(h for h in range(18, 24) if "ramesh" not in w.present_ids("home", at(h), state()))
        st = state()
        sit, _ = w.situation(at(late), st, {"segments": [], "entries": [], "steps": []}, {"end": f"{late:02d}:00", "voice": voice})
        self.assertIn(f"The tea is ready, sahib.” {name} has gone.", sit["event"])


class WardrobeTest(unittest.TestCase):
    def setUp(self):
        self.w, self.st = World(repairs=True), state()
        self.st["flags"]["bandhgala"] = "collected"
        self.st["wardrobe"][-1]["status"] = "Collected from Masterji."

    def test_he_changes_at_home_before_a_formal_place_and_takes_off_the_kurta(self):
        day = play(self.w, self.st, at(10), action="walk", place="iic")
        self.assertEqual(self.st["wearing"], "bandhgala")
        kurta = self.w.garment(self.st, "kurta")
        self.assertTrue(kurta["status"].startswith("Taken off at"), kurta)
        worn = [e for e in day["entries"] if e.get("k") == "wear"]
        self.assertEqual([e["item"] for e in worn], ["Bandhgala, charcoal"])

    def test_he_does_not_change_away_from_home(self):
        self.st["place"] = "khan"
        play(self.w, self.st, at(11), action="walk", place="iic")
        self.assertEqual(self.st["wearing"], "kurta")                       # was changed at Khan Market, and again on arrival
        self.assertEqual(self.w.garment(self.st, "bandhgala")["status"], "Collected from Masterji.")


class OffTest(unittest.TestCase):
    """Off by default, and off nothing changes (tests/test_opened.py holds the ten days to the byte)."""

    def test_the_switch(self):
        self.assertFalse(Config({}).world_repairs)
        self.assertTrue(Config({"HEGEL_WORLD_REPAIRS": "1"}).world_repairs)
        self.assertFalse(World().repairs)

    def test_off_the_plate_is_drawn_by_the_hour_and_eating_away_is_not_refused(self):
        w, st = World(), state()
        self.assertEqual(w.plate_seed(at(15, 10), st), "plate|2026-10-03|15")
        st["place"] = "khan"
        sit, ctx = w.situation(at(13), st, {"segments": [], "entries": [], "steps": []}, None)
        self.assertEqual(w.check(answer(action="eat", place="khan"), sit, ctx, st)[0], [])

    def test_off_a_snack_leaves_no_new_field(self):
        w, st = World(), state()
        st["last_meal"] = "2026-10-03T07:00+05:30"
        w.feed(st, at(15), "snack")
        self.assertNotIn("fed_at", st)
        self.assertEqual(w.fed_at(at(16), st), at(9))


if __name__ == "__main__":
    unittest.main()
