"""W8 verdict, from three sealed ballots on main. CPU only.

    python tools/lora_fresh_verdict.py --main-ref refs/remotes/github/main
    python tools/lora_fresh_verdict.py --main-ref refs/remotes/github/main --keys DIR --out VERDICT.json

The first command reports ballot readiness. Only the second can open the private keys.
The main ref should be fetched before invoking either command.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.prompt_screen import DOCTRINE

FOLDER = "pc/exports/lora-fresh-scenes-20261119/readers"
READERS = ("sol", "claude", "welt")
VERSIONS = ("adapter", "plain1", "plain2")
INITIAL_PACKET_COMMIT = "cc39511b6157094714fb82d3bf2c8defec896e55"
MODEL_LABELS = "ABC"
PREFERENCE_LABELS = "XYZ"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def object_pairs(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate JSON object key")
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=object_pairs)


def indexed(rows):
    result = {row["id"]: row for row in rows}
    if not result or len(result) != len(rows):
        raise ValueError("empty or duplicated item ID")
    return result


def git(*args):
    return subprocess.check_output(("git", *args))


def git_inputs(main_ref):
    if not re.fullmatch(r"refs/(heads/main|remotes/[\w.\-]+/main)", main_ref):
        raise ValueError("choose an actual main ref, e.g. refs/remotes/github/main")
    commit = git("rev-parse", "--verify", main_ref + "^{commit}").decode().strip()
    def blob(name):
        return git("show", f"{commit}:{FOLDER}/{name}")
    manifest = blob("HASHES.json")
    if manifest != git("show", f"{INITIAL_PACKET_COMMIT}:{FOLDER}/HASHES.json"):
        raise ValueError("packet manifest differs from W8's original draw")
    files = set(git("ls-tree", "--name-only", f"{commit}:{FOLDER}").decode().splitlines())
    return commit, parse(manifest), files, blob


def sealed_ballots(files, blob, manifest):
    ballots, packets, seals, waiting = {}, {}, {}, []
    for rater in READERS:
        name = f"ballot-{rater}"
        if not {name + ".jsonl", name + ".sha256"} <= files:
            waiting.append(rater)
            continue
        ballot = blob(name + ".jsonl")
        seal = blob(name + ".sha256").decode().strip().split()
        if not seal or seal[0] != sha(ballot):
            raise ValueError(f"{rater} ballot seal mismatch")
        packet = blob(f"packet-{rater}.json")
        if sha(packet) != manifest["readers"][rater]["packet_sha256"]:
            raise ValueError(f"{rater} packet was changed")
        packets[rater] = indexed(parse(packet))
        rows = indexed([parse(line) for line in ballot.splitlines() if line.strip()])
        expected = 24 if rater == "welt" else 72
        if (rows.keys() != packets[rater].keys() or len(rows) != expected
                or manifest["readers"][rater]["items"] != expected):
            raise ValueError(f"{rater} ballot coverage differs from the frozen packet")
        for row in rows.values():
            if rater == "welt":
                most, least = row["most"], row["least"]
                options = {"X", "Y", "Z", "none"}
                if most not in options or least not in options or (most == least and most != "none"):
                    raise ValueError(f"invalid preference in {row['id']}")
            else:
                if row["adapter_guess"] not in {"A", "B", "C", "none"}:
                    raise ValueError(f"invalid guess in {row['id']}")
                for label in MODEL_LABELS:
                    mark = row[label]
                    if mark["mark"] not in ("E", "C", "R", "P"):
                        raise ValueError(f"invalid mark in {row['id']}")
                    if mark["mark"] in ("E", "C") and (mark.get("weight") not in ("minor","substantive")
                            or not all(isinstance(mark.get(k), str) and mark[k].strip() for k in ("source_words","rewrite_words"))):
                        raise ValueError(f"defect missing weight or evidence in {row['id']}")
        ballots[rater], seals[rater] = rows, seal[0]
    return ballots, packets, seals, waiting


def align(ballots, packets, key_for):
    """After all seals pass, join the independent shuffles to the declared cases."""
    cases = {}
    for rater in READERS:
        model_reader = rater != "welt"
        key = key_for(rater)
        if key.keys() != ballots[rater].keys():
            raise ValueError(f"{rater} key coverage")
        seen = set()
        labels = MODEL_LABELS if model_reader else PREFERENCE_LABELS
        expected_versions = set(VERSIONS if model_reader else ("source","plain1","adapter"))
        for item, row in ballots[rater].items():
            k = key[item]
            case = k["case"]
            if case in seen or {k[x] for x in labels} != expected_versions:
                raise ValueError(f"{rater} duplicate case or invalid version mapping")
            seen.add(case)
            meta = {x:k[x] for x in ("set","group","day")}
            if meta["set"] not in ("development","confirmation") or meta["group"] not in ("ordinary","occasion"):
                raise ValueError("unexpected cohort or group")
            if not model_reader and meta["set"] != "confirmation":
                raise ValueError("preference outside confirmation")
            c = cases.setdefault(case,dict(meta=meta,text={}))
            if c["meta"] != meta:
                raise ValueError("independent keys disagree on case membership")
            packet = packets[rater][item]
            texts = {k[x]:packet[x] for x in labels}
            if model_reader:
                texts["source"] = packet["source"]
            for version, words in texts.items():
                if c["text"].setdefault(version, words) != words:
                    raise ValueError("different text maps to the same version across readers")
            if model_reader:
                c[rater] = dict(marks={k[x]:row[x] for x in labels},guess=k.get(row["adapter_guess"],"none"))
            else:
                c[rater] = {x:k.get(row[x],"none") for x in ("most","least")}
    days = {}
    for case in cases.values():
        meta = case["meta"]
        subset = days.setdefault(meta["day"],meta["set"])
        if subset != meta["set"] or not all(x in case for x in ("sol","claude")) or ("welt" in case) != (subset=="confirmation"):
            raise ValueError("case or day crosses the frozen split")
    counts = Counter(c["meta"]["set"] for c in cases.values())
    byd = Counter(c["meta"]["day"] for c in cases.values())
    if counts != {"development":48,"confirmation":24} or byd != {i:12 for i in range(44,50)}:
        raise ValueError("invalid day or split sizes")
    return cases


def joint_weight(a,b):
    if any(x["mark"] not in ("E","C") for x in (a,b)):
        return None
    return "substantive" if any(x["weight"]=="substantive" for x in (a,b)) else "minor"


def summarize(cases):
    counts = Counter()
    per_case = []
    for name, case in cases.items():
        per_case.append(dict(case=name, **case["meta"], defects={}, guesses={}, readers={}))
        out = per_case[-1]
        counts["items"] += 1
        for r in ("sol","claude"):
            guess = case[r]["guess"]
            out["guesses"][r] = guess
            out["readers"][r] = case[r]["marks"]
            counts[f"{r}_guess_{guess}"] += 1
        for v in VERSIONS:
            w = joint_weight(case["sol"]["marks"][v],case["claude"]["marks"][v])
            out["defects"][v] = w
            if w:
                counts[f"{v}_{w}"] += 1
        for v, words in case["text"].items():
            counts[f"{v}_words"] += len(words.split())
            counts[f"{v}_notions"] += len(DOCTRINE.findall(words))
        if "welt" in case:
            grp = case["meta"]["group"]
            counts[grp] += 1
            out["preference"] = case["welt"]
            for pos,opt in case["welt"].items():
                counts[f"{grp}_{pos}_{opt}"] += 1
    notions = {v:100*counts[f"{v}_notions"]/counts[f"{v}_words"] for v in ("source",*VERSIONS) if counts[f"{v}_words"]}
    return counts, notions, per_case


def bars(c):
    minor_limit = c["plain1_minor"] + abs(c["plain2_minor"] - c["plain1_minor"])
    def bar(observed, limit, outcome):
        return {"observed":observed, "bound":limit, "passed":outcome}
    return {
        "no_joint_substantive":bar(c["adapter_substantive"],0,c["adapter_substantive"]==0),
        "joint_minor_within_plain_band":bar(c["adapter_minor"],minor_limit,c["adapter_minor"]<=minor_limit),
        "occasion_adapter_most":bar(c["occasion_most_adapter"],f">= 2/3 of {c['occasion']}",
                                    3*c["occasion_most_adapter"]>=2*c["occasion"] if c["occasion"] else None),
        "occasion_plain_most_lower":bar(c["occasion_most_plain1"],f"< {c['occasion_most_adapter']}",
                                        c["occasion_most_plain1"]<c["occasion_most_adapter"] if c["occasion"] else None),
        "ordinary_adapter_least":bar(c["ordinary_least_adapter"],f"<= 1/4 of {c['ordinary']}",
                                     4*c["ordinary_least_adapter"]<=c["ordinary"] if c["ordinary"] else None)
    }


def verdict(cases):
    reports = {}
    for which in ("development","confirmation"):
        cohort = {k:c for k,c in cases.items() if c["meta"]["set"]==which}
        counts, notions, per_case = summarize(cohort)
        instructions = {}
        for era in ("old","new"):
            sub = {k:c for k,c in cohort.items() if (c["meta"]["day"]<48)==(era=="old")}
            detail, vocab, _ = summarize(sub)
            instructions[era] = {"counts":detail,"notions_per_100_words":vocab}
        reports[which] = dict(counts=counts,notions_per_100_words=notions,cases=per_case,by_instructions=instructions)
    gates = bars(reports["confirmation"]["counts"])
    states = [g["passed"] for g in gates.values()]
    status = "FAIL" if False in states else "UNDETERMINED" if None in states else "PASS"
    return {"status":status,"bars":gates,"sets":reports,"training_eligible":False}


def evaluate(main_ref, key_dir=None):
    commit, manifest, files, blob = git_inputs(main_ref)
    ballots, packets, seals, waiting = sealed_ballots(files,blob,manifest)
    meta = dict(main=commit,seals=seals,missing=waiting,training_eligible=False)
    if waiting or key_dir is None:
        return dict(meta,status="AWAITING_BALLOTS" if waiting else "READY_FOR_KEYS")
    def key_for(rater):
        data = (key_dir/f"key-{rater}.json").read_bytes()
        if sha(data)!=manifest["readers"][rater]["key_sha256"]:
            raise ValueError(f"{rater} key hash differs from the original registration")
        return parse(data)
    return dict(meta, **{k:v for k,v in verdict(align(ballots,packets,key_for)).items() if k not in meta})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-ref", required=True)
    parser.add_argument("--keys", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.keys and not args.out:
        parser.error("provide a new --out file to preserve an unblinded verdict")
    result = evaluate(args.main_ref,args.keys)
    if args.out and result["status"] in ("PASS", "FAIL", "UNDETERMINED"):
        with args.out.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2)
            f.write("\n")
    print(json.dumps({k:result[k] for k in ("main","status","missing","seals")}))
