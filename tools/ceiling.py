#!/usr/bin/env python3
"""The ceiling test (pc/CEILING-TEST.md): where is the limit of what he writes about this century, in the pipeline, in the
model, or in the measure? Evaluation only.

    python3 tools/ceiling.py candidates --days <docs/days> --out F     # no GPU, no network: the mornings a brief can be made from
    python3 tools/ceiling.py texts --folder F                          # on the PC: Wikipedia's introduction for each brief
    python3 tools/ceiling.py requests --folder F --days <docs/days>    # no GPU: REQUESTS-ceiling-1.jsonl .. -3.jsonl

A brief is one of his real mornings, one headline he saw that morning, and one real text on what the headline is about
(F/BRIEFS.json, chosen by agents that never judge; F/TEXTS.json, fetched by `texts`). The morning is rebuilt by the engine's
own code: the state the day before ended in, `new_day`, and the waking situation, with that morning's own headlines, the plan
he made and the event as his record has it. A state is saved only at a day's end, so a waking is the one moment that can be
rebuilt exactly. The writing call is his own: his instructions, that situation, his own first decision of the morning, and
the live writing request with its manuscripts and its schema; one sentence names the headline as what he writes about.

Five arms, the same brief in each:
  A   as above.
  A2  the same with another seed: how far two runs of one arm lie apart (the band).
  B   adds the text, in the words a look-up reaches him with ("On your phone you read: ...").
  C   the fuller instructions (mind/soul.md) and a reasoning budget of 2,048 tokens.
  D   B and C.
A sixth, F, is D's messages answered by a cloud model; it is made in the cloud from the D requests.

The requests go to tools/run_requests.py: three files, one for each slot of the night. Replies are evaluation material and
never training data. Wikipedia's text is under CC BY-SA 4.0; TEXTS.json names each article and its link."""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from world import contract, lookup, works  # noqa: E402
from world.__main__ import make_world  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Days, Engine  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.task_prompt import for_task  # noqa: E402
from world.world import at_dt  # noqa: E402

ARMS = ("A", "A2", "B", "C", "D")
LIVE = {"HEGEL_SOUL_FILE": "mind/soul-ordinary.md", "HEGEL_CORRESPONDENT": "1", "HEGEL_STREET": "1", "HEGEL_RAMESH_DAYS": "1",
        "HEGEL_SHELF_ADDITIONS": "1", "HEGEL_WORLD_REPAIRS": "1", "HEGEL_CULTURE": "1", "HEGEL_KEEP_TIME": "1",
        "HEGEL_FILE_ACT": "1"}          # the switches the Pi runs on Day 55; the decision draws do not change a prompt
FULLER = "mind/soul.md"                 # arm C's instructions
BUDGET = 2048                           # arm C's reasoning budget, tokens
MAX_TOKENS, TEMPERATURE = 1100, 0.7     # his writing call's own
TEXT, MIN_TEXT = 1800, 600              # characters of the article's introduction that are shown; fewer than MIN_TEXT is no text
SHARDS = 3
PAPERS = "Morning papers"
FRAME = "This morning you sat down to write about one of the headlines in the papers: “{headline}”. "
LOOKED = "Before you wrote, you looked it up. On your phone you read: {title}. {text}\n\n"
WIKI = "https://en.wikipedia.org"


def rows(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def headlines(day):
    """The headlines of a day file's morning papers, as its record shows them."""
    e = next((e for e in day.get("entries", []) if e.get("k") == "world" and str(e.get("text", "")).startswith(PAPERS)), None)
    return re.findall(r"“([^”]+)”", e["text"]) if e else []


def load_day(days, d):
    p = Path(days) / f"{d}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def usable(days, d):
    """The day file of d if a brief can be made from its morning: it woke with headlines, and the day before left a state."""
    day, prev = load_day(days, d), load_day(days, date.fromisoformat(d) - timedelta(days=1))
    if not day or not prev or not prev.get("state") or not day.get("steps"):
        return None
    return day if str(day["steps"][0].get("event", "")).startswith("You wake") and headlines(day) else None


def cmd_candidates(days, out):
    found = []
    for p in sorted(Path(days).glob("????-??-??.json")):
        day = usable(days, p.stem)
        if day:
            found.append({"date": p.stem, "day": day.get("n"), "headlines": headlines(day)})
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CANDIDATES.json").write_text(json.dumps(found, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"mornings": len(found), "headlines": sum(len(x["headlines"]) for x in found)}


# ── the texts (on the PC: Wikipedia refuses the cloud's address) ────

def introduction(title, fetch=lookup.fetch):
    """{title, text, url} for the introduction of the English Wikipedia article `title`, or None when it has none."""
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1, "redirects": 1,
                                "format": "json", "titles": title})
    pages = ((fetch(f"{WIKI}/w/api.php?{q}") or {}).get("query") or {}).get("pages") or {}
    page = next((p for p in pages.values() if p.get("extract")), None)
    if not page:
        return None
    text = " ".join(str(page["extract"]).split())
    name = str(page.get("title") or title)
    return {"title": name, "text": works.cut(text, TEXT), "url": f"{WIKI}/wiki/{urllib.parse.quote(name.replace(' ', '_'))}"}


def cmd_texts(folder, fetch=lookup.fetch, pause=2.0):
    """TEXTS.json: for each brief the introduction of its article, or of its second choice. A brief without a text of MIN_TEXT
    characters is left out and named. What is there already is kept, so the command resumes."""
    folder = Path(folder)
    path = folder / "TEXTS.json"
    texts = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    missing = []
    for b in json.loads((folder / "BRIEFS.json").read_text(encoding="utf-8")):
        if b["id"] in texts:
            continue
        for which in ("wiki", "alt"):
            try:
                got = introduction(b[which], fetch)
            except OSError as e:
                got = None
                print(f"{b['id']} {which}: {e}", file=sys.stderr)
            if pause:
                time.sleep(pause)                         # one request at a time, with a pause, as Wikipedia asks
            if got and len(got["text"]) >= MIN_TEXT:
                texts[b["id"]] = dict(got, source="Wikipedia", licence="CC BY-SA 4.0", used=which)
                break
        else:
            missing.append(b["id"])
        path.write_text(json.dumps(texts, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return {"briefs": len(texts) + len(missing), "with_text": len(texts), "missing": missing}


# ── a morning, rebuilt ──────────────────────────────────────────────

class Capture(StubMind):
    """A stand-in mind that keeps the first situation it is asked to decide in."""
    def __init__(self):
        super().__init__()
        self.sit = None

    def decide(self, messages, sit):
        if self.sit is None:
            self.sit = copy.deepcopy(sit)
        return super().decide(messages, sit)


def waking(days, d, scratch):
    """(the situation of d's waking, the state he woke in, his manuscripts as a sitting is shown them, his first decision)."""
    live, when = load_day(days, d), date.fromisoformat(d)
    docs = Path(scratch) / "docs" / "days"
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir(parents=True)
    for p in Path(days).glob("????-??-??.json"):
        if p.stem < d:
            shutil.copy(p, docs / p.name)                 # he remembers only the days before this one
    index = Path(days) / "index.json"
    if index.exists():
        ix = json.loads(index.read_text(encoding="utf-8"))
        ix["days"] = [r for r in ix.get("days", []) if r["date"] < d]
        (docs / "index.json").write_text(json.dumps(ix), encoding="utf-8")
    state = Path(scratch) / "state"
    (state / "feeds").mkdir(parents=True, exist_ok=True)
    (state / "feeds" / f"news-{d}.json").write_text(json.dumps(headlines(live), ensure_ascii=False), encoding="utf-8")
    cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(state), "HEGEL_FEEDS": "0", "HEGEL_ENV": os.devnull, **LIVE})
    cfg.docs = docs.parent
    mind = Capture()
    engine = Engine(cfg, make_world(cfg), mind)
    day = engine.new_day(Days(cfg.docs).load(when - timedelta(days=1)), when)
    woke = copy.deepcopy(day["state"])
    first = live["steps"][0]
    plan = live.get("plan") if (live.get("plan") or {}).get("written", "99:99") <= first["t"] else None
    hh, mm = map(int, first["t"].split(":"))
    engine.step(day, at_dt(when, hh * 60 + mm))
    sit = mind.sit
    if sit is None:
        raise ValueError(f"{d}: the engine asked for no decision at {first['t']}")
    sit["on_mind"] = [x for x in sit["on_mind"] if not x.startswith("Your plan for today")]          # a stand-in's plan is not his
    if plan:
        day["plan"] = copy.deepcopy(plan)
        engine.world.show_plan(sit, day)                  # the plan he made that morning, where the engine puts it
    sit["event"] = first["event"]                         # as his record has it, with what was said to him
    m = re.match(r"Weather: (.*)\. Air quality index: (.*?)\.?$", (first.get("observations") or [""])[0])
    hours = (live.get("weather") or {}).get("hours") or []
    if m:
        sit["weather"], sit["aqi"] = m.group(1), m.group(2)
    elif len(hours) > hh:                                 # an older day file: the hour's weather as the day kept it
        sit["weather"], sit["aqi"] = f"{hours[hh]['temp']} °C, {hours[hh]['sky']}", str(hours[hh].get("aqi", sit["aqi"]))
    manuscripts = engine.memory.manuscripts(day, before_time=first["t"])
    return sit, woke, manuscripts, first["decision"]


def seed_of(brief_id):
    return int(hashlib.sha256(f"ceiling|{brief_id}".encode()).hexdigest(), 16) % (2 ** 31 - 2)


def messages_of(arm, sit, woke, manuscripts, decision, brief, text, souls):
    """The writing call of one arm: his own, with the brief's frame before the request."""
    ask = FRAME.format(headline=brief["headline"])
    if arm in ("B", "D"):
        ask += LOOKED.format(title=text["title"], text=text["text"])
    ask += works.ask(woke, date.fromisoformat(brief["date"]))
    if manuscripts:
        ask += "\n\n" + manuscripts
    base = [{"role": "system", "content": souls["fuller" if arm in ("C", "D") else "live"]},
            {"role": "user", "content": contract.render(sit)},
            {"role": "assistant", "content": json.dumps(decision, ensure_ascii=False)},
            {"role": "user", "content": ask}]
    return for_task(base, "writing")


def params_of(arm, brief_id):
    p = {"seed": seed_of(brief_id) + (1 if arm == "A2" else 0), "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "cache_prompt": False}
    if arm in ("C", "D"):
        p.update(max_tokens=MAX_TOKENS + BUDGET, reasoning_budget_tokens=BUDGET)
    return p


def cmd_requests(folder, days, scratch=None):
    """REQUESTS-ceiling-<n>.jsonl, one file a slot, each with whole briefs (five arms a brief), and MANIFEST.json."""
    folder = Path(folder)
    briefs = json.loads((folder / "BRIEFS.json").read_text(encoding="utf-8"))
    texts = json.loads((folder / "TEXTS.json").read_text(encoding="utf-8"))
    souls = {"live": (REPO / LIVE["HEGEL_SOUL_FILE"]).read_text(encoding="utf-8"), "fuller": (REPO / FULLER).read_text(encoding="utf-8")}
    used = [b for b in briefs if b["id"] in texts]
    for b in used:
        day = usable(days, b["date"])
        if not day or b["headline"] not in headlines(day):
            raise ValueError(f"{b['id']}: {b['date']} has no such morning or headline")
    own = scratch is None
    scratch = Path(scratch or tempfile.mkdtemp(prefix="ceiling-"))
    shards, mornings = [[] for _ in range(SHARDS)], {}
    try:
        for i, b in enumerate(used):
            if b["date"] not in mornings:
                mornings[b["date"]] = waking(days, b["date"], scratch)
            sit, woke, manuscripts, decision = mornings[b["date"]]
            for arm in ARMS:
                shards[i % SHARDS].append({"id": f"{arm}|{b['id']}", "schema": contract.WRITE_SCHEMA, "params": params_of(arm, b["id"]),
                                           "messages": messages_of(arm, sit, woke, manuscripts, decision, b, texts[b["id"]], souls)})
    finally:
        if own:
            shutil.rmtree(scratch, ignore_errors=True)
    files = {}
    for n, shard in enumerate(shards, 1):
        p = folder / f"REQUESTS-ceiling-{n}.jsonl"
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in shard), encoding="utf-8")
        files[p.name] = {"requests": len(shard), "sha256": sha(p)}
    manifest = {"briefs": len(used), "left_out_for_no_text": sorted(b["id"] for b in briefs if b["id"] not in texts), "arms": list(ARMS),
                "requests": sum(f["requests"] for f in files.values()), "files": files,
                "sha256": {"BRIEFS.json": sha(folder / "BRIEFS.json"), "TEXTS.json": sha(folder / "TEXTS.json"),
                           LIVE["HEGEL_SOUL_FILE"]: sha(REPO / LIVE["HEGEL_SOUL_FILE"]), FULLER: sha(REPO / FULLER)},
                "switches": LIVE, "reasoning_budget_tokens": BUDGET, "max_tokens": MAX_TOKENS, "temperature": TEMPERATURE,
                "training_eligible": False}
    (folder / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("candidates")
    c.add_argument("--days", required=True)
    c.add_argument("--out", required=True)
    t = sub.add_parser("texts")
    t.add_argument("--folder", required=True)
    r = sub.add_parser("requests")
    r.add_argument("--folder", required=True)
    r.add_argument("--days", required=True)
    a = ap.parse_args(argv)
    res = cmd_candidates(a.days, a.out) if a.cmd == "candidates" else cmd_texts(a.folder) if a.cmd == "texts" else cmd_requests(a.folder, a.days)
    print(json.dumps({k: v for k, v in res.items() if k != "switches"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
