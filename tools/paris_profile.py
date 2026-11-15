#!/usr/bin/env python3
"""The Paris backtest, stage 1: what he writes about abroad, the real man against the simulated one (pc/PARIS-BACKTEST.md).

    python3 tools/paris_profile.py sample --repo . --shadow SHA --out DIR      the sheet, frozen before any coding
    python3 tools/paris_profile.py requests --sheet DIR                       plain Qwen as the second coder: one request per sentence
    python3 tools/paris_profile.py report --sheet DIR [--qwen REPLIES.jsonl]   the profiles, after the codes are committed

Three groups of sentences, each drawn with seed 1831:
  - letters: 300 from his letters to his wife from three journeys, 100 per journey (mind/shelf/briefe-2);
  - evening: 300 from the simulation's nearest genre, the owl's diary and his writings on complete shadow days;
  - thoughts: 150 from his decision thoughts on the same days, reported beside the other two.
The sheet holds the sentences in one shuffled order under opaque IDs; KEY.json says which group each came from.
Claude codes the sheet into CODES-CLAUDE.jsonl ({"id", "code"}) by CODEBOOK.md. Evaluation only: no sentence,
code or reply here is ever training data.
"""
import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.travel_register import JOURNEYS, journeys, work  # noqa: E402
from world.shelf import sentences  # noqa: E402

SEED = 1831
SIZES = {"letters": 300, "evening": 300, "thoughts": 150}
MIN_WORDS = 5
CODES = {
    1: "travel, logistics and errands",
    2: "money and prices",
    3: "food, drink and the body",
    4: "people met and what they said",
    5: "sights, art and the theatre",
    6: "comparison with home",
    7: "family and affection",
    8: "public affairs and history",
    9: "philosophy proper",
    10: "other",
}
CODEBOOK = """# Codebook: what a sentence is about

One code per sentence, for its main topic. The main clause decides. When two topics weigh the same, the one named first.

1. **Travel, logistics and errands.** Journeys, routes and transport; lodging and rooms; times, plans and arrangements for the day; passports, offices and paperwork about his own affairs; errands.
2. **Money and prices.** What something costs, paying, cash, accounts, debts, budgets, earnings.
3. **Food, drink and the body.** Meals, eating and drinking, hunger, thirst, tiredness, sleep, health and illness, heat and cold as the body feels them.
4. **People met and what they said.** Who was there, encounters and visits, conversations, a person described, someone's words or manner.
5. **Sights, art and the theatre.** Buildings, monuments, streets and city views, landscapes, gardens; museums and paintings; theatre, opera and music.
6. **Comparison with home.** An explicit comparison of the place with his home country or city.
7. **Family and affection.** His wife and children, greetings and love, longing for home, family news.
8. **Public affairs and history.** The state, politics, laws and institutions as such; the news; wars and historical events and figures.
9. **Philosophy proper.** A general philosophical claim, or a reflection in the concepts of his system (spirit, the universal and the particular, the concept, the idea, mediation, negation, freedom as a concept), religion as doctrine, a judgment about ideas or books of philosophy.
10. **Other.** Anything else: weather as such, his reading and writing as activities, a mood with no object, a sentence that cannot be placed.

A concrete sentence keeps its concrete code even when it carries a philosophical phrase: "I paid fifty rupees for the immediate negation of hunger" is 2. A sentence whose point is the philosophical claim is 9: "Hunger is the negation that the body must sublate" is 9.
"""
INSTRUCTION = ("You code sentences by topic. Read the codebook, then answer with the number of the one code that fits the "
               "sentence's main topic, and nothing else.\n\n")


def digest(b):
    return hashlib.sha256(b).hexdigest()


def usable(sentence):
    return len(sentence.split()) >= MIN_WORDS and not re.match(r"^(aus|Aus) (Hegels )?Briefen", sentence)


def split(text):
    """Sentences of a text, by paragraph: a paragraph under 8 words (a date, a heading) is left out."""
    out = []
    for para in re.split(r"\n\s*\n", text or ""):
        para = " ".join(para.split())
        if para.startswith("#") or len(para.split()) < 8:
            continue
        out += [s for s in sentences(para) if usable(s)]
    return out


def letter_pool(repo):
    trips = journeys(work("briefe-2", repo))
    return {name: split(trips[name]) for name in JOURNEYS}


def shadow_days(repo, sha):
    """{date: day} of the complete days on the shadow branch at sha."""
    names = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", sha, "docs/days/"], check=True,
                           capture_output=True, text=True).stdout.split()
    out = {}
    for name in sorted(n for n in names if re.search(r"/\d{4}-\d{2}-\d{2}\.json$", n)):
        day = json.loads(subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{name}"], check=True,
                                        capture_output=True, text=True).stdout)
        if day.get("complete"):
            out[day["date"]] = day
    return out


def simulated_pools(days):
    """(evening, thoughts): [(date, sentence)] from the owl's diary and his writings, and from his decision thoughts."""
    evening, thoughts = [], []
    for date, day in sorted(days.items()):
        owl = day.get("owl") or {}
        texts = [owl.get("diary")] if isinstance(owl, dict) and isinstance(owl.get("diary"), str) else []
        texts += [e.get("text") for e in day.get("entries", []) if e.get("k") == "writing" and isinstance(e.get("text"), str)]
        for t in texts:
            evening += [(date, s) for s in split(t)]
        for e in day.get("entries", []):
            if e.get("k") == "diary" and isinstance(e.get("text"), str):
                thoughts += [(date, s) for s in sentences(" ".join(e["text"].split())) if usable(s)]
    return evening, thoughts


def draw(pool, n, rng):
    if len(pool) < n:
        raise ValueError(f"too few sentences: {len(pool)} for {n}")
    return rng.sample(pool, n)


def sample(repo, sha, out):
    repo, out = Path(repo), Path(out)
    if out.exists():
        raise FileExistsError("use a new directory")
    letters = letter_pool(repo)
    days = shadow_days(repo, sha)
    evening, thoughts = simulated_pools(days)
    rows = []
    per = SIZES["letters"] // len(JOURNEYS)
    for name in JOURNEYS:
        rows += [dict(group="letters", source=name, text=s) for s in draw(letters[name], per, random.Random(f"{SEED}:{name}"))]
    rows += [dict(group="evening", source=d, text=s) for d, s in draw(evening, SIZES["evening"], random.Random(f"{SEED}:evening"))]
    rows += [dict(group="thoughts", source=d, text=s) for d, s in draw(thoughts, SIZES["thoughts"], random.Random(f"{SEED}:thoughts"))]
    for n, r in enumerate(rows):
        r["id"] = digest(f"{r['group']}|{r['source']}|{n}|{r['text']}".encode())[:12]
    random.Random(SEED).shuffle(rows)
    out.mkdir(parents=True)
    sheet = "".join(json.dumps({"id": r["id"], "text": r["text"]}, ensure_ascii=False) + "\n" for r in rows)
    (out / "SHEET.jsonl").write_text(sheet, encoding="utf-8")
    key = {r["id"]: {"group": r["group"], "source": r["source"]} for r in rows}
    (out / "KEY.json").write_text(json.dumps(key, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "CODEBOOK.md").write_text(CODEBOOK, encoding="utf-8")
    manifest = dict(
        study="Paris backtest, stage 1 (pc/PARIS-BACKTEST.md)", shadow=sha, seed=SEED, sizes=SIZES,
        pools={"letters": {k: len(v) for k, v in letters.items()}, "evening": len(evening), "thoughts": len(thoughts)},
        shadow_days=sorted(days), codes=CODES,
        files={n: digest((out / n).read_bytes()) for n in ("SHEET.jsonl", "KEY.json", "CODEBOOK.md")},
        coders=["Claude, by CODEBOOK.md, into CODES-CLAUDE.jsonl", "plain Qwen, temperature 0, by the same codebook (requests)"],
        note="German against English gives the letters away; the codebook, the second coder and the committed codes stand in for blinding.",
        training_eligible=False)
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def read_sheet(folder):
    return [json.loads(x) for x in (Path(folder) / "SHEET.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def requests(folder):
    """One chat request per sentence for plain Qwen as the second coder, in the sheet's order."""
    book = (Path(folder) / "CODEBOOK.md").read_text(encoding="utf-8")
    return [{"id": r["id"], "messages": [{"role": "system", "content": INSTRUCTION + book},
                                          {"role": "user", "content": r["text"]}],
             "settings": {"temperature": 0, "max_tokens": 4, "seed": SEED}} for r in read_sheet(folder)]


def parse(reply):
    """The code in a reply, or None: the first whole number from 1 to 10."""
    m = re.search(r"\b(10|[1-9])\b", reply or "")
    return int(m.group(1)) if m else None


def kappa(a, b):
    """Cohen's kappa of two equal-length lists of codes."""
    n = len(a)
    if not n:
        return None
    seen = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    chance = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((seen - chance) / (1 - chance), 3) if chance < 1 else 1.0


def shares(codes):
    n = len(codes)
    c = Counter(codes)
    return {k: round(c[k] / n, 3) if n else 0.0 for k in CODES}


def distance(p, q):
    """Total variation distance of two code distributions: half the summed absolute differences, 0 to 1."""
    return round(sum(abs(p[k] - q[k]) for k in CODES) / 2, 3)


def report(folder, qwen=None):
    folder = Path(folder)
    key = json.loads((folder / "KEY.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, want in manifest["files"].items():
        if digest((folder / name).read_bytes()) != want:
            raise ValueError(f"{name} changed after the sample was frozen")
    claude = {r["id"]: r["code"] for r in (json.loads(x) for x in (folder / "CODES-CLAUDE.jsonl").read_text(encoding="utf-8").splitlines() if x.strip())}
    if set(claude) != set(key) or not all(c in CODES for c in claude.values()):
        raise ValueError("CODES-CLAUDE.jsonl must give every sheet ID one code from 1 to 10")
    coders = {"claude": claude}
    if qwen is not None:
        replies = {r["id"]: parse(r.get("reply")) for r in (json.loads(x) for x in Path(qwen).read_text(encoding="utf-8").splitlines() if x.strip())}
        if set(replies) != set(key):
            raise ValueError("the Qwen replies must cover the sheet's IDs exactly")
        coders["qwen"] = replies
    out = {"groups": {}, "rule": "Paris backtest stage 1; a profile, never a gate", "training_eligible": False}
    for g in SIZES:
        ids = sorted(i for i, k in key.items() if k["group"] == g)
        out["groups"][g] = {name: shares([c[i] for i in ids if c[i] is not None]) for name, c in coders.items()}
        out["groups"][g]["n"] = len(ids)
        if g == "letters":
            out["groups"][g]["by_journey"] = {j: shares([claude[i] for i in ids if key[i]["source"] == j]) for j in JOURNEYS}
    out["distance"] = {f"letters vs {g}": {name: distance(out["groups"]["letters"][name], out["groups"][g][name]) for name in coders}
                       for g in ("evening", "thoughts")}
    if "qwen" in coders:
        both = [i for i in key if coders["qwen"][i] is not None]
        out["agreement"] = {"kappa_all": kappa([claude[i] for i in both], [coders["qwen"][i] for i in both]),
                            "unparsed_replies": len(key) - len(both)}
        for g in SIZES:
            ids = [i for i in both if key[i]["group"] == g]
            out["agreement"][f"kappa_{g}"] = kappa([claude[i] for i in ids], [coders["qwen"][i] for i in ids])
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--repo", type=Path, default=Path("."))
    s.add_argument("--shadow", required=True)
    s.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("requests")
    r.add_argument("--sheet", type=Path, required=True)
    r.add_argument("--out", type=Path, help="a new JSONL file; else standard output")
    t = sub.add_parser("report")
    t.add_argument("--sheet", type=Path, required=True)
    t.add_argument("--qwen", type=Path)
    t.add_argument("--out", type=Path)
    a = p.parse_args(argv)
    if a.cmd == "sample":
        print(json.dumps({k: v for k, v in sample(a.repo, a.shadow, a.out).items() if k in ("pools", "sizes", "shadow_days")}))
    elif a.cmd == "requests":
        text = "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in requests(a.sheet))
        if a.out:
            if a.out.exists():
                p.error(f"{a.out} exists")
            a.out.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
    else:
        result = report(a.sheet, a.qwen)
        text = json.dumps(result, indent=1) + "\n"
        if a.out:
            if a.out.exists():
                p.error(f"{a.out} exists")
            a.out.write_text(text, encoding="utf-8")
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
