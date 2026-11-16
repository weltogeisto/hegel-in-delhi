"""Trace the first N mind calls of a seeded rehearsal: seed, a hash of the request, the first words of the reply.
    python3 trace_calls.py N LOG OUTDIR SEED
Nothing is changed: the real request goes to the real server and the reply goes back unchanged. After N calls the run is stopped."""
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

N, LOG, OUT, SEED = int(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, str(Path.home() / "w2/main"))
import world.__main__ as wm          # noqa: E402

real = urllib.request.urlopen
count = [0]


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def sha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def tap(req, timeout=None):
    if isinstance(req, str) or getattr(req, "data", None) is None:       # the health check and other GETs: untouched
        return real(req, timeout=timeout)
    payload = json.loads(req.data.decode("utf-8"))
    with real(req, timeout=timeout) as r:
        body = r.read()
    count[0] += 1
    if str(count[0]) in __import__("os").environ.get("DUMP", "").split(","):          # keep the whole request for a replay
        Path(LOG).with_name(f"{Path(LOG).stem}-payload{count[0]}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    content = (json.loads(body)["choices"][0]["message"].get("content") or "").replace("\n", " ")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"n": count[0], "seed": payload.get("seed"), "max_tokens": payload["max_tokens"], "request_sha": sha(payload),
                            "messages_sha": sha(payload["messages"]), "reply": content[:140]}, ensure_ascii=False) + "\n")
    if count[0] >= N:
        raise SystemExit(f"stopped after {N} calls")
    return Reply(body)


urllib.request.urlopen = tap
sys.argv = ["world", "simulate", "--docs", str(Path.home() / "w2/shadow-docs"), "--date", "2026-11-16", "--days", "1",
            "--mind", "http://127.0.0.1:8082", "--set", "HEGEL_DECISION_DRAWS=4", "--set", "HEGEL_CORRESPONDENT=1",
            "--seed", SEED, "--out", OUT]
wm.main()
