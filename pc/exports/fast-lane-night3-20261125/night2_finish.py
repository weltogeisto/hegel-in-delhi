"""WSL, after a future has stopped: keep its complete days, drop the one in progress, write each day's health row and RUN.json,
and copy them to the branch folder.  python3 night2_finish.py SEED DEST [dry] [STOPPED_HOW]
Prints FINISH {seed, days_complete, first, last, dropped}."""
import json, shutil, subprocess, sys, time
from pathlib import Path

seed, dest = sys.argv[1], Path(sys.argv[2])
dry = len(sys.argv) > 3 and sys.argv[3] == "dry"
how = sys.argv[4] if len(sys.argv) > 4 else ""
if how.startswith("/") and Path(how).is_file():
    how = Path(how).read_text(encoding="utf-8").strip()
import os
base = Path(os.environ.get("NIGHT2_BASE", "/home/ai/night2"))
FIRST = os.environ.get("NIGHT2_DATE", "2026-11-25")
sfx = "-dry" if dry else ""
out = base / ("futures-dry" if dry else "futures") / seed
days_dir = out / "days"
files = sorted(p for p in days_dir.glob("2026-*.json")) if days_dir.exists() else []
complete, dropped = [], []
for p in files:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    (complete if d.get("complete") else dropped).append(p)
for p in files:
    if p.stem < FIRST:               # the saved morning's own days, carried by simulate: not this future's
        complete = [x for x in complete if x != p]
        dropped = [x for x in dropped if x != p]
# a complete day is one whose next day exists or which simulate marked complete; anything after the first dropped day is dropped too
if dropped:
    first_drop = min(x.name for x in dropped)
    dropped += [x for x in complete if x.name > first_drop]
    complete = [x for x in complete if x.name < first_drop]
rows = []
for p in complete:
    date = p.stem
    r = subprocess.run(["python3", "-m", "world", "report", "--health", "--json", "--floor", "1", "--docs", str(out), date],
                       cwd=base / "engine", capture_output=True, text=True)
    line = next((x for x in r.stdout.splitlines() if x.strip().startswith("{")), None)
    rows.append(json.loads(line) if line else {"date": date, "error": (r.stderr or r.stdout)[-400:]})
start = json.loads((base / f"START-{seed}{sfx}.json").read_text()) if (base / f"START-{seed}{sfx}.json").exists() else {}
end = json.loads((base / f"END-{seed}{sfx}.json").read_text()) if (base / f"END-{seed}{sfx}.json").exists() else {}
srv = json.loads((base / "SERVER.json").read_text())
rec = {"seed": int(seed), "commit": (base / "ENGINE").read_text().split()[0], "morning": json.loads((base / "MORNING.json").read_text()),
       "model_sha256": srv["model_sha256"], "server_argv": srv["argv"], "server_argv_sha256": srv["argv_sha256"],
       "server_pid": srv["pid"], "server": "http://127.0.0.1:8082 (live, no adapter, never restarted)",
       "prompt_cache": False, "phone_cache": "frozen", "feeds": False, "switches": start.get("switches"), "argv": start.get("argv"),
       "start": start.get("start"), "end": end.get("end") or time.strftime("%Y-%m-%dT%H:%M:%S%z"), "stopped": how or "ran to its end",
       "rc": end.get("rc"), "days_complete": len(complete), "first_day": complete[0].stem if complete else None,
       "last_day": complete[-1].stem if complete else None, "dropped": [p.stem for p in dropped],
       "phone_lookups_refused": end.get("phone_lookups_refused"), "network_blocked": end.get("network_blocked"), "dry": dry}
t = dest / "futures" / seed
(t / "days").mkdir(parents=True, exist_ok=True)
for p in complete:
    shutil.copyfile(p, t / "days" / p.name)
(t / "health.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
(t / "RUN.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for f in ("logs/%s.log" % seed, "logs/%s.slots.txt" % seed):
    if (base / f).exists():
        shutil.copyfile(base / f, t / Path(f).name.replace(seed + ".", ""))
print("FINISH", json.dumps({"seed": int(seed), "days_complete": len(complete), "first": rec["first_day"], "last": rec["last_day"],
                            "dropped": rec["dropped"], "health_errors": sum(1 for r in rows if "error" in r)}))
