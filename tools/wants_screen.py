#!/usr/bin/env python3
"""T69, the `wants` line's screen (pc/WANTS-SCREEN.md). Evaluation only, never training data.

Three arms on the 24 contexts frozen as M1's confirmation froze its own (tools/prompt_screen.py):
    A   the instructions the manifest names (its arm A), seeds 1831, 2718, 3141
    A2  the same again, seeds 4253, 5167, 6079: with A, the band of noise
    W   the same, with contract.WANTS_LINE after them and the optional field `wants` in the schema, seeds 1831, 2718, 3141

    python3 tools/wants_screen.py freeze --repo NATIVE --shadow SHA --out DIR --from-day N   # prompt_screen.freeze; its arm B is not used here
    wants_screen.run(DIR, post)                                                              # 216 calls; the guarded transport, as M1's
    python3 tools/wants_screen.py measure --dir DIR

`measure` prints, per arm, the five measures of the file, the band (A against A2), pass or fail for W by the file's rule, and how many of W's
decisions carry a wish. Every request carries "cache_prompt": false, so that a reply depends on its prompt and seed and not on how much of the prompt the server took
from its cache (measured 16 November: with the cache on, two same-seed days differed; off, they were identical over 30 steps).
A read for Welt, not a gate on its own: a pass earns a provisional trial on his word.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import prompt_screen as ps  # noqa: E402
from tools.decision_pairs import shown  # noqa: E402
from tools.decision_sampler import checked, decision_payload, digest, json_bytes, restored_context, save  # noqa: E402
from world import contract, health  # noqa: E402
from world.report import grams  # noqa: E402

ARMS = {"A": (1831, 2718, 3141), "A2": (4253, 5167, 6079), "W": (1831, 2718, 3141)}
WORSE = {"accepted": "fewer", "echo": "more", "notions": "more", "words": "more than a tenth longer", "acts": "further from A than A2 is"}
DEAD, FILLER = 1 / 20, 1 / 2           # the file's reads on how many decisions carry a wish


def requests(folder):
    """The 216 calls: every context, three arms, three seeds each. Their user message is the same; W's system message is the arm A's and the sentence."""
    _, souls, rows = ps.contexts(folder)
    out = []
    for row in rows:
        sit, _, _ = restored_context(row["check"])
        for arm, seeds in ARMS.items():
            system = souls["A"] + "\n\n" + contract.WANTS_LINE if arm == "W" else souls["A"]
            for seed in seeds:
                s = dict(sit, wants=True) if arm == "W" else sit
                payload = decision_payload([{"role": "system", "content": system}, row["messages"][1]], s, 1831)
                payload["seed"] = seed              # decision_sampler registers only its own four seeds; this screen's are declared in its file
                payload["cache_prompt"] = False     # likewise: decision_payload does not send it; the reply must not depend on what the server cached
                out.append((f"wants/{row['id']}/{arm}/{seed}", row, arm, seed, payload))
    return out


def run(folder, post, world=None):
    """Post each call once through the guarded transport (post(key, payload) -> (response, receipt)); saved replies are replayed, never re-sent."""
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
            if arm == "W":
                sit["wants"] = True                 # as live: the field is read, and judged, only with the switch on
            errors, warnings, _ = world.check(parsed, sit, ctx, state)
            rec = dict(key=key, id=row["id"], arm=arm, seed=seed, raw=raw, answer=parsed, accepted=not errors, errors=errors, warnings=warnings,
                       finish_reason=choice.get("finish_reason"), receipt=receipt, payload_sha256=digest(json_bytes(payload)), training_eligible=False)
            save(path, rec)
        done.append(rec)
    return done


def records(folder):
    """{arm: [(row, record)]}: every saved reply of the screen, checked against its request."""
    folder, out = Path(folder), {arm: [] for arm in ARMS}
    for key, row, arm, seed, payload in requests(folder):
        rec = checked(folder / "records" / (digest(key.encode()) + ".json"))
        if rec["payload_sha256"] != digest(json_bytes(payload)):
            raise ValueError("a saved reply belongs to another request")
        out[arm].append((row, rec))
    return out


def measures(replies):
    """The five measures of one arm over its replies [(row, record)]. `acts` is the minutes by act of the accepted replies, for the divergence."""
    n = accepted = words = echo = terms = thoughts = 0
    acts = {}
    for row, rec in replies:
        n += 1
        accepted += rec["accepted"]
        a = rec["answer"] if isinstance(rec["answer"], dict) else {}
        thought = a.get("thought")
        if isinstance(thought, str):
            thoughts += 1
            words += len(thought.split())
            terms += len(ps.DOCTRINE.findall(thought))
            echo += bool(grams(thought) & set().union(set(), *(grams(first) for *_, first in shown(row["messages"]))))
        if rec["accepted"]:
            acts[a["action"]] = acts.get(a["action"], 0) + a["minutes"]
    wishes = sum(1 for _, rec in replies if rec["accepted"] and isinstance(rec["answer"], dict) and isinstance(rec["answer"].get("wants"), str) and rec["answer"]["wants"].strip())
    return {"replies": n, "accepted": accepted / n, "echo": echo / n, "notions": 100 * terms / words if words else 0.0,
            "words": words / thoughts if thoughts else 0.0, "acts": acts, "wishes": wishes}


def passes(m, a, a2, band):
    """W's verdict on each measure, by the file's rule: not worse than the worse of A and A2 by more than one band. For the words the worse is a
    tenth longer than the longer of the two; for the acts it is further from A than A2 is."""
    return {"accepted": m["accepted"] >= min(a["accepted"], a2["accepted"]) - band["accepted"],
            "echo": m["echo"] <= max(a["echo"], a2["echo"]) + band["echo"],
            "notions": m["notions"] <= max(a["notions"], a2["notions"]) + band["notions"],
            "words": m["words"] <= max(a["words"], a2["words"]) * 1.1,
            "acts": m["divergence"] is not None and band["acts"] is not None and m["divergence"] <= band["acts"]}


def measure(folder):
    by = {arm: measures(replies) for arm, replies in records(folder).items()}
    for arm in by:
        by[arm]["divergence"] = 0.0 if arm == "A" else health.divergence(by["A"]["acts"], by[arm]["acts"])
    band = {k: abs(by["A"][k] - by["A2"][k]) for k in ("accepted", "echo", "notions", "words")}
    band["acts"] = by["A2"]["divergence"]
    verdict = passes(by["W"], by["A"], by["A2"], band)
    w = by["W"]
    read = "dead (under one in twenty)" if w["wishes"] / w["replies"] < DEAD else "filler (over one in two)" if w["wishes"] / w["replies"] > FILLER else "between"
    return {"arms": {arm: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items() if k != "acts"} for arm, m in by.items()},
            "band": {k: round(v, 3) if v is not None else None for k, v in band.items()}, "W_passes": verdict, "passed": all(verdict.values()),
            "wishes": {"W": w["wishes"], "of": w["replies"], "read": read}}


def table(result):
    cols = ("accepted", "echo", "notions", "words", "divergence")
    lines = ["arm   " + "  ".join(f"{c:>10}" for c in cols)]
    for arm, m in result["arms"].items():
        lines.append(f"{arm:<5} " + "  ".join(f"{m[c]:>10}" if m[c] is not None else f"{'-':>10}" for c in cols))
    lines.append("band  " + "  ".join(f"{result['band'].get(c if c != 'divergence' else 'acts'):>10}" for c in cols))
    lines.append("W     " + "  ".join(f"{'pass' if result['W_passes'][c if c != 'divergence' else 'acts'] else 'FAIL':>10}" for c in cols))
    lines.append(f"W passes the screen: {result['passed']}; {result['wishes']['W']} of {result['wishes']['of']} decisions carry a wish: {result['wishes']['read']}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--repo", type=Path, required=True)
    f.add_argument("--shadow", required=True)
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--from-day", type=int, required=True)
    m = sub.add_parser("measure")
    m.add_argument("--dir", type=Path, required=True)
    m.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "freeze":
        r = ps.freeze(a.repo, a.shadow, a.out, first_day=a.from_day)
        print(json.dumps({"shadow": r["shadow"], "days": r["days"], "pool": r["pool"], "contexts": len(r["rows"]), "arms": r["arms"]}))
    else:
        result = measure(a.dir)
        print(json.dumps(result, indent=1) if a.json else table(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
