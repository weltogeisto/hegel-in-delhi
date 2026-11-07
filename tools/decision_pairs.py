#!/usr/bin/env python3
"""Training 3: preference pairs for his decisions, labelled by the world's own checks.

Input: one JSON row per situation, written by Astra's sampler (tools/decision_sampler.py):
    {"id": "shadow:35:17", "source": "shadow" | "rehearsal", "day": 35, "step": 17, "date": "2026-11-05",
     "messages": [system, user],           # the exact prompt the candidates were sampled from
     "earlier_thoughts": ["...", ...],     # that day's thoughts before this step, from the record
     "candidates": [{"seed": 1831, "raw": "...", "answer": {...} or null, "finish_reason": "stop",
                     "accepted": true, "errors": [...], "warnings": [...]}, ...]}   # seeds 1831, 2718, 3141, 4271

Every candidate comes from plain Qwen; World.check (the rules, the 1831 gate, the repetition guard) decides
"accepted". Nobody's taste enters: no text here is written or chosen by Claude or any other model.

Two views. Training 3 trains on the revised one only (Welt, 7 November; pc/HEGEL-IMPLEMENTATION-MANUAL.md §7.3-7.5).

revised: judged on what the exact prompt shows him
    clean      accepted, complete, with a thought, and no loop. Shared phrases are allowed: recurrence is no fault.
    loop       accepted, but he goes round where nothing new happened: the thought shares a four-word phrase
               (report.grams) with a thought shown under "Earlier today", repeats that step's action at that step's
               place, and the event is the quiet default ("Nothing in particular happens").
    refused    refused for a reason his prompt lets him avoid: the contract, the 1831 gate, money, tickets, or
               repeating a thought the prompt shows.
    hidden     refused only for what the prompt does not show: a place that is closed on arrival, or a repeat of a
               thought that is no longer shown. Never paired; the adapter cannot learn it from its input.
    truncated  the reply hit the token limit. Never paired.
    invalid    no parsable answer, or no thought. Never paired.
    One pair per situation: the first clean candidate in seed order that has a loop or refused partner whose thought
    is within 20% of its length in words; partners are tried in seed order. Every clean candidate gets its turn.

legacy: the rule of 6 November, kept for comparison
    clean      accepted, a thought, and no phrase shared with any of the day's earlier thoughts (T9's rule)
    repeating  accepted, but it reuses such a phrase
    refused    the world refused it
    invalid    no parsable answer
    One pair per situation: the first clean candidate in seed order against the first repeating or refused one
    whose thought is within 20% of its length.

Length matching keeps the adapter from learning that shorter, or silent, is better (report p. 10). The revised stats
also count, as diagnostics only, the clean candidates that share a phrase with the whole day or with what is shown,
and report the legacy view's yield beside their own.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world import contract  # noqa: E402
from world.report import grams  # noqa: E402

TEST_DAYS = frozenset({12, 27})   # T39's frozen shadow days
SEEDS = (1831, 2718, 3141, 4271)
FIRST_REHEARSAL = "2026-11-10"     # new rehearsals only; T9's rehearsal days come before
LENGTH_RATIO = 0.8
VIEWS = ("revised", "legacy")
RULE_VERSION = {"revised": "training3-labels-2 (7 November)", "legacy": "training3-labels-1 (6 November)"}
RULE = {"revised": "first clean (accepted, no loop) vs a loop or a refusal the prompt shows how to avoid; "
                   "within 20% length, seed order",
        "legacy": "one pair per situation; first clean vs first repeating or refused within 20% length, seed order"}
QUIET = "Nothing in particular happens"
SHOWN_STEP = re.compile(r"- (\d{2}:\d{2}) recorded step: (\S+) \(([^)]*)\)")
SHOWN_THOUGHT = re.compile(r"; you thought: “(.*)”$")
REPEAT_ERROR = re.compile(r"this repeats what you thought at (\d{2}:\d{2})")
CLOSED_ON_ARRIVAL = re.compile(r" opens at \d{1,2}:\d{2}; walking there you would arrive| is closed when you would arrive")


def thought_of(candidate):
    answer = candidate.get("answer")
    if isinstance(answer, dict) and isinstance(answer.get("thought"), str) and answer["thought"].strip():
        return answer["thought"]
    return None


def words(text):
    return len(text.split())


def length_matched(a, b, ratio=LENGTH_RATIO):
    x, y = words(a), words(b)
    return min(x, y) / max(x, y) >= ratio if x and y else False


# ── the legacy view ──────────────────────────────────────────────────

def label(candidate, earlier):
    thought = thought_of(candidate)
    if thought is None and not isinstance(candidate.get("answer"), dict):
        return "invalid"
    if not candidate.get("accepted"):
        return "refused"
    if thought is None:
        return "refused"          # the world accepted a step without a thought; no use as a chosen example
    seen = set().union(*(grams(t) for t in earlier if t)) if earlier else set()
    return "repeating" if grams(thought) & seen else "clean"


def pair(row):
    """The legacy labels of a situation's candidates, and its one pair (or None)."""
    earlier = row.get("earlier_thoughts") or []
    cands = sorted(row["candidates"], key=lambda c: c["seed"])
    labels = [label(c, earlier) for c in cands]
    chosen = next((c for c, l in zip(cands, labels) if l == "clean"), None)
    if chosen is None:
        return labels, None
    for c, l in zip(cands, labels):
        if l in ("repeating", "refused") and thought_of(c) and length_matched(thought_of(chosen), thought_of(c)):
            return labels, made(row, chosen, c, l, "legacy")
    return labels, None


# ── the revised view: only what the prompt shows ─────────────────────

def shown(messages):
    """The earlier steps the prompt shows under "Earlier today": [(time, action, place, the thought as shown)]."""
    user = messages[-1]["content"] if messages else ""
    if "\nEarlier today:\n" not in user:
        return []
    out = []
    for line in user.split("\nEarlier today:\n", 1)[1].split("\n\n", 1)[0].splitlines():
        step = SHOWN_STEP.match(line)
        said = SHOWN_THOUGHT.search(line.split(" Engine note: ", 1)[0])
        if step and said:
            out.append((step.group(1), step.group(2), step.group(3), said.group(1)))
    return out


def quiet(messages):
    """Does the prompt say that nothing new happens?"""
    user = messages[-1]["content"] if messages else ""
    m = re.search(r"\nWhat happens: (.*)", user)
    return bool(m) and m.group(1).startswith(QUIET)


def error_kind(error, steps):
    m = REPEAT_ERROR.match(error)
    if m:
        return "repeat_shown" if m.group(1) in {t for t, *_ in steps} else "repeat_not_shown"
    if CLOSED_ON_ARRIVAL.search(error):
        return "closed_on_arrival"
    if "in 1831 you could not know it" in error:
        return "1831"
    return "contract"


def visible(errors, steps):
    """Could the prompt have told him to avoid at least one of these refusals?"""
    return any(error_kind(e, steps) not in ("repeat_not_shown", "closed_on_arrival") for e in errors)


def loops(candidate, steps, is_quiet):
    if not is_quiet:
        return False
    answer, said = candidate["answer"], grams(thought_of(candidate))
    return any(said & grams(first) and answer.get("action") == action and answer.get("place") == place
               for _, action, place, first in steps)


def revised_label(candidate, steps, is_quiet):
    if not isinstance(candidate.get("answer"), dict):
        return "invalid"
    if candidate.get("finish_reason") == "length":
        return "truncated"
    if not candidate.get("accepted"):
        return "refused" if visible(candidate.get("errors") or [], steps) else "hidden"
    if thought_of(candidate) is None:
        return "invalid"
    return "loop" if loops(candidate, steps, is_quiet) else "clean"


def revised_pair(row):
    """The revised labels of a situation's candidates, and its one pair (or None)."""
    steps, is_quiet = shown(row["messages"]), quiet(row["messages"])
    cands = sorted(row["candidates"], key=lambda c: c["seed"])
    labels = [revised_label(c, steps, is_quiet) for c in cands]
    partners = [(c, l) for c, l in zip(cands, labels) if l in ("loop", "refused") and thought_of(c)]
    for chosen, l in zip(cands, labels):
        if l != "clean":
            continue
        for c, why in partners:
            if length_matched(thought_of(chosen), thought_of(c)):
                return labels, made(row, chosen, c, why, "revised")
    return labels, None


def made(row, chosen, rejected, why, view):
    return {"id": row["id"], "source": row["source"], "day": row["day"], "step": row["step"],
            "prompt": row["messages"], "chosen": chosen["raw"], "rejected": rejected["raw"],
            "chosen_seed": chosen["seed"], "rejected_seed": rejected["seed"], "rejected_as": why,
            "rejected_errors": rejected.get("errors", []),
            "words": [words(thought_of(chosen)), words(thought_of(rejected))],
            "chars": [len(chosen["raw"]), len(rejected["raw"])],
            "view": view, "rule_version": RULE_VERSION[view]}


# ── checks and the build ─────────────────────────────────────────────

def check_row(row, seen_ids):
    if row["id"] in seen_ids:
        raise ValueError("duplicate situation: " + row["id"])
    if row["source"] not in ("shadow", "rehearsal"):
        raise ValueError("unknown source: " + str(row["source"]))
    if row["source"] == "shadow" and row["day"] in TEST_DAYS:
        raise ValueError("T39's test day may not train: " + row["id"])
    if row["source"] == "rehearsal" and not str(row.get("date") or "") >= FIRST_REHEARSAL:
        raise ValueError("a rehearsal before 10 November (T9's days) may not train: " + row["id"])
    if [m.get("role") for m in row["messages"]] != ["system", "user"]:
        raise ValueError("the one original two-message prompt is required: " + row["id"])
    seeds = [c["seed"] for c in row["candidates"]]
    if len(seeds) != len(set(seeds)) or not seeds:
        raise ValueError("candidates need distinct seeds: " + row["id"])
    if tuple(sorted(seeds)) != SEEDS:
        raise ValueError("the four frozen seeds are required: " + row["id"])
    for c in row["candidates"]:
        if bool(c.get("accepted")) == bool(c.get("errors")):
            raise ValueError(f"accepted and errors disagree: {row['id']} seed {c['seed']}")
        if c.get("answer") != contract.extract_json(c.get("raw") or ""):
            raise ValueError(f"the answer is not the parsed raw reply: {row['id']} seed {c['seed']}")


def build(rows, view="revised"):
    if view not in VIEWS:
        raise ValueError("unknown view: " + str(view))
    pairs, counts, by, seen = [], Counter(), Counter(), set()
    legacy_pairs, legacy_by = 0, Counter()
    overlap, reasons = Counter(), Counter()
    for row in rows:
        check_row(row, seen)
        seen.add(row["id"])
        labels, p = (revised_pair if view == "revised" else pair)(row)
        counts.update(labels)
        if p:
            pairs.append(p)
            by[(p["source"], p["rejected_as"])] += 1
        else:
            counts["situations_without_pair"] += 1
        if view == "revised":
            _, old = pair(row)
            if old:
                legacy_pairs += 1
                legacy_by[(old["source"], old["rejected_as"])] += 1
            steps = shown(row["messages"])
            day = set().union(*(grams(t) for t in row.get("earlier_thoughts") or [] if t))
            on_view = set().union(*(grams(first) for *_, first in steps))
            for c, l in zip(sorted(row["candidates"], key=lambda c: c["seed"]), labels):
                if l == "clean":
                    said = grams(thought_of(c))
                    overlap["clean_sharing_a_phrase_with_the_day"] += bool(said & day)
                    overlap["clean_sharing_a_phrase_with_what_is_shown"] += bool(said & on_view)
                if not c.get("accepted"):
                    reasons.update({error_kind(e, steps) for e in c.get("errors") or []})
    stats = {"situations": len(seen), "pairs": len(pairs), "labels": dict(counts),
             "pairs_by_source_and_reason": {f"{s}/{r}": n for (s, r), n in sorted(by.items())},
             "view": view, "rule_version": RULE_VERSION[view], "rule": RULE[view],
             "test_days_excluded": sorted(TEST_DAYS)}
    if view == "revised":
        stats.update(diagnostics=dict(overlap), refusal_kinds=dict(sorted(reasons.items())),
                     legacy_view={"pairs": legacy_pairs, "rule_version": RULE_VERSION["legacy"],
                                  "pairs_by_source_and_reason": {f"{s}/{r}": n for (s, r), n in sorted(legacy_by.items())}})
    return pairs, stats


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--candidates", type=Path, required=True, help="the sampler's JSONL, one situation per line")
    p.add_argument("--out", type=Path, required=True, help="new JSONL of pairs; a stats file is written beside it")
    p.add_argument("--view", choices=VIEWS, default="revised", help="revised (trains) or legacy (comparison only)")
    a = p.parse_args(argv)
    raw = a.candidates.read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    pairs, stats = build(rows, a.view)
    stats["candidates_sha256"] = hashlib.sha256(raw).hexdigest()
    body = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in pairs).encode()
    stats["pairs_sha256"] = hashlib.sha256(body).hexdigest()
    with a.out.open("xb") as f:
        f.write(body)
    with a.out.with_suffix(".stats.json").open("x") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(stats, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
