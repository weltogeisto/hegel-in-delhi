import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pc import run_training3 as run
from pc import run_training1 as lifecycle
from world import contract


class LauncherTest(unittest.TestCase):
    def root(self):
        return Path(tempfile.mkdtemp(prefix="training3-launcher-test-"))

    def test_admission_uses_stdlib_child_before_ml_worker(self):
        backend = run.Backend.__new__(run.Backend)
        backend.data = {"python": "/fake/ml/python"}
        backend.path, backend.hash = Path("/fake/INTENT.json"), "abc"
        backend.check_time = lambda: time.time()+1000
        seen = []
        class Child:
            def __init__(self, backend, name, argv): seen.append((name,argv))
            def wait(self,end,training=False): seen.append(("wait",training))
        with patch.object(lifecycle,"OwnedChild",Child):
            backend.admission()
            backend.worker("train",time.time()+1000)
        self.assertEqual(seen[0][1][0],"/usr/bin/python3")
        self.assertEqual(seen[2][1][0],"/fake/ml/python")
        self.assertTrue(seen[0][1][2].endswith("run_training3.py"))
        self.assertEqual(seen[1],("wait",False))
        self.assertEqual(seen[3],("wait",True))

    def test_serve_checks_use_both_scales_and_candidate_schema_with_durable_chains(self):
        root = self.root()
        lifecycle.write_new(root/"ADAPTER-READY.json",{"identity":{"synthetic":True}})
        lifecycle.write_new(root/"TRAINING-ROSTER.json",{"ids":["shadow:35:1"]})
        messages=[dict(role="system",content="synthetic soul"),dict(role="user",content="synthetic situation")]
        schema=copy.deepcopy(contract.SCHEMA)
        schema["title"]="frozen candidate schema"
        candidates=root/"candidates.jsonl"
        candidates.write_text(json.dumps(dict(id="shadow:35:1",decision_schema=schema))+"\n")
        pair=dict(id="shadow:35:1",prompt=messages)
        data=dict(run_dir=str(root),candidates=str(candidates),pairs="fake",pair_stats="fake",
                  trial_port=19083,model_alias="qwen")
        answer=dict(thought="A synthetic test thought",action="stay",place="home",minutes=30,
                    says=None,buys=[],revision=None)
        captured=[]
        def http(port,path,payload,timeout):
            captured.append(json.loads(payload))
            return 200,json.dumps({"choices":[{"message":{"content":json.dumps(answer)}}]}).encode()
        with patch.object(run,"load",return_value=data), patch.object(lifecycle,"deadline",return_value=time.time()+1000), \
             patch.object(lifecycle,"same_process",return_value=True), patch.object(lifecycle,"http",side_effect=http), \
             patch.object(run.preparation,"validated_pairs",return_value=([pair],{})):
            run.serve_checks(data,root/"INTENT.json","synthetic")
        self.assertEqual([r["lora"][0]["scale"] for r in captured],[1,0])
        self.assertTrue(all(r["id_slot"]==1 and r["model"]=="qwen" for r in captured))
        self.assertTrue(all(r["response_format"]["json_schema"]["schema"]==schema for r in captured))
        self.assertEqual(len(list((root/"benchmark").rglob("*.done.json"))),2)
        self.assertTrue(lifecycle.read(root/"PHASE-C-END.json")["quality_test_pending"])

    def test_unknown_serve_response_stops_before_second_scale(self):
        root=self.root()
        lifecycle.write_new(root/"ADAPTER-READY.json",{"identity":{}})
        lifecycle.write_new(root/"TRAINING-ROSTER.json",{"ids":["shadow:35:1"]})
        c=root/"candidates.jsonl"
        c.write_text(json.dumps(dict(id="shadow:35:1",decision_schema=contract.SCHEMA))+"\n")
        data=dict(run_dir=str(root),candidates=str(c),pairs="fake",pair_stats="fake",trial_port=19083,model_alias="qwen")
        pair=dict(id="shadow:35:1",prompt=[])
        with patch.object(run,"load",return_value=data),patch.object(lifecycle,"deadline",return_value=time.time()+1000), \
             patch.object(lifecycle,"same_process",return_value=True),patch.object(lifecycle,"http",side_effect=TimeoutError("unknown")) as http, \
             patch.object(run.preparation,"validated_pairs",return_value=([pair],{})):
            with self.assertRaises(Exception):
                run.serve_checks(data,root/"INTENT.json","synthetic")
        self.assertEqual(http.call_count,1)
        self.assertTrue((root/"unknown/1.json").exists())
        self.assertFalse((root/"PHASE-C-END.json").exists())

    def test_inherited_pipeline_restores_after_each_training3_failure(self):
        for stage in ("handover","admission","phase_b","phase_c","sheets"):
            calls=[]
            class Backend:
                data={"dry_run":False}
                def handover(self): self.stage("handover")
                def admission(self): self.stage("admission")
                def phase_b(self): self.stage("phase_b")
                def phase_c(self): self.stage("phase_c")
                def sheets(self): self.stage("sheets")
                def c_fits(self): return True
                def restore(self):
                    calls.append("restore")
                    return {"status":"ORIGINAL_QWEN_AND_TIMER_RESTORED","before_deadline":True}
                def stage(self,name):
                    calls.append(name)
                    if name==stage: raise RuntimeError("injected failure")
            outcome=lifecycle.run_pipeline(Backend())
            self.assertEqual(outcome["status"],"FAILED")
            self.assertEqual(calls[-1],"restore")
            self.assertEqual(calls.count("restore"),1)

    def test_rehearsal_verdict_requires_both_actual_scales_and_memory_gate(self):
        root=self.root()
        lifecycle.write_new(root/"INTENT.json",{"synthetic":True})
        lifecycle.write_new(root/"training/training.json",dict(pairs=200,reference_seconds=100,loaded_seconds=50))
        lifecycle.write_new(root/"RESTORATION.json",{"synthetic":True})
        lifecycle.write_new(root/"PHASE-C-END.json",dict(status="TWO_DECISION_SERVE_CHECKS",cases=[{"scale":1},{"scale":0}]))
        lifecycle.write_new(root/"DPO-C-TIMING.json",dict(seconds=120))
        log=[dict(event="step",step=n,seconds=s,peak_reserved=23*1024**3)
             for n,s in ((1,15),(2,10),(3,11))]
        log.append(dict(event="evaluate_end",seconds=20))
        (root/"timing.jsonl").write_text("".join(json.dumps(x)+"\n" for x in log))
        result=dict(restoration=dict(status="ORIGINAL_QWEN_AND_TIMER_RESTORED",
                                     pi_probe={"status":"PI_HEALTH_AND_ONE_TOKEN_VERIFIED"}))
        data=dict(run_dir=str(root),estimate={"phase_c_seconds":600})
        report=run.verdict(data,result)
        self.assertTrue(report["passed"])
        self.assertEqual(report["measured"]["conversion_and_test_seconds"],138.0)
        # A distinct synthetic modified snapshot, not an actual run record.
        log[0]["peak_reserved"]=24*1024**3
        (root/"timing.jsonl").write_text("".join(json.dumps(x)+"\n" for x in log))
        self.assertFalse(run.verdict(data,result)["passed"])


class RehearsedInputsTest(unittest.TestCase):
    """A real run may reuse a rehearsal only for the same bytes at the same paths."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="training3-rehearsed-"))
        files = dict(candidates="candidates.jsonl", pairs="pairs.jsonl", pair_stats="pairs.stats.json",
                     converter="convert/convert_lora.py", base_gguf="base.gguf")
        self.config = {key: str(self.dir / name) for key, name in files.items()}
        self.config.update(base_model=str(self.dir / "base"), converter_base=str(self.dir / "converter-base"),
                           original=dict(launcher=str(self.dir / "serve.sh")))
        for name in list(files.values()) + ["serve.sh", "base/tokenizer_config.json", "converter-base/config.json"]:
            path = self.dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original " + name)

    def frozen(self):
        data = dict(self.config)
        paths = [Path(self.config[k]) for k in run.REHEARSED_FILES] + [Path(self.config["original"]["launcher"])]
        for key in run.REHEARSED_TREES:
            paths += [p for p in Path(self.config[key]).rglob("*") if p.is_file()]
        lifecycle.freeze_inputs(data, paths)
        data["pair_provenance"] = dict(candidates_sha256=lifecycle.filehash(self.config["candidates"]),
                                       pairs_sha256=lifecycle.filehash(self.config["pairs"]))
        return data

    def test_unchanged_bytes_are_accepted(self):
        rehearsal = self.frozen()
        run.same_as_rehearsal(rehearsal, self.frozen())

    def test_changed_candidate_or_pair_data_at_unchanged_paths_is_refused(self):
        for key in ("candidates", "pairs", "pair_stats"):
            with self.subTest(key=key):
                self.setUp()
                rehearsal = self.frozen()
                Path(self.config[key]).write_text("rewritten in place")       # same path, new bytes
                with self.assertRaisesRegex(ValueError, "changed"):
                    run.same_as_rehearsal(rehearsal, self.frozen())

    def test_changed_tokenizer_or_converter_is_refused(self):
        for name in ("base/tokenizer_config.json", "convert/convert_lora.py"):
            with self.subTest(name=name):
                self.setUp()
                rehearsal = self.frozen()
                (self.dir / name).write_text("a different template")
                with self.assertRaisesRegex(ValueError, "same paths"):
                    run.same_as_rehearsal(rehearsal, self.frozen())


class NaturalRestorationTest(unittest.TestCase):
    def evidence(self, source="mind", stamp=100, mutate=False):
        before={"steps":[{"t":"09:00","decision":{"thought":"old"},"mind":{"source":"away"}}]}
        after=copy.deepcopy(before)
        if mutate: after["steps"][0]["decision"]["thought"]="changed"
        after["steps"].append(dict(t="09:31",decision={"thought":"new"},mind={"source":source,"latency_s":9.1}))
        def output(argv,**kwargs):
            args=argv[3:]
            if args[0]=="rev-list":return b"child base\n"
            if args[:3]==["show","-s","--format=%ct"]:return str(stamp).encode()
            if args[0]=="diff":return b"docs/days/2026-11-08.json\n"
            if args[0]=="show":return json.dumps(after).encode()
            raise AssertionError(args)
        def completed(argv,**kwargs):
            return type("Result",(),dict(returncode=0,stdout=json.dumps(before).encode()))()
        return output,completed

    def test_requires_a_real_append_after_restoration(self):
        output,completed=self.evidence()
        with patch.object(run,"shadow_head",return_value="child"),patch.object(run.subprocess,"check_output",side_effect=output),patch.object(run.subprocess,"run",side_effect=completed):
            proof=run.natural_restoration("/fake/native","base","1970-01-01T00:01:00+00:00")
        self.assertEqual(proof["commit"],"child")
        self.assertEqual(proof["mind"]["source"],"mind")
        self.assertTrue(proof["no_forced_tick"])

    def test_old_commit_away_and_changed_history_do_not_prove_restoration(self):
        for options in (dict(stamp=50),dict(source="away"),dict(mutate=True)):
            output,completed=self.evidence(**options)
            with patch.object(run,"shadow_head",return_value="child"),patch.object(run.subprocess,"check_output",side_effect=output),patch.object(run.subprocess,"run",side_effect=completed):
                with self.assertRaises(RuntimeError):
                    run.natural_restoration("/fake/native","base","1970-01-01T00:01:00+00:00")


if __name__=="__main__":
    unittest.main()
