"""The fast lane, night 1 (pc/FAST-LANE-NIGHT1.md, W10): one one-day run.  python3 night1_run.py NAME DAY ARM SEED BLOCK
DAY is the saved morning: 50, 51 or 52 (the docs on shadow at "Day N begins", the commit that marked Day N-1 complete).
ARM: off (HEGEL_CULTURE=0), on (=1) or act (=1 with HEGEL_FILE_ACT=1, block 2); every other switch as the Pi runs on Day 53.
The live server (127.0.0.1:8082), never restarted; every slot while he sleeps (DECISIONS 62). Prompt cache off (--seed), phone cache frozen (no fetch), no feeds, no network but the live server.
NIGHT1_DRY=1: the stand-in mind (stub:walker), for a smoke test only. Scratch folder only; nothing reaches his world."""
import json, os, sys, time
from pathlib import Path
from unittest.mock import patch

name, day, arm, seed, block = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), sys.argv[5]
assert arm in ("off", "on", "act") and day in (50, 51, 52)
DATES = {50: "2026-11-20", 51: "2026-11-21", 52: "2026-11-22"}
date = DATES[day]
base = Path("/home/ai/night1")
engine, morning = base / "engine", base / "mornings" / f"day{day}"
DRY = os.environ.get("NIGHT1_DRY") == "1"
out = base / ("runs-dry" if DRY else "runs") / name
if out.exists():
    sys.exit(f"{out} exists: one run per name")
SWITCHES = ["HEGEL_SOUL_FILE=mind/soul-ordinary.md", "HEGEL_DECISION_DRAWS=4", "HEGEL_CORRESPONDENT=1", "HEGEL_STREET=1",
            "HEGEL_RAMESH_DAYS=1", "HEGEL_KEEP_DRAWS=1", "HEGEL_SHELF_ADDITIONS=1", "HEGEL_WORLD_REPAIRS=1"]   # the Pi's env for Day 53, read 21 Nov 19:55
SWITCHES = SWITCHES + {"off": ["HEGEL_CULTURE=0"], "on": ["HEGEL_CULTURE=1"], "act": ["HEGEL_CULTURE=1", "HEGEL_FILE_ACT=1"]}[arm]
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
argv = ["world", "simulate", "--date", date, "--days", "1", "--docs", str(morning), "--out", str(out),
        "--mind", "stub:walker" if DRY else URL, "--seed", str(seed)] + sets
start = time.strftime("%Y-%m-%dT%H:%M:%S%z"); t0 = time.time()
with patch.object(sys, "argv", argv), patch("world.lookup.fetch", frozen_fetch):
    rc = app.main()
secs = time.time() - t0
d = json.loads((out / f"days/{date}.json").read_text(encoding="utf-8"))
steps = [s for s in d["steps"] if "decision" in s]
sources, attempts, mind_s, draws, refused = {}, 0, 0.0, 0, 0
for s in steps:
    m = s.get("mind") or {}
    sources[m.get("source")] = sources.get(m.get("source"), 0) + 1
    attempts += m.get("attempts") or 0
    mind_s += m.get("latency_s") or 0
    dr = m.get("draws") or {}
    draws += dr.get("n") or 0
    refused += dr.get("refused") or 0
srv = json.loads((base / "SERVER.json").read_text())
rec = {"name": name, "block": block, "morning_day": day, "date": date, "arm": arm, "culture": 0 if arm == "off" else 1,
       "file_act": int(arm == "act"), "seed": seed, "rc": rc,
       "commit": (base / "ENGINE").read_text().split()[0], "morning": json.loads((base / "MORNINGS.json").read_text())[str(day)],
       "model_sha256": srv["model_sha256"], "server_argv": srv["argv"], "server_argv_sha256": srv["argv_sha256"], "server_pid": srv["pid"],
       "server": URL + " (live, no adapter)", "concurrency": "every slot of the live server (DECISIONS 62); slot samples in slots.txt",
       "prompt_cache": False, "phone_cache": "frozen", "feeds": False, "switches": SWITCHES, "argv": argv[1:],
       "start": start, "end": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "wall_minutes": round(secs / 60, 2),
       "mind_seconds": round(mind_s, 1), "complete": d.get("complete"), "decisions": len(steps), "sources": sources,
       "attempts": attempts, "draws": draws, "draws_refused": refused, "phone_lookups_refused": len(lookups),
       "network_blocked": blocked, "dry": DRY}
(out / "RUN.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("NIGHT1-RUN", json.dumps(rec, ensure_ascii=False)[:400])
sys.exit(0 if rc in (None, 0) and not blocked else 1)
