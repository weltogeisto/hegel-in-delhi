#!/usr/bin/env python3
"""World health: what the world gave him to live through on each full day. No model call.

    python3 tools/world_health.py --ref origin/shadow            # the day files of a branch
    python3 tools/world_health.py --days docs/days [--json OUT]  # or of a folder

The day report (world/report.py) says how the mind did. This says how the world did (WORLD-2.md): of the moments he
decided with a mind, how many opened with

  answered   the reply to what he had just said, and nothing else from the world;
  empty      "Nothing in particular happens.";
  brought    something he did not start: a beat of a storyline or an offer, the morning papers, the day's listings,
             a letter, a person he has not met, a person who speaks first, a power cut, rain, bad air;
  routine    the rest: arriving, a closing hour, a meal laid out, hunger.

Beside them: where he was (the share at home, the entropy of his places in bits), the people who spoke, what he did,
and how many notions of his system his thoughts carry per 100 words (tools.prompt_screen.DOCTRINE; his travel letters
have 0.17, tools/travel_register.py). A day counts when it has at least world.report.FLOOR thoughts, as in T10.

Limits. The labels are read from the event's words, so a gallery or a part of a performance (HEGEL_CULTURE), which
carry no fixed words, count as routine until the step record names what opened it. A greeting and a reply in one
moment count once, as brought.

A read, never a gate: it names no target and no pass. Evaluation only.
"""
import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.prompt_screen import DOCTRINE  # noqa: E402
from world.report import FLOOR  # noqa: E402
from world.voices import heard  # noqa: E402

MINDS = ("mind", "stub")
EMPTY = "Nothing in particular happens."
SPEAKS = " says: “"
# What the world brings of its own, by the words world.situation() and world.post use for it.
BROUGHT = re.compile(r"Headlines: |Today's listings: |Open today: |Tonight here: |you have not met\.|The power goes\."
                     r"|It begins to rain\.|Heavy rain begins\.|The air is very poor today|brings the post: |The post has come: ")
DAY_FILE = re.compile(r"\d{4}-\d{2}-\d{2}\.json$")


def entropy(counts):
    """Shannon entropy in bits: 0 when he was in one place all day."""
    n = sum(counts.values())
    return -sum(c / n * math.log2(c / n) for c in counts.values() if c) if n else 0.0


def opening(step, prev):
    """How this moment opened: brought, answered, empty or routine. One label a step; what the world brings comes first."""
    event = step.get("event") or ""
    reply = heard(prev["voice"]) if prev and prev.get("voice") and prev.get("end") == step.get("t") and not prev.get("left") else None
    others = event.count(SPEAKS) - (1 if reply and reply in event else 0)       # a person who speaks first is not his echo
    if step.get("beat") or BROUGHT.search(event) or others > 0:
        return "brought"
    if reply and reply in event:
        return "answered"
    return "empty" if EMPTY in event else "routine"


def row(day):
    """One day's read, or None when the day has fewer than FLOOR thoughts."""
    decided = [s for s in day.get("steps") or [] if "decision" in s]
    steps = [(s, decided[i - 1] if i else None) for i, s in enumerate(decided)
             if (s.get("mind") or {}).get("source") in MINDS and s["decision"].get("thought")]
    if len(steps) < FLOOR:
        return None
    n = len(steps)
    opens = Counter(opening(s, prev) for s, prev in steps)
    places = Counter(s["decision"]["place"] for s, _ in steps)
    acts = Counter(s["decision"]["action"] for s, _ in steps)
    text = " ".join(s["decision"]["thought"] for s, _ in steps)
    words = len(re.findall(r"\w+", text))
    said = {e["by"] for e in day.get("entries") or [] if e.get("k") == "said" and e.get("by")}
    return {"n": day.get("n"), "date": day["date"], "moments": n,
            "opens": {k: opens.get(k, 0) for k in ("answered", "empty", "brought", "routine")},
            "home": places.get("home", 0), "places": len(places), "place_bits": round(entropy(places), 2),
            "voices": len(said), "acts": dict(sorted(acts.items())),
            "words": words, "doctrine": len(DOCTRINE.findall(text)),
            "cash": (day.get("state") or {}).get("imprest")}


def pooled(rows):
    """All counted days together: shares of moments, and the doctrine rate over all words."""
    n = sum(r["moments"] for r in rows)
    if not n:
        return {"days": 0, "moments": 0}
    acts = Counter()
    for r in rows:
        acts.update(r["acts"])
    share = lambda x: round(x / n, 3)
    return {"days": len(rows), "moments": n,
            "opens": {k: share(sum(r["opens"][k] for r in rows)) for k in ("answered", "empty", "brought", "routine")},
            "brought_per_day": round(sum(r["opens"]["brought"] for r in rows) / len(rows), 1),
            "home": share(sum(r["home"] for r in rows)),
            "place_bits": round(sum(r["place_bits"] for r in rows) / len(rows), 2),
            "voices_per_day": round(sum(r["voices"] for r in rows) / len(rows), 1),
            "acts": {k: share(v) for k, v in sorted(acts.items(), key=lambda kv: -kv[1])},
            "doctrine_per_100_words": round(100 * sum(r["doctrine"] for r in rows) / max(1, sum(r["words"] for r in rows)), 2)}


def pct(x, n):
    return f"{100 * x / n:.0f}%"


def table(rows):
    out = ["| Day | Date | Moments | Answered | Empty | Brought | At home | Places | Bits | Voices | Doctrine /100 words | Cash |",
           "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        n, o = r["moments"], r["opens"]
        cash = "–" if r["cash"] is None else f"₹{r['cash']:,}"
        out.append(f"| {r['n']} | {r['date']} | {n} | {pct(o['answered'], n)} | {pct(o['empty'], n)} | {o['brought']} | {pct(r['home'], n)} | "
                   f"{r['places']} | {r['place_bits']:.2f} | {r['voices']} | {100 * r['doctrine'] / max(1, r['words']):.2f} | {cash} |")
    return "\n".join(out)


def days_of_folder(folder):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(folder).iterdir()) if DAY_FILE.match(p.name)]


def days_of_ref(ref, repo):
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout
    names = [x for x in git("ls-tree", "--name-only", ref, "docs/days/").split() if DAY_FILE.search(x)]
    return [json.loads(git("show", f"{ref}:{name}")) for name in sorted(names)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--ref", help="a git ref whose docs/days to read, e.g. origin/shadow")
    src.add_argument("--days", type=Path, help="a folder of day files")
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--json", type=Path, help="also write the rows and the pooled read here")
    args = ap.parse_args(argv)
    days = days_of_ref(args.ref, args.repo) if args.ref else days_of_folder(args.days)
    rows = [r for r in map(row, days) if r]
    read = {"source": args.ref or str(args.days), "floor": FLOOR, "days_read": len(days), "rows": rows, "pooled": pooled(rows)}
    print(f"{len(rows)} of {len(days)} days have at least {FLOOR} thoughts.\n")
    print(table(rows))
    print("\nPooled: " + json.dumps(read["pooled"], ensure_ascii=False))
    if args.json:
        args.json.write_text(json.dumps(read, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
