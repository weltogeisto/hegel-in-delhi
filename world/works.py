"""His manuscripts: what he writes when he sits down to write, and the index of his works in state["works"]."""
import re
import string
from collections import Counter

from .clock import MONTHS, day_number
from .contract import SITTING_ASK, SITTING_FORMAT, WRITE_ASK, WRITE_FORMAT, WRITING_KINDS
from .shelf import sentences

CAP = 3000              # characters a sitting may run to (about 450 words)
TOKENS = 600            # what a plain-text completion may run to
MIN_WORDS = 20          # a completion with fewer words is unusable
TAIL = 800              # characters of the latest sitting kept in the index, for the next one to flow on from
CARRY = 120             # words of that tail that go into the next prompt

# The plain-text prompt: a passage of his English books as a document of its own (PRIMER), then a header line in the style of his books, the
# argument and a note on his situation as the editor's lines in square brackets, a blank line, then the salutation of a new letter or the tail
# of the sitting before.
PRIMER = "{head}\n\n{text}\n\n\n"
PRIMER_WORDS = (80, 220)        # the passages of the shelf that will do
PRIMER_HEADS = {                # the header line of each English book as the training corpus has it (tools/train_data.py header()), without the ref
    "wallace-logic": "Hegel, The Logic of Hegel, tr. William Wallace (1892)",
    "wallace-mind": "Hegel's Philosophy of Mind, tr. William Wallace (1894)",
    "dyde-right": "Hegel's Philosophy of Right, tr. S. W. Dyde (1896)",
    "sibree-history": "Hegel, Lectures on the Philosophy of History, tr. J. Sibree (1857)",
    "haldane-1": "Hegel, Lectures on the History of Philosophy, volume I, tr. E. S. Haldane (1892)",
    "haldane-2": "Hegel, Lectures on the History of Philosophy, volume II, tr. E. S. Haldane and Frances H. Simson (1894)",
    "haldane-3": "Hegel, Lectures on the History of Philosophy, volume III, tr. E. S. Haldane and Frances H. Simson (1896)",
    "baillie-1": "Hegel, The Phenomenology of Mind, volume I, tr. J. B. Baillie (1910)",
    "baillie-2": "Hegel, The Phenomenology of Mind, volume II, tr. J. B. Baillie (1910)",
    "bosanquet-art": "Hegel, The Introduction to Hegel's Philosophy of Fine Art, tr. Bernard Bosanquet (1886)"}
SCAN_LITTER = re.compile(r"[a-z][A-Z]|\w' s\b|\w ' \w|[\\|■^~{}<>_]")       # a capital inside a word, a broken apostrophe, a stray sign
RARE, COMMON = 10, 2000         # a word the English books use fewer than RARE times, one letter from one they use COMMON times, is a misreading
MISREAD_RARE, MISREAD_COMMON = 50, 300      # and one used fewer than 50 times, a tenth as often as the word old type misreads it from
MISREAD = (("li", "h"), ("h", "li"), ("rn", "m"))        # old type misread: h as li and li as h ("tlie", "hke"), m as rn ("rnay")
HEADERS = {"essay": "Hegel, {title}. Written at Delhi, {date}.",
           "letter": "Hegel to {to}. Delhi, {date}.",
           "poem": "Hegel, {title}. A poem, written at Delhi, {date}."}
ARGUMENT = "[{about}]"
NOTE = "[Until November 1831 he was professor of philosophy at Berlin.{stay}]"
STAY = " He has been in Delhi {days}."          # where the world knows how long (clock.DAY_ONE, the morning he woke)
HEADLINE = re.compile(r"Hegel,|Hegel to\b|Hegel's [^,\n]*, tr\.")
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


def english_counts(shelf):
    """{word: how often} over the English books on the shelf, counted once per shelf; empty for a shelf without its texts."""
    counts = getattr(shelf, "english_counts", None)
    if counts is None:
        texts, counts = getattr(shelf, "data", {}).get("texts", []), Counter()
        for w in getattr(shelf, "works", []):
            if w["lang"] == "en":
                for text in texts[w["start"]:w["start"] + w["n"]]:
                    counts.update(re.findall(r"[a-z]{2,}", text.lower()))
        shelf.english_counts = counts
    return counts


def near(word):
    """The spellings one letter away from word: a letter dropped, changed or added."""
    abc = string.ascii_lowercase
    return ({word[:i] + word[i + 1:] for i in range(len(word))} | {word[:i] + c + word[i + 1:] for i in range(len(word)) for c in abc}
            | {word[:i] + c + word[i:] for i in range(len(word) + 1) for c in abc}) - {word}


def damaged(text, counts):
    """Whether a passage still shows its scan, which the model would copy: SCAN_LITTER, a rare word one letter from a common one ('tho', 'hke'),
    or a rare word that is a common one misread by old type ('tlie'). `counts` from english_counts; with none, only SCAN_LITTER counts."""
    if SCAN_LITTER.search(text):
        return True
    for w in set(re.findall(r"[a-z]{2,}", text.lower())) if counts else ():
        if counts[w] < RARE and any(counts[x] >= COMMON for x in near(w)):
            return True
        if counts[w] < MISREAD_RARE and any(a in w and counts[w.replace(a, b)] >= max(MISREAD_COMMON, 10 * counts[w]) for a, b in MISREAD):
            return True
    return False


def primer(shelf, plan):
    """The passage of his English books that fits the sitting best, {"label", "head", "text"}, or None (no shelf, or nothing English of
    PRIMER_WORDS words without the marks of its scan among what the title and what the sitting is about call up). `head` is the header line
    of its work and ref."""
    counts = english_counts(shelf) if shelf else None
    for hit in (shelf.search([(plan["title"], 1.0), (plan["about"], 1.0)]) if shelf else []):
        if hit["lang"] == "en" and PRIMER_WORDS[0] <= len(hit["text"].split()) <= PRIMER_WORDS[1] and not damaged(hit["text"], counts):
            head = PRIMER_HEADS.get(hit["id"].rpartition(":")[0], f"Hegel, {hit['work']}")
            return {"label": hit["label"], "head": head + (f", {hit['ref']}" if hit["ref"] else ""), "text": hit["text"]}
    return None


def note(d):
    """The editor's note on his situation on the day d: what he was until November 1831, and how long he has been in Delhi."""
    days = day_number(d) - 1
    stay = STAY.format(days=f"for {days} day{'s' * (days > 1)}" if days else "since this morning") if days >= 0 else ""
    return NOTE.format(stay=stay)


def prompt(plan, state, d, book=None):
    """(the prompt for a plain-text completion of the sitting, its opening line): the primer `book` (works.primer), if there is one, as a document
    of its own; then the header in the style of his books for the day d, the argument and the note on his situation in square brackets and a
    blank line; then the last words of the manuscript's latest sitting when he carries one on (one from before the index kept tails starts
    fresh), or the salutation of a new letter, which is the opening line that his text begins with ('' otherwise)."""
    work = find(state.get("works") or [], plan["title"]) if plan["continues"] else None
    src = work or plan
    kind = src["kind"] if src["kind"] != "letter" or src["to"] else "essay"
    when = f"{d.day} {MONTHS[d.month - 1]} {d.year}"
    header = HEADERS.get(kind, HEADERS["essay"]).format(title=src["title"].rstrip("."), to=src["to"], date=when)
    head = (PRIMER.format(**book) if book else "") + header + "\n" + ARGUMENT.format(about=plan["about"]) + "\n" + note(d) + "\n\n"
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
    document: leading echoes are dropped, and the text stops at a line that begins a new header or is only "* * *", THE END or Footnotes.
    Paragraphs stay (and a poem's lines), other whitespace is collapsed, quotes are straight, a sentence that repeats an earlier one of the
    sitting goes (and a paragraph with it, if nothing else is left of it; a poem's refrains stay), and the text is cut to CAP and back to its
    last sentence end (a poem's not); fewer than MIN_WORDS words is unusable. A new letter's opening line goes in front."""
    poem, body = plan["kind"] == "poem", []
    for ln in (x.strip() for x in (raw or "").replace("\r\n", "\n").translate(STRAIGHT).replace("--", "—").split("\n")):
        if not body and (not ln or echoes(ln, plan["title"], opening)):
            continue
        if HEADLINE.match(ln) or ENDING.match(ln):
            break
        body.append(ln)
    paras = [("\n" if poem else " ").join(" ".join(x.split()) for x in p.split("\n") if x.strip()) for p in re.split(r"\n\s*\n", "\n".join(body))]
    text = cut("\n\n".join(p for p in (paras if poem else fresh(paras)) if p), CAP - (len(opening) + 2 if opening else 0))
    ends = [m.end() for m in SENTENCE_END.finditer(text)]
    if not poem and not (ends and ends[-1] == len(text)):
        text = text[:ends[-1]] if ends else ""
    if len(text.split()) < MIN_WORDS:
        return None
    return {"title": plan["title"], "kind": plan["kind"], "to": plan["to"], "continues": plan["continues"], "about": plan["about"],
            "text": opening + "\n\n" + text if opening else text}
