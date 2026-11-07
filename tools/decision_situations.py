#!/usr/bin/env python3
"""Freeze Training 3's shadow situations without using a later step as input.

A native, first-parent Git snapshot supplies each decision's exact before-state.
The event, people and shelf actually shown at that decision supply its observations.
This is a documented reconstruction, not a claim that historical HTTP bytes exist.
"""
import argparse
import copy
import functools
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from world import contract, engine, shelf
from world.memory import Memory, encountered_text
from world.world import World
from tools.decision_sampler import TEST_DAYS, digest, json_bytes, save, situation_record

# Owner approved before any sampling: exact native before-state or exclusion.
PROVENANCE_EXCLUSIONS = frozenset((
    "shadow:25:26", "shadow:26:1", "shadow:36:4", "shadow:36:6", "shadow:36:7",
    "shadow:37:4", "shadow:37:5", "shadow:37:8", "shadow:37:9",
))
PROVENANCE_DECISION = "https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6704597355"
DAY_FILE = re.compile(r"\d{4}-\d{2}-\d{2}\.json$")


class SnapshotGit:
    def __init__(self, repo, head):
        self.repo = str(Path(repo).resolve())
        self.head = self.run("rev-parse", head + "^{commit}").decode().strip()
        if self.head != head:
            raise ValueError("use an exact frozen commit, not a moving ref")

    def run(self, *args):
        return subprocess.check_output(["git", "-C", self.repo, *args],
                                       stderr=subprocess.PIPE, timeout=30)

    @functools.lru_cache(maxsize=4000)
    def blob(self, sha):
        return self.run("cat-file", "blob", sha)

    def days(self, commit, before=None):
        rows = self.run("ls-tree", commit + ":docs/days").decode().splitlines()
        result = {}
        for row in rows:
            meta, name = row.split("\t")
            if DAY_FILE.fullmatch(name) and (before is None or name[:-5] < before):
                raw = self.blob(meta.split()[2])
                value = json.loads(raw)
                if value["date"] != name[:-5]:
                    raise ValueError("day filename/date mismatch")
                result[name[:-5]] = (value, raw, meta.split()[2])
        return result

    def before_steps(self, day):
        name = "docs/days/" + day["date"] + ".json"
        commits = self.run("log", "--first-parent", "--reverse", "--format=%H",
                           self.head, "--", name).decode().split()
        found = {}
        for commit in commits:
            parents = self.run("rev-list", "--parents", "-n", "1", commit).decode().split()
            if len(parents) != 2:
                # No exact direct-parent state: do not invent one.
                continue
            parent = parents[1]
            old = subprocess.run(["git", "-C", self.repo, "show", parent + ":" + name],
                                 capture_output=True, timeout=30)
            if old.returncode:
                continue
            before = json.loads(old.stdout)
            after = json.loads(self.run("show", commit + ":" + name))
            n = len(before["steps"])
            if len(after["steps"]) == n:
                continue
            if (len(after["steps"]) <= n or before["steps"] != day["steps"][:n]
                    or after["steps"] != day["steps"][:len(after["steps"])] or n in found):
                raise ValueError("nonlinear or ambiguous day history")
            # A batch proves the state before its first row only. Never infer
            # intermediate state from the batch's final state.
            found[n] = (before, old.stdout, parent, commit)
        return found


class HistoricalMemory(Memory):
    def __init__(self, world, past):
        super().__init__(None, world)
        self.past = past

    def load(self, when):
        return self.past.get(when.isoformat())

    def known_before(self, when):
        return "\n".join(encountered_text(self.past[k])
                         for k in sorted(self.past) if k < when)


def project(world, soul, day, index, prefix, past, provenance):
    step = day["steps"][index]
    if day["n"] in TEST_DAYS or (step.get("mind") or {}).get("source") != "mind":
        raise ValueError("only non-held shadow mind decisions may enter")
    if prefix["steps"] != day["steps"][:index]:
        raise ValueError("before-state is not the exact earlier prefix")
    work = copy.deepcopy(prefix)
    state = work["state"]
    when = engine.at_dt(date.fromisoformat(day["date"]), engine.hm(step["t"]))
    # These are observations from this decision, not a future action or result.
    world._wx[when.date()] = copy.deepcopy(prefix.get("weather") or day["weather"])
    if not work.get("plan") and day.get("plan") and day["plan"]["written"] == step["t"]:
        work["plan"] = copy.deepcopy(day["plan"])
    previous = next((s for s in reversed(work["steps"]) if s.get("decision")), None)
    sit, ctx = world.situation(when, state, work, previous)
    ids = {world.short(k): k for k in world.cast}
    sit["event"], sit["present"] = step["event"], step["present"]
    ctx["present"] = [ids[name] for name in step["present"]]
    sit["speakers"] = [dict(id=k, name=world.short(k)) for k in ctx["present"]]
    memory = HistoricalMemory(world, past)
    sit["remember"] = memory.recall(sit, ctx, work)
    sit["shelf"] = [{**x, "label": shelf.label(x["work"], x["ref"])}
                    for x in step.get("shelf_exposure", [])]
    ctx["recent"] = memory.recent_thoughts(work)
    ctx["known_text"] = memory.known_text(work, sit)
    if sit["shelf"]:
        ctx["known_text"] += "\n" + "\n".join(x["text"] for x in sit["shelf"])
    earlier = [s["decision"]["thought"] for s in prefix["steps"]
               if s.get("decision") and s["decision"].get("thought")]
    messages = [dict(role="system", content=soul),
                dict(role="user", content=contract.render(sit))]
    return situation_record("shadow", day["n"], index, day["date"], messages,
                            earlier, sit, ctx, state, provenance)


def freeze(repo, head, soul_file, output, expected_count=109):
    output = Path(output)
    if output.exists():
        raise FileExistsError("use a new freeze directory; preserve the old one")
    git = SnapshotGit(repo, head)
    world = World()
    soul_raw = Path(soul_file).read_bytes()
    soul = soul_raw.decode("utf-8")
    records, objects = [], {}
    days = git.days(head)
    for day_date in sorted(days):
        day, day_raw, _ = days[day_date]
        if day["n"] in TEST_DAYS:
            continue
        wanted = [i for i, step in enumerate(day.get("steps", []))
                  if (step.get("mind") or {}).get("source") == "mind"]
        if not wanted:
            continue
        before = git.before_steps(day)
        for index in wanted:
            ident = f"shadow:{day['n']}:{index}"
            if ident in PROVENANCE_EXCLUSIONS:
                if index in before:
                    raise ValueError("excluded situation unexpectedly acquired a before-state; review the frozen roster")
                continue
            if index not in before:
                raise ValueError(f"no exact parent snapshot for day {day['n']} step {index}")
            prefix, raw, parent, child = before[index]
            history = git.days(parent, before=day_date)
            references = {}
            for key, (_, prior_raw, _) in history.items():
                h = digest(prior_raw)
                objects[h] = prior_raw
                references[key] = h
            objects[digest(raw)] = raw
            provenance = dict(kind="T39-style exact-parent reconstruction",
                              frozen_shadow=head, parent=parent, child=child,
                              before_sha256=digest(raw), prior_days=references,
                              observed_day_sha256=digest(day_raw))
            row = project(world, soul, day, index, prefix,
                          {k: v[0] for k, v in history.items()}, provenance)
            records.append(row)
        objects[digest(day_raw)] = day_raw
    if len(records) != expected_count:
        raise ValueError(f"expected {expected_count} shadow situations, found {len(records)}")
    roster = [row["id"] for row in records]
    roster_bytes = json_bytes(roster)
    output.mkdir(parents=True, exist_ok=False)
    from tools.decision_sampler import write_new
    for sha, raw in objects.items():
        write_new(output / "objects" / sha, raw)
    write_new(output / "objects" / digest(soul_raw), soul_raw)
    write_new(output / "SHADOW-IDS.json", roster_bytes)
    manifest = dict(version=1, head=head, situations=len(records), test_days_excluded=sorted(TEST_DAYS),
                    soul_sha256=digest(soul_raw), roster_sha256=digest(roster_bytes),
                    provenance_decision=PROVENANCE_DECISION,
                    excluded_for_missing_before_state=sorted(PROVENANCE_EXCLUSIONS), rows=[])
    for row in records:
        raw = json_bytes(row)
        name = digest(row["id"].encode()) + ".json"
        save(output / "situations" / name, row)
        manifest["rows"].append(dict(id=row["id"], path="situations/" + name, sha256=digest(raw)))
    save(output / "MANIFEST.json", manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--shadow", required=True, help="exact native shadow commit")
    parser.add_argument("--soul", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=109)
    args = parser.parse_args(argv)
    result = freeze(args.repo, args.shadow, args.soul, args.out, args.expected_count)
    print(json.dumps({k: result[k] for k in ("head", "situations", "test_days_excluded")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
