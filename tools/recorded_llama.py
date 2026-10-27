"""Recorded llama-server transport for round-two work; no health probes or implicit retries."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import urllib.error
import urllib.request


class TransportError(RuntimeError):
    pass


class UnknownRequest(TransportError):
    """A request began but its response was not durably recorded. Never resend it."""


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data)
        f.flush()
        import os
        os.fsync(f.fileno())


def freeze_plan(path, plan):
    """A resumed job must use the identical frozen plan, without replacing its original."""
    path, data = Path(path), json_bytes(plan)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("the frozen plan differs: use a new job, not these saved replies")
    else:
        write_new(path, data)
    return digest(data)


class LatencyGuard:
    """Read an existing natural-step observation; never make a model or Pi probe.

    The phase controller supplies an observation JSON with observed_unix, latency_s
    and limit_s measured before the phase. Missing, stale or slower observations stop
    new requests. A limit is explicit, never inferred by allowing an arbitrary slowdown.
    """
    def __init__(self, path, max_age=300, clock=time.time, limit=None):
        self.path, self.max_age, self.clock = Path(path), max_age, clock
        self.limit = limit

    def __call__(self):
        try:
            row = json.loads(self.path.read_text(encoding="utf-8"))
            observed, elapsed, limit = (float(row[k]) for k in ("observed_unix", "latency_s", "limit_s"))
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise TransportError("no valid natural-step latency observation") from e
        if not all(math.isfinite(x) for x in (observed, elapsed, limit)) or elapsed < 0 or limit <= 0:
            raise TransportError("invalid natural-step latency budget")
        age = self.clock() - observed
        if age < 0 or age > self.max_age:
            raise TransportError("natural-step latency observation is stale")
        if self.limit is None:
            self.limit = limit
        if limit != self.limit:
            raise TransportError("natural-step limit changed from its frozen baseline")
        if elapsed > limit:
            raise TransportError("natural step is slower than its frozen limit; stop new GPU work")
        return row


class RecordedClient:
    def __init__(self, url, root, timeout=300, slot=1, lora=None, model="qwen", before_request=None, opener=None):
        self.url, self.root = url.rstrip("/"), Path(root)
        self.timeout, self.slot, self.lora, self.model = timeout, slot, lora, model
        self.before_request = before_request
        self.opener = opener or urllib.request.urlopen
        if slot != 1:
            raise ValueError("round-two work uses spare slot1 only")

    def stem(self, request_id):
        return self.root / hashlib.sha256(request_id.encode("utf-8")).hexdigest()

    def post(self, request_id, payload):
        original = json_bytes(payload)
        forwarded = dict(payload, id_slot=self.slot)
        if self.lora is not None:
            forwarded["lora"] = self.lora
        data = json_bytes(forwarded)
        stem = self.stem(request_id)
        path = lambda suffix: Path(str(stem) + suffix)
        begin_path, done_path = path(".begin.json"), path(".done.json")
        if begin_path.exists():
            begin = json.loads(begin_path.read_text(encoding="utf-8"))
            if (begin["request_id"] != request_id or begin["url"] != self.url
                    or begin["original_sha256"] != digest(original) or begin["forwarded_sha256"] != digest(data)):
                raise ValueError("cached request/payload/URL differs from the frozen request")
            if path(".request.json").read_bytes() != original or path(".forwarded.json").read_bytes() != data:
                raise ValueError("cached request bytes changed")
            if not done_path.exists():
                raise UnknownRequest("request began without a saved end: reconcile " + request_id)
            done = json.loads(done_path.read_text(encoding="utf-8"))
            response = path(".response.bin").read_bytes()
            if done["response_sha256"] != digest(response):
                raise ValueError("cached response bytes changed")
            if done.get("error"):
                raise TransportError("recorded transport failure: " + done["error"])
            return json.loads(response)
        if done_path.exists():
            raise ValueError("orphan response receipt; reconcile before proceeding")
        if self.before_request:
            self.before_request()
        write_new(path(".request.json"), original)
        write_new(path(".forwarded.json"), data)
        write_new(begin_path, json_bytes({
            "request_id": request_id, "url": self.url,
            "original_sha256": digest(original), "forwarded_sha256": digest(data),
            "utc": datetime.now(timezone.utc).isoformat()
        }))
        start, raw, status, error = time.monotonic(), b"", None, None
        try:
            request = urllib.request.Request(self.url + "/v1/chat/completions", data=data,
                                             headers={"Content-Type": "application/json"})
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    raw, status = response.read(), getattr(response, "status", 200)
            except urllib.error.HTTPError as e:
                raw, status = e.read(), e.code
                raise TransportError("HTTP " + str(e.code)) from e
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("server response is not an object")
        except (OSError, urllib.error.URLError, ValueError, TransportError) as e:
            error = type(e).__name__ + ": " + str(e)
        write_new(path(".response.bin"), raw)
        write_new(done_path, json_bytes({
            "response_sha256": digest(raw), "http_status": status, "error": error,
            "seconds": time.monotonic() - start, "utc": datetime.now(timezone.utc).isoformat()
        }))
        if error:
            raise TransportError(error)
        return result

    def chat(self, request_id, messages, temperature, tokens, seed):
        payload = {"model": self.model, "messages": messages, "temperature": temperature,
                   "max_tokens": tokens, "seed": seed, "chat_template_kwargs": {"enable_thinking": False}}
        result = self.post(request_id, payload)
        try:
            choice = result["choices"][0]
            text = choice["message"].get("content")
            if not isinstance(text, str):
                raise ValueError("chat content is not text")
            return text, choice.get("finish_reason")
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            raise TransportError("saved HTTP response has no chat choice") from e
