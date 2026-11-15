"""His correspondent, Niethammer (HEGEL_CORRESPONDENT, world/post.py, world/data/correspondent.json)."""
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox  # noqa: E402

from world import post  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World  # noqa: E402

C = post.card()
D = date(2026, 11, 16)
LETTER = "Dear friend, " + "the city is loud and the library is quiet, and I think of you there. " * 6 + "Your Niethammer"


class Pieces(unittest.TestCase):
    def test_the_switch_is_off_until_set(self):
        self.assertFalse(Config({}).correspondent)
        self.assertTrue(Config({"HEGEL_CORRESPONDENT": "1"}).correspondent)

    def test_a_letter_to_him_and_nothing_else_goes_to_the_post_the_next_morning(self):
        st = {}
        self.assertFalse(post.written(st, {"kind": "letter", "to": "Niethammer", "text": "x"}, D, C))     # no post without the switch
        post.start(st, D)
        self.assertFalse(post.written(st, {"kind": "essay", "to": None, "text": "x"}, D, C))
        self.assertFalse(post.written(st, {"kind": "letter", "to": "Karl", "text": "x"}, D, C))
        self.assertTrue(post.written(st, {"kind": "letter", "to": "my friend Niethammer in Munich", "title": "To N.", "text": "Dear N."}, D, C))
        self.assertIsNone(post.to_post(st, D, C))                                       # not the same day
        sent = post.to_post(st, D + timedelta(days=1), C)
        self.assertEqual((sent["text"], sent["due"]), ("Dear N.", (D + timedelta(days=11)).isoformat()))
        self.assertEqual(st["post"]["outbox"], [])

    def test_what_is_due_first_reply_nudge(self):
        st = {}
        post.start(st, D)
        self.assertEqual(post.due(st, D, C), ("first", []))
        post.arrived(st, "first", [], LETTER, D, C)
        self.assertIsNone(post.due(st, D + timedelta(days=5), C))
        self.assertEqual(post.due(st, D + timedelta(days=21), C), ("nudge", []))
        post.arrived(st, "nudge", [], LETTER, D + timedelta(days=21), C)
        self.assertIsNone(post.due(st, D + timedelta(days=50), C))                          # one nudge, not a stream
        post.written(st, {"kind": "letter", "to": "Niethammer", "text": "Dear N."}, D + timedelta(days=22), C)
        sent = post.to_post(st, D + timedelta(days=23), C)
        self.assertIsNone(post.due(st, D + timedelta(days=32), C))
        self.assertEqual(post.due(st, D + timedelta(days=33), C), ("reply", [sent]))

    def test_the_call_carries_his_card_the_correspondence_and_the_letter_he_answers(self):
        st = {}
        post.start(st, D)
        post.arrived(st, "first", [], LETTER, D, C)
        post.written(st, {"kind": "letter", "to": "Niethammer", "text": "Yes, it is I. Bamberg, the newspaper."}, D, C)
        sent = post.to_post(st, D + timedelta(days=1), C)
        msgs = post.messages(st, "reply", [sent], D + timedelta(days=11), C)
        self.assertIn("Friedrich Immanuel Niethammer", msgs[0]["content"])
        self.assertIn("never invent his circumstances", msgs[0]["content"])
        self.assertIn("You wrote, 2026-11-16", msgs[1]["content"])
        self.assertIn("Hegel's letter you are answering:", msgs[1]["content"])
        self.assertIn("Bamberg, the newspaper", msgs[1]["content"])
        self.assertIn('{"letter": "..."}', msgs[1]["content"])
        first = post.messages({"post": {"letters": []}}, "first", [], D, C)
        self.assertIn("Tughlak Road", first[1]["content"])

    def test_a_letter_is_shown_once_and_then_waits_for_an_answer(self):
        st = {}
        post.start(st, D)
        post.arrived(st, "first", [], LETTER, D, C)
        line, entry = post.event(st, ["ramesh"], C)
        self.assertTrue(line.startswith("Ramesh brings the post: a letter from Munich, addressed in a hand you know."))
        self.assertEqual((entry["k"], entry["by"], entry["text"]), ("letter", "Niethammer", LETTER))
        self.assertIsNone(post.event(st, ["ramesh"], C))
        self.assertEqual(post.on_mind(st, C), ["Niethammer's letter from Munich of 2026-11-16 awaits your answer."])
        self.assertIn("Niethammer's last letter to you", post.last_letter(st, C))
        post.written(st, {"kind": "letter", "to": "Niethammer", "text": "Dear N."}, D, C)
        self.assertEqual(post.on_mind(st, C), ["Your letter to Niethammer goes to the post tomorrow morning."])

    def test_an_unusable_letter_is_refused(self):
        self.assertIsNone(post.clean("not json"))
        self.assertIsNone(post.clean(json.dumps({"letter": "Too short."})))
        self.assertEqual(post.clean(json.dumps({"letter": LETTER})), LETTER)


class Days(unittest.TestCase):
    def test_without_the_switch_nothing_of_the_post_appears(self):
        box = Sandbox()
        self.addCleanup(box.close)
        day = box.run_day(date(2026, 10, 3))
        self.assertNotIn("post", day["state"])
        self.assertFalse(any(e.get("k") == "letter" for e in day["entries"]))

    def test_his_first_letter_his_answer_and_the_reply(self):
        box = Sandbox()
        self.addCleanup(box.close)
        box.cfg.correspondent = True

        class Writer(StubMind):
            def decide(self, messages, sit):
                if sit["place"] == "home" and "awaits your answer" in " ".join(sit["on_mind"]) and "16:00" <= sit["time"] < "19:00":
                    return json.dumps({"thought": "I owe Niethammer an answer, and I shall write it now, at the table.",
                                       "action": "write", "place": "home", "minutes": 45, "says": None, "buys": [], "revision": None})
                return super().decide(messages, sit)

            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                props = (schema or {}).get("properties", {})
                if "continues" in props:
                    out = {"title": "To Niethammer", "kind": "letter", "to": "Niethammer", "continues": False}
                    out.update({"about": "(rehearsal) an answer"} if "about" in props else {"text": "(rehearsal) Dear Niethammer, it is I."})
                    return json.dumps(out)
                return super().chat(messages, schema, max_tokens, temperature)

        quick = dict(C, days_each_way=1)
        with mock.patch.object(post, "card", return_value=quick):
            engine = Engine(box.cfg, World(), Writer())
            engine.lookup = box.engine().lookup
            days = [box.run_day(date(2026, 10, 3) + timedelta(days=i), engine) for i in range(4)]
        letters = [(d["date"], e) for d in days for e in d["entries"] if e.get("k") == "letter"]
        self.assertGreaterEqual(len(letters), 2)
        self.assertEqual(letters[0][0], "2026-10-03")                   # the first letter comes on the first day
        self.assertTrue(any(e.get("k") == "writing" and e.get("to") == "Niethammer" for d in days for e in d["entries"]))
        self.assertGreater(letters[1][0], letters[0][0])                 # his answer went, and Niethammer's reply came
        first_event = next(s["event"] for s in days[0]["steps"] if "addressed in a hand you know" in s.get("event", ""))
        self.assertIn("Friedrich Immanuel Niethammer", first_event)


if __name__ == "__main__":
    unittest.main()
