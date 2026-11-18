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
