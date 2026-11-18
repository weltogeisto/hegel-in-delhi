"""The Paris backtest, stage 2 (pc/PARIS-BACKTEST.md; DECISIONS.md 55): given the same day, does he write home the way
the real Hegel did?

    python3 tools/paris_stage2.py entries --out <folder>            # the dated passages and their seeded order
    python3 tools/paris_stage2.py soul --out <folder>               # the travel version of his instructions, a fixed edit
    python3 tools/paris_stage2.py requests --folder <folder>        # after the cards: the PC's calls (letters, translations)
    python3 tools/paris_stage2.py sheet --folder <folder> --keyout <path outside the repo>   # after the replies: the judge's sheet

The real side is his own passage, put into English by plain Qwen under one fixed instruction, so that both sides have
passed through the same model's English. The cards are written by Claude agents that never judge; the judge is a fresh
agent that never sees the German. Evaluation only: no card, letter, translation or judgment is ever training data."""
import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.travel_register import JOURNEYS, journeys, work  # noqa: E402

SEED = 1831
PER_JOURNEY = 8
MIN_WORDS = 40
SEEDS = (1831, 2718, 3141)
LETTER_WORDS = 150
SOUL = REPO / "mind/soul-ordinary.md"
YEAR = {"Netherlands 1822": 1822, "Vienna 1824": 1824, "Paris 1827": 1827}
DATE_LINE = re.compile(r"^\s*(?:([A-ZÄÖÜ][\wäöüß\.]+),\s*)?(?:den|Den|d\.)\s*(\d{1,2})\.?\s*(\w+)", re.U)
PREMISE = ("You are Georg Wilhelm Friedrich Hegel, philosopher, born 1770 in Stuttgart, professor in Berlin since 1818. "
           "It is {year}, and you are on a journey through {country}. Your wife Marie and your sons are at home in Berlin, "
           "and you write to her as you travel.")
COUNTRY = {"Netherlands 1822": "the Rhineland and the Netherlands", "Vienna 1824": "Bohemia and Austria",
           "Paris 1827": "the Rhineland, Luxembourg and France"}
TRANSLATE = ("You translate German letters of the 1820s into plain modern English. Keep every fact, name, place, time and "
             "number. Add nothing, explain nothing, leave out nothing. Answer with the translation only.")


def entries():
    """Per journey, every paragraph of at least MIN_WORDS words, with the date line or heading it falls under."""
    out = {}
    for name, text in journeys(work("briefe-2")).items():
        dated, rows = None, []
        head = text.splitlines()[0].lstrip("# ").strip()
        for n, para in enumerate(re.split(r"\n\s*\n", text)):
            para = " ".join(para.split())
            first = para.split(". ")[0] if para else ""
            if DATE_LINE.match(para) and len(para.split()) < 12:
                dated = para
                continue
            if para.startswith("#") or para.lower().startswith("aus briefen") or len(para.split()) < MIN_WORDS:
                continue
            rows.append({"id": hashlib.sha256(f"{name}|{n}|{para}".encode()).hexdigest()[:10], "journey": name,
                         "dated": dated or head, "words": len(para.split()), "text": para})
        out[name] = rows
    return out


def order(rows, journey):
    """The seeded order in which passages are offered to the card writers."""
    rng = random.Random(f"{SEED}|{journey}")
    return rng.sample(rows, len(rows))


def travel_soul(text, journey):
    """His live instructions with the Delhi premise taken out, by one fixed edit: the opening becomes PREMISE; 'Who you
    are', 'Your life' and the first paragraph of 'How you sound' stay; Delhi's lines in them go, and so does his death;
    'What you know', the first day's thoughts, the world's rules and the answer format are not for a letter."""
    sections = re.split(r"(?m)^## ", text)
    keep = {}
    for sec in sections[1:]:
        title, _, body = sec.partition("\n")
        keep[title.strip()] = body.strip()
    who = "\n".join(l for l in keep["Who you are"].splitlines()
                    if "Hindi" not in l and "Delhi" not in l).replace("(whist in Berlin, bridge now)", "(whist)")
    life = re.sub(r"\s*You died in[^.]*\.", "", keep["Your life"].strip())              # a traveller of 1827 knows nothing after it
    sound = keep["How you sound"].split("\n\n")[0].strip()
    premise = PREMISE.format(year=YEAR[journey], country=COUNTRY[journey])
    return f"{premise}\n\n## Who you are\n\n{who}\n\n## Your life\n\n{life}\n\n## How you sound\n\n{sound}\n"


def letter_messages(soul, card):
    user = (f"{card['when']}, evening, {card['place']}.\n\nToday: {card['card']}\n\n"
            f"Write to Marie tonight, as you would: at most {LETTER_WORDS} words. Answer with the letter only.")
    return [{"role": "system", "content": soul}, {"role": "user", "content": user}]


def requests(folder):
    folder = Path(folder)
    cards = [json.loads(l) for l in (folder / "CARDS.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    passages = {r["id"]: r for rows in json.loads((folder / "ENTRIES.json").read_text(encoding="utf-8")).values() for r in rows}
    out = []
    for c in cards:
        soul = (folder / f"soul-{YEAR[c['journey']]}.md").read_text(encoding="utf-8")
        for seed in SEEDS:
            out.append({"id": f"letter|{c['id']}|{seed}", "messages": letter_messages(soul, c),
                        "params": {"seed": seed, "temperature": 0.7, "max_tokens": 400, "cache_prompt": False}})
        out.append({"id": f"translate|{c['id']}", "messages": [{"role": "system", "content": TRANSLATE},
                                                                  {"role": "user", "content": passages[c["id"]]["text"]}],
                    "params": {"seed": SEED, "temperature": 0, "max_tokens": 900, "cache_prompt": False}})
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out).encode()
    (folder / "REQUESTS.jsonl").write_bytes(data)
    return {"requests": len(out), "sha256": hashlib.sha256(data).hexdigest()}


def sheet(folder, keyout):
    """One pair per card: the first seed's letter against the translated passage, sides shuffled; the key apart."""
    folder = Path(folder)
    replies = {json.loads(l)["id"]: json.loads(l)["reply"] for l in (folder / "REPLIES.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    cards = [json.loads(l) for l in (folder / "CARDS.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rng = random.Random(SEED)
    rows, key = [], {}
    for c in cards:
        sim, real = replies[f"letter|{c['id']}|{SEEDS[0]}"], replies[f"translate|{c['id']}"]
        x_real = rng.random() < 0.5
        pid = hashlib.sha256(f"{SEED}|{c['id']}".encode()).hexdigest()[:8]
        rows.append({"pair": pid, "card": c["card"], "X": real if x_real else sim, "Y": sim if x_real else real})
        key[pid] = {"card": c["id"], "real": "X" if x_real else "Y"}
    rng.shuffle(rows)
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode()
    (folder / "SHEET.jsonl").write_bytes(data)
    k = json.dumps(key, indent=1, sort_keys=True).encode()
    Path(keyout).parent.mkdir(parents=True, exist_ok=True)
    Path(keyout).write_bytes(k)
    return {"pairs": len(rows), "sheet_sha256": hashlib.sha256(data).hexdigest(), "key_sha256": hashlib.sha256(k).hexdigest()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("entries"); e.add_argument("--out", required=True)
    s = sub.add_parser("soul"); s.add_argument("--out", required=True)
    r = sub.add_parser("requests"); r.add_argument("--folder", required=True)
    h = sub.add_parser("sheet"); h.add_argument("--folder", required=True); h.add_argument("--keyout", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "entries":
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        ent = entries()
        (out / "ENTRIES.json").write_text(json.dumps(ent, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (out / "ORDER.json").write_text(json.dumps({j: [r["id"] for r in order(rows, j)] for j, rows in ent.items()}, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({j: len(rows) for j, rows in ent.items()}))
    elif a.cmd == "soul":
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        text = SOUL.read_text(encoding="utf-8")
        for j in JOURNEYS:
            (out / f"soul-{YEAR[j]}.md").write_text(travel_soul(text, j), encoding="utf-8")
        print("ok")
    elif a.cmd == "requests":
        print(json.dumps(requests(a.folder)))
    else:
        print(json.dumps(sheet(a.folder, a.keyout)))


if __name__ == "__main__":
    main()
