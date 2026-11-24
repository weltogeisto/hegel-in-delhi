#!/usr/bin/env python3
"""Count what Hegel's manuscripts do, sitting by sitting, so that changes to the world can be compared before and after.

    python3 tools/works_score.py --days <folder of day files> [--before <folder of earlier day files>] [--from DATE] --out <folder>
    python3 tools/works_score.py --futures <folder>/futures --before <folder of the live days> --from 2026-11-25 --out <folder>

A sitting is a `writing` entry with text in a complete day file; sittings are taken in order of date, then of their place in
the day's entries. `--before` names day files that came earlier: their sittings are not scored but count as "written before".
`--from DATE` scores only sittings from that date on; earlier ones in the same folder also count as written before.
`--futures` scores each future folder (`<seed>/days/`) on its own, each with the same `--before`.

For each sitting it counts:
  opens_dated  whether its first 30 words hold a date ("24 November 2026"), a clock time ("15:44") or an air-quality figure
               ("air quality index", "AQI", "air index"): true means it opens like a diary entry.
  century      the terms of world/data/after_1831.txt in it (list and count), matched as the engine matches them: whole
               words, any case, with an optional plural "s".
  said_before  the share of its six-word runs (lower-cased, letters only) that already stand in any sitting written before it,
               in any manuscript. (The very first sitting has nothing before it and scores 0.)
  stock        the share of its four-word runs that already stood in at least three earlier sittings: his standing formulas.
  new_words    its content words (letters only, lower-case, six letters or more, minus a small stop list) that no earlier
               sitting used: the count, and the share of its distinct content words; with the ten longest as a sample.
               A proxy for new matter.
  read_used    for each `read` entry with a title in the 14 days before the sitting (same record): whether at least two of the
               title's content words (five letters or more) appear in the sitting. How many readings were available, how many
               it used, and their titles.
  words        its length, with the manuscript (work id, title, kind, sitting number).

This tool counts. It does not judge. Whether a sitting is worth anything, whether it thinks something new, is read by people.
The record and the futures are evaluation material, never training data. Standard library only."""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import date as Date, timedelta
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from world.world import wordlist  # noqa: E402

OPEN_WORDS = 30
REPEAT = 6
STOCK_RUN = 4
STOCK_MIN = 3
NEW_MIN = 6
READ_MIN = 5
READ_NEEDS = 2
READ_DAYS = 14
SAMPLE = 10

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATED = re.compile(r"\b\d{1,2}\s+(?:%s)\s+\d{4}\b|\b(?:%s)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}:\d{2}\b|"
                   r"\bair\s+quality\s+index\b|\bAQI\b|\bair\s+index\b" % (MONTHS, MONTHS), re.I)

STOP = frozenset("""
because through without before between should another something nothing though therefore himself herself itself however
whether against during rather almost himself myself themselves yourself everything anything having whereas whatever
whenever wherever perhaps instead towards toward within beyond across around behind beneath become becomes became
being really still would could might shall always never again after under above their there these those which where while
""".split())


def words_of(text):
    return re.findall(r"[a-z]+", (text or "").lower())


def runs(words, n):
    return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


def content(words, minimum=NEW_MIN):
    return {w for w in words if len(w) >= minimum and w not in STOP}


def opens_dated(text):
    return bool(DATED.search(" ".join((text or "").split()[:OPEN_WORDS])))


def century_terms(text, rx):
    """The distinct terms (in the form the text has them), in order of appearance."""
    out, seen = [], set()
    for m in (rx.finditer(text) if rx and text else ()):
        if m.group(1).lower() not in seen:
            seen.add(m.group(1).lower())
            out.append(m.group(1))
    return out


def load_days(folder):
    """The complete day files of a folder, in date order."""
    days = []
    for p in sorted(Path(folder).glob("????-??-??.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("complete") and isinstance(d, dict):
            d.setdefault("date", p.stem)
            days.append(d)
    return days


def collect(days):
    """(sittings, readings) of day files, each in order of date and place in the day."""
    sittings, readings = [], []
    for d in sorted(days, key=lambda x: x["date"]):
        for i, e in enumerate(d.get("entries") or []):
            if e.get("k") == "writing" and (e.get("text") or "").strip():
                sittings.append({"date": d["date"], "i": i, "t": e.get("t"), "work": e.get("work") or e.get("title"),
                                 "title": e.get("title"), "kind": e.get("kind"), "sitting": e.get("sitting"), "text": e["text"],
                                 "words_given": e.get("words")})
            elif e.get("k") == "read" and (e.get("title") or "").strip():
                readings.append({"date": d["date"], "i": i, "title": e["title"]})
    return sittings, readings


def key_of(s):
    return (s["date"], s["work"], s["sitting"], s["text"])


def score(scored_days, before_days=(), start=None, rx=None):
    """The scores of the sittings of scored_days (from `start` on), each against everything written before it."""
    if rx is None:
        rx = wordlist("after_1831.txt", "s?")
    s_before, r_before = collect(before_days)
    s_main, r_main = collect(scored_days)
    seen_keys = {key_of(s) for s in s_before}
    s_main = [s for s in s_main if key_of(s) not in seen_keys]
    seen_reads = {(r["date"], r["title"]) for r in r_before}
    r_all = r_before + [r for r in r_main if (r["date"], r["title"]) not in seen_reads]
    s_main = sorted(s_main, key=lambda s: (s["date"], s["i"]))
    sixes, fours, vocab = set(), Counter(), set()
    out = []

    def learn(w):
        sixes.update(runs(w, REPEAT))
        fours.update(set(runs(w, STOCK_RUN)))
        vocab.update(content(w))

    for s in s_before:
        learn(words_of(s["text"]))
    for s in s_main:
        w = words_of(s["text"])
        if start and s["date"] < start:
            learn(w)
            continue
        six, four = runs(w, REPEAT), runs(w, STOCK_RUN)
        terms = century_terms(s["text"], rx)
        cw = content(w)
        new = sorted(cw - vocab)
        day = Date.fromisoformat(s["date"])
        lo = (day - timedelta(days=READ_DAYS)).isoformat()
        avail = [r for r in r_all if lo <= r["date"] <= s["date"] and (r["date"], r["i"]) < (s["date"], s["i"])]
        used = [r["title"] for r in avail
                if len(content(words_of(r["title"]), READ_MIN) & set(w)) >= READ_NEEDS]
        out.append({"date": s["date"], "t": s["t"], "work": s["work"], "title": s["title"], "kind": s["kind"], "sitting": s["sitting"],
                    "words": len(s["text"].split()),
                    "opens_dated": opens_dated(s["text"]),
                    "century": {"terms": terms, "count": len(terms)},
                    "said_before": round(sum(1 for r in six if r in sixes) / len(six), 4) if six else None,
                    "stock": round(sum(1 for r in four if fours[r] >= STOCK_MIN) / len(four), 4) if four else None,
                    "new_words": {"count": len(new), "share": round(len(new) / len(cw), 4) if cw else None,
                                  "sample": sorted(new, key=lambda x: (-len(x), x))[:SAMPLE]},
                    "read_used": {"available": len(avail), "used": len(used), "titles": used}})
        learn(w)
    return out


def avg(values, digits=4):
    v = [x for x in values if x is not None]
    return round(mean(v), digits) if v else None


def summarize(sittings):
    """Per manuscript, and overall."""
    order, by = [], {}
    for s in sittings:
        k = s["work"]
        if k not in by:
            by[k] = []
            order.append(k)
        by[k].append(s)
    works = []
    for k in order:
        g = by[k]
        works.append({"work": k, "title": g[0]["title"], "kind": g[0]["kind"], "sittings": len(g),
                      "words": sum(x["words"] for x in g), "first": g[0]["date"], "last": g[-1]["date"],
                      "opens_dated": sum(1 for x in g if x["opens_dated"]),
                      "said_before": avg(x["said_before"] for x in g), "stock": avg(x["stock"] for x in g),
                      "century_terms": sum(x["century"]["count"] for x in g),
                      "new_words_per_sitting": [x["new_words"]["count"] for x in g]})
    terms = {t.lower() for s in sittings for t in s["century"]["terms"]}
    overall = {"sittings": len(sittings), "words": sum(s["words"] for s in sittings), "manuscripts": len(works),
               "open_dated_share": round(sum(1 for s in sittings if s["opens_dated"]) / len(sittings), 4) if sittings else None,
               "sittings_with_century": sum(1 for s in sittings if s["century"]["count"]),
               "century_terms_distinct": len(terms), "century_terms": sorted(terms),
               "said_before_mean": avg(s["said_before"] for s in sittings), "stock_mean": avg(s["stock"] for s in sittings),
               "new_words_share_mean": avg(s["new_words"]["share"] for s in sittings),
               "readings_available": sum(s["read_used"]["available"] for s in sittings),
               "readings_used": sum(s["read_used"]["used"] for s in sittings)}
    return {"overall": overall, "works": works, "sittings": sittings}


def pct(x):
    return "–" if x is None else f"{100 * x:.0f}%"


def block(title, res, level="##"):
    o, lines = res["overall"], [f"{level} {title}", ""]
    lines += [f"- Sittings: {o['sittings']}; words: {o['words']:,}; manuscripts: {o['manuscripts']}",
              f"- Open like a diary entry (date, time or air): {pct(o['open_dated_share'])}",
              f"- Sittings with a name or term from after 1831: {o['sittings_with_century']}; distinct terms: {o['century_terms_distinct']}"
              + (f" ({', '.join(o['century_terms'])})" if o["century_terms"] else ""),
              f"- Said before (six-word runs), mean: {pct(o['said_before_mean'])}",
              f"- Stock (four-word runs in 3+ earlier sittings), mean: {pct(o['stock_mean'])}",
              f"- New words, mean share of a sitting's content words: {pct(o['new_words_share_mean'])}",
              f"- Readings available: {o['readings_available']}; used: {o['readings_used']}", ""]
    if not res["sittings"]:
        return lines
    lines += ["| Manuscript | Sittings | Words | Dates | Open dated | Said before / stock | Century |", "|---|---:|---:|---|---:|---|---:|"]
    for w in res["works"]:
        lines.append(f"| {w['title'] or w['work']} | {w['sittings']} | {w['words']:,} | {w['first'][5:]} to {w['last'][5:]} | "
                     f"{w['opens_dated']}/{w['sittings']} | {pct(w['said_before'])} / {pct(w['stock'])} | {w['century_terms']} |")
    lines.append("")
    for w in res["works"]:
        if w["sittings"] < 3:
            continue
        lines += [f"{level}# {w['title'] or w['work']}", "", "| Date | Words | Dated | Said | Stock | New | Century |", "|---|---:|---|---:|---:|---:|---:|"]
        for s in res["sittings"]:
            if s["work"] == w["work"]:
                lines.append(f"| {s['date'][5:]}{' ' + s['t'] if s['t'] else ''} | {s['words']} | {'yes' if s['opens_dated'] else 'no'} | "
                             f"{pct(s['said_before'])} | {pct(s['stock'])} | {s['new_words']['count']} | {s['century']['count']} |")
        lines.append("")
    return lines


def report(results):
    """WORKS.md text for {name: result}; with several, a comparison table first."""
    lines = ["# Works: what the manuscripts do", "",
             "Counts, not judgements: worth is read by people. Evaluation only, never training data.", ""]
    if len(results) > 1 or "" not in results:
        lines += ["| Future | Sittings | Open dated | Century (sittings / terms) | Said before | Stock | New words |",
                  "|---|---:|---:|---|---:|---:|---:|"]
        for name, r in results.items():
            o = r["overall"]
            lines.append(f"| {name} | {o['sittings']} | {pct(o['open_dated_share'])} | "
                         f"{o['sittings_with_century']} / {o['century_terms_distinct']} | {pct(o['said_before_mean'])} | "
                         f"{pct(o['stock_mean'])} | {pct(o['new_words_share_mean'])} |")
        lines.append("")
        for name, r in results.items():
            lines += block(f"Future {name}", r)
    else:
        lines += block("Overall", results[""])
    return "\n".join(lines).rstrip() + "\n"


def future_days(folder):
    f = Path(folder) / "days"
    return f if f.is_dir() else Path(folder)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Count what the manuscripts do. Counts, does not judge.")
    ap.add_argument("--days", help="folder of day files to score")
    ap.add_argument("--futures", help="folder holding <seed>/days/ for each future")
    ap.add_argument("--before", help="folder of day files written earlier (not scored)")
    ap.add_argument("--from", dest="start", help="score only sittings from this date on")
    ap.add_argument("--out", required=True, help="folder for WORKS.md and works.json")
    a = ap.parse_args(argv)
    if bool(a.days) == bool(a.futures):
        ap.error("give exactly one of --days and --futures")
    before = load_days(a.before) if a.before else []
    if a.days:
        results = {"": summarize(score(load_days(a.days), before, a.start))}
    else:
        seeds = sorted(p for p in Path(a.futures).iterdir() if p.is_dir())
        results = {p.name: summarize(score(load_days(future_days(p)), before, a.start)) for p in seeds}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "WORKS.md").write_text(report(results), encoding="utf-8")
    payload = results[""] if a.days else results
    (out / "works.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
