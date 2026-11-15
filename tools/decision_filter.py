#!/usr/bin/env python3
"""T49: what a live filter would do, from answers that already exist. No model call, no training.

    python3 tools/decision_filter.py --candidates FILE.jsonl [--out ESTIMATE.json]

One JSON row per situation: {"id": ..., "messages": [system, user], "earlier_thoughts": [...] (optional),
"candidates": [{"seed": 1831, "answer": {...} or null, "accepted": true, "errors": [...], "finish_reason": "stop"}, ...]}.
Any number of answers per situation, taken in seed order. Training 3's candidate file has this shape as it is;
T39's saved arm-A answers (three seeds per case) fit it once each case's three answers sit in one row.
The rule and the arms are tools.decision_pairs.filter_estimate. Evaluation only.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.decision_pairs import filter_estimate  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--out", type=Path, help="a new file for the estimate")
    a = p.parse_args(argv)
    raw = a.candidates.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    result = dict(filter_estimate(rows), candidates_sha256=hashlib.sha256(raw).hexdigest(), rule="T49 filter estimate")
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if a.out:
        with a.out.open("x", encoding="utf-8") as f:
            f.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
