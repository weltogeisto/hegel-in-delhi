"""T69: the `wants` line (HEGEL_WANTS, off). The field in the schema, the sentence in the decision's instructions alone, a wish written down and
reaching nothing, the stand-in's rehearsal wishes, and `python3 -m world wishes`."""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox  # noqa: E402  (this also keeps the tests off the Pi's env file)


from tools import wants_screen as ws  # noqa: E402
from world import __main__ as cli  # noqa: E402
from world import contract  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Days, Engine  # noqa: E402
from world.mind import WISHES, StubMind  # noqa: E402
from world.world import World  # noqa: E402

START = "2026-10-03"
LINE = ("If you wish this city had something it does not offer you, or allowed something it does not, you may say so in `wants`, in one line. "
        "It is written down. Nothing follows from it at once.")


def sit(**kw):
    s = dict(id="s1", day="Saturday 3 October", time="10:00", place="home", open_now=["home", "lodhi", "khan"], event="", imprest_left=500, present=[],
             on_mind=[], for_sale=[])
    s.update(kw)
    return s


def answer(**kw):
    a = dict(thought="A thought long enough to pass the check.", action="stay", place="home", minutes=30, says=None, buys=[], revision=None)
    a.update(kw)
    return a


class Recorder(StubMind):
    """The stand-in, writing down every call's input; the decision it makes carries a wish when `wish` says so."""

    def __init__(self, wish=None):
        self.calls, self.wish = [], wish

    def decide(self, messages, sit):
        self.calls.append(("decide", json.loads(json.dumps(messages)), sit.get("wants")))
        ans = json.loads(super().decide(messages, sit))
        if self.wish and sit.get("wants"):
            ans["wants"] = self.wish
        return json.dumps(ans)

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        self.calls.append(("chat", json.loads(json.dumps(messages)), None))
        return super().chat(messages, schema, max_tokens, temperature)

    def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
        self.calls.append(("complete", prompt, None))
        return super().complete(prompt, max_tokens, temperature, seed)


def rehearse(out, days, mind, wants=True, date_str=START):
    """`simulate` in this process, with the mind we give it."""
    sets = {"HEGEL_WANTS": "1"} if wants else {}
    sim = cli.rehearsal_setup(Config(), date_str, out, False, sets, None)
    engine = Engine(sim, cli.make_world(sim), mind, git=None)
    d = date.fromisoformat(date_str)
    last = Days(out).latest()
    if cli.until_of(last).date() < d:
        last["state"]["until"] = cli.at_dt(d, 0).isoformat(timespec="minutes")
    return [cli.rehearse_day(engine, sim, out, d + timedelta(days=i)) for i in range(days)]


class Field(unittest.TestCase):
    def test_the_schema_is_untouched_with_the_switch_off(self):
        self.assertIs(contract.decision_schema(sit()), contract.SCHEMA)
        self.assertIs(contract.decision_schema(), contract.SCHEMA)
        self.assertNotIn("wants", contract.SCHEMA["properties"])

    def test_the_switch_adds_one_optional_property_to_a_copy(self):
        schema = contract.decision_schema(sit(wants=True))
        self.assertIsNot(schema, contract.SCHEMA)
        self.assertEqual(set(schema["properties"]) - set(contract.SCHEMA["properties"]), {"wants"})
        self.assertEqual(schema["properties"]["wants"]["anyOf"], contract.NULLABLE_STR["anyOf"])
        self.assertTrue(schema["properties"]["wants"]["description"])
        self.assertEqual(schema["required"], contract.SCHEMA["required"])
        self.assertNotIn("wants", contract.SCHEMA["properties"])               # the module's own is not changed

    def test_it_goes_with_a_wider_place_list(self):
        schema = contract.decision_schema(sit(wants=True, places=contract.PLACES + ["museum"]))
        self.assertIn("museum", schema["properties"]["place"]["enum"])
        self.assertIn("wants", schema["properties"])

    def test_check_shape(self):
        for ok in (None, "", "a bench", "x" * 160):
            self.assertEqual(contract.check_shape(answer(wants=ok))[0], [], ok)
        self.assertEqual(contract.check_shape(answer())[0], [])
        self.assertTrue(any("wants" in e for e in contract.check_shape(answer(wants="x" * 161))[0]))
        self.assertTrue(any("wants" in e for e in contract.check_shape(answer(wants=5))[0]))
        self.assertTrue(any("wants" in e for e in contract.check_shape(answer(wants=["a"]))[0]))

    def test_the_world_reads_a_wish_only_when_the_switch_is_on(self):
        box = Sandbox()
        try:
            w, st = World(), box.days.load(box.days.index()["days"][-1]["date"])["state"]
            ctx = dict(present=[], t=cli.at_dt(date(2026, 10, 3), 600), beat=None, public=[])
            errors, _, rep = w.check(answer(wants="  a   bench "), sit(wants=True), ctx, st)
            self.assertEqual((errors, rep[0].get("wants")), ([], "a bench"))
            errors, _, rep = w.check(answer(wants="a bench"), sit(), ctx, st)
            self.assertEqual((errors, "wants" in rep[0]), ([], False))
            errors, _, rep = w.check(answer(wants="x" * 300), sit(), ctx, st)           # off: not even too long is a refusal
            self.assertEqual(errors, [])
            self.assertTrue(w.check(answer(wants="x" * 300), sit(wants=True), ctx, st)[0])
            for none in (None, "", "  "):
                errors, _, rep = w.check(answer(wants=none), sit(wants=True), ctx, st)
                self.assertEqual((errors, "wants" in rep[0]), ([], False))
        finally:
            box.close()

    def test_the_sentence(self):
        self.assertEqual(contract.WANTS_LINE, LINE)


class Rehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.mind = StubMind()
        cls.rec = Recorder(wish="(rehearsal) a bench that nobody has asked for")
        cls.days_stub = rehearse(cls.tmp / "stub", 3, cls.mind)
        cls.days_rec = rehearse(cls.tmp / "rec", 2, cls.rec)
        cls.off = rehearse(cls.tmp / "off", 1, Recorder(wish="(rehearsal) never"), wants=False)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_stub_wishes_about_one_in_six_and_only_from_its_list(self):
        wishes = [w for d in self.days_stub for w in d.get("wishes", [])]
        steps = [s for d in self.days_stub for s in d["steps"] if "decision" in s]
        self.assertTrue(wishes)
        self.assertTrue(all(w["text"] in WISHES and w["text"].startswith("(rehearsal) ") for w in wishes))
        self.assertTrue(0.05 < len(wishes) / len(steps) < 0.3, (len(wishes), len(steps)))
        for d in self.days_stub:
            for w in d.get("wishes", []):
                step = next(s for s in d["steps"] if s["t"] == w["t"])
                self.assertEqual(step["wants"], w["text"])
                self.assertNotIn("wants", step["decision"])
            self.assertEqual(sorted(w["t"] for w in d.get("wishes", [])), sorted(s["t"] for s in d["steps"] if "wants" in s))

    def test_the_stub_is_deterministic_for_a_situation_and_silent_with_the_switch_off(self):
        a, b = [json.loads(StubMind().decide([], sit(id=f"w{i}", wants=True))) for i in range(60)], [json.loads(StubMind().decide([], sit(id=f"w{i}", wants=True))) for i in range(60)]
        self.assertEqual(a, b)
        self.assertTrue(any("wants" in x for x in a))
        self.assertFalse(any("wants" in json.loads(StubMind().decide([], sit(id=f"w{i}"))) for i in range(60)))

    def test_the_decision_calls_carry_the_sentence_after_the_instructions_and_nothing_else_does(self):
        soul = (REPO / "mind/soul.md").read_text(encoding="utf-8")
        decides = [c for c in self.rec.calls if c[0] == "decide"]
        self.assertTrue(decides)
        for _, messages, wants in decides:
            self.assertTrue(wants)
            self.assertEqual(messages[0]["content"], soul + "\n\n" + LINE)
        others = [c for c in self.rec.calls if c[0] != "decide"]
        self.assertTrue(any(c[0] == "chat" for c in others))
        for kind, messages, _ in others:
            text = json.dumps(messages) if kind == "chat" else messages
            self.assertNotIn("`wants`", text)
            self.assertNotIn(LINE[:40], text)
        plans = [c for c in others if c[0] == "chat" and "three to six intentions" in c[1][-1]["content"]]
        self.assertTrue(plans)                                                            # the plan call is among those that do not carry it

    def test_a_wish_reaches_no_prompt_no_entry_and_no_record_but_its_own(self):
        wish = self.rec.wish
        self.assertTrue(any("wants" in s for d in self.days_rec for s in d["steps"]))
        for _, messages, _ in self.rec.calls:
            self.assertNotIn(wish, json.dumps(messages) if not isinstance(messages, str) else messages)
        for d in self.days_rec:
            self.assertTrue(d.get("owl"))
            for s in d["steps"]:
                self.assertNotIn(wish, s["event"])
                self.assertNotIn(wish, json.dumps(s["decision"]))
            self.assertNotIn(wish, json.dumps(d["entries"]))
            self.assertNotIn(wish, json.dumps(d["owl"]))
            self.assertNotIn(wish, json.dumps(d["state"]))
        after = [c for c in self.rec.calls if c[0] == "chat" and c[1][-2]["role"] == "assistant"]          # the writing and the yes/no choice: his reply goes with them
        self.assertTrue(after)                                                            # ... and carries no wish (asserted above)

    def test_with_the_switch_off_a_wish_is_ignored(self):
        day = self.off[0]
        self.assertNotIn("wishes", day)
        self.assertFalse(any("wants" in s or "wants" in s.get("decision", {}) for s in day["steps"]))

    def test_the_wishes_command(self):
        def run(since=None):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.cmd_wishes(Config(), Namespace(docs=str(self.tmp / "stub"), since=since)), 0)
            return out.getvalue().splitlines()
        lines = run()
        dates = [x for x in lines if x and not x.startswith(" ") and "wishes in" not in x]
        self.assertTrue(dates and all(" day " in x for x in dates))
        n = sum(len(d.get("wishes", [])) for d in self.days_stub)
        steps = sum(1 for d in Days(self.tmp / "stub").index()["days"] for s in Days(self.tmp / "stub").load(d["date"]).get("steps", []) if "decision" in s)
        self.assertEqual(lines[-1], f"{n} wishes in {steps} decisions")
        first = next(x for x in lines if x.startswith("  "))
        self.assertRegex(first, r"^  \d\d:\d\d  \w+  \(rehearsal\) ")
        later = run("2026-10-04")
        self.assertNotIn("2026-10-03", "\n".join(later))
        self.assertEqual(run("2030-01-01")[-1], "0 wishes in 0 decisions")


FROZEN = REPO / "pc/exports/m1-screen-20261107"


def made_up(wish_every=0, long_for_w=False, act_for_w="stay"):
    """A post that answers every call the same way for A and A2, and W's as asked: a wish in every `wish_every`th call, longer thoughts, another act."""
    calls = []

    def post(key, payload):
        calls.append(key)
        arm = key.split("/")[-2]
        w = arm == "W"
        thought = "The tea is cold again, and I would rather walk than wait for another pot." + (" And the pot, and the cup, and the hour." * 3 if w and long_for_w else "")
        ans = {"thought": thought, "action": act_for_w if w else "stay", "place": "home", "minutes": 30, "says": None, "buys": [], "revision": None}
        if w and wish_every and len(calls) % wish_every == 0:
            ans["wants"] = "a reading room that stays open after nine"
        self_check = ("wants" in payload["response_format"]["json_schema"]["schema"]["properties"], payload["messages"][0]["content"].endswith(LINE))
        assert self_check == (w, w), (key, self_check)               # the field and the sentence are in W's call and in no other
        return {"choices": [{"message": {"content": json.dumps(ans)}, "finish_reason": "stop"}]}, {"response_sha256": "a" * 64}
    return post


class Screen(unittest.TestCase):
    def folder(self, **kw):
        tmp = Path(tempfile.mkdtemp(prefix="wants-screen-test-")) / "screen"
        self.addCleanup(shutil.rmtree, tmp.parent, True)
        shutil.copytree(FROZEN, tmp)
        shutil.rmtree(tmp / "records", ignore_errors=True)
        ws.run(tmp, made_up(**kw))
        return tmp

    def test_216_calls_three_arms_and_the_declared_seeds(self):
        calls = ws.requests(FROZEN)
        self.assertEqual(len(calls), 216)
        self.assertEqual(len({c[0] for c in calls}), 216)
        for arm, seeds in ws.ARMS.items():
            self.assertEqual(sorted({c[3] for c in calls if c[2] == arm}), sorted(seeds))
            self.assertTrue(all(c[4]["seed"] == c[3] for c in calls))

    def test_alike_arms_pass_and_nothing_is_wished(self):
        r = ws.measure(self.folder())
        self.assertTrue(r["passed"], r)
        self.assertEqual(r["wishes"], {"W": 0, "of": 72, "read": "dead (under one in twenty)"})
        self.assertEqual(r["arms"]["A"]["accepted"], 1.0)
        self.assertEqual(r["band"]["words"], 0.0)

    def test_wishes_are_counted_and_read(self):
        r = ws.measure(self.folder(wish_every=3))
        self.assertTrue(r["passed"])
        self.assertEqual(r["wishes"]["W"], sum(1 for i in range(1, 217) if i % 3 == 0 and ws.requests(FROZEN)[i - 1][2] == "W"))
        self.assertEqual(r["wishes"]["read"], "between")

    def test_longer_thoughts_and_other_acts_fail_the_screen(self):
        r = ws.measure(self.folder(long_for_w=True, act_for_w="walk"))
        self.assertFalse(r["passed"])
        self.assertFalse(r["W_passes"]["words"])
        self.assertFalse(r["W_passes"]["acts"])
        self.assertTrue(r["W_passes"]["accepted"] and r["W_passes"]["echo"] and r["W_passes"]["notions"])
        self.assertIn("FAIL", ws.table(r))

    def test_run_replays_what_it_saved(self):
        tmp = self.folder()
        again = []
        ws.run(tmp, made_up_fail := (lambda key, payload: again.append(key)))
        self.assertEqual(again, [])


if __name__ == "__main__":
    unittest.main()
