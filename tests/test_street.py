"""The street (HEGEL_STREET, world/street.py, tools/street_lint.py): a card at an empty moment, and nowhere else.
The fixture deck is passed in explicitly, so the real deck's presence does not matter."""
import copy
import json
import subprocess
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO, Sandbox, state  # noqa: E402

from world import health, street  # noqa: E402
from world.clock import at_dt, fmt, hm  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World  # noqa: E402

FIXTURE = REPO / "tests/data/street_fixture.json"
CARDS = {c["id"]: c for c in json.loads(FIXTURE.read_text(encoding="utf-8"))["cards"]}
EMPTY = "Nothing in particular happens."
TUE = date(2026, 11, 17)


class Weathered(World):
    """A world whose hour of weather is given: code, rain and aqi."""

    def __init__(self, wx=None, **kw):
        super().__init__(**kw)
        self.wx = wx or {}

    def wx_at(self, t):
        return {**super().wx_at(t), **self.wx}


def worlds(**wx):
    return Weathered(wx, street_on=False), Weathered(wx, street_on=True, street_file=FIXTURE)


def moments(d, pid, lo=555, hi=1260):
    for m in range(lo, hi, 5):
        yield at_dt(d, m)


def calm(w, t, pid="home"):
    """A state in which nothing is due: every beat done, fed, the day's rain and bad air already said, everyone present already seen."""
    st = state()
    st["place"], st["asleep"] = pid, False
    st["beats"] = [b["id"] for b in w.beats]
    st["last_meal"] = (t - timedelta(hours=1)).isoformat(timespec="minutes")
    st["today"] = {"woke": "09:15", "breakfast": True, "lunch": True, "dinner": True, "tea": True, "no_meals": True, "late": True, "power": True,
                   "bad_air": True, "rain_reported": 10**6, "seen": {pid: sorted(w.present_ids(pid, t, st))}}
    return st


def at(w, t, pid="home"):
    st = calm(w, t, pid)
    sit, ctx = w.situation(t, st, {"steps": [], "entries": []}, None)
    return sit, ctx, st


def drawn(on, off, d, pid, **kw):
    """[(t, card id, ctx, sit, off's sit)] for the moments of a day on which the street gave a card."""
    out = []
    for t in moments(d, pid, **kw):
        sit, ctx, _ = at(on, t, pid)
        if ctx.get("street"):
            out.append((t, ctx["street"]["id"], ctx, sit, at(off, t, pid)[0]))
    return out


class Draw(unittest.TestCase):
    def test_off_by_default(self):
        self.assertFalse(Config({}).street)
        self.assertTrue(Config({"HEGEL_STREET": "1"}).street)
        self.assertIsNone(Config({}).street_file)
        self.assertFalse(World().street)

    def test_a_card_only_at_an_otherwise_empty_moment(self):
        off, on = worlds()
        n = 0
        for d in (TUE, TUE + timedelta(days=3)):
            for pid in ("home", "lodhi", "khan"):
                for t in moments(d, pid):
                    a, b = at(off, t, pid)[0], at(on, t, pid)[0]
                    if a["event"] != b["event"]:
                        n += 1
                        self.assertTrue(a["event"].startswith(EMPTY[:-1]), f"{t}: {a['event']}")
                        self.assertIn(b["event"], [c["text"] for c in CARDS.values()])
                    else:
                        self.assertNotIn("street", at(on, t, pid)[1])
        self.assertGreater(n, 10)

    def test_never_outside_its_place_month_hours_day_or_weather(self):
        seen = set()
        for label, wx in (("dry", {}), ("rain", {"rain": 2.0, "code": 61}), ("fog", {"code": 45}), ("air", {"aqi": 340})):
            off, on = worlds(**wx)
            for d in [date(2026, 11, 17) + timedelta(days=i) for i in range(9)] + [date(2026, 3, 4), date(2026, 8, 15)]:
                for pid in ("home", "lodhi", "khan"):
                    for t, cid, ctx, sit, _ in drawn(on, off, d, pid):
                        c, m = CARDS[cid], t.hour * 60 + t.minute
                        seen.add(cid)
                        self.assertIn(pid, c["places"], cid)
                        self.assertIn(d.month, c["months"], cid)
                        self.assertTrue(hm(c["hours"][0]) <= m < hm(c["hours"][1]), f"{cid} at {fmt(m)}")
                        if c.get("days"):
                            self.assertTrue(street.days_match(c["days"], d), cid)
                        if c.get("weather"):
                            self.assertIn(c["weather"], {"dry": ("dry",), "rain": ("rain",), "fog": ("fog",), "air": ("dry", "poor_air")}[label], f"{cid} in {label}")
        self.assertTrue({"rain_on_tin", "fog_lamps", "haze_sun", "dry_wind", "gate_caller", "khan_cart"} <= seen, seen)

    def test_the_weather_words(self):
        d = date(2026, 12, 3)
        words = lambda m=700, **wx: street.weather_words({"rain": 0, "code": 1, "aqi": None, **wx}, d, m)
        self.assertEqual(words(), {"dry"})
        self.assertEqual(words(rain=0.1), {"rain"})
        self.assertEqual(words(code=63), {"rain"})
        self.assertEqual(words(code=45), {"fog"})
        self.assertEqual(words(aqi=299), {"dry"})
        self.assertEqual(words(aqi=300), {"dry", "poor_air"})
        self.assertEqual(words(code=None, m=570), {"fog"})            # no feed: a December morning before ten
        self.assertEqual(words(code=None, m=600), {"dry"})
        self.assertEqual(street.weather_words({"code": None}, date(2026, 11, 3), 570), {"dry"})

    def test_a_probability_of_about_two_in_three(self):
        off, on = worlds()
        got = tried = 0
        for i in range(20):
            d = TUE + timedelta(days=i)
            for t in moments(d, "home", 600, 960):
                if at(off, t)[0]["event"].startswith(EMPTY[:-1]):
                    tried += 1
                    got += bool(at(on, t)[1].get("street"))
        self.assertGreater(tried, 200)
        self.assertTrue(0.45 < got / tried < 0.75, got / tried)       # fewer than 2/3: some moments have no fitting card

    def test_the_same_moment_twice_is_the_same_card(self):
        off, on = worlds()
        first = [(t, cid) for t, cid, *_ in drawn(on, off, TUE, "home")]
        again = [(t, cid) for t, cid, *_ in drawn(on, off, TUE, "home")]
        self.assertTrue(first)
        self.assertEqual(first, again)

    def test_a_draw_with_an_empty_deck_or_no_deck_changes_nothing(self):
        off, _ = worlds()
        for w in (World(street_on=True, street_file=Path("/nonexistent/street.json")),):
            for t in moments(TUE, "home"):
                self.assertEqual(at(off, t)[0]["event"], at(w, t)[0]["event"])
                self.assertNotIn("street", at(w, t)[1])

    def test_no_card_while_asleep_or_at_night(self):
        off, on = worlds()
        for m in (120, 200, 1265, 1300):
            self.assertNotIn("street", at(on, at_dt(TUE, m))[1])


def run_days(first, days, deck=FIXTURE, mind=StubMind):
    box = Sandbox()
    try:
        box.cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "0", "HEGEL_STREET": "1"})
        box.cfg.docs = box.tmp / "docs"
        e = Engine(box.cfg, World(street_on=True, street_file=deck), mind())
        e.lookup = lambda q, c: {"title": q, "text": "A page.", "source": "Wikipedia", "url": "https://en.wikipedia.org/wiki/x"}
        return [box.run_day(first + timedelta(days=i), e) for i in range(days)]
    finally:
        box.close()


_DAYS = []


def days():
    if not _DAYS:
        _DAYS.extend(run_days(date(2026, 10, 3), 14))
    return _DAYS


def seen_cards(ds):
    """[(date, time, card id)] over the days, from the steps."""
    return [(d["date"], s["t"], k.split(":", 1)[1]) for d in ds for s in d["steps"] for k in s.get("opened", []) if k.startswith("street:")]


class Rehearsed(unittest.TestCase):
    def test_cards_come_once_a_day_and_not_within_their_cooldown(self):
        seen = seen_cards(days())
        self.assertGreater(len(seen), 8)
        last = {}
        for ds, t, cid in seen:
            d = date.fromisoformat(ds)
            if cid in last:
                gap = (d - last[cid]).days
                self.assertGreaterEqual(gap, 1, f"{cid} twice on {ds}")
                self.assertGreaterEqual(gap, CARDS[cid].get("cooldown_days", street.COOLDOWN), f"{cid} on {ds}")
            last[cid] = d
        for day in days():
            self.assertEqual(day["state"].get("street", {}).keys() - {c for _, _, c in seen}, set())

    def test_the_card_is_on_the_page_in_the_event_and_the_state(self):
        for day in days():
            for s in day["steps"]:
                for k in s.get("opened", []):
                    if k.startswith("street:"):
                        text = CARDS[k.split(":", 1)[1]]["text"]
                        self.assertIn(text, s["event"])
                        self.assertNotIn(EMPTY, s["event"])
                        self.assertTrue(any(e.get("k") == "world" and e.get("text") == text and e["t"] == s["t"] for e in day["entries"]))
                        self.assertEqual(day["state"]["street"][k.split(":", 1)[1]] >= day["date"], True)

    def test_health_calls_a_street_moment_brought(self):
        n = 0
        for day in days():
            prev = None
            for s in day["steps"]:
                if any(k.startswith("street:") for k in s.get("opened", [])):
                    self.assertEqual(health.opening(s, prev), "brought")
                    self.assertTrue(any(k.startswith("street:") for k in health.brought_kinds(s, prev)))
                    n += 1
                if "decision" in s:
                    prev = s
        self.assertGreater(n, 5)

    def test_the_same_rehearsal_twice_is_identical(self):
        a = [json.dumps(d["steps"], sort_keys=True) for d in run_days(date(2026, 10, 3), 5)]
        b = [json.dumps(d["steps"], sort_keys=True) for d in days()[:5]]
        self.assertEqual(a, b)

    def test_a_card_is_the_event_and_so_known_to_him(self):
        from world.memory import encountered_text
        for day in days():
            for s in day["steps"]:
                for k in s.get("opened", []):
                    if k.startswith("street:"):
                        self.assertIn(CARDS[k.split(":", 1)[1]]["text"], encountered_text(day))
                        return
        self.fail("no card seen")


class Quiet(unittest.TestCase):
    def test_a_quiet_step_spends_no_card(self):
        off, on = worlds()
        t, cid, ctx, sit, off_sit = drawn(on, off, TUE, "home")[0]
        st = calm(on, t)
        day = {"steps": [], "entries": [], "segments": [], "state": st, "date": TUE.isoformat(), "n": 1}
        sit, ctx = on.situation(t, st, day, None)
        self.assertEqual(ctx["street"]["id"], cid)
        engine = Engine(Config({"HEGEL_PUSH": "0", "HEGEL_FEEDS": "0"}), on, StubMind())
        ans, plan = engine.quiet(st, t, sit, day)
        self.assertIsNone(ans["thought"])
        step = on.apply(ans, plan, sit, ctx, st, day)
        self.assertNotIn(cid, st.get("street", {}))
        self.assertTrue(step["event"].startswith(EMPTY[:-1]), step["event"])
        self.assertFalse(any(k.startswith("street") for k in step["opened"]))
        self.assertFalse(any(e.get("text") == CARDS[cid]["text"] for e in day["entries"]))
        self.assertEqual(health.opening(step, None), "empty")
        again, ctx2 = on.situation(t, st, day, None)             # the same moment, met again by a mind: the card is still there
        self.assertEqual(ctx2["street"]["id"], cid)


class Off(unittest.TestCase):
    def test_with_the_switch_off_the_day_is_byte_for_byte_what_it_was(self):
        a, b = Sandbox(), Sandbox()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        e1 = a.engine()
        e2 = Engine(b.cfg, World(street_on=False, street_file=FIXTURE), StubMind())
        e2.lookup = e1.lookup
        d1, d2 = a.run_day(date(2026, 10, 3), e1), b.run_day(date(2026, 10, 3), e2)
        self.assertEqual(json.dumps(d1["steps"], sort_keys=True), json.dumps(d2["steps"], sort_keys=True))
        self.assertEqual(json.dumps(d1["state"], sort_keys=True), json.dumps(d2["state"], sort_keys=True))
        self.assertNotIn("street", d2["state"])
        self.assertFalse(any(k.startswith("street") for s in d2["steps"] for k in s.get("opened", [])))


GOOD = {"id": "x_card", "text": "A cart goes by with a bell tied to its handle.", "places": ["home"], "months": [11], "hours": ["10:00", "12:00"]}
PLACES = json.loads((REPO / "world/data/places.json").read_text(encoding="utf-8"))["places"]
BAD = {   # one bad card of each kind: what to change, and what the linter says
    "too long": ({"text": "A cart. " * 40}, "text must be"),
    "empty text": ({"text": ""}, "text must be"),
    "unknown place": ({"places": ["mars"]}, "unknown place"),
    "bad month": ({"months": [13]}, "months"),
    "bad hour": ({"hours": ["10:00", "25:00"]}, "hours must be"),
    "hours backwards": ({"hours": ["12:00", "10:00"]}, "from must be before"),
    "outside opening": ({"places": ["gandhi"], "hours": ["06:00", "08:00"]}, "outside the opening hours"),
    "bad days": ({"days": "Someday"}, "not a day spec"),
    "bad weather": ({"weather": "snow"}, "weather must be"),
    "bad cooldown": ({"cooldown_days": -1}, "cooldown_days"),
    "bad id": ({"id": "Bad Id"}, "id must be"),
    "you": ({"text": "A cart goes by and You hear its bell."}, "you/your"),
    "your": ({"text": "A cart stops at your gate."}, "you/your"),
    "question": ({"text": "Is that a cart going by."[:-1] + "?"}, "question mark"),
    "imperative": ({"text": "A cart goes by. Look at the bell."}, "instruction"),
    "imperative first": ({"text": "Go past the gate."}, "instruction"),
    "rupee sign": ({"text": "A cart sells limes at ₹10 a heap."}, "price"),
    "Rs": ({"text": "A cart sells limes at Rs 10 a heap."}, "price"),
    "doctrine": ({"text": "A cart goes by, and the dialectic of the street goes on."}, "term of his system"),
    "rehearsal": ({"text": "A cart goes by (rehearsal)."}, "(rehearsal)"),
}


class Lint(unittest.TestCase):
    def check(self, cards):
        return street.problems(cards, PLACES)

    def test_the_good_card_and_the_fixture_pass(self):
        self.assertEqual(self.check([GOOD]), ([], []))
        self.assertEqual(street.check_file(FIXTURE, PLACES), ([], []))

    def test_each_kind_of_bad_card_is_refused(self):
        for name, (change, said) in BAD.items():
            bad, _ = self.check([{**GOOD, **change}])
            self.assertTrue(any(said in x and x.startswith(change.get("id", "x_card") if "id" not in change else "") for x in bad), f"{name}: {bad}")

    def test_a_duplicate_id_and_a_missing_field(self):
        self.assertTrue(any("duplicate id" in x for x in self.check([GOOD, GOOD])[0]))
        self.assertTrue(self.check([{k: v for k, v in GOOD.items() if k != "months"}])[0])

    def test_a_deck_with_too_few_cards_at_home(self):
        out = {**GOOD, "places": ["lodhi"], "hours": ["06:00", "09:00"]}
        cards = [GOOD] + [{**out, "id": f"o{i}"} for i in range(4)]
        self.assertEqual(self.check(cards)[0], ["deck: fewer than a quarter of the cards happen at home"])
        self.assertEqual(self.check(cards[:4])[0], [])

    def test_two_capitalised_words_is_a_warning_not_a_failure(self):
        bad, warn = self.check([{**GOOD, "text": "A man called Anil Sharma waves from the gate."}])
        self.assertEqual(bad, [])
        self.assertEqual(len(warn), 1)
        self.assertTrue(warn[0].startswith("x_card:"))
        self.assertEqual(self.check([{**GOOD, "text": "A cart goes by near Khan Market."}])[1], [])     # a place's name is not a person

    def test_the_command_line(self):
        tmp = Path(Sandbox().tmp)
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        bad = tmp / "bad.json"
        bad.write_text(json.dumps({"note": "", "cards": [{**GOOD, "text": "Is it your cart?"}]}))
        run = lambda f: subprocess.run([sys.executable, str(REPO / "tools/street_lint.py"), str(f)], capture_output=True, text=True, cwd=REPO)
        r = run(bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn("x_card: has a question mark", r.stdout)
        r = run(FIXTURE)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
