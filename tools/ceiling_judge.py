#!/usr/bin/env python3
"""The ceiling test's judging (pc/CEILING-TEST.md): blind pairs, sealed judgments, and the reads declared before the run.

    python3 tools/ceiling_judge.py sheet --folder F --keys K          # F/SHEET.jsonl, F/WELT-24.jsonl; K/KEY.json (outside the repository)
    python3 tools/ceiling_judge.py seal  --folder F --judgments J...   # F/SEALS.json: the hash of each reader's file, before any key
    python3 tools/ceiling_judge.py score --folder F --keys K --judgments J...   # F/RESULT.json and F/RESULT.md

F holds BRIEFS.json, TEXTS.json, the arms' replies (REPLIES-ceiling-1..3.jsonl from the PC, REPLIES-F.jsonl from the cloud).

A pair sets two arms' pieces on one brief side by side as X and Y, with the headline and the text he may have had before him.
Every pair is in the sheet twice, the second time the other way round. A reader answers, for each row,
{"pair", "q1": "X" | "Y" | "neither", "q2": "X" | "Y" | "both" | "neither"}:
  q1  Which piece argues something about this object that is neither in the text nor his doctrine restated?
  q2  Which piece keeps the positions he held in 1831?
An arm wins a brief against another when the reader names it on q1 both ways round; anything else is no win. `score` reads
only files whose hashes `seal` wrote down, so that no judgment is changed after a key is opened.

The reads (declared in pc/CEILING-TEST.md): of the n briefs a comparison has, an arm is "outside the band" with two thirds of
them or more (32 of 48) and more wins than A2 has over A. Evaluation only; nothing here is training data."""
import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from world import contract  # noqa: E402

PAIRS = (("A", "A2"), ("A", "B"), ("A", "C"), ("A", "D"), ("D", "F"), ("A", "F"))
SEED = 1831
WELT = 24
Q1 = "Which piece argues something about this object that is neither in the text nor his doctrine restated? X, Y or neither."
Q2 = "Which piece keeps the positions he held in 1831? X, Y, both or neither."
ANSWERS = {"q1": ("X", "Y", "neither"), "q2": ("X", "Y", "both", "neither")}


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


def cmd_sheet(folder, keys, seed=SEED):
    folder, keys = Path(folder), Path(keys)
    briefs = {b["id"]: b for b in json.loads((folder / "BRIEFS.json").read_text(encoding="utf-8"))}
    texts = json.loads((folder / "TEXTS.json").read_text(encoding="utf-8"))
    have = pieces(folder)
    sheet, key, lacking = [], {}, []
    for bid in sorted(texts):
        for first, second in PAIRS:
            if (first, bid) not in have or (second, bid) not in have:
                lacking.append(f"{first}-{second}|{bid}")
                continue
            for way in (0, 1):
                x, y = (first, second) if way == 0 else (second, first)
                pid = hashlib.sha256(f"{seed}|{bid}|{first}|{second}|{way}".encode()).hexdigest()[:10]
                sheet.append({"pair": pid, "headline": briefs[bid]["headline"], "about": texts[bid]["title"], "text": texts[bid]["text"],
                              "X": have[(x, bid)], "Y": have[(y, bid)]})
                key[pid] = {"brief": bid, "first": first, "second": second, "X": x, "Y": y}
    random.Random(seed).shuffle(sheet)
    res = {"rows": len(sheet), "pairs_lacking_a_piece": lacking, "sheet_sha256": put(folder / "SHEET.jsonl", sheet)}
    by = {}
    for r in sheet:
        k = key[r["pair"]]
        if k["X"] == k["first"]:                                  # one way round only for Welt's reading
            by.setdefault((k["first"], k["second"]), []).append(r)
    rnd, welt = random.Random(f"{seed}|welt"), []
    for pair in PAIRS:
        got = by.get(pair, [])
        welt += rnd.sample(got, min(len(got), WELT // len(PAIRS)))
    rnd.shuffle(welt)
    res["welt_rows"], res["welt_sha256"] = len(welt), put(folder / "WELT-24.jsonl", welt)
    keys.mkdir(parents=True, exist_ok=True)
    data = json.dumps(key, indent=1, sort_keys=True).encode()
    (keys / "KEY.json").write_bytes(data)
    res["key_sha256"] = hashlib.sha256(data).hexdigest()
    return res


def cmd_seal(folder, judgments):
    """Write down each reader's file by its hash. Done before any key is opened; `score` reads nothing else."""
    folder = Path(folder)
    path = folder / "SEALS.json"
    seals = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for j in judgments:
        name, h = Path(j).name, hashlib.sha256(Path(j).read_bytes()).hexdigest()
        if seals.get(name, h) != h:
            raise ValueError(f"{name} was sealed with another hash: a sealed judgment is not changed")
        seals[name] = h
    path.write_text(json.dumps(seals, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return seals


def outcome(key, answers):
    """{(brief, first, second): the arm that won q1 both ways round, or None} for one reader."""
    named = {}
    for pid, k in key.items():
        a = answers.get(pid)
        if a is None:
            continue
        named.setdefault((k["brief"], k["first"], k["second"]), []).append(k.get(a["q1"]))      # "neither" names nobody
    return {c: (v[0] if len(v) == 2 and v[0] and v[0] == v[1] else None) for c, v in named.items() if len(v) == 2}


def tally(key, answers):
    """Per comparison: the briefs judged both ways round, the wins of each arm, and on q2 how often each arm was named."""
    out = {f"{a}-{b}": {"briefs": 0, a: 0, b: 0, "none": 0} for a, b in PAIRS}
    for (brief, a, b), won in outcome(key, answers).items():
        t = out[f"{a}-{b}"]
        t["briefs"] += 1
        t[won or "none"] += 1
    kept = {}
    for pid, k in key.items():
        a = answers.get(pid)
        if a is None:
            continue
        for side in ("X", "Y"):
            k2 = kept.setdefault(k[side], {"shown": 0, "named": 0})
            k2["shown"] += 1
            k2["named"] += a["q2"] in (side, "both")
    return out, kept


def reads(t):
    """The declared reads for one reader's tally."""
    def outside(pair, arm):
        n = t[pair]["briefs"]
        return n > 0 and t[pair][arm] >= math.ceil(2 * n / 3) and t[pair][arm] > band
    band = t["A-A2"]["A2"]
    need = lambda pair: math.ceil(2 * t[pair]["briefs"] / 3) if t[pair]["briefs"] else None
    return {"band_A2_over_A": band, "A_over_A2": t["A-A2"]["A"],
            "needed": {p: need(p) for p in t},
            "D_over_A_outside_the_band": outside("A-D", "D"),
            "B_over_A_outside_the_band": outside("A-B", "B"),
            "C_over_A_outside_the_band": outside("A-C", "C"),
            "F_over_D_two_thirds": t["D-F"]["briefs"] > 0 and t["D-F"]["F"] >= need("D-F"),
            "F_over_A_two_thirds": t["A-F"]["briefs"] > 0 and t["A-F"]["F"] >= need("A-F")}


def verdict(per_reader):
    """One line from the declared table, over all readers."""
    r = list(per_reader.values())
    if not r:
        return "no reader"
    if not all(x["F_over_A_two_thirds"] for x in r) or len({x["D_over_A_outside_the_band"] for x in r}) > 1:
        return "The measure is the ceiling: a stronger model's piece does not win two thirds over his, or the readers disagree."
    if all(x["D_over_A_outside_the_band"] for x in r):
        return "The pipeline is the ceiling: with the text, the fuller instructions and time to think he wins outside the band."
    if all(x["F_over_D_two_thirds"] for x in r):
        return "The 27B is the ceiling: his best arm stays inside the band, and the stronger model wins two thirds over it."
    return "No declared read holds: his best arm is inside the band, and the stronger model does not win two thirds over it."


def cmd_score(folder, keys, judgments):
    folder = Path(folder)
    key = json.loads((Path(keys) / "KEY.json").read_text(encoding="utf-8"))
    seals = json.loads((folder / "SEALS.json").read_text(encoding="utf-8")) if (folder / "SEALS.json").exists() else {}
    readers, outcomes = {}, {}
    for j in judgments:
        name = Path(j).name
        if seals.get(name) != hashlib.sha256(Path(j).read_bytes()).hexdigest():
            raise ValueError(f"{name} is not sealed, or was changed after its seal")
        answers = {}
        for a in rows(j):
            if a.get("pair") not in key or a.get("q1") not in ANSWERS["q1"] or a.get("q2") not in ANSWERS["q2"]:
                raise ValueError(f"{name}: a judgment of an unknown pair or with an answer outside the form: {a.get('pair')}")
            answers[a["pair"]] = a
        t, kept = tally(key, answers)
        readers[name] = {"judged": len(answers), "of": len(key), "tally": t, "kept_1831": kept, "reads": reads(t)}
        outcomes[name] = outcome(key, answers)
    names = sorted(outcomes)
    agree = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            both = set(outcomes[a]) & set(outcomes[b])
            agree[f"{a} / {b}"] = {"compared": len(both), "same": sum(outcomes[a][c] == outcomes[b][c] for c in both)}
    res = {"readers": readers, "agreement": agree, "verdict": verdict({n: r["reads"] for n, r in readers.items()}),
           "B_against_A": {n: r["reads"]["B_over_A_outside_the_band"] for n, r in readers.items()}}
    (folder / "RESULT.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (folder / "RESULT.md").write_text(render(res), encoding="utf-8")
    return res


def render(res):
    out = ["# The ceiling test: the judgments", "", res["verdict"], ""]
    for name, r in sorted(res["readers"].items()):
        out += [f"## {name}", "", f"{r['judged']} of {r['of']} rows judged. The band: A2 over A in {r['reads']['band_A2_over_A']} briefs, A over A2 in {r['reads']['A_over_A2']}.", "",
                "| Pair | Briefs | First wins | Second wins | No win | Needed |", "|---|---:|---:|---:|---:|---:|"]
        for a, b in PAIRS:
            t = r["tally"][f"{a}-{b}"]
            out.append(f"| {a} and {b} | {t['briefs']} | {t[a]} | {t[b]} | {t['none']} | {r['reads']['needed'][f'{a}-{b}']} |")
        out += ["", "Kept his positions of 1831, by arm: " + "; ".join(f"{arm} {k['named']} of {k['shown']}" for arm, k in sorted(r["kept_1831"].items())) + ".", ""]
    if res["agreement"]:
        out += ["## Between readers", ""] + [f"- {k}: the same outcome in {v['same']} of {v['compared']} comparisons." for k, v in res["agreement"].items()] + [""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet")
    s.add_argument("--folder", required=True)
    s.add_argument("--keys", required=True)
    s.add_argument("--seed", type=int, default=SEED)
    e = sub.add_parser("seal")
    e.add_argument("--folder", required=True)
    e.add_argument("--judgments", nargs="+", required=True)
    c = sub.add_parser("score")
    c.add_argument("--folder", required=True)
    c.add_argument("--keys", required=True)
    c.add_argument("--judgments", nargs="+", required=True)
    a = ap.parse_args(argv)
    res = cmd_sheet(a.folder, a.keys, a.seed) if a.cmd == "sheet" else cmd_seal(a.folder, a.judgments) if a.cmd == "seal" \
        else cmd_score(a.folder, a.keys, a.judgments)
    print(json.dumps({k: v for k, v in res.items() if k != "readers"} if a.cmd == "score" else res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
