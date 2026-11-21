"""WSL: the engine, the three saved mornings, the server's identity.  python3 night1_setup.py ENGINE_COMMIT MODEL_SHA256"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

WSP = Path("/mnt/c/Users/hendr/AppData/Local/Temp/claude/cd74254ce8d0a965/90b4347d-b5da-4fc9-99db-4ff38302b710/scratchpad")
b = Path("/home/ai/night1")
commit, model_sha = sys.argv[1], sys.argv[2]
if (b / "engine").exists():
    sys.exit(f"{b}/engine exists")
for d in ("engine", "mornings", "runs", "logs"):
    (b / d).mkdir(parents=True, exist_ok=True)
subprocess.run(["tar", "-xf", str(WSP / "night1-engine.tar"), "-C", str(b / "engine")], check=True)
(b / "ENGINE").write_text(f"{commit} (git archive)\n")
mor = json.loads((WSP / "night1-mornings.json").read_text())
for d, m in mor.items():
    root = b / "mornings" / f"day{d}"
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-xf", str(WSP / f"night1-m{d}.tar"), "-C", str(root), "--strip-components=1"], check=True)
    h = hashlib.sha256()
    files = sorted(x for x in root.rglob("*") if x.is_file())
    for p in files:
        h.update(str(p.relative_to(root)).encode() + b"\0" + hashlib.sha256(p.read_bytes()).hexdigest().encode() + b"\n")
    m["files"] = len(files)
    m["tree_sha256"] = h.hexdigest()
(b / "MORNINGS.json").write_text(json.dumps(mor, indent=1) + "\n")
for f in ("night1_run.py", "night1_run.sh", "night1_row.py"):
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
print("MORNINGS", json.dumps(mor))
