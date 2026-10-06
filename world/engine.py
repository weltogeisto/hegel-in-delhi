"""The engine: keeps the published day a little ahead of Delhi time.

Each tick it looks at where the timeline ends. While that is less than LEAD_MIN minutes away, it builds
the next situation, asks the mind, checks the answer, writes the step into docs/days/<date>.json and
moves on. The page reveals each step when its time comes. The day file is the state: no database.
"""
import copy
import json
import logging
import os
import random
import time
from datetime import date, datetime, timedelta

from . import contract, lookup, owl, shelf, voices, works
from .clock import day_number, fmt, hm, long_date, minute_of, sun
from .memory import Memory, record_text
from .money import ADVANCE
from .mind import MindAway
from .world import at_dt

log = logging.getLogger("world")
MAX_DECISIONS = 8
SHELF_MEMORY = 6                # steps of the day in which a passage of the shelf is not offered again
CHOICE_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string", "enum": ["yes", "no"]}}, "required": ["answer"]}


class Days:
    """docs/days: one JSON file per day plus index.json."""

    def __init__(self, docs):
        self.dir = docs / "days"

    def path(self, d):
        return self.dir / f"{d.isoformat() if hasattr(d, 'isoformat') else d}.json"

    def load(self, d):
        p = self.path(d)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def save(self, day):
        self.dir.mkdir(parents=True, exist_ok=True)
        p = self.path(day["date"])
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(day, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, p)
        ix = self.index()
        row = {"date": day["date"], "n": day["n"], "title": day["title"], "holiday": day.get("holiday")}
        if day.get("owl"):
            row["owl"] = True
        ix["days"] = sorted([r for r in ix["days"] if r["date"] != day["date"]] + [row], key=lambda r: r["date"])
        tmp = (self.dir / "index.json").with_suffix(".tmp")
        tmp.write_text(json.dumps(ix, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, self.dir / "index.json")

    def index(self):
        p = self.dir / "index.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"format": 1, "days": []}

    def latest(self, on_or_before=None):
        rows = [r for r in self.index()["days"] if on_or_before is None or r["date"] <= on_or_before.isoformat()]
        return self.load(rows[-1]["date"]) if rows else None


def until_of(day):
    u = day["state"]["until"]
    if "T" in u:
        return datetime.fromisoformat(u)
    d = datetime.fromisoformat(day["date"]).date()
    return at_dt(d, hm(u))


class Engine:
    def __init__(self, cfg, world, mind, git=None, owl_mind=None):
        self.cfg, self.world, self.mind, self.git = cfg, world, mind, git
        self.owl_mind = owl_mind or mind
        self.days = Days(cfg.docs)
        self.memory = Memory(self.days, world)
        self.lookup = lookup.find           # (query, cache folder) -> the page he reads, or a note; tests put a stand-in here
        self.soul = (cfg.repo / "mind/soul.md").read_text(encoding="utf-8")
        self.voice_prompt = (cfg.repo / "mind/voices.md").read_text(encoding="utf-8")
        self.shelf = shelf.load(cfg.repo / "mind/shelf/index.json.gz", cfg.repo / "world/data/shelf_terms.json") if cfg.shelf else None

    # ── days ────────────────────────────────────────────────────────
    def migrate(self, prev, st):
        """A state from before the economy (day 1's) gets its accounts: a voucher for every purchase in the bag entries of
        the days so far, and the places he has been."""
        acc = st["account"] = {"advance": ADVANCE, "vouchers": [], "admitted": 0, "queried": 0}
        visits = st.setdefault("visits", {})
        earlier = [self.days.load(r["date"]) for r in self.days.index()["days"] if r["date"] < prev["date"]]
        for day in [x for x in earlier if x] + [prev]:
            acc["vouchers"] += [{"date": day["date"], "t": e["t"], "item": e["item"], "price": e["price"], "office": self.world.is_office(e["item"])}
                                for e in day["entries"] if e["k"] == "bag" and e["price"]]
            for sg in day["segments"]:
                pid = sg.get("at") or sg.get("b")
                if pid and day["date"] not in visits.setdefault(pid, []):
                    visits[pid].append(day["date"])

    def new_day(self, prev, d):
        st = copy.deepcopy(prev["state"])
        st["today"] = {}
        st.pop("yesterday", None)
        if "account" not in st:
            self.migrate(prev, st)
        self.world.ledger(st)
        rise, set_ = sun(d)
        hol = self.world.holiday(d)
        day = {
            "format": 1, "n": day_number(d), "date": d.isoformat(), "title": long_date(d),
            "holiday": hol["name"] if hol else None,
            "sun": {"rise": fmt(rise), "set": fmt(set_)},
            "weather": self.world.weather_public(d),
            "places": self.world.place_info(d),
            "opening": {"imprest": st["imprest"], "wearing": st["wearing"],
                        "wardrobe": [{"item": w["item"], "status": w["status"]} for w in st["wardrobe"]],
                        "cash": st["imprest"], "account": copy.deepcopy(st["account"]), "owed": copy.deepcopy(st["owed"]),
                        "cheques": copy.deepcopy(st["cheques"])},
            "segments": [], "entries": [], "steps": [], "owl": None, "complete": False, "state": st,
        }
        if st.get("asleep"):
            wake = at_dt(d, self.world.wake_time(d))
            day["segments"].append({"from": "00:00", "to": fmt(minute_of(wake)), "mode": "inside", "at": "home",
                                    "asleep": True, "owl": True, "now": "Asleep."})
            st["place"], st["until"] = "home", wake.isoformat(timespec="minutes")
        else:
            st["until"] = at_dt(d, 0).isoformat(timespec="minutes")
        log.info("day %s begins (%s)", day["n"], day["date"])
        return day

    def resume(self, day, now):
        """The world was off for a while. Pick up at home, now, without inventing what happened meanwhile."""
        d = now.date()
        start = until_of(day)
        if day["date"] < d.isoformat():
            day["complete"] = True
            self.days.save(day)
            day = self.new_day(day, d)
            start = until_of(day)
        st = day["state"]
        now = now.replace(second=0, microsecond=0)
        if start < now:
            st["asleep"] = False
            day["segments"].append({"from": fmt(minute_of(start)), "to": fmt(minute_of(now)), "mode": "inside",
                                    "at": st["place"] if st["place"] == "home" else "home", "now": "At home."})
            st["place"], st["until"] = "home", now.isoformat(timespec="minutes")
            st.setdefault("today", {})["woke"] = fmt(minute_of(now))        # his clock for hunger starts when he picks up
            day["steps"].append({"t": fmt(minute_of(start)), "end": fmt(minute_of(now)), "resumed": True})
        log.warning("resumed at %s after a gap", now.isoformat(timespec="minutes"))
        return day

    # ── one step ────────────────────────────────────────────────────
    def step(self, day, t):
        st = day["state"]
        if "account" not in st:
            self.migrate(day, st)               # a day file from before the economy: its books are made on first need
        prev = next((s for s in reversed(day["steps"]) if "decision" in s), None)
        sit, ctx = self.world.situation(t, st, day, prev)
        remember = self.memory.recall(sit, ctx, day)
        if remember:
            sit["remember"] = remember
        ctx["recent"], ctx["known_text"] = self.memory.recent_thoughts(day), self.memory.known_text(day, sit)
        m = minute_of(t)
        t_start = time.time()
        refused, warnings, raw, result, attempts, source = [], [], "", None, 0, self.mind.source
        if 30 <= m < 240 and not st.get("asleep"):
            source = "bedtime"          # the world sends him to bed after half past midnight
        elif st.get("asleep") and not self.make_plan(day, t, sit, ctx) and not getattr(self.mind, "ready", True):
            refused.append(["the PC did not wake for the morning plan"])
            source = "away"             # no second wake in the same step; an awake PC that fumbled the plan still decides
        elif not self.greet(day, sit, ctx):
            refused.append(["the PC did not wake for a greeting"])
            source = "away"
        else:
            sit["shelf"] = self.offer(day, sit, ctx, st)
            if sit["shelf"]:
                ctx["shelf"] = sit["shelf"]
                ctx["known_text"] += "\n" + "\n".join(x["text"] for x in sit["shelf"])         # what is open before him he has met
            messages = [{"role": "system", "content": self.soul}, {"role": "user", "content": contract.render(sit)}]
            try:
                for _ in range(3):
                    attempts += 1
                    raw = self.mind.decide(messages, sit)
                    ans = contract.extract_json(raw)
                    errors, warnings, rep = self.world.check(ans, sit, ctx, st)
                    if not errors:
                        result = rep
                        break
                    refused.append(errors)
                    log.info("refused at %s: %s", sit["time"], "; ".join(errors))
                    messages += [{"role": "assistant", "content": raw},
                                 {"role": "user", "content": "The world refuses this step: " + "; ".join(errors)
                                  + ". Decide again. Answer with the JSON object only."}]
            except MindAway as e:
                log.warning("mind away at %s: %s", sit["time"], e)
                refused.append([str(e)])
                source = "away"
            if result is None and source != "away":
                source = "quiet"
        if result is None:
            result = self.quiet(st, t, sit)
        ans, plan = result
        beat = ctx["beat"]
        if beat and source in ("mind", "stub"):
            ctx["beat_entries"] = self.world.fire(beat, t, st)
            if beat.get("choice"):
                yes = self.ask_choice(messages, raw, beat)
                ctx["beat_entries"] += self.world.settle_choice(beat, yes, st, t)
        if source in ("mind", "stub"):
            if ans.get("says") and ctx["present"]:
                ctx["reply"] = self.reply(day, sit, ctx, ans["says"])
            if ans["action"] == "write":
                ctx["writing"] = self.write(messages, raw, ctx, st)
            if ans.get("looks_up"):
                ctx["read"] = self.look(ans["looks_up"], st)
        step = self.world.apply(ans, plan, sit, ctx, st, day)
        step["mind"] = {"source": source, "attempts": attempts, "latency_s": round(time.time() - t_start, 1)}
        if ctx.get("shelf") and source in ("mind", "stub"):
            step["shelf"] = [{"work": x["work"], "ref": x["ref"], "id": x["id"]} for x in ctx["shelf"]]
        if refused:
            step["mind"]["refused"] = refused
        if warnings:
            step["mind"]["warnings"] = warnings
        if beat and "beat_entries" in ctx:
            step["beat"] = beat["id"]
        day["steps"].append(step)
        log.info("%s %s %s → %s until %s (%s)", day["date"], step["t"], ans["action"], ans["place"], step["end"], source)
        return step

    def offer(self, day, sit, ctx, st):
        """The passages of his shelf for this decision: the two that fit the event, the place, the people present and their
        roles, his last two thoughts and his theses best, leaving out any that were offered in the last SHELF_MEMORY steps of
        the day. [] without a shelf, or when nothing on it fits."""
        if not self.shelf:
            return []
        used = {x["id"] for step in day["steps"][-SHELF_MEMORY:] for x in step.get("shelf") or []}
        roles = [self.world.cast[c]["role"] for c in ctx["present"]]
        thoughts = [text for _, text in ctx["recent"][-2:]]
        parts = shelf.query_parts(sit["event"], self.world.places[sit["place"]]["short"], roles, thoughts, [x["text"] for x in st.get("theses", [])])
        return self.shelf.pick(parts, avoid=used)

    def make_plan(self, day, t, sit, ctx):
        """On waking: one extra call for the day's intentions. With no usable answer he simply has no plan.
        False only when the mind is away."""
        messages = [{"role": "system", "content": self.soul}, {"role": "user", "content": contract.render(sit, contract.PLAN_ASK)}]
        try:
            items = self.world.plan_items(contract.extract_json(self.mind.chat(messages, contract.PLAN_SCHEMA, max_tokens=500)), ctx)
        except MindAway as e:
            log.warning("mind away for the plan at %s: %s", sit["time"], e)
            return False
        if not items:
            log.warning("no usable plan at %s", sit["time"])
            return True
        day["plan"], ctx["plan"] = {"written": fmt(minute_of(t)), "items": items}, items
        self.world.show_plan(sit, day)
        return True

    def voice(self, cid, day, sit, says):
        """One call: the person cid answers what he said, or speaks first when says is None. {by, says, does}, or None
        when the answer is unusable. MindAway goes up."""
        c = self.world.cast[cid]
        remember = self.memory.moments(c, day, list(self.memory.before(date.fromisoformat(day["date"]))), voice=True)
        where = self.world.places[sit["place"]]["name"]
        messages = [{"role": "system", "content": self.voice_prompt}, {"role": "user", "content": voices.render(c, sit, where, says, remember)}]
        return voices.clean(c, contract.extract_json(self.mind.chat(messages, contract.VOICE_SCHEMA, max_tokens=250)))

    def greet(self, day, sit, ctx):
        """A person he knows, new in sight today, may speak first: the line joins the event and what he has met.
        False only when the PC did not wake."""
        cid = self.world.greeter(ctx)
        try:
            said = self.voice(cid, day, sit, None) if cid else None
        except MindAway as e:
            log.warning("mind away for a greeting at %s: %s", sit["time"], e)
            return getattr(self.mind, "ready", True)
        if said:
            ctx["greeting"] = said
            sit["event"] += " " + voices.heard(said)
            ctx["known_text"] += "\n" + voices.heard(said)
        return True

    def reply(self, day, sit, ctx, says):
        """The one he spoke to answers (one call). None if the mind is away or the answer is unusable."""
        try:
            return self.voice(voices.pick(self.world.cast, says, ctx["present"]), day, sit, says)
        except MindAway as e:
            log.warning("mind away for an answer at %s: %s", sit["time"], e)
            return None

    def write(self, messages, raw, ctx, st):
        """He chose to write: the sitting, {title, kind, to, continues, text, mode, ...}, or None if it is dropped (the decision stands).
        In plain mode (write_mode, with a mind that can complete) the text comes from a plain-text completion; when that gives nothing
        the chat call writes it, as it does throughout in chat mode."""
        if self.cfg.write_mode == "plain" and callable(getattr(self.mind, "complete", None)):
            try:
                w = self.write_plain(messages, raw, ctx, st)
            except MindAway as e:
                log.warning("mind away for the writing: %s", e)
                return None
            if w:
                log.info("writing by plain completion: %s", w["title"])
                return w
            log.info("writing: no text from a plain completion, falling back to the chat call")
        w = self.write_chat(messages, raw, ctx, st)
        if w:
            log.info("writing by chat call: %s", w["title"])
        return w

    def write_plain(self, messages, raw, ctx, st):
        """One small chat call says what the sitting is (title, kind, to, continues, about), then the text is a plain-text completion under a
        header in the style of his books (works.prompt), after two passages of his books each under a header that names its topic
        (works.exemplars, which are not part of the text). A completion that copies an exemplar or is off the subject (works.flaw), and names
        from after 1831 that he has not met, cannot be asked away here: the completion is made once more with another seed. None if no
        usable text came, and it is then for the chat call; MindAway only from the first call, when the chat call could not answer either."""
        msgs = messages + [{"role": "assistant", "content": raw}, {"role": "user", "content": works.sitting_ask(st)}]
        plan = works.outline(contract.extract_json(self.mind.chat(msgs, contract.SITTING_SCHEMA, max_tokens=300)))
        if not plan:
            log.info("writing: no usable account of what the sitting is")
            return None
        shown = works.exemplars(plan, ctx["t"].date(), self.cfg.repo)
        log.info("writing: exemplars %s", ", ".join(x["topic"] for x in shown) or "none")
        prompt, opening = works.prompt(plan, st, ctx["t"].date(), shown)
        for seed in (None, random.randrange(1, 2 ** 31)):
            try:
                w = works.sitting(plan, self.mind.complete(prompt, works.TOKENS, seed=seed), opening)
            except MindAway as e:
                log.warning("completion failed for the writing: %s", e)
                return None
            if not w:
                log.info("writing: the completion is unusable")
                return None
            bad = works.flaw(plan, w, shown, opening)
            if bad:
                log.info("writing: the completion %s", bad)
                continue
            wrong = self.world.unmet(w["title"] + "\n" + w["about"] + "\n" + w["text"], ctx["known_text"])
            if not wrong:
                return dict(w, mode="plain")
            log.info("writing: the completion has names he has not met: %s", "; ".join(wrong))
        return None

    def write_chat(self, messages, raw, ctx, st):
        """One chat call for what he wrote. Names from after 1831 that he has not met: he is asked once to write it again without them,
        then the writing is dropped (the decision stands). None if dropped."""
        msgs = messages + [{"role": "assistant", "content": raw}, {"role": "user", "content": works.ask(st)}]
        for _ in range(2):
            try:
                reply = self.mind.chat(msgs, contract.WRITE_SCHEMA, max_tokens=1100)
            except MindAway as e:
                log.warning("mind away for the writing: %s", e)
                return None
            w = works.clean(contract.extract_json(reply))
            if not w:
                return None
            wrong = self.world.unmet(w["title"] + "\n" + w["text"], ctx["known_text"])
            if not wrong:
                return dict(w, mode="chat")
            msgs += [{"role": "assistant", "content": reply}, {"role": "user", "content":
                     "Write it again without " + ", ".join(f"'{x}'" for x in wrong) + ": you have not met them in Delhi, and in 1831 you could not know them. "
                     "Answer with the JSON object only."}]
        log.info("writing dropped: %s", "; ".join(wrong))
        return None

    def look(self, query, st):
        """He looks something up on his phone: the page he reads, {title, text, source, url}, or {note} for what went wrong."""
        if not (st["tech"]["phone"] and st["tech"]["sim"]):
            return {"note": "You have nothing to look it up on."}
        return self.lookup(query, self.cfg.state / "lookup")

    def quiet(self, st, t, sit):
        """No usable answer: he carries on, without a thought on the page."""
        m, cur = minute_of(t), st["place"]
        if m >= 1320 or m < 240:
            action, dest = "sleep", "home"
        elif cur != "home" and cur not in sit["open_now"]:
            action, dest = "walk", "home"
        else:
            action, dest = ("rest" if cur == "home" else "stay"), cur
        ans = {"thought": None, "action": action, "place": dest, "minutes": 30, "says": None, "buys": [], "revision": None}
        plan = {"moves": dest != cur, "dest": dest, "arrival": t + timedelta(minutes=self.world.walk(cur, dest)), "buys": []}
        return ans, plan

    def ask_choice(self, messages, raw, beat):
        q = beat["choice"]["question"]
        msgs = messages + [{"role": "assistant", "content": raw},
                           {"role": "user", "content": f"For the record, one word: {q} Answer {{\"answer\": \"yes\"}} or {{\"answer\": \"no\"}}."}]
        try:
            a = contract.extract_json(self.mind.chat(msgs, CHOICE_SCHEMA, max_tokens=20, temperature=0))
            return isinstance(a, dict) and a.get("answer") == "yes"
        except MindAway:
            return False

    # ── the tick ────────────────────────────────────────────────────
    def advance(self, now):
        """Fill the timeline up to now + lead. Returns the dates whose files changed."""
        changed = []
        day = self.days.latest(now.date() + timedelta(days=1))
        if day is None:
            raise RuntimeError("no day files in docs/days; day 1 must be there")
        if until_of(day) < now - timedelta(minutes=45):
            day = self.resume(day, now)
            changed.append(day["date"])
        horizon = now + timedelta(minutes=self.cfg.lead)
        for _ in range(MAX_DECISIONS):
            until = until_of(day)
            if until >= horizon:
                break
            if until.date().isoformat() > day["date"]:
                if not day.get("complete"):
                    day["complete"] = True
                    self.days.save(day)
                    changed.append(day["date"])
                day = self.days.load(until.date()) or self.new_day(day, until.date())
                self.days.save(day)
                changed.append(day["date"])
                continue
            self.step(day, until)
            day["weather"] = self.world.weather_public(datetime.fromisoformat(day["date"]).date())
            self.days.save(day)
            changed.append(day["date"])
        return list(dict.fromkeys(changed))

    def owl_ready(self, now):
        """Yesterday's day, if it is finished, not yet written up, it is past OWL_AT and no try in the last hour."""
        d = now.date() - timedelta(days=1)
        day = self.days.load(d)
        if not day or day.get("owl") or not day.get("complete") or now < at_dt(now.date(), hm(self.cfg.owl_at)):
            return None
        mark = self.cfg.state / f"owl-{d.isoformat()}.tried"
        if mark.exists() and time.time() - mark.stat().st_mtime < 3600:
            return None
        return day

    def due(self, now):
        day = self.days.latest(now.date() + timedelta(days=1))
        return day is None or until_of(day) < now + timedelta(minutes=self.cfg.lead)

    def run_owl(self, day, now):
        latest = self.days.latest(now.date() + timedelta(days=1))
        st = latest["state"]
        weekday = datetime.fromisoformat(day["date"]).strftime("%A")
        n = st.get("depesche_n", 0) + 1 if weekday == self.cfg.depesche_day else None
        known = self.memory.known_before(day["date"]) + "\n" + record_text(day)
        written = owl.write(self.cfg, day, st, self.owl_mind, depesche_n=n, problems=lambda text: self.world.problems(text, known),
                            flag=self.world.flag, topic=self.world.topic)
        written["written"] = fmt(minute_of(now))
        day["owl"] = written
        self.days.save(day)
        if n:
            st["depesche_n"] = n
        if latest["date"] != day["date"]:
            self.days.save(latest)
        log.info("the owl wrote up day %s", day["n"])
        return [day["date"], latest["date"]]

    def tick(self, now):
        owl_day = self.owl_ready(now)
        if not owl_day and not self.due(now):
            return []           # most minutes: nothing to decide, no network
        if self.git:
            self.git.sync()
        changed = self.advance(now)
        msg = None
        if changed:
            day = self.days.load(changed[-1])
            last = next((s for s in reversed(day["steps"]) if "decision" in s), None)
            msg = f"Day {day['n']}, {last['t']}: {last['decision']['action']} ({last['decision']['place']})" if last else f"Day {day['n']} begins"
        owl_day = self.owl_ready(now)
        if owl_day:
            self.cfg.state.mkdir(parents=True, exist_ok=True)
            (self.cfg.state / f"owl-{owl_day['date']}.tried").touch()
            try:
                changed += self.run_owl(owl_day, now)
                msg = (msg + "; " if msg else "") + f"the owl writes up day {owl_day['n']}"
            except (MindAway, owl.OwlError) as e:
                log.warning("owl failed: %s", e)
        if changed and self.git:
            paths = [self.days.path(x) for x in dict.fromkeys(changed)] + [self.days.dir / "index.json"]
            self.git.publish(paths, msg)
        return changed
