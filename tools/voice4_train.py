#!/usr/bin/env python3
"""Training 4's training set (pc/TRAINING-4.md, "Training 4 · His letters"): a card in, his real passage out. The PC runs the
model calls; this tool writes the request files and assembles the results. No model call is made here, and the same input
gives the same bytes.

    python3 tools/voice4_train.py passages --out F            # no GPU: his passages (train and held out), the OCR rule, the leak check
    python3 tools/voice4_train.py cards --folder F            # requests: a card for each passage
    python3 tools/voice4_train.py check --folder F --round 1  # after the cards' replies: the symmetry check
    python3 tools/voice4_train.py merge --folder F --round 1  # after the check's replies (then check and merge --round 2)
    python3 tools/voice4_train.py build --folder F            # after the final cards: TRAIN.jsonl, HELDOUT.jsonl, TRAIN-MANIFEST.json

Each requests file goes to the PC with tools/run_requests.py; its replies come back as REPLIES-<name>.jsonl in the folder.
`cards`, `check` and `merge` are tools/voice4.py's own, with its instructions and its symmetry check, unchanged.

- **Targets:** his own words, untouched. The training passages are the instrument's pool (`tools/voice4.py`): his letters
  outside the tenth held out, the Netherlands journey of 1822 (the one journey given to training, `DECISIONS.md` 65) and his
  two diaries, German paragraphs only. The held-out passages are the tenth of his letters held out, for early stopping.
  Cleaning is by rule only (`voice4.paragraphs`), plus the OCR rule: a passage is dropped whole when more than OCR_SHARE of
  its words are not in the corpus's own word list (a word is known if it occurs OCR_KNOWN times). Nothing is rewritten.
- **The leak check:** no passage may share LEAK_RUN words in a row with any passage of the development journey (Vienna 1824)
  or the sealed one (Paris 1827). It raises an error. It runs again on the targets in `build`.
- **Pairs:** for each training passage with a card, one row with the card's lines in order and one with the same lines
  shuffled (a second call at temperature 0 would return the same card, so the second pair varies only the order). Each
  held-out passage with a card gives one row. The prompt is `works.letter4_prompt`.

Nothing from pc/exports/ evaluation folders is training data; the folder given here is this tool's own."""
import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools import voice4  # noqa: E402
from tools.travel_register import work  # noqa: E402
from world import works  # noqa: E402

SEED = voice4.SEED
OCR_KNOWN = 3                       # a word occurring at least this often in the corpus is known
OCR_SHARE = 0.30                    # a passage with more than this share of unknown words is dropped
LEAK_RUN = 12                       # words in a row that a target may not share with a development or sealed passage
SEALED = ("Vienna 1824", "Paris 1827")
CORPUS = ("briefe-1", "briefe-2", "rosenkranz-urkunden")
ALPHA = re.compile(r"[^\W\d_]{2,}")
SENTENCE = "Targets are his own words; inputs are the local model's cards under fixed instructions (pc/TRAINING-4.md)."


def volume(name, volumes=None):
    """A volume of the shelf; when `volumes` is given (a test's corpus) it is the whole shelf, and a missing volume is empty."""
    return volumes.get(name, "") if volumes is not None else work(name)


# ── the passages ────────────────────────────────────────────────────

def mark_first(passage_rows, key):
    """Each row gains `first`: true for the first row of its `key`."""
    seen, out = set(), []
    for p in passage_rows:
        out.append(dict(p, first=p[key] not in seen))
        seen.add(p[key])
    return out


def training_journey(volumes=None):
    """The training journey's passages (`voice4.training_journey`: each date line a letter to his wife); the first under a date
    line is `first`."""
    return [dict(p, source="journey") for p in mark_first(voice4.training_journey(volumes), "letter")]


def diaries(volumes=None):
    """His two diaries' passages (`voice4.diaries`: German paragraphs only); each stands for itself, so each is `first`."""
    return [dict(p, first=True, source="diary") for p in voice4.diaries(volumes)]


def tokens(text):
    return ALPHA.findall(text.lower())


def word_list(volumes=None):
    """The words of the corpus itself that occur at least OCR_KNOWN times."""
    count = Counter()
    for name in CORPUS:
        count.update(tokens(volume(name, volumes)))
    return {w for w, n in count.items() if n >= OCR_KNOWN}


def unknown_share(text, known):
    toks = tokens(text)
    return sum(t not in known for t in toks) / len(toks) if toks else 0.0


def split_ocr(passage_rows, known):
    """(kept, dropped): a passage with more than OCR_SHARE unknown words is dropped, with its share and its start."""
    kept, dropped = [], []
    for p in passage_rows:
        share = unknown_share(p["text"], known)
        if share > OCR_SHARE:
            dropped.append({"id": p["id"], "set": p["set"], "share": round(share, 3), "start": p["text"][:80]})
        else:
            kept.append(p)
    return kept, dropped


def grams(text, n=LEAK_RUN):
    w = re.findall(r"\w+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def leak_check(texts, volumes=None):
    """Raise when any of `texts` shares LEAK_RUN words in a row with a passage of the development or the sealed journey."""
    sealed = set()
    for p in voice4.development(volumes, names=SEALED):
        sealed |= grams(p["text"])
    for t in texts:
        if grams(t) & sealed:
            raise ValueError(f"leak: a passage shares {LEAK_RUN} words in a row with {' or '.join(SEALED)}: {t[:60]!r}")


def cmd_passages(out, volumes=None):
    out = Path(out)
    pool, held, _ = voice4.split(voice4.letters(volumes))
    his = lambda letters: [dict(p, source="letter") for p in mark_first(voice4.passages_of(letters, "hegel"), "letter")]
    train = his(pool) + training_journey(volumes) + diaries(volumes)
    heldp = his(held)
    every = [dict(p, set="train") for p in train] + [dict(p, set="held") for p in heldp]
    kept, dropped = split_ocr(every, word_list(volumes))
    leak_check([p["text"] for p in kept], volumes)
    out.mkdir(parents=True, exist_ok=True)
    (out / "DROPPED-OCR.json").write_text(json.dumps({"known_at_least": OCR_KNOWN, "share_over": OCR_SHARE, "dropped": dropped},
                                                     ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    res = {"passages": voice4.put(out / "PASSAGES.jsonl", kept), "dropped_ocr": len(dropped)}
    for s in ("train", "held"):
        mine = [p for p in kept if p["set"] == s]
        res[s] = {"passages": len(mine), "words": sum(p["words"] for p in mine), "letters": len({p["letter"] for p in mine}),
                  "by_source": dict(sorted(Counter(p["source"] for p in mine).items()))}
    res["leak_check"] = f"no run of {LEAK_RUN} words shared with {' or '.join(SEALED)}"
    (out / "PASSAGES-MANIFEST.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return res


# ── the pairs ───────────────────────────────────────────────────────

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows_for(p, lines):
    """The rows of one passage with a card: training gives the card's order and, if it differs, a shuffled order; held gives one."""
    orders = [("a", lines)]
    if p["set"] == "train":
        shuffled = list(lines)
        random.Random(f"{SEED}|order|{p['id']}").shuffle(shuffled)
        if len(lines) >= 2 and shuffled != lines:
            orders.append(("b", shuffled))
    return [{"id": f"{p['id']}|{tag}" if p["set"] == "train" else p["id"],
             "prompt": works.letter4_prompt(p["head"], order, goes_on=not p["first"]), "target": p["text"]} for tag, order in orders]


GERMAN_RECORD = 4                    # this many different German function words in a card, and the card has kept his German
NAME_WORDS = {"von", "so"}           # a German name or an English word: not counted


def copies(card_lines, text):
    """Does the card hand him his own words? It shares LEAK_RUN words in a row with the passage, or it is written in German.
    A row built from such a card teaches the adapter to copy from the prompt, not to write from the facts (25 November)."""
    card = "\n".join(card_lines)
    german = {w.lower() for w in voice4.GERMAN.findall(card)} - NAME_WORDS
    return bool(grams(card) & grams(text)) or len(german) >= GERMAN_RECORD


def cmd_build(folder, volumes=None):
    folder = Path(folder)
    passages = voice4.rows(folder / "PASSAGES.jsonl")
    cards = {c["id"]: c["card"].split("\n") for c in voice4.rows(folder / "CARDS.jsonl")}
    if any(p.get("journey") in SEALED for p in passages):
        raise ValueError("a development or sealed journey is among the passages")
    train, held, used, copied = [], [], [], []
    for p in passages:
        if p["id"] in cards and copies(cards[p["id"]], p["text"]):
            copied.append(p["id"])
        elif p["id"] in cards:
            (train if p["set"] == "train" else held).extend(rows_for(p, cards[p["id"]]))
            used.append(p)
    leak_check([p["text"] for p in used], volumes)
    res = {"train": voice4.put(folder / "TRAIN.jsonl", train), "held": voice4.put(folder / "HELDOUT.jsonl", held)}
    mine = [p for p in used if p["set"] == "train"]
    lost = json.loads((folder / "DROPPED.json").read_text(encoding="utf-8")) if (folder / "DROPPED.json").exists() else {}
    ocr = folder / "DROPPED-OCR.json"
    manifest = {"passages": len(mine), "pairs": len(train), "held": len(held),
                "words": {"train_passages": sum(p["words"] for p in mine), "train_targets": sum(voice4.n_words(r["target"]) for r in train),
                          "held_passages": sum(p["words"] for p in used if p["set"] == "held")},
                "sha256": {"TRAIN.jsonl": res["train"]["sha256"], "HELDOUT.jsonl": res["held"]["sha256"],
                           "PASSAGES.jsonl": sha(folder / "PASSAGES.jsonl"), "CARDS.jsonl": sha(folder / "CARDS.jsonl")},
                "dropped": {"ocr": len(json.loads(ocr.read_text(encoding="utf-8"))["dropped"]) if ocr.exists() else None,
                            "no_card": len(lost.get("no_card", [])), "lacking_after_two_rounds": len(lost.get("lacking_after_two_rounds", [])),
                            "card_copies_his_words": len(copied), "copied": copied},
                "constants": {"SEED": SEED, "OCR_KNOWN": OCR_KNOWN, "OCR_SHARE": OCR_SHARE, "LEAK_RUN": LEAK_RUN, "LO": voice4.LO,
                              "HI": voice4.HI, "HELD_EVERY": voice4.HELD_EVERY},
                "leak_check": f"no run of {LEAK_RUN} words shared with {' or '.join(SEALED)}",
                "note": SENTENCE}
    (folder / "TRAIN-MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("passages").add_argument("--out", required=True)
    for name in ("cards", "build"):
        sub.add_parser(name).add_argument("--folder", required=True)
    for name in ("check", "merge"):
        p = sub.add_parser(name)
        p.add_argument("--folder", required=True)
        p.add_argument("--round", type=int, required=True, choices=(1, 2))
    a = ap.parse_args(argv)
    res = (cmd_passages(a.out) if a.cmd == "passages" else voice4.cmd_cards(a.folder) if a.cmd == "cards"
           else voice4.cmd_check(a.folder, a.round) if a.cmd == "check" else voice4.cmd_merge(a.folder, a.round) if a.cmd == "merge"
           else cmd_build(a.folder))
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
