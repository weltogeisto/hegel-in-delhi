"""World health: what the world gave him to live through on each full day, and how much his days differ. No model call.

The day report (world/report.py) says how the mind did. This says how the world did (WORLD-2.md): of the moments he
decided with a mind, how many opened with

  answered   the reply to what he had just said, and nothing else from the world;
  empty      "Nothing in particular happens.";
  brought    something he did not start: a beat of a storyline or an offer, the morning papers, the day's listings,
             a letter, a person he has not met, a person who speaks first, a power cut, rain, bad air;
  routine    the rest: arriving, a closing hour, a meal laid out, hunger.

Beside them: where he was (the share at home, the entropy of his places in bits), the people who spoke, what he did,
and, when the caller passes a compiled pattern, how many notions of his system his thoughts carry (the pattern stays
with the caller, tools/world_health.py). A day counts when it has at least world.report.FLOOR thoughts, as in T10.

Variety. How often he changes what he is doing (`switches`, `place_switches`: of two moments that follow each other
among the ones he decided with a mind, how many differ in act or in place), how long a stretch of one act lasts
(`dwell`, `dwell_all`: the median minutes of an unbroken run, a run's minutes being the sum of its steps'
decision.minutes), and what the day brought (`kinds`) and what he chose (`act_places`, as "act@place"). Across the full days
of a set, `across` adds how far a day lies from the day before (`variation`, Jensen-Shannon divergence in bits between
the two days' shares of minutes by act: 0 is the same day again, 1 is nothing shared) and how much of its kinds and
pairs earlier days already had (`kinds_seen`, `acts_seen`; `_5` looks only at the five full days before).

Limits. A step may carry `opened`, a list the engine writes; health reads it when the key is there (an empty list
means empty) and otherwise reads the event's words, so a gallery or a part of a performance, which carry no fixed
words, count as routine in recorded days until the step names what opened it. A greeting and a reply in one moment
count once, as brought. Kinds read from words are coarser than kinds read from `opened` (the words give `stranger`,
`greeting`, `beat:<id>`; the list gives `stranger:<id>`, `greeting:<id>`), so a set that mixes the two will show less
repeat than there is. Runs and switches are counted only between moments that follow each other in the day's record
and were both decided with a mind; a moment the mind did not decide breaks the run. Each row's `acts` holds the counts by
act, as it always has; the pairs are in `act_places`, the minutes by act in `act_minutes`.

A read, never a gate: it names no target and no pass. Evaluation only.
"""
import math
import re
from collections import Counter
from statistics import median

from world.report import FLOOR
from world.voices import heard

MINDS = ("mind", "stub")
EMPTY = "Nothing in particular happens."
SPEAKS = " says: “"
OPENS = ("answered", "empty", "brought", "routine")
# What the world brings of its own, by the words world.situation() and world.post use for it.
BROUGHT = re.compile(r"Headlines: |Today's listings: |Open today: |Tonight here: |you have not met\.|The power goes\."
                     r"|It begins to rain\.|Heavy rain begins\.|The air is very poor today|brings the post: |The post has come: ")
# The same words, one by one, for the kind each names.
WORDS = (("papers", re.compile(r"Headlines: ")),
         ("listings", re.compile(r"Today's listings: |Open today: |Tonight here: ")),
         ("stranger", re.compile(r"you have not met\.")),
         ("power", re.compile(r"The power goes\.")),
         ("rain", re.compile(r"It begins to rain\.|Heavy rain begins\.")),
         ("air", re.compile(r"The air is very poor today")),
         ("post", re.compile(r"brings the post: |The post has come: ")))
# The kinds in `opened` that count as brought, and the ones that only answer.
BROUGHT_KINDS = {"beat", "offer", "session", "papers", "listings", "post", "stranger", "greeting", "power", "rain", "air",
                 "sight", "part", "street"}
ANSWERED_KINDS = {"reply", "read"}


def entropy(counts):
    """Shannon entropy in bits: 0 when he was in one place all day."""
    n = sum(counts.values())
    return -sum(c / n * math.log2(c / n) for c in counts.values() if c) if n else 0.0


def _opened(step):
    """The step's `opened` as a list of strings with anything after "@" cut off, or None when the key is absent."""
    if "opened" not in step:
        return None
    return [str(x).split("@", 1)[0] for x in step["opened"] or []]


def _kind(label):
    return label.split(":", 1)[0]


def _greeting(step, prev):
    """True when a person who is not the echo of his own words speaks first in the event."""
    event = step.get("event") or ""
    reply = heard(prev["voice"]) if prev and prev.get("voice") and prev.get("end") == step.get("t") and not prev.get("left") else None
    return event.count(SPEAKS) - (1 if reply and reply in event else 0) > 0, reply, event


def opening(step, prev):
    """How this moment opened: brought, answered, empty or routine. One label a step; what the world brings comes first.

    Reads `step["opened"]` when the key is there (an empty list is "empty"), the event's words when it is not."""
    opened = _opened(step)
    if opened is not None:
        kinds = {_kind(x) for x in opened}
        if kinds & BROUGHT_KINDS:
            return "brought"
        if kinds & ANSWERED_KINDS:
            return "answered"                   # as the words read it: the reply, with or without an arrival or a meal beside it
        return "routine" if kinds else "empty"
    other, reply, event = _greeting(step, prev)
    if step.get("beat") or BROUGHT.search(event) or other:
        return "brought"
    if reply and reply in event:
        return "answered"
    return "empty" if EMPTY in event else "routine"


def brought_kinds(step, prev=None):
    """The kinds this moment brought, as a list without repeats in the order found: from `opened` when the key is there,
    with anything after "@" cut off, otherwise from the event's words. Those are `beat:<id>` (the step's beat),
    papers, listings, post, stranger, power, rain, air and greeting."""
    opened = _opened(step)
    if opened is not None:
        out = []
        for x in opened:
            if _kind(x) in BROUGHT_KINDS and x not in out:
                out.append(x)
        return out
    out = []
    if step.get("beat"):
        out.append(f"beat:{step['beat']}")
    event = step.get("event") or ""
    out += [name for name, rx in WORDS if rx.search(event)]
    if _greeting(step, prev)[0]:
        out.append("greeting")
    return out


def _runs(steps):
    """Unbroken runs of one act among moments that follow each other in the record: [(act, minutes), ...]."""
    runs, last = [], None
    for i, s in steps:
        act, minutes = s["decision"]["action"], s["decision"].get("minutes") or 0
        if runs and last == i - 1 and runs[-1][0] == act:
            runs[-1][1] += minutes
        else:
            runs.append([act, minutes])
        last = i
    return runs


def _switches(steps, key):
    return sum(1 for (i, a), (j, b) in zip(steps, steps[1:]) if j == i + 1 and a["decision"][key] != b["decision"][key])


def row(day, doctrine=None, floor=FLOOR):
    """One day's read, or None when the day has fewer than `floor` thoughts (FLOOR, unless a rehearsal with a stand-in,
    whose days are shorter, asks for less).

    `doctrine` is an optional compiled pattern; the row counts its matches in the thoughts as `doctrine`, and
    `doctrine` is None without one."""
    decided = [s for s in day.get("steps") or [] if "decision" in s]
    indexed = [(i, s) for i, s in enumerate(decided)
               if (s.get("mind") or {}).get("source") in MINDS and s["decision"].get("thought")]
    if len(indexed) < max(1, floor):
        return None
    steps = [(s, decided[i - 1] if i else None) for i, s in indexed]
    n = len(steps)
    opens = Counter(opening(s, prev) for s, prev in steps)
    places = Counter(s["decision"]["place"] for s, _ in steps)
    acts = Counter(s["decision"]["action"] for s, _ in steps)
    act_minutes = Counter()
    for s, _ in steps:
        act_minutes[s["decision"]["action"]] += s["decision"].get("minutes") or 0
    runs = _runs(indexed)
    by_act = {}
    for act, minutes in runs:
        by_act.setdefault(act, []).append(minutes)
    kinds = sorted({k for s, prev in steps for k in brought_kinds(s, prev)})
    text = " ".join(s["decision"]["thought"] for s, _ in steps)
    words = len(re.findall(r"\w+", text))
    said = {e["by"] for e in day.get("entries") or [] if e.get("k") == "said" and e.get("by")}
    return {"n": day.get("n"), "date": day["date"], "moments": n,
            "opens": {k: opens.get(k, 0) for k in OPENS},
            "home": places.get("home", 0), "places": len(places), "place_bits": round(entropy(places), 2),
            "voices": len(said), "acts": dict(sorted(acts.items())),
            "words": words, "doctrine": len(doctrine.findall(text)) if doctrine else None,
            "cash": (day.get("state") or {}).get("imprest"),
            "switches": _switches(indexed, "action"), "place_switches": _switches(indexed, "place"),
            "dwell": {a: median(v) for a, v in sorted(by_act.items())},
            "dwell_all": median([m for _, m in runs]),
            "kinds": kinds,
            "act_places": sorted({f"{s['decision']['action']}@{s['decision']['place']}" for s, _ in steps}),
            "act_minutes": dict(sorted(act_minutes.items()))}


def divergence(a, b):
    """Jensen-Shannon divergence in bits (log base 2) between two minute counts by act; None when either has no minutes."""
    ta, tb = sum(a.values()), sum(b.values())
    if not ta or not tb:
        return None
    p = {k: a.get(k, 0) / ta for k in set(a) | set(b)}
    q = {k: b.get(k, 0) / tb for k in p}
    m = {k: (p[k] + q[k]) / 2 for k in p}
    kl = lambda x: sum(x[k] * math.log2(x[k] / m[k]) for k in x if x[k] > 0)
    return max(0.0, (kl(p) + kl(q)) / 2)


def _seen(now, before):
    """The share of `now` that `before` already has; None when `now` is empty or there is no day before."""
    if before is None or not now:
        return None
    return round(sum(1 for x in now if x in before) / len(now), 3)


def across(rows):
    """The rows of full days in date order (None rows skipped), each with variation, kinds_seen, kinds_seen_5, acts_seen
    and acts_seen_5. All are None on the first day; kinds_seen is None on a day that brought no kinds."""
    rows = [r for r in rows if r]
    out = []
    for i, r in enumerate(rows):
        earlier, last5 = rows[:i], rows[max(0, i - 5):i]
        union = lambda rs, key: set().union(*(set(x[key]) for x in rs)) if rs else None
        v = divergence(rows[i - 1]["act_minutes"], r["act_minutes"]) if i else None
        out.append(dict(r, variation=None if v is None else round(v, 3),
                        kinds_seen=_seen(r["kinds"], union(earlier, "kinds")),
                        kinds_seen_5=_seen(r["kinds"], union(last5, "kinds")),
                        acts_seen=_seen(r["act_places"], union(earlier, "act_places")),
                        acts_seen_5=_seen(r["act_places"], union(last5, "act_places"))))
    return out


def _mean(rows, key, digits):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(sum(vals) / len(vals), digits) if vals else None


def pooled(rows):
    """All counted days together: shares of moments, and the doctrine rate over all words (None when no day counted it).
    The variety fields are means over the days: switches, place_switches and dwell_all over the days that carry them,
    and variation, kinds_seen(_5) and acts_seen(_5) over the days that have a value (the first day of a set has none)."""
    n = sum(r["moments"] for r in rows)
    if not n:
        return {"days": 0, "moments": 0}
    acts = Counter()
    for r in rows:
        acts.update(r.get("acts") or {})
    share = lambda x: round(x / n, 3)
    counted = [r for r in rows if r.get("doctrine") is not None]
    out = {"days": len(rows), "moments": n,
           "opens": {k: share(sum(r["opens"][k] for r in rows)) for k in OPENS},
           "brought_per_day": round(sum(r["opens"]["brought"] for r in rows) / len(rows), 1),
           "home": share(sum(r["home"] for r in rows)),
           "place_bits": round(sum(r["place_bits"] for r in rows) / len(rows), 2),
           "voices_per_day": round(sum(r["voices"] for r in rows) / len(rows), 1),
           "acts": {k: share(v) for k, v in sorted(acts.items(), key=lambda kv: -kv[1])},
           "doctrine_per_100_words": (round(100 * sum(r["doctrine"] for r in counted) / max(1, sum(r["words"] for r in counted)), 2)
                                      if counted else None)}
    for key, digits in (("switches", 1), ("place_switches", 1), ("dwell_all", 1), ("variation", 3), ("kinds_seen", 3),
                        ("kinds_seen_5", 3), ("acts_seen", 3), ("acts_seen_5", 3)):
        out[key] = _mean(rows, key, digits)
    return out


def pct(x, n):
    return f"{100 * x / n:.0f}%"


def table(rows):
    """A markdown table, a line a day: the old columns, then switches, dwell_all (minutes), variation, kinds_seen, acts_seen."""
    dash = lambda v, f="{}": "–" if v is None else f.format(v)
    out = ["| Day | Date | Moments | Answered | Empty | Brought | At home | Places | Bits | Voices | Doctrine /100 words | Cash "
           "| Switches | Dwell | Variation | Kinds seen | Acts seen |",
           "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        n, o = r["moments"], r["opens"]
        cash = "–" if r["cash"] is None else f"₹{r['cash']:,}"
        doc = "–" if r["doctrine"] is None else f"{100 * r['doctrine'] / max(1, r['words']):.2f}"
        out.append(f"| {r['n']} | {r['date']} | {n} | {pct(o['answered'], n)} | {pct(o['empty'], n)} | {o['brought']} | {pct(r['home'], n)} | "
                   f"{r['places']} | {r['place_bits']:.2f} | {r['voices']} | {doc} | {cash} | "
                   f"{dash(r.get('switches'))} | {dash(r.get('dwell_all'), '{:g}')} | {dash(r.get('variation'), '{:.2f}')} | "
                   f"{dash(r.get('kinds_seen'), '{:.2f}')} | {dash(r.get('acts_seen'), '{:.2f}')} |")
    return "\n".join(out)
