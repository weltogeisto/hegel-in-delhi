"""Max and median of each column of the night's gpu-log.csv (nvidia-smi --format=csv).  python night1_gpustats.py GPU_LOG_CSV"""
import csv, statistics, sys

rows = list(csv.reader(open(sys.argv[1], encoding="utf-8")))
if len(rows) < 2:
    print("no GPU samples")
    sys.exit()
head, data = [h.strip() for h in rows[0]], [[c.strip() for c in r] for r in rows[1:] if len(r) == len(rows[0])]
out = [f"{len(data)} samples"]
for i, h in enumerate(head):
    if h == "timestamp":
        continue
    vals = [r[i] for r in data]
    if h.startswith("clocks_event_reasons") or h.startswith("clocks_throttle_reasons"):
        out.append(f"{h}: " + ", ".join(sorted(set(vals))))
        continue
    nums = []
    for v in vals:
        try:
            nums.append(float(v.split()[0]))
        except (ValueError, IndexError):
            pass
    if nums:
        unit = vals[0].split()[1] if len(vals[0].split()) > 1 else ""
        out.append(f"{h}: max {max(nums):g}{unit}, median {statistics.median(nums):g}{unit}")
    else:
        out.append(f"{h}: {vals[0]}")
print("; ".join(out))
