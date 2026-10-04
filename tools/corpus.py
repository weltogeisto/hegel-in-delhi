#!/usr/bin/env python3
"""Hegel in Delhi: the corpus. Builds his shelf from public-domain texts.

    python3 tools/corpus.py --list                # the works, and what is cached and built
    python3 tools/corpus.py --fetch [id ...]      # download the raw texts to tools/.cache/corpus/ (polite, once)
    python3 tools/corpus.py --clean [id ...]      # clean them into mind/shelf/<id>.txt.gz
    python3 tools/corpus.py --index               # split into passages and build mind/shelf/index.json.gz
    python3 tools/corpus.py --manifest            # write mind/shelf/MANIFEST.md
    python3 tools/corpus.py --all                 # fetch, clean, index, manifest
    python3 tools/corpus.py --probe id            # headings found, and a sample of the cleaned text (for writing a spec)

Standard library only. Nothing is fetched at runtime on the Pi: the shelf is built here and committed.
A cleaned work is text in paragraphs separated by a blank line; '# x' and '## x' are headings, a paragraph that
starts with '§ 189.' is a numbered section."""
import argparse
import bisect
import difflib
import gzip
import itertools
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
from world import shelf  # noqa: E402

CACHE, SHELF = HERE / ".cache/corpus", REPO / "mind/shelf"
UA = "hegel-in-delhi-corpus/1.0 (private research project; contact hendriksteinort@gmail.com)"
DELAY = 1.5                                         # seconds between requests
GUTENBERG = "https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt"
ARCHIVE = "https://archive.org/download/{i}/{i}_djvu.txt"
LETTER = r"A-Za-zÀ-ÖØ-öø-ÿ"
ROMAN = re.compile(r"^(?=[ivxlcdm]+$)m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$", re.I)


# ── fetching ────────────────────────────────────────────────────────
def fetch(url, name, force=False):
    """The cached file `name`, downloaded from url if it is not there. Waits DELAY seconds after a request, retries slow answers."""
    p = CACHE / name
    if p.exists() and not force:
        return p
    CACHE.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                p.write_bytes(r.read())
            time.sleep(DELAY)
            return p
        except (urllib.error.URLError, OSError) as e:
            print(f"  retry {attempt + 1} for {url}: {e}", file=sys.stderr)
            time.sleep(DELAY * 3 * (attempt + 1))
    raise SystemExit(f"could not fetch {url}")


# ── cleaning ────────────────────────────────────────────────────────
def squash(line):
    return re.sub(r"\s+", " ", line.replace("\xa0", " ")).strip()


def paragraphs(text):
    """The raw paragraphs of text: lists of squashed lines, split at blank lines."""
    out, cur = [], []
    for line in text.replace("\r", "").split("\n"):
        line = squash(line)
        if line:
            cur.append(line)
        elif cur:
            out.append(cur)
            cur = []
    return out + [cur] if cur else out


def junk(line):
    """An OCR scrap: hardly any letters (a section sign with its number is no scrap)."""
    letters = len(re.findall(f"[{LETTER}]", line))
    return not line.startswith("§") and (letters < 3 or letters < 0.4 * len(line))


def header_key(line):
    """A line without its page number or roman numeral, in lower case letters only."""
    return " ".join(w for w in re.findall(f"[{LETTER}]+", line.lower()) if not ROMAN.match(w) or len(w) > 4)


def numbered(line):
    """A short line with a page number at one end: '112 THE PHILOSOPHY OF RIGHT.', 'Ethical Action 467'."""
    return len(line) <= 70 and bool(re.match(r"^(\d{1,4}|[ivxlc]{1,7})\.?\s+\S", line, re.I) or re.search(r"\S\s+(\d{1,4}|[ivxlc]{1,7})\.?$", line, re.I))


def similar(a, b):
    return abs(len(a) - len(b)) < 8 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.75


class Running:
    """The running heads of a work: one-line paragraphs that recur so often (spec 'repeat', default 4) that they can only
    be page headers. Keys that differ by an OCR slip or two ('PART I. THE ORIENTAL WORLD', '... OEIENTAL WOELD') count as
    one. Each cluster knows its commonest wording, without the page number."""

    def __init__(self, paras, spec):
        count = Counter(p[0] for p in paras if len(p) == 1 and len(p[0]) <= 70 and (numbered(p[0]) or p[0].upper() == p[0]))
        keep = re.compile(spec.get("keep", r"^(addition|remark|note|zusatz|anmerkung|footnotes?|anm)\b"), re.I)
        clusters = []                                              # [key, total count, Counter of wordings]
        for line, n in count.most_common():
            key = header_key(line)
            if key and not keep.match(key):
                hit = next((c for c in clusters if similar(key, c[0])), None)
                if hit:
                    hit[1] += n
                    hit[2][line] += n
                else:
                    clusters.append([key, n, Counter({line: n})])
        self.clusters = [c for c in clusters if c[1] >= spec.get("repeat", 4)]

    def find(self, line):
        key = header_key(line)
        return next((c for c in self.clusters if key and similar(key, c[0])), None)

    @staticmethod
    def label(cluster):
        """'Ethical Action' for the cluster of 'Ethical Action 467', 'Ethical Action 465' ..."""
        line = cluster[2].most_common(1)[0][0]
        return squash(re.sub(r"^(\d{1,4}|[ivxlc]{1,7})\.?\s+|\s+(\d{1,4}|[ivxlc]{1,7})\.?$", "", line, flags=re.I)).strip(" .")


def is_header(line, running, spec, open_before=False):
    """The running-head cluster of `line` (or True) if it is a page header or page number standing alone in its paragraph,
    else None. `open_before`: the text before it stops mid-sentence, as it does where a page break falls."""
    if line.startswith("§"):
        return None
    if re.fullmatch(r"[\[{(]?\s*(\d{1,4}|[ivxlc]{1,7})\s*[\]})]?\.?", line, re.I) or any(re.search(p, line) for p in spec.get("drop", ())):
        return True
    cluster = running.find(line) if len(line) <= 70 and (numbered(line) or line.upper() == line) else None
    letters = re.findall(f"[{LETTER}]", line)
    if cluster or (numbered(line) and open_before and not re.search(r"[.!?]\S?$", line.rstrip("0123456789 ")[-2:])) \
            or (numbered(line) and len(letters) >= 6 and sum(c.isupper() for c in letters) >= 0.6 * len(letters)):
        return cluster or True                                    # the last: capitals with a page number ('124 PART I. THE ORIENTAL WOELD')
    return None


SMALL = {"of", "the", "and", "in", "to", "from", "for", "on", "at", "by", "as", "or", "a", "an", "with", "its", "der", "die", "das", "und", "des", "von", "zu"}


def smart_title(text):
    """'THE RANGE OF ÆSTHETIC DEFINED' as 'The Range of Æsthetic Defined'; roman numerals stay."""
    out = []
    for i, w in enumerate(text.split()):
        low = w.lower()
        out.append(w if w.strip(".") in ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")
                   else low if i and low in SMALL else "-".join(x.capitalize() for x in low.split("-")))
    return " ".join(out)


def heading_machine(heads):
    """match(text, mode) for `heads` [(level, regex, label[, mode])], used in order, each at most once, skipping at most two
    that never turn up. mode 'line' (the default): a paragraph of one line is the heading; 'para': a paragraph of any
    length is the heading; 'keep': the heading comes before the paragraph that starts like this, which stays.
    Returns (level, label) or None."""
    state = {"i": 0}

    def match(text, mode):
        for j in range(state["i"], min(len(heads), state["i"] + 3)):
            level, rx, label, *m = heads[j]
            if (m[0] if m else "line") == mode and re.search(rx, text):
                state["i"] = j + 1
                return level, label if label is not None else smart_title(re.sub(r"[.\s]+$", "", text))
        return None
    return match


def auto_heading(line, running, auto=True):
    """(level, label) if `line` is a heading. `auto` True: a heading of a clean text, in capitals only, as 'B. ARISTOTLE.' or
    '1. THE METAPHYSICS.' (a lettered or plain heading is level 1, a numbered or lower-case-lettered one level 2). `auto` a list
    of (level, regex): the label is group 1 of the first regex that matches."""
    if auto is not True:
        return next(((lvl, m.group(1).strip(" .,")) for lvl, rx in auto if (m := re.match(rx, line)) and len(line) <= 75
                     and not running.find(line)), None)
    letters = "".join(re.findall(f"[{LETTER}]", line))
    if len(line) > 80 or len(letters) < 6 or letters != letters.upper() or running.find(line) or "§" in line \
            or re.match(r"^(FOOTNOTES|INDEX|CONTENTS|TRANSLATOR|TRANSCRIBER|PREFATORY|DELIVERED|END OF|START:)", line) \
            or re.match(r"^(PART|SECTION|CHAPTER|BOOK)\s+([IVXLC]+|ONE|TWO|THREE|FOUR|FIVE|\d+)\.?$", line):
        return None
    m = re.match(r"^(?:_?([a-z0-9α-ω]+)_?[.)]|([A-Z]|[IVX]+)\.(?:—|-)?)\s*(.+)$", line)
    text = re.sub(r"^[_.\s—-]+|[_.\s]+$", "", m.group(3) if m else line)
    return ((2 if m and m.group(1) else 1), smart_title(text)) if text else None


def lines_to_paragraphs(lines, spec):
    """Paragraphs from a scan that puts a blank line after every line: a line that is clearly shorter than the usual one and
    ends a sentence ends the paragraph, and so does any line that a head or a running head would match."""
    size = sorted(len(x) for x in lines)[len(lines) // 2] if lines else 0
    auto = spec["auto"] if isinstance(spec.get("auto"), list) else []
    stop = [re.compile(h[1]) for h in spec.get("heads", ()) if len(h) < 4 or h[3] == "line"] + [re.compile(x) for x in spec.get("drop", ())] \
        + [re.compile(rx) for _, rx in auto]
    out, cur = [], []
    for line in lines:
        if any(r.search(line) for r in stop):
            out += [cur] if cur else []
            out, cur = out + [[line]], []
            continue
        cur.append(line)
        if len(line) < 0.7 * size and re.search(r"[.!?:”\"»]$", line):
            out.append(cur)
            cur = []
    return out + [cur] if cur else out


def rejoin(lines, words):
    """The lines of a paragraph as one text. A word split by a hyphen at the end of a line is joined; the hyphen stays
    if the text itself writes the compound that way elsewhere (more often than as one word)."""
    out = lines[0]
    for nxt in lines[1:]:
        if re.search(f"[{LETTER}]-$", out) and re.match("[a-zäöüß]", nxt):
            head, tail = re.search(f"([{LETTER}]+)-$", out).group(1), re.match(f"[{LETTER}]+", nxt).group(0)
            solid, hyph = (head + tail).lower(), f"{head}-{tail}".lower()
            out = out[:-1] + ("-" if words[hyph] > words[solid] else "") + nxt
        else:
            out += " " + nxt
    return out


def word_counts(paras):
    """Counts of words and hyphenated compounds written whole within a line."""
    c = Counter()
    for p in paras:
        for line in p:
            c.update(w.lower() for w in re.findall(f"[{LETTER}]+(?:-[{LETTER}]+)*", line))
    return c


def tidy(text):
    """Spacing, markup and footnote marks of one paragraph."""
    text = re.sub(r"_([^_]+)_", r"\1", text).replace("_", "")
    text = re.sub(r"\[Greek: ([^\]]*)\]", r"\1", text)
    text = re.sub(r"\[\d{1,3}\]", "", text)                                   # [11]: footnote mark
    text = re.sub(rf"(?<=[{LETTER}.,;:)”’])\s?[*†‡^]+(?!\w)", "", text)        # a star, dagger or caret after a word
    text = re.sub(r"\s+([,.;:!?)”’])", r"\1", text)
    text = re.sub(r"([(“‘])\s+", r"\1", text)
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ſ", "s").replace("­", "")
    return re.sub(r"\s+", " ", text).strip()


def one_digit_off(a, b):
    return len(a) == len(b) and len(a) >= 2 and sum(x != y for x, y in zip(a, b)) <= 1


def increasing(values):
    """The positions of a longest strictly increasing run in values (a list of numbers)."""
    tails, ends, back = [], [], [None] * len(values)           # tails[k]: the least value that ends a run of length k + 1
    for i, v in enumerate(values):
        k = bisect.bisect_left(tails, v)
        if k == len(tails):
            tails.append(v)
            ends.append(i)
        else:
            tails[k], ends[k] = v, i
        back[i] = ends[k - 1] if k else None
    out, i = [], ends[-1] if ends else None
    while i is not None:
        out.append(i)
        i = back[i]
    return out[::-1]


def number_sections(paras, rx):
    """'11.] Text', '116. Text' or '§. 11. Text' as '§ 11. Text'. The sections of such a work are numbered without a gap, so the
    numbers that run on in order are believed (a year, a list item, a reference at the start of a line do not run on), and a
    marker whose number the scan has spoiled ('lOL', '256' for 255, '267' for 257) takes the number that is missing there."""
    marks = [(i, m) for i, m in ((i, re.match(rx, p)) for i, p in enumerate(paras)) if m]
    nums = [int(m.group(1)) if m.group(1).isdigit() else 0 for _, m in marks]
    chain = set(increasing(nums))
    chain = {k for k in chain if nums[k]}
    label, pending, last = {}, [], 0

    def settle(until):
        """The markers waiting since the last believed one take, in order, the numbers between `last` and `until`."""
        nonlocal pending
        free = list(range(last + 1, until))
        for k in pending:
            got = marks[k][1].group(1)
            hit = next((g for g in free if not nums[k] or one_digit_off(got, str(g))), None)
            if hit is not None:
                label[k] = hit
                free = [g for g in free if g > hit]
        pending = []

    for k in range(len(marks)):
        if k in chain:
            settle(nums[k])
            label[k], last = nums[k], nums[k]
        else:
            pending.append(k)
    settle(last + 1 + len(pending))
    out = list(paras)
    for k, (i, m) in enumerate(marks):
        if k in label:
            out[i] = f"§ {label[k]}. " + paras[i][m.end():].lstrip(" -–—")
        elif paras[i].startswith("§"):
            out[i] = "… " + paras[i]                              # a reference that starts a line: not a section
    return [p.strip() for p in out]


def merge_breaks(paras):
    """A paragraph cut by a page break (no full stop at its end, the next starting in lower case) is made whole again,
    and a paragraph that is only a section sign and its number takes the text that follows."""
    out = []
    for p in paras:
        if out and re.fullmatch(r"§\s*\d+[a-z]?\.?[\s\-–—]*", out[-1]) and not p.startswith("#"):
            out[-1] = f"{out[-1]} {p}"
        elif out and not out[-1].startswith("#") and not p.startswith("#") and not re.search(r"[.!?:;”’\"»]$", out[-1]) \
                and re.match(r"[a-zäöüß(]", p):
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def clean(raw, spec):
    """The cleaned text of one work from its raw download. `spec` keys (all optional): gutenberg (cut the licence), start and
    end (regexes of lines: the text runs from the nth match of start, 'nth', to the first match of end after it), heads (see
    heading_machine), auto (headings in capitals are headings), first (a heading for the very start), running (a heading level:
    the running heads of the work, each new one, become headings; 'running_skip' is a regex for those that are not topics),
    labels (regex, label) to name running heads properly, brackets (drop the translator's summaries in square brackets), caps (lines in capitals that are no head are dropped), sections (a regex with the number in group 1: numbered
    paragraphs), zusatz (a regex whose group 1 is a section number: lecture additions become '§ N Zusatz.'), drop (regexes of lines to drop), footnotes (a paragraph starting like this is a footnote), repeat (how often
    a one-line paragraph must recur to be a running head), keep (a regex for lines never to drop), single (every line is a
    paragraph, as in some scans), pre (a function on the raw text, to repair an OCR habit)."""
    if spec.get("pre"):
        raw = spec["pre"](raw)
    if spec.get("gutenberg"):
        m = re.search(r"\*\*\* ?START OF.*?\*\*\*", raw)
        raw = raw[m.end():] if m else raw
        m = re.search(r"\*\*\* ?END OF", raw)
        raw = raw[:m.start()] if m else raw
    lines = raw.replace("\r", "").split("\n")
    if spec.get("start"):
        hits = [i for i, l in enumerate(lines) if re.search(spec["start"], squash(l))]
        lines = lines[hits[spec.get("nth", 0)]:] if len(hits) > spec.get("nth", 0) else lines
    if spec.get("end"):
        hits = [i for i, l in enumerate(lines) if re.search(spec["end"], squash(l))]
        lines = lines[:hits[0]] if hits and hits[0] > 0 else lines
    paras = paragraphs("\n".join(lines))
    if spec.get("single"):                                  # the running heads go first, or they end up in the middle of a paragraph
        lines = [x for p in paras for x in p]
        heads = Running([[x] for x in lines], spec)
        asked = [re.compile(h[1]) for h in spec.get("heads", ()) if len(h) < 4 or h[3] == "line"]
        paras = lines_to_paragraphs([x for x in lines if any(r.search(x) for r in asked) or not is_header(x, heads, spec)], spec)
    running = Running(paras, spec)
    match = heading_machine(spec.get("heads", ()))
    foot = re.compile(spec.get("footnotes", r"^(\[\d{1,3}\]\s|[*†‡]\s?\w|FOOTNOTES?:?$|\[Illustration)"))
    words = word_counts(paras)
    out, seen, skipping = (["# " + spec["first"]] if spec.get("first") else []), set(), False
    for p in paras:
        text = " ".join(p)
        got = (match(p[0], "line") or (auto_heading(p[0], running, spec["auto"]) if spec.get("auto") else None)) if len(p) == 1 else None
        got = got or match(text[:200], "para")
        if got:
            out.append("#" * got[0] + " " + tidy(got[1]))
            continue
        if len(p) == 1:
            before = out[-1] if out and not out[-1].startswith("#") else "."
            head = is_header(p[0], running, spec, open_before=not re.search(r"[.!?:;”’\"»]$", before))
            if head:
                label = Running.label(head) if head is not True else ""
                label = next((lab for rx, lab in spec.get("labels", ()) if re.search(rx, label, re.I)), label)
                if spec.get("running") and len(label) > 3 and head is not True and id(head) not in seen \
                        and not re.search(spec.get("running_skip", r"^$"), label, re.I):
                    out.append("#" * spec["running"] + " " + tidy(label))          # a running head is a heading, the first time it is seen
                    seen.add(id(head))
                continue
        if spec.get("caps") and len(text) <= 100 and text == text.upper() and len(re.findall(f"[{LETTER}]", text)) >= 3:
            continue                                        # a heading or running head in capitals that no head asked for
        if spec.get("brackets"):                           # the translator's own summaries, in [square brackets]
            if skipping or (text.startswith("[") and len(text) > 200):
                skipping = not text.rstrip().endswith("]")
                continue
        got = match(text[:200], "keep")
        if got:
            out.append("#" * got[0] + " " + tidy(got[1]))
        p = [x for x in p if not junk(x)]
        if not p or foot.match(p[0]):
            continue
        out.append(tidy(rejoin(p, words)))
    out = [p for p in out if p]
    if spec.get("sections"):
        out = number_sections(out, spec["sections"])
    if spec.get("zusatz"):                                  # '2. Zusatz zu § 1. (Die Idee.) Text' as '§ 1 Zusatz. (Die Idee.) Text'
        out = [re.sub(spec["zusatz"], lambda m: f"§ {m.group(1)} Zusatz.", p) for p in out]
    return "\n\n".join(merge_breaks(out)) + "\n"


# ── the works ───────────────────────────────────────────────────────
def gutenberg(n):
    return dict(page=f"https://www.gutenberg.org/ebooks/{n}", url=GUTENBERG.format(n=n), cache=f"gutenberg-{n}.txt", base=dict(gutenberg=True))


def archive(i):
    return dict(page=f"https://archive.org/details/{i}", url=ARCHIVE.format(i=i), cache=f"ia-{i}.txt", base={})


WORKS = []


def work(id, work, lang, title, who, year, edition, source, why, spec, ref="head", skip=None):
    """One text on the shelf. `work` is the short title shown with a passage ('Philosophy of Right'); ref 'sec' cites by §
    ('§189'), 'head' by the heading it stands under; `skip` says what of the book was left out."""
    WORKS.append(dict(id=id, work=work, lang=lang, title=title, who=who, year=year, edition=edition, source=source, why=why,
                      spec={**source["base"], **spec}, ref=ref, skip=skip))


def pd_en(who, y):
    return f"Hegel d. 1831; {who} died more than 70 years ago (public domain in the EU and the UK); published {y}, before 1929 (public domain in the US)"


FOOT_DE = r"^(\d{1,2}\)|\*+\)|\[Illustration)"             # Lasson's footnotes: '1) Hugo, Gustav Ritter von, 1764-1844 ...'
AUTO_DE = [(2, r"^\d\.\s+([A-ZÄÖÜ][^.]{2,60}?)[.,]?$"), (2, r"^[a-e]\)\s+([A-ZÄÖÜ].{2,60}?)[.,]?$")]
NO_PART = r"^(Erster|Zweiter|Dritter|Vierter) (Teil|Abschnitt)\.?$"

work("wallace-logic", "Encyclopaedia Logic", "en", "The Logic of Hegel (Encyclopaedia of the Philosophical Sciences, part 1)", "tr. William Wallace",
     "1892 (2nd ed.; 1st 1874)", "Oxford: Clarendon Press, 2nd edition, revised and augmented", gutenberg(55108), pd_en("Wallace (1844-1897)", 1892),
     dict(start=r"^CHAPTER I\.$", nth=1, end=r"^NOTES AND ILLUSTRATIONS$", sections=r"^(\d+)\.\]\s*", caps=True,
          drop=[r"^(INTRODUCTION|PRELIMINARY NOTION)\.?$", r"^CHAPTER [IVX]+\.?$"]),
     ref="sec", skip="Wallace's bibliographical notice and his Notes and Illustrations (his own writing, not Hegel's)")
work("wallace-mind", "Philosophy of Mind", "en", "Hegel's Philosophy of Mind (Encyclopaedia, part 3), §§ 377-577", "tr. William Wallace",
     "1894", "Oxford: Clarendon Press", gutenberg(39064), pd_en("Wallace (1844-1897)", 1894),
     dict(start=r"^INTRODUCTION\.$", end=r"^INDEX\.$", caps=True), ref="sec",
     skip="Wallace's five introductory essays and the index (he left out Hegel's Zusätze to this part)")
work("dyde-right", "Philosophy of Right", "en", "Hegel's Philosophy of Right", "tr. S. W. Dyde", "1896", "London: George Bell and Sons",
     archive("cu31924014578979"), pd_en("Dyde (1862-1947)", 1896),
     dict(start=r"^AUTHOR'S PREFACE\.?$", end=r"^INDEX OF WORDS\.?$", sections=r"^(\d{1,3})\.\s+(?=[A-Z])", caps=True, repeat=4,
          heads=[(1, r"^AUTHOR'S PREFACE\.?$", "Preface"), (1, r"^INTRODUCTION\.?$", "Introduction"), (1, r"^FIRST PART\.?$", "Abstract Right"),
                 (1, r"^SECOND PART\.?$", "Morality"), (1, r"^THIRD PART\.?$", "Ethical Life")]),
     ref="sec", skip="Dyde's translator's preface, notes and indexes (Cornell copy, OCR cleaned)")
work("sibree-history", "Philosophy of History", "en", "Lectures on the Philosophy of History", "tr. J. Sibree", "1857 (3rd German ed.)",
     "London: Henry G. Bohn, Bohn's Philosophical Library", archive("lecturesonphilos00hegeiala"), pd_en("Sibree (1816-1896)", 1857),
     dict(start=r"^INTRODUCTION\.?$", end=r"^THE END\.?$", caps=True, repeat=4,
          heads=[(1, r"^INTRODUCTION\.?$", "Introduction"),
                 (1, r"^GEOGRAPHICAL BASIS OF HIST\w+\.?$", "Introduction: the Geographical Basis of History"),
                 (1, r"^CLASSIFICATION OF HISTORIC DATA\.?$|^CLASSIFICATION OF HIST.{1,3}IC DATA", "Introduction: Classification of Historic Data"),
                 (1, r"^THE ORIENTAL .{3,6}\.?$", "The Oriental World"),
                 (2, r"^CHINA\.?$", "China"), (2, r"^INDIA\.?$", "India"), (2, r"^INDIA\s*[—-]\s*BUDDHISM", "India: Buddhism"),
                 (2, r"^P.ESIA\.?$", "Persia"), (2, r"^THE ASSYRIANS, BABYLONIANS", "The Assyrians, Babylonians, Medes and Persians"),
                 (2, r"^SYRIA AND THE SEMITIC", "Syria"), (2, r"^JUD.{1,3}A\.?$", "Judaea"), (2, r"^EGYPT\.?$", "Egypt"),
                 (2, r"^TRANSITION TO THE GREEK WORLD", "Transition to the Greek World"),
                 (1, r"^THE GREEK WORLD\.?$", "The Greek World"), (2, r"^THE ELEMENTS OF THE GREEK SPIRIT", "The Elements of the Greek Spirit"),
                 (2, r"^THE WARS WITH THE PERSIANS", "The Wars with the Persians"), (2, r"^ATHENS\.?$", "Athens"), (2, r"^SPARTA\.?$", "Sparta"),
                 (2, r"^THE PELOPONNESIAN WAR", "The Peloponnesian War"), (2, r"^THE MACEDONIAN EMPIRE", "The Macedonian Empire"),
                 (1, r"^THE ROMAN WORLD\.?$", "The Roman World"), (2, r"^ROME TO THE TIME OF THE SECOND PUNIC WAR", "Rome to the Second Punic War"),
                 (2, r"^ROME FROM THE SECOND PUNIC WAR", "Rome from the Second Punic War to the Emperors"),
                 (2, r"^ROME UNDER THE EMPERORS", "Rome under the Emperors"), (2, r"^CHRISTIANITY\.?$", "Christianity"),
                 (2, r"^THE BYZANTINE EMPIRE", "The Byzantine Empire"),
                 (1, r"^THE GERMAN WORLD\.?$", "The German World"),
                 (2, r"^THE ELEMENTS OF THE CHRISTIAN GERMAN WORLD", "The Elements of the Christian German World"),
                 (2, r"^THE BARBARIAN MIGRATIONS", "The Barbarian Migrations"), (2, r"^MAHOMETANISM", "Mahometanism"),
                 (2, r"^THE EMPIRE OF CHARLEMAGNE", "The Empire of Charlemagne"), (1, r"^THE MIDDLE AGES\.?$", "The Middle Ages"),
                 (2, r"^THE FEUDALITY AND THE HIERARCHY", "The Feudality and the Hierarchy"), (2, r"^THE CRUSADES", "The Crusades"),
                 (2, r"^THE TRANSITION FROM FEUDALISM", "The Transition from Feudalism to Monarchy"),
                 (1, r"^THE MODERN TIME\.?$", "The Modern Time"), (2, r"^THE REFORMATION\.?$", "The Reformation"),
                 (2, r"^THE ECLAIRCISSEMENT AND REVOLUTION", "The Enlightenment and the Revolution")]),
     skip="the prefaces (Sibree's, Gans's, Karl Hegel's) and the publisher's advertisements (OCR cleaned)")
for n, (vol, gid, years, first, start) in enumerate([
        ("I", 51635, "1892", "Inaugural Address", r"^INAUGURAL ADDRESS$"),
        ("II", 51636, "1894", None, r"^A\. PLATO\.$"),
        ("III", 58169, "1896", "Philosophy of the Middle Ages", r"^INTRODUCTION$")], 1):
    work(f"haldane-{n}", "History of Philosophy", "en", f"Lectures on the History of Philosophy, volume {vol}",
         "tr. E. S. Haldane" + ("" if n == 1 else " and Frances H. Simson"), years,
         "London: Kegan Paul, Trench, Trübner (the Gutenberg file is the 1955 Routledge reprint of the text)", gutenberg(gid),
         f"Hegel d. 1831; published {years}, before 1929 (public domain in the US); Haldane (1862-1937) died more than 70 years ago; "
         "the dates of her co-translator Frances H. Simson are not recorded in any source I could reach (see the notes below)",
         dict(start=start, end=r"^FOOTNOTES:", auto=True, **({"first": first} if first else {})), skip="the translators' notes, the footnotes and the index")
work("baillie-1", "Phenomenology of Mind", "en", "The Phenomenology of Mind, volume I (Preface to Reason)", "tr. J. B. Baillie", "1910",
     "London: Swan Sonnenschein; New York: Macmillan, 1st edition (not the revised edition of 1931)", archive("cu31924097557171"),
     "Hegel d. 1831; Baillie (1872-1940) died more than 70 years ago (public domain in the EU and the UK since 2011); the 1910 edition was published "
     "before 1929 (public domain in the US); the revised edition of 1931 is not used",
     dict(start=r"^PREFACE$", end=r"^END OF VOLUME I", caps=True, repeat=4, running=1, running_skip=r"phenomenology|^vol|^$", first="Preface",
          labels=[(r"^Sense", "Sense-certainty"), (r"^Perception", "Perception"), (r"^Understanding", "Force and Understanding"),
                  (r"Truth of Self|^T.ie Truth", "The Truth of Self-certainty"), (r"^Independence", "Independence of Self-consciousness"),
                  (r"LORDSHIP", "Lordship and Bondage"), (r"^Stoicism", "Stoicism"), (r"Unhappy|UnTiappy|Unliappy", "The Unhappy Consciousness"),
                  (r"Reasons? Cert", "Reason's Certainty and Reason's Truth"), (r"^Observation of Nature", "Observation of Nature"),
                  (r"Organic Nature", "Observation of Organic Nature"), (r"Self-c", "Observation of Self-consciousness"),
                  (r"^Physiognomy", "Physiognomy"), (r"^Phrenology", "Phrenology"), (r"^Realisation", "Realisation of Rational Self-consciousness"),
                  (r"^Pleas", "Pleasure and Necessity"), (r"^Virtue", "Virtue and the Course of the World"), (r"Herd", "The Spiritual Animal Kingdom"),
                  (r"Lawgiver", "Reason as Lawgiver"), (r"Testing", "Reason as Testing Laws"), (r"^INTRODUCTION$", "Introduction"), (r"^Preface$", "Preface")],
          brackets=True, heads=[(1, r"^INTEODUCTION$|^INTRODUCTION$", "Introduction")]),
     skip="Baillie's introduction, his bracketed summaries and notes (Cornell copy, OCR cleaned)")
work("baillie-2", "Phenomenology of Mind", "en", "The Phenomenology of Mind, volume II (Spirit, Religion, Absolute Knowledge)", "tr. J. B. Baillie", "1910",
     "London: Swan Sonnenschein; New York: Macmillan, 1st edition", archive("cu31924091023832"),
     "as volume I: Hegel d. 1831; Baillie (1872-1940); published 1910",
     dict(start=r"^SPIRIT \*$", end=r"BRBNDON AND SON", caps=True, repeat=4, running=1, running_skip=r"phenomenology|^vol|^$", first="Spirit",
          labels=[(r"^SPIRIT", "Spirit"), (r"Ethical Wor", "The Ethical World"), (r"Ethical Action", "Ethical Action"), (r"Q?u?ilt and Destiny", "Guilt and Destiny"),
                  (r"Legal Status", "Legal Status"), (r"Self-es", "Spirit in Self-estrangement"), (r"^Culture", "Culture and its Sphere of Reality"),
                  (r"^Belief and", "Belief and Pure Insight"), (r"Struggle of En", "The Struggle of Enlightenment with Superstition"),
                  (r"True Eesult|True Result", "The Truth of Enlightenment"), (r"Absolute Freedom", "Absolute Freedom and Terror"), (r"^Morality", "Morality"),
                  (r"Moral View", "The Moral View of the World"), (r"^Dissemblance", "Dissemblance"), (r"^Conscience", "Conscience: the Beautiful Soul"),
                  (r"^Evil and", "Evil and Forgiveness"), (r"^Religion$", "Religion"), (r"^Natural Religion", "Natural Religion"), (r"Artificer", "The Artificer"),
                  (r"Religion in the Form", "Religion in the Form of Art"), (r"Abstract Wor", "The Abstract Work of Art"), (r"Living Work|LivrNG", "The Living Work of Art"),
                  (r"Spiritual Work", "The Spiritual Work of Art"), (r"R?e?vealed|Eevealed", "Revealed Religion"), (r"ABSOLUTE KNOWLEDGE", "Absolute Knowledge")],
          brackets=True),
     skip="Baillie's bracketed summaries and notes (Cornell copy, OCR cleaned)")
work("bosanquet-art", "Philosophy of Fine Art", "en", "The Introduction to Hegel's Philosophy of Fine Art", "tr. Bernard Bosanquet", "1886",
     "London: Kegan Paul, Trench", gutenberg(46330), pd_en("Bosanquet (1848-1923)", 1886),
     dict(start=r"^INTRODUCTION\.$", end=r"^FOOTNOTES:", caps=True,
          heads=[(1, r"^THE RANGE OF", "Range of Aesthetic"), (1, r"^METHODS OF SCIENCE", "Methods of Science"),
                 (1, r"^THE CONCEPTION OF ARTISTIC BEAUTY", "Artistic Beauty"), (2, r"^PART I\.--THE WORK OF ART", "The Work of Art"),
                 (2, r"^PART II\.--THE END OF ART", "The End of Art"), (1, r"^HISTORICAL DEDUCTION", "Historical Deduction"),
                 (1, r"^DIVISION OF THE SUBJECT", "Division of the Subject")]),
     skip="Bosanquet's translator's preface, prefatory essay and notes")
work("phaen", "Phänomenologie des Geistes", "de", "Phänomenologie des Geistes", "Gutenberg-DE transcription of the first edition (Bamberg und Würzburg, 1807)",
     "1807 (transcribed 2004)", "Project Gutenberg #6698, from the Gutenberg Projekt-DE", gutenberg(6698),
     "Hegel d. 1831; a transcription of the 1807 edition: a nineteenth-century text, public domain everywhere",
     dict(start=r"^Vorrede$", nth=1, first="Vorrede", heads=[
         (1, r"^Einleitung$", "Einleitung", "para"), (1, r"^I\. Die sinnliche Gewißheit", "Die sinnliche Gewißheit", "para"),
         (1, r"^II\. Die Wahrnehmung", "Die Wahrnehmung", "para"), (1, r"^III\. Kraft und Verstand", "Kraft und Verstand", "para"),
         (1, r"^IV\. Die Wahrheit", "Selbstbewußtsein", "para"), (2, r"^A\. Selbstständigkeit und Unselbst", "Herrschaft und Knechtschaft", "para"),
         (2, r"^B\. Freiheit des Selbstbewußtseins", "Stoizismus, Skeptizismus und das unglückliche Bewußtsein", "para"),
         (1, r"^V\. Gewißheit und Wahrheit der Vernunft", "Die Vernunft", "para"), (2, r"^A\. Beobachtende Vernunft", "Beobachtende Vernunft", "para"),
         (2, r"^B\. Die Verwirklichung", "Die Verwirklichung des vernünftigen Selbstbewußtseins", "para"),
         (2, r"^C\. Die Individualität", "Die Individualität", "para"), (1, r"^VI\. Der Geist", "Der Geist", "para"),
         (2, r"^A\. Der wahre Geist", "Sittlichkeit", "para"), (2, r"^B\. Der sich entfremdete Geist", "Bildung", "para"),
         (2, r"^I\. Die Welt des sich entfremdeten", "Die Welt des sich entfremdeten Geistes", "para"), (2, r"^II\. Die Aufklärung", "Aufklärung", "para"),
         (2, r"^III\. Die absolute Freiheit", "Die absolute Freiheit und der Schrecken", "para"),
         (2, r"^C\. Der seiner selbst gewisse Geist", "Moralität", "para"), (1, r"^VII\. Die Religion", "Die Religion", "para"),
         (2, r"^A\. Natürliche Religion", "Natürliche Religion", "para"), (2, r"^B\. Die Kunst-Religion", "Kunst-Religion", "para"),
         (2, r"^C\. Die offenbare Religion", "Die offenbare Religion", "para"), (1, r"^VIII\. Das absolute Wissen", "Das absolute Wissen", "para")]),
     skip="the Gutenberg-DE blurb and table of contents")
work("rechts", "Philosophie des Rechts", "de", "Grundlinien der Philosophie des Rechts, with Gans's Zusätze", "ed. Georg Lasson (Philosophische Bibliothek 124)",
     "1911 (text of 1821, Zusätze of 1833)", "Leipzig: Felix Meiner", archive("grundlinienderph00hege"),
     "Hegel d. 1831; Lasson (1862-1932) died more than 70 years ago; Gans's Zusätze of 1833; published 1911, before 1929: public domain in the US and the EU",
     dict(start=r"^Vorrede\.$", end=r"^Namenregister\.$", first="Vorrede", footnotes=FOOT_DE, sections=r"^§\s*(\d{1,3}|[0-9OIl]{1,4})(?=\W|$)\.?\s*",
          zusatz=r"^\d+[.,]\s+Zusatz zu §§?\s*(\d+)\.?", drop=[r"§\s*[\d—\-– ]+\.?\s+\d+$", r"^\d+\s+(Erster|Zweiter|Dritter) Teil", NO_PART], repeat=4,
          heads=[(1, r"^Einleitung\.$", "Einleitung"), (1, r"^Erster Teil\.$", "Das abstrakte Recht"), (1, r"^Zweiter Teil\.$", "Die Moralität"),
                 (1, r"^Dritter Teil\.$", "Die Sittlichkeit"), (1, r"^Zusätze\.$", "Zusätze")]),
     ref="sec", skip="Lasson's long introduction, his notes and the registers")
work("welt-1", "Philosophie der Geschichte", "de", "Vorlesungen über die Philosophie der Weltgeschichte, I: Die Vernunft in der Geschichte (Einleitung)",
     "ed. Georg Lasson (Philosophische Bibliothek 171a)", "1917", "Leipzig: Felix Meiner", archive("11171849"),
     "Hegel d. 1831; Lasson (1862-1932) died more than 70 years ago; published 1917, before 1929: public domain in the US and the EU",
     dict(start=r"^Der Gegenstand dieser Vorlesungen ist die Philo-$", end=r"^Für die vorliegende Ausgabe", single=True, first="Einleitung", footnotes=FOOT_DE,
          drop=[r"^(I|II|III|[IVX]+)\.\s.*\s\d{1,3}\.?$", r"^\S{0,4}\s?Ph\w+ie der Geschichte\W+Einleitung\W*\d*$", r"^[\d.\s]*Einleitung[,. ]*\d*$"],
          heads=[(1, r"^[1I]\.\s*Die\.? Vernunftansicht der Weltgeschichte", "Die Vernunftansicht der Weltgeschichte"),
                 (1, r"^[1I]\. Die Idee\.?$", "Die Idee der Weltgeschichte"), (2, r"^a\) Die geistige Welt", "Die geistige Welt"),
                 (2, r"^b\) Der Begriff des Geistes", "Der Begriff des Geistes"), (2, r"^c\) Der Inhalt der Weltgeschichte", "Der Inhalt der Weltgeschichte"),
                 (2, r"^d\) Der Pro", "Der Prozeß des Weltgeistes"), (2, r"^e\) Der Endzweck", "Der Endzweck"),
                 (1, r"^2\. Die Mittel der Verwirklichung", "Die Mittel der Verwirklichung"), (2, r"^a\) Die Individualität", "Die Individualität"),
                 (2, r"^b\) Die erhaltenden Individuen", "Die erhaltenden Individuen"),
                 (2, r"^c\) Die weltgeschichtlichen Individuen", "Die weltgeschichtlichen Individuen"),
                 (2, r"^d\) Das Schicksal der Individuen", "Das Schicksal der Individuen"), (2, r"^e\) Der Wert des Individuums", "Der Wert des Individuums"),
                 (1, r"^3\. Das Material der Verwirklichung", "Das Material der Verwirklichung"), (2, r"^a\) Der Staat", "Der Staat"),
                 (2, r"^b\) Der Rechtszustand", "Der Rechtszustand"), (2, r"^c\) Staat und Religion", "Staat und Religion"),
                 (2, r"^e\) Die Verfassung", "Die Verfassung"), (1, r"^III\. Der Gang d\w*\.? Weltgeschichte", "Der Gang der Weltgeschichte"),
                 (1, r"^[1I]\. Die verschiedenen Arten der .?eschichtsbetrachtung", "Die Arten der Geschichtsbetrachtung"),
                 (1, r"^II\. Der Naturzusammenhang oder die geographische", "Die geographische Grundlage der Weltgeschichte"),
                 (2, r"^2\. Die Neue Welt", "Die Neue Welt"), (2, r"^a\) Afrika", "Afrika"), (2, r"^b\) Asien", "Asien"), (2, r"^c\) Europa", "Europa"),
                 (1, r"^III\. Einteilung", "Einteilung der Weltgeschichte")]),
     skip="Lasson's preface (war-time politics, not Hegel), his report on the text and the registers")
for n, (vol, gid, first, start, end, name, year) in enumerate([
        ("II", "11171850", "Die orientalische Welt", r"^Erster Teil\.$", r"^Erläuterungen und Berichtigungen$", "Die orientalische Welt", "1919"),
        ("III", "11171851", "Die griechische Welt", r"^Zweiter Teil\.$", r"^Sachregister\.", "Die griechische und die römische Welt", "1920"),
        ("IV", "11171852", "Die germanische Welt", r"^Übersicht\.$", r"Sachregister\.\s*[=\-—]?$", "Die germanische Welt", "1920")], 2):
    heads = {2: [(1, r"^China\.$", "China"), (1, r"^Indien\.$", "Indien"), (1, r"^Persien\.$", "Persien"), (1, r"^Westasien\.$", "Westasien"),
                 (1, r"^Ägypten\.$", "Ägypten")],
             3: [(1, r"^Übersicht\.$", "Die römische Welt")], 4: []}[n]
    work(f"welt-{n}", "Philosophie der Geschichte", "de", f"Vorlesungen über die Philosophie der Weltgeschichte, {vol}: {name}",
         f"ed. Georg Lasson (Philosophische Bibliothek 171{'bcd'[n - 2]})", year, "Leipzig: Felix Meiner", archive(gid),
         f"Hegel d. 1831; Lasson (1862-1932) died more than 70 years ago; published {year}, before 1929: public domain in the US and the EU",
         dict(start=start, end=end, single=True, first=first, heads=heads, auto=AUTO_DE, footnotes=FOOT_DE,
              drop=[r"^[\d.\s]*Die \w+ Welt\W.*\d{1,3}$", r"^\d*\s*Philosophie der Geschichte\W+Die \w+ Welt\W*\d*$", NO_PART]),
         skip="Lasson's preface, his notes and the registers")
work("enzyklopaedie", "Enzyklopädie", "de", "Encyklopädie der philosophischen Wissenschaften im Grundrisse (3rd ed. 1830), as far as this volume goes (§§ 1-496)",
     "ed. Karl Rosenkranz (Kirchmann's Philosophische Bibliothek 30)", "1870", "Berlin: L. Heimann", archive("encyklopdiederph00hege"),
     "Hegel d. 1831; Rosenkranz (1805-1879) and Kirchmann (1802-1884) died more than 70 years ago; published 1870: public domain everywhere",
     dict(start=r"^Vorrede zur ersten Ausgabe\.?$", end=r"^Erläuterungen\.?$", first="Vorrede", sections=r"^§[.•]?\s*(\d{1,3}|\S{1,4})\.",
          drop=[r"^Einleitung\.\s*\d*$", r"^\d*\s*(Erster|Zweiter|Dritter) Theil\.?\s*\d*$"],
          heads=[(1, r"^Vorrede zur zweiten Ausgabe\.?$", "Vorrede zur zweiten Ausgabe"), (1, r"^Einleitung\.$", "Einleitung")]),
     ref="sec", skip="Rosenkranz's introduction; the scanned volume breaks off at §496")

LEFT_OUT = [
    ("Rosenkranz, Georg Wilhelm Friedrich Hegel's Leben (1844)", "Public domain, but every scan on archive.org is Fraktur read by an OCR engine for roman type: about three words "
     "in ten are wrong (long s read as f or j, d as b, ch as d), and no clean transcription is reachable. A shelf that offers him 'muftifcher' is worse than none. "
     "It needs a hand transcription (the Deutsches Textarchiv or Zeno carry no copy I could use)."),
    ("Vorlesungen über die Ästhetik; Vorlesungen über die Geschichte der Philosophie, in German", "The nineteenth-century editions (Hotho 1835-38, Michelet 1833-36) exist only as "
     "Fraktur scans with the same OCR damage. The 1927 Jubiläumsausgabe is in roman type but is no nineteenth-century text, and I left it out rather than weigh its editor's rights. "
     "Both works are on the shelf in English (Bosanquet's Introduction to the Aesthetics; Haldane and Simson)."),
    ("Briefe von und an Hegel (K. Hegel, 1887); Neue Briefe Hegels und Verwandtes (Lasson, 1912)", "The first is a Fraktur scan. The second prints the letters among articles by "
     "Ernst Crous (d. 1967) and Herman Nohl (d. 1960), still in copyright in the EU, and the OCR cannot separate them. No clean public-domain edition of selected letters is reachable."),
    ("Speirs and Burdon Sanderson, Lectures on the Philosophy of Religion (1895); Osmaston, The Philosophy of Fine Art (1920)", "Public domain in the US by their dates, but I could not "
     "establish when the translators died, so the status in the EU is unclear. Left out."),
    ("Hegel's Science of Logic (Gutenberg 6729 and 6834, in German)", "Public domain and clean, but not asked for and as long as the rest together; the Encyclopaedia Logic carries the same thought."),
    ("Schriften zur Politik und Rechtsphilosophie (Lasson 1913); Hegels theologische Jugendschriften (Nohl 1907)", "Editors' introductions and apparatus of uncertain status "
     "(Nohl d. 1960); not needed for this round."),
]


# ── the shelf on disk ───────────────────────────────────────────────
def path_of(w):
    return SHELF / f"{w['id']}.txt.gz"


def read_work(w):
    with gzip.open(path_of(w), "rt", encoding="utf-8") as f:
        return f.read()


def write_work(w, text):
    SHELF.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(path_of(w), "wb", compresslevel=9, mtime=0) as f:
        f.write(text.encode("utf-8"))


def pick(ids):
    chosen = [w for w in WORKS if not ids or w["id"] in ids]
    if ids and len(chosen) != len(set(ids)):
        sys.exit("unknown work: " + ", ".join(set(ids) - {w["id"] for w in WORKS}))
    return chosen


def cmd_fetch(ids):
    for w in pick(ids):
        cached = (CACHE / w["source"]["cache"]).exists()
        p = fetch(w["source"]["url"], w["source"]["cache"])
        print(f"{'cached ' if cached else 'fetched'} {w['id']:15} {p.stat().st_size / 1e6:6.2f} MB  {w['source']['url']}")


def cmd_clean(ids):
    for w in pick(ids):
        raw = (CACHE / w["source"]["cache"]).read_text(encoding="utf-8", errors="replace")
        text = clean(raw, w["spec"])
        write_work(w, text)
        print(f"cleaned {w['id']:15} {len(raw) / 1e6:6.2f} MB -> {len(text) / 1e6:6.2f} MB text, {text.count(chr(10) * 2)} paragraphs, "
              f"{path_of(w).stat().st_size / 1e6:5.2f} MB gz")


def probe(ids):
    """The headings and a few paragraphs of a cleaned work, to check a spec by eye."""
    for w in pick(ids):
        text = clean((CACHE / w["source"]["cache"]).read_text(encoding="utf-8", errors="replace"), w["spec"])
        paras = text.split("\n\n")
        print(f"== {w['id']}: {len(text)} characters, {len(paras)} paragraphs")
        print("\n".join(p for p in paras if p.startswith("#")))
        for p in paras[len(paras) // 3: len(paras) // 3 + 3]:
            print("   >", p[:300])


def known_ratio(text, vocab):
    toks = re.findall(r"[a-z]{3,}", shelf.fold(text))
    return sum(vocab[t] >= 3 for t in toks) / len(toks) if len(toks) >= 20 else 0.0


GARBLE = re.compile(r"[a-zäöüß][A-ZÄÖÜ]|\\|[a-z][|{}][a-z]")       # a capital inside a word, a backslash, a bar: OCR ('moraUty', 'difEerences')


def readable(text, vocab, minimum=0.88):
    """Enough real words and letters, and no letter the scan has spoiled: a passage of OCR litter or a table is not worth showing."""
    return known_ratio(text, vocab) >= minimum and sum(c.isalpha() for c in text) >= 0.78 * len(text) and len(text) >= 150 \
        and not GARBLE.search(text)


# what a capital inside a word stands for in these scans: 'itseK' (itself), 'aU' (all), 'reaUty' (reality), 'simpHcity', 'difEerence'
SPOILT = {"U": ("ll", "li", "l", "il"), "K": ("lf", "ll", "li", "h"), "H": ("li", "lf", "ll"), "E": ("f", "ff", "ll"), "M": ("hi", "lf"), "I": ("l",), "T": ("h", "li"), "J": ("h", "li")}


def mend(text, vocab):
    """(text, n): the words of text that the scan has spoiled with a capital inside, set right where exactly one reading is a known word (`vocab`
    counts the words of the shelf that are not spoiled themselves; a reading must occur five times), or one is at least four times as common as
    the others; and 'w' for the '\\v' of a scanned w. n is the number of words changed."""
    count = 0

    def fix(m):
        nonlocal count
        word = m.group(0)
        spots = [i for i in range(1, len(word)) if word[i].isupper() and word[i - 1].islower()]
        if not spots or len(spots) > 3 or sum(c.isupper() for c in word) > len(word) // 2:       # (a word in capitals is a heading, not a spoiled word)
            return word
        options = [(word[i].lower(),) + SPOILT.get(word[i], ()) for i in spots]
        found = {}
        for pick in itertools.product(*options):
            cand, last = "", 0
            for i, x in zip(spots, pick):
                cand, last = cand + word[last:i] + x, i + 1
            cand += word[last:]
            known = vocab[shelf.fold(cand)]
            if known >= 5:
                found[cand] = known
        ranked = sorted(found.items(), key=lambda x: -x[1])
        if ranked and (len(ranked) == 1 or ranked[0][1] >= 4 * ranked[1][1]):
            count += 1
            return ranked[0][0]
        return word

    text = re.sub(r"\\v(?=[a-z])", "w", text)
    return re.sub(r"[A-Za-zÄÖÜäöüß]{2,}", fix, text), count


def kept_works():
    """The passages of every cleaned work that are worth keeping, as the index holds them: split, spoiled words mended, and dropped where the
    scan is damaged or the text names something from after 1831 (world/data/after_1831.txt). [{id, work, lang, dropped, mended, passages}].
    tools/train_data.py reads the same passages for the training corpus, so a damaged one is out of both."""
    from world.world import wordlist
    later = wordlist("after_1831.txt", "s?")
    texts = {w["id"]: read_work(w) for w in WORKS if path_of(w).exists()}
    split = {w["id"]: shelf.split_passages(texts[w["id"]], w["ref"]) for w in WORKS if w["id"] in texts}
    vocab, good = {lang: Counter() for lang in ("en", "de")}, {lang: Counter() for lang in ("en", "de")}
    for w in WORKS:
        if w["id"] in split:
            for _, p in split[w["id"]]:
                vocab[w["lang"]].update(re.findall(r"[a-z]{3,}", shelf.fold(p)))
                good[w["lang"]].update(t for t in re.findall(r"[a-z]{3,}", shelf.fold(GARBLE.sub(" ", p))))
    works = []
    for w in WORKS:
        if w["id"] not in split:
            continue
        kept, noise, anachronism, mended = [], 0, 0, 0
        for ref, p in split[w["id"]]:
            p, n = mend(p, good[w["lang"]])
            mended += n
            if (later and later.search(p)) or (w["spec"].get("footnotes") == FOOT_DE and re.search(r"\b1[4-9]\d\d\s?[—–-]\s?1[4-9]\d\d\b", p)):
                anachronism += 1                          # (in Lasson's volumes, a pair of dates is his footnote on a person)
            elif not readable(p, vocab[w["lang"]]):
                noise += 1
            else:
                kept.append((ref, p))
        works.append({"id": w["id"], "work": w["work"], "lang": w["lang"], "dropped": {"damaged": noise, "later": anachronism}, "mended": mended, "passages": kept})
    return works


def build():
    """The index of every cleaned work, built from its kept passages and saved."""
    index = shelf.build_index(kept_works())
    shelf.save_index(index)
    return index


def stats(index):
    sizes = sorted(len(t) for t in index["texts"])
    q = lambda f: sizes[int(f * (len(sizes) - 1))]
    print(f"index: {len(sizes)} passages from {len(index['works'])} works; length min {sizes[0]}, 10% {q(0.1)}, median {q(0.5)}, 90% {q(0.9)}, max {sizes[-1]};"
          f" {len(index['terms'])} terms; {shelf.INDEX.stat().st_size / 1e6:.1f} MB")
    for w in index["works"]:
        print(f"  {w['id']:15} {w['n']:5} passages   dropped: damaged {w['dropped']['damaged']}, later or editor's {w['dropped']['later']}; words mended {w['mended']}")


def mb(n):
    return f"{n / 1e6:.2f}"


def manifest():
    """mind/shelf/MANIFEST.md: every text with its source and why it is public domain, what was left out, the sizes."""
    index = json.loads(gzip.open(shelf.INDEX, "rt", encoding="utf-8").read())
    meta = {w["id"]: w for w in index["works"]}
    rows, chars, gz = [], 0, 0
    for w in WORKS:
        if not path_of(w).exists():
            continue
        size, text = path_of(w).stat().st_size, read_work(w)
        chars, gz = chars + len(text), gz + size
        m = meta.get(w["id"], {"n": 0, "dropped": {"damaged": 0, "later": 0}, "mended": 0})
        rows.append(f"| `{w['id']}` | **{w['title']}**<br>{w['who']}<br>{w['year']}; {w['edition']} | {'English' if w['lang'] == 'en' else 'German'} "
                    f"| [{w['source']['page'].split('//')[1]}]({w['source']['page']}) | {w['why']} | {mb(len(text.encode('utf-8')))} / {mb(size)} | {m['n']} "
                    f"({m['dropped']['damaged']} damaged, {m['dropped']['later']} after 1831 dropped; {m.get('mended', 0)} spoiled words mended) |")
    isz = shelf.INDEX.stat().st_size
    out = ["# The shelf: manifest", "",
           "Hegel's own books, as far as public-domain texts could be had. Written by `python3 tools/corpus.py --manifest`; the texts are cleaned "
           "by `tools/corpus.py --clean`, split into passages and indexed by `--index` (see `world/shelf.py`). Nothing is fetched at runtime.", "",
           "Public-domain rule: Hegel died in 1831; the translator or editor died more than 70 years ago (so the text is free in the EU and the UK); "
           "and the edition was published before 1929 (so it is free in the US). A text whose status is unclear is not here.", "",
           "## On the shelf", "",
           "| id | work | language | source | why it is public domain | MB text / MB gz | passages |", "|---|---|---|---|---|---|---|", *rows, "",
           f"**Total:** {len(rows)} texts, {mb(chars)} MB of text, {mb(gz)} MB gzipped on disk (`mind/shelf/*.txt.gz`), and the index "
           f"`mind/shelf/index.json.gz`, {mb(isz)} MB, with {len(index['texts'])} passages. Together {mb(gz + isz)} MB in the repository.", "",
           "## Notes on status", "",
           "- **Haldane and Simson, History of Philosophy (volumes II and III; the title page of volume I names Haldane alone).** Published 1892-96, so free in the US. "
           "Elizabeth Haldane died in 1937. Frances H. Simson, who translated volumes II and III with her, is a name I could not date in any source I could reach; "
           "she was an adult translator in 1892, so she would have had to live beyond 1956 for the text to be protected in the EU. Welt may strike these two files "
           "(`haldane-2`, `haldane-3`) if that is too thin.",
           "- **Dyde, Philosophy of Right.** Samuel Walters Dyde died in 1947 (from memory, not checked against a record); the book is of 1896.",
           "- **Baillie, Phenomenology of Mind.** The 1910 edition only. Baillie died in 1940, so the text has been free in the EU and the UK since 2011; "
           "the revised edition of 1931 is not used.",
           "- **The Gutenberg files of Haldane and Simson** are the 1955 Routledge reprint; only the text of 1892-96 is used.",
           "- **Lasson's Meiner volumes (1911-1920)** carry the editor's prefaces and notes; they are cut. The 1917 preface of the first volume is war-time politics.",
           "- Passages that name anything on `world/data/after_1831.txt` are dropped from the index, and so are passages in which fewer than 88% of the words "
           "are known words of the shelf, or in which a letter is still spoiled by the scan (a capital inside a word, a backslash). Words the scan spoiled in "
           "a regular way ('itseK' for itself, 'aU' for all, 'reaUty') are set right first, but only where one reading is a word that occurs on the shelf "
           "and no other is nearly as common; the table says how many each text needed. About 8% of all passages are lost to damage, up to 16% in the worst scans "
           "(Baillie volume II, Dyde).", "",
           "## Left out, and why", ""]
    out += [f"- **{what}.** {why}" for what, why in LEFT_OUT]
    out += ["", "## What the cleaning did", "",
            "Running heads and page numbers removed (the ones that recur, and the ones that fall in the middle of a sentence), words split by a hyphen at a line end "
            "joined (the hyphen stays where the text writes the compound that way elsewhere), footnote marks and the translators' footnotes dropped, italics marks removed, "
            "OCR spacing mended, paragraphs made whole across page breaks. Section numbers are kept (`§ 189.`), and the headings each work stands under; "
            "the lecture additions of the Philosophy of Right (Gans's Zusätze) are marked `§ N Zusatz.`.", ""]
    (SHELF / "MANIFEST.md").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {SHELF / 'MANIFEST.md'}: {len(rows)} texts, {mb(chars)} MB text, {mb(gz)} MB gz, index {mb(isz)} MB")


def cmd_list():
    for w in WORKS:
        raw = CACHE / w["source"]["cache"]
        print(f"{w['id']:15} {w['lang']}  cached {'yes' if raw.exists() else 'no ':3}  built {'yes' if path_of(w).exists() else 'no ':3}  {w['title']}")
    print(f"index: {'yes' if shelf.INDEX.exists() else 'no'}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*", help="work ids (default: all)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--clean", action="store_true")
    p.add_argument("--index", action="store_true")
    p.add_argument("--manifest", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--probe", action="store_true")
    a = p.parse_args()
    if a.list or not (a.fetch or a.clean or a.index or a.manifest or a.all or a.probe):
        return cmd_list()
    if a.fetch or a.all:
        cmd_fetch(a.ids)
    if a.clean or a.all:
        cmd_clean(a.ids)
    if a.probe:
        probe(a.ids)
    if a.index or a.all:
        t0 = time.time()
        stats(build())
        print(f"built in {time.time() - t0:.1f} s")
    if a.manifest or a.all:
        manifest()


if __name__ == "__main__":
    main()
