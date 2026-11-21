"""Paris stage 2c (pc/PARIS-BACKTEST.md): both sides through the same German-to-English path, and a letter block that names
no kinds of content.

    python3 tools/paris_german.py round1 --cards <CARDS.jsonl> --out <folder>     # 72 calls: German letters off/on, real translations
    python3 tools/paris_german.py round2 --folder <folder>                         # after round 1's replies: 48 translations
    python3 tools/paris_german.py sheet --folder <folder> --arm <off|on> --keyout <dir outside the repo>

The model writes his letter in German, as he wrote in that year, and stage 2's fixed instruction puts it into English,
as it puts the real passage. Form then gives nothing away, and the count can move with content. Evaluation only."""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.paris_stage2 import LETTER_WORDS, TRANSLATE, YEAR  # noqa: E402

STAGE2 = REPO / "pc/exports/paris-stage2-20261118"
SEED = 1831
LEAVE_OUT = ("Put nothing in the letter that the card does not give you. Tell two or three things of the day, unevenly, "
             "and stop when the news is told. Draw no lesson from it. ")       # names no kinds of content (stage 2b's lesson)


def rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def german_letter(soul, card, block):
    ask = (f"{card['when']}, evening, {card['place']}.\n\nToday: {card['card']}\n\n"
           f"Write to Marie tonight, as you would, in German, as you wrote in {YEAR[card['journey']]}: at most {LETTER_WORDS} words. "
           + (LEAVE_OUT if block else "") + "Answer with the letter only.")
    return [{"role": "system", "content": soul}, {"role": "user", "content": ask}]


def translate(text):
    return [{"role": "system", "content": TRANSLATE}, {"role": "user", "content": text}]


def write(path, reqs):
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reqs).encode()
    Path(path).write_bytes(data)
    return {"requests": len(reqs), "sha256": hashlib.sha256(data).hexdigest()}


def round1(cards, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    passages = {r["id"]: r for rs in json.loads((STAGE2 / "ENTRIES.json").read_text(encoding="utf-8")).values() for r in rs}
    soul = {j: (STAGE2 / f"soul-{y}.md").read_text(encoding="utf-8") for j, y in YEAR.items()}
    letter = {"seed": SEED, "temperature": 0.7, "max_tokens": 600, "cache_prompt": False}
    tr = {"seed": SEED, "temperature": 0, "max_tokens": 900, "cache_prompt": False}
    reqs = []
    for c in rows(cards):
        reqs.append({"id": f"de-off|{c['id']}", "messages": german_letter(soul[c["journey"]], c, False), "params": letter})
        reqs.append({"id": f"de-on|{c['id']}", "messages": german_letter(soul[c["journey"]], c, True), "params": letter})
        reqs.append({"id": f"translate|{c['id']}", "messages": translate(passages[c["id"]]["text"]), "params": tr})
    return write(out / "REQUESTS-1.jsonl", reqs)


def round2(folder):
    folder = Path(folder)
    replies = {r["id"]: r["reply"] for r in rows(folder / "REPLIES-1.jsonl")}
    tr = {"seed": SEED, "temperature": 0, "max_tokens": 900, "cache_prompt": False}
    reqs = [{"id": f"tr-{arm}|{c['id']}", "messages": translate(replies[f"de-{arm}|{c['id']}"]), "params": tr}
            for c in rows(folder / "CARDS.jsonl") for arm in ("off", "on")]
    return write(folder / "REQUESTS-2.jsonl", reqs)


def sheet(folder, arm, keyout):
    folder = Path(folder)
    r1 = {r["id"]: r["reply"] for r in rows(folder / "REPLIES-1.jsonl")}
    r2 = {r["id"]: r["reply"] for r in rows(folder / "REPLIES-2.jsonl")}
    rng = random.Random(f"{SEED}|2c|{arm}")
    out, key = [], {}
    for c in rows(folder / "CARDS.jsonl"):
        sim, truth = r2[f"tr-{arm}|{c['id']}"], r1[f"translate|{c['id']}"]
        x_real = rng.random() < 0.5
        pid = hashlib.sha256(f"{SEED}|2c|{arm}|{c['id']}".encode()).hexdigest()[:8]
        out.append({"pair": pid, "card": c["card"], "X": truth if x_real else sim, "Y": sim if x_real else truth})
        key[pid] = {"card": c["id"], "real": "X" if x_real else "Y", "arm": arm}
    rng.shuffle(out)
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out).encode()
    (folder / f"SHEET-{arm}.jsonl").write_bytes(data)
    k = json.dumps(key, indent=1, sort_keys=True).encode()
    Path(keyout).mkdir(parents=True, exist_ok=True)
    (Path(keyout) / f"KEY-2c-{arm}.json").write_bytes(k)
    return {"arm": arm, "pairs": len(out), "sheet_sha256": hashlib.sha256(data).hexdigest(), "key_sha256": hashlib.sha256(k).hexdigest()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("round1"); a1.add_argument("--cards", required=True); a1.add_argument("--out", required=True)
    a2 = sub.add_parser("round2"); a2.add_argument("--folder", required=True)
    s = sub.add_parser("sheet"); s.add_argument("--folder", required=True); s.add_argument("--arm", required=True, choices=("off", "on"))
    s.add_argument("--keyout", required=True)
    a = ap.parse_args(argv)
    res = round1(a.cards, a.out) if a.cmd == "round1" else round2(a.folder) if a.cmd == "round2" else sheet(a.folder, a.arm, a.keyout)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
