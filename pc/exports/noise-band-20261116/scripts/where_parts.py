"""Where two forks first differ at any field of a step (not only the decision), ignoring the stopwatch."""
import json
import sys
from pathlib import Path

OUT = Path.home() / "w2/out"


def steps(f):
    d = json.load(open(OUT / f / "days/2026-11-16.json", encoding="utf-8"))
    return d["steps"]


def strip(x):
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if k != "latency_s"}
    if isinstance(x, list):
        return [strip(v) for v in x]
    return x


def diff(a, b, path=""):
    if type(a) != type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((f"{path}.{k}", a.get(k, "<absent>"), b.get(k, "<absent>")))
            else:
                out += diff(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [(path + "[len]", len(a), len(b))]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [(path, a, b)]


a, b = sys.argv[1], sys.argv[2]
A, B = steps(a), steps(b)
for i, (x, y) in enumerate(zip(A, B)):
    d = diff(strip(x), strip(y))
    if d:
        print(f"{a} vs {b}: step {i + 1} (t={x.get('t')}) is the first to differ; {len(d)} fields differ; the first few:")
        for p, u, v in d[:6]:
            print(f"  {p}\n    {a}: {str(u)[:110]!r}\n    {b}: {str(v)[:110]!r}")
        break
else:
    print(f"{a} vs {b}: no step differs in the {min(len(A), len(B))} steps both have")
