#!/usr/bin/env python3
"""Training 3's split rule, training3-split-1 (Claude, 7 November): no training situation carries T39's held days.

T39, and later Training 3's test, run on shadow Days 12 and 27 and on T9's two rehearsal days. No shadow day and
no new rehearsal can recall T9's rehearsal days: they were separate runs whose text never entered the shadow
history. Days 12 and 27 can reach later prompts, because his memory ("You remember") quotes earlier days' thoughts
word for word. A situation is held-related when its prompt's user message shares a run of 12 words with anything
recorded on a held day: the entries' text and titles, and the owl's diary, revision log and Depesche.

The rule reads prompts only, so it is decided before any candidate exists, and results never enter it. Measured on
the 109 shadow situations before sampling: every hit is a "You remember" line quoting Day 12 or 27, and boilerplate
gives none at 12 words (at 8 words every prompt matches). World templates that recur across his whole life are not
a held family; the channel by which a held day reaches a later prompt is memory, and this rule closes it.

    python3 tools/decision_split.py --repo NATIVE_REPO --write      # once, from the frozen shadow commit
    python3 tools/decision_split.py --repo NATIVE_REPO --verify     # the frozen file matches the shadow history
"""
import argparse
import functools
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULE = "training3-split-1"
RUN_WORDS = 12
FROZEN_SHADOW = "45479027d4cba09f60710c02468197801f0a5722"     # the 109-situation freeze's shadow commit
HELD_DAYS = {12: "2026-10-13", 27: "2026-10-28"}
RUNS_FILE = REPO / "pc/training3-held-runs.json"
SHADOW_EXCLUDED_FILE = REPO / "pc/training3-held-related-shadow-ids.json"


def words(text):
    return re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold())


def runs(text):
    w = words(text)
    return {" ".join(w[i:i + RUN_WORDS]) for i in range(len(w) - RUN_WORDS + 1)}


def key(run):
    return hashlib.sha256(run.encode("utf-8")).hexdigest()[:16]


def held_texts(day):
    out = [e[k] for e in day.get("entries", []) for k in ("text", "title") if isinstance(e.get(k), str)]
    owl = day.get("owl") or {}
    out += [owl[k] for k in ("diary", "revision_log") if isinstance(owl.get(k), str)]
    if isinstance(owl.get("depesche"), dict) and isinstance(owl["depesche"].get("text"), str):
        out.append(owl["depesche"]["text"])
    return out


def keys_of(days):
    return sorted({key(r) for day in days for text in held_texts(day) for r in runs(text)})


def body(keys, day_hashes):
    return {"rule": RULE, "run_words": RUN_WORDS, "source_commit": FROZEN_SHADOW,
            "held_days": {str(n): {"date": HELD_DAYS[n], "sha256": day_hashes[n]} for n in sorted(HELD_DAYS)},
            "keys": keys, "keys_sha256": hashlib.sha256("\n".join(keys).encode()).hexdigest()}


@functools.lru_cache(maxsize=1)
def frozen_keys():
    data = json.loads(RUNS_FILE.read_text(encoding="utf-8"))
    if (data.get("rule"), data.get("run_words"), data.get("source_commit")) != (RULE, RUN_WORDS, FROZEN_SHADOW):
        raise ValueError("the held-run file is not training3-split-1")
    if hashlib.sha256("\n".join(data["keys"]).encode()).hexdigest() != data["keys_sha256"]:
        raise ValueError("the held-run file changed")
    return frozenset(data["keys"])


def held_related(user_text, keys=None):
    """Does this prompt's user message carry a held day's text?"""
    keys = frozen_keys() if keys is None else keys
    return any(key(r) in keys for r in runs(user_text or ""))


@functools.lru_cache(maxsize=1)
def frozen_shadow_exclusions():
    data = json.loads(SHADOW_EXCLUDED_FILE.read_text(encoding="utf-8"))
    if data.get("rule") != RULE:
        raise ValueError("the shadow exclusion list is not training3-split-1")
    return tuple(data["ids"])


def from_history(repo):
    days, hashes = [], {}
    for n, date in sorted(HELD_DAYS.items()):
        raw = subprocess.check_output(["git", "-C", str(repo), "show", f"{FROZEN_SHADOW}:docs/days/{date}.json"])
        day = json.loads(raw)
        if day["n"] != n:
            raise ValueError(f"{date} is not Day {n}")
        days.append(day)
        hashes[n] = hashlib.sha256(raw).hexdigest()
    return body(keys_of(days), hashes)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", type=Path, required=True, help="a checkout holding the frozen shadow commit")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--verify", action="store_true")
    a = p.parse_args(argv)
    data = from_history(a.repo)
    raw = (json.dumps(data, indent=1, sort_keys=True) + "\n").encode()
    if a.write:
        with RUNS_FILE.open("xb") as f:
            f.write(raw)
    elif RUNS_FILE.read_bytes() != raw:
        raise SystemExit("the frozen held-run file differs from the shadow history")
    print(json.dumps({k: data[k] for k in ("rule", "run_words", "source_commit", "keys_sha256")} | {"keys": len(data["keys"])}))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    raise SystemExit(main())
