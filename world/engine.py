"""The engine: keeps the published day a little ahead of Delhi time.

Each tick it looks at where the timeline ends. While that is less than LEAD_MIN minutes away, it builds
the next situation, asks the mind, checks the answer, writes the step into docs/days/<date>.json and
moves on. The page reveals each step when its time comes. The day file is the state: no database.
"""
import copy
import gzip
import json
import logging
import os
import random
import time
from datetime import date, datetime, timedelta

from . import calls, claim_check, contract, lookup, owl, papers, post, prefer, prompt_budget, records, report, shelf, talk, voices, works
from .clock import day_number, fmt, hm, long_date, minute_of, sun
from .memory import Memory, encountered_text
from .money import ADVANCE
from .mind import MindAway
from .publish import GitError
from .task_prompt import for_task
from .world import BED_M, MEAL_WINDOWS, at_dt, meal_at

log = logging.getLogger("world")
MAX_DECISIONS = 8
FUNNEL = ("live", "eligible", "shown", "yes", "no")      # what a day counts for each offer and beat (day["funnel"])
SHELF_MEMORY = 6                # steps of the day in which a passage of the shelf is not offered again


def funnel_key(beat):
    """The funnel's name for a beat: its id, or "session:<id>" for a session of a standing engagement, which shares its id with the offer
    that made it and must not be counted as that offer shown again."""
    return f"session:{beat['session']}" if beat.get("session") else beat["id"]


CHOICE_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string", "enum": ["yes", "no"]}}, "required": ["answer"]}


ECHO_LINE = "Already said today, more than once: {phrases}. Find other words, or another thought."


class Days:
    """docs/days: one JSON file per day plus index.json."""

    def __init__(self, docs, shift_min=None):
        self.dir = docs / "days"
        self.shift_min = shift_min          # None leaves the index's clock shift as it is

    def path(self, d):
        return self.dir / f"{d.isoformat() if hasattr(d, 'isoformat') else d}.json"

    def load(self, d):
        p = self.path(d)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def save(self, day):
        records.refresh(day)
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
        if self.shift_min:
            ix["clock_shift_min"] = self.shift_min          # the page reads its clock from here
        elif self.shift_min == 0:
            ix.pop("clock_shift_min", None)
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
    def __init__(self, cfg, world, mind, git=None, owl_mind=None, claim_guard=None):
        self.cfg, self.world, self.mind, self.git = cfg, world, mind, git
        self.owl_mind = owl_mind or mind
        self.recorder = None
        if getattr(cfg, "record_calls", False):              # HEGEL_RECORD_CALLS: one record for the engine's minds, in the order they are asked
            self.recorder = calls.Recorder(cfg.state / "calls", {"code": calls.code_hash(cfg.repo), "switches": calls.switches(cfg),
                                                                  "owl_mind_separate": self.owl_mind is not mind})
            for m in {id(mind): mind, id(self.owl_mind): self.owl_mind}.values():
                if hasattr(m, "recorder"):
                    m.recorder = self.recorder
        if getattr(cfg, "consumed", False):
            world.consumed = True           # HEGEL_CONSUMED reaches the entries however the world was built
        if getattr(cfg, "papers", False):
            world.papers = True             # HEGEL_PAPERS likewise
        if getattr(cfg, "borrowed_lookup", False):
            world.borrowed_lookup = True    # HEGEL_BORROWED_LOOKUP likewise
        self.days = Days(cfg.docs, getattr(cfg, "clock_shift_min", 0))
        self.memory = Memory(self.days, world)
        self.lookup = lookup.find           # (query, cache folder) -> the page he reads, or a note; tests put a stand-in here
        self.soul = cfg.soul_file.read_text(encoding="utf-8")
        self.voice_prompt = (cfg.repo / "mind/voices.md").read_text(encoding="utf-8")
        self.shelf = shelf.load(cfg.repo / "mind/shelf/index.json.gz", cfg.repo / "world/data/shelf_terms.json") if cfg.shelf else None
        # The LLM checker failed the factuality/cost evaluation. Audit callers
        # may still inject a guard explicitly; runtime flags never construct one.
        self.claim_guard = claim_guard

    def regenerate_prose(self, mind, text, unsupported, evidence, system=None):
        schema={'type':'object','properties':{'text':{'type':'string'}},'required':['text']}
        request=("Rewrite this text once, preserving its subject and argument, but removing or qualifying the unsupported claims. "
                 "Do not add events. Records are evidence; statements prove only words said.\n" + evidence +
                 "\nUnsupported claims: "+json.dumps(unsupported,ensure_ascii=False)+"\nText: "+text)
        raw=mind.chat([dict(role='system',content=system or self.soul),dict(role='user',content=request)],schema,max_tokens=1200)
        answer=contract.extract_json(raw)
        if not isinstance(answer,dict) or not isinstance(answer.get('text'),str):
            raise claim_check.ClaimProtocolError('Prose regeneration returned unusable JSON')
        return answer['text']

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
            "segments": [], "entries": [], "steps": [], "funnel": {}, "owl": None, "complete": False, "state": st,
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
            self.days.save(day)             # asleep until morning, it has no step to save it; unsaved, every tick made it again
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
        if (getattr(self.cfg, "seed_streams", False) or getattr(self.cfg, "record_calls", False)) and callable(getattr(self.mind, "at", None)):
            self.mind.at(t.isoformat(timespec="minutes"))       # this moment's calls: their own seed stream, and their place in the record
        if "account" not in st:
            self.migrate(day, st)               # a day file from before the economy: its books are made on first need
        prev = next((s for s in reversed(day["steps"]) if "decision" in s), None)
        if getattr(self.cfg, "correspondent", False) and not st.get("asleep"):
            self.post_round(t, st)                  # letters from Munich: the outbox to the post, and an answer if it is due
        self._voice_retries = 0
        sit, ctx = self.world.situation(t, st, day, prev)
        if not getattr(self.cfg, "thesis_reminders", True):
            sit["on_mind"] = [line for line in sit.get("on_mind", []) if not line.startswith("Your theses: ")]
        if getattr(self.cfg, "echo_guard", False):        # T36, arm B: what he has said too often today, shown back to him
            said = report.echoes([s["decision"]["thought"] for s in day["steps"] if "decision" in s and s["decision"].get("thought")])
            if said:
                sit.setdefault("on_mind", []).append(ECHO_LINE.format(phrases=", ".join(f"“{p}”" for p in said)))
        if getattr(self.cfg, "wants", False):
            sit["wants"] = True                     # HEGEL_WANTS: the decision's schema gains `wants`, and its instructions a sentence
        remember = self.memory.recall(sit, ctx, day)
        if remember:
            sit["remember"] = remember
        if getattr(self.cfg, "notebook", False) and (st.get("notebook") or {}).get("text"):
            sit["notebook"] = st["notebook"]["text"]          # HEGEL_NOTEBOOK: what he has come to understand of this century
        ctx["recent"], ctx["known_text"] = self.memory.recent_thoughts(day), self.memory.known_text(day, sit)
        m = minute_of(t)
        t_start = time.time()
        refused, warnings, raw, result, attempts, source = [], [], "", None, 0, self.mind.source
        draws, drawn = getattr(self.cfg, "decision_draws", 1), None
        if (m >= BED_M or m < 240) and not st.get("asleep"):
            source = "bedtime"          # the world sends him to bed from a quarter past eight
        elif st.get("asleep") and not self.make_plan(day, t, sit, ctx) and not getattr(self.mind, "ready", True):
            refused.append(["the PC did not wake for the morning plan"])
            source = "away"             # no second wake in the same step; an awake PC that fumbled the plan still decides
        elif not self.greet(day, sit, ctx):
            refused.append(["the PC did not wake for a greeting"])
            source = "away"
        else:
            if getattr(self.cfg,'outcome_memory',False):
                sit['reconcile_payments'] = True
                store=records.current(day,sit,ctx)
                past=list(self.memory.before(t.date()))[:3]
                # The current snapshot wins; older snapshots retain their own dates.
                for old in past:
                    store['records'].extend(records.project(old)['records'])
                ctx['records']=store
                prior=[x for x in remember if 'as the owl wrote it up' in x or 'you thought:' in x][:1]
                prior=[('Prior interpretation, not event evidence: '+x)[:220] for x in prior]
                room=600-sum(len(x)+3 for x in prior)
                sit['remember']=records.recall(store, ' '.join(sit.get('present',[])),
                    limit=room,lines=8-len(prior))+prior
            sit["shelf"] = self.offer(day, sit, ctx, st)
            if sit["shelf"]:
                ctx["shelf"] = sit["shelf"]
                ctx["known_text"] += "\n" + "\n".join(x["text"] for x in sit["shelf"])         # what is open before him he has met
            system = self.soul + "\n\n" + contract.WANTS_LINE if sit.get("wants") else self.soul
            messages = [{"role": "system", "content": system}, {"role": "user", "content": contract.render(sit)}]
            try:
                for turn in range(3):
                    if turn == 0 and draws > 1:                    # T49: the first fresh reply among up to `draws`
                        raw, drawn = self.draw(messages, sit, ctx, st, draws)
                        attempts += drawn["n"]
                    else:
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
            result = self.quiet(st, t, sit, day)
        ans, plan = result
        wish = ans.pop("wants", None)               # a wish is read off the decision here and goes into no later prompt, nor into the decision's record
        if self.claim_guard and ans.get('thought'):
            proof=records.relevant(ctx['records'],ans['thought'])
            compact=records.relevant(ctx['records'],ans['thought'],limit=9000)
            ans=dict(ans,thought=self.claim_guard.protect(ans['thought'],proof,
                lambda bad:self.regenerate_prose(self.mind,ans['thought'],bad,compact),
                label=f"{day['date']} {sit['time']} diary"))
            wrong=self.world.problems(ans['thought'],ctx.get('known_text',''))
            if wrong:
                raise claim_check.ClaimProtocolError('Regenerated thought failed the knowledge check: '+'; '.join(wrong))
        beat = ctx["beat"]
        if source in ("mind", "stub"):
            self.count_funnel(day, t, st)                  # before the beat fires: what could have been shown at this moment
        yes = None
        if beat and source in ("mind", "stub") and beat.get("choice"):
            yes = self.ask_choice(self.plain(messages), self.unwish(raw), beat)
            if yes is None:
                beat = None                 # the PC went away before he answered: the offer is not made and stays open
        if beat and source in ("mind", "stub"):
            ctx["beat_entries"] = self.world.fire(beat, t, st)
            tally = day.setdefault("funnel", {}).setdefault(funnel_key(beat), dict.fromkeys(FUNNEL, 0))
            tally["shown"] += 1
            if beat.get("choice"):
                tally["yes" if yes else "no"] += 1
                ctx["beat_entries"] += self.world.settle_choice(beat, yes, st, t)
        if source in ("mind", "stub"):
            if ans.get("says") and ctx["present"]:
                ctx["purchases"] = plan["buys"] + [{"item": e["item"], "price": e["amount"]}
                                                       for e in ctx["public"] if e.get("k") == "expense" and e.get("settles") is True]
                ctx["reply"] = self.reply(day, sit, ctx, ans["says"], recipient=ans.get("speaks_to"))
            if beat and "beat_entries" in ctx and beat.get("talk") and self.world.talk_scene:
                self.give_talk(day, sit, ctx, self.plain(messages), self.unwish(raw), st)
            if ans["action"] == "write":
                ctx["manuscripts"] = self.memory.manuscripts(day, before_time=fmt(minute_of(t)))
                letter = post.last_letter(st, self.post_card()) if st.get("post") else None
                if letter:
                    ctx["manuscripts"] = ((ctx["manuscripts"] or "") + "\n\n" + letter).strip()
                ctx["writing"] = self.write(self.plain(messages), self.unwish(raw), ctx, st)
            if ans.get("looks_up"):
                ctx["read"] = self.look(ans["looks_up"], st, ctx["present"])
            elif self.world.papers and ans["action"] == "read" and ans["place"] == st["place"] == "home":
                ctx["read"] = self.paper(t, st)
        step = self.world.apply(ans, plan, sit, ctx, st, day)
        if ctx.get("paper") and source in ("mind", "stub") and ans.get("thought"):
            papers.trace(st, ctx["paper"], ans["thought"])          # the piece that opened this moment, and his first sentence about it
        if ctx.get("writing") and st.get("post"):
            post.written(st, ctx["writing"], t.date(), self.post_card())          # a letter to Munich goes to the post tomorrow
        if wish and sit.get("wants") and source in ("mind", "stub"):
            step["wants"] = wish
            day.setdefault("wishes", []).append({"t": step["t"], "place": sit["place"], "text": wish})      # the ledger: for Welt, `python3 -m world wishes`
        step["mind"] = {"source": source, "attempts": attempts, "latency_s": round(time.time() - t_start, 1)}
        if ctx.get("shelf") and source in ("mind", "stub"):
            step["shelf"] = [{"work": x["work"], "ref": x["ref"], "id": x["id"]} for x in ctx["shelf"]]
            # Save only the passage actually shown, not the model's interpretation.
            step["shelf_exposure"] = [{k: x[k] for k in ("work", "ref", "text")} for x in ctx["shelf"]]
        if drawn:
            step["mind"]["draws"] = drawn
        if getattr(self, "_voice_retries", 0):
            step["mind"]["voice_retries"] = self._voice_retries            # HEGEL_PROMISES: a promise the world refused, and the voice asked once more
        if ctx.get("promised"):
            step["promise"] = ctx["promised"][0] if len(ctx["promised"]) == 1 else ctx["promised"]
        if refused:
            step["mind"]["refused"] = refused
        if warnings:
            step["mind"]["warnings"] = warnings
        if beat and "beat_entries" in ctx:
            step["beat"] = beat["id"]
        day["steps"].append(step)
        log.info("%s %s %s → %s until %s (%s)", day["date"], step["t"], ans["action"], ans["place"], step["end"], source)
        return step

    def plain(self, messages):
        """The conversation of a decision for a call that is not a decision (the writing, the yes/no choice): with HEGEL_WANTS the system message
        is the instructions alone, without the sentence about `wants`. The messages themselves when it is off."""
        if not messages[0]["content"].endswith(contract.WANTS_LINE):
            return messages
        return [dict(messages[0], content=self.soul)] + [dict(m, content=self.unwish(m["content"])) if m["role"] == "assistant" else dict(m) for m in messages[1:]]

    @staticmethod
    def unwish(raw):
        """The reply as the later calls see it: without `wants`, so that a wish reaches no prompt. Unchanged when it carries none."""
        if '"wants"' not in raw:
            return raw
        ans = contract.extract_json(raw)
        if not isinstance(ans, dict) or "wants" not in ans:
            return raw
        return json.dumps({k: v for k, v in ans.items() if k != "wants"}, ensure_ascii=False)

    def count_funnel(self, day, t, st):
        """The day's count of the offers and beats at a moment he decided: `live` once a day when its conditions other than
        his place, its people and its time held; `eligible` for each moment all of them held. Reads the state, changes none."""
        funnel, pid = day.setdefault("funnel", {}), st["place"]
        for b in self.world.beats + self.world.sessions(t.date(), st):
            key = funnel_key(b)
            tally = funnel.get(key)
            if self.world.eligible(b, t, st, pid):
                tally = funnel.setdefault(key, dict.fromkeys(FUNNEL, 0))
                tally["live"], tally["eligible"] = 1, tally["eligible"] + 1
            elif not (tally and tally["live"]) and self.world.eligible(b, t, st, timed=False, placed=False):
                funnel.setdefault(key, dict.fromkeys(FUNNEL, 0))["live"] = 1

    def post_card(self):
        if getattr(self, "_post_card", None) is None:
            self._post_card = post.card()
        return self._post_card

    def post_round(self, t, st):
        """HEGEL_CORRESPONDENT: yesterday's letters go to the post; while he is at home in the post's hours, the letter
        from Munich comes if one is due (one call). If the mind is away or the letter unusable, it comes on a later step."""
        c, d, m = self.post_card(), t.date(), minute_of(t)
        post.start(st, d)
        post.to_post(st, d, c)
        if st.get("place") != "home" or st["post"].get("deliver") or not hm(c["deliver_from"]) <= m < hm(c["deliver_to"]):
            return
        what = post.due(st, d, c)
        if not what:
            return
        kind, answered = what
        try:
            raw = self.mind.chat(post.messages(st, kind, answered, d, c), post.LETTER_SCHEMA, max_tokens=900)
        except MindAway as e:
            log.warning("mind away for the letter from Munich: %s", e)
            return
        text = post.clean(raw)
        if text:
            post.arrived(st, kind, answered, text, d, c)
            log.info("a letter from %s (%s)", c["name"], kind)
        else:
            log.warning("the letter from Munich was unusable; it comes on a later step")

    def draw(self, messages, sit, ctx, st, draws):
        """T49 (world/prefer.py): up to `draws` replies to the same prompt; the first that the world accepts and that
        repeats no phrase of a thought shown under "Earlier today". Returns (the reply, the note for the record).
        World.check reads its inputs and changes none of them, so each reply is judged against the same state."""
        def check(raw):
            errors, _, rep = self.world.check(contract.extract_json(raw), sit, ctx, st)
            return errors, None if errors else rep[0]["thought"]
        keep = [] if getattr(self.cfg, "keep_draws", False) else None
        raw, note = prefer.choose(lambda: self.mind.decide(messages, sit), check,
                                  prefer.shown_thoughts(sit.get("earlier")), draws, away=MindAway, keep=keep)
        if keep and len(keep) > 1:
            self.keep_draws(ctx["t"], messages, keep, note)
        return raw, note

    def keep_draws(self, t, messages, keep, note):
        """HEGEL_KEEP_DRAWS: a decision that took more than one reply, with every reply the world judged, appended to
        <state>/draws/<date>.jsonl.gz. The local model's own replies, sorted by the world's fixed checks: preference data
        within the data rule (pc/FILTER-PAIRS.md). Never in the day file or the repository; a failure here costs nothing."""
        try:
            folder = self.cfg.state / "draws"
            folder.mkdir(parents=True, exist_ok=True)
            row = {"date": t.date().isoformat(), "t": t.strftime("%H:%M"), "soul": getattr(self.cfg, "soul_file", None) and self.cfg.soul_file.name,
                   "messages": messages, "draws": keep, "picked": note.get("picked")}
            with gzip.open(folder / f"{row['date']}.jsonl.gz", "at", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as e:                      # keeping data must never stop his day
            log.warning("draws not kept at %s: %s", t, e)

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
        return self.shelf.pick(parts, avoid=used, whole=getattr(self.cfg, 'shelf_whole', False), additions=getattr(self.cfg, "shelf_additions", False))

    def make_plan(self, day, t, sit, ctx):
        """On waking: one extra call for the day's intentions. With no usable answer he simply has no plan.
        False only when the mind is away."""
        messages = for_task([{"role": "system", "content": self.soul}, {"role": "user", "content": contract.render(sit, contract.PLAN_ASK)}], "day-planning")
        try:
            ask = getattr(self.mind, "chat_decision", self.mind.chat)
            items = self.world.plan_items(contract.extract_json(ask(messages, contract.PLAN_SCHEMA, max_tokens=500)), ctx)
        except MindAway as e:
            log.warning("mind away for the plan at %s: %s", sit["time"], e)
            return False
        if not items:
            log.warning("no usable plan at %s", sit["time"])
            return True
        day["plan"], ctx["plan"] = {"written": fmt(minute_of(t)), "items": items}, items
        self.world.show_plan(sit, day)
        return True

    def voice_repairs(self):
        """HEGEL_VOICE_REPAIRS (config.py): is the switch on."""
        return getattr(getattr(self, "cfg", None), "voice_repairs", False) is True

    def voice(self, cid, day, sit, says, purchases=None, lead=None):
        """One call: the person cid answers what he said, or speaks first when says is None. {by, says, does}, or None
        when the answer is unusable. MindAway goes up."""
        c = self.world.cast[cid]
        remember = self.memory.moments(c, day, list(self.memory.before(date.fromisoformat(day["date"]))), voice=True)
        where = self.world.places[sit["place"]]["name"]
        people = day.get("state", {}).get("people")
        first_meeting = cid not in people if people is not None else None
        meal_status = None
        if cid == "ramesh" and sit["place"] == "home" and day.get("state") is not None:
            when = at_dt(date.fromisoformat(day["date"]), hm(sit["time"]))
            meal_status = (self.world.served(when, day["state"]) or "none") + ". " + self.world.meal_status(when, day["state"])
        vf = getattr(getattr(self, "cfg", None), "voice_facts", False) is True
        vr = self.voice_repairs()
        menu = getattr(self.world, "menu", {}).get(cid) if getattr(self.world, "promises", False) else None      # HEGEL_PROMISES: what this person may promise
        schema = contract.voice_schema(menu)
        extra = {"today": day["date"]} if menu and day.get("date") else {}
        facts = voices.recorded_facts(self.world, cid, day.get("state") or {}, **({"voice_facts": True} if vf else {}), **extra)
        facts += voices.paid_here(self.world.places[sit["place"]], day.get("entries", []))
        if getattr(getattr(self, 'cfg', None), 'outcome_memory', False):
            facts += voices.recorded_receipts(day, sit['place'])
        if self.world.talk_scene:
            facts += [x for x in [self.world.open_line(sit["place"], at_dt(date.fromisoformat(day["date"]), hm(sit["time"])))] if x]       # HEGEL_TALK_SCENE: the holiday, and whether this place is open
        messages = [{"role": "system", "content": self.voice_prompt}, {"role": "user", "content": voices.render(c, sit, where, says, remember, first_meeting=first_meeting, purchases=purchases, meal_status=meal_status, world_facts=facts, **({"voice_facts": True} if vf else {}), **({"menu": menu} if menu else {}), **({"repairs": True} if vr else {}), **({"lead": lead} if lead else {}))}]
        voice_chat = getattr(type(self.mind), "chat_voice", None)
        ask = (lambda msgs: voice_chat(self.mind, msgs, schema, max_tokens=250)) if voice_chat else (lambda msgs: self.mind.chat(msgs, schema, max_tokens=250))
        reply = ask(messages)
        out = contract.extract_json(reply)
        said = voices.clean(c, out, **({"repairs": True} if vr else {}))
        if menu and said and isinstance(out, dict) and out.get("act") is not None and day.get("state") is not None:
            said = self.promised(cid, day, sit, menu, messages, reply, out, said, ask)
        return said

    def promised(self, cid, day, sit, menu, messages, reply, out, said, ask):
        """HEGEL_PROMISES, the check before he hears the reply: a promise the world cannot keep is refused with its reason and the voice asked once
        more (the same messages, its reply, one line). A second refusal, or a second answer that is unusable, drops the act and the first reply's
        words stand; an answer without an act is taken as it comes. A promise that stands is written down (World.promise_make) and its id rides
        on the reply as `promise`, for the caller to take off. MindAway on the second ask is no refusal: the first words stand, without the act."""
        st, c = day["state"], self.world.cast[cid]
        when = at_dt(date.fromisoformat(day["date"]), hm(sit["time"]))
        why = self.world.promise_problem(cid, out["act"], when, sit["place"], st)
        if why:
            self._voice_retries = getattr(self, "_voice_retries", 0) + 1
            log.info("promise refused at %s: %s", sit["time"], why)
            msgs = messages + [{"role": "assistant", "content": reply},
                               {"role": "user", "content": f"The world refuses this promise: {why}. Answer again; if you cannot promise it, do not."}]
            try:
                out = contract.extract_json(ask(msgs))
            except MindAway as e:
                log.warning("mind away for the second answer at %s: %s", sit["time"], e)
                return said
            again = voices.clean(c, out, **({"repairs": True} if self.voice_repairs() else {}))
            if again is None:
                return said
            if not isinstance(out, dict) or out.get("act") is None:
                return again
            why = self.world.promise_problem(cid, out["act"], when, sit["place"], st)
            if why:
                log.info("promise refused again at %s: %s", sit["time"], why)
                return said
            said = again
        return dict(said, promise=self.world.promise_make(cid, out["act"], said["says"], when, sit["place"], st)["id"])

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
            if said.get("promise"):
                ctx.setdefault("promised", []).append(said.pop("promise"))
            ctx["greeting"] = said
            sit["event"] += " " + voices.heard(said)
            ctx.setdefault("opened", []).append(f"greeting:{cid}")
            ctx["known_text"] += "\n" + voices.heard(said)
        return True

    def reply_facts(self, ctx):
        """HEGEL_VOICE_REPAIRS: what routing reads of this step: who spoke first (the greeting), and whom the beat that fired in it needs."""
        greeter = next((x[len("greeting:"):] for x in ctx.get("opened", []) if isinstance(x, str) and x.startswith("greeting:")), None)
        return {"greeting": greeter, "needs": (ctx.get("beat") or {}).get("needs", []) if "beat_entries" in ctx else []}

    def reply(self, day, sit, ctx, says, recipient=None):
        """The one he spoke to answers (one call). None if the mind is away or the answer is unusable."""
        try:
            vf = getattr(getattr(self, "cfg", None), "voice_facts", False) is True
            more = dict(facts=True) if vf else {}
            if vf or self.voice_repairs():
                more.update(purchases=ctx.get("purchases"), entries=day.get("entries"), segments=day.get("segments"), place=sit["place"])
            if self.voice_repairs():
                more["repairs"] = self.reply_facts(ctx)
            present = ctx["present"]
            if self.world.talk_scene:                        # HEGEL_TALK_SCENE: in the hall the officer answers, not the guard
                present = self.world.in_the_hall(present, day["state"], ctx["t"], sit["place"])
                recipient = recipient if recipient in present else None
            who = voices.pick(self.world.cast, says, present, recipient=recipient, **more)
            said = self.voice(who, day, sit, says, purchases=ctx.get("purchases"))
            if said and said.get("promise"):
                ctx.setdefault("promised", []).append(said.pop("promise"))
            return said
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
                return self.check_writing(w,ctx)
            log.info("writing: no text from a plain completion, falling back to the chat call")
        w = self.write_chat(messages, raw, ctx, st)
        if w:
            log.info("writing by chat call: %s", w["title"])
        return self.check_writing(w,ctx)

    def give_talk(self, day, sit, ctx, messages, raw, st):
        """HEGEL_TALK_SCENE: the talk beat has fired. He gives the lecture (ctx["lecture"]), and one listener asks one question about it
        (ctx["question"]). Neither is there if the mind is away or its answer is unusable: the talk has still happened."""
        w = self.lecture(day, ctx, messages, raw)
        if not w:
            return
        ctx["lecture"] = w
        lead = talk.question_lead(w["title"], talk.last_paragraph(w["text"]))
        try:
            ctx["question"] = self.voice("hall_listener", day, sit, None, lead=lead)
        except MindAway as e:
            log.warning("mind away for the question from the hall: %s", e)

    def lecture(self, day, ctx, messages, raw):
        """One writing call for the lecture, as write_chat makes one for a sitting: {title, kind, to, continues, text, about}, or None. What he
        draws on is the excerpts of his latest manuscripts (memory.manuscripts) and the index of his works. Names from after 1831 that he has
        not met: he is asked once to give it again without them, then it is dropped. The claim guard sees it as it sees any writing."""
        st = day["state"]
        request = talk.LECTURE_ASK + works.manuscripts(st)
        excerpts = self.memory.manuscripts(day, before_time=fmt(minute_of(ctx["t"])), limit=6000)
        if excerpts:
            request += "\n\n" + excerpts
        msgs = for_task(messages + [dict(role="assistant", content=raw), dict(role="user", content=request + "\n\n" + talk.LECTURE_FORMAT)], "writing")
        for attempt in range(2):
            try:
                reply = getattr(self.mind, "chat_writing", self.mind.chat)(msgs, talk.LECTURE_SCHEMA, max_tokens=talk.TOKENS)
            except MindAway as e:
                log.warning("mind away for the lecture: %s", e)
                return None
            w = talk.clean(contract.extract_json(reply))
            if not w:
                log.warning("lecture dropped: unusable JSON or too short")
                return None
            wrong = self.world.unmet(w["title"] + "\n" + w["text"], ctx["known_text"])
            if not wrong:
                return self.check_writing(w, ctx)
            msgs += [{"role": "assistant", "content": reply}, {"role": "user", "content":
                     "Give it again without " + ", ".join(f"'{x}'" for x in wrong) + ": you have not met them in Delhi, and in 1831 you could not know them. "
                     "Answer with the JSON object only."}]
        log.info("lecture dropped: %s", "; ".join(wrong))
        return None

    def check_writing(self,w,ctx):
        if w and self.claim_guard:
            proof=records.relevant(ctx['records'],w['text'])
            compact=records.relevant(ctx['records'],w['text'],limit=9000)
            text=self.claim_guard.protect(w['text'],proof,
                lambda bad:self.regenerate_prose(self.mind,w['text'],bad,compact),
                label=f"{ctx['t'].isoformat()} writing",context=w['title'])
            wrong=self.world.problems(text,ctx.get('known_text',''))
            if wrong:
                raise claim_check.ClaimProtocolError('Regenerated writing failed the knowledge check: '+'; '.join(wrong))
            return dict(w,text=text) if text.strip() else None
        return w

    def write_plain(self, messages, raw, ctx, st):
        """One small chat call says what the sitting is (title, kind, to, continues, about), then the text is a plain-text completion under a
        header in the style of his books (works.prompt), after two passages of his books each under a header that names its topic
        (works.exemplars, which are not part of the text). A completion that copies an exemplar or is off the subject (works.flaw), and names
        from after 1831 that he has not met, cannot be asked away here: the completion is made once more with another seed. None if no
        usable text came, and it is then for the chat call; MindAway only from the first call, when the chat call could not answer either."""
        msgs = for_task(messages + [{"role": "assistant", "content": raw}, {"role": "user", "content": works.sitting_ask(st)}], "planning")
        plan = works.outline(contract.extract_json(self.mind.chat(msgs, contract.SITTING_SCHEMA, max_tokens=300)))
        if not plan:
            log.info("writing: no usable account of what the sitting is")
            return None
        shown = works.exemplars(plan, ctx["t"].date(), self.cfg.repo)
        log.info("writing: exemplars %s", ", ".join(x["topic"] for x in shown) or "none")
        prompt, opening = works.prompt(plan, st, ctx["t"].date(), shown)
        if ctx.get('records'):
            # Preserve the writing examples. The context shares the existing
            # 9000-character manuscript allowance; the writing's header stays last.
            prefix=''.join(works.EXEMPLAR.format(**x) for x in shown)
            room=min(3000,9000-len(prompt)-45)
            factual=records.relevant(ctx['records'],plan['about'],limit=room,view=getattr(self.cfg,'evidence_view','full'))
            body = prompt[len(prefix):]
            prompt=prefix+'[Typed records for this sitting:\n'+factual+']\n'+body
            if getattr(self.cfg, 'evidence_view', 'full') == 'compact':
                prompt = prompt_budget.fit(self.mind, lambda n: prefix + '[Typed records for this sitting:\n' +
                    records.compact(ctx['records'], plan['about'], limit=n) + ']\n' + body, room)
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
        request = works.ask(st, ctx["t"].date(), letter_register=getattr(getattr(self, "cfg", None), "letter_register", False) is True)
        if ctx.get("manuscripts"):
            manuscript=ctx['manuscripts'][:6000] if ctx.get('records') else ctx['manuscripts']
            request += '\n\n'+manuscript
        compact_view = bool(ctx.get('records')) and getattr(self.cfg, 'evidence_view', 'full') == 'compact'
        def build(room):
            ask = request
            if ctx.get('records'):
                ask += '\n\n' + records.relevant(ctx['records'], limit=room, view=getattr(self.cfg, 'evidence_view', 'full'))
            return for_task(messages + [dict(role='assistant', content=raw), dict(role='user', content=ask)], 'writing')
        msgs = prompt_budget.fit(self.mind, build, 3000,
            thinking=bool(getattr(self.cfg, 'writing_reasoning_tokens', 0))) if compact_view else build(3000)
        for attempt in range(2):
            try:
                if compact_view and callable(getattr(self.mind, 'prompt_tokens', None)):
                    size = self.mind.prompt_tokens(msgs, thinking=bool(getattr(self.cfg, 'writing_reasoning_tokens', 0)))
                    if size > prompt_budget.MAX_TOKENS:
                        raise prompt_budget.PromptBudgetError(f'Writing retry has {size} tokens, above {prompt_budget.MAX_TOKENS}')
                writing_call = getattr(self.mind, "chat_writing", self.mind.chat)
                reply = writing_call(msgs, contract.WRITE_SCHEMA, max_tokens=1100)
            except MindAway as e:
                log.warning("mind away for the writing: %s", e)
                return None
            w = works.clean(contract.extract_json(reply))
            if not w:
                log.warning("writing dropped: unusable JSON or empty manuscript")
                return None
            if w["continues"] and not works.find(st.get("works") or [], w["title"]):
                log.warning("writing: unknown continuation title %r", w["title"])
                if attempt:
                    log.warning("writing dropped: continuation still names no existing manuscript")
                    return None
                titles = [x["title"] for x in (st.get("works") or [])[-5:]]
                correction = ("That title is not an existing manuscript. To continue a manuscript, use its existing title exactly. "
                              "Recent existing titles: " + json.dumps(titles, ensure_ascii=False) + ". "
                              "For a new work, set continues to false. Do not invent an earlier sitting. "
                              "Answer with the JSON object only.")
                msgs += [{"role": "assistant", "content": reply}, {"role": "user", "content": correction}]
                continue
            wrong = self.world.unmet(w["title"] + "\n" + w["text"], ctx["known_text"])
            if not wrong:
                return dict(w, mode="chat")
            msgs += [{"role": "assistant", "content": reply}, {"role": "user", "content":
                     "Write it again without " + ", ".join(f"'{x}'" for x in wrong) + ": you have not met them in Delhi, and in 1831 you could not know them. "
                     "Answer with the JSON object only."}]
        log.info("writing dropped: %s", "; ".join(wrong))
        return None

    def look(self, query, st, present=()):
        """He looks something up on his phone: the page he reads, {title, text, source, url}, or {note} for what went wrong.
        HEGEL_BORROWED_LOOKUP: with no phone of his own, whoever with a phone is with him looks it up, and the answer says who ("by")."""
        if not (st["tech"]["phone"] and st["tech"]["sim"]):
            by = self.world.phone_holder(present)
            if not by:
                return {"note": "You have nothing to look it up on."}
            return dict(self.lookup(query, self.cfg.state / "lookup"), by=by)
        return self.lookup(query, self.cfg.state / "lookup")

    def paper(self, t, st):
        """HEGEL_PAPERS: the next piece of today's papers that he has not read, as {paper, title, source, url, date, i}: no text, which
        the next situation takes from the state folder. None when the papers are read or were not kept."""
        d, done = t.date(), (st.get("today") or {}).get("papers_read", [])
        for i, p in enumerate(self.world.feeds.pieces(d) if self.world.feeds else []):
            if i not in done:
                st.setdefault("today", {})["papers_read"] = done + [i]
                return {"paper": True, "title": p["title"], "source": p["source"], "url": p["link"], "date": d.isoformat(), "i": i}
        return None

    QUIET_OUT = 2           # quiet steps he may stay out before he goes home: an hour
    EAT_OUT = "khan"        # where he eats when nothing is cooked at home: a dhaba in Khan Market

    def quiet(self, st, t, sit, day=None):
        """No usable answer: he keeps the household's day, without a thought on the page. At night he goes to bed.
        At home he eats the meal Ramesh lays out, once, and between meals the plate he asks for when hungry.
        When nothing is cooked at home (Ramesh's day off, or the kitchen shut for an unpaid bill), he eats at a dhaba
        in Khan Market if it is open and he has the cash. Out, he goes home when the place closes, when he is hungry,
        when a meal is laid out or after an hour."""
        m, cur, buys = minute_of(t), st["place"], []
        if m >= BED_M or m < 240:
            action, dest = "sleep", "home"
        elif cur == "home":
            if self.quiet_meal(st, t):
                action, dest = "eat", "home"
            elif self.eat_out(st, t):
                action, dest = "walk", self.EAT_OUT
            else:
                action, dest = "rest", "home"
        elif cur == self.EAT_OUT and self.wants_food(st, t) and (meal := self.dhaba(st, t)):
            action, dest, buys = "eat", cur, [meal]
        elif (cur not in sit["open_now"] or st.get("today", {}).get("hunger") or self.world.served(t, st)
              or self.quiet_out(day, cur) >= self.QUIET_OUT):
            action, dest = "walk", "home"
        else:
            action, dest = "stay", cur
        ans = {"thought": None, "action": action, "place": dest, "minutes": 30, "says": None, "revision": None,
               "buys": [{"item": b["item"], "price_inr": b["price"]} for b in buys]}
        plan = {"moves": dest != cur, "dest": dest, "arrival": t + timedelta(minutes=self.world.walk(cur, dest)), "buys": buys}
        return ans, plan

    def eaten(self, st, t, name):
        """Has he eaten since this meal's window opened today?"""
        start = at_dt(t.date(), MEAL_WINDOWS[name][0])
        return bool(st.get("last_meal") and datetime.fromisoformat(st["last_meal"]) >= start)

    def wants_food(self, st, t):
        """A meal's window is open and he has not eaten in it, or he is hungry."""
        name = meal_at(minute_of(t))
        return bool((name and not self.eaten(st, t, name)) or st.get("today", {}).get("hunger"))

    def dhaba(self, st, t):
        """The cheapest meal at the dhaba, if it is open now and he can pay for it."""
        meals = [x for x in self.world.places[self.EAT_OUT].get("sells", []) if x.get("food") == "meal"]
        cheap = min(meals, key=lambda x: x["price"], default=None)
        if not cheap or cheap["price"] > st["imprest"] or not self.world.is_open(self.EAT_OUT, t, st):
            return None
        return {"item": cheap["item"], "price": cheap["price"], "food": "meal"}

    def eat_out(self, st, t):
        """Nothing will be cooked at home (Ramesh is not there, or the kitchen is shut) and he wants food: the dhaba,
        if it is open when he gets there and he has the cash."""
        if not self.wants_food(st, t):
            return False
        if "ramesh" in self.world.present_ids("home", t, st) and not self.world.kitchen(st, t):
            return False
        arrival = t + timedelta(minutes=self.world.walk("home", self.EAT_OUT))
        return self.dhaba(st, arrival) is not None

    def quiet_meal(self, st, t):
        """At home without a mind: the laid-out meal he has not yet eaten, or Ramesh's plate if he is hungry."""
        if name := self.world.served(t, st):
            return not self.eaten(st, t, name)
        soon = any(0 < a - minute_of(t) <= 60 for a, _ in MEAL_WINDOWS.values())     # no plate an hour before a meal
        return bool(st.get("today", {}).get("hunger") and not soon and self.world.plate(t, st)) or bool(st.get("today", {}).get("laid") and self.world.plate(t, st))

    @staticmethod
    def quiet_out(day, place):
        """How many quiet steps in a row he has already spent at this place away from home."""
        n = 0
        for s in reversed((day or {}).get("steps", [])):
            if "decision" not in s:
                continue
            if s.get("mind", {}).get("source") not in ("away", "quiet") or s["decision"].get("place") != place:
                break
            n += 1
        return n

    def ask_choice(self, messages, raw, beat):
        """His yes or no to an offer: True or False, or None when the PC went away before it answered (not a no)."""
        q = beat["choice"]["question"]
        msgs = messages + [{"role": "assistant", "content": raw},
                           {"role": "user", "content": f"For the record, one word: {q} Answer {{\"answer\": \"yes\"}} or {{\"answer\": \"no\"}}."}]
        try:
            a = contract.extract_json(self.mind.chat(for_task(msgs, "choice"), CHOICE_SCHEMA, max_tokens=20, temperature=0))
            return isinstance(a, dict) and a.get("answer") == "yes"
        except MindAway:
            return None

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
        # Days.load returns a distinct object. When this is still the latest
        # day, update the state on the object that will actually be saved.
        if latest["date"] == day["date"]:
            latest = day
        st = latest["state"]
        weekday = datetime.fromisoformat(day["date"]).strftime("%A")
        n = st.get("depesche_n", 0) + 1 if weekday == self.cfg.depesche_day else None
        known = self.memory.known_before(day["date"]) + "\n" + encountered_text(day)
        if (getattr(self.cfg, "seed_streams", False) or getattr(self.cfg, "record_calls", False)) and callable(getattr(self.owl_mind, "at", None)):
            self.owl_mind.at(f"owl|{day['date']}")
        written = owl.write(self.cfg, day, st, self.owl_mind, depesche_n=n, problems=lambda text: self.world.problems(text, known),
                            flag=self.world.flag, topic=self.world.topic, claim_guard=self.claim_guard,
                            notebook=getattr(self.cfg, "notebook", False))
        written["written"] = fmt(minute_of(now))
        day["owl"] = written
        if n:
            st["depesche_n"] = n
        self.days.save(day)
        if latest["date"] != day["date"]:
            self.days.save(latest)
        log.info("the owl wrote up day %s", day["n"])
        return [day["date"], latest["date"]]

    def tick(self, now):
        if self.git:
            try:
                self.git.push_pending()     # a push the network refused earlier goes out within a minute, not at the next step
            except GitError as e:
                log.warning("could not push held-back commits: %s", e)
        owl_day = self.owl_ready(now)
        if not owl_day and not self.due(now):
            return []           # most minutes: nothing to decide, no network
        if getattr(self, "recorder", None):
            self.recorder.tick(now, calls.folder_hash(self.cfg.state / "feeds"))
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
