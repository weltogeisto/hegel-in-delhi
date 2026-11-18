"""The filter's kept draws as preference pairs, by Training 3's rules (pc/TRAINING-3.md, pc/FILTER-PAIRS.md).

HEGEL_KEEP_DRAWS keeps every decision that took more than one reply in <state>/draws/<date>.jsonl.gz: the prompt, each
reply and what the world's checks said of it. This turns them into pairs:
  - chosen: the reply the filter picked, accepted by the world, repeating no thought shown under "Earlier today";
  - rejected: another reply to the same prompt that the world refused, or that repeated a shown thought;
  - length matched: the two thoughts within 20% of each other in words, so that shorter or silent cannot win.
A refused reply with no readable thought makes no pair. Nothing here is chosen by a model's taste: the local model's own
replies, sorted by the world's fixed checks, as the data rule allows (DECISIONS.md, the data rule). No training runs from
this; a training needs Welt's word.

    python3 tools/filter_pairs.py --draws <folder with *.jsonl.gz> --out <folder>
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from world.contract import extract_json  # noqa: E402

BAR = 200             # Training 3's data gate, declared before its sampling
LENGTH = 0.2


def thought_of(draw):
    if draw.get("thought"):
        return draw["thought"]
    ans = extract_json(draw.get("raw") or "")
    return ans.get("thought") if isinstance(ans, dict) and isinstance(ans.get("thought"), str) else None


def matched(a, b):
    x, y = len(a.split()), len(b.split())
    return max(x, y) > 0 and abs(x - y) <= LENGTH * max(x, y)


def pairs_of(row):
    """The pairs of one kept decision, and why each other draw made no pair."""
    picked = row.get("picked")
    draws = row.get("draws") or []
    if picked is None or not 0 <= picked < len(draws):
        return [], ["no pick"]
    chosen = draws[picked]
    if chosen.get("errors") or not chosen.get("fresh"):
        return [], ["the pick was not fresh"]            # every reply echoed: the filter kept the first accepted one
    out, skipped = [], []
    for i, d in enumerate(draws):
        if i == picked:
            continue
        why = "refused" if d.get("errors") else "repeats a shown thought" if d.get("fresh") is False else None
        if why is None:
            skipped.append("another fresh reply")
            continue
        rt, ct = thought_of(d), chosen.get("thought")
        if not rt or not ct:
            skipped.append("no readable thought")
            continue
        if not matched(ct, rt):
            skipped.append("lengths differ by more than 20%")
            continue
        out.append({"date": row["date"], "t": row["t"], "soul": row.get("soul"), "prompt": row["messages"],
                    "chosen": chosen["raw"], "rejected": d["raw"], "rejected_why": why, "rejected_errors": d.get("errors")})
    return out, skipped


def read(folder):
    rows = []
    for path in sorted(Path(folder).glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            rows += [json.loads(line) for line in f if line.strip()]
    return rows


def build(folder, out=None):
    rows = read(folder)
    pairs, skipped = [], {}
    for row in rows:
        p, s = pairs_of(row)
        pairs += p
        for why in s:
            skipped[why] = skipped.get(why, 0) + 1
    stats = {"decisions_kept": len(rows), "days": sorted({r["date"] for r in rows}), "pairs": len(pairs),
             "by_reason": {w: sum(1 for p in pairs if p["rejected_why"] == w) for w in ("refused", "repeats a shown thought")},
             "no_pair": skipped, "bar": BAR, "bar_met": len(pairs) >= BAR, "training_eligible": "on Welt's word only"}
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "pairs.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pairs), encoding="utf-8")
        (out / "STATS.json").write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    return pairs, stats


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    print(json.dumps(build(a.draws, a.out)[1], indent=1))


if __name__ == "__main__":
    main()
