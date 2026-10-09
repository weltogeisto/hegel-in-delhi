#!/usr/bin/env python3
"""Hegel in Delhi: the Hegelizer's training data. Standard library only, Python 3.9 and later; runs on the PC under WSL2.

    python3 tools/hegelizer.py --build                                   # mind/train/hegelizer-units.jsonl: passages of his English books, 150 to 250 words each
    python3 tools/hegelizer.py --paraphrase --url http://127.0.0.1:8082 --workers 4 [--limit 20] [--retry-failed]
    python3 tools/hegelizer.py --stats                                   # units, done, failed, the mean word ratio and three samples to read

The method is inverse paraphrasing (Krishna et al., EMNLP 2020, "Reformulating Unsupervised Style Transfer as Paraphrase Generation"): take authentic
passages, have a model rewrite each in plain modern prose, then train a LoRA to turn the plain version back into the authentic original
(pc/train_hegel.py --phase restyle). Every training target is his translators' real text from the shelf, so the project's rule holds (mind/train/README.md):
the model-written text is the INPUT only. At runtime the chat model writes plainly and the Hegelizer restyles it (world/restyle.py).

--build. A unit is UNIT_WORDS words: consecutive passages of one work merged until they are in the window, an overlong passage cut at sentence ends. A unit
is dropped if it shares a run of RUN words with one of the 20 passages ("passage" or "original") of mind/hegeltest/questions.json (the rule of
train_data.held_out(), whose shingles it uses), or if it still shows its scan (damaged(): the check that the writings' primer once used, with the
English word counts of the whole shelf as the yardstick). Of the rest, HELD_SHARE of each work is held out for the test, chosen by SPLIT_SEED.

--paraphrase. One llama-server chat call per unit without a plain version (thinking off, TEMPERATURE), asked with PARAPHRASE_SYSTEM and PARAPHRASE_ASK. The
reply stands if it is not empty, not cut off, in RATIO of the original's words, has no list marker or heading, and shares no run of RUN words with the
original (folded: lower case, punctuation gone). Otherwise it is asked once more at RETRY_TEMPERATURE, and then the unit is recorded as failed. The units
come in a fixed shuffled order, so that a run cut short still has every work in it. Rows are appended to hegelizer.jsonl one whole line at a time; a run
that is stopped (Ctrl-C, a crash, a server that stops answering) loses nothing, and the same command carries on. Failed units wait in hegelizer-failed.jsonl
and are tried again only with --retry-failed. A server that does not answer is no failure of a unit: nothing is recorded for it."""
import argparse
import json
import math
import os
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
from world import shelf  # noqa: E402

TRAIN = REPO / "mind/train"
UNITS, DONE, FAILED = "hegelizer-units.jsonl", "hegelizer.jsonl", "hegelizer-failed.jsonl"
BLIND = REPO / "mind/hegeltest/questions.json"
UNIT_WORDS = (150, 250)                         # a unit's length in words
HELD_SHARE, SPLIT_SEED = 0.05, 1831             # the share of each work held out for the test; the seed that chooses it
RUN = 8                                         # words in a row that two texts may not share (as train_data.HELD_OUT_RUN)
RATIO = (0.6, 1.4)                              # the plain version's words, as a share of the original's
TOKENS_PER_WORD = 1.6                           # for max_tokens: a word of English philosophy in tokens, rounded up
TEMPERATURE, RETRY_TEMPERATURE = 0.3, 0.7
PARAPHRASE_SYSTEM = "You rewrite passages of old philosophy in plain present-day English."
PARAPHRASE_ASK = ("Rewrite the passage below in plain, modern English, as a careful writer would today. Keep every claim, example and step of the argument, "
                  "in the same order. Add nothing, explain nothing, leave nothing out. Do not quote it. Use clear sentences and everyday words, about the "
                  "same length. Answer with the rewritten text only.\n\n{original}")
MARKUP = re.compile(r"^[ \t]*(?:[-*•+–]\s+\S|\d{1,3}[.)]\s+\S|#{1,6}\s|\*\*|>\s)", re.M)       # a list marker, a heading or bold at the start of a line
PREFACE_WORDS = 15                              # a first line this short that ends in a colon announces the text ("Here is the rewrite:") and is no text
TRIES, PATIENCE = 3, 15                         # a call the server does not answer is tried again this often, waiting PATIENCE seconds more each time
PROGRESS_EVERY = 25
GATE_FAILED, GATE_RATIO = 0.10, (0.8, 1.2)     # the runbook's gate before training: failed share of the units; mean word ratio plain / original

# The check that the writings' primer once made of the shelf's passages (world/works.py at 3c9bb7d), ported: a unit that still shows its scan would teach the
# adapter the scan's mistakes, and its plain version would be written from a text with holes.
SCAN_LITTER = re.compile(r"[a-z][A-Z]|\w' s\b|\w ' \w|[\\|■^~{}<>_]")       # a capital inside a word, a broken apostrophe, a stray sign
RARE, COMMON = 10, 2000         # a word the English books use fewer than RARE times, one letter from one they use COMMON times, is a misreading
MISREAD_RARE, MISREAD_COMMON = 50, 300      # and one used fewer than 50 times, a tenth as often as the word old type misreads it from
MISREAD = (("li", "h"), ("h", "li"), ("rn", "m"))        # old type misread: h as li and li as h ("tlie", "hke"), m as rn ("rnay")


def duration(seconds):
    m = int(seconds // 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


def read_rows(path, repair=False):
    """The rows of a jsonl file as dicts, [] if it is missing. A last line that a crash left half written is skipped, and with repair=True cut off the file,
    so that the next row starts on a line of its own."""
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raw = raw[:raw.rfind(b"\n") + 1]
        if repair:
            path.write_bytes(raw)
    rows = []
    for n, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                raise SystemExit(f"{path}:{n} is not JSON; move the file away or mend the line")
    return rows


def write_rows(path, rows):
    """rows as lines of JSON, written atomically; returns how many."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return len(rows)


def append_row(f, row):
    """One whole line, flushed to the disk: whatever stops the run later, the file holds only complete lines (and at most one half line from a crash in the write itself)."""
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    f.flush()
    os.fsync(f.fileno())


# ── the units ───────────────────────────────────────────────────────
def words_of(text):
    return len(text.split())


def fill(text, room):
    """(front, rest): the whole sentences at the front of text that fit in `room` words, and what is left."""
    ss, front, n = shelf.sentences(text), [], 0
    for i, s in enumerate(ss):
        if n + words_of(s) > room:
            return " ".join(front), " ".join(ss[i:])
        front.append(s)
        n += words_of(s)
    return " ".join(front), ""


def split_long(text, limit):
    """text in pieces of at most `limit` words, cut at sentence ends (a sentence longer than that stays whole)."""
    out = []
    while words_of(text) > limit:
        front, rest = fill(text, limit)
        if not front:
            ss = shelf.sentences(text)
            front, rest = ss[0], " ".join(ss[1:])
        out.append(front)
        text = rest
    return out + [text] if text.strip() else out


def work_units(passages, window=UNIT_WORDS):
    """([(ref, text)], lost): the units of one work from its passages [(ref, text)] in order. Consecutive passages are merged until the unit has `window[0]`
    words; if the next passage would take it past `window[1]`, the whole sentences at its front that fit are taken and the rest begins the next unit.
    A passage longer than the window is cut at sentence ends. The ref is that of the passage a unit begins in. `lost` counts the fragments that make no
    unit: the tail of the work, a short run before a sentence too long to fit, a single sentence longer than the window."""
    lo, hi = window
    out, buf, size, ref, lost = [], [], 0, "", 0
    for pref, text in passages:
        for piece in split_long(" ".join(text.split()), hi):
            if buf and size + words_of(piece) > hi:             # the buffer is short: it would have been closed at lo
                front, rest = fill(piece, hi - size)
                if front and size + words_of(front) >= lo:
                    out.append((ref, " ".join(buf + [front])))
                    buf, size, piece = [], 0, rest
                else:
                    buf, size, lost = [], 0, lost + 1
            if not piece:
                continue
            if not buf:
                ref = pref
            buf.append(piece)
            size += words_of(piece)
            if size >= lo:
                if size <= hi:
                    out.append((ref, " ".join(buf)))
                else:
                    lost += 1
                buf, size = [], 0
    return out, lost + bool(buf)


def english_counts(books):
    """{word: how often} over the English books on the shelf, counted once per shelf; empty for a shelf without its texts."""
    counts = getattr(books, "english_counts", None)
    if counts is None:
        from collections import Counter
        texts, counts = getattr(books, "data", {}).get("texts", []), Counter()
        for w in getattr(books, "works", []):
            if w["lang"] == "en":
                for text in texts[w["start"]:w["start"] + w["n"]]:
                    counts.update(re.findall(r"[a-z]{2,}", text.lower()))
        books.english_counts = counts
    return counts


def near(word):
    """The spellings one letter away from word: a letter dropped, changed or added."""
    abc = "abcdefghijklmnopqrstuvwxyz"
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


def written_out_shingles(text, n):
    """train_data.shingles, for where tools/train_data.py cannot be imported: the runs of n words (letters, digits, apostrophes, hyphens) of text, lower case."""
    w = re.findall(r"[\w'’-]+", (text or "").lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def blind_runs(questions=BLIND):
    """The RUN-word runs of the 20 passages of the Hegel test's blind part (the cleaned "passage" and the "original" as printed), by the rule of
    train_data.held_out(): its shingles, if tools/train_data.py can be imported, else the same rule written out here."""
    try:
        import train_data
        shingles, run = train_data.shingles, train_data.HELD_OUT_RUN
    except Exception:
        shingles, run = written_out_shingles, RUN
    runs = set()
    for q in json.loads(Path(questions).read_text(encoding="utf-8"))["questions"] if Path(questions).exists() else []:
        for text in (q.get("passage"), q.get("original")):
            runs |= shingles(text or "", run)
    return runs, shingles, run


def assign_split(units, seed=SPLIT_SEED, share=HELD_SHARE):
    """The units with "split" set to "train" or "held": share of each work (at least one, if the work has two units or more), a sample that the seed and the
    work decide, so that the same units always split the same way."""
    by_work = {}
    for u in units:
        by_work.setdefault(u["work"], []).append(u)
    held = set()
    for work, us in by_work.items():
        k = max(1, round(share * len(us))) if len(us) > 1 else 0
        held |= {us[i]["id"] for i in random.Random(f"{seed}|{work}").sample(range(len(us)), k)}
    return [{**u, "split": "held" if u["id"] in held else "train"} for u in units]


def build_units(books, seed=SPLIT_SEED, questions=BLIND):
    """(units, report): the units of every English work of the shelf, [{"id", "work", "ref", "original", "split"}], and per work how many were made and
    how many dropped for overlapping the blind passages ("overlap"), for a scan's damage ("damaged") or as fragments ("lost"). Ids are 'work:k' for the
    k-th unit made (before the drops), so they stay while the shelf does."""
    runs, shingles, run = blind_runs(questions)
    counts = english_counts(books)
    units, report = [], {}
    for w in books.works:
        if w["lang"] != "en":
            continue
        refs, texts = books.data["refs"][w["start"]:w["start"] + w["n"]], books.data["texts"][w["start"]:w["start"] + w["n"]]
        made, lost = work_units(list(zip(refs, texts)))
        rep = report[w["id"]] = {"made": len(made), "overlap": 0, "damaged": 0, "lost": lost}
        for k, (ref, text) in enumerate(made):
            if runs & shingles(text, run):
                rep["overlap"] += 1
            elif damaged(text, counts):
                rep["damaged"] += 1
            else:
                units.append({"id": f"{w['id']}:{k}", "work": w["id"], "ref": ref, "original": text})
    return assign_split(units, seed), report


def mismatched(units, rows):
    """How many of the finished rows are no longer the unit of their id (another shelf, another seed): they would train on a text that is not the unit's."""
    by_id = {u["id"]: u for u in units}
    return sum(1 for r in rows if r["id"] not in by_id or any(r.get(k) != by_id[r["id"]][k] for k in ("original", "split")))


def cmd_build(a, out):
    books = shelf.load()
    if not books:
        print("no shelf: mind/shelf/index.json.gz is missing", file=sys.stderr)
        return 1
    units, report = build_units(books, SPLIT_SEED if a.seed is None else a.seed)
    write_rows(out / UNITS, units)
    print(f"{out / UNITS}\n  {'work':15} {'units':>6} {'train':>6} {'held':>5} {'words':>8}   dropped: {'overlap':>7} {'damaged':>7} {'fragments':>9}")
    total = {"units": 0, "train": 0, "held": 0, "words": 0, "overlap": 0, "damaged": 0, "lost": 0}
    for work, rep in report.items():
        mine = [u for u in units if u["work"] == work]
        row = {"units": len(mine), "train": sum(u["split"] == "train" for u in mine), "held": sum(u["split"] == "held" for u in mine),
               "words": sum(words_of(u["original"]) for u in mine), **{k: rep[k] for k in ("overlap", "damaged", "lost")}}
        total = {k: total[k] + v for k, v in row.items()}
        print(f"  {work:15} {row['units']:6} {row['train']:6} {row['held']:5} {row['words']:8}   {'':8} {row['overlap']:7} {row['damaged']:7} {row['lost']:9}")
    print(f"  {'all':15} {total['units']:6} {total['train']:6} {total['held']:5} {total['words']:8}   {'':8} {total['overlap']:7} {total['damaged']:7} {total['lost']:9}")
    stale = mismatched(units, read_rows(out / DONE))
    if stale:
        print(f"WARNING: {stale} rows of {out / DONE} do not match these units (another shelf or seed?); --paraphrase will refuse them. Move that file away to start over.")
    return 0


# ── the paraphrase ──────────────────────────────────────────────────
class ServerError(Exception):
    """The llama-server did not answer (or not with a chat completion). No fault of the unit asked."""


def chat(url, messages, temperature, tokens, timeout):
    """(reply, finish_reason) of one chat call to a llama-server, thinking off. Raises ServerError."""
    payload = {"model": "local", "messages": messages, "temperature": temperature, "max_tokens": tokens, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            choice = json.loads(r.read().decode("utf-8"))["choices"][0]
        return (choice["message"].get("content") or ""), choice.get("finish_reason")
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as e:
        raise ServerError(f"{type(e).__name__}: {e}")


def folded_words(text):
    return re.findall(r"[a-z0-9]+", shelf.fold(text))


def runs_of(text, n=RUN):
    """The runs of n words in a row of text, folded (lower case, no punctuation, no diacritics), so that typography cannot hide a copy."""
    w = folded_words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def judge(original, reply, finish=None):
    """(plain, None) if the reply is a plain version of original that may stand, else (None, why not). The plain text is one paragraph, as the original is."""
    text = re.sub(r"<think>.*?</think>", "", reply or "", flags=re.S).strip()
    if not text:
        return None, "empty"
    if finish == "length":
        return None, "cut off at max_tokens"
    lines = [x for x in text.splitlines() if x.strip()]
    if MARKUP.search(text):
        return None, "list marker or heading"
    if len(lines) > 1 and lines[0].rstrip().endswith(":") and words_of(lines[0]) <= PREFACE_WORDS:
        return None, "a heading before the text"
    plain = " ".join(text.split())
    if len(plain) > 1 and plain[0] in "\"“" and plain[-1] in "\"”" and not re.search(r"[\"“”]", plain[1:-1]):
        plain = plain[1:-1].strip()
    ratio = words_of(plain) / max(1, words_of(original))
    if not RATIO[0] <= ratio <= RATIO[1]:
        return None, f"{ratio:.2f} times the original's words"
    if runs_of(plain) & runs_of(original):
        return None, f"shares {RUN} words in a row with the original"
    return plain, None


def paraphrase_one(unit, url, timeout):
    """(plain, None) or (None, why not) for one unit: asked at TEMPERATURE and, if the reply cannot stand, once more at RETRY_TEMPERATURE. A server that does
    not answer is tried TRIES times and then raises ServerError."""
    original = unit["original"]
    messages = [{"role": "system", "content": PARAPHRASE_SYSTEM}, {"role": "user", "content": PARAPHRASE_ASK.format(original=original)}]
    tokens, why = math.ceil(TOKENS_PER_WORD * RATIO[1] * words_of(original)), []
    for temperature in (TEMPERATURE, RETRY_TEMPERATURE):
        for k in range(TRIES):
            try:
                reply, finish = chat(url, messages, temperature, tokens, timeout)
                break
            except ServerError:
                if k == TRIES - 1:
                    raise
                time.sleep(PATIENCE * (k + 1))
        plain, problem = judge(original, reply, finish)
        if plain:
            return plain, None
        why.append(f"at {temperature}: {problem}")
    return None, "; ".join(why)


def failed_ids(rows, done):
    """The ids recorded as failed that have no plain version (yet)."""
    return {r["id"] for r in rows} - set(done)


def cmd_paraphrase(a, out):
    units = read_rows(out / UNITS)
    if not units:
        print(f"no units in {out / UNITS}: run --build first", file=sys.stderr)
        return 1
    rows = read_rows(out / DONE, repair=True)
    stale = mismatched(units, rows)
    if stale:
        print(f"{stale} rows of {out / DONE} do not match the units (another shelf or seed?): move that file away to start over", file=sys.stderr)
        return 1
    done = {r["id"] for r in rows}
    failed = failed_ids(read_rows(out / FAILED, repair=True), done)
    order = list(units)
    random.Random(SPLIT_SEED).shuffle(order)               # a fixed order: a run cut short still has every work in it
    todo = [u for u in order if u["id"] not in done and (a.retry_failed or u["id"] not in failed)]
    if a.limit:
        todo = todo[:a.limit]
    total, finished = len(units), len(done)
    print(f"{total} units, {len(done)} done, {len(failed)} failed" + ("" if a.retry_failed or not failed else " (skipped; --retry-failed tries them again)")
          + f", {len(todo)} to do with {a.workers} worker(s)", flush=True)
    if not todo:
        return 0
    try:
        urllib.request.urlopen(a.url.rstrip("/") + "/health", timeout=10).close()
    except urllib.error.HTTPError as e:
        print(f"warning: {a.url}/health answers {e.code}", file=sys.stderr)
    except (urllib.error.URLError, OSError) as e:
        print(f"no llama-server at {a.url}: {e}", file=sys.stderr)
        return 1
    t0, ok, bad, code, hold = time.time(), 0, 0, 0, False
    pool, pending, queue = ThreadPoolExecutor(max_workers=a.workers), {}, iter(todo)
    hard = True
    with open(out / DONE, "a", encoding="utf-8") as fd, open(out / FAILED, "a", encoding="utf-8") as ff:
        try:
            while True:
                while not hold and len(pending) < a.workers:
                    unit = next(queue, None)
                    if unit is None:
                        break
                    pending[pool.submit(paraphrase_one, unit, a.url, a.timeout)] = unit
                if not pending:
                    break
                try:
                    ready, _ = wait(pending, return_when=FIRST_COMPLETED)
                except KeyboardInterrupt:
                    if hold:
                        raise                               # the second time: the calls in flight are dropped
                    hold = True
                    code = 130
                    print(f"\ninterrupted: not starting more; finishing the {len(pending)} call(s) in flight (Ctrl-C again drops them). Run the same command to carry on.", flush=True)
                    continue
                for fut in ready:
                    unit = pending.pop(fut)
                    try:
                        plain, why = fut.result()
                    except ServerError as e:
                        if code != 1:
                            print(f"\nthe server stopped answering ({e}); nothing is recorded for the unit it failed on. Run the same command to carry on.", flush=True)
                        hold, code = True, code or 1
                        continue
                    if plain:
                        append_row(fd, {"id": unit["id"], "work": unit["work"], "ref": unit["ref"], "split": unit["split"], "plain": plain, "original": unit["original"]})
                        ok += 1
                    else:
                        append_row(ff, {"id": unit["id"], "work": unit["work"], "reason": why})
                        bad += 1
                    if (ok + bad) % PROGRESS_EVERY == 0:
                        each = (time.time() - t0) / (ok + bad)
                        print(f"{finished + ok}/{total} done, {bad} failed in this run; {each:.1f} s per unit; {duration(each * (len(todo) - ok - bad))} to go", flush=True)
            hard = False
        finally:
            pool.shutdown(wait=not hard, cancel_futures=True)
    print(f"{finished + ok}/{total} done; this run: {ok} written, {bad} failed, {duration(time.time() - t0)}", flush=True)
    return code


# ── the stats ───────────────────────────────────────────────────────
def cmd_stats(a, out):
    units = read_rows(out / UNITS)
    if not units:
        print(f"no units in {out / UNITS}: run --build first", file=sys.stderr)
        return 1
    rows = {r["id"]: r for r in read_rows(out / DONE)}
    failures = {r["id"]: r for r in read_rows(out / FAILED)}
    failed = failed_ids(failures.values(), rows) & {u["id"] for u in units}
    by_split = lambda f: ", ".join(f"{s} {sum(1 for u in units if u['split'] == s and f(u))}" for s in ("train", "held"))
    print(f"{out}\n  units {len(units)} ({by_split(lambda u: True)}); done {len(rows)} ({by_split(lambda u: u['id'] in rows)}); "
          f"failed {len(failed)} ({by_split(lambda u: u['id'] in failed)}); to do {len(units) - len(rows) - len(failed)}")
    print(f"  {'work':15} {'units':>6} {'train':>6} {'held':>5} {'done':>6} {'failed':>6}")
    for work in sorted({u["work"] for u in units}):
        mine = [u for u in units if u["work"] == work]
        print(f"  {work:15} {len(mine):6} {sum(u['split'] == 'train' for u in mine):6} {sum(u['split'] == 'held' for u in mine):5} "
              f"{sum(u['id'] in rows for u in mine):6} {sum(u['id'] in failed for u in mine):6}")
    ratios = [words_of(r["plain"]) / max(1, words_of(r["original"])) for r in rows.values()]
    share = len(failed) / len(units)
    if ratios:
        mean = statistics.mean(ratios)
        print(f"  words of the plain version / the original: mean {mean:.2f} (min {min(ratios):.2f}, max {max(ratios):.2f}) over {len(ratios)} units")
        gate = share < GATE_FAILED and GATE_RATIO[0] <= mean <= GATE_RATIO[1]
        print(f"  gate (failed under {GATE_FAILED:.0%} of the units, mean ratio {GATE_RATIO[0]} to {GATE_RATIO[1]}): failed {share:.1%}, ratio {mean:.2f}: " + ("passes" if gate else "STOP, report"))
    if failed:
        print("  failures:")
        for i in sorted(failed)[:3]:
            print(f"    {i}: {failures[i]['reason']}")
    rng = random.Random(1 if a.seed is None else a.seed)
    train = [r for r in rows.values() if r["split"] == "train"]
    for r in rng.sample(train, min(3, len(train))):
        print(f"\n[{r['id']}] {r['work']} {r['ref']}\n  plain:    {r['plain']}\n  original: {r['original']}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--build", action="store_true", help="write hegelizer-units.jsonl from the English books of the shelf")
    p.add_argument("--paraphrase", action="store_true", help="write a plain version of every unit that has none, through a llama-server")
    p.add_argument("--stats", action="store_true", help="units, done, failed, the mean word ratio and three samples")
    p.add_argument("--url", help="with --paraphrase: the llama-server of plain Qwen, e.g. http://127.0.0.1:8082")
    p.add_argument("--workers", type=int, default=1, help="with --paraphrase: calls in parallel (the server needs --parallel N; default 1)")
    p.add_argument("--limit", type=int, help="with --paraphrase: only this many units in this run (to try it)")
    p.add_argument("--retry-failed", action="store_true", help="with --paraphrase: ask the units that failed before again")
    p.add_argument("--timeout", type=int, default=300, help="with --paraphrase: seconds to wait for one answer")
    p.add_argument("--seed", type=int, help=f"with --build: the seed of the split (default {SPLIT_SEED}); with --stats: which samples (default 1)")
    p.add_argument("--out", help=f"the folder of the data (default {TRAIN.relative_to(REPO)})")
    a = p.parse_args(argv)
    out = Path(a.out) if a.out else TRAIN
    if not (a.build or a.paraphrase or a.stats):
        p.error("say what to do: --build, --paraphrase or --stats")
    if a.paraphrase and not a.url:
        p.error("--paraphrase needs --url")
    if a.workers < 1:
        p.error("--workers must be at least 1")
    code = 0
    try:
        if a.build:
            code = cmd_build(a, out) or code
        if a.paraphrase:
            code = cmd_paraphrase(a, out) or code
        if a.stats:
            code = cmd_stats(a, out) or code
    except KeyboardInterrupt:
        print("\nstopped; the files hold whole lines only.", flush=True)
        os._exit(130)
    return code


if __name__ == "__main__":
    sys.exit(main())
