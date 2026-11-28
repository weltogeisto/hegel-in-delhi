"""The fast lane, night 4 (pc/FAST-LANE-NIGHT4.md, W21): one future of one arm.  NIGHT2_BASE=<arm base> python3 night4_run.py SEED
As night 3's night3_run.py (simulate --days 14 from the saved morning, every switch of SWITCHES.json, the live server 127.0.0.1:8082 never
restarted, prompt cache off by --seed, phone cache frozen, no feeds, no network but the live server), plus one thing the order asks for:
every call to the server is timed and written to logs/SEED.calls.jsonl (its kind, so the writing calls' latency can be read apart).
NIGHT2_DRY=1: the stand-in mind (stub:walker) and 2 days, for a smoke test only. Scratch folder only; nothing reaches his world."""
import json, os, sys, time
from pathlib import Path
from unittest.mock import patch

seed = int(sys.argv[1])
DATE = os.environ["NIGHT2_DATE"]
base = Path(os.environ["NIGHT2_BASE"])
engine, morning = base / "engine", base / "morning"
DRY = os.environ.get("NIGHT2_DRY") == "1"
out = base / ("futures-dry" if DRY else "futures") / str(seed)
if out.exists():
    sys.exit(f"{out} exists: one future per seed")
SWITCHES = json.loads((base / "SWITCHES.json").read_text())
URL, PORT = "http://127.0.0.1:8082", 8082
for k in list(os.environ):
    if k.startswith(("HEGEL_", "MIND_", "OWL_", "PC_", "NEWS_")) or k.lower() in ("http_proxy", "https_proxy", "all_proxy"):
        del os.environ[k]
os.environ["NO_PROXY"] = os.environ["no_proxy"] = "*"
os.environ["HEGEL_ENV"] = str(base / "no-env-file")
os.environ["HEGEL_REPO"] = str(engine)
sys.path.insert(0, str(engine))
os.chdir(engine)
from world import __main__ as app
from world import mind as mind_mod

blocked, lookups = [], []
(base / "logs").mkdir(exist_ok=True)
CALLS = open(base / "logs" / f"{seed}{'-dry' if DRY else ''}.calls.jsonl", "a", encoding="utf-8")
_post = mind_mod.HTTPMind._post


def timed_post(self, path, payload, kind=None):
    t0, err, data = time.time(), None, None
    try:
        data = _post(self, path, payload, kind)
        return data
    except Exception as e:
        err = type(e).__name__
        raise
    finally:
        usage = (data or {}).get("usage") or {}
        timings = (data or {}).get("timings") or {}
        CALLS.write(json.dumps({"t": time.strftime("%H:%M:%S"), "at": getattr(self, "stream_at", None), "kind": kind, "path": path,
                                "secs": round(time.time() - t0, 2), "max_tokens": payload.get("max_tokens") or payload.get("n_predict"),
                                "reasoning_budget": payload.get("reasoning_budget_tokens", 0),
                                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                                "predicted_n": timings.get("predicted_n"), "error": err}) + "\n")
        CALLS.flush()


def audit(ev, args):
    if ev == "socket.getaddrinfo":
        if str(args[0]) not in ("127.0.0.1",):
            blocked.append(f"{ev} {args[0]}"); raise RuntimeError("network forbidden in the rehearsal")
    elif ev in ("socket.connect", "socket.sendto"):
        a = args[1]
        if not (isinstance(a, tuple) and a[:2] == ("127.0.0.1", PORT)):
            blocked.append(f"{ev} {a!r}"); raise RuntimeError("network forbidden in the rehearsal")


def frozen_fetch(url, timeout=10):
    lookups.append(url)
    raise OSError("frozen phone cache: not in the saved morning")


sys.addaudithook(audit)
sets = sum((["--set", s] for s in SWITCHES), [])
argv = ["world", "simulate", "--date", DATE, "--days", "2" if DRY else os.environ.get("NIGHT2_DAYS", "14"), "--docs", str(morning), "--out", str(out),
        "--mind", "stub:walker" if DRY else URL, "--seed", str(seed)] + sets
(base / f"START-{seed}{'-dry' if DRY else ''}.json").write_text(json.dumps(
    {"seed": seed, "argv": argv[1:], "switches": SWITCHES, "start": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "dry": DRY}, indent=1) + "\n")
with patch.object(sys, "argv", argv), patch("world.lookup.fetch", frozen_fetch), patch.object(mind_mod.HTTPMind, "_post", timed_post):
    rc = app.main()
(base / f"END-{seed}{'-dry' if DRY else ''}.json").write_text(json.dumps(
    {"rc": rc, "end": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "phone_lookups_refused": len(lookups), "network": "none", "network_blocked": blocked}, indent=1) + "\n")
print("NIGHT2-RUN", seed, "rc", rc, "blocked", blocked)
sys.exit(0 if rc in (None, 0) and not blocked else 1)
