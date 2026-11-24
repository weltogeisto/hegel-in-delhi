#!/usr/bin/env python3
"""The ceiling test's judging (pc/CEILING-TEST.md, as amended on 24 November 2026 after the second family's review and
before any arm ran): blind pairs, sealed ballots, and the reads declared before the run.

    python3 tools/ceiling_judge.py sheet --folder F --keys K          # F/SHEET-1.jsonl, F/SHEET-2.jsonl, F/WELT-24.jsonl, F/PACKET.json; K/KEY.json, K/SALT
    python3 tools/ceiling_judge.py parts --folder F --out P            # P/s1-01/ ... P/s2-14/: a sheet cut into parts one reader session can hold
    python3 tools/ceiling_judge.py join  --out P --family NAME         # P/NAME-1.jsonl, P/NAME-2.jsonl: the parts' ballots, checked, in the sheet's order
    python3 tools/ceiling_judge.py seal  --folder F --ballots B...     # F/SEALS.json: the hash of each ballot file, before any key
    python3 tools/ceiling_judge.py score --folder F --keys K --family NAME B... [--family NAME B...] [--welt W]
    python3 tools/ceiling_judge.py counts --folder F                   # for every arm, beside the ballots: words, this century's terms, diary openings

F holds BRIEFS.json, TEXTS.json, the arms' replies (REPLIES-ceiling-1..3.jsonl from the PC, REPLIES-F.jsonl from the cloud)
and, if they were made, CONTROLS.jsonl (the calibration pairs). K is a folder outside the repository.

A pair sets two arms' pieces on one brief side by side as X and Y, with the headline, the text he may have had before him,
and the two passages of his own books that the shelf's search puts nearest (the same for every reader). Every pair is in
both sheets, one way round in each; the two sheets are read in separate sessions, so that no reader sees a pair twice. Row
ids and the way round come from a salt that is kept with the key, so that nothing in the repository tells which arm is which.
A reader must not have the repository: the packet is all a reader gets.

A sheet is too long for one reader session, so it is read in parts of 25 rows, each by a fresh session that is given its
part's folder and nothing else: the rows as plain text, the instructions (PROMPT.md), and a script that checks the form of
its answers. Both families read the same parts under the same instructions. P is a folder outside the repository.

A ballot row:
  {"pair", "q1": "X"|"Y"|"both"|"neither",          which piece argues something about this object that is neither in the
                                                     text nor his doctrine restated; "both" if each does on its own
   "claim": "...", "warrant": "...",                the new claim, quoted from the piece, and what the piece rests it on
                                                     (required unless q1 is "neither")
   "invented": "X"|"Y"|"both"|"neither",            which piece rests a claim on a premise it made up
   "fidelity": "X"|"Y"|"both"|"neither",            which piece keeps the positions he held in 1831
   "stance_X", "stance_Y": "defence"|"revision"|"reversal"|"none"}   a reasoned defence of a position of his, a reasoned
                                                     revision of one, an unsupported reversal, or no position of his at issue

An arm wins a brief against another when a family names it alone on q1 both ways round. A comparison is read against its
bar only with 40 eligible briefs or more; the bar is two thirds of them, rounded up. A brief with a missing piece or a
missing ballot row is not eligible for that comparison. Welt's rows (--welt: {"pair", "q1"}, 24 rows of the first sheet, each
seen one way round) are counted by comparison and stand beside the families; they enter no bar. `score` reads only ballot files whose hashes `seal` wrote down.
Evaluation only; nothing here is training data."""
import argparse
import hashlib
import json
import math
import random
import secrets
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from world import contract, shelf  # noqa: E402
from world.world import wordlist  # noqa: E402
from tools import works_score  # noqa: E402

PAIRS = (("A", "A2"), ("A", "B"), ("A", "C"), ("A", "D"), ("B", "D"), ("C", "D"), ("D", "F"), ("A", "F"))
WELT, ELIGIBLE, BOOKS, BOOK_CHARS, RESAMPLES = 24, 40, 2, 700, 2000
CONTROL_BAR = (6, 8)                    # a family passes the calibration with this many of the controls right, of this many
Q1 = ("Which piece argues something about this object that is neither in the text nor his doctrine restated? X, Y, both (each "
      "does, on its own) or neither. Quote the new claim, say what the piece rests it on, and say which piece, if any, rests a "
      "claim on a premise it made up.")
Q2 = ("Which piece keeps the positions he held in 1831? X, Y, both or neither. And for each piece: a reasoned defence of a "
      "position of his, a reasoned revision of one, an unsupported reversal, or no position of his at issue.")
FOUR, STANCES = ("X", "Y", "both", "neither"), ("defence", "revision", "reversal", "none")
PART = 25                               # rows a reader session reads
PROMPT = """You are a reader in a blind reading test. You are given one file of rows and these instructions, and nothing else.

**Read only your input file.** Do not open, list or search any other file or folder, and nothing on the web. Do not look at any git repository. Do not try to find out how a piece was made. The only other things you may touch are your output file and the check script named below.

Input: `{input}` (plain text, about 1,000 lines; read all of it, in parts if needed). It holds rows, each beginning with a line `################ ROW n ################` and then:
- `pair:` the row's id;
- `HEADLINE:` a newspaper headline of a morning in Delhi in the autumn of 2026;
- `THE TEXT (...)`: the title and the introduction of an encyclopedia article on what the headline concerns. The writer of a piece may or may not have had this text before him;
- `HIS BOOKS:` two passages from G. W. F. Hegel's own books, for your reference;
- `PIECE X` and `PIECE Y`: two pieces about the headline. Each is written in the first person by a simulated Hegel, who died in 1831 and has woken in Delhi in 2026. The two were written under different conditions. You are not told which.

## Two questions for every row

**Question 1.** Which piece argues something about this object that is neither in the text nor his doctrine restated? X, Y, both (each does, on its own) or neither.
- "This object" is what the headline and the text are about.
- "His doctrine" is what Hegel taught up to 1831, as his books have it. A piece that applies a formula of his to the object and concludes nothing more has restated his doctrine.
- If you name a piece, quote the new claim from it, and say in a sentence what the piece rests it on.
- Say which piece, if any, rests a claim on a premise it made up: a fact about the object that is not in the text and that the piece gives no ground for.

**Question 2.** Which piece keeps the positions he held in 1831? X, Y, both or neither. And for each piece, one of:
- `defence`: it defends a position of his, with reasons;
- `revision`: it revises a position of his, with reasons;
- `reversal`: it gives a position of his up, without reasons;
- `none`: no position of his is at issue in it.

A reasoned revision is not a fault. Length is not a merit. "Neither" is a full answer.

Judge each row on its own. Do not carry a judgment from one row to another, and do not go back to change a row after reading a later one.

## What to write

Output: `{output}`: one line for every row, in the file's order, each a JSON object:

`{{"pair": "<the row's id>", "q1": "X" | "Y" | "both" | "neither", "claim": "<the new claim, quoted from the piece; empty if neither>", "warrant": "<what the piece rests it on; empty if neither>", "invented": "X" | "Y" | "both" | "neither", "fidelity": "X" | "Y" | "both" | "neither", "stance_X": "defence" | "revision" | "reversal" | "none", "stance_Y": "defence" | "revision" | "reversal" | "none"}}`

Then run `{check}` and fix the form of any line it names (never your judgment for the sake of the script) until it prints `ALL OK`.

Report back only: the output path and the check's last line. Do not describe the pieces or your judgments."""
CHECK = '''"""Check one reader's ballots: python3 check.py <part>   (e.g. s1-03)"""
import json, sys
from pathlib import Path
here = Path(__file__).resolve().parent
part = sys.argv[1]
want = (here / f"{part}.pairs").read_text().split()
rows = [json.loads(l) for l in (here / f"{part}.out.jsonl").read_text().splitlines() if l.strip()]
FOUR, ST = ("X", "Y", "both", "neither"), ("defence", "revision", "reversal", "none")
errs = []
if [r.get("pair") for r in rows] != want:
    errs.append(f"pair ids differ: {len(rows)} lines for {len(want)} rows, or another order")
for r in rows:
    if r.get("q1") not in FOUR or r.get("invented") not in FOUR or r.get("fidelity") not in FOUR or r.get("stance_X") not in ST or r.get("stance_Y") not in ST:
        errs.append(f"{r.get('pair')}: an answer outside the form")
    elif r["q1"] != "neither" and not (str(r.get("claim") or "").strip() and str(r.get("warrant") or "").strip()):
        errs.append(f"{r.get('pair')}: a piece is named and the claim or its warrant is empty")
print("ALL OK" if not errs else "\\n".join(errs))
'''


def rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def put(path, items):
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items).encode("utf-8")
    Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def piece(reply):
    """The piece of a reply as a reader sees it: its title and its text. None when the reply is not the writing object."""
    w = contract.extract_json(reply or "")
    if not isinstance(w, dict) or not str(w.get("text") or "").strip():
        return None
    title = str(w.get("title") or "").strip()
    return (title + "\n\n" if title else "") + str(w["text"]).strip()


def pieces(folder):
    """{(arm, brief id): piece} from every replies file in the folder."""
    out = {}
    for p in sorted(Path(folder).glob("REPLIES-*.jsonl")):
        for r in rows(p):
            arm, brief = r["id"].split("|", 1)
            got = piece(r.get("reply"))
            if got:
                out[(arm, brief)] = got
    return out


def his_books(brief, text, books):
    """The passages of his own books, in English, that the shelf's search puts nearest to the brief: the same for every reader."""
    if books is None:
        return []
    hits = books.search([(f"{brief.get('object', '')} {text['title']} {brief['headline']}", 1.0)], n=40)
    return [{"from": h["label"], "text": h["text"][:BOOK_CHARS]} for h in hits if h["lang"] == "en"][:BOOKS]


def cmd_sheet(folder, keys, books="load"):
    folder, keys = Path(folder), Path(keys)
    keys.mkdir(parents=True, exist_ok=True)
    salt_file = keys / "SALT"
    if not salt_file.exists():
        salt_file.write_text(secrets.token_hex(16), encoding="utf-8")
    salt = salt_file.read_text(encoding="utf-8").strip()
    briefs = {b["id"]: b for b in json.loads((folder / "BRIEFS.json").read_text(encoding="utf-8"))}
    texts = json.loads((folder / "TEXTS.json").read_text(encoding="utf-8"))
    books = shelf.load() if books == "load" else books
    have = pieces(folder)
    controls = rows(folder / "CONTROLS.jsonl") if (folder / "CONTROLS.jsonl").exists() else []
    sheets, key, lacking = ([], []), {}, []

    def add(bid, first, second, one, two, extra):
        """One comparison, into both sheets, opposite ways round; which way goes into the first sheet is the salt's draw."""
        flip = random.Random(f"{salt}|way|{bid}|{first}|{second}").random() < 0.5
        shown = {"headline": briefs[bid]["headline"], "about": texts[bid]["title"], "text": texts[bid]["text"],
                 "his_books": his_books(briefs[bid], texts[bid], books)}
        for n in (0, 1):
            x_first = (n == 0) != flip
            pid = hashlib.sha256(f"{salt}|{bid}|{first}|{second}|{n}".encode()).hexdigest()[:12]
            sheets[n].append({"pair": pid, **shown, "X": one if x_first else two, "Y": two if x_first else one})
            key[pid] = {"brief": bid, "first": first, "second": second, "sheet": n + 1,
                        "X": first if x_first else second, "Y": second if x_first else first, **extra}

    for bid in sorted(texts):
        for first, second in PAIRS:
            if (first, bid) not in have or (second, bid) not in have:
                lacking.append(f"{first}-{second}|{bid}")
                continue
            add(bid, first, second, have[(first, bid)], have[(second, bid)], {})
    for c in controls:
        add(c["brief"], "good", "bad", c["good"], c["bad"], {"control": c["type"], "id": c["id"]})
    for n in (0, 1):
        random.Random(f"{salt}|order|{n}").shuffle(sheets[n])
    res = {"rows_a_sheet": len(sheets[0]), "pairs_lacking_a_piece": lacking, "controls": len(controls),
           "sha256": {"SHEET-1.jsonl": put(folder / "SHEET-1.jsonl", sheets[0]), "SHEET-2.jsonl": put(folder / "SHEET-2.jsonl", sheets[1])}}
    by = {}
    for r in sheets[0]:
        k = key[r["pair"]]
        if "control" not in k:
            by.setdefault((k["first"], k["second"]), []).append(r)
    rnd, welt = random.Random(f"{salt}|welt"), []
    for pair in PAIRS:
        got = by.get(pair, [])
        welt += rnd.sample(got, min(len(got), WELT // len(PAIRS)))
    rnd.shuffle(welt)
    res["welt_rows"] = len(welt)
    res["sha256"]["WELT-24.jsonl"] = put(folder / "WELT-24.jsonl", welt)
    data = json.dumps(key, indent=1, sort_keys=True).encode()
    (keys / "KEY.json").write_bytes(data)
    res["sha256"]["KEY.json"] = hashlib.sha256(data).hexdigest()
    (folder / "PACKET.json").write_text(json.dumps({"questions": [Q1, Q2], **res}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return res


def row_text(r, n):
    """One row as a reader sees it."""
    books = "\n\n".join(f"From {b['from']}:\n{b['text']}" for b in r["his_books"])
    return (f"################ ROW {n} ################\npair: {r['pair']}\n\nHEADLINE: {r['headline']}\n\nTHE TEXT ({r['about']}):\n{r['text']}\n\n"
            f"HIS BOOKS:\n{books}\n\n======== PIECE X ========\n{r['X']}\n\n======== PIECE Y ========\n{r['Y']}\n\n")


def sheet_file(folder, n):
    """A sheet as the packet holds it, checked against the hash that was committed before any reading."""
    folder = Path(folder)
    path = next(p for p in (folder / "packet" / f"session-{n}" / "SHEET.jsonl", folder / f"SHEET-{n}.jsonl") if p.exists())
    want = json.loads((folder / "PACKET.json").read_text(encoding="utf-8"))["sha256"][f"SHEET-{n}.jsonl"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != want:
        raise ValueError(f"{path} is not the sheet whose hash PACKET.json holds")
    return rows(path)


def cmd_parts(folder, out, size=PART):
    """Cut both sheets into parts, a folder a part: all that one reader session gets."""
    out, res = Path(out), {}
    for n in (1, 2):
        sheet = sheet_file(folder, n)
        for c in range(0, len(sheet), size):
            name = f"s{n}-{c // size + 1:02d}"
            d = out / name
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{name}.txt").write_text("".join(row_text(r, i + 1) for i, r in enumerate(sheet[c:c + size])), encoding="utf-8")
            (d / f"{name}.pairs").write_text("\n".join(r["pair"] for r in sheet[c:c + size]) + "\n", encoding="utf-8")
            (d / "check.py").write_text(CHECK, encoding="utf-8")
            (d / "PROMPT.md").write_text(PROMPT.format(input=f"{name}.txt", output=f"{name}.out.jsonl", check=f"python3 check.py {name}") + "\n", encoding="utf-8")
            res[name] = len(sheet[c:c + size])
    return res


def cmd_join(out, family):
    """The parts' ballots as one file a sheet, in the sheet's order. A part that is missing, out of order or outside the form stops it."""
    out, res = Path(out), {}
    for n in (1, 2):
        got = []
        for d in sorted(p for p in out.iterdir() if p.is_dir() and p.name.startswith(f"s{n}-")):
            want = (d / f"{d.name}.pairs").read_text(encoding="utf-8").split()
            file = d / f"{d.name}.out.jsonl"
            part = rows(file) if file.exists() else []
            if [a.get("pair") for a in part] != want:
                raise ValueError(f"{d.name}: its ballots are missing, or are not its rows in their order")
            for a in part:
                check(a, d.name)
            got += part
        res[f"{family}-{n}.jsonl"] = {"rows": len(got), "sha256": put(out / f"{family}-{n}.jsonl", got)}
    return res


def cmd_counts(folder, rx=None):
    """For every arm, counted and not judged: its pieces, their words, the names and terms of this century in them (and those
    that neither the headline nor the text gave it), and how many open like a diary entry."""
    folder = Path(folder)
    rx = rx or wordlist("after_1831.txt", "s?")
    briefs = {b["id"]: b for b in json.loads((folder / "BRIEFS.json").read_text(encoding="utf-8"))}
    texts = json.loads((folder / "TEXTS.json").read_text(encoding="utf-8"))
    got = {}
    for (arm, bid), text in sorted(pieces(folder).items()):
        if bid not in texts:
            continue
        shown = {t.lower() for t in works_score.century_terms(f"{briefs[bid]['headline']} {texts[bid]['title']} {texts[bid]['text']}", rx)}
        terms = works_score.century_terms(text, rx)
        got.setdefault(arm, []).append({"words": len(text.split()), "terms": len(terms), "own": sum(t.lower() not in shown for t in terms),
                                        "dated": works_score.opens_dated(text)})
    out = {}
    for arm, ps in got.items():
        n = len(ps)
        out[arm] = {"pieces": n, "words_mean": round(sum(p["words"] for p in ps) / n), "century_terms_mean": round(sum(p["terms"] for p in ps) / n, 2),
                    "century_terms_not_shown_mean": round(sum(p["own"] for p in ps) / n, 2),
                    "pieces_with_a_term_not_shown": sum(p["own"] > 0 for p in ps), "opens_like_a_diary": sum(p["dated"] for p in ps)}
    return out


def cmd_seal(folder, ballots):
    """Write down each ballot file by its hash. Done before any key is opened; `score` reads nothing else."""
    folder = Path(folder)
    path = folder / "SEALS.json"
    seals = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for j in ballots:
        name, h = Path(j).name, hashlib.sha256(Path(j).read_bytes()).hexdigest()
        if seals.get(name, h) != h:
            raise ValueError(f"{name} was sealed with another hash: a sealed ballot is not changed")
        seals[name] = h
    path.write_text(json.dumps(seals, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return seals


def check(a, name):
    ok = (a.get("q1") in FOUR and a.get("invented") in FOUR and a.get("fidelity") in FOUR
          and a.get("stance_X") in STANCES and a.get("stance_Y") in STANCES
          and (a["q1"] == "neither" or (str(a.get("claim") or "").strip() and str(a.get("warrant") or "").strip())))
    if not ok:
        raise ValueError(f"{name}: a ballot row outside the form: {a.get('pair')}")


def named(k, answer):
    """The arms a q1-like answer names: a set of zero, one or two."""
    return {k["X"], k["Y"]} if answer == "both" else {k[answer]} if answer in ("X", "Y") else set()


def outcomes(key, ballots):
    """{(brief, first, second): "first"|"second"|"both"|"neither"|"reversal"|"mixed"} for the comparisons judged both ways round."""
    seen = {}
    for pid, k in key.items():
        if pid in ballots:
            seen.setdefault((k["brief"], k["first"], k["second"]), []).append(named(k, ballots[pid]["q1"]))
    out = {}
    for (brief, first, second), v in seen.items():
        if len(v) != 2:
            continue                                              # one way round is missing: not eligible
        a, b = v
        out[(brief, first, second)] = ("first" if a == b == {first} else "second" if a == b == {second} else
                                       "both" if a == b == {first, second} else "neither" if not a and not b else
                                       "reversal" if {frozenset(a), frozenset(b)} == {frozenset({first}), frozenset({second})} else "mixed")
    return out


def interval(wins, mornings, seed="ceiling"):
    """A 95% interval for a share of wins, resampling mornings: 13 mornings give two briefs, and they are not independent."""
    groups = {}
    for won, m in zip(wins, mornings):
        groups.setdefault(m, []).append(won)
    g = list(groups.values())
    if not g:
        return None
    rnd, shares = random.Random(seed), []
    for _ in range(RESAMPLES):
        pick = [x for _ in g for x in rnd.choice(g)]
        shares.append(sum(pick) / len(pick))
    shares.sort()
    return [round(shares[int(0.025 * RESAMPLES)], 3), round(shares[int(0.975 * RESAMPLES) - 1], 3)]


def tally(key, ballots, dates):
    out = {}
    got = outcomes({p: k for p, k in key.items() if "control" not in k}, ballots)
    for a, b in PAIRS:
        mine = {c: o for c, o in got.items() if (c[1], c[2]) == (a, b)}
        n = len(mine)
        t = {"eligible": n, "first": 0, "second": 0, "both": 0, "neither": 0, "reversal": 0, "mixed": 0,
             "bar": math.ceil(2 * n / 3) if n >= ELIGIBLE else None}
        for o in mine.values():
            t[o] += 1
        t["second_share_95"] = interval([o == "second" for o in mine.values()], [dates[c[0]] for c in mine], f"{a}|{b}")
        out[f"{a}-{b}"] = t
    return out


def by_arm(key, ballots):
    """For each arm: how often it was shown, named as keeping his positions, named as inventing a premise, and its stances."""
    out = {}
    for pid, k in key.items():
        a = ballots.get(pid)
        if a is None or "control" in k:
            continue
        for side in ("X", "Y"):
            t = out.setdefault(k[side], {"shown": 0, "kept_1831": 0, "invented": 0, **{s: 0 for s in STANCES}})
            t["shown"] += 1
            t["kept_1831"] += a["fidelity"] in (side, "both")
            t["invented"] += a["invented"] in (side, "both")
            t[a[f"stance_{side}"]] += 1
    return out


def calibration(key, ballots):
    """The controls: right when the good piece alone is named on q1 both ways round; for an invention, also whether the
    made-up premise was flagged both ways round."""
    ctl = {p: k for p, k in key.items() if "control" in k}
    got = outcomes(ctl, ballots)
    flagged = {}
    for pid, k in ctl.items():
        if pid in ballots and k["control"] == "invention":
            flagged.setdefault(k["id"], []).append("bad" in named(k, ballots[pid]["invented"]))
    n = len({k["id"] for k in ctl.values()})
    right = sum(o == "first" for o in got.values())               # "first" is the good piece
    return {"controls": n, "judged": len(got), "right": right, "inventions_flagged": sum(len(v) == 2 and all(v) for v in flagged.values()),
            "passed": None if not n else (len(got) == n and right * CONTROL_BAR[1] >= CONTROL_BAR[0] * n)}


def reads(t):
    """The declared reads for one family. None where a comparison has fewer than ELIGIBLE briefs: nothing is declared there."""
    band = max(t["A-A2"]["second"], t["A-A2"]["first"])

    def over(pair, outside=True):
        bar = t[pair]["bar"]
        return None if bar is None else t[pair]["second"] >= bar and (not outside or t[pair]["second"] > band)

    return {"band": {"A2_over_A": t["A-A2"]["second"], "A_over_A2": t["A-A2"]["first"], "taken": band},
            "bundle_lifts_him": over("A-D"), "text_lifts_him": over("A-B"), "fuller_and_thinking_lift_him": over("A-C"),
            "text_helps_under_fuller": over("C-D"), "fuller_helps_with_text": over("B-D"),
            "cloud_over_his_best": over("D-F", outside=False), "cloud_over_his_live": over("A-F", outside=False)}


def statements(families):
    """What may be said, over all families whose calibration did not fail. Each line is as narrow as the test."""
    used = {n: f for n, f in families.items() if f["calibration"]["passed"] is not False}
    out = [f"{n} failed the calibration pairs: its ballots are shown and not used. The measure is in question for that family."
           for n, f in families.items() if f["calibration"]["passed"] is False]
    if not used:
        return out + ["No family passed the calibration: nothing is read from these ballots."]

    def all_say(key, want=True):
        return all(f["reads"][key] is want for f in used.values())

    def split(key):
        return len({f["reads"][key] for f in used.values()}) > 1

    for key, yes, no in (
            ("bundle_lifts_him", "With the text, the fuller instructions and time to think together, he wins outside the band: this bundle lifts what he writes on an assigned headline.",
             "The bundle does not win outside the band."),
            ("text_lifts_him", "A short Wikipedia introduction, assigned to him, lifts what he writes.",
             "A short, assigned Wikipedia introduction does not lift what he writes. This says nothing of a text he sought out, or of a longer one."),
            ("fuller_and_thinking_lift_him", "The fuller instructions with time to think lift what he writes. The two were changed together and cannot be told apart here.",
             "The fuller instructions with time to think do not lift what he writes."),
            ("text_helps_under_fuller", "Under the fuller instructions the text still helps.", "Under the fuller instructions the text does not help further."),
            ("fuller_helps_with_text", "With the text before him the fuller instructions still help.", "With the text before him the fuller instructions do not help further."),
            ("cloud_over_his_best", "The cloud model, as it was configured, beats his best arm on these briefs.", "The cloud model does not beat his best arm by the bar."),
            ("cloud_over_his_live", "The cloud model, as it was configured, beats his live call on these briefs.",
             "The cloud model does not beat his live call by the bar: the cause is unresolved, and the measure is in question.")):
        out.append(f"The families disagree on this, so it is unresolved: {yes}" if split(key) else yes if all_say(key) else
                   no if all_say(key, False) else f"Not declared (fewer than {ELIGIBLE} eligible briefs): {yes}")
    return out


def welt_tally(key, ballots):
    """Welt's own rows: for each comparison, how often he named the first arm, the second, both or neither. One way round."""
    out = {f"{a}-{b}": {"read": 0, "first": 0, "second": 0, "both": 0, "neither": 0} for a, b in PAIRS}
    for pid, a in ballots.items():
        k = key[pid]
        got = named(k, a["q1"])
        t = out[f"{k['first']}-{k['second']}"]
        t["read"] += 1
        t["both" if len(got) == 2 else "neither" if not got else "first" if got == {k["first"]} else "second"] += 1
    return out


def cmd_score(folder, keys, families, welt=None):
    folder = Path(folder)
    key = json.loads((Path(keys) / "KEY.json").read_text(encoding="utf-8"))
    dates = {b["id"]: b["date"] for b in json.loads((folder / "BRIEFS.json").read_text(encoding="utf-8"))}
    seals = json.loads((folder / "SEALS.json").read_text(encoding="utf-8")) if (folder / "SEALS.json").exists() else {}
    out, got = {}, {}
    for name, files in families.items():
        ballots = {}
        for j in files:
            fname = Path(j).name
            if seals.get(fname) != hashlib.sha256(Path(j).read_bytes()).hexdigest():
                raise ValueError(f"{fname} is not sealed, or was changed after its seal")
            for a in rows(j):
                if a.get("pair") not in key or a["pair"] in ballots:
                    raise ValueError(f"{fname}: a ballot row for an unknown pair, or for one already judged: {a.get('pair')}")
                check(a, fname)
                ballots[a["pair"]] = a
        t = tally(key, ballots, dates)
        out[name] = {"judged": len(ballots), "of": len(key), "tally": t, "arms": by_arm(key, ballots),
                     "calibration": calibration(key, ballots), "reads": reads(t)}
        got[name] = outcomes({p: k for p, k in key.items() if "control" not in k}, ballots)
    names, agree = sorted(got), {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            both = set(got[a]) & set(got[b])
            agree[f"{a} / {b}"] = {"compared": len(both), "same": sum(got[a][c] == got[b][c] for c in both)}
    res = {"families": out, "agreement": agree, "statements": statements(out)}
    if welt:
        wname = Path(welt).name
        if seals.get(wname) != hashlib.sha256(Path(welt).read_bytes()).hexdigest():
            raise ValueError(f"{wname} is not sealed, or was changed after its seal")
        mine = {a["pair"]: a for a in rows(welt)}
        if any(p not in key or "control" in key[p] or a.get("q1") not in FOUR for p, a in mine.items()):
            raise ValueError(f"{wname}: a row for an unknown pair, or an answer outside the form")
        res["welt"] = welt_tally(key, mine)
    (folder / "RESULT.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (folder / "RESULT.md").write_text(render(res), encoding="utf-8")
    return res


def render(res):
    out = ["# The ceiling test: the ballots", "", "What may be said, by the reads declared before the run:", ""] + [f"- {s}" for s in res["statements"]] + [""]
    for name, f in sorted(res["families"].items()):
        c, b = f["calibration"], f["reads"]["band"]
        out += [f"## {name}", "", f"{f['judged']} of {f['of']} rows judged. The band: A2 over A in {b['A2_over_A']} briefs, A over A2 in {b['A_over_A2']}; the larger is taken.",
                "Calibration: " + ("no controls were made." if not c["controls"] else
                                   f"{c['right']} of {c['controls']} controls right, {c['inventions_flagged']} inventions flagged: {'passed' if c['passed'] else 'failed'}."), "",
                "| Pair | Eligible | First | Second | Both | Neither | Reversed | Mixed | Bar | Second's share, 95% |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for a, bb in PAIRS:
            t = f["tally"][f"{a}-{bb}"]
            iv = t["second_share_95"]
            out.append(f"| {a} and {bb} | {t['eligible']} | {t['first']} | {t['second']} | {t['both']} | {t['neither']} | {t['reversal']} | {t['mixed']} | "
                       f"{t['bar'] if t['bar'] is not None else '–'} | {f'{iv[0]:.2f} to {iv[1]:.2f}' if iv else '–'} |")
        out += ["", "| Arm | Shown | Kept 1831 | Defence | Revision | Reversal | No position | Invented a premise |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        out += [f"| {arm} | {t['shown']} | {t['kept_1831']} | {t['defence']} | {t['revision']} | {t['reversal']} | {t['none']} | {t['invented']} |"
                for arm, t in sorted(f["arms"].items())] + [""]
    if res.get("welt"):
        out += ["## Welt's rows", "", "Each seen once, one way round. They stand beside the families and enter no bar.", "",
                "| Pair | Read | First | Second | Both | Neither |", "|---|---:|---:|---:|---:|---:|"]
        out += [f"| {a} and {b} | {t['read']} | {t['first']} | {t['second']} | {t['both']} | {t['neither']} |"
                for a, b in PAIRS for t in [res["welt"][f"{a}-{b}"]]] + [""]
    if res["agreement"]:
        out += ["## Between families", ""] + [f"- {k}: the same outcome in {v['same']} of {v['compared']} comparisons." for k, v in res["agreement"].items()] + [""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("--folder", required=True)
    s.add_argument("--keys", required=True)
    p = sub.add_parser("parts")
    p.add_argument("--folder", required=True)
    p.add_argument("--out", required=True)
    j = sub.add_parser("join")
    j.add_argument("--out", required=True)
    j.add_argument("--family", required=True)
    e = sub.add_parser("seal")
    e.add_argument("--folder", required=True)
    e.add_argument("--ballots", nargs="+", required=True)
    n = sub.add_parser("counts")
    n.add_argument("--folder", required=True)
    c = sub.add_parser("score")
    c.add_argument("--folder", required=True)
    c.add_argument("--keys", required=True)
    c.add_argument("--family", nargs="+", action="append", required=True, metavar=("NAME", "BALLOTS"))
    c.add_argument("--welt", help="Welt's own rows: {pair, q1} for the 24 rows of WELT-24.jsonl")
    a = ap.parse_args(argv)
    if a.cmd == "sheet":
        res = cmd_sheet(a.folder, a.keys)
    elif a.cmd == "parts":
        res = cmd_parts(a.folder, a.out)
    elif a.cmd == "join":
        res = cmd_join(a.out, a.family)
    elif a.cmd == "counts":
        res = cmd_counts(a.folder)
    elif a.cmd == "seal":
        res = cmd_seal(a.folder, a.ballots)
    else:
        res = cmd_score(a.folder, a.keys, {f[0]: f[1:] for f in a.family}, a.welt)
        res = {"statements": res["statements"], "agreement": res["agreement"]}
    print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
