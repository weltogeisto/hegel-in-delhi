"""P5: once any adapter scale is set, every call names its adapter; with none set, no payload carries lora."""
import json, unittest
from unittest import mock
from world import mind as mind_mod
from world.mind import HTTPMind

class Reply:
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self.body

class Routing(unittest.TestCase):
    def setUp(self):
        self.sent = []
        def fake(req, timeout=None):
            body = json.loads(req.data.decode())
            self.sent.append((req.full_url.rsplit("/", 1)[-1], body))
            if req.full_url.endswith("/completion"):
                return Reply(json.dumps({"content": "text"}).encode())
            return Reply(json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode())
        p = mock.patch.object(mind_mod.urllib.request, "urlopen", fake); p.start(); self.addCleanup(p.stop)
        self.m = lambda **kw: self._mind(**kw)
    def _mind(self, **kw):
        m = HTTPMind("http://x", **kw); m.ready = True; return m
    def calls(self, m):
        """One of each kind of call; returns their lora, in order: voice, decision, writing, plain chat, choice-like chat, complete."""
        m.chat_voice([{"role": "user", "content": "v"}])
        m.chat_decision([{"role": "user", "content": "d"}])
        m.chat_writing([{"role": "user", "content": "w"}])
        m.chat([{"role": "user", "content": "owl"}])
        m.chat([{"role": "user", "content": "choice"}], max_tokens=20, temperature=0)
        m.complete("prose")
        return [b.get("lora") for _, b in self.sent]
    def test_nothing_configured_no_lora_anywhere(self):
        self.assertEqual(self.calls(self.m()), [None] * 6)
    def test_voice_only_gets_one_everything_else_zero(self):
        zero, one = [{"id": 0, "scale": 0}], [{"id": 0, "scale": 1}]
        self.assertEqual(self.calls(self.m(voice_adapter_scale=1)), [one, zero, zero, zero, zero, zero])
    def test_decision_only_leaves_the_voice_at_zero(self):
        zero, one = [{"id": 0, "scale": 0}], [{"id": 0, "scale": 1}]
        self.assertEqual(self.calls(self.m(decision_adapter_scale=1)), [zero, one, zero, zero, zero, zero])
    def test_writing_only(self):
        zero, one = [{"id": 0, "scale": 0}], [{"id": 0, "scale": 1}]
        self.assertEqual(self.calls(self.m(writing_adapter_scale=1)), [zero, zero, one, zero, zero, zero])
    def test_explicit_zero_wins(self):
        m = self.m(voice_adapter_scale=1)
        m.chat([{"role": "user", "content": "x"}], adapter_scale=0)
        self.assertEqual(self.sent[0][1]["lora"], [{"id": 0, "scale": 0}])
    def test_explicit_one_on_a_plain_chat(self):
        m = self.m(voice_adapter_scale=0)
        m.chat([{"role": "user", "content": "x"}], adapter_scale=1)
        self.assertEqual(self.sent[0][1]["lora"], [{"id": 0, "scale": 1}])
    def test_complete_goes_to_completion_endpoint(self):
        self.m(voice_adapter_scale=1).complete("p")
        self.assertEqual(self.sent[0][0], "completion")

if __name__ == "__main__": unittest.main()
