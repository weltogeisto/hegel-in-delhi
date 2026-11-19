#!/usr/bin/env python3
"""The packets for W8's readers (pc/LORA-FRESH-SCENES.md, "The readers"): a ballot of all 72 thoughts for Sol and for a
fresh Claude session, and Welt's choice on the 24 held back. The keys go outside the repository; their hashes stay in it.

    python3 tools/lora_fresh_packets.py --plan plan.json --outputs outputs.jsonl --out <folder in the repo> --keyout <folder outside>

- **Sol and Claude:** each item shows the thought as he had it and the three rewrites (the adapter's, the plain, the plain
  again) as A, B and C, in an order shuffled for each reader and item. The development set comes first, then the held-back
  days, each in its own shuffled order; the reader is not told which is which.
- **Welt:** for each of the 24 held back, three versions without labels as X, Y and Z (the thought as he had it, the first
  plain rewrite, the adapter's), in a shuffled order. Two answers: which he likes most, which least.

Item ids are opaque and differ between readers. Evaluation only: no packet, mark or choice is ever training data."""
import argparse
import hashlib
import json
import random
from pathlib import Path

SEED = 1831
REWRITES = ("adapter", "plain1", "plain2")
WELT = ("source", "plain1", "adapter")


def jbytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def load(plan_path, outputs_path):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    outs = {}
    for line in Path(outputs_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("fallback"):
                raise ValueError(f"{r['id']} {r['version']} fell back: it is not a rewrite")
            outs[(r["id"], r["version"])] = r["output"]
    cases = plan["cases"]
    for c in cases:
        for v in REWRITES:
            if (c["id"], v) not in outs:
                raise ValueError(f"no {v} rewrite for {c['id']}")
    return plan, cases, outs


def text_of(case, version, outs):
    return case["thought"] if version == "source" else outs[(case["id"], version)]


def build(plan_path, outputs_path, out, keyout):
    plan, cases, outs = load(plan_path, outputs_path)
    out, keyout = Path(out), Path(keyout)
    out.mkdir(parents=True, exist_ok=True)
    keyout.mkdir(parents=True, exist_ok=True)
    hashes = {"plan_sha256": hashlib.sha256(Path(plan_path).read_bytes()).hexdigest(),
              "outputs_sha256": hashlib.sha256(Path(outputs_path).read_bytes()).hexdigest(), "readers": {}}
    for reader, prefix in (("sol", "S"), ("claude", "K")):
        rng = random.Random(f"{SEED}|{reader}")
        order = []
        for part in ("development", "confirmation"):
            group = [c for c in cases if c["set"] == part]
            rng.shuffle(group)
            order += group
        items, key = [], {}
        for n, c in enumerate(order, 1):
            iid = f"{prefix}{n:02d}"
            versions = list(REWRITES)
            random.Random(f"{SEED}|{reader}|{c['id']}").shuffle(versions)
            items.append({"id": iid, "source": c["thought"], **{lab: text_of(c, v, outs) for lab, v in zip("ABC", versions)}})
            key[iid] = {"case": c["id"], "set": c["set"], "group": c["group"], "day": c["day"], **dict(zip("ABC", versions))}
        hashes["readers"][reader] = write(out, keyout, reader, items, key)
    rng = random.Random(f"{SEED}|welt")
    held = [c for c in cases if c["set"] == "confirmation"]
    rng.shuffle(held)
    items, key = [], {}
    for n, c in enumerate(held, 1):
        iid = f"H{n:02d}"
        versions = list(WELT)
        random.Random(f"{SEED}|welt|{c['id']}").shuffle(versions)
        items.append({"id": iid, **{lab: text_of(c, v, outs) for lab, v in zip("XYZ", versions)}})
        key[iid] = {"case": c["id"], "set": c["set"], "group": c["group"], "day": c["day"], **dict(zip("XYZ", versions))}
    hashes["readers"]["welt"] = write(out, keyout, "welt", items, key)
    hashes["note"] = "The keys stay outside the repository until every ballot is sealed with its sha256 on main."
    hashes["training_eligible"] = False
    (out / "HASHES.json").write_bytes(jbytes(hashes))
    (out / "BALLOT.md").write_text(BALLOT, encoding="utf-8")
    return hashes


def write(out, keyout, reader, items, key):
    packet = jbytes(items)
    (out / f"packet-{reader}.json").write_bytes(packet)
    (out / f"sheet-{reader}.md").write_text(sheet(reader, items), encoding="utf-8")
    k = jbytes(key)
    (keyout / f"key-{reader}.json").write_bytes(k)
    return {"items": len(items), "packet_sha256": hashlib.sha256(packet).hexdigest(), "key_sha256": hashlib.sha256(k).hexdigest()}


def sheet(reader, items):
    if reader == "welt":
        head = (f"# His recent thoughts, three ways: for Welt\n\nRead `BALLOT.md` first. Each item is one thought of his in three versions, "
                "X, Y and Z, in no particular order. Say which you like most and which least.\n")
        body = "".join(f"\n## {it['id']}\n\n" + "".join(f"**{lab}:** {it[lab]}\n\n" for lab in "XYZ") for it in items)
    else:
        head = (f"# His recent thoughts and three rewrites: for {reader}\n\nRead `BALLOT.md` first. For each item read the source, "
                "then mark rewrites A, B and C against it, and guess which one is the adapter's.\n")
        body = "".join(f"\n## {it['id']}\n\n**Source:** {it['source']}\n\n" + "".join(f"**{lab}:** {it[lab]}\n\n" for lab in "ABC")
                       for it in items)
    return head + body


BALLOT = """# W8's readers: how to mark

Declared in `pc/LORA-FRESH-SCENES.md` before any output. Evaluation only: no mark, text or choice here becomes training data.

**What this is.** 72 thoughts he had on Days 44 to 49, each rewritten three times: by the adapter, and twice by the plain
model with two seeds. Which is which is hidden, and the order is shuffled differently for each reader. Work alone. Open
only your own packet: not another reader's, not `pc/exports/lora-fresh-scenes-20261119/`, not `pc/exports/lora-forty-20261118/`.

## Sol and the fresh Claude reader: one mark for each rewrite

The marks of the forty, unchanged (`pc/exports/lora-forty-20261118/BALLOT.md`):

| Mark | Meaning |
|---|---|
| **E** | A fact or event is changed or invented: who did it, what happened, an hour, a sum, a distance, a place, whether a thing was done |
| **C** | His conclusion, his decision or his certainty is changed: he will do something else, a "perhaps" is dropped or added, a refusal becomes a consent |
| **R** | The facts and the decision stand, and the reasoning is new: he gives another reason, draws another distinction, sees the thing differently |
| **P** | Wording only: the same facts, decision and reasoning in other words. A rewrite that returns the source unchanged is P |

E and C are defects. R and P are not. A rewrite with a defect is marked E or C whatever else it does; if it has both, mark
the one that matters more and name the other in the note. **For every E or C,** quote the words of the source and of the
rewrite that show it, and say whether it is **substantive** (it changes what happened or what he will do) or **minor**.
Older, heavier or plainer English is wording, not a defect and not a merit.

**Then guess** which of A, B and C is the adapter's (a model tuned on Hegel's own texts), or "none" if you cannot tell.

One line for each item, in `ballot-<reader>.jsonl`:

```
{"id": "S01", "A": {"mark": "P"}, "B": {"mark": "E", "weight": "substantive", "source_words": "four cups", "rewrite_words": "three cups"}, "C": {"mark": "R"}, "adapter_guess": "B", "note": ""}
```

## Welt: which you like most, which least

24 items. Each is one thought of his in three versions, X, Y and Z: one is the thought as he had it, two are rewrites.
Two answers for each: which you like **most** and which **least**. "none" is an answer to either, when none stands out.

```
{"id": "H01", "most": "Y", "least": "none", "note": ""}
```

## Sealing

Every ballot is sealed with its sha256 on main before any key is opened. The keys are outside the repository; their
hashes are in `HASHES.json`.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plan", required=True)
    ap.add_argument("--outputs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keyout", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(build(a.plan, a.outputs, a.out, a.keyout), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
