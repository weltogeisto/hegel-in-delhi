import contextlib
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tools import hegelizer_exclusive as ex
from tools import hegelizer_round2 as r2
from tools.recorded_llama import RecordedClient, json_bytes, UnknownRequest, TransportError

def unit(i):
    return dict(id="work:"+str(i), parent_id="work:"+str(i), work="work", ref=str(i),
                original=" ".join("old"+str(j) for j in range(80))+".",
                split="train", kind="full", recipe=4)

def answer(tag):
    return " ".join(["old"+str(i) for i in reversed(range(30))]+[tag+str(i) for i in range(50)])+"."

def row(i,ok):
    return dict(unit(i),accepted=ok,versions=[dict(variant=1,plain=answer("a") if ok else None),
                                            dict(variant=2,plain=answer("b") if ok else None)])

class Reply:
    status=200
    def __init__(self,raw):self.raw=raw
    def read(self):return self.raw
    def __enter__(self):return self
    def __exit__(self,*a):pass

def response(text):
    return json_bytes({"choices":[{"message":{"content":text},"finish_reason":"stop"}]})

class ExclusiveTests(unittest.TestCase):
    def test_legacy_payload_replay_never_sends_and_refuses_drift(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); payload={"value":"original"}
            old=RecordedClient("http://old.example",p/"old",opener=lambda *a,**k:Reply(b'{"saved":1}'))
            old.post("case",payload)
            client=ex.ExclusiveClient(p/"new",p/"old","http://old.example",ex.deny,time.time()+1000)
            self.assertEqual(client.post("case",payload),{"saved":1})
            self.assertFalse((p/"new").exists())
            self.assertEqual(len(ex.reconcile_raw(p/"old")),1)
            with self.assertRaises(ValueError):client.post("case",{"value":"edited"})

    def test_new_record_uses_automatic_slots_and_replays_exactly(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); sent=[]
            def sender(raw,timeout):
                sent.append(json.loads(raw));return 200,b'{"ok":true}'
            client=ex.ExclusiveClient(p/"raw",p/"old","http://old",sender,time.time()+1000)
            self.assertEqual(client.post("new",{"model":"qwen"}),{"ok":True})
            self.assertEqual(client.post("new",{"model":"qwen"}),{"ok":True})
            self.assertEqual(sent,[{"model":"qwen"}])
            self.assertEqual(len(ex.reconcile_raw(p/"raw")),1)

    def test_unknown_is_preserved_and_blocks_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            def partial(*a):raise ex.PartialReply(b"partial","timeout")
            client=ex.ExclusiveClient(p/"raw",p/"old","http://old",partial,time.time()+1000)
            with self.assertRaises(ex.PartialReply):client.post("new",{})
            self.assertEqual(next((p/"raw").glob("*.partial.bin")).read_bytes(),b"partial")
            with self.assertRaises(UnknownRequest):ex.reconcile_raw(p/"raw")
            with self.assertRaises(UnknownRequest):client.post("new",{})
            self.assertFalse(list((p/"raw").glob("*.done.json")))

    def test_cutoff_prevents_transmission_without_begin(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); client=ex.ExclusiveClient(p/"raw",p/"old","http://old",ex.deny,1300,clock=lambda:1000)
            with self.assertRaises(ex.Cutoff):client.post("case",{})
            self.assertFalse((p/"raw").exists())

    def test_four_actual_recipe_workers_skip_all_completed_units(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); data=p/"data";data.mkdir()
            (data/r2.UNITS).write_bytes(b"".join(json_bytes(unit(i)) for i in range(6)))
            (data/r2.DONE).write_bytes(json_bytes(row(0,True)))
            (data/r2.FAILED).write_bytes(json_bytes(row(1,False)))
            initial_good=(data/r2.DONE).read_bytes(); initial_bad=(data/r2.FAILED).read_bytes()
            barrier=threading.Barrier(4); lock=threading.Lock()
            active=0;peak=0;calls=[]
            def sender(raw,timeout):
                nonlocal active,peak
                payload=json.loads(raw)
                with lock:
                    calls.append(payload); active+=1;peak=max(peak,active)
                    ordinal=len(calls)
                if ordinal<=4:barrier.wait(timeout=3)
                time.sleep(.01)
                with lock:active-=1
                return 200,response(answer("seed"+str(payload["seed"])+"x"))
            client=ex.ExclusiveClient(p/"raw",p/"old","http://old",sender,time.time()+1000)
            with contextlib.redirect_stdout(io.StringIO()):gate=ex.continue_units(data,client,4)
            self.assertEqual(peak,4)
            self.assertEqual(len(calls),8)
            self.assertEqual(gate["pending_units"],0)
            self.assertEqual(gate["failed_units"],1)
            self.assertTrue((data/r2.DONE).read_bytes().startswith(initial_good))
            self.assertEqual((data/r2.FAILED).read_bytes(),initial_bad)
            self.assertEqual(len(ex.reconcile_raw(p/"raw")),8)
            self.assertTrue(all("id_slot" not in x for x in calls))

    def test_http_short_body_and_deadline_do_not_return_success(self):
        class Handler(BaseHTTPRequestHandler):
            mode="short"
            def log_message(self,*a):pass
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200);self.send_header("Content-Length","100");self.end_headers()
                self.wfile.write(b"x");self.wfile.flush()
                if self.mode=="slow":time.sleep(.3)
                self.close_connection=True
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            send=ex.BoundedHTTP(lambda:True,server.server_port)
            with self.assertRaises(ex.PartialReply):send(b"{}",1)
            Handler.mode="slow";started=time.monotonic()
            with self.assertRaises(ex.PartialReply):send(b"{}",.05)
            self.assertLess(time.monotonic()-started,.25)
        finally:server.shutdown();server.server_close();thread.join()

    def test_http_identity_failure_sends_nothing(self):
        with self.assertRaises(ex.PartialReply),mock.patch.object(ex.http.client,"HTTPConnection",side_effect=AssertionError("must not connect")):
            ex.BoundedHTTP(lambda:False)(b"{}",1)

    def test_reconcile_rejects_orphan_and_tampered_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);p.joinpath("orphan.done.json").write_text("{}")
            with self.assertRaises(ValueError):ex.reconcile_raw(p)

class OwnedLifecycleTest(unittest.TestCase):
    def test_owned_fake_server_readiness_and_confirmed_exit(self):
        import os, socket, sys
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            with socket.socket() as s:
                s.bind(("127.0.0.1",0)); port=s.getsockname()[1]
            source=p/"fake_server.py"
            source.write_text("""from http.server import BaseHTTPRequestHandler,HTTPServer
import json,sys
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  values={'/health':{'status':'ok'},'/slots':[{'n_ctx':16384,'is_processing':False} for _ in range(4)],'/props':{'lora_adapters':[]}}
  raw=json.dumps(values[self.path]).encode()
  self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
HTTPServer(('127.0.0.1',int(sys.argv[1])),Handler).serve_forever()
""")
            server=ex.OwnedServer(p,[sys.executable,str(source),str(port)],os.environ.copy(),port=port)
            try:
                with mock.patch.object(ex,"verify_gpu",return_value=b"<synthetic/>"):server.start()
                self.assertTrue(server.identity())
                self.assertTrue((p/"SERVER-READY.json").is_file())
            finally:
                end=server.stop()
            self.assertTrue(end["exit_confirmed"])
            self.assertFalse(server.identity())

class DeadlinePolicyTest(unittest.TestCase):
    def test_extension_requires_exact_verified_receipt_and_never_exceeds_ceiling(self):
        import datetime as dt
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); state=p/"state.json"; result=p/"result.json"
            def at(h):return "2030-01-01T"+str(h).zfill(2)+":00:00+00:00"
            plan=dict(power_state=str(state),power_result=str(result),power_boot="boot",
                      initial_power_deadline=at(12),authorized_power_deadline=at(20),
                      shutdown_reserve_s=900,stop_utc=at(19))
            s=dict(boot="boot",deadlineUtc=at(12),pendingUtc=None,lastRequestId="")
            state.write_text(json.dumps(s)); policy=ex.DeadlinePolicy(plan)
            self.assertEqual(policy(),dt.datetime.fromisoformat(at(12)).timestamp()-900)
            s.update(deadlineUtc=at(20),lastRequestId="request");state.write_text(json.dumps(s))
            self.assertEqual(policy(),dt.datetime.fromisoformat(at(12)).timestamp()-900)
            result.write_text(json.dumps(dict(status="VERIFIED",state=s,requested_deadline=at(20))))
            self.assertEqual(policy(),dt.datetime.fromisoformat(at(19)).timestamp())
            s["pendingUtc"]=at(11);state.write_text(json.dumps(s))
            with self.assertRaises(ex.Cutoff):policy()

    def test_boot_change_cannot_renew_a_running_job(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"state.json";p.write_text(json.dumps(dict(boot="new",pendingUtc=None)))
            with self.assertRaises(ex.Cutoff):
                ex.DeadlinePolicy(dict(power_state=str(p),power_boot="old"))()
