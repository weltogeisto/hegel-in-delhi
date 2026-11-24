"""WSL: the engine and Day 55's saved morning from one shadow commit, the switches, the server's identity.
python3 night2_setup.py COMMIT MODEL_SHA256 [dry]   (reads night2-engine.tar, the git archive of COMMIT, from the scratchpad)"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

WSP = Path("/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad")
b = Path(os.environ.get("NIGHT2_BASE", "/home/ai/night2"))
from datetime import date, timedelta
DATE = os.environ.get("NIGHT2_DATE", "2026-11-25")
PREV = (date.fromisoformat(DATE) - timedelta(days=1)).isoformat()
commit, model_sha = sys.argv[1], sys.argv[2]
if (b / "engine").exists():
    sys.exit(f"{b}/engine exists")
for d in ("engine", "morning", "futures", "logs"):
    (b / d).mkdir(parents=True, exist_ok=True)
subprocess.run(["tar", "-xf", str(WSP / "night2-engine.tar"), "-C", str(b / "engine")], check=True)
shutil.copytree(b / "engine" / "docs", b / "morning", dirs_exist_ok=True)
(b / "ENGINE").write_text(f"{commit} (git archive of shadow at 'Day 55 begins')\n")
h = hashlib.sha256()
files = sorted(x for x in (b / "morning").rglob("*") if x.is_file())
for p in files:
    h.update(str(p.relative_to(b / "morning")).encode() + b"\0" + hashlib.sha256(p.read_bytes()).hexdigest().encode() + b"\n")
day54 = json.loads((b / "morning" / "days" / f"{PREV}.json").read_text())
assert day54.get("complete"), f"{PREV} is not complete in the saved morning"
(b / "MORNING.json").write_text(json.dumps({"commit": commit, "files": len(files), "tree_sha256": h.hexdigest(),
                                            "previous_day": PREV, "previous_complete": True, "date": DATE}, indent=1) + "\n")
# Every switch as the Pi runs on Day 55 (its env, read 23 Nov), less the two that only the live world has: the clock shift
# (the Pi's own clock) and the pause while the PC is away. As night 1 did.
SWITCHES = ["HEGEL_SOUL_FILE=mind/soul-ordinary.md", "HEGEL_DECISION_DRAWS=4", "HEGEL_CORRESPONDENT=1", "HEGEL_STREET=1",
            "HEGEL_RAMESH_DAYS=1", "HEGEL_KEEP_DRAWS=1", "HEGEL_SHELF_ADDITIONS=1", "HEGEL_WORLD_REPAIRS=1", "HEGEL_CULTURE=1",
            "HEGEL_KEEP_TIME=1", "HEGEL_FILE_ACT=1"]
(b / "SWITCHES.json").write_text(json.dumps(SWITCHES) + "\n")
for f in ("night2_run.py", "night2_run.sh", "night2_finish.py"):
    shutil.copy(WSP / f, b / f)
srv = []
for p in os.listdir("/proc"):
    if not p.isdigit():
        continue
    try:
        if Path(f"/proc/{p}/comm").read_text().strip() != "llama-server":
            continue
        raw = Path(f"/proc/{p}/cmdline").read_bytes()
    except OSError:
        continue
    argv = raw.rstrip(b"\0").split(b"\0")
    if b"8082" in argv:   # the pin hashes the raw cmdline, each argument NUL-terminated (hegel-qwen-8082-start.py)
        srv.append({"pid": int(p), "argv": [a.decode() for a in argv], "argv_sha256": hashlib.sha256(raw).hexdigest(),
                    "cwd": os.readlink(f"/proc/{p}/cwd")})
assert len(srv) == 1, srv
srv = srv[0]
srv["model_sha256"] = model_sha
srv["pin_matches"] = srv["argv_sha256"] == "1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0"
(b / "SERVER.json").write_text(json.dumps(srv, indent=1) + "\n")
print("SERVER", json.dumps({k: srv[k] for k in ("pid", "argv_sha256", "pin_matches", "model_sha256")}))
print("MORNING", (b / "MORNING.json").read_text().replace("\n", " "))
