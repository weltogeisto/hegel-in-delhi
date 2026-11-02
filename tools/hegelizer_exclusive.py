"""Four-worker continuation of frozen recipe4 while Hegel is explicitly paused.

An owned loopback server is required. Existing completed and failed units stay
done; legacy receipts are replayed with their original URL/slot contract.
No training or automatic world/power changes occur here.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import random
import select
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import hegelizer_round2 as r2
from tools.recorded_llama import RecordedClient, TransportError, UnknownRequest, json_bytes, write_new

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(path, value):
    write_new(path, json_bytes(value))

def deny(*args, **kwargs):
    raise AssertionError("legacy cache cannot transmit")

class Cutoff(TransportError):
    pass

class DeadlinePolicy:
    """Use the existing cutoff until the authorized one-night change is verified."""
    def __init__(self, plan):
        self.plan = plan
    def __call__(self):
        p = self.plan
        state = json.loads(Path(p["power_state"]).read_bytes())
        if state["boot"] != p["power_boot"] or state.get("pendingUtc"):
            raise Cutoff("power session changed or shutdown is pending")
        initial = dt.datetime.fromisoformat(p["initial_power_deadline"]).timestamp()
        actual = dt.datetime.fromisoformat(state["deadlineUtc"]).timestamp()
        verified = False
        result_path = Path(p["power_result"])
        if result_path.exists():
            result = json.loads(result_path.read_bytes())
            verified = (result.get("status") == "VERIFIED"
                        and result.get("state", {}).get("lastRequestId") == state.get("lastRequestId")
                        and result.get("state", {}).get("deadlineUtc") == state["deadlineUtc"]
                        and dt.datetime.fromisoformat(result["requested_deadline"]).timestamp()
                            == dt.datetime.fromisoformat(p["authorized_power_deadline"]).timestamp())
        effective = actual if verified or actual <= initial else initial
        return min(effective - p["shutdown_reserve_s"],
                   dt.datetime.fromisoformat(p["stop_utc"]).timestamp())

class PartialReply(TransportError):
    def __init__(self, raw, message):
        super().__init__(message)
        self.raw = raw

def reconcile_raw(root):
    """Independently check membership, byte hashes and successful complete chains."""
    root = Path(root)
    if not root.exists():
        return []
    files = {p.name for p in root.iterdir() if p.is_file()}
    expected, records = set(), []
    for p in sorted(root.glob("*.begin.json")):
        stem = p.name.removesuffix(".begin.json")
        names = {stem + suffix for suffix in
                 (".begin.json", ".done.json", ".request.json", ".forwarded.json", ".response.bin")}
        if not names <= files:
            raise UnknownRequest("incomplete saved chain: " + stem)
        begin = json.loads(p.read_bytes())
        done = json.loads((root / (stem + ".done.json")).read_bytes())
        if sha(begin["request_id"].encode()) != stem:
            raise ValueError("receipt identity mismatch")
        for suffix, digest in ((".request.json", begin["original_sha256"]),
                               (".forwarded.json", begin["forwarded_sha256"]),
                               (".response.bin", done["response_sha256"])):
            if sha((root / (stem + suffix)).read_bytes()) != digest:
                raise ValueError("receipt hash mismatch: " + stem + suffix)
        if done.get("error") or done.get("http_status") != 200:
            raise TransportError("saved failure requires reconciliation: " + begin["request_id"])
        records.append(begin)
        expected.update(names)
    if files != expected:
        raise ValueError("orphan or unexpected raw files: " + repr(sorted(files - expected)))
    return records

class BoundedHTTP:
    """Independent connections; one absolute watchdog per call, without retries."""
    def __init__(self, identity, port=8082, max_body=16*1024*1024):
        self.identity, self.port, self.max_body = identity, port, max_body

    def __call__(self, data, timeout):
        conn = None
        timer = None
        chunks = []
        deadline = time.monotonic() + timeout
        try:
            if not self.identity():
                raise TransportError("owned server identity is unavailable")
            conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
            conn.connect()
            wire = conn.sock
            if wire is None:
                raise TransportError("connected socket missing")
            def interrupt():
                try:
                    wire.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("request deadline")
            wire.settimeout(remaining)
            timer = threading.Timer(remaining, interrupt)
            timer.daemon = True
            timer.start()
            conn.request("POST", "/v1/chat/completions", body=data,
                         headers={"Content-Type": "application/json", "Connection": "close"})
            response = conn.getresponse()
            length = response.length
            if length is None and not response.chunked:
                raise TransportError("unverifiable response framing")
            if length is not None and length > self.max_body:
                raise TransportError("response exceeds cap")
            total = 0
            while not response.isclosed():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("absolute request deadline")
                wire.settimeout(remaining)
                block = response.read1(min(65536, self.max_body-total+1))
                if not block:
                    break
                chunks.append(block)
                total += len(block)
                if total > self.max_body:
                    raise TransportError("response exceeds cap")
            if length is not None and total != length:
                raise TransportError("incomplete response body")
            if time.monotonic() > deadline or not self.identity():
                raise TransportError("deadline or process identity changed")
            return response.status, b"".join(chunks)
        except BaseException as exc:
            if isinstance(exc, http.client.IncompleteRead) and exc.partial:
                chunks.append(exc.partial)
            raise PartialReply(b"".join(chunks), type(exc).__name__ + ": " + str(exc)) from exc
        finally:
            if timer:
                timer.cancel()
            if conn:
                conn.close()

class ExclusiveClient(RecordedClient):
    """Automatic slot assignment is only used for this separately owned server."""
    def __init__(self, root, legacy_root, legacy_url, sender, cutoff, timeout=300, clock=time.time):
        super().__init__("http://127.0.0.1:8082", root, timeout=timeout)
        self.legacy = RecordedClient(legacy_url, legacy_root, opener=deny)
        self.sender, self.cutoff, self.clock = sender, cutoff, clock
        self.stop = threading.Event()
        self.cutoff_reached = False
        self.lock = threading.Lock()
        self.active_ids = set()
        self.replayed = set()

    def check(self):
        if self.stop.is_set():
            if self.cutoff_reached:
                raise Cutoff("exclusive continuation stopped at cutoff")
            raise TransportError("exclusive continuation stopped")
        cutoff = self.cutoff() if callable(self.cutoff) else self.cutoff
        if self.clock() + self.timeout >= cutoff:
            raise Cutoff("no new request: approaching the verified power cutoff")
        if self.before_request:
            self.before_request()

    def post(self, request_id, payload):
        legacy_begin = Path(str(self.legacy.stem(request_id)) + ".begin.json")
        if legacy_begin.exists():
            result = self.legacy.post(request_id, payload)
            with self.lock:
                self.replayed.add(request_id)
            return result
        with self.lock:
            if request_id in self.active_ids:
                raise TransportError("duplicate concurrent request")
            self.active_ids.add(request_id)
        try:
            return self._post_new(request_id, payload)
        except BaseException as exc:
            if isinstance(exc, Cutoff):
                self.cutoff_reached = True
            self.stop.set()
            raise
        finally:
            with self.lock:
                self.active_ids.remove(request_id)

    def _post_new(self, request_id, payload):
        original = json_bytes(payload)
        stem = self.stem(request_id)
        path = lambda suffix: Path(str(stem) + suffix)
        if path(".begin.json").exists():
            begin = json.loads(path(".begin.json").read_bytes())
            if begin["request_id"] != request_id or begin["url"] != self.url:
                raise ValueError("saved identity changed")
            if (begin["original_sha256"] != sha(original) or
                begin["forwarded_sha256"] != sha(original) or
                path(".request.json").read_bytes() != original or
                path(".forwarded.json").read_bytes() != original):
                raise ValueError("saved payload changed")
            if not path(".done.json").exists():
                raise UnknownRequest("never resend: " + request_id)
            done = json.loads(path(".done.json").read_bytes())
            raw = path(".response.bin").read_bytes()
            if done["response_sha256"] != sha(raw) or done.get("error") or done["http_status"] != 200:
                raise TransportError("saved response needs reconciliation")
            return json.loads(raw)
        if any(path(s).exists() for s in (".done.json", ".request.json", ".forwarded.json", ".response.bin")):
            raise ValueError("orphan receipt; reconcile before sending")
        self.check()
        write_new(path(".request.json"), original)
        write_new(path(".forwarded.json"), original)
        save(path(".begin.json"), {"request_id": request_id, "url": self.url, "utc": utc(),
             "original_sha256": sha(original), "forwarded_sha256": sha(original),
             "slot_assignment": "automatic; owned four-slot server"})
        started = time.monotonic()
        try:
            self.check()
            status, raw = self.sender(original, self.timeout)
        except BaseException as exc:
            write_new(path(".partial.bin"), getattr(exc, "raw", b""))
            save(path(".error.json"), {"error": type(exc).__name__ + ": " + str(exc),
                 "utc": utc(), "request_not_sent": isinstance(exc, Cutoff)})
            raise
        write_new(path(".response.bin"), raw)
        error = None
        try:
            result = json.loads(raw)
            if status != 200 or not isinstance(result, dict):
                raise ValueError("HTTP " + str(status) + " or invalid JSON object")
        except (ValueError, UnicodeError) as exc:
            error = str(exc)
        save(path(".done.json"), {"http_status": status, "response_sha256": sha(raw),
             "error": error, "seconds": time.monotonic()-started, "utc": utc()})
        if error:
            raise TransportError(error)
        return result

def continue_units(data, client, workers=4):
    units = r2.strict_rows(data / r2.UNITS)
    good, bad = r2.strict_rows(data / r2.DONE), r2.strict_rows(data / r2.FAILED)
    done = r2.validate_results(units, good + bad)
    if any(not x["accepted"] for x in good) or any(x["accepted"] for x in bad):
        raise ValueError("ledger classification changed")
    order = list(units)
    random.Random(1831).shuffle(order)
    todo = [u for u in order if u["id"] not in done]
    print(json.dumps({"event": "continuation", "utc": utc(), "workers": workers,
                      **r2.gate(units, good, bad)}), flush=True)
    count = 0
    for row in r2.generate_units(todo, client, workers, 1831):
        with (data / (r2.DONE if row["accepted"] else r2.FAILED)).open("ab") as f:
            f.write(json_bytes(row))
            f.flush()
            os.fsync(f.fileno())
        (good if row["accepted"] else bad).append(row)
        count += 1
        if count == 1 or count % 25 == 0:
            print(json.dumps({"event": "progress", "utc": utc(), **r2.gate(units, good, bad)}), flush=True)
    return r2.gate(units, good, bad)

def verify_gpu():
    raw = subprocess.check_output(["/usr/lib/wsl/lib/nvidia-smi", "-q", "-x"], timeout=20)
    doc = ET.fromstring(raw)
    gpus = doc.findall("gpu")
    if len(gpus) != 1 or "3090" not in gpus[0].findtext("product_name", ""):
        raise RuntimeError("expected one RTX 3090")
    gpu = gpus[0]
    used = int(gpu.findtext("fb_memory_usage/used").split()[0])
    compute = [p for p in gpu.findall("processes/process_info") if "C" in p.findtext("type", "")]
    if used > 1024 or compute:
        raise RuntimeError("card is not available: " + str(used) + " MiB, compute=" + str(len(compute)))
    return raw

class OwnedServer:
    def __init__(self, job, argv, env, port=8082):
        self.job, self.argv, self.env, self.port = job, argv, env, port
        self.proc = None
        self.pidfd = None

    def identity(self):
        if self.proc is None or self.proc.poll() is not None:
            return False
        try:
            proc = Path("/proc") / str(self.proc.pid)
            return (os.readlink(proc / "exe") == os.path.realpath(self.argv[0]) and
                    (proc / "cmdline").read_bytes() == ("\0".join(self.argv)+"\0").encode())
        except OSError:
            return False

    def start(self):
        listener = subprocess.check_output(["ss", "-ltnp", "sport = :" + str(self.port)], text=True, timeout=10)
        if "LISTEN" in listener:
            raise RuntimeError("8082 occupied; preserve existing process")
        write_new(self.job / "gpu-before.xml", verify_gpu())
        out = (self.job / "server-stdout.log").open("xb")
        err = (self.job / "server-stderr.log").open("xb")
        child = Path(__file__).with_name("hegelizer_owned_child.py")
        try:
            self.proc = subprocess.Popen([sys.executable, "-B", str(child), str(os.getpid()), *self.argv],
                         env=self.env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                         start_new_session=True, close_fds=True)
            self.pidfd = os.pidfd_open(self.proc.pid)
        finally:
            out.close()
            err.close()
        save(self.job / "SERVER-START.json", {"pid": self.proc.pid, "argv": self.argv, "utc": utc()})
        until = time.monotonic() + 240
        while time.monotonic() < until:
            if self.proc.poll() is not None:
                raise RuntimeError("owned server exited during load: " + str(self.proc.returncode))
            if self.identity():
                try:
                    with urllib.request.urlopen("http://127.0.0.1:" + str(self.port) + "/health", timeout=3) as resp:
                        ready = json.load(resp)
                    if ready.get("status") == "ok":
                        with urllib.request.urlopen("http://127.0.0.1:" + str(self.port) + "/slots", timeout=3) as resp:
                            slots = json.load(resp)
                        if len(slots) != 4 or any(s["n_ctx"] != 16384 or s.get("is_processing") for s in slots):
                            raise RuntimeError("four idle 16K slots not established")
                        with urllib.request.urlopen("http://127.0.0.1:" + str(self.port) + "/props", timeout=3) as resp:
                            props = json.load(resp)
                        if props.get("lora_adapters"):
                            raise RuntimeError("unexpected adapter")
                        save(self.job / "SERVER-READY.json", {"utc": utc(), "slots": slots, "props": props})
                        return
                except (OSError, ValueError):
                    pass
            time.sleep(1)
        raise RuntimeError("owned server not ready before startup deadline")

    def stop(self):
        if self.proc is None:
            return {"spawned": False}
        if self.proc.poll() is None:
            save(self.job / "SERVER-STOP-INTENT.json", {"pid": self.proc.pid, "utc": utc(), "signal": "SIGTERM"})
            signal.pidfd_send_signal(self.pidfd, signal.SIGTERM)
        try:
            code = self.proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            return {"pid": self.proc.pid, "exit_confirmed": False}
        finally:
            if self.pidfd is not None:
                os.close(self.pidfd)
        result = {"pid": self.proc.pid, "exit_confirmed": True, "exit_code": code, "utc": utc()}
        save(self.job / "SERVER-END.json", result)
        return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True, type=Path)
    args = parser.parse_args()
    job = args.job.resolve()
    plan = json.loads((job / "PLAN.json").read_bytes())
    if plan["mode"] != "exclusive-paused" or plan["workers"] != 4:
        raise SystemExit("only explicitly authorized four-worker paused mode")
    cutoff = DeadlinePolicy(plan)
    if time.time() + 1200 >= cutoff():
        raise SystemExit("insufficient safe time before cutoff")
    for name, digest in plan["source_sha256"].items():
        if sha((Path(__file__).resolve().parents[1] / name).read_bytes()) != digest:
            raise SystemExit("frozen source changed: " + name)
    for name, digest in plan["initial_data_sha256"].items():
        if sha((job / "data" / name).read_bytes()) != digest:
            raise SystemExit("initial data changed; a new continuation is required")
    records = reconcile_raw(job / "legacy-raw")
    if len(records) != plan["legacy_request_count"] or {r["url"] for r in records} != {plan["legacy_url"]}:
        raise SystemExit("legacy receipt set changed")
    if (job / "raw").exists() and list((job / "raw").iterdir()):
        raise SystemExit("one-shot run already has requests; reconcile before continuation")
    if (job / "RUN-start.json").exists():
        raise SystemExit("this one-shot session already started")
    model = Path(plan["argv"][2])
    before = model.stat()
    with model.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    after = model.stat()
    if digest != plan["model_sha256"] or (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns):
        raise SystemExit("model bytes changed")
    if sha(Path(plan["argv"][0]).read_bytes()) != plan["binary_sha256"]:
        raise SystemExit("binary changed")
    # The shared 8082 startup lock is also used by Hegel's installed launcher.
    lockpath = Path.home() / ".local/state/hegel-qwen/startup.lock"
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    lock = lockpath.open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = plan["cuda"]
    server = OwnedServer(job, plan["argv"], env)
    result = {"utc_start": utc(), "outcome": "FAILED", "gate": None}
    save(job / "RUN-start.json", {"utc": utc(), "pid": os.getpid(), "plan_sha256": sha((job / "PLAN.json").read_bytes())})
    client = None
    try:
        # Validate the ledgers before consuming GPU memory.
        units = r2.strict_rows(job/"data"/r2.UNITS)
        r2.gate(units, r2.strict_rows(job/"data"/r2.DONE), r2.strict_rows(job/"data"/r2.FAILED))
        server.start()
        client = ExclusiveClient(job/"raw", job/"legacy-raw", plan["legacy_url"],
                                 BoundedHTTP(server.identity), cutoff, plan["timeout"])
        gate = continue_units(job/"data", client)
        result.update(gate=gate, outcome="COMPLETE_PASS" if gate["passed"] else "COMPLETE_GATE_FAILED")
    except Cutoff as exc:
        result.update(outcome="PAUSED_CUTOFF", error=str(exc))
    except BaseException as exc:
        result.update(error=type(exc).__name__+": "+str(exc))
        if client and client.cutoff_reached:
            result["outcome"] = "PAUSED_CUTOFF"
    finally:
        if client:
            client.stop.set()
            result["replayed_request_ids"] = sorted(client.replayed)
        result["server_end"] = server.stop()
        result["utc_finish"] = utc()
        save(job / "RUN-end.json", result)
        print(json.dumps(result), flush=True)
        lock.close()
    return 0 if result["outcome"] == "COMPLETE_PASS" and result["server_end"].get("exit_confirmed") else 1

if __name__ == "__main__":
    raise SystemExit(main())
