import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import decision_sampling as api
from tools.decision_sampler import digest, json_bytes


class SupportAndHistoryTest(unittest.TestCase):
    def test_support_calls_use_same_guard_and_exact_key(self):
        seen = []
        def post(key, payload):
            seen.append((key, payload))
            return {"choices":[{"message":{"content":"saved support"}}]}, {"response_sha256":"a"*64}
        world = SimpleNamespace(current_day={"n":40,"steps":[]})
        aux = api.Auxiliary(world, post)
        self.assertEqual(aux([{"role":"user","content":"question"}]), "saved support")
        aux([{"role":"user","content":"question"}])
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(seen[0][1]["id_slot"],1)
        self.assertTrue(seen[0][0].startswith("support/40/0/"))
        def unknown(*a):
            raise RuntimeError("unknown; no resend")
        with self.assertRaisesRegex(RuntimeError,"unknown"):
            api.Auxiliary(world, unknown)([{"role":"user","content":"q"}])

    def test_all_rehearsal_versions_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            days=api.PreservedDays(Path(tmp))
            day={"date":"2026-11-10","n":41,"title":"Synthetic","state":{},"steps":[]}
            # The real Days.save/refresh path, no model.
            days.save(day)
            before=days.path(day["date"]).read_bytes()
            day["title"]="Later";days.save(day)
            after=days.path(day["date"]).read_bytes()
            self.assertNotEqual(before,after)
            self.assertEqual((days.history/(digest(before)+".json")).read_bytes(),before)
            self.assertEqual((days.history/(digest(after)+".json")).read_bytes(),after)

    def test_refuses_a_t39_arm_as_the_candidate_source(self):
        for arm in (dict(echo_guard=True), dict(decision_dry=0.8), dict(decision_draws=4)):
            cfg=SimpleNamespace(repo=Path("/repo"),docs=Path("/scratch/docs"),push=False,feeds=False,**arm)
            with self.assertRaisesRegex(ValueError,"plain Qwen"):
                api.rehearse(cfg,Path("/none"),lambda *a:self.fail("request"))

    def test_refuses_live_docs_before_engine_or_transport(self):
        cfg=SimpleNamespace(repo=Path("/repo"),docs=Path("/repo/docs"),push=False,feeds=False)
        with self.assertRaisesRegex(ValueError,"isolated"):
            api.rehearse(cfg,Path("/none"),lambda *a:self.fail("request"))

    def test_dataset_exports_only_complete_shadow_and_fresh_rosters(self):
        with patch.object(api,"sample_shadow",return_value=["shadow:1:1"]) as a, \
             patch.object(api,"rehearse",return_value=["rehearsal:41:1"]) as b, \
             patch.object(api,"export_rows",return_value={"situations":500}) as export:
            value=api.run_dataset("freeze","records",object(),lambda *a:None,"out")
            self.assertEqual(value,{"situations":500})
            self.assertEqual(export.call_args.args[1],["shadow:1:1","rehearsal:41:1"])
            self.assertEqual(b.call_args.kwargs["target"],499)          # 500 less the eligible shadow
        with patch.object(api,"sample_shadow",side_effect=RuntimeError("partial")), \
             patch.object(api,"rehearse") as b:
            with self.assertRaisesRegex(RuntimeError,"partial"):
                api.run_dataset("freeze","records",object(),lambda *a:None,"out")
            b.assert_not_called()

class HeldShadowTest(unittest.TestCase):
    def freeze(self, held_at):
        from tests.test_decision_split import HELD
        from tools.decision_sampler import save
        root = Path(tempfile.mkdtemp(prefix="held-shadow-test-"))
        ids, rows = [], []
        for i in range(109):
            ident = f"shadow:35:{i}"
            user = ("You remember: " + HELD) if i in held_at else f"Situation {i}, nothing remembered."
            row = dict(id=ident, source="shadow", messages=[dict(role="system",content="soul"),dict(role="user",content=user)])
            name = digest(ident.encode()) + ".json"
            save(root/"situations"/name, row)
            ids.append(ident)
            rows.append(dict(id=ident, path="situations/"+name, sha256=digest(json_bytes(row))))
        (root/"SHADOW-IDS.json").write_bytes(json_bytes(ids))
        roster = digest(json_bytes(ids))
        save(root/"MANIFEST.json", dict(situations=109, roster_sha256=roster, rows=rows))
        return root, roster, [ids[i] for i in sorted(held_at)]

    def test_held_related_shadow_is_never_sampled_and_must_match_the_frozen_list(self):
        root, roster, held = self.freeze({3, 50})
        sampled = []
        sampler = SimpleNamespace(sample=lambda row: sampled.append(row["id"]))
        with patch.object(api,"ROSTER_SHA256",roster), patch.object(api,"frozen_shadow_exclusions",return_value=tuple(held)):
            eligible = api.sample_shadow(root, sampler)
        self.assertEqual(len(eligible), 107)
        self.assertEqual(sampled, eligible)
        self.assertFalse(set(held) & set(sampled))
        with patch.object(api,"ROSTER_SHA256",roster), patch.object(api,"frozen_shadow_exclusions",return_value=(held[0],)):
            with self.assertRaisesRegex(ValueError,"frozen training3-split-1"):
                api.sample_shadow(root, SimpleNamespace(sample=lambda row: None))


class ActualRehearsalLoopTest(unittest.TestCase):
    def test_real_engine_with_fake_guard_preserves_prefix_and_four_seeds(self):
        import shutil
        from world.mind import StubMind
        from world.engine import Days
        from tools.decision_sampler import CandidateWorld, checked
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);docs=root/"rehearsal";(docs/"days").mkdir(parents=True)
            raw=(repo/"docs/days/2026-10-02.json").read_bytes()
            (docs/"days/2026-10-02.json").write_bytes(raw)
            old=json.loads(raw)
            (docs/"days/index.json").write_text(json.dumps({"format":1,"days":[
                {k:old.get(k) for k in ("date","n","title","holiday")}]}))
            cfg=SimpleNamespace(repo=repo,docs=docs,state=root/"state",push=False,feeds=False,
                news_feeds=[],soul_file=repo/"mind/soul.md",shelf=False,write_mode="chat",
                lead=15,owl_at="09:10",depesche_day="Saturday",clock_shift_min=0)
            world=CandidateWorld()
            fake=StubMind()
            seen=[]
            def post(key,payload):
                seen.append((key,copy.deepcopy(payload)))
                schema=payload.get("response_format",{}).get("json_schema",{}).get("schema")
                if key.startswith("decision/"):
                    raw=fake.decide(payload["messages"],world.current[0])
                else:
                    raw=fake.chat(payload["messages"],schema=schema,max_tokens=payload["max_tokens"])
                return {"choices":[{"message":{"content":raw},"finish_reason":"stop"}]},{
                    "response_sha256":digest(raw.encode())}
            with patch.object(api,"REHEARSAL_SITUATIONS",2):
                ids=api.rehearse(cfg,root/"records",post,max_days=1,
                                 world_type=lambda feeds:world)
            rows=[checked(p) for p in (root/"records").glob("*/ROW.json")]
            self.assertEqual(len(ids),2)
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r["date"]=="2026-11-10" for r in rows))
            self.assertEqual(len([k for k,p in seen if k.startswith("decision/")]),8)
            self.assertTrue(all(p["id_slot"]==1 for k,p in seen))
            self.assertEqual((repo/"docs/days/2026-10-02.json").read_bytes(),raw)
            self.assertTrue(list((docs/"versions").glob("*.json")))
            self.assertEqual(sorted(len(r["earlier_thoughts"]) for r in rows),[0,1])
            with patch.object(api,"REHEARSAL_SITUATIONS",2):
                again=api.rehearse(cfg,root/"records",lambda *a:self.fail("already complete"),max_days=1,world_type=lambda feeds:world)
            self.assertEqual(again,ids)
