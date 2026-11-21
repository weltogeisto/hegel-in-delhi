#!/usr/bin/env python3
"""Replay a recorded live morning offline and compare it with what the live world wrote (the check asked on PR #1, 21 November).

    python3 tools/replay_morning.py --start <folder> --calls <calls-*.jsonl> [...] --live <folder> --out <folder> [--decisions 5]

--start   a folder with days/ as the live docs held them before the first recorded tick, and state/ with feeds/ and lookup/ as they
          were after the last tick compared (the caches he read; nothing else of the state is used)
--calls   the recording, HEGEL_RECORD_CALLS's state/calls/calls-<date>.jsonl, one file or more, in order
--live    a folder with days/ as the live docs held them after the last decision compared (the shadow commit of that step)

The engine runs in --out on a copy of --start, ticked at the recorded times with the recorded `now`, the feeds offline and read from
the cache, and the mind answered from the recording (world/calls.py): no model is called. Every request must equal the recorded one,
field by field. It stops after --decisions accepted decisions, then compares the replay's day files with --live, step by step and
field by field (the stopwatch, mind.latency_s, left out).

The result is one of: **match** (every request and every step equal), **mismatch** (the first difference: a request field, a step
field, or a day field), or **inconclusive** (the recording ends early, the code or the switches differ from the recording's, or the
feed cache changed inside the window). Evaluation only: nothing here is training data."""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from world import calls, health  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import HTTPMind  # noqa: E402

FORCED = {"HEGEL_FEEDS": "0", "HEGEL_PUSH": "0", "HEGEL_PAUSE_AWAY": "0"}


def day_files(folder):
    folder = Path(folder)
    days = folder / "days" if (folder / "days").is_dir() else folder
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(days.glob("????-??-??.json"))}


def strip(day):
    day = json.loads(json.dumps(day))
    for s in day.get("steps") or []:
        (s.get("mind") or {}).pop("latency_s", None)
    return day


def accepted(days, before):
    """Decisions a mind made, in days not in `before` or beyond the steps they had there."""
    n = 0
    for date, day in days.items():
        steps = day.get("steps") or []
        start = len((before.get(date) or {}).get("steps") or [])
        n += sum(1 for s in steps[start:] if "decision" in s and (s.get("mind") or {}).get("source") in health.MINDS)
    return n


def compare(replay, live, before):
    """The first difference between the replay's days and the live ones, over the days the replay wrote; None when they agree."""
    for date, rday in sorted(replay.items()):
        if date in before and before[date] == rday:
            continue
        lday = live.get(date)
        if lday is None:
            return f"day {date}: the replay wrote it, the live docs do not have it"
        r, l = strip(rday), strip(lday)
        rs, ls = r.pop("steps", []), l.pop("steps", [])
        for i, s in enumerate(rs):
            if i >= len(ls):
                return f"day {date}, step {i + 1} ({s.get('t')}): the replay has it, the live day ends at step {len(ls)}"
            d = calls.first_difference(ls[i], s)
            if d:
                return f"day {date}, step {i + 1} ({s.get('t')}){d if d.startswith(('.', '[')) else ' ' + d}"
        if len(rs) == len(ls):
            d = calls.first_difference(l, r)
            if d:
                return f"day {date}, the day's record{d if d.startswith(('.', '[')) else ' ' + d}"
    return None


def replay(start, call_files, live, out, decisions=5, repo=REPO):
    start, out = Path(start), Path(out)
    rows = calls.read(call_files)
    header = next((r for r in rows if r.get("type") == "header"), {})
    ticks = [r for r in rows if r.get("type") == "tick"]
    report = {"calls_files": {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in call_files},
              "recorded": {"ticks": len(ticks), "calls": sum(r.get("type") == "call" for r in rows)}, "inconclusive": []}
    if out.exists():
        shutil.rmtree(out)
    (out / "days").mkdir(parents=True)
    for p in (start / "days").glob("*.json"):
        shutil.copy(p, out / "days" / p.name)
    for sub in ("feeds", "lookup"):
        if (start / "state" / sub).is_dir():
            shutil.copytree(start / "state" / sub, out / "state" / sub)
    before = day_files(out)
    old_env = os.environ.get("HEGEL_ENV")
    os.environ["HEGEL_ENV"] = os.devnull                       # the replay is made from the recording's switches alone
    try:
        sim = Config({**header.get("switches", {}), **FORCED, "HEGEL_STATE": str(out / "state"), "HEGEL_REPO": str(repo)})
    finally:
        if old_env is None:
            os.environ.pop("HEGEL_ENV", None)
        else:
            os.environ["HEGEL_ENV"] = old_env
    sim.docs = out
    code = calls.code_hash(repo)
    if header.get("code") != code:
        report["inconclusive"].append(f"the code differs from the recording's ({str(header.get('code'))[:12]} recorded, {code[:12]} here)")
    got = {k: v for k, v in calls.switches(sim).items() if k not in FORCED}
    want = {k: v for k, v in header.get("switches", {}).items() if k not in FORCED}
    if got != want:
        report["inconclusive"].append(f"the switches differ: {calls.first_difference(want, got)}")
    from world.__main__ import make_mind, make_world       # noqa: E402  (the live tick's own builders)
    player = calls.Player(rows)
    mind = calls.play(make_mind(sim, "http://replay.invalid"), player)
    owl = calls.play(HTTPMind("http://replay-owl.invalid", timeout=sim.timeout), player) if header.get("owl_mind_separate") else mind
    engine = Engine(sim, make_world(sim), mind, git=None, owl_mind=owl)
    feeds_seen = {t.get("feeds") for t in ticks}
    if len(feeds_seen) > 1:
        report["inconclusive"].append("the feed cache changed between recorded ticks: the replay reads it as it was at the end")
    first = datetime.fromisoformat(ticks[0]["now"]) if ticks else None
    for p in (out / "state" / "feeds").glob("*") if first else ():
        os.utime(p, (first.timestamp(), first.timestamp()))   # the cache as fresh as it was at the first tick
    done, mismatch, replayed = 0, None, 0
    for t in ticks:
        now = datetime.fromisoformat(t["now"])
        try:
            with mock.patch("world.engine.time.time", return_value=now.timestamp()), \
                    mock.patch("world.feeds.time.time", return_value=now.timestamp()):
                engine.tick(now)
        except calls.Mismatch as e:
            mismatch = f"request: {e}"
            break
        replayed += 1
        done = accepted(day_files(out), before)
        if done >= decisions:
            break
    report.update(ticks_replayed=replayed, calls_served=player.pos, decisions=done)
    if mismatch is None:
        mismatch = compare(day_files(out), day_files(live), before)
    if mismatch:
        report["result"], report["first_difference"] = "mismatch", mismatch
    elif done < decisions:
        report["inconclusive"].append(f"the recording ends after {done} of {decisions} decisions")
        report["result"] = "inconclusive"
    elif report["inconclusive"]:
        report["result"] = "inconclusive"
    else:
        report["result"] = "match"
    return report


def markdown(r, decisions):
    lines = ["# A live morning against its replay", "",
             f"**Result: {r['result']}.**" + (f" First difference: {r['first_difference']}" if r.get("first_difference") else
                                              f" All {r['decisions']} decisions and every request match." if r["result"] == "match" else ""), "",
             f"- Recorded: {r['recorded']['ticks']} ticks, {r['recorded']['calls']} calls.",
             f"- Replayed: {r['ticks_replayed']} ticks, {r['calls_served']} calls served, {r['decisions']} of {decisions} decisions."]
    lines += [f"- Inconclusive because {x}." for x in r["inconclusive"]]
    lines += [f"- `{Path(p).name}` sha256 `{h}`" for p, h in r["calls_files"].items()]
    lines += ["", "Raw records stay where they were made. Evaluation only.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", required=True)
    ap.add_argument("--calls", required=True, nargs="+")
    ap.add_argument("--live", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--decisions", type=int, default=5)
    a = ap.parse_args(argv)
    r = replay(a.start, a.calls, a.live, a.out, a.decisions)
    (Path(a.out) / "REPORT.md").write_text(markdown(r, a.decisions), encoding="utf-8")
    (Path(a.out) / "report.json").write_text(json.dumps(r, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": r["result"], "first_difference": r.get("first_difference"), "inconclusive": r["inconclusive"]}))
    return 0 if r["result"] == "match" else 1


if __name__ == "__main__":
    raise SystemExit(main())
