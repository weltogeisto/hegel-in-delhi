#!/usr/bin/env python3
"""The fast lane's night 2, read as declared (pc/FAST-LANE-NIGHT2.md): his future lived straight on, two seeds.

    python3 tools/night2_read.py --futures <folder>/futures --from 2026-11-25 --out <folder>

Each future is a folder `futures/<seed>/` whose `days/` holds the rehearsal's day files (the copied days before --from are
ignored). For each future, day by day: the health row (moments, brought, the empty share, the share at home, places,
voices), how far the day lies from the one before (`variation`), how much of its kinds and of its pairs of act and place
the five days before already had, his cash at night and its change (wages, bills, income and purchases together), the cheques he holds and what he owes, the beats
that fired, the file's line, and whether the owl wrote.

Then the first day each future shows what the declaration named: cash under ₹2,000; seven days running with no beat;
variation under 0.2 three days running; a day under the floor of thoughts; a day the owl did not write. A look ahead,
never a gate. Evaluation only: nothing here is training data. Standard library only."""
import argparse
import json
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world import health  # noqa: E402
from world.report import FLOOR  # noqa: E402

LOW_CASH = 2000
QUIET_DAYS = 7
SAME = 0.2
SAME_DAYS = 3


def day_rows(folder, start):
    """The days of one future from `start` on, in date order, one row each."""
    days_dir = Path(folder) / "days" if (Path(folder) / "days").is_dir() else Path(folder)
    days = []
    for p in sorted(days_dir.glob("????-??-??.json")):
        if p.stem >= start:
            days.append(json.loads(p.read_text(encoding="utf-8")))
    before = None
    prior = sorted(p for p in days_dir.glob("????-??-??.json") if p.stem < start)
    if prior:
        before = json.loads(prior[-1].read_text(encoding="utf-8"))
    rows, beats_before = [], list(((before or {}).get("state") or {}).get("beats") or [])
    cash_before = ((before or {}).get("state") or {}).get("imprest")
    base = [health.row(d, floor=1) for d in days]
    full = {r["date"]: r for r in health.across(base)}
    for d, h in zip(days, base):
        st = d.get("state") or {}
        beats = list(st.get("beats") or [])
        new = [b for b in beats if b not in beats_before]
        beats_before = beats
        h = full.get(d["date"]) or h or {}
        n = h.get("moments", 0)
        bought = sum(v.get("price") or 0 for v in (st.get("account") or {}).get("vouchers") or [] if v.get("date") == d["date"])
        cash = st.get("imprest")
        change = None if cash is None or cash_before is None else cash - cash_before      # wages, bills, income and purchases together
        cash_before = cash if cash is not None else cash_before
        owl = d.get("owl") or {}
        rows.append({"n": d.get("n"), "date": d["date"], "complete": bool(d.get("complete")), "moments": n, "under_floor": n < FLOOR,
                     "brought": (h.get("opens") or {}).get("brought", 0),
                     "empty_share": round((h.get("opens") or {}).get("empty", 0) / n, 3) if n else None,
                     "home_share": round(h.get("home", 0) / n, 3) if n else None,
                     "places": h.get("places"), "voices": h.get("voices"), "variation": h.get("variation"),
                     "kinds_seen_5": h.get("kinds_seen_5"), "acts_seen_5": h.get("acts_seen_5"),
                     "cash": cash, "change": change, "bought": bought,
                     "cheques": sum(c.get("amount") or 0 for c in st.get("cheques") or []),
                     "owed": sum(o.get("amount") or 0 for o in st.get("owed") or []),
                     "beats": new, "file": st.get("file"),
                     "owl": bool(isinstance(owl.get("diary"), str) and owl["diary"].strip())})
    return rows


def first_run(rows, test, length=1):
    """The date on which `test` has held for `length` days running, for the first time; None if never."""
    run = 0
    for r in rows:
        run = run + 1 if test(r) else 0
        if run >= length:
            return r["date"]
    return None


def milestones(rows):
    whole = [r for r in rows if r["complete"]]
    return {"days": len(whole),
            "cash_under": first_run(whole, lambda r: r["cash"] is not None and r["cash"] < LOW_CASH),
            "no_beat_for_a_week": first_run(whole, lambda r: not r["beats"], QUIET_DAYS),
            "same_day_again": first_run(whole, lambda r: r["variation"] is not None and r["variation"] < SAME, SAME_DAYS),
            "under_floor": first_run(whole, lambda r: r["under_floor"]),
            "owl_silent": first_run(whole[:-1], lambda r: not r["owl"])}          # the last day's owl may not have run when the night stopped


def thirds(rows, key):
    """The mean of a measure over the first, middle and last third of the days: does it drift?"""
    vals = [r[key] for r in rows if r["complete"] and r[key] is not None]
    if len(vals) < 3:
        return None
    k = len(vals) // 3
    return [round(mean(vals[:k]), 3), round(mean(vals[k:len(vals) - k]), 3), round(mean(vals[-k:]), 3)]


def fmt(x, share=False):
    if x is None:
        return "–"
    return f"{100 * x:.0f}%" if share else (f"{x:.2f}" if isinstance(x, float) else f"{x:,}" if isinstance(x, int) else str(x))


def report(futures):
    lines = ["# Night 2: his future, lived straight on", "",
             "Declared in `pc/FAST-LANE-NIGHT2.md` before any run. A look ahead, never a gate. Evaluation only.", ""]
    out = {}
    for seed, rows in sorted(futures.items()):
        m = milestones(rows)
        drift = {k: thirds(rows, k) for k in ("home_share", "empty_share", "brought", "variation", "acts_seen_5", "change", "moments")}
        out[seed] = {"milestones": m, "thirds": drift, "days": rows}
        whole = [r for r in rows if r["complete"]]
        lines += [f"## Seed {seed}: {m['days']} days", ""]
        if whole:
            changes = [r["change"] for r in whole if r["change"] is not None]
            lines += [f"- **Money:** ₹{fmt(whole[0]['cash'])} on the first night, ₹{fmt(whole[-1]['cash'])} on the last; "
                      f"{fmt(round(mean(changes))) if changes else '–'} a day on average, all in and out; "
                      f"cheques held at the end ₹{fmt(whole[-1]['cheques'])}; owed ₹{fmt(whole[-1]['owed'])}.",
                      f"- **Beats fired:** {sum(len(r['beats']) for r in whole)} on {sum(1 for r in whole if r['beats'])} days. "
                      f"The file at the end: {whole[-1]['file']}"]
        named = {"cash_under": f"cash under ₹{LOW_CASH:,}", "no_beat_for_a_week": "seven days with no beat",
                 "same_day_again": f"variation under {SAME} three days running", "under_floor": f"a day under {FLOOR} thoughts",
                 "owl_silent": "a day the owl did not write"}
        lines += ["- **First seen:** " + "; ".join(f"{label}: {m[k] or 'never'}" for k, label in named.items()) + ".", "",
                  "| Measure | First third | Middle | Last third |", "|---|---:|---:|---:|"]
        for k, label, share in (("moments", "moments", False), ("home_share", "at home", True), ("empty_share", "empty", True),
                                ("brought", "brought", False), ("variation", "variation from the day before", False),
                                ("acts_seen_5", "acts already seen in the five days before", True), ("change", "₹ change a day", False)):
            if drift[k]:
                lines.append(f"| {label} | " + " | ".join(fmt(x, share) for x in drift[k]) + " |")
        lines += ["", "| Day | Date | Moments | At home | Empty | Brought | Variation | ₹ at night | ₹ change | Beats | Owl |",
                  "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
        for r in rows:
            lines.append(f"| {r['n']} | {r['date']} | {r['moments']}{'' if r['complete'] else ' (cut)'} | {fmt(r['home_share'], True)} | "
                         f"{fmt(r['empty_share'], True)} | {r['brought']} | {fmt(r['variation'])} | {fmt(r['cash'])} | {fmt(r['change'])} | "
                         f"{', '.join(r['beats']) or '–'} | {'yes' if r['owl'] else 'no'} |")
        lines.append("")
    return "\n".join(lines), out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--futures", required=True)
    ap.add_argument("--from", dest="start", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    futures = {p.name: day_rows(p, a.start) for p in sorted(Path(a.futures).iterdir()) if p.is_dir()}
    text, res = report(futures)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "RESULT.md").write_text(text, encoding="utf-8")
    (out / "result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({seed: r["milestones"] for seed, r in res.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
