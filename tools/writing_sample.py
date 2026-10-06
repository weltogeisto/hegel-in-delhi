#!/usr/bin/env python3
"""Hegel in Delhi: what the world's plain-text writing path makes of a plan. Standard library only; run it from the repo root on the PC.

    python3 tools/writing_sample.py --url http://127.0.0.1:8081                      # the essay and the letter of the first samples
    python3 tools/writing_sample.py --url http://127.0.0.1:8081 --seed 7 --date 2026-10-20 \\
        --plan '{"title": "On tea", "kind": "essay", "to": null, "continues": false, "about": "the tea at Khan Market"}'

Each --plan is a JSON object as the world's account of a sitting: title, kind, to, continues, about. The prompt is made as the world makes it
(works.primer from the shelf in mind/shelf, works.prompt with the editor's notes), completed by the mind as it is in the world (works.TOKENS,
the sampling of HTTPMind.complete) and cleaned by works.sitting. Per plan it prints the full prompt, then the sitting (or why it is unusable),
then "-----". A plan with "continues" carries on an earlier plan of the same title, as a manuscript does."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from world import shelf, works  # noqa: E402
from world.clock import now_ist  # noqa: E402
from world.mind import HTTPMind, MindAway  # noqa: E402

PLANS = [{"title": "On the noise of the street", "kind": "essay", "to": None, "continues": False,
          "about": "the din of the street below the verandah, and what thought makes of what it cannot shut out"},
         {"title": "Letter to Niethammer", "kind": "letter", "to": "Niethammer", "continues": False,
          "about": "his first days in Delhi, the heat and the noise, and what has become of the system here"}]


def sample(mind, books, plan, st, d, seed=None):
    """(the primer or None, the prompt, the sitting or None, why not): one plan through the world's path. A usable sitting is filed in st, as the
    engine does, so that a later plan that continues it flows on from it."""
    plan = works.outline(dict({"kind": "essay", "to": None, "continues": False}, **plan))
    if not plan:
        return None, "", None, "the plan has no title or no about"
    book = works.primer(books, plan)
    prompt, opening = works.prompt(plan, st, d, book)
    try:
        raw = mind.complete(prompt, works.TOKENS, seed=seed)
    except MindAway as e:
        return book, prompt, None, f"the mind did not answer: {e}"
    w = works.sitting(plan, raw, opening)
    if w:
        works.file(st, w, d)
    return book, prompt, w, "" if w else f"fewer than {works.MIN_WORDS} words were left of the completion ({raw.strip()!r})" if raw.strip() else "the completion was empty"


def main(argv=None, mind=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", help="llama-server base URL, e.g. http://127.0.0.1:8081")
    p.add_argument("--plan", action="append", metavar="JSON", help="a plan: {title, kind, to, continues, about}; repeat for more (default: the essay and the letter)")
    p.add_argument("--date", type=date.fromisoformat, default=now_ist().date(), help="the day written at Delhi, YYYY-MM-DD (default: today)")
    p.add_argument("--seed", type=int)
    p.add_argument("--timeout", type=int, default=300)
    a = p.parse_args(argv)
    if not a.url and not mind:
        p.error("--url is required")
    try:
        plans = [json.loads(x) for x in a.plan] if a.plan else PLANS
    except ValueError as e:
        p.error(f"--plan is not JSON: {e}")
    if not all(isinstance(x, dict) for x in plans):
        p.error("--plan must be a JSON object")
    books = shelf.load(REPO / "mind/shelf/index.json.gz", REPO / "world/data/shelf_terms.json")
    if not books:
        print("(no shelf in mind/shelf: no primer)", file=sys.stderr)
    mind, st = mind or HTTPMind(a.url, timeout=a.timeout), {}
    for plan in plans:
        book, prompt, w, why = sample(mind, books, plan, st, a.date, a.seed)
        print(f"=== prompt (primer: {book['label'] if book else 'none'}) ===\n{prompt}\n=== sitting ===\n" + (w["text"] if w else f"(unusable) {why}") + "\n-----")
    return 0


if __name__ == "__main__":
    sys.exit(main())
