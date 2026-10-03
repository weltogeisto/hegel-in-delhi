"""His manuscripts: what he writes when he sits down to write, and the index of his works in state["works"]."""
import re

from .contract import WRITE_ASK, WRITE_FORMAT, WRITING_KINDS

CAP = 3000              # characters a sitting may run to (about 450 words)


def cut(text, n=CAP):
    """text in at most n characters: cut at the last sentence end in the final fifth, or else at a word."""
    if len(text) <= n:
        return text
    head = text[:n]
    end = max(head.rfind(x) for x in (". ", "! ", "? ", ".\n"))
    return head[:end + 1] if end >= n * 0.8 else head.rsplit(" ", 1)[0].rstrip(" ,;:-—") + "…"


def clean(out):
    """The sitting from the mind's answer, or None if it is unusable: a title and some text at least."""
    if not isinstance(out, dict):
        return None
    title = " ".join(out["title"].split())[:100] if isinstance(out.get("title"), str) else ""
    text = out["text"].strip() if isinstance(out.get("text"), str) else ""
    if not title or len(text) < 20:
        return None
    to = " ".join(out["to"].split())[:80] if isinstance(out.get("to"), str) else ""
    return {"title": title, "kind": out["kind"] if out.get("kind") in WRITING_KINDS else "other", "to": to or None,
            "continues": out.get("continues") is True, "text": cut(text)}


def find(works, title):
    """The latest manuscript called title, in any case, or None."""
    key = " ".join(title.lower().split())
    return next((w for w in reversed(works) if " ".join(w["title"].lower().split()) == key), None)


def slug(works, title):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "work"
    ids, n, out = {w["id"] for w in works}, 1, base
    while out in ids:
        n += 1
        out = f"{base}-{n}"
    return out


def file(state, w, d):
    """Enter a sitting in state["works"], on the manuscript it continues or on a new one. Returns its entry for the page."""
    works, n = state.setdefault("works", []), len(w["text"].split())
    work = find(works, w["title"]) if w["continues"] else None
    if work:
        work.update(words=work["words"] + n, sittings=work["sittings"] + 1, last=d.isoformat())
    else:
        work = {"id": slug(works, w["title"]), "title": w["title"], "kind": w["kind"], "to": w["to"],
                "started": d.isoformat(), "words": n, "sittings": 1, "last": d.isoformat()}
        works.append(work)
    return {"k": "writing", "title": work["title"], "kind": work["kind"], "to": work["to"], "sitting": work["sittings"],
            "text": w["text"], "work": work["id"], "words": n}


def ask(state):
    """The question, with his latest manuscripts so that he can say which one he carries on."""
    shelf = [f"“{x['title']}” ({x['kind']}, {x['sittings']} sitting{'s' if x['sittings'] > 1 else ''})" for x in (state.get("works") or [])[-5:]]
    return WRITE_ASK + (" Your manuscripts so far: " + "; ".join(shelf) + "." if shelf else "") + " " + WRITE_FORMAT
