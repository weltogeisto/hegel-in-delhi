"""WSL: the fast lane, night 3 (W15, pc/FAST-LANE-NIGHT3.md): main's engine (f34e42b0, the repaired packet) with Day 57's saved
morning (shadow at 'Day 57 begins'); arms off, on (+HEGEL_EXITS=1) and lookup (+HEGEL_EXITS=1, HEGEL_BORROWED_LOOKUP=1).
python3 night3_setup.py MORNING_COMMIT MODEL_SHA256   (reads night3-engine.tar and night3-morning.tar from the scratchpad)"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
WSP = Path("/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad")
B = Path("/home/ai/night3"); DATE, PREV = "2026-11-27", "2026-11-26"; MC, MODEL = sys.argv[1], sys.argv[2]
if B.exists(): sys.exit(f"{B} exists")
for d in ("engine", "morning", "m"): (B / d).mkdir(parents=True)
subprocess.run(["tar", "-xf", str(WSP / "night3-engine.tar"), "-C", str(B / "engine")], check=True)
subprocess.run(["tar", "-xf", str(WSP / "night3-morning.tar"), "-C", str(B / "m"), "docs"], check=True)
shutil.copytree(B / "m" / "docs", B / "morning", dirs_exist_ok=True); shutil.rmtree(B / "m")
h = hashlib.sha256(); files = sorted(x for x in (B / "morning").rglob("*") if x.is_file())
for p in files:
    h.update(str(p.relative_to(B / "morning")).encode() + b"\0" + hashlib.sha256(p.read_bytes()).hexdigest().encode() + b"\n")
assert json.loads((B / "morning" / "days" / f"{PREV}.json").read_text()).get("complete"), "Day 56 not complete in the saved morning"
morning = {"commit": MC, "note": "shadow at 'Day 57 begins'", "files": len(files), "tree_sha256": h.hexdigest(),
           "previous_day": PREV, "previous_complete": True, "date": DATE}
# Every switch as the Pi runs on Day 56 (its env, read 25 Nov 23:20), less the clock shift and the pause while the PC is away.
BASE = ["HEGEL_SOUL_FILE=mind/soul-ordinary.md", "HEGEL_DECISION_DRAWS=4", "HEGEL_CORRESPONDENT=1", "HEGEL_STREET=1",
        "HEGEL_RAMESH_DAYS=1", "HEGEL_KEEP_DRAWS=1", "HEGEL_SHELF_ADDITIONS=1", "HEGEL_WORLD_REPAIRS=1", "HEGEL_CULTURE=1",
        "HEGEL_KEEP_TIME=1", "HEGEL_FILE_ACT=1"]
srv = []
for p in os.listdir("/proc"):
    if not p.isdigit(): continue
    try:
        if Path(f"/proc/{p}/comm").read_text().strip() != "llama-server": continue
        raw = Path(f"/proc/{p}/cmdline").read_bytes()
    except OSError: continue
    argv = raw.rstrip(b"\0").split(b"\0")
    if b"8082" in argv:
        srv.append({"pid": int(p), "argv": [a.decode() for a in argv], "argv_sha256": hashlib.sha256(raw).hexdigest(), "cwd": os.readlink(f"/proc/{p}/cwd")})
assert len(srv) == 1, srv
srv = srv[0]; srv["model_sha256"] = MODEL
srv["pin_matches"] = srv["argv_sha256"] == "1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0"
for arm, sw in (("off", BASE), ("on", BASE + ["HEGEL_EXITS=1"]), ("lookup", BASE + ["HEGEL_EXITS=1", "HEGEL_BORROWED_LOOKUP=1"])):
    a = B / arm; a.mkdir()
    (a / "engine").symlink_to(B / "engine"); (a / "morning").symlink_to(B / "morning")
    (a / "ENGINE").write_text(f"f34e42b0 (git archive of main, the repaired packet) with the morning of shadow {MC[:7]}\n")
    (a / "MORNING.json").write_text(json.dumps(morning, indent=1) + "\n")
    (a / "SWITCHES.json").write_text(json.dumps(sw) + "\n")
    (a / "SERVER.json").write_text(json.dumps(srv, indent=1) + "\n")
    for f in ("night3_run.py", "night3_run.sh", "night2_finish.py"): shutil.copyfile(WSP / f, a / f)
print("SERVER", json.dumps({k: srv[k] for k in ("pid", "argv_sha256", "pin_matches")}))
print("MORNING", json.dumps(morning))
