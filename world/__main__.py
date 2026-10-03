"""Hegel in Delhi: the world engine.

    python3 -m world start --date 2026-10-07   # the first live day begins at that midnight
    python3 -m world tick                 # run by the timer every minute: keep the day 15 minutes ahead
    python3 -m world status               # where he is, what was last decided, whether the mind answers
    python3 -m world simulate --date 2026-10-03            # rehearse a whole day offline (stand-in mind)
    python3 -m world simulate --date 2026-10-03 --mind URL # the same day with the real mind, nothing pushed
    python3 -m world owl --date 2026-10-03                 # write up a finished day now
    python3 -m world check                # sanity-check the world's data and the day files
"""
import argparse
import fcntl
import json
import logging
import logging.handlers
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

from . import shelf
from .clock import fmt, minute_of, now_ist, parse_now
from .config import Config
from .engine import Days, Engine, until_of
from .feeds import Feeds
from .mind import HTTPMind, StubMind
from .publish import Git
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
    if which == "stub":
        return StubMind()
    url = cfg.mind_url if which in (None, "pc") else which
    if not url:
        sys.exit("no mind configured: set PC_HOST (and MIND_PORT) in ~/.config/hegel/env, or pass --mind URL or --mind stub")
    return HTTPMind(url, wake=cfg.wake if wake else None, timeout=cfg.timeout)


def cmd_tick(cfg, args):
    cfg.state.mkdir(parents=True, exist_ok=True)
    lock = open(cfg.state / "tick.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log.debug("another tick is running")
        return 0
    now = parse_now(args.now) if args.now else now_ist()
    mind = make_mind(cfg, args.mind)
    owl_mind = mind if args.mind == "stub" or not cfg.owl_url or cfg.owl_url == cfg.mind_url else HTTPMind(cfg.owl_url, wake=cfg.wake, timeout=cfg.timeout)
    engine = Engine(cfg, World(Feeds(cfg)), mind, git=Git(cfg) if not args.no_git else None, owl_mind=owl_mind)
    engine.tick(now)
    return 0


def cmd_start(cfg, args):
    """Schedule the first live day: the world stays quiet until that midnight, then begins cleanly."""
    d = date.fromisoformat(args.date) if args.date else now_ist().date() + timedelta(days=1)
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
    now = now_ist()
    day = days.latest(now.date() + timedelta(days=1))
    if not day:
        print("no day files")
        return 1
    st = day["state"]
    until = until_of(day)
    ahead = (until - now).total_seconds() / 60
    steps = [s for s in day["steps"] if "decision" in s]
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
    if cfg.mind_url:
        print(f"mind           {cfg.mind_url}: {'answers' if HTTPMind(cfg.mind_url).health() else 'asleep or away'}")
    return 0


def cmd_simulate(cfg, args):
    d = date.fromisoformat(args.date)
    out = Path(args.out).resolve()
    (out / "days").mkdir(parents=True, exist_ok=True)
    src = Days(cfg.docs)
    prev = [r for r in src.index()["days"] if r["date"] < args.date]
    if not prev:
        sys.exit("simulate needs an earlier day in docs/days to start from")
    for r in src.index()["days"]:
        if r["date"] < args.date:
            shutil.copy(src.path(r["date"]), out / "days" / f"{r['date']}.json")
    (out / "days/index.json").write_text(json.dumps({"format": 1, "days": prev}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if (cfg.docs / "index.html").exists():
        shutil.copy(cfg.docs / "index.html", out / "index.html")
    sim = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(out / "state"), "HEGEL_FEEDS": "1" if args.feeds else "0"})
    sim.docs = out
    world = World(Feeds(sim))
    mind = make_mind(sim, args.mind or "stub", wake=args.wake)
    engine = Engine(sim, world, mind, git=None)
    last = Days(out).latest()
    if until_of(last).date() < d:          # a gap before the rehearsed day: start it fresh at midnight
        last["state"]["until"] = at_dt(d, 0).isoformat(timespec="minutes")
    now = at_dt(d, 0)
    end = at_dt(d, 1440)
    while now < end:
        engine.advance(now)
        now += timedelta(minutes=5)
    owl_day = Days(out).load(d)
    owl_day["complete"] = True
    Days(out).save(owl_day)
    engine.run_owl(owl_day, at_dt(d + timedelta(days=1), minute_of(at_dt(d, 0)) + 90))
    day = Days(out).load(d)
    steps = [s for s in day["steps"] if "decision" in s]
    srcs = {}
    for s in steps:
        srcs[s["mind"]["source"]] = srcs.get(s["mind"]["source"], 0) + 1
    refused = sum(len(s["mind"].get("refused", [])) for s in steps)
    print(f"day {day['n']} ({day['date']}): {len(steps)} steps, {len(day['segments'])} segments, {len(day['entries'])} entries; "
          f"by {srcs}; {refused} refusals; cash ₹{day['state']['imprest']:,}")
    print(f"wrote {out}/days/{day['date']}.json  (serve {out} and open index.html#{day['date']} to watch it)")
    return 0


def cmd_owl(cfg, args):
    days = Days(cfg.docs)
    day = days.load(args.date)
    if not day:
        sys.exit(f"no day file for {args.date}")
    mind = make_mind(cfg, args.mind) if args.mind or not cfg.owl_url else HTTPMind(cfg.owl_url, wake=cfg.wake, timeout=cfg.timeout)
    engine = Engine(cfg, World(), mind, git=None if args.no_git else Git(cfg), owl_mind=mind)
    changed = engine.run_owl(day, now_ist())
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
                                         "world/data/shelf_terms.json") if not (cfg.repo / f).exists()]
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
    s.add_argument("--mind", help="'stub' (default) or a llama-server URL")
    s.add_argument("--wake", action="store_true", help="wake the PC first (needs PC_MAC)")
    s.add_argument("--feeds", action="store_true", help="use the real weather and news feeds")
    s.add_argument("--out", default="/tmp/hegel-rehearsal")
    o = sub.add_parser("owl", help="write up a finished day now")
    o.add_argument("--date", required=True)
    o.add_argument("--mind", help="'stub' or a URL (default: OWL_URL / OWL_PORT on the PC)")
    o.add_argument("--no-git", action="store_true")
    sub.add_parser("check", help="sanity-check data and day files")
    args = p.parse_args()
    cfg = Config()
    setup_logging(cfg, args.verbose)
    return {"tick": cmd_tick, "start": cmd_start, "status": cmd_status, "simulate": cmd_simulate, "owl": cmd_owl, "check": cmd_check}[args.cmd](cfg, args)


if __name__ == "__main__":
    sys.exit(main())
