#!/usr/bin/env python3
"""T36's truth and quality gates, from a sealed blind judgment and the key. No model call.

    python3 tools/blind_verdict.py --export pc/exports/t49-arm-d-20261114 --key KEY.json [--out VERDICT.json]
    python3 tools/blind_verdict.py --export pc/exports/t49-arm-d-20261114 --chance [--out CHANCE.json]

The export holds for-claude/ (the packet) and judgment/ (TRUTH-AUDIT.jsonl, VOICE-ARGUMENT-SCORES.jsonl and
SEALED.json, committed before the key was asked for). The key names the arm of every opaque ID; any JSON or
JSONL shape works as long as each ID sits beside an "arm". The tool refuses a key whose hash is not the sealed
one, and judgment or packet files that changed after sealing.

The gates, against the baseline arm (T36, as T39 used it): contradictions per 100 sentences at most 0.3 higher,
statements as fact per 100 sentences at most 0.5 higher, argument and voice at most 0.25 lower. The echo measure
is the machine's and is not judged here. Evaluation only.

--chance needs no key. It asks what the gates would say if the arm made no difference: it splits each case's
thoughts into random halves, and the scored thoughts into random halves, and reports how often a gate fails by
chance alone. A diagnostic beside the verdict, never a gate.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

GATES = {"contradictions_per_100": 0.3, "statements_as_fact_per_100": 0.5, "argument": -0.25, "voice": -0.25}
EPS = 1e-9


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def arms(key, ids):
    """{id: arm} from a key of any shape: every known ID that sits beside an arm."""
    found = {}

    def note(i, arm):
        if i in ids and isinstance(arm, str):
            if found.setdefault(i, arm) != arm:
                raise ValueError(f"the key gives {i} two arms")

    def walk(x):
        if isinstance(x, dict):
            for name in ("id", "opaque_id", "blind_id"):
                if isinstance(x.get(name), str):
                    note(x[name], x.get("arm"))
            for k, v in x.items():
                if k in ids:
                    note(k, v if isinstance(v, str) else v.get("arm") if isinstance(v, dict) else None)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(key)
    return found


def load_key(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(x) for x in text.splitlines() if x.strip()]


def verdict(export, key_path, baseline="A", candidate="D"):
    export = Path(export)
    judgment, packet = export / "judgment", export / "for-claude"
    sealed = json.loads((judgment / "SEALED.json").read_text(encoding="utf-8"))
    if sha(key_path) != sealed["key_sha256_as_published_by_astra"]:
        raise ValueError("this is not the sealed key: its hash differs from SEALED.json")
    for name, want in sealed["judgments"].items():
        if sha(judgment / name) != want:
            raise ValueError(f"{name} changed after sealing")
    for name, want in sealed["inputs"].items():
        if sha(export / name) != want:
            raise ValueError(f"{name} changed after sealing")

    audit = jsonl(judgment / "TRUTH-AUDIT.jsonl")
    scores = jsonl(judgment / "VOICE-ARGUMENT-SCORES.jsonl")
    review = {r["id"]: r for r in jsonl(packet / "truth-review.jsonl")}
    ids = {a["id"] for a in audit}
    if ids != set(review) or len(ids) != len(audit):
        raise ValueError("the audit does not cover the packet's IDs exactly once")
    arm = arms(load_key(key_path), ids)
    missing = sorted(ids - set(arm))
    if missing:
        raise ValueError(f"the key names no arm for {len(missing)} IDs, e.g. {missing[:3]}")
    if set(arm.values()) != {baseline, candidate}:
        raise ValueError(f"expected arms {baseline} and {candidate}, the key has {sorted(set(arm.values()))}")

    dates = {}
    for p in sorted((packet / "evidence").glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        dates[e["reference"]] = e["date"]

    def blank():
        return dict(thoughts=0, empty=0, sentences=0, contradictions=0, statements_as_fact=0, uncertain=0)

    out = {a: dict(blank(), by_day={}) for a in (baseline, candidate)}
    for a in audit:
        day = dates.get(review[a["id"]]["reference"], "?")
        for t in (out[arm[a["id"]]], out[arm[a["id"]]]["by_day"].setdefault(day, blank())):
            t["thoughts"] += 1
            t["empty"] += a["sentences"] == 0
            for k in ("sentences", "contradictions", "statements_as_fact", "uncertain"):
                t[k] += a[k]
    for a in (baseline, candidate):
        for t in [out[a], *out[a]["by_day"].values()]:
            n = t["sentences"] or 1
            t["contradictions_per_100"] = round(100 * t["contradictions"] / n, 3)
            t["statements_as_fact_per_100"] = round(100 * t["statements_as_fact"] / n, 3)
        mine = [s for s in scores if arm[s["id"]] == a]
        if not mine:
            raise ValueError(f"no scored thought belongs to arm {a}")
        out[a]["scored_thoughts"] = len(mine)
        out[a]["argument"] = round(sum(s["argument"] for s in mine) / len(mine), 3)
        out[a]["voice"] = round(sum(s["voice"] for s in mine) / len(mine), 3)

    gates = {}
    for name, limit in GATES.items():
        diff = round(out[candidate][name] - out[baseline][name], 3)
        ok = diff <= limit + EPS if limit > 0 else diff >= limit - EPS
        gates[name] = dict(baseline=out[baseline][name], candidate=out[candidate][name], difference=diff,
                           limit=("at most +%s" % limit) if limit > 0 else ("at least %s" % limit), passed=ok)
    return dict(study=sealed.get("study"), baseline=baseline, candidate=candidate, arms=out, gates=gates,
                passed=all(g["passed"] for g in gates.values()), key_sha256=sha(key_path),
                sealed_sha256=sha(judgment / "SEALED.json"), rule="T36 truth and quality gates", training_eligible=False)


def chance(export, runs=5000, seed=1831):
    """How often each gate fails when the arm makes no difference. Reads the judgment and the packet, no key."""
    export = Path(export)
    audit = jsonl(export / "judgment/TRUTH-AUDIT.jsonl")
    scores = jsonl(export / "judgment/VOICE-ARGUMENT-SCORES.jsonl")
    ref = {r["id"]: r["reference"] for r in jsonl(export / "for-claude/truth-review.jsonl")}
    cases = {}
    for a in audit:
        cases.setdefault(ref[a["id"]], []).append((a["sentences"], a["contradictions"], a["statements_as_fact"]))
    cases = [cases[k] for k in sorted(cases)]
    rng = random.Random(seed)
    diffs = {k: [] for k in GATES}
    for _ in range(runs):
        tot = [[0, 0, 0], [0, 0, 0]]
        for rows in cases:
            order = list(range(len(rows)))
            rng.shuffle(order)
            half = len(rows) // 2 + (len(rows) % 2 and rng.random() < 0.5)
            for n, i in enumerate(order):
                side = tot[n < half]
                for j in range(3):
                    side[j] += rows[i][j]
        base, cand = tot
        diffs["contradictions_per_100"].append(100 * cand[1] / (cand[0] or 1) - 100 * base[1] / (base[0] or 1))
        diffs["statements_as_fact_per_100"].append(100 * cand[2] / (cand[0] or 1) - 100 * base[2] / (base[0] or 1))
        order = list(range(len(scores)))
        rng.shuffle(order)
        half = len(scores) // 2
        for k in ("argument", "voice"):
            c = [scores[i][k] for i in order[:half]]
            b = [scores[i][k] for i in order[half:]]
            diffs[k].append(sum(c) / len(c) - sum(b) / len(b))
    out = {}
    for k, limit in GATES.items():
        d = sorted(diffs[k])
        fails = sum(x > limit + EPS if limit > 0 else x < limit - EPS for x in d)
        out[k] = dict(limit=limit, fails_by_chance=round(fails / runs, 3),
                      middle_90_percent=[round(d[int(0.05 * runs)], 3), round(d[int(0.95 * runs) - 1], 3)])
    return dict(gates=out, runs=runs, seed=seed, cases=len(cases), thoughts=len(audit), scored_thoughts=len(scores),
                method="random halves of each case's thoughts and of the scored thoughts; no key, no arm effect",
                rule="T36 chance diagnostic; never a gate", training_eligible=False)


def table(v):
    a, d = v["baseline"], v["candidate"]
    rows = ["| Measure | %s | %s | Difference | Bar | |" % (a, d), "|---|---:|---:|---:|---|---|"]
    names = {"contradictions_per_100": "Contradictions per 100 sentences",
             "statements_as_fact_per_100": "Statements as fact per 100 sentences",
             "argument": "Argument, 1 to 5", "voice": "Voice, 1 to 5"}
    for k, g in v["gates"].items():
        rows.append("| %s | %s | %s | %+.3f | %s | %s |" % (names[k], g["baseline"], g["candidate"], g["difference"],
                                                           g["limit"], "pass" if g["passed"] else "FAIL"))
    for x in (a, d):
        t = v["arms"][x]
        rows.append("")
        rows.append("%s: %d thoughts (%d empty), %d sentences, %d contradictions, %d statements as fact, %d uncertain; "
                    "%d thoughts scored." % (x, t["thoughts"], t["empty"], t["sentences"], t["contradictions"],
                                             t["statements_as_fact"], t["uncertain"], t["scored_thoughts"]))
    return "\n".join(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--export", type=Path, required=True)
    p.add_argument("--key", type=Path)
    p.add_argument("--chance", action="store_true", help="the keyless chance diagnostic instead of the verdict")
    p.add_argument("--baseline", default="A")
    p.add_argument("--candidate", default="D")
    p.add_argument("--out", type=Path, help="a new file for the verdict")
    a = p.parse_args(argv)
    if a.chance == bool(a.key):
        p.error("give either --key or --chance")
    if a.out and a.out.exists():
        p.error(f"{a.out} exists")
    v = chance(a.export) if a.chance else verdict(a.export, a.key, a.baseline, a.candidate)
    if a.out:
        a.out.write_text(json.dumps(v, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if a.chance:
        for k, g in v["gates"].items():
            print("%-28s fails by chance in %4.1f%% of splits; middle 90%%: %+.3f to %+.3f"
                  % (k, 100 * g["fails_by_chance"], *g["middle_90_percent"]))
        return 0
    print(table(v))
    print("\nPASSED" if v["passed"] else "\nNOT PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
