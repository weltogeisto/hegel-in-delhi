#!/usr/bin/env python3
"""World health: what the world gave him to live through on each full day. No model call.

    python3 tools/world_health.py --ref origin/shadow            # the day files of a branch
    python3 tools/world_health.py --days docs/days [--json OUT]  # or of a folder

This is the command line of world/health.py, which holds the read and its limits; the tool adds the doctrine count
(tools.prompt_screen.DOCTRINE) and the source of the days. The day report (world/report.py) says how the mind did.
This says how the world did (WORLD-2.md): of the moments he decided with a mind, how many opened with

  answered   the reply to what he had just said, and nothing else from the world;
  empty      "Nothing in particular happens.";
  brought    something he did not start: a beat of a storyline or an offer, the morning papers, the day's listings,
             a letter, a person he has not met, a person who speaks first, a power cut, rain, bad air;
  routine    the rest: arriving, a closing hour, a meal laid out, hunger.

Beside them: where he was (the share at home, the entropy of his places in bits), the people who spoke, what he did,
and how many notions of his system his thoughts carry per 100 words (tools.prompt_screen.DOCTRINE; his travel letters
have 0.17, tools/travel_register.py). A day counts when it has at least world.report.FLOOR thoughts, as in T10.

Beside the columns of the old read: switches, the median minutes of a run of one act (Dwell), how far a day lies from
the day before (Variation) and how much of its kinds and pairs of act and place earlier days had (Kinds seen, Acts
seen). Limits: see world/health.py.

A read, never a gate: it names no target and no pass. Evaluation only.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.prompt_screen import DOCTRINE  # noqa: E402
from world import health  # noqa: E402
from world.health import across, brought_kinds, divergence, entropy, opening, pooled, table  # noqa: E402,F401
from world.report import FLOOR  # noqa: E402
from world.voices import heard  # noqa: E402,F401

DAY_FILE = re.compile(r"\d{4}-\d{2}-\d{2}\.json$")


def row(day):
    """One day's read (world/health.py), with the doctrine count of this tool."""
    return health.row(day, DOCTRINE)


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
    rows = across(map(row, days))
    read = {"source": args.ref or str(args.days), "floor": FLOOR, "days_read": len(days), "rows": rows, "pooled": pooled(rows)}
    print(f"{len(rows)} of {len(days)} days have at least {FLOOR} thoughts.\n")
    print(table(rows))
    print("\nPooled: " + json.dumps(read["pooled"], ensure_ascii=False))
    if args.json:
        args.json.write_text(json.dumps(read, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
