#!/usr/bin/env python3
"""Training 4's instrument (pc/TRAINING-4.md): full-fact cards by rule, the rungs without training, blind pairs and the
rule for invented particulars. Plain Qwen only; nothing here trains or loads an adapter.

    python3 tools/voice4.py passages --out F                 # no GPU: the development passages (Vienna), the pool, the controls
    python3 tools/voice4.py cards --folder F                 # requests: a card for each development passage
    python3 tools/voice4.py check --folder F --round 1       # after the cards' replies: the symmetry check
    python3 tools/voice4.py merge --folder F --round 1       # after the check's replies: lines added (then check and merge --round 2)
    python3 tools/voice4.py arms --folder F                  # after the final cards: letters P0, P1, P2 in German; the real side's translations
    python3 tools/voice4.py translate --folder F             # after the letters: each put into English by the same instruction
    python3 tools/voice4.py sheet --folder F --arm P0 --keyout D [--mirror]
    python3 tools/voice4.py particulars --folder F           # particulars a letter has and its card lacks, beside the real side's floor
    python3 tools/voice4.py classify --folder F              # can a classifier tell him from his correspondents, and each arm from him?
    python3 tools/voice4.py judge --folder F                 # requests: the fixed judge on the rewrites readers have already marked
    python3 tools/voice4.py judge-score --folder F           # after its replies: does the judge find what the readers found?

Each requests file goes to the PC with tools/run_requests.py; its replies come back as REPLIES-<name>.jsonl in the folder.

- **Cards:** plain Qwen at temperature 0 lists what a passage states about the world, in short English lines. A second call
  lists what the passage states and the card lacks; those lines are added, once more at most, and a passage whose card
  still lacks any is dropped and counted. A card then carries every fact its passage states.
- **Arms:** the same request for each, in German, as long as the real passage. P0 plain; P1 with three of his letters in
  front; P2 with as many as twenty, within a word budget. The letters come from the pool: his letters outside the tenth
  held out, the training journey (the Netherlands) and his two diaries. What is of the journeys' kind comes first: the
  letters to his wife, the training journey and the diary of the Alps.
- **Controls:** passages of his letters and of his correspondents', for the classifier's qualification.
- **Particulars:** numbers and names in a letter's English that its card lacks. The real passage's own count against its
  card is the rule's floor.
- **The classifier:** Burrows's Delta over the most frequent words and marks, on bundles of about 600 words, each bundle
  judged against the two sides without it. It qualifies if it tells his letters from his correspondents'; then it is read
  for each arm against him.
- **The fixed judge:** plain Qwen lists what a rewrite states or changes that its source does not. It is validated on the
  forty (80 rewrites) and W8 (216), which readers marked: it gates only if it flags at least 80% of the substantive
  defects and at most 10% of the rewrites the readers passed.

Evaluation only: no card, letter, translation or judgment made here is ever training data. The cards for the training
letters are made later, by the same instructions, in a run of their own."""
import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.paris_stage2 import TRANSLATE, YEAR  # noqa: E402
from tools.travel_register import JOURNEYS, journeys, work  # noqa: E402

SEED = 1831
STAGE2 = REPO / "pc/exports/paris-stage2-20261118"
DEVELOPMENT = ("Vienna 1824",)                              # Paris 1827 is the sealed confirmation
TRAINING_JOURNEY = "Netherlands 1822"                       # one journey joins the training letters (DECISIONS.md 65)
DIARIES = {"Tagebuch der Reise in die Berner Oberalpen": True, "Hegel's Tagebuch aus der Gymnasialzeit": False}   # his diaries: is it the journeys' kind?
GERMAN = re.compile(r"\b(der|die|das|und|ich|nicht|ein|eine|zu|den|mit|von|ist|war|wir|auf|sich|so|als|daß)\b", re.I)
LO, HI = 80, 350                                            # words a passage holds
HELD_EVERY = 10                                             # every tenth of his letters, by year, is held out
CONTROLS = 150                                              # passages a side for the classifier's qualification
BUNDLE = 600                                                # words a text needs before the classifier can tell writers apart
NEAR = re.compile(r"seine Frau|Braut")                      # letters of the journeys' kind: to his wife or bride
P1_SHOWN, P2_SHOWN, P2_WORDS = 3, 20, 6000                  # exemplars in front; P2's word budget (about 12,000 tokens)
ARMS = ("P0", "P1", "P2")

CARD = ("You read a passage from a German letter of the early nineteenth century and list what it states about the world. "
        "Write short English lines, one statement a line, each beginning with '- '. List every event, person, place, time, "
        "weather, price, sum, thing seen, heard or eaten, plan and decision the passage states, each with its particulars "
        "(names, numbers, hours) exactly as given. Do not list the writer's judgments, feelings, greetings or reflections. "
        "Add nothing the passage does not state. Answer with the lines only.")
CHECK = ("You compare a German passage with a list of English lines. List every statement about the world that the passage "
         "makes and the lines lack: events, persons, places, times, weather, prices, sums, things seen, heard or eaten, plans "
         "and decisions, each with its particulars. One short English line each, beginning with '- '. Do not list judgments, "
         "feelings, greetings or reflections. If the lines lack nothing, answer NONE.")
FACTS = "Tell what the day's record holds; add no event, person, price or hour that it does not give. "
JUDGE = ("You compare a source text with a rewrite of it. List every statement about the world that the rewrite makes and the "
         "source does not make, or that the rewrite changes: events, persons, places, times, quantities, prices, sums, and what "
         "the writer decides or concludes. One short line each, beginning with '- '. Do not list changes of wording, tone or "
         "reasoning. If there is none, answer NONE.")
T0 = {"seed": SEED, "temperature": 0, "cache_prompt": False}
FORTY = REPO / "pc/exports/training1-20261106"
W8 = REPO / "pc/exports/lora-fresh-scenes-20261119/readers"
TOP = 150                                                   # the classifier's most frequent words and marks
RECALL, FALSE_ALARM = 0.8, 0.1                              # the judge's bars (pc/TRAINING-4.md)
TOKEN = re.compile(r"[a-zäöüß']+|[;:,!?—–]")

FOOT_LINE = re.compile(r"^\W{0,3}(\d{1,2}\)|\)|\*\))")          # a footnote of the edition
FOOT_MARK = re.compile(r"(?<=\w)[\d?!]\)|\s\d{1,2}\)(?=[\s.,;:!?]|$)")
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ„\"])")
NUMBER = re.compile(r"\b\d+(?:[.,:/]\d+)*\b")
WORDS_NUM = {w: str(n) for n, w in enumerate("two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                                             "sixteen seventeen eighteen nineteen twenty".split(), 2)}      # "one" is mostly a pronoun
WORDS_NUM.update({"thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80", "ninety": "90",
                  "hundred": "100", "thousand": "1000"})
NAME = re.compile(r"(?<=[a-z,;:] )([A-ZÄÖÜ][\wäöüßé'-]{2,})")
COMMON = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "January", "February", "March", "April",
          "May", "June", "July", "August", "September", "October", "November", "December", "God", "Lord", "Sir", "Madame",
          "Mrs", "Herr", "Frau", "Professor", "Marie", "German", "French", "Dutch", "English", "Italian"}


def rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def put(path, items):
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items).encode()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)
    return {"rows": len(items), "sha256": hashlib.sha256(data).hexdigest()}


def n_words(text):
    return len(text.split())


# ── the letters ─────────────────────────────────────────────────────

def paragraphs(text):
    """The paragraphs of one section of the edition: footnotes dropped, their marks removed, and a paragraph the page broke
    (it ends without a full stop and the next begins in lower case) joined to the next. Nothing is rewritten."""
    out = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if not para or para.startswith("#") or FOOT_LINE.match(para):
            continue
        para = FOOT_MARK.sub("", para)
        if out and not re.search(r"[.!?…:\"“»]$", out[-1]) and para[:1].islower():
            out[-1] += " " + para
        else:
            out.append(para)
    return out


def chunks(paras, lo=LO, hi=HI):
    """Passages of lo to hi words, cut at paragraph ends; a paragraph longer than hi is cut at sentence ends. A tail
    shorter than lo joins the passage before it when that keeps it within hi, and is dropped otherwise."""
    units = []
    for para in paras:
        if n_words(para) <= hi:
            units.append(para)
            continue
        part = []
        for s in SENT.split(para):
            if part and n_words(" ".join(part + [s])) > hi:
                units.append(" ".join(part))
                part = []
            part.append(s)
        if part:
            units.append(" ".join(part))
    out, cur = [], []
    for u in units:
        if cur and n_words(" ".join(cur + [u])) > hi:
            out.append(" ".join(cur))
            cur = []
        cur.append(u)
        if n_words(" ".join(cur)) >= lo:
            out.append(" ".join(cur))
            cur = []
    if cur:
        tail = " ".join(cur)
        if out and n_words(out[-1] + " " + tail) <= hi:
            out[-1] += " " + tail
        elif n_words(tail) >= lo:
            out.append(tail)
    return [p for p in out if n_words(p) >= lo]


def letters(volumes=None):
    """Every section of the two volumes that is a letter: {id, volume, head, by ("hegel" or "other"), year, paragraphs}.
    The journeys and the editor's introductions are left out."""
    out = []
    for name in ("briefe-1", "briefe-2"):
        text = (volumes or {}).get(name) or work(name)
        for n, part in enumerate(re.split(r"^## ", text, flags=re.M)[1:]):
            head, _, body = part.partition("\n")
            head = head.strip()
            if head.startswith("Reise nach"):
                continue
            by = "hegel" if head.startswith("Hegel an") else "other" if " an Hegel" in head else None
            if by is None:
                continue
            years = re.findall(r"\b(1[78]\d\d)\b", head)
            out.append({"id": hashlib.sha256(f"{name}|{n}|{head}".encode()).hexdigest()[:10], "volume": name, "head": head, "by": by,
                        "year": int(years[-1]) if years else None, "paragraphs": paragraphs(body)})
    return out


def split(all_letters):
    """(pool, held, others): his letters by year, every HELD_EVERY-th held out; his correspondents' letters."""
    his = sorted((l for l in all_letters if l["by"] == "hegel"), key=lambda l: (l["year"] or 0, l["id"]))
    held = [l for i, l in enumerate(his) if i % HELD_EVERY == HELD_EVERY - 1]
    ids = {l["id"] for l in held}
    return [l for l in his if l["id"] not in ids], held, [l for l in all_letters if l["by"] == "other"]


def passages_of(letter_list, kind):
    out = []
    for l in letter_list:
        for n, text in enumerate(chunks(l["paragraphs"])):
            out.append({"id": hashlib.sha256(f"{l['id']}|{n}|{text}".encode()).hexdigest()[:10], "letter": l["id"], "head": l["head"],
                        "year": l["year"], "kind": kind, "near": bool(NEAR.search(l["head"])), "words": n_words(text), "text": text})
    return out


def development(volumes=None, names=DEVELOPMENT):
    """The passages of the named journeys (the development journey unless said otherwise), each under the date line or
    heading it falls under."""
    out = []
    for name, text in journeys((volumes or {}).get("briefe-2") or work("briefe-2")).items():
        if name not in names:
            continue
        head = text.splitlines()[0].lstrip("# ").strip()
        dated, group = head, []

        def flush():
            for n, p in enumerate(chunks(group)):
                out.append({"id": hashlib.sha256(f"{name}|{dated}|{n}|{p}".encode()).hexdigest()[:10], "journey": name, "dated": dated,
                            "words": n_words(p), "text": p})
        for para in paragraphs(text):
            if para.lower().startswith("aus hegels briefen"):
                continue
            if n_words(para) < 12 and re.search(r"\d", para):          # a date line: what follows falls under it
                flush()
                dated, group = para, []
            else:
                group.append(para)
        flush()
    return out


def training_journey(volumes=None):
    """The training journey's passages in the pool's form: each date line is a letter to his wife."""
    return [{"id": p["id"], "letter": hashlib.sha256(f"{p['journey']}|{p['dated']}".encode()).hexdigest()[:10],
             "head": f"Hegel an seine Frau, {p['dated'].rstrip('.')}", "year": YEAR[p["journey"]], "kind": "hegel", "near": True,
             "words": p["words"], "text": p["text"]} for p in development(volumes, (TRAINING_JOURNEY,))]


def diaries(volumes=None):
    """His two diaries in the pool's form (`rosenkranz-urkunden`): German paragraphs only, since the schoolboy also wrote
    Latin. Each passage stands for itself. The journey through the Alps is the journeys' kind."""
    text = volumes.get("rosenkranz-urkunden", "") if volumes is not None else work("rosenkranz-urkunden")
    out = []
    for part in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = part.partition("\n")
        head = head.strip()
        if head not in DIARIES:
            continue
        german = [p for p in paragraphs(body) if len(GERMAN.findall(p)) >= 0.08 * n_words(p)]
        for n, chunk in enumerate(chunks(german)):
            pid = hashlib.sha256(f"{head}|{n}|{chunk}".encode()).hexdigest()[:10]
            out.append({"id": pid, "letter": pid, "head": head, "year": None, "kind": "hegel", "near": DIARIES[head],
                        "words": n_words(chunk), "text": chunk})
    return out


def cmd_passages(out, volumes=None):
    out = Path(out)
    pool, held, others = split(letters(volumes))
    rng = random.Random(f"{SEED}|controls")
    hp, op = passages_of(pool + held, "hegel"), passages_of(others, "other")
    controls = sorted(rng.sample(hp, min(CONTROLS, len(hp))) + rng.sample(op, min(CONTROLS, len(op))), key=lambda r: (r["kind"], r["letter"], r["id"]))
    res = {"development": put(out / "PASSAGES.jsonl", development(volumes)),
           "pool": put(out / "POOL.jsonl", passages_of(pool, "hegel") + training_journey(volumes) + diaries(volumes)),
           "controls": put(out / "CONTROLS.jsonl", controls),
           "letters": {"pool": len(pool), "held": len(held), "others": len(others)},
           "passages": {"journey": len(training_journey(volumes)), "diaries": len(diaries(volumes))}}
    (out / "PASSAGES-MANIFEST.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return res


# ── the cards ───────────────────────────────────────────────────────

def lines_of(reply):
    """The '- ' lines of a reply, or [] when it says NONE or holds no such line."""
    if re.fullmatch(r"\W*NONE\W*", (reply or "").strip(), re.I):
        return []
    return [re.sub(r"^\s*[-•*]\s*", "- ", l).rstrip() for l in (reply or "").splitlines() if re.match(r"\s*[-•*]\s+\S", l)]


def cmd_cards(folder):
    folder = Path(folder)
    reqs = [{"id": f"card|{p['id']}", "messages": [{"role": "system", "content": CARD}, {"role": "user", "content": p["text"]}],
             "params": dict(T0, max_tokens=900)} for p in rows(folder / "PASSAGES.jsonl")]
    return put(folder / "REQUESTS-cards.jsonl", reqs)


def state(folder, upto):
    """{passage id: card lines} after the merges of rounds before `upto`."""
    folder = Path(folder)
    if upto == 1:
        got = {r["id"].split("|", 1)[1]: lines_of(r["reply"]) for r in rows(folder / "REPLIES-cards.jsonl")}
        return {k: v for k, v in got.items() if v}
    return {r["id"]: r["lines"] for r in rows(folder / f"CARDS-after-{upto - 1}.jsonl") if r["open"]}


def cmd_check(folder, rnd):
    folder = Path(folder)
    text = {p["id"]: p["text"] for p in rows(folder / "PASSAGES.jsonl")}
    reqs = [{"id": f"check{rnd}|{pid}", "messages": [{"role": "system", "content": CHECK},
                                                     {"role": "user", "content": f"Passage:\n{text[pid]}\n\nLines:\n" + "\n".join(lines)}],
             "params": dict(T0, max_tokens=600)} for pid, lines in sorted(state(folder, rnd).items())]
    return put(folder / f"REQUESTS-check{rnd}.jsonl", reqs)


def cmd_merge(folder, rnd):
    """Round 1: lines the check found are added, and those cards are open for round 2. Round 2: a card that still lacks
    a line is dropped. The final cards are written after round 2 (or after round 1 when none is open)."""
    folder = Path(folder)
    cards = state(folder, rnd)
    missing = {r["id"].split("|", 1)[1]: lines_of(r["reply"]) for r in rows(folder / f"REPLIES-check{rnd}.jsonl")}
    after, dropped = [], []
    for pid, lines in sorted(cards.items()):
        more = missing.get(pid)
        if more is None:
            raise ValueError(f"no check reply for {pid}")
        if more and rnd == 2:
            dropped.append({"id": pid, "lacking": more})
            continue
        after.append({"id": pid, "lines": lines + more, "open": bool(more)})
    put(folder / f"CARDS-after-{rnd}.jsonl", after)
    done = {}
    for r in range(1, rnd + 1):
        done.update({x["id"]: x["lines"] for x in rows(folder / f"CARDS-after-{r}.jsonl") if not x["open"]})
    still = [x["id"] for x in after if x["open"]]
    res = {"round": rnd, "complete": len(done), "open": len(still), "dropped": len(dropped)}
    if not still:
        passages = {p["id"]: p for p in rows(folder / "PASSAGES.jsonl")}
        final = [{**{k: passages[pid][k] for k in ("id", "journey", "dated", "words")}, "card": "\n".join(lines)}
                 for pid, lines in sorted(done.items())]
        res["cards"] = put(folder / "CARDS.jsonl", final)
        no_card = sorted(set(passages) - set(done) - {d["id"] for d in dropped})
        (folder / "DROPPED.json").write_text(json.dumps({"lacking_after_two_rounds": dropped, "no_card": no_card}, ensure_ascii=False,
                                                        indent=1) + "\n", encoding="utf-8")
    return res


# ── the arms ────────────────────────────────────────────────────────

def shown(pool, card_id, arm):
    """The exemplars an arm puts in front, drawn by a seed from the card: passages of different letters."""
    if arm == "P0":
        return []
    rng = random.Random(f"{SEED}|{arm}|{card_id}")
    near, rest = [p for p in pool if p.get("near")], [p for p in pool if not p.get("near")]
    rng.shuffle(near)
    rng.shuffle(rest)
    order = near + rest                                         # the nearest kind first: the rung gets its best chance
    out, seen, words = [], set(), 0
    want = P1_SHOWN if arm == "P1" else P2_SHOWN
    for p in order:
        if p["letter"] in seen or (arm == "P2" and words + p["words"] > P2_WORDS):
            continue
        out.append(p)
        seen.add(p["letter"])
        words += p["words"]
        if len(out) == want:
            break
    return out


def letter_messages(soul, card, exemplars):
    front = ("Letters of yours from other years:\n\n" + "".join(f"[{x['head']}]\n{x['text']}\n\n" for x in exemplars)) if exemplars else ""
    about = max(LO, round(card["words"] / 10) * 10)
    ask = (f"{front}{card['dated'].rstrip('.')}.\n\nThe day's record:\n{card['card']}\n\n"
           f"Write to Marie tonight, as you would, in German, as you wrote in {YEAR[card['journey']]}: about {about} words. {FACTS}"
           "Answer with the letter only.")
    return [{"role": "system", "content": soul}, {"role": "user", "content": ask}]


def translation(rid, text):
    return {"id": rid, "messages": [{"role": "system", "content": TRANSLATE}, {"role": "user", "content": text}],
            "params": dict(T0, max_tokens=1400)}


def cmd_arms(folder, souls=None):
    folder = Path(folder)
    souls = souls or {j: (STAGE2 / f"soul-{y}.md").read_text(encoding="utf-8") for j, y in YEAR.items()}
    pool, text = rows(folder / "POOL.jsonl"), {p["id"]: p["text"] for p in rows(folder / "PASSAGES.jsonl")}
    reqs, plan = [], {}
    for c in rows(folder / "CARDS.jsonl"):
        for arm in ARMS:
            ex = shown(pool, c["id"], arm)
            plan[f"{arm}|{c['id']}"] = [x["id"] for x in ex]
            reqs.append({"id": f"letter|{arm}|{c['id']}", "messages": letter_messages(souls[c["journey"]], c, ex),
                         "params": {"seed": SEED, "temperature": 0.7, "max_tokens": 1100, "cache_prompt": False}})
        reqs.append(translation(f"real|{c['id']}", text[c["id"]]))
    for p in rows(folder / "CONTROLS.jsonl"):
        reqs.append(translation(f"control|{p['kind']}|{p['id']}", p["text"]))
    (folder / "EXEMPLARS.json").write_text(json.dumps(plan, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    return put(folder / "REQUESTS-arms.jsonl", reqs)


def cmd_translate(folder):
    folder = Path(folder)
    reqs = [translation("english|" + r["id"].split("|", 1)[1], r["reply"]) for r in rows(folder / "REPLIES-arms.jsonl")
            if r["id"].startswith("letter|")]
    return put(folder / "REQUESTS-translate.jsonl", reqs)


def english(folder):
    """({card id: the real passage's English}, {arm: {card id: the letter's English}})."""
    folder = Path(folder)
    real = {r["id"].split("|", 1)[1]: r["reply"] for r in rows(folder / "REPLIES-arms.jsonl") if r["id"].startswith("real|")}
    made = {arm: {} for arm in ARMS}
    for r in rows(folder / "REPLIES-translate.jsonl"):
        _, arm, cid = r["id"].split("|")
        made[arm][cid] = r["reply"]
    return real, made


def cmd_sheet(folder, arm, keyout, mirror=False):
    folder = Path(folder)
    real, made = english(folder)
    rng = random.Random(f"{SEED}|sheet|{arm}")
    out, key = [], {}
    for c in rows(folder / "CARDS.jsonl"):
        x_real = (rng.random() < 0.5) != bool(mirror)
        pid = hashlib.sha256(f"{SEED}|{arm}|{c['id']}".encode()).hexdigest()[:8]
        truth, sim = real[c["id"]], made[arm][c["id"]]
        out.append({"pair": pid, "X": truth if x_real else sim, "Y": sim if x_real else truth})
        key[pid] = {"card": c["id"], "real": "X" if x_real else "Y", "arm": arm, "mirror": bool(mirror)}
    random.Random(f"{SEED}|order|{arm}|{bool(mirror)}").shuffle(out)
    name = f"SHEET-{arm}{'-mirror' if mirror else ''}.jsonl"
    res = put(folder / name, out)
    k = json.dumps(key, indent=1, sort_keys=True).encode()
    Path(keyout).mkdir(parents=True, exist_ok=True)
    (Path(keyout) / f"KEY-{arm}{'-mirror' if mirror else ''}.json").write_bytes(k)
    return {"arm": arm, "mirror": bool(mirror), "pairs": res["rows"], "sheet_sha256": res["sha256"], "key_sha256": hashlib.sha256(k).hexdigest()}


# ── invented particulars ────────────────────────────────────────────

def particulars(text):
    """The numbers (figures, and number words as figures) and the names (capitalised words inside a sentence) of an English text."""
    nums = set(NUMBER.findall(text)) | {WORDS_NUM[w] for w in re.findall(r"[a-z]+", text.lower()) if w in WORDS_NUM}
    names = {m.casefold() for m in NAME.findall(text) if m not in COMMON}
    return nums, names


def lacking(text, reference):
    """The particulars of text that reference does not hold: {"numbers": [...], "names": [...]}."""
    nums, names = particulars(text)
    ref_nums, _ = particulars(reference)
    ref = reference.casefold()
    return {"numbers": sorted(nums - ref_nums), "names": sorted(n for n in names if n not in ref)}


def cmd_particulars(folder):
    folder = Path(folder)
    real, made = english(folder)
    out, table = [], {}
    for side, texts in [("real", real)] + [(arm, made[arm]) for arm in ARMS]:
        counts = []
        for c in rows(folder / "CARDS.jsonl"):
            if c["id"] not in texts:
                continue
            lack = lacking(texts[c["id"]], c["card"] + "\n" + c["dated"] + "\nMarie")
            n = len(lack["numbers"]) + len(lack["names"])
            counts.append(n)
            out.append({"side": side, "card": c["id"], "count": n, **lack})
        table[side] = {"letters": len(counts), "per_letter": round(sum(counts) / len(counts), 2) if counts else None,
                       "with_any": sum(1 for n in counts if n)}
    put(folder / "PARTICULARS.jsonl", out)
    (folder / "PARTICULARS.json").write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
    return table


# ── the classifier ──────────────────────────────────────────────────

def wilson(k, n, z=1.96):
    if not n:
        return None
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def delta_accuracy(a, b, top=TOP):
    """Leave-one-out accuracy of Burrows's Delta at telling the texts of a from those of b: each text against the two
    sides' mean profiles without it, over the `top` most frequent words and marks, each scaled by its spread."""
    docs = [TOKEN.findall(x.lower()) for x in a + b]
    side = [0] * len(a) + [1] * len(b)
    if min(len(a), len(b)) < 2:
        return None
    vocab = [w for w, _ in Counter(w for d in docs for w in d).most_common(top)]
    rel = [[Counter(d)[w] / max(1, len(d)) for w in vocab] for d in docs]
    cols = list(zip(*rel))
    mean = [sum(c) / len(c) for c in cols]
    sd = [math.sqrt(sum((x - m) ** 2 for x in c) / len(c)) or 1.0 for c, m in zip(cols, mean)]
    z = [[(x - m) / s for x, m, s in zip(r, mean, sd)] for r in rel]
    right = 0
    for i, zi in enumerate(z):
        dist = []
        for s in (0, 1):
            rest = [z[j] for j in range(len(z)) if j != i and side[j] == s]
            centre = [sum(c) / len(c) for c in zip(*rest)]
            dist.append(sum(abs(x - c) for x, c in zip(zi, centre)) / len(vocab))
        right += (dist[1] < dist[0]) == bool(side[i])
    n = len(docs)
    return {"texts": [len(a), len(b)], "accuracy": round(right / n, 3), "interval": wilson(right, n)}


def bundles(texts, size=BUNDLE):
    """Texts joined in their order into bundles of at least `size` words; a short remainder is left out. Passages of 200
    words are too short for the classifier: on the German originals it tells him from his correspondents 6 times in 10 at
    that length and more than 8 in 10 at 600 words (23 November)."""
    out, cur = [], []
    for x in texts:
        cur.append(x)
        if sum(n_words(c) for c in cur) >= size:
            out.append(" ".join(cur))
            cur = []
    return out


def cmd_classify(folder):
    """Qualification on the controls' English (his held-out letters against his correspondents'), then each arm against the
    real passages. An accuracy near 0.5 means the classifier cannot tell the two sides apart."""
    folder = Path(folder)
    real, made = english(folder)
    ctrl = {"hegel": [], "other": []}
    for r in rows(folder / "REPLIES-arms.jsonl"):
        if r["id"].startswith("control|"):
            ctrl[r["id"].split("|")[1]].append(r["reply"])
    q = delta_accuracy(bundles(ctrl["hegel"]), bundles(ctrl["other"]))
    order = [c["id"] for c in rows(folder / "CARDS.jsonl")]
    side = lambda texts: bundles([texts[i] for i in order if i in texts])
    res = {"bundle_words": BUNDLE, "qualification": q, "qualifies": bool(q and q["accuracy"] >= 0.75 and q["interval"][0] > 0.6),
           "arms": {arm: delta_accuracy(side(real), side(made[arm])) for arm in ARMS if made[arm]}}
    (folder / "CLASSIFIER.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return res


# ── the fixed judge, on what readers have marked ────────────────────

def marked(forty=FORTY, w8=W8):
    """The rewrites readers have marked, [{id, set, source, rewrite, label}]. The label is substantive, minor, clean or
    disputed. The forty: the new rubric's class (E or C is a defect). W8: a defect when both readers mark E or C,
    substantive if either says so (the rule of 20 November); disputed when only one of the two marks a defect."""
    out = []
    labels = {(j["id"], j["arm"]): j for j in rows(forty / "new-rubric/JUDGMENTS-BY-ARM.jsonl")}
    for case in rows(forty / "FORTY-CASES.jsonl"):
        for arm, a in sorted(case["arms"].items()):
            j = labels[(case["id"], arm)]
            label = ("minor" if j["minor"] else "substantive") if j["new_class"] in ("E", "C") else "clean"
            out.append({"id": f"forty|{case['id']}|{arm}", "set": "forty", "source": case["input"], "rewrite": a["output"], "label": label})
    readers = {}
    for name in ("sol", "claude"):
        key = json.loads((w8 / f"key-{name}.json").read_text(encoding="utf-8"))
        packet = {x["id"]: x for x in json.loads((w8 / f"packet-{name}.json").read_text(encoding="utf-8"))}
        for b in rows(w8 / f"ballot-{name}.jsonl"):
            for lab in "ABC":
                k = (key[b["id"]]["case"], key[b["id"]][lab])
                readers.setdefault(k, {})[name] = b[lab]
                readers[k].update(source=packet[b["id"]]["source"], rewrite=packet[b["id"]][lab])
    for (case, version), r in sorted(readers.items()):
        marks = [r[n] for n in ("sol", "claude") if n in r]
        bad = [m for m in marks if m["mark"] in ("E", "C")]
        label = ("clean" if not bad else "disputed" if len(bad) < len(marks) or len(marks) < 2
                 else "substantive" if any(m.get("weight") == "substantive" for m in bad) else "minor")
        out.append({"id": f"w8|{case}|{version}", "set": "w8", "source": r["source"], "rewrite": r["rewrite"], "label": label})
    return out


def cmd_judge(folder, items=None):
    folder = Path(folder)
    items = marked() if items is None else items
    put(folder / "JUDGE-SET.jsonl", [{"id": x["id"], "set": x["set"], "label": x["label"]} for x in items])
    reqs = [{"id": "judge|" + x["id"], "messages": [{"role": "system", "content": JUDGE},
                                                    {"role": "user", "content": f"Source:\n{x['source']}\n\nRewrite:\n{x['rewrite']}"}],
             "params": dict(T0, max_tokens=500)} for x in items]
    return put(folder / "REQUESTS-judge.jsonl", reqs)


def cmd_judge_score(folder):
    folder = Path(folder)
    flagged = {r["id"].split("|", 1)[1]: bool(lines_of(r["reply"])) for r in rows(folder / "REPLIES-judge.jsonl")}
    by = {}
    for x in rows(folder / "JUDGE-SET.jsonl"):
        by.setdefault(x["label"], []).append(flagged[x["id"]])
    rate = lambda k: {"n": len(by.get(k, [])), "flagged": sum(by.get(k, [])),
                      "rate": round(sum(by[k]) / len(by[k]), 3) if by.get(k) else None, "interval": wilson(sum(by.get(k, [])), len(by.get(k, [])))}
    res = {k: rate(k) for k in ("substantive", "minor", "clean", "disputed")}
    res["gates"] = bool(by.get("substantive") and by.get("clean") and res["substantive"]["rate"] >= RECALL and res["clean"]["rate"] <= FALSE_ALARM)
    (folder / "JUDGE-VALIDATION.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("passages").add_argument("--out", required=True)
    for name in ("cards", "arms", "translate", "particulars", "classify", "judge", "judge-score"):
        sub.add_parser(name).add_argument("--folder", required=True)
    for name in ("check", "merge"):
        p = sub.add_parser(name)
        p.add_argument("--folder", required=True)
        p.add_argument("--round", type=int, required=True, choices=(1, 2))
    s = sub.add_parser("sheet")
    s.add_argument("--folder", required=True)
    s.add_argument("--arm", required=True, choices=ARMS)
    s.add_argument("--keyout", required=True)
    s.add_argument("--mirror", action="store_true")
    a = ap.parse_args(argv)
    res = (cmd_passages(a.out) if a.cmd == "passages" else cmd_cards(a.folder) if a.cmd == "cards"
           else cmd_check(a.folder, a.round) if a.cmd == "check" else cmd_merge(a.folder, a.round) if a.cmd == "merge"
           else cmd_arms(a.folder) if a.cmd == "arms" else cmd_translate(a.folder) if a.cmd == "translate"
           else cmd_sheet(a.folder, a.arm, a.keyout, a.mirror) if a.cmd == "sheet" else cmd_particulars(a.folder) if a.cmd == "particulars"
           else cmd_classify(a.folder) if a.cmd == "classify" else cmd_judge(a.folder) if a.cmd == "judge" else cmd_judge_score(a.folder))
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
