"""T49: a preference among his own answers (world/prefer.py, HEGEL_DECISION_DRAWS)."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import decision_pairs
from world import contract, prefer
from world.engine import Engine
from world.mind import MindAway
from world.world import World, at_dt

R = Path(__file__).resolve().parents[1]
EARLIER = "The friction of the particular against the universal is plain in this market."
ECHO = "Again the friction of the particular against the universal, and the tea goes cold on the counter."
FRESH = "Sunil counts his change twice before he hands it over, and I like him the better for it."
OTHER = "The tailor has left a pin in the collar, and I will tell him so tomorrow."


def answer(thought, **kw):
    a = dict(thought=thought, action="stay", place="khan", minutes=15, says=None, buys=[], revision=None)
    a.update(kw)
    return json.dumps(a)


class ChooseTest(unittest.TestCase):
    def run_choose(self, replies, draws=4):
        replies = list(replies)
        calls = []

        def draw():
            calls.append(1)
            item = replies.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        def check(raw):
            a = json.loads(raw)
            return (["refused by the world"], None) if a.get("refuse") else ([], a["thought"])
        raw, note = prefer.choose(draw, check, [EARLIER], draws, away=MindAway)
        return json.loads(raw)["thought"], note, len(calls)

    def test_the_first_fresh_accepted_reply_wins_and_drawing_stops(self):
        thought, note, calls = self.run_choose([answer(ECHO), answer(FRESH), answer(OTHER)])
        self.assertEqual((thought, calls), (FRESH, 2))
        self.assertEqual(note, {"n": 2, "refused": 0, "echo": 1, "picked": 1})

    def test_a_fresh_first_reply_costs_one_call(self):
        thought, note, calls = self.run_choose([answer(FRESH), answer(OTHER)])
        self.assertEqual((thought, calls, note["picked"]), (FRESH, 1, 0))

    def test_when_every_reply_echoes_the_first_accepted_one_stands(self):
        thought, note, calls = self.run_choose([answer(FRESH, refuse=True), answer(ECHO), answer(ECHO + " Again."), answer(ECHO)])
        self.assertEqual((thought, calls), (ECHO, 4))
        self.assertEqual(note, {"n": 4, "refused": 1, "echo": 3, "picked": 1})

    def test_when_every_reply_is_refused_the_first_goes_to_the_refusal_loop(self):
        thought, note, calls = self.run_choose([answer(FRESH, refuse=True), answer(OTHER, refuse=True)], draws=2)
        self.assertEqual((thought, note), (FRESH, {"n": 2, "refused": 2, "echo": 0, "picked": 0}))

    def test_a_mind_that_goes_away_mid_drawing_keeps_what_it_said(self):
        thought, note, _ = self.run_choose([answer(ECHO), MindAway("gone")])
        self.assertEqual((thought, note["picked"], note["cut_short"]), (ECHO, 0, True))
        with self.assertRaises(MindAway):
            self.run_choose([MindAway("never came")])

    def test_shown_thoughts_match_the_labellers_reading_of_the_prompt(self):
        lines = [f"09:00 recorded step: stay (home); you thought: “{EARLIER}”",
                 f"09:30 recorded step: walk (lodhi); executed activity: Walking.; you thought: “{FRESH}” Engine note: price set."]
        sit = dict(day="Saturday, 7 November 2026", time="10:00", place="Home", weather="clear", aqi=180, outfit="kurta",
                   imprest_left=1200, present=[], open_now=["Home"], event="Nothing in particular happens.", earlier=lines)
        messages = [{"role": "system", "content": "soul"}, {"role": "user", "content": contract.render(sit)}]
        self.assertEqual(prefer.shown_thoughts(lines), [EARLIER, FRESH])
        self.assertEqual(prefer.shown_thoughts(lines), [first for *_, first in decision_pairs.shown(messages)])
        self.assertFalse(prefer.fresh(ECHO, [EARLIER]))
        self.assertTrue(prefer.fresh(FRESH, [EARLIER]))
        self.assertTrue(prefer.fresh(ECHO, []))


class EngineDrawsTest(unittest.TestCase):
    """The real Engine.step with a scripted mind; only the people and the memory are held still."""

    def setUp(self):
        self.w = World()
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-prefer-test-")
        self.addCleanup(self.tmp.cleanup)

    def step(self, replies, draws):
        day = json.loads((R / "docs/days/2026-10-02.json").read_text())
        day.update(date="2026-10-03", n=2, entries=[], segments=[], complete=False)
        day["steps"] = [{"t": "18:30", "end": "19:00", "event": "Nothing in particular happens.", "present": [],
                         "decision": {"thought": EARLIER, "action": "stay", "place": "khan", "minutes": 30, "says": None, "buys": []},
                         "arrived": None, "mind": {"source": "mind", "attempts": 1}}]
        st = day["state"]
        st.update(place="khan", asleep=False, today={}, people=list(self.w.cast), beats=[b["id"] for b in self.w.beats])
        self.w.ledger(st)
        t = at_dt(date(2026, 10, 3), 19 * 60)
        st["until"] = t.isoformat(timespec="minutes")
        cfg = SimpleNamespace(repo=R, docs=Path(self.tmp.name) / "docs", soul_file=R / "mind/soul.md", shelf=False, decision_draws=draws)
        mind = mock.Mock()
        mind.source, mind.ready = "stub", True
        mind.decide.side_effect = list(replies)
        e = Engine(cfg, self.w, mind)
        e.greet = mock.Mock(return_value=True)
        e.memory.recall = mock.Mock(return_value=[])
        e.memory.recent_thoughts = mock.Mock(return_value=[])
        e.memory.known_text = mock.Mock(return_value="Masterji, Sunil and the bookseller have met him.")
        with mock.patch.object(self.w, "present_ids", return_value=[]):
            step = e.step(day, t)
        return step, mind, day

    def test_off_is_one_call_and_leaves_no_note(self):
        step, mind, _ = self.step([answer(ECHO)], draws=1)
        self.assertEqual((step["decision"]["thought"], step["mind"]["attempts"], mind.decide.call_count), (ECHO, 1, 1))
        self.assertNotIn("draws", step["mind"])

    def test_the_prompt_shows_the_earlier_thought(self):
        _, mind, _ = self.step([answer(FRESH)], draws=4)
        self.assertIn("you thought: “" + EARLIER + "”", mind.decide.call_args.args[0][-1]["content"])

    def test_an_echo_is_passed_over_for_the_next_fresh_reply(self):
        step, mind, _ = self.step([answer(ECHO), answer(FRESH), answer(OTHER)], draws=4)
        self.assertEqual(step["decision"]["thought"], FRESH)
        self.assertEqual(step["mind"]["draws"], {"n": 2, "refused": 0, "echo": 1, "picked": 1})
        self.assertEqual((step["mind"]["attempts"], mind.decide.call_count), (2, 2))
        self.assertNotIn("refused", step["mind"])
        prompts = [c.args[0] for c in mind.decide.call_args_list]
        self.assertTrue(all(len(p) == 2 for p in prompts))                 # the same question each time, no refusal history
        self.assertEqual(prompts[0], prompts[1])

    def test_a_refused_reply_is_passed_over_without_the_refusal_loop(self):
        step, mind, _ = self.step([answer(FRESH, place="nowhere"), answer(OTHER)], draws=4)
        self.assertEqual(step["decision"]["thought"], OTHER)
        self.assertEqual(step["mind"]["draws"], {"n": 2, "refused": 1, "echo": 0, "picked": 1})
        self.assertNotIn("refused", step["mind"])

    def test_all_echoes_keep_the_first(self):
        step, mind, _ = self.step([answer(ECHO), answer(ECHO + " Still."), answer(ECHO + " Yet again.")], draws=3)
        self.assertEqual(step["decision"]["thought"], ECHO)
        self.assertEqual(step["mind"]["draws"], {"n": 3, "refused": 0, "echo": 3, "picked": 0})

    def test_all_refused_hands_the_first_reply_to_the_refusal_loop(self):
        bad = answer(FRESH, place="nowhere")
        step, mind, _ = self.step([bad, answer(OTHER, place="nowhere"), answer(OTHER)], draws=2)
        self.assertEqual(step["decision"]["thought"], OTHER)
        self.assertEqual((step["mind"]["attempts"], len(step["mind"]["refused"])), (3, 1))
        last = mind.decide.call_args_list[-1].args[0]
        self.assertEqual((len(last), last[2]["content"]), (4, bad))         # the world's refusal of the first reply was shown

    def test_passed_over_replies_leave_no_trace_in_his_state(self):
        with_draws, _, day_a = self.step([answer(ECHO, buys=[{"item": "Chai, a cup", "price_inr": 20}]), answer(FRESH)], draws=4)
        alone, _, day_b = self.step([answer(FRESH)], draws=1)
        for key in ("decision", "end", "t"):
            self.assertEqual(with_draws[key], alone[key])
        self.assertEqual(day_a["state"], day_b["state"])                   # the echo's purchase was never made
        self.assertEqual(day_a["entries"], day_b["entries"])


if __name__ == "__main__":
    unittest.main()
