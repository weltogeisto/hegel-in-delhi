"""The simulated economy of his days: cash, the imprest account and its vouchers, debts, cheques, the costs that recur
and the offers that bring money in. Everything here is simulated; nothing is bought for real. World inherits it."""
from datetime import date, timedelta

from .clock import DAY_ONE, DAYNAMES, WEEKDAYS, at_dt, day_number, days_match, fmt, hm, minute_of

ADVANCE = 15000                 # the imprest advance he must account for
SESSION_WAIT = 30               # minutes a person waits for him at a standing engagement
HOME_GIFT = (50, 5000)          # what a gift or payment to a person at home may come to


def cap(text):
    return text[:1].upper() + text[1:]


def nice(d):
    """'Sat 10 Oct'."""
    return f"{DAYNAMES[d.weekday()]} {d.day} {d.strftime('%b')}"


class Economy:
    # ── the books ───────────────────────────────────────────────────
    def ledger(self, st):
        """The money keys a state may lack (day 1's does), with their defaults, so that older states carry on."""
        st.setdefault("account", {"advance": ADVANCE, "vouchers": [], "admitted": 0, "queried": 0})
        for k in ("owed", "cheques", "receipts", "engagements"):
            st.setdefault(k, [])
        for k in ("costs", "met_days", "visits", "refused"):
            st.setdefault(k, {})
        st.setdefault("tech", {"phone": False, "sim": False})
        for c in st.get("people", []):
            st["met_days"].setdefault(c, [DAY_ONE.isoformat()])
        return st

    def track(self, st, d, pid, present):
        """The days he has met each person and been in each place: the offers count them."""
        iso = d.isoformat()
        for c in present:
            if not self.cast[c].get("background"):
                days = st["met_days"].setdefault(c, [])
                if iso not in days:
                    days.append(iso)
        days = st["visits"].setdefault(pid, [])
        if iso not in days:
            days.append(iso)

    def is_office(self, item):
        """Is this the kind of thing the Directorate admits on a voucher (stationery, notebooks, ink, newspapers)?"""
        low = item.lower()
        return any(s.get("office") and any(k in low for k in s["match"]) for pl in self.places.values() for s in pl.get("sells", []))

    def voucher(self, st, t, item, price, office):
        if price:                                       # a free thing has nothing to account for
            st["account"]["vouchers"].append({"date": t.date().isoformat(), "t": fmt(minute_of(t)), "item": item, "price": price, "office": bool(office)})

    def money_line(self, st, t):
        """The one line of what he has, owes and must pay next: at most 200 characters, saying less of the debts if need be
        (first not why, then fewer of them, with shorter names)."""
        v, whom, why = st["account"]["vouchers"], {}, {}
        for o in st["owed"]:
            whom[o["to"]] = whom.get(o["to"], 0) + o["amount"]
            why[(o["to"], o["why"])] = why.get((o["to"], o["why"]), 0) + o["amount"]
        for tier in range(3):
            bits = [f"cash ₹{st['imprest']:,}"]
            if v:
                bits.append(f"{len(v)} voucher{'s' if len(v) > 1 else ''} pending ₹{sum(x['price'] for x in v):,}")
            rows = [f"{to} ₹{n:,} ({w})" for (to, w), n in why.items()] if tier == 0 else \
                [f"{to.replace('the Directorate of Estates', 'the Directorate') if tier == 2 else to} ₹{n:,}" for to, n in whom.items()]
            show = rows[:2 if tier == 2 else 3]
            if rows:
                bits.append("owes " + ", ".join(show) + (f" and {len(rows) - len(show)} more" if len(rows) > len(show) else ""))
            if st["cheques"]:
                n = len(st["cheques"])
                bits.append(f"{n} cheque{'s' if n > 1 else ''} ₹{sum(c['amount'] for c in st['cheques']):,} uncashed")
            nxt = self.next_cost(st, t.date())
            if nxt:
                bits.append("next: " + nxt)
            line = "Money: " + "; ".join(bits) + "."
            if len(line) <= 200:
                break
        return line

    # ── recurring costs ─────────────────────────────────────────────
    def last_due(self, when, d, st):
        """The latest date up to d on which a cost with this rule fell due, or None."""
        if "weekday" in when:
            return d - timedelta(days=(d.weekday() - DAYNAMES.index(when["weekday"])) % 7)
        if "monthday" in when:
            n = when["monthday"]
            x = d.replace(day=n) if d.day >= n else (d.replace(day=1) - timedelta(days=1)).replace(day=n)
            return x if x.isoformat() >= when.get("from", "") else None
        anchor = max((st["tech"][k] for k in ("sim_from", "data_from") if st["tech"].get(k)), default=None)
        if not anchor:
            return None                                   # every N days, from the SIM or the last data pack
        a = date.fromisoformat(anchor)
        k = (d - a).days // when["every"]
        return a + timedelta(days=when["every"] * k) if k >= 1 else None

    def next_due(self, when, after, st):
        """The first date after `after` on which a cost with this rule falls due, or None."""
        for i in range(1, 63):
            x = after + timedelta(days=i)
            if self.last_due(when, x, st) == x:
                return x
        return None

    def next_cost(self, st, d):
        """'dhobi ₹300 Sat 10 Oct': the next recurring cost to fall due."""
        best = None
        for c in self.costs:
            last = date.fromisoformat(st["costs"].get(c["id"]) or (d - timedelta(days=1)).isoformat())
            nd = self.next_due(c["when"], last, st)
            if nd and (best is None or nd < best[0]):
                best = (nd, c)
        return f"{best[1]['short']} ₹{best[1]['amount']:,} {nice(best[0])}" if best else None

    def accrue(self, t, st):
        """Costs that have fallen due since he last looked go onto what he owes. Returns them."""
        d, fresh = t.date(), []
        for c in self.costs:
            last = st["costs"].setdefault(c["id"], (d - timedelta(days=1)).isoformat())
            due = self.last_due(c["when"], d, st)
            if due and due.isoformat() > last:
                st["costs"][c["id"]] = due.isoformat()
                o = {"to": c["to"], "amount": c["amount"], "why": c["why"], "since": due.isoformat(), "cost": c["id"], "item": c["item"]}
                o.update({k: c[k] for k in ("at", "with") if c.get(k)})
                st["owed"].append(o)
                fresh.append(o)
        return fresh

    def reachable(self, o, pid, present):
        """Can this creditor be paid here and now?"""
        return (not o.get("at") or o["at"] == pid) and (not o.get("with") or o["with"] in present)

    def settle(self, t, st, pid, present, today):
        """Pay what he owes wherever its creditor can be reached and he has the cash. Returns (event lines, entries)."""
        lines, entries, now = [], [], t.date().isoformat()
        for o in list(st["owed"]):
            if o.get("after", "") > now or not self.reachable(o, pid, present):
                continue
            if o["amount"] <= st["imprest"]:
                st["imprest"] -= o["amount"]
                st["owed"].remove(o)
                entries.append({"k": "expense", "item": o.get("item") or cap(o["why"]), "amount": o["amount"], "to": o["to"], "why": o["why"],
                                "settles": True, "text": f"Paid to {o['to']}."})
                lines.append(f"You pay {o['to']} ₹{o['amount']:,} for {o['why']}.")
            elif f"{o['to']}|{o['why']}" not in today.setdefault("pressed", []):
                today["pressed"].append(f"{o['to']}|{o['why']}")
                lines.append(f"{cap(o['to'])} asks for ₹{o['amount']:,} ({o['why']}), and you have only ₹{st['imprest']:,}.")
        return lines, entries

    def kitchen(self, st):
        """Why nothing is cooked at home just now (an unpaid wage or unpaid groceries), or None."""
        for c in self.costs:
            if c.get("lapse") and any(o.get("cost") == c["id"] for o in st.get("owed", [])):
                return c["lapse"]
        return None

    # ── money that is due to him ────────────────────────────────────
    def pay(self, st, r, t):
        """Money comes to him: cash into the purse, or a cheque he has no bank account for. Returns the entry.
        Collected long after its time, it is what they left for him."""
        cheque, n = bool(r.get("cheque")), r["amount"]
        e = {"k": "income", "item": r["item"], "amount": n, "from": r["from"]}
        if cheque:
            st["cheques"].append({"from": r["from"], "amount": n, "since": t.date().isoformat()})
            e["cheque"] = True
        else:
            st["imprest"] += n
        what = f"a cheque for ₹{n:,}" if cheque else f"₹{n:,}"
        late = r["after"] < (t - timedelta(minutes=SESSION_WAIT)).isoformat(timespec="minutes")
        e["text"] = f"You collect {what} that {r['from']} left for you." if late else \
            f"{cap(r['from'])} hands you {what}." if cheque else f"{cap(r['from'])} pays you {what} in cash."
        if cheque:
            e["text"] += " You have no bank account to put it in."
        return e

    def receive(self, st, spec, t, cheque):
        """Money promised to him. At once, or when its time comes, where `at` says, or at his next sitting of `write` words."""
        r = {"from": spec["from"], "amount": spec["amount"], "item": spec["item"], "cheque": cheque,
             "after": (t + timedelta(minutes=spec.get("after_min", 0))).isoformat(timespec="minutes")}
        r.update({k: spec[k] for k in ("at", "write") if spec.get(k)})
        if r["after"] == t.isoformat(timespec="minutes") and not (r.get("at") or r.get("write")):
            return [self.pay(st, r, t)]
        st["receipts"].append(r)
        return []

    def collect(self, t, st, pid):
        """What is due to him, paid when its time has come and he is where it is paid. Returns (event lines, entries)."""
        lines, entries, now = [], [], t.isoformat(timespec="minutes")
        for r in list(st["receipts"]):
            if r.get("write") or r["after"] > now or (r.get("at") and r["at"] != pid):
                continue
            st["receipts"].remove(r)
            entries.append(self.pay(st, r, t))
            lines.append(entries[-1]["text"])
        return lines, entries

    def on_writing(self, st, words, t):
        """A sitting of enough words earns what a magazine promised. Returns entries."""
        out = []
        for r in list(st["receipts"]):
            if r.get("write") and words >= r["write"]:
                st["receipts"].remove(r)
                out.append(self.pay(st, r, t))
        return out

    # ── the imprest account ─────────────────────────────────────────
    def recoup(self, t, st, pid, present, today):
        """The first decision at the Directorate on a working day with Mr. Saxena there and vouchers pending: he goes
        through them. What is office expenditure is refilled in cash; the rest is queried and owed to the Directorate."""
        acc = st["account"]
        if pid != "estates":
            today.pop("recouped", None)                              # once a visit: leaving the Directorate ends it
        if pid != "estates" or "saxena" not in present or not acc["vouchers"] or today.get("recouped") or not self.is_open(pid, t, st):
            return [], []
        today["recouped"] = True
        admitted = sum(v["price"] for v in acc["vouchers"] if v["office"])
        queried = sum(v["price"] for v in acc["vouchers"] if not v["office"])
        acc.update(vouchers=[], admitted=acc["admitted"] + admitted, queried=acc["queried"] + queried)
        st["imprest"] += admitted
        said = [f"₹{admitted:,} is admitted and refilled to you in cash" if admitted else "nothing is admitted"]
        said.append(f"₹{queried:,} is queried as personal and will be recovered from you" if queried else "nothing is queried")
        entries = []
        if admitted:
            entries.append({"k": "income", "item": "Imprest refilled against vouchers", "amount": admitted, "from": "the Directorate of Estates",
                            "text": "Admitted by Mr. Saxena: stationery, notebooks, ink, newspapers."})
        if queried:
            o = {"to": "the Directorate of Estates", "amount": queried, "why": "queried vouchers", "since": t.date().isoformat(),
                 "at": "estates", "with": "saxena", "after": (t.date() + timedelta(days=1)).isoformat()}
            st["owed"].append(o)
            entries.append({"k": "file", "text": f"Mr. Saxena queries ₹{queried:,} of personal expenditure on the imprest: recovery from the allottee.",
                            "owe": {k: o[k] for k in ("to", "amount", "why", "since")}})
        entries[0]["recoup"] = {"admitted": admitted, "queried": queried}
        return [f"Mr. Saxena goes through your vouchers: {'; '.join(said)}."], entries

    # ── time and the purse ──────────────────────────────────────────
    def upkeep(self, t, st, pid, present, today):
        """What the clock does to his purse before he decides: sessions missed, money due to him, costs fallen due, debts paid,
        the vouchers gone through. Returns (event lines for the mind, entries for the page)."""
        lines, entries = self.lapse(t, st)
        got = self.collect(t, st, pid)
        lines, entries = lines + got[0], entries + got[1]
        fresh = self.accrue(t, st)
        got = self.settle(t, st, pid, present, today)
        lines, entries = lines + got[0], entries + got[1]
        for o in fresh:
            if any(o is x for x in st["owed"]):                       # not paid at once: it stands
                entries.append({"k": "world", "text": f"{cap(o['why'])}: ₹{o['amount']:,} falls due to {o['to']}.",
                                "owe": {k: o[k] for k in ("to", "amount", "why", "since")}})
        got = self.recoup(t, st, pid, present, today)
        return lines + got[0], entries + got[1]

    # ── offers and their conditions ─────────────────────────────────
    def when_ok(self, w, t, st):
        """The conditions of an offer: days met, visits, day count, cash, flags, a garment, a manuscript, a date."""
        d, cash = t.date(), st["imprest"]
        if w.get("on") and w["on"] != d.isoformat():
            return False
        if day_number(d) < w.get("since_day", 0) or cash >= w.get("cash_below", 10 ** 9) or cash < w.get("cash_min", 0):
            return False
        if any(len(st["met_days"].get(c, [])) < n for c, n in w.get("met_days", {}).items()):
            return False
        if any(len(st["visits"].get(p, [])) < n for p, n in w.get("visits", {}).items()):
            return False
        if any(c not in st.get("people", []) for c in w.get("known", [])) or any(st["flags"].get(k) != v for k, v in w.get("flags", {}).items()):
            return False
        if w.get("wardrobe") and not self.garment(st, w["wardrobe"]):
            return False
        return not w.get("words") or any(x["words"] >= w["words"] for x in st.get("works", []))

    def effects(self, spec, t, st):
        """The economy's effects of a beat, or of one answer to its choice: owe, pay, cheque, sell, schedule. Returns entries."""
        self.ledger(st)
        out = []
        for key, cheque in (("pay", False), ("cheque", True)):
            if spec.get(key):
                out += self.receive(st, spec[key], t, cheque)
        if spec.get("sell"):
            out += self.sell(st, spec["sell"], t)
        if spec.get("owe"):
            o = dict(spec["owe"], since=t.date().isoformat())
            if o.get("after_days"):
                o["after"] = (t.date() + timedelta(days=o.pop("after_days"))).isoformat()
            st["owed"].append(o)
            out.append({"k": "world", "text": f"You owe {o['to']} ₹{o['amount']:,}: {o['why']}.",
                        "owe": {k: o[k] for k in ("to", "amount", "why", "since")}})
        if spec.get("schedule"):
            self.schedule(st, spec["schedule"], t)
        return out

    def sell(self, st, spec, t):
        """A garment leaves the wardrobe now; what it fetches is paid when he is next where the dealer is."""
        g = self.garment(st, spec["garment"])
        if not g:
            return []
        st["wardrobe"].remove(g)
        if st["wearing"] == g["id"]:
            st["wearing"] = "kurta" if self.garment(st, "kurta") else "shirt"       # he cannot go on wearing what he has sold
        self.receive(st, {"from": spec["to"], "amount": spec["amount"], "item": f"{g['item']}, sold", "at": spec["at"]}, t, False)
        return [{"k": "wear", "item": g["item"], "status": f"Sold to {spec['to']}.", "gone": True}]

    def schedule(self, st, spec, t):
        """A standing engagement (days of the week, a time) from tomorrow, or one appointment for a beat that follows."""
        if "days" in spec:
            st["engagements"].append(dict(spec, **{"from": (t.date() + timedelta(days=1)).isoformat(), "checked": t.date().isoformat(), "missed": 0}))
        else:
            self.appoint(st, spec, t)

    # ── standing engagements: the sessions are beats ────────────────
    def sessions(self, d, st):
        """The sessions of his engagements on date d, as beats that bring the other person."""
        out = []
        for e in st.get("engagements", []):
            if days_match(e["days"], d) and d.isoformat() >= e["from"]:
                who, end = self.cast[e["with"]], fmt(hm(e["t"]) + e["minutes"])
                out.append({"id": f"{e['id']}@{d.isoformat()}", "at": e["t"], "window": [e["t"], fmt(hm(e["t"]) + SESSION_WAIT)],
                            "where": e["place"], "brings": [e["with"]], "kind": "world", "session": e["id"],
                            "prompt": f"{who['short']}, arrives for the {e['what']}. It runs until {end}.",
                            "public": f"{who['name']} arrives for the {e['what']}, {e['minutes']} minutes at ₹{e['pay']:,}."})
        return out

    def in_session(self, st, pid, t):
        """The people whose session with him is on at this minute: they came, and have not yet gone."""
        d, m = t.date(), minute_of(t)
        return [e["with"] for e in st.get("engagements", []) if e["place"] == pid and days_match(e["days"], d)
                and f"{e['id']}@{d.isoformat()}" in st["beats"] and hm(e["t"]) <= m < hm(e["t"]) + e["minutes"]]

    def attend(self, beat, t, st):
        """He came to a session: the run of misses ends, and the fee is paid when the hour is over."""
        e = next((x for x in st["engagements"] if x["id"] == beat["session"]), None)
        if not e:
            return
        e["missed"] = 0
        d = date.fromisoformat(beat["id"].split("@")[1])
        wait = max(0, int((at_dt(d, hm(e["t"]) + e["minutes"]) - t).total_seconds() // 60))
        self.receive(st, {"from": self.cast[e["with"]]["name"], "amount": e["pay"], "item": cap(e["what"]), "at": e["place"], "after_min": wait}, t, False)

    def lapse(self, t, st):
        """Sessions that came and went without him are missed; the second in a row ends the engagement.
        Returns (event lines, entries)."""
        lines, entries = [], []
        for e in list(st["engagements"]):
            d = date.fromisoformat(e["checked"]) + timedelta(days=1)
            while d <= t.date():
                sid = f"{e['id']}@{d.isoformat()}"
                if days_match(e["days"], d) and d.isoformat() >= e["from"] and sid not in st["beats"] and sid not in st.get("missed", []):
                    if t < at_dt(d, hm(e["t"]) + SESSION_WAIT):
                        break                                       # still to come, or just now
                    st.setdefault("missed", []).append(sid)
                    e["missed"] += 1
                    who = self.cast[e["with"]]["name"]
                    lines.append(f"You missed the {e['what']}: {who} waited and went away.")
                    entries.append({"k": "world", "text": f"{who} waited for the {e['what']} and went away: it was missed."})
                    if e["missed"] >= e.get("cancel_after", 2):
                        st["engagements"].remove(e)
                        entries.append({"k": "file", "text": f"{who} cancels the {e['what']}s after {e['missed']} missed sessions."})
                        lines.append(f"{who} cancels the {e['what']}s: {e['missed']} sessions missed.")
                        break
                e["checked"] = d.isoformat()
                d += timedelta(days=1)
        return lines, entries

    def engagement_lines(self, t, st):
        """For what is on his mind: the next session of each standing engagement."""
        out = []
        for e in st["engagements"]:
            for i in range(8):
                d = t.date() + timedelta(days=i)
                sid = f"{e['id']}@{d.isoformat()}"
                if days_match(e["days"], d) and d.isoformat() >= e["from"] and sid not in st["beats"] and sid not in st.get("missed", []) \
                        and t < at_dt(d, hm(e["t"]) + SESSION_WAIT):
                    out.append(f"{WEEKDAYS[d.weekday()]} {d.day} {d.strftime('%B')} {e['t']}: {e['what']} for {self.cast[e['with']]['name']}, "
                               f"{self.places[e['place']]['at']}, ₹{e['pay']:,} in cash.")
                    break
        return out

    def names_present(self, st, ids):
        """People of the cast he knows (met, not background) among ids."""
        return [c for c in ids if c in st.get("people", []) and not self.cast[c].get("background")]
