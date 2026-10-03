"""The shelf: his own books, split into passages and indexed with BM25. `python3 tools/corpus.py --index` builds
mind/shelf/index.json.gz once; the Engine loads it once and asks it for the passages that fit a situation.
Standard library only, no embeddings: retrieval is lexical, helped by a small English<->German table
(world/data/shelf_terms.json), so that 'caste' finds Kaste and 'the system of needs' finds the Bedürfnisse.

The postings of a term are packed as two arrays (documents, counts) in one base64 string and unpacked only for the
terms of a query, so the index loads fast and holds little more than the passages themselves."""
import base64
import gzip
import heapq
import json
import math
import re
import sys
import unicodedata
from array import array
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX, TERMS = REPO / "mind/shelf/index.json.gz", REPO / "world/data/shelf_terms.json"
MIN_CHARS, TARGET, MAX_CHARS = 500, 700, 900     # a passage: pieces are closed at TARGET and never run past MAX_CHARS
LIMIT, MAX_SECTION, REF_CHARS = 380, 850, 48     # characters of one excerpt; of the whole "From your shelf" section; of a reference
K1, B, FORMAT = 1.2, 0.75, 1
EXPANDED, RELATIVE, FLOOR = 0.6, 0.45, 14.0      # weight of a table term; how strong the other language must be; the weakest hit worth showing (precision over coverage: a loose passage distracts a small model)
PHRASE, PHRASE_POOL = 6.0, 40                    # bonus for a phrase of the table found in a passage; passages looked at again for it
ABBREV = {"mr", "mrs", "dr", "st", "cf", "vol", "pp", "no", "fr", "hr", "hrn", "bzw", "usw", "ibid", "viz", "etc", "ch", "sect", "bd", "ed"}

_STOP = """a about above after again all also am an and any are as at be because been before being between both but by can could
did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its
just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their
them then there these they this those through to too under until up us very was we were what when where which while who whom why
will with would you your one may must shall thus yet upon whose whether either neither itself himself themselves
aber alle allem allen aller alles als also am an andere anderen anderer anderes auch auf aus bei bin bis bist da damit dann das
dass daß dem den denn der des die dies diese diesem diesen dieser dieses doch dort du durch ein eine einem einen einer eines er es
euch euer fur für gegen hat hatte hatten hier hin ich ihm ihn ihnen ihr ihre ihrem ihren ihrer im in ist ja jede jedem jeden jeder
jedes kann kein keine keinem keinen keiner man mehr mein meine mit muss nach nicht noch nun nur ob oder ohne sehr sein seine
seinem seinen seiner seines sich sie sind so soll sollte sondern uber über um und uns unter vom von vor war waren was weil weiter
wenn wer werden wie wir wird wo wurde wurden zu zum zur zwar zwischen""".split()
# words of the world's own bookkeeping that say nothing about what Hegel thought
NOISE = """arrive arrives arrived closes close closing opens open nothing particular happens happen goes go afternoon morning
evening wake wakes test ramesh nobody present headlines today tomorrow yesterday mr mrs ms dr shri smt sir madam ji""".split()
SUFFIX = (("ungen", ""), ("ings", ""), ("ing", ""), ("ies", "y"), ("ied", "y"), ("ung", ""), ("ed", ""), ("ly", ""), ("en", ""),
          ("er", ""), ("es", ""), ("em", ""), ("s", ""))


def fold(s):
    """Lower case, no diacritics, ß as ss: one spelling for the index and the query."""
    s = s.lower().replace("ß", "ss")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


STOP = {fold(w) for w in _STOP}
IGNORE = STOP | {fold(w) for w in NOISE}


def stem(w):
    """A light stemmer for both languages: plural and case endings, then a trailing e and a doubled s."""
    if len(w) < 5 or w.isdigit():
        return w
    for suf, rep in SUFFIX:
        if suf == "s" and w.endswith(("is", "us", "ss")):          # Bedürfnis, basis, class: no plural s
            continue
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[:-len(suf)] + rep
            break
    if len(w) > 4 and w.endswith("e"):
        w = w[:-1]
    return w[:-1] if len(w) > 4 and w.endswith("ss") else w


def tokens(text, ignore=STOP):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", fold(text)) if len(w) > 1 and w not in ignore]


def label(work, ref):
    """'Philosophy of Right §189', 'Philosophie der Geschichte, Einleitung'."""
    return f"{work} {ref}" if (ref or "").startswith("§") else f"{work}, {ref}" if ref else work


# ── passages ────────────────────────────────────────────────────────
def sentences(text):
    """The sentences of text, each with its closing punctuation; abbreviations and initials do not end one."""
    out, start = [], 0
    for m in re.finditer(r"[.!?;]+[\"”’)\]]*\s+(?=[A-ZÄÖÜ“\"‘'(§\[])", text):
        words = text[start:m.start() + 1].split()
        last = words[-1].rstrip(".!?;").lstrip("(“\"‘'[").lower() if words else ""
        if m.group(0).startswith(";") or last in ABBREV or (len(last) == 1 and last.isalpha()):
            continue
        out.append(text[start:m.end()].strip())
        start = m.end()
    tail = text[start:].strip()
    return out + [tail] if tail else out


def pieces(text, limit=800):
    """A long paragraph in pieces of at most `limit` characters, cut at sentence ends (at a clause or a word if a sentence is longer)."""
    out, cur = [], ""
    for s in sentences(text):
        while len(s) > MAX_CHARS:
            cut = max(s.rfind(x, 0, limit) for x in ("; ", ", ", " — ", ": "))
            cut = cut if cut > limit // 2 else s.rfind(" ", 0, limit)
            if cur:
                out.append(cur)
                cur = ""
            out.append(s[:cut + 1].strip())
            s = s[cut + 1:].strip()
        if cur and len(cur) + 1 + len(s) > limit:
            out.append(cur)
            cur = ""
        cur = f"{cur} {s}".strip()
    return out + [cur] if cur else out


def fill(text, room):
    """(front, rest): the whole sentences at the front of text that fit in `room` characters, and what is left."""
    front = ""
    ss = sentences(text)
    for i, sent in enumerate(ss):
        if len(front) + len(sent) + (1 if front else 0) > room:
            return front, " ".join(ss[i:])
        front = f"{front} {sent}".strip()
    return front, ""


def split_passages(text, style="head"):
    """[(ref, passage)] from a cleaned work. Paragraphs are separated by a blank line; '# x' and '## x' lines are headings
    (they set the ref and end a passage), a paragraph that starts with '§ 189' sets the section. style 'sec' refers to
    '§189' once a section is known, else (and for style 'head') to the headings, 'Part, Section'."""
    out, buf, ref0 = [], [], ""
    h1 = h2 = sec = ""

    def where():
        if style == "sec" and sec:
            return f"§{sec}"
        ref = ", ".join(dict.fromkeys(x for x in (h1, h2) if x))
        ref = h2 if len(ref) > REF_CHARS and h2 else ref          # a long path is cut to its last heading
        return ref if len(ref) <= REF_CHARS else ref[:REF_CHARS - 1].rsplit(" ", 1)[0] + "…"

    def flush():
        nonlocal buf
        if buf:
            out.append((ref0, " ".join(buf)))
        buf = []

    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if para.startswith("# ") or para.startswith("## "):
            flush()
            if para.startswith("## "):
                h2 = para[3:].strip()
            else:
                h1, h2 = para[2:].strip(), ""
            continue
        m = re.match(r"§\s*(\d+[a-z]?)", para)
        if m:
            if sum(len(x) + 1 for x in buf) >= MIN_CHARS:
                flush()
            sec = m.group(1)
        for piece in pieces(para) if len(para) > MAX_CHARS else [para]:
            size = sum(len(x) + 1 for x in buf)
            if buf and size + len(piece) > MAX_CHARS:
                if size < MIN_CHARS:                    # a short passage is filled from the front of this piece, not left short
                    take, piece = fill(piece, MAX_CHARS - size - 1)
                    buf += [take] if take else []
                flush()
            if not piece:
                continue
            if not buf:
                ref0 = where()
            buf.append(piece)
            if sum(len(x) + 1 for x in buf) >= TARGET:
                flush()
    flush()
    return out


# ── the index ───────────────────────────────────────────────────────
def pack(post):
    """{term: [(doc, count)]} to {term: 'docs,counts'}: arrays of unsigned shorts (documents) and bytes (counts), in base64."""
    out = {}
    for term in sorted(post):
        docs, tfs = array("H"), array("B")
        for d, tf in post[term]:
            docs.append(d)
            tfs.append(min(tf, 255))
        if sys.byteorder == "big":
            docs.byteswap()
        out[term] = base64.b64encode(docs.tobytes()).decode() + "," + base64.b64encode(tfs.tobytes()).decode()
    return out


def build_index(works):
    """The index for works = [{"id", "work", "lang", "passages": [(ref, text)], ...}]. Keys of a work other than 'passages' are kept."""
    refs, texts, lens, post, meta = [], [], [], {}, []
    for w in works:
        meta.append({**{k: v for k, v in w.items() if k != "passages"}, "start": len(texts), "n": len(w["passages"])})
        for ref, text in w["passages"]:
            toks = tokens(text)
            for t, tf in Counter(toks).items():
                post.setdefault(t, []).append((len(texts), tf))
            refs.append(ref)
            texts.append(text)
            lens.append(len(toks))
    if len(texts) > 65535:
        raise ValueError("more than 65535 passages: the postings are packed as unsigned shorts")
    return {"format": FORMAT, "avglen": sum(lens) / max(1, len(lens)), "works": meta, "refs": refs, "texts": texts, "len": lens,
            "terms": pack(post)}


def save_index(index, path=INDEX):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(path, "wb", compresslevel=9, mtime=0) as f:             # mtime 0: the same index gives the same bytes
        f.write(json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


# ── the query ───────────────────────────────────────────────────────
class Terms:
    """Groups of words that mean one thing in two languages ('caste', 'Kaste'): any member of a group in the query brings the
    others along. 'brings' are one-way: a word of Delhi's that calls up what Hegel called it ('grocer', 'tailor' bring the
    system of needs)."""

    def __init__(self, groups, brings=()):
        self.groups, self.keys, self.bring = [], {}, {}
        for g in groups:
            members = [tuple(tokens(m)) for m in g]
            self.groups.append([m for m in members if m])
            for m in members:
                if m:
                    self.keys.setdefault(m, set()).add(len(self.groups) - 1)
        for b in brings:
            add = [tuple(tokens(m)) for m in b["add"] if tokens(m)]
            for m in b["when"]:
                if tokens(m):
                    self.bring.setdefault(tuple(tokens(m)), []).extend(add)

    def expand(self, seq, weight=1.0):
        """({term: weight}, {phrase: weight}) for what the words in seq (a list of stems, in order) call up, at EXPANDED of
        `weight`. A phrase is a member of two words or more, or a phrase of the query that is in the table."""
        terms, phrases = {}, {}
        for n in (3, 2, 1):
            for i in range(len(seq) - n + 1):
                key = tuple(seq[i:i + n])
                called = [m for g in self.keys.get(key, ()) for m in self.groups[g]] + self.bring.get(key, [])
                if called and n > 1:
                    phrases[key] = weight
                for member in called:
                    for t in member:
                        terms[t] = EXPANDED * weight
                    if len(member) > 1:
                        phrases[member] = EXPANDED * weight
        return terms, phrases


class Shelf:
    def __init__(self, data, terms=None):
        if data.get("format") != FORMAT:
            raise ValueError("unknown shelf index format")
        self.data, self.terms, self.n = data, terms or Terms([]), len(data["texts"])
        self.lens, self.works = data["len"], data["works"]
        avg = data["avglen"] or 1
        self.norm = [K1 * (1 - B + B * n / avg) for n in self.lens]
        self.cache = {}                                   # term -> (documents, counts, idf)

    def work_of(self, doc):
        return next(w for w in self.works if w["start"] <= doc < w["start"] + w["n"])

    def ident(self, doc):
        w = self.work_of(doc)
        return f"{w['id']}:{doc - w['start']}"

    def doc_of(self, ident):
        """The document number of a passage id like 'dyde-right:412', or None."""
        wid, _, k = ident.rpartition(":")
        w = next((x for x in self.works if x["id"] == wid), None)
        return w["start"] + int(k) if w and k.isdigit() and int(k) < w["n"] else None

    def postings(self, term):
        got = self.cache.get(term)
        if got is None and term in self.data["terms"]:
            docs, tfs = (base64.b64decode(x) for x in self.data["terms"][term].split(","))
            d = array("H")
            d.frombytes(docs)
            if sys.byteorder == "big":
                d.byteswap()
            df = len(d)
            got = self.cache[term] = (d, tfs, math.log(1 + (self.n - df + 0.5) / (df + 0.5)))
        return got

    def weights(self, parts):
        """({term: weight}, {phrase: weight}) of the query: the terms of each (text, weight) part, and what the table calls up."""
        w, phrases = {}, {}
        for text, weight in parts:
            seq = tokens(text, IGNORE)
            for t in seq:
                w[t] = max(w.get(t, 0), weight)
            terms, called = self.terms.expand(seq, weight)
            for t, x in terms.items():
                w[t] = max(w.get(t, 0), x)
            for ph, x in called.items():
                phrases[ph] = max(phrases.get(ph, 0), x)
        return w, phrases

    def scores(self, weights):
        """{doc: BM25 score}."""
        acc, norm = {}, self.norm
        for term, wt in weights.items():
            p = self.postings(term)
            if not p:
                continue
            docs, tfs, idf = p
            a = wt * idf * (K1 + 1)
            for d, tf in zip(docs, tfs):
                acc[d] = acc.get(d, 0.0) + a * tf / (tf + norm[d])
        return acc

    def ranked(self, weights, phrases, skip=lambda doc: False):
        """[(doc, score)], best first. The best PHRASE_POOL passages by BM25 are looked at again: one that has a phrase of
        the table in it ('system of needs') gains PHRASE times the phrase's weight."""
        top = [x for x in heapq.nlargest(PHRASE_POOL, self.scores(weights).items(), key=lambda x: x[1]) if not skip(x[0])]
        if phrases:
            top = [(d, s + sum(PHRASE * x for ph, x in phrases.items() if " " + " ".join(ph) + " " in joined))
                   for d, s in top for joined in [" " + " ".join(tokens(self.data["texts"][d])) + " "]]
            top.sort(key=lambda x: -x[1])
        return top

    def hit(self, doc, score):
        w = self.work_of(doc)
        ref = self.data["refs"][doc]
        return {"id": self.ident(doc), "doc": doc, "work": w["work"], "ref": ref, "lang": w["lang"], "label": label(w["work"], ref),
                "score": round(score, 2), "text": self.data["texts"][doc]}

    def search(self, parts, n=40, skip=lambda doc: False):
        """The n best passages for the query parts [(text, weight)], best first, whole and as dicts; `skip(doc)` leaves some out."""
        weights, phrases = self.weights(parts)
        return [self.hit(d, s) for d, s in self.ranked(weights, phrases, skip)[:n]]

    def pick(self, parts, avoid=(), hold=(), k=2):
        """The k passages to show for the query parts, each cut to an excerpt: the best German and the best English one if both
        are strong (RELATIVE of the best score), else the best two. Passages in `avoid` (ids) and works in `hold` (work ids) are
        left out, and so is a passage right next to one already chosen. [] when even the best is weaker than FLOOR."""
        held, avoided = set(hold), set(avoid)
        weights, phrases = self.weights(parts)
        hits = [self.hit(d, s) for d, s in self.ranked(weights, phrases, lambda d: self.work_of(d)["id"] in held or self.ident(d) in avoided)]
        if not hits or hits[0]["score"] < FLOOR:
            return []
        best = {}
        for h in hits:
            if h["score"] >= RELATIVE * hits[0]["score"]:
                best.setdefault(h["lang"], h)
        both = sorted(best.values(), key=lambda h: -h["score"]) if len(best) > 1 else []
        chosen = []
        for h in both + hits:
            if len(chosen) < k and all(h["id"] != c["id"] and not (self.work_of(h["doc"]) is self.work_of(c["doc"]) and abs(h["doc"] - c["doc"]) <= 1)
                                       for c in chosen):
                chosen.append(h)
        return fit([{**{a: b for a, b in h.items() if a != "doc"}} for h in chosen], weights, self)


def excerpt(text, weights, limit=LIMIT):
    """text in at most `limit` characters: the whole sentences that hold most of the query's terms, or, if no whole
    sentence fits, the best sentence cut at a clause and marked with an ellipsis. A section sign at the start goes."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    ss = sentences(text)
    value = lambda s: sum(weights.get(t, 0) for t in set(tokens(s, IGNORE)))
    best = (0, 0, "")
    for i in range(len(ss)):
        j, size = i, 0
        while j < len(ss) and size + len(ss[j]) + (j > i) <= limit:
            size += len(ss[j]) + (j > i)
            j += 1
        if j > i:
            window = " ".join(ss[i:j])
            best = max(best, (value(window), -i, window))
    if best[2]:
        return best[2]
    s = max(ss, key=value)
    cut = max(s.rfind(x, 0, limit - 1) for x in ("; ", ", ", " — ", ": "))
    cut = cut if cut > limit // 2 else s.rfind(" ", 0, limit - 1)
    return s[:cut].rstrip(" ,;:—-") + "…"


def section_size(items):
    """Characters of the 'From your shelf' section for items, as contract.render prints it."""
    return len("From your shelf:\n") + sum(len(f"- {x['label']}: “{x['text']}”\n") for x in items)


def shown(item, text):
    """item with `text` as its excerpt, minus the section signs that begin paragraphs ('§ 170.', '§ 258 Zusatz.'); if the excerpt
    itself starts with one, that is the reference."""
    m = re.match(r"§\s*(\d+[a-z]?)(?:\s+Zusatz)?\.?\s*", text)
    text = re.sub(r"(?<=[.!?:”])\s+§\s*\d+[a-z]?(?:\s+Zusatz)?\.\s+(?=\S)", " ", text[m.end():] if m else text)
    if m and (item["ref"] or "").startswith("§"):
        item["ref"] = f"§{m.group(1)}"
        item["label"] = label(item["work"], item["ref"])
    item["text"] = text.strip()
    return item


def fit(items, weights, shelf, limit=LIMIT):
    """items with their texts cut to excerpts, then shortened until the whole section is at most MAX_SECTION characters."""
    full = {x["id"]: x["text"] for x in items}
    while True:
        for x in items:
            shown(x, excerpt(full[x["id"]], weights, limit))
        if section_size(items) <= MAX_SECTION or limit <= 120:
            return items
        limit -= 20


_loaded = {}


def load(path=None, terms=None):
    """The shelf, or None if there is no index. Read once per process and file."""
    path, terms = Path(path or INDEX), Path(terms or TERMS)
    try:
        stamp = (path.stat().st_mtime_ns, terms.stat().st_mtime_ns if terms.exists() else 0)
    except OSError:
        return None
    if _loaded.get(path, (None,))[0] != stamp:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        table = json.loads(terms.read_text(encoding="utf-8")) if terms.exists() else {}
        _loaded[path] = (stamp, Shelf(data, Terms(table.get("groups", ()), table.get("brings", ()))))
    return _loaded[path][1]


def query_parts(event, place, roles, thoughts, theses):
    """The query for a situation as [(text, weight)]: what happens counts most, then the people, the place, the last
    two thoughts and the theses."""
    return [(event, 1.0), (" ".join(roles), 0.8), (place, 0.6), (" ".join(thoughts), 0.5), (" ".join(theses), 0.4)]
