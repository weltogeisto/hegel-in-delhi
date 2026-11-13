#!/usr/bin/env python3
"""M1, the ordinary-life prompt screen (manual v1.1 §5.3-5.4; DECISIONS.md 20-21). Evaluation only, never training data.

Two arms on the same recorded situations, plain Qwen, seeds 1831, 2718 and 3141:
    A  mind/soul.md, as he runs live
    B  mind/soul-ordinary.md: practical by default, philosophy when the moment calls for it, natural modern English
24 contexts, frozen before any output: every moment on shadow Days 13, 14, 28 and 38 where nobody speaks to him
(16), and 8 encounters where someone does, drawn with seed 1831. Each has an exact before-state (a single-step
commit) and is rebuilt as Training 3 rebuilds its shadow situations. None of these days trains Training 3.

    python3 tools/prompt_screen.py freeze --repo NATIVE --shadow SHA --out DIR     # CPU, once
    prompt_screen.run(DIR, post)                                                   # 144 calls; Astra's guarded transport
    python3 tools/prompt_screen.py packet --dir DIR --sheet SHEET.jsonl --key KEY.json
    python3 tools/prompt_screen.py verdict --dir DIR --judgments J.jsonl --key KEY.json

Pass (manual §5.4): B preferred for practical appropriateness in at least 16 of the 24 contexts, seeds taken
together, with no concrete consequential regression in B. A pass earns the fresh 24-context confirmation, not
adoption.

The confirmation (Welt's go, 13 November) is frozen with `freeze --from-day 44`: every complete shadow day from
Day 44 on, once they hold 16 ordinary moments and 8 encounters. Its pass rule, m1-v2, is written into its manifest
before any output: B preferred in at least 16 of 24, and B's flagged contexts at most A's plus one. The first
screen's rule, m1-v1 (no flagged context that A doesn't share), failed either version against the other.
"""
import argparse
import copy
import json
import random
import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.decision_pairs import shown  # noqa: E402
from tools.decision_sampler import checked, decision_payload, digest, json_bytes, restored_context, save  # noqa: E402
from world import contract  # noqa: E402
from world.report import grams  # noqa: E402

DAYS = (13, 14, 28, 38)
ORDINARY, ENCOUNTERS = 16, 8
SEEDS = (1831, 2718, 3141)
ARMS = {"A": "mind/soul.md", "B": "mind/soul-ordinary.md"}
SPEAKS = " says: “"
PASS_AT = 16
PASS_RULES = {"m1-v1": "B preferred in at least 16 of 24, and no context flagged for B that isn't flagged for A",
              "m1-v2": "B preferred in at least 16 of 24, and B's flagged contexts at most A's plus one"}
# Diagnostics only, fixed before the confirmation's outputs: the vocabulary of his lecture hall.
DOCTRINE = re.compile(r"\b(dialectic\w*|universal\w*|particular\w*|spirit\w*|ethical|negat\w+|mediat\w+|sublat\w+|actuali\w+"
                      r"|absolute|substance|abstract\w*|concept\w*|civil society|system of needs|the idea)\b", re.I)


def kind(row):
    return "encounter" if SPEAKS in row["check"]["situation"].get("event", "") else "ordinary"


def freeze(repo, head, out, souls=None, first_day=None):
    """The 24 contexts and both arms' system prompts, before any output exists.

    Without first_day: the first screen's Days 13, 14, 28 and 38, under m1-v1. With it: every complete shadow day
    from that day on, under m1-v2; it refuses until those days hold enough contexts."""
    from tools.decision_situations import SnapshotGit, project
    from world.world import World
    out, repo = Path(out), Path(repo)
    if out.exists():
        raise FileExistsError("use a new screen directory")
    souls = souls or {arm: (repo / path).read_text(encoding="utf-8") for arm, path in ARMS.items()}
    git, world = SnapshotGit(repo, head), World()
    days = git.days(head)
    pool, used = [], []
    for date in sorted(days):
        day, raw, _ = days[date]
        if (day["n"] not in DAYS) if first_day is None else (day["n"] < first_day or not day.get("complete")):
            continue
        used.append(day["n"])
        before = git.before_steps(day)
        for i, step in enumerate(day.get("steps", [])):
            if (step.get("mind") or {}).get("source") != "mind" or i not in before:
                continue
            prefix, praw, parent, child = before[i]
            history = {k: v[0] for k, v in git.days(parent, before=date).items()}
            prov = dict(kind="exact-parent reconstruction for the M1 screen", shadow=head, parent=parent, child=child,
                        before_sha256=digest(praw), observed_day_sha256=digest(raw))
            pool.append(project(world, souls["A"], day, i, prefix, history, prov))
    ordinary = sorted((r for r in pool if kind(r) == "ordinary"), key=lambda r: (r["day"], r["step"]))
    encounters = sorted((r for r in pool if kind(r) == "encounter"), key=lambda r: (r["day"], r["step"]))
    if len(ordinary) < ORDINARY or len(encounters) < ENCOUNTERS:
        raise ValueError(f"too few contexts: {len(ordinary)} ordinary, {len(encounters)} encounters")
    rng = random.Random(1831)
    chosen = sorted(rng.sample(ordinary, ORDINARY), key=lambda r: (r["day"], r["step"])) if len(ordinary) > ORDINARY else ordinary
    chosen += sorted(rng.sample(encounters, ENCOUNTERS), key=lambda r: (r["day"], r["step"]))
    for arm, text in souls.items():
        save(out / "souls" / f"{arm}.json", {"arm": arm, "path": ARMS[arm], "text": text})
    rows = []
    for r in chosen:
        name = digest(r["id"].encode()) + ".json"
        save(out / "contexts" / name, dict(r, kind=kind(r)))
        rows.append({"id": r["id"], "kind": kind(r), "path": "contexts/" + name, "sha256": digest(json_bytes(dict(r, kind=kind(r))))})
    rule = "m1-v1" if first_day is None else "m1-v2"
    manifest = {"screen": "M1 ordinary-life prompt screen" + ("" if first_day is None else ", the confirmation"),
                "shadow": head, "days": sorted(used), "seeds": list(SEEDS), "pass_rule": rule, "pass_rule_text": PASS_RULES[rule],
                "arms": {a: {"path": ARMS[a], "sha256": digest(t.encode("utf-8"))} for a, t in souls.items()},
                "pool": {"ordinary": len(ordinary), "encounters": len(encounters)}, "rows": rows, "training_eligible": False}
    save(out / "MANIFEST.json", manifest)
    return manifest


def contexts(folder):
    folder = Path(folder)
    manifest = checked(folder / "MANIFEST.json")
    souls = {arm: checked(folder / "souls" / f"{arm}.json")["text"] for arm in ARMS}
    for arm, soul in souls.items():
        if digest(soul.encode("utf-8")) != manifest["arms"][arm]["sha256"]:
            raise ValueError("an arm's prompt changed")
    rows = []
    for ref in manifest["rows"]:
        row = checked(folder / ref["path"])
        if digest(json_bytes(row)) != ref["sha256"] or row["id"] != ref["id"]:
            raise ValueError("a frozen context changed")
        rows.append(row)
    return manifest, souls, rows


def requests(folder):
    """The 144 calls: every context, both arms, three seeds; the user message is the same for both arms."""
    _, souls, rows = contexts(folder)
    out = []
    for row in rows:
        sit, _, _ = restored_context(row["check"])
        for arm in ARMS:
            messages = [{"role": "system", "content": souls[arm]}, row["messages"][1]]
            for seed in SEEDS:
                out.append((f"screen/{row['id']}/{arm}/{seed}", row, arm, seed, decision_payload(messages, sit, seed)))
    return out


def run(folder, post, world=None):
    """Post each call once through the guarded transport; saved replies are replayed, never re-sent."""
    from world.world import World
    world = world or World()
    folder, done = Path(folder), []
    for key, row, arm, seed, payload in requests(folder):
        path = folder / "records" / (digest(key.encode()) + ".json")
        if path.exists():
            rec = checked(path)
            if rec["key"] != key or rec["payload_sha256"] != digest(json_bytes(payload)):
                raise ValueError("a saved reply belongs to another request")
        else:
            answer, receipt = post(key, payload)
            if not isinstance(receipt, dict) or not receipt.get("response_sha256"):
                raise ValueError("durable response receipt required")
            choice = answer["choices"][0]
            raw = choice["message"].get("content")
            if not isinstance(raw, str):
                raise ValueError("response has no text; preserve its chain")
            parsed = contract.extract_json(raw)
            sit, ctx, state = restored_context(row["check"])
            errors, warnings, _ = world.check(parsed, sit, ctx, state)
            rec = dict(key=key, id=row["id"], arm=arm, seed=seed, raw=raw, answer=parsed, accepted=not errors,
                       errors=errors, warnings=warnings, finish_reason=choice.get("finish_reason"), receipt=receipt,
                       payload_sha256=digest(json_bytes(payload)), training_eligible=False)
            save(path, rec)
        done.append(rec)
    return done


def records(folder):
    folder = Path(folder)
    out = {}
    for key, row, arm, seed, payload in requests(folder):
        rec = checked(folder / "records" / (digest(key.encode()) + ".json"))
        if rec["payload_sha256"] != digest(json_bytes(payload)):
            raise ValueError("a saved reply belongs to another request")
        out.setdefault(row["id"], {}).setdefault(arm, []).append(rec)
    return out


def shown_output(rec):
    a = rec["answer"] if isinstance(rec["answer"], dict) else {}
    return {"seed": rec["seed"], "thought": a.get("thought"), "action": a.get("action"), "place": a.get("place"),
            "says": a.get("says"), "buys": a.get("buys"), "accepted": rec["accepted"], "errors": rec["errors"]}


def packet(folder, sheet, key):
    """One blind row per context: the situation and both arms' three replies, as X and Y in a random order."""
    _, _, rows = contexts(folder)
    recs, rng, out, k = records(folder), secrets.SystemRandom(), [], {}
    for row in rows:
        arms = list(ARMS)
        rng.shuffle(arms)
        k[row["id"]] = {"X": arms[0], "Y": arms[1]}
        out.append({"id": row["id"], "kind": row["kind"], "situation": row["messages"][1]["content"],
                    "X": [shown_output(r) for r in recs[row["id"]][arms[0]]],
                    "Y": [shown_output(r) for r in recs[row["id"]][arms[1]]]})
    Path(sheet).write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
    raw = json.dumps(k, sort_keys=True).encode()
    with Path(key).open("xb") as f:
        f.write(raw)
    return digest(raw)


def diagnostics(folder):
    """Machine counts per arm, beside the judgments: never a gate on their own."""
    _, _, rows = contexts(folder)
    recs, out = records(folder), {}
    for arm in ARMS:
        n = accepted = words = echo = terms = plain = spoken = 0
        for row in rows:
            seen = set().union(*(grams(first) for *_, first in shown(row["messages"])))
            for rec in recs[row["id"]][arm]:
                n += 1
                accepted += rec["accepted"]
                thought = (rec["answer"] or {}).get("thought") if isinstance(rec["answer"], dict) else None
                if isinstance(thought, str):
                    words += len(thought.split())
                    echo += bool(grams(thought) & seen)
                    hits = len(DOCTRINE.findall(thought))
                    terms += hits
                    plain += hits == 0
                says = (rec["answer"] or {}).get("says") if isinstance(rec["answer"], dict) else None
                spoken += len(DOCTRINE.findall(says)) if isinstance(says, str) else 0
        out[arm] = {"replies": n, "accepted": accepted, "mean_thought_words": round(words / n, 1) if n else None,
                    "echo_of_shown_thoughts": echo, "doctrinal_terms_per_thought": round(terms / n, 2) if n else None,
                    "thoughts_without_doctrinal_terms": plain, "doctrinal_terms_per_reply_in_speech": round(spoken / n, 2) if n else None}
    return out


def verdict(folder, judgments, key, rule=None):
    """judgments: one row per context, {"id", "prefer": "X"|"Y"|"tie", "regression": {"X": bool, "Y": bool}, "reason"}.
    The pass rule is the one frozen in the manifest; a manifest without one is the first screen's (m1-v1)."""
    manifest, _, rows = contexts(folder)
    rule = rule or manifest.get("pass_rule", "m1-v1")
    if rule not in PASS_RULES:
        raise ValueError("unknown pass rule: " + str(rule))
    k = json.loads(Path(key).read_text())
    j = {r["id"]: r for r in (json.loads(x) for x in Path(judgments).read_text(encoding="utf-8").splitlines() if x.strip())}
    if set(j) != {r["id"] for r in rows}:
        raise ValueError("a judgment is missing or extra")
    prefer_b = sum(1 for i, r in j.items() if r["prefer"] in ("X", "Y") and k[i][r["prefer"]] == "B")
    prefer_a = sum(1 for i, r in j.items() if r["prefer"] in ("X", "Y") and k[i][r["prefer"]] == "A")
    regress = {arm: sorted(i for i, r in j.items() for slot in ("X", "Y") if r["regression"].get(slot) and k[i][slot] == arm)
               for arm in ARMS}
    new_regressions = sorted(set(regress["B"]) - set(regress["A"]))
    clean = not new_regressions if rule == "m1-v1" else len(regress["B"]) <= len(regress["A"]) + 1
    return {"prefer_B": prefer_b, "prefer_A": prefer_a, "ties": len(rows) - prefer_a - prefer_b,
            "regressions": regress, "B_only_regressions": new_regressions, "pass_rule": rule,
            "passed": prefer_b >= PASS_AT and clean, "diagnostics": diagnostics(folder)}


def welt_pairs(folder, out):
    """Six of the contexts, drawn with seed 1831, and each arm's seed-1831 reply in a shuffled order, with the key at
    the bottom: for Welt to read himself. Written only after the judgments are sealed."""
    _, _, rows = contexts(folder)
    recs, ids = records(folder), [r["id"] for r in rows]
    rng = random.Random(1831)
    picked = sorted(rng.sample(ids, 6), key=ids.index)
    order = {cid: rng.sample(list(ARMS), 2) for cid in picked}
    by_id = {r["id"]: r for r in rows}

    def one(cid, arm):
        rec = next(x for x in recs[cid][arm] if x["seed"] == SEEDS[0])
        a = rec["answer"] if isinstance(rec["answer"], dict) else {}
        text = (a.get("thought") or "(no usable reply)").strip()
        if a.get("says"):
            text += f"\n  *He says:* “{a['says'].strip()}”"
        if not rec["accepted"]:
            text += f"\n  *(The world refused this one: {'; '.join(rec['errors'])}.)*"
        return text
    lines = ["# Six pairs for Welt", "",
             "Six of the 24 situations, drawn with seed 1831, and each version's first reply. The order within a pair is "
             "shuffled; the key is at the bottom. Which of each pair sounds more like the Hegel you want on an ordinary day?", ""]
    key = []
    for n, cid in enumerate(picked, 1):
        sit = by_id[cid]["messages"][1]["content"]
        event = re.search(r"\nWhat happens: (.*)", sit)
        lines += [f"## {n}. {sit.splitlines()[0]}", "", f"**What happens:** {event.group(1) if event else ''}", ""]
        for label, arm in zip(("First", "Second"), order[cid]):
            lines += [f"**{label}:** {one(cid, arm)}", ""]
        names = {"A": "live", "B": "new"}
        key.append(f"{n}. First = {names[order[cid][0]]} instructions, Second = {names[order[cid][1]]} instructions.")
    lines += ["## Key", "", f"Live = `{ARMS['A']}`; new = `{ARMS['B']}`.", ""] + key + [""]
    with Path(out).open("x", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return picked


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--repo", type=Path, required=True)
    f.add_argument("--shadow", required=True)
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--from-day", type=int, help="the confirmation: every complete shadow day from this one on, under m1-v2")
    w = sub.add_parser("pairs")
    w.add_argument("--dir", type=Path, required=True)
    w.add_argument("--out", type=Path, required=True)
    k = sub.add_parser("packet")
    k.add_argument("--dir", type=Path, required=True)
    k.add_argument("--sheet", type=Path, required=True)
    k.add_argument("--key", type=Path, required=True)
    v = sub.add_parser("verdict")
    v.add_argument("--dir", type=Path, required=True)
    v.add_argument("--judgments", type=Path, required=True)
    v.add_argument("--key", type=Path, required=True)
    a = p.parse_args(argv)
    if a.cmd == "freeze":
        m = freeze(a.repo, a.shadow, a.out, first_day=a.from_day)
        print(json.dumps({"shadow": m["shadow"], "days": m["days"], "pool": m["pool"], "contexts": len(m["rows"]),
                          "pass_rule": m["pass_rule"], "arms": m["arms"]}))
    elif a.cmd == "pairs":
        print(json.dumps({"contexts": welt_pairs(a.dir, a.out)}))
    elif a.cmd == "packet":
        print(json.dumps({"key_sha256": packet(a.dir, a.sheet, a.key)}))
    else:
        print(json.dumps(verdict(a.dir, a.judgments, a.key), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
