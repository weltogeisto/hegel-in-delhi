"""His manuscripts: what he writes when he sits down to write, and the index of his works in state["works"]."""
import json
import random
import re
from pathlib import Path

from .clock import DAY_ONE, MONTHS, day_number
from .contract import SITTING_ASK, SITTING_FORMAT, WRITE_ASK, WRITE_FORMAT, WRITING_KINDS
from .shelf import sentences

REPO = Path(__file__).resolve().parent.parent
CAP = 3000              # characters a sitting may run to (about 450 words)
TOKENS = 600            # what a plain-text completion may run to
MIN_WORDS = 20          # a completion with fewer words is unusable
TAIL = 800              # characters of the latest sitting kept in the index, for the next one to flow on from
CARRY = 120             # words of that tail that go into the next prompt

# The plain-text prompt: two passages of his English books, each a short document under a header that names its topic, so that the model sees a
# header decide what follows (EXEMPLAR, from QUESTIONS); then the writing's own header in the same shape, the argument and a note on his
# situation as the editor's lines in square brackets, a blank line, then the salutation of a new letter or the tail of the sitting before.
QUESTIONS = "mind/hegeltest/questions.json"      # the Hegel test's hand-cleaned passages, each with a "topic", a "work" and the "passage"
EXEMPLAR = "Hegel, On {topic}. From the {work}.\n\n{text}\n\n\n"
SHOWN = 2               # exemplars in front of the header
COPY_RUN = 8            # words in a row that a sitting may not share with an exemplar
HEADERS = {"essay": "Hegel, {title}. Written at Delhi, {date}.",
           "letter": "Hegel to {to}. Delhi, {date}.",
           "poem": "Hegel, {title}. A poem, written at Delhi, {date}."}
ARGUMENT = "[{about}]"
NOTE = "[He died at Berlin in November 1831, professor of philosophy there, and woke in Delhi on {woke}{ago}.]"      # as mind/soul.md has him
NUMBERS = "zero one two three four five six seven eight nine ten eleven twelve".split()         # the days that are told in words
HEADLINE = re.compile(r"Hegel, \S|Hegel to\b")          # a header, of an exemplar or of a writing: a new document
CLOSING = r"(?i:(?:(?:ever|always|most|very|as ever)[ ,]+)*(?:yours|your (?:(?:most|ever|very) )?(?:faithful|friend|affectionate|loving|devoted|obedient|humble|sincere|old)))\b"
FILLER = r"(?:(?i:ever|always|very|most|truly|sincerely|faithfully|affectionately|devotedly|friend|servant|and|my|dear)|[A-Z][\w.]*)"
SIGN_OFF = re.compile(CLOSING + r"(?:[ ,]+" + FILLER + r"){0,6}[ ,.]*$")      # "Yours ever," "Your faithful friend, Hegel": a short closing line, with the name if it has one
SIGNATURE = re.compile(r"(?:(?:G\. ?W\. ?F\.|Georg|Wilhelm|Wilh\.|Friedrich|G\.|W\.|F\.) )*Hegel[.,]?$")      # a line that is only his name
IDLE = set("""about above after again against among around because before being below between cannot could doing during every first having itself might never
other shall should since still their there these those through under until using where whether which while whose would without within""".split())
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


def when(d):
    """'6 October 2026'."""
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def note(d):
    """The editor's note on his situation on the day d: that he died at Berlin in November 1831, where he was professor of philosophy, and woke in
    Delhi on clock.DAY_ONE; and how long ago that is, where the day is not before it."""
    days = day_number(d) - 1
    ago = "" if days < 0 else ", this morning" if days == 0 else ", yesterday" if days == 1 else f", {NUMBERS[days] if days < len(NUMBERS) else days} days ago"
    return NOTE.format(woke=when(DAY_ONE), ago=ago)


_passages = {}


def passages(repo=REPO):
    """The passages of the Hegel test in repo/QUESTIONS as [{"topic", "work", "text"}], read once per process and repo. [] if the file is missing
    or is not as expected (and then looked at again next time)."""
    path = Path(repo) / QUESTIONS
    if path not in _passages:
        try:
            rows = [q for q in json.loads(path.read_text(encoding="utf-8"))["questions"] if isinstance(q, dict) and isinstance(q.get("passage"), str)]
        except (OSError, ValueError, KeyError, TypeError):
            return []
        got = [{"topic": line(q.get("topic"), 80), "work": line(q.get("work"), 80), "text": q["passage"].strip()} for q in rows]
        got = [x for x in got if x["topic"] and x["work"] and x["text"]]
        if not got:
            return []
        _passages[path] = got
    return _passages[path]


def words(text, n):
    """The words of text of at least n letters, in lower case, a plural s dropped."""
    return {w[:-1] if w.endswith("s") and not w.endswith("ss") else w for w in re.findall(r"[^\W\d_]+", text.lower()) if len(w) >= n}


def exemplars(plan, d, repo=REPO):
    """The passages that stand in front of the header, [{"topic", "work", "text"}]: SHOWN of them, drawn by a seed from the title and the day, from
    those whose topic shares no word with the title or what the sitting is about, so that none is the real passage on its subject. A word is one
    of four letters or more (of three, for a topic with none longer, as 'war'), in lower case, a plural s dropped. Fewer if fewer qualify; []
    if the file is missing."""
    taken = words(plan["title"] + " " + plan["about"], 3)
    fit = [x for x in passages(repo) if not (words(x["topic"], 4) or words(x["topic"], 3)) & taken]
    return random.Random(f"{plan['title']}|{d.isoformat()}").sample(fit, min(SHOWN, len(fit)))


def prompt(plan, state, d, shown=()):
    """(the prompt for a plain-text completion of the sitting, its opening line): the exemplars `shown` (works.exemplars), each as a document of
    its own; then the header in the style of his books for the day d, the argument and the note on his situation in square brackets and a blank
    line; then the last words of the manuscript's latest sitting when he carries one on (one from before the index kept tails starts fresh), or
    the salutation of a new letter, which is the opening line that his text begins with ('' otherwise)."""
    work = find(state.get("works") or [], plan["title"]) if plan["continues"] else None
    src = work or plan
    kind = src["kind"] if src["kind"] != "letter" or src["to"] else "essay"
    header = HEADERS.get(kind, HEADERS["essay"]).format(title=src["title"].rstrip("."), to=src["to"], date=when(d))
    head = "".join(EXEMPLAR.format(**x) for x in shown) + header + "\n" + ARGUMENT.format(about=plan["about"]) + "\n" + note(d) + "\n\n"
    carry = carried((work or {}).get("tail") or "")
    opening = (f"Dear {plan['to']}," if plan["to"][:1].isupper() else "Dear friend,") if kind == "letter" and not work else ""
    return head + (carry or (opening + "\n\n" if opening else "")), opening


def fold(x):
    """x in lower case with punctuation and whitespace folded: what two sentences must share to be the same."""
    return re.sub(r"\W+", " ", x.lower()).strip()


def fresh(paras):
    """paras without the sentences that repeat an earlier sentence (in any paragraph), and without the paragraphs that are left empty by it, which
    is every paragraph that repeats an earlier one."""
    seen, out = set(), []
    for para in paras:
        keep = []
        for s in sentences(para):
            key = fold(s)
            if not key or key not in seen:
                keep.append(s)
                seen.add(key)
        if keep:
            out.append(" ".join(keep))
    return out


def echoes(text, title, opening):
    """Is this line one that the prompt already has: the title, a header, the argument or the salutation?"""
    return fold(text) == fold(title) or HEADLINE.match(text) or text[:1] == "[" and text[-1:] == "]" or bool(opening) and text == opening


def sitting(plan, raw, opening=""):
    """The sitting from a plain-text completion, or None if it is unusable. The model may say the title or header again, or run on into another
    document: leading echoes are dropped, and the text stops at a line that begins a new section or document (a "§", a header) or is only
    "* * *", THE END or Footnotes. A letter stops after its sign-off ("Yours ever,", or his name alone), which stays with the signature line
    that follows it, if there is one, as a paragraph of its own. Paragraphs stay (and a poem's lines), other whitespace is collapsed, quotes are
    straight, a sentence that repeats an earlier one of the sitting goes (and a paragraph with it, if nothing else is left of it; a poem's
    refrains stay), and the text is cut to CAP and back to its last sentence end (a poem's not); fewer than MIN_WORDS words is unusable. A new
    letter's opening line goes in front."""
    poem, letter, body, close = plan["kind"] == "poem", plan["kind"] == "letter", [], []
    lines = [x.strip() for x in (raw or "").replace("\r\n", "\n").translate(STRAIGHT).replace("--", "—").split("\n")]
    for i, ln in enumerate(lines):
        if not body and (not ln or echoes(ln, plan["title"], opening)):
            continue
        if HEADLINE.match(ln) or ln.startswith("§") or ENDING.match(ln):
            break
        if letter and (SIGN_OFF.match(ln) or SIGNATURE.match(ln)):
            after = next((x for x in lines[i + 1:] if x), "")
            close = [ln] + ([after] if SIGN_OFF.match(ln) and SIGNATURE.match(after) else [])
            break
        body.append(ln)
    paras = [("\n" if poem else " ").join(" ".join(x.split()) for x in p.split("\n") if x.strip()) for p in re.split(r"\n\s*\n", "\n".join(body))]
    text = "\n\n".join(p for p in (paras if poem else fresh(paras)) if p)
    kept = cut(text, CAP - (len(opening) + 2 if opening else 0) - (len("\n".join(close)) + 2 if close else 0))
    ends = [m.end() for m in SENTENCE_END.finditer(kept)]
    signed = "\n".join(close) if kept == text else ""          # a sign-off belongs to a page that is all here
    if not poem and not (ends and ends[-1] == len(kept)):
        kept = kept[:ends[-1]] if ends else ""
    if len(kept.split()) < MIN_WORDS:
        return None
    kept = kept + "\n\n" + signed if signed else kept
    return {"title": plan["title"], "kind": plan["kind"], "to": plan["to"], "continues": plan["continues"], "about": plan["about"],
            "text": opening + "\n\n" + kept if opening else kept}


def flaw(plan, w, shown, opening=""):
    """Why the sitting w (from works.sitting) must not stand, or None: it copies an exemplar of `shown` (a run of COPY_RUN words, in lower case and
    without punctuation, that both have), or it is off the subject (the plan's title and what it is about have words of five letters or more that
    are not IDLE, and none of them is in the text, without the salutation `opening`)."""
    text = w["text"][len(opening):]
    run = fold(text).split()
    grams = {tuple(run[i:i + COPY_RUN]) for i in range(len(run) - COPY_RUN + 1)}
    for x in shown:
        theirs = fold(x["text"]).split()
        if any(tuple(theirs[i:i + COPY_RUN]) in grams for i in range(len(theirs) - COPY_RUN + 1)):
            return f"copies the exemplar on {x['topic']}"
    about = words(plan["title"] + " " + plan["about"], 5) - IDLE
    if about and not about & words(text, 5):
        return "is off the subject: it has none of " + ", ".join(sorted(about)[:8])
    return None
