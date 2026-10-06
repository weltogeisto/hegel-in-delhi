"""His manuscripts: what he writes when he sits down to write, and the index of his works in state["works"]."""
import re

from .clock import MONTHS
from .contract import SITTING_ASK, SITTING_FORMAT, WRITE_ASK, WRITE_FORMAT, WRITING_KINDS

CAP = 3000              # characters a sitting may run to (about 450 words)
TOKENS = 700            # what a plain-text completion may run to
MIN_WORDS = 20          # a completion with fewer words is unusable
TAIL = 800              # characters of the latest sitting kept in the index, for the next one to flow on from
CARRY = 120             # words of that tail that go into the next prompt

# The plain-text prompt: a header line in the style of his books, the argument as an editor's line in square brackets, a blank line, then the
# salutation of a new letter or the tail of the sitting before.
HEADERS = {"essay": "Hegel, {title}. Written at Delhi, {date}.",
           "letter": "Hegel to {to}. Delhi, {date}.",
           "poem": "Hegel, {title}. A poem, written at Delhi, {date}."}
ARGUMENT = "[{about}]"
HEADLINE = re.compile(r"Hegel,|Hegel to\b")
ENDING = re.compile(r"(\*\s*){3,}$|(?i:THE END|FOOTNOTES?)[.:]?$")
SENTENCE_END = re.compile(r"[.!?][\"')\]]*(?=\s|$)")
STRAIGHT = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


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


def line(x, n):
    """x as one line of at most n characters, '' if it is not text."""
    return " ".join(x.split())[:n].strip() if isinstance(x, str) else ""


def outline(out):
    """What he means to write, from the mind's answer, or None if it is unusable: a title and what the sitting is about at least."""
    if not isinstance(out, dict):
        return None
    title, about = line(out.get("title"), 100), line(out.get("about"), 200).replace("[", "(").replace("]", ")")
    if not title or not about:
        return None
    return {"title": title, "kind": out["kind"] if out.get("kind") in WRITING_KINDS else "other", "to": line(out.get("to"), 80) or None,
            "continues": out.get("continues") is True, "about": about}


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


def tail_of(text):
    """The last TAIL characters of text, from the start of a word."""
    if len(text) <= TAIL:
        return text.strip()
    head, tail = text[:-TAIL], text[-TAIL:]
    return (tail if head[-1].isspace() or tail[0].isspace() else re.sub(r"^\S+\s*", "", tail)).strip()


def carried(tail):
    """The last CARRY words of tail, with their paragraph breaks."""
    words = list(re.finditer(r"\S+", tail))
    return tail[words[-CARRY].start():] if len(words) > CARRY else tail.strip()


def file(state, w, d):
    """Enter a sitting in state["works"], on the manuscript it continues or on a new one. Returns its entry for the page."""
    works, n = state.setdefault("works", []), len(w["text"].split())
    work = find(works, w["title"]) if w["continues"] else None
    if work:
        work.update(words=work["words"] + n, sittings=work["sittings"] + 1, last=d.isoformat(), tail=tail_of(w["text"]))
    else:
        work = {"id": slug(works, w["title"]), "title": w["title"], "kind": w["kind"], "to": w["to"],
                "started": d.isoformat(), "words": n, "sittings": 1, "last": d.isoformat(), "tail": tail_of(w["text"])}
        works.append(work)
    entry = {"k": "writing", "title": work["title"], "kind": work["kind"], "to": work["to"], "sitting": work["sittings"],
             "text": w["text"], "work": work["id"], "words": n}
    for k in ("mode", "about"):
        if w.get(k):
            entry[k] = w[k]
    return entry


def manuscripts(state):
    """' Your manuscripts so far: ...' with his latest five, so that he can say which one he carries on; '' if there are none."""
    shelf = [f"“{x['title']}” ({x['kind']}, {x['sittings']} sitting{'s' if x['sittings'] > 1 else ''})" for x in (state.get("works") or [])[-5:]]
    return " Your manuscripts so far: " + "; ".join(shelf) + "." if shelf else ""


def ask(state):
    """The question for the chat call that writes the whole sitting."""
    return WRITE_ASK + manuscripts(state) + " " + WRITE_FORMAT


def sitting_ask(state):
    """The question for the chat call that only says what the sitting is: no text."""
    return SITTING_ASK + manuscripts(state) + " " + SITTING_FORMAT


def prompt(plan, state, d):
    """(the prompt for a plain-text completion of the sitting, its opening line): the header in the style of his books for the day d, the
    argument in square brackets and a blank line, then the last words of the manuscript's latest sitting when he carries one on (one from before
    the index kept tails starts fresh), or the salutation of a new letter, which is the opening line that his text begins with ('' otherwise)."""
    work = find(state.get("works") or [], plan["title"]) if plan["continues"] else None
    src = work or plan
    kind = src["kind"] if src["kind"] != "letter" or src["to"] else "essay"
    when = f"{d.day} {MONTHS[d.month - 1]} {d.year}"
    header = HEADERS.get(kind, HEADERS["essay"]).format(title=src["title"].rstrip("."), to=src["to"], date=when)
    head = header + "\n" + ARGUMENT.format(about=plan["about"]) + "\n\n"
    carry = carried((work or {}).get("tail") or "")
    opening = (f"Dear {plan['to']}," if plan["to"][:1].isupper() else "Dear friend,") if kind == "letter" and not work else ""
    return head + (carry or (opening + "\n\n" if opening else "")), opening


def echoes(text, title, opening):
    """Is this line one that the prompt already has: the title, a header, the argument or the salutation?"""
    key = lambda x: re.sub(r"\W+", " ", x.lower()).strip()
    return key(text) == key(title) or HEADLINE.match(text) or text[:1] == "[" and text[-1:] == "]" or bool(opening) and text == opening


def sitting(plan, raw, opening=""):
    """The sitting from a plain-text completion, or None if it is unusable. The model may say the title or header again, or run on into another
    document: leading echoes are dropped, and the text stops at a line that begins a new header or is only "* * *", THE END or Footnotes.
    Paragraphs stay (and a poem's lines), other whitespace is collapsed, quotes are straight, and the text is cut to CAP and back to its last
    sentence end (a poem's not); fewer than MIN_WORDS words is unusable. A new letter's opening line goes in front."""
    poem, body = plan["kind"] == "poem", []
    for ln in (x.strip() for x in (raw or "").replace("\r\n", "\n").translate(STRAIGHT).replace("--", "—").split("\n")):
        if not body and (not ln or echoes(ln, plan["title"], opening)):
            continue
        if HEADLINE.match(ln) or ENDING.match(ln):
            break
        body.append(ln)
    paras = [("\n" if poem else " ").join(" ".join(x.split()) for x in p.split("\n") if x.strip()) for p in re.split(r"\n\s*\n", "\n".join(body))]
    text = cut("\n\n".join(p for p in paras if p), CAP - (len(opening) + 2 if opening else 0))
    ends = [m.end() for m in SENTENCE_END.finditer(text)]
    if not poem and not (ends and ends[-1] == len(text)):
        text = text[:ends[-1]] if ends else ""
    if len(text.split()) < MIN_WORDS:
        return None
    return {"title": plan["title"], "kind": plan["kind"], "to": plan["to"], "continues": plan["continues"], "about": plan["about"],
            "text": opening + "\n\n" + text if opening else text}
