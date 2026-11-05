"""CPU-only launcher contracts. No GPU, Pi, model, or power mutation."""
import ast
import builtins
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from pc import run_training1 as r

XML = b"""<nvidia_smi_log><gpu><product_name>NVIDIA GeForce RTX 3090</product_name>
<fb_memory_usage><used>443 MiB</used></fb_memory_usage><processes>
<process_info><pid>100</pid><process_name>/usr/bin/python3</process_name><type>C</type></process_info>
</processes></gpu></nvidia_smi_log>"""
LINUX = [{"pid":100,"ppid":1,"name":"python3"}]
WINDOWS = [{"pid":12,"name":"dwm.exe"}]

def scratch():
    # Keep failures and successful fixture receipts for inspection.
    return Path(tempfile.mkdtemp(prefix="training1-launcher-test-"))

def fixture(root, dry=True):
    return dict(version=1, run_dir=str(root), source_dir=str(r.REPO), dry_run=dry,
                steps=3 if dry else 517, eval_steps=2 if dry else 100,
                base_model="/fixture/base", data_dir="/fixture/data", chapter_splits="/fixture/splits",
                confirmation_seal="/fixture/seal", legacy_trial="/fixture/trial",
                converter="/fixture/converter.py", converter_base="/fixture/metadata",
                python="/usr/bin/python3", power_state=str(root/"power.json"), power_receipt="/fixture/receipt",
                base_gguf="/fixture/base.gguf", commit="fixture", restore_by="2030-01-01T06:30:00Z",
                estimate=dict(step_seconds=20, evaluation_seconds=1260, phase_c_seconds=7200),
                original=dict(ld_library_path=""), linux_boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip())

class AdmissionTests(unittest.TestCase):
    def test_low_memory_generic_cuda_context_is_allowed(self):
        self.assertTrue(r.admission_decision(XML, LINUX, WINDOWS, 100)["allowed"])

    def test_llama_is_refused_in_each_inventory(self):
        for linux, windows, xml in [
            (LINUX+[{"name":"llama-server","pid":2}], WINDOWS, XML),
            (LINUX,WINDOWS+[{"name":"llama-server.exe","pid":2}],XML),
            (LINUX,WINDOWS,XML.replace(b"/usr/bin/python3",b"/bin/llama-server"))]:
            with self.subTest(linux=linux,windows=windows):
                self.assertFalse(r.admission_decision(xml,linux,windows)["allowed"])

    def test_strict_memory_boundary(self):
        for value, allowed in [(2047,True),(2048,False),(24576,False)]:
            self.assertEqual(r.admission_decision(XML.replace(b"443 MiB",str(value).encode()+b" MiB"),LINUX,WINDOWS)["allowed"],allowed)

    def test_malformed_snapshots_fail(self):
        for xml in (b"",b"<invalid/>",XML.replace(b"MiB",b"bad"),XML.replace(b"3090",b"4090")):
            with self.subTest(xml=xml),self.assertRaises((ValueError,ET.ParseError)):
                r.admission_decision(xml,LINUX,WINDOWS)

    def test_refusal_preserves_all_raw_inputs(self):
        root=scratch()/"admission"
        def run(argv,**kw):
            raw=XML.replace(b"443 MiB",b"24249 MiB") if "nvidia-smi" in argv[0] else (
                b"100 1 python3\n" if argv[0]=="ps" else b'"dwm.exe","12","Console","1","100 K"\r\n')
            return types.SimpleNamespace(stdout=raw,stderr=b"",returncode=0)
        with patch.object(r.subprocess,"run",side_effect=run),self.assertRaises(RuntimeError):
            r.gpu_admission(root)
        self.assertEqual((root/"gpu.stdout").read_bytes(),XML.replace(b"443 MiB",b"24249 MiB"))
        self.assertTrue((root/"linux.stdout").exists())
        self.assertTrue((root/"windows.stdout").exists())
        self.assertFalse(r.read(root/"ADMISSION.json")["allowed"])

    def test_imported_torch_refused_without_probe(self):
        with patch.dict(sys.modules,{"torch":types.ModuleType("torch")}),patch.object(r.subprocess,"run") as run:
            with self.assertRaises(RuntimeError):
                r.gpu_admission(scratch()/"admission")
            run.assert_not_called()

    def test_worker_requires_admission_before_unsloth(self):
        root=scratch();data=fixture(root);r.write_new(root/"INTENT.json",data)
        original=builtins.__import__
        reached=[]
        def importing(name,*a,**kw):
            if name in ("unsloth","torch"):
                reached.append(name)
                raise LookupError("import boundary")
            return original(name,*a,**kw)
        for allowed in (False,True):
            adm=dict(utc=r.utc(),allowed=allowed,before_ml_import=True)
            with patch.object(r,"read",return_value=adm),patch("builtins.__import__",side_effect=importing):
                with self.assertRaises(LookupError if allowed else RuntimeError):
                    r.train_worker(data,root/"INTENT.json",r.filehash(root/"INTENT.json"))
        self.assertEqual(reached,["unsloth"])

class IntentTests(unittest.TestCase):
    def test_every_output_uses_original_intent(self):
        root=scratch();data=fixture(root);r.write_new(root/"INTENT.json",data)
        loaded=r.load_intent(root/"INTENT.json",r.filehash(root/"INTENT.json"))
        self.assertEqual(r.intent_paths(loaded)["training"],root/"training")
        argv=r.training_argv(loaded)
        self.assertEqual(argv[argv.index("--out")+1],str(root/"training"))
        self.assertNotIn("--resume",argv)
        other=scratch();r.write_new(other/"INTENT.json",data)
        with self.assertRaises(ValueError):r.load_intent(other/"INTENT.json")

    def test_hash_and_schedule_drift_refused(self):
        root=scratch();data=fixture(root);r.write_new(root/"INTENT.json",data)
        with self.assertRaises(RuntimeError):r.load_intent(root/"INTENT.json","0"*64)
        data["eval_steps"]=3
        with patch.object(Path,"read_bytes",return_value=r.encoded(data)),self.assertRaises(ValueError):
            r.load_intent(root/"INTENT.json")

    def test_frozen_file_and_commit_must_match(self):
        root=scratch();f=root/"source";f.write_text("original")
        data=fixture(root);data["training_argv"]=r.training_argv(data)
        data["frozen_files"]={str(f):r.filehash(f)}
        with patch.object(r.subprocess,"check_output",return_value="fixture\n"):
            r.verify_intent(data)
            f.write_text("changed")
            with self.assertRaises(RuntimeError):r.verify_intent(data)

    def test_power_time_equivalent_formats_and_changed_request(self):
        root=scratch();data=fixture(root)
        state=dict(boot="2026-11-05T20:54:21.5Z",deadlineUtc="2030-01-01T07:30:00Z",lastRequestId="approved",pendingUtc=None)
        data["power"]=state.copy();r.write_new(root/"power.json",state)
        self.assertEqual(r.deadline(data),r.epoch(data["restore_by"])-1800)
        alternate=dict(state,boot="2026-11-05T21:54:21.500000+01:00")
        with patch.object(r,"read",return_value=alternate):self.assertEqual(r.deadline(data),r.epoch(data["restore_by"])-1800)
        with patch.object(r,"read",return_value=dict(state,lastRequestId="different")),self.assertRaises(RuntimeError):r.deadline(data)

    def test_real_run_requires_same_completed_passing_rehearsal(self):
        root=scratch();prior=fixture(root);prior["frozen_files"]={}
        r.write_new(root/"INTENT.json",prior)
        report=dict(passed=True,intent_sha256=r.filehash(root/"INTENT.json"),estimate=prior["estimate"])
        r.write_new(root/"REHEARSAL.json",report)
        r.write_new(root/"RUN-END.json",dict(status="B_AND_C_COMPLETE"))
        data=dict(prior,dry_run=False,passed_rehearsal=str(root/"REHEARSAL.json"),
                  passed_rehearsal_sha256=r.filehash(root/"REHEARSAL.json"))
        r.validate_rehearsal(data)
        with self.assertRaises(ValueError):r.validate_rehearsal(dict(data,commit="other"))
        with self.assertRaises(ValueError):r.validate_rehearsal(dict(data,estimate=dict(data["estimate"],step_seconds=1)))
        with self.assertRaises(ValueError):r.validate_rehearsal(dict(data,passed_rehearsal_sha256="wrong"))

class GuardTests(unittest.TestCase):
    def log(self):
        return [dict(event="step",step=i,seconds=20,unix=i*20) for i in range(1,101)]+[
            dict(event="evaluate_begin",step=100,unix=2001),
            dict(event="evaluate_end",step=100,unix=3261,seconds=1260)]

    def test_projection_counts_all_six_evaluations(self):
        self.assertEqual(r.projection(20,1260),180+517*20*1.15+6*1260*1.15)

    def test_post_eval_guard_allows_variation_but_stops_sustained_or_severe_slowdown(self):
        log=self.log()
        self.assertIsNone(r.guard_reason(log+[dict(event="step",step=101,seconds=45,unix=3300)],3300,100000,517,100,{}))
        sustained=log+[dict(event="step",step=i,seconds=31,unix=3300+i) for i in range(101,106)]
        self.assertIn("first five",r.guard_reason(sustained,3400,100000,517,100,{}))
        self.assertIn("3x",r.guard_reason(log+[dict(event="step",step=101,seconds=61,unix=3300)],3300,100000,517,100,{}))
        self.assertIn("while running",r.guard_reason(log+[dict(event="step_begin",step=101,unix=3300)],3361,100000,517,100,{}))

    def test_projection_stops_before_late_launch(self):
        self.assertIn("projected",r.guard_reason([],1000,1100,517,100,dict(step_seconds=20,evaluation_seconds=1260)))

    def test_partial_log_tail_never_becomes_a_step(self):
        root=scratch();p=root/"timing"
        p.write_bytes(b'{"event":"step","step":1}\n{"event":"step"')
        self.assertEqual(r.rows(p),[dict(event="step",step=1)])

class FailureTests(unittest.TestCase):
    def backend(self, fail=None,dry=False,fits=True):
        calls=[]
        class Backend:
            root=scratch()
            data=dict(dry_run=dry)
            def go(self,name):
                calls.append(name)
                if fail==name:raise RuntimeError("injected "+name)
            def handover(self):self.go("handover")
            def admission(self):self.go("admission")
            def phase_b(self):self.go("phase_b")
            def c_fits(self):self.go("c_fits");return fits
            def phase_c(self):self.go("phase_c")
            def sheets(self):self.go("sheets")
            def restore(self):self.go("restore");return dict(status="RESTORED")
        return Backend(),calls

    def test_failure_at_each_stage_restores_without_retry(self):
        for stage in ("handover","admission","phase_b","c_fits","phase_c","sheets"):
            b,calls=self.backend(stage)
            result=r.run_pipeline(b)
            self.assertEqual(result["status"],"FAILED")
            self.assertEqual(calls[-1],"restore")
            self.assertEqual(calls.count(stage),1)
            self.assertEqual(calls.count("restore"),1)

    def test_late_c_is_deferred_after_b_and_restored(self):
        b,calls=self.backend(fits=False)
        self.assertEqual(r.run_pipeline(b)["status"],"B_COMPLETE_C_DEFERRED")
        self.assertEqual(calls,["handover","admission","phase_b","c_fits","restore"])

    def test_late_restoration_never_claims_success(self):
        b,calls=self.backend()
        b.restore=lambda:dict(status="RESTORED",before_deadline=False)
        result=r.run_pipeline(b)
        self.assertEqual(result["status"],"FAILED")
        self.assertIn("deadline",result["error"])

    def test_restoration_failure_never_claims_completion(self):
        b,calls=self.backend("restore")
        self.assertEqual(r.run_pipeline(b)["status"],"RESTORATION_FAILED")

class OwnedProcessTests(unittest.TestCase):
    def backend(self):
        root=scratch()
        class B:
            paths=dict(children=root/"children")
            data=dict(source_dir=str(r.REPO),original=dict(ld_library_path=""),dry_run=False)
            children=[]
            def check_time(self,end=None):
                if end and time.time()>=end:raise TimeoutError()
        b=B();b.root=root
        return b

    def test_real_owned_child_tees_and_records_exit(self):
        b=self.backend()
        child=r.OwnedChild(b,"echo",["/usr/bin/python3","-B","-c","print('fixture output')"])
        child.wait(time.time()+10)
        self.assertEqual((child.root/"combined.log").read_bytes(),b"fixture output\n")
        self.assertEqual(r.read(child.root/"END.json")["returncode"],0)
        child.stop() # idempotent, no second signal

    def test_real_owned_pidfd_stop(self):
        b=self.backend()
        child=r.OwnedChild(b,"sleep",["/usr/bin/sleep","30"])
        self.assertIsNotNone(child.row)
        child.stop()
        self.assertEqual(r.read(child.root/"END.json")["returncode"],-15)

class HTTPTests(unittest.TestCase):
    def serve(self,wire):
        listener=socket.socket();listener.bind(("127.0.0.1",0));listener.listen()
        port=listener.getsockname()[1]
        def run():
            try:
                conn,_=listener.accept()
                with conn:
                    conn.recv(65536);conn.sendall(wire)
            finally:listener.close()
        t=threading.Thread(target=run);t.start()
        return port,t

    def test_complete_error_body_is_not_lost(self):
        p,t=self.serve(b"HTTP/1.1 503 Busy\r\nContent-Length: 4\r\nConnection: close\r\n\r\nbusy")
        self.assertEqual(r.http(p), (503,b"busy"));t.join()

    def test_truncated_reply_preserves_received_bytes(self):
        p,t=self.serve(b"HTTP/1.1 200 OK\r\nContent-Length: 9\r\nConnection: close\r\n\r\nabc")
        with self.assertRaises(r.PartialReply) as cm:r.http(p)
        self.assertEqual(cm.exception.partial,b"abc");t.join()

    def test_missing_framing_is_unknown(self):
        p,t=self.serve(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\nabc")
        with self.assertRaises(r.PartialReply):r.http(p)
        t.join()

class SourceTests(unittest.TestCase):
    def test_no_top_level_ml_imports_and_no_resume_or_phase0(self):
        tree=ast.parse(Path(r.__file__).read_text())
        imports=[]
        for n in tree.body:
            if isinstance(n,ast.Import):imports += [k.name for k in n.names]
            if isinstance(n,ast.ImportFrom):imports.append(n.module)
        self.assertFalse(any(n in ("torch","unsloth","transformers") for n in imports))
        self.assertNotIn("--resume",r.training_argv(fixture(scratch(),False)))
        self.assertNotIn("phase0",[n.name for n in tree.body if isinstance(n,ast.FunctionDef)])

    def test_pi_helper_is_syntax_valid_and_scoped(self):
        compile(r.PI_HELPER,"pi-helper","exec")
        self.assertNotIn("awake.flag",r.PI_HELPER)
        self.assertNotIn('"hegel-world.service"]',r.PI_HELPER)
        self.assertIn('"systemctl","--user","start","hegel-world.timer"',r.PI_HELPER)


class RehearsalCaseTests(unittest.TestCase):
    def test_two_cases_exercise_both_scales_and_diagnostics_without_rewriting_plan(self):
        from tools import hegel_test_round2 as t, voice_dashboard as v
        from world import contract
        dest=scratch();(dest/"private/inputs").mkdir(parents=True)
        (dest/"private/inputs/cast.json").write_text("[]")
        plan=dict(seed=10,cohort=[dict(id="a",plain="original a"),dict(id="b",plain="original b")],
                  cases=[dict(id="one"),dict(id="two")])
        frozen=r.encoded(plan)
        calls=[]
        class Guard:
            def matches(self,text):return []
        def client(folder,scale):
            calls.append((folder,scale))
            return types.SimpleNamespace(folder=folder,scale=scale)
        def restyler(c,g,plain,rid,seed):
            return dict(text=plain,attempts=[dict(raw=plain,finish_reason="stop")],fallback=False)
        with patch.object(t,"contract_answer",return_value='{"thought":"original"}'), \
             patch.object(t,"run_restyle",side_effect=restyler) as rewrite, \
             patch.object(t,"meaning_check",return_value=dict(format_valid=True)) as meaning, \
             patch.object(v,"meaning_propositions",return_value=dict(format_valid=True,added=[],omitted=[])) as props, \
             patch.object(v,"retention",return_value={}),patch.object(contract,"check",return_value=([],{})):
            report=r.rehearsal_cases(plan,Guard(),client,dest)
        self.assertEqual(r.encoded(plan),frozen)
        self.assertEqual(len(report["cases"]),2)
        self.assertEqual(rewrite.call_count,8)
        self.assertEqual(meaning.call_count,4)
        self.assertEqual(props.call_count,4)
        self.assertTrue(report["diagnostic_only"])
        for case in report["cases"]:
            self.assertEqual(set(case["scales"]),{"0.8","0.0"})

    def test_length_limited_rehearsal_answer_remains_recorded_data(self):
        from tools import hegel_test_round2 as t, voice_dashboard as v
        from world import contract
        dest=scratch();(dest/"private/inputs").mkdir(parents=True)
        (dest/"private/inputs/cast.json").write_text("[]")
        plan=dict(seed=10,cohort=[dict(id="a",plain="original")],cases=[dict(id="one")])
        with patch.object(t,"contract_answer",return_value="{}"),patch.object(t,"run_restyle",return_value=dict(
                text="partial",attempts=[dict(raw="partial",finish_reason="length")])), \
             patch.object(t,"meaning_check",return_value={}),patch.object(v,"meaning_propositions",return_value={}), \
             patch.object(v,"retention",return_value={}),patch.object(contract,"check",return_value=([],{})):
            result=r.rehearsal_cases(plan,types.SimpleNamespace(matches=lambda text:[]),lambda *a:None,dest)
        self.assertEqual(result["cases"][0]["scales"]["0.8"]["restyle"]["attempts"][0]["finish_reason"],"length")


class ReviewTests(unittest.TestCase):
    def test_shared_counter_failure_is_diagnostic(self):
        root=scratch();data=fixture(root);data["windows_pwsh"]="/fixture/pwsh"
        b=object.__new__(r.Backend);b.root=root;b.data=data;b.paths=r.intent_paths(data);b.last_sample=0
        with patch.object(r.subprocess,"check_output",return_value=XML),patch.object(r.subprocess,"run",side_effect=TimeoutError("counter unavailable")):
            b.sample_memory(force=True)
        row=r.rows(root/"telemetry/events.jsonl")[-1]
        self.assertEqual(row["used_mib"],443)
        self.assertIsNone(row["shared_bytes"])
        self.assertEqual(row["shared_status"],"unavailable")

    def test_weight_stat_mode_detects_change_and_hashes_small_files(self):
        root=scratch();weight=root/"weights.gguf";weight.write_bytes(b"fixture")
        small=root/"source.py";small.write_text("source")
        data=dict(weight_verification_mode="stat",weight_stats={str(weight):r.stat_identity(weight)})
        with patch.object(r,"filehash",side_effect=AssertionError("weight rehashed")):
            r.verify_frozen_file(data,str(weight),"preserved-hash")
        r.verify_frozen_file(data,str(small),r.filehash(small))
        with self.assertRaises(RuntimeError):r.verify_frozen_file(data,str(small),"wrong")
        weight.write_bytes(b"different")
        with self.assertRaises(RuntimeError):r.verify_frozen_file(data,str(weight),"preserved-hash")

    def test_freeze_times_weights_and_reuses_verified_stat_identity(self):
        root=scratch();p=root/"weights.gguf"
        # Sparse fixture is never read; the injected hasher supplies its fixture digest.
        with p.open("wb") as f:f.truncate(128*1024**2)
        data={}
        ticks=iter([0,0,181,182])
        with patch.object(r,"filehash",return_value="fixture-hash") as h,patch.object(r.time,"monotonic",side_effect=lambda:next(ticks)):
            r.freeze_inputs(data,[p])
            self.assertEqual(h.call_count,1)
        self.assertEqual(data["weight_verification_mode"],"stat")
        self.assertEqual(data["weight_hash_seconds"],181)
        second={}
        with patch.object(r,"filehash",side_effect=AssertionError("must reuse rehearsal hash")):
            r.freeze_inputs(second,[p],prior=data)
        self.assertEqual(second["frozen_files"],data["frozen_files"])

    def test_length_limited_held_generation_is_not_promoted_to_a_failure(self):
        tree=ast.parse(Path(r.__file__).read_text())
        worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="train_worker")
        fn=next(n for n in ast.walk(worker) if isinstance(n,ast.FunctionDef) and n.name=="recorded_generate")
        # Execute the actual nested recorder with the same closure, but a fake model/generator.
        wrapper=ast.FunctionDef(name="make_recorder",args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
            body=[ast.parse("call = 0").body[0],fn,ast.Return(value=ast.Name(id="recorded_generate",ctx=ast.Load()))],decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]))
        root=scratch();ns=dict(r.__dict__);ns.update(root=root,data={},path="fixture",expected="fixture",
            load_intent=lambda *a:None,deadline=lambda d:time.time()+9999,
            original_generate=lambda *a:dict(text="partial",finish_reason="length",generated_tokens=4))
        exec(compile(module,"recorder-fixture","exec"),ns)
        result=ns["make_recorder"]()(None,None,"plain",1,4,types.SimpleNamespace(cuda=types.SimpleNamespace(synchronize=lambda:None)))
        self.assertEqual(result["finish_reason"],"length")
        self.assertEqual(r.read(root/"held-generations/0001.response.json")["result"],result)

    def test_sighup_runs_finally_restoration_in_a_real_detached_process(self):
        root=scratch();data=fixture(root);r.write_new(root/"INTENT.json",data)
        code = """
import json,sys,time
from pathlib import Path
from pc import run_training1 as r
root=Path(sys.argv[1])
class Fake:
 def __init__(self,path):self.root=root;self.data=dict(dry_run=False)
 def handover(self):
  (root/'READY').write_text('ready')
  while True:time.sleep(.02)
 def restore(self):
  (root/'RESTORED').write_text('restored')
  return dict(status='RESTORED')
r.Backend=Fake
r.verify_intent=lambda data:None
raise SystemExit(r.main(['--intent',str(root/'INTENT.json')]))
"""
        with (root/"fake.log").open("wb") as output:
            child=subprocess.Popen(["/usr/bin/python3","-B","-c",code,str(root)],cwd=r.REPO,
                                   stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            fd=os.pidfd_open(child.pid)
            try:
                until=time.monotonic()+10
                while not (root/"READY").exists() and child.poll() is None and time.monotonic()<until:time.sleep(.02)
                self.assertTrue((root/"READY").exists(),(root/"fake.log").read_text())
                self.assertEqual(os.getsid(child.pid),child.pid)
                r.signal.pidfd_send_signal(fd,r.signal.SIGHUP)
                self.assertEqual(child.wait(timeout=10),1)
                self.assertTrue((root/"RESTORED").exists())
                ended=r.read(root/"RUN-END.json")
                self.assertEqual(ended["status"],"FAILED")
                self.assertEqual(ended["restoration"]["status"],"RESTORED")
            finally:
                if child.poll() is None:
                    r.signal.pidfd_send_signal(fd,r.signal.SIGTERM)
                    child.wait(timeout=10)
                os.close(fd)

    def test_detach_launches_once_with_null_input_and_a_new_session(self):
        root=scratch();data=fixture(root)
        with patch.object(r.subprocess,"Popen",return_value=types.SimpleNamespace(pid=999)) as popen, \
             patch.object(r,"identity",return_value=dict(pid=999)):
            self.assertEqual(r.detach_launcher(data,root/"INTENT.json","hash"),0)
            kwargs=popen.call_args.kwargs
            self.assertTrue(kwargs["start_new_session"])
            self.assertEqual(kwargs["stdin"],subprocess.DEVNULL)
            with self.assertRaises(RuntimeError):r.detach_launcher(data,root/"INTENT.json","hash")
        self.assertTrue(r.read(root/"DETACHED-PROCESS.json")["no_parent_death_signal"])

if __name__=="__main__":
    unittest.main(verbosity=2)
