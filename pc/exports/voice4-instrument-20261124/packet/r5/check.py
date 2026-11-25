"""Check one reader's answers: python3 check.py <name>   (e.g. r3)"""
import json, sys
from pathlib import Path
here = Path(__file__).resolve().parent
name = sys.argv[1]
want = (here / f"{name}.pairs").read_text().split()
rows = [json.loads(l) for l in (here / f"{name}.out.jsonl").read_text().splitlines() if l.strip()]
errs = []
if [r.get("pair") for r in rows] != want:
    errs.append(f"pair ids differ: {len(rows)} lines for {len(want)} pairs, or another order")
errs += [f"{r.get('pair')}: the answer must be X or Y" for r in rows if r.get("real") not in ("X", "Y")]
print("ALL OK" if not errs else "\n".join(errs))
