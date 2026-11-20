"""DECISIONS 59: one arm of the exploratory fork. python3 fork59_arm.py A|B SEED
The saved morning of FORK-STANDIN.json (shadow 7dfd9bb, Days 1-50), Day 51 (2026-11-21) rehearsed once with the real mind on the trial server.
Every switch shadow runs; only HEGEL_DECISION_ADAPTER_SCALE differs between the arms (A 0, B 1); voice and writing scales empty.
The phone cache is frozen: the saved morning holds none, and a page not in it does not load, the same in both arms (no fetch).
No network but the trial server. Feeds off. Scratch folder only; nothing is pushed by the world."""
import hashlib, json, os, sys, time
from pathlib import Path
from unittest.mock import patch

arm, seed = sys.argv[1], int(sys.argv[2])
scale = {"A": "0", "B": "1"}[arm]
base = Path("/home/ai/fork59")
engine, morning = base / "engine", base / "morning"
DRY = os.environ.get("FORK59_DRY") == "1"          # a smoke test with the stand-in mind, before any server changes
out = base / ("runs-dry" if DRY else "runs") / f"seed{seed}-{arm}"
if out.exists():
    sys.exit(f"{out} exists: one run per arm and seed")
SWITCHES = ["HEGEL_SOUL_FILE=mind/soul-ordinary.md", "HEGEL_DECISION_DRAWS=4", "HEGEL_CORRESPONDENT=1", "HEGEL_STREET=1",
            "HEGEL_RAMESH_DAYS=1", "HEGEL_KEEP_DRAWS=1", "HEGEL_SHELF_ADDITIONS=1", "HEGEL_WORLD_REPAIRS=1"]   # the Pi's env, 20 Nov 23:50
URL, PORT = "http://127.0.0.1:18802", 18802
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


def audit(name, args):
    if name == "socket.getaddrinfo":
        if str(args[0]) not in ("127.0.0.1",):
            blocked.append(f"{name} {args[0]}"); raise RuntimeError("network forbidden in the fork")
    elif name in ("socket.connect", "socket.sendto"):
        a = args[1]
        if not (isinstance(a, tuple) and a[:2] == ("127.0.0.1", PORT)):
            blocked.append(f"{name} {a!r}"); raise RuntimeError("network forbidden in the fork")


def frozen_fetch(url, timeout=10):
    lookups.append(url)
    raise OSError("frozen phone cache: not in the saved morning")


sys.addaudithook(audit)
sets = sum((["--set", s] for s in SWITCHES + [f"HEGEL_DECISION_ADAPTER_SCALE={scale}"]), [])
argv = ["world", "simulate", "--date", "2026-11-21", "--days", "1", "--docs", str(morning), "--out", str(out), "--mind", "stub:walker" if DRY else URL, "--seed", str(seed)] + sets
t0 = time.time()
with patch.object(sys, "argv", argv), patch("world.lookup.fetch", frozen_fetch):
    rc = app.main()
secs = round(time.time() - t0, 1)
day = json.loads((out / "days/2026-11-21.json").read_text(encoding="utf-8"))
steps = [s for s in day["steps"] if "decision" in s]
sources = {}
for s in steps:
    sources[s["mind"]["source"]] = sources.get(s["mind"]["source"], 0) + 1
rec = {"arm": arm, "seed": seed, "HEGEL_DECISION_ADAPTER_SCALE": scale, "switches": SWITCHES, "argv": argv[1:], "rc": rc, "seconds": secs,
       "engine": (base / "ENGINE").read_text().strip(), "morning_sha256": (base / "MORNING").read_text().strip(),
       "complete": day.get("complete"), "decisions": len(steps), "sources": sources,
       "phone_lookups_refused": len(lookups), "network_blocked": blocked, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
(out / "FORK-RUN.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
print("FORK-ARM", json.dumps(rec))
sys.exit(0 if rc in (None, 0) and not blocked else 1)
