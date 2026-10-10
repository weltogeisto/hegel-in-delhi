"""Memory from the day files: what Hegel recalls of the people in front of him, of the place he is in and of the
last nights. No embeddings and no index; the day files are the record and are read most recent first.

The Engine owns this, so that the World stays free of file I/O. Past days are read once per Engine."""
import re
from datetime import date, timedelta

from . import contract, owl
from .clock import WEEKDAYS

DAYNAMES = [w[:3] for w in WEEKDAYS]
LOOKBACK, NIGHTS = 14, 3                  # days of day files to look through; nights of the owl's diary to recall
PER_PERSON, MAX_LINES, MAX_CHARS, MAX_TOTAL = 3, 8, 220, 850     # MAX_TOTAL: characters for the whole section
GIST, WINDOW = 90, 6                      # characters of a diary; steps in 'Earlier today'
TITLES = {"mr", "mrs", "ms", "dr", "shri", "smt"}


def when(day):
    """'Day 3 (Sat 3 Oct)'."""
    d = date.fromisoformat(day["date"])
    return f"Day {day['n']} ({DAYNAMES[d.weekday()]} {d.day} {d.strftime('%b')})"


def fit(head, text, quote=False):
    """head and text in at most MAX_CHARS, cutting the text at a word."""
    q = ("“", "”") if quote else ("", "")
    room = MAX_CHARS - len(head) - len(q[0]) - len(q[1])
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > room:
        text = text[:room - 1].rsplit(" ", 1)[0].rstrip(" ,;:-—") + "…"
    return head + q[0] + text + q[1]


def moment(label, e, pov=None):
    """One line for one entry of the record. With pov, a person's name, the same seen from that person's side."""
    head, k = f"{label}, {e['t']}, ", e["k"]
    if k == "said" and pov:
        who = "you said: " if (e.get("by") or "").lower() == pov.lower() else f"{e['by']} said: " if e.get("by") else \
            f"he said to {e['to']}: " if e.get("to") else "he said: "
        return fit(head + who, e["text"], quote=True)
    if k == "said":
        who = f"{e['by']} said to you: " if e.get("by") else f"to {e['to']}: " if e.get("to") else "you said: "
        return fit(head + who, e["text"], quote=True)
    if k == "people":
        return fit(head + f"you met {e['name']}: ", e["text"])
    if k == "diary":
        return fit(head + "you thought: ", e["text"], quote=True)
    return fit(head + ("the file: " if k == "file" else ""), e["text"])


def names_of(c):
    """How he would name a cast member: the full name, and the surname (or, with no title, the first name)."""
    if c.get("background"):
        return {c["name"]}
    words = [w.strip(".") for w in c["name"].split()]
    named = [w for w in words if len(w) > 1 and w.lower() not in TITLES]
    return {c["name"]} | ({named[-1] if len(named) < len(words) else named[0]} if named else set())


def involves(c, pat, e):
    """Does entry e concern cast member c?"""
    k = e["k"]
    if k == "said":
        return bool(pat.search(e.get("to", "")) or pat.search(e.get("by", "")))
    if k == "people":
        return e.get("name") == c["name"]
    return k in ("diary", "world", "file") and bool(pat.search(e["text"]))


def strings(v):
    """Every piece of text in an entry, however it is nested."""
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for k, x in v.items():
            if k not in ("k", "t", "sprite"):
                yield from strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from strings(x)


def record_text(day):
    """All the text of a day: its entries, whatever their kind, and what happened at each step."""
    return "\n".join(list(strings(day.get("entries") or [])) + [s.get("event") or "" for s in day.get("steps") or []])


def encountered_text(day):
    """Evidence of exposure, not proof a received claim is true.

    A thought, manuscript, intention, own utterance or owl interpretation cannot
    introduce a modern name into the knowledge gate. The full record remains
    available through record_text and the attributed recall functions.
    """
    parts = []
    for entry in day.get("entries") or []:
        kind = entry.get("k")
        if kind in {"world", "people", "file", "wear", "bag", "read"} or (kind == "said" and entry.get("by")):
            parts.extend(strings(entry))
    for step in day.get("steps") or []:
        parts.append(step.get("event") or "")
        parts.extend(x["text"] for x in step.get("shelf_exposure") or [] if isinstance(x.get("text"), str))
    return "\n".join(parts)


class Memory:
    def __init__(self, days, world):
        self.days, self.world = days, world
        self._days, self._text, self._known = {}, {}, None

    def load(self, d):
        """A past day, read once: again only if the file has changed since (the owl writes to it overnight)."""
        key, p = d.isoformat(), self.days.path(d)
        if not p.exists():
            return None
        stamp = (p.stat().st_mtime_ns, p.stat().st_size)
        if key not in self._days or self._days[key][0] != stamp:
            self._days[key] = (stamp, self.days.load(d))
        return self._days[key][1]

    def before(self, d, n=LOOKBACK):
        """The days before date d, most recent first, up to n days back."""
        for i in range(1, n + 1):
            day = self.load(d - timedelta(days=i))
            if day:
                yield day

    def trail(self, day, past, window=True):
        """(when, entry) of his record, newest first: today before the 'Earlier today' window (all of it without),
        then each past day."""
        steps = (day.get("steps") or [])[-WINDOW:]
        cut = steps[0]["t"] if steps and window else "00:00" if window else "24:00"
        for e in reversed(sorted((e for e in day["entries"] if e["t"] < cut), key=lambda e: e["t"])):
            yield "Today", e
        for p in past:
            for e in reversed(sorted(p["entries"], key=lambda e: e["t"])):
                yield when(p), e

    def recall(self, sit, ctx, day):
        """The lines under 'You remember': his last moments with each person present, the last thing he thought
        in this place, and the owl's gist of the last three nights. At most MAX_LINES lines and MAX_TOTAL characters,
        each line at most MAX_CHARS. Over budget, a person's oldest moment goes first, then the older nights, then the
        place; last night and one moment with each person stay."""
        d = date.fromisoformat(day["date"])
        past, taken, groups = list(self.before(d)), set(), []
        for cid in ctx["present"]:
            c = self.world.cast[cid]
            if c.get("background"):
                continue
            mine = self.moments(c, day, past, taken)
            if mine:
                groups.append(mine)
        place = self.place_line(sit["place"], past)
        nights = [fit(f"{when(p)}, as the owl wrote it up: ", owl.gist(p["owl"]["diary"], GIST)) for p in past
                  if (d - date.fromisoformat(p["date"])).days <= NIGHTS and (p.get("owl") or {}).get("diary")]
        lines = lambda: nights[::-1] + place + [m for g in groups for m in g]
        while len(lines()) > MAX_LINES or sum(len(x) + 3 for x in lines()) > MAX_TOTAL:
            big = max(groups, key=len, default=[])
            if len(big) > 1:
                big.pop(0)
            elif len(nights) > 1:
                nights.pop()                                    # the oldest night
            elif place:
                place = []
            else:
                break
        return lines()

    def moments(self, c, day, past, taken=None, voice=False):
        """His last PER_PERSON moments with cast member c, oldest first. Those in `taken` are passed over, those found
        are added. For a voice: only what was said, in c's eyes, and all of today's."""
        pat = re.compile(r"\b(" + "|".join(re.escape(x) for x in names_of(c)) + r")\b", re.I)
        taken, mine = set() if taken is None else taken, []
        for label, e in self.trail(day, past, window=not voice):
            key = (label, e["t"], e["k"], e.get("text") or e.get("name"))
            if key not in taken and (not voice or e["k"] == "said") and involves(c, pat, e):
                taken.add(key)
                mine.append(moment(label, e, c["name"] if voice else None))
                if len(mine) == PER_PERSON:
                    break
        return mine[::-1]

    def place_line(self, pid, past):
        """The last thought he had here on an earlier day, as a list of one line or none."""
        for p in past:
            for s in reversed(p.get("steps") or []):
                dec = s.get("decision") or {}
                if dec.get("place") == pid and (dec.get("thought") or "").strip():
                    return [fit(f"{when(p)}, {s['t']}, {self.world.places[pid]['at']}, you thought: ", dec["thought"], quote=True)]
        return []

    def manuscripts(self, day, before_time=None, limit=9000):
        """Earlier text of the latest three works, attributed as drafts, not facts.

        Read the first and two latest sittings of each work, including across day
        boundaries. The current in-memory day wins over its saved copy. No future
        day or later sitting is eligible. No generated summary changes the text.
        """
        works = (day.get("state", {}).get("works") or [])[-3:]
        ids = {w.get("id") for w in works if w.get("id")}
        if not ids:
            return ""
        start = min((w.get("started", day["date"]) for w in works))
        past_dates = sorted({r["date"] for r in self.days.index()["days"] if start <= r["date"] < day["date"]})
        prior = [self.load(date.fromisoformat(d)) for d in past_dates] + [day]
        groups = {key: [] for key in ids}
        for old in prior:
            if not old:
                continue
            for entry in old.get("entries", []):
                if entry.get("k") != "writing" or entry.get("work") not in ids:
                    continue
                if old["date"] == day["date"] and before_time and entry.get("t", "24:00") >= before_time:
                    continue
                groups[entry["work"]].append((old["date"], entry))
        from .works import manuscript_excerpts
        selected = []
        for work in works:
            rows = sorted(groups.get(work.get("id"), []), key=lambda pair: (pair[0], pair[1]["t"], pair[1].get("sitting", 0)))
            if not rows:
                continue
            indices = sorted({0, *range(max(0, len(rows) - 2), len(rows))})
            selected.append((work, [rows[i] for i in indices]))
        return manuscript_excerpts(selected, limit=limit)

    def recent_thoughts(self, day, n=12):
        """(time, text) of his last n thoughts, oldest first: today's, and the end of yesterday's if today has fewer."""
        out = [(e["t"], e["text"]) for e in day["entries"] if e["k"] == "diary"][-n:]
        for p in self.before(date.fromisoformat(day["date"])):
            if len(out) >= n:
                break
            out = [(e["t"], e["text"]) for e in p["entries"] if e["k"] == "diary"][-(n - len(out)):] + out
        return out

    def known_before(self, date_str):
        """Observed/received material before date_str, refreshed when a source file changes."""
        paths = [p for p in sorted(self.days.dir.glob("????-??-??.json")) if p.stem < date_str]
        stamps = tuple((p.stem, p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
        if not self._known or self._known[0] != stamps:
            for p, stamp in zip(paths, stamps):
                if p.stem not in self._text or self._text[p.stem][0] != stamp:
                    self._text[p.stem] = (stamp, encountered_text(self.days.load(p.stem)))
            self._known = (stamps, "\n".join(self._text[p.stem][1] for p in paths))
        return self._known[1]

    def known_text(self, day, sit):
        """Past and current exposure; recalled thoughts and intentions are not new evidence."""
        current = {k: v for k, v in sit.items() if k not in {"on_mind", "remember", "earlier"}}
        return "\n".join([self.known_before(day["date"]), encountered_text(day), contract.render(current)])
