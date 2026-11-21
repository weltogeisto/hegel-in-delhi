"""One line of runs.jsonl from a run folder: RUN.json without the long argv lists, the health row (JSON), and the concurrency it ran at.
python3 night1_row.py RUNDIR SLOTS_TXT
gpu_minutes = wall_minutes / the mean number of busy slots while it ran (the server's GPU time shared among the runs side by side)."""
import json, sys

o, slots = sys.argv[1], sys.argv[2]
r = json.load(open(o + "/RUN.json", encoding="utf-8"))
try:
    h = json.loads(open(o + "/health.json", encoding="utf-8").read().strip().splitlines()[-1])
except Exception as e:
    h = {"error": str(e)}
busy = []
try:
    for line in open(slots, encoding="utf-8"):
        parts = line.split()
        if len(parts) >= 3 and parts[1] == "busy":
            busy.append(int(parts[2]))
except OSError:
    pass
on = [b for b in busy if b > 0]
r["slots_busy_mean"] = round(sum(on) / len(on), 2) if on else None
r["slots_busy_counts"] = {str(k): busy.count(k) for k in sorted(set(busy))}
r["gpu_minutes"] = round(r["wall_minutes"] / r["slots_busy_mean"], 2) if r.get("slots_busy_mean") else r.get("wall_minutes")
r.pop("argv", None)
r.pop("server_argv", None)
r["health"] = h
print(json.dumps(r, ensure_ascii=False))
