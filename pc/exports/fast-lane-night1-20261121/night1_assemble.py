"""runs.jsonl in the declared order from each run's row.json, and the counts.  python night1_assemble.py DESTDIR ORDERFILE
ORDERFILE lines: BLOCK NAME DAY ARM SEED (the band's two runs are block "band"; their lines go to band/runs.jsonl).
Prints: per block, complete / failed-or-stopped / declared, and the GPU minutes of the complete runs."""
import json, os, sys

dest, order = sys.argv[1], sys.argv[2]
out = {"main": [], "band": []}
count = {}
for line in open(order, encoding="utf-8"):
    p = line.split()
    if len(p) != 5:
        continue
    block, name = p[0], p[1]
    c = count.setdefault(block, {"complete": 0, "failed": 0, "declared": 0, "gpu": 0.0})
    c["declared"] += 1
    sub = "band" if block == "band" else "main"
    f = os.path.join(dest, "band" if sub == "band" else "", "runs", name, "row.json")
    if not os.path.exists(f):
        continue
    row = json.loads(open(f, encoding="utf-8").read().strip())
    out[sub].append(json.dumps(row, ensure_ascii=False))
    if row.get("killed_or_failed") or row.get("rc") not in (0, None):
        c["failed"] += 1
    else:
        c["complete"] += 1
        c["gpu"] += row.get("gpu_minutes") or 0
open(os.path.join(dest, "runs.jsonl"), "w", encoding="utf-8", newline="\n").write("".join(l + "\n" for l in out["main"]))
os.makedirs(os.path.join(dest, "band"), exist_ok=True)
open(os.path.join(dest, "band", "runs.jsonl"), "w", encoding="utf-8", newline="\n").write("".join(l + "\n" for l in out["band"]))
print(" ".join(f"{b}:{c['complete']}/{c['failed']}/{c['declared']}/{round(c['gpu'])}" for b, c in count.items()))
