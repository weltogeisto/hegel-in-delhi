#!/usr/bin/env python3
"""The fast lane's night 1, read as declared (pc/FAST-LANE-NIGHT1.md): the museums off and on, from saved mornings.

    python3 tools/night1_read.py --runs <folder>/runs --out <folder> [--db <runs.sqlite>]

Each run is a folder `runs/<day>-<arm>-<seed>/` holding the fork's day file (in `days/` or beside RUN.json) and RUN.json.
The arm is `off`/`on` or `0`/`1`; RUN.json's `morning`, `seed` and `switches` win over the folder's name when given.

Per run: the health row of world/health.py (taken with a floor of one, and a day under world.report.FLOOR thoughts is
named), the share of moments at home (the primary), cash spent (the day's vouchers), calls and refusals per decision, his
moments at the four venues, the galleries seen, the parts of performances watched and the tickets bought.

Reported, as declared: for each morning and arm the median, the interquartile range and the range; on against off as the
mean of the within-morning differences of means, with a 95% bootstrap interval that resamples runs within each morning
and arm, and the probability that an "on" run exceeds an "off" run of the same morning; and every run's own line, with a
day that changes regime (at home for at least 80% of his moments, or for at most 20%) named. Block 1 is read alone,
then pooled with block 3 (more seeds) when it ran. Block 2 (`<day>-act-<seed>`, `HEGEL_FILE_ACT=1` beside the museums)
is read against block 1's "on" runs of its mornings, with the act's beats that fired, the flags they set and the file's
line at night. A read, never a gate.
Evaluation only: nothing here is training data. Standard library only."""
import argparse
import json
import random
import re
import sqlite3
import sys
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.prompt_screen import DOCTRINE  # noqa: E402
from world import health  # noqa: E402
from world.report import FLOOR  # noqa: E402

VENUES = ("national_museum", "ngma", "habitat", "kamani")
SEED = 1831
SEEDS1 = (1831, 2718, 3141, 1618, 1414, 1732, 2236, 2645)     # block 1's eight (pc/FAST-LANE-NIGHT1.md)
BOOT = 10000
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
ARM = {"off": "off", "0": "off", "on": "on", "1": "on", "act": "act"}
ACT = json.loads((Path(__file__).resolve().parents[1] / "world/data/plot_file_act.json").read_text(encoding="utf-8"))["beats"]
ACT_IDS = tuple(b["id"] for b in ACT)
ACT_FLAGS = tuple(sorted({k for b in ACT for side in ("yes", "no") for k in ((b.get("choice") or {}).get(side) or {}).get("flags", {})}
                        | {k for b in ACT for k in (b.get("flags") or {})}))
METRICS = (  # (key, label, the share of moments?) in the order of the report; the first is the primary
    ("home_share", "share of moments at home (primary)", True),
    ("brought", "moments brought by the world", False),
    ("empty_share", "share of empty moments", True),
    ("moments", "moments decided with a mind", False),
    ("place_bits", "place entropy, bits", False),
    ("voices", "voices that spoke", False),
    ("switches", "changes of act", False),
    ("dwell_all", "median minutes of a run of one act", False),
    ("cash_spent", "cash spent, ₹", False),
    ("calls_per_decision", "calls per decision", False),
    ("refused", "draws refused", False),
    ("doctrine_per_thought", "lecture-hall terms per thought", False),
    ("venue_moments", "moments at the four venues", False),
    ("galleries", "galleries seen", False),
    ("stage_parts", "parts of performances watched", False),
    ("tickets", "tickets bought", False),
)


def day_file(folder):
    """The fork's own day: the latest-dated day file in `days/`, or beside RUN.json."""
    folder = Path(folder)
    for where in (folder / "days", folder):
        files = sorted(p for p in where.glob("*.json") if DATE.match(p.name)) if where.is_dir() else []
        if files:
            return files[-1]
    raise FileNotFoundError(f"no day file in {folder}")


def identify(folder):
    """(morning, arm, seed, run) from RUN.json, falling back on the folder's name <day>-<arm>-<seed>."""
    folder = Path(folder)
    run = json.loads((folder / "RUN.json").read_text(encoding="utf-8")) if (folder / "RUN.json").exists() else {}
    parts = folder.name.split("-")
    morning, arm, seed = (parts + [None, None, None])[:3] if len(parts) >= 3 else (None, None, None)
    if isinstance(morning, str) and morning.startswith("day"):
        morning = morning[3:]                                  # the PC seat's names: day50-off-1831
    sw = run.get("switches") or {}
    if isinstance(sw, list):                                   # ["HEGEL_CULTURE=1", ...]
        sw = dict(x.split("=", 1) for x in sw if "=" in x)
    if isinstance(sw, dict) and "HEGEL_CULTURE" in sw:
        arm = str(sw["HEGEL_CULTURE"])
    if isinstance(sw, dict) and str(sw.get("HEGEL_FILE_ACT", "0")).lower() in ("1", "yes", "true"):
        arm = "act"
    arm = ARM.get(str(run.get("arm", arm)).lower())
    if arm is None:
        raise ValueError(f"{folder.name}: no arm (off/on or 0/1)")
    m = run.get("morning_day", run.get("morning"))
    morning = str(m if isinstance(m, (str, int)) else morning)
    seed = int(run.get("seed", seed))
    return morning, arm, seed, run


def measure(day):
    """One run's numbers, from its day file."""
    row = health.row(day, DOCTRINE, floor=1) or {}
    n = row.get("moments", 0)
    steps = [s for s in day.get("steps") or [] if "decision" in s and (s.get("mind") or {}).get("source") in health.MINDS]
    state = day.get("state") or {}
    today = state.get("today") or {}
    vouchers = (state.get("account") or {}).get("vouchers") or []
    minds = [s.get("mind") or {} for s in steps]
    return {
        "moments": n, "under_floor": n < FLOOR,
        "home_share": row.get("home", 0) / n if n else None,
        "brought": row.get("opens", {}).get("brought", 0),
        "empty_share": row.get("opens", {}).get("empty", 0) / n if n else None,
        "place_bits": row.get("place_bits"), "voices": row.get("voices"), "switches": row.get("switches"),
        "dwell_all": row.get("dwell_all"),
        "cash_spent": sum(v.get("price") or 0 for v in vouchers if v.get("date") == day.get("date")),
        "calls_per_decision": mean(m.get("attempts") or 1 for m in minds) if minds else None,
        "refused": sum((m.get("draws") or {}).get("refused", 0) for m in minds),
        "doctrine_per_thought": row["doctrine"] / n if n and row.get("doctrine") is not None else None,
        "venue_moments": sum(1 for s in steps if s["decision"].get("place") in VENUES),
        "venues": sorted({s["decision"]["place"] for s in steps if s["decision"].get("place") in VENUES}),
        "galleries": sum((today.get("sights") or {}).values()),
        "stage_parts": sum(len(v) for v in (today.get("stage") or {}).values()),
        "tickets": len(today.get("tickets") or []),
        "act_beats": [b for b in ACT_IDS if b in (state.get("beats") or [])],
        "act_flags": {k: (state.get("flags") or {})[k] for k in ACT_FLAGS if k in (state.get("flags") or {})},
        "file": state.get("file"),
    }


def load(runs_dir):
    out = []
    for folder in sorted(p for p in Path(runs_dir).iterdir() if p.is_dir()):
        morning, arm, seed, run = identify(folder)
        path = day_file(folder)
        day = json.loads(path.read_text(encoding="utf-8"))
        out.append({"run": folder.name, "morning": morning, "arm": arm, "seed": seed, "date": day.get("date"),
                    "meta": run, **measure(day)})
    return out


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def cells(runs, key):
    """{morning: {arm: [values]}}, None values left out."""
    out = {}
    for r in runs:
        if r.get(key) is not None:
            out.setdefault(r["morning"], {}).setdefault(r["arm"], []).append(r[key])
    return out


def effect(runs, key, boot=BOOT, seed=SEED, a="on", b="off"):
    """`a` against `b`, on against off unless named: the mean of the within-morning differences of means, its 95% bootstrap interval (runs resampled
    within each morning and arm) and the probability that an on run exceeds an off run of the same morning."""
    c = {m: {"on": x[a], "off": x[b]} for m, x in cells(runs, key).items() if x.get(a) and x.get(b)}
    if not c:
        return None
    diff = lambda cc: mean(mean(x["on"]) - mean(x["off"]) for x in cc.values())
    rng = random.Random(f"{seed}|{key}" + ("" if (a, b) == ("on", "off") else f"|{a}|{b}"))
    draws = sorted(diff({m: {arm: rng.choices(v, k=len(v)) for arm, v in a.items()} for m, a in c.items()})
                   for _ in range(boot))
    wins = pairs = 0
    for x2 in c.values():
        for x in x2["on"]:
            for y in x2["off"]:
                wins += 1 if x > y else 0.5 if x == y else 0
                pairs += 1
    return {"diff": diff(c), "lo": quantile(draws, 0.025), "hi": quantile(draws, 0.975),
            "p_on_greater": wins / pairs, "mornings": sorted(c), "n_on": sum(len(x["on"]) for x in c.values()),
            "n_off": sum(len(x["off"]) for x in c.values())}


def spread(runs, key):
    return {m: {arm: {"n": len(v), "median": median(v), "q1": quantile(v, 0.25), "q3": quantile(v, 0.75),
                      "min": min(v), "max": max(v)} for arm, v in sorted(a.items())}
            for m, a in sorted(cells(runs, key).items())}


def regime(r):
    h = r.get("home_share")
    return None if h is None else "at home" if h >= 0.8 else "away" if h <= 0.2 else None


def fmt(x, share=False):
    if x is None:
        return "–"
    if share:
        return f"{100 * x:.0f}%"
    return f"{x:.2f}" if isinstance(x, float) and not x.is_integer() else f"{x:.0f}"


def table(runs, boot, a="on", b="off"):
    """The comparison table of `a` against `b`, and its effects by measure."""
    lines = [f"| Measure | {b.capitalize()}, mean | {a.capitalize()}, mean | {a} − {b} (mean of the mornings) | 95% interval | P({a} > {b}) |",
             "|---|---:|---:|---:|---:|---:|"]
    effects = {}
    for key, label, share in METRICS:
        e = effects[key] = effect(runs, key, boot, a=a, b=b)
        if e is None:
            continue
        xb = [r[key] for r in runs if r["arm"] == b and r["morning"] in e["mornings"] and r[key] is not None]
        xa = [r[key] for r in runs if r["arm"] == a and r["morning"] in e["mornings"] and r[key] is not None]
        k = 100 if share else 1
        lines.append(f"| {label} | {fmt(mean(xb), share)} | {fmt(mean(xa), share)} | {e['diff'] * k:+.1f}{' pts' if share else ''} | "
                     f"{e['lo'] * k:+.1f} to {e['hi'] * k:+.1f} | {e['p_on_greater']:.2f} |")
    return lines, effects


def report(runs, boot=BOOT):
    culture = [r for r in runs if r["arm"] in ("on", "off")]
    block1 = [r for r in culture if r["seed"] in SEEDS1]
    acts = [r for r in runs if r["arm"] == "act"]
    lines = ["# Night 1: the museums off and on, read as declared", "",
             "Declared in `pc/FAST-LANE-NIGHT1.md` before any run. A measurement, not a gate. Evaluation only.", "",
             f"Runs read: {len(runs)} ({sum(r['arm'] == 'off' for r in runs)} off, {sum(r['arm'] == 'on' for r in runs)} on, "
             f"{len(acts)} with the file's act), mornings {', '.join(sorted({r['morning'] for r in runs}))}.", ""]
    thin = [r["run"] for r in runs if r["under_floor"]]
    if thin:
        lines += [f"**Under the floor of {FLOOR} thoughts:** {', '.join(thin)}. They are read with the rest and named here.", ""]
    t1, effects = table(block1, boot)
    lines += ["## Block 1: on against off", ""] + t1
    out = {"block1": effects}
    if len(culture) > len(block1):
        tp, out["pooled"] = table(culture, boot)
        lines += ["", "## Blocks 1 and 3 pooled: on against off", ""] + tp
    if acts:
        ta, out["act"] = table(acts + [r for r in block1 if r["arm"] == "on"], boot, a="act", b="on")
        fired = {b: sum(b in r["act_beats"] for r in acts) for b in ACT_IDS}
        lines += ["", "## Block 2: the file's next act against the museums alone", "",
                  "Doors: " + "; ".join(f"`{b}` fired in {n} of {len(acts)}" for b, n in fired.items()) + ".", ""] + ta
        lines += ["", "| Run | Beats of the act | Flags | The file at night |", "|---|---|---|---|"]
        for r in sorted(acts, key=lambda r: (r["morning"], r["seed"])):
            flags = ", ".join(f"{k}={v}" for k, v in r["act_flags"].items()) or "–"
            lines.append(f"| {r['run']} | {', '.join(r['act_beats']) or '–'} | {flags} | {r['file'] or '–'} |")
    lines += ["", "## Each morning and arm", "", "| Measure | Morning | Arm | n | Median | IQR | Range |", "|---|---|---|---:|---:|---:|---:|"]
    for key, label, share in METRICS[:4] + (METRICS[8], METRICS[12]):
        for m, arms in spread(runs, key).items():
            for arm, s in arms.items():
                lines.append(f"| {label} | {m} | {arm} | {s['n']} | {fmt(s['median'], share)} | {fmt(s['q1'], share)}–{fmt(s['q3'], share)} | "
                             f"{fmt(s['min'], share)}–{fmt(s['max'], share)} |")
    lines += ["", "## Every run", "", "| Run | Morning | Arm | Seed | Moments | At home | Brought | Empty | Venues | Galleries | Parts | ₹ spent | Regime |",
              "|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for r in sorted(runs, key=lambda r: (r["morning"], r["arm"], r["seed"])):
        lines.append(f"| {r['run']} | {r['morning']} | {r['arm']} | {r['seed']} | {r['moments']} | {fmt(r['home_share'], True)} | {r['brought']} | "
                     f"{fmt(r['empty_share'], True)} | {', '.join(r['venues']) or '–'} | {r['galleries']} | {r['stage_parts']} | {r['cash_spent']} | {regime(r) or ''} |")
    lines += ["", "With about 24 runs a side and a between-seed SD of about 5 points in a share, a difference of about 4 points is "
              "visible; a smaller one is not. Pairs of the same seed are not read as pairs.", ""]
    return "\n".join(lines), out


def write_db(path, runs):
    con = sqlite3.connect(path)
    keys = [k for k, _, _ in METRICS] + ["under_floor"]
    con.execute("CREATE TABLE IF NOT EXISTS runs (run TEXT PRIMARY KEY, morning TEXT, arm TEXT, seed INTEGER, date TEXT, "
                + ", ".join(f"{k} REAL" for k in keys) + ", venues TEXT, meta TEXT)")
    for r in runs:
        con.execute(f"INSERT OR REPLACE INTO runs VALUES ({', '.join('?' * (5 + len(keys) + 2))})",
                    [r["run"], r["morning"], r["arm"], r["seed"], r["date"]] + [r[k] for k in keys]
                    + [json.dumps(r["venues"]), json.dumps(r["meta"], sort_keys=True)])
    con.commit()
    con.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--db")
    ap.add_argument("--boot", type=int, default=BOOT)
    a = ap.parse_args(argv)
    runs = load(a.runs)
    text, effects = report(runs, a.boot)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "RESULT.md").write_text(text, encoding="utf-8")
    (out / "result.json").write_text(json.dumps({"runs": runs, "effects": effects}, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                     encoding="utf-8")
    if a.db:
        write_db(a.db, runs)
    print(json.dumps({"runs": len(runs), "primary": effects["block1"].get("home_share")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
