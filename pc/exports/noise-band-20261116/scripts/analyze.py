"""W2 analysis: per-fork figures and the moment each pair of forks parts. Reads ~/w2/out/<fork>/days/2026-11-16.json."""
import json
import re
import sys
from pathlib import Path

OUT, LOGS = Path.home() / "w2/out", Path.home() / "w2/logs"
FORKS = [f for f in ("s1a", "s1b", "s1c", "s1d", "s1e", "n1", "n2", "s2", "s0") if (OUT / f / "days/2026-11-16.json").exists()]
DATE = "2026-11-16"


def day(f):
    return json.load(open(OUT / f / "days" / f"{DATE}.json", encoding="utf-8"))


def decisions(f):
    return [(s["t"], s["decision"]) for s in day(f)["steps"] if "decision" in s]


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(decisions(a), decisions(b))):
        if x != y:
            return i + 1, x[0]
    return None, None


print("| fork | seed | decisions | mind | refusals | calls per decision | draws used (of 4) | echoing draws | wall | cash |")
print("|---|---|---:|---:|---:|---:|---:|---:|---|---:|")
seeds = {"s1a": "1", "s1b": "1", "s1c": "1", "s1d": "1 (flushed)", "s1e": "1 (flushed)", "n1": "1 (cache off)", "n2": "1 (cache off)", "s2": "2", "s0": "none"}
for f in FORKS:
    d = day(f)
    steps = [s for s in d["steps"] if "decision" in s]
    mind = [s for s in steps if s["mind"]["source"] == "mind"]
    refused = sum(len(s["mind"].get("refused", [])) for s in steps)
    calls = [s["mind"].get("attempts", 1) for s in mind]
    dr = [s["mind"]["draws"] for s in mind if s["mind"].get("draws")]
    err = (LOGS / f"{f}.err").read_text() if (LOGS / f"{f}.err").exists() else ""
    m = re.search(r"Elapsed \(wall clock\) time.*: (.+)", err)
    print(f"| {f} | {seeds[f]} | {len(steps)} | {len(mind)} | {refused} | {sum(calls) / max(1, len(calls)):.2f} | "
          f"{sum(x['n'] for x in dr)}/{4 * len(dr)} | {sum(x['echo'] for x in dr)} | {m.group(1) if m else '-'} | ₹{d['state']['imprest']:,} |")
print()
print("| pair | what differs | first differing decision | at (his clock) |")
print("|---|---|---:|---|")
pairs = [("s1a", "s1b", "same seed"), ("s1a", "s1c", "same seed"), ("s1b", "s1c", "same seed"), ("s1d", "s1e", "same seed, slots flushed"), ("n1", "n2", "same seed, cache off"), ("s1a", "s2", "seed 1 / seed 2"), ("s1a", "s0", "seed 1 / none"), ("s2", "s0", "seed 2 / none")]
for a, b, why in pairs:
    if a in FORKS and b in FORKS:
        i, t = first_diff(a, b)
        print(f"| {a} / {b} | {why} | {i} | {t} |")
