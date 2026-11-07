"""Saved replies survive a JSON round trip; all transport here is synthetic."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import decision_sampler as ds, decision_sampling as api
from tests.test_decision_sampler import CheckWorld, Transport, context
from world.mind import StubMind


class InjectedStop(Exception):
    pass


class CanonicalSituationTest(unittest.TestCase):
    def test_completed_row_with_recent_tuples_replays_without_calls(self):
        root = Path(tempfile.mkdtemp(prefix="decision-resume-json-"))
        transport = Transport()
        sampler = ds.Sampler(root, CheckWorld(), transport)
        situation = context()
        situation["check"]["context"]["recent"] = [("2026-11-05", "A prior thought")]
        row = sampler.sample(situation)
        before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        saved = ds.checked(next(root.glob("*/SITUATION.json")))
        self.assertNotEqual(saved, situation)  # JSON arrays replace Python tuples.
        self.assertEqual(ds.json_bytes(saved), ds.json_bytes(situation))
        self.assertEqual(sampler.sample(situation), row)
        self.assertEqual(sampler.sample(saved), row)
        self.assertEqual(len(transport.calls), 4)
        self.assertTrue(all(p.read_bytes() == raw for p, raw in before.items()))

    def test_changed_recent_content_still_refused_before_transport(self):
        root = Path(tempfile.mkdtemp(prefix="decision-resume-drift-"))
        transport = Transport()
        sampler = ds.Sampler(root, CheckWorld(), transport)
        situation = context()
        situation["check"]["context"]["recent"] = [("2026-11-05", "A prior thought")]
        sampler.sample(situation)
        changed = copy.deepcopy(situation)
        changed["check"]["context"]["recent"][0] = ("2026-11-05", "Different thought")
        with self.assertRaisesRegex(ValueError, "saved situation differs"):
            sampler.sample(changed)
        self.assertEqual(len(transport.calls), 4)

    def test_situation_hash_is_checked_even_when_json_bytes_match(self):
        root = Path(tempfile.mkdtemp(prefix="decision-resume-hash-"))
        transport = Transport()
        sampler = ds.Sampler(root, CheckWorld(), transport)
        situation = context()
        sampler.sample(situation)
        sidecar = next(root.glob("*/SITUATION.json.sha256"))
        sidecar.write_text("0" * 64 + "\n")
        with self.assertRaisesRegex(ValueError, "record changed"):
            sampler.sample(situation)
        self.assertEqual(len(transport.calls), 4)


class InterruptedRehearsalTest(unittest.TestCase):
    def exercise(self, unknown):
        repo = Path(__file__).resolve().parents[1]
        root = Path(tempfile.mkdtemp(prefix="decision-resume-engine-"))
        docs = root / "rehearsal"
        (docs / "days").mkdir(parents=True)
        raw = (repo / "docs/days/2026-10-02.json").read_bytes()
        (docs / "days/2026-10-02.json").write_bytes(raw)
        old = json.loads(raw)
        (docs / "days/index.json").write_text(json.dumps({"format": 1, "days": [
            {k: old.get(k) for k in ("date", "n", "title", "holiday")}]}))
        cfg = SimpleNamespace(
            repo=repo, docs=docs, state=root / "state", push=False, feeds=False,
            news_feeds=[], soul_file=repo / "mind/soul.md", shelf=False,
            write_mode="chat", lead=15, owl_at="09:10", depesche_day="Saturday",
            clock_shift_min=0)
        cache, sent, attempts, blocked, holder = {}, [], [], set(), {}
        fired = False
        fake = StubMind()

        def world_type(feeds):
            holder["world"] = ds.CandidateWorld()
            return holder["world"]

        def post(key, payload):
            nonlocal fired
            encoded = ds.json_bytes(payload)
            attempts.append(key)
            if key in blocked:
                raise InjectedStop("saved unknown: never resend")
            if key in cache:
                before, reply, receipt = cache[key]
                self.assertEqual(encoded, before, "resume changed the exact prompt")
                return copy.deepcopy(reply), copy.deepcopy(receipt)
            target = (key.startswith("decision/") and not fired and
                      sum(k.startswith("decision/") for k in sent) == 5)
            if target and unknown:
                fired = True
                blocked.add(key)
                raise InjectedStop("unknown response")
            schema = payload.get("response_format", {}).get("json_schema", {}).get("schema")
            if key.startswith("decision/"):
                answer = fake.decide(payload["messages"], holder["world"].current[0])
            else:
                answer = fake.chat(payload["messages"], schema=schema,
                                   max_tokens=payload["max_tokens"])
            reply = {"choices": [{"message": {"content": answer}, "finish_reason": "stop"}]}
            receipt = {"response_sha256": ds.digest(ds.json_bytes(reply))}
            cache[key] = (encoded, copy.deepcopy(reply), copy.deepcopy(receipt))
            sent.append(key)
            if target:
                fired = True
                raise InjectedStop("reply durable, caller interrupted")
            return reply, receipt

        records = root / "records"
        with patch.object(api, "REHEARSAL_SITUATIONS", 2):
            with self.assertRaises(InjectedStop):
                api.rehearse(cfg, records, post, max_days=1, world_type=world_type)
            self.assertTrue(fired)
            self.assertEqual(len(list(records.glob("*/ROW.json"))), 1)
            before = {p: p.read_bytes() for p in records.rglob("*") if p.is_file()}
            before_sent = list(sent)
            if unknown:
                with self.assertRaisesRegex(InjectedStop, "saved unknown"):
                    api.rehearse(cfg, records, post, max_days=1, world_type=world_type)
                self.assertEqual(sent, before_sent)
            else:
                ids = api.rehearse(cfg, records, post, max_days=1, world_type=world_type)
                self.assertEqual(len(ids), 2)
                decision_sends = [k for k in sent if k.startswith("decision/")]
                self.assertEqual(len(decision_sends), 8)
                self.assertEqual(len(sent), len(set(sent)))
                self.assertEqual(attempts.count(before_sent[-1]), 2)
                rows = [ds.checked(p) for p in records.glob("*/ROW.json")]
                self.assertEqual(sorted(len(r["earlier_thoughts"]) for r in rows), [0, 1])
            self.assertTrue(all(p.read_bytes() == value for p, value in before.items()))
            self.assertEqual((repo / "docs/days/2026-10-02.json").read_bytes(), raw)

    def test_later_saved_reply_replays_after_completed_situation(self):
        self.exercise(unknown=False)

    def test_later_unknown_reply_still_stops_without_new_sends(self):
        self.exercise(unknown=True)


if __name__ == "__main__":
    unittest.main()
