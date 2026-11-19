"""The adapter on his recent thoughts: freeze the draw, then run the rewrites. Declared in pc/LORA-FRESH-SCENES.md.

  freeze   read day files (a git ref or a folder), draw twelve thoughts a day, write a plan with its sha256.
  run      check the plan's hash and the adapter, then make three rewrites of every thought through world.restyle:
           "adapter" (scale 1.0), "plain1" (scale 0.0), "plain2" (scale 0.0, another seed).

Evaluation only. No model is called by freeze. run calls only the server it is given, and only on the PC, on Welt's word.
"""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import random
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.recorded_llama import RecordedClient, TransportError, json_bytes
from world import health, restyle

REPO = Path(__file__).resolve().parents[1]
DECLARED = "pc/LORA-FRESH-SCENES.md"
SEED = 1831
PER_DAY = 12
ORDINARY_MAX = 6
MIN_WORDS = 40
NEW_FROM = 48          # days from here on ran on the new instructions; the days before ran on the old
VERSIONS = (("adapter", 1.0, 0), ("plain1", 0.0, 0), ("plain2", 0.0, 1000))   # name, scale, seed offset


def canonical(value):
    """The bytes the plan's hash is taken over: sorted keys, no spaces."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def plan_hash(plan):
    return hashlib.sha256(canonical({k: v for k, v in plan.items() if k != "sha256"})).hexdigest()


def parse_days(text):
    """'44-49' or '44,46,48' as a sorted list of day numbers."""
    out = set()
    for part in text.split(","):
        lo, _, hi = part.strip().partition("-")
        out.update(range(int(lo), int(hi or lo) + 1))
    return sorted(out)


# ---- reading the days -------------------------------------------------------------------------------------------

def _git_show(ref, path):
    r = subprocess.run(["git", "show", ref + ":" + path], cwd=REPO, capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def load_days(numbers, ref=None, docs=None):
    """{n: day} for the asked day numbers. The number is the day file's `n`, listed with its date in docs/days/index.json."""
    found = {}
    if docs is not None:
        for path in sorted(Path(docs).glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict) and value.get("n") in numbers:
                found[value["n"]] = value
    else:
        index = _git_show(ref, "docs/days/index.json")
        if not index:
            raise SystemExit("freeze: no docs/days/index.json on " + ref)
        for entry in index["days"]:
            if entry["n"] in numbers:
                day = _git_show(ref, "docs/days/" + entry["date"] + ".json")
                if day is not None:
                    found[entry["n"]] = day
    missing = [n for n in numbers if n not in found]
    if missing:
        raise SystemExit("freeze: no day file for day " + ", ".join(map(str, missing)))
    return found


# ---- the candidates ---------------------------------------------------------------------------------------------

def candidates(day):
    """The day's candidate thoughts in step order: a thought of at least MIN_WORDS words, the first of any repeated text.

    Each is {step, time, thought, words, group, kinds}. The group is world.health's: an occasion when the moment opened
    as brought (the world brought something, a person spoke first) or answered (a reply, a letter read), else ordinary.
    `opened` is read where the step has it; health.opening and brought_kinds read the event's words where it does not."""
    prev, seen, out = None, set(), []
    for index, step in enumerate(day.get("steps") or []):
        if "decision" not in step:
            continue
        before, prev = prev, step
        thought = step["decision"].get("thought")
        if not isinstance(thought, str) or len(thought.split()) < MIN_WORDS or thought in seen:
            continue
        seen.add(thought)
        opening = health.opening(step, before)
        kinds = health.brought_kinds(step, before)
        if opening == "answered":
            opened = health._opened(step)
            kinds = kinds + [x for x in (opened if opened is not None else ["reply"]) if health._kind(x) in health.ANSWERED_KINDS]
        row = {"step": index, "thought": thought, "words": len(thought.split()),
               "group": "occasion" if opening in ("brought", "answered") else "ordinary", "kinds": kinds}
        if step.get("t"):
            row["time"] = step["t"]
        out.append(row)
    return out


def check_day(day, n):
    if not day.get("complete"):
        raise SystemExit("freeze: day " + str(n) + " is not marked complete")
    if not any(isinstance(s.get("decision"), dict) and s["decision"].get("thought") for s in day.get("steps") or []):
        raise SystemExit("freeze: day " + str(n) + " has no thoughts")


def draw(rows, seed, day_number):
    """Twelve of a day's candidates. Up to six ordinary, the rest occasions; occasions fill when ordinary are short,
    ordinary fill when occasions are. The generator is random.Random(seed * 1000 + day), the pools in step order."""
    rng = random.Random(seed * 1000 + day_number)
    ordinary = [r for r in rows if r["group"] == "ordinary"]
    occasion = [r for r in rows if r["group"] == "occasion"]
    n_ord = min(ORDINARY_MAX, len(ordinary))
    n_occ = PER_DAY - n_ord
    if len(occasion) < n_occ:
        n_occ = len(occasion)
        n_ord = PER_DAY - n_occ
    if n_ord > len(ordinary) or len(rows) < PER_DAY:
        raise SystemExit("freeze: day " + str(day_number) + " has " + str(len(rows)) + " candidates, cannot give " + str(PER_DAY))
    return sorted(rng.sample(ordinary, n_ord) + rng.sample(occasion, n_occ), key=lambda r: r["step"])


def held_back(numbers, seed):
    """One day from those present before NEW_FROM and one from those present from it, by random.Random(seed)."""
    rng = random.Random(seed)
    sides = ([n for n in numbers if n < NEW_FROM], [n for n in numbers if n >= NEW_FROM])
    return [rng.choice(side) for side in sides if side]


def freeze(days, ref, commit, seed=SEED):
    """The plan for the loaded days: {n: day}. Raises SystemExit when a day is incomplete, without thoughts or too thin."""
    numbers = sorted(days)
    for n in numbers:
        check_day(days[n], n)
    held = held_back(numbers, seed)
    cases, table = [], []
    for n in numbers:
        rows = candidates(days[n])
        drawn = draw(rows, seed, n)
        table.append({"day": n, "candidates": len(rows), "ordinary": sum(r["group"] == "ordinary" for r in drawn),
                      "occasion": sum(r["group"] == "occasion" for r in drawn),
                      "set": "confirmation" if n in held else "development"})
        for r in drawn:
            case = {"i": len(cases), "id": "D%d-S%02d" % (n, r["step"]), "day": n, "date": days[n]["date"], "step": r["step"]}
            if "time" in r:
                case["time"] = r["time"]
            case.update(group=r["group"], kinds=r["kinds"], set=table[-1]["set"], words=r["words"], thought=r["thought"])
            cases.append(case)
    plan = {"declared": DECLARED, "ref": ref, "commit": commit, "seed": seed, "held_back": held, "cases": cases}
    plan["sha256"] = plan_hash(plan)
    return plan, table


def format_table(table):
    lines = ["day  candidates  ordinary  occasion  set"]
    lines += ["%3d  %10d  %8d  %8d  %s" % (t["day"], t["candidates"], t["ordinary"], t["occasion"], t["set"]) for t in table]
    return "\n".join(lines)


# ---- the run ----------------------------------------------------------------------------------------------------

def load_plan(path):
    """The plan, after its hash is checked."""
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if plan.get("sha256") != plan_hash(plan):
        raise SystemExit("run: the plan's sha256 does not match its contents; it was changed after it was frozen")
    return plan


def probe_adapter(url, lora_id):
    """GET <url>/lora-adapters and refuse when no adapter with this id is listed. Tests replace this."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/lora-adapters", timeout=30) as response:
            listed = json.loads(response.read())
    except (OSError, ValueError) as e:
        raise SystemExit("run: could not read " + url + "/lora-adapters: " + str(e))
    if not isinstance(listed, list) or not any(isinstance(a, dict) and a.get("id") == lora_id for a in listed):
        raise SystemExit("run: the server lists no adapter with id " + str(lora_id))
    return listed


class SceneClient(RecordedClient):
    """RecordedClient whose chat requests also say cache_prompt false, as the lora field is said: in the payload."""
    def chat(self, request_id, messages, temperature, tokens, seed):
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": tokens,
                   "seed": seed, "chat_template_kwargs": {"enable_thinking": False}, "cache_prompt": False}
        result = self.post(request_id, payload)
        try:
            choice = result["choices"][0]
            text = choice["message"].get("content")
            if not isinstance(text, str):
                raise ValueError("chat content is not text")
            return text, choice.get("finish_reason")
        except (KeyError, IndexError, TypeError, AttributeError, ValueError) as e:
            raise TransportError("saved HTTP response has no chat choice") from e


def real_client(url, root, lora_id, scale):
    return SceneClient(url, root, 600, lora=[{"id": lora_id, "scale": scale}])


def real_guard():
    from world import shelf
    return restyle.ShelfGuard.from_shelf(shelf.load(REPO / "mind/shelf/index.json.gz"))


def seconds_of(client, request_id):
    """The recorded wall time of a request, 0.0 when the client keeps none."""
    try:
        stem = client.stem(request_id)
        return float(json.loads(Path(str(stem) + ".done.json").read_text(encoding="utf-8"))["seconds"])
    except (AttributeError, OSError, ValueError, KeyError):
        return 0.0


def rewrite(client, guard, case, version, scale, seed):
    """One guarded rewrite with the procedure of 6 November: two asks at most, the attempt added to the seed."""
    plain = case["thought"]
    tokens = math.ceil(2.5 * case["words"])

    def fetch(messages, attempt):
        rid = "scene/" + case["id"] + "/" + version + "/ask" + str(attempt + 1)
        raw, finish = client.chat(rid, messages, 0.9, tokens, seed + attempt)
        return {"text": raw, "finish_reason": finish, "seconds": seconds_of(client, rid)}
    return restyle.guarded_restyle(plain, fetch, guard)


def existing(path):
    done = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done[(row["i"], row["version"])] = row
    return done


def run(plan, url, out, lora_id=0, limit=None, probe=probe_adapter, client_factory=real_client, guard=None):
    """Make the rewrites. Skips every case/version already in outputs.jsonl; never rewrites a line of it."""
    probe(url, lora_id)
    guard = guard or real_guard()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    clients = {}
    for _, scale, _ in VERSIONS:
        if scale not in clients:
            clients[scale] = client_factory(url, out / "raw", lora_id, scale)
    outputs = out / "outputs.jsonl"
    done = existing(outputs)
    run_file = out / "RUN.json"
    started = json.loads(run_file.read_text(encoding="utf-8"))["started"] if run_file.exists() else datetime.now(timezone.utc).isoformat()
    cases = plan["cases"][:limit] if limit is not None else plan["cases"]
    made = 0
    with outputs.open("a", encoding="utf-8") as f:
        for case in cases:
            for version, scale, offset in VERSIONS:
                if (case["i"], version) in done:
                    continue
                seed = SEED + offset + 17 * case["i"]
                result = rewrite(clients[scale], guard, case, version, scale, seed)
                row = {"i": case["i"], "id": case["id"], "version": version, "scale": scale, "seed": seed,
                       "output": result["text"], "fallback": result["fallback"], "attempts": len(result["attempts"])}
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                f.flush()
                done[(case["i"], version)] = row
                made += 1
    data = outputs.read_bytes() if outputs.exists() else b""
    fallbacks = {v: sum(1 for (i, ver), r in done.items() if ver == v and r["fallback"]) for v, _, _ in VERSIONS}
    summary = {"plan_sha256": plan["sha256"], "url": url, "lora_id": lora_id, "started": started,
               "finished": datetime.now(timezone.utc).isoformat(), "cases": len(plan["cases"]), "cases_asked": len(cases),
               "outputs": len(done), "made_this_run": made, "fallbacks": fallbacks,
               "outputs_sha256": hashlib.sha256(data).hexdigest()}
    run_file.write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return summary


# ---- command line -----------------------------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze", help="draw the thoughts and write the plan")
    f.add_argument("--ref", default="origin/shadow")
    f.add_argument("--docs", type=Path, help="read day files from this folder instead of the ref")
    f.add_argument("--days", required=True, help="e.g. 44-49")
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--seed", type=int, default=SEED)
    r = sub.add_parser("run", help="make the three rewrites of every thought")
    r.add_argument("--plan", type=Path, required=True)
    r.add_argument("--url", required=True)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--lora-id", type=int, default=0)
    r.add_argument("--limit", type=int)
    a = p.parse_args(argv)
    if a.command == "freeze":
        days = load_days(parse_days(a.days), a.ref, a.docs)
        if a.docs is not None:
            ref, commit = "docs:" + str(a.docs), None
        else:
            ref = a.ref
            commit = subprocess.run(["git", "rev-parse", a.ref], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        plan, table = freeze(days, ref, commit, a.seed)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_bytes(json_bytes(plan))
        print(format_table(table))
        print("held back: " + ", ".join(map(str, plan["held_back"])) + "  cases: " + str(len(plan["cases"])) + "  sha256: " + plan["sha256"])
    else:
        summary = run(load_plan(a.plan), a.url, a.out, a.lora_id, a.limit)
        print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
