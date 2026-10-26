"""One row per day: what the scoreboard needs from a day file (T18).

Only the day file is read. Repetition follows T9 and T10 exactly (`pc/thought_repetition.py` on Codex's branch):
a phrase is four words in a row with at least one outside a fixed stopword list, and a thought is marked when it
reuses a phrase from an earlier thought that day. Only his thoughts count, and a day with fewer than 30 is not measured.
"""
import re
import unicodedata
from collections import Counter

STOPWORDS = frozenset("""a about above after again against all am an and any are aren't as at be because been before being below between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself just me more most must mustn't my myself no nor not of off on once only or other ought our ours ourselves out over own same she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's will with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves""".split())
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*|\d+(?:[,.]\d+)*", re.UNICODE)
FLOOR = 20              # T10: fewer thoughts than this and the share is not measured (30 for a day of sixteen waking hours; 20 since his day runs nine to nine)
LOOP = 4                # the same refusal this often in a day is a loop (world status)
QUIET = ("away", "quiet")


def grams(text):
    text = unicodedata.normalize('NFKC', text).casefold().replace('\u2019', "'").replace('\u2018', "'")
    words = WORD.findall(text)
    out = set()
    for i in range(len(words) - 3):
        g = tuple(words[i:i+4])
        # Numerals are boundaries, not removed words that could create a phrase.
        if any(w[0].isdigit() for w in g) or all(w in STOPWORDS for w in g):
            continue
        out.add(' '.join(g))
    return out


def repetition(day):
    """His thoughts that day, how many reuse an earlier phrase, and the most reused phrases."""
    thoughts = [s["decision"]["thought"] for s in day.get("steps", []) if "decision" in s and s["decision"].get("thought") is not None]
    seen, marked = Counter(), 0
    for text in thoughts:
        g = grams(text)
        marked += any(seen[p] for p in g)
        seen.update(g)
    if len(thoughts) < FLOOR:
        return {"thoughts": len(thoughts), "marked": None, "share": None, "phrases": []}
    top = sorted((p for p, c in seen.items() if c > 1), key=lambda p: (-seen[p], p))[:3]
    return {"thoughts": len(thoughts), "marked": marked, "share": marked / len(thoughts), "phrases": top}


def refusal_kind(e):
    return re.sub(r"\d+", "#", e.split(";")[0].split(". ")[0]).strip()[:80]


def names(raw):
    """Everyone he spoke with or who spoke to him, once each: "Ramesh and Shri G. Hegde" is two people, "the bookseller" one."""
    seen = {}
    for name in raw:
        for one in re.split(r",\s*|\s+and\s+", name):
            one = one.strip()
            if one and one != "Hegel":
                seen.setdefault(one.casefold(), one[:1].upper() + one[1:])
    return sorted(seen.values())


def row(day):
    """The scoreboard row for one day."""
    steps = [s for s in day.get("steps", []) if "decision" in s]
    source = lambda s: (s.get("mind") or {}).get("source") or "unknown"
    waking = [s for s in steps if s["decision"]["action"] != "sleep" and source(s) != "bedtime"]
    quiet = [s for s in waking if source(s) in QUIET]
    # an away step's refusal is the outage itself ("no answer from …"), not the world saying no
    refused = [e for s in steps if source(s) != "away" for tries in (s.get("mind") or {}).get("refused", []) for e in tries
               if isinstance(e, str)]
    top = Counter(refusal_kind(e) for e in refused).most_common(1)
    said = [e for e in day.get("entries", []) if e.get("k") == "said"]
    people = names([e["to"] for e in said if not e.get("by") and e.get("to")] + [e["by"] for e in said if e.get("by")])
    owl = day.get("owl") or {}
    rep = repetition(day)
    return {
        "n": day.get("n"), "date": day["date"], "complete": bool(day.get("complete")),
        "decisions": len(steps), "thoughts": rep["thoughts"],
        "sources": dict(sorted(Counter(source(s) for s in steps).items())),
        "waking": len(waking), "quiet": len(quiet), "quiet_share": len(quiet) / len(waking) if waking else 0.0,
        "refusals": len(refused), "top_refusal": top[0][0] if top else None, "top_refusal_n": top[0][1] if top else 0,
        "loop": bool(top and top[0][1] >= LOOP),
        "repetition": rep["share"], "repeated": rep["marked"], "phrases": rep["phrases"],
        "meals": sum(1 for s in steps if s["decision"]["action"] == "eat"),
        "cash_open": (day.get("opening") or {}).get("imprest"), "cash": (day.get("state") or {}).get("imprest"),
        "places": sorted({s["decision"]["place"] for s in steps}), "people": people,
        "theses": [f"{t['id']}: {t.get('from')} → {t.get('to')}" for t in owl.get("theses") or []],
        "owl": bool(owl),
    }


def pct(x):
    return "–" if x is None else f"{100 * x:.0f}%"


def table(rows):
    """A Markdown table, one line per day, for pc/SCOREBOARD.md and the daily review."""
    out = ["| Day | Date | Thoughts | Quiet | Refusals | Repetition | Meals | Cash | Places | People | Theses | Owl |",
           "|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|"]
    for r in rows:
        ref = f"{r['refusals']}" + (f" ({r['top_refusal_n']}× {r['top_refusal']}{', a loop?' if r['loop'] else ''})" if r["top_refusal"] else "")
        cash = "–" if r["cash"] is None else f"₹{r['cash']:,}"
        out.append(f"| {r['n']} | {r['date']}{'' if r['complete'] else ' (running)'} | {r['thoughts']} | {pct(r['quiet_share'])} | {ref} | "
                   f"{pct(r['repetition'])} | {r['meals']} | {cash} | {len(r['places'])} | {len(r['people'])} | "
                   f"{'; '.join(r['theses']) or '–'} | {'yes' if r['owl'] else 'no'} |")
    return "\n".join(out)


def text(r):
    """The same row, readable."""
    lines = [f"Day {r['n']} ({r['date']}){'' if r['complete'] else ', still running'}",
             f"  thoughts     {r['thoughts']} of {r['decisions']} decisions; sources {r['sources']}",
             f"  quiet        {r['quiet']} of {r['waking']} waking steps ({pct(r['quiet_share'])})",
             f"  refusals     {r['refusals']}" + (f"; most often ({r['top_refusal_n']}×): {r['top_refusal']}" if r["top_refusal"] else "") + ("  ← a loop?" if r["loop"] else ""),
             f"  repetition   " + (f"{r['repeated']}/{r['thoughts']} ({pct(r['repetition'])}); most reused: {', '.join(r['phrases'])}" if r["repetition"] is not None
                                  else f"not measured (fewer than {FLOOR} thoughts)"),
             f"  meals        {r['meals']}",
             f"  cash         " + ("–" if r["cash"] is None else f"₹{r['cash']:,}") + ("" if r["cash_open"] is None else f" (opened with ₹{r['cash_open']:,})"),
             f"  places       {', '.join(r['places']) or '–'}",
             f"  people       {', '.join(r['people']) or '–'}",
             f"  theses       {'; '.join(r['theses']) or 'none moved'}",
             f"  owl          {'written' if r['owl'] else 'not yet'}"]
    return "\n".join(lines)
