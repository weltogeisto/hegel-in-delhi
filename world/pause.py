"""A pause for his world when the PC is away (HEGEL_PAUSE_AWAY; Welt, 15 November; DECISIONS.md 32; pc/PAUSE.md).

Without it, a PC that stays away lets his days run on empty: Days 39 to 43 had no thoughts at all. With it, when the
PC does not answer as he is about to wake, his world is held at the start of that day, asleep. When the PC answers
again, he lives the held day from that point, and his calendar trails Delhi's by whole days from then on. Whole days
keep his hours where the PC's are (his day is nine to nine, the PC's twelve hours). A PC that leaves in the middle of
a day changes nothing here: the rest of that day runs as it always has, and the hold, if the PC is still away, comes
at the next waking.

The trail is kept in the state folder (pause.json) and reaches the page through the index's clock shift."""
import json
import logging
import os
from datetime import date, timedelta

from .clock import minute_of
from .mind import MindAway
from .world import BED_M

log = logging.getLogger(__name__)


def path(cfg):
    return cfg.state / "pause.json"


def load(cfg):
    p = path(cfg)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"lag_days": 0, "held": None, "since": None, "history": []}


def save(cfg, data):
    cfg.state.mkdir(parents=True, exist_ok=True)
    tmp = path(cfg).with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path(cfg))


def lag_min(cfg):
    """Minutes his clock trails Delhi's: whole days."""
    return load(cfg)["lag_days"] * 1440


def apply(cfg):
    """At start-up, with the switch on: his clock trails by the kept number of days, everywhere the clock shift is read."""
    cfg.base_shift_min = getattr(cfg, "clock_shift_min", 0)
    cfg.clock_shift_min = cfg.base_shift_min - lag_min(cfg)


def next_step(engine, now):
    """(the latest day, when its next step falls) if a step is due now, else None."""
    from .engine import until_of
    day = engine.days.latest(now.date() + timedelta(days=1))
    if not day:
        return None
    until = until_of(day)
    return (day, until) if until < now + timedelta(minutes=engine.cfg.lead) else None


def needs_wake(engine, now):
    """Whether the step that is due is his waking: asleep, at or after his wake time, before bedtime."""
    due = next_step(engine, now)
    if not due:
        return False
    day, until = due
    m = minute_of(until)
    return bool(day["state"].get("asleep")) and engine.world.wake_time(until.date()) <= m < BED_M


def answers(mind):
    try:
        mind.ensure_awake()
        return True
    except MindAway as e:
        log.info("the PC does not answer: %s", e)
        return False


def gate(cfg, engine, mind, real_now):
    """The world's now for this tick, or None while his world is held. real_now is Delhi time with the base clock shift."""
    data = load(cfg)
    if data.get("held"):
        if not answers(mind):
            log.info("his world is held at the start of %s, since %s", data["held"], data["since"])
            return None
        held = date.fromisoformat(data["held"])
        lag = max(data["lag_days"], (real_now.date() - held).days)
        data["history"].append({"held": data["held"], "since": data["since"],
                                "resumed": real_now.isoformat(timespec="minutes"), "lag_days": lag})
        data.update(lag_days=lag, held=None, since=None)
        save(cfg, data)
        cfg.clock_shift_min = getattr(cfg, "base_shift_min", 0) - lag * 1440
        engine.days.shift_min = cfg.clock_shift_min
        log.warning("the PC answers again: his world resumes on %s and now trails Delhi by %d days", held, lag)
        return real_now - timedelta(days=lag)
    now = real_now - timedelta(days=data["lag_days"])
    if needs_wake(engine, now) and not answers(mind):
        _, until = next_step(engine, now)
        data.update(held=until.date().isoformat(), since=real_now.isoformat(timespec="minutes"))
        save(cfg, data)
        log.warning("the PC does not answer as he wakes: his world is held at the start of %s", data["held"])
        return None
    return now
