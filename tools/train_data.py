#!/usr/bin/env python3
"""Hegel in Delhi: the training data for a Hegel LoRA. Standard library only, Python 3.9 and later; runs on the PC under WSL2 or on the Pi.

    python3 tools/train_data.py --corpus                      # mind/train/corpus.jsonl: his books, his papers and his lives as continued-pretraining text
    python3 tools/train_data.py --general 1000                # mind/train/general.jsonl: human-written instruction data, for balance
    python3 tools/train_data.py --distill --url http://127.0.0.1:8080 --days 20 --candidates 4 --start 2026-10-03
    python3 tools/train_data.py --stats                       # counts, token estimates and a few random samples to read
    python3 tools/train_data.py --serve-stub 8099             # a stand-in llama-server, to try --distill without the PC

The hard rule: no target in this data is written by Claude. Anthropic's terms bar training other models on Claude's output, so every assistant
turn comes from one of two places, and the code has no third: Hegel's own public-domain texts (`--corpus`), or Qwen itself (`--distill`, the
mind that the world already talks to). `--general` is the exception that the brief asks for: human-written answers of a public dataset, taken
only from subsets that no language model generated (see GENERAL_SOURCES and mind/train/README.md). Prompts are the project's own files:
the soul, the situations the world renders, the voices' card.

Distillation, in short. The world rehearses days with the real mind (the machinery of `python3 -m world simulate`: no git, feeds off). At each
decision the mind is asked K times at temperature 0.9 with the live schema. The world checks every candidate (World.check: the rules, the
1831 gate, the repetition guard); those it accepts are scored by a plain heuristic, and the best becomes the step's decision, the next
situation grows from it, and the example {system = soul, user = the rendered situation, assistant = the chosen JSON} is appended to
decisions.jsonl. The plan, the writing and the voices' answers that the world accepts are kept in plans.jsonl, writings.jsonl and voices.jsonl.

The heuristic (score, higher is better; every candidate that reaches it is already valid):
    + length      2.0 for a thought of 25 to 90 words, less by one point per 20 words outside
    + event       0.5 per content word (stemmed, as the shelf search does) shared with what happens, who is present, what is for sale and
                  where he is, up to 3.0
    + shelf       0.5 per content word shared with the passages under "From your shelf", up to 3.0 (nothing when none were offered)
    + names       0.5 per proper name of the situation that the thought uses, up to 1.5
    - generic     0.75 per stock phrase ("tapestry", "a reminder that", "the cunning of reason" ...), up to 3.0
    - copied      2.0 if the thought repeats five words in a row of the soul's example thoughts (the soul says not to)
    - opening     1.5 if its first three words open a thought already chosen today, 0.5 if its first word opens one of the last three
    - warnings    0.5 per warning of the world's check
Ties go to the first candidate. A step with no valid candidate hands the world the one with the fewest errors, which makes the world refuse it
and ask again (as it does live); nothing is written for it.

Resuming: the rehearsal lives in mind/train/rehearsal/ (the day files are its state) and every example is appended with its step key. A crash,
Ctrl-C or a PC that stops answering ends the run without losing a step; run the same command again and it carries on from the last saved step,
replaying a recorded step's answer instead of asking again. Time on the PC: a decision costs K calls for the candidates and, on average, about
one more for the voices, the plan (once a day), the writings and the owl at night; (K + 3) calls is the figure to plan with, and each call is a few
seconds on a 3090 (the prompt is cached across the K), so 20 days of about 26 decisions at K = 4 is roughly 4 to 7 hours."""
import argparse
import collections
import hashlib
import json
import os
import random
import re
import statistics
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
from world import contract, shelf, works  # noqa: E402
from world.mind import HTTPMind, MindAway, StubMind  # noqa: E402
from world.world import World  # noqa: E402

TRAIN = REPO / "mind/train"
FILES = {"decision": "decisions.jsonl", "plan": "plans.jsonl", "write": "writings.jsonl", "voice": "voices.jsonl"}
LABEL = {"decision": "decisions", "plan": "plans", "write": "writings", "voice": "voices"}
DOC_CHARS, HEAD_ROOM, MIN_DOC = 6000, 200, 300         # a corpus document: at most this long, room kept for its header, none shorter than MIN_DOC
SAMPLING_TEMPERATURE = 0.9                             # of the K candidates at each decision
TRIES, PATIENCE = 3, 15                                # a call that fails is tried again this often, waiting PATIENCE seconds more each time
DAY_ONE = "2026-10-03"                                 # the first day that can be rehearsed: day 1 is the hand-written prologue
STAND_IN = ("(rehearsal)", "(stub)")                   # what a stand-in mind writes into its answers; never training data


def tokens_of(chars):
    """The token estimate used everywhere in this tool: characters / 4 (German runs nearer 3 characters per token)."""
    return chars // 4


def write_jsonl(path, rows):
    """Write rows (dicts) as lines of JSON, atomically; returns how many."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    n = 0
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, path)
    return n


def read_jsonl(path, repair=False):
    """The rows of a jsonl file, [] if it is missing. With repair=True a last line that a crash left half written is cut off the file."""
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    if repair and raw and not raw.endswith(b"\n"):
        raw = raw[:raw.rfind(b"\n") + 1]
        path.write_bytes(raw)
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def duration(seconds):
    m = int(seconds // 60)
    return f"{m // 60} h {m % 60:02d} min" if m >= 60 else f"{m} min"


# ── the corpus: his books ───────────────────────────────────────────
TITLE_NOISE = re.compile(r"\s*\([^)]*\)|,\s*(?:with|as far as)\b.*$|,\s*§§.*$")


def work_title(w):
    """The title of a work for a header: the manifest's title without its parentheses, section range and notes on the edition."""
    return TITLE_NOISE.sub("", w["title"]).strip()


def header(w, first, last):
    """'Hegel, Grundlinien der Philosophie des Rechts, §188' for a German text; an English one adds the translator and the year:
    'Hegel's Philosophy of Right, tr. S. W. Dyde (1896), §188 ff.'; a life of him names its author and year: 'Karl Rosenkranz, Georg
    Wilhelm Friedrich Hegel's Leben (1844), Jena'. `first` and `last` are the refs of the document's first and last passage."""
    title = work_title(w)
    if w.get("author", "Hegel") != "Hegel":
        year = re.match(r"\d{4}", w["year"])
        line = f"{w['author']}, {title}" + (f" ({year.group(0)})" if year else "")
    else:
        line = title if title.startswith("Hegel") else f"Hegel, {title}"
    if w["who"].startswith("tr. "):
        year = re.match(r"\d{4}", w["year"])
        line += f", {w['who']}" + (f" ({year.group(0)})" if year else "")
    if first.startswith("§"):
        line += f", {first}" + (" ff." if last != first else "")
    elif first:
        line += f", {first}"
    return line[:HEAD_ROOM - 2]


def documents(kept, meta, limit=DOC_CHARS):
    """[(work id, language, text)]: each work's kept passages, in order, in documents of at most `limit` characters, each under a
    header line. A passage is never cut; a tail shorter than MIN_DOC is dropped. `kept` is corpus.kept_works(), `meta` the manifest by id."""
    out = []
    for w in kept:
        m, run, size = meta[w["id"]], [], 0

        def flush():
            nonlocal run, size
            if run and size >= MIN_DOC:
                text = header(m, run[0][0], run[-1][0]) + "\n\n" + "\n\n".join(t for _, t in run)
                out.append((w["id"], w["lang"], text))
            run, size = [], 0

        for ref, text in w["passages"]:
            if run and size + 2 + len(text) > limit - HEAD_ROOM:
                flush()
            run.append((ref, text))
            size += len(text) + (2 if len(run) > 1 else 0)
        flush()
    return out


BLIND = REPO / "mind/hegeltest/questions.json"
HELD_OUT_RUN = 8                                       # a passage that shares a run of this many words with a blind passage of the Hegel test stays out


def held_out(kept, questions=BLIND):
    """(kept, n): the works' passages without those that overlap the twenty real passages of the Hegel test's blind part, so that the trained
    mind cannot have learnt the answers by heart; n is how many were dropped."""
    runs = set()
    for q in json.loads(Path(questions).read_text(encoding="utf-8"))["questions"] if Path(questions).exists() else []:
        for text in (q.get("passage"), q.get("original")):
            runs |= shingles(text or "", HELD_OUT_RUN)
    dropped, out = 0, []
    for w in kept:
        passages = [(ref, t) for ref, t in w["passages"] if not runs & shingles(t, HELD_OUT_RUN)]
        dropped += len(w["passages"]) - len(passages)
        out.append({**w, "passages": passages})
    return out, dropped


def subsample(docs, max_chars):
    """About max_chars characters of the documents, every k-th one, so that every work stays in the same proportion."""
    total = sum(len(t) for _, _, t in docs)
    if total <= max_chars:
        return docs
    n = max(1, round(len(docs) * max_chars / total))
    return [docs[i * len(docs) // n] for i in range(n)]


def cmd_corpus(a, out):
    import corpus                                       # tools/corpus.py: the damaged-passage filter lives there
    t0 = time.time()
    kept = corpus.kept_works()                          # the passages of the shelf's index and of the lives: mended, no damaged scan, nothing after 1831
    kept, blind = held_out(kept)
    docs = documents(kept, {w["id"]: w for w in corpus.WORKS})
    if a.max_chars:
        docs = subsample(docs, a.max_chars)
    n = write_jsonl(out / "corpus.jsonl", ({"text": t} for _, _, t in docs))
    by_work = collections.OrderedDict()
    for wid, lang, text in docs:
        by_work.setdefault(wid, [lang, 0, 0])
        by_work[wid][1] += 1
        by_work[wid][2] += len(text)
    for wid, (lang, count, chars) in by_work.items():
        print(f"  {wid:15} {lang}  {count:4} documents  {chars / 1e6:5.2f} M characters")
    chars = sum(len(t) for _, _, t in docs)
    langs = {lang: sum(len(t) for _, g, t in docs if g == lang) for lang in ("de", "en")}
    print(f"wrote {out / 'corpus.jsonl'}: {n} documents, {chars / 1e6:.2f} M characters (German {langs['de'] / 1e6:.2f}, English {langs['en'] / 1e6:.2f}), "
          f"longest {max(len(t) for _, _, t in docs)}; about {tokens_of(chars) / 1e6:.2f} M tokens (characters / 4) in {time.time() - t0:.0f} s; "
          f"{blind} passages left out because they overlap the Hegel test's blind passages")
    return 0


# ── general instruction data: for balance ───────────────────────────
# The Tulu 3 SFT mixture (allenai/tulu-3-sft-mixture, ODC-BY-1.0) is 18 sets. Only those whose answers people wrote are used: OpenAssistant
# (oasst1, Apache 2.0, volunteers) and Aya (Apache 2.0, annotators). The rest were generated by language models (GPT-4, GPT-4o and others,
# the personas sets among them) or are non-commercial (No Robots), and none of them goes into a model trained here. FLAN is human-sourced but
# its answers are one-word task labels, which teach nothing about conversation.
GENERAL_DATASET = "allenai/tulu-3-sft-mixture"
GENERAL_API = "https://datasets-server.huggingface.co"
GENERAL_SOURCES = ("oasst1", "aya")                    # substrings of the `source` field of a row
GENERAL_LICENSE = "ODC-BY-1.0 (the mixture); Apache-2.0 (the OpenAssistant and Aya subsets)"
PAGE = 100                                             # rows per request: the API's maximum
STOPWORDS = frozenset("the of and to in is that it for you with as on are this be or have was not at by from but an they we can will my your "
                      "what which there their one all would i a if so do about how".split())


class GeneralError(Exception):
    pass


def fetch_json(url, tries=6, sleep=None):
    """JSON from the datasets server, tried again on the errors that pass: a dropped connection or a 5xx after a short pause, a 429 (too many
    requests) after the pause the server asks for in Retry-After, or else 30, 60, 90 ... seconds. A Hugging Face token in HF_TOKEN raises the
    server's limits."""
    sleep, last, headers = sleep or time.sleep, None, {"User-Agent": "hegel-in-delhi-train-data/1.0"}
    if os.environ.get("HF_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['HF_TOKEN']}"
    for attempt in range(1, tries + 1):
        wait = 2 * attempt
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 429:
                after = (e.headers or {}).get("Retry-After", "")
                wait = min(600, int(after)) if after.isdigit() else 30 * attempt
            e.close()
            if e.code not in (429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, OSError, ValueError) as e:
            last = str(e)
        if attempt < tries:
            sleep(wait)
    raise GeneralError(f"{url}: {last}")


def is_english(text):
    """Plain ASCII-heavy text in which at least three words in ten are common English words."""
    words = [w.lower() for w in re.findall(r"[A-Za-z']+", text)[:200]]
    return len(words) >= 15 and sum(ord(c) > 127 for c in text) <= 0.02 * len(text) and sum(w in STOPWORDS for w in words) / len(words) >= 0.30


def usable(row, sources=GENERAL_SOURCES):
    """The chat of a dataset row if it is fit for the general set, else None: from an allowed source, English, at most three exchanges that
    start with the user and end with the assistant, no system turn, 3,000 characters at the most."""
    msgs = row.get("messages")
    if not any(s in str(row.get("source", "")) for s in sources) or not isinstance(msgs, list) or not 2 <= len(msgs) <= 6 or len(msgs) % 2:
        return None
    if any(not isinstance(m, dict) or m.get("role") != ("user", "assistant")[i % 2] or not isinstance(m.get("content"), str) or not m["content"].strip()
           for i, m in enumerate(msgs)):
        return None
    text = " ".join(m["content"] for m in msgs)
    if len(text) > 3000 or len(msgs[-1]["content"].strip()) < 40 or not is_english(text):
        return None
    return [{"role": m["role"], "content": m["content"].strip()} for m in msgs]


def fetch_general(n, base=GENERAL_API, dataset=GENERAL_DATASET, sources=GENERAL_SOURCES, seed=1831, sleep=None, say=print, skip=(), pace=1.0):
    """n examples of the general set: [{"messages": [...], "meta": {...}}], fewer if the dataset runs out. The rows API is read in pages of 100.
    The mixture is stored in blocks, one subset after the other, so the first step is to probe the size and a row every `stride` rows to find where
    the allowed subsets lie (a block narrower than the stride can be missed); then random pages inside those stretches are read, round-robin over the
    sources so that each gives an equal share, until n examples are in or the pages given for the search are used up. Rows whose ids are in `skip`
    (a top-up) are passed over; `pace` seconds pass between pages. If the server stops answering once some examples are in, those are returned."""
    sleep = sleep or time.sleep
    q = urllib.parse.urlencode({"dataset": dataset, "config": "default", "split": "train"})
    rows_url = f"{base}/rows?{q}&offset={{}}&length={{}}"
    total = fetch_json(rows_url.format(0, 1), sleep=sleep).get("num_rows_total") or 0
    if not total:
        raise GeneralError("the dataset reports no rows")
    stride = max(PAGE, total // 48)
    stretches = collections.OrderedDict((s, []) for s in sources)
    for off in range(0, total, stride):
        got = fetch_json(rows_url.format(off, 1), sleep=sleep)["rows"]
        src = str(got[0]["row"].get("source", "")) if got else ""
        for s in sources:
            if s in src:
                stretches[s].append((max(0, off - stride), min(total, off + stride)))
    found = {s: v for s, v in stretches.items() if v}
    say(f"dataset {dataset}: {total} rows; stretches with allowed sources: " + (", ".join(f"{s} {len(v)}" for s, v in found.items()) or "none"))
    if not found:
        raise GeneralError(f"none of the sources {sources} was found in {dataset}")
    rng, seen, tried, out = random.Random(seed + len(skip)), set(skip), set(), collections.OrderedDict((s, []) for s in found)
    budget = 25 + n // 4                                             # rounds of one page per source
    for spent in range(budget):
        if sum(map(len, out.values())) >= n:
            break
        share = -(-n // len(found)) if spent < budget // 2 else n     # an equal share each at first, then whoever still has rows
        for s in found:
            lo, hi = rng.choice(found[s])
            off = rng.randrange(lo, hi - PAGE + 1) if hi - lo > PAGE else lo
            if len(out[s]) >= share or off in tried:
                continue
            tried.add(off)
            sleep(pace)
            try:
                page = fetch_json(rows_url.format(off, PAGE), sleep=sleep)["rows"]
            except GeneralError as e:
                if not any(out.values()):
                    raise
                say(f"  the server stopped answering ({e}); keeping {sum(map(len, out.values()))}. Run the same command again later to top up.")
                return [x for v in out.values() for x in v][:n]
            for item in page:
                row = item["row"]
                chat = usable(row, (s,))
                if chat and row["id"] not in seen and len(out[s]) < share and sum(map(len, out.values())) < n:
                    seen.add(row["id"])
                    out[s].append({"messages": chat, "meta": {"kind": "general", "source": dataset, "subset": row["source"], "id": row["id"],
                                                             "license": GENERAL_LICENSE}})
        say(f"  {sum(map(len, out.values()))}/{n}  " + "  ".join(f"{s} {len(v)}" for s, v in out.items()))
    return [x for v in out.values() for x in v][:n]


def answer_with(rows, url, say=print):
    """Optional (--answer-with): keep each example's first question and let Qwen write the answer, so that no assistant turn of the training data
    comes from anyone but Qwen and Hegel. Answers that stop short of a full stop are dropped. One call per example."""
    mind = HTTPMind(url, timeout=300)
    out = []
    for i, row in enumerate(rows, 1):
        ask = row["messages"][0]
        try:
            reply = mind.chat([ask], max_tokens=900, temperature=0.7)
        except MindAway as e:
            raise GeneralError(f"the mind stopped answering: {e}")
        if reply and reply[-1] in ".!?)\"”'`*" and len(reply) <= 3000:
            out.append({"messages": [ask, {"role": "assistant", "content": reply}], "meta": {**row["meta"], "answered_by": "qwen", "answer_url": url}})
        if i % 25 == 0:
            say(f"  answered {i}/{len(rows)}, kept {len(out)}")
    return out


def cmd_general(a, out):
    if a.answer_with and health(a.answer_with).get("stub"):
        print("that server is a stand-in: its answers are not training data", file=sys.stderr)
        return 1
    have = read_jsonl(out / "general.jsonl", repair=True)            # an earlier run, cut short by the server: top it up
    if len(have) >= a.general:
        print(f"{out / 'general.jsonl'} already has {len(have)} examples")
        return 0
    try:
        rows = fetch_general(a.general - len(have), base=a.general_url, skip={r["meta"]["id"] for r in have})
        if rows and a.answer_with:
            rows = answer_with(rows, a.answer_with)
    except GeneralError as e:
        print(f"cannot make the general set: {e}" + (f"; {len(have)} examples from before are kept" if have else ""), file=sys.stderr)
        return 1
    if not rows and not have:
        print("no usable examples found", file=sys.stderr)
        return 1
    random.Random(1831).shuffle(rows)
    rows = have + rows
    write_jsonl(out / "general.jsonl", rows)
    chars = sum(len(m["content"]) for r in rows for m in r["messages"])
    print(f"wrote {out / 'general.jsonl'}: {len(rows)} of {a.general} examples, {chars / 1e6:.2f} M characters, about {tokens_of(chars) / 1e6:.2f} M tokens; "
          f"prompts and " + ("answers by Qwen" if a.answer_with else "answers (human-written)") + f" from {GENERAL_DATASET}, license {GENERAL_LICENSE}")
    if len(rows) < a.general:
        print(f"only {len(rows)} of {a.general} so far: run the same command again later to top up (with HF_TOKEN set, the server allows more)", file=sys.stderr)
    return 0


# ── distillation: Qwen's own decisions, chosen by the world ─────────
class DistillAbort(Exception):
    """The mind stopped answering. The run ends cleanly; the same command picks up where it was."""


GENERIC = ("tapestry", "testament to", "interplay", "dance between", "a reminder that", "reminds me that", "reminder of", "delve", "profound",
           "in the grand scheme", "at the end of the day", "the human condition", "fascinating", "intriguing", "speaks volumes", "a journey",
           "in essence", "ultimately", "once again", "serves as", "stands as", "the cunning of reason", "owl of minerva", "unity of opposites",
           "thesis and antithesis", "thesis, antithesis")
MIN_WORDS, MAX_WORDS, SHINGLE = 25, 90, 5


def words(text):
    return re.findall(r"[\w'’-]+", (text or "").lower())


def shingles(text, n=SHINGLE):
    w = words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def soul_shingles(soul):
    """The five-word runs of the example thoughts in the soul's 'How you sound' list."""
    out = set()
    for quote in re.findall(r"^- [“\"](.+?)[”\"]\s*$", soul, re.M):
        out |= shingles(quote)
    return out


def stems(text):
    return set(shelf.tokens(text, shelf.IGNORE))


def capitals(text):
    """Every capitalised word of text, lower-cased: in a list of names (who is present, where he is) each one is a name."""
    return {w.lower() for w in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text or "")}


def names_in(text):
    """The capitalised words of running text that do not just open a sentence: names of people, places and things."""
    return set().union(*(capitals(sentence.partition(" ")[2]) for sentence in re.split(r"(?<=[.!?:;])\s+", text or "")))


def score(ans, sit, place_name, warnings, earlier, soul):
    """(total, parts): how much this valid decision is worth as a training example. See the heuristic in the module's docstring.
    `earlier` are the thoughts already chosen today (oldest first); `soul` is the set of five-word runs of its examples (soul_shingles)."""
    thought = ans["thought"].strip()
    n = len(thought.split())
    mine = stems(thought)
    seen = " ".join([sit["event"], " ".join(sit["present"]), " ".join(sit.get("for_sale") or []), place_name])
    parts = {
        "length": 2.0 - min(2.0, (MIN_WORDS - n if n < MIN_WORDS else max(0, n - MAX_WORDS)) / 20),
        "event": 0.5 * min(6, len(mine & stems(seen))),
        "shelf": 0.5 * min(6, len(mine & stems(" ".join(x["text"] for x in sit.get("shelf") or [])))),
        "names": 0.5 * min(3, len((names_in(sit["event"]) | capitals(" ".join(sit["present"]) + " " + place_name)) & set(words(thought)))),
        "generic": -min(3.0, 0.75 * sum(p in thought.lower() for p in GENERIC)),
        "copied": -2.0 if soul & shingles(thought) else 0.0,
        "warnings": -0.5 * len(warnings),
    }
    w = words(thought)
    opening = [tuple(words(x)[:3]) for x in earlier]
    parts["opening"] = (-1.5 if tuple(w[:3]) in opening else 0.0) + (-0.5 if w and w[0] in {o[0] for o in opening[-3:] if o} else 0.0)
    return round(sum(parts.values()), 2), {k: round(v, 2) for k, v in parts.items()}


def canonical(raw, ans):
    """The assistant turn to train on: the model's own text when it is bare JSON, else the same object written out again (a fence or a
    think block of the reply stripped)."""
    text = (raw or "").strip()
    return text if text.startswith("{") and text.endswith("}") else json.dumps(ans, ensure_ascii=False)


class Sink:
    """The example files of a distillation, appended as they come, and what a run needs to know of them: every recorded answer by step key
    (a resumed run replays these instead of asking again), the decisions of each day, and the thoughts chosen on each day."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.done = {kind: {} for kind in FILES}
        self.per_day = collections.Counter()
        self.thoughts = collections.defaultdict(list)
        for kind, name in FILES.items():
            for row in read_jsonl(self.folder / name, repair=True):
                self.done[kind][row["meta"]["key"]] = row["messages"][-1]["content"]
                if kind == "decision":
                    self.per_day[row["meta"]["day"]] += 1
                    self.thoughts[row["meta"]["day"]].append(json.loads(row["messages"][-1]["content"])["thought"])

    def add(self, kind, key, messages, answer, **meta):
        row = {"messages": list(messages) + [{"role": "assistant", "content": answer}], "meta": {"kind": kind, "key": key, **meta}}
        with open(self.folder / FILES[kind], "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
        self.done[kind][key] = answer
        if kind == "decision":
            self.per_day[meta["day"]] += 1
            self.thoughts[meta["day"]].append(json.loads(answer)["thought"])


class RecordingWorld(World):
    """The world, remembering the situation it built last (with its context and the state), so that the mind can check its candidates against
    the very state the engine is about to check the chosen one against."""
    current = None

    def situation(self, t, state, day, prev_step=None):
        sit, ctx = super().situation(t, state, day, prev_step)
        self.current = (sit, ctx, state)
        return sit, ctx


class DistillMind(HTTPMind):
    """The mind of a distillation: Qwen on the PC, asked K times for each decision. The world calls decide() and chat() as it does with any
    mind; this one picks the best valid candidate, records what the world accepts, and replays what an earlier run recorded."""
    source = "mind"
    pause = staticmethod(time.sleep)

    def __init__(self, url, sink, soul, k=4, workers=1, timeout=300, start=None, days=1):
        super().__init__(url, wake=None, timeout=timeout)
        self.sink, self.k, self.workers, self.soul = sink, k, workers, soul_shingles(soul)
        self.world = None                 # the RecordingWorld whose situation() says which step this is; set by the caller
        self.start, self.days = start or date.fromisoformat(DAY_ONE), days
        self.t0, self.new, self.replayed, self.stuck = time.time(), 0, 0, 0
        self.recorded = collections.Counter()           # examples written in this run, by kind
        self.nth = collections.Counter()                # voice calls so far in a step: (step, kind) -> n

    def ask(self, messages, schema=None, max_tokens=700, temperature=None):
        """One call, tried again a few times; after that the run stops (DistillAbort) rather than let the world record a quiet step."""
        for attempt in range(1, TRIES + 1):
            try:
                return HTTPMind.chat(self, messages, schema, max_tokens, temperature)
            except MindAway as e:
                last = e
                if attempt < TRIES:
                    self.pause(PATIENCE * attempt)
        raise DistillAbort(f"the mind stopped answering ({last}); run the same command again to carry on")

    def sample(self, messages):
        """K answers to the live decision prompt, at temperature 0.9."""
        one = lambda _: self.ask(messages, contract.SCHEMA, 700, SAMPLING_TEMPERATURE)
        if self.workers > 1:
            with ThreadPoolExecutor(self.workers) as pool:
                return list(pool.map(one, range(self.k)))
        return [one(i) for i in range(self.k)]

    def decide(self, messages, sit):
        key = sit["id"]
        if key in self.sink.done["decision"]:                       # a step of an earlier run: the same answer, no call
            self.replayed += 1
            return self.sink.done["decision"][key]
        _, ctx, state = self.world.current
        place, day = self.world.places[sit["place"]]["name"], key[:10]
        valid, refused, seen = [], [], set()
        for raw in self.sample(messages):
            ans = contract.extract_json(raw)
            errors, warnings, _ = self.world.check(ans, sit, ctx, state)
            if errors:
                refused.append((len(errors), raw))
            elif ans["thought"].strip() not in seen:
                seen.add(ans["thought"].strip())
                valid.append((score(ans, sit, place, warnings, self.sink.thoughts[day], self.soul), canonical(raw, ans)))
        if not valid:
            self.stuck += 1
            self.report(sit, 0, None)
            return min(refused, key=lambda x: x[0])[1]                  # the world refuses it and asks again, as it does live
        (total, parts), answer = max(valid, key=lambda x: x[0][0])        # a tie goes to the first
        attempt = (len(messages) - 2) // 2 + 1                             # 1, or the try after the world's refusals
        self.sink.add("decision", key, messages[:2], answer, day=day, t=sit["time"], candidates=self.k, valid=len(valid), score=total, parts=parts, attempt=attempt)
        self.report(sit, len(valid), total)
        return answer

    def report(self, sit, valid, total):
        """The progress line: where the rehearsal is, how this decision went, and when it will be done."""
        self.new += 1
        day = sit["id"][:10]
        n = min(self.days, (date.fromisoformat(day) - self.start).days + 1)           # (the engine also decides the first step of the next day)
        finished = [c for d, c in self.sink.per_day.items() if d < day]
        left = max(0.0, (statistics.mean(finished) if finished else 26) * (self.days - n + 1) - self.sink.per_day[day])
        eta = left * (time.time() - self.t0) / self.new
        extra = "".join(f", {self.recorded[k]} {LABEL[k]}" for k in ("plan", "voice", "write") if self.recorded[k])
        best = f"best {total:+.2f}" if total is not None else "none valid, the world will refuse"
        print(f"day {n}/{self.days} {day} {sit['time']}  {valid}/{self.k} valid, {best}  | {sum(self.sink.per_day.values())} decisions"
              + (f" ({self.replayed} replayed)" if self.replayed else "") + f"{extra}  | ETA {duration(eta)} for about {left:.0f} more", flush=True)

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        """The plan, the voices and the writings: one call each, kept when the world would take the answer. Any other call (the owl, a yes or
        no) passes through."""
        props = (schema or {}).get("properties", {})
        kind = "plan" if "plan" in props else "voice" if "does" in props else "write" if "continues" in props else None
        if kind is None or self.world.current is None:
            return self.ask(messages, schema, max_tokens, temperature)
        sit, ctx, _ = self.world.current
        self.nth[(sit["id"], kind)] += 1
        key = f"{sit['id']}|{kind}" + (f"|{self.nth[(sit['id'], kind)]}" if kind == "voice" else "")      # a step may hear two voices
        if key in self.sink.done[kind]:
            return self.sink.done[kind][key]
        raw = self.ask(messages, schema, max_tokens, temperature)
        out = contract.extract_json(raw)
        if self.accepted(kind, out, ctx):
            if kind == "write":                 # system, the situation, the decision it carries on from, the ask: an earlier refused writing is left out
                i = next(i for i, m in enumerate(messages) if m["role"] == "user" and m["content"].startswith(contract.WRITE_ASK[:40]))
                base = [messages[0], messages[1], messages[i - 1], messages[i]]
            else:
                base = messages[:2]
            self.sink.add(kind, key, base, canonical(raw, out), day=sit["id"][:10], t=sit["time"])
            self.recorded[kind] += 1
        return raw

    def accepted(self, kind, out, ctx):
        """Would the world take this plan, voice or writing as it stands, free of what he could not know in 1831?"""
        if not isinstance(out, dict):
            return False
        if kind == "plan":
            items = self.world.plan_items(out, ctx)
            return isinstance(out.get("plan"), list) and 3 <= len(items) == len(out["plan"]) <= 6
        if kind == "voice":
            says, does = out.get("says"), out.get("does")
            return isinstance(says, str) and 2 <= len(says.strip()) <= 420 and (does is None or isinstance(does, str) and len(does) <= 200) \
                and not self.world.unmet(f"{says} {does or ''}", ctx["known_text"])
        w = works.clean(out)
        return bool(w) and not self.world.unmet(w["title"] + "\n" + w["text"], ctx["known_text"])


def health(url):
    """The JSON of the server's /health, {} if it does not answer."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=10) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, OSError, ValueError):
        return {}


def cmd_distill(a, out, explicit_out):
    from world.__main__ import rehearsal_config, rehearsal_setup
    from world.config import Config
    from world.clock import minute_of
    from world.engine import Days, Engine, until_of
    from world.feeds import Feeds
    from world.owl import OwlError
    from world.world import at_dt

    info = health(a.url)
    if not info:
        print(f"no answer from {a.url}/health: start the llama-server first", file=sys.stderr)
        return 1
    if info.get("stub"):
        if explicit_out:
            print("that server is a stand-in: its answers are not training data. Leave out --out, or point it at a scratch folder.", file=sys.stderr)
            return 1
        out = Path(tempfile.gettempdir()) / "hegel-train-stub"           # never mind/train: a stand-in's answers must not look like data
        print(f"a stand-in server: writing to {out}, not to mind/train")
    start = date.fromisoformat(a.start)
    folder = out / "rehearsal"
    marker = folder / "run.json"
    if marker.exists():
        was = json.loads(marker.read_text(encoding="utf-8"))
        if was["start"] != a.start or was["feeds"] != a.feeds:
            print(f"{folder} holds a rehearsal that started {was['start']} (feeds {was['feeds']}); rerun with those, or remove {folder} and the "
                  f"{', '.join(FILES.values())} beside it to start over", file=sys.stderr)
            return 1
        sim = rehearsal_config(folder, a.feeds)
    else:
        if any((out / name).exists() for name in FILES.values()):
            print(f"{out} has example files but no rehearsal to go with them; remove them, or {out}/rehearsal's missing marker, before starting", file=sys.stderr)
            return 1
        sim = rehearsal_setup(Config(), a.start, folder, a.feeds)
        marker.write_text(json.dumps({"start": a.start, "feeds": a.feeds}), encoding="utf-8")
    sink = Sink(out)
    world = RecordingWorld(Feeds(sim))
    engine = Engine(sim, world, None, git=None)
    mind = DistillMind(a.url, sink, engine.soul, k=a.candidates, workers=a.workers, timeout=a.timeout, start=start, days=a.days)
    mind.world = world
    engine.mind = engine.owl_mind = mind
    days = Days(folder)
    if sink.per_day:
        print(f"resuming: {sum(sink.per_day.values())} decisions on {len(sink.per_day)} days are recorded; the folder is {folder}")
    try:
        for i in range(a.days):
            d = start + timedelta(days=i)
            day = days.load(d)
            if day and day.get("complete") and (day.get("owl") or a.no_owl):
                continue                                                      # done in an earlier run
            now, end = at_dt(d, 0), at_dt(d, 1440)
            if day:
                now = max(now, until_of(day) - timedelta(minutes=sim.lead))
            while now < end:
                engine.advance(now)
                now += timedelta(minutes=5)
            finished = days.load(d)
            finished["complete"] = True
            days.save(finished)
            if not a.no_owl:                                                  # the owl's gist of the night is part of tomorrow's prompts
                try:
                    engine.run_owl(finished, at_dt(d + timedelta(days=1), 90))
                except (MindAway, OwlError) as e:
                    print(f"the owl did not write up {d}: {e}", file=sys.stderr)
            print(f"== {d} done: {sink.per_day[d.isoformat()]} decisions", flush=True)
    except DistillAbort as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nstopped by hand; run the same command again to carry on", file=sys.stderr)
        return 130
    print(f"done in {duration(time.time() - mind.t0)}: " + ", ".join(f"{len(sink.done[k])} {LABEL[k]}" for k in FILES)
          + f" in {out}; {mind.stuck} decisions had no valid candidate")
    return 0


# ── a stand-in llama-server ─────────────────────────────────────────
class StubLlama(BaseHTTPRequestHandler):
    """A llama-server that answers like a stand-in: valid decisions for the contract's schema (the words are the rehearsal mind's own bank,
    marked '(rehearsal)'), the plan, voices and writings of the rehearsal mind, and now and then an invalid decision so that the filter has
    something to filter. It says so in /health, and --distill will not write its answers into mind/train."""
    calls, invalid_every, fail_after = 0, 4, None
    lock = threading.Lock()

    def log_message(self, *a):
        pass

    def reply(self, text, code=200):
        data = json.dumps({"choices": [{"message": {"content": text}}]}).encode() if code == 200 else b"{}"
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        data = b'{"status":"ok","stub":true}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        schema = ((body.get("response_format") or {}).get("json_schema") or {}).get("schema") or {}
        if not schema:
            return self.reply("(stub) A plain answer would go here.")
        if "thought" not in schema.get("properties", {}):
            return self.reply(StubMind().chat(body["messages"], schema))
        with StubLlama.lock:
            StubLlama.calls += 1
            n = StubLlama.calls
        if StubLlama.fail_after is not None and n > StubLlama.fail_after:
            return self.reply("", 503)                       # 503, as a llama-server answers while it has no slot: the mind is away (a 500 would be tried unconstrained)
        text = body["messages"][1]["content"]
        here = (re.search(r"You are at: (\w+)\.", text) or [0, "home"])[1]
        open_now = re.search(r"Open now: ([^\n]+)\.", text)
        places = [re.match(r"\w+", x.strip())[0] for x in open_now[1].split(",")] if open_now else [here]
        clock = (re.search(r", (\d\d:\d\d) Delhi time", text) or [0, "12:00"])[1]
        place = here if here in places else "home"
        ans = {"action": "walk" if place != here else ["stay", "read", "write", "rest"][n % 4], "place": place, "minutes": 30,
               "says": "Namaste." if "Present: nobody" not in text and place == here else None, "buys": [], "revision": None}
        ans = {"thought": StubMind.thought(dict(ans), {"id": f"{n}|{text[:40]}", "time": clock})["thought"], **ans}      # thought first, as the schema has it
        if n % self.invalid_every == 0:
            ans["thought"] = "(stub-invalid) " + ans["thought"]
            if n % (2 * self.invalid_every) == 0:
                ans["place"] = "mars"                                                # unknown place: the world's check refuses it
                return self.reply(json.dumps(ans))
            return self.reply(json.dumps(ans)[:-8])                                  # cut off: not JSON at all
        self.reply(json.dumps(ans))


# ── stats ───────────────────────────────────────────────────────────
def clip(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def cmd_stats(a, out):
    rng = random.Random(a.seed)
    names = ["corpus.jsonl"] + [FILES[k] for k in FILES] + ["general.jsonl"]
    rows = {name: read_jsonl(out / name) for name in names}
    print(f"{out}")
    total = 0
    for name in names:
        r = rows[name]
        if not r:
            print(f"  {name:16} missing" if not (out / name).exists() else f"  {name:16} empty")
            continue
        chars = sum(len(x["text"]) for x in r) if name == "corpus.jsonl" else sum(len(m["content"]) for x in r for m in x["messages"])
        total += chars
        print(f"  {name:16} {len(r):6} {'documents' if name == 'corpus.jsonl' else 'examples'}  {chars / 1e6:6.2f} M characters  about {tokens_of(chars) / 1e6:5.2f} M tokens")
    print(f"  all files        about {tokens_of(total) / 1e6:.2f} M tokens (characters / 4)")
    dec = rows["decisions.jsonl"]
    if dec:
        acts = collections.Counter(json.loads(x["messages"][-1]["content"])["action"] for x in dec)
        scores = [x["meta"]["score"] for x in dec]
        valid = [x["meta"]["valid"] / x["meta"]["candidates"] for x in dec]
        print(f"  decisions: {len({x['meta']['day'] for x in dec})} days; score mean {statistics.mean(scores):.2f} (min {min(scores):.2f}, max {max(scores):.2f}); "
              f"{100 * statistics.mean(valid):.0f}% of candidates valid; actions " + ", ".join(f"{k} {v}" for k, v in acts.most_common()))
    flagged = [name for name in names if any(m in json.dumps(x, ensure_ascii=False) for x in rows[name] for m in STAND_IN)]
    if flagged:
        print(f"  WARNING: stand-in text {STAND_IN} in {', '.join(flagged)}: those files are not training data")
    print(f"\nsamples (seed {a.seed}; run again with --seed to see others)")
    for name in names:
        for x in rng.sample(rows[name], min(a.samples, len(rows[name]))) if rows[name] else []:
            if name == "corpus.jsonl":
                print(f"\n[{name}] {len(x['text'])} characters\n  {clip(x['text'][:700], 700)}")
            else:
                last = x["messages"][-1]["content"]
                if name == "decisions.jsonl":
                    m = x["meta"]
                    print(f"\n[{name}] {m['key']}  score {m['score']:+.2f} ({m['valid']}/{m['candidates']} valid)\n  situation: {clip(x['messages'][1]['content'].split('What happens:')[-1], 260)}"
                          f"\n  answer:    {clip(last, 700)}")
                else:
                    print(f"\n[{name}] {x['meta'].get('key', x['meta'].get('id'))}\n  asked:  {clip(x['messages'][-2]['content'], 260)}\n  answer: {clip(last, 600)}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus", action="store_true", help="write corpus.jsonl from the shelf")
    p.add_argument("--max-chars", type=int, help="with --corpus: keep about this many characters, spread evenly over the works")
    p.add_argument("--distill", action="store_true", help="rehearse days with Qwen and keep the best decisions")
    p.add_argument("--url", help="with --distill: the Qwen llama-server, e.g. http://127.0.0.1:8080")
    p.add_argument("--days", type=int, default=20, help="with --distill: days to rehearse (default 20)")
    p.add_argument("--candidates", type=int, default=4, help="with --distill: K, candidates per decision (default 4)")
    p.add_argument("--start", default=DAY_ONE, help=f"with --distill: the first day, YYYY-MM-DD (default {DAY_ONE}; must come after day 1)")
    p.add_argument("--workers", type=int, default=1, help="with --distill: ask the K candidates in parallel (needs llama-server --parallel K; default 1)")
    p.add_argument("--feeds", action="store_true", help="with --distill: use the real weather and news (default off: the rehearsal is offline)")
    p.add_argument("--no-owl", action="store_true", help="with --distill: skip the owl's write-up each night (its gist is in the next day's prompts)")
    p.add_argument("--timeout", type=int, default=300, help="with --distill: seconds to wait for one answer")
    p.add_argument("--general", type=int, metavar="N", help="write general.jsonl with N human-written instruction examples")
    p.add_argument("--answer-with", metavar="URL", help="with --general: keep the questions and let this Qwen server write the answers (one call each)")
    p.add_argument("--general-url", default=GENERAL_API, help=argparse.SUPPRESS)
    p.add_argument("--stats", action="store_true", help="counts, token estimates and random samples")
    p.add_argument("--samples", type=int, default=3, help="with --stats: samples per file (default 3)")
    p.add_argument("--seed", type=int, default=1, help="with --stats: which samples")
    p.add_argument("--serve-stub", type=int, metavar="PORT", help="serve a stand-in llama-server on this port")
    p.add_argument("--out", help=f"the folder of the data (default {TRAIN.relative_to(REPO)})")
    a = p.parse_args(argv)
    out = Path(a.out) if a.out else TRAIN
    if a.serve_stub:
        print(f"stand-in llama-server on http://127.0.0.1:{a.serve_stub}", flush=True)
        HTTPServer(("127.0.0.1", a.serve_stub), StubLlama).serve_forever()
        return 0
    if not (a.corpus or a.distill or a.general or a.stats):
        p.error("say what to do: --corpus, --general N, --distill, --stats or --serve-stub PORT")
    if a.distill and not a.url:
        p.error("--distill needs --url")
    code = 0
    if a.corpus:
        code = cmd_corpus(a, out) or code
    if a.general:
        code = cmd_general(a, out) or code
    if a.distill:
        code = cmd_distill(a, out, bool(a.out)) or code
    if a.stats:
        code = cmd_stats(a, out) or code
    return code


if __name__ == "__main__":
    sys.exit(main())
