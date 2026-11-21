"""W9's blind reading (pc/VOICE-REPAIRS-CHECK.md, Part 2): a packet of the 174 replies for two readers, blind to the arm.

    python3 tools/voice_repairs_readers.py --ref <codex/voice-repairs-check-20261120 sha> --out <folder in the repo> --keyout <dir outside>

Each item shows the moment as the record has it (place, time, who is there, what is for sale, what happens), what he said,
and the reply heard; and which questions its set asks: set A, whether the reply treats the speaker's own name as another
person; set B, whether it offers, arranges or describes food, drink or goods there; both, whether the record shown
contradicts it, and whether it is empty or a refusal. Item ids are opaque and the order shuffled; the key (item -> moment,
arm, seed) stays outside the repository until both readers' labels are sealed. Evaluation only."""
import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path

FOLDER = "pc/exports/voice-repairs-check-20261120"
SEED = 1831


def show(ref, path):
    return subprocess.run(["git", "show", f"{ref}:{path}"], check=True, capture_output=True, text=True).stdout


def build(ref, out, keyout):
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, f"{FOLDER}/run/records"], check=True, capture_output=True,
                           text=True).stdout.split()
    recs = [json.loads(show(ref, n)) for n in names if n.endswith(".json")]
    ctx = {}
    items, key = [], {}
    for r in recs:
        if r["id"] not in ctx:
            ctx[r["id"]] = json.loads(show(ref, f"{FOLDER}/contexts/{r['id']}.json"))
        c, s = ctx[r["id"]], ctx[r["id"]]["sit"]
        items.append({"moment": {"place": s.get("place"), "time": s.get("time"), "present": s.get("present"),
                                 "for_sale": s.get("for_sale"), "event": s.get("event")},
                      "he_said": c.get("says"), "reply": {"by": r["heard"].get("by"), "says": r["heard"].get("says"), "does": r["heard"].get("does")},
                      "questions": (["own_name"] if c.get("in_A") else []) + (["goods"] if c.get("in_B") else []) + ["contradicted", "empty"],
                      "_key": {"moment": r["id"], "arm": r["arm"], "seed": r["seed"], "sets": c.get("sets")}})
    random.Random(SEED).shuffle(items)
    for n, it in enumerate(items, 1):
        iid = f"V{n:03d}"
        key[iid] = it.pop("_key")
        it["id"] = iid
    out, keyout = Path(out), Path(keyout)
    out.mkdir(parents=True, exist_ok=True)
    keyout.mkdir(parents=True, exist_ok=True)
    packet = "".join(json.dumps({"id": it["id"], **{k: v for k, v in it.items() if k != "id"}}, ensure_ascii=False) + "\n" for it in items).encode()
    (out / "PACKET.jsonl").write_bytes(packet)
    k = json.dumps(key, indent=1, sort_keys=True).encode()
    (keyout / "KEY-W9.json").write_bytes(k)
    h = {"ref": ref, "items": len(items), "packet_sha256": hashlib.sha256(packet).hexdigest(), "key_sha256": hashlib.sha256(k).hexdigest(),
         "note": "The key stays outside the repository until both readers' labels are sealed on main.", "training_eligible": False}
    (out / "HASHES.json").write_text(json.dumps(h, indent=1) + "\n", encoding="utf-8")
    (out / "READING.md").write_text(READING, encoding="utf-8")
    return h


READING = """# W9: how to read

You read replies that people in a simulation gave to a man (Hegel) in Delhi. `PACKET.jsonl` has one item per line: the
moment as the record shows it (place, time, who is there, what is for sale there, what happens), what he said, and the
reply (who answered, what they said, what the italic gesture says they did). Only what the item shows is the record.
Judge each reply on its own. Some replies are word for word the same; label each all the same.

Answer only the questions the item lists in `questions`:
- **own_name** (true or false): the reply treats the speaker's own name as another person, as if someone else of that name
  were present or meant ("Hegde ji, you're still here?" said by Shri Hegde himself).
- **goods** (true or false): the reply offers, arranges or describes food, drink or goods to be had there (a meal, tea, a
  plate, something to buy), at a place where the item says nothing is for sale.
- **contradicted**: a list of statements in the reply that the record shown contradicts, each with the reply's words and the
  record's words. Empty list when there is none. A statement the record merely does not mention is not contradicted.
- **empty** (true or false): the reply is empty, cut off, or a refusal to answer as the person.

One JSON line per item, in `labels-<reader>.jsonl`:

```
{"id": "V001", "own_name": false, "goods": null, "contradicted": [], "empty": false, "note": ""}
```

Use null for a question the item does not list. Work alone; open no other file.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keyout", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(build(a.ref, a.out, a.keyout), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
