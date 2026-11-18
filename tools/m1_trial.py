"""M1's trial on shadow, read (pc/M1-TRIAL-READING.md): the days on mind/soul.md against the days on
mind/soul-ordinary.md, by machine counts and by a blind topic profile with stage 1's codebook (tools/paris_profile.py).

    python3 tools/m1_trial.py freeze --ref <shadow sha> --out <folder> --keyout <path outside the repo>
    python3 tools/m1_trial.py counts --ref <shadow sha> --out <folder>
    python3 tools/m1_trial.py report --folder <folder> --key <key path> --codes A.jsonl B.jsonl

Evaluation only: no sentence, code or result here is ever training data."""
import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from paris_profile import CODEBOOK, CODES, INSTRUCTION, distance, kappa, parse, shares, split, usable  # noqa: E402
from prompt_screen import DOCTRINE  # noqa: E402
from world.shelf import sentences  # noqa: E402
from world.prefer import fresh  # noqa: E402
from world.world import RECENT_CHARS  # noqa: E402

SEED = 1831
GROUPS = {"old": ["2026-11-16", "2026-11-17"], "new": ["2026-11-18", "2026-11-19"]}
PER_GROUP = 150
LETTER_DAY = "2026-11-19"


def day(ref, date):
    return json.loads(subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:docs/days/{date}.json"], check=True,
                                     capture_output=True, text=True).stdout)


def shown(d, i):
    """The first sentences of the thoughts the prompt showed under "Earlier today" at step i (as World.situation)."""
    out = []
    for s in d["steps"][:i][-6:]:
        dec = s.get("decision") or {}
        if not dec.get("thought"):
            continue
        first = re.split(r"(?<=[.!?])\s", dec["thought"].strip())[0]
        if len(first) > 140:
            first = first[:139].rsplit(" ", 1)[0] + "…"
        activity = [seg["now"] for seg in d.get("segments", [])
                    if seg.get("now") and s["t"] <= seg["from"] < s["end"] and seg["to"] <= s["end"]]
        completed = " ".join(dict.fromkeys(activity))
        if len(completed) > 140:
            completed = completed[:139].rsplit(" ", 1)[0] + "…"
        line = f"{s['t']} recorded step: {dec['action']} ({dec['place']})" + (f"; executed activity: {completed}" if completed else "")
        line += f"; you thought: “{first}”"
        warnings = (s.get("mind") or {}).get("warnings") or []
        if warnings:
            note = "; ".join(warnings[:2])
            line += " Engine note: " + (note[:139].rsplit(" ", 1)[0] + "…" if len(note) > 140 else note) + "."
        out.append((line, first))
    while len(out) > 1 and sum(len(x) + 3 for x, _ in out) > RECENT_CHARS:
        out.pop(0)
    return [f for _, f in out]


def counts(ref):
    """Machine counts per day: the decision thoughts the mind wrote, and what he said."""
    out = {}
    for group, dates in GROUPS.items():
        for date in dates:
            d = day(ref, date)
            n = terms = plain = words = echo = calls = refused = spoken = said = 0
            for i, s in enumerate(d["steps"]):
                m, dec = s.get("mind") or {}, s.get("decision") or {}
                if m.get("source") != "mind" or not dec.get("thought"):
                    continue
                t = dec["thought"]
                hits = len(DOCTRINE.findall(t))
                n, terms, plain, words = n + 1, terms + hits, plain + (hits == 0), words + len(t.split())
                echo += not fresh(t, shown(d, i))
                calls += m.get("attempts", 1)
                refused += bool(m.get("refused"))
                if isinstance(dec.get("says"), str) and dec["says"].strip():
                    said, spoken = said + 1, spoken + len(DOCTRINE.findall(dec["says"]))
            out[date] = {"group": group, "day": d.get("n"), "thoughts": n,
                         "doctrinal_terms_per_thought": round(terms / n, 2) if n else None,
                         "thoughts_without_doctrinal_terms": plain, "share_without": round(plain / n, 3) if n else None,
                         "mean_thought_words": round(words / n, 1) if n else None,
                         "echo_of_shown_thoughts": echo, "calls_per_decision": round(calls / n, 2) if n else None,
                         "steps_with_a_refusal": refused, "spoken_lines": said,
                         "doctrinal_terms_per_spoken_line": round(spoken / said, 2) if said else None}
    return out


def letter(ref):
    """His first letter to Munich as it goes to the post: the last sitting, which rewrote the first (world/post.py)."""
    outbox = day(ref, LETTER_DAY)["state"]["post"]["outbox"]
    return outbox[-1]["text"] if outbox else ""


def freeze(ref, out, keyout):
    out, keyout = Path(out), Path(keyout)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    items = []
    for group, dates in GROUPS.items():
        pool = []
        for date in dates:
            for e in day(ref, date).get("entries", []):
                if e.get("k") == "diary" and isinstance(e.get("text"), str):
                    pool += [(date, s) for s in sentences(" ".join(e["text"].split())) if usable(s)]
        drawn = pool if len(pool) <= PER_GROUP else rng.sample(pool, PER_GROUP)
        items += [(group, date, s) for date, s in drawn]
    items += [("letter", LETTER_DAY, s) for s in split(letter(ref))]
    rng.shuffle(items)
    sheet, key = [], {}
    for n, (group, date, s) in enumerate(items, 1):
        sid = hashlib.sha256(f"{SEED}|{n}|{s}".encode()).hexdigest()[:10]
        sheet.append({"id": sid, "sentence": s})
        key[sid] = {"group": group, "date": date}
    sheet_bytes = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sheet).encode()
    (out / "SHEET.jsonl").write_bytes(sheet_bytes)
    (out / "CODEBOOK.md").write_text(CODEBOOK, encoding="utf-8")
    key_bytes = json.dumps(key, indent=1, sort_keys=True).encode()
    keyout.parent.mkdir(parents=True, exist_ok=True)
    keyout.write_bytes(key_bytes)
    manifest = {"shadow": ref, "seed": SEED, "groups": GROUPS, "letter_day": LETTER_DAY, "per_group": PER_GROUP,
                "items": len(sheet), "by_group": {g: sum(1 for x in key.values() if x["group"] == g) for g in ("old", "new", "letter")},
                "sheet_sha256": hashlib.sha256(sheet_bytes).hexdigest(), "key_sha256": hashlib.sha256(key_bytes).hexdigest(),
                "training_eligible": False}
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest


def qwen_requests(folder):
    """Plain Qwen as the third coder: one call per sentence, the same instruction and settings as stage 1's second coder."""
    book = (Path(folder) / "CODEBOOK.md").read_text(encoding="utf-8")
    rows = [json.loads(l) for l in (Path(folder) / "SHEET.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return [{"id": r["id"], "messages": [{"role": "system", "content": INSTRUCTION + book}, {"role": "user", "content": r["sentence"]}],
             "settings": {"temperature": 0, "max_tokens": 4, "seed": SEED, "cache_prompt": False}} for r in rows]


def qwen_codes(replies_path, out_path):
    """{"id", "reply"} lines from the PC into {"id", "code"} lines, as the two Claude coders gave them; unreadable replies are 10."""
    rows = [json.loads(l) for l in Path(replies_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    Path(out_path).write_text("".join(json.dumps({"id": r["id"], "code": parse(r["reply"]) or 10}) + "\n" for r in rows), encoding="utf-8")


def read_codes(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["id"]] = int(r["code"])
    return out


def report(folder, keypath, code_paths, letters=None):
    folder = Path(folder)
    key = json.loads(Path(keypath).read_text(encoding="utf-8"))
    manifest = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
    if hashlib.sha256(Path(keypath).read_bytes()).hexdigest() != manifest["key_sha256"]:
        raise SystemExit("the key does not match the manifest")
    coders = [read_codes(p) for p in code_paths]
    ids = sorted(key)
    for c in coders:
        if sorted(c) != ids:
            raise SystemExit("a coder's codes do not cover the sheet exactly")
    stage1 = json.loads((REPO / "pc/exports/paris-stage1-20261115/PROFILE-BOTH.json").read_text(encoding="utf-8"))["groups"]
    real = letters or {c: {int(k): v for k, v in stage1["letters"][c].items()} for c in ("claude", "qwen")}
    out = {"items": len(ids), "n": {g: sum(1 for i in ids if key[i]["group"] == g) for g in ("old", "new", "letter")}, "coders": {}}
    for name, codes in zip([Path(p).stem for p in code_paths], coders):
        prof = {g: shares([codes[i] for i in ids if key[i]["group"] == g]) for g in ("old", "new", "letter")}
        out["coders"][name] = {"profiles": prof,
                               "distance_to_his_letters": {g: {c: distance(prof[g], real[c]) for c in real} for g in prof}}
    if len(coders) == 2:
        a, b = coders
        out["kappa"] = {g: round(kappa([a[i] for i in ids if key[i]["group"] == g], [b[i] for i in ids if key[i]["group"] == g]), 2)
                        for g in ("old", "new", "letter")}
        out["kappa"]["all"] = round(kappa([a[i] for i in ids], [b[i] for i in ids]), 2)
    out["his_real_letters"] = {c: real[c] for c in real}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze"); f.add_argument("--ref", required=True); f.add_argument("--out", required=True); f.add_argument("--keyout", required=True)
    c = sub.add_parser("counts"); c.add_argument("--ref", required=True); c.add_argument("--out", required=True)
    r = sub.add_parser("report"); r.add_argument("--folder", required=True); r.add_argument("--key", required=True); r.add_argument("--codes", nargs="+", required=True)
    q = sub.add_parser("requests"); q.add_argument("--folder", required=True); q.add_argument("--out", required=True)
    k = sub.add_parser("qwen-codes"); k.add_argument("--replies", required=True); k.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "freeze":
        print(json.dumps(freeze(a.ref, a.out, a.keyout), indent=1))
    elif a.cmd == "counts":
        res = counts(a.ref)
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "COUNTS.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(res, indent=1))
    elif a.cmd == "requests":
        rows = qwen_requests(a.folder)
        Path(a.out).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        print(len(rows))
    elif a.cmd == "qwen-codes":
        qwen_codes(a.replies, a.out)
    else:
        print(json.dumps(report(a.folder, a.key, a.codes), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
