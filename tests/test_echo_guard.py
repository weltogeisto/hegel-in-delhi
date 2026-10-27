"""T36: two switches against his repetition, both off until they pass the ratchet.

Arm B, the echo guard (HEGEL_ECHO_GUARD=1): the phrases he has used more than once today, by T9's rule, shown back to him.
Arm C, the DRY sampler (HEGEL_DECISION_DRY=<multiplier>): llama.cpp penalises continuing a run of words already in the context.
"""
import json
import sys
import threading
import unittest
from datetime import date
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import FakeLlama, Sandbox  # noqa: E402

from world import report  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import ECHO_LINE  # noqa: E402
from world.mind import DRY_ALLOWED, DRY_BASE, HTTPMind, StubMind  # noqa: E402

SAT = date(2026, 10, 3)


class EchoesTest(unittest.TestCase):
    def test_the_phrases_used_by_more_than_one_thought_most_used_first(self):
        thoughts = ["The friction of the state is plain today.",
                    "Again the friction of the state presses on me.",
                    "I walk; the friction of the state follows, and the system of needs.",
                    "The system of needs is a market, nothing more."]
        got = report.echoes(thoughts)
        self.assertEqual(got[:2], ["friction of the state", "the friction of the"])      # three thoughts each, then alphabetical
        self.assertIn("the system of needs", got)
        self.assertNotIn("is a market nothing", got)                                       # said once only

    def test_stopwords_alone_and_numerals_are_no_phrase_and_five_at_most(self):
        thoughts = ["It is in the way of it.", "It is in the way of it.", "At 10 30 I left the house quickly.", "At 10 30 I left the house quickly."]
        got = report.echoes(thoughts)
        self.assertNotIn("it is in the", got)
        self.assertFalse([p for p in got if any(c.isdigit() for c in p)])
        letters = "abcdefghi"
        many = [" ".join(f"word{c} other{c} more{c} last{c}" for c in letters)] * 2              # 33 phrases, each said twice
        self.assertEqual(len(report.echoes(many)), 5)
        self.assertEqual(report.echoes([None, ""]), [])


class Seen(StubMind):
    """The stand-in, keeping every decision prompt."""

    def __init__(self):
        super().__init__()
        self.prompts = []

    def decide(self, messages, sit):
        self.prompts.append(messages[1]["content"])
        return super().decide(messages, sit)


class EchoGuardTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def run_day(self, on):
        self.box.cfg.echo_guard = on
        mind = Seen()
        day = self.box.run_day(SAT, self.box.engine(mind))
        return day, mind.prompts

    def test_off_by_default_and_his_prompts_are_as_they_were(self):
        self.assertFalse(Config({"HEGEL_PUSH": "0"}).echo_guard)
        _, prompts = self.run_day(False)
        self.assertFalse([p for p in prompts if "Already said today" in p])

    def test_on_he_is_shown_what_he_has_said_too_often_today(self):
        day, prompts = self.run_day(True)
        shown = [p for p in prompts if "Already said today, more than once: “" in p]
        self.assertTrue(shown)                                                             # the stand-in's templates repeat
        self.assertNotIn("Already said today", prompts[0])                                 # nothing said yet at waking
        thoughts = [s["decision"]["thought"] for s in day["steps"] if "decision" in s and s["decision"].get("thought")]
        for phrase in report.echoes(thoughts[:3]):
            self.assertTrue(any(f"“{phrase}”" in p for p in prompts[3:]), phrase)
        self.assertTrue(ECHO_LINE.endswith("Find other words, or another thought."))


class DrySamplerTest(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), FakeLlama)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        FakeLlama.calls = []
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.messages = [{"role": "system", "content": "x"}, {"role": "user", "content": "You are at: home\nDecide your next step."}]

    def test_the_decision_call_carries_the_sampler_only_when_set(self):
        HTTPMind(self.url).decide(self.messages, {})
        self.assertFalse([k for k in FakeLlama.calls[-1] if k.startswith("dry_")])
        HTTPMind(self.url, decision_dry=0.8).decide(self.messages, {})
        body = FakeLlama.calls[-1]
        self.assertEqual((body["dry_multiplier"], body["dry_base"], body["dry_allowed_length"], body["dry_penalty_last_n"]), (0.8, DRY_BASE, DRY_ALLOWED, -1))
        self.assertEqual(body["response_format"]["type"], "json_schema")                    # the contract is unchanged

    def test_his_writings_and_the_voices_of_others_are_not_touched(self):
        mind = HTTPMind(self.url, decision_dry=0.8)
        mind.chat(self.messages)
        self.assertFalse([k for k in FakeLlama.calls[-1] if k.startswith("dry_")])

    def test_the_setting_is_read_and_checked(self):
        cfg = Config({"HEGEL_PUSH": "0", "HEGEL_ECHO_GUARD": "1", "HEGEL_DECISION_DRY": "0.8"})
        self.assertEqual((cfg.echo_guard, cfg.decision_dry), (True, 0.8))
        self.assertEqual(Config({"HEGEL_PUSH": "0"}).decision_dry, 0.0)
        with self.assertRaises(ValueError):
            Config({"HEGEL_PUSH": "0", "HEGEL_DECISION_DRY": "3"})
        with self.assertRaises(ValueError):
            HTTPMind(self.url, decision_dry=-1)


if __name__ == "__main__":
    unittest.main()
