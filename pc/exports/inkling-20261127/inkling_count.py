"""W22: counts from the receipts' metadata only (finish reason, tokens, seconds, whether reasoning came back); no reply text is printed.
python3 inkling_count.py JOB_DIR   Prints one line."""
import json, sys
from pathlib import Path
job = Path(sys.argv[1]); fin, toks, secs, reasoned, errors = {}, [], [], 0, 0
for done in sorted((job / "receipts").glob("*.done.json")):
    d = json.loads(done.read_text())
    secs.append(d.get("seconds") or 0)
    if d.get("error"):
        errors += 1; continue
    r = json.loads(Path(str(done).replace(".done.json", ".response.bin")).read_bytes())
    c = r["choices"][0]
    fin[c.get("finish_reason")] = fin.get(c.get("finish_reason"), 0) + 1
    toks.append((r.get("usage") or {}).get("completion_tokens") or 0)
    reasoned += bool((c.get("message") or {}).get("reasoning_content"))
n = len(secs)
print(f"{n} calls; finish {', '.join(f'{k} {v}' for k, v in sorted(fin.items(), key=str))}; with reasoning {reasoned}; errors {errors}; "
      f"completion tokens mean {sum(toks) // max(1, len(toks))}, max {max(toks, default=0)}; seconds mean {sum(secs) / max(1, n):.0f}, max {max(secs, default=0):.0f}")
