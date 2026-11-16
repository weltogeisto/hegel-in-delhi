"""What is said and what is done agree: where he can eat, what an eating step needs, and what a voice may promise.

At the IIC on 17 November (Day 47) the guard's voice offered a cafeteria, a meal token and a lift that the world did not have; he
said for three hours that he would go and eat, chose "stay" and "talk", and a step "eat" at a place where he bought nothing fed no one."""
import json
import shutil
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO, answer, state  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import voices  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.world import World, at_dt  # noqa: E402

SAT = date(2026, 10, 3)


def at(h, m=0, d=SAT):
    return at_dt(d, h * 60 + m)


class EatingOutTest(unittest.TestCase):
    def setUp(self):
        self.w = World()
        self.st = state()
        self.st["imprest"] = 2000

    def check(self, when, place, **kw):
        sit = {"open_now": self.w.open_places(when, self.st)}
        ctx = {"t": when, "present": [], "beat": None, "public": []}
        return self.w.check(answer(place=place, **kw), sit, ctx, self.st)

    def test_the_iic_serves_a_meal_that_feeds_him(self):
        errors, _, rep = self.check(at(13), "iic", action="eat", buys=[{"item": "Lunch in the IIC dining hall", "price_inr": 480}])
        self.assertEqual(errors, [])
        buy = rep[1]["buys"][0]
        self.assertEqual((buy["price"], buy["food"]), (480, "meal"))

    def test_the_iic_coffee_house_sells_a_snack_and_coffee_that_is_not_food(self):
        errors, _, rep = self.check(at(15), "iic", action="eat", buys=[{"item": "a sandwich", "price_inr": 160}])
        self.assertEqual((errors, rep[1]["buys"][0]["food"]), ([], "snack"))
        errors, _, _ = self.check(at(15), "iic", action="eat", buys=[{"item": "filter coffee", "price_inr": 110}])
        self.assertTrue(any("means buying food" in x for x in errors), errors)                  # coffee is bought, but it is not a meal

    def test_eating_where_nothing_is_bought_is_refused_and_says_where_food_is(self):
        errors, _, _ = self.check(at(13), "iic", action="eat")
        (msg,) = [x for x in errors if "means buying food" in x]
        self.assertIn("Lunch in the IIC dining hall", msg)                                        # what is sold here, in the refusal
        errors, _, _ = self.check(at(14), "gandhi", action="eat")
        (msg,) = [x for x in errors if "means buying food" in x]
        self.assertIn("nothing to eat is sold at Gandhi Smriti", msg)
        self.assertIn("Khan Market, 20 min on foot: Chole bhature at a dhaba ₹180", msg)
        self.assertIn("the IIC, 19 min on foot", msg)
        self.assertIn("at home:", msg)

    def test_a_cup_of_chai_is_not_a_meal_but_a_samosa_is_a_snack(self):
        errors, _, _ = self.check(at(12), "khan", action="eat", buys=[{"item": "chai", "price_inr": 20}])
        self.assertTrue(any("means buying food" in x for x in errors), errors)
        errors, _, _ = self.check(at(12), "khan", action="eat", buys=[{"item": "a samosa", "price_inr": 30}])
        self.assertEqual(errors, [])

    def test_eating_at_home_is_judged_as_before(self):
        errors, _, _ = self.check(at(11), "home", action="eat")
        self.assertFalse(any("means buying food" in x for x in errors), errors)

    def food_lines(self, when, **st):
        self.st.update(place="gandhi", last_meal="2026-10-03T07:30+05:30", snacks=0, **st)
        self.st["today"] = {"woke": "06:00"}
        sit, _ = self.w.situation(when, self.st, {"segments": [], "entries": [], "steps": []}, None)
        return sit, [x for x in sit["on_mind"] if x.startswith("Food:")]

    def test_hungry_he_is_told_where_food_is_and_otherwise_not(self):
        sit, lines = self.food_lines(at(11))                                                    # three and a half hours, no meal's window: nothing
        self.assertEqual(lines, [])
        sit, (line,) = self.food_lines(at(14))                                                  # hungry (more than five hours awake) and in lunch's window
        self.assertIn("nothing to eat is sold at Gandhi Smriti", line)
        self.assertIn("Khan Market, 20 min on foot", line)
        self.assertNotIn("..", line)
        self.assertTrue(sit["on_mind"][-1].startswith("Body:"))                                 # the Body line stays last

    def test_a_meal_window_without_a_meal_in_it_is_enough_but_not_a_meal_in_it(self):
        sit, lines = self.food_lines(at(13, 30))                                                # lunch's window (13:00-14:30), last meal at 07:30
        self.assertEqual(len(lines), 1)
        self.st["last_meal"] = "2026-10-03T13:10+05:30"                                         # he has eaten since it opened
        sit, _ = self.w.situation(at(13, 30), self.st, {"segments": [], "entries": [], "steps": []}, None)
        self.assertFalse([x for x in sit["on_mind"] if x.startswith("Food:")])

    def test_at_home_with_a_meal_laid_out_the_household_line_is_enough(self):
        self.st.update(place="home", last_meal="2026-10-03T07:30+05:30", snacks=0)
        self.st["today"] = {"woke": "06:00"}
        sit, _ = self.w.situation(at(13, 30), self.st, {"segments": [], "entries": [], "steps": []}, None)   # Saturday: Ramesh is there and lunch is served
        self.assertFalse([x for x in sit["on_mind"] if x.startswith("Food:")])
        self.assertTrue(any(x.startswith("Household:") for x in sit["on_mind"]))

    def test_where_food_is_sold_the_line_does_not_repeat_the_list(self):
        self.st.update(place="iic", last_meal="2026-10-03T07:30+05:30", snacks=0)
        self.st["today"] = {"woke": "06:00"}
        sit, _ = self.w.situation(at(14), self.st, {"segments": [], "entries": [], "steps": []}, None)
        (line,) = [x for x in sit["on_mind"] if x.startswith("Food:")]
        self.assertNotIn("nothing to eat", line)
        self.assertNotIn("dining hall", line)                                                   # "For sale here" already says it
        self.assertTrue(any("dining hall" in x for x in sit["for_sale"]))


class TalkRunTest(unittest.TestCase):
    def day(self, *steps):
        return {"steps": [{"t": t, "decision": {"action": a, "place": p}, **({"voice": {"by": v, "says": "x"}} if v else {})} for t, a, p, v in steps]}

    def test_a_run_of_talk_is_a_plain_fact(self):
        w, guard = World(), "The guard at the library"
        steps = [(f"10:{i:02d}", "talk", "iic", guard) for i in range(0, 50, 10)]
        self.assertEqual(w.talk_run(self.day(*steps), "iic"),
                         "You have been talking at the IIC for 5 steps in a row, since 10:00 (answers from The guard at the library).")
        self.assertIsNone(w.talk_run(self.day(*steps[:3]), "iic"))                              # under TALK_RUN
        self.assertIsNone(w.talk_run(self.day(*steps, ("10:50", "read", "iic", None)), "iic"))  # broken by anything else
        self.assertIsNone(w.talk_run(self.day(*steps, ("10:50", "talk", "khan", None)), "khan"))
        self.assertIsNone(w.talk_run({"steps": []}, "iic"))


class VoiceFactsTest(unittest.TestCase):
    def setUp(self):
        self.w, self.st = World(), state()

    def test_a_place_that_sells_nothing_says_so_and_names_the_meal(self):
        facts = voices.place_facts(self.w, "gandhi", at(14), self.st)
        self.assertTrue(facts[0].startswith("No food is served at Gandhi Smriti: there is no canteen, café, kitchen, counter, meal token"))
        self.assertIn("Khan Market, 20 minutes on foot (Chole bhature at a dhaba ₹180)", facts[1])

    def test_a_place_with_food_or_the_home_adds_nothing(self):
        self.assertEqual(voices.place_facts(self.w, "iic", at(14), self.st), [])
        self.assertEqual(voices.place_facts(self.w, "khan", at(14), self.st), [])
        self.assertEqual(voices.place_facts(self.w, "home", at(14), self.st), [])

    def test_the_voice_is_told_both_in_its_message(self):
        e = Engine.__new__(Engine)
        e.world, e.voice_prompt = self.w, "Delhi NPC"
        e.memory = mock.Mock()
        e.memory.before.return_value, e.memory.moments.return_value = [], []
        e.mind = mock.Mock(spec=["chat"])
        e.mind.chat.return_value = '{"says":"Ji.","does":null}'
        day = {"date": "2026-10-03", "state": self.st}
        sit = dict(day="Saturday 3 October", time="14:00", place="gandhi", outfit="white cotton kurta", event="He asks for lunch.", for_sale=[])
        e.voice("kapoor", day, sit, "Where can I eat?")
        text = e.mind.chat.call_args.args[0][-1]["content"]
        self.assertIn("No food is served at Gandhi Smriti", text)
        self.assertIn("do not offer, promise or point him to a canteen", text)
        self.assertIn("Listed goods and prices here: none listed", text)

    def test_the_voice_prompt_asks_for_the_third_person_and_for_nothing_invented(self):
        text = (REPO / "mind/voices.md").read_text(encoding="utf-8")
        self.assertIn('never "I pull ..."', text)
        self.assertIn("Offer only what the message shows", text)

    def test_what_a_voice_does_is_never_written_in_the_first_person(self):
        c = self.w.cast["guard"]
        said = voices.clean(c, {"says": "Take the lift.", "does": "I gesture towards the front desk."})
        self.assertEqual((said["says"], said["does"]), ("Take the lift.", None))
        for does in ("I'm waving him on.", "My hand points to the desk.", "We nod."):
            self.assertIsNone(voices.clean(c, {"says": "Ji.", "does": does})["does"], does)
        for does in ("She gestures towards the front desk.", "Imran nods.", "Wendy looks up."):
            self.assertEqual(voices.clean(c, {"says": "Ji.", "does": does})["does"], does)


class PageTest(unittest.TestCase):
    """The page draws what the words say: a talk is a talk even in a library, and the guard and the programme officer have figures."""

    HTML = (REPO / "docs/index.html").read_text(encoding="utf-8")

    def run_js(self, body):
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        h = self.HTML
        grab = lambda a, b: h[h.index(a):h.index(b, h.index(a))]
        harness = ("const acts = " + json.dumps(grab("const ACTS = [", "function actAt(")) + ", who = " + json.dumps(grab("const WHO = {", "function lastOf(")) + ";\n"
                   "const page = new Function(acts + '\\n' + who + '; return {actsOf, keyOfSpeaker, WHO};')();\n" + body)
        out = subprocess.run(["node", "-e", harness], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_the_script_parses(self):
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        js = self.HTML[self.HTML.index("<script>") + 8:self.HTML.rindex("</script>")]
        out = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(0, 'utf8')); console.log('ok')"], input=js, capture_output=True, text=True,
                             encoding="utf-8")
        self.assertEqual(out.stdout.strip(), "ok", out.stderr)

    def test_the_verb_of_the_step_decides_what_he_is_doing_not_the_word_library(self):
        segs = [{"now": "Talking with the guard at the library and the programme officer at the IIC.", "at": "iic"},
                {"now": "Talking with the librarian at the IIC.", "at": "iic"}, {"now": "Eating at the IIC.", "at": "iic"},
                {"now": "Reading at the IIC.", "at": "iic"}, {"now": "At the IIC.", "at": "iic"}, {"now": "Resting at home.", "at": "home"},
                {"now": "Writing at home.", "at": "home"}, {"now": "At home. Breakfast, then the Constitution of India, then his own notebook.", "at": "home"},
                {"now": "Asleep.", "at": "home", "asleep": True}]
        got = self.run_js("console.log(JSON.stringify(" + json.dumps(segs) + ".map(s => page.actsOf(s))));")
        self.assertEqual(got, [["talk"], ["talk"], ["eat"], ["read"], ["read"], ["rest"], ["write"], ["eat", "read", "write"], ["sleep"]])

    def test_the_guard_and_the_programme_officer_are_somebody(self):
        got = self.run_js("console.log(JSON.stringify(['The guard at the library', 'The programme officer', 'The librarian', 'Ramesh', 'Mr. Saxena']"
                          ".map(by => page.keyOfSpeaker(by))));")
        self.assertEqual(got, ["guard", "officer", "librarian", "ramesh", "saxena"])
        for who in ("guard", "officer"):
            self.assertRegex(self.HTML, rf"\n  {who}:\s+\{{skin:")                                   # a figure to draw

    def test_eating_at_the_iic_is_drawn_in_the_dining_hall_and_the_library_librarian_does_not_eat(self):
        self.assertIn("seg.at === 'iic' && actAt(seg, m) === 'eat' ? 'iicd' : seg.at", self.HTML)
        self.assertIn("iicd: IICD_ROOM", self.HTML)
        self.assertNotIn("'eat' : 'sitF', '', 1),150,108, 'librarian'", self.HTML)


if __name__ == "__main__":
    unittest.main()
