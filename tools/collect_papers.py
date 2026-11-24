#!/usr/bin/env python3
"""Collect one day's papers into a folder of their own, for a rehearsal's archive (pc/PAPERS.md, HEGEL_PAPERS_ARCHIVE).

    python3 tools/collect_papers.py --state ~/hegel-eval/papers-archive            # his next date: the day after today
    python3 tools/collect_papers.py --state <folder> --date 2026-11-26

It fetches the news feeds once, as his morning does, and writes <state>/feeds/papers-<date>.json: every piece that pass kept
(title, summary, link, source). It touches nothing of his: the folder is its own, and no switch on the Pi changes. A date whose
headlines are already in the folder is not fetched again. The pieces are a newspaper's text: they stay on the machine that
collected them and are never pushed (WORLD-3.md, rule 4). Evaluation material, never training data."""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world.config import Config  # noqa: E402
from world.feeds import Feeds  # noqa: E402


def collect(state, d, feeds=None):
    """The pieces kept for date d in the folder `state`, fetched now if the day is not there yet. Returns (headlines, pieces)."""
    env = {"HEGEL_PUSH": "0", "HEGEL_STATE": str(Path(state).expanduser()), "HEGEL_FEEDS": "1", "HEGEL_PAPERS_RECORD": "1"}
    if feeds:
        env["NEWS_FEEDS"] = feeds
    f = Feeds(Config(env))
    heads = f.headlines(d)
    return heads, f.pieces(d)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", required=True, help="the archive's own folder; feeds/papers-<date>.json is written there")
    ap.add_argument("--date", help="the date the papers are kept under (default: tomorrow, his next day)")
    ap.add_argument("--feeds", help="comma-separated RSS feeds (default: the engine's own)")
    a = ap.parse_args(argv)
    d = date.fromisoformat(a.date) if a.date else date.today() + timedelta(days=1)
    heads, pieces = collect(a.state, d, a.feeds)
    print(json.dumps({"date": d.isoformat(), "headlines": len(heads), "pieces": len(pieces),
                      "with_summary": sum(1 for p in pieces if p.get("summary"))}))
    return 0 if pieces else 1


if __name__ == "__main__":
    raise SystemExit(main())
