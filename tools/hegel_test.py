#!/usr/bin/env python3
"""Hegel in Delhi: the Hegel test. The yardstick that decides between Bonsai, Qwen and a trained model.

    python3 tools/hegel_test.py --url http://PC:8081 --label bonsai            # the three parts, without the shelf
    python3 tools/hegel_test.py --url http://PC:8081 --label bonsai-shelf --shelf
    python3 tools/hegel_test.py --compare bonsai bonsai-shelf qwen             # writes mind/results/hegeltest.md
    python3 tools/hegel_test.py --serve-stub 8099                              # a stand-in llama-server, to try the tool

Three parts. (a) Blind passages, after Schwitzgebel et al.: 20 questions that Hegel answered in his own texts; the mind answers
each four times as Hegel, and the sheet mind/results/hegeltest-<label>.html shows five answers (one is the real passage, from a
19th-century translation) in shuffled order to judges, who choose; the score is how often they pick the real one (chance is 20%,
lower means the model sounds more like Hegel). (b) Thirty questions about his life, scored by tolerant matching. (c) The 20 test
situations of the bake-off through the live contract: valid JSON, what the world would refuse, words of after 1831, thought length.
With --shelf the mind gets passages from his shelf with every question; in the blind test the book the real passage comes from
(and its German or English twin) is held out, so the shelf cannot hand over the answer. Standard library only."""
import argparse
import glob
import hashlib
import html
import json
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "mind"))
import bakeoff  # noqa: E402  (the 20 test situations and the one way of asking the mind)
from world import contract, shelf  # noqa: E402
from world.world import wordlist  # noqa: E402

DATA, RESULTS = REPO / "mind/hegeltest", REPO / "mind/results"
ANSWERS, TEMPERATURE, WORDS = 4, 0.9, (80, 140)
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


def sheet_data(label, blind):
    """The questions of the sheet, five answers each in shuffled order, and the key: {title, questions: [...]}, key: [...]."""
    qs, key = [], []
    by_id = {q["id"]: q for q in load("questions.json")["questions"]}
    for b in blind:
        q = by_id[b["id"]]
        pool = b["answers"] + [q["passage"]]                    # the real one last, then shuffled
        pos = order_for(label, q["id"], len(b["answers"]))
        letters = "ABCDEFGH"[:len(pool)]
        shown = [pool[i] for i in pos]
        real = letters[pos.index(len(pool) - 1)]
        qs.append({"id": q["id"], "topic": q["topic"], "question": q["question"], "options": dict(zip(letters, shown)), "real": real,
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
.verdict{margin:8px 0 0}.hit{color:var(--ok)}.miss{color:var(--no)}.sticky{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:1}
</style></head><body>
<header>
<h1>Which one is Hegel?</h1>
<p class="muted">Candidate: <b>__LABEL__</b>__SHELF__. Twenty questions that Hegel answered in his own books and lectures. Each has five answers: one is the real passage from a nineteenth-century English translation, four were written by the model as Hegel. Pick the one you think is real. Chance is one in five: the lower the judges' hit rate, the more the model sounds like him. Some passages hold his nineteenth-century views as he lectured them, unsoftened.</p>
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
  document.getElementById('qs').innerHTML = DATA.map((q, n) => `<section class="card" id="c-${q.id}"><h2>${n + 1}. ${esc(q.topic)}</h2><p><i>${esc(q.question)}</i></p>`
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


def write_sheet(label, blind, shelf_on):
    qs, key = sheet_data(label, blind)
    data = json.dumps(qs, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    page = (SHEET.replace("__LABEL_JSON__", json.dumps(label)).replace("__RUN__", hashlib.sha1(data.encode()).hexdigest()[:8]).replace("__LABEL__", html.escape(label))
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


# ── the run, and the comparison ─────────────────────────────────────
def run(args):
    books, system = Books(args.shelf), voice()
    out = {"label": args.label, "url": args.url, "started": datetime.now().isoformat(timespec="seconds"), "shelf": bool(args.shelf),
           "holdout": args.holdout if args.shelf else None, "answers_per_question": args.answers}
    parts = set(args.only.split(",")) if args.only else {"blind", "bio", "behaviour"}
    if "blind" in parts:
        out["blind"] = run_blind(args.url, books, args, system)
        write_sheet(args.label, out["blind"], args.shelf)
    if "bio" in parts:
        out["biography"] = run_bio(args.url, books, args, system)
    if "behaviour" in parts:
        out["behaviour"] = run_behaviour(args.url, books, args)
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"hegeltest-{args.label}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {path}" + (f" and {RESULTS / ('hegeltest-' + args.label + '.html')}" if "blind" in out else ""))
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
    lines += ["", "## Blind test by judge", ""]
    for l in runs:
        for x in judged(l):
            lines.append(f"- **{l}**, {x['judge']}: {x['hits']} real passages picked of {x['answered']} answered" + (f" ({100 * x['hits'] / x['answered']:.0f}%)" if x["answered"] else ""))
    if not any(judged(l) for l in runs):
        lines.append("Nobody has judged a sheet yet: open `mind/results/hegeltest-<label>.html`, choose, press Export judgments, and save the file as "
                     "`mind/results/hegeltest-<label>-judged.json` (one file per judge: `-judged.json`, `-judged-claude.json`).")
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


class StubLlama(BaseHTTPRequestHandler):
    """A llama-server that answers like a stub: a valid decision for the contract's schema, the right fact for a question about his life,
    and a paragraph of prose for the rest. For trying the tool and for the tests."""
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
    p.add_argument("--only", help="comma-separated parts: blind, bio, behaviour")
    p.add_argument("--answers", type=int, default=ANSWERS, help="model answers per blind question (default 4)")
    p.add_argument("--seed", type=int, default=1831)
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--compare", nargs="+", metavar="LABEL", help="write mind/results/hegeltest.md for these runs")
    p.add_argument("--serve-stub", type=int, metavar="PORT", help="serve a stand-in llama-server on this port")
    a = p.parse_args()
    if a.serve_stub:
        print(f"stub llama-server on http://127.0.0.1:{a.serve_stub}")
        HTTPServer(("127.0.0.1", a.serve_stub), StubLlama).serve_forever()
        return 0
    if a.compare:
        return compare(a.compare)
    if not a.url or not a.label:
        p.error("--url and --label are required (or --compare, or --serve-stub)")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
