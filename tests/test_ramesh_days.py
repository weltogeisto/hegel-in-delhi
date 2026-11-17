"""Ramesh's days, both ways (DECISIONS 47). Short of money, Hegel may agree that Ramesh comes three days a week for
half the wage (ramesh_parttime). With HEGEL_RAMESH_DAYS on, once nothing is owed for the wage or the groceries and
what is left after everything owed holds two months of the full wage, Ramesh offers to come every day but Wednesday
again (ramesh_fulltime). Each yes lets the opposite offer be made again later. Off, the offer does not exist."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import D, There, fresh, look, offer  # noqa: E402

from world.config import Config  # noqa: E402
from world.world import World, at_dt  # noqa: E402

THU = D(19, 11)          # a Thursday: Ramesh comes on either schedule


def part_time(cash=30000, owed=()):
    st = fresh(settled=THU.isoformat())                  # no cost falls due during the test
    st["flags"]["ramesh_parttime"] = True
    st["beats"].append("ramesh_parttime")               # he said yes to it once
    st["owed"], st["imprest"] = list(owed), cash
    return st


def wage(amount=4000):
    return {"to": "Ramesh", "amount": amount, "why": "the wage for cooking, three days a week", "since": "2026-11-01",
            "cost": "wage", "item": "Ramesh's wage for cooking, three days a week", "at": "home", "with": "ramesh"}


def groceries(amount=900):
    return {"to": "Ramesh", "amount": amount, "why": "groceries", "since": "2026-11-15", "cost": "groceries",
            "item": "Groceries for Ramesh's kitchen", "at": "home", "with": "ramesh"}


class WayBackTest(unittest.TestCase):
    def setUp(self):
        self.w = World(ramesh_days=True)

    def beat(self, st, t=None):
        with There(home=["ramesh"]):
            return (look(self.w, t or at_dt(THU, 600), st, "home")[1]["beat"] or {}).get("id")

    def week(self, st):
        return {D(n, 11).strftime("%a"): "ramesh" in self.w.present_ids("home", at_dt(D(n, 11), 540), st) for n in range(16, 23)}

    def test_offered_once_paid_up_with_two_months_in_hand(self):
        st = part_time()
        with There(home=["ramesh"]):
            oid, out = offer(self.w, at_dt(THU, 600), st, "home")
        self.assertEqual(oid, "ramesh_fulltime")
        self.assertIn("every day but Wednesday", out[-1]["text"])
        self.assertIs(st["flags"]["ramesh_parttime"], False)
        self.assertNotIn("ramesh_parttime", st["beats"])                          # short of money again, he may be offered it
        self.assertEqual(self.week(st), {"Mon": True, "Tue": True, "Wed": False, "Thu": True, "Fri": True, "Sat": True, "Sun": True})
        grocery_due = [o for o in self.w.accrue(at_dt(D(22, 11), 540), st) if o["cost"] == "groceries"]     # accrue moves the books on,
        self.assertEqual([o["amount"] for o in grocery_due], [1500])                                     # so the earlier date first
        wage_due = [o for o in self.w.accrue(at_dt(D(1, 12), 540), st) if o["cost"] == "wage"]
        self.assertEqual([(o["amount"], o["why"]) for o in wage_due], [(8000, "the wage for cooking")])

    def test_not_while_wage_or_groceries_stand_owed(self):
        for owed in ([wage()], [groceries()]):
            with self.subTest(owed=owed[0]["cost"]):
                st = part_time(owed=owed)
                self.assertNotEqual(self.beat(st), "ramesh_fulltime")
                self.assertEqual(st["owed"], [])                                  # paid in that same moment, Ramesh being there
                self.assertEqual(self.beat(st, at_dt(THU, 630)), "ramesh_fulltime")   # so the offer comes at the next one

    def test_not_with_a_thin_purse(self):
        self.assertNotEqual(self.beat(part_time(cash=15999)), "ramesh_fulltime")
        self.assertEqual(self.beat(part_time(cash=16000)), "ramesh_fulltime")

    def test_not_unless_he_is_on_three_days(self):
        st = part_time()
        st["flags"].pop("ramesh_parttime")
        self.assertNotEqual(self.beat(st), "ramesh_fulltime")

    def test_not_away_from_home_or_without_ramesh(self):
        st = part_time()
        with There(home=[]):
            self.assertNotEqual((look(self.w, at_dt(THU, 600), st, "home")[1]["beat"] or {}).get("id"), "ramesh_fulltime")
        with There(khan=["ramesh"]):
            self.assertNotEqual((look(self.w, at_dt(THU, 600), st, "khan")[1]["beat"] or {}).get("id"), "ramesh_fulltime")

    def test_a_no_keeps_three_days_and_comes_back_after_a_week(self):
        st = part_time()
        with There(home=["ramesh"]):
            oid, out = offer(self.w, at_dt(THU, 600), st, "home", yes=False)
        self.assertEqual(oid, "ramesh_fulltime")
        self.assertIn("three days a week", out[-1]["text"])
        self.assertIs(st["flags"]["ramesh_parttime"], True)
        st["costs"] = {c["id"]: D(28, 11).isoformat() for c in self.w.costs}     # nothing falls due meanwhile
        self.assertNotEqual(self.beat(st, at_dt(D(23, 11), 600)), "ramesh_fulltime")
        self.assertEqual(self.beat(st, at_dt(D(26, 11), 600)), "ramesh_fulltime")

    def test_short_again_he_may_go_back_to_three_days_and_later_up_again(self):
        st = part_time()
        with There(home=["ramesh"]):
            self.assertEqual(offer(self.w, at_dt(THU, 600), st, "home")[0], "ramesh_fulltime")
        st["owed"], st["imprest"] = [dict(wage(8000), why="the wage for cooking", item="Ramesh's wage for cooking")], 500
        with There(home=["ramesh"]):
            oid, _ = offer(self.w, at_dt(D(21, 11), 600), st, "home")
        self.assertEqual(oid, "ramesh_parttime")
        self.assertIs(st["flags"]["ramesh_parttime"], True)
        self.assertNotIn("ramesh_fulltime", st["beats"])                           # the way back is open again
        self.assertEqual([o["amount"] for o in st["owed"] if o.get("cost") == "wage"], [4000])


    def test_a_bill_falling_due_in_that_moment_counts_against_the_purse(self):
        sat = at_dt(D(21, 11), 540)                     # the dhobi falls due on Saturday, a day Ramesh comes
        due = sum(c["amount"] for c in self.w.falling_due(sat, part_time()))
        self.assertGreaterEqual(due, 300)
        self.assertNotEqual(self.beat(part_time(cash=16000 + due - 1), sat), "ramesh_fulltime")
        self.assertEqual(self.beat(part_time(cash=16000 + due), sat), "ramesh_fulltime")

    def test_a_wage_falling_due_in_that_moment_holds_the_offer_back(self):
        mon = at_dt(D(1, 2).replace(year=2027), 540)    # 1 February 2027, a Monday: the month's wage falls due as he wakes
        st = part_time()
        st["costs"] = {c["id"]: "2027-01-31" for c in self.w.costs}
        self.assertNotEqual(self.beat(st, mon), "ramesh_fulltime")
        self.assertFalse([o for o in st["owed"] if o.get("cost") == "wage"])                # accrued and paid in that moment
        self.assertEqual(self.beat(st, at_dt(D(1, 2).replace(year=2027), 570)), "ramesh_fulltime")

    def test_what_he_owes_elsewhere_counts_too(self):
        st = part_time(cash=25000, owed=[{"to": "the Directorate of Estates", "amount": 9294, "why": "queried vouchers",
                                          "since": "2026-11-05", "at": "estates", "with": "saxena"}])
        self.assertNotEqual(self.beat(st), "ramesh_fulltime")                                # 25,000 less 9,294 is short of 16,000
        st["imprest"] = 25294
        self.assertEqual(self.beat(st), "ramesh_fulltime")


class SwitchTest(unittest.TestCase):
    def test_off_by_default_the_offer_does_not_exist(self):
        self.assertFalse(Config({}).ramesh_days)
        self.assertTrue(Config({"HEGEL_RAMESH_DAYS": "1"}).ramesh_days)
        self.assertNotIn("ramesh_fulltime", [b["id"] for b in World().beats])
        self.assertIn("ramesh_fulltime", [b["id"] for b in World(ramesh_days=True).beats])
        st = part_time()
        with There(home=["ramesh"]):
            beat = look(World(), at_dt(THU, 600), st, "home")[1]["beat"]
        self.assertNotEqual((beat or {}).get("id"), "ramesh_fulltime")
        self.assertIs(st["flags"]["ramesh_parttime"], True)

    def test_the_rehearsal_and_the_tick_build_the_same_world(self):
        from world.__main__ import make_world
        cfg = Config({"HEGEL_RAMESH_DAYS": "1", "HEGEL_FEEDS": "0"})
        self.assertIn("ramesh_fulltime", [b["id"] for b in make_world(cfg).beats])


if __name__ == "__main__":
    unittest.main()
