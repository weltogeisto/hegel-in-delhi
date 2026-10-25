"""The watchman (T17): is Hegel's mind with him, and is the world still publishing?

    python3 tools/watchman.py PATH/TO/docs/days [--now 2026-10-14T04:10Z]

Reads the day files of the shadow branch and prints one JSON line: {"state", "title", "detail"}, where state is
"ok", "mind_away" (his last three waking steps ran without a mind) or "pi_quiet" (the published day ran out an hour
ago and nothing new came). `.github/workflows/watchman.yml` runs it every hour and turns anything but "ok" into an
issue, which GitHub emails to the owner, and closes the issue when "ok" returns. Standard library only.
"""
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
AWAY_IN_A_ROW = 3                       # three half-hour steps: about ninety minutes of his day without a mind
QUIET_AFTER = timedelta(minutes=60)     # the published day ran out this long ago


def until_of(day):
    u = day["state"]["until"]
    if "T" in u:
        return datetime.fromisoformat(u)
    h, m = (int(x) for x in u.split(":"))
    d = datetime.fromisoformat(day["date"])
    return datetime(d.year, d.month, d.day, tzinfo=IST) + timedelta(hours=h, minutes=m)


def source(step):
    return (step.get("mind") or {}).get("source")


def last_word(step):
    """The world's note on the last step, without the PC's address: the issue is public."""
    refused = (step.get("mind") or {}).get("refused") or [[]]
    said = refused[-1][-1] if refused[-1] else ""
    return re.sub(r"https?://\S+", "the mind's address", str(said))


def check(days_dir, now):
    days_dir = Path(days_dir)
    index = json.loads((days_dir / "index.json").read_text(encoding="utf-8"))
    rows = index.get("days") or []
    if not rows:
        return {"state": "ok", "title": "Watchman: nothing to watch", "detail": "No day files yet."}
    day = json.loads((days_dir / f"{rows[-1]['date']}.json").read_text(encoding="utf-8"))
    his_now = now.astimezone(IST) + timedelta(minutes=index.get("clock_shift_min", 0))
    until, n = until_of(day), day.get("n")
    if his_now - until > QUIET_AFTER:
        late = int((his_now - until).total_seconds() // 60)
        return {"state": "pi_quiet", "title": "Watchman: the world has stopped publishing",
                "detail": f"Day {n} is published up to {until:%d %b %H:%M} on his clock, and it is now {his_now:%d %b %H:%M}: "
                          f"{late} minutes with nothing new. The Pi's timer may be stopped, or its pushes are failing."}
    steps = [s for s in day.get("steps", []) if "decision" in s]
    waking = [s for s in steps if s["decision"]["action"] != "sleep" and source(s) != "bedtime"]
    last = waking[-AWAY_IN_A_ROW:]
    awake = bool(waking) and steps[-1] is waking[-1]          # asleep, he needs no mind until morning
    if awake and len(last) == AWAY_IN_A_ROW and all(source(s) == "away" for s in last):
        times = ", ".join(s["t"] for s in last)
        return {"state": "mind_away", "title": "Watchman: Hegel's mind is away",
                "detail": f"Day {n}: his last {AWAY_IN_A_ROW} waking steps ({times} on his clock) ran without a mind. "
                          f"The world's last word: “{last_word(last[-1])}”. Meanwhile he keeps the household (T12). "
                          f"Check that the PC is on and its 8082 server answers (pc/TASKS.md, T16)."}
    tail = steps[-1] if steps else None
    where = f"last step {tail['t']}, {tail['decision']['action']} ({source(tail)})" if tail else "no steps yet"
    return {"state": "ok", "title": "Watchman: all well",
            "detail": f"Day {n}, published up to {until:%H:%M} on his clock; {where}."}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("days", help="a docs/days folder, e.g. from a checkout of the shadow branch")
    p.add_argument("--now", help="pretend it is this time (ISO, with zone), for testing")
    args = p.parse_args()
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    print(json.dumps(check(args.days, now), ensure_ascii=False))


if __name__ == "__main__":
    main()
