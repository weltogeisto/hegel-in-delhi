"""Compare two rehearsal folders day by day: the state of each day, then each step's decision, in order.

    python3 tools/fork_diff.py A B [--json]

A and B are folders that hold days/ (what `python3 -m world simulate --out FOLDER` writes). Per day it says same or different; for the first
day that differs it names the first moment the decisions part (date, time, both sides), or, when the decisions agree, the state keys that differ.
The stopwatch (a step's mind.latency_s) is not compared: only `state` and each step's `decision` are. Exit 0 when identical, 1 when not.
Standard library only."""
import argparse
import json
import sys
from pathlib import Path


def load_days(folder):
    """{date: day} for every day file of a rehearsal folder (its index lists them; without an index, every YYYY-MM-DD.json)."""
    days = Path(folder) / "days"
    index = days / "index.json"
    if index.exists():
        dates = [r["date"] for r in json.loads(index.read_text(encoding="utf-8"))["days"]]
    else:
        dates = [p.stem for p in days.glob("????-??-??.json")]
    out = {}
    for d in sorted(dates):
        p = days / f"{d}.json"
        if p.exists():
            out[d] = json.loads(p.read_text(encoding="utf-8"))
    return out


def decisions(day):
    return [(s.get("t"), s["decision"]) for s in day.get("steps", []) if "decision" in s]


def brief(decision):
    if decision is None:
        return "(no step)"
    thought = (decision.get("thought") or "").replace("\n", " ")
    return f"{decision.get('action')} → {decision.get('place')}, {decision.get('minutes')} min" + (f' "{thought[:70]}"' if thought else "")


def state_keys(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def compare_day(da, db):
    """How two versions of one day part: {state_same, decisions_same, first}, where first is the first difference, or None."""
    state_same = da.get("state") == db.get("state")
    pa, pb = decisions(da), decisions(db)
    first = None
    for i in range(max(len(pa), len(pb))):
        a = pa[i] if i < len(pa) else None
        b = pb[i] if i < len(pb) else None
        if a is None or b is None or a[1] != b[1] or a[0] != b[0]:
            first = {"step": i, "t": (a or b)[0], "a": brief(a and a[1]), "b": brief(b and b[1])}
            if a and b and a[0] != b[0]:
                first["t"] = f"{a[0]} / {b[0]}"
            break
    if first is None and not state_same:
        first = {"state": state_keys(da.get("state", {}), db.get("state", {}))}
    return {"state_same": state_same, "decisions_same": first is None or "state" in first, "first": first}


def compare(a, b):
    a_days, b_days = load_days(a), load_days(b)
    rows, first = [], None
    for date in sorted(set(a_days) | set(b_days)):
        if date not in a_days or date not in b_days:
            row = {"date": date, "state_same": False, "decisions_same": False, "first": {"only_in": "A" if date in a_days else "B"}}
        else:
            row = {"date": date, **compare_day(a_days[date], b_days[date])}
        rows.append(row)
        if first is None and row["first"] is not None:
            first = {"date": date, **row["first"]}
    return {"identical": first is None, "days": rows, "first": first}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    for f in (args.a, args.b):
        if not (Path(f) / "days").is_dir():
            sys.exit(f"{f}: no days/ folder")
    result = compare(args.a, args.b)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        for r in result["days"]:
            print(f"{r['date']}  " + ("same" if r["first"] is None else "different"
                  + ("" if r["state_same"] else "  (state differs)") + ("" if r["decisions_same"] else "  (decisions differ)")))
        f = result["first"]
        if f is None:
            print("identical")
        elif "only_in" in f:
            print(f"first difference: {f['date']} exists only in {f['only_in']}")
        elif "state" in f:
            print(f"first difference: {f['date']}: the decisions agree, the state differs in {', '.join(f['state'])}")
        else:
            print(f"first difference: {f['date']} {f['t']}\n  A: {f['a']}\n  B: {f['b']}")
    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
