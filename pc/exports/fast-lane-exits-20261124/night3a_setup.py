"""WSL: tonight's money futures (Welt's word, 24 Nov ~22:15): main's engine (4c1fdc0d, holds HEGEL_EXITS) with Day 55's saved
morning (shadow faa17f7 'Day 55 begins', the docs of night 2's archive); arms off (every switch as the Pi runs) and on (+HEGEL_EXITS=1).
python3 night3a_setup.py MODEL_SHA256"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
WSP = Path("/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad")
B = Path("/home/ai/night3a"); DATE, PREV = "2026-11-25", "2026-11-24"
if B.exists(): sys.exit(f"{B} exists")
for d in ("engine", "morning", "m"): (B / d).mkdir(parents=True)
subprocess.run(["tar", "-xf", str(WSP / "night3a-engine.tar"), "-C", str(B / "engine")], check=True)
subprocess.run(["tar", "-xf", str(WSP / "night2-engine.tar"), "-C", str(B / "m"), "docs"], check=True)
shutil.copytree(B / "m" / "docs", B / "morning", dirs_exist_ok=True); shutil.rmtree(B / "m")
h = hashlib.sha256(); files = sorted(x for x in (B / "morning").rglob("*") if x.is_file())
for p in files:
    h.update(str(p.relative_to(B / "morning")).encode() + b"\0" + hashlib.sha256(p.read_bytes()).hexdigest().encode() + b"\n")
assert json.loads((B / "morning" / "days" / f"{PREV}.json").read_text()).get("complete"), "Day 54 not complete"
morning = {"commit": "faa17f7485d7477c86173ed2bb2fb13bed6d6f0c", "note": "shadow at 'Day 55 begins', as night 2", "files": len(files),
           "tree_sha256": h.hexdigest(), "previous_day": PREV, "previous_complete": True, "date": DATE}
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
srv = srv[0]; srv["model_sha256"] = sys.argv[1]
srv["pin_matches"] = srv["argv_sha256"] == "1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0"
for arm, sw in (("off", BASE), ("on", BASE + ["HEGEL_EXITS=1"])):
    a = B / arm; a.mkdir()
    (a / "engine").symlink_to(B / "engine"); (a / "morning").symlink_to(B / "morning")
    (a / "ENGINE").write_text("4c1fdc0d (git archive of main, holds HEGEL_EXITS) with the morning of shadow faa17f7\n")
    (a / "MORNING.json").write_text(json.dumps(morning, indent=1) + "\n")
    (a / "SWITCHES.json").write_text(json.dumps(sw) + "\n")
    (a / "SERVER.json").write_text(json.dumps(srv, indent=1) + "\n")
    for f in ("night3a_run.py", "night3a_run.sh"): shutil.copy(WSP / f, a / f)
    shutil.copy(WSP / "night2_finish.py", a / "night2_finish.py")
print("SERVER", json.dumps({k: srv[k] for k in ("pid", "argv_sha256", "pin_matches")}))
print("MORNING", json.dumps(morning))
