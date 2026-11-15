"""The literature watch (research/LITERATURE-GAPS.md, section 6): new arXiv papers on what Hegel in Delhi is doing.

    python3 tools/arxiv_watch.py                                   # the last nine days, as Markdown on stdout
    python3 tools/arxiv_watch.py --out /tmp/candidates.md --update-seen

Puts each query in TOPICS to arXiv's API, newest first, three seconds apart as arXiv asks. Keeps papers first submitted
within --days of --today, drops those whose ID is in research/watch/seen.txt or cited in research/*.md or
research/watch/*.md, and prints the rest grouped by topic: date, title, link and the start of the abstract. It judges
nothing: the weekly run reads the candidates and keeps what bears on the project. --update-seen appends every printed
candidate to seen.txt so that next week does not offer it again. A failed query is named in the output and the rest
go on; the exit code is 1 only if every query failed. Standard library only.
"""
import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESEARCH = REPO / "research"
SEEN = RESEARCH / "watch" / "seen.txt"
API = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
AGENT = "hegel-in-delhi literature watch (https://github.com/weltogeisto/hegel-in-delhi)"
ID = re.compile(r"(?<![\d.])\d{4}\.\d{4,5}(?![\d])")   # new-style arXiv IDs, without the version
PAUSE = 3.0           # seconds between queries, as arXiv's API terms ask
PER_QUERY = 50        # newest results per query; a week's matches fit with room to spare
ABSTRACT_CAP = 600    # characters of abstract shown per candidate

# The handover's questions (research/HANDOVER-SIMULATION.md, section 5) and the gaps of LITERATURE-GAPS.md.
# arXiv's search stems words, so "language model" also finds "large language models".
TOPICS = {
    "Projects like ours: worlds that referee their characters": [
        'abs:"game master" AND abs:"language model"',
        'abs:"generative agents" AND abs:simulation',
        'abs:"world state" AND abs:"language model" AND abs:narrative',
    ],
    "Projects like ours: one agent over a long horizon": [
        'abs:"long-term coherence" AND abs:agent',
        'abs:"long-horizon" AND abs:agent AND abs:economy',
        'abs:"identity drift"',
        'abs:"persona drift"',
    ],
    "What he may know: knowledge boundaries and history": [
        'abs:"historical figures" AND abs:"language model"',
        'abs:"knowledge boundary" AND abs:character',
        'abs:"historical text" AND abs:"language model"',
        'abs:"temporal leakage"',
    ],
    "A. Memory": [
        'abs:"memory consolidation" AND abs:agent',
        'abs:"long-term memory" AND abs:"language model" AND abs:agent',
        'abs:provenance AND abs:memory AND abs:agent',
    ],
    "B. Persona and role-play": [
        'abs:"role-playing" AND abs:character',
        'abs:"role-play" AND abs:persona AND abs:consistency',
        'abs:"character hallucination"',
    ],
    "C. Voice and style": [
        'abs:"style transfer" AND abs:authorship',
        'abs:stylometry AND abs:"language model"',
    ],
    "D. Belief": [
        'abs:"belief update" AND abs:"language model"',
        'abs:"opinion dynamics" AND abs:"language model"',
        'abs:"belief revision" AND abs:"language model"',
    ],
    "E. Repetition and diversity": [
        'abs:"mode collapse" AND abs:diversity',
        'abs:repetition AND abs:"language model" AND abs:decoding',
    ],
    "G. Evaluation with few judges": [
        'abs:"LLM-as-a-judge" AND abs:bias',
    ],
    "H. Local hardware": [
        'abs:"consumer GPU" AND abs:"language model"',
        'abs:"24GB" AND abs:"language model"',
    ],
    "I. Narrative, audience and ethics": [
        'abs:"emergent narrative"',
        'abs:"interactive narrative" AND abs:"language model"',
        'abs:deceased AND abs:"language model"',
    ],
    "An architecture from an account of mind": [
        'abs:"cognitive architecture" AND abs:"language model"',
        'abs:"cognitive model" AND abs:"language model" AND abs:discovery',
        'abs:"think-aloud" AND abs:"language model"',
    ],
}


def fetch(query, n=PER_QUERY, tries=3):
    """arXiv's Atom answer to one query, newest first. Retries twice, waiting longer each time."""
    url = API + "?" + urllib.parse.urlencode({"search_query": query, "sortBy": "submittedDate",
                                              "sortOrder": "descending", "max_results": n})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=60) as r:
                return r.read()
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(PAUSE * 2 ** (i + 1))


def parse(atom):
    """[{id, date, title, abstract}] from one Atom answer. arXiv answers a bad query with an entry that has no paper ID;
    that entry is skipped."""
    out = []
    for e in ET.fromstring(atom).findall("a:entry", ATOM):
        m = ID.search(e.findtext("a:id", "", ATOM))
        if not m:
            continue
        out.append({"id": m.group(0), "date": e.findtext("a:published", "", ATOM)[:10],
                    "title": " ".join(e.findtext("a:title", "", ATOM).split()),
                    "abstract": " ".join(e.findtext("a:summary", "", ATOM).split())})
    return out


def known(seen=SEEN, research=RESEARCH):
    """Every arXiv ID already in seen.txt or cited in the research notes and earlier digests."""
    ids = set()
    for p in [seen, *sorted(research.glob("*.md")), *sorted(research.glob("watch/*.md"))]:
        if p.is_file():
            ids.update(ID.findall(p.read_text(encoding="utf-8")))
    return ids


def collect(get, topics, since, skip, pause=PAUSE, sleep=time.sleep):
    """(candidates, failed). A candidate is a paper first submitted on or after `since` and not in `skip`; it is
    listed under the first topic that found it, and `topics` names every topic that did."""
    found, failed, first = {}, [], True
    for topic, queries in topics.items():
        for q in queries:
            if not first:
                sleep(pause)
            first = False
            try:
                entries = parse(get(q))
            except (OSError, ET.ParseError) as e:
                failed.append((q, str(e) or type(e).__name__))
                continue
            for x in entries:
                if x["date"] < since.isoformat() or x["id"] in skip:
                    continue
                if x["id"] not in found:
                    found[x["id"]] = {**x, "topics": [topic]}
                elif topic not in found[x["id"]]["topics"]:
                    found[x["id"]]["topics"].append(topic)
    return list(found.values()), failed


def cut(text, cap=ABSTRACT_CAP):
    return text if len(text) <= cap else text[:cap].rsplit(" ", 1)[0] + " …"


def render(cands, failed, topics, since, today):
    """The candidates as Markdown, by topic, newest first."""
    n = sum(len(q) for q in topics.values())
    lines = [f"# Literature watch: candidates, {today}", "",
             f"Papers first submitted from {since} to {today} and not seen before: {len(cands)}, from {n} queries. "
             "Keyword hits, not yet judged."]
    if failed:
        lines += ["", f"**{len(failed)} of {n} queries failed, so this list is incomplete:**"]
        lines += [f"- `{q}`: {err}" for q, err in failed]
    for topic in topics:
        items = sorted((c for c in cands if c["topics"][0] == topic), key=lambda c: (c["date"], c["id"]), reverse=True)
        if not items:
            continue
        lines += ["", f"## {topic}", ""]
        for c in items:
            also = f" (also: {'; '.join(c['topics'][1:])})" if len(c["topics"]) > 1 else ""
            lines += [f"- {c['date']} · [{c['title']}](https://arxiv.org/abs/{c['id']}) · {c['id']}{also}",
                      f"  {cut(c['abstract'])}"]
    return "\n".join(lines) + "\n"


def remember(cands, today, seen=SEEN):
    """Append the candidates to seen.txt: ID, the day it was offered, title."""
    seen.parent.mkdir(parents=True, exist_ok=True)
    with seen.open("a", encoding="utf-8") as f:
        for c in cands:
            f.write(f"{c['id']}  {today}  {c['title']}\n")


def main(argv=None, get=fetch, sleep=time.sleep):
    ap = argparse.ArgumentParser(description="New arXiv papers on what Hegel in Delhi is doing.")
    ap.add_argument("--days", type=int, default=9, help="how far back, by first submission (default 9)")
    ap.add_argument("--today", type=date.fromisoformat, default=date.today(), help="YYYY-MM-DD (default today)")
    ap.add_argument("--out", type=Path, help="write the Markdown here instead of stdout")
    ap.add_argument("--update-seen", action="store_true", help="append the candidates to the seen list")
    ap.add_argument("--seen", type=Path, default=SEEN, help=argparse.SUPPRESS)
    ap.add_argument("--research", type=Path, default=RESEARCH, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    since = a.today - timedelta(days=a.days)
    cands, failed = collect(get, TOPICS, since, known(a.seen, a.research), sleep=sleep)
    text = render(cands, failed, TOPICS, since, a.today)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    n = sum(len(q) for q in TOPICS.values())
    if failed:
        print(f"{len(failed)} of {n} queries failed", file=sys.stderr)
    if len(failed) == n:
        return 1
    if a.update_seen:
        remember(cands, a.today, a.seen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
