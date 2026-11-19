#!/usr/bin/env python3
"""W9, the voices' repairs, Part 2 of their check (pc/VOICE-REPAIRS-CHECK.md). Evaluation only; never training data.

    freeze  --repo NATIVE --shadow SHA --out DIR     the moments by rule from the complete Days 44-49 (sets A and B), rebuilt
                                                      with W4's tools/voice_screen.rebuild; no model call
    run     --dir DIR --server URL --job JOBDIR       both arms (HEGEL_VOICE_REPAIRS off, on) x seeds 1831, 2718, 3141; resumable
    packet  --dir DIR --sheet SHEET --key KEY         the blind sheet (arm hidden) and the key, which stays on the PC

Set A: a recorded reply whose speaker's own presence sentence stood in the event his voice read (the repairs' own
voices.own_presence_out changes it). Set B: a recorded reply at a place with nothing for sale that is not his home (the
repairs' own condition in voices.render). Greetings are not rebuilt by W4's rebuild (it captures the reply path only): they
are listed as excluded with that reason. Twenty of each at most, drawn with random.Random(1831), A first, then B.
"""
import argparse, copy, json, random, secrets, sys
from pathlib import Path
from types import SimpleNamespace
HOME_TOOLS = Path(__file__).resolve()
REPO_ROOT = Path(sys.argv[sys.argv.index("--tools") + 1]) if "--tools" in sys.argv else Path.home() / "w9" / "main"
sys.path.insert(0, str(REPO_ROOT))
from tools.decision_sampler import checked, digest, json_bytes, save          # noqa: E402
from tools.decision_situations import SnapshotGit, HistoricalMemory         # noqa: E402
from tools import voice_claims as vc, voice_screen as vs                    # noqa: E402
from tools.recorded_llama import RecordedClient                              # noqa: E402
from world import voices                                                     # noqa: E402
from world.engine import Engine                                              # noqa: E402
from world.world import World                                                # noqa: E402

DAYS = range(44, 50)
ARMS = {"off": (1831, 2718, 3141), "on": (1831, 2718, 3141)}
CAP = 20


def freeze(repo, head, out):
    repo, out = Path(repo), Path(out)
    if out.exists():
        raise FileExistsError(out)
    g = SnapshotGit(repo, head)
    days = [v[0] for v in g.days(head).values() if v[0]["n"] in DAYS]
    if sorted(d["n"] for d in days) != list(DAYS) or not all(d.get("complete") for d in days):
        raise ValueError("Days 44-49 are not all present and complete at this commit")
    bydate = {d["date"]: d for d in days}
    items = vc.collect(sorted(days, key=lambda d: d["n"]))
    snap = {d: g.before_steps(bydate[d]) for d in bydate}
    w = World()
    name_to_id = {w.short(k).casefold(): k for k in w.cast}
    for k, c in w.cast.items():
        name_to_id[c["name"].casefold()] = k
    excluded, rebuilt = [], []
    for x in items:
        base = dict(date=x["date"], day=x["day"], step=x["_step"], t=x["t"], by=x["by"], kind=x["kind"])
        if x["kind"] != "reply":
            excluded.append(dict(base, reason="greeting: W4's rebuild captures the reply path only")); continue
        if x["_step"] not in snap[x["date"]]:
            excluded.append(dict(base, reason="no exact pre-step parent")); continue
        cid = name_to_id.get((x["by"] or "").casefold())
        if cid is None:
            excluded.append(dict(base, reason="speaker not on the cast card")); continue
        try:
            r = vs.rebuild(repo, g, bydate[x["date"]], x, snap[x["date"]][x["_step"]])
        except Exception as e:                      # a moment that no longer reaches its voice is reported, never forced
            excluded.append(dict(base, reason="not rebuildable: " + str(e)[:160])); continue
        card = w.cast[cid]
        r["cid"] = cid
        r["in_A"] = voices.own_presence_out(card, r["sit"]["event"]) != r["sit"]["event"]
        r["in_B"] = (not r["sit"].get("for_sale")) and r["sit"].get("place") != "home"
        if r["in_A"] or r["in_B"]:
            rebuilt.append(r)
    pool_A = [r for r in rebuilt if r["in_A"]]
    pool_B = [r for r in rebuilt if r["in_B"]]
    rng = random.Random(1831)
    key = lambda r: (r["observed"]["date"], r["observed"]["_step"])
    chosen_A = sorted(rng.sample(pool_A, CAP) if len(pool_A) > CAP else pool_A, key=key)
    chosen_B = sorted(rng.sample(pool_B, CAP) if len(pool_B) > CAP else pool_B, key=key)
    chosen, seen = [], set()
    for r in chosen_A + chosen_B:
        k = key(r)
        if k not in seen:
            seen.add(k); chosen.append(r)
    out.mkdir(parents=True)
    manifest = dict(screen="W9, the voices' repairs, Part 2", declared="pc/VOICE-REPAIRS-CHECK.md", shadow=head, days=list(DAYS),
                    arms=ARMS, selection_seed=1831, cap=CAP, pool={"A": len(pool_A), "B": len(pool_B)},
                    chosen={"A": len(chosen_A), "B": len(chosen_B), "both": len(chosen_A) + len(chosen_B) - len(chosen)},
                    excluded=excluded, rows=[], training_eligible=False)
    for i, r in enumerate(chosen):
        r["id"] = f"R{i + 1:02}"
        r["sets"] = [s for s, rows in (("A", chosen_A), ("B", chosen_B)) if any(key(x) == key(r) for x in rows)]
        name = r["id"] + ".json"
        save(out / "contexts" / name, r)
        manifest["rows"].append(dict(id=r["id"], sets=r["sets"], path="contexts/" + name, sha256=digest(json_bytes(r))))
    save(out / "MANIFEST.json", manifest)
    return manifest


def contexts(folder):
    folder = Path(folder)
    m = checked(folder / "MANIFEST.json")
    rows = []
    for x in m["rows"]:
        r = checked(folder / x["path"])
        if digest(json_bytes(r)) != x["sha256"]:
            raise ValueError("a frozen context changed")
        rows.append(r)
    return rows


def engine(row, arm, mind):
    w = World(promises=False)
    e = object.__new__(Engine)
    e.cfg = SimpleNamespace(voice_facts=False, outcome_memory=False, voice_repairs=(arm == "on"))
    e.world = w; e.mind = mind; e.memory = HistoricalMemory(w, row["past"]); e.voice_prompt = row["voice_prompt"]
    return e


def exercise(row, arm, seed, post):
    calls = []

    class Mind:
        def chat(self, messages, schema, max_tokens=250):
            p = vs.payload(messages, schema, seed, max_tokens)
            k = f"repairs/{row['id']}/{arm}/{seed}/{len(calls) + 1}"
            answer, receipt = post(k, p)
            if not receipt.get("response_sha256"):
                raise ValueError("durable receipt required")
            raw = answer["choices"][0]["message"].get("content")
            if not isinstance(raw, str):
                raise ValueError("missing response text")
            calls.append(dict(key=k, payload=p, payload_sha256=digest(json_bytes(p)), raw=raw, receipt=receipt,
                              finish_reason=answer["choices"][0].get("finish_reason")))
            return raw
    e = engine(row, arm, Mind())
    d = copy.deepcopy(row["day"]); sit = copy.deepcopy(row["sit"])
    heard = e.voice(row["cid"], d, sit, row["says"], purchases=row["ctx"].get("purchases"))
    return dict(id=row["id"], arm=arm, seed=seed, calls=calls, heard=heard, training_eligible=False)


def run(folder, server, job):
    folder, job = Path(folder), Path(job)
    client = RecordedClient(server, job / "receipts")

    def post(k, p):
        result = client.post(k, p)
        return result, json.loads(Path(str(client.stem(k)) + ".done.json").read_text())
    done = []
    for row in contexts(folder):
        for arm, seeds in ARMS.items():
            for seed in seeds:
                p = job / "records" / (digest(f"{row['id']}/{arm}/{seed}".encode()) + ".json")
                if p.exists():
                    rec = checked(p)
                else:
                    rec = exercise(row, arm, seed, post); save(p, rec)
                done.append(rec)
    return done


def packet(folder, job, sheet, keyfile):
    rows = {r["id"]: r for r in contexts(folder)}
    records = [checked(p) for p in sorted((Path(job) / "records").glob("*.json"))]
    if len(records) != len(rows) * 6:
        raise ValueError("complete screen required")
    order = list(records); secrets.SystemRandom().shuffle(order)
    public, mapping = [], {}
    for i, r in enumerate(order):
        label = f"VR{i + 1:03}"; row = rows[r["id"]]
        public.append(dict(id=label, sets=row["sets"], place=row["sit"].get("place"), for_sale=row["sit"].get("for_sale"),
                           moment=row["sit"], record_before=row["day"], he_said=row["says"], speaker=row["observed"]["by"],
                           heard=r["heard"], answers=[c["raw"] for c in r["calls"]], training_eligible=False))
        mapping[label] = dict(id=r["id"], arm=r["arm"], seed=r["seed"])
    key = dict(mapping=mapping, training_eligible=False)
    save(Path(keyfile), key)
    save(Path(sheet), dict(rows=public, key_sha256=digest(json_bytes(key))))
    return digest(json_bytes(key))


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze"); f.add_argument("--repo", required=True); f.add_argument("--shadow", required=True); f.add_argument("--out", required=True)
    r = sub.add_parser("run"); r.add_argument("--dir", required=True); r.add_argument("--server", required=True); r.add_argument("--job", required=True)
    k = sub.add_parser("packet"); k.add_argument("--dir", required=True); k.add_argument("--job", required=True); k.add_argument("--sheet", required=True); k.add_argument("--key", required=True)
    for s in (f, r, k):
        s.add_argument("--tools")
    a = p.parse_args()
    if a.cmd == "freeze":
        m = freeze(a.repo, a.shadow, a.out)
        print(json.dumps({k: m[k] for k in ("shadow", "pool", "chosen")} | {"rows": len(m["rows"]), "excluded": len(m["excluded"]),
              "excluded_by_reason": {r: sum(1 for x in m["excluded"] if x["reason"].split(":")[0] == r) for r in {x["reason"].split(":")[0] for x in m["excluded"]}}}))
    elif a.cmd == "run":
        done = run(a.dir, a.server, a.job)
        print(json.dumps({"records": len(done), "calls": sum(len(x["calls"]) for x in done), "empty": sum(1 for x in done if not x["heard"])}))
    else:
        print(json.dumps({"key_sha256": packet(a.dir, a.job, a.sheet, a.key)}))


if __name__ == "__main__":
    main()
