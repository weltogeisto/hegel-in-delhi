"""P1, HEGEL_PROMISES: a promise is a record. The menu, the `act`, the check and its one retry, the record, the keeping by the engine
(tea, the plate, the engine's own meal and tea), what each side sees, and a rehearsed week. Off, nothing changes (tests/test_opened.py)."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO, Sandbox, answer, page_about, state  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import __main__ as cli  # noqa: E402
from world import contract, health, voices  # noqa: E402
from world.clock import at_dt, hm  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Days, Engine  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World  # noqa: E402

TUE = date(2026, 11, 17)
MENU = json.loads((REPO / "world/data/promises.json").read_text(encoding="utf-8"))["people"]["ramesh"]
OWES = {"cost": "groceries", "amount": 1500, "to": "Ramesh", "why": "groceries", "with": "ramesh", "at": "home", "since": "2026-11-15"}
TEA, PLATE = {"kind": "promise", "what": "tea", "minutes": 10}, {"kind": "promise", "what": "plate", "minutes": 15}


def when(hhmm, d=TUE):
    return at_dt(d, hm(hhmm))


def calm(w, t, pid="home"):
    """A state in which nothing but what a test sets is due: every beat done, fed an hour ago, the day's own meals and tea said."""
    st = state()
    st["place"], st["asleep"], st["owed"] = pid, False, []
    st["beats"] = [b["id"] for b in w.beats]
    st["last_meal"] = (t - timedelta(hours=1)).isoformat(timespec="minutes")
    st["today"] = {"woke": "09:15", "late": True, "power": True, "bad_air": True, "rain_reported": 10 ** 6, "seen": {pid: sorted(w.present_ids(pid, t, st))}}
    return st


def moment(w, t, st, day=None):
    return w.situation(t, st, day or {"steps": [], "entries": []}, None)


def make(w, st, act, hhmm, pid="home", says="I will see to it."):
    return w.promise_make("ramesh", act, says, when(hhmm), pid, st)


class Scripted(StubMind):
    """A voice that answers from a list, writing down what it was sent."""

    def __init__(self, *answers):
        self.answers, self.sent = list(answers), []

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        self.sent.append((json.loads(json.dumps(messages)), schema))
        a = self.answers.pop(0)
        return a if isinstance(a, str) else json.dumps(a)


def say(text, act=None, **kw):
    return dict({"says": text, "does": None, "act": act}, **kw)


class Voiced:
    """An engine on the sandbox's first day, for calls to `voice` at Tuesday 16:00 at home."""

    def __init__(self, mind, promises=True):
        self.box = Sandbox()
        self.engine = self.box.engine(mind)
        self.engine.world = World(promises=promises)
        self.day = self.box.days.load("2026-10-02")
        self.day["date"] = TUE.isoformat()
        t = when("11:00")
        self.day["state"] = calm(self.engine.world, t)
        self.sit = dict(day="Tuesday 17 November", time="11:00", place="home", outfit="white cotton kurta", event="He asks.", for_sale=[], weather="24 °C")

    def ask(self, cid="ramesh", says="Is there tea?"):
        return self.engine.voice(cid, self.day, self.sit, says)

    def close(self):
        self.box.close()


class Menu(unittest.TestCase):
    def test_the_menu_names_what_keeps_each_thing(self):
        data = json.loads((REPO / "world/data/promises.json").read_text(encoding="utf-8"))
        self.assertEqual(list(data["people"]), ["ramesh"])
        places = json.loads((REPO / "world/data/places.json").read_text(encoding="utf-8"))["places"]
        for what, x in MENU.items():
            self.assertTrue(x["says"] and x["kept_by"] and x["event"] and x["by_meal"], what)
            self.assertIn(x["place"], places)
            self.assertIn(x["keeps"], ("tea", "plate"))
            lo, hi = x["minutes"]
            self.assertTrue(5 <= lo < hi <= 240)
        self.assertEqual(MENU["tea"]["says"], "tea")
        self.assertEqual(MENU["plate"]["says"], "a plate of food")

    def test_the_switch(self):
        self.assertFalse(Config().promises)
        self.assertTrue(Config({"HEGEL_PROMISES": "1"}).promises)
        self.assertEqual(World().menu, {})
        self.assertEqual(list(World(promises=True).menu), ["ramesh"])
        self.assertTrue(cli.make_world(Config({"HEGEL_PROMISES": "1"})).promises)
        self.assertFalse(cli.make_world(Config()).promises)


class Act(unittest.TestCase):
    def test_schema_with_and_without(self):
        self.assertIs(contract.voice_schema(None), contract.VOICE_SCHEMA)
        self.assertIs(contract.voice_schema({}), contract.VOICE_SCHEMA)
        self.assertNotIn("act", contract.VOICE_SCHEMA["properties"])
        s = contract.voice_schema(MENU)
        act = s["properties"]["act"]["anyOf"]
        self.assertEqual(act[0], {"type": "null"})
        self.assertEqual(act[1]["properties"]["kind"]["enum"], ["promise"])
        self.assertEqual(act[1]["properties"]["what"]["enum"], ["tea", "plate"])
        self.assertEqual((act[1]["properties"]["minutes"]["minimum"], act[1]["properties"]["minutes"]["maximum"]), (5, 90))
        self.assertEqual(s["required"], ["says", "does"])            # `act` is optional
        self.assertNotIn("act", contract.VOICE_SCHEMA["properties"])    # the shared schema is untouched

    def test_prompt_with_and_without(self):
        w = World(promises=True)
        sit = dict(day="Tuesday 17 November", time="11:00", outfit="white cotton kurta", event="He asks.")
        plain = voices.render(w.cast["ramesh"], sit, "the bungalow", "Is there tea?", [], world_facts=["A fact."])
        self.assertNotIn("promise", plain)
        self.assertTrue(plain.endswith(contract.VOICE_ASK))
        self.assertEqual(plain, voices.render(w.cast["ramesh"], sit, "the bungalow", "Is there tea?", [], world_facts=["A fact."], menu=None))
        text = voices.render(w.cast["ramesh"], sit, "the bungalow", "Is there tea?", [], world_facts=["A fact."], menu=MENU)
        lines = contract.PROMISE_LINES.format(menu='tea (`what` "tea", 5 to 60 minutes), or a plate of food (`what` "plate", 5 to 90 minutes)')
        self.assertIn("- A fact.\n" + lines, text)                        # with the facts about the person
        self.assertEqual(lines.count("\n"), 3)
        self.assertTrue(text.endswith(contract.VOICE_ASK_ACT))
        self.assertEqual(text.replace(lines, "").replace(contract.VOICE_ASK_ACT, contract.VOICE_ASK), plain)

    def test_the_engine_asks_by_switch_and_menu(self):
        for promises, cid, menu in ((True, "ramesh", True), (True, "nidhi", False), (False, "ramesh", False)):
            mind = Scripted(say("Yes."))
            v = Voiced(mind, promises)
            try:
                v.ask(cid)
                messages, schema = mind.sent[0]
                self.assertEqual("act" in (schema or {}).get("properties", {}), menu, (promises, cid))
                self.assertEqual("`act`" in messages[1]["content"], menu)
                if not menu:
                    self.assertIs(schema, contract.VOICE_SCHEMA)
                    self.assertTrue(messages[1]["content"].endswith(contract.VOICE_ASK))
                    self.assertNotIn("promise", messages[1]["content"])
            finally:
                v.close()


class Check(unittest.TestCase):
    def setUp(self):
        self.w = World(promises=True)
        self.t = when("11:00")
        self.st = calm(self.w, self.t)

    def why(self, act, hhmm="11:00", pid="home", cid="ramesh"):
        return self.w.promise_problem(cid, act, when(hhmm), pid, self.st)

    def test_a_promise_it_can_keep(self):
        self.assertIsNone(self.why(TEA))
        self.assertIsNone(self.why(PLATE))

    def test_each_refusal(self):
        self.assertIn("not on your list", self.why({"kind": "promise", "what": "whisky", "minutes": 10}))
        self.assertIn("not on your list", self.why({"kind": "promise", "what": ["tea"], "minutes": 10}))
        self.assertIn("form", self.why({"kind": "vow", "what": "tea", "minutes": 10}))
        self.assertIn("form", self.why("tea"))
        for minutes in (4, 61, "10", 10.5, True, None):
            self.assertIn("a whole number from 5 to 60", self.why({"kind": "promise", "what": "tea", "minutes": minutes}), minutes)
        self.assertIn("from 5 to 90", self.why({"kind": "promise", "what": "plate", "minutes": 120}))
        self.assertIn("left by 20:35", self.why({"kind": "promise", "what": "tea", "minutes": 45}, "19:50"))      # Ramesh goes home at half past eight
        self.assertIn("after bedtime", self.why({"kind": "promise", "what": "tea", "minutes": 30}, "20:50"))
        self.assertEqual(self.why(TEA, pid="khan"), "it can be kept only at home")
        self.st["owed"] = [dict(OWES)]
        for act in (TEA, PLATE):
            self.assertIn("the kitchen is shut (Nothing is cooked at home: the groceries have not been paid for)", self.why(act))

    def test_a_second_promise_of_the_same_thing_is_refused(self):
        make(self.w, self.st, TEA, "11:00")
        self.assertEqual(self.why(TEA), "you have already promised him tea, and it is still open")
        self.assertIsNone(self.why(PLATE))                      # another thing may be promised
        self.st["promises"][0]["status"] = "kept"
        self.assertIsNone(self.why(TEA))                        # not once it is resolved

    def test_the_cast_hours_for_the_day(self):
        self.st["flags"]["ramesh_parttime"] = True              # Mondays, Thursdays and Saturdays only
        self.assertIsNone(self.w.promise_problem("ramesh", TEA, when("11:00", date(2026, 11, 19)), "home", self.st))      # Thursday
        self.assertIn("left by", self.w.promise_problem("ramesh", TEA, when("11:00"), "home", self.st))                  # Tuesday

    def test_a_person_without_a_menu_promises_nothing(self):
        self.assertIn("not on your list", self.w.promise_problem("nidhi", TEA, self.t, "home", self.st))

    def test_never_across_midnight_nor_bedtime(self):
        self.assertIn("after bedtime", self.why({"kind": "promise", "what": "tea", "minutes": 60}, "20:30"))


class Retry(unittest.TestCase):
    REFUSED = "The world refuses this promise: {}. Answer again; if you cannot promise it, do not."

    def run_voice(self, *answers):
        mind = Scripted(*answers)
        v = Voiced(mind)
        try:
            return v.ask(), mind, v.day["state"], v.engine
        finally:
            v.close()

    def test_a_promise_that_stands(self):
        got, mind, st, e = self.run_voice(say("Tea in ten.", TEA))
        self.assertEqual(len(mind.sent), 1)
        self.assertEqual(got["promise"], "p1")
        self.assertEqual(got["says"], "Tea in ten.")
        p = st["promises"][0]
        self.assertEqual({k: p[k] for k in ("id", "by", "what", "said", "made", "due", "place", "status")},
                         {"id": "p1", "by": "ramesh", "what": "tea", "said": "Tea in ten.", "made": "2026-11-17T11:00+05:30",
                          "due": "2026-11-17T11:10+05:30", "place": "home", "status": "open"})
        self.assertEqual(getattr(e, "_voice_retries", 0), 0)

    def test_no_act_is_never_retried(self):
        for a in (say("Tea in ten."), {"says": "Tea in ten."}, say("Tea in ten.", None)):
            got, mind, st, e = self.run_voice(a)
            self.assertEqual(len(mind.sent), 1)
            self.assertNotIn("promise", got)
            self.assertNotIn("promises", st)

    def test_refused_then_answered_again_without_a_promise(self):
        got, mind, st, e = self.run_voice(say("Tea in two hours.", {"kind": "promise", "what": "tea", "minutes": 120}), say("I cannot say when."))
        self.assertEqual(len(mind.sent), 2)
        second = mind.sent[1][0]
        self.assertEqual(second[:-2], mind.sent[0][0])                     # the same messages
        self.assertEqual(second[-2], {"role": "assistant", "content": json.dumps(say("Tea in two hours.", {"kind": "promise", "what": "tea", "minutes": 120}))})
        self.assertEqual(second[-1], {"role": "user", "content": self.REFUSED.format("the minutes for tea are a whole number from 5 to 60")})
        self.assertEqual(got["says"], "I cannot say when.")
        self.assertNotIn("promise", got)
        self.assertEqual(e._voice_retries, 1)
        self.assertNotIn("promises", st)

    def test_refused_then_made_good(self):
        got, mind, st, e = self.run_voice(say("Tea in two hours.", {"kind": "promise", "what": "tea", "minutes": 120}), say("Tea in twenty.", {"kind": "promise", "what": "tea", "minutes": 20}))
        self.assertEqual(got["says"], "Tea in twenty.")
        self.assertEqual(got["promise"], "p1")
        self.assertEqual((st["promises"][0]["said"], st["promises"][0]["due"]), ("Tea in twenty.", "2026-11-17T11:20+05:30"))
        self.assertEqual(e._voice_retries, 1)

    def test_a_second_refusal_drops_the_act_and_the_first_words_stand(self):
        bad = {"kind": "promise", "what": "tea", "minutes": 120}
        got, mind, st, e = self.run_voice(say("Tea in two hours.", bad), say("Tea in three hours.", bad))
        self.assertEqual(len(mind.sent), 2)                                # asked once more, not twice
        self.assertEqual(got["says"], "Tea in two hours.")
        self.assertNotIn("promise", got)
        self.assertNotIn("promises", st)
        self.assertEqual(e._voice_retries, 1)

    def test_an_unusable_second_answer_drops_the_act_too(self):
        got, mind, st, e = self.run_voice(say("Tea in two hours.", {"kind": "promise", "what": "tea", "minutes": 120}), "not json at all")
        self.assertEqual(got["says"], "Tea in two hours.")
        self.assertNotIn("promise", got)
        self.assertNotIn("promises", st)

    def test_a_second_promise_of_the_same_thing_is_refused_and_asked_again(self):
        got, mind, st, e = self.run_voice(say("Tea.", TEA))
        mind2 = Scripted(say("More tea.", TEA), say("No more tea."))
        v = Voiced(mind2)
        try:
            v.day["state"]["promises"] = st["promises"]
            got = v.ask()
        finally:
            v.close()
        self.assertEqual(mind2.sent[1][0][-1]["content"], self.REFUSED.format("you have already promised him tea, and it is still open"))
        self.assertNotIn("promise", got)
        self.assertEqual(len(st["promises"]), 1)

    def test_the_extra_call_is_counted_in_the_step(self):
        """A voice that always asks for the impossible: every step that has Ramesh answer carries one retry in its mind record."""
        class Pushy(StubMind):
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                if "act" in (schema or {}).get("properties", {}):
                    if "refuses this promise" in messages[-1]["content"]:
                        return json.dumps(say("Not today."))
                    return json.dumps(say("Tea in a day.", {"kind": "promise", "what": "tea", "minutes": 240}))
                return super().chat(messages, schema, max_tokens, temperature)
        box = Sandbox()
        try:
            e = box.engine(Pushy())
            e.world = World(promises=True)
            day = box.run_day(date(2026, 10, 3), e)
        finally:
            box.close()
        counted = [s for s in day["steps"] if s.get("mind", {}).get("voice_retries")]
        voiced = [s for s in day["steps"] if s.get("voice", {}).get("by") == "Ramesh"]
        self.assertTrue(counted)
        self.assertTrue(all(s["mind"]["voice_retries"] >= 1 and "promise" not in s for s in counted))
        self.assertTrue(voiced and all(s["mind"].get("voice_retries") for s in voiced))
        self.assertTrue(all("voice_retries" not in s["mind"] for s in day["steps"] if s not in counted))
        self.assertNotIn("promises", day["state"])


class Plated(unittest.TestCase):
    def test_a_plate_promised_to_the_stand_in_is_set_down_and_eaten_once(self):
        """Ramesh promises a plate in five minutes whenever he is asked; the stand-in takes it when it is set down."""
        class Plate(StubMind):
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                if "act" in (schema or {}).get("properties", {}) and "refuses this promise" not in messages[-1]["content"]:
                    return json.dumps(say("A plate in five.", PLATE_5))
                return super().chat(messages, schema, max_tokens, temperature)
        PLATE_5 = {"kind": "promise", "what": "plate", "minutes": 5}
        box = Sandbox()
        try:
            e = box.engine(Plate())
            e.world = World(promises=True)
            days = [box.run_day(date(2026, 10, 3) + timedelta(days=i), e) for i in range(3)]
        finally:
            box.close()
        steps = [(day, s) for day in days for s in day["steps"]]
        laid = [(day, s) for day, s in steps if "promise:plate" in s.get("opened", [])]
        self.assertTrue(laid)
        for day, s in laid:
            if "sets down the plate" in s["event"]:
                self.assertEqual(s["decision"]["action"], "eat")
                self.assertEqual(day["state"]["last_meal"][:10], day["date"])
        self.assertTrue(any("sets down the plate" in s["event"] for _, s in laid))
        for day in days:                                                    # a plate set down is on the page once, and no second "puts a plate together" beside it
            texts = [x["text"] for x in day["entries"] if x.get("k") == "world"]
            self.assertEqual(len(texts), len(set(texts)))


class Keeping(unittest.TestCase):
    def setUp(self):
        self.w = World(promises=True)

    def at(self, hhmm, st, pid=None, day=None):
        t = when(hhmm)
        if pid:
            st["place"] = pid
        sit, ctx = moment(self.w, t, st, day)
        return t, sit, ctx

    def test_tea_kept(self):
        st = calm(self.w, when("12:00"))
        make(self.w, st, TEA, "12:00")
        self.assertEqual(st["promises"][0]["due"], "2026-11-17T12:10+05:30")
        before = st.get("snacks", 0)
        _, sit, ctx = self.at("12:10", st)
        self.assertIn("Ramesh brings the tea he promised.", sit["event"])
        self.assertIn("promise:tea", ctx["opened"])
        self.assertIn({"k": "world", "text": "Ramesh brings the tea he promised."}, ctx["public"])
        p = st["promises"][0]
        self.assertEqual((p["status"], p["resolved"]), ("kept", "2026-11-17T12:10+05:30"))
        self.assertEqual(st["snacks"], before + 1)                     # as the engine's own tea: a snack
        _, sit2, ctx2 = self.at("12:20", st)
        self.assertNotIn("promised", sit2["event"])                    # said once
        self.assertEqual([x for x in ctx2["opened"] if x.startswith("promise")], [])
        self.assertNotIn("has promised", " ".join(sit2["on_mind"]))

    def test_the_first_moment_at_or_after_the_due_minute(self):
        st = calm(self.w, when("12:00"))
        make(self.w, st, TEA, "12:00")
        _, sit, ctx = self.at("12:05", st)
        self.assertEqual(st["promises"][0]["status"], "open")
        self.assertNotIn("promised", sit["event"])
        _, sit, ctx = self.at("12:45", st)                              # a long step ended late: kept then
        self.assertIn("promise:tea", ctx["opened"])
        self.assertEqual(st["promises"][0]["resolved"], "2026-11-17T12:45+05:30")

    def test_plate_kept_and_eaten_once_as_a_meal(self):
        st = calm(self.w, when("11:30"))
        st["last_meal"] = when("11:00").isoformat(timespec="minutes")      # fed half an hour ago: Ramesh's own plate would not come
        t = when("11:30")
        self.assertIsNone(self.w.plate(t, st))
        make(self.w, st, PLATE, "11:30")
        t, sit, ctx = self.at("11:45", st)
        dish = st["today"]["laid"]["dish"]
        self.assertIn(f"Ramesh sets down the plate he promised: {dish}.", sit["event"])
        self.assertIn("promise:plate", ctx["opened"])
        self.assertIn({"k": "world", "text": f"Ramesh sets down the plate he promised: {dish}."}, ctx["public"])
        self.assertEqual(st["promises"][0]["status"], "kept")
        self.assertEqual(self.w.plate(t, st), dish)
        self.assertIn(f"Ramesh has set down a plate: {dish}.", self.w.meal_status(t, st))
        self.assertIn(f"Household: No set meal now", " ".join(sit["on_mind"]))
        eat = answer(action="eat", place="home", minutes=30)
        errors, _, rep = self.w.check(eat, sit, dict(ctx, known_text="", recent=[]), st)
        self.assertEqual(errors, [])
        day = {"entries": [], "segments": [], "steps": []}
        self.w.apply(rep[0], rep[1], sit, ctx, st, day)
        self.assertEqual(st["last_meal"], "2026-11-17T11:45+05:30")        # a meal, for hunger
        self.assertEqual(st["snacks"], 0)
        self.assertNotIn("laid", st["today"])
        self.assertEqual([e["text"] for e in day["entries"] if "plate" in e.get("text", "")], [f"Ramesh sets down the plate he promised: {dish}."])      # on the page once
        self.assertIsNone(self.w.plate(when("12:15"), st))                 # and not again
        t2 = when("12:15")
        sit2, ctx2 = moment(self.w, t2, st)
        errors, _, _ = self.w.check(eat, sit2, dict(ctx2, known_text="", recent=[]), st)
        self.assertTrue(errors)

    def test_the_quiet_stand_in_eats_a_laid_plate_too(self):
        st = calm(self.w, when("11:30"))
        make(self.w, st, PLATE, "11:30")
        t, sit, ctx = self.at("11:45", st)
        e = Engine.__new__(Engine)
        e.world = self.w
        self.assertTrue(e.quiet_meal(st, t))
        st2 = calm(self.w, t)
        self.assertFalse(e.quiet_meal(st2, t))

    def test_a_meal_he_eats_elsewhere_takes_the_laid_plate_away(self):
        st = calm(self.w, when("11:45"))
        st["today"]["laid"] = {"dish": "a plate of khichdi with ghee", "id": "p1"}
        self.w.feed(st, when("11:50"), "snack")
        self.assertIn("laid", st["today"])
        self.w.feed(st, when("11:50"), "meal")
        self.assertNotIn("laid", st["today"])

    def test_the_engines_own_meal_keeps_the_plate_promise(self):
        st = calm(self.w, when("12:45"))
        make(self.w, st, PLATE, "12:45")                                   # due at 13:00, when lunch is laid out
        t, sit, ctx = self.at("13:00", st)
        self.assertEqual(sit["event"].count("laid out"), 2)                # "Ramesh has laid out lunch" and the promise kept by it
        self.assertIn("The lunch Ramesh has laid out is the plate he promised.", sit["event"])
        self.assertNotIn("sets down", sit["event"])
        self.assertNotIn("laid", st["today"])
        self.assertEqual(st["promises"][0]["status"], "kept")
        self.assertIn("promise:plate", ctx["opened"])
        self.assertEqual(ctx["opened"].count("meal"), 1)
        self.assertEqual(self.w.served(t, st), "lunch")
        self.assertIsNone(self.w.plate(t, st))                             # one meal, not two

    def test_the_engines_own_tea_keeps_the_tea_promise(self):
        st = calm(self.w, when("16:20"))
        make(self.w, st, TEA, "16:20")
        t, sit, ctx = self.at("16:35", st)
        self.assertIn("Ramesh brings tea: ", sit["event"])
        self.assertIn("The tea Ramesh brings is the tea he promised.", sit["event"])
        self.assertNotIn("Ramesh brings the tea he promised.", sit["event"])
        self.assertEqual(st["snacks"], 1)                                  # one tea
        self.assertEqual([e["text"] for e in ctx["public"] if "tea" in e.get("text", "")], ["Ramesh brings tea."])
        self.assertEqual(st["promises"][0]["status"], "kept")

    def test_lapsed_when_he_is_out(self):
        st = calm(self.w, when("12:00"), "khan")
        make(self.w, st, TEA, "12:00", pid="home")
        _, sit, ctx = self.at("12:30", st, "khan")
        self.assertEqual(st["promises"][0]["status"], "lapsed")
        self.assertNotIn("promised", sit["event"])
        self.assertEqual([x for x in ctx["opened"] if x.startswith("promise")], [])
        self.assertEqual(ctx["public"], [x for x in ctx["public"] if "promise" not in x["text"]])
        self.assertNotIn("laid", st["today"])

    def test_broken_when_the_kitchen_shuts_meanwhile(self):
        for act, hhmm in ((TEA, "12:10"), (PLATE, "12:15")):
            st = calm(self.w, when("12:00"))
            make(self.w, st, act, "12:00")
            st["owed"], st["imprest"] = [dict(OWES)], 0                    # the groceries fall due and he cannot pay them
            _, sit, ctx = self.at(hhmm, st)
            p = st["promises"][0]
            self.assertEqual((p["status"], p["why"]), ("broken", "the kitchen was shut"))
            self.assertNotIn("promised", sit["event"])                     # nothing is said now
            self.assertEqual([x for x in ctx["opened"] if x.startswith("promise")], [])
            self.assertNotIn("laid", st["today"])
            self.assertEqual(st.get("snacks", 0), 0)

    def test_broken_when_the_person_left_early(self):
        st = calm(self.w, when("19:50"))
        make(self.w, st, TEA, "19:50")
        st["promises"][0]["due"] = "2026-11-17T20:40+05:30"                # he was not at his desk of promises when it fell due: Ramesh had gone at half past eight
        _, sit, ctx = self.at("20:45", st)
        self.assertEqual((st["promises"][0]["status"], st["promises"][0]["why"]), ("broken", "Ramesh had left"))
        self.assertNotIn("promised", sit["event"])

    def test_never_across_midnight(self):
        st = calm(self.w, when("20:00"))
        make(self.w, st, TEA, "20:00")
        st["promises"][0]["due"] = "2026-11-17T20:50+05:30"
        _, sit, ctx = self.at("21:00", st)                                  # bedtime: Ramesh has gone and the day is out
        self.assertNotEqual(st["promises"][0]["status"], "open")
        st = calm(self.w, when("20:00"))
        make(self.w, st, TEA, "20:00")
        t = when("08:00", TUE + timedelta(days=1))
        st = dict(st, today={"woke": "08:00", "seen": {"home": ["ramesh"]}})
        moment(self.w, t, st)
        self.assertEqual(st["promises"][0]["status"], "lapsed")
        self.assertNotIn("laid", st["today"])
        st = calm(self.w, when("12:00"))
        make(self.w, st, TEA, "12:00")
        st["promises"][0]["due"] = "2026-11-17T21:30+05:30"
        moment(self.w, when("21:05"), st)
        self.assertEqual(st["promises"][0]["status"], "lapsed")            # bedtime comes before the due minute

    def test_the_record_keeps_the_last_twenty_resolved_and_all_open(self):
        st = calm(self.w, when("12:00"))
        for i in range(25):
            st.setdefault("promises", []).append({"id": f"x{i}", "by": "ramesh", "what": "tea", "said": "", "made": "2026-11-16T12:00+05:30",
                                                  "due": "2026-11-16T12:10+05:30", "place": "home", "status": "kept"})
        make(self.w, st, PLATE, "12:00")
        moment(self.w, when("12:05"), st)
        self.assertEqual([p["id"] for p in st["promises"] if p["status"] != "open"], [f"x{i}" for i in range(5, 25)])
        self.assertEqual([p["id"] for p in st["promises"] if p["status"] == "open"], ["p1"])
        moment(self.w, when("12:20"), st)
        self.assertEqual(len([p for p in st["promises"] if p["status"] != "open"]), 20)
        self.assertEqual(st["promises"][-1]["status"], "kept")


class Seen(unittest.TestCase):
    def setUp(self):
        self.w = World(promises=True)
        self.st = calm(self.w, when("12:00"))

    def test_his_line(self):
        make(self.w, self.st, TEA, "16:00")
        make(self.w, self.st, PLATE, "12:00")
        sit, _ = moment(self.w, when("12:00"), self.st)
        self.assertIn("Ramesh has promised tea by 16:10.", sit["on_mind"])
        self.assertIn("Ramesh has promised a plate of food by 12:15.", sit["on_mind"])
        self.assertLess(sit["on_mind"].index("Ramesh has promised tea by 16:10."), len(sit["on_mind"]) - 2)       # among what is on his mind, before his purse and body
        self.assertTrue(sit["on_mind"][-1].startswith("Body:"))

    def test_no_line_with_the_switch_off(self):
        w = World()
        st = calm(w, when("12:00"))
        sit, _ = moment(w, when("12:00"), st)
        self.assertEqual([x for x in sit["on_mind"] if "has promised" in x], [])

    def facts(self, st=None, today=TUE):
        return voices.recorded_facts(self.w, "ramesh", st or self.st, today=today.isoformat())

    def test_the_persons_facts(self):
        self.assertEqual([f for f in self.facts() if "promised" in f], [])
        make(self.w, self.st, TEA, "16:00")
        self.assertIn("You promised him tea by 16:10; it is not yet due.", self.facts())
        self.assertNotIn("promised", " ".join(voices.recorded_facts(self.w, "nidhi", self.st, today=TUE.isoformat())))
        self.assertNotIn("promised", " ".join(voices.recorded_facts(World(), "ramesh", self.st, today=TUE.isoformat())))
        self.assertNotIn("promised", " ".join(voices.recorded_facts(self.w, "ramesh", self.st)))

    def test_the_last_resolved_one_today_or_yesterday(self):
        def done(status, due, what="plate", **kw):
            return dict({"id": "x", "by": "ramesh", "what": what, "said": "", "made": due, "due": due, "place": "home", "status": status}, **kw)
        cases = [(done("lapsed", "2026-11-17T13:00+05:30"), "You promised him a plate of food by 13:00; he was out when it was due."),
                 (done("kept", "2026-11-17T13:00+05:30"), "You promised him a plate of food by 13:00; you brought it."),
                 (done("broken", "2026-11-17T13:00+05:30", why="the kitchen was shut"), "You promised him a plate of food by 13:00; you could not: the kitchen was shut."),
                 (done("kept", "2026-11-16T16:10+05:30", "tea"), "You promised him tea by 16:10 yesterday; you brought it.")]
        for p, line in cases:
            self.st["promises"] = [p]
            self.assertIn(line, self.facts())
        self.st["promises"] = [done("kept", "2026-11-15T16:10+05:30", "tea")]
        self.assertEqual([f for f in self.facts() if "promised" in f], [])       # the day before yesterday is not told
        self.st["promises"] = [done("kept", "2026-11-16T13:00+05:30"), done("lapsed", "2026-11-17T09:00+05:30")]
        self.assertEqual([f for f in self.facts() if "promised" in f], ["You promised him a plate of food by 09:00; he was out when it was due."])      # the last one only

    def test_facts_and_lines_are_facts(self):
        self.st["promises"] = [dict(id="x", by="ramesh", what="tea", said="", made="", due="2026-11-17T16:00+05:30", place="home", status="broken", why="the kitchen was shut")]
        for line in self.facts():
            self.assertNotRegex(line, r"(?i)\b(should|must|ought|sorry|guilt|disappoint|angry|ashamed)\b")


class Health(unittest.TestCase):
    def test_a_promise_kept_is_brought(self):
        self.assertIn("promise", health.BROUGHT_KINDS)
        self.assertEqual(health.brought_kinds({"opened": ["promise:tea", "meal"]}), ["promise:tea"])
        self.assertEqual(health.opening({"opened": ["promise:plate"], "event": "x"}, None), "brought")


class StandIn(unittest.TestCase):
    MSG = [{"role": "system", "content": "s"}, {"role": "user", "content": "He says: “Is there tea?”"}]

    def test_the_stub_reads_the_menu_from_the_schema(self):
        schema = contract.voice_schema(MENU)
        made = []
        for i in range(200):
            out = json.loads(StubMind().chat([self.MSG[0], {"role": "user", "content": f"He says: {i}"}], schema))
            if out.get("act"):
                made.append(out["act"])
                self.assertEqual(out["act"]["kind"], "promise")
                self.assertIn(out["act"]["what"], ("tea", "plate"))
        self.assertTrue(40 < len(made) < 120, len(made))
        self.assertEqual({a["what"] for a in made}, {"tea", "plate"})
        self.assertTrue(any(not 5 <= a["minutes"] <= 60 for a in made if a["what"] == "tea"))      # so that a rehearsal meets a refusal

    def test_the_stub_is_deterministic_and_does_not_promise_after_a_refusal(self):
        schema = contract.voice_schema(MENU)
        a, b = (StubMind().chat(self.MSG, schema) for _ in range(2))
        self.assertEqual(a, b)
        again = self.MSG + [{"role": "assistant", "content": a}, {"role": "user", "content": "The world refuses this promise: x. Answer again; if you cannot promise it, do not."}]
        self.assertNotIn("act", json.loads(StubMind().chat(again, schema)))

    def test_without_the_act_in_the_schema_its_answers_are_todays(self):
        for i in range(30):
            out = json.loads(StubMind().chat([self.MSG[0], {"role": "user", "content": f"He says: {i}"}], contract.VOICE_SCHEMA))
            self.assertEqual(set(out), {"says", "does"})


WEEK = 7


class Week(unittest.TestCase):
    def rehearse(self, out, sets):
        sim = cli.rehearsal_setup(Config(), "2026-10-03", out, False, sets, None)
        engine = Engine(sim, cli.make_world(sim), StubMind(), git=None)
        engine.lookup = page_about                # no test goes to Wikipedia: a live page one time and none the next made two runs differ
        d = date(2026, 10, 3)
        last = Days(out).latest()
        if cli.until_of(last).date() < d:
            last["state"]["until"] = cli.at_dt(d, 0).isoformat(timespec="minutes")
        return [cli.rehearse_day(engine, sim, out, d + timedelta(days=i)) for i in range(WEEK)]

    def test_a_week_makes_and_resolves_promises_and_is_the_same_twice(self):
        tmp = Path(tempfile.mkdtemp(prefix="hegel-promises-"))
        try:
            a = self.rehearse(tmp / "a", {"HEGEL_PROMISES": "1"})
            b = self.rehearse(tmp / "b", {"HEGEL_PROMISES": "1"})
            off = self.rehearse(tmp / "c", {})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        same = lambda days: re.sub(r'"latency_s": [\d.]+', "", json.dumps(days, sort_keys=True))        # the one thing a clock writes
        self.assertEqual(same(a), same(b))
        steps = [s for day in a for s in day["steps"]]
        made = [s["promise"] for s in steps if s.get("promise")]
        book = a[-1]["state"]["promises"]
        self.assertTrue(made)
        self.assertTrue({p["id"] for p in book} >= set(made[-1:]))
        status = {p["status"] for p in book}
        self.assertIn("kept", status)
        self.assertTrue(any("voice_retries" in s["mind"] for s in steps))
        self.assertTrue(any(k.startswith("promise:") for s in steps for k in s.get("opened", [])))
        self.assertTrue(any("the tea he promised" in e.get("text", "") or "the plate he promised" in e.get("text", "") for day in a for e in day["entries"]))
        self.assertFalse([p for p in book if p["status"] == "open" and p["due"][:10] < a[-1]["date"]])      # nothing open from an earlier day
        self.assertLessEqual(len([p for p in book if p["status"] != "open"]), 20)
        for day in off:                                                      # off: no trace
            self.assertNotIn("promises", day["state"])
            self.assertNotIn("promise_seq", day["state"])
            for s in day["steps"]:
                self.assertNotIn("promise", s)
                self.assertNotIn("voice_retries", s.get("mind", {}))
                self.assertFalse([k for k in s.get("opened", []) if k.startswith("promise")])


if __name__ == "__main__":
    unittest.main()
