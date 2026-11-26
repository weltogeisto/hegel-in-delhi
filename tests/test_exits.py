"""HEGEL_EXITS (pc/EXITS.md): ways out of the money trouble that cost him effort and that he may decline: a second pupil, a course of
lectures, Ramesh's early offer, Sunil's slate, Shri Hegde's plate, a plain kitchen and the week's dues said at waking; and the file's
line that keeps Mr. Malhotra's letter. Each item on and off. Off, none of it exists."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import D, There, act, fresh, look, offer  # noqa: E402  (this also keeps the tests off the Pi's env file)
from test_world import answer  # noqa: E402

from world.world import World, at_dt  # noqa: E402

ON, OFF = World(exits=True), World()
NOV = lambda day: D(day, 11)
GERMAN = {"id": "tutoring_german", "days": "Tue,Fri", "t": "17:00", "minutes": 60, "place": "home", "with": "ananya", "what": "German lesson",
          "pay": 1000, "cancel_after": 2, "from": "2026-10-04", "checked": "2026-10-16", "missed": 0}
GROCERIES = {"to": "Ramesh", "amount": 1500, "why": "groceries", "since": "2026-11-22", "cost": "groceries", "at": "home", "with": "ramesh",
             "item": "Groceries for Ramesh's kitchen"}


LATER = "2026-12-31"           # costs settled to a date after every test's day: the purse is left alone


def lessons(held=4, cash=2000):
    """The German lessons running, `held` of them given."""
    st = fresh(settled=LATER, imprest=cash)
    st["beats"] += ["tutoring_german"] + [f"tutoring_german@2026-10-{x:02d}" for x in (6, 9, 13, 16)[:held]]
    st["engagements"].append(dict(GERMAN, cancel_after=99))        # not cancelled by the weeks the test skips
    return st


def at(w, t, st, pid, who):
    with There(**{pid: who}):
        return offer(w, t, st, pid)


class SecondPupil(unittest.TestCase):
    def test_offered_by_nidhi_once_four_lessons_are_held_and_cash_is_short(self):
        oid, _ = at(ON, at_dt(D(17), 800), lessons(), "khan", ["nidhi"])
        self.assertEqual(oid, "exits_second_pupil")
        for st in (lessons(held=3), lessons(cash=5000), fresh(settled=LATER)):                     # three lessons; cash enough; no lessons at all
            self.assertNotEqual(at(ON, at_dt(D(17), 800), st, "khan", ["nidhi"])[0], "exits_second_pupil")
        self.assertNotEqual(at(ON, at_dt(D(17), 800), lessons(), "khan", ["masterji"])[0], "exits_second_pupil")      # nobody to ask him

    def test_yes_adds_a_weekly_session_that_brings_the_pupil_and_pays(self):
        st = lessons()
        at(ON, at_dt(D(17), 800), st, "khan", ["nidhi"])
        e = next(x for x in st["engagements"] if x["id"] == "tutoring_german_2")
        self.assertEqual((e["days"], e["t"], e["place"], e["with"], e["pay"], e["from"]), ("Wed", "17:00", "home", "vikram", 1000, "2026-10-18"))
        self.assertEqual(len(st["engagements"]), 2)                                  # the old lessons stand as they were
        with There(home=[]):
            sit, ctx = look(ON, at_dt(D(21), 17 * 60), st, "home")
            self.assertEqual(ctx["beat"]["id"], "tutoring_german_2@2026-10-21")
            self.assertIn("Vikram, a friend of Nidhi's", sit["present"])
            ON.fire(ctx["beat"], at_dt(D(21), 17 * 60), st)
            cash = st["imprest"]
            _, ctx = look(ON, at_dt(D(21), 18 * 60), st, "home")
        self.assertEqual(st["imprest"], cash + 1000)
        self.assertEqual([(x["item"], x["from"]) for x in ctx["public"] if x["k"] == "income"], [("German lesson", "Vikram")])

    def test_no_brings_it_back_after_a_fortnight_and_off_it_does_not_exist(self):
        st = lessons()
        with There(khan=["nidhi"]):
            offer(ON, at_dt(D(17), 800), st, "khan", yes=False)
            self.assertEqual([e["id"] for e in st["engagements"]], ["tutoring_german"])
            self.assertIsNone(look(ON, at_dt(D(24), 800), st, "khan")[1]["beat"])
            self.assertEqual(look(ON, at_dt(D(31), 800), st, "khan")[1]["beat"]["id"], "exits_second_pupil")
        self.assertNotIn("exits_second_pupil", OFF.offer_ids)
        self.assertNotIn("vikram", OFF.cast)
        self.assertNotEqual(at(OFF, at_dt(D(17), 800), lessons(), "khan", ["nidhi"])[0], "exits_second_pupil")



def told(**kw):
    """A state in which the dues line has been said: the public's first offers wait for it (Welt, 26 November)."""
    st = fresh(**kw)
    st["dues_said"] = "2026-10-20"
    return st


class Course(unittest.TestCase):
    def talked(self):
        st = told(settled=LATER)
        st["beats"] += ["iic_talk", "iic_talk_day"]
        return st

    def test_offered_on_a_later_visit_by_the_officer_after_a_talk(self):
        st = self.talked()
        st["fired_on"] = {"iic_talk_day": "2026-10-14"}
        self.assertNotEqual(at(ON, at_dt(D(14), 19 * 60), st, "iic", ["officer"])[0], "exits_course")      # the day of the talk itself
        self.assertEqual(at(ON, at_dt(D(15), 11 * 60), self.talked(), "iic", ["officer"])[0], "exits_course")
        self.assertNotEqual(at(ON, at_dt(D(15), 11 * 60), told(settled=LATER), "iic", ["officer"])[0], "exits_course")  # no talk given
        self.assertNotEqual(at(ON, at_dt(D(15), 11 * 60), self.talked(), "iic", ["guard"])[0], "exits_course")
        second = told(settled=LATER)
        second["beats"] += ["iic_talk_again", "iic_talk_day2"]
        self.assertEqual(at(World(exits=True, keep_time=True), at_dt(D(15), 11 * 60), second, "iic", ["officer"])[0], "exits_course")

    def test_the_fire_of_a_talk_records_its_day_only_with_the_switch_on(self):
        for w, want in ((ON, {"iic_talk_day": "2026-10-14"}), (OFF, None)):
            st = self.talked()
            st["beats"].remove("iic_talk_day")
            st["appointments"].append({"date": "2026-10-14", "t": "18:30", "what": "your talk at the IIC", "beat": "iic_talk_day"})
            with There(iic=["officer"]):
                _, ctx = look(w, at_dt(D(14), 18 * 60 + 30), st, "iic")
                w.fire(ctx["beat"], at_dt(D(14), 18 * 60 + 30), st)
            self.assertEqual(st.get("fired_on"), want)

    def test_yes_keeps_four_evenings_a_week_apart_each_a_talk_that_pays(self):
        st = self.talked()
        at(ON, at_dt(D(15), 11 * 60), st, "iic", ["officer"])
        self.assertEqual([(a["date"], a["t"], a["beat"]) for a in st["appointments"]],
                         [("2026-10-22", "18:30", "exits_course_1"), ("2026-10-29", "18:30", "exits_course_2"),
                          ("2026-11-05", "18:30", "exits_course_3"), ("2026-11-12", "18:30", "exits_course_4")])
        for n in range(1, 5):
            self.assertIn("talk", ON.beat(f"exits_course_{n}"))                      # the talk scene (if on) lets him give each lecture
        for n, day in ((1, D(22)), (2, D(29)), (3, NOV(5)), (4, NOV(12))):
            with There(iic=["officer"]):
                sit, ctx = look(ON, at_dt(day, 18 * 60 + 30), st, "iic")
                self.assertEqual(ctx["beat"]["id"], f"exits_course_{n}")
                ON.fire(ctx["beat"], at_dt(day, 18 * 60 + 30), st)
                cash = st["imprest"]
                _, ctx = look(ON, at_dt(day, 19 * 60 + 30), st, "iic")
            self.assertEqual(st["imprest"], cash + 3000)                              # in cash, at the door
            self.assertEqual([x["amount"] for x in ctx["public"] if x["k"] == "income"], [3000])
        self.assertEqual(st["appointments"], [])
        self.assertEqual(st["cheques"], [])

    def test_off_there_is_no_course(self):
        self.assertFalse([b for b in OFF.beats if b["id"].startswith("exits_")])
        self.assertNotEqual(at(OFF, at_dt(D(15), 11 * 60), self.talked(), "iic", ["officer"])[0], "exits_course")


class CourseByNote(unittest.TestCase):
    def test_the_centre_writes_when_he_does_not_come(self):
        st = told(settled=LATER)
        st["beats"] += ["iic_talk", "iic_talk_day"]
        with There(home=["ramesh"]):
            sit, ctx = look(ON, at_dt(D(15), 11 * 60), st, "home")
        self.assertEqual(ctx["beat"]["id"], "exits_course")
        self.assertIn("Ramesh brings a note from the India International Centre.", sit["event"])
        with There(home=[]):
            self.assertIsNone(look(ON, at_dt(D(15), 11 * 60), told(settled=LATER, beats=st["beats"][:]), "home")[1]["beat"])   # nobody to bring it


class EssayAgain(unittest.TestCase):
    """Day 27: the Review's essay took a no and could never come back, and the column behind it never opened."""
    ESSAY = {"kind": "essay", "title": "On the Republic", "started": "2026-11-27"}

    def declined(self, words=4146):
        st = told(settled=LATER)
        st["beats"].append("essay_fee")                                               # offered once, and declined: no flag
        st["works"] = [{"id": "w", "title": "On the Ethical Substance", "kind": "notes", "to": None, "started": "2026-10-13", "words": words,
                        "sittings": 8, "last": "2026-11-24", "tail": ""}]
        return st

    def agreed(self):
        st = self.declined()
        at(ON, at_dt(NOV(26), 11 * 60), st, "home", ["ramesh"])
        return st

    def test_the_editor_asks_again_once_the_pages_have_grown_and_names_no_question(self):
        st = self.declined()
        with There(home=["ramesh"]):
            sit, ctx = look(ON, at_dt(NOV(26), 11 * 60), st, "home")
        self.assertEqual(ctx["beat"]["id"], "exits_essay_again")
        self.assertIn("She asks again for an essay of yours, on a subject of your own choosing: ₹6,000 in cash when it is written", sit["event"])
        for b in (ON.beat("exits_essay_again"), ON.beat("exits_column")):             # DECISIONS 69: no invented person argues at him
            said = [v["prompt"] for v in b["variants"].values()] + [b["public"]]
            self.assertFalse([x for x in said if "?" in x or "you taught" in x or "your sentence" in x])
        self.assertNotEqual(at(ON, at_dt(NOV(26), 11 * 60), self.declined(words=2000), "home", ["ramesh"])[0], "exits_essay_again")
        paid = self.declined()
        paid["flags"]["essay_paid"] = True
        self.assertNotEqual(at(ON, at_dt(NOV(26), 11 * 60), paid, "home", ["ramesh"])[0], "exits_essay_again")
        never = told(settled=LATER, works=self.declined()["works"])
        self.assertNotEqual(at(ON, at_dt(NOV(26), 11 * 60), never, "home", ["ramesh"])[0], "exits_essay_again")       # the first offer never came
        self.assertNotEqual(at(OFF, at_dt(NOV(26), 11 * 60), self.declined(), "home", ["ramesh"])[0], "exits_essay_again")

    def test_yes_keeps_the_essay_on_his_mind_until_it_is_written(self):
        st = self.agreed()
        with There(home=[]):
            sit, _ = look(ON, at_dt(NOV(26), 12 * 60), st, "home")
        self.assertIn("The Yamuna Review waits for your essay: ₹6,000 in cash when it is written, an essay of three hundred words or more, begun after you agreed.", sit["on_mind"])
        cash = st["imprest"]
        ON.on_writing(st, 450, at_dt(NOV(27), 15 * 60), self.ESSAY)
        self.assertEqual(st["imprest"], cash + 6000)
        self.assertIs(st["flags"]["essay_paid"], True)
        self.assertEqual(st["out"], [{"id": "Fee for an essay", "date": "2026-11-27", "title": "On the Republic"}])       # a piece of his went out
        with There(home=[]):
            self.assertFalse(any("Yamuna Review waits" in x for x in look(ON, at_dt(NOV(27), 16 * 60), st, "home")[0]["on_mind"]))

    def test_the_fee_is_for_the_essay_and_not_for_whatever_he_writes_next(self):
        for piece in ({"kind": "notes", "title": "Notes on the Kettle", "started": "2026-11-27"},          # notes on his day
                      {"kind": "letter", "title": "Letter to Dr. Lindner", "started": "2026-11-27"},        # a letter
                      {"kind": "essay", "title": "An older essay", "started": "2026-11-20"},                # begun before he agreed
                      None):
            st = self.agreed()
            cash = st["imprest"]
            self.assertEqual(ON.on_writing(st, 500, at_dt(NOV(27), 15 * 60), piece), [])
            self.assertEqual(st["imprest"], cash)
            self.assertEqual(len(st["receipts"]), 1)                                  # the Review still waits
        st = self.agreed()
        self.assertEqual(ON.on_writing(st, 250, at_dt(NOV(27), 15 * 60), self.ESSAY), [])                   # too short
        self.assertEqual(len(ON.on_writing(st, 320, at_dt(NOV(26), 18 * 60), dict(self.ESSAY, started="2026-11-26"))), 1)   # the day he agreed counts

    def test_through_a_sitting_as_the_world_files_it(self):
        st = self.agreed()
        w = {"title": "On the Republic", "kind": "essay", "to": None, "continues": False, "text": "word " * 400}
        st["place"], day = "home", {"segments": [], "entries": [], "steps": []}
        with There(home=[]):
            sit, ctx = ON.situation(at_dt(NOV(27), 15 * 60), st, day, None)
            errors, _, rep = ON.check(answer(action="write", place="home", minutes=60), sit, ctx, st)
            self.assertEqual(errors, [])
            ctx["writing"] = w
            ON.apply(rep[0], rep[1], sit, ctx, st, day)
        self.assertEqual([e["amount"] for e in day["entries"] if e["k"] == "income"], [6000])
        self.assertEqual(st["out"][0]["title"], "On the Republic")

    def test_the_old_offer_keeps_its_old_rule(self):
        for w in (ON, OFF):
            st = told(settled=LATER)
            st["receipts"].append({"from": "the Yamuna Review", "amount": 6000, "item": "Fee for an essay", "cheque": False, "write": 300,
                                   "after": "2026-11-26T11:00", "flag": "essay_paid", "charge_id": "c1"})       # as `essay_fee` makes it: no piece named
            self.assertEqual(len(w.on_writing(st, 450, at_dt(NOV(27), 15 * 60), {"kind": "notes", "title": "Notes", "started": "2026-10-13"})), 1)
            self.assertEqual("out" in st, w is ON)

    def test_the_column_opens_behind_the_essay_in_its_own_words(self):
        st = self.agreed()
        ON.on_writing(st, 450, at_dt(NOV(27), 15 * 60), self.ESSAY)
        self.assertNotIn("column", ON.offer_ids)                                      # with the switch on the old offer is gone
        self.assertIn("column", OFF.offer_ids)
        self.assertNotIn("exits_column", OFF.offer_ids)
        with There(home=["ramesh"]):
            sit, ctx = look(ON, at_dt(NOV(29), 11 * 60), st, "home")
            self.assertEqual(ctx["beat"]["id"], "exits_column")
            self.assertIn("asks for a column: an essay every fortnight, three hundred words or more, ₹4,000 in cash for each", sit["event"])
            ON.fire(ctx["beat"], at_dt(NOV(29), 11 * 60), st)
            ON.settle_choice(ctx["beat"], True, st, at_dt(NOV(29), 11 * 60))
        (r,) = [x for x in st["receipts"] if x.get("commission") == "column"]
        self.assertEqual((r["piece"], r["amount"]), ("essay", 4000))
        self.assertEqual(ON.on_writing(st, 400, at_dt(NOV(30), 15 * 60), {"kind": "notes", "title": "Notes", "started": "2026-11-30"}), [])
        self.assertEqual(len(ON.on_writing(st, 400, at_dt(NOV(30), 16 * 60), {"kind": "essay", "title": "On Air", "started": "2026-11-30"})), 1)
        self.assertEqual(st["commissions"][0]["next"], "2026-12-14")                  # the next piece, a fortnight on

    def test_a_manuscript_earns_one_fee(self):
        st = self.agreed()
        ON.on_writing(st, 450, at_dt(NOV(27), 13 * 60), self.ESSAY)                   # the essay, paid
        with There(home=["ramesh"]):
            _, ctx = look(ON, at_dt(NOV(29), 11 * 60), st, "home")
            ON.fire(ctx["beat"], at_dt(NOV(29), 11 * 60), st)
            ON.settle_choice(ctx["beat"], True, st, at_dt(NOV(29), 11 * 60))          # the column, agreed
        cash = st["imprest"]
        self.assertEqual(ON.on_writing(st, 450, at_dt(NOV(29), 15 * 60), self.ESSAY), [])     # more of the essay that was paid for
        self.assertEqual(st["imprest"], cash)
        self.assertEqual(len(ON.on_writing(st, 400, at_dt(NOV(29), 17 * 60), {"kind": "essay", "title": "On Air", "started": "2026-11-29"})), 1)
        self.assertEqual([o["title"] for o in st["out"]], ["On the Republic", "On Air"])

    def test_the_column_waits_until_the_essay_can_have_been_read(self):
        st = self.agreed()
        ON.on_writing(st, 450, at_dt(NOV(27), 13 * 60), self.ESSAY)
        for day_, opens in ((27, False), (28, False), (29, True)):
            with There(home=["ramesh"]):
                _, ctx = look(ON, at_dt(NOV(day_), 16 * 60), st, "home")
            self.assertEqual(bool(ctx.get("beat")) and ctx["beat"]["id"] == "exits_column", opens, day_)

    def test_the_publics_offers_come_one_a_day(self):
        st = self.agreed()
        ON.on_writing(st, 450, at_dt(NOV(27), 13 * 60), self.ESSAY)                   # on the 29th the column and an envelope are both due
        seen = []
        for day_ in (29, 29, 30):
            with There(home=["ramesh"]):
                _, ctx = look(ON, at_dt(NOV(day_), 11 * 60 + 30 * len(seen)), st, "home")
                seen.append(ctx["beat"]["id"] if ctx.get("beat") else None)
                if ctx.get("beat"):
                    ON.fire(ctx["beat"], at_dt(NOV(day_), 11 * 60), st)
                    if ctx["beat"].get("choice"):
                        ON.settle_choice(ctx["beat"], True, st, at_dt(NOV(day_), 11 * 60))
        self.assertEqual(sorted(x for x in (seen[0], seen[2]) if x), ["exits_column", "exits_gift"])
        self.assertNotIn(seen[1], ("exits_column", "exits_gift", "exits_course", "exits_essay_again"))    # nothing more of the public's that day
        self.assertNotIn("public_on", fresh(settled=LATER))                           # and the state holds nothing of it until one is made

    def test_no_brings_her_back_after_a_fortnight(self):
        st = self.declined()
        with There(home=["ramesh"]):
            offer(ON, at_dt(NOV(26), 11 * 60), st, "home", yes=False)
            self.assertIsNone(look(ON, at_dt(date(2026, 12, 5), 11 * 60), st, "home")[1]["beat"])
            self.assertEqual(look(ON, at_dt(date(2026, 12, 10), 11 * 60), st, "home")[1]["beat"]["id"], "exits_essay_again")


class AfterDues(unittest.TestCase):
    def test_the_review_and_the_course_wait_until_he_has_been_told_he_is_short(self):
        for told_ in (False, True):
            st = fresh(settled=LATER)
            st["beats"] += ["iic_talk", "iic_talk_day"]
            st.setdefault("fired_on", {})["iic_talk_day"] = "2026-10-20"
            if told_:
                st["dues_said"] = "2026-11-24"
            with There(iic=["officer"]):
                beat = look(ON, at_dt(NOV(26), 11 * 60), st, "iic")[1].get("beat")
            self.assertEqual(bool(beat) and beat["id"] == "exits_course", told_)
        st = EssayAgain().declined()
        st.pop("dues_said", None)
        self.assertNotEqual(at(ON, at_dt(NOV(26), 11 * 60), st, "home", ["ramesh"])[0], "exits_essay_again")
        st["dues_said"] = "2026-11-25"
        self.assertEqual(at(ON, at_dt(NOV(26), 11 * 60), st, "home", ["ramesh"])[0], "exits_essay_again")


class NidhiOut(unittest.TestCase):
    """She has been in the cast from the start, and he met her on Day 1 only: her hours were not his."""
    def test_she_keeps_three_more_rows_of_hours_only_with_the_switch(self):
        on, off = ON.cast["nidhi"]["where"], OFF.cast["nidhi"]["where"]
        self.assertEqual(len(off), 3)
        self.assertEqual([{k: v for k, v in w.items()} for w in on[:3]], off)          # her old hours stand, in their old order
        self.assertEqual([(w["place"], w["days"], w["from"], w["to"]) for w in on[3:]],
                         [("khan", "daily", "13:00", "19:00"), ("iic", "Mon-Fri", "12:00", "18:30"), ("lodhi", "daily", "08:00", "10:30")])

    def test_she_is_at_khan_market_on_days_she_never_was(self):
        days = [date(2026, 11, n) for n in range(2, 30) if date(2026, 11, n).strftime("%a") not in ("Wed", "Sat")]
        seen = lambda w: sum("nidhi" in w.present_ids("khan", at_dt(d, 15 * 60), fresh()) for d in days)
        self.assertEqual(seen(OFF), 0)
        self.assertGreater(seen(ON), 5)                                               # about one day in two, by her own chance


class Gift(unittest.TestCase):
    """Welt, 24 November: gifts of secret admirers may occur, and each reminds him of the value he has to keep bringing."""
    def talked(self, on=None):
        st = fresh(settled=LATER)
        st["beats"] += ["iic_talk", "iic_talk_day", "exits_course"]                   # the course already offered, out of the way
        if on:
            st["fired_on"] = {"iic_talk_day": on}
            st["out"] = [{"id": "iic_talk_day", "date": on}]
        return st

    def home(self, st, day, hour=11):
        with There(home=["ramesh"]):
            return look(ON, at_dt(day, hour * 60), st, "home")

    def test_an_envelope_names_the_piece_two_days_after_it_went_out(self):
        st = self.talked(on="2026-11-24")
        self.assertIsNone(self.home(st, NOV(25))[1]["beat"])                          # too soon
        sit, ctx = self.home(st, NOV(26))
        self.assertEqual(ctx["beat"]["id"], "exits_gift")
        self.assertIn("'For your talk at the Centre. I have thought of it every day since.", sit["event"])
        self.assertIn("What comes next?'", sit["event"])
        cash = st["imprest"]
        out = ON.fire(ctx["beat"], at_dt(NOV(26), 11 * 60), st)
        self.assertEqual(st["imprest"], cash + 2000)
        self.assertEqual(st["gifts"], [{"date": "2026-11-26", "piece": "iic_talk_day", "of": "2026-11-24", "amount": 2000}])
        self.assertIn("a card that thanks him for your talk at the Centre and asks what comes next", out[0]["text"])
        self.assertEqual([(e["k"], e["amount"], e["text"]) for e in out if e["k"] == "income"], [("income", 2000, "The envelope holds ₹2,000.")])
        self.assertNotIn("exits_gift", st["beats"])                                   # it may come again

    def test_no_second_gift_without_a_new_piece_and_none_within_ten_days(self):
        st = self.talked(on="2026-11-24")
        ON.fire(self.home(st, NOV(26))[1]["beat"], at_dt(NOV(26), 11 * 60), st)
        for day in (NOV(27), date(2026, 12, 10), date(2026, 12, 20)):
            self.assertIsNone(self.home(st, day)[1]["beat"])                          # the same piece is never thanked twice
        st["out"].append({"id": "Fee for an essay", "date": "2026-11-28"})            # a new piece, two days after the gift
        self.assertIsNone(self.home(st, NOV(30))[1]["beat"])                          # ten days have not passed
        sit, ctx = self.home(st, date(2026, 12, 6))
        self.assertEqual(ctx["beat"]["id"], "exits_gift")
        self.assertIn("'For your essay in the Yamuna Review.", sit["event"])

    def test_a_talk_given_before_the_switch_is_thanked_once(self):
        st = self.talked()                                                            # no date was kept: the switch was off
        sit, ctx = self.home(st, NOV(26))
        self.assertEqual(ctx["beat"]["id"], "exits_gift")
        ON.fire(ctx["beat"], at_dt(NOV(26), 11 * 60), st)
        self.assertEqual(st["gifts"][0]["of"], None)
        self.assertIsNone(self.home(st, date(2026, 12, 20))[1]["beat"])

    def test_no_piece_no_gift_and_off_there_is_none(self):
        st = fresh(settled=LATER)
        self.assertIsNone(self.home(st, NOV(26))[1]["beat"])
        self.assertNotIn("exits_gift", OFF.offer_ids)
        with There(home=["ramesh"]):
            self.assertIsNone(look(OFF, at_dt(NOV(26), 11 * 60), self.talked(on="2026-11-24"), "home")[1]["beat"])

    def test_a_talk_fired_with_the_switch_on_is_a_piece_that_went_out(self):
        st = fresh(settled=LATER)
        st["beats"] += ["iic_talk"]
        st["appointments"].append({"date": "2026-10-14", "t": "18:30", "what": "your talk at the IIC", "beat": "iic_talk_day"})
        with There(iic=["officer"]):
            _, ctx = look(ON, at_dt(D(14), 18 * 60 + 30), st, "iic")
            ON.fire(ctx["beat"], at_dt(D(14), 18 * 60 + 30), st)
        self.assertEqual(st["out"], [{"id": "iic_talk_day", "date": "2026-10-14"}])


class RameshEarly(unittest.TestCase):
    def setUp(self):
        self.st = lambda cash=2000: fresh(settled="2026-11-20", imprest=cash)

    def test_offered_five_days_before_the_wage_when_the_purse_cannot_carry_the_fortnight(self):
        self.assertEqual(at(ON, at_dt(NOV(26), 10 * 60), self.st(), "home", ["ramesh"])[0], "exits_ramesh_early")
        self.assertNotEqual(at(ON, at_dt(NOV(24), 10 * 60), self.st(), "home", ["ramesh"])[0], "exits_ramesh_early")     # seven days off
        self.assertEqual(at(ON, at_dt(NOV(26), 10 * 60), self.st(9000), "home", ["ramesh"])[0], "exits_ramesh_early")     # it holds the wage, and not the fortnight
        self.assertNotEqual(at(ON, at_dt(NOV(26), 10 * 60), self.st(30000), "home", ["ramesh"])[0], "exits_ramesh_early")  # the purse can carry it
        part = self.st()
        part["flags"]["ramesh_parttime"] = True
        self.assertNotEqual(at(ON, at_dt(NOV(26), 10 * 60), part, "home", ["ramesh"])[0], "exits_ramesh_early")
        self.assertNotEqual(at(OFF, at_dt(NOV(26), 10 * 60), self.st(), "home", ["ramesh"])[0], "exits_ramesh_early")

    def test_it_is_the_old_choice_with_the_old_effects(self):
        self.assertEqual(ON.beat("exits_ramesh_early")["choice"], ON.beat("ramesh_parttime")["choice"])
        st = self.st()
        at(ON, at_dt(NOV(26), 10 * 60), st, "home", ["ramesh"])
        self.assertIs(st["flags"]["ramesh_parttime"], True)
        ON.accrue(at_dt(date(2026, 12, 1), 6 * 60), st)
        wage = next(o for o in st["owed"] if o["cost"] == "wage")
        self.assertEqual(wage["amount"], 4000)
        self.assertNotIn("exits_ramesh_early", [b for b in st["beats"] if b != "exits_ramesh_early"])

    def test_refused_it_comes_back_after_a_week(self):
        st = self.st()
        with There(home=["ramesh"]):
            offer(ON, at_dt(NOV(26), 10 * 60), st, "home", yes=False)
            self.assertNotIn("ramesh_parttime", st["flags"])
            self.assertIsNone(look(ON, at_dt(NOV(28), 10 * 60), st, "home")[1]["beat"])


class Slate(unittest.TestCase):
    def buy(self, w, cash, item="Chai, a cup", st=None, who=("sunil",), hour=14):
        st = st or fresh(settled=LATER, imprest=cash)
        with There(khan=list(who)):
            errors, entries = act(w, at_dt(D(12), hour * 60), st, "khan", answer(action="buy", place="khan", minutes=10,
                                                                            buys=[{"item": item, "price_inr": 20}]))
        return st, errors, entries

    def test_a_cup_of_chai_goes_through_and_is_owed_to_sunil(self):
        st, errors, entries = self.buy(ON, 5)
        self.assertEqual(errors, [])
        (o,) = st["owed"]
        self.assertEqual((o["to"], o["amount"], o["slate"], o["at"], o["with"]), ("Sunil", 20, True, "khan", "sunil"))
        self.assertEqual(st["imprest"], 5)
        self.assertEqual([e["k"] for e in entries if e["k"] == "bag"], [])           # nothing was paid
        self.assertTrue(any(e.get("owe", {}).get("to") == "Sunil" for e in entries))

    def test_only_one_debt_may_stand_the_second_is_refused_as_before(self):
        st, _, _ = self.buy(ON, 5)
        _, errors, _ = self.buy(ON, 5, item="Samosa", st=st)
        self.assertEqual(len(errors), 1)
        self.assertIn("you have only ₹5 in cash", errors[0])
        self.assertEqual(len(st["owed"]), 1)

    def test_repaid_as_other_debts_are_when_he_is_there_with_the_cash(self):
        st, _, _ = self.buy(ON, 5)
        with There(khan=[]):
            _, ctx = look(ON, at_dt(D(12), 15 * 60), st, "khan")                      # Sunil is not there
        self.assertEqual(len(st["owed"]), 1)
        st["imprest"] = 100
        with There(khan=["sunil"]):
            sit, ctx = look(ON, at_dt(D(12), 16 * 60), st, "khan")
        self.assertEqual(st["owed"], [])
        self.assertEqual(st["imprest"], 80)
        self.assertIn("You pay Sunil ₹20 for chai, a cup on the slate.", sit["event"])
        st, errors, _ = self.buy(ON, 5, item="Samosa", st=st)                         # a new one may stand once this is paid
        self.assertEqual(errors, [])

    def test_only_chai_or_a_samosa_only_at_khan_and_only_with_sunil(self):
        self.assertTrue(self.buy(ON, 5, item="Glucose biscuits")[1])                  # not on the slate's list
        self.assertTrue(self.buy(ON, 5, who=())[1])                                   # Sunil is not there
        self.assertTrue(self.buy(ON, 5, item="Cappuccino at a café")[1])
        self.assertTrue(self.buy(ON, 0, item="Samosa")[1] == [] and self.buy(ON, 0, item="Samosa")[0]["owed"][0]["amount"] == 30)

    def test_his_voice_is_told_by_the_record(self):
        from world import voices
        st, _, _ = self.buy(ON, 5)
        facts = voices.recorded_facts(ON, "sunil", st)
        self.assertEqual(len(facts), 1)
        self.assertIn("₹20 stands owed to you, recorded, unpaid", facts[0])
        self.assertEqual(voices.recorded_facts(OFF, "sunil", st), [])

    def test_off_the_old_refusal_applies(self):
        st, errors, _ = self.buy(OFF, 5)
        self.assertIn("you have only ₹5 in cash", errors[0])
        self.assertEqual(st["owed"], [])


class Household(unittest.TestCase):
    def owing(self, cash=100):
        st = fresh(settled="2026-11-23", imprest=cash)
        st["owed"].append(dict(GROCERIES))
        return st

    def eat(self, w, hour, st=None):
        st = st or self.owing()
        with There(home=["ramesh"]):
            errors, _ = act(w, at_dt(NOV(24), hour * 60 + 45), st, "home", answer(action="eat", place="home", minutes=30))
        return st, errors

    def test_the_plain_kitchen_gives_one_dinner_a_day(self):
        st, errors = self.eat(ON, 19)
        self.assertEqual(errors, [])
        self.assertTrue(st["last_meal"].startswith("2026-11-24T19:45"))
        for hour in (8, 13):
            _, errors = self.eat(ON, hour)
            self.assertEqual(len(errors), 1)
            self.assertIn("Ramesh cooks one plain meal a day, dal and rice in the evening: the groceries have not been paid for.", errors[0])
        self.assertEqual(st["owed"][0]["amount"], 1500)                              # the debt is untouched

    def test_off_every_meal_is_refused_in_the_old_words(self):
        for hour in (8, 13, 19):
            _, errors = self.eat(OFF, hour)
            self.assertEqual(len(errors), 1)
            self.assertIn("Nothing is cooked at home: the groceries have not been paid for.", errors[0])
            self.assertNotIn("plain meal", errors[0])

    def test_the_wage_has_its_plain_line_too_and_the_dinner_is_said_plainly(self):
        st = fresh(settled="2026-11-23", imprest=2000)
        st["owed"].append(dict(GROCERIES, amount=8000, why="the wage for cooking", cost="wage"))
        with There(home=["ramesh"]):
            sit, _ = look(ON, at_dt(NOV(24), 8 * 60), st, "home")
            self.assertIn("one plain meal a day, dal and rice in the evening: he has not been paid his wage for cooking.", sit["event"])
            sit, ctx = look(ON, at_dt(NOV(24), 19 * 60 + 40), st, "home")
        self.assertIn("Ramesh serves the one plain meal of the day before he goes home: dal and rice.", sit["event"])
        self.assertIn("meal", ctx["opened"])

    def test_shri_hegde_sets_a_plate_after_two_days_on_the_plain_meal_and_not_before(self):
        st = self.owing()
        st["flags"]["hegde_lodger"] = True
        for day in (24, 25):
            look(ON, at_dt(NOV(day), 10 * 60), st, "home")                            # the record of the plain kitchen begins on the 24th
        self.assertNotEqual(at(ON, at_dt(NOV(24), 19 * 60 + 10), self.owing(), "home", ["hegde"])[0], "exits_hegde_plate")
        probe = self.owing()
        look(ON, at_dt(NOV(24), 10 * 60), probe, "home")
        self.assertNotEqual(at(ON, at_dt(NOV(24), 19 * 60 + 10), probe, "home", ["hegde"])[0], "exits_hegde_plate")     # one day
        st["last_meal"] = at_dt(NOV(25), 7 * 60).isoformat(timespec="minutes")
        oid, out = at(ON, at_dt(NOV(25), 19 * 60 + 10), st, "home", ["hegde"])
        self.assertEqual(oid, "exits_hegde_plate")
        self.assertTrue(st["last_meal"].startswith("2026-11-25T19:10"))                         # fed a meal by the world's own feed
        self.assertEqual(st["fed_by"], [{"by": "hegde", "date": "2026-11-25", "t": "19:10"}])

    def test_the_plate_comes_again_after_three_days_and_without_a_kitchen_problem_never(self):
        st = self.owing()
        for day in (24, 25, 26, 27, 28, 29):
            look(ON, at_dt(NOV(day), 10 * 60), st, "home")
        self.assertEqual(at(ON, at_dt(NOV(25), 19 * 60 + 10), st, "home", ["hegde"])[0], "exits_hegde_plate")
        with There(home=["hegde"]):
            self.assertIsNone(look(ON, at_dt(NOV(27), 19 * 60 + 10), st, "home")[1]["beat"])
            self.assertEqual(look(ON, at_dt(NOV(28), 19 * 60 + 10), st, "home")[1]["beat"]["id"], "exits_hegde_plate")
        paid = fresh(settled="2026-11-23", imprest=2000)
        for day in (24, 25):
            look(ON, at_dt(NOV(day), 10 * 60), paid, "home")
        self.assertNotEqual(at(ON, at_dt(NOV(25), 19 * 60 + 10), paid, "home", ["hegde"])[0], "exits_hegde_plate")

    def test_off_nobody_sets_a_plate(self):
        st = self.owing()
        for day in (24, 25):
            look(OFF, at_dt(NOV(day), 10 * 60), st, "home")
        self.assertNotIn("plain", st)
        self.assertNotEqual(at(OFF, at_dt(NOV(25), 19 * 60 + 10), st, "home", ["hegde"])[0], "exits_hegde_plate")


class Dues(unittest.TestCase):
    def wake(self, w, cash, asleep=True, day=26, st=None):
        st = st or fresh(settled="2026-11-25", imprest=cash)
        st["asleep"] = asleep
        with There(home=[]):
            return look(w, at_dt(NOV(day), 9 * 60 + 15), st, "home") + (st,)

    def test_the_fortnight_is_said_at_waking_when_the_dues_exceed_the_cash(self):
        sit, ctx, _ = self.wake(ON, 2400)
        self.assertIn("Due within the fortnight: ₹11,600 in all. ", sit["event"])              # wage, two Sundays, two Saturdays
        self.assertIn("Ramesh's wage ₹8,000 on Tuesday 1 December", sit["event"])
        self.assertIn("groceries ₹1,500 on Sunday 29 November and Sunday 6 December", sit["event"])
        self.assertIn("the dhobi ₹300 on Saturday 28 November and Saturday 5 December", sit["event"])
        self.assertIn("You hold ₹2,400.", sit["event"])
        self.assertIn("dues", ctx["opened"])

    def test_a_purse_that_holds_the_wage_but_not_the_fortnight_is_told(self):
        self.assertIn("Due within the fortnight", self.wake(ON, 9000)[0]["event"])           # night 2: he held about ₹10,000 on the eve of the wage
        self.assertNotIn("Due within the fortnight", self.wake(ON, 11600)[0]["event"])       # it carries them exactly

    def test_not_when_the_cash_carries_it_not_awake_and_not_off(self):
        self.assertNotIn("Due within the fortnight", self.wake(ON, 20000)[0]["event"])
        sit, ctx, _ = self.wake(ON, 2400, asleep=False)
        self.assertNotIn("Due within the fortnight", sit["event"])
        self.assertNotIn("dues", ctx["opened"])
        sit, ctx, st = self.wake(OFF, 2400)
        self.assertNotIn("Due within the fortnight", sit["event"])
        self.assertNotIn("dues", ctx["opened"])
        self.assertNotIn("dues_said", st)

    def test_part_time_amounts_are_respected(self):
        st = fresh(settled="2026-11-25", imprest=2400)
        st["flags"]["ramesh_parttime"] = True
        sit, _, _ = self.wake(ON, 2400, st=st)
        self.assertIn("Ramesh's wage, three days a week ₹4,000 on Tuesday 1 December", sit["event"])
        self.assertIn("groceries ₹900 on Sunday 29 November", sit["event"])

    def test_only_what_falls_due_in_fourteen_days(self):
        sit, _, _ = self.wake(ON, 100, day=17)                                        # the 1st is fourteen days off: the fortnight ends the day before
        self.assertIn("Due within the fortnight", sit["event"])
        self.assertNotIn("wage", sit["event"])

    def test_said_again_only_on_the_third_day(self):
        sit, _, st = self.wake(ON, 2400)
        self.assertEqual(st["dues_said"], "2026-11-26")
        self.assertIn("Due within the fortnight", self.wake(ON, 2400, st=st)[0]["event"])              # the same morning, rendered again
        self.assertNotIn("Due within the fortnight", self.wake(ON, 2400, day=27, st=st)[0]["event"])
        self.assertNotIn("Due within the fortnight", self.wake(ON, 2400, day=28, st=st)[0]["event"])
        self.assertIn("Due within the fortnight", self.wake(ON, 2400, day=29, st=st)[0]["event"])


class FileLine(unittest.TestCase):
    def refuse(self, vouched):
        w = World(file_act=True)
        st = fresh()
        st["beats"].append("saxena_query")
        if vouched:
            st["flags"]["file_vouched"] = "malhotra"
        with There(estates=["saxena"]):
            offer(w, at_dt(D(14), 11 * 60), st, "estates", yes=False)
        return st

    def test_a_refusal_keeps_mr_malhotras_letter_on_the_line(self):
        self.assertEqual(self.refuse(True)["file"],
                         "The query stands unanswered. A letter from Shri R. K. Malhotra, IAS (retired), is on the file.")

    def test_without_the_letter_the_line_is_what_it_was(self):
        self.assertEqual(self.refuse(False)["file"], "The query stands unanswered: proof of identity as Shri G. Hegde.")

    def test_it_is_a_general_rule_and_the_yes_branch_is_untouched(self):
        w = World(file_act=True)
        self.assertEqual(w.beat("saxena_reply")["choice"]["yes"]["file"], "His representation is on the file, in his own name: he is not Shri G. Hegde. Put up.")
        self.assertNotIn("file_if", w.beat("saxena_reply")["choice"]["yes"])
        st = fresh()
        beat = {"id": "x", "choice": {"yes": {"file": "plain", "file_if": [{"flags": {"a": 1, "b": 2}, "file": "both"}, {"flags": {"a": 1}, "file": "a"}]}}}
        for flags, want in (({}, "plain"), ({"a": 1}, "a"), ({"a": 1, "b": 2}, "both")):
            st["flags"] = dict(flags)
            World().settle_choice(beat, True, st, at_dt(D(14), 0))
            self.assertEqual(st["file"], want)


if __name__ == "__main__":
    unittest.main()
