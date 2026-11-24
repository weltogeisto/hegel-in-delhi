"""The fast lane, night 2 (pc/FAST-LANE-NIGHT2.md, W12): one future.  python3 night2_run.py SEED
simulate --days 60 from Day 55's saved morning (the docs on shadow at "Day 55 begins"), every switch as the Pi runs on Day 55.
The live server (127.0.0.1:8082), never restarted; prompt cache off (--seed), phone cache frozen, no feeds, no network but the
live server. It runs until the driver stops it (07:30/07:45) or the 60 days are done; the driver writes RUN.json afterwards.
NIGHT2_DRY=1: the stand-in mind (stub:walker) and 2 days, for a smoke test only. Scratch folder only; nothing reaches his world."""
import json, os, sys, time
from pathlib import Path
from unittest.mock import patch

seed = int(sys.argv[1])
DATE = os.environ.get("NIGHT2_DATE", "2026-11-25")
base = Path(os.environ.get("NIGHT2_BASE", "/home/ai/night2"))
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

blocked, lookups = [], []


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
argv = ["world", "simulate", "--date", DATE, "--days", "2" if DRY else os.environ.get("NIGHT2_DAYS", "60"), "--docs", str(morning), "--out", str(out),
        "--mind", "stub:walker" if DRY else URL, "--seed", str(seed)] + sets
(base / f"START-{seed}{'-dry' if DRY else ''}.json").write_text(json.dumps(
    {"seed": seed, "argv": argv[1:], "switches": SWITCHES, "start": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "dry": DRY}, indent=1) + "\n")
with patch.object(sys, "argv", argv), patch("world.lookup.fetch", frozen_fetch):
    rc = app.main()
(base / f"END-{seed}{'-dry' if DRY else ''}.json").write_text(json.dumps(
    {"rc": rc, "end": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "phone_lookups_refused": len(lookups), "network_blocked": blocked}, indent=1) + "\n")
print("NIGHT2-RUN", seed, "rc", rc, "blocked", blocked)
sys.exit(0 if rc in (None, 0) and not blocked else 1)
