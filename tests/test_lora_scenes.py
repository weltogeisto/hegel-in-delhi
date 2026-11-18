"""tools/lora_scenes.py: the draw, the plan's hash, and the run with a fake client. No git, no network."""
import contextlib
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import lora_scenes as ls


def words(tag, n=45):
    return " ".join(tag + str(i) for i in range(n))


def make_day(n, ordinary=10, occasion=10, complete=True, short=0, dup=False):
    """A day file: `ordinary` steps opening nothing, `occasion` steps opening with a reply, `short` thin thoughts."""
    steps = []
    for k in range(ordinary):
        steps.append({"t": "09:%02d" % k, "opened": [], "decision": {"thought": words("o%d_%d_" % (n, k))}})
    for k in range(occasion):
        steps.append({"t": "10:%02d" % k, "opened": ["reply"] if k % 2 else ["post"], "decision": {"thought": words("c%d_%d_" % (n, k))}})
    for k in range(short):
        steps.append({"t": "11:%02d" % k, "opened": [], "decision": {"thought": "too short"}})
    if dup:
        steps.append({"t": "12:00", "opened": [], "decision": {"thought": steps[0]["decision"]["thought"]}})
    return {"n": n, "date": "2026-11-%02d" % (n - 30), "complete": complete, "steps": steps}


def write_days(folder, days):
    for d in days:
        Path(folder, d["date"] + ".json").write_text(json.dumps(d), encoding="utf-8")


class FakeClient:
    """Records every payload; the reply is a fixed distinct text per request."""
    def __init__(self, sink, scale):
        self.sink, self.scale = sink, scale

    def chat(self, rid, messages, temperature, tokens, seed):
        self.sink.append({"rid": rid, "scale": self.scale, "temperature": temperature, "tokens": tokens, "seed": seed,
                          "cache_prompt": False})
        return "rewritten " + rid, "stop"


class NoGuard:
    def matches(self, text):
        return []


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def plan(self, days, seed=1831):
        loaded = {d["n"]: d for d in days}
        return ls.freeze(loaded, "docs:test", None, seed)

    def test_deterministic_and_twelve_a_day(self):
        days = [make_day(n) for n in (46, 47, 48, 49)]
        a, _ = self.plan(days)
        b, _ = self.plan(days)
        self.assertEqual(ls.json_bytes(a), ls.json_bytes(b))
        for n in (46, 47, 48, 49):
            self.assertEqual(sum(c["day"] == n for c in a["cases"]), 12)
        self.assertEqual([c["i"] for c in a["cases"]], list(range(48)))
        order = [(c["day"], c["step"]) for c in a["cases"]]
        self.assertEqual(order, sorted(order))
        self.assertNotEqual(ls.json_bytes(a), ls.json_bytes(self.plan(days, seed=7)[0]))

    def test_six_ordinary_and_fill_rules(self):
        plan, table = self.plan([make_day(47), make_day(48)])
        self.assertTrue(all(t["ordinary"] == 6 and t["occasion"] == 6 for t in table))
        plan, table = self.plan([make_day(47, ordinary=2, occasion=15)])
        self.assertEqual((table[0]["ordinary"], table[0]["occasion"]), (2, 10))
        plan, table = self.plan([make_day(47, ordinary=15, occasion=3)])
        self.assertEqual((table[0]["ordinary"], table[0]["occasion"]), (9, 3))
        with self.assertRaises(SystemExit):
            self.plan([make_day(47, ordinary=5, occasion=4)])

    def test_group_and_kinds(self):
        plan, _ = self.plan([make_day(47)])
        for c in plan["cases"]:
            if c["group"] == "ordinary":
                self.assertEqual(c["kinds"], [])
            else:
                self.assertTrue(set(c["kinds"]) & {"reply", "post"})

    def test_incomplete_or_thoughtless_day_refused(self):
        with self.assertRaises(SystemExit) as cm:
            self.plan([make_day(47), make_day(48, complete=False)])
        self.assertIn("not marked complete", str(cm.exception))
        empty = make_day(48)
        for s in empty["steps"]:
            s["decision"]["thought"] = ""
        with self.assertRaises(SystemExit) as cm:
            self.plan([empty])
        self.assertIn("no thoughts", str(cm.exception))

    def test_held_back_one_each_side(self):
        for seed in (1831, 1, 2, 3, 4, 5):
            plan, table = self.plan([make_day(n) for n in range(44, 50)], seed)
            old, new = plan["held_back"]
            self.assertIn(old, range(44, 48))
            self.assertIn(new, (48, 49))
            for t in table:
                self.assertEqual(t["set"], "confirmation" if t["day"] in (old, new) else "development")
            for c in plan["cases"]:
                self.assertEqual(c["set"], "confirmation" if c["day"] in (old, new) else "development")
        plan, _ = self.plan([make_day(n) for n in range(44, 49)])
        self.assertEqual(len(plan["held_back"]), 2)
        plan, _ = self.plan([make_day(44), make_day(45)])
        self.assertEqual(len(plan["held_back"]), 1)

    def test_floor_and_duplicates(self):
        plan, table = self.plan([make_day(47, ordinary=8, occasion=8, short=5, dup=True)])
        self.assertEqual(table[0]["candidates"], 16)
        self.assertTrue(all(c["words"] >= 40 for c in plan["cases"]))
        self.assertEqual(len({c["thought"] for c in plan["cases"]}), 12)
        edge = make_day(47, ordinary=6, occasion=6)
        edge["steps"][0]["decision"]["thought"] = words("x", 39)
        rows = ls.candidates(edge)
        self.assertEqual(len(rows), 11)
        edge["steps"][0]["decision"]["thought"] = words("x", 40)
        self.assertEqual(len(ls.candidates(edge)), 12)

    def test_words_path_without_opened(self):
        day = make_day(46, ordinary=3, occasion=0)
        for s in day["steps"]:
            del s["opened"]
            s["event"] = "Nothing in particular happens."
        day["steps"][1]["event"] = "Headlines: war."
        rows = ls.candidates(day)
        self.assertEqual([r["group"] for r in rows], ["ordinary", "occasion", "ordinary"])
        self.assertEqual(rows[1]["kinds"], ["papers"])

    def test_freeze_cli_from_docs(self):
        docs = Path(self.tmp.name) / "docs"
        docs.mkdir()
        write_days(docs, [make_day(47), make_day(48)])
        out = Path(self.tmp.name) / "plan.json"
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ls.main(["freeze", "--docs", str(docs), "--days", "47-48", "--out", str(out)])
        self.assertIn("confirmation", buf.getvalue())
        plan = json.loads(out.read_text())
        self.assertEqual(plan["sha256"], ls.plan_hash(plan))
        self.assertEqual(plan["declared"], "pc/LORA-FRESH-SCENES.md")


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.plan, _ = ls.freeze({47: make_day(47), 48: make_day(48)}, "docs:test", None)
        self.sent = []
        self.factory = lambda url, root, lora_id, scale: FakeClient(self.sent, scale)

    def go(self, out="out", **kw):
        return ls.run(self.plan, "http://x:1", self.dir / out, probe=lambda url, i: None,
                      client_factory=self.factory, guard=NoGuard(), **kw)

    def test_three_requests_per_case(self):
        self.go(limit=2)
        self.assertEqual(len(self.sent), 6)
        for k, case in enumerate(self.plan["cases"][:2]):
            mine = self.sent[3 * k:3 * k + 3]
            self.assertEqual([m["scale"] for m in mine], [1.0, 0.0, 0.0])
            self.assertEqual([m["seed"] for m in mine], [1831 + 17 * k, 1831 + 17 * k, 2831 + 17 * k])
            for m in mine:
                self.assertEqual(m["tokens"], math.ceil(2.5 * case["words"]))
                self.assertEqual(m["temperature"], 0.9)
                self.assertIs(m["cache_prompt"], False)
        rows = [json.loads(x) for x in (self.dir / "out/outputs.jsonl").read_text().splitlines()]
        self.assertEqual([r["version"] for r in rows], ["adapter", "plain1", "plain2"] * 2)
        run = json.loads((self.dir / "out/RUN.json").read_text())
        self.assertEqual(run["plan_sha256"], self.plan["sha256"])
        self.assertEqual(run["outputs"], 6)

    def test_resume_skips_and_never_overwrites(self):
        self.go(limit=2)
        path = self.dir / "out/outputs.jsonl"
        before = path.read_bytes()
        self.sent.clear()
        self.go(limit=2)
        self.assertEqual(self.sent, [])
        self.assertEqual(path.read_bytes(), before)
        self.go(limit=3)
        self.assertEqual(len(self.sent), 3)
        self.assertTrue(path.read_bytes().startswith(before))
        lines = path.read_text().splitlines()
        self.assertEqual(len(lines), 9)
        self.assertEqual(len(set((json.loads(x)["i"], json.loads(x)["version"]) for x in lines)), 9)

    def test_adapter_probe_refusal(self):
        def probe(url, lora_id):
            raise SystemExit("run: the server lists no adapter with id " + str(lora_id))
        with self.assertRaises(SystemExit):
            ls.run(self.plan, "http://x:1", self.dir / "o2", probe=probe, client_factory=self.factory, guard=NoGuard())
        self.assertEqual(self.sent, [])

    def test_real_probe_checks_the_id(self):
        import urllib.request
        listed = [{"id": 0, "path": "a.gguf", "scale": 0.0}]

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        original = urllib.request.urlopen
        urllib.request.urlopen = lambda *a, **k: Response(json.dumps(listed).encode())
        try:
            self.assertEqual(ls.probe_adapter("http://x:1", 0), listed)
            with self.assertRaises(SystemExit):
                ls.probe_adapter("http://x:1", 3)
        finally:
            urllib.request.urlopen = original

    def test_tampered_plan_refused(self):
        path = self.dir / "plan.json"
        path.write_bytes(ls.json_bytes(self.plan))
        self.assertEqual(ls.load_plan(path)["sha256"], self.plan["sha256"])
        tampered = json.loads(path.read_text())
        tampered["cases"][0]["thought"] += " extra"
        path.write_bytes(ls.json_bytes(tampered))
        with self.assertRaises(SystemExit):
            ls.load_plan(path)

    def test_attempt_added_to_seed_on_retry(self):
        class Copier(NoGuard):
            calls = 0

            def matches(self, text):
                Copier.calls += 1
                return ["copied run"] if Copier.calls == 1 else []
        ls.run(self.plan, "http://x:1", self.dir / "o3", limit=1, probe=lambda u, i: None,
               client_factory=self.factory, guard=Copier())
        self.assertEqual([m["seed"] for m in self.sent[:2]], [1831, 1832])
        rows = [json.loads(x) for x in (self.dir / "o3/outputs.jsonl").read_text().splitlines()]
        self.assertEqual(rows[0]["attempts"], 2)
        self.assertFalse(rows[0]["fallback"])


class SceneClientTests(unittest.TestCase):
    def test_payload_carries_lora_and_cache_prompt_false(self):
        seen = []

        class Reply(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def opener(request, timeout):
            seen.append(json.loads(request.data))
            return Reply(json.dumps({"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}]}).encode())
        with tempfile.TemporaryDirectory() as d:
            client = ls.SceneClient("http://x:1", d, lora=[{"id": 0, "scale": 0.0}], opener=opener)
            self.assertEqual(client.chat("r", [{"role": "user", "content": "a"}], 0.9, 10, 5), ("hi", "stop"))
        self.assertIs(seen[0]["cache_prompt"], False)
        self.assertEqual(seen[0]["lora"], [{"id": 0, "scale": 0.0}])
        self.assertEqual(seen[0]["seed"], 5)


if __name__ == "__main__":
    unittest.main()
