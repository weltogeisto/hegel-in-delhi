"""Reviewed, single-intent Training 1 launcher.

No ML import occurs in the launcher. Workers read the same immutable INTENT.json.
The real run has no resume, restart supervisor, or automatic retry. Rehearsal is
three steps with evaluation at two and at the terminal step, then two C cases.
"""
import argparse
import base64
import contextlib
import csv
import ctypes
from datetime import datetime, timezone
import fcntl
import hashlib
import http.client as http_client
import io
import json
import math
import os
from pathlib import Path
import select
import selectors
import shlex
import signal
import socket
import statistics
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
RESTORE_RESERVE = 1800
HTTP_TIMEOUT = 300
INTENT_VERSION = 1


def utc():
    return datetime.now(timezone.utc).isoformat()


def epoch(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def filehash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, value, raw=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value if raw else encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def event(root, name, **fields):
    path = Path(root) / "events.jsonl"
    with path.open("ab") as stream:
        stream.write((json.dumps(dict(event=name, utc=utc(), unix=time.time(), **fields), sort_keys=True) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def rows(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    lines = raw.splitlines()
    if raw and not raw.endswith(b"\n"):
        lines = lines[:-1]
    return [json.loads(line) for line in lines if line.strip()]


def intent_paths(intent):
    root = Path(intent["run_dir"])
    # This is the only output-path derivation, used by every process and check.
    return {name: root / name for name in ("training", "benchmark", "converted", "children", "telemetry", "sheets")}


def load_intent(path, expected=None):
    path = Path(path).resolve()
    raw = path.read_bytes()
    if expected and digest(raw) != expected:
        raise RuntimeError("intent changed")
    data = json.loads(raw)
    if data.get("version") != INTENT_VERSION or path != Path(data["run_dir"]) / "INTENT.json":
        raise ValueError("intent must remain at its original path")
    if data["steps"] != (3 if data["dry_run"] else 517) or data["eval_steps"] != (2 if data["dry_run"] else 100):
        raise ValueError("unreviewed training schedule")
    for name in ("source_dir", "base_model", "data_dir", "chapter_splits", "confirmation_seal",
                 "legacy_trial", "converter", "converter_base", "python", "power_state", "power_receipt"):
        if not Path(data[name]).is_absolute():
            raise ValueError("absolute intent path required: " + name)
    if Path(data["source_dir"]).resolve() != REPO:
        raise ValueError("worker source does not match the intent")
    return data


def create_intent(config, destination, deadline, dry_run=False, eval_steps=None):
    """CPU preparation only. Configuration arrives on stdin, never as a copied intent."""
    root = Path(destination).resolve()
    if root.exists():
        raise FileExistsError("new output directory required")
    if eval_steps not in (None, 2 if dry_run else 100):
        raise ValueError("eval interval differs from the runbook")
    if epoch(deadline) <= time.time() + RESTORE_RESERVE:
        raise ValueError("restoration deadline too close")
    data = dict(config, version=INTENT_VERSION, run_dir=str(root), source_dir=str(REPO),
                restore_by=deadline, dry_run=bool(dry_run), steps=3 if dry_run else 517,
                eval_steps=2 if dry_run else 100, written_utc=utc(), phase_b_cap_s=25200,
                no_restarts=True, no_automatic_adoption=True)
    data["commit"] = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain"]):
        raise RuntimeError("reviewed source checkout must be clean")
    tracked = subprocess.check_output(["git", "-C", str(REPO), "ls-files", "-z"]).decode().split("\0")
    files = [REPO / n for n in tracked if n]
    files += [Path(data["data_dir"]) / n for n in ("hegelizer2-units.jsonl", "hegelizer2.jsonl", "hegelizer2-failed.jsonl")]
    files += [Path(data[k]) for k in ("chapter_splits", "confirmation_seal", "converter", "power_receipt")]
    files += [Path(data["original"]["launcher"]), Path(data["base_gguf"])]
    for key in ("base_model", "converter_base", "legacy_trial"):
        files += [p for p in Path(data[key]).rglob("*") if p.is_file()]
    files += [p for p in Path(data["converter"]).parent.rglob("*.py") if ".git" not in p.parts]
    if not dry_run:
        proof = Path(data["passed_rehearsal"])
        files += [proof, proof.parent / "INTENT.json", proof.parent / "RUN-END.json"]
        validate_rehearsal(data)
    if any(root == p.resolve() or root in p.resolve().parents for p in files):
        raise ValueError("output overlaps a frozen input")
    data["frozen_files"] = {str(p): filehash(p) for p in files}
    data["power"] = read(data["power_state"])
    if data["power"].get("pendingUtc"):
        raise RuntimeError("pending shutdown")
    receipt = read(data["power_receipt"])
    if receipt.get("status") != "VERIFIED" or receipt["state"]["lastRequestId"] != data["power"]["lastRequestId"]:
        raise RuntimeError("power deadline lacks the approved receipt")
    if epoch(data["power"]["deadlineUtc"]) < epoch(deadline) + 900:
        raise ValueError("power cutoff leaves insufficient restoration margin")
    data["linux_boot"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    data["training_argv"] = training_argv(data)
    root.mkdir()
    write_new(root / "INTENT.json", data)
    load_intent(root / "INTENT.json")
    return root / "INTENT.json"


def validate_rehearsal(data):
    proof = Path(data["passed_rehearsal"])
    if proof.name != "REHEARSAL.json" or filehash(proof) != data["passed_rehearsal_sha256"]:
        raise ValueError("passed rehearsal receipt changed")
    result = read(proof)
    prior_path = proof.parent / "INTENT.json"
    prior = load_intent(prior_path)
    ended = read(proof.parent / "RUN-END.json")
    if not result.get("passed") or ended.get("status") != "B_AND_C_COMPLETE":
        raise ValueError("real run needs a completed passing rehearsal")
    if not prior["dry_run"] or result.get("intent_sha256") != filehash(prior_path):
        raise ValueError("rehearsal intent identity missing")
    for name in ("commit", "base_model", "base_gguf", "data_dir", "chapter_splits",
                 "confirmation_seal", "legacy_trial", "converter", "converter_base", "restore_by"):
        if prior[name] != data[name]:
            raise ValueError("rehearsal differs: " + name)
    if result["estimate"] != data["estimate"]:
        raise ValueError("real projection must use the actual rehearsal measurement")
    for name, expected in prior["frozen_files"].items():
        if filehash(name) != expected:
            raise ValueError("rehearsal input changed: " + name)

def training_argv(data):
    p = intent_paths(data)
    argv = ["--round-two", "--phase", "restyle", "--goldfish", "--base", data["base_model"],
            "--data", data["data_dir"], "--out", str(p["training"]), "--chapter-splits", data["chapter_splits"],
            "--confirmation-seal", data["confirmation_seal"], "--rank", "16", "--alpha", "32",
            "--batch", "1", "--accum", "8", "--lr-restyle", "0.0002", "--epochs-restyle", "1",
            "--seq-restyle", "1024", "--seed", "3407", "--eval-steps", str(data["eval_steps"]),
            "--max-steps-restyle", str(data["steps"]), "--text-only", "--loss-target-gib", "0.125"]
    if data["dry_run"]:
        argv.append("--dry-run")
    return argv


def verify_intent(data):
    if training_argv(data) != data["training_argv"]:
        raise ValueError("worker and intent arguments disagree")
    for name, expected in data["frozen_files"].items():
        if filehash(name) != expected:
            raise RuntimeError("frozen input changed: " + name)
    actual = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    if actual != data["commit"]:
        raise RuntimeError("source commit changed")
    if not data["dry_run"]:
        validate_rehearsal(data)


def deadline(data):
    state = read(data["power_state"])
    if epoch(state["boot"]) != epoch(data["power"]["boot"]) or state.get("pendingUtc"):
        raise RuntimeError("new boot or pending shutdown")
    if epoch(state["deadlineUtc"]) != epoch(data["power"]["deadlineUtc"]) or state["lastRequestId"] != data["power"]["lastRequestId"]:
        raise RuntimeError("authorized one-night power state changed")
    if Path("/proc/sys/kernel/random/boot_id").read_text().strip() != data["linux_boot"]:
        raise RuntimeError("WSL boot changed")
    return min(epoch(data["restore_by"]) - RESTORE_RESERVE, epoch(state["deadlineUtc"]) - RESTORE_RESERVE)


def projection(step_seconds, evaluation_seconds, steps=517, interval=100, overhead=180):
    if not all(math.isfinite(v) and v > 0 for v in (step_seconds, evaluation_seconds)):
        raise ValueError("actual positive timings required")
    evaluations = math.ceil(steps / interval)
    return overhead + steps * step_seconds * 1.15 + evaluations * evaluation_seconds * 1.15


def guard_reason(log, now, end, planned, interval, estimate):
    steps = [r for r in log if r["event"] == "step"]
    evaluations = [r for r in log if r["event"] == "evaluate_begin"]
    if evaluations:
        last = evaluations[-1]
        before = [r["seconds"] for r in steps if r["step"] <= last["step"]][-20:]
        after = [r for r in steps if r["step"] > last["step"]]
        if before:
            limit = 1.5 * statistics.median(before)
            if any(r["seconds"] > limit for r in after):
                return "post-evaluation step exceeded 1.5x baseline"
            starts = [r for r in log if r["event"] == "step_begin" and r["step"] > last["step"]]
            if starts and (not steps or starts[-1]["step"] > steps[-1]["step"]) and now - starts[-1]["unix"] > limit:
                return "post-evaluation step exceeded 1.5x baseline while running"
    done = steps[-1]["step"] if steps else 0
    cost = statistics.median([r["seconds"] for r in steps[-20:]]) if steps else estimate["step_seconds"]
    complete_evals = [r["seconds"] for r in log if r["event"] == "evaluate_end"]
    eval_cost = max(complete_evals) if complete_evals else estimate["evaluation_seconds"]
    remaining = max(0, planned - done) * cost * 1.15
    remaining += max(0, math.ceil(planned / interval) - len(complete_evals)) * eval_cost * 1.15
    if now + remaining + 120 > end:
        return "projected Phase B end exceeds deadline minus 30 minutes"
    return None


def is_llama(name):
    return str(name).replace("\\", "/").split("/")[-1].lower() in ("llama-server", "llama-server.exe")


def admission_decision(xml, linux, windows, own_pid=None):
    gpu = ET.fromstring(xml).findall("gpu")
    if len(gpu) != 1 or "3090" not in gpu[0].findtext("product_name", ""):
        raise ValueError("expected one RTX 3090")
    text = gpu[0].findtext("fb_memory_usage/used", "").split()
    if len(text) != 2 or text[1] != "MiB":
        raise ValueError("invalid VRAM snapshot")
    used = int(text[0])
    processes = list(linux) + list(windows)
    processes += [{"name": p.findtext("process_name"), "pid": p.findtext("pid")} for p in gpu[0].findall("processes/process_info")]
    llama = [p for p in processes if is_llama(p["name"])]
    # own_pid is deliberately irrelevant: generic CUDA process counts are not a veto.
    return dict(allowed=not llama and used < 2048, used_mib=used, llama=llama, limit_mib=2048,
                generic_compute_processes_not_a_gate=True)


def gpu_admission(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    if any(n == "torch" or n.startswith("torch.") or n == "unsloth" or n.startswith("unsloth.") for n in sys.modules):
        raise RuntimeError("admission ran after an ML import")
    commands = {"gpu": ["/usr/lib/wsl/lib/nvidia-smi", "-q", "-x"],
                "linux": ["ps", "-eo", "pid=,ppid=,comm="],
                "windows": ["/mnt/c/Windows/System32/tasklist.exe", "/FO", "CSV", "/NH"]}
    captured, errors = {}, []
    for name, argv in commands.items():
        try:
            r = subprocess.run(argv, capture_output=True, timeout=25)
            captured[name] = r.stdout
            write_new(root / (name + ".stdout"), r.stdout, True)
            write_new(root / (name + ".stderr"), r.stderr, True)
            if r.returncode:
                errors.append(name + " exit " + str(r.returncode))
        except Exception as exc:
            errors.append(name + ": " + str(exc))
    result = None
    try:
        if errors:
            raise RuntimeError("; ".join(errors))
        linux = []
        for line in captured["linux"].decode().splitlines():
            pid, ppid, name = line.split(None, 2)
            linux.append(dict(pid=int(pid), ppid=int(ppid), name=name))
        windows = [{"pid": int(r[1]), "name": r[0]} for r in csv.reader(io.StringIO(captured["windows"].decode(errors="replace"))) if r]
        if not linux or not windows:
            raise ValueError("empty process inventory")
        result = admission_decision(captured["gpu"], linux, windows, os.getpid())
    except Exception as exc:
        errors.append(str(exc))
    report = dict(utc=utc(), allowed=not errors and result is not None and result["allowed"],
                  before_ml_import=True, decision=result, errors=errors)
    write_new(root / "ADMISSION.json", report)
    if not report["allowed"]:
        raise RuntimeError("GPU admission refused; saved snapshots: " + str(root))
    return report


def identity(pid):
    p = Path("/proc") / str(pid)
    st = (p / "stat").read_text().rsplit(")", 1)[1].split()
    return dict(pid=pid, start_ticks=st[19], boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                argv_sha256=digest((p / "cmdline").read_bytes()), exe=os.readlink(p / "exe"), cwd=os.readlink(p / "cwd"))


def same_process(saved):
    try:
        return identity(saved["pid"]) == saved
    except OSError:
        return False


def stop_exact(saved, root):
    fd = os.pidfd_open(saved["pid"])
    try:
        if select.select([fd], [], [], 0)[0]:
            return
        if not same_process(saved):
            raise RuntimeError("process identity changed; no signal")
        event(root, "TERM", identity=saved)
        signal.pidfd_send_signal(fd, signal.SIGTERM)
        if not select.select([fd], [], [], 90)[0]:
            raise RuntimeError("owned process did not exit after SIGTERM")
        event(root, "EXIT_CONFIRMED", identity=saved)
    finally:
        os.close(fd)


class PartialReply(RuntimeError):
    def __init__(self, message, partial):
        super().__init__(message)
        self.partial = partial


def http(port, path="/health", payload=None, timeout=5):
    connection = http_client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    timer, pieces = None, []
    end = time.monotonic() + timeout
    try:
        connection.connect()
        wire = connection.sock
        def interrupt():
            with contextlib.suppress(OSError):
                wire.shutdown(socket.SHUT_RDWR)
        timer = threading.Timer(max(.001, end-time.monotonic()), interrupt)
        timer.daemon = True
        timer.start()
        connection.request("POST" if payload is not None else "GET", path, payload,
                           {"Content-Type": "application/json", "Connection": "close"})
        reply = connection.getresponse()
        length = reply.length
        if length is None and not reply.chunked:
            raise RuntimeError("unverifiable HTTP framing")
        total = 0
        while True:
            chunk = reply.read1(65536)
            if not chunk:
                break
            pieces.append(chunk)
            total += len(chunk)
            if total > 16 * 1024 * 1024 or time.monotonic() >= end:
                raise RuntimeError("oversized or overdue HTTP body")
        raw = b"".join(pieces)
        if length is not None and len(raw) != length or reply.chunked and not reply.isclosed():
            raise RuntimeError("incomplete HTTP body")
        return reply.status, raw
    except BaseException as exc:
        if isinstance(exc, http_client.IncompleteRead) and exc.partial:
            pieces.append(exc.partial)
        raise PartialReply(type(exc).__name__ + ": " + str(exc), b"".join(pieces)) from exc
    finally:
        if timer:
            timer.cancel()
        connection.close()


class OwnedChild:
    def __init__(self, backend, name, argv, extra_env=None):
        self.backend, self.name = backend, name
        self.root = backend.paths["children"] / name
        self.root.mkdir(parents=True, exist_ok=False)
        self.argv = [str(x) for x in argv]
        env = os.environ.copy()
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                   TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1",
                   TORCHINDUCTOR_CACHE_DIR=str(backend.root / "cache/inductor"),
                   UNSLOTH_COMPILE_LOCATION=str(backend.root / "cache/unsloth"),
                   LD_LIBRARY_PATH=backend.data["original"]["ld_library_path"])
        if extra_env:
            env.update(extra_env)
        self.row, self.fd = None, None
        self.output = (self.root / "combined.log").open("xb")
        self.proc = subprocess.Popen(["/usr/bin/python3", "-B", str(Path(__file__).resolve()),
                                      "--exec-child", str(os.getpid()), *self.argv],
                                     cwd=backend.data["source_dir"], env=env, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        backend.children.append(self)
        self.fd = os.pidfd_open(self.proc.pid)
        def copy_output():
            try:
                for block in iter(lambda: self.proc.stdout.read1(65536), b""):
                    self.output.write(block)
                    self.output.flush()
                    with contextlib.suppress(BrokenPipeError, OSError):
                        sys.stdout.buffer.write(block)
                        sys.stdout.buffer.flush()
            finally:
                self.proc.stdout.close()
        self.reader = threading.Thread(target=copy_output, daemon=True)
        self.reader.start()
        until = time.monotonic() + 20
        while self.proc.poll() is None and time.monotonic() < until:
            try:
                candidate = identity(self.proc.pid)
                if candidate["argv_sha256"] == digest(("\0".join(self.argv) + "\0").encode()):
                    self.row = candidate
                    break
            except (FileNotFoundError, ProcessLookupError):
                pass
            time.sleep(.02)
        write_new(self.root / "START.json", dict(utc=utc(), argv=self.argv, identity=self.row))
        if self.row is None and self.proc.poll() is None:
            raise RuntimeError("child did not establish its exact identity")

    def end(self, reason):
        code = self.proc.poll()
        if code is None:
            raise RuntimeError("cannot record a live child as finished")
        if not (self.root / "END.json").exists():
            self.reader.join(timeout=10)
            if self.reader.is_alive():
                raise RuntimeError("child log pipe did not close")
            self.output.flush()
            os.fsync(self.output.fileno())
            self.output.close()
            write_new(self.root / "END.json", dict(utc=utc(), returncode=code, reason=reason, identity=self.row))
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        return code

    def stop(self):
        if self.proc.poll() is None:
            # pidfd was opened immediately after our own Popen, before any exec race.
            if self.fd is None:
                raise RuntimeError("owned child identity unavailable; no signal")
            event(self.backend.root, "OWNED_TERM", child_name=self.name, identity=self.row)
            signal.pidfd_send_signal(self.fd, signal.SIGTERM)
            if not select.select([self.fd], [], [], 90)[0]:
                raise RuntimeError("owned child did not exit; no escalation")
            self.proc.wait(timeout=2)
        self.end("owned_stop")

    def wait(self, end, training=False):
        while self.proc.poll() is None:
            self.backend.check_time(end)
            if training:
                log = rows(self.backend.root / "timing.jsonl")
                reason = guard_reason(log, time.time(), end, self.backend.data["steps"],
                                      self.backend.data["eval_steps"], self.backend.data["estimate"])
                if reason:
                    event(self.backend.root, "GUARD_STOP", reason=reason)
                    raise RuntimeError(reason)
                if self.backend.data["dry_run"]:
                    self.backend.sample_memory()
            time.sleep(.5)
        code = self.end("returned")
        if code:
            raise RuntimeError(self.name + " exited " + str(code))

# Executed only on the Pi by the reviewed launcher; no repo/config/clock edits.
PI_HELPER = r'''
import fcntl,json,os,pathlib,subprocess,sys,time,urllib.request,base64,hashlib
from datetime import datetime,timezone
q=json.loads(base64.b64decode(sys.argv[1]));root=pathlib.Path(q["root"])
def now():return datetime.now(timezone.utc).isoformat()
def save(name,obj):
 root.mkdir(parents=True,exist_ok=True)
 with (root/name).open("x") as f:json.dump(obj,f,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True,timeout=25)
 if p.returncode:raise RuntimeError(p.stderr.strip())
 return p.stdout
def props(unit,names):
 return dict(l.split("=",1) for l in run(["systemctl","--user","show",unit,*sum((["-p",n] for n in names),[])]).splitlines() if "=" in l)
def service():return props("hegel-world.service",["LoadState","ActiveState","MainPID","ControlPID","Job"])
def timer():return props("hegel-world.timer",["LoadState","ActiveState","UnitFileState"])
def idle(s):return s["LoadState"]=="loaded" and s["ActiveState"]=="inactive" and s["MainPID"]=="0" and s["ControlPID"]=="0" and s["Job"] in ("","0")
out={"utc":now(),"action":q["action"]}
try:
 os.chdir(q["repo"]);sys.path.insert(0,os.getcwd())
 from world.config import Config
 cfg=Config()
 if cfg.branch!="shadow" or cfg.clock_shift_min!=1170 or cfg.owl_at!="09:10":raise RuntimeError("natural schedule differs")
 action=q["action"]
 if action in ("pause","restore"):
  if action=="pause" and root.exists():raise RuntimeError("pause already has receipts")
  if action=="restore" and not (root/"PAUSE.json").exists():out["status"]="NO_PAUSE"
  else:
   with (cfg.state/"tick.lock").open("r+") as lock:
    until=time.monotonic()+180
    while True:
     try:
      fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
      if idle(service()):break
      fcntl.flock(lock,fcntl.LOCK_UN)
     except BlockingIOError:pass
     if time.monotonic()>=until:raise RuntimeError("active natural service preserved")
     time.sleep(1)
    before=timer()
    if before["LoadState"]!="loaded":raise RuntimeError("timer missing")
    if action=="pause":
     if before["ActiveState"]!="active" or before["UnitFileState"]!="enabled":raise RuntimeError("timer not in expected prior state")
     save("PAUSE.json",{"utc":now(),"timer":before,"service":service()})
     run(["systemctl","--user","stop","hegel-world.timer"])
     after=timer()
     if after["ActiveState"]!="inactive" or after["UnitFileState"]!=before["UnitFileState"]:raise RuntimeError("pause did not verify")
     out.update(status="PAUSED",before=before,after=after)
     save("PAUSED.json",out)
    else:
     prior=json.loads((root/"PAUSE.json").read_text())["timer"]
     if before["UnitFileState"]!=prior["UnitFileState"]:raise RuntimeError("timer enabled state changed independently")
     if before["ActiveState"]=="inactive":run(["systemctl","--user","start","hegel-world.timer"])
     after=timer()
     if after["ActiveState"]!=prior["ActiveState"] or after["UnitFileState"]!=prior["UnitFileState"]:raise RuntimeError("restore did not verify")
     out.update(status="RESTORED",before=before,after=after)
     if not (root/"RESTORED.json").exists():save("RESTORED.json",out)
 elif action=="verify":
  base=q["base_url"]
  with urllib.request.urlopen(base+"/health",timeout=15) as r:health=json.load(r)
  if health.get("status")!="ok":raise RuntimeError("Pi-to-PC health failed")
  payload={"model":q["model"],"messages":[{"role":"user","content":"Reply OK."}],"temperature":0,"max_tokens":1,"chat_template_kwargs":{"enable_thinking":False}}
  save("CHAT-BEGIN.json",{"utc":now(),"payload":payload})
  req=urllib.request.Request(base+"/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
  with urllib.request.urlopen(req,timeout=30) as r:raw=r.read();status=r.status
  with (root/"CHAT-RESPONSE.bin").open("xb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
  save("CHAT-RESPONSE.json",{"utc":now(),"status":status,"response":json.loads(raw),"sha256":hashlib.sha256(raw).hexdigest()})
  response=json.loads(raw)
  if status!=200 or not response["choices"][0]["message"].get("content"):raise RuntimeError("one-token response absent")
  out.update(status="PI_HEALTH_AND_ONE_TOKEN_VERIFIED",health=health,completion_tokens=response.get("usage",{}).get("completion_tokens"),response_sha256=hashlib.sha256(raw).hexdigest())
  save("VERIFY.json",out)
 else:raise ValueError("unknown action")
except BaseException as exc:
 out.update(status="FAILED",error=type(exc).__name__+": "+str(exc))
 print(json.dumps(out),flush=True);sys.exit(1)
print(json.dumps(out),flush=True)
'''


class Backend:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.hash = filehash(self.path)
        self.data = load_intent(self.path, self.hash)
        self.root = Path(self.data["run_dir"])
        self.paths = intent_paths(self.data)
        self.children = []
        self.startlock = None
        self.paused = False
        self.last_sample = 0
        self.server = None

    def check_time(self, end=None, reserve=0):
        load_intent(self.path, self.hash)
        limit = deadline(self.data)
        if time.time() + reserve >= min(limit, end or limit):
            raise TimeoutError("operation cannot fit before restoration reserve")
        return limit

    def pi(self, action):
        q = dict(action=action, root=self.data["pi_receipts"], repo=self.data["pi_repo"],
                 base_url=self.data["pi_base_url"], model=self.data["model_alias"])
        arg = base64.b64encode(encoded(q)).decode()
        result = subprocess.run([*self.data["ssh_argv"], "python3 -B - " + shlex.quote(arg)],
                                input=PI_HELPER.encode(), capture_output=True, timeout=240)
        name = action + "-" + str(time.time_ns())
        write_new(self.root / "pi" / (name + ".stdout"), result.stdout, True)
        write_new(self.root / "pi" / (name + ".stderr"), result.stderr, True)
        try:
            reply = json.loads(result.stdout)
        except Exception as exc:
            raise RuntimeError("Pi reply missing; preserve receipts") from exc
        if result.returncode or reply["status"] == "FAILED":
            raise RuntimeError("Pi " + action + ": " + str(reply))
        write_new(self.root / "pi" / (name + ".json"), reply)
        return reply

    def original(self):
        expected = digest(("\0".join(self.data["original"]["argv"]) + "\0").encode())
        found = []
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                if (entry / "comm").read_text().strip() != "llama-server":
                    continue
                argv = (entry / "cmdline").read_bytes()
                if b"--port\x008082\x00" in argv:
                    row = identity(int(entry.name))
                    if row["argv_sha256"] != expected or row["cwd"] != self.data["original"]["cwd"]:
                        raise RuntimeError("foreign 8082 process")
                    found.append(row)
            except (FileNotFoundError, ProcessLookupError):
                continue
        if len(found) > 1:
            raise RuntimeError("multiple original servers")
        return found

    def handover(self):
        self.check_time(reserve=300)
        old = self.original()
        if len(old) != 1:
            raise RuntimeError("exact original server must be serving before handover")
        self.startlock = Path(self.data["original"]["startup_lock"]).open("a+")
        fcntl.flock(self.startlock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Marker precedes the remote request, so lost replies still trigger restoration.
        write_new(self.root / "PAUSE-REQUEST.json", dict(utc=utc(), original=old[0]))
        self.paused = True
        reply = self.pi("pause")
        if reply["status"] != "PAUSED":
            raise RuntimeError("Pi timer pause unconfirmed")
        status, raw = http(8082, "/slots")
        slots = json.loads(raw)
        write_new(self.root / "ORIGINAL-SLOTS.json", slots)
        connections = subprocess.check_output(["ss", "-Htn", "state", "established", "sport = :8082"], timeout=10)
        write_new(self.root / "ORIGINAL-CONNECTIONS.txt", connections, True)
        if status != 200 or len(slots) != 3 or any(s.get("n_ctx") != 16384 or s.get("is_processing") is not False for s in slots):
            raise RuntimeError("original server has an active call or wrong slots")
        if connections.strip():
            raise RuntimeError("active original connection preserved")
        stop_exact(old[0], self.root)
        write_new(self.root / "ORIGINAL-EXIT.json", dict(utc=utc(), identity=old[0], confirmed=True))

    def worker(self, name, end):
        child = OwnedChild(self, name, [self.data["python"], "-B", str(Path(__file__).resolve()),
                                       "--intent", self.path, "--intent-sha256", self.hash, "--worker", name])
        child.wait(end, training=name == "train")
        return child

    def admission(self):
        # This process exits before the ML Python worker starts.
        child = OwnedChild(self, "admission", ["/usr/bin/python3", "-B", str(Path(__file__).resolve()),
                                             "--intent", self.path, "--intent-sha256", self.hash, "--worker", "admission"])
        child.wait(self.check_time())

    def phase_b(self):
        estimate = self.data["estimate"]
        cost = projection(estimate["step_seconds"], estimate["evaluation_seconds"],
                          self.data["steps"], self.data["eval_steps"])
        end = min(self.check_time(), time.time() + self.data["phase_b_cap_s"])
        if time.time() + cost > end:
            raise RuntimeError("Phase B projection does not fit; no trainer started")
        write_new(self.root / "B-BUDGET.json", dict(utc=utc(), projected_seconds=cost, phase_b_end=end,
                                                  restore_by=self.data["restore_by"]))
        self.worker("train", end)
        result = read(self.paths["training"] / "training.json")
        if result["steps"] != self.data["steps"]:
            raise RuntimeError("trainer stopped before the intended step cap")
        write_new(self.root / "PHASE-B-END.json", dict(utc=utc(), steps=result["steps"],
                                                     report_sha256=filehash(self.paths["training"] / "training.json")))
        if self.data["dry_run"]:
            self.sample_memory(force=True)

    def sample_memory(self, force=False):
        if not force and time.monotonic() - self.last_sample < 5:
            return
        self.last_sample = time.monotonic()
        stamp = str(time.time_ns())
        root = self.paths["telemetry"]
        xml = subprocess.check_output(["/usr/lib/wsl/lib/nvidia-smi", "-q", "-x"], timeout=15)
        write_new(root / (stamp + ".xml"), xml, True)
        used = int(ET.fromstring(xml).findtext("gpu/fb_memory_usage/used").split()[0])
        script = "$p=Get-CimInstance Win32_Process -Filter \"Name='vmwp.exe'\"; $g=Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory; [pscustomobject]@{VMs=@($p|Select-Object ProcessId);Memory=@($g|Select-Object Name,SharedUsage,DedicatedUsage)}|ConvertTo-Json -Depth 5 -Compress"
        r = subprocess.run([self.data["windows_pwsh"], "-NoProfile", "-Command", script],
                           capture_output=True, timeout=25)
        write_new(root / (stamp + ".windows.stdout"), r.stdout, True)
        write_new(root / (stamp + ".windows.stderr"), r.stderr, True)
        if r.returncode:
            raise RuntimeError("shared-memory observation failed")
        values = json.loads(r.stdout.decode("utf-8-sig"))
        vms = values["VMs"]
        if len(vms) != 1:
            raise RuntimeError("cannot attribute shared GPU memory to one WSL VM")
        prefix = "pid_" + str(vms[0]["ProcessId"]) + "_"
        shared = sum(int(r["SharedUsage"]) for r in values["Memory"] if r["Name"].startswith(prefix))
        event(root, "memory", used_mib=used, shared_bytes=shared)

    def c_fits(self):
        needed = self.data["estimate"]["phase_c_seconds"]
        if self.data["dry_run"]:
            needed = self.data["estimate"].get("rehearsal_c_seconds", 600)
        fits = time.time() + needed < self.check_time()
        write_new(self.root / "C-BUDGET.json", dict(utc=utc(), required_seconds=needed, fits=fits))
        return fits

    def phase_c(self):
        self.paths["converted"].mkdir(parents=True, exist_ok=False)
        target = self.paths["converted"] / "adapter-f16.gguf"
        command = [self.data["python"], self.data["converter"], str(self.paths["training"]),
                   "--base", self.data["converter_base"], "--outtype", "f16", "--outfile", str(target)]
        child = OwnedChild(self, "convert", command, {"CUDA_VISIBLE_DEVICES": ""})
        child.wait(min(time.time() + 1200, self.check_time()))
        with target.open("rb") as stream:
            if stream.read(4) != b"GGUF":
                raise RuntimeError("converter did not write a GGUF")
        self.worker("verify-conversion", self.check_time())
        gpu_admission(self.root / "admission-before-adapter")
        port = self.data["trial_port"]
        if "LISTEN" in subprocess.check_output(["ss", "-ltnp", "sport = :" + str(port)], text=True):
            raise RuntimeError("adapter server port already in use")
        original = self.data["original"]["argv"]
        argv = [original[0], "-m", self.data["base_gguf"], "-ngl", "99", "-c", "49152",
                "-np", "3", "--host", "127.0.0.1", "--port", str(port), "--alias", self.data["model_alias"],
                "--lora-scaled", str(target) + ":0"]
        self.server = OwnedChild(self, "adapter-server", argv)
        end = time.time() + 240
        while time.time() < end:
            self.check_time()
            if self.server.proc.poll() is not None:
                self.server.end("load_failed")
                raise RuntimeError("adapter server exited during load")
            try:
                status, raw = http(port, timeout=3)
                if status == 200 and json.loads(raw).get("status") == "ok":
                    break
            except (OSError, ValueError, RuntimeError):
                pass
            time.sleep(2)
        else:
            raise TimeoutError("adapter server readiness timeout")
        status, raw = http(port, "/lora-adapters")
        adapters = json.loads(raw)
        status2, raw2 = http(port, "/slots")
        slots = json.loads(raw2)
        if status != 200 or len(adapters) != 1 or adapters[0].get("id") != 0 or adapters[0].get("scale") != 0:
            raise RuntimeError("adapter/global-zero routing mismatch")
        if os.path.realpath(adapters[0]["path"]) != os.path.realpath(target):
            raise RuntimeError("different adapter loaded")
        if status2 != 200 or len(slots) != 3 or any(s["n_ctx"] != 16384 for s in slots):
            raise RuntimeError("adapter server slot mismatch")
        if "libggml-cuda.so" not in (Path("/proc") / str(self.server.row["pid"]) / "maps").read_text():
            raise RuntimeError("adapter server CUDA backend absent")
        write_new(self.root / "ADAPTER-READY.json", dict(utc=utc(), identity=self.server.row, adapters=adapters, slots=slots))
        self.worker("benchmark", self.check_time())
        self.server.stop()
        self.server = None

    def sheets(self):
        if not self.data["dry_run"]:
            self.worker("sheets", self.check_time())

    def restore(self):
        # There is no competing watchdog or recovery supervisor.
        for child in reversed(self.children):
            if child.name == "adapter-server":
                pending = [r["deadline"] for r in rows(self.root / "http-windows.jsonl")
                           if r["event"] == "http_begin"]
                if pending:
                    # A crashed client cannot prove cancellation; preserve its full request allowance.
                    ends = {r["request"] for r in rows(self.root / "http-windows.jsonl") if r["event"] == "http_end"}
                    pending = [r["deadline"] for r in rows(self.root / "http-windows.jsonl")
                               if r["event"] == "http_begin" and r["request"] not in ends]
                    if pending:
                        time.sleep(max(0, max(pending) - time.time()))
            child.stop()
        if not self.paused:
            if self.startlock:
                fcntl.flock(self.startlock, fcntl.LOCK_UN)
                self.startlock.close()
                self.startlock = None
            return dict(status="NO_WORLD_CHANGE", utc=utc())
        live = self.original()
        if not live:
            gpu_admission(self.root / "admission-before-restore")
        old = self.data["original"]
        if filehash(old["launcher"]) != self.data["frozen_files"][old["launcher"]]:
            raise RuntimeError("original startup launcher changed")
        if self.startlock:
            fcntl.flock(self.startlock, fcntl.LOCK_UN)
            self.startlock.close()
            self.startlock = None
        r = subprocess.run(["/usr/bin/python3", "-B", old["launcher"]],
                           cwd=old["cwd"], capture_output=True, timeout=240)
        write_new(self.root / "RESTORE.stdout", r.stdout, True)
        write_new(self.root / "RESTORE.stderr", r.stderr, True)
        ready = json.loads(r.stdout)
        if r.returncode or ready.get("outcome") != "GPU_READY":
            raise RuntimeError("original Qwen restoration unconfirmed")
        slots = ready.get("slots", [])
        if len(slots) != 3 or any(s["n_ctx"] != 16384 for s in slots):
            raise RuntimeError("restored Qwen slot mismatch")
        status, raw = http(8082)
        if status != 200 or json.loads(raw).get("status") != "ok":
            raise RuntimeError("restored Qwen health failed")
        timer = self.pi("restore")
        if timer["status"] != "RESTORED":
            raise RuntimeError("Pi timer restoration unconfirmed")
        answer = self.pi("verify") if self.data["dry_run"] else None
        result = dict(status="ORIGINAL_QWEN_AND_TIMER_RESTORED", utc=utc(), server=ready,
                      timer=timer, pi_probe=answer, before_deadline=time.time() <= epoch(self.data["restore_by"]))
        write_new(self.root / "RESTORATION.json", result)
        return result

def train_worker(data, path, expected):
    """Instrument the reviewed CLI; all recipe/path arguments come from INTENT."""
    load_intent(path, expected)
    root = Path(data["run_dir"])
    admission = read(root / "admission" / "ADMISSION.json")
    if not admission["allowed"] or not admission["before_ml_import"]:
        raise RuntimeError("no successful pre-Python admission")
    if time.time() - epoch(admission["utc"]) > 120:
        raise RuntimeError("admission is stale")
    os.environ["UNSLOTH_CE_LOSS_TARGET_GB"] = "0.125"
    import unsloth  # noqa: F401; must patch Transformers before training imports
    from pc import train_hegel as trainer_api, restyle_round2 as r2
    engine = r2.runtime()
    base_trainer = engine.Trainer
    timing = root / "timing.jsonl"
    state = {}

    def emit(kind, **fields):
        with timing.open("ab") as stream:
            stream.write((json.dumps(dict(event=kind, utc=utc(), unix=time.time(), **fields)) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())

    class Timing(engine.TrainerCallback):
        def on_step_begin(self, args, model_state, control, **kwargs):
            load_intent(path, expected)
            if time.time() + 120 >= deadline(data):
                raise TimeoutError("trainer deadline")
            engine.torch.cuda.synchronize()
            state["step_start"] = time.monotonic()
            emit("step_begin", step=model_state.global_step + 1)

        def on_step_end(self, args, model_state, control, **kwargs):
            engine.torch.cuda.synchronize()
            emit("step", step=model_state.global_step, seconds=time.monotonic() - state["step_start"],
                 peak_reserved=engine.torch.cuda.max_memory_reserved(), peak_allocated=engine.torch.cuda.max_memory_allocated())
            return control

    class MeasuredTrainer(base_trainer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_callback(Timing())

        def evaluate(self, *args, **kwargs):
            began = time.monotonic()
            emit("evaluate_begin", step=self.state.global_step)
            result = super().evaluate(*args, **kwargs)
            emit("evaluate_end", step=self.state.global_step, seconds=time.monotonic() - began)
            return result

        def _save_checkpoint(self, *args, **kwargs):
            began = time.monotonic()
            result = super()._save_checkpoint(*args, **kwargs)
            emit("checkpoint", step=self.state.global_step, seconds=time.monotonic() - began)
            return result

    engine.Trainer = MeasuredTrainer
    original_runtime, original_generate = r2.runtime, r2.generate_for_model
    r2.runtime = lambda: engine
    call = 0

    def recorded_generate(model, tok, plain, seed, tokens, torch):
        nonlocal call
        call += 1
        load_intent(path, expected)
        if time.time() + HTTP_TIMEOUT >= deadline(data):
            raise TimeoutError("held generation cannot fit")
        payload = dict(plain=plain, seed=seed, max_tokens=tokens)
        base = root / "held-generations" / ("%04d" % call)
        write_new(str(base) + ".begin.json", payload)
        start = time.monotonic()
        result = original_generate(model, tok, plain, seed, tokens, torch)
        torch.cuda.synchronize()
        write_new(str(base) + ".response.json",
                  dict(result=result, seconds=time.monotonic() - start, payload_sha256=digest(encoded(payload))))
        if result.get("finish_reason") != "stop":
            raise RuntimeError("held generation incomplete; no retry")
        return result

    r2.generate_for_model = recorded_generate
    try:
        result = trainer_api.main(training_argv(data))
        if result:
            raise RuntimeError("training CLI failed")
    finally:
        r2.runtime, r2.generate_for_model = original_runtime, original_generate


def verify_conversion(data):
    sys.path.insert(0, str(Path(data["converter"]).parent / "gguf-py"))
    from gguf import GGUFReader
    paths = intent_paths(data)
    target = paths["converted"] / "adapter-f16.gguf"
    adapter, base = GGUFReader(str(target)), GGUFReader(data["base_gguf"])
    metadata = {name: adapter.fields[name].contents() for name in
                ("general.architecture", "general.type", "adapter.type", "adapter.lora.alpha")}
    if metadata["general.architecture"] != base.fields["general.architecture"].contents():
        raise RuntimeError("adapter architecture differs from the serving base")
    if metadata["adapter.type"] != "lora" or metadata["adapter.lora.alpha"] != 32:
        raise RuntimeError("adapter metadata mismatch")
    if not adapter.tensors or not all(16 in list(t.shape) for t in adapter.tensors):
        raise RuntimeError("adapter rank mismatch")
    write_new(Path(data["run_dir"]) / "CONVERTED.json",
              dict(utc=utc(), path=str(target), bytes=target.stat().st_size, sha256=filehash(target),
                   metadata=metadata, tensors=len(adapter.tensors),
                   input_adapter_sha256=filehash(paths["training"] / "adapter_model.safetensors")))


def rehearsal_cases(plan, guard, client, dest):
    from tools import hegel_test_round2 as test
    from tools.voice_dashboard import meaning_propositions, retention
    from world import contract
    cast = json.loads((dest / "private/inputs/cast.json").read_bytes())
    judge = client("raw-rehearsal-meaning", 0.0)
    base = client("raw-contract-base", 0.0)  # exact completed base requests replay locally
    results = []
    for index, thought in enumerate(plan["cohort"][:2]):
        seed = plan["seed"] + index
        case = plan["cases"][index]
        raw_base = test.contract_answer(base, plan, case, seed)
        answer = contract.extract_json(raw_base)
        per_case = dict(id=thought["id"], contract_id=case["id"], scales={})
        for scale in (0.8, 0.0):
            c = client("raw-rehearsal-scale-" + str(scale), scale)
            rid = "rehearsal/" + str(index)
            changed = test.run_restyle(c, guard, thought["plain"], rid + "/voice", seed)
            if not changed["attempts"] or any(a["finish_reason"] != "stop" or not a["raw"].strip()
                                               for a in changed["attempts"]):
                raise RuntimeError("rehearsal adapter answer incomplete")
            meaning = test.meaning_check(judge, thought["plain"], changed["text"],
                                         rid + "/" + str(scale) + "/meaning", seed)
            propositions = meaning_propositions(judge, thought["plain"], changed["text"],
                                                 rid + "/" + str(scale) + "/propositions", seed)
            behavior = answer
            if isinstance(answer, dict) and isinstance(answer.get("thought"), str) and answer["thought"].strip():
                restyled = test.run_restyle(c, guard, answer["thought"], rid + "/contract", seed)
                behavior = dict(answer, thought=restyled["text"])
            errors = contract.check(behavior, case)[0] if isinstance(behavior, dict) else ["no JSON"]
            per_case["scales"][str(scale)] = dict(restyle=changed, meaning=meaning,
                meaning_propositions=propositions, retention=retention(thought["plain"], changed["text"], cast),
                copied12=bool(guard.matches(changed["text"])), behavior=behavior, contract_errors=errors)
        results.append(per_case)
    return dict(cases=results, diagnostic_only=True, canonical_cohort_unchanged=True,
                full_40_case_dashboard_reserved_for_real_run=True)


def benchmark_worker(data, path, expected):
    import shutil
    from tools import hegel_test_round2 as test
    from tools.recorded_llama import RecordedClient, TransportError
    from world import restyle, shelf
    root = Path(data["run_dir"])
    dest = intent_paths(data)["benchmark"]
    # Preserve the exact frozen cohort, key and all earlier raw responses. No plan rewrite.
    shutil.copytree(data["legacy_trial"], dest)
    frozen = test.load_plan(dest)
    if filehash(frozen["shelf_path"]) != frozen["source_sha256"]["shelf"]:
        raise RuntimeError("frozen shelf changed")
    guard = restyle.ShelfGuard.from_shelf(shelf.load(frozen["shelf_path"]))
    server = read(root / "ADAPTER-READY.json")["identity"]
    port = data["trial_port"]
    sequence = 0

    class Response:
        def __init__(self, raw, status):
            self.raw, self.status = raw, status
        def read(self):
            return self.raw
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def opener(request, timeout):
        nonlocal sequence
        load_intent(path, expected)
        if time.time() + HTTP_TIMEOUT >= deadline(data) or not same_process(server):
            raise RuntimeError("request cannot fit or server identity changed")
        sequence += 1
        rid = str(sequence)
        event_path = root / "http-windows.jsonl"
        def append(kind, **kwargs):
            with event_path.open("ab") as stream:
                stream.write((json.dumps(dict(event=kind, request=rid, unix=time.time(), **kwargs)) + "\n").encode())
                stream.flush()
                os.fsync(stream.fileno())
        append("http_begin", deadline=time.time() + HTTP_TIMEOUT, payload_sha256=digest(request.data))
        start = time.monotonic()
        try:
            status, raw = http(port, "/v1/chat/completions", request.data, HTTP_TIMEOUT)
        except BaseException as exc:
            write_new(root / "unknown" / (rid + ".partial.bin"), getattr(exc, "partial", b""), True)
            write_new(root / "unknown" / (rid + ".json"), dict(utc=utc(), error=str(exc),
                                                             payload_sha256=digest(request.data)))
            raise TransportError("unknown HTTP response; no resend") from exc
        append("http_end", seconds=time.monotonic() - start, status=status, response_sha256=digest(raw))
        if status != 200:
            raise urllib.error.HTTPError(request.full_url, status, "HTTP failure", {}, io.BytesIO(raw))
        return Response(raw, status)

    def client(folder, scale):
        return RecordedClient("http://127.0.0.1:" + str(port), dest / "private" / folder,
                              timeout=HTTP_TIMEOUT, slot=1, lora=[{"id": 0, "scale": scale}], opener=opener)

    if data["dry_run"]:
        report = rehearsal_cases(frozen, guard, client, dest)
        write_new(root / "REHEARSAL-C-DIAGNOSTICS.json", report)
        write_new(root / "PHASE-C-END.json", dict(utc=utc(), status="REHEARSAL_TWO_CASES",
                 cases=report["cases"], diagnostics_sha256=filehash(root / "REHEARSAL-C-DIAGNOSTICS.json"),
                 automatic_quality_pass_not_claimed=True))
        return

    private = dest / "private"
    control = test.run_arm(dest, "control", "plain", client("raw-control-plain", 0.0),
                           client("raw-meaning", 0.0), client("raw-contract-base", 0.0), guard)
    adapter = test.run_arm(dest, "adapter", "training1", client("raw-adapter-training1", data["adapter_scale"]),
                           client("raw-meaning", 0.0), client("raw-contract-base", 0.0), guard)
    from tools.voice_dashboard import dashboard, render_html
    cast = (private / "inputs/cast.json").read_bytes()
    if digest(cast) != frozen["source_sha256"]["cast"]:
        raise RuntimeError("frozen cast changed")
    report = dashboard(frozen, control, adapter, guard, json.loads(cast))
    write_new(private / "VOICE-DASHBOARD.json", report)
    write_new(private / "VOICE-DASHBOARD.html", render_html(report).encode(), True)
    write_new(root / "PHASE-C-END.json",
              dict(utc=utc(), status="MACHINE_TEST_COMPLETE", control=test.automatic_metrics(control),
                   adapter=test.automatic_metrics(adapter), KPI4="nothing copied",
                   all_five_kpis_passed=False, human_preference_and_meaning_pending=True,
                   confirmation_set_unused=True, dashboard=str(private / "VOICE-DASHBOARD.html")))


def sheets_worker(data):
    from tools import hegel_test_round2 as test
    paths = intent_paths(data)
    private = paths["benchmark"] / "private"
    control, adapter = read(private / "RESULT-control-plain.json"), read(private / "RESULT-adapter-training1.json")
    exported = test.export_sheets(paths["benchmark"], control, adapter, paths["sheets"])
    write_new(Path(data["run_dir"]) / "SHEETS.json",
              dict(utc=utc(), files=exported, welt_ready=True, claude_reserved_for_claude=True,
                   human_scores_pending=True, no_key_release=True))


def rehearsal_verdict(data, root, restored, now=None):
    root = Path(root)
    log = rows(root / "timing.jsonl")
    step = [r for r in log if r["event"] == "step"]
    before = [r["seconds"] for r in step if r["step"] <= 2]
    after = [r["seconds"] for r in step if r["step"] > 2]
    evaluations = [r["seconds"] for r in log if r["event"] == "evaluate_end"]
    memory = rows(root / "telemetry/events.jsonl")
    base = read(root / "MEMORY-BASELINE.json")
    if len(before) != 2 or not after or not evaluations or not memory:
        raise RuntimeError("rehearsal measurement incomplete")
    baseline = statistics.median(before)
    ratio = max(after) / baseline
    peak_mib = max(r["used_mib"] for r in memory)
    peak_shared = max(r["shared_bytes"] for r in memory)
    # Both sampled total VRAM and PyTorch's allocator high-water mark must fit.
    peak_reserved = max(r["peak_reserved"] for r in step)
    estimate = dict(step_seconds=statistics.median(r["seconds"] for r in step),
                    evaluation_seconds=max(evaluations), phase_c_seconds=data["estimate"]["phase_c_seconds"],
                    rehearsal_c_seconds=data["estimate"].get("rehearsal_c_seconds", 600))
    b_seconds = projection(estimate["step_seconds"], estimate["evaluation_seconds"])
    timestamp = time.time() if now is None else now
    b_fits = timestamp + b_seconds < epoch(data["restore_by"]) - RESTORE_RESERVE
    bc_fits = timestamp + b_seconds + estimate["phase_c_seconds"] < epoch(data["restore_by"]) - RESTORE_RESERVE
    c = read(root / "PHASE-C-END.json")
    gates = dict(post_eval_speed=ratio <= 1.5, vram=peak_mib < 23 * 1024 and peak_reserved < 23 * 1024**3,
                 no_shared_spill=peak_shared <= base["shared_bytes"],
                 adapter_answers=c["status"] == "REHEARSAL_TWO_CASES" and len(c["cases"]) == 2,
                 qwen_and_timer=restored["status"] == "ORIGINAL_QWEN_AND_TIMER_RESTORED",
                 pi_route=restored.get("pi_probe", {}).get("status") == "PI_HEALTH_AND_ONE_TOKEN_VERIFIED",
                 phase_b_fits=b_fits)
    # Owner's 5-Nov overnight answer replaces the sleeping-mind tick and resume gates.
    return dict(utc=utc(), intent_sha256=filehash(root / "INTENT.json"),
                passed=all(gates.values()), gates=gates, before_step_seconds=before,
                after_step_seconds=after, ratio=ratio, peak_vram_mib=peak_mib, peak_torch_reserved_bytes=peak_reserved,
                shared_baseline_bytes=base["shared_bytes"], peak_shared_bytes=peak_shared,
                estimate=estimate, projected_B_seconds=b_seconds,
                projected_B_plus_C_seconds=b_seconds + estimate["phase_c_seconds"], B_and_C_fit_now=bc_fits,
                C_may_be_deferred=True, no_forced_tick=True, first_awake_tick_for_claude=True)


def run_pipeline(backend):
    """The same step order is exercised by failure-injection tests and the real run."""
    result = dict(status="FAILED", started_utc=utc())
    try:
        backend.handover()
        backend.admission()
        if backend.data["dry_run"]:
            backend.sample_memory(force=True)
            samples = rows(backend.root / "telemetry/events.jsonl")
            write_new(backend.root / "MEMORY-BASELINE.json", samples[-1])
        backend.phase_b()
        if backend.c_fits():
            backend.phase_c()
            backend.sheets()
            result["status"] = "B_AND_C_COMPLETE"
        else:
            result["status"] = "B_COMPLETE_C_DEFERRED"
            if backend.data["dry_run"]:
                raise RuntimeError("rehearsal cannot pass without C")
    except BaseException as exc:
        result.update(status="FAILED", error=type(exc).__name__ + ": " + str(exc), traceback=traceback.format_exc())
    finally:
        try:
            result["restoration"] = backend.restore()
        except BaseException as exc:
            result.update(status="RESTORATION_FAILED", restoration_error=type(exc).__name__ + ": " + str(exc))
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--exec-child":
        parent = int(argv[1])
        if ctypes.CDLL(None).prctl(1, signal.SIGTERM) != 0 or os.getppid() != parent:
            raise SystemExit("parent-death guard failed")
        os.execv(argv[2], argv[2:])
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--intent", type=Path)
    p.add_argument("--intent-sha256")
    p.add_argument("--write-intent", type=Path, metavar="NEW_RUN_DIR")
    p.add_argument("--restore-by")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--eval-steps", type=int)
    p.add_argument("--worker", choices=["admission", "train", "benchmark", "sheets", "verify-conversion"])
    a = p.parse_args(argv)
    if a.write_intent:
        if not a.restore_by or a.intent or a.worker:
            p.error("--write-intent needs --restore-by and configuration JSON on stdin")
        path = create_intent(json.load(sys.stdin), a.write_intent, a.restore_by, a.dry_run, a.eval_steps)
        print(json.dumps(dict(intent=str(path), sha256=filehash(path))))
        return 0
    if not a.intent:
        p.error("--intent is required")
    data = load_intent(a.intent, a.intent_sha256)
    if a.dry_run != data["dry_run"] and a.dry_run or a.eval_steps and a.eval_steps != data["eval_steps"]:
        p.error("command flags disagree with the immutable intent")
    if a.worker:
        if not a.intent_sha256:
            p.error("workers require the pinned intent hash")
        if a.worker == "admission":
            gpu_admission(Path(data["run_dir"]) / "admission")
        elif a.worker == "train":
            train_worker(data, a.intent, a.intent_sha256)
        elif a.worker == "benchmark":
            benchmark_worker(data, a.intent, a.intent_sha256)
        elif a.worker == "verify-conversion":
            verify_conversion(data)
        else:
            sheets_worker(data)
        return 0
    verify_intent(data)
    root = Path(data["run_dir"])
    with (root / "run.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_new(root / "RUN-BEGIN.json", dict(utc=utc(), pid=os.getpid(), intent_sha256=filehash(a.intent)))
        def interrupted(sig, frame):
            raise RuntimeError("launcher interrupted; restore, no restart")
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        backend = Backend(a.intent)
        outcome = run_pipeline(backend)
        if data["dry_run"] and outcome["status"] == "B_AND_C_COMPLETE":
            try:
                outcome["rehearsal"] = rehearsal_verdict(data, root, outcome["restoration"])
                if not outcome["rehearsal"]["passed"]:
                    outcome["status"] = "REHEARSAL_FAILED"
                write_new(root / "REHEARSAL.json", outcome["rehearsal"])
            except BaseException as exc:
                outcome.update(status="REHEARSAL_FAILED", error=str(exc))
        outcome["finished_utc"] = utc()
        write_new(root / "RUN-END.json", outcome)
        print(json.dumps(dict(status=outcome["status"], run_dir=str(root), error=outcome.get("error"))))
        return 0 if outcome["status"] in ("B_AND_C_COMPLETE", "B_COMPLETE_C_DEFERRED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
