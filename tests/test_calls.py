"""HEGEL_RECORD_CALLS and its replay (world/calls.py, tools/replay_morning.py): a morning written down, then lived again from the record."""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO  # noqa: E402  (this also keeps the tests off the Pi's env file)

from tools import replay_morning as rm  # noqa: E402
from world import calls  # noqa: E402
from world.__main__ import make_mind, make_world  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import HTTPMind  # noqa: E402
from world.world import at_dt  # noqa: E402

PLACES = ("home", "lodhi", "khan")
ACTS = ("stay", "read", "write", "rest")


def fake_send(path, payload):
    """A server that answers from what it is asked: the same request, the same reply."""
    h = int(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), 16)
    if path == "/completion":
        return {"content": "(test) A page of prose."}
    if path == "/tokenize":
        return {"tokens": list(range(100))}
    if path == "/apply-template":
        return {"prompt": "x"}
    props = ((payload.get("response_format") or {}).get("json_schema") or {}).get("schema", {}).get("properties", {})
    if "action" in props:
        ans = {"thought": f"(test) a thought {h % 97}.", "action": ACTS[h % 4], "place": "home", "minutes": 15 + 15 * (h % 3),
               "says": None, "buys": [], "revision": None}
    else:
        ans = {"says": "(test) Yes.", "answer": "yes", "plan": [{"time": "09:00", "intention": "(test) read"}]}
    return {"choices": [{"message": {"content": json.dumps(ans)}}]}


class Box:
    def __init__(self, record):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-calls-"))
        (self.tmp / "docs/days").mkdir(parents=True)
        for f in ("2026-10-02.json", "index.json"):
            shutil.copy(REPO / "docs/days" / f, self.tmp / "docs/days" / f)
        self.cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(self.tmp / "state"), "HEGEL_FEEDS": "0",
                           "HEGEL_RECORD_CALLS": "1" if record else "0"})
        self.cfg.docs = self.tmp / "docs"

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class RecordTest(unittest.TestCase):
    def mind(self, folder, send=fake_send):
        m = HTTPMind("http://pc.invalid:8082")
        m.ready = True
        m._send = send
        m.recorder = calls.Recorder(folder, {"code": "c"})
        return m

    def rows(self, folder):
        return calls.read(sorted(Path(folder).glob("calls-*.jsonl")))

    def test_off_by_default(self):
        self.assertFalse(Config({}).record_calls)
        self.assertTrue(Config({"HEGEL_RECORD_CALLS": "1"}).record_calls)
        self.assertIsNone(HTTPMind("http://x").recorder)

    def test_each_call_is_written_with_its_moment_kind_and_reply(self):
        with tempfile.TemporaryDirectory() as d:
            m = self.mind(d)
            m.at("2026-11-25T09:00")
            m.chat_decision([{"role": "user", "content": "hi"}], {"type": "object", "properties": {"action": {}}})
            m.complete("Once")
            rows = self.rows(d)
            self.assertEqual([r["type"] for r in rows], ["header", "call", "call"])
            self.assertEqual(rows[0]["code"], "c")
            self.assertEqual((rows[1]["kind"], rows[1]["at"], rows[1]["path"]), ("decision", "2026-11-25T09:00", "/v1/chat/completions"))
            self.assertEqual(rows[1]["payload"]["messages"][0]["content"], "hi")
            self.assertIn("choices", rows[1]["reply"])
            self.assertEqual((rows[2]["kind"], rows[2]["reply"]["content"]), ("complete", "(test) A page of prose."))

    def test_an_error_is_written_and_the_fallback_runs_as_before(self):
        def old_server(path, payload):
            if "response_format" in payload:
                raise urllib.error.HTTPError(path, 400, "no json_schema", None, None)
            return fake_send(path, payload)
        with tempfile.TemporaryDirectory() as d:
            m = self.mind(d, old_server)
            m.chat([{"role": "user", "content": "hi"}], {"type": "object", "properties": {"answer": {}}})
            calls_ = [r for r in self.rows(d) if r["type"] == "call"]
            self.assertEqual([c["error"] for c in calls_], [{"http": 400}, None])
            replay = HTTPMind("http://pc.invalid:8082")
            calls.play(replay, calls.Player(self.rows(d)))
            self.assertIn("yes", replay.chat([{"role": "user", "content": "hi"}], {"type": "object", "properties": {"answer": {}}}))


class PlayerTest(unittest.TestCase):
    def rows(self):
        return [{"type": "header"},
                {"type": "call", "i": 1, "at": "09:00", "kind": "decision", "path": "/v1/chat/completions",
                 "payload": {"messages": [{"role": "user", "content": "Delhi at nine."}], "max_tokens": 700}, "reply": {"ok": 1}, "error": None}]

    def test_the_same_request_gets_the_recorded_reply(self):
        p = calls.Player(self.rows())
        self.assertEqual(p.send("/v1/chat/completions", {"messages": [{"role": "user", "content": "Delhi at nine."}], "max_tokens": 700}), {"ok": 1})

    def test_a_different_request_names_its_first_field(self):
        p = calls.Player(self.rows())
        with self.assertRaises(calls.Mismatch) as e:
            p.send("/v1/chat/completions", {"messages": [{"role": "user", "content": "Delhi at ten."}], "max_tokens": 700})
        self.assertIn(".messages[0].content at character 9", str(e.exception))
        with self.assertRaises(calls.Mismatch) as e:
            calls.Player(self.rows()).send("/v1/chat/completions", {"messages": [{"role": "user", "content": "Delhi at nine."}]})
        self.assertIn(".max_tokens", str(e.exception))

    def test_a_call_beyond_the_recording_is_a_mismatch(self):
        p = calls.Player(self.rows())
        p.send("/v1/chat/completions", {"messages": [{"role": "user", "content": "Delhi at nine."}], "max_tokens": 700})
        with self.assertRaises(calls.Mismatch):
            p.send("/completion", {})

    def test_switches_keep_no_places_and_no_secrets(self):
        cfg = Config({"HEGEL_CULTURE": "1", "HEGEL_STATE": "/x", "HEGEL_API_TOKEN": "s", "LEAD_MIN": "15"})
        got = calls.switches(cfg)
        self.assertEqual((got.get("HEGEL_CULTURE"), got.get("LEAD_MIN")), ("1", "15"))
        self.assertNotIn("HEGEL_STATE", got)
        self.assertNotIn("HEGEL_API_TOKEN", got)


class MorningTest(unittest.TestCase):
    """A stand-in morning, ticked each minute as the Pi ticks, recorded; then replayed from the record."""

    @classmethod
    def setUpClass(cls):
        cls.box = Box(record=True)
        cls.start = cls.box.tmp / "start"
        shutil.copytree(cls.box.tmp / "docs/days", cls.start / "days")
        mind = make_mind(cls.box.cfg, "http://pc.invalid:8082")
        mind.ready = True
        mind._send = fake_send
        engine = Engine(cls.box.cfg, make_world(cls.box.cfg), mind, git=None)
        d = date(2026, 10, 3)
        now = at_dt(d, 0)
        while now < at_dt(d, 13 * 60):
            engine.tick(now)
            now += timedelta(minutes=1)
        cls.files = sorted((cls.box.tmp / "state/calls").glob("calls-*.jsonl"))
        cls.live = cls.box.tmp / "docs"

    @classmethod
    def tearDownClass(cls):
        cls.box.close()

    def test_the_morning_is_recorded(self):
        rows = calls.read(self.files)
        self.assertEqual(rows[0]["type"], "header")
        self.assertEqual(rows[0]["code"], calls.code_hash(REPO))
        self.assertTrue(any(r["type"] == "tick" for r in rows))
        self.assertTrue(any(r["type"] == "call" and r["kind"] == "decision" for r in rows))

    def test_the_replay_matches(self):
        r = rm.replay(self.start, self.files, self.live, self.box.tmp / "r1", decisions=5)
        self.assertEqual(r["result"], "match", r)
        self.assertGreaterEqual(r["decisions"], 5)

    def test_a_changed_reply_is_found_at_its_step(self):
        rows = calls.read(self.files)
        i = next(n for n, r in enumerate(rows) if r["type"] == "call" and r["kind"] == "decision"
                 and '"minutes"' in r["reply"]["choices"][0]["message"]["content"])
        ans = json.loads(rows[i]["reply"]["choices"][0]["message"]["content"])
        ans["minutes"] = 240 if ans["minutes"] != 240 else 5
        rows[i]["reply"]["choices"][0]["message"]["content"] = json.dumps(ans)
        f = self.box.tmp / "tampered.jsonl"
        f.write_text("".join(json.dumps(r) + "\n" for r in rows))
        r = rm.replay(self.start, [f], self.live, self.box.tmp / "r2", decisions=5)
        self.assertEqual(r["result"], "mismatch", r)

    def test_a_recording_cut_short_is_inconclusive(self):
        rows = calls.read(self.files)
        ticks = [n for n, r in enumerate(rows) if r["type"] == "tick"]
        f = self.box.tmp / "short.jsonl"
        f.write_text("".join(json.dumps(r) + "\n" for r in rows[:ticks[1]]))
        r = rm.replay(self.start, [f], self.live, self.box.tmp / "r3", decisions=50)
        self.assertEqual(r["result"], "inconclusive", r)


if __name__ == "__main__":
    unittest.main()
