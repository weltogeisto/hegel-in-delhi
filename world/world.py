"""The world: places and hours, the cast, the Hegde file, the rules. It decides when Hegel must decide,
tells the mind what is happening, checks the answer, and turns it into the day's segments and entries."""
import copy
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

from . import contract
from .clock import IST, WEEKDAYS, fmt, hm, minute_of, sun

DATA = Path(__file__).resolve().parent / "data"
DAYNAMES = [w[:3] for w in WEEKDAYS]
SPRITES = {"frock": "frock", "shirt": "shirt", "kurta": "kurta", "kurta2": "kurta", "bandhgala": "bandhgala", "nightshirt": "nightshirt"}
NOW = {"read": "Reading {at}.", "write": "Writing {at}.", "buy": "Shopping {at}.", "eat": "Eating {at}.",
       "rest": "Resting {at}.", "stay": "{At}.", "sleep": "Asleep."}
STROLL = {"lodhi": "Walking the paths of Lodhi Gardens.", "khan": "Going from shop to shop in Khan Market."}
LUNCH = ["dal, rice, bhindi and curd", "rajma, rice and a cucumber raita", "kadhi, rice and aloo gobhi", "chhole, rotis and onions in lemon"]
DINNER = ["rotis, dal makhani and a bowl of curd", "khichdi with ghee and papad", "rotis, palak paneer and dal", "vegetable pulao and raita"]
BREAKFAST = ["aloo parathas, curd and pickle", "poha with peanuts and a pot of tea", "idli with sambar and coconut chutney",
             "toast, butter and a plate of cut papaya"]
MEAL_WINDOWS = {"breakfast": (420, 570), "lunch": (780, 870), "dinner": (1170, 1230)}   # laid out at home while Ramesh is there
HUNGRY_H, VERY_HUNGRY_H, TIRED_H, TIRED_M = 5, 8, 16, 10_000        # hours since a meal, hours awake, metres walked
WALK_M, HOT_C = 75, 33                  # metres a minute; from this temperature walking counts one and a half times
NUMBERS = "zero one two three four five six seven eight nine ten eleven twelve".split()
PLAN_TIME = re.compile(r"(\d{1,2}):(\d{2})$")


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def wordlist(name, plural=""):
    """data/<name>: one word or phrase a line, # for comments. A regex for them as whole words, any case."""
    lines = (DATA / name).read_text(encoding="utf-8").splitlines()
    terms = [x.strip() for x in lines if x.strip() and not x.strip().startswith("#")]
    return re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")" + plural + r"\b", re.I) if terms else None


def meal_at(m):
    """The meal whose window minute m of the day falls in."""
    return next((k for k, (a, b) in MEAL_WINDOWS.items() if a <= m < b), None)


def repeats(a, b):
    """Does thought a closely repeat thought b? The same first six words, or half its word-trigrams in common."""
    wa, wb = (re.findall(r"\w+", x.lower()) for x in (a, b))
    if len(wa) >= 6 and wa[:6] == wb[:6]:
        return True
    ga, gb = ({tuple(w[i:i + 3]) for i in range(max(1, len(w) - 2))} for w in (wa, wb))
    return len(ga & gb) / len(ga | gb) >= 0.5


def hours_ago(minutes):
    h = max(1, round(minutes / 60))
    if minutes < 30:
        return "just now"
    return "an hour ago" if h == 1 else f"{NUMBERS[h] if h < len(NUMBERS) else h} hours ago"


def days_match(spec, d):
    """'daily', 'Mon-Fri', 'Tue-Sun', 'Mon,Wed,Sat'."""
    if spec == "daily":
        return True
    wd = d.weekday()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = (DAYNAMES.index(x) for x in part.split("-"))
            if (a <= wd <= b) if a <= b else (wd >= a or wd <= b):
                return True
        elif DAYNAMES.index(part) == wd:
            return True
    return False


def at_dt(d, minutes):
    return datetime(d.year, d.month, d.day, tzinfo=IST) + timedelta(minutes=minutes)


def names(lst):
    lst = list(lst)
    if len(lst) < 2:
        return "".join(lst)
    return ", ".join(lst[:-1]) + " and " + lst[-1]


class World:
    def __init__(self, feeds=None):
        p = load("places.json")
        self.places, self.walks = p["places"], p["walk"]
        self.cast = load("cast.json")["cast"]
        self.beats = load("plot.json")["beats"]
        self.holidays = load("holidays.json")["holidays"]
        self.never = wordlist("never.txt")
        self.after = wordlist("after_1831.txt", "s?")
        self.feeds = feeds
        self._wx = {}

    # ── calendar and hours ──────────────────────────────────────────
    def holiday(self, d):
        return self.holidays.get(d.isoformat())

    def hours(self, pid, d):
        """(open, close) in minutes for date d, 'always', or None if closed all day."""
        spec = self.places[pid]["hours"]
        if spec == "always":
            return "always"
        if self.places[pid].get("holidays_closed") and self.holiday(d):
            return None
        rise, set_ = sun(d)
        for days, (a, b) in spec.items():
            if days_match(days, d):
                return (rise if a == "sun" else hm(a), set_ if b == "sun" else hm(b))
        return None

    def host_here(self, pid, t, state):
        host = self.places[pid].get("host")
        return host is None or host in self.present_ids(pid, t, state)

    def is_open(self, pid, t, state, margin=0):
        h = self.hours(pid, t.date())
        if h == "always":
            return True
        if not h:
            return False
        m = minute_of(t)
        return h[0] <= m and m + margin < h[1] and self.host_here(pid, t, state)

    def closes(self, pid, t, state):
        """Minute of the day this place closes (or the host leaves), or None."""
        h = self.hours(pid, t.date())
        if h in ("always", None):
            return None
        close = h[1]
        host = self.places[pid].get("host")
        if host:
            for w in self.cast[host]["where"]:
                if w["place"] == pid and hm(w["from"]) <= minute_of(t) < hm(w["to"]):
                    close = min(close, hm(w["to"]))
        return close

    def open_places(self, t, state):
        return [p for p in self.places if self.is_open(p, t, state)]

    def place_info(self, d):
        """What the Places tab says about each place on date d."""
        info = {}
        for pid, pl in self.places.items():
            h = self.hours(pid, d)
            if h == "always":
                continue
            if pl.get("host"):
                info[pid] = {"note": "Only as a member's guest."}
            elif not h:
                nxt = d + timedelta(days=1)
                while not self.hours(pid, nxt) and (nxt - d).days < 8:
                    nxt += timedelta(days=1)
                when = "tomorrow" if (nxt - d).days == 1 else WEEKDAYS[nxt.weekday()]
                info[pid] = {"note": f"Closed today. Open again {when}."}
            else:
                info[pid] = {"hours": f"{fmt(h[0])}–{fmt(h[1])}"}
        return info

    def walk(self, a, b):
        if a == b:
            return 0
        return self.walks.get(f"{a}-{b}") or self.walks[f"{b}-{a}"]

    def wake_time(self, d):
        rise, _ = sun(d)
        return rise - 16 + random.Random(f"wake|{d}").randint(-8, 8)

    # ── weather ─────────────────────────────────────────────────────
    def weather(self, d):
        if d not in self._wx:
            from .feeds import normal_hours
            self._wx[d] = self.feeds.weather(d) if self.feeds else {"source": "normal", "hours": normal_hours(d)}
        return self._wx[d]

    def wx_at(self, t):
        return self.weather(t.date())["hours"][t.hour]

    def weather_public(self, d):
        w = self.weather(d)
        return {"source": w["source"], "hours": [{k: h[k] for k in ("temp", "sky", "rain", "aqi")} for h in w["hours"]]}

    # ── people ──────────────────────────────────────────────────────
    def present_ids(self, pid, t, state):
        out = []
        d, m = t.date(), minute_of(t)
        flags = state.get("flags", {})
        for cid, c in self.cast.items():
            for i, w in enumerate(c["where"]):
                if w["place"] != pid or not days_match(w["days"], d):
                    continue
                if w.get("if") and not flags.get(w["if"]):
                    continue
                if hm(w["from"]) <= m < hm(w["to"]) and random.Random(f"{d}|{cid}|{i}").random() < w["p"]:
                    out.append(cid)
                    break
        return out

    def short(self, cid):
        return self.cast[cid]["short"]

    # ── wardrobe ────────────────────────────────────────────────────
    def garment(self, state, gid):
        return next((w for w in state["wardrobe"] if w["id"] == gid), None)

    def dress(self, state, pid, asleep=False):
        """What he wears for a segment at place pid."""
        owned = {w["id"] for w in state["wardrobe"]}
        if asleep:
            return "nightshirt" if "nightshirt" in owned else state["wearing"]
        if self.places[pid].get("formal") and state["flags"].get("bandhgala") == "collected":
            return "bandhgala"
        return "kurta" if "kurta" in owned else state["wearing"]

    def outfit_name(self, state):
        g = self.garment(state, state["wearing"])
        return g["item"].split(",")[0].lower() if g else state["wearing"]

    # ── the body ────────────────────────────────────────────────────
    def served(self, t, state):
        """The meal Ramesh has laid out at home at time t, if any."""
        name = meal_at(minute_of(t))
        return name if name and "ramesh" in self.present_ids("home", t, state) else None

    def feed(self, state, t, food):
        """A meal starts the clock again; a snack pushes hunger back two hours."""
        if food == "meal":
            state["last_meal"], state["snacks"] = t.isoformat(timespec="minutes"), 0
        else:
            state["snacks"] = state.get("snacks", 0) + 1

    def walked(self, state, t, minutes):
        """Metres on foot today, and the same weighted by the heat."""
        today, metres = state.setdefault("today", {}), minutes * WALK_M
        today["walked"] = today.get("walked", 0) + metres
        today["strain"] = today.get("strain", 0) + int(metres * (1.5 if self.wx_at(t)["temp"] >= HOT_C else 1))

    def needs(self, t, state):
        """The Body line, and what the body says once an episode: hungry, very hungry, tired."""
        today = state.setdefault("today", {})
        meal = datetime.fromisoformat(state["last_meal"]) if state.get("last_meal") else at_dt(t.date() - timedelta(days=1), 1200)
        woke = at_dt(t.date(), hm(today["woke"])) if today.get("woke") else None
        fed = min(t, meal + timedelta(hours=2 * state.get("snacks", 0)))
        hungry = (t - max(fed, woke or fed)).total_seconds() / 3600       # sleep does not make him hungry
        level = 2 if hungry > VERY_HUNGRY_H else 1 if hungry > HUNGRY_H else 0
        felt = []
        if level > today.get("hunger", 0):
            felt.append("You are very hungry." if level == 2 else "You are hungry.")
        if level:
            today["hunger"] = level          # after food it drops back, so the next episode speaks again
        else:
            today.pop("hunger", None)
        awake = (t - woke).total_seconds() / 3600 if woke else 0
        if "tired" not in today and (today.get("strain", 0) >= TIRED_M or awake >= TIRED_H):
            today["tired"] = True
            felt.append("You are tired.")
        snacks = state.get("snacks", 0)
        since = f" and {'a snack' if snacks == 1 else 'snacks'} since" if snacks else ""
        when = {0: "", 1: "yesterday "}.get((t.date() - meal.date()).days)
        last = "last meal more than a day ago" if when is None else \
            f"last meal {when}{fmt(minute_of(meal))}, {hours_ago((t - meal).total_seconds() / 60)}{since}"
        line = f"Body: {last}; walked {today.get('walked', 0) / 1000:.1f} km today"
        return line + (f"; awake since {today['woke']}." if woke else "."), felt

    # ── the plan ────────────────────────────────────────────────────
    def unmet(self, text, known):
        """Names from after 1831 in text that the record (known) has not met."""
        out = []
        for m in (self.after.finditer(text) if self.after and text else ()):
            term = m.group(1)
            if term.lower() not in [x.lower() for x in out] and not re.search(r"\b" + re.escape(term) + r"s?\b", known, re.I):
                out.append(term)
        return out

    def problems(self, text, known):
        """What the page will not publish in text: listed words, and names from after 1831 the record has not met."""
        out = [f"the word '{m.group(0)}'" for m in (self.never.finditer(text) if self.never and text else ())]
        return out + [f"'{x}', which you have not met in Delhi" for x in self.unmet(text, known)]

    def plan_items(self, out, ctx):
        """The usable intentions of a morning plan: a time, under 120 characters, nothing the page will not publish
        and nothing from after 1831 that he has not met. Invalid ones are dropped."""
        items, raw = [], out.get("plan") if isinstance(out, dict) else None
        for x in raw if isinstance(raw, list) else []:
            when, what = (x.get("time"), x.get("intention")) if isinstance(x, dict) else (None, None)
            at = PLAN_TIME.match(when.strip()) if isinstance(when, str) else None
            what = " ".join(what.split()) if isinstance(what, str) else ""
            if not at or int(at[1]) > 23 or int(at[2]) > 59 or not what or len(what) > 120:
                continue
            if (self.never and self.never.search(what)) or self.unmet(what, ctx.get("known_text", "")):
                continue
            items.append({"time": f"{int(at[1]):02d}:{at[2]}", "intention": what})
        return items[:6]

    def plan_line(self, day):
        items = (day.get("plan") or {}).get("items")
        return "Your plan for today: " + "; ".join(f"{i['time']} {i['intention'].rstrip('.')}" for i in items) + "." if items else None

    def show_plan(self, sit, day):
        """Put the day's plan on his mind, just above the Body line."""
        line = self.plan_line(day)
        if line:
            sit["on_mind"].insert(len(sit["on_mind"]) - 1, line)

    # ── the Hegde file ──────────────────────────────────────────────
    def _appointment(self, state, beat_id):
        return next((a for a in state["appointments"] if a["beat"] == beat_id), None)

    def expire(self, state, t):
        """Appointments whose fixed time has passed unmet become missed beats."""
        for a in list(state["appointments"]):
            beat = self.beat(a["beat"])
            if not beat.get("at"):
                continue
            end = at_dt(datetime.fromisoformat(a["date"]).date(), hm(beat["window"][1]))
            if t >= end:
                state["appointments"].remove(a)
                state.setdefault("missed", []).append(a["beat"])

    def beat(self, bid):
        return next(b for b in self.beats if b["id"] == bid)

    def eligible(self, b, t, state, pid=None, timed=True):
        """Does beat b want to fire at time t with Hegel at pid? With timed=False the time window is ignored."""
        d, m = t.date(), minute_of(t)
        if b["id"] in state["beats"] or b["id"] in state.get("missed", []):
            return None
        if b.get("from") and d.isoformat() < b["from"]:
            return None
        if any(x not in state["beats"] for x in b.get("after", [])):
            return None
        if b.get("if_missed") and b["if_missed"] not in state.get("missed", []):
            return None
        if b.get("on_appointment"):
            a = self._appointment(state, b["id"])
            if not a or a["date"] > d.isoformat() or (b.get("at") and a["date"] != d.isoformat()):
                return None
        if timed and b.get("window") and not hm(b["window"][0]) <= m < hm(b["window"][1]):
            return None
        variant = dict(b)
        if b.get("variants"):
            if pid not in b["variants"]:
                return None
            variant.update(b["variants"][pid])
        elif b.get("where") and pid is not None and b["where"] != pid:
            return None
        if pid is not None and any(c not in self.present_ids(pid, t, state) for c in variant.get("needs", [])):
            return None
        return variant

    def due_beat(self, t, state, pid):
        for b in self.beats:
            v = self.eligible(b, t, state, pid)
            if v:
                return v
        return None

    def interrupt(self, t0, end, state, pid):
        """The earliest fixed-time beat between t0 and end that needs Hegel where he will be."""
        best = end
        for b in self.beats:
            if not b.get("at"):
                continue
            at = at_dt(t0.date(), hm(b["at"]))
            if t0 < at < best and self.eligible(b, at, state, pid):
                best = at
        return best

    def fire(self, beat, t, state):
        """Apply a beat's effects. Returns entries for the page."""
        state["beats"].append(beat["id"])
        out = []
        if beat.get("public"):
            out.append({"k": beat.get("kind", "world"), "text": beat["public"]})
        if beat.get("file"):
            state["file"] = beat["file"]
        state["flags"].update(beat.get("flags", {}))
        for gid, status in beat.get("wardrobe", {}).items():
            g = self.garment(state, gid)
            if g:
                g["status"] = status
                out.append({"k": "wear", "item": g["item"], "status": status})
        if beat.get("on_appointment"):
            a = self._appointment(state, beat["id"])
            if a:
                state["appointments"].remove(a)
        ap = beat.get("appointment")
        if ap:
            d = t.date()
            if "weekday" in ap:
                d += timedelta(days=1)
                while DAYNAMES[d.weekday()] != ap["weekday"]:
                    d += timedelta(days=1)
            else:
                d += timedelta(days=ap["in_days"])
            state["appointments"].append({"date": d.isoformat(), "t": ap.get("t"), "what": ap["what"], "beat": ap["beat"]})
        return out

    def settle_choice(self, beat, yes, state):
        branch = beat["choice"]["yes" if yes else "no"]
        state["flags"].update(branch.get("flags", {}))
        if branch.get("file"):
            state["file"] = branch["file"]
        return [{"k": beat.get("kind", "world"), "text": branch["public"]}] if branch.get("public") else []

    # ── the situation ───────────────────────────────────────────────
    def situation(self, t, state, day, prev_step=None):
        """What Hegel knows at t, and what happens. Returns (situation, context for the rules)."""
        self.expire(state, t)
        d, m, pid = t.date(), minute_of(t), state["place"]
        today = state.setdefault("today", {})
        wx = self.wx_at(t)
        present = self.present_ids(pid, t, state)
        events = []          # (prompt, public entry or None)
        beat = self.due_beat(t, state, pid)
        for c in (beat or {}).get("brings", []):
            if c not in present:
                present.append(c)

        if state.get("asleep"):
            today["woke"] = fmt(m)
            line = f"You wake. {wx['sky'].capitalize()}, {wx['temp']} °C."
            hol = self.holiday(d)
            if hol:
                line += f" Today is {hol['name']}, a national holiday." + (" A dry day: no alcohol is sold." if hol.get("dry") else "")
            papers = self.feeds.headlines(d) if self.feeds else []
            where = "Ramesh has left the papers on the verandah." if "ramesh" in present else "The papers lie on the step where the hawker threw them."
            if papers:
                line += f" {where} Headlines: " + "; ".join(papers) + "."
            events.append((line, {"k": "world", "text": "Morning papers: " + " · ".join(f"“{x}”" for x in papers)} if papers else None))
        elif m == 0:
            events.append(("Midnight. The house is dark and quiet.", None))

        if prev_step and prev_step.get("arrived") == pid and pid != "home":
            close = self.closes(pid, t, state)
            line = f"You arrive at {self.places[pid]['name']}."
            if close:
                line += f" It closes at {fmt(close)}."
            events.append((line, None))

        if beat:
            events.append((beat["prompt"], None))

        if pid != "home" and not self.is_open(pid, t, state):
            events.append((f"{self.places[pid]['name']} is closing. You must leave.", None))
        elif pid != "home":
            close = self.closes(pid, t, state)
            if close and 0 < close - m <= 30 and not (prev_step and prev_step.get("arrived") == pid):
                events.append((f"{self.places[pid]['name']} closes at {fmt(close)}.", None))

        if pid == "home" and not state.get("asleep"):
            meal = meal_at(m)
            if meal == "breakfast" and "breakfast" not in today and "ramesh" in present:
                today["breakfast"] = True
                events.append((f"Ramesh has laid out breakfast: {random.Random(f'breakfast|{d}').choice(BREAKFAST)}.", None))
            if meal == "lunch" and "lunch" not in today:
                today["lunch"] = True
                if "ramesh" in present:
                    menu = random.Random(f"lunch|{d}").choice(LUNCH)
                    events.append((f"Ramesh has laid out lunch: {menu}.", None))
                else:
                    events.append(("Ramesh has his day off. There is no lunch at home today.", None))
            if meal == "dinner" and "dinner" not in today and "ramesh" in present:
                today["dinner"] = True
                menu = random.Random(f"dinner|{d}").choice(DINNER)
                events.append((f"Ramesh serves dinner before he goes home: {menu}.", None))
            cut = random.Random(f"power|{d}")
            if cut.random() < 0.06:
                at = cut.randint(1140, 1290)
                if at <= m < at + 90 and "power" not in today:
                    today["power"] = True
                    light = "Ramesh lights two candles." if "ramesh" in present else "You find candles in the kitchen drawer."
                    events.append((f"The power goes. The fan stops. {light}", {"k": "world", "text": "A power cut. The fan stops."}))
            if m >= 1380 and "late" not in today:
                today["late"] = True
                events.append(("It is late. The house is quiet.", None))

        outdoor = self.places[pid].get("outdoor")
        if outdoor and wx["rain"] >= 1 and today.get("rain_reported", -999) < m - 120:
            today["rain_reported"] = m
            heavy = wx["rain"] >= 4
            events.append(("Heavy rain begins." if heavy else "It begins to rain.",
                           {"k": "world", "text": "Heavy rain." if heavy else "Rain."}))
        if wx.get("aqi") and wx["aqi"] >= 300 and "bad_air" not in today and not state.get("asleep"):
            today["bad_air"] = True
            events.append((f"The air is very poor today: the index stands at {wx['aqi']}.", None))

        seen = set(today.get("seen", {}).get(pid, []))
        new = [c for c in present if c not in seen and not self.cast[c].get("background") and not (beat and c in beat.get("brings", []))]
        if new:
            known = set(state["people"])
            bits = [f"{self.cast[c]['name']} is here." if c in known else f"{self.short(c)} is here; you have not met." for c in new]
            events.append((" ".join(bits), None))
        today.setdefault("seen", {})[pid] = sorted(seen | set(present))

        body, felt = self.needs(t, state)
        events += [(x, None) for x in felt]
        if not events:
            part = "morning" if m < 720 else "afternoon" if m < 1020 else "evening" if m < 1260 else "night"
            events.append((f"Nothing in particular happens. The {part} goes on.", None))

        open_now = self.open_places(t, state)
        closes = {p: fmt(c) for p in open_now if (c := self.closes(p, t, state)) and c - m <= 180}
        for_sale = [f"{s['item']} ₹{s['price']}" for s in self.places[pid].get("sells", [])
                    if not s.get("needs_flag") or state["flags"].get(s["needs_flag"][0]) == s["needs_flag"][1]]
        if self.places[pid].get("books"):
            for_sale.append("books")
        on_mind = [f"The file: {state['file']}"]
        for a in state["appointments"]:
            when = datetime.fromisoformat(a["date"]).date()
            on_mind.append(f"{WEEKDAYS[when.weekday()]} {when.day} {when.strftime('%B')}{' ' + a['t'] if a.get('t') else ''}: {a['what']}.")
        flag = state["flags"].get("bandhgala")
        if flag == "ordered":
            on_mind.append("Your bandhgala is with Masterji at Khan Market, promised for Thursday 8 October.")
        elif flag == "ready":
            on_mind.append("Your bandhgala is ready at Masterji's. The balance is ₹3,500.")
        if state.get("theses"):
            on_mind.append("Your theses: " + "; ".join(f"{x['text']} ({x['status']})" for x in state["theses"]) + ".")
        on_mind.append(body)
        earlier = []
        for s in (day.get("steps") or [])[-6:]:
            dec = s.get("decision") or {}
            if not dec.get("thought"):
                continue
            first = re.split(r"(?<=[.!?])\s", dec["thought"].strip())[0]
            earlier.append(f"{s['t']} {dec['action']} ({dec['place']}): {first}")
        hol = self.holiday(d)
        sit = {
            "id": f"{d.isoformat()}T{fmt(m)}",
            "day": f"{WEEKDAYS[d.weekday()]} {d.day} {d.strftime('%B')}" + (f" ({hol['name']})" if hol else ""),
            "time": fmt(m), "place": pid,
            "weather": f"{wx['temp']} °C, {wx['sky']}", "aqi": wx.get("aqi") or "unknown",
            "imprest_left": state["imprest"], "outfit": self.outfit_name(state),
            "present": [self.short(c) for c in present], "open_now": open_now, "closes": closes,
            "for_sale": for_sale, "on_mind": on_mind, "earlier": earlier,
            "event": " ".join(p for p, _ in events),
        }
        self.show_plan(sit, day)
        ctx = {"t": t, "present": present, "beat": beat, "public": [e for _, e in events if e]}
        return sit, ctx

    # ── the rules ───────────────────────────────────────────────────
    def check(self, ans, sit, ctx, state):
        """Errors (the mind must decide again), warnings, and the repaired decision with its plan."""
        errors, warnings = contract.check_shape(ans)
        if errors:
            return errors, warnings, None
        ans = copy.deepcopy(ans)
        t, cur = ctx["t"], state["place"]
        action, dest = ans["action"], ans["place"]
        if action == "walk" and dest == cur:
            warnings.append("walks to where he already is; treated as stay")
            ans["action"] = action = "stay"
        if action == "sleep" and dest != "home":
            errors.append("you can sleep only at home")
        moves = dest != cur
        arrival = t + timedelta(minutes=self.walk(cur, dest)) if moves else t
        if moves and not self.is_open(dest, arrival, state, margin=10 if action != "walk" else 0):
            h = self.hours(dest, arrival.date())
            name = self.places[dest]["name"]
            if self.places[dest].get("host") and h and h != "always" and h[0] <= minute_of(arrival) < h[1]:
                errors.append(f"{name} admits {self.places[dest]['host_note']}")
            elif h and h != "always" and minute_of(arrival) < h[0]:
                errors.append(f"{name} opens at {fmt(h[0])}; walking there you would arrive at {fmt(minute_of(arrival))}")
            else:
                errors.append(f"{name} is closed when you would arrive ({fmt(minute_of(arrival))})")
        if not moves and cur != "home" and not self.is_open(cur, t, state):
            errors.append(f"{self.places[cur]['name']} has closed; you must leave")
        # money
        where = dest
        pl = self.places[where]
        hol = self.holiday(arrival.date())
        buys = []
        for b in ans["buys"]:
            item, price = b["item"].strip(), b["price_inr"]
            low = item.lower()
            match = next((s for s in pl.get("sells", []) if any(k in low for k in s["match"])), None)
            if match:
                if match.get("alcohol") and hol and hol.get("dry"):
                    errors.append(f"today is a dry day ({hol['name']}); no alcohol is sold")
                    continue
                nf = match.get("needs_flag")
                if nf and state["flags"].get(nf[0]) != nf[1]:
                    errors.append(match.get("not_ready", f"'{item}' is not to be had yet"))
                    continue
                if price != match["price"]:
                    warnings.append(f"price of '{item}' set to ₹{match['price']}")
                buys.append({"item": match["item"], "price": match["price"], "garment": match.get("garment"), "wear": match.get("wear"),
                             "food": match.get("food")})
            elif pl.get("books") and any(k in low for k in pl["books"]["match"]):
                lo, hi = pl["books"]["range"]
                if not lo <= price <= hi:
                    errors.append(f"₹{price} is not a believable price for '{item}' here (books run ₹{lo}–{hi:,})")
                buys.append({"item": item, "price": price})
            elif pl.get("range"):
                lo, hi = pl["range"]
                if not lo <= price <= hi:
                    errors.append(f"₹{price} is not a believable price for '{item}' {pl['at']}")
                buys.append({"item": item, "price": price})
            else:
                errors.append(f"nothing is sold {pl['at']}")
                break
        spent = sum(b["price"] for b in buys)
        if spent > state["imprest"]:
            errors.append(f"that costs ₹{spent:,} and only ₹{state['imprest']:,} of the imprest is left")
        if pl.get("entry") and action != "walk" and where not in state.get("today", {}).get("tickets", []):
            if not any(any(k in b["item"].lower() for k in pl["entry"]["match"]) for b in buys):
                errors.append(f"you need an entry ticket for {pl['name']}; buy one at the counter")
        # words the page will not publish
        for k in ("thought", "says", "revision"):
            if ans.get(k) and self.never and self.never.search(ans[k]):
                errors.append(f"the page cannot publish the word '{self.never.search(ans[k]).group(0)}'; say it otherwise")
        # what he cannot know from 1831, and what he has just thought
        met = []
        for k in ("thought", "says", "revision"):
            met += [x for x in self.unmet(ans.get(k), ctx.get("known_text", "")) if x not in met]
        errors += [f"you have not met '{x}' in Delhi; in 1831 you could not know it" for x in met[:3]]
        again = next((t for t, text in reversed(ctx.get("recent", [])) if repeats(ans["thought"], text)), None)
        if again:
            errors.append(f"this repeats what you thought at {again}; think something new")
        if ans["says"] and not ctx["present"]:
            warnings.append("talks although nobody is present")
        plan = {"moves": moves, "dest": dest, "arrival": arrival, "buys": buys}
        return errors, warnings, (ans, plan)

    # ── the step ────────────────────────────────────────────────────
    def apply(self, ans, plan, sit, ctx, state, day):
        """Turn a checked decision into segments and entries, and move the state on. Returns the step record."""
        t0, cur = ctx["t"], state["place"]
        dest, arrival = plan["dest"], plan["arrival"]
        action = ans["action"]
        d = t0.date()
        midnight = at_dt(d, 1440)
        segs, entries = [], []

        def entry(t, e):
            e = dict(e)
            e["t"] = fmt(minute_of(t))
            entries.append(e)

        def dress(t, pid, asleep=False):
            want = self.dress(state, pid, asleep)
            if want != state["wearing"]:
                state["wearing"] = want
                g = self.garment(state, want)
                if g:
                    g["status"] = f"Worn from {fmt(minute_of(t))}."
                    entry(t, {"k": "wear", "item": g["item"], "status": g["status"], "sprite": SPRITES.get(want, "kurta")})

        for e in ctx["public"]:
            entry(t0, e)
        if ctx.get("beat_entries"):
            for e in ctx["beat_entries"]:
                entry(t0, e)
        for c in ctx["present"]:
            if c not in state["people"] and not self.cast[c].get("background"):
                state["people"].append(c)
                card = self.cast[c].get("card")
                if card:
                    entry(t0, {"k": "people", "name": self.cast[c]["name"], "role": self.cast[c]["role"], "text": card})
        if ctx.get("plan"):
            entry(t0, {"k": "plan", "items": ctx["plan"]})
        if ans.get("thought"):
            entry(t0, {"k": "diary", "text": ans["thought"].strip()})
        if ans.get("says"):
            who = [self.cast[c]["name"] for c in ctx["present"] if not self.cast[c].get("background")] or \
                  [self.cast[c]["name"] for c in ctx["present"]]
            e = {"k": "said", "text": ans["says"].strip()}
            if who:
                e["to"] = names(who)
            entry(t0, e)

        t = t0
        if plan["moves"]:
            dress(t0, dest)
            segs.append({"from": t0, "to": arrival, "mode": "walk", "a": cur, "b": dest})
            self.walked(state, t0, self.walk(cur, dest))
            state["place"] = dest
            t = arrival
        arrived = dest if plan["moves"] and action == "walk" else None
        night = False

        if action != "walk":
            asleep = action == "sleep"
            night = asleep and (minute_of(t) >= 1200 or minute_of(t) < 240)
            if night:
                end = at_dt(d, self.wake_time(d)) if minute_of(t) < 240 else midnight
            else:
                end = t + timedelta(minutes=min(ans["minutes"], 120) if asleep else ans["minutes"])
                close = self.closes(dest, t, state)
                if close is not None and dest != "home":
                    end = min(end, at_dt(d, close))
                end = self.interrupt(t, end, state, dest)
                end = min(end, midnight)
            if end <= t:
                end = t + timedelta(minutes=5)
            dress(t, dest, asleep=night)
            pl = self.places[dest]
            if dest == "home":
                mode = "stand" if action == "talk" else "inside"
            elif dest in STROLL and action in ("stay", "talk", "buy"):
                mode = "stroll"
            elif dest == "khan" and action in ("eat", "read", "write", "rest"):
                mode = "inside"
            elif dest in ("safdarjung", "gandhi", "lodhi"):
                mode = "stand"
            else:
                mode = "inside"
            if action == "talk":
                who = [self.cast[c]["name"] for c in ctx["present"] if not self.cast[c].get("background")] or \
                      [self.cast[c]["name"] for c in ctx["present"]]
                now = f"Talking with {names(who)} {pl['at']}." if who else f"Talking to himself {pl['at']}."
            elif night:
                now = "Asleep. The owl is writing up the day." if minute_of(t) >= 1200 else "Asleep."
            elif mode == "stroll" and action == "stay":
                now = STROLL[dest]
            else:
                now = NOW[action].format(at=pl["at"], At=pl["at"][0].upper() + pl["at"][1:])
            seg = {"from": t, "to": end, "mode": mode, "at": dest, "now": now}
            if asleep:
                seg["asleep"] = True
            if night:
                seg["owl"] = True
            segs.append(seg)
        else:
            end = arrival

        if action == "eat" and dest == "home" and self.served(t, state):
            self.feed(state, t, "meal")
        for b in plan["buys"]:
            entry(t, {"k": "bag", "item": b["item"], "price": b["price"]})
            state["imprest"] -= b["price"]
            if b.get("food"):
                self.feed(state, t, b["food"])
            pl = self.places[dest]
            if pl.get("entry") and any(k in b["item"].lower() for k in pl["entry"]["match"]):
                state.setdefault("today", {}).setdefault("tickets", []).append(dest)
            gid = b.get("garment")
            if gid == "bandhgala":
                state["flags"]["bandhgala"] = "collected"
                g = self.garment(state, "bandhgala")
                if g:
                    g["status"] = "Collected from Masterji."
                    entry(t, {"k": "wear", "item": g["item"], "status": g["status"]})
            elif gid and not self.garment(state, gid):
                item = b["item"].split(",")[0]
                if any(w["item"] == item for w in state["wardrobe"]):
                    item += ", a second one"
                state["wardrobe"].append({"id": gid, "item": item, "status": "Bought today."})
                entry(t, {"k": "wear", "item": item, "status": "Bought today."})
        if ans.get("revision"):
            entry(t0, {"k": "work", "title": "Revision log", "text": ans["revision"].strip()})

        for s in segs:
            s["from"], s["to"] = fmt(minute_of(s["from"])), ("24:00" if s["to"] >= midnight else fmt(minute_of(s["to"])))
        day["segments"].extend(segs)
        day["entries"].extend(entries)
        state["until"] = end.isoformat(timespec="minutes")
        state["asleep"] = night
        return {"t": fmt(minute_of(t0)), "end": "24:00" if end >= midnight else fmt(minute_of(end)),
                "event": sit["event"], "present": sit["present"], "decision": ans, "arrived": arrived}
