"""Paris stage 2b, the letter register (pc/PARIS-BACKTEST.md; DECISIONS.md 60): does the block of HEGEL_LETTER_REGISTER make
his letters home harder to tell from Hegel's own?

    python3 tools/paris_letters.py requests --heldout <CARDS-HELDOUT.jsonl> --out <folder>    # the PC's 96 calls
    python3 tools/paris_letters.py sheet --folder <folder> --arm <heldout-off|heldout-on|old-on> --keyout <dir outside the repo>

The block was written after stage 2's judge gave its reasons, so the 24 cards of stage 2 cannot test it fairly. The test is
on 24 held-out cards, from passages of the same journeys that no card, prompt or judge had used: their letters without
the block and with it, each against the real passage, judged by separate fresh judges. Stage 2's own cards get letters
with the block too, as a development check only. Evaluation only: nothing here is ever training data."""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.paris_stage2 import LETTER_WORDS, TRANSLATE, YEAR  # noqa: E402
from world.works import LETTER_REGISTER  # noqa: E402

STAGE2 = REPO / "pc/exports/paris-stage2-20261118"
SEED = 1831
ARMS = {"heldout-off": ("heldout", "off"), "heldout-on": ("heldout", "on"), "old-on": ("old", "on")}


def rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def letter_messages(soul, card, register):
    ask = (f"{card['when']}, evening, {card['place']}.\n\nToday: {card['card']}\n\n"
           f"Write to Marie tonight, as you would: at most {LETTER_WORDS} words. " + (LETTER_REGISTER if register else "")
           + "Answer with the letter only.")
    return [{"role": "system", "content": soul}, {"role": "user", "content": ask}]


def requests(heldout, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    passages = {r["id"]: r for rs in json.loads((STAGE2 / "ENTRIES.json").read_text(encoding="utf-8")).values() for r in rs}
    soul = {j: (STAGE2 / f"soul-{y}.md").read_text(encoding="utf-8") for j, y in YEAR.items()}
    letter = lambda c, reg: {"seed": SEED, "temperature": 0.7, "max_tokens": 400, "cache_prompt": False}
    reqs = []
    for c in rows(heldout):
        for reg, tag in ((False, "off"), (True, "on")):
            reqs.append({"id": f"heldout-{tag}|{c['id']}|{SEED}", "messages": letter_messages(soul[c["journey"]], c, reg), "params": letter(c, reg)})
        reqs.append({"id": f"translate|{c['id']}", "messages": [{"role": "system", "content": TRANSLATE},
                                                                {"role": "user", "content": passages[c["id"]]["text"]}],
                     "params": {"seed": SEED, "temperature": 0, "max_tokens": 900, "cache_prompt": False}})
    for c in rows(STAGE2 / "CARDS.jsonl"):
        reqs.append({"id": f"old-on|{c['id']}|{SEED}", "messages": letter_messages(soul[c["journey"]], c, True), "params": letter(c, True)})
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs).encode()
    (out / "REQUESTS.jsonl").write_bytes(data)
    return {"requests": len(reqs), "sha256": hashlib.sha256(data).hexdigest()}


def sheet(folder, arm, keyout):
    folder = Path(folder)
    which, _ = ARMS[arm]
    replies = {r["id"]: r["reply"] for r in rows(folder / "REPLIES.jsonl")}
    cards = rows(folder / "CARDS-HELDOUT.jsonl") if which == "heldout" else rows(STAGE2 / "CARDS.jsonl")
    real = replies if which == "heldout" else {r["id"]: r["reply"] for r in rows(STAGE2 / "replies-20261119/REPLIES.jsonl")}
    rng = random.Random(f"{SEED}|{arm}")
    out, key = [], {}
    for c in cards:
        sim, truth = replies[f"{arm}|{c['id']}|{SEED}"], real[f"translate|{c['id']}"]
        x_real = rng.random() < 0.5
        pid = hashlib.sha256(f"{SEED}|{arm}|{c['id']}".encode()).hexdigest()[:8]
        out.append({"pair": pid, "card": c["card"], "X": truth if x_real else sim, "Y": sim if x_real else truth})
        key[pid] = {"card": c["id"], "real": "X" if x_real else "Y", "arm": arm}
    rng.shuffle(out)
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out).encode()
    (folder / f"SHEET-{arm}.jsonl").write_bytes(data)
    k = json.dumps(key, indent=1, sort_keys=True).encode()
    Path(keyout).mkdir(parents=True, exist_ok=True)
    (Path(keyout) / f"KEY-{arm}.json").write_bytes(k)
    return {"arm": arm, "pairs": len(out), "sheet_sha256": hashlib.sha256(data).hexdigest(), "key_sha256": hashlib.sha256(k).hexdigest()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("requests"); r.add_argument("--heldout", required=True); r.add_argument("--out", required=True)
    s = sub.add_parser("sheet"); s.add_argument("--folder", required=True); s.add_argument("--arm", required=True, choices=ARMS)
    s.add_argument("--keyout", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(requests(a.heldout, a.out) if a.cmd == "requests" else sheet(a.folder, a.arm, a.keyout)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
