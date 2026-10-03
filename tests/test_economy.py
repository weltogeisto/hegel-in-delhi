"""Tests for the simulated economy: cash and vouchers, the Directorate's recoupment, the offers and what follows them,
the costs that recur and what stops when they go unpaid, home payments and gifts, and the prompt's Money line."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import DAY1, REPO, Sandbox, answer, state  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import contract  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World, at_dt  # noqa: E402

D = lambda day, month=10: date(2026, month, day)      # October unless said


class There:
    """Who is where: a stand-in for World.present_ids, so that a test needs no luck with the cast's chances."""

    def __init__(self, **where):
        self.where = where

    def __enter__(self):
        self.patch = mock.patch.object(World, "present_ids", lambda w, pid, t, st: list(self.where.get(pid, [])))
        self.patch.start()
        return self

    def __exit__(self, *exc):
        self.patch.stop()


PLOT = ["hegde_note", "hegde_call", "hegde_card", "saxena_file", "saxena_query", "bandhgala_ready", "hegde_gate"]


def fresh(settled="2026-10-09", **kw):
    """Day 1's closing state, with the economy's keys, the Hegde file out of the way and the costs settled up to a date (None: not yet
    looked at, so that the first situation starts them)."""
    st = World().ledger(state())
    st["account"]["vouchers"] = []
    st["beats"] += PLOT
    if settled:
        st["costs"] = {c["id"]: settled for c in World().costs}
    st.update(kw)
    return st


def look(w, t, st, pid):
    """The situation at t with him at pid, over an empty day."""
    st["place"] = pid
    return w.situation(t, st, {"steps": [], "entries": []}, None)


def act(w, t, st, pid, ans):
    """One whole step by hand: the situation, the rules, the step. Returns (errors, entries of the step)."""
    st["place"], day = pid, {"segments": [], "entries": [], "steps": []}
    sit, ctx = w.situation(t, st, day, None)
    errors, _, rep = w.check(ans, sit, ctx, st)
    if errors:
        return errors, []
    w.apply(rep[0], rep[1], sit, ctx, st, day)
    return [], day["entries"]


def offer(w, t, st, pid, yes=True):
    """The offer made at t (if any), fired and answered as the engine does. Returns (beat id, entries)."""
    sit, ctx = look(w, t, st, pid)
    beat = ctx["beat"]
    if not beat:
        return None, []
    out = w.fire(beat, t, st)
    if beat.get("choice"):
        out += w.settle_choice(beat, yes, st, t)
    return beat["id"], out


def kinds(entries):
    return [e["k"] for e in entries]


class StateTest(unittest.TestCase):
    def test_a_state_from_before_the_economy_gets_its_keys(self):
        st = state()
        for k in ("account", "owed", "cheques", "tech"):
            self.assertNotIn(k, st)
        World().ledger(st)
        self.assertEqual(st["account"], {"advance": 15000, "vouchers": [], "admitted": 0, "queried": 0})
        self.assertEqual((st["owed"], st["cheques"], st["tech"]), ([], [], {"phone": False, "sim": False}))
        self.assertEqual(st["met_days"]["nidhi"], ["2026-10-02"])                  # those he met on day 1 were met that day
        again = copy.deepcopy(st)
        World().ledger(st)
        self.assertEqual(st, again)                                                # and the keys are only defaults

    def test_day_ones_purchases_become_vouchers_on_the_first_new_day(self):
        box = Sandbox()
        try:
            e = box.engine()
            day = e.new_day(box.days.load(date(2026, 10, 2)), D(3))
            acc = day["state"]["account"]
            self.assertEqual(acc["advance"], 15000)
            self.assertEqual(len(acc["vouchers"]), 7)
            self.assertEqual(sum(v["price"] for v in acc["vouchers"]), 4499)                 # day 1's ₹4,499 spent, all vouchered
            self.assertEqual({v["item"] for v in acc["vouchers"] if v["office"]}, {"Fountain pen and a bound notebook"})
            self.assertEqual(sum(v["price"] for v in acc["vouchers"] if v["office"]), 640)
            self.assertEqual(day["state"]["imprest"], 10501)                                  # and ₹10,501 left in cash
            self.assertEqual(day["opening"]["imprest"], 10501)
            self.assertEqual(day["opening"]["cash"], 10501)
            self.assertEqual(day["opening"]["account"], acc)
            self.assertEqual((day["opening"]["owed"], day["opening"]["cheques"]), ([], []))
            self.assertEqual(day["state"]["visits"]["khan"], ["2026-10-02"])
            self.assertNotIn("account", box.days.load(date(2026, 10, 2))["state"])             # day 1's file is untouched
        finally:
            box.close()

    def test_day_one_is_as_it_was(self):
        bag = [x for x in DAY1["entries"] if x["k"] == "bag"]
        self.assertEqual(sum(x["price"] for x in bag), 4499)
        self.assertEqual(DAY1["state"]["imprest"], 10501)
        self.assertNotIn("cash", DAY1["opening"])                                              # nothing was added to the old file


class RenderTest(unittest.TestCase):
    GOLDEN = "d60b6f75dc60d6aeb3fc8e835b922fb42540d13f19b214892d6e23140668a27c"      # sha256 of the twenty renders before the economy

    def test_the_bakeoff_renders_byte_for_byte_as_before(self):
        sits = json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"]
        text = "\x00".join(contract.render(s) for s in sits)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), self.GOLDEN)
        self.assertIn("Imprest left: ₹", text)
        self.assertNotIn("Cash:", text)

    def test_the_live_world_says_cash(self):
        sit, _ = look(World(), at_dt(D(6), 600), fresh(), "home")
        text = contract.render(sit)
        self.assertIn("Cash: ₹10,501.", text)
        self.assertNotIn("Imprest left", text)

    def test_looks_up_is_optional_in_the_contract(self):
        self.assertIn("looks_up", contract.SCHEMA["properties"])
        self.assertNotIn("looks_up", contract.SCHEMA["required"])
        for ok in (answer(), answer(looks_up=None), answer(looks_up="Karl Marx")):
            self.assertEqual(contract.check_shape(ok)[0], [])
        for bad in (answer(looks_up=3), answer(looks_up="x" * 101)):
            self.assertTrue(contract.check_shape(bad)[0])

    def test_the_cash_check_names_cash(self):
        w, st = World(), fresh()
        st["imprest"] = 10
        errors, _ = act(w, at_dt(D(3), 720), st, "khan", answer(action="buy", place="khan", buys=[{"item": "chai", "price_inr": 20}]))
        self.assertEqual(errors, ["that costs ₹20 and you have only ₹10 in cash"])


class MoneyLineTest(unittest.TestCase):
    def line(self, st, t=None):
        sit, _ = look(World(), t or at_dt(D(9), 600), st, "khan")                                  # away from home and the Directorate: nothing is paid
        return next(x for x in sit["on_mind"] if x.startswith("Money:"))

    def test_cash_vouchers_debts_cheques_and_the_next_cost(self):
        st = fresh()
        self.assertEqual(self.line(st), "Money: cash ₹10,501; next: the dhobi ₹300 Sat 10 Oct.")
        st = fresh()
        st["account"]["vouchers"] = [{"date": "2026-10-02", "t": "10:00", "item": "x", "price": 4499, "office": False}] * 1
        st["owed"] = [{"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "2026-10-04", "at": "home", "with": "ramesh"},
                      {"to": "the Directorate of Estates", "amount": 3859, "why": "queried vouchers", "since": "2026-10-05", "at": "estates", "with": "saxena"}]
        st["cheques"] = [{"from": "the IIC", "amount": 10000, "since": "2026-10-12"}]
        line = self.line(st)
        self.assertEqual(line, "Money: cash ₹10,501; 1 voucher pending ₹4,499; owes Ramesh ₹1,500 (groceries), the Directorate of Estates ₹3,859 (queried vouchers); "
                               "1 cheque ₹10,000 uncashed; next: the dhobi ₹300 Sat 10 Oct.")
        self.assertLessEqual(len(line), 200)

    def test_it_stays_compact_with_a_heap_of_debts(self):
        st = fresh()
        st["account"]["vouchers"] = [{"date": "2026-10-02", "t": "10:00", "item": "x", "price": 120, "office": False}] * 12
        st["owed"] = [{"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "x", "at": "home"}, {"to": "Ramesh", "amount": 8000, "why": "the wage for cooking", "since": "x", "at": "home"},
                      {"to": "the dhobi", "amount": 300, "why": "the washing", "since": "x", "at": "home"}, {"to": "the electricity company", "amount": 1800, "why": "electricity", "since": "x", "at": "home"},
                      {"to": "the Directorate of Estates", "amount": 3859, "why": "queried vouchers", "since": "x", "at": "estates"}]
        st["cheques"] = [{"from": "a", "amount": 10000, "since": "x"}] * 2
        line = self.line(st)
        self.assertLessEqual(len(line), 200)
        self.assertEqual(line, "Money: cash ₹10,501; 12 vouchers pending ₹1,440; owes Ramesh ₹9,500, the dhobi ₹300, the electricity company ₹1,800 and 1 more; "
                               "2 cheques ₹20,000 uncashed; next: the dhobi ₹300 Sat 10 Oct.")
        st["owed"] += [{"to": "Mr. R. K. Malhotra", "amount": 5000, "why": "the loan", "since": "x", "with": "malhotra"}]
        line = self.line(st)
        self.assertLessEqual(len(line), 200)
        self.assertIn("owes Ramesh ₹9,500, the dhobi ₹300, the electricity company ₹1,800 and 2 more", line)
        st["owed"] = [{"to": "the Directorate of Estates", "amount": 3859, "why": "queried vouchers", "since": "x", "at": "estates"},
                      {"to": "Mr. R. K. Malhotra", "amount": 5000, "why": "the loan", "since": "x", "with": "malhotra"},
                      {"to": "the electricity company", "amount": 1800, "why": "electricity", "since": "x", "at": "home"},
                      {"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "x", "at": "home"}, {"to": "the dhobi", "amount": 300, "why": "the washing", "since": "x", "at": "home"}]
        st["account"]["vouchers"] = [{"date": "2026-10-02", "t": "10:00", "item": "x", "price": 1200, "office": False}] * 40
        st["cheques"] = [{"from": "a", "amount": 10000, "since": "x"}] * 12
        line = self.line(st)
        self.assertLessEqual(len(line), 200)
        self.assertIn("owes the Directorate ₹3,859, Mr. R. K. Malhotra ₹5,000 and 3 more", line)           # when even that is too long: fewer of them, by shorter names

    def test_a_phone_with_a_sim_is_remembered_in_the_prompt(self):
        st = fresh()
        sit, _ = look(World(), at_dt(D(3), 600), st, "home")
        self.assertFalse(any("phone" in x for x in sit["on_mind"]))
        st["tech"] = {"phone": True, "sim": True}
        sit, _ = look(World(), at_dt(D(3), 640), st, "home")
        self.assertIn("You have a phone with a SIM: you may look something up (looks_up).", sit["on_mind"])


class VoucherTest(unittest.TestCase):
    def setUp(self):
        self.w, self.st = World(), fresh()
        self.t = at_dt(D(3), 720)

    def test_every_purchase_leaves_a_voucher_and_office_things_are_marked(self):
        buys = [{"item": "notebook", "price_inr": 120}, {"item": "ink", "price_inr": 90}, {"item": "a stationery set", "price_inr": 160},
                {"item": "newspapers", "price_inr": 45}, {"item": "chai", "price_inr": 20}, {"item": "samosa", "price_inr": 30}]
        errors, entries = act(self.w, self.t, self.st, "khan", answer(action="buy", place="khan", buys=buys))
        self.assertEqual(errors, [])
        vouchers = self.st["account"]["vouchers"]
        self.assertEqual([(v["item"], v["price"], v["office"]) for v in vouchers], [
            ("Notebook, bound", 120, True), ("Ink cartridges", 90, True), ("Stationery set", 160, True), ("Newspapers", 45, True),
            ("Chai, a cup", 20, False), ("Samosa", 30, False)])
        self.assertTrue(all(v["date"] == "2026-10-03" and v["t"] == "12:00" for v in vouchers))
        self.assertEqual(self.st["imprest"], 10501 - 465)
        self.assertEqual([e.get("office") for e in entries if e["k"] == "bag"], [True, True, True, True, None, None])

    def test_a_book_and_a_gift_are_personal(self):
        errors, _ = act(self.w, self.t, self.st, "khan", answer(action="buy", place="khan", buys=[{"item": "a Hindi dictionary", "price_inr": 300}]))
        self.assertEqual(errors, [])
        self.assertEqual([v["office"] for v in self.st["account"]["vouchers"]], [False])

    def go_through(self, st, day=D(5), minute=700, saxena=True):
        with There(estates=["saxena"] if saxena else []):
            return look(self.w, at_dt(day, minute), st, "estates")

    def test_mr_saxena_refills_what_is_office_and_queries_the_rest(self):
        st = self.st
        st["account"]["vouchers"] = [{"date": "2026-10-03", "t": "12:30", "item": "Notebook, bound", "price": 120, "office": True},
                                     {"date": "2026-10-03", "t": "12:31", "item": "Ink cartridges", "price": 90, "office": True},
                                     {"date": "2026-10-03", "t": "12:40", "item": "Mobile phone", "price": 9000, "office": False}]
        st["imprest"] = 1000
        sit, ctx = self.go_through(st)
        self.assertIn("Mr. Saxena goes through your vouchers: ₹210 is admitted and refilled to you in cash; ₹9,000 is queried as personal and will be recovered from you.", sit["event"])
        self.assertEqual(st["imprest"], 1210)
        self.assertEqual(st["account"], {"advance": 15000, "vouchers": [], "admitted": 210, "queried": 9000})
        self.assertEqual(st["owed"][0]["to"], "the Directorate of Estates")
        self.assertEqual((st["owed"][0]["amount"], st["owed"][0]["why"]), (9000, "queried vouchers"))
        income = next(e for e in ctx["public"] if e["k"] == "income")
        self.assertEqual((income["amount"], income["item"], income["recoup"]), (210, "Imprest refilled against vouchers", {"admitted": 210, "queried": 9000}))
        filed = next(e for e in ctx["public"] if e["k"] == "file")
        self.assertIn("queries ₹9,000", filed["text"])
        self.assertEqual(filed["owe"]["amount"], 9000)
        sit2, ctx2 = look(self.w, at_dt(D(5), 740), st, "estates")                       # the same visit: nothing more
        self.assertNotIn("goes through", sit2["event"])

    def test_only_office_spending_or_only_personal(self):
        st = self.st
        st["account"]["vouchers"] = [{"date": "2026-10-03", "t": "12:30", "item": "Ink", "price": 90, "office": True}]
        sit, ctx = self.go_through(st)
        self.assertIn("₹90 is admitted and refilled to you in cash; nothing is queried.", sit["event"])
        self.assertEqual(kinds(ctx["public"]), ["income"])
        self.assertEqual(st["owed"], [])
        st["account"]["vouchers"] = [{"date": "2026-10-03", "t": "12:30", "item": "Tea", "price": 220, "office": False}]
        st["account"]["vouchers"] = [{"date": "2026-10-03", "t": "12:30", "item": "Tea", "price": 220, "office": False}]
        look(self.w, at_dt(D(5), 800), st, "home")                                         # he leaves: the visit is over
        sit, ctx = self.go_through(st, minute=900)
        self.assertIn("nothing is admitted; ₹220 is queried", sit["event"])
        self.assertEqual(kinds(ctx["public"]), ["file"])
        self.assertEqual(ctx["public"][0]["recoup"], {"admitted": 0, "queried": 220})        # the page clears its vouchers on this one

    def test_once_a_visit_not_once_a_day(self):
        st = self.st
        st["account"]["vouchers"] = [{"date": "2026-10-03", "t": "12:30", "item": "Ink", "price": 90, "office": True}]
        self.go_through(st, minute=600)
        st["account"]["vouchers"] = [{"date": "2026-10-05", "t": "11:00", "item": "Ink", "price": 90, "office": True}]
        sit, _ = self.go_through(st, minute=640)
        self.assertNotIn("goes through", sit["event"])                                      # the same visit
        look(self.w, at_dt(D(5), 700), st, "khan")
        sit, _ = self.go_through(st, minute=900)
        self.assertIn("goes through", sit["event"])                                         # a second visit, with new vouchers

    def test_not_at_the_weekend_nor_on_a_holiday_nor_with_nothing_to_show(self):
        st = self.st
        st["account"]["vouchers"] = [{"date": "2026-10-03", "t": "12:30", "item": "Ink", "price": 90, "office": True}]
        for day in (D(3), D(4), D(20)):                                                      # Saturday, Sunday, Dussehra
            sit, ctx = self.go_through(st, day=day)
            self.assertNotIn("goes through", sit["event"], day)
        self.assertEqual(len(st["account"]["vouchers"]), 1)
        st["account"]["vouchers"] = []
        sit, ctx = self.go_through(st, day=D(6))
        self.assertNotIn("goes through", sit["event"])

    def test_what_is_queried_is_repaid_on_a_later_visit_when_he_can(self):
        st = self.st
        st["owed"] = [{"to": "the Directorate of Estates", "amount": 3859, "why": "queried vouchers", "since": "2026-10-05", "at": "estates",
                       "with": "saxena", "after": "2026-10-06"}]
        sit, ctx = self.go_through(st, day=D(5), minute=900)
        self.assertEqual(len(st["owed"]), 1)                                                # not on the day it was queried
        with There(estates=["saxena"]):
            sit, ctx = look(self.w, at_dt(D(6), 700), st, "estates")
        self.assertEqual(st["owed"], [])
        self.assertEqual(st["imprest"], 10501 - 3859)
        self.assertEqual([(e["k"], e["amount"], e["to"], e["settles"]) for e in ctx["public"] if e["k"] == "expense"], [("expense", 3859, "the Directorate of Estates", True)])
        st["owed"] = [{"to": "the Directorate of Estates", "amount": 99999, "why": "queried vouchers", "since": "2026-10-05", "at": "estates", "with": "saxena"}]
        with There(estates=["saxena"]):
            sit, ctx = look(self.w, at_dt(D(6), 800), st, "estates")
        self.assertIn("asks for ₹99,999", sit["event"])                                      # he cannot pay it: it stands, and he is asked
        self.assertEqual(len(st["owed"]), 1)


class OfferTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def test_the_offers_are_all_there_and_none_is_made_out_of_nothing(self):
        ids = [b["id"] for b in self.w.beats]
        for oid in ("tutoring_german", "iic_talk", "iic_talk_day", "sell_frock", "loan_malhotra", "essay_fee", "diwali_bakshish"):
            self.assertIn(oid, ids)
        for t, pid in ((at_dt(D(3), 700), "home"), (at_dt(D(3), 900), "khan"), (at_dt(D(6), 900), "lodhi")):
            with There():
                self.assertIsNone(look(self.w, t, fresh(), pid)[1]["beat"])

    # tutoring
    def test_tutoring_is_offered_by_nidhi_once_he_has_met_her_on_two_days(self):
        with There(khan=["nidhi", "masterji"]):
            self.assertIsNone(look(self.w, at_dt(D(2), 800), fresh(), "khan")[1]["beat"])           # on day 1 itself he has met her on one day only
            beat = look(self.w, at_dt(D(3), 800), fresh(), "khan")[1]["beat"]
        self.assertEqual(beat["id"], "tutoring_german")
        self.assertIn("Nidhi says her cousin Ananya needs German before a semester in Leipzig", beat["prompt"])
        self.assertIn("₹1,000 each", beat["prompt"])
        with There(khan=["masterji"]):
            self.assertNotEqual((look(self.w, at_dt(D(3), 800), fresh(), "khan")[1]["beat"] or {}).get("id"), "tutoring_german")       # nobody to ask him

    def test_yes_sets_two_lessons_a_week_and_no_brings_it_back_after_a_fortnight(self):
        w, st, t = self.w, fresh(), at_dt(D(3), 800)
        with There(khan=["nidhi"]):
            oid, out = offer(w, t, st, "khan", yes=False)
            self.assertEqual(oid, "tutoring_german")
            self.assertEqual(st["engagements"], [])
            self.assertNotIn("tutoring_german", st["beats"])
            self.assertEqual(st["refused"]["tutoring_german"], "2026-10-03")
            self.assertIsNone(look(w, at_dt(D(10), 800), st, "khan")[1]["beat"])             # a week later: not yet
            self.assertIsNone(look(w, at_dt(D(16), 800), st, "khan")[1]["beat"])
            self.assertEqual(look(w, at_dt(D(17), 800), st, "khan")[1]["beat"]["id"], "tutoring_german")      # fourteen days on
            oid, out = offer(w, at_dt(D(17), 800), st, "khan", yes=True)
        self.assertEqual(oid, "tutoring_german")
        (e,) = st["engagements"]
        self.assertEqual((e["days"], e["t"], e["minutes"], e["place"], e["with"], e["pay"], e["from"]), ("Tue,Fri", "17:00", 60, "home", "ananya", 1000, "2026-10-18"))
        self.assertIn("tutoring_german", st["beats"])
        with There(khan=["nidhi"]):
            self.assertIsNone(look(w, at_dt(D(31), 800), st, "khan")[1]["beat"])             # offered at most once more, and taken

    def test_a_session_brings_the_cousin_and_pays_in_cash_after_the_hour(self):
        w, st = self.w, fresh()
        with There(khan=["nidhi"]):
            offer(w, at_dt(D(3), 800), st, "khan")
        self.assertIn("Tuesday 6 October 17:00: German lesson for Ananya, at home, ₹1,000 in cash.", look(w, at_dt(D(5), 600), st, "home")[0]["on_mind"])
        self.assertIsNone(look(w, at_dt(D(6), 16 * 60 + 55), st, "home")[1]["beat"])                # not yet five
        self.assertEqual(w.interrupt(at_dt(D(6), 16 * 60), at_dt(D(6), 19 * 60), st, "home"), at_dt(D(6), 17 * 60))     # the world stops his step at five
        self.assertEqual(w.interrupt(at_dt(D(6), 16 * 60), at_dt(D(6), 19 * 60), st, "khan"), at_dt(D(6), 19 * 60))
        sit, ctx = look(w, at_dt(D(6), 17 * 60), st, "home")
        self.assertEqual(ctx["beat"]["id"], "tutoring_german@2026-10-06")
        self.assertIn("Ananya, Nidhi's cousin", sit["present"])
        self.assertIn("Ananya, Nidhi's cousin, arrives for the German lesson. It runs until 18:00.", sit["event"])
        entries = w.fire(ctx["beat"], at_dt(D(6), 17 * 60), st)
        self.assertEqual(kinds(entries), ["world"])
        self.assertEqual(st["imprest"], 10501)                                              # nothing yet: after the hour
        self.assertEqual(len(st["receipts"]), 1)
        self.assertIn("ananya", w.present_ids("home", at_dt(D(6), 17 * 60 + 40), st))        # she is there for the lesson
        self.assertNotIn("ananya", w.present_ids("home", at_dt(D(6), 18 * 60 + 1), st))
        sit, ctx = look(w, at_dt(D(6), 17 * 60 + 40), st, "home")
        self.assertEqual(st["imprest"], 10501)
        sit, ctx = look(w, at_dt(D(6), 18 * 60), st, "home")
        income = [e for e in ctx["public"] if e["k"] == "income"]
        self.assertEqual([(e["item"], e["amount"], e["from"]) for e in income], [("German lesson", 1000, "Ananya")])
        self.assertEqual(income[0]["text"], "Ananya pays you ₹1,000 in cash.")
        self.assertIn("Ananya pays you ₹1,000 in cash.", sit["event"])
        self.assertEqual(st["imprest"], 11501)
        self.assertEqual(st["receipts"], [])

    def test_the_fee_waits_for_him_to_be_home_and_is_then_what_she_left(self):
        w, st = self.w, fresh()
        with There(khan=["nidhi"]):
            offer(w, at_dt(D(3), 800), st, "khan")
        w.fire(look(w, at_dt(D(6), 17 * 60), st, "home")[1]["beat"], at_dt(D(6), 17 * 60), st)
        sit, ctx = look(w, at_dt(D(6), 18 * 60 + 10), st, "khan")
        self.assertEqual(st["imprest"], 10501)
        sit, ctx = look(w, at_dt(D(6), 20 * 60), st, "home")
        self.assertEqual(st["imprest"], 11501)
        self.assertEqual(next(e for e in ctx["public"] if e["k"] == "income")["text"], "You collect ₹1,000 that Ananya left for you.")

    def test_two_missed_sessions_in_a_row_end_it_and_a_visit_in_between_does_not(self):
        w = self.w
        st = fresh()
        with There(khan=["nidhi"]):
            offer(w, at_dt(D(3), 800), st, "khan")
        sit, ctx = look(w, at_dt(D(6), 17 * 60 + 20), st, "khan")                          # Tuesday: he is out at five, and still has time
        self.assertEqual(st.get("missed"), None)
        sit, ctx = look(w, at_dt(D(6), 17 * 60 + 31), st, "khan")
        self.assertIn("tutoring_german@2026-10-06", st["missed"])
        self.assertIn("You missed the German lesson: Ananya waited and went away.", sit["event"])
        self.assertEqual([e["text"] for e in ctx["public"]], ["Ananya waited for the German lesson and went away: it was missed."])
        self.assertEqual(st["engagements"][0]["missed"], 1)
        w.fire(look(w, at_dt(D(9), 17 * 60), st, "home")[1]["beat"], at_dt(D(9), 17 * 60), st)       # Friday: he is there
        self.assertEqual(st["engagements"][0]["missed"], 0)
        look(w, at_dt(D(13), 18 * 60), st, "khan")                                         # next Tuesday: missed again
        self.assertEqual(st["engagements"][0]["missed"], 1)
        sit, ctx = look(w, at_dt(D(16), 18 * 60), st, "khan")                              # and the Friday after: the second in a row
        self.assertEqual(st["engagements"], [])
        self.assertTrue(any(e["k"] == "file" and "cancels the German lessons after 2 missed sessions" in e["text"] for e in ctx["public"]))
        self.assertFalse(any("German lesson" in x for x in look(w, at_dt(D(17), 600), st, "home")[0]["on_mind"]))
        self.assertIsNone(w.due_beat(at_dt(D(20), 17 * 60), st, "home"))

    # the talk at the IIC
    def test_the_programme_officer_asks_on_his_second_visit_and_the_cheque_follows_the_talk(self):
        w, st = self.w, fresh()
        with There(iic=["officer"]):
            self.assertIsNone(look(w, at_dt(D(5), 700), st, "iic")[1]["beat"])                   # his first visit to the IIC
            look(w, at_dt(D(5), 760), st, "home")
            sit, ctx = look(w, at_dt(D(7), 700), st, "iic")                                       # the second
            self.assertEqual(ctx["beat"]["id"], "iic_talk")
            self.assertIn("The programme officer of the Centre comes over. Mr. Malhotra has spoken well of you", sit["event"])
            self.assertIn("₹10,000, by cheque after the talk", sit["event"])
            w.fire(ctx["beat"], at_dt(D(7), 700), st)
            out = w.settle_choice(ctx["beat"], True, st, at_dt(D(7), 700))
        self.assertEqual(st["appointments"], [{"date": "2026-10-14", "t": "18:30", "what": "your talk at the IIC", "beat": "iic_talk_day"}])
        self.assertEqual(kinds(out), ["world"])
        self.assertIn("Wednesday 14 October 18:30: your talk at the IIC.", look(w, at_dt(D(8), 600), st, "home")[0]["on_mind"])
        with There(iic=["officer"]):
            self.assertIsNone(look(w, at_dt(D(13), 18 * 60 + 30), st, "iic")[1]["beat"])          # not before the day
            sit, ctx = look(w, at_dt(D(14), 18 * 60 + 30), st, "iic")
            self.assertEqual(ctx["beat"]["id"], "iic_talk_day")
            w.fire(ctx["beat"], at_dt(D(14), 18 * 60 + 30), st)
            self.assertEqual((st["cheques"], st["imprest"]), ([], 10501))                      # the cheque comes after the talk
            sit, ctx = look(w, at_dt(D(14), 19 * 60 + 20), st, "iic")
            self.assertEqual(st["cheques"], [])
            sit, ctx = look(w, at_dt(D(14), 19 * 60 + 35), st, "iic")
        self.assertEqual(st["cheques"], [{"from": "the India International Centre", "amount": 10000, "since": "2026-10-14"}])
        self.assertEqual(st["imprest"], 10501)                                                  # a cheque is not cash
        (e,) = [x for x in ctx["public"] if x["k"] == "income"]
        self.assertTrue(e["cheque"])
        self.assertEqual((e["amount"], e["item"]), (10000, "Honorarium for the talk at the IIC"))
        self.assertIn("You have no bank account to put it in.", e["text"])
        self.assertIn("1 cheque ₹10,000 uncashed", look(w, at_dt(D(15), 600), st, "home")[0]["on_mind"][-2])

    def test_a_talk_he_does_not_give_pays_nothing(self):
        w, st = self.w, fresh()
        st["appointments"].append({"date": "2026-10-14", "t": "18:30", "what": "your talk at the IIC", "beat": "iic_talk_day"})
        st["beats"].append("iic_talk")
        look(w, at_dt(D(14), 19 * 60 + 20), st, "home")
        self.assertIn("iic_talk_day", st["missed"])
        with There(iic=["officer"]):
            self.assertIsNone(look(w, at_dt(D(14), 20 * 60), st, "iic")[1]["beat"])
        self.assertEqual((st["cheques"], st["receipts"]), ([], []))

    def test_the_talk_wants_a_second_visit_malhotra_known_and_the_officer_there(self):
        w = self.w
        with There(iic=["officer"]):
            st = fresh()
            st["visits"]["iic"] = ["2026-10-03"]
            st["people"].remove("malhotra")
            self.assertIsNone(look(w, at_dt(D(5), 700), st, "iic")[1]["beat"])                 # he has not met Mr. Malhotra
            st = fresh()
            st["visits"]["iic"] = ["2026-10-03"]
            self.assertEqual(look(w, at_dt(D(5), 700), st, "iic")[1]["beat"]["id"], "iic_talk")
        with There(iic=[]):
            st = fresh()
            st["visits"]["iic"] = ["2026-10-03"]
            self.assertIsNone(look(w, at_dt(D(5), 700), st, "iic")[1]["beat"])                 # nobody to ask him

    # the frock coat
    def test_masterji_finds_a_buyer_for_the_frock_coat_from_day_five(self):
        w = self.w
        with There(khan=["masterji"]):
            self.assertNotEqual((look(w, at_dt(D(5), 700), fresh(), "khan")[1]["beat"] or {}).get("id"), "sell_frock")       # day 4
            self.assertEqual(look(w, at_dt(D(6), 700), fresh(), "khan")[1]["beat"]["id"], "sell_frock")                       # day 5
            st = fresh()
            st["wardrobe"] = [g for g in st["wardrobe"] if g["id"] != "frock"]
            self.assertIsNone(look(w, at_dt(D(6), 700), st, "khan")[1]["beat"])
        with There(khan=[]):
            self.assertIsNone(look(w, at_dt(D(6), 700), fresh(), "khan")[1]["beat"])
        with There(home=["masterji"]):
            self.assertIsNone(look(w, at_dt(D(6), 700), fresh(), "home")[1]["beat"])

    def test_yes_sends_the_coat_away_and_the_cash_comes_when_he_is_next_at_khan(self):
        w, st, t = self.w, fresh(), at_dt(D(6), 700)
        with There(khan=["masterji"], home=["ramesh"]):
            oid, out = offer(w, t, st, "khan")
            self.assertEqual(oid, "sell_frock")
            self.assertNotIn("frock", [g["id"] for g in st["wardrobe"]])
            gone = [e for e in out if e["k"] == "wear"]
            self.assertEqual([(e["item"], e["status"], e["gone"]) for e in gone], [("Black frock coat, Berlin tailoring", "Sold to a dealer in Sunder Nagar.", True)])
            self.assertEqual(st["imprest"], 10501)
            look(w, at_dt(D(6), 705), st, "home")
            self.assertEqual(st["imprest"], 10501)                                              # not at home
            sit, ctx = look(w, at_dt(D(6), 710), st, "khan")
        self.assertEqual(st["imprest"], 22501)
        (e,) = [x for x in ctx["public"] if x["k"] == "income"]
        self.assertEqual((e["amount"], e["from"], e["item"]), (12000, "a dealer in Sunder Nagar", "Black frock coat, Berlin tailoring, sold"))
        self.assertIn("A dealer in Sunder Nagar pays you ₹12,000 in cash.", sit["event"])

    def test_no_keeps_the_coat(self):
        w, st = self.w, fresh()
        with There(khan=["masterji"]):
            offer(w, at_dt(D(6), 700), st, "khan", yes=False)
        self.assertIn("frock", [g["id"] for g in st["wardrobe"]])
        self.assertEqual(st["receipts"], [])
        self.assertIn("sell_frock", st["beats"])                                                # offered once: not again

    # the loan
    def test_a_man_with_a_thin_purse_is_offered_a_loan_by_malhotra(self):
        w = self.w
        with There(lodhi=["malhotra"]):
            st = fresh()
            st["imprest"] = 1000
            self.assertIsNone(look(w, at_dt(D(5), 450), st, "lodhi")[1]["beat"])                # ₹1,000 is not below ₹1,000
            st["imprest"] = 999
            self.assertEqual(look(w, at_dt(D(5), 450), st, "lodhi")[1]["beat"]["id"], "loan_malhotra")
        with There(lodhi=[]):
            self.assertIsNone(look(w, at_dt(D(5), 450), st, "lodhi")[1]["beat"])

    def test_the_loan_is_cash_now_and_owed_to_malhotra_to_be_repaid_after_a_week(self):
        w, st = self.w, fresh()
        st["imprest"] = 400
        with There(lodhi=["malhotra"]):
            oid, out = offer(w, at_dt(D(5), 450), st, "lodhi")
            self.assertEqual(oid, "loan_malhotra")
            self.assertEqual(st["imprest"], 5400)
            self.assertEqual([(e["k"], e.get("amount")) for e in out], [("world", None), ("world", None), ("income", 5000), ("world", None)])
            self.assertEqual(out[-1]["owe"], {"to": "Mr. R. K. Malhotra", "amount": 5000, "why": "the loan", "since": "2026-10-05"})
            self.assertEqual(st["owed"][0]["after"], "2026-10-12")
            look(w, at_dt(D(6), 450), st, "lodhi")
            look(w, at_dt(D(11), 450), st, "lodhi")
            self.assertEqual([o["amount"] for o in st["owed"] if o["to"] == "Mr. R. K. Malhotra"], [5000])      # not before the week is out
            sit, ctx = look(w, at_dt(D(12), 450), st, "lodhi")
        self.assertEqual([o for o in st["owed"] if o["to"] == "Mr. R. K. Malhotra"], [])
        self.assertEqual(st["imprest"], 400)
        self.assertIn("You pay Mr. R. K. Malhotra ₹5,000 for the loan.", sit["event"])

    # the essay
    def test_the_magazine_wants_a_long_manuscript_and_is_met_at_the_iic_or_through_nidhi(self):
        w = self.w
        long = {"id": "a", "title": "On Sense", "kind": "essay", "to": None, "words": 1500, "sittings": 4}
        short = dict(long, words=1499)
        for works, who, pid, want in (([long], ["officer"], "iic", "essay_fee"), ([short], ["officer"], "iic", None),
                                      ([long], ["nidhi"], "khan", "essay_fee"), ([long], ["nidhi"], "lodhi", "essay_fee"),
                                      ([long], ["masterji"], "khan", None), ([], ["officer"], "iic", None)):
            st = fresh()
            st["works"], st["visits"] = works, {"iic": ["2026-10-03"]}
            st["people"].remove("malhotra")                                                      # no talk to offer instead
            st["beats"].append("tutoring_german")                                                # nor lessons
            with There(**{pid: who}):
                beat = look(w, at_dt(D(5), 700), st, pid)[1]["beat"]
            self.assertEqual((beat or {}).get("id"), want, (works, who, pid))
        with There(khan=["nidhi"]):
            self.assertIn("Nidhi says a friend of hers edits the Yamuna Review",
                          look(w, at_dt(D(5), 700), dict(fresh(), works=[long], beats=PLOT + ["tutoring_german"]), "khan")[0]["event"])

    def test_the_fee_is_paid_on_the_next_sitting_of_three_hundred_words(self):
        w, st = self.w, fresh()
        st["works"] = [{"id": "a", "title": "On Sense", "kind": "essay", "to": None, "words": 1600, "sittings": 4}]
        st["beats"].append("tutoring_german")
        with There(khan=["nidhi"]):
            oid, out = offer(w, at_dt(D(5), 700), st, "khan")
        self.assertEqual(oid, "essay_fee")
        self.assertEqual(st["imprest"], 10501)
        self.assertEqual(st["receipts"][0]["write"], 300)
        self.assertEqual(w.on_writing(st, 299, at_dt(D(5), 900)), [])                           # a short sitting earns nothing
        (e,) = w.on_writing(st, 300, at_dt(D(5), 1000))
        self.assertEqual((e["k"], e["amount"], e["from"], e["item"]), ("income", 6000, "the Yamuna Review", "Fee for an essay"))
        self.assertEqual((st["imprest"], st["receipts"]), (16501, []))

    def test_the_fee_comes_through_the_whole_step_when_he_writes(self):
        w, st = self.w, fresh()
        st["receipts"] = [{"from": "the Yamuna Review", "amount": 6000, "item": "Fee for an essay", "cheque": False, "after": "2026-10-05T07:00+05:30", "write": 300}]
        day = {"segments": [], "entries": [], "steps": []}
        st["place"] = "home"
        sit, ctx = w.situation(at_dt(D(5), 900), st, day, None)
        ctx["writing"] = {"title": "On Sense", "kind": "essay", "to": None, "continues": False, "text": "word " * 320}
        errors, _, rep = w.check(answer(action="write", place="home"), sit, ctx, st)
        self.assertEqual(errors, [])
        w.apply(rep[0], rep[1], sit, ctx, st, day)
        self.assertEqual(kinds([e for e in day["entries"] if e["k"] in ("writing", "income")]), ["writing", "income"])
        self.assertEqual(st["imprest"], 16501)

    # conditions in general
    def test_the_conditions_are_what_they_say(self):
        w, st, t = self.w, fresh(), at_dt(D(6), 700)
        cases = [({"since_day": 5}, True), ({"since_day": 6}, False), ({"cash_below": 10502}, True), ({"cash_below": 10501}, False),
                 ({"cash_min": 10501}, True), ({"cash_min": 10502}, False), ({"flags": {"bandhgala": "ordered"}}, True), ({"flags": {"bandhgala": "ready"}}, False),
                 ({"met_days": {"nidhi": 1}}, True), ({"met_days": {"nidhi": 2}}, False), ({"visits": {"khan": 1}}, True), ({"visits": {"khan": 2}}, False),
                 ({"known": ["nidhi"]}, True), ({"known": ["kapoor"]}, False), ({"wardrobe": "frock"}, True), ({"wardrobe": "toga"}, False),
                 ({"words": 100}, False), ({"on": "2026-10-06"}, True), ({"on": "2026-10-07"}, False)]
        st["visits"] = {"khan": ["2026-10-02"]}
        for cond, want in cases:
            self.assertEqual(w.when_ok(cond, t, st), want, cond)
        st["works"] = [{"words": 100}]
        self.assertTrue(w.when_ok({"words": 100}, t, st))

    def test_met_days_and_visits_are_counted_once_a_day(self):
        w, st = self.w, fresh()
        with There(khan=["nidhi", "sunil"]):
            look(w, at_dt(D(3), 700), st, "khan")
            look(w, at_dt(D(3), 760), st, "khan")
            look(w, at_dt(D(4), 700), st, "khan")
        self.assertEqual(st["met_days"]["nidhi"], ["2026-10-02", "2026-10-03", "2026-10-04"])
        self.assertEqual(st["met_days"]["sunil"], ["2026-10-03", "2026-10-04"])
        self.assertEqual(st["visits"]["khan"], ["2026-10-03", "2026-10-04"])
        self.assertNotIn("bookseller", st["met_days"])                                           # background people are not met

    def test_a_beat_reads_its_effects_in_the_same_shape_as_the_plot(self):
        w, st = self.w, fresh()
        beat = {"id": "x", "kind": "world", "public": "A letter comes.", "owe": {"to": "the tailor", "amount": 100, "why": "a coat", "after_days": 3},
                "pay": {"from": "a friend", "amount": 50, "item": "A gift"}, "cheque": {"from": "a bank", "amount": 70, "item": "A draft"}}
        out = w.fire(beat, at_dt(D(5), 700), st)
        self.assertEqual([e["k"] for e in out], ["world", "income", "income", "world"])
        self.assertEqual((st["imprest"], st["cheques"][0]["amount"], st["owed"][0]["after"]), (10551, 70, "2026-10-08"))
        self.assertTrue(out[2]["cheque"] and "cheque" not in out[1])


class CostTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def paid(self, ctx):
        return [(e["item"], e["amount"], e["to"]) for e in ctx["public"] if e["k"] == "expense"]

    def test_groceries_are_paid_to_ramesh_at_home_on_sunday(self):
        w, st = self.w, fresh(None)
        look(w, at_dt(D(3), 700), st, "khan")                                                    # Saturday: the dhobi, not the groceries
        with There(home=["ramesh"]):
            sit, ctx = look(w, at_dt(D(4), 7 * 60), st, "home")
        self.assertEqual(self.paid(ctx), [("The dhobi", 300, "the dhobi"), ("Groceries for Ramesh's kitchen", 1500, "Ramesh")])      # Saturday's dhobi, unpaid while he was out, and the groceries
        self.assertEqual(st["imprest"], 10501 - 1800)
        self.assertIn("You pay Ramesh ₹1,500 for groceries.", sit["event"])
        sit, ctx = look(w, at_dt(D(4), 9 * 60), st, "home")
        self.assertEqual(self.paid(ctx), [])                                                       # once a week
        self.assertEqual(st["costs"]["groceries"], "2026-10-04")

    def test_out_all_day_it_is_paid_the_next_time_he_is_home(self):
        w, st = self.w, fresh(None)
        with There(khan=["masterji"], home=["ramesh"]):
            sit, ctx = look(w, at_dt(D(4), 11 * 60), st, "khan")
            self.assertEqual(st["owed"], [{"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "2026-10-04", "cost": "groceries", "item": "Groceries for Ramesh's kitchen",
                                         "at": "home", "with": "ramesh"}])
            self.assertEqual(self.paid(ctx), [])
            note = next(e for e in ctx["public"] if e.get("owe"))
            self.assertEqual((note["k"], note["text"]), ("world", "Groceries: ₹1,500 falls due to Ramesh."))
            self.assertEqual(note["owe"], {"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "2026-10-04"})
            self.assertEqual(st["imprest"], 10501)
            self.assertIn("owes Ramesh ₹1,500 (groceries)", look(w, at_dt(D(4), 15 * 60), st, "khan")[0]["on_mind"][-2])
            sit, ctx = look(w, at_dt(D(4), 19 * 60), st, "home")
        self.assertEqual(self.paid(ctx), [("Groceries for Ramesh's kitchen", 1500, "Ramesh")])
        self.assertTrue(ctx["public"][0]["settles"])
        self.assertEqual((st["owed"], st["imprest"]), ([], 9001))

    def test_he_who_cannot_pay_is_asked_and_nothing_is_cooked_until_he_does(self):
        w, st = self.w, fresh(None)
        st["imprest"] = 1000
        with There(home=["ramesh"]):
            sit, ctx = look(w, at_dt(D(4), 7 * 60 + 5), st, "home")                               # breakfast time
            self.assertIn("Ramesh asks for ₹1,500 (groceries), and you have only ₹1,000.", sit["event"])
            self.assertIn("Nothing is cooked at home: the groceries have not been paid for.", sit["event"])
            self.assertNotIn("laid out breakfast", sit["event"])
            self.assertEqual(st["imprest"], 1000)
            sit, ctx = look(w, at_dt(D(4), 7 * 60 + 30), st, "home")
            self.assertNotIn("asks for", sit["event"])                                            # asked once a day
            self.assertNotIn("Nothing is cooked", sit["event"])                                   # and said once
            self.assertIsNone(w.served(at_dt(D(4), 7 * 60 + 30), st))
            sit, ctx = look(w, at_dt(D(4), 13 * 60 + 5), st, "home")
            self.assertNotIn("laid out lunch", sit["event"])
            st["imprest"] = 2000                                                                  # the next payment
            sit, ctx = look(w, at_dt(D(4), 18 * 60), st, "home")
            self.assertIn("You pay Ramesh ₹1,500 for groceries.", sit["event"])
            self.assertEqual((st["owed"], st["imprest"]), ([], 500))
            sit, ctx = look(w, at_dt(D(4), 19 * 60 + 30), st, "home")
            self.assertIn("serves dinner", sit["event"])
            self.assertEqual(w.served(at_dt(D(4), 19 * 60 + 30), st), "dinner")

    def test_eating_at_home_does_not_feed_him_while_the_kitchen_is_shut(self):
        w, st = self.w, fresh(None)
        st["imprest"], st["last_meal"] = 100, "2026-10-04T06:00+05:30"
        with There(home=["ramesh"]):
            errors, entries = act(w, at_dt(D(4), 13 * 60 + 5), st, "home", answer(action="eat", place="home"))
        self.assertEqual(errors, [])
        self.assertEqual(st["last_meal"], "2026-10-04T06:00+05:30")

    def test_the_dhobi_comes_on_saturdays_and_is_paid_at_home(self):
        w, st = self.w, fresh(None)
        with There(home=["ramesh"]):
            sit, ctx = look(w, at_dt(D(3), 9 * 60), st, "home")
        self.assertEqual(self.paid(ctx), [("The dhobi", 300, "the dhobi")])
        self.assertEqual(st["imprest"], 10201)
        st = fresh(None)
        st["imprest"] = 100
        sit, ctx = look(w, at_dt(D(10), 9 * 60), st, "home")                                      # a week later, and short of cash
        self.assertEqual(self.paid(ctx), [])
        self.assertEqual([(o["to"], o["amount"]) for o in st["owed"]], [("the dhobi", 300), ("the electricity company", 1800)])     # and the 10th is electricity's
        self.assertIn("The dhobi asks for ₹300 (the washing), and you have only ₹100.", sit["event"])
        self.assertNotIn("Nothing is cooked", sit["event"])                                       # an unpaid dhobi shuts no kitchen

    def test_electricity_is_due_on_the_tenth_of_each_month(self):
        w, st = self.w, fresh(None)
        sit, ctx = look(w, at_dt(D(9), 9 * 60), st, "home")
        self.assertNotIn("electricity", json.dumps(ctx["public"]))
        self.assertEqual(st["owed"], [])
        sit, ctx = look(w, at_dt(D(10), 9 * 60), st, "home")
        self.assertIn(("Electricity", 1800, "the electricity company"), self.paid(ctx))
        self.assertIn("You pay the electricity company ₹1,800 for electricity.", sit["event"])
        sit, ctx = look(w, at_dt(D(11), 9 * 60), st, "home")
        self.assertNotIn("Electricity", [x[0] for x in self.paid(ctx)])
        st = fresh(None)
        sit, ctx = look(w, at_dt(D(10, 11), 9 * 60), st, "home")                                  # and again on 10 November
        self.assertIn(("Electricity", 1800, "the electricity company"), self.paid(ctx))

    def test_ramesh_is_paid_for_cooking_on_the_first_from_november(self):
        w = self.w
        st = fresh(None)
        for day in (D(1), D(15), D(31)):
            look(w, at_dt(day, 9 * 60), st, "home")
        self.assertNotIn("wage", [o["cost"] for o in st["owed"]])                                  # none in October: first due 1 November
        with There(home=["ramesh"]):
            sit, ctx = look(w, at_dt(D(1, 11), 9 * 60), fresh(None), "home")
        self.assertIn(("Ramesh's wage for cooking", 8000, "Ramesh"), self.paid(ctx))                  # 1 November is a Sunday: the groceries too
        self.assertIn(("Groceries for Ramesh's kitchen", 1500, "Ramesh"), self.paid(ctx))

    def test_without_his_wage_ramesh_cooks_nothing_and_says_so_once(self):
        w, st = self.w, fresh(None)
        st["imprest"] = 3000
        with There(home=["ramesh"]):
            sit, ctx = look(w, at_dt(D(1, 11), 7 * 60 + 30), st, "home")
            self.assertEqual({o["cost"] for o in st["owed"]}, {"wage"})                           # the groceries, ₹1,500, were paid; the wage was not
            self.assertIn("Ramesh asks for ₹8,000 (the wage for cooking)", sit["event"])
            self.assertIn("Nothing is cooked at home: Ramesh has not been paid his wage for cooking.", sit["event"])
            self.assertNotIn("laid out", sit["event"])
            self.assertEqual(st["owed"][0]["amount"], 8000)
            for minute in (8 * 60, 13 * 60 + 5, 19 * 60 + 35):
                sit, _ = look(w, at_dt(D(1, 11), minute), st, "home")
                self.assertNotIn("laid out", sit["event"])
                self.assertNotIn("serves dinner", sit["event"])
                self.assertNotIn("Nothing is cooked", sit["event"])
            st["imprest"] = 9000
            sit, _ = look(w, at_dt(D(2, 11), 7 * 60 + 10), st, "home")                            # paid the next morning: and breakfast is laid out
            self.assertEqual(st["owed"], [])
            self.assertIn("You pay Ramesh ₹8,000 for the wage for cooking.", sit["event"])
            self.assertIn("Ramesh has laid out breakfast", sit["event"])
            self.assertNotIn("Nothing is cooked", sit["event"])

    def test_mobile_data_every_28_days_once_he_has_a_sim(self):
        w, st = self.w, fresh(None)
        look(w, at_dt(D(20), 9 * 60), st, "khan")
        self.assertNotIn("data", [o["cost"] for o in st["owed"]])                                   # no SIM, no data bill
        st["tech"] = {"phone": True, "sim": True, "sim_from": "2026-10-07", "data_from": "2026-10-07"}
        sit, ctx = look(w, at_dt(D(3, 11), 11 * 60), st, "khan")
        self.assertEqual(self.paid(ctx), [])
        self.assertIn("next: mobile data ₹350 Wed 4 Nov", [x for x in sit["on_mind"] if x.startswith("Money:")][0])
        sit, ctx = look(w, at_dt(D(4, 11), 11 * 60), st, "khan")                                    # paid wherever he is: day 28 after the 7th
        self.assertIn(("Mobile data", 350, "the mobile company"), self.paid(ctx))
        st["imprest"] = 100
        sit, ctx = look(w, at_dt(D(2, 12), 11 * 60), st, "khan")                                    # 28 days on again, and he is short
        self.assertEqual([(o["to"], o["why"]) for o in st["owed"] if o["cost"] == "data"], [("the mobile company", "mobile data")])
        self.assertEqual(st["imprest"], 100)

    def test_cash_is_never_below_zero_whatever_falls_due(self):
        w, st = self.w, fresh(None)
        st["imprest"] = 700
        with There(home=["ramesh"]):
            for day in range(3, 12):
                look(w, at_dt(D(day), 7 * 60 + 30), st, "home")
                look(w, at_dt(D(day), 19 * 60), st, "home")
                self.assertGreaterEqual(st["imprest"], 0)
        self.assertTrue(st["owed"])

    def test_diwali_morning_ramesh_and_the_dhobi_expect_bakshish(self):
        w = self.w
        with There(home=["ramesh"]):
            for day in (D(7, 11), D(9, 11)):
                self.assertNotIn("Diwali", look(w, at_dt(day, 9 * 60), fresh(None), "home")[0]["event"])
            sit, ctx = look(w, at_dt(D(8, 11), 9 * 60), fresh(None), "home")
            self.assertEqual(ctx["beat"]["id"], "diwali_bakshish")
            self.assertEqual(ctx["present"], ["ramesh", "dhobi"])
            self.assertIn("It is Diwali. Ramesh, and the dhobi who has come by with the washing, wait", sit["event"])
            self.assertIsNone(look(w, at_dt(D(8, 11), 14 * 60), fresh(None), "home")[1]["beat"])       # that morning only
            st = fresh(None)
            sit, ctx = look(w, at_dt(D(8, 11), 9 * 60), st, "home")
            errors, _, rep = w.check(answer(action="buy", place="home", buys=[{"item": "Bakshish for Ramesh", "price_inr": 500},
                                                                           {"item": "A gift for the dhobi", "price_inr": 300}]), sit, ctx, st)
        self.assertEqual(errors, [])
        self.assertEqual([(b["item"], b["price"]) for b in rep[1]["buys"]], [("Bakshish for Ramesh", 500), ("A gift for the dhobi", 300)])

    def test_at_home_a_man_may_pay_or_give_only_to_a_person_there(self):
        w = self.w

        def check(buys, present):
            with There(home=present):
                st = fresh(None)
                sit, ctx = look(w, at_dt(D(5), 9 * 60), st, "home")
                return w.check(answer(action="buy", place="home", buys=buys), sit, ctx, st)[0]

        self.assertEqual(check([{"item": "A tip for Ramesh", "price_inr": 50}], ["ramesh"]), [])
        self.assertEqual(check([{"item": "A gift for Ramesh", "price_inr": 5000}], ["ramesh"]), [])
        self.assertEqual(check([{"item": "A horse", "price_inr": 100}], ["ramesh"]), ["nothing is sold at home"])
        self.assertEqual(check([{"item": "A gift for Ramesh", "price_inr": 49}], ["ramesh"]), ["₹49 is not a believable gift or payment for Ramesh (₹50–5,000)"])
        self.assertEqual(check([{"item": "A gift for Ramesh", "price_inr": 5001}], ["ramesh"]), ["₹5,001 is not a believable gift or payment for Ramesh (₹50–5,000)"])
        self.assertEqual(check([{"item": "A gift for Ramesh", "price_inr": 500}], []), ["nothing is sold at home"])        # he is not there
        self.assertEqual(check([{"item": "A gift for Nidhi", "price_inr": 500}], ["ramesh"]), ["nothing is sold at home"])  # nor she

    def test_a_gift_is_a_purchase_with_a_voucher_that_is_personal(self):
        w, st = self.w, fresh(None)
        with There(home=["ramesh"]):
            errors, entries = act(w, at_dt(D(5), 9 * 60), st, "home", answer(action="buy", place="home", buys=[{"item": "Bakshish for Ramesh", "price_inr": 500}]))
        self.assertEqual(errors, [])
        self.assertEqual((st["imprest"], [(v["item"], v["office"]) for v in st["account"]["vouchers"]]), (10001, [("Bakshish for Ramesh", False)]))
        self.assertEqual([(e["k"], e["item"], e["price"]) for e in entries if e["k"] == "bag"], [("bag", "Bakshish for Ramesh", 500)])


class TechTest(unittest.TestCase):
    def setUp(self):
        self.w = World()
        self.t = at_dt(D(5), 12 * 60)

    def buy(self, items, present=("masterji",), st=None, pid="khan"):
        st = st or fresh(imprest=20000)
        with There(**{pid: list(present)}):
            errors, entries = act(self.w, self.t, st, pid, answer(action="buy", place=pid, buys=[{"item": i, "price_inr": p} for i, p in items]))
        return st, errors, entries

    def test_the_catalog_has_them(self):
        sells = {s["item"]: s for s in World().places["khan"]["sells"]}
        self.assertEqual((sells["Mobile phone, basic Android"]["price"], sells["Mobile phone, basic Android"]["tech"]), (9000, "phone"))
        self.assertEqual((sells["Prepaid SIM card"]["price"], sells["Prepaid SIM card"]["tech"]), (300, "sim"))
        self.assertEqual((sells["Mobile data, 28 days"]["price"], sells["Mobile data, 28 days"]["tech"]), (350, "data"))
        self.assertEqual({k for k, s in sells.items() if s.get("office")}, {"Notebook, bound", "Ink cartridges", "Stationery set", "Newspapers"})

    def test_a_phone_is_just_a_purchase(self):
        st, errors, entries = self.buy([("a mobile phone", 8000)])
        self.assertEqual(errors, [])
        self.assertEqual((st["tech"]["phone"], st["tech"]["sim"], st["imprest"]), (True, False, 11000))
        self.assertEqual([(e["item"], e["price"]) for e in entries if e["k"] == "bag"], [("Mobile phone, basic Android", 9000)])
        st, errors, _ = self.buy([("a handset", 9000)], st=st)
        self.assertEqual(errors, ["you already have a phone"])

    def test_a_sim_needs_someone_he_knows_to_vouch_for_him(self):
        for present, why in (((), "nobody"), (("the bookseller",), "background"), (("sunil",), "a stranger"), (("kapoor",), "a stranger")):
            ids = {"the bookseller": "bookseller"}.get(present[0], present[0]) if present else None
            st, errors, _ = self.buy([("a SIM card", 300)], present=[ids] if ids else [])
            self.assertEqual(errors, ["The shop wants an ID for a SIM; you have none."], why)
            self.assertFalse(st["tech"]["sim"])
            self.assertEqual(st["imprest"], 20000)

    def test_with_a_known_person_present_it_is_bought_in_their_name(self):
        for present, name in (("nidhi", "Nidhi"), ("masterji", "Masterji"), ("malhotra", "Malhotra"), ("ramesh", "Ramesh")):
            st, errors, entries = self.buy([("a prepaid SIM", 300)], present=[present])
            self.assertEqual(errors, [])
            self.assertTrue(st["tech"]["sim"])
            self.assertEqual(st["tech"]["sim_from"], "2026-10-05")
            bag = next(e for e in entries if e["k"] == "bag")
            self.assertEqual((bag["item"], bag["price"], bag["note"]), ("Prepaid SIM card", 300, f"Bought in {name}'s name."))
        st, errors, _ = self.buy([("a prepaid SIM", 300)], st=st)
        self.assertEqual(errors, ["you already have a SIM"])

    def test_the_first_data_pack_goes_with_the_sim(self):
        st, errors, _ = self.buy([("mobile data", 350)])
        self.assertEqual(errors, ["A data pack is for a SIM, and you have none."])
        st, errors, entries = self.buy([("mobile data", 350), ("a SIM card", 300), ("a phone", 9000)])         # the pack first, the SIM in the same purchase: refused
        self.assertEqual(errors, ["A data pack is for a SIM, and you have none."])
        st, errors, entries = self.buy([("a SIM card", 300), ("mobile data, 28 days", 350), ("a phone", 9000)])
        self.assertEqual(errors, [])
        self.assertEqual(st["tech"], {"phone": True, "sim": True, "sim_from": "2026-10-05", "data_from": "2026-10-05"})
        self.assertEqual(st["imprest"], 20000 - 9650)
        st, errors, _ = self.buy([("mobile data", 350)], st=st)                                                 # a later pack is allowed
        self.assertEqual(errors, [])

    def test_a_phone_and_sim_he_has_are_no_longer_for_sale(self):
        st = fresh()
        sit, _ = look(self.w, self.t, st, "khan")
        self.assertTrue(all(any(x.startswith(i) for x in sit["for_sale"]) for i in ("Mobile phone", "Prepaid SIM", "Mobile data")))
        st["tech"] = {"phone": True, "sim": True}
        sit, _ = look(self.w, self.t + timedelta(minutes=30), st, "khan")
        self.assertFalse(any(x.startswith(("Mobile phone", "Prepaid SIM")) for x in sit["for_sale"]))
        self.assertTrue(any(x.startswith("Mobile data") for x in sit["for_sale"]))

    def test_the_vouch_is_checked_where_he_will_be_when_he_walks_there_to_buy(self):
        st = fresh(imprest=20000)
        st["place"] = "home"
        with There(khan=["masterji"], home=[]):
            sit, ctx = self.w.situation(at_dt(D(5), 11 * 60), st, {"steps": [], "entries": []}, None)
            errors, _, _ = self.w.check(answer(action="buy", place="khan", buys=[{"item": "a SIM card", "price_inr": 300}]), sit, ctx, st)
        self.assertEqual(errors, [])


class StubTest(unittest.TestCase):
    """The stand-in's economy: it says yes, keeps its engagements, goes to the Directorate, buys a phone, looks up Marx once."""

    def sit(self, **kw):
        sit = {"id": "2026-10-07T12:00", "day": "Wednesday 7 October", "time": "12:00", "place": "home", "weather": "30 °C", "aqi": 100,
               "imprest_left": 5000, "outfit": "kurta", "present": [], "open_now": ["home", "khan", "lodhi", "iic", "estates"], "closes": {},
               "for_sale": [], "on_mind": ["Money: cash ₹5,000."], "earlier": [], "event": "Nothing in particular happens."}
        sit.update(kw)
        return sit

    def decide(self, sit, mind=None):
        return json.loads((mind or StubMind()).decide([{"role": "system", "content": ""}, {"role": "user", "content": ""}], sit))

    def test_it_says_yes_to_every_offer(self):
        self.assertEqual(json.loads(StubMind().chat([{"role": "user", "content": "x"}], {"properties": {"answer": {}}})), {"answer": "yes"})

    def test_it_goes_to_the_directorate_on_a_weekday_once_the_vouchers_pass_two_thousand(self):
        on = ["Money: cash ₹5,000; 3 vouchers pending ₹2,001."]
        got = self.decide(self.sit(on_mind=on))
        self.assertEqual((got["action"], got["place"]), ("walk", "estates"))
        for sit in (self.sit(on_mind=["Money: cash ₹5,000; 3 vouchers pending ₹2,000."]), self.sit(on_mind=on, day="Saturday 10 October"),
                    self.sit(on_mind=on, open_now=["home", "khan"]), self.sit(on_mind=on, time="17:00", id="x2"), self.sit(on_mind=on, place="estates")):
            got = self.decide(sit)
            self.assertFalse(got["action"] == "walk" and got["place"] == "estates" and sit["place"] != "estates", sit)

    def test_it_buys_a_phone_and_sim_at_khan_once_it_has_ten_thousand_and_someone_who_knows_it(self):
        base = dict(place="khan", imprest_left=10000, present=["Masterji, the tailor"], for_sale=["Mobile phone, basic Android ₹9000", "Prepaid SIM card ₹300"])
        got = self.decide(self.sit(**base))
        self.assertEqual([(b["item"], b["price_inr"]) for b in got["buys"]], [("Mobile phone, basic Android", 9000), ("Prepaid SIM card", 300), ("Mobile data, 28 days", 350)])
        for change in ({"imprest_left": 9999}, {"present": []}, {"present": ["the bookseller"]}, {"place": "lodhi"}, {"for_sale": []},
                       {"event": "Sunil, who sells chai is here; you have not met.", "present": ["Sunil, who sells chai"]}):
            got = self.decide(self.sit(**dict(base, **change)))
            self.assertFalse(any("phone" in b["item"] for b in got["buys"]), change)

    def test_it_looks_up_marx_once_it_has_the_phone_and_not_before_nor_after(self):
        mind = StubMind()
        self.assertNotIn("looks_up", self.decide(self.sit(), mind))
        owns = self.sit(on_mind=["Money: cash ₹5,000.", "You have a phone with a SIM: you may look something up (looks_up)."])
        self.assertEqual(self.decide(owns, mind)["looks_up"], "Karl Marx")
        self.assertEqual(self.decide(owns, mind)["looks_up"], "Karl Marx")                           # until it hears how it went
        read = dict(owns, event="On your phone you read: Karl Marx. A German philosopher.")
        self.assertNotIn("looks_up", self.decide(read, mind))
        self.assertNotIn("looks_up", self.decide(owns, mind))

    def test_it_keeps_a_lesson_and_the_talk(self):
        lesson = ["Tuesday 6 October 17:00: German lesson for Ananya, at home, ₹1,000 in cash."]
        got = self.decide(self.sit(day="Tuesday 6 October", time="16:00", place="khan", on_mind=lesson, id="a"))
        self.assertEqual((got["action"], got["place"]), ("walk", "home"))
        got = self.decide(self.sit(day="Tuesday 6 October", time="16:00", place="home", on_mind=lesson, id="b"))
        self.assertEqual((got["action"], got["place"], got["minutes"]), ("rest", "home", 60))
        got = self.decide(self.sit(day="Tuesday 6 October", time="17:00", place="home", on_mind=[], id="c", event="Ananya, Nidhi's cousin, arrives for the German lesson. It runs until 18:00."))
        self.assertEqual((got["action"], got["place"]), ("rest", "home"))
        talk = ["Wednesday 14 October 18:30: your talk at the IIC."]
        got = self.decide(self.sit(day="Wednesday 14 October", time="17:30", place="home", on_mind=talk, id="d"))
        self.assertEqual((got["action"], got["place"]), ("walk", "iic"))


class EngineOfferTest(unittest.TestCase):
    """Offers through the engine: the decision first, then the yes or no, and nothing when the mind is away."""

    def day(self, box, e, d, minute, pid):
        prev = box.days.load(date(2026, 10, 2))
        prev["state"]["asleep"] = False
        day = e.new_day(prev, d)
        st = day["state"]
        st.update(place=pid, today={"woke": "06:00"}, until=at_dt(d, minute).isoformat(timespec="minutes"))
        st["beats"] += PLOT
        return day

    def test_the_frock_is_sold_when_he_says_yes_and_kept_when_he_says_no(self):
        for answer_, sold in (("yes", True), ("no", False)):
            class Mind(StubMind):
                def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                    if "answer" in (schema or {}).get("properties", {}):
                        return json.dumps({"answer": answer_})
                    return super().chat(messages, schema, max_tokens, temperature)

            box = Sandbox()
            try:
                e = box.engine(Mind())
                day = self.day(box, e, D(6), 11 * 60, "khan")
                with There(khan=["masterji"]):
                    step = e.step(day, at_dt(D(6), 11 * 60))
                st = day["state"]
                self.assertEqual(step["beat"], "sell_frock")
                self.assertEqual("frock" in [g["id"] for g in st["wardrobe"]], not sold)
                texts = [x["text"] for x in day["entries"] if x["k"] == "world"]
                self.assertEqual(any("dealer in Sunder Nagar pays" in t or "send a boy" in t for t in texts), sold)
                self.assertEqual(bool(st["receipts"]), sold)
                self.assertEqual(any(x["k"] == "wear" and x.get("gone") for x in day["entries"]), sold)
                self.assertIn("sell_frock", st["beats"])
            finally:
                box.close()

    def test_an_offer_waits_when_the_mind_is_away(self):
        from world.mind import HTTPMind
        box = Sandbox()
        try:
            e = box.engine(HTTPMind("http://127.0.0.1:9"))
            day = self.day(box, e, D(6), 11 * 60, "khan")
            with There(khan=["masterji"]):
                step = e.step(day, at_dt(D(6), 11 * 60))
            self.assertEqual(step["mind"]["source"], "away")
            self.assertNotIn("sell_frock", day["state"]["beats"])
            self.assertEqual(day["state"]["wardrobe"][0]["id"], "frock")
        finally:
            box.close()

    def test_a_decision_that_buys_a_phone_with_no_one_to_vouch_is_refused_and_asked_again(self):
        class Buyer(StubMind):
            def decide(self, messages, sit):
                if any("refuses" in x["content"] for x in messages):
                    return super().decide(messages, sit)
                return json.dumps(answer(thought=f"(rehearsal) {sit['time']} a phone and a SIM would do me good.", action="buy", place="khan", minutes=30,
                                         buys=[{"item": "Mobile phone, basic Android", "price_inr": 9000}, {"item": "Prepaid SIM card", "price_inr": 300}]))

        box = Sandbox()
        try:
            e = box.engine(Buyer())
            day = self.day(box, e, D(6), 11 * 60, "khan")
            day["state"]["imprest"] = 20000
            with There(khan=[]):
                step = e.step(day, at_dt(D(6), 11 * 60))
            self.assertEqual(step["mind"]["refused"], [["The shop wants an ID for a SIM; you have none."]])
            self.assertEqual(day["state"]["tech"], {"phone": False, "sim": False})
        finally:
            box.close()


class CheckTest(unittest.TestCase):
    def test_the_shipped_costs_and_offers_are_sound(self):
        from world.__main__ import economy_problems
        self.assertEqual(economy_problems(World()), [])

    def test_unknown_places_people_and_beats_are_found(self):
        from world.__main__ import economy_problems
        w = World()
        w.costs = w.costs + [{"id": "x", "at": "mars", "with": "nobody", "when": {}}]
        w.beats = w.beats + [{"id": "y", "choice": {"yes": {"schedule": {"beat": "nothing", "in_days": 1, "what": "z"}, "pay": {"at": "venus", "from": "a", "amount": 1, "item": "i"}}},
                              "when": {"met_days": {"ghost": 2}}}]
        got = economy_problems(w)
        for want in ("cost x: unknown place mars", "cost x: unknown cast nobody", "cost x: no rule for when it falls due", "beat y: schedule refers to unknown beat nothing",
                     "beat y: pay refers to unknown at venus", "beat y: unknown ghost in its conditions"):
            self.assertIn(want, got)

    def test_world_check_finds_a_day_whose_entries_do_not_add_up_to_its_cash(self):
        box = Sandbox()
        try:
            shutil.copytree(REPO / "mind", box.tmp / "mind")
            shutil.copytree(REPO / "world", box.tmp / "world", ignore=shutil.ignore_patterns("__pycache__"))
            day = box.run_day(D(3))
            self.assertEqual(self._check(box), (0, "ok"))
            day["state"]["imprest"] += 7
            box.days.save(day)
            code, out = self._check(box)
            self.assertEqual(code, 1)
            self.assertIn("2026-10-03: the entries leave", out)
        finally:
            box.close()

    @staticmethod
    def _check(box):
        got = subprocess.run([sys.executable, "-m", "world", "check"], cwd=REPO, env=dict(os.environ, HEGEL_ENV=os.devnull, HEGEL_REPO=str(box.tmp)), capture_output=True, text=True)
        return got.returncode, got.stdout.strip().splitlines()[-1] if got.returncode == 0 else got.stdout


class MigrationTest(unittest.TestCase):
    def test_a_day_file_from_before_the_economy_gets_its_books_on_the_first_step(self):
        box = Sandbox()
        try:
            e = box.engine()
            day = e.new_day(box.days.load(date(2026, 10, 2)), D(3))
            for k in ("account", "owed", "cheques", "tech", "receipts", "costs", "visits", "met_days"):
                day["state"].pop(k, None)                                     # as a day file written by the world as it was
            day["entries"].append({"t": "09:00", "k": "bag", "item": "Notebook, bound", "price": 120})
            day["state"].update(place="home", until=at_dt(D(3), 10 * 60).isoformat(timespec="minutes"), asleep=False, today={"woke": "06:00"})
            e.step(day, at_dt(D(3), 10 * 60))
            acc = day["state"]["account"]
            self.assertEqual(sum(v["price"] for v in acc["vouchers"]), 4499 + 120)                 # day 1's, and what this day had already bought
            self.assertEqual(sum(v["price"] for v in acc["vouchers"] if v["office"]), 640 + 120)
            self.assertEqual((day["state"]["owed"], day["state"]["cheques"], day["state"]["tech"]["phone"]), ([], [], False))
        finally:
            box.close()


class LessonVoiceTest(unittest.TestCase):
    def test_he_can_speak_to_the_cousin_during_the_lesson_and_she_answers(self):
        from test_deal import Talker
        asked = []

        class Teacher(Talker):
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                if "does" in (schema or {}).get("properties", {}):
                    asked.append(messages[1]["content"])
                return super().chat(messages, schema, max_tokens, temperature)

        mind = Teacher(says="Ananya, we begin with the articles: der, die, das.", voice=json.dumps({"says": "Der, die, das, sir. Is that all of them?", "does": "She opens her notebook"}))
        box = Sandbox()
        try:
            e = box.engine(mind)
            prev = box.days.load(date(2026, 10, 2))
            prev["state"]["asleep"] = False
            day = e.new_day(prev, D(6))
            st = day["state"]
            st["beats"] += PLOT
            st["engagements"] = [{"id": "tutoring_german", "days": "Tue,Fri", "t": "17:00", "minutes": 60, "place": "home", "with": "ananya", "what": "German lesson",
                                  "pay": 1000, "cancel_after": 2, "from": "2026-10-06", "checked": "2026-10-05", "missed": 0}]
            st.update(place="home", today={"woke": "06:00"}, until=at_dt(D(6), 17 * 60).isoformat(timespec="minutes"))
            with mock.patch("world.world.GREET_P", 0.0):                                  # nobody else speaks first
                step = e.step(day, at_dt(D(6), 17 * 60 + 5))
            self.assertEqual(step["beat"], "tutoring_german@2026-10-06")
            self.assertEqual(step["voice"]["by"], "Ananya")
            self.assertIn("You are Ananya, Nidhi's cousin, a student who needs German before a semester in Leipzig.", asked[-1])
            self.assertIn("He says: “Ananya, we begin with the articles", asked[-1])
            self.assertEqual([x["by"] for x in day["entries"] if x["k"] == "said" and x.get("by")], ["Ananya"])
        finally:
            box.close()
