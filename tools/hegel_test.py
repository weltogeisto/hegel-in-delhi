#!/usr/bin/env python3
"""Hegel in Delhi: the Hegel test. The yardstick that decides between Bonsai, Qwen and a trained model.

    python3 tools/hegel_test.py --url http://PC:8081 --label bonsai            # the four parts, without the shelf
    python3 tools/hegel_test.py --url http://PC:8081 --label bonsai-shelf --shelf
    python3 tools/hegel_test.py --url http://PC:8082 --label qwen --only cont  # one part; the others already in the file stay
    python3 tools/hegel_test.py --compare bonsai bonsai-shelf qwen             # writes mind/results/hegeltest.md
    python3 tools/hegel_test.py --export-ppl mind/results/ppl                  # held-out and seen text for llama-perplexity
    python3 tools/hegel_test.py --serve-stub 8099                              # a stand-in llama-server, to try the tool

Four parts. (a) Blind passages, after Schwitzgebel et al.: 20 questions that Hegel answered in his own texts; the mind answers
each four times as Hegel, and the sheet mind/results/hegeltest-<label>.html shows five answers (one is the real passage, from a
19th-century translation) in shuffled order to judges, who choose; the score is how often they pick the real one (chance is 20%,
lower means the model sounds more like Hegel). (b) Thirty questions about his life, scored by tolerant matching. (c) The 20 test
situations of the bake-off through the live contract: valid JSON, what the world would refuse, words of after 1831, thought length.
(d) Continuations: the chat answers of (a) are modern prose set against translations of 1857 to 1910, so judges tell them apart by form
alone. Here the mind gets the first half of each real passage under the header line that his books carry in the training text, in plain
completion mode (no chat template, no system prompt), and writes on; the sheet mind/results/hegeltest-<label>-cont.html offers the real
second half and four continuations in one typography, and a Burrows' Delta over the 150 commonest words says how close the continuations
lie to his English translators. With --shelf the mind gets passages from his shelf with every question; in the blind test the book the real
passage comes from (and its German or English twin) is held out, so the shelf cannot hand over the answer; the continuations ignore it.
--export-ppl writes the text for llama.cpp's llama-perplexity: the 20 real passages, which the adapter never saw, and 20 that it did.
Standard library only."""
import argparse
import functools
import glob
import hashlib
import html
import json
import math
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "mind"))
sys.path.insert(0, str(HERE))                  # tools/corpus.py and tools/train_data.py, for the header line of a document
import bakeoff  # noqa: E402  (the 20 test situations and the one way of asking the mind)
from world import contract, shelf  # noqa: E402
from world.world import wordlist  # noqa: E402

DATA, RESULTS = REPO / "mind/hegeltest", REPO / "mind/results"
ANSWERS, TEMPERATURE, WORDS = 4, 0.9, (80, 140)
PARTS = ("blind", "bio", "behaviour", "cont")
RUN, SPLIT_MIN, TRIES = 8, 35, 3                # words in a row that two texts share when one has the other's wording (as train_data.HELD_OUT_RUN); the shortest half of a split passage; tries for one continuation
STYLE_SEGMENT, STYLE_FEATURES = 1000, 150       # words in a segment of the Delta reference; the commonest words Delta looks at
# the book a real passage comes from, with its twin in the other language: held out of the shelf in the blind test
FAMILY = {"sibree-history": ["sibree-history", "welt-1", "welt-2", "welt-3", "welt-4"], "dyde-right": ["dyde-right", "rechts"],
          "wallace-mind": ["wallace-mind", "enzyklopaedie"], "wallace-logic": ["wallace-logic", "enzyklopaedie"],
          "baillie-1": ["baillie-1", "baillie-2", "phaen"], "baillie-2": ["baillie-1", "baillie-2", "phaen"], "bosanquet-art": ["bosanquet-art"]}
BLIND_ASK = ("A visitor puts this question to you: {q}\n\nAnswer it as yourself, in English, in 80 to 140 words, the way you answer in your books and "
             "lectures: continuous prose, no list, no heading, no JSON, nothing before or after the answer.")
BIO_ASK = "{q}\n\nAnswer plainly, in character, in one or two sentences."
SHELF_NOTE = "\nFrom your shelf:\n{lines}\n"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def voice():
    """The soul without the world's rules and the JSON answer: Hegel as the day mind knows him, for questions that want prose."""
    soul = (REPO / "mind/soul.md").read_text(encoding="utf-8")
    keep = re.split(r"^## ", soul, flags=re.M)
    return "## ".join(p for p in keep if not p.startswith(("The world's rules", "Your answer"))).strip() + "\n"


def fold(s):
    return shelf.fold(s)


def clean_answer(text):
    """The mind's reply as plain prose: no think tags, fences, quotes around it, speaker label or JSON wrapper."""
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    t = re.sub(r"^```\w*\s*|\s*```$", "", t).strip()
    j = contract.extract_json(t) if t.startswith("{") else None
    if isinstance(j, dict):
        t = next((str(j[k]) for k in ("answer", "text", "says", "thought") if isinstance(j.get(k), str)), t)
    t = re.sub(r"^(Hegel|G\. ?W\. ?F\. Hegel)\s*:\s*", "", t)
    return " ".join(t.strip().strip("“”\"").split())


def ask(url, system, user, temperature, tokens, timeout, seed=None):
    """One reply from a llama-server as text; '' if it did not answer."""
    payload = {"model": "local", "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "temperature": temperature, "max_tokens": tokens, "chat_template_kwargs": {"enable_thinking": False}}
    if seed is not None:
        payload["seed"] = seed
    try:
        data = bakeoff.post(url, payload, timeout)
        return (data["choices"][0]["message"].get("content") or "").strip()
    except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError) as e:
        print(f"  no answer: {e}", file=sys.stderr)
        return ""


def complete(url, prompt, tokens, temperature, timeout, seed=None):
    """The raw continuation of prompt from a llama-server's /completion (no chat template, no system prompt, stopping at a blank line); '' if it did not answer."""
    payload = {"prompt": prompt, "n_predict": tokens, "temperature": temperature, "stop": ["\n\n"], "cache_prompt": False}
    if seed is not None:
        payload["seed"] = seed
    req = urllib.request.Request(url.rstrip("/") + "/completion", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (json.loads(r.read().decode("utf-8")).get("content") or "").strip()
    except (urllib.error.URLError, OSError, ValueError, AttributeError) as e:
        print(f"  no continuation: {e}", file=sys.stderr)
        return ""


# ── the shelf for a question ────────────────────────────────────────
class Books:
    """The shelf as the test uses it: passages for a question, leaving out some works."""

    def __init__(self, on):
        self.shelf = shelf.load() if on else None

    def lines(self, parts, hold=()):
        if not self.shelf:
            return ""
        got = self.shelf.pick(parts, hold=hold)
        return SHELF_NOTE.format(lines="\n".join(f"- {x['label']}: “{x['text']}”" for x in got)) if got else ""

    def hold(self, source):
        return FAMILY.get(source, [source])


# ── (a) the blind passages ──────────────────────────────────────────
def run_blind(url, books, args, system):
    out = []
    for q in load("questions.json")["questions"]:
        t0 = time.time()
        extra = books.lines([(q["question"], 1.0)], books.hold(q["source"]) if args.holdout == "family" else ())
        user = (extra + "\n" if extra else "") + BLIND_ASK.format(q=q["question"])
        answers = [clean_answer(ask(url, system, user, TEMPERATURE, 420, args.timeout, seed=args.seed + 17 * i)) for i in range(args.answers)]
        out.append({"id": q["id"], "shelf": bool(extra), "answers": answers, "latency_s": round(time.time() - t0, 1)})
        print(f"blind {q['id']:12} {sum(map(bool, answers))}/{args.answers} answers  {out[-1]['latency_s']:5.1f}s", flush=True)
    return out


def order_for(label, qid, n):
    """The positions of the n model answers and the real one (index n) in the sheet: a shuffle that only the label and the question decide."""
    seed = int(hashlib.sha256(f"{label}|{qid}".encode()).hexdigest()[:12], 16)
    pos = list(range(n + 1))
    random.Random(seed).shuffle(pos)
    return pos


def sheet_data(label, rows):
    """The items of the sheet, five options each in shuffled order, and the key. `rows` are the blind answers (an item shows the question; the
    real option is the passage) or the continuations (they carry the real second half as "rest"; an item shows the opening of the passage)."""
    qs, key = [], []
    by_id = {q["id"]: q for q in load("questions.json")["questions"]}
    for b in rows:
        q = by_id[b["id"]]
        pool = b["answers"] + [b.get("rest", q["passage"])]     # the real one last, then shuffled
        pos = order_for(label, q["id"], len(b["answers"]))
        letters = "ABCDEFGH"[:len(pool)]
        shown = [pool[i] for i in pos]
        real = letters[pos.index(len(pool) - 1)]
        lead = {"opening": b["opening"]} if "rest" in b else {"question": q["question"]}
        qs.append({"id": q["id"], "topic": q["topic"], **lead, "options": dict(zip(letters, shown)), "real": real,
                   "from": f"{q['work']} {q['ref']}" if q["ref"].startswith("§") else f"{q['work']}, {q['ref']}", "translation": q["translation"]})
        key.append({"id": q["id"], "real": real, "order": ["real" if i == len(pool) - 1 else f"model {i + 1}" for i in pos], "from": qs[-1]["from"]})
    return qs, key


SHEET = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hegel test: __LABEL__</title>
<style>
:root{--bg:#f6f3ea;--ink:#1d2340;--muted:#5a6080;--card:#fffdf7;--line:#cfc8b4;--accent:#3b4a9c;--ok:#1d6b3a;--okbg:#e2f2e6;--no:#8a2a2a}
@media (prefers-color-scheme:dark){:root{--bg:#161823;--ink:#e8e6f0;--muted:#a3a7c4;--card:#1f2232;--line:#3a3e58;--accent:#9db0ff;--ok:#8fe0a8;--okbg:#1d3326;--no:#f0a0a0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.5 Georgia,'Times New Roman',serif}
header,main{max-width:46rem;margin:0 auto;padding:0 16px}header{padding-top:18px}
h1{font-size:1.5rem;margin:0 0 .3rem}h2{font-size:1.05rem;margin:0 0 .4rem}.muted{color:var(--muted);font-size:.9rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:16px 0}
.opt{display:flex;gap:10px;align-items:flex-start;padding:10px;margin:8px 0;border:1px solid var(--line);border-radius:8px;cursor:pointer}
.opt input{margin-top:.45rem;flex:none;width:1.2rem;height:1.2rem}.opt .l{font-weight:700;flex:none;width:1.2rem}.opt p{margin:0}
.opt.real{border-color:var(--ok);background:var(--okbg)}.opt.real .l::after{content:" ✓";color:var(--ok)}
button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid var(--accent);background:none;color:var(--accent);cursor:pointer}
button:disabled{opacity:.5}.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0}
input[type=text]{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);min-width:9rem}
blockquote{margin:.3rem 0 .8rem;padding:.1rem 12px;border-left:3px solid var(--accent)}blockquote p{margin:.3rem 0}
.verdict{margin:8px 0 0}.hit{color:var(--ok)}.miss{color:var(--no)}.sticky{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:1}
</style></head><body>
<header>
<h1>__HEAD__</h1>
<p class="muted">Candidate: <b>__LABEL__</b>__SHELF__. __INTRO__</p>
<div class="row"><label>Judge: <input type="text" id="judge" placeholder="your name"></label><button id="export" type="button">Export judgments</button></div>
<div class="sticky muted" id="score" aria-live="polite"></div>
</header>
<main id="qs"></main>
<script>
const LABEL = __LABEL_JSON__, RUN = '__RUN__', DATA = __DATA__;
const key = 'hegeltest:' + LABEL + ':' + RUN;                  // a new run of the same label starts with clean choices
const store = {get(){ try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch (e) { return {}; } },
               set(v){ try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) {} }};
let state = Object.assign({judge: '', choices: {}, shown: {}}, store.get());
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const real = id => (DATA.find(q => q.id === id) || {}).real;
function tally(){ const ids = Object.keys(state.choices).filter(real); const hits = ids.filter(id => state.choices[id] === real(id)).length;
  return {answered: ids.length, hits}; }
function paint(){
  const t = tally(), k = Object.keys(state.shown).filter(id => state.choices[id] && real(id));
  const seen = k.filter(id => state.choices[id] === real(id)).length;
  document.getElementById('score').textContent = `${t.answered} of ${DATA.length} answered` + (k.length ? `; of the ${k.length} whose key you have seen, you found the real one ${seen} times (chance: 20%)` : '');
  document.getElementById('judge').value = state.judge || '';
}
function build(){
  document.getElementById('qs').innerHTML = DATA.map((q, n) => `<section class="card" id="c-${q.id}"><h2>${n + 1}. ${esc(q.topic)}</h2>`
    + (q.opening ? `<p class="muted">The passage begins:</p><blockquote><p>${esc(q.opening)}</p></blockquote><p class="muted">How does it go on?</p>` : `<p><i>${esc(q.question)}</i></p>`)
    + Object.entries(q.options).map(([l, text]) => `<label class="opt" data-l="${l}"><input type="radio" name="${q.id}" value="${l}"><span class="l">${l}</span><p>${esc(text)}</p></label>`).join('')
    + `<div class="row"><button type="button" data-key="${q.id}">Show key</button></div><p class="verdict" id="v-${q.id}"></p></section>`).join('');
  DATA.forEach(q => { const c = state.choices[q.id]; if (c) document.querySelector(`input[name="${q.id}"][value="${c}"]`).checked = true; if (state.shown[q.id]) reveal(q.id); });
  paint();
}
function reveal(id){
  const q = DATA.find(x => x.id === id), card = document.getElementById('c-' + id);
  card.querySelectorAll('.opt').forEach(o => o.classList.toggle('real', o.dataset.l === q.real));
  const c = state.choices[id], v = document.getElementById('v-' + id);
  v.innerHTML = `The real one is <b>${q.real}</b>: ${esc(q.from)} (${esc(q.translation)}). ` + (c ? (c === q.real ? '<span class="hit">You found it.</span>' : `<span class="miss">You chose ${c}.</span>`) : 'You had not chosen.');
}
document.addEventListener('change', e => { if (e.target.type === 'radio') { state.choices[e.target.name] = e.target.value; store.set(state); paint(); } });
document.addEventListener('click', e => { const id = e.target.dataset && e.target.dataset.key; if (id){ state.shown[id] = true; store.set(state); reveal(id); paint(); } });
document.getElementById('judge').addEventListener('input', e => { state.judge = e.target.value; store.set(state); });
document.getElementById('export').addEventListener('click', () => {
  const t = tally(), out = {label: LABEL, judge: state.judge || 'anonymous', exported: new Date().toISOString(), answered: t.answered, hits: t.hits, choices: state.choices};
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], {type: 'application/json'}));
  a.download = `hegeltest-${LABEL}-judged.json`; document.body.appendChild(a); a.click(); a.remove();
});
build();
</script></body></html>
"""


INTRO = ("Twenty questions that Hegel answered in his own books and lectures. Each has five answers: one is the real passage from a nineteenth-century "
         "English translation, four were written by the model as Hegel. Pick the one you think is real. Chance is one in five: the lower the judges' hit "
         "rate, the more the model sounds like him. Some passages hold his nineteenth-century views as he lectured them, unsoftened.")
INTRO_CONT = ("Twenty passages from his books in nineteenth-century English translation, each cut in two. You see the opening and five continuations: one is the "
              "real second half, four were written by the model, which was given the opening as the start of a page of his books and wrote on. Pick the one you "
              "think is real. Chance is one in five: the lower the judges' hit rate, the more the model sounds like him. Some passages hold his nineteenth-century "
              "views as he lectured them, unsoftened.")


def write_sheet(label, rows, shelf_on):
    """mind/results/hegeltest-<label>.html and -key.json for the blind answers or, if the rows are continuations, for the sheet of the cont part."""
    qs, key = sheet_data(label, rows)
    cont = any("rest" in b for b in rows)
    data = json.dumps(qs, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    page = (SHEET.replace("__LABEL_JSON__", json.dumps(label)).replace("__RUN__", hashlib.sha1(data.encode()).hexdigest()[:8]).replace("__LABEL__", html.escape(label))
            .replace("__HEAD__", "Which ending is Hegel's?" if cont else "Which one is Hegel?").replace("__INTRO__", INTRO_CONT if cont else INTRO)
            .replace("__SHELF__", " (with his shelf)" if shelf_on else "").replace("__DATA__", data))
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"hegeltest-{label}.html").write_text(page, encoding="utf-8")
    (RESULTS / f"hegeltest-{label}-key.json").write_text(json.dumps({"label": label, "questions": key}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return qs, key


# ── (b) the biography ───────────────────────────────────────────────
def matches(reply, groups):
    """How many of the groups of accepted variants appear in reply (case, diacritics and ß ignored; a number must stand alone)."""
    text = fold(reply)
    hit = 0
    for variants in groups:
        for v in variants:
            v = fold(v)
            if re.search(rf"(?<![a-z0-9]){re.escape(v)}(?![0-9])" if v.isdigit() else re.escape(v), text):
                hit += 1
                break
    return hit


def run_bio(url, books, args, system):
    items = []
    for q in load("biography.json")["questions"]:
        extra = books.lines([(q["question"], 1.0)])
        reply = clean_answer(ask(url, system, (extra + "\n" if extra else "") + BIO_ASK.format(q=q["question"]), 0.3, 160, args.timeout, seed=args.seed))
        got = matches(reply, q["answers"])
        items.append({"id": q["id"], "question": q["question"], "fact": q["fact"], "reply": reply, "groups": len(q["answers"]), "matched": got, "right": got == len(q["answers"])})
    n = len(items)
    score = {"right": sum(i["right"] for i in items), "n": n, "partial": round(sum(i["matched"] for i in items) / max(1, sum(i["groups"] for i in items)), 3), "items": items}
    print(f"biography {score['right']}/{n} right, {score['partial'] * 100:.0f}% of the facts")
    return score


# ── (c) behaviour ───────────────────────────────────────────────────
def run_behaviour(url, books, args):
    soul = (REPO / "mind/soul.md").read_text(encoding="utf-8")
    later = wordlist("after_1831.txt", "s?")
    situations = json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"]
    rows = []
    for s in situations:
        s = dict(s)
        if books.shelf:
            parts = shelf.query_parts(s["event"], s["place"], s["present"], [], [])
            s["shelf"] = books.shelf.pick(parts)
        prompt = contract.render(s)
        try:
            raw, _ = bakeoff.ask(url, soul, prompt, "local", args.timeout)
            ans = contract.extract_json(raw)
            errors, _ = contract.check(ans, s)
        except Exception as e:  # a failed request is a failed answer, and the run goes on
            raw, ans, errors = "", None, [f"request failed: {e}"]
        shape = contract.check_shape(ans)[0] if ans is not None else ["no JSON"]
        said = " ".join(str(ans.get(k) or "") for k in ("thought", "says", "revision", "looks_up")) if isinstance(ans, dict) else ""
        leaks = sorted({m.group(1) for m in (later.finditer(said) if later else ())
                        if not re.search(r"\b" + re.escape(m.group(1)) + r"s?\b", prompt, re.I)})
        thought = ans.get("thought") if isinstance(ans, dict) and isinstance(ans.get("thought"), str) else ""
        rows.append({"id": s["id"], "valid": not shape, "refused": bool(errors) and not shape, "errors": errors, "leaks": leaks, "thought_chars": len(thought),
                     "thought_words": len(thought.split()), "shelf": [x["label"] for x in s.get("shelf") or []]})
    n = len(rows)
    thoughts = [r["thought_words"] for r in rows if r["valid"]]
    out = {"n": n, "valid": sum(r["valid"] for r in rows), "refused": sum(r["refused"] for r in rows), "leaking": sum(bool(r["leaks"]) for r in rows),
           "leaks": sorted({x for r in rows for x in r["leaks"]}), "thought_words": round(statistics.mean(thoughts), 1) if thoughts else 0,
           "thought_chars": round(statistics.mean(r["thought_chars"] for r in rows if r["valid"]), 0) if thoughts else 0, "rows": rows}
    print(f"behaviour {out['valid']}/{n} valid, {out['refused']} refused by the rules, {out['leaking']} with words from after 1831, thoughts of {out['thought_words']} words")
    return out


# ── (d) the continuations ───────────────────────────────────────────
ABBREVIATIONS = {"i.e", "e.g", "viz", "etc", "cf", "mr", "mrs", "dr", "st", "vs", "sc", "ibid"}
SENTENCE_END = re.compile(r"[.?!;:][\"”’')\]]*(?=\s|$)")
DASH = re.compile(r"\s*[—–―]\s*|\s*--+\s*|\s+-\s+")
TYPOGRAPHY = str.maketrans({"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "‚": "'", "…": "...", "\u00a0": " ", "ﬁ": "fi", "ﬂ": "fl"})


def sentence_ends(text, marks=".?!;:"):
    """[(words, end)]: for each sentence end of text, the words before it and the index just after it. One of `marks` followed by white space or the end
    of the text closes a sentence, but not the point of an abbreviation (i.e., e.g., viz., etc., cf., Mr., St.) nor of a single capital letter (S. W. Dyde)."""
    out = []
    for m in SENTENCE_END.finditer(text):
        mark = m.group(0)[0]
        last = (text[:m.start() + 1].split() or [""])[-1].lstrip("(“\"‘'[")
        if mark in marks and not (mark == "." and (last.rstrip(".").lower() in ABBREVIATIONS or re.fullmatch(r"[A-Z]\.", last))):
            out.append((len(text[:m.end()].split()), m.end()))
    return out


def split_passage(text):
    """(opening, rest): text cut at the sentence end nearest its middle, both halves of at least SPLIT_MIN words; at the word nearest the middle if
    no sentence end leaves both that long. The same text always splits the same way."""
    n = len(text.split())
    ends = [(k, e) for k, e in sentence_ends(text) if SPLIT_MIN <= k <= n - SPLIT_MIN]
    if ends:
        e = min(ends, key=lambda x: (abs(x[0] - n / 2), x[0]))[1]
        return text[:e].strip(), text[e:].strip()
    words = text.split()
    return " ".join(words[:n // 2]), " ".join(words[n // 2:])


def cut(text, words):
    """text trimmed to the sentence end nearest `words` words, between 0.7 and 1.3 times as many; None if no sentence ends there. Only . ? and ! end it,
    as the real halves end: a model's text that stopped at a semicolon would show."""
    ends = [(k, e) for k, e in sentence_ends(text, ".?!") if 0.7 * words <= k <= 1.3 * words]
    if not ends:
        return None
    return text[:min(ends, key=lambda x: (abs(x[0] - words), x[0]))[1]].strip()


def typography(text):
    """text in one typography, for the real half and the model's alike: straight quotes, one dash (an em dash with no space round it, as the translations
    print it), three dots for an ellipsis, single spaces. Nothing else about the wording changes."""
    return " ".join(DASH.sub("—", (text or "").translate(TYPOGRAPHY)).split())


def folded_words(text):
    """The words of text as runs of letters and digits, lower case, without diacritics (ß as ss): one spelling for a copy and its original."""
    w = re.findall(r"[^\W_]+", text.lower())
    return w if "".join(w).isascii() else [x for t in w for x in ((t,) if t.isascii() else re.findall(r"[a-z0-9]+", fold(t)))]


def shingles(text, n=RUN):
    """The runs of n words in a row of text, folded, so that typography and hyphens cannot hide a copy."""
    w = folded_words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def shares_run(text, runs):
    """Whether text has a run of RUN words in a row that is in `runs`, a set of shingles (of the real half, or of the held-out passages)."""
    w = folded_words(text)
    return any(g in runs for g in zip(*(w[i:] for i in range(RUN))))


@functools.lru_cache(maxsize=None)
def corpus_tools():
    """(train_data.header, {work id: manifest entry}) from tools/, the way the training text writes its header lines; None where they cannot be imported."""
    try:
        import corpus
        import train_data
        return train_data.header, {w["id"]: w for w in corpus.WORKS}
    except Exception as e:  # a missing module, a Python too old for them: the header is then built from the question
        print(f"  corpus headers unavailable ({type(e).__name__}: {e}); building them from the questions", file=sys.stderr)
        return None


def header_for(q, ref=None):
    """The header line that the training text puts above a document of q's work, ending in `ref` (the question's own by default): 'Hegel's Philosophy of
    Right, tr. S. W. Dyde (1896), §258, Addition'. Without tools/corpus.py it is built from the question: 'Hegel, Philosophy of Right, tr. S. W. Dyde (1896), ...'."""
    ref = q["ref"] if ref is None else ref
    tools = corpus_tools()
    if tools and q["source"] in tools[1]:
        return tools[0](tools[1][q["source"]], ref, ref)
    who = re.match(r"(.*?),\s*(\d{4})$", q["translation"])
    line = f"Hegel, {q['work']}, tr. " + (f"{who[1]} ({who[2]})" if who else q["translation"])
    return line + (f", {ref}" if ref else "")


def continuation(url, prompt, words, real, args, seed):
    """One model continuation of prompt for a real half of `words` words, as (text, recited, cut). It is asked for with up to TRIES seeds (seed, seed + 1 ...)
    until it is neither a copy of the real half (a run of RUN words shared with `real`, its shingles) nor without a sentence end near the right length;
    then the best try stays: not recited before not cut, the earlier before the later. A try that has no sentence end is cut at `words` words."""
    tries = []
    for k in range(TRIES):
        text = typography(complete(url, prompt, int(2.5 * words), TEMPERATURE, args.timeout, seed=seed + k))
        trimmed = cut(text, words)
        shown = trimmed if trimmed is not None else " ".join(text.split()[:words])
        tries.append((shares_run(shown, real), trimmed is None, shown))
        if not tries[-1][0] and not tries[-1][1]:
            break
    recited, hard, shown = min(tries, key=lambda t: t[:2])
    return shown, recited, hard


def run_cont(url, args):
    out = []
    for q in load("questions.json")["questions"]:
        t0 = time.time()
        opening, rest = split_passage(q["passage"])
        prompt, words, real = header_for(q) + "\n\n" + opening, len(rest.split()), shingles(rest)
        row = {"id": q["id"], "opening": typography(opening), "rest": typography(rest), "answers": [], "recited": [], "cut": []}
        for i in range(args.answers):
            text, recited, hard = continuation(url, prompt, words, real, args, args.seed + 17 * i)
            row["answers"].append(text)
            row["recited"].append(recited)
            row["cut"].append(hard)
        row["latency_s"] = round(time.time() - t0, 1)
        out.append(row)
        print(f"cont  {q['id']:12} {sum(map(bool, row['answers']))}/{args.answers} answers, {sum(row['recited'])} recited, {sum(row['cut'])} cut  {row['latency_s']:5.1f}s", flush=True)
    return out


# ── Burrows' Delta: how close a text lies to his translators ────────
STYLE_WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*")


def style_words(text):
    return STYLE_WORD.findall(text.lower().replace("’", "'"))


@functools.lru_cache(maxsize=1)
def reference():
    """The yardstick of Burrows' Delta, built once per process from the English books on the shelf (his translators), without the passages that share a
    run of RUN words with the 20 real ones: {features, mean, sd, segments, words, left_out}. The books are cut into segments of about STYLE_SEGMENT words;
    a feature is one of the STYLE_FEATURES commonest words, with the mean and the standard deviation of its share of a segment. None without a shelf."""
    books = shelf.load()
    if not books:
        return None
    held = set()
    for q in load("questions.json")["questions"]:
        held |= shingles(q["passage"]) | shingles(q["original"])
    segments, left_out = [], 0
    for w in books.works:
        if w["lang"] != "en":
            continue
        words = []
        for text in books.data["texts"][w["start"]:w["start"] + w["n"]]:
            if shares_run(text, held):
                left_out += 1
            else:
                words += style_words(text)
        k = round(len(words) / STYLE_SEGMENT)
        size = len(words) // k if k else 0
        segments += [Counter(words[j * size:(j + 1) * size]) for j in range(k)]
    sizes = [sum(c.values()) for c in segments]
    totals = Counter()
    for c in segments:
        totals.update(c)
    features, mean, sd = [], [], []
    for f, _ in totals.most_common(STYLE_FEATURES):
        shares = [c[f] / n for c, n in zip(segments, sizes)]
        m = sum(shares) / len(shares)
        s = math.sqrt(sum((x - m) ** 2 for x in shares) / len(shares))
        if s > 0:
            features.append(f)
            mean.append(m)
            sd.append(s)
    return {"features": features, "mean": mean, "sd": sd, "segments": len(segments), "words": sum(sizes), "left_out": left_out} if features else None


def delta(text):
    """Burrows' Delta of text: the mean over the reference's features of how many standard deviations the feature's share in text lies from its mean
    in the English translations of Hegel. Lower is closer; None without a shelf or without words. A short text scores higher than a long one of the same hand."""
    ref, words = reference(), style_words(text)
    if not ref or not words:
        return None
    counts = Counter(words)
    return sum(abs((counts[f] / len(words) - m) / s) for f, m, s in zip(ref["features"], ref["mean"], ref["sd"])) / len(ref["features"])


def groups_of(rows):
    """The answers of rows in one text per position: all first answers together, all second answers, and so on."""
    return [" ".join(r["answers"][i] for r in rows if i < len(r["answers"])) for i in range(max((len(r["answers"]) for r in rows), default=0))]


def continuation_style(out):
    """The summary of a run's continuations as it goes into the run JSON: answers, how many were recited and cut, and the Delta of the continuations (one
    per group of the same seed, about as long as the real halves together, and their mean), of the real second halves together (the floor), and, when the
    run has blind answers, of those chat answers grouped the same way, for contrast. Delta falls as a text grows, so each chat answer is cut to the length
    of the real half of its question: every group is as long as the group of real halves."""
    rows, ref = out["continuation"], reference()
    summary = {"answers": sum(len(r["answers"]) for r in rows), "recited": sum(sum(r["recited"]) for r in rows), "cut": sum(sum(r["cut"]) for r in rows),
               "delta": None, "reference": None}
    if ref:
        size = {r["id"]: len(r["rest"].split()) for r in rows}
        chat = [{"answers": [" ".join(a.split()[:size[b["id"]]]) for a in b["answers"]]} for b in out.get("blind") or [] if b["id"] in size]
        model, chat = [delta(t) for t in groups_of(rows)], [delta(t) for t in groups_of(chat)]
        mean = lambda xs: round(sum(xs) / len(xs), 3) if xs and None not in xs else None
        summary["delta"] = {"model": mean(model), "model_groups": [round(x, 3) for x in model if x is not None],
                            "real": mean([delta(" ".join(r["rest"] for r in rows))]), "chat": mean(chat), "chat_groups": [round(x, 3) for x in chat if x is not None]}
        summary["reference"] = {"segments": ref["segments"], "words": ref["words"], "left_out": ref["left_out"], "features": len(ref["features"])}
    return summary


# ── the text for llama-perplexity ───────────────────────────────────
@functools.lru_cache(maxsize=1)
def english_vocabulary():
    """{word: how often} over every passage of the English books on the shelf; empty without a shelf."""
    books, vocab = shelf.load(), Counter()
    for w in books.works if books else ():
        if w["lang"] == "en":
            for text in books.data["texts"][w["start"]:w["start"] + w["n"]]:
                vocab.update(style_words(text))
    return vocab


def misprinted(text, vocab):
    """Whether text has a mark of the scan: a capital inside a word, a backslash, a word that the English books use fewer than three times ('Theldea'), or one
    they use fewer than ten times that lies one letter from a word they use 100 times or more ('purpoee', 'eather'). The shelf's passages are filtered for
    such litter, but not quite clean."""
    if re.search(r"[a-z][A-Z]|\\", text):
        return True
    letters = "abcdefghijklmnopqrstuvwxyz"
    for word in {w for w in style_words(text) if len(w) > 2 and vocab[w] < 10}:
        near = ({word[:i] + word[i + 1:] for i in range(len(word))} | {word[:i] + c + word[i + 1:] for i in range(len(word)) for c in letters}
                | {word[:i] + c + word[i:] for i in range(len(word) + 1) for c in letters}) - {word}
        if vocab[word] < 3 or any(vocab[x] >= 100 for x in near):
            return True
    return False


def export_ppl(dirname, seed):
    """DIR/heldout.txt: the 20 real passages of the blind part, which the adapter never saw in training, each under its header line, a blank line between
    all; DIR/seen.txt: 20 passages that it did see (shelf passages of the same works, 80 to 140 words, none sharing a run of RUN words with the first
    file and none with a mark of the scan), one per question, picked by `seed`. Prints the paths and the llama-perplexity command lines. Returns 0, or 1 without a shelf."""
    books = shelf.load()
    if not books:
        print("no shelf: mind/shelf/index.json.gz is missing", file=sys.stderr)
        return 1
    questions = load("questions.json")["questions"]
    held = set()
    for q in questions:
        held |= shingles(q["passage"]) | shingles(q["original"])
    rng, taken, seen, vocab = random.Random(seed), set(), [], english_vocabulary()
    for q in questions:
        w = next(x for x in books.works if x["id"] == q["source"])
        pool = [d for d in range(w["start"], w["start"] + w["n"]) if WORDS[0] <= len(books.data["texts"][d].split()) <= WORDS[1]
                and d not in taken and not shares_run(books.data["texts"][d], held)]
        rng.shuffle(pool)
        d = next(d for d in pool if not misprinted(books.data["texts"][d], vocab))      # (the first of a shuffled pool: most pass, so few are looked at)
        taken.add(d)
        seen.append(header_for(q, books.data["refs"][d]) + "\n\n" + books.data["texts"][d])
    out = Path(dirname)
    out.mkdir(parents=True, exist_ok=True)
    files = {"heldout": [header_for(q) + "\n\n" + q["passage"] for q in questions], "seen": seen}
    for name, parts in files.items():
        (out / f"{name}.txt").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        print(f"wrote {out / (name + '.txt')}: {len(parts)} passages, {sum(len(x.split()) for x in parts)} words")
    print("\nWith the server stopped, the perplexity of each file on the plain model and on the model with the adapter (QWEN.gguf: the file the server uses):")
    for lora in ("", " --lora pc/out/hegel-lora.gguf"):
        for name in files:
            print(f"  llama-perplexity -m QWEN.gguf{lora} -f {out / (name + '.txt')} -c 512 -ngl 99")
    return 0


# ── the run, and the comparison ─────────────────────────────────────
def run(args):
    """Runs the parts (all, or --only) and writes mind/results/hegeltest-<label>.json. A file that is already there keeps the parts that are not run now."""
    books, system = Books(args.shelf), voice()
    path = RESULTS / f"hegeltest-{args.label}.json"
    parts = set(args.only.split(",")) if args.only else set(PARTS)
    out = {"label": args.label, "url": args.url, "started": "", "shelf": bool(args.shelf), "holdout": args.holdout if args.shelf else None, "answers_per_question": args.answers}
    if path.exists():
        out = {**out, **json.loads(path.read_text(encoding="utf-8"))}
        if parts & {"blind", "bio", "behaviour"}:               # these say how the parts that ran now were run
            out.update(url=args.url, shelf=bool(args.shelf), holdout=args.holdout if args.shelf else None, answers_per_question=args.answers)
    out["started"] = datetime.now().isoformat(timespec="seconds")
    sheets = []
    if "blind" in parts:
        out["blind"] = run_blind(args.url, books, args, system)
        write_sheet(args.label, out["blind"], args.shelf)
        sheets.append(RESULTS / f"hegeltest-{args.label}.html")
    if "bio" in parts:
        out["biography"] = run_bio(args.url, books, args, system)
    if "behaviour" in parts:
        out["behaviour"] = run_behaviour(args.url, books, args)
    if "cont" in parts:
        out["continuation"] = run_cont(args.url, args)
        write_sheet(f"{args.label}-cont", out["continuation"], False)
        sheets.append(RESULTS / f"hegeltest-{args.label}-cont.html")
    if "continuation" in out and parts & {"cont", "blind"}:       # (the chat answers of a new blind part change the contrast)
        st = out["continuation_style"] = continuation_style(out)
        d = st["delta"] or {}
        print(f"continuation {st['recited']}/{st['answers']} recited, {st['cut']} cut; Delta: model {d.get('model')}, real second halves {d.get('real')}, "
              f"chat answers {d.get('chat')} (lower is closer to his translators)")
    RESULTS.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {path}" + "".join(f" and {x}" for x in sheets))
    return 0


def judged(label):
    """The judgments for a label: [{judge, answered, hits}] from every mind/results/hegeltest-<label>-judged*.json, scored against the key."""
    key = RESULTS / f"hegeltest-{label}-key.json"
    if not key.exists():
        return []
    real = {q["id"]: q["real"] for q in json.loads(key.read_text(encoding="utf-8"))["questions"]}
    out = []
    for p in sorted(glob.glob(str(RESULTS / f"hegeltest-{label}-judged*.json"))):
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except ValueError:
            continue
        for j in d.get("judges", [d]) if isinstance(d, dict) else d:
            ch = {k: v for k, v in (j.get("choices") or {}).items() if k in real}
            out.append({"judge": j.get("judge", "anonymous"), "answered": len(ch), "hits": sum(v == real[k] for k, v in ch.items())})
    return out


def compare(labels):
    runs = {l: json.loads((RESULTS / f"hegeltest-{l}.json").read_text(encoding="utf-8")) for l in labels}
    lines = ["# The Hegel test: " + " vs ".join(labels), "",
             "Biography: questions about his life answered right, of 30, and the share of the single facts. Behaviour: the 20 bake-off situations through the live contract: valid JSON, "
             "answers the world's rules would refuse, answers with words from after 1831 that the situation did not give, and the average thought in words. "
             "Blind test: how often judges picked the real passage out of five (chance 20%; **lower is better**: the model sounds more like Hegel).", "",
             "| mind | shelf | biography | facts | valid JSON | refused | after 1831 | thought (words) | blind: real picked | judges |", "|---|---|---|---|---|---|---|---|---|---|"]
    for l, r in runs.items():
        b, h = r.get("biography"), r.get("behaviour")
        j = judged(l)
        n, hit = sum(x["answered"] for x in j), sum(x["hits"] for x in j)
        lines.append(f"| {l} | {'yes' if r.get('shelf') else 'no'} | " + (f"{b['right']}/{b['n']}" if b else "-") + " | " + (f"{b['partial'] * 100:.0f}%" if b else "-") + " | "
                     + (f"{h['valid']}/{h['n']}" if h else "-") + " | " + (str(h["refused"]) if h else "-") + " | " + (str(h["leaking"]) if h else "-") + " | "
                     + (str(h["thought_words"]) if h else "-") + " | " + (f"{hit}/{n} = {100 * hit / n:.0f}%" if n else "not yet judged") + " | "
                     + (", ".join(x["judge"] for x in j) if j else "-") + " |")
    lines += ["", "## Continuation", "",
              "The mind continues the first half of each of the 20 passages in plain completion mode; judges pick the real second half out of five (chance 20%; **lower is "
              "better**). Recited: continuations that share 8 words in a row with the real second half; cut: continuations without a sentence end near the right length, "
              "cut at the word. Delta: Burrows' Delta over the 150 commonest words against his English translators, **lower is closer**: of the continuations, of the real "
              "second halves (the floor) and of the chat answers of the blind part cut to the same length (for contrast).", "",
              "| mind | continuation: real picked | judges | recited | cut | Delta (model) | Delta (real halves) | Delta (chat answers) |", "|---|---|---|---|---|---|---|---|"]
    for l, r in runs.items():
        c, d = r.get("continuation"), ((r.get("continuation_style") or {}).get("delta") or {})
        j = judged(f"{l}-cont")
        n, hit = sum(x["answered"] for x in j), sum(x["hits"] for x in j)
        total = sum(len(x["answers"]) for x in c) if c else 0
        num = lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else "–"
        lines.append(f"| {l} | " + ((f"{hit}/{n} = {100 * hit / n:.0f}%" if n else "not yet judged") if c else "–") + " | " + (", ".join(x["judge"] for x in j) if c and j else "–") + " | "
                     + (f"{sum(sum(x['recited']) for x in c)}/{total}" if c else "–") + " | " + (f"{sum(sum(x['cut']) for x in c)}/{total}" if c else "–") + " | "
                     + num(d.get("model")) + " | " + num(d.get("real")) + " | " + num(d.get("chat")) + " |")
    lines += ["", "## Blind test by judge", ""]
    for l in runs:
        for x in judged(l):
            lines.append(f"- **{l}**, {x['judge']}: {x['hits']} real passages picked of {x['answered']} answered" + (f" ({100 * x['hits'] / x['answered']:.0f}%)" if x["answered"] else ""))
    if not any(judged(l) for l in runs):
        lines.append("Nobody has judged a sheet yet: open `mind/results/hegeltest-<label>.html`, choose, press Export judgments, and save the file as "
                     "`mind/results/hegeltest-<label>-judged.json` (one file per judge: `-judged.json`, `-judged-claude.json`).")
    judges = [(l, x) for l, r in runs.items() if r.get("continuation") for x in judged(f"{l}-cont")]
    if judges:
        lines += ["", "## Continuation by judge", ""] + [f"- **{l}**, {x['judge']}: {x['hits']} real second halves picked of {x['answered']} answered"
                                                        + (f" ({100 * x['hits'] / x['answered']:.0f}%)" if x["answered"] else "") for l, x in judges]
    for l, r in runs.items():
        wrong = [i for i in (r.get("biography") or {}).get("items", []) if not i["right"]]
        if wrong:
            lines += ["", f"## {l}: biography answers missed", ""] + [f"- {i['question']} Expected: {i['fact']}. Said: {i['reply'][:160]}" for i in wrong[:12]]
    (RESULTS / "hegeltest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {RESULTS / 'hegeltest.md'}")
    return 0


# ── a stand-in llama-server ─────────────────────────────────────────
PROSE = ["The state is not a machine laid over free persons; it is the actuality of freedom, in which the single will finds itself again in the universal. "
         "Whoever asks what it is for has not yet understood that it is its own end. The family gives feeling, civil society gives need, and only the state gives reason its home, "
         "so that what each man wills for himself and what the whole wills are one thing known as such. Take that away and you have a crowd with a ledger, not a people with a history. "
         "Nor is this a dream of the study: it is what has been working itself out through the centuries, and the philosopher only arrives, at dusk, to read it."]


STUB_PARTS = (["The state", "Every people", "Whoever doubts the family", "The understanding", "A right that is only claimed", "Art in its time", "The history of the world", "What is rational"],
              ["is not what it seems to the single will", "learns nothing from what it has itself made", "keeps its own law before it knows it", "mistakes the part for the whole",
               "finds itself again in what it has put aside", "waits on a necessity that it does not yet see", "needs the other to be itself", "stands in its own light"],
              ["and so the matter is not yet thought.", "though the habit of the age forbids it to say so.", "which is the work of centuries and not of a day.",
               "until it has gone out of itself and come back.", "for freedom is not the absence of every bond.", "as the beginning always holds the end in germ.",
               "and what is near is thus the furthest of all.", "so that nothing is lost but the form of it."])


def stub_continuation(body):
    """A paragraph of plain sentences for a /completion request, a different one for each prompt and seed, ending at the sentence end nearest the number
    of words that n_predict was sized for (n_predict is 2.5 times the real half's words)."""
    rng = random.Random(int(hashlib.sha1(f"{body['prompt']}|{body.get('seed')}".encode()).hexdigest()[:12], 16))
    sentences, sizes = [], []
    while not sizes or sizes[-1] < body.get("n_predict", 100) / 2.5 + 20:
        subject, verb, tail = (rng.choice(part) for part in STUB_PARTS)
        sentences.append(f"{subject} {verb}, {tail}")
        sizes.append(len(" ".join(sentences).split()))
    k = min(range(len(sizes)), key=lambda i: (abs(sizes[i] - body.get("n_predict", 100) / 2.5), i))
    return " " + " ".join(sentences[:k + 1])


class StubLlama(BaseHTTPRequestHandler):
    """A llama-server that answers like a stub: a valid decision for the contract's schema, the right fact for a question about his life,
    a paragraph of prose for the rest, and plain sentences for a /completion. For trying the tool and for the tests."""
    calls = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        StubLlama.calls.append(body)
        if self.path.endswith("/completion"):
            data = json.dumps({"content": stub_continuation(body), "stop": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        user = body["messages"][-1]["content"]
        if body.get("response_format"):
            place = (re.search(r"You are at: (\w+)\.", user) or [0, "home"])[1]
            open_now = re.search(r"Open now: ([^\n]+)\.", user)
            places = [re.match(r"\w+", x.strip())[0] for x in open_now[1].split(",")] if open_now else [place]
            text = json.dumps({"thought": "(stub) The day goes on, and the state of things asks to be thought.", "action": "stay",
                               "place": place if place in places else places[0], "minutes": 30, "says": None, "buys": [], "revision": None})
        elif "one or two sentences" in user:
            q = next((x for x in load("biography.json")["questions"] if x["question"] in user), None)
            text = f"I would say: {q['fact']}." if q else "I do not recall."
        else:
            text = PROSE[0] + " " + hashlib.sha1(f"{user}|{body.get('seed')}".encode()).hexdigest()[:6]      # a seed gives its own answer
        data = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", help="llama-server base URL, e.g. http://192.168.178.50:8081")
    p.add_argument("--label", help="name of this run: bonsai, bonsai-shelf, qwen ...")
    p.add_argument("--shelf", action="store_true", help="give the mind passages from his shelf with every question")
    p.add_argument("--holdout", choices=["family", "none"], default="family", help="blind test with the shelf: leave out the book of the real passage and its twin")
    p.add_argument("--only", help="comma-separated parts: blind, bio, behaviour, cont (a file already there keeps the others)")
    p.add_argument("--answers", type=int, default=ANSWERS, help="model answers per blind question and continuations per passage (default 4)")
    p.add_argument("--seed", type=int, default=1831)
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--compare", nargs="+", metavar="LABEL", help="write mind/results/hegeltest.md for these runs")
    p.add_argument("--export-ppl", metavar="DIR", help="write DIR/heldout.txt and DIR/seen.txt for llama-perplexity and print the commands")
    p.add_argument("--serve-stub", type=int, metavar="PORT", help="serve a stand-in llama-server on this port")
    a = p.parse_args()
    if a.serve_stub:
        print(f"stub llama-server on http://127.0.0.1:{a.serve_stub}")
        HTTPServer(("127.0.0.1", a.serve_stub), StubLlama).serve_forever()
        return 0
    if a.export_ppl:
        return export_ppl(a.export_ppl, a.seed)
    if a.compare:
        return compare(a.compare)
    if not a.url or not a.label:
        p.error("--url and --label are required (or --compare, --export-ppl or --serve-stub)")
    if a.only and not set(a.only.split(",")) <= set(PARTS):
        p.error(f"--only takes parts out of {', '.join(PARTS)}")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
