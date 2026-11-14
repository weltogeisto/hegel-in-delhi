#!/usr/bin/env python3
"""The Paris backtest's first read: how much lecture-hall vocabulary he used when he wrote home from a journey. No model call.

    python3 tools/travel_register.py [--thoughts FILE.jsonl --field text] [--out READ.json]

It counts sixteen notions of the system per 100 words in four places:
  - his letters to his wife from three journeys (the Netherlands 1822, Vienna 1824, Paris 1827; mind/shelf/briefe-2),
  - his own treatise in German (Philosophie des Rechts) and in English (Dyde), as anchors for the two word lists,
  - and, with --thoughts, any JSONL of the simulation's texts.
The English list is tools.prompt_screen.DOCTRINE, as the M1 screen declared it; the German one names the same notions.
The anchors say how far the two lists agree on one book. A read, never a gate. Evaluation only.
"""
import argparse
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.prompt_screen import DOCTRINE as EN  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DE = re.compile(r"\b(dialekti\w*|allgemein\w*|besonder\w*|geist\w*|sittlich\w*|negat\w+|vermitt\w+|aufheb\w+|aufgehoben\w*"
                r"|wirklichkeit\w*|verwirklich\w+|absolut\w*|substanz\w*|abstra[ck]t\w*|begriff\w*"
                r"|bürgerliche\w* gesellschaft|system der bedürfnisse|die idee|der idee)\b", re.I)
JOURNEYS = {"Netherlands 1822": "## Reise nach den Niederlanden", "Vienna 1824": "## Reise nach Wien", "Paris 1827": "## Reise nach Paris"}


def work(name, repo=REPO):
    with gzip.open(Path(repo) / f"mind/shelf/{name}.txt.gz", "rt", encoding="utf-8") as f:
        return f.read()


def journeys(letters):
    """{journey: its section of the letters}, each from its heading to the next heading."""
    heads = [(m.start(), m.group(0)) for m in re.finditer(r"^## .*$", letters, re.M)]
    out = {}
    for name, start in JOURNEYS.items():
        k = next(i for i, (_, h) in enumerate(heads) if h.startswith(start))
        out[name] = letters[heads[k][0]:heads[k + 1][0] if k + 1 < len(heads) else len(letters)]
    return out


def rate(text, terms):
    words = len(re.findall(r"\w+", text))
    hits = len(terms.findall(text))
    return {"words": words, "terms": hits, "per_100_words": round(100 * hits / words, 2) if words else None}


def read(repo=REPO, thoughts=None):
    trips = journeys(work("briefe-2", repo))
    whole = "\n\n".join(trips.values())
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", whole) if len(s.split()) > 4]
    out = {"journeys": {k: rate(v, DE) for k, v in trips.items()},
           "letters_from_three_journeys": dict(rate(whole, DE), sentences=len(sentences), sentences_with_a_term=sum(bool(DE.search(s)) for s in sentences)),
           "anchor_philosophie_des_rechts_german_list": rate(work("rechts", repo), DE),
           "anchor_philosophy_of_right_english_list": rate(work("dyde-right", repo), EN),
           "rule": "Paris backtest, first read; never a gate", "training_eligible": False}
    if thoughts is not None:
        texts = [t for t in thoughts if t.strip()]
        out["simulation"] = dict(rate(" ".join(texts), EN), texts=len(texts), texts_with_a_term=sum(bool(EN.search(t)) for t in texts))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--thoughts", type=Path, help="a JSONL of the simulation's texts")
    p.add_argument("--field", default="text")
    p.add_argument("--out", type=Path, help="a new file for the read")
    a = p.parse_args(argv)
    if a.out and a.out.exists():
        p.error(f"{a.out} exists")
    thoughts = None
    if a.thoughts:
        thoughts = [json.loads(x).get(a.field) or "" for x in a.thoughts.read_text(encoding="utf-8").splitlines() if x.strip()]
    result = read(thoughts=thoughts)
    text = json.dumps(result, indent=1, ensure_ascii=False) + "\n"
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
