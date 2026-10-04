#!/usr/bin/env python3
"""OCR of a scan on archive.org with Tesseract: the raw text that tools/corpus.py cleans, for books whose own archive.org text is too damaged.

    python3 tools/ocr.py bub_gb_MjCJlAnRvYoC                 # Fraktur (frak2021): tools/.cache/ocr-frak2021-bub_gb_MjCJlAnRvYoC.txt
    python3 tools/ocr.py hegel00cair_0 --model eng           # roman type (Tesseract's best English model)

archive.org's own text of a Fraktur book comes from an engine for roman type, which gets about three words in ten wrong (long s read as f,
d as b). UB Mannheim's frak2021 was trained on German Fraktur prints of the 16th to 20th centuries and gets about one word in fifty wrong on
a clean nineteenth-century page. Needs the tesseract command (Ubuntu: apt install tesseract-ocr); the model is fetched once into
tools/.cache/tessdata. Every page is kept in tools/.cache/ocr/<model>/<item>/, so a stopped run picks up where it was. About two seconds a
page per core."""
import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
MODELS = {"frak2021": "https://ub-backup.bib.uni-mannheim.de/~stweil/tesstrain/frak2021/tessdata_best/frak2021-0.905.traineddata",
          "eng": "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/eng.traineddata"}
PAGE = "https://archive.org/download/{item}/page/n{n}.jpg"
UA = "hegel-in-delhi-corpus/1.0 (private research project)"
UMLAUT = {"a": "ä", "o": "ö", "u": "ü", "A": "Ä", "O": "Ö", "U": "Ü"}
SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"
FOLIO = re.compile(rf"^[\d{SUP}IVXLCivxlc]+\s+|\s+[\d{SUP}IVXLCivxlc]+\.?$")       # a page number at either end of a running head
BOOK = 20                                               # a running head on more pages than this is the book's or the part's, not a chapter's


def get(url, path, tries=4):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                path.write_bytes(r.read())
            return path
        except OSError as e:
            if attempt == tries - 1:
                raise SystemExit(f"could not fetch {url}: {e}")
            time.sleep(3 * (attempt + 1))


def normalize(text):
    """Modern letters for the print's: long s as s, a small e written over a vowel as its umlaut, the Fraktur hyphen as a hyphen; and the
    English model's one habit, a 1 for an i inside a word ('1s', 'pun1shment')."""
    text = text.replace("ſ", "s").replace("⸗", "-").replace("­", "-")
    text = re.sub(r"(?<![\d.,])1(?=[a-z])|(?<=[a-z])1(?![\d.,])", "i", text)
    text = re.sub("([aouAOU])ͤ", lambda m: UMLAUT[m.group(1)], text)
    text = text.replace("ͤ", "")                                    # an e over a letter that already has its umlaut
    text = re.sub(r"(?<=\w)[—=–](?=\n)", "-", text)                      # a word broken at the end of a line
    text = re.sub(r"(?m)^#+\S*\s*", "", text)                             # a smudge read as '#' would pass for a heading
    return re.sub(r"[ \t]+\n", "\n", text)


def title_of(head):
    return re.sub(r"[\s.,—–-]+$", "", FOLIO.sub("", head)).strip()


def same(a, b):
    """Two readings of one heading: at most one letter in eight differs (two in a short one). 'Arkunden' is 'Urkunden', 'Hegel's Verheirathung,
    Herbst 181I' is 'Hegel's Verheirathung, Herbst 1811'; 'Fragmente historischer Studien' is not 'Fragmente theologischer Studien', and
    'machen' is not 'Umgang'. A worse misreading is caught in assemble, when it stands next to its chapter."""
    a, b = a.lower().replace(" ", ""), b.lower().replace(" ", "")
    matched = sum(m.size for m in difflib.SequenceMatcher(None, a, b).get_matching_blocks())
    return max(len(a), len(b)) - matched <= max(2, len(max(a, b, key=len)) // 8)


def rule(line):
    """A printed rule or a smudge read as text: '——— — i ———————— a — _ -', '*«', '+ >'."""
    seen = line.replace(" ", "")
    return bool(seen) and (sum(c.isalnum() for c in seen) < 0.5 * len(seen) or len(re.findall(r"[—_]{3,}", line)) >= 1 and sum(c.isalpha() for c in seen) < 0.7 * len(seen))


def assemble(pages):
    """The text of the book from its pages: each page's running head ('86 Erstes Buch.', 'Hauslehrerleben in Frankfurt a. M. 81') taken off,
    and the chapters marked as headings, '@@ Title' on a line of its own, where they begin: at the line in the text that is a chapter's
    heading (named as that line reads, the best-printed form), or else at the first page that carries it as its running head (named by the
    commonest reading of that head). A chapter's title is a head with its page number at the end (the right-hand page); the head with the
    number first names the book or the part, and so does any head on more than BOOK pages: those mark nothing."""
    heads, bodies = [], []
    for page in pages:
        lines = [x for x in page.split("\n") if not rule(x)]
        while lines and not lines[0].strip():
            lines.pop(0)
        first = lines[0].strip() if lines else ""
        head = len(first) <= 90 and bool(FOLIO.search(first)) and len(title_of(first)) >= 4
        recto = head and not re.match(rf"^[\d{SUP}IVXLCivxlc]+\s", first)
        heads.append((title_of(first), recto) if head else None)
        bodies.append("\n".join(lines[1:] if head else lines).strip())
    groups = []                                         # [{"readings": Counter, "verso": bool}]
    for t, recto in filter(None, heads):
        g = next((g for g in groups if any(same(r, t) for r in g["readings"])), None)
        if g is None:
            g = {"readings": {}, "verso": False}
            groups.append(g)
        g["readings"][t] = g["readings"].get(t, 0) + 1
        g["verso"] |= not recto
    chapters = [g for g in groups if sum(g["readings"].values()) <= BOOK and not g["verso"]]
    find = lambda text: next((i for i, g in enumerate(chapters) if any(same(r, text) for r in g["readings"])), None)
    name = lambda i: max(chapters[i]["readings"].items(), key=lambda x: x[1])[0]
    out, last = [], None
    for head, body in zip(heads, bodies):
        i = find(head[0]) if head else None
        marked = False
        spoilt = i is not None and last is not None and sum(chapters[i]["readings"].values()) <= 2 and difflib.SequenceMatcher(None, name(last), name(i)).ratio() >= 0.7
        if i is not None and i != last and not spoilt:  # (a head read once or twice, close to the last chapter's, is that chapter misread)
            out.append(f"@@ {name(i)}")
            marked = True
        if i is not None and not spoilt:
            last = i
        for k, para in enumerate(re.split(r"\n\s*\n", body)):
            line = re.sub(r"^[IVX]+\.\n", "", para.strip())                 # 'IX.' over a heading is its number
            j = find(title_of(line)) if "\n" not in line and len(line) <= 90 else None
            if j is None:
                out.append(para)
                continue
            if k == 0 and marked:
                out.pop()                               # the running head named the chapter that begins on this very page
            if j != last or (k == 0 and marked):
                out.append(f"@@ {title_of(line)}")
            last = j
    text = "\n\n".join(p for p in out if p.strip())
    return re.sub(f"[{SUP}]", "", text)


def pages_of(item):
    url = f"https://archive.org/metadata/{item}/metadata/imagecount"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return int(json.loads(r.read())["result"])


def ocr_page(item, n, folder, tessdata, model):
    out = folder / f"n{n:04d}.txt"
    if out.exists():
        return normalize(out.read_text(encoding="utf-8"))              # (normalize again: a page read before a rule was added gets it too)
    with tempfile.TemporaryDirectory() as tmp:
        img = get(PAGE.format(item=item, n=n), Path(tmp) / "page.jpg")
        run = subprocess.run(["tesseract", str(img), "stdout", "--tessdata-dir", str(tessdata), "-l", model, "--psm", "4"],
                             capture_output=True, text=True, env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    if run.returncode:
        raise SystemExit(f"tesseract failed on page {n}: {run.stderr.strip()[-300:]}")
    text = normalize(run.stdout).strip()
    out.write_text(text, encoding="utf-8")
    return text


def ocr(item, model="frak2021", workers=None, say=print):
    """tools/.cache/ocr-<model>-<item>.txt: every page of the scan, read, normalized and put together (see assemble)."""
    if not shutil.which("tesseract"):
        raise SystemExit("tesseract is not installed (Ubuntu: sudo apt install tesseract-ocr)")
    tessdata = CACHE / "tessdata"
    tessdata.mkdir(parents=True, exist_ok=True)
    if not (tessdata / f"{model}.traineddata").exists():
        get(MODELS[model], tessdata / f"{model}.traineddata")
    folder = CACHE / "ocr" / model / item
    folder.mkdir(parents=True, exist_ok=True)
    total, t0 = pages_of(item), time.time()
    say(f"{item}: {total} pages, model {model}")
    texts = []
    with ThreadPoolExecutor(workers or os.cpu_count() or 2) as pool:
        for i, text in enumerate(pool.map(lambda n: ocr_page(item, n, folder, tessdata, model), range(total)), 1):
            texts.append(text)
            if i % 25 == 0 or i == total:
                say(f"  {i}/{total} pages, {time.time() - t0:.0f} s", flush=True)
    out = CACHE / f"ocr-{model}-{item}.txt"
    out.write_text(assemble(texts) + "\n", encoding="utf-8")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("item", help="the archive.org identifier of the scan")
    p.add_argument("--model", choices=sorted(MODELS), default="frak2021", help="frak2021 for Fraktur (default), eng for roman type")
    p.add_argument("--workers", type=int, help="pages read at once (default: one per core)")
    a = p.parse_args()
    print(f"wrote {ocr(a.item, a.model, a.workers)}")


if __name__ == "__main__":
    sys.exit(main())
