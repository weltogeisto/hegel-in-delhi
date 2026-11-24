"""HEGEL_PAPERS: what he reads in the day's papers and what the engine keeps of it (pc/PAPERS.md).

The pieces themselves live in the state folder (Feeds.pieces). What reaches the day file is the title, the source, the link and where to find the
piece again; what the engine keeps of his reading is state["readings"], with the line of his own thought that followed. No call to a model."""
import re
from datetime import date

KEEP, WINDOW, LINE, SHOWN = 40, 14, 160, 5      # readings kept; days a story may run; characters of his line; readings in the manuscripts' block
STOP = {"about", "after", "again", "against", "along", "among", "amid", "being", "could", "delhi", "first", "india", "indian", "other", "over",
        "their", "there", "these", "those", "three", "under", "until", "union", "where", "which", "while", "would", "years", "state", "says",
        "said", "centre", "government", "minister", "ahead", "since", "before"}


def words(text):
    """The content words of a title: lower-case letters, five or more, not in the stop list."""
    return {w for w in re.findall(r"[a-z]+", (text or "").lower()) if len(w) >= 5 and w not in STOP}


def first_line(thought, n=LINE):
    """The first sentence of his thought, at most n characters (cut at a word)."""
    text = " ".join((thought or "").split())
    one = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return one if len(one) <= n else one[:n - 1].rsplit(" ", 1)[0].rstrip(" ,;:-—") + "…"


def trace(state, seen, thought):
    """Keep that he read this piece (`seen`, from the situation), with his own first sentence after it: the latest KEEP readings."""
    row = {"date": seen["date"], "title": seen["title"], "source": seen["source"], "line": first_line(thought),
           "piece": seen["piece"]}                           # `piece`: [date, index], to find the text again in the state folder
    state["readings"] = ((state.get("readings") or []) + [row])[-KEEP:]


def nice(day):
    d = date.fromisoformat(day)
    return f"{d.day} {d.strftime('%B')}"


def story(readings, headlines, d):
    """(index of the headline, the note) for the first of today's headlines that continues a title he read in the last WINDOW days
    (two content words in common), or None. The note gives his own line back."""
    for i, h in enumerate(headlines):
        mine = words(h)
        for r in reversed(readings or []):
            if r.get("line") and 0 < (d - date.fromisoformat(r["date"])).days <= WINDOW and len(mine & words(r["title"])) >= 2:
                return i, f'(You read of this on {nice(r["date"])}: "{r["line"]}")'
    return None


def block(readings, n=SHOWN):
    """'What you have read lately': the latest n readings, each with his line. '' if there are none."""
    rows = [f"- {nice(r['date'])}, {r['source']}, “{r['title']}”" + (f": you thought “{r['line']}”" if r.get("line") else "")
            for r in (readings or [])[-n:]]
    return "What you have read lately:\n" + "\n".join(rows) if rows else ""


def read_text(readings, feeds):
    """Titles and summaries of what he read, as the claim gate takes them: he has met them."""
    out = []
    for r in readings or []:
        p = feeds.piece(date.fromisoformat(r["piece"][0]), r["piece"][1]) if feeds and r.get("piece") else None
        out.append(r["title"] + (" " + p["summary"] if p else ""))
    return "\n".join(out)
