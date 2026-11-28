"""IA2 (Welt's word, 28 November): arm IA again with the room it lacked. Each request byte for byte as in REQUESTS-inkling-A.jsonl
(messages, schema, seed, temperature, reasoning_effort "none"), except: the id "IA|…" becomes "IA2|…" and max_tokens 1100 becomes
3148, the room ID has (1100 + the 2048 Qwen's reasoning budget left). Split in two halves in the file's order, one a slot.
python3 make_ia2.py SRC_DIR OUT_DIR"""
import hashlib, json, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = [json.loads(l) for l in (src / "REQUESTS-inkling-A.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
assert len(rows) == 44 and all(r["id"].startswith("IA|") and r["params"]["max_tokens"] == 1100 for r in rows)
new = []
for r in rows:
    r = json.loads(json.dumps(r))
    r["id"] = "IA2|" + r["id"][3:]
    r["params"]["max_tokens"] = 3148
    new.append(r)
for name, part in (("A2a", new[:22]), ("A2b", new[22:])):
    raw = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in part).encode("utf-8")
    (out / f"REQUESTS-inkling-{name}.jsonl").write_bytes(raw)
    print(name, len(part), part[0]["id"], part[-1]["id"], hashlib.sha256(raw).hexdigest()[:16])
