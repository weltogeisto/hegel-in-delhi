"""tools/run_requests.py: a frozen requests file to the plain live server, one durable receipt per call, resumable."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import run_requests
from tools.recorded_llama import TransportError, UnknownRequest


class Response:
    def __init__(self, text):
        self.status, self.body = 200, json.dumps({"choices": [{"message": {"content": text}, "finish_reason": "stop"}]}).encode()

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def echo(request, timeout=None):
    body = json.loads(request.data)
    return Response(f"reply to {body['messages'][-1]['content']} at seed {body['seed']}")


class RunRequestsTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)
        self.req = self.dir / "REQUESTS.jsonl"
        rows = [{"id": "a|1831", "messages": [{"role": "user", "content": "one"}],
                 "params": {"seed": 1831, "temperature": 0.7, "max_tokens": 400, "cache_prompt": False}},
                {"id": "b", "messages": [{"role": "user", "content": "two"}],
                 "settings": {"temperature": 0, "max_tokens": 4, "seed": 1831, "cache_prompt": False}},
                {"id": "c", "messages": [{"role": "user", "content": "three"}], "params": {"seed": 7, "max_tokens": 9}}]
        self.req.write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.job, self.out = self.dir / "job", self.dir / "REPLIES.jsonl"

    def tearDown(self):
        self.td.cleanup()

    def go(self, opener, **kw):
        return run_requests.run(self.req, "http://127.0.0.1:8082", self.job, self.out, opener=opener, **kw)

    def test_a_reasoning_budget_turns_thinking_on_for_that_call_and_a_schema_is_sent(self):
        rows = [{"id": "think", "messages": [{"role": "user", "content": "one"}], "schema": {"type": "object", "properties": {"text": {"type": "string"}}},
                 "params": {"seed": 3, "temperature": 0.7, "max_tokens": 3148, "cache_prompt": False, "reasoning_budget_tokens": 2048}},
                {"id": "plain", "messages": [{"role": "user", "content": "two"}], "params": {"seed": 3, "max_tokens": 1100}}]
        self.req.write_text("".join(json.dumps(r) + "\n" for r in rows))
        opener = mock.Mock(side_effect=echo)
        ledger = self.go(opener)
        self.assertTrue(ledger["complete"])
        first, second = (json.loads(c.args[0].data) for c in opener.call_args_list)
        self.assertEqual((first["chat_template_kwargs"], first["reasoning_budget_tokens"], first["max_tokens"]), ({"enable_thinking": True}, 2048, 3148))
        self.assertEqual(first["response_format"]["json_schema"]["schema"], rows[0]["schema"])
        self.assertEqual(second["chat_template_kwargs"], {"enable_thinking": False})
        self.assertNotIn("reasoning_budget_tokens", second)
        self.assertNotIn("response_format", second)
        self.assertIs(json.loads((self.job / "PLAN.json").read_text())["thinking"], True)

    def test_another_models_template_arguments_ride_along(self):
        row = {"id": "IA|b01", "messages": [{"role": "user", "content": "x"}], "params": {"seed": 1, "temperature": 0.7, "max_tokens": 100,
               "cache_prompt": False, "template_kwargs": {"reasoning_effort": "none"}}}
        self.assertEqual(run_requests.payload(row)["chat_template_kwargs"], {"enable_thinking": False, "reasoning_effort": "none"})
        bad = Path(self.td.name) / "bad.jsonl"
        bad.write_text(json.dumps(dict(row, params=dict(row["params"], template_kwargs="none"))) + "\n")
        with self.assertRaises(ValueError):
            run_requests.load(bad)

    def test_a_budget_must_leave_room_for_the_answer(self):
        bad = {"id": "x", "messages": [{"role": "user", "content": "one"}], "params": {"max_tokens": 2048, "reasoning_budget_tokens": 2048}}
        self.req.write_text(json.dumps(bad) + "\n")
        with self.assertRaises(ValueError):
            self.go(mock.Mock(side_effect=echo))

    def test_the_other_slots_only_at_night(self):
        with self.assertRaises(ValueError):
            self.go(mock.Mock(side_effect=echo), slot=0)                         # by day slot 0 is his
        opener = mock.Mock(side_effect=echo)
        ledger = self.go(opener, slot=2, night=True)
        self.assertTrue(ledger["complete"])
        self.assertEqual(json.loads(opener.call_args_list[0].args[0].data)["id_slot"], 2)
        self.assertEqual(json.loads((self.job / "PLAN.json").read_text())["slot"], 2)
        with self.assertRaises(ValueError):
            run_requests.run(self.req, "http://127.0.0.1:8082", self.dir / "job3", self.dir / "R3.jsonl", opener=opener, slot=3, night=True)

    def test_every_call_once_in_order_on_the_spare_slot_with_thinking_off(self):
        opener = mock.Mock(side_effect=echo)
        ledger = self.go(opener)
        self.assertTrue(ledger["complete"])
        self.assertEqual((ledger["sent_this_run"], ledger["reused"], ledger["failed"]), (3, 0, []))
        lines = [json.loads(l) for l in self.out.read_text().splitlines()]
        self.assertEqual([l["id"] for l in lines], ["a|1831", "b", "c"])
        self.assertEqual(lines[0]["reply"], "reply to one at seed 1831")
        sent = json.loads(opener.call_args_list[0].args[0].data)
        self.assertEqual((sent["id_slot"], sent["cache_prompt"], sent["chat_template_kwargs"]), (1, False, {"enable_thinking": False}))
        self.assertEqual((sent["temperature"], sent["max_tokens"]), (0.7, 400))
        self.assertNotIn("lora", sent)
        self.assertFalse(ledger["training_eligible"])

    def test_a_second_run_sends_nothing_and_writes_the_same_replies(self):
        self.go(mock.Mock(side_effect=echo))
        first = self.out.read_bytes()
        again = mock.Mock(side_effect=echo)
        ledger = self.go(again)
        self.assertEqual(again.call_count, 0)
        self.assertEqual((ledger["reused"], self.out.read_bytes()), (3, first))

    def test_a_limit_stops_and_the_next_run_resumes(self):
        ledger = self.go(mock.Mock(side_effect=echo), limit=1)
        self.assertEqual((ledger["complete"], ledger["stopped"], ledger["replied"]), (False, "limit", 1))
        self.assertFalse(self.out.exists())
        opener = mock.Mock(side_effect=echo)
        self.assertTrue(self.go(opener)["complete"])
        self.assertEqual(opener.call_count, 2)

    def test_a_call_cut_off_is_never_sent_again(self):
        with self.assertRaises(KeyboardInterrupt):
            self.go(mock.Mock(side_effect=KeyboardInterrupt))
        again = mock.Mock(side_effect=echo)
        with self.assertRaises(UnknownRequest):
            self.go(again)
        self.assertEqual(again.call_count, 0)

    def test_the_guard_stops_new_calls_before_they_are_sent(self):
        calls = []
        def guard():
            calls.append(1)
            if len(calls) > 1:
                raise TransportError("natural step is slower than its frozen limit; stop new GPU work")
        opener = mock.Mock(side_effect=echo)
        ledger = self.go(opener, before_request=guard)
        self.assertEqual((opener.call_count, ledger["replied"], ledger["complete"]), (1, 1, False))
        self.assertIn("stopped before b", ledger["stopped"])

    def test_another_requests_file_cannot_reuse_the_job(self):
        self.go(mock.Mock(side_effect=echo))
        self.req.write_text(self.req.read_text().replace("three", "four"))
        with self.assertRaises(ValueError):
            self.go(mock.Mock(side_effect=echo))

    def test_the_real_files_load(self):
        repo = Path(__file__).resolve().parents[1]
        raw, rows = run_requests.load(repo / "pc/exports/paris-stage2-20261118/REQUESTS.jsonl")
        self.assertEqual(len(rows), 96)
        p = run_requests.payload(rows[0])
        self.assertEqual((p["cache_prompt"], p["seed"]), (False, 1831))


if __name__ == "__main__":
    unittest.main()
