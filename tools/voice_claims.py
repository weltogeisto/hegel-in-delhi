#!/usr/bin/env python3
"""Draw recorded voice replies from a ref's days, with the record up to each, for readers who list their claims.

Where the record keeps a voice's words:
  - a reply: the step's `voice` {by, says, does}, answering the step's `decision.says`; also a `said` entry (by=…, to Hegel) at the step's time.
  - a greeting (a person he knows spoke first): NOT a step key. It is a `said` entry with `by` at the step's time whose text is not the step's
    `voice`; the same words were appended to the step's `event` as 'Name says: “…” <does>', so `does` is read from the event's tail.
Entries carry `t` ("HH:MM", the step's start); diary/said/plan/writing/read entries are not context. At the moment itself only entries written before anyone spoke count.
"""
import argparse
import json
import random
import re
import statistics
import subprocess
from collections import Counter
from pathlib import Path

DAY_FILE = re.compile(r"(\d{4}-\d{2}-\d{2})\.json$")
SKIP_KINDS = {"diary", "said", "plan", "writing", "read"}
BUDGET_WORDS = 350


def days_of_ref(ref, repo):
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout
    names = [x for x in git("ls-tree", "--name-only", ref, "docs/days/").split() if DAY_FILE.search(x)]
    return [json.loads(git("show", f"{ref}:{name}")) for name in sorted(names)]


def days_of_folder(folder):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(folder).iterdir()) if DAY_FILE.search(p.name)]


def words(s):
    return len(s.split())


def clip(s, n):
    w = " ".join(str(s).split()).split(" ")
    return " ".join(w) if len(w) <= n else " ".join(w[:n]) + " …"


def quote_tail(event, by, says):
    """What follows a greeting's quoted words at the end of the event: the voice's `does`."""
    mark = f"{by} says: “{says}”"
    i = event.rfind(mark)
    return " ".join(event[i + len(mark):].split()) or None if i >= 0 else None


def collect(days):
    """Every recorded reply and greeting, in order of the record."""
    items = []
    for d in days:
        for i, s in enumerate(d.get("steps") or []):
            dec = s.get("decision") or {}
            base = {"date": d["date"], "day": d.get("n"), "t": s["t"], "place": dec.get("place") or (s.get("arrived") or None),
                    "event": s.get("event", "")}
            v = s.get("voice")
            for e in d.get("entries") or []:       # a greeting: a person's entry at this moment that is not the step's voice
                if e.get("k") == "said" and e.get("by") and e.get("t") == s["t"] and (not v or e["text"] != v["says"]):
                    items.append({**base, "kind": "greeting", "by": e["by"], "says": e["text"],
                                  "does": quote_tail(s.get("event", ""), e["by"], e["text"]), "he_said": None, "_step": i})
            if v:
                items.append({**base, "kind": "reply", "by": v.get("by"), "says": v.get("says") or "", "does": v.get("does"),
                              "he_said": dec.get("says"), "_step": i})
    return items


def entry_line(e):
    k = e["k"]
    if k == "bag":
        return f"{e['t']} bought {e['item']} ₹{e.get('price')}"
    if k == "expense":
        return f"{e['t']} paid {e.get('item')} ₹{e.get('amount')} to {e.get('to')}" + (" (settles)" if e.get("settles") else "")
    if k == "income":
        return f"{e['t']} received ₹{e.get('amount')} from {e.get('from')}: {e.get('text', '')}"
    if k == "wear":
        return f"{e['t']} wardrobe: {e['item']}: {e['status']}"
    if k == "people":
        return f"{e['t']} met {e['name']}, {e['role']}"
    if k == "work":
        return f"{e['t']} wrote: {e.get('title')}"
    return f"{e.get('t', '--:--')} [{k}] {e.get('text', '')}"


def day_entries(day, t, cap=8, w=22):
    es, spoke = [], False                    # at the moment itself only what came before anyone spoke (public news, beats, who he met):
    for e in day.get("entries") or []:       # what his act then did (a purchase, a change of coat) is written after, and is not the record yet
        if e.get("t") is not None and e["t"] == t and e["k"] in ("said", "diary"):
            spoke = True
        if e["k"] not in SKIP_KINDS and (e.get("t") is None or e["t"] < t or (e["t"] == t and not spoke)):
            es.append(e)
    lines = [clip(entry_line(e), w) for e in es]
    return lines[-cap:], max(0, len(lines) - cap)


def reduce_state(st, cap=4):
    """What a voice could make claims about, as {category: [lines]} plus counts of what was cut."""
    out, cut = {}, {}

    def put(name, lines, n=cap):
        lines = [clip(x, 22) for x in lines]
        out[name] = lines[:n] or ["none"]
        if len(lines) > n:
            cut[name] = len(lines) - n

    put("file", [st["file"]] if st.get("file") else [])
    put("owed", [f"{o.get('to')} ₹{o.get('amount')} {o.get('why', '')} (since {o.get('since')})" for o in st.get("owed") or []])
    put("engagements", [f"{a.get('date')} {a.get('t') or ''} {a.get('what')}".replace("  ", " ") for a in st.get("engagements") or []])
    put("appointments", [f"{a.get('date')} {a.get('t') or ''} {a.get('what')}".replace("  ", " ") for a in st.get("appointments") or []])
    put("wardrobe", [f"{g.get('item')}: {g.get('status')}" for g in st.get("wardrobe") or []], 5)
    put("flags", [f"{k}={v}" for k, v in (st.get("flags") or {}).items()])
    put("cash", [f"imprest ₹{st['imprest']}" + (f", cash ₹{st['cash']}" if st.get("cash") is not None else "")] if "imprest" in st else [])
    put("people met", [", ".join(st.get("people") or [])] if st.get("people") else [])
    return out, cut


def previous_state(days, date):
    prev = [d for d in days if d["date"] < date]
    if not prev:
        return None, None
    d = prev[-1]
    return d["date"], d.get("state")


def build_context(item, days_by_date, days, earlier):
    day = days_by_date[item["date"]]
    ent, ent_cut = day_entries(day, item["t"])
    pdate, pst = previous_state(days, item["date"])
    state = None
    if pst:
        state, scut = reduce_state(pst)
    prior = [x for x in earlier if x["by"] == item["by"]][-3:]
    ex = [{"date": x["date"], "he_said": clip(x["he_said"], 30) if x["he_said"] else None, "they_said": clip(x["says"], 30)} for x in prior]
    return {"entries": ent, "entries_cut": ent_cut, "state_of": pdate, "state": state, "state_cut": scut if pst else {},
            "earlier_exchanges": ex}


def context_text(c):
    L = ["The day so far (ledger, world and file entries up to this moment):"]
    if c["entries_cut"]:
        L.append(f"  …({c['entries_cut']} more, earlier)")
    L += ["  " + x for x in c["entries"]] or ["  none"]
    L.append(f"The record at the end of the previous recorded day ({c['state_of']}):" if c["state_of"] else "The record at the end of the previous recorded day: none kept.")
    if c["state"]:
        for k, v in c["state"].items():
            more = c["state_cut"].get(k)
            L.append(f"  {k}: " + "; ".join(v) + (f"; …({more} more)" if more else ""))
    L.append("Earlier exchanges with this person (last three):")
    for x in c["earlier_exchanges"]:
        L.append(f"  {x['date']}: he said {('“' + x['he_said'] + '”') if x['he_said'] else '(nothing: they spoke first)'}; they said “{x['they_said']}”")
    if not c["earlier_exchanges"]:
        L.append("  none recorded")
    return "\n".join(L)


def fit(c, budget=BUDGET_WORDS):
    """Shrink the oldest entries first, then the exchanges, until the context fits; the cut is always counted."""
    while words(context_text(c)) > budget and len(c["entries"]) > 1:
        c["entries"] = c["entries"][1:]
        c["entries_cut"] += 1
    while words(context_text(c)) > budget and len(c["earlier_exchanges"]) > 1:
        c["earlier_exchanges"] = c["earlier_exchanges"][1:]   # not counted elsewhere: say so
        c["exchanges_cut"] = c.get("exchanges_cut", 0) + 1
    return c


def context_with_cut_note(c):
    t = context_text(c)
    if c.get("exchanges_cut"):
        t = t.replace("Earlier exchanges with this person (last three):", f"Earlier exchanges with this person (last three; …({c['exchanges_cut']} more cut)):")
    return t


def sheet_item(n, it):
    L = [f"## {n}. {it['id']} · {it['date']} (day {it['day']}), {it['t']}, at {it['place']}", ""]
    L.append(context_with_cut_note(it["context"]))
    L += ["", f"The moment: {clip(it['event'], 120)}", ""]
    L.append(f"He said: “{it['he_said']}”" if it["he_said"] else "He had said nothing; this person spoke first.")
    L += ["", f"**{it['by']} says:** “{it['says']}”"]
    if it["does"]:
        L.append(f"*{it['does']}*")
    return "\n".join(L) + "\n"


LABELS = """# Voice claims: how to read

You will read about a hundred replies that people in the simulation gave to a man (Hegel) in Delhi. For each reply you list what it claims about
the world **outside the sentence itself**, and say whether the record shown with it holds the claim. You do not judge whether the reply is good,
in character or well written.

Read in `sheet.md`. Each item shows the record up to that moment (the day's ledger, world and file entries so far; the end of the previous recorded
day reduced to what a voice could speak of; the last three earlier exchanges with the same person), then what he said, then the reply. Only what is
shown is the record. A line cut with `…(n more)` is cut: treat what it hides as not shown.

## Claims

List every claim, by type:

- **promise**: the speaker will do something, or something will happen by some time.
- **appointment**: a time or place to meet or come back.
- **price**: a price or a sum.
- **third person**: a fact about a third person (someone who is not the speaker and not he).
- **happened**: something that happened before now.
- **place or goods**: a fact about the place, its goods or its hours.
- **other**: any other claim about the world outside the sentence.

Not claims: greetings, opinions, questions, pleasantries, and what the speaker says about the conversation itself. A reply with no claim gets an
empty list. Split a sentence into separate claims when it makes several.

## Marks

One mark for each claim:

- **held**: the record shown holds it.
- **silent**: the record shown says nothing either way.
- **against**: the record shown says otherwise.

Use `silent`, not `held`, when the claim is merely plausible. Use `against` only when something shown contradicts it.

## Follow-up note

For each promise or appointment, add `follow-up: yes|no|unknown` to the item's `note`, left for a later pass (yes: the record later shows it was
kept; no: later record shows it was not; unknown: you cannot tell, or you were not asked to look ahead). If you are not looking ahead, write
`follow-up: unknown`.

## Output

One JSON line per reply, in `labels-<reader>.jsonl`:

```
{"id": "VC001", "claims": [{"text": "...", "type": "promise", "mark": "silent"}], "note": ""}
```

`type` is one of `promise`, `appointment`, `price`, `third person`, `happened`, `place or goods`, `other`. `mark` is one of `held`, `silent`, `against`.
`note` is free text; for a promise or appointment it carries `follow-up: yes|no|unknown`. Work alone; do not look at another reader's lines.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--ref", help="a git ref whose docs/days to read, e.g. origin/shadow")
    src.add_argument("--days", type=Path, help="a folder of day files")
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1831)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    days = days_of_ref(args.ref, args.repo) if args.ref else days_of_folder(args.days)
    days = sorted(days, key=lambda d: d["date"])
    by_date = {d["date"]: d for d in days}
    items = collect(days)
    for k, it in enumerate(items):
        it["context"] = build_context(it, by_date, days, items[:k])
    pool = [it for it in items if (it["says"] or "").strip()]
    sample = random.Random(args.seed).sample(pool, min(args.n, len(pool)))
    for k, it in enumerate(sample, 1):
        it["id"] = f"VC{k:03d}"
        fit(it["context"])
        it["context_words"] = words(context_with_cut_note(it["context"]))
    args.out.mkdir(parents=True, exist_ok=True)
    keep = ("id", "date", "day", "t", "place", "by", "kind", "says", "does", "he_said", "event", "context", "context_words")
    (args.out / "sample.jsonl").write_text("".join(json.dumps({k: it[k] for k in keep}, ensure_ascii=False) + "\n" for it in sample), encoding="utf-8")
    (args.out / "sheet.md").write_text("# Voice claims: sheet\n\n" + "\n".join(sheet_item(k, it) for k, it in enumerate(sample, 1)), encoding="utf-8")
    (args.out / "LABELS-TEMPLATE.md").write_text(LABELS, encoding="utf-8")
    nums = [d.get("n") for d in days if d.get("n") is not None]
    per_range = Counter(f"days {n // 10 * 10}-{n // 10 * 10 + 9}" for n in (it["day"] for it in pool))
    cw = [it["context_words"] for it in sample]
    pop = {"source": args.ref or str(args.days), "seed": args.seed, "n_asked": args.n, "n_drawn": len(sample),
           "days_read": len(days), "day_numbers": [min(nums), max(nums)] if nums else None,
           "replies_recorded": len(items), "population": len(pool),
           "by_kind": dict(Counter(it["kind"] for it in pool)),
           "by_voice": dict(Counter(it["by"] for it in pool).most_common()),
           "by_day": dict(sorted(Counter(f"{it['date']} (day {it['day']})" for it in pool).items())),
           "by_day_range": dict(sorted(per_range.items(), key=lambda x: int(x[0].split()[1].split("-")[0]))),
           "sample_by_voice": dict(Counter(it["by"] for it in sample).most_common()),
           "context_words": {"median": statistics.median(cw), "max": max(cw)} if cw else None}
    (args.out / "population.json").write_text(json.dumps(pop, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"population {len(pool)} (of {len(items)} recorded); drew {len(sample)}; context words median/max {pop['context_words']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
