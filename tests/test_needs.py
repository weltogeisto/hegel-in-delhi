"""Tests for the morning plan, the body's needs, theses that show their evidence, and a rehearsed week."""
import json
import re
import shutil
import statistics
import subprocess
import sys
import threading
import unittest
from datetime import date, timedelta
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO, FakeLlama, Sandbox, answer, state  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import contract, owl  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import HTTPMind, MindAway, StubMind  # noqa: E402
from world.world import World, at_dt, repeats  # noqa: E402

SAT, WED = date(2026, 10, 3), date(2026, 10, 7)       # Ramesh is off on Wednesdays


class Planner(StubMind):
    """Answers the plan call with `plan` (a dict, a string, or an exception to raise); everything else as the stub."""

    def __init__(self, plan):
        self.plan, self.calls, self.seen = plan, [], []

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        if "plan" in (schema or {}).get("properties", {}):
            self.calls.append(messages)
            if isinstance(self.plan, Exception):
                raise self.plan
            return self.plan if isinstance(self.plan, str) else json.dumps(self.plan)
        return super().chat(messages, schema, max_tokens, temperature)

    def decide(self, messages, sit):
        self.seen.append(messages[1]["content"])
        return super().decide(messages, sit)


def item(time, what):
    return {"time": time, "intention": what}


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def run_with(self, mind, d=SAT):
        day = self.box.run_day(d, self.box.engine(mind))
        return day, [s for s in day["steps"] if "decision" in s]

    def test_a_morning_plan_is_made_stored_and_revealed(self):
        day, steps = self.run_with(StubMind())
        plan = day["plan"]
        self.assertEqual(plan["written"], steps[0]["t"])                                    # on the wake-up step
        self.assertTrue(3 <= len(plan["items"]) <= 6)
        for i in plan["items"]:
            self.assertRegex(i["time"], r"^\d\d:\d\d$")
            self.assertLessEqual(len(i["intention"]), 120)
        entry = next(e for e in day["entries"] if e["k"] == "plan")
        self.assertEqual(entry, {"k": "plan", "t": steps[0]["t"], "items": plan["items"]})
        self.assertEqual(sum(e["k"] == "plan" for e in day["entries"]), 1)

    def test_one_extra_call_before_the_decision_and_the_plan_is_on_his_mind_all_day(self):
        mind = Planner({"plan": [item("08:00", "Lodhi Gardens with the papers"), item("11:00", "Khan Market for ink"), item("13:00", "Lunch at home")]})
        day, steps = self.run_with(mind)
        self.assertEqual(len(mind.calls), 1)
        ask = mind.calls[0][1]["content"]
        self.assertTrue(ask.endswith(contract.PLAN_ASK))
        self.assertNotIn("Decide your next step", ask)
        self.assertEqual(len(mind.seen), len(steps))                                        # a decision came after the plan
        line = "Your plan for today: 08:00 Lodhi Gardens with the papers; 11:00 Khan Market for ink; 13:00 Lunch at home."
        self.assertTrue(all(line in m for m in mind.seen))                                  # the wake-up decision too
        self.assertEqual(day["plan"]["items"][1], item("11:00", "Khan Market for ink"))
        first = mind.seen[0]
        self.assertLess(first.index("Your plan for today"), first.index("Body:"))
        nxt = self.box.days.load(SAT + timedelta(days=1))
        self.assertNotIn("plan", nxt)                                                       # a new day, a new plan

    def test_no_plan_when_the_mind_is_away_or_answers_nonsense(self):
        for plan in (MindAway("no answer"), "I would rather not.", {"plan": []}, {"plan": "Lodhi"}, {"nothing": 1}):
            with self.subTest(plan=str(plan)):
                box = Sandbox()
                try:
                    day = box.run_day(SAT, box.engine(Planner(plan)))
                    steps = [s for s in day["steps"] if "decision" in s]
                    self.assertNotIn("plan", day)
                    self.assertFalse(any(e["k"] == "plan" for e in day["entries"]))
                    self.assertEqual({s["mind"]["source"] for s in steps}, {"stub"})        # he carried on
                finally:
                    box.close()

    def test_invalid_items_are_dropped(self):
        ok = item("09:30", "Walk to Safdarjung's Tomb")
        plan = {"plan": [ok, item("25:00", "An hour that does not exist"), item("noon", "Not a time"), item("10:00", "x" * 121),
                         item("10:30", "Plan a murder"), item("11:00", "Read what Marx wrote"), item("11:30", ""), "text", item("9:05", "  Tea   on the verandah ")]}
        day, _ = self.run_with(Planner(plan))
        self.assertEqual(day["plan"]["items"], [ok, item("10:30", "Plan a murder"), item("09:05", "Tea on the verandah")])    # no never-list any more; Marx is not met yet
        many = {"plan": [item(f"{h:02d}:00", f"Intention number {h}") for h in range(7, 15)]}
        box = Sandbox()
        try:
            self.assertEqual(len(box.run_day(SAT, box.engine(Planner(many)))["plan"]["items"]), 6)
        finally:
            box.close()

    def test_not_asked_when_he_is_sent_to_bed_or_the_world_resumes(self):
        mind = Planner(None)
        e = self.box.engine(mind)
        prev = self.box.days.load(date(2026, 10, 2))
        prev["state"]["asleep"] = False
        self.box.days.save(e.new_day(prev, SAT))
        e.advance(at_dt(SAT, 40))                                                           # awake at midnight: no waking, so no plan
        self.assertEqual(mind.calls, [])
        box = Sandbox()
        try:
            mind = Planner(None)
            box.engine(mind).advance(at_dt(date(2026, 10, 7), 14 * 60))                     # a resume after a gap
            self.assertEqual(mind.calls, [])
        finally:
            box.close()

    def test_the_stand_in_answers_the_plan_schema_the_same_way_every_time(self):
        ask = [{"role": "user", "content": "x"}]
        a = StubMind().chat(ask, contract.PLAN_SCHEMA)
        self.assertEqual(a, StubMind().chat(ask, contract.PLAN_SCHEMA))
        self.assertTrue(3 <= len(json.loads(a)["plan"]) <= 6)

    def test_the_plan_call_goes_out_with_its_schema(self):
        server = HTTPServer(("127.0.0.1", 0), FakeLlama)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        FakeLlama.calls = []
        try:
            e = self.box.engine(HTTPMind(f"http://127.0.0.1:{server.server_port}"))
            now = at_dt(SAT, 0)
            while now < at_dt(SAT, 6 * 60):          # a quiet night, then the wake-up step
                e.advance(now)
                now += timedelta(minutes=5)
        finally:
            server.shutdown()
            server.server_close()
        schema = FakeLlama.calls[0]["response_format"]["json_schema"]["schema"]
        self.assertEqual(list(schema["properties"]), ["plan"])
        self.assertIn("plan today", FakeLlama.calls[0]["messages"][1]["content"])
        self.assertNotIn("plan", self.box.days.load(SAT))                                   # the fake answers with a decision: unusable

    def test_the_page_shows_a_plan_entry_and_the_changes_the_owl_made(self):
        html = (REPO / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn("plan:'Plan'", html)
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        js = html[html.index("<script>") + 8:html.rindex("</script>")]
        out = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(0, 'utf8')); console.log('ok')"], input=js,
                             capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "ok", out.stderr)                              # the page's script still parses
        harness = """
        const h = require('fs').readFileSync(process.argv[1], 'utf8');
        const grab = (a, b) => { const i = h.indexOf(a); return h.slice(i, h.indexOf(b, i)); };
        const src = ["const esc = s =>", "const rupees", "const paras = t =>"].map(a => grab(a, "\\n")).concat(
          [grab("function line(e){", "function owlHtml"), grab("function owlHtml(m){", "function renderPanel")]).join("\\n");
        const D = JSON.parse(process.argv[2]), page = new Function("D", "DAY", "dayMode", src + "; return {line, owlHtml};")(D, [], 'archive');
        console.log(JSON.stringify([page.line(D.entry), page.owlHtml(0)]));"""
        day = {"entry": {"k": "plan", "t": "06:00", "items": [item("09:00", "Lodhi Gardens with the papers"), item("13:00", "Lunch at <home>")]},
               "state": {"theses": [{"id": "india", "text": "India has no history", "status": "revised"}]},
               "owl": {"diary": "A diary.", "revision_log": "Something moved.",
                       "theses": [{"id": "india", "from": "shaken", "to": "revised", "evidence": [{"t": "14:05", "text": "Article 17"}]}]}}
        got = subprocess.run(["node", "-e", harness, str(REPO / "docs/index.html"), json.dumps(day)], capture_output=True, text=True)
        line, owl_html = json.loads(got.stdout)
        self.assertEqual(line, "09:00 Lodhi Gardens with the papers · 13:00 Lunch at &lt;home&gt;")
        self.assertIn("<h3>Revision log</h3><p>Something moved.</p><p>India has no history: shaken → revised (14:05 “Article 17”)</p>", owl_html)
        day["owl"] = {"written": "03:10", "depesche": {"title": "Depesche", "text": "x"}}                  # day one's owl: as before
        self.assertNotIn("Revision log", json.loads(subprocess.run(["node", "-e", harness, str(REPO / "docs/index.html"), json.dumps(day)],
                                                                   capture_output=True, text=True).stdout)[1])


def play(w, st, when, **kw):
    """One decision at `when`, through the world's own situation, check and apply. Returns the day it wrote to."""
    day = st.setdefault("_day", {"segments": [], "entries": [], "steps": []})
    sit, ctx = w.situation(when, st, day, None)
    errors, _, rep = w.check(answer(**kw), sit, ctx, st)
    assert not errors, errors
    w.apply(rep[0], rep[1], sit, ctx, st, day)
    return sit


class NeedsTest(unittest.TestCase):
    def setUp(self):
        self.w = World()
        self.st = state()

    def at(self, d, h, m=0):
        return at_dt(d, h * 60 + m)

    def test_the_body_line(self):
        self.st["last_meal"], self.st["today"] = "2026-10-03T08:40+05:30", {"woke": "05:58", "walked": 7500}
        line, felt = self.w.needs(self.at(SAT, 13, 40), self.st)
        self.assertEqual(line, "Body: last meal 08:40, five hours ago; walked 7.5 km today; awake since 05:58.")
        self.assertEqual(felt, [])

    def test_without_a_last_meal_he_dined_at_eight_the_evening_before(self):
        self.st["today"] = {"woke": "05:58"}
        line, felt = self.w.needs(self.at(SAT, 6), self.st)
        self.assertEqual(line, "Body: last meal yesterday 20:00, ten hours ago; walked 0.0 km today; awake since 05:58.")
        self.assertEqual(felt, [])                                  # the night's fast is not hunger: the clock runs from waking

    def test_hungry_once_very_hungry_once_and_again_after_eating(self):
        self.st["last_meal"], self.st["today"] = "2026-10-03T08:40+05:30", {"woke": "08:00"}
        self.assertEqual(self.w.needs(self.at(SAT, 13, 40), self.st)[1], [])
        self.assertEqual(self.w.needs(self.at(SAT, 13, 41), self.st)[1], ["You are hungry."])
        self.assertEqual(self.w.needs(self.at(SAT, 14, 30), self.st)[1], [])                 # once
        self.assertEqual(self.w.needs(self.at(SAT, 16, 41), self.st)[1], ["You are very hungry."])
        self.assertEqual(self.w.needs(self.at(SAT, 17, 30), self.st)[1], [])
        self.w.feed(self.st, self.at(SAT, 18), "meal")
        self.assertEqual(self.st["last_meal"], "2026-10-03T18:00+05:30")
        self.assertEqual(self.w.needs(self.at(SAT, 20), self.st)[1], [])
        self.assertEqual(self.w.needs(self.at(SAT, 23, 1), self.st)[1], ["You are hungry."])   # a new episode

    def test_a_snack_pushes_hunger_back_two_hours(self):
        self.st["last_meal"], self.st["today"] = "2026-10-03T08:40+05:30", {"woke": "05:58"}
        self.w.feed(self.st, self.at(SAT, 12), "snack")
        line, felt = self.w.needs(self.at(SAT, 13, 41), self.st)
        self.assertEqual(felt, [])
        self.assertIn("last meal 08:40, five hours ago and a snack since;", line)
        self.assertEqual(self.w.needs(self.at(SAT, 15, 40), self.st)[1], [])
        self.assertEqual(self.w.needs(self.at(SAT, 15, 41), self.st)[1], ["You are hungry."])

    def test_tired_once_from_distance_or_from_hours_awake(self):
        self.st["last_meal"], self.st["today"] = "2026-10-03T12:00+05:30", {"woke": "07:00", "strain": 9999}
        self.assertEqual(self.w.needs(self.at(SAT, 13), self.st)[1], [])
        self.st["today"]["strain"] = 10000
        self.assertEqual(self.w.needs(self.at(SAT, 13, 5), self.st)[1], ["You are tired."])
        self.assertEqual(self.w.needs(self.at(SAT, 13, 10), self.st)[1], [])
        st = state()
        st["last_meal"], st["today"] = "2026-10-03T19:00+05:30", {"woke": "06:00"}
        self.assertEqual(self.w.needs(self.at(SAT, 21, 59), st)[1], [])
        self.assertEqual(self.w.needs(self.at(SAT, 22), st)[1], ["You are tired."])

    def test_walking_counts_75_metres_a_minute_and_heat_makes_it_harder(self):
        cool = {"temp": 24, "sky": "clear", "rain": 0, "aqi": 50}
        walked = self.w.walk("home", "lodhi") * 75           # the walk table's minutes, at 75 metres a minute
        for temp, strain in ((24, walked), (33, walked * 3 // 2)):
            st = state()
            self.w._wx[SAT] = {"source": "test", "hours": [dict(cool, temp=temp)] * 24}
            play(self.w, st, self.at(SAT, 9), action="walk", place="lodhi", minutes=30)
            self.assertEqual(st["today"]["walked"], walked)
            self.assertEqual(st["today"]["strain"], strain)
            line, _ = self.w.needs(self.at(SAT, 10), st)
            self.assertIn(f"walked {walked / 1000:.1f} km today", line)
        self.w._wx[SAT]["hours"][9]["temp"] = 24
        st = state()
        st["today"] = {"woke": "06:00", "strain": 9000, "walked": 9000}
        play(self.w, st, self.at(SAT, 9), action="walk", place="lodhi", minutes=30)
        self.assertEqual(self.w.needs(self.at(SAT, 10), st)[1], ["You are tired."])

    def test_the_events_come_with_the_situation_and_once(self):
        self.st["place"], self.st["last_meal"], self.st["today"] = "lodhi", "2026-10-03T07:30+05:30", {"woke": "06:00"}
        day = {"segments": [], "entries": [], "steps": []}
        sit, ctx = self.w.situation(self.at(SAT, 13, 30), self.st, day)
        self.assertTrue(sit["event"].endswith("You are hungry."))
        self.assertTrue(sit["on_mind"][-1].startswith("Body: last meal 07:30, six hours ago"))
        sit, ctx = self.w.situation(self.at(SAT, 14), self.st, day)
        self.assertNotIn("hungry", sit["event"])

    def test_breakfast_is_laid_out_once_when_ramesh_is_there(self):
        day = {"segments": [], "entries": [], "steps": []}
        sit, _ = self.w.situation(self.at(SAT, 7, 30), self.st, day)
        self.assertIn("Ramesh has laid out breakfast: ", sit["event"])
        sit, _ = self.w.situation(self.at(SAT, 8), self.st, day)
        self.assertNotIn("breakfast", sit["event"])
        st = state()
        sit, _ = self.w.situation(self.at(WED, 7, 30), st, day)                              # his day off
        self.assertNotIn("breakfast", sit["event"])
        sit, _ = self.w.situation(self.at(SAT, 9, 45), state(), day)                         # the window closed at half past nine
        self.assertNotIn("breakfast", sit["event"])

    def test_eating_at_home_is_a_meal_only_when_a_meal_is_laid_out(self):
        st = state()
        sit, ctx = self.w.situation(self.at(SAT, 11), st, {"steps": []})
        self.assertTrue(self.w.check(answer(action="eat", place="home"), sit, ctx, st)[0])  # unavailable eating is refused
        self.assertNotIn("last_meal", st)                                                    # nothing on the table at eleven
        play(self.w, st, self.at(SAT, 13, 10), action="eat", place="home")
        self.assertEqual(st["last_meal"], "2026-10-03T13:10+05:30")
        st = state()
        play(self.w, st, self.at(SAT, 7, 30), action="eat", place="home")
        self.assertEqual(st["last_meal"], "2026-10-03T07:30+05:30")                          # breakfast counts
        st = state()
        sit, ctx = self.w.situation(self.at(WED, 13, 10), st, {"steps": []})
        self.assertTrue(self.w.check(answer(action="eat", place="home"), sit, ctx, st)[0])
        self.assertNotIn("last_meal", st)                                                    # Ramesh's day off: no lunch
        st = state()
        play(self.w, st, self.at(SAT, 13, 10), action="read", place="home")
        self.assertNotIn("last_meal", st)                                                    # only eating counts

    def test_buying_food_marked_as_a_meal_or_a_snack(self):
        st = state()
        st["place"] = "khan"
        play(self.w, st, self.at(SAT, 12), action="buy", place="khan", buys=[{"item": "chai", "price_inr": 20}])
        self.assertNotIn("last_meal", st)
        self.assertNotIn("snacks", st)
        play(self.w, st, self.at(SAT, 12, 30), action="buy", place="khan", buys=[{"item": "a samosa", "price_inr": 30}])
        self.assertEqual((st.get("last_meal"), st["snacks"]), (None, 1))
        play(self.w, st, self.at(SAT, 13), action="eat", place="khan", buys=[{"item": "chole bhature", "price_inr": 180}])
        self.assertEqual((st["last_meal"], st["snacks"]), ("2026-10-03T13:00+05:30", 0))
        play(self.w, st, self.at(SAT, 14), action="buy", place="khan", buys=[{"item": "Lunch at a dhaba", "price_inr": 220}])
        self.assertEqual(st["last_meal"], "2026-10-03T14:00+05:30")
        data = json.loads((REPO / "world/data/places.json").read_text(encoding="utf-8"))["places"]
        food = {s["item"]: s["food"] for p in data.values() for s in p.get("sells", []) if s.get("food")}
        self.assertEqual({k for k, v in food.items() if v == "meal"}, {"Chole bhature at a dhaba", "Lunch at a dhaba: dal, rice, roti"})
        self.assertEqual({k for k, v in food.items() if v == "snack"}, {"Samosa", "Glucose biscuits", "Roasted corn on the cob"})

    def test_the_state_carries_wake_time_from_the_wake_up_step(self):
        box = Sandbox()
        try:
            day = box.run_day(SAT)
            first = next(s for s in day["steps"] if "decision" in s)
            self.assertEqual(day["state"]["today"]["woke"], first["t"])
            self.assertTrue(day["state"]["last_meal"].startswith("2026-10-03T"))
            self.assertGreater(day["state"]["today"]["walked"], 0)
            nxt = box.days.load(SAT + timedelta(days=1))
            self.assertNotIn("walked", nxt["state"]["today"])                                # per day
            self.assertEqual(nxt["state"]["last_meal"], day["state"]["last_meal"])           # but the last meal travels
        finally:
            box.close()


class Owlet(StubMind):
    """An owl that answers with the given theses."""

    def __init__(self, theses):
        self.theses = theses

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        if "diary" in (schema or {}).get("properties", {}):
            return json.dumps({"diary": "A night's diary of the day, long enough to be believed by the rules of the owl. " * 2,
                               "revision_log": "Something moved.", "theses": self.theses})
        return super().chat(messages, schema, max_tokens, temperature)


class ThesisTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.box.run_day(SAT)
        self.day = self.box.days.load(SAT)
        self.t = next(e["t"] for e in self.day["entries"] if e["k"] == "diary")

    def tearDown(self):
        self.box.close()

    def night(self, theses):
        e = Engine(self.box.cfg, World(), StubMind(), owl_mind=Owlet(theses))
        e.run_owl(self.box.days.load(SAT), at_dt(SAT + timedelta(days=1), 90))
        return self.box.days.load(SAT), self.box.days.load(SAT + timedelta(days=1))["state"]["theses"]

    def test_a_change_without_evidence_is_not_applied(self):
        for evidence in ([], ["03:33"], ["lunch"], "14:05", None):
            with self.subTest(evidence=evidence):
                with self.assertLogs("world", "WARNING") as log:
                    day, theses = self.night([{"id": "india", "status": "revised", "evidence": evidence}])
                self.assertIn("no evidence", log.output[0])
                self.assertEqual(day["owl"]["theses"], [])
                self.assertEqual({x["id"]: x["status"] for x in theses}, {"india": "unshaken", "state": "unshaken"})
                self.assertIn("diary", day["owl"])

    def test_a_change_with_evidence_is_applied_and_stored(self):
        day, theses = self.night([{"id": "india", "status": "revised", "evidence": ["03:33", self.t]},
                                  {"id": "state", "status": "unshaken", "evidence": [self.t]}])
        entry = next(e for e in self.day["entries"] if e["t"] == self.t and e["k"] == "diary")
        self.assertEqual(day["owl"]["theses"], [{"id": "india", "from": "unshaken", "to": "revised", "evidence": [{"t": self.t, "text": entry["text"]}]}])
        self.assertEqual({x["id"]: x["status"] for x in theses}, {"india": "revised", "state": "unshaken"})

    def test_revise_in_detail(self):
        day = {"entries": [{"t": "10:00", "k": "bag", "item": "Samosa", "price": 30}, {"t": "10:00", "k": "diary", "text": "word " * 100},
                           {"t": "11:00", "k": "wear", "item": "Kurta", "status": "Worn."}, {"t": "12:00", "k": "plan", "items": [item("13:00", "Lunch")]}]}
        theses = [{"id": "a", "text": "A", "status": "shaken"}, {"id": "b", "text": "B", "status": "unshaken"}]
        got = owl.revise(day, theses, [{"id": "a", "status": "abandoned", "evidence": ["10:00", "10:00", " 11:00 ", "9:99", "12:00"]},
                                       {"id": "b", "status": "unshaken", "evidence": ["10:00"]},          # no change
                                       {"id": "c", "status": "revised", "evidence": ["10:00"]},           # no such thesis
                                       {"id": "b", "status": "doubtful", "evidence": ["10:00"]},          # no such status
                                       "nonsense"])
        self.assertEqual([(c["id"], c["from"], c["to"]) for c in got], [("a", "shaken", "abandoned")])
        ev = got[0]["evidence"]
        self.assertEqual([v["t"] for v in ev], ["10:00", "11:00", "12:00"])
        self.assertTrue(ev[0]["text"].startswith("word word") and len(ev[0]["text"]) <= 160)             # the thought, cut short
        self.assertEqual(ev[1]["text"], "Kurta. Worn.")
        self.assertEqual(ev[2]["text"], "13:00 Lunch")
        self.assertEqual([t["status"] for t in theses], ["abandoned", "unshaken"])

    def test_the_stand_in_owl_answers_with_the_new_field_and_changes_nothing(self):
        self.box.engine().run_owl(self.box.days.load(SAT), at_dt(SAT + timedelta(days=1), 90))
        self.assertEqual(self.box.days.load(SAT)["owl"]["theses"], [])
        ask = "01:00 thought: x\n\nYour theses: india: India has no history (shaken); state: The state is the actuality of the ethical idea (unshaken).\n\n"
        out = json.loads(StubMind().chat([{"role": "user", "content": ask}], owl.schema(False)))
        self.assertEqual([(t["id"], t["status"]) for t in out["theses"]], [("india", "shaken"), ("state", "unshaken")])
        self.assertTrue(all(t["evidence"] == ["01:00"] for t in out["theses"]))
        self.assertIn("evidence", owl.schema(False)["properties"]["theses"]["items"]["required"])

    def test_the_prompt_asks_for_the_evidence(self):
        text = (REPO / "mind/owl.md").read_text(encoding="utf-8")
        self.assertIn("`evidence`", text)
        self.assertIn("does not change", text)


class WeekTest(unittest.TestCase):
    """Seven rehearsed days with the stand-in, the owl writing up each night."""

    @classmethod
    def setUpClass(cls):
        cls.box = Sandbox()
        cls.messages = []
        cls.calls = {}                      # the extra calls, by kind
        outer, calls = cls.messages, cls.calls

        class Watcher(StubMind):
            def decide(self, messages, sit):
                if not any("refuses" in x["content"] for x in messages):
                    outer.append(messages[1]["content"])
                return super().decide(messages, sit)

            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                props = (schema or {}).get("properties", {})
                kind = "plan" if "plan" in props else "voice" if "does" in props else "write" if "continues" in props else "owl" if "diary" in props else "other"
                calls[kind] = calls.get(kind, 0) + 1
                return super().chat(messages, schema, max_tokens, temperature)

        e = cls.box.engine(Watcher())
        cls.days = []
        for i in range(7):
            d = SAT + timedelta(days=i)
            cls.days.append(cls.box.run_day(d, e))
            e.run_owl(cls.box.days.load(d), at_dt(d + timedelta(days=1), 90))

    @classmethod
    def tearDownClass(cls):
        cls.box.close()

    def test_every_day_is_whole_with_a_plan_and_a_sensible_number_of_steps(self):
        refusals = 0
        for day in self.days:
            segs = day["segments"]
            self.assertEqual((segs[0]["from"], segs[-1]["to"]), ("00:00", "24:00"))
            self.assertTrue(all(a["to"] == b["from"] for a, b in zip(segs, segs[1:])))
            steps = [s for s in day["steps"] if "decision" in s]
            self.assertTrue(15 <= len(steps) <= 30, len(steps))
            refusals += sum(len(s["mind"].get("refused", [])) for s in steps)
            self.assertTrue(day["plan"]["items"], day["date"])
            self.assertEqual([e["k"] for e in day["entries"]].count("plan"), 1)
        self.assertLessEqual(refusals / 7, 2)

    def test_memory_body_and_hunger_appear_in_what_he_is_told(self):
        self.assertEqual(len(self.messages), sum(len([s for s in d["steps"] if "decision" in s and s["mind"]["source"] == "stub"]) for d in self.days))
        self.assertTrue(all("- Body: last meal" in m for m in self.messages))
        caretaker = [m for m in self.messages if "Ramesh, the caretaker" in m.split("Present:")[1].split("\n")[0]]
        self.assertTrue(caretaker)
        self.assertTrue(all("You remember:" in m for m in caretaker))
        events = " ".join(s["event"] for d in self.days for s in d["steps"] if "decision" in s)
        self.assertIn("You are hungry.", events)
        self.assertIn("laid out breakfast", events)
        self.assertTrue(all("Your plan for today:" in m for m in self.messages))                   # the wake-up decision too

    def test_the_prompts_stay_compact(self):
        sizes = [len(re.sub(r"\nFrom your shelf:\n(?:- .*\n)+", "", m)) for m in self.messages]           # the shelf has its own budget (test_shelf)
        self.assertLess(statistics.mean(sizes), 2500)
        self.assertLess(max(sizes), 3600)
        for m in self.messages:
            if "You remember:" in m:
                lines = m.split("You remember:\n")[1].split("\n\n")[0].split("\n")
                self.assertLessEqual(len(lines), 8)
                self.assertTrue(all(len(x) - 2 <= 220 for x in lines))

    def test_the_people_answer_and_he_writes_and_nothing_is_refused_for_its_words(self):
        said_days = 0
        for day in self.days:
            ents = day["entries"]
            talked = [e for e in ents if e["k"] == "said" and not e.get("by")]
            replies = [e for e in ents if e["k"] == "said" and e.get("by")]
            said_days += bool(talked)
            if talked:
                self.assertTrue(replies, day["date"])                                       # a voice reply on every day with conversation
            self.assertTrue(all(e["to"] == "Hegel" and e["by"] for e in replies))
            steps = [s for s in day["steps"] if "decision" in s]
            self.assertEqual(sum(1 for s in steps if s.get("voice")), len([s for s in steps if s["decision"].get("says") and s["present"]]))
            for s in steps:
                for errors in s["mind"].get("refused", []):
                    self.assertFalse(any("cannot publish" in x or "the word" in x for x in errors), errors)
            self.assertTrue(all(not e.get("sensitive") for e in ents))                      # the stand-in says nothing sensitive
        self.assertGreaterEqual(said_days, 4)
        sittings = [e for d in self.days for e in d["entries"] if e["k"] == "writing"]
        self.assertTrue(sittings)                                                           # at least one sitting in the week
        works = self.days[-1]["state"]["works"]
        self.assertEqual(sum(w["sittings"] for w in works), len(sittings))
        self.assertEqual(sum(w["words"] for w in works), sum(e["words"] for e in sittings))
        self.assertEqual(self.calls["write"], len(sittings))                                # one extra chat call a sitting, no more
        self.assertTrue(all(e["mode"] == "chat" and "about" not in e for e in sittings))       # default: one chat call retains the situation
        self.assertTrue(all(e["text"].startswith("(rehearsal) ") for e in sittings))
        self.assertTrue(all(0 < len(w["tail"]) <= 800 for w in works))
        self.assertEqual(self.calls["plan"], 7)
        voice_calls = self.calls["voice"]
        steps = sum(len([s for s in d["steps"] if "decision" in s]) for d in self.days)
        replies = sum(1 for d in self.days for s in d["steps"] if s.get("voice"))
        self.assertTrue(replies <= voice_calls <= 2 * steps)

    def test_the_stand_in_never_repeats_itself_over_the_week(self):
        thoughts = [s["decision"]["thought"] for d in self.days for s in d["steps"] if "decision" in s]
        for i, a in enumerate(thoughts):
            self.assertFalse(any(repeats(a, b) for b in thoughts[max(0, i - 12):i]), a)


if __name__ == "__main__":
    unittest.main()
