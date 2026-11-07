"""CPU-only checks. The transport is fake; no model, service or GPU is contacted."""
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from tools import decision_pairs, decision_sampler as ds


class CheckWorld:
    def check(self, answer, sit, ctx, state):
        if not isinstance(answer, dict):
            return ["invalid"], [], None
        # Deliberately mutate the state to test candidate isolation.
        self.last_state = dict(state)
        state["seen"] = answer["thought"]
        if "refused" in answer["thought"]:
            return ["refused by world"], ["a recorded warning"], None
        return [], ["a recorded warning"], (answer, {})


def context(source="shadow", day=35, step=1, when="2026-11-05"):
    return ds.situation_record(
        source, day, step, when,
        [{"role": "system", "content": "frozen soul"}, {"role": "user", "content": "exact situation"}],
        ["An earlier recorded thought"],
        {"id": when + "/09:30", "time": "09:30", "reconcile_payments": False},
        {"t": datetime.fromisoformat(when + "T09:30:00+05:30"), "present": [],
         "public": [], "recent": [], "known_text": "", "transient": object()},
        {"place": "home"}, {"kind": "synthetic test"})


class Transport:
    def __init__(self):
        self.calls = []
        self.saved = {}
        self.fail_seed = None

    def __call__(self, key, payload):
        if key in self.saved:
            old_payload, value = self.saved[key]
            if old_payload != payload:
                raise ValueError("changed request")
            return copy.deepcopy(value)
        self.calls.append((key, copy.deepcopy(payload)))
        if payload["seed"] == self.fail_seed:
            raise TimeoutError("unknown, no retry")
        thought = ("refused " if payload["seed"] == 2718 else "") + "a clerk sent this particular petition to the counter for its number"
        text = "  " + json.dumps({"thought": thought, "action": "stay"}) + "\n"
        value = ({"choices": [{"message": {"content": text}, "finish_reason": "stop"}]},
                 {"response_sha256": hashlib.sha256(text.encode()).hexdigest()})
        self.saved[key] = (copy.deepcopy(payload), copy.deepcopy(value))
        return value


class SamplerTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="decision-sampler-test-"))
        self.world, self.transport = CheckWorld(), Transport()
        self.sampler = ds.Sampler(self.root, self.world, self.transport)

    def test_four_frozen_candidates_world_verdicts_and_labeller_format(self):
        row = self.sampler.sample(context())
        self.assertEqual([c["seed"] for c in row["candidates"]], list(ds.SEEDS))
        self.assertEqual([c["accepted"] for c in row["candidates"]], [True, False, True, True])
        self.assertEqual(row["candidates"][1]["errors"], ["refused by world"])
        self.assertTrue(all(c["warnings"] == ["a recorded warning"] for c in row["candidates"]))
        self.assertTrue(row["candidates"][0]["raw"].startswith("  "))
        self.assertEqual(self.world.last_state, {"place": "home"})
        pairs, stats = decision_pairs.build([row])
        self.assertEqual(stats["pairs"], 1)
        self.assertEqual(pairs[0]["chosen_seed"], 1831)
        self.assertEqual(pairs[0]["rejected_seed"], 2718)
        for _, payload in self.transport.calls:
            self.assertEqual((payload["id_slot"], payload["model"], payload["temperature"]), (1, "qwen", .7))
            self.assertNotIn("lora", payload)
            self.assertEqual(payload["response_format"]["json_schema"]["schema"],
                             ds.decision_schema(context()["check"]["situation"]))

    def test_complete_row_reuses_all_four_without_new_sends(self):
        row = self.sampler.sample(context())
        self.transport.calls.clear()
        self.assertEqual(self.sampler.sample(context()), row)
        self.assertEqual(self.transport.calls, [])

    def test_unknown_stops_before_later_candidates_and_preserves_files(self):
        self.transport.fail_seed = 2718
        with self.assertRaises(TimeoutError):
            self.sampler.sample(context())
        self.assertEqual([p["seed"] for _, p in self.transport.calls], [1831, 2718])
        self.assertEqual(len(list(self.root.glob("*/candidate-*.json"))), 1)
        self.assertEqual(list(self.root.glob("*/ROW.json")), [])

    def test_completed_reply_after_crash_replayed_without_new_send(self):
        real_save = ds.save
        def fail_candidate(path, row):
            if Path(path).name == "candidate-2718.json":
                raise OSError("simulated crash after durable HTTP reply")
            return real_save(path, row)
        with patch.object(ds, "save", fail_candidate):
            with self.assertRaises(OSError):
                self.sampler.sample(context())
        self.assertEqual(len(self.transport.calls), 2)
        self.sampler.sample(context())
        self.assertEqual([p["seed"] for _, p in self.transport.calls], list(ds.SEEDS))

    def test_prompt_drift_refused_before_transport(self):
        self.sampler.sample(context())
        changed = context()
        changed["messages"][1]["content"] += " drift"
        with self.assertRaisesRegex(ValueError, "situation differs"):
            self.sampler.sample(changed)
        self.assertEqual(len(self.transport.calls), 4)

    def test_changed_candidate_or_torn_hash_refused(self):
        self.sampler.sample(context())
        p = next(self.root.glob("*/candidate-1831.json"))
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "record changed"):
            self.sampler.sample(context())
        self.assertEqual(len(self.transport.calls), 4)

    def test_partial_export_refused_and_full_export_preserves_raw(self):
        first = self.sampler.sample(context())
        out = self.root / "CANDIDATES.jsonl"
        with self.assertRaisesRegex(ValueError, "incomplete"):
            ds.export_rows(self.root, [first["id"], "shadow:35:2"], out)
        self.assertFalse(out.exists())
        result = ds.export_rows(self.root, [first["id"]], out)
        self.assertEqual(result["candidates"], 4)
        self.assertEqual(json.loads(out.read_bytes()), first)
        with self.assertRaises(FileExistsError):
            ds.export_rows(self.root, [first["id"]], out)

    def test_test_days_and_old_rehearsals_rejected(self):
        for day in (12, 27):
            with self.assertRaises(ValueError):
                context(day=day)
        with self.assertRaisesRegex(ValueError, "10 November"):
            context(source="rehearsal")
        self.assertEqual(context(source="rehearsal", when="2026-11-10")["date"], "2026-11-10")

    def test_schema_matches_actual_http_mind_and_keeps_extensions(self):
        sit=context()["check"]["situation"]
        called=[]
        mind=ds.HTTPMind.__new__(ds.HTTPMind)
        mind.chat_decision=lambda messages,schema: called.append(schema)
        mind.decide([],sit)
        self.assertEqual(ds.decision_schema(sit),called[0])
        extra={"type":"object","properties":{"payment":{"type":"string"}}}
        with patch.object(ds.contract,"decision_schema",return_value=extra,create=True):
            self.assertEqual(ds.decision_schema(sit),extra)

    def test_live_default_temperature_is_pinned(self):
        import inspect
        self.assertEqual(inspect.signature(ds.HTTPMind).parameters["temperature"].default,
                         ds.LIVE_TEMPERATURE)


class RehearsalAdapterTest(unittest.TestCase):
    def test_refusal_replay_and_frozen_count_never_add_candidates(self):
        from types import SimpleNamespace
        root = Path(tempfile.mkdtemp(prefix="decision-mind-test-"))
        checker = CheckWorld()
        checker.check = lambda answer,sit,ctx,state: (["refused"],[],None)
        transport = Transport()
        sampler = ds.Sampler(root,checker,transport)
        frozen = context(source="rehearsal",day=40,step=0,when="2026-11-10")
        sit,ctx,state = ds.restored_context(frozen["check"])
        world = SimpleNamespace(current_day=dict(n=40,date="2026-11-10",steps=[]),
                                current=(sit,ctx,state))
        mind = ds.CandidateMind(sampler,world,lambda *a,**k: None,limit=1)
        raw = mind.decide(frozen["messages"],sit)
        state["checker_normalized_state"] = True
        again = frozen["messages"] + [dict(role="assistant",content=raw),
                                      dict(role="user",content="world refuses")]
        self.assertEqual(mind.decide(again,sit),raw)
        self.assertEqual(len(transport.calls),4)
        world.current_day["steps"].append({"decision":None})
        with self.assertRaises(ds.DatasetComplete):
            mind.decide(frozen["messages"],sit)
        self.assertEqual(len(transport.calls),4)

    def test_held_related_rehearsal_advances_with_one_recorded_call(self):
        from types import SimpleNamespace
        from tests.test_decision_split import HELD
        root = Path(tempfile.mkdtemp(prefix="decision-held-test-"))
        transport = Transport()
        sampler = ds.Sampler(root,CheckWorld(),transport)
        frozen = context(source="rehearsal",day=40,step=0,when="2026-11-10")
        sit,ctx,state = ds.restored_context(frozen["check"])
        world = SimpleNamespace(current_day=dict(n=40,date="2026-11-10",steps=[]),current=(sit,ctx,state))
        messages = [frozen["messages"][0], dict(role="user",content="You remember:\n- Day 12, you thought: " + HELD + " and more.")]
        mind = ds.CandidateMind(sampler,world,lambda *a,**k: None,limit=1)
        raw = mind.decide(messages,sit)
        self.assertEqual([k for k,_ in transport.calls],["held/rehearsal:40:0/1831"])
        self.assertEqual(mind.completed_ids,set())
        self.assertFalse(list(root.glob("*/ROW.json")))
        record = ds.checked(next((root/"held-related").glob("*.json")))
        self.assertEqual((record["id"],record["training_eligible"],record["raw"]),("rehearsal:40:0",False,raw))
        again = messages + [dict(role="assistant",content=raw),dict(role="user",content="world refuses")]
        self.assertEqual(mind.decide(again,sit),raw)
        restarted = ds.CandidateMind(sampler,world,lambda *a,**k: None,limit=1)
        self.assertEqual(restarted.decide(messages,sit),raw)
        self.assertEqual(len(transport.calls),1)

    def test_published_roster_is_the_fixed_provenance_selection(self):
        from tools.decision_situations import PROVENANCE_EXCLUSIONS
        path = Path(ds.__file__).resolve().parents[1] / "pc/training3-shadow-ids.json"
        raw = path.read_bytes()
        ids = json.loads(raw)
        self.assertEqual(ds.digest(raw),"a7f6c59b8038d4fbf38f7e57aea6ddb6e5458f6db256ec82b1c7f872b407e264")
        self.assertEqual(len(ids),109)
        self.assertEqual(len(set(ids)),109)
        self.assertFalse(set(ids)&PROVENANCE_EXCLUSIONS)
        self.assertFalse(any(int(i.split(":")[1]) in (12,27,38) for i in ids))


if __name__ == "__main__":
    unittest.main()
