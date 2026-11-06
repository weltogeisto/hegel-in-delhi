#!/usr/bin/env python3
"""Training 3: preference pairs for his decisions, labelled by the world's own checks.

Input: one JSON row per situation, written by Astra's sampler (pc/TRAINING-3.md, Training 3):
    {"id": "shadow:35:17", "source": "shadow" | "rehearsal", "day": 35, "step": 17,
     "messages": [...],                    # the exact prompt the mind saw (soul + rendered situation)
     "earlier_thoughts": ["...", ...],     # that day's thoughts before this step, from the record
     "candidates": [{"seed": 1831, "raw": "...", "answer": {...} or null,
                     "accepted": true, "errors": [...], "warnings": [...]}, ...]}

Every candidate comes from plain Qwen; World.check (the rules, the 1831 gate, the repetition guard) decides
"accepted". Nobody's taste enters: no text here is written or chosen by Claude or any other model.

Labels, per candidate:
    clean      accepted, a thought, and no phrase (report.grams, T9's rule) shared with the day's earlier thoughts
    repeating  accepted, but it reuses such a phrase
    refused    the world refused it
    invalid    no parsable answer (never paired: it has no thought to length-match)

One pair per situation at most, so no situation weighs more than another: the first clean candidate in seed order
is chosen; the first repeating or refused one in seed order whose thought is within 20% of its length (in words)
is rejected. Length matching keeps the adapter from learning that shorter, or silent, is better (report p. 10).
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world.report import grams  # noqa: E402

TEST_DAYS = frozenset({12, 27})   # T39's frozen shadow days; T9's rehearsal days are not shadow days
LENGTH_RATIO = 0.8


def thought_of(candidate):
    answer = candidate.get("answer")
    if isinstance(answer, dict) and isinstance(answer.get("thought"), str) and answer["thought"].strip():
        return answer["thought"]
    return None


def label(candidate, earlier):
    thought = thought_of(candidate)
    if thought is None and not isinstance(candidate.get("answer"), dict):
        return "invalid"
    if not candidate.get("accepted"):
        return "refused"
    if thought is None:
        return "refused"          # the world accepted a step without a thought; no use as a chosen example
    seen = set().union(*(grams(t) for t in earlier if t)) if earlier else set()
    return "repeating" if grams(thought) & seen else "clean"


def words(text):
    return len(text.split())


def length_matched(a, b, ratio=LENGTH_RATIO):
    x, y = words(a), words(b)
    return min(x, y) / max(x, y) >= ratio if x and y else False


def pair(row):
    """The labels of a situation's candidates, and its one pair (or None)."""
    earlier = row.get("earlier_thoughts") or []
    cands = sorted(row["candidates"], key=lambda c: c["seed"])
    labels = [label(c, earlier) for c in cands]
    chosen = next((c for c, l in zip(cands, labels) if l == "clean"), None)
    if chosen is None:
        return labels, None
    for c, l in zip(cands, labels):
        if l in ("repeating", "refused") and thought_of(c) and length_matched(thought_of(chosen), thought_of(c)):
            return labels, {"id": row["id"], "source": row["source"], "day": row["day"], "step": row["step"],
                            "prompt": row["messages"], "chosen": chosen["raw"], "rejected": c["raw"],
                            "chosen_seed": chosen["seed"], "rejected_seed": c["seed"], "rejected_as": l,
                            "rejected_errors": c.get("errors", []),
                            "words": [words(thought_of(chosen)), words(thought_of(c))]}
    return labels, None


def check_row(row, seen_ids):
    if row["id"] in seen_ids:
        raise ValueError("duplicate situation: " + row["id"])
    if row["source"] not in ("shadow", "rehearsal"):
        raise ValueError("unknown source: " + str(row["source"]))
    if row["source"] == "shadow" and row["day"] in TEST_DAYS:
        raise ValueError("T39's test day may not train: " + row["id"])
    seeds = [c["seed"] for c in row["candidates"]]
    if len(seeds) != len(set(seeds)) or not seeds:
        raise ValueError("candidates need distinct seeds: " + row["id"])


def build(rows):
    pairs, counts, by = [], Counter(), Counter()
    seen = set()
    for row in rows:
        check_row(row, seen)
        seen.add(row["id"])
        labels, p = pair(row)
        counts.update(labels)
        if p:
            pairs.append(p)
            by[(p["source"], p["rejected_as"])] += 1
        else:
            counts["situations_without_pair"] += 1
    stats = {"situations": len(seen), "pairs": len(pairs), "labels": dict(counts),
             "pairs_by_source_and_reason": {f"{s}/{r}": n for (s, r), n in sorted(by.items())},
             "rule": "one pair per situation; first clean vs first repeating or refused within 20% length, seed order",
             "test_days_excluded": sorted(TEST_DAYS)}
    return pairs, stats


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidates", type=Path, required=True, help="the sampler's JSONL, one situation per line")
    p.add_argument("--out", type=Path, required=True, help="new JSONL of pairs; a stats file is written beside it")
    a = p.parse_args(argv)
    raw = a.candidates.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    pairs, stats = build(rows)
    stats["candidates_sha256"] = hashlib.sha256(raw).hexdigest()
    body = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in pairs).encode()
    stats["pairs_sha256"] = hashlib.sha256(body).hexdigest()
    with a.out.open("xb") as f:
        f.write(body)
    with a.out.with_suffix(".stats.json").open("x") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(stats, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
