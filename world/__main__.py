"""Hegel in Delhi: the world engine.

    python3 -m world start --date 2026-10-07   # the first live day begins at that midnight
    python3 -m world tick                 # run by the timer every minute: keep the day 15 minutes ahead
    python3 -m world status               # where he is, what was last decided, whether the mind answers
    python3 -m world simulate --date 2026-10-03            # rehearse a whole day offline (stand-in mind)
    python3 -m world simulate --date 2026-10-03 --mind URL # the same day with the real mind, nothing pushed
    python3 -m world owl --date 2026-10-03                 # write up a finished day now
    python3 -m world check                # sanity-check the world's data and the day files
    python3 -m world report [DATE [DATE]] # the scoreboard row of a day or a range (--table, --json)
    python3 -m world wishes [--since DATE] # what he said he wished the city had (HEGEL_WANTS), by day
"""
import argparse
import fcntl
import json
import logging
import logging.handlers
import re
import shutil
import sys
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from . import health, nightly_report, pause, report, shelf, street, works
from .clock import fmt, minute_of, now_ist, parse_now
from .config import Config
from .engine import Days, Engine, until_of
from .feeds import Feeds
from .mind import STAND_INS, HTTPMind, StubMind
from .publish import Git, GitError
from .world import World, at_dt

log = logging.getLogger("world")


def setup_logging(cfg, verbose):
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    log.addHandler(h)
    try:
        cfg.state.mkdir(parents=True, exist_ok=True)
        f = logging.handlers.RotatingFileHandler(cfg.state / "world.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        f.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(f)
    except OSError:
        pass


def make_mind(cfg, which, wake=True):
    if which in STAND_INS:
        return STAND_INS[which]()
    if which and which.startswith("stub:"):
        sys.exit(f"no such stand-in {which!r}: stub, {', '.join(k for k in STAND_INS if k != 'stub')}")
    url = cfg.mind_url if which in (None, "pc") else which
    if not url:
        sys.exit("no mind configured: set PC_HOST (and MIND_PORT) in ~/.config/hegel/env, or pass --mind URL or --mind stub")
    return HTTPMind(url, wake=cfg.wake if wake else None, timeout=cfg.timeout, voice_adapter_scale=cfg.voice_adapter_scale,
                    writing_reasoning_tokens=cfg.writing_reasoning_tokens, writing_adapter_scale=cfg.writing_adapter_scale,
                    decision_reasoning_tokens=cfg.decision_reasoning_tokens, decision_adapter_scale=cfg.decision_adapter_scale,
                    decision_dry=getattr(cfg, "decision_dry", 0.0), seed=getattr(cfg, "seed", None), cache_prompt=getattr(cfg, "cache_prompt", None),
                    seed_streams=getattr(cfg, "seed_streams", False))


def make_world(cfg):
    """The world as the tick builds it, and as a rehearsal builds it: what the Config switches on (the culture) is on in both."""
    return World(Feeds(cfg), culture=getattr(cfg, "culture", False), street_on=getattr(cfg, "street", False),
                 street_file=getattr(cfg, "street_file", None), promises=getattr(cfg, "promises", False),
                 ramesh_days=getattr(cfg, "ramesh_days", False), consumed=getattr(cfg, "consumed", False),
                 file_act=getattr(cfg, "file_act", False), repairs=getattr(cfg, "world_repairs", False),
                 keep_time=getattr(cfg, "keep_time", False), talk_scene=getattr(cfg, "talk_scene", False),
                 papers=getattr(cfg, "papers", False), exits=getattr(cfg, "exits", False),
                 borrowed_lookup=getattr(cfg, "borrowed_lookup", False))


def cmd_tick(cfg, args):
    cfg.state.mkdir(parents=True, exist_ok=True)
    lock = open(cfg.state / "tick.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.debug("another tick is running")
        return 0
    now = parse_now(args.now) if args.now else now_ist(getattr(cfg, "clock_shift_min", 0))
    mind = make_mind(cfg, args.mind)
    owl_mind = mind if args.mind in STAND_INS or not cfg.owl_url or cfg.owl_url == cfg.mind_url else HTTPMind(cfg.owl_url, wake=cfg.wake, timeout=cfg.timeout)
    engine = Engine(cfg, make_world(cfg), mind, git=Git(cfg) if not args.no_git else None, owl_mind=owl_mind)
    if getattr(cfg, "pause_away", False) and not args.now:
        now = pause.gate(cfg, engine, mind, now_ist(cfg.base_shift_min))       # None while his world is held
        if now is None:
            return 0
    engine.tick(now)
    if engine.git:
        try:
            nightly_report.publish_yesterday(cfg, now, engine.git)
        except (OSError, ValueError, nightly_report.ReportError, GitError) as exc:
            log.error("nightly report failed; will retry next tick: %s", exc)
            return 1
    return 0


def cmd_start(cfg, args):
    """Schedule the first live day: the world stays quiet until that midnight, then begins cleanly."""
    d = date.fromisoformat(args.date) if args.date else now_ist(getattr(cfg, "clock_shift_min", 0)).date() + timedelta(days=1)
    days = Days(cfg.docs)
    day = days.latest()
    if day["date"] >= d.isoformat():
        sys.exit(f"there is already a day file for {day['date']}; start must be later")
    if until_of(day) > at_dt(d, 0):
        sys.exit(f"day {day['n']} runs past {d}; nothing to schedule")
    day["state"]["until"] = at_dt(d, 0).isoformat(timespec="minutes")
    day["state"]["asleep"] = True
    days.save(day)
    print(f"the first live day is {d} (day {(d - date(2026, 10, 2)).days + 1}); the world begins at its midnight, carrying on from day {day['n']}")
    if not args.no_git:
        Git(cfg).publish([days.path(day["date"]), days.dir / "index.json"], f"The world begins on {d}")
    return 0


def cmd_status(cfg, args):
    days = Days(cfg.docs)
    now = now_ist(getattr(cfg, "clock_shift_min", 0))
    day = days.latest(now.date() + timedelta(days=1))
    if not day:
        print("no day files")
        return 1
    st = day["state"]
    until = until_of(day)
    ahead = (until - now).total_seconds() / 60
    # The handwritten prologue predates engine decision steps.
    steps = [s for s in day.get("steps", []) if "decision" in s]
    last = steps[-1] if steps else None
    print(f"Delhi now      {now:%Y-%m-%d %H:%M}")
    print(f"latest day     {day['n']} ({day['date']}), {len(steps)} steps, complete: {day.get('complete', False)}")
    print(f"published to   {until:%Y-%m-%d %H:%M} ({ahead:+.0f} min)" + ("  ← behind" if ahead < 0 else ""))
    print(f"he is          {'asleep' if st.get('asleep') else 'awake'}, place {st['place']}, cash ₹{st['imprest']:,}")
    print(f"the file       {st.get('file')}")
    if last:
        d, m = last["decision"], last.get("mind", {})
        print(f"last step      {last['t']}–{last['end']} {d['action']} → {d['place']} ({m.get('source')}, {m.get('latency_s')}s, {m.get('attempts')} tries)")
    away = sum(1 for s in steps if s.get("mind", {}).get("source") in ("away", "quiet"))
    print(f"quiet steps    {away} today (mind away or refused three times)")
    print("refusals       " + refusal_line(steps))
    if cfg.mind_url:
        print(f"mind           {cfg.mind_url}: {'answers' if HTTPMind(cfg.mind_url).health() else 'asleep or away'}")
    return 0


def cmd_report(cfg, args):
    """The scoreboard row of the latest day, of one day, or of every day in a range."""
    days = Days(Path(args.docs) if args.docs else cfg.docs)
    index = [r["date"] for r in days.index()["days"]]
    if not args.dates:
        picked = index[-1:]
    else:
        first, last = args.dates[0], args.dates[-1]
        picked = [d for d in index if first <= d <= last]
    loaded = [day for day in (days.load(d) for d in picked) if day]
    if len(loaded) > 1:
        loaded = [day for day in loaded if any("decision" in s for s in day.get("steps", []))]   # not the handwritten prologue
    if not loaded:
        print("no day files")
        return 1
    if args.health:
        return health_report(days, index, picked, args.json, args.floor)
    rows = [report.row(day) for day in loaded]
    if args.json:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
    elif args.table:
        print(report.table(rows))
    else:
        print("\n\n".join(report.text(r) for r in rows))
    return 0


def cmd_wishes(cfg, args):
    """The wishes written down on the days (day["wishes"]), by day, for Welt; then how many, among how many decisions."""
    days = Days(Path(args.docs) if args.docs else cfg.docs)
    wishes = decisions = 0
    for r in days.index()["days"]:
        if args.since and r["date"] < args.since:
            continue
        day = days.load(r["date"])
        if not day:
            continue
        decisions += sum(1 for s in day.get("steps", []) if "decision" in s)
        if day.get("wishes"):
            print(f"{day['date']}  day {day['n']}")
            for w in day["wishes"]:
                print(f"  {w['t']}  {w['place']}  {w['text']}")
            wishes += len(day["wishes"])
    print(f"{wishes} wishes in {decisions} decisions")
    return 0


def health_report(days, index, picked, as_json, floor=report.FLOOR):
    """What the world gave him on the picked days (world/health.py): a line a full day. The days before them are read too,
    so that a day can say how far it lies from the one before and how much of it earlier days already had."""
    upto = [d for d in index if d <= picked[-1]]
    rows = health.across([health.row(day, floor=floor) for day in (days.load(d) for d in upto) if day])
    rows = [r for r in rows if r["date"] in picked]
    if not rows:
        print(f"no full day among them: a day counts from {floor} thoughts (--floor N for a stand-in's shorter days)")
        return 0
    if as_json:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
    else:
        print(health.table(rows))
    return 0


LOOP_REFUSALS = 4      # the same refusal this often in one day is a loop: a rule that says no and offers nothing else


def refusal_line(steps):
    """How often the world refused his choices today, and the refusal that came most often. A refusal repeated LOOP_REFUSALS
    times is flagged: on Day 12 'no household meal is available now' came back all afternoon and nothing else showed it."""
    said = [e for s in steps if s.get("mind", {}).get("source") != "away"       # an away step's note is the outage, not a refusal
            for tries in s.get("mind", {}).get("refused", []) for e in tries
            if isinstance(e, str) and not e.startswith("the PC did not wake")]
    if not said:
        return "0 today"
    kind = lambda e: re.sub(r"\d+", "#", e.split(";")[0].split(". ")[0]).strip()[:80]
    top, n = Counter(kind(e) for e in said).most_common(1)[0]
    return f"{len(said)} today; most often ({n}×): {top}" + ("  ← a loop?" if n >= LOOP_REFUSALS else "")


PINNED = ("HEGEL_PUSH", "HEGEL_STATE", "HEGEL_PAUSE_AWAY")      # a rehearsal never pushes, keeps its state in its own folder, and is never held


def parse_sets(items, seed=None):
    """`--set KEY=VALUE` (repeated) as a dict of HEGEL_ switches for the rehearsal's Config; `--seed N` is HEGEL_SEED=N."""
    sets = {}
    for item in items or []:
        key, eq, value = item.partition("=")
        key = key.strip()
        if not eq or not key.startswith("HEGEL_") or not key.isupper():
            sys.exit(f"--set wants HEGEL_KEY=VALUE, not {item!r}")
        if key in PINNED:
            sys.exit(f"--set {key}: a rehearsal keeps that off or fixed")
        sets[key] = value.strip()
    if seed is not None:
        sets["HEGEL_SEED"] = str(seed)
    return sets


def seeded_sets(cfg, args):
    """The rehearsal's --set switches, and the notice to print before its days (or None). With --seed and a real mind, the prompt cache is off
    unless the rehearsal's settings (--set, the environment, the env file) name HEGEL_CACHE_PROMPT themselves: a reply depends on how much of the
    prompt the server took from its cache, so with it on the same seed is not the same day."""
    sets = parse_sets(args.set, args.seed)
    which = args.mind or "stub"
    if args.seed is None or which in STAND_INS or which.startswith("stub") or "HEGEL_CACHE_PROMPT" in sets or str(cfg.values.get("HEGEL_CACHE_PROMPT", "")).strip():
        return sets, None
    sets["HEGEL_CACHE_PROMPT"] = "0"
    return sets, (f"seed {args.seed}: the prompt cache is off for this rehearsal, so that the same seed is the same day "
                  "(HEGEL_CACHE_PROMPT=1 to keep it on)")


def rehearsal_config(out, feeds=False, sets=None):
    """The Config of a rehearsal folder: nothing is pushed, the state lives under out/state, the feeds are off unless asked for, his world is never
    held (pause), and `sets` (HEGEL_ switches) are applied on top of what the env file and the environment give."""
    sim = Config({"HEGEL_FEEDS": "1" if feeds else "0", **(sets or {}), "HEGEL_PUSH": "0", "HEGEL_STATE": str(out / "state"), "HEGEL_PAUSE_AWAY": "0"})
    sim.docs = out
    return sim


def rehearsal_setup(cfg, date_str, out, feeds=False, sets=None, docs=None):
    """Make `out` a scratch copy of the day files before date_str (and the page), and return the Config that writes there: nothing is
    pushed, its state lives under out/state. `simulate` and tools/train_data.py both rehearse in such a folder.
    `docs` is another rehearsal's folder to start from instead of the repo's docs (a fork): its day files, and the caches under its state
    (lookup/ and feeds/: a page he once looked up must read the same in the fork, not be fetched again)."""
    src_root = Path(docs).resolve() if docs else cfg.docs
    if docs and src_root == out:
        sys.exit("--docs and --out are the same folder: a fork needs a folder of its own")
    (out / "days").mkdir(parents=True, exist_ok=True)
    src = Days(src_root)
    prev = [r for r in src.index()["days"] if r["date"] < date_str]
    if not prev:
        sys.exit("a rehearsal needs an earlier day in docs/days to start from")
    for old in (out / "days").glob("????-??-??.json"):       # a day left by an earlier run into this folder must not be taken for the continuation
        if old.stem >= date_str:
            old.unlink()
    for r in prev:
        shutil.copy(src.path(r["date"]), out / "days" / f"{r['date']}.json")
    (out / "days/index.json").write_text(json.dumps({"format": 1, "days": prev}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if (src_root / "index.html").exists():
        shutil.copy(src_root / "index.html", out / "index.html")
    elif (cfg.docs / "index.html").exists():
        shutil.copy(cfg.docs / "index.html", out / "index.html")
    if docs:
        for sub in ("lookup", "feeds"):
            if (src_root / "state" / sub).is_dir():
                shutil.copytree(src_root / "state" / sub, out / "state" / sub, dirs_exist_ok=True)
    if (sets or {}).get("HEGEL_PAPERS_ARCHIVE") or cfg.get("HEGEL_PAPERS_ARCHIVE"):
        sets = {**(sets or {}), "HEGEL_PAPERS_FROM": date_str}       # the archive's papers cycle from the rehearsal's first day
    return rehearsal_config(out, feeds, sets)


def rehearse_day(engine, sim, out, d):
    """One day of a rehearsal, then the owl, as the single-day simulate always did it; the day as written."""
    now, end = at_dt(d, 0), at_dt(d, 1440)
    while now < end:
        engine.advance(now)
        now += timedelta(minutes=5)
    owl_day = Days(out).load(d)
    owl_day["complete"] = True
    Days(out).save(owl_day)
    engine.run_owl(owl_day, at_dt(d + timedelta(days=1), minute_of(at_dt(d, 0)) + 90))
    return Days(out).load(d)


def summary_line(day):
    steps = [s for s in day["steps"] if "decision" in s]
    srcs = {}
    for s in steps:
        srcs[s["mind"]["source"]] = srcs.get(s["mind"]["source"], 0) + 1
    refused = sum(len(s["mind"].get("refused", [])) for s in steps)
    return (f"day {day['n']} ({day['date']}): {len(steps)} steps, {len(day['segments'])} segments, {len(day['entries'])} entries; "
            f"by {srcs}; {refused} refusals; cash ₹{day['state']['imprest']:,}")


def cmd_simulate(cfg, args):
    t0 = time.time()
    d = date.fromisoformat(args.date)
    out = Path(args.out).resolve()
    sets, notice = seeded_sets(cfg, args)
    sim = rehearsal_setup(cfg, args.date, out, args.feeds, sets, args.docs)
    world = make_world(sim)
    mind = make_mind(sim, args.mind or "stub", wake=args.wake)
    engine = Engine(sim, world, mind, git=None)
    if notice:
        print(notice)
    last = Days(out).latest()
    if until_of(last).date() < d:          # a gap before the rehearsed day: start it fresh at midnight
        last["state"]["until"] = at_dt(d, 0).isoformat(timespec="minutes")
    for i in range(max(1, args.days)):      # one folder, one engine, one mind: each day starts from what the one before left
        day = rehearse_day(engine, sim, out, d + timedelta(days=i))
        print(summary_line(day))
    print(f"wrote {out}/days/{day['date']}.json  (serve {out} and open index.html#{day['date']} to watch it)")
    print(f"{max(1, args.days)} day(s) in {time.time() - t0:.1f}s")
    return 0


def cmd_owl(cfg, args):
    days = Days(cfg.docs)
    day = days.load(args.date)
    if not day:
        sys.exit(f"no day file for {args.date}")
    mind = make_mind(cfg, args.mind) if args.mind or not cfg.owl_url else HTTPMind(cfg.owl_url, wake=cfg.wake, timeout=cfg.timeout)
    engine = Engine(cfg, World(), mind, git=None if args.no_git else Git(cfg), owl_mind=mind)
    changed = engine.run_owl(day, now_ist(getattr(cfg, "clock_shift_min", 0)))
    if engine.git:
        engine.git.publish([days.path(x) for x in dict.fromkeys(changed)] + [days.dir / "index.json"], f"Day {day['n']}: the owl's write-up")
    return 0


def economy_problems(w):
    """What is wrong with the costs and the offers: places, people and beats that do not exist."""
    out, beats = [], {b["id"] for b in w.beats}
    for c in w.costs:
        if c.get("at") and c["at"] not in w.places:
            out.append(f"cost {c['id']}: unknown place {c['at']}")
        if c.get("with") and c["with"] not in w.cast:
            out.append(f"cost {c['id']}: unknown cast {c['with']}")
        if not {"weekday", "monthday", "every"} & set(c["when"]):
            out.append(f"cost {c['id']}: no rule for when it falls due")
    for b in w.beats:
        for spec in [b] + [x for x in (b.get("choice") or {}).values() if isinstance(x, dict)]:
            for key in ("pay", "cheque", "sell", "schedule", "owe"):
                x = spec.get(key) or {}
                for ref, known in (("at", w.places), ("with", w.cast), ("beat", beats)):
                    if x.get(ref) and x[ref] not in known:
                        out.append(f"beat {b['id']}: {key} refers to unknown {ref} {x[ref]}")
        for cond in (b.get("when") or {}).get("met_days", {}), (b.get("when") or {}).get("visits", {}):
            for k in cond:
                if k not in w.cast and k not in w.places:
                    out.append(f"beat {b['id']}: unknown {k} in its conditions")
    return out


def cmd_check(cfg, args):
    w = World()
    problems = [f"missing {f}" for f in ("mind/soul.md", "mind/owl.md", "mind/voices.md", "world/data/sensitive.txt", "mind/shelf/index.json.gz",
                                         "world/data/shelf_terms.json", works.QUESTIONS) if not (cfg.repo / f).exists()]
    try:
        if (cfg.repo / "mind/shelf/index.json.gz").exists() and not shelf.load(cfg.repo / "mind/shelf/index.json.gz", cfg.repo / "world/data/shelf_terms.json"):
            problems.append("the shelf index cannot be read")
    except (OSError, ValueError, KeyError) as e:
        problems.append(f"the shelf index is damaged: {e}")
    ids = list(w.places)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            try:
                w.walk(a, b)
            except KeyError:
                problems.append(f"no walking time {a}-{b}")
    for cid, c in w.cast.items():
        for x in c["where"]:
            if x["place"] not in w.places:
                problems.append(f"{cid}: unknown place {x['place']}")
    for b in w.beats:
        for c in b.get("needs", []) + b.get("brings", []):
            if c not in w.cast:
                problems.append(f"beat {b['id']}: unknown cast {c}")
        for v in (b.get("variants") or {}).values():
            for c in v.get("needs", []):
                if c not in w.cast:
                    problems.append(f"beat {b['id']}: unknown cast {c}")
        if b.get("where") and b["where"] not in w.places:
            problems.append(f"beat {b['id']}: unknown place {b['where']}")
        for x in b.get("after", []) + [b.get("missed"), b.get("if_missed"), (b.get("appointment") or {}).get("beat")]:
            if x and x not in {y["id"] for y in w.beats}:
                problems.append(f"beat {b['id']}: unknown beat {x}")
    problems += economy_problems(w)
    deck = Path(getattr(cfg, "street_file", None) or street.DECK)
    if deck.exists():                                 # the street deck, when there is one: the linter's own rules (tools/street_lint.py)
        every = {**w.places, **json.loads((street.DATA / "culture.json").read_text(encoding="utf-8"))["places"]}
        bad, _ = street.check_file(deck, every)       # its warnings (a name to look at) are for tools/street_lint.py, not for this check
        problems += [f"street: {x}" for x in bad]
    days = Days(cfg.docs)
    for r in days.index()["days"]:
        day = days.load(r["date"])
        if not day:
            problems.append(f"index lists {r['date']} but the file is missing")
            continue
        last = 0
        for s in day["segments"]:
            a, b = int(s["from"][:2]) * 60 + int(s["from"][3:]), int(s["to"][:2]) * 60 + int(s["to"][3:])
            if a < last or b <= a:
                problems.append(f"{r['date']}: segment {s['from']}–{s['to']} out of order")
            last = b
            for p in (s.get("at"), s.get("a"), s.get("b")):
                if p and p not in w.places:
                    problems.append(f"{r['date']}: unknown place {p}")
        if day["segments"] and day["segments"][0]["from"] != "00:00":
            problems.append(f"{r['date']}: first segment does not start at 00:00")
        if "cash" in day["opening"]:                 # from the economy on, the entries add up to the cash he ends the day with
            cash = day["opening"]["cash"] + sum(e["amount"] for e in day["entries"] if e["k"] == "income" and not e.get("cheque")) \
                - sum(e["price"] for e in day["entries"] if e["k"] == "bag") - sum(e["amount"] for e in day["entries"] if e["k"] == "expense")
            if cash != day["state"]["imprest"]:
                problems.append(f"{r['date']}: the entries leave ₹{cash:,} but the state says ₹{day['state']['imprest']:,}")
        manuscripts = {x["id"] for x in day["state"].get("works", [])}
        for e in day["entries"]:
            if e.get("sensitive") and not e.get("why"):
                problems.append(f"{r['date']}: the sensitive entry at {e['t']} has no reason")
            if e["k"] == "writing" and e.get("work") not in manuscripts:
                problems.append(f"{r['date']}: the writing at {e['t']} is in no manuscript")
    for p in problems:
        print("✗", p)
    print("ok" if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


def main():
    p = argparse.ArgumentParser(prog="python3 -m world", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tick", help="advance the world and publish")
    t.add_argument("--now", help="pretend it is this Delhi time, e.g. 2026-10-03T06:00 (testing)")
    t.add_argument("--mind", help="'stub' for the stand-in, or a llama-server URL (default: the PC from the env file)")
    t.add_argument("--no-git", action="store_true", help="write files but do not commit or push")
    st = sub.add_parser("start", help="schedule the first live day at a midnight")
    st.add_argument("--date", help="the first live day (default: tomorrow)")
    st.add_argument("--no-git", action="store_true")
    sub.add_parser("status", help="show where things stand")
    s = sub.add_parser("simulate", help="rehearse a whole day into a scratch folder; nothing is committed")
    s.add_argument("--date", required=True)
    s.add_argument("--mind", help="'stub' (default), 'stub:no', 'stub:home', 'stub:walker', or a llama-server URL")
    s.add_argument("--wake", action="store_true", help="wake the PC first (needs PC_MAC)")
    s.add_argument("--feeds", action="store_true", help="use the real weather and news feeds")
    s.add_argument("--out", default="/tmp/hegel-rehearsal")
    s.add_argument("--days", type=int, default=1, help="rehearse this many days in a row (default 1), the owl after each")
    s.add_argument("--set", action="append", metavar="KEY=VALUE", help="a HEGEL_ switch for the rehearsal's Config (repeatable), e.g. --set HEGEL_CULTURE=1")
    s.add_argument("--docs", help="start from another rehearsal's folder instead of the repo's docs (a fork)")
    s.add_argument("--seed", type=int, help="a base seed for the real mind's calls (HEGEL_SEED)")
    o = sub.add_parser("owl", help="write up a finished day now")
    o.add_argument("--date", required=True)
    o.add_argument("--mind", help="'stub' or a URL (default: OWL_URL / OWL_PORT on the PC)")
    o.add_argument("--no-git", action="store_true")
    sub.add_parser("check", help="sanity-check data and day files")
    r = sub.add_parser("report", help="the scoreboard row of a day, or of every day in a range")
    r.add_argument("dates", nargs="*", help="one date, or the first and last of a range (default: the latest day)")
    r.add_argument("--docs", help="another docs folder, e.g. a checkout of the shadow branch")
    r.add_argument("--table", action="store_true", help="a Markdown table")
    r.add_argument("--health", action="store_true", help="what the world gave him instead: a line a full day (world/health.py)")
    r.add_argument("--floor", type=int, default=report.FLOOR, help="with --health: the fewest thoughts that make a full day")
    r.add_argument("--json", action="store_true", help="one JSON object per day")
    w = sub.add_parser("wishes", help="the wishes he has written down (HEGEL_WANTS), by day")
    w.add_argument("--since", help="from this date (YYYY-MM-DD) on")
    w.add_argument("--docs", help="another docs folder, e.g. a rehearsal's folder")
    args = p.parse_args()
    cfg = Config()
    if getattr(cfg, "pause_away", False):
        pause.apply(cfg)                        # his clock trails Delhi's by the days his world was held
    setup_logging(cfg, args.verbose)
    return {"tick": cmd_tick, "start": cmd_start, "status": cmd_status, "simulate": cmd_simulate, "owl": cmd_owl, "check": cmd_check,
            "report": cmd_report, "wishes": cmd_wishes}[args.cmd](cfg, args)


if __name__ == "__main__":
    sys.exit(main())
