"""Tests for the world engine. Standard library only:  python3 -m unittest discover -s tests"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.environ["HEGEL_ENV"] = os.devnull       # never read the Pi's real env file in tests

from world import contract  # noqa: E402
from world.clock import fmt, hm, sun  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Days, Engine, until_of  # noqa: E402
from world.feeds import naqi, sky  # noqa: E402
from world.mind import HTTPMind, StubMind  # noqa: E402
from world.publish import Git  # noqa: E402
from world.world import World, at_dt  # noqa: E402

DAY1 = json.loads((REPO / "docs/days/2026-10-02.json").read_text(encoding="utf-8"))


def state():
    st = copy.deepcopy(DAY1["state"])
    st["asleep"], st["today"] = False, {}
    return st


def answer(**kw):
    a = {"thought": "A thought of sufficient length for the rules.", "action": "read", "place": "home",
         "minutes": 30, "says": None, "buys": [], "revision": None}
    a.update(kw)
    return a


class Sandbox:
    """A scratch copy of docs/days with day 1, and a config pointing at it."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hegel-test-"))
        (self.tmp / "docs/days").mkdir(parents=True)
        for f in ("2026-10-02.json", "index.json"):
            shutil.copy(REPO / "docs/days" / f, self.tmp / "docs/days" / f)
        self.cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(self.tmp / "state"), "HEGEL_FEEDS": "0"})
        self.cfg.docs = self.tmp / "docs"
        self.days = Days(self.cfg.docs)

    def engine(self, mind=None, git=None):
        return Engine(self.cfg, World(), mind or StubMind(), git=git)

    def run_day(self, d, engine=None):
        engine = engine or self.engine()
        now, end = at_dt(d, 0), at_dt(d, 1440)
        while now < end:
            engine.advance(now)
            now += timedelta(minutes=5)
        return self.days.load(d)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class ClockTest(unittest.TestCase):
    def test_sun_matches_day_one(self):
        rise, set_ = sun(date(2026, 10, 2))
        self.assertEqual(fmt(rise), DAY1["sun"]["rise"])
        self.assertEqual(fmt(set_), DAY1["sun"]["set"])

    def test_hm_fmt(self):
        self.assertEqual(hm("06:05"), 365)
        self.assertEqual(fmt(1440), "24:00")


class ContractTest(unittest.TestCase):
    def test_bakeoff_situations_render_without_extras(self):
        for s in json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"]:
            text = contract.render(s)
            self.assertNotIn("On your mind", text)
            self.assertTrue(text.endswith("Answer with the JSON object only."))

    def test_extract_json_tolerates_fences_and_think(self):
        self.assertEqual(contract.extract_json('<think>hm</think>```json\n{"a": 1}\n```'), {"a": 1})

    def test_shape(self):
        self.assertEqual(contract.check_shape(answer())[0], [])
        self.assertTrue(contract.check_shape(answer(minutes=500))[0])
        self.assertTrue(contract.check_shape(answer(buys=[{"item": "x", "price_inr": "20"}]))[0])


class FeedsTest(unittest.TestCase):
    def test_naqi(self):
        self.assertEqual(naqi(45, None), 75)
        self.assertEqual(naqi(None, 300), 250)
        self.assertEqual(naqi(100, 120), 233)

    def test_open_meteo_parsing(self):
        from world.feeds import Feeds
        box = Sandbox()
        try:
            d = date(2026, 10, 3)
            fc = {"hourly": {"time": [f"2026-10-03T{h:02d}:00" for h in range(24)],
                             "temperature_2m": [22.4 + h * 0.4 for h in range(24)],
                             "precipitation": [0.0] * 15 + [5.2] + [0.0] * 8,
                             "weather_code": [0] * 15 + [81] + [2] * 8}}
            air = {"hourly": {"time": [f"x{h}" for h in range(48)], "pm2_5": [70.0] * 48, "pm10": [140.0] * 48}}
            (box.cfg.state / "feeds").mkdir(parents=True)
            (box.cfg.state / "feeds/weather-2026-10-03.json").write_text(json.dumps({"forecast": fc, "air": air}))
            w = Feeds(box.cfg).weather(d)
            self.assertEqual(w["source"], "open-meteo")
            self.assertEqual(w["hours"][0]["temp"], 22)
            self.assertEqual(w["hours"][15]["sky"], "a sudden heavy shower")
            self.assertEqual(w["hours"][12]["aqi"], 133)          # PM2.5 70 over 24 hours → 133
            self.assertEqual(w["hours"][12]["sky"], "clear")
        finally:
            box.close()

    def test_sky(self):
        self.assertEqual(sky(0, 250, 0), "a brown haze")
        self.assertEqual(sky(81, 90, 5), "a sudden heavy shower")


class RulesTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def ctx(self, when, st, present=()):
        return {"t": when, "present": list(present), "beat": None, "public": []}

    def check(self, when, st, **kw):
        sit = {"open_now": self.w.open_places(when, st)}
        return self.w.check(answer(**kw), sit, self.ctx(when, st), st)

    def test_hours(self):
        st = state()
        mon, sat = date(2026, 10, 5), date(2026, 10, 3)
        self.assertFalse(self.w.is_open("gandhi", at_dt(mon, 660), st))     # Gandhi Smriti rests on Mondays
        self.assertTrue(self.w.is_open("gandhi", at_dt(sat, 660), st))
        self.assertFalse(self.w.is_open("estates", at_dt(sat, 660), st))    # weekend
        self.assertTrue(self.w.is_open("estates", at_dt(mon, 660), st))
        self.assertFalse(self.w.is_open("estates", at_dt(date(2026, 10, 20), 660), st))  # Dussehra
        self.assertIsNone(self.w.hours("estates", date(2026, 10, 2)))       # Gandhi Jayanti

    def test_gymkhana_needs_its_member(self):
        st = state()
        tue = date(2026, 10, 6)
        open_at = [m for m in range(1020, 1170, 10) if self.w.is_open("gym", at_dt(tue, m), st)]
        present = "malhotra" in self.w.present_ids("gym", at_dt(tue, 1080), st)
        self.assertEqual(bool(open_at), present)
        self.assertFalse(self.w.is_open("gym", at_dt(tue, 600), st))

    def test_closed_destination_is_refused(self):
        st = state()
        errors, _, _ = self.check(at_dt(date(2026, 10, 5), 600), st, action="walk", place="gandhi")
        self.assertTrue(any("Gandhi Smriti" in e for e in errors))

    def test_opening_on_arrival_counts(self):
        st = state()   # leaves at 10:00, arrives at Khan Market at 10:25: still shut
        errors, _, _ = self.check(at_dt(date(2026, 10, 3), 600), st, action="walk", place="khan")
        self.assertTrue(any("opens at 10:30" in e for e in errors))
        errors, _, _ = self.check(at_dt(date(2026, 10, 3), 610), st, action="walk", place="khan")
        self.assertEqual(errors, [])

    def test_money(self):
        st = state()
        st["place"] = "khan"
        t = at_dt(date(2026, 10, 3), 720)
        errors, warnings, (ans, plan) = self.check(t, st, action="buy", place="khan", buys=[{"item": "chai", "price_inr": 15}])
        self.assertEqual(errors, [])
        self.assertEqual(plan["buys"][0]["price"], 20)                       # the world's price, not the mind's
        st["imprest"] = 10
        errors, _, _ = self.check(t, st, action="buy", place="khan", buys=[{"item": "chai", "price_inr": 20}])
        self.assertTrue(any("imprest" in e for e in errors))

    def test_dry_day_and_unready_bandhgala(self):
        st = state()
        st["place"] = "khan"
        errors, _, _ = self.check(at_dt(date(2026, 10, 20), 720), st, action="buy", place="khan",
                                  buys=[{"item": "a bottle of wine", "price_inr": 1100}])
        self.assertTrue(any("dry day" in e for e in errors))
        errors, _, _ = self.check(at_dt(date(2026, 10, 6), 720), st, action="buy", place="khan",
                                  buys=[{"item": "bandhgala balance", "price_inr": 3500}])
        self.assertTrue(any("Thursday" in e for e in errors))

    def test_words_the_page_will_not_publish(self):
        st = state()
        errors, _, _ = self.check(at_dt(date(2026, 10, 3), 600), st, thought="I would murder a cup of Prussian coffee this morning.")
        self.assertTrue(any("cannot publish" in e for e in errors))

    def test_ticket_and_sleep_and_nothing_for_sale(self):
        st = state()
        st["place"] = "safdarjung"
        t = at_dt(date(2026, 10, 3), 600)
        errors, _, _ = self.check(t, st, action="stay", place="safdarjung")
        self.assertTrue(any("ticket" in e for e in errors))
        errors, _, _ = self.check(t, st, action="stay", place="safdarjung", buys=[{"item": "entry ticket", "price_inr": 300}])
        self.assertEqual(errors, [])
        errors, _, _ = self.check(t, st, action="sleep", place="safdarjung", buys=[{"item": "ticket", "price_inr": 25}])
        self.assertTrue(any("sleep only at home" in e for e in errors))
        st["place"] = "home"
        errors, _, _ = self.check(t, st, action="buy", place="home", buys=[{"item": "a horse", "price_inr": 100}])
        self.assertTrue(any("nothing is sold" in e for e in errors))


class PlotTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def test_hegde_note_then_the_call(self):
        st = state()
        sat = date(2026, 10, 3)
        self.assertIsNone(self.w.due_beat(at_dt(sat, 540), st, "home"))   # 09:00, too early
        beat = self.w.due_beat(at_dt(sat, 600), st, "home")
        self.assertEqual(beat["id"], "hegde_note")
        self.w.fire(beat, at_dt(sat, 600), st)
        self.assertEqual(st["appointments"][0]["date"], "2026-10-05")
        mon = date(2026, 10, 5)
        self.assertEqual(self.w.interrupt(at_dt(mon, 570), at_dt(mon, 660), st, "home"), at_dt(mon, 600))
        self.assertEqual(self.w.interrupt(at_dt(mon, 570), at_dt(mon, 660), st, "khan"), at_dt(mon, 660))
        self.assertEqual(self.w.due_beat(at_dt(mon, 600), st, "home")["id"], "hegde_call")

    def test_missed_call_leaves_a_card(self):
        st = state()
        self.w.fire(self.w.beat("hegde_note"), at_dt(date(2026, 10, 3), 600), st)
        mon = date(2026, 10, 5)
        self.w.expire(st, at_dt(mon, 700))
        self.assertIn("hegde_call", st["missed"])
        beat = self.w.due_beat(at_dt(mon, 700), st, "home")
        self.assertEqual(beat["id"], "hegde_card")

    def test_saxena_sets_a_fortnight(self):
        st = state()
        mon = date(2026, 10, 5)
        beat = self.w.due_beat(at_dt(mon, 660), st, "estates")
        self.assertEqual(beat["id"], "saxena_file")
        self.w.fire(beat, at_dt(mon, 660), st)
        self.assertEqual(st["appointments"][-1]["date"], "2026-10-20")
        self.assertIsNone(self.w.due_beat(at_dt(date(2026, 10, 19), 660), st, "estates"))


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def assert_day_is_whole(self, day):
        segs = day["segments"]
        self.assertEqual(segs[0]["from"], "00:00")
        self.assertEqual(segs[-1]["to"], "24:00")
        for a, b in zip(segs, segs[1:]):
            self.assertEqual(a["to"], b["from"], f"gap or overlap at {a['to']}/{b['from']}")
        for s in segs:
            self.assertLess(hm(s["from"]), hm(s["to"]))
        spent = sum(e["price"] for e in day["entries"] if e["k"] == "bag")
        self.assertEqual(day["opening"]["imprest"] - spent, day["state"]["imprest"])

    def test_a_whole_day(self):
        day = self.box.run_day(date(2026, 10, 3))
        self.assert_day_is_whole(day)
        steps = [s for s in day["steps"] if "decision" in s]
        self.assertTrue(12 <= len(steps) <= 40, len(steps))
        self.assertIn("hegde_note", day["state"]["beats"])
        self.assertTrue(day["complete"])
        nxt = self.box.days.load(date(2026, 10, 4))
        self.assertEqual(nxt["segments"][0]["from"], "00:00")
        self.assertTrue(nxt["segments"][0]["asleep"])
        self.assertEqual(nxt["opening"]["imprest"], day["state"]["imprest"])

    def test_a_week_holds_together(self):
        e = self.box.engine()
        for i in range(7):
            day = self.box.run_day(date(2026, 10, 3) + timedelta(days=i), e)
            self.assert_day_is_whole(day)
        beats = day["state"]["beats"]
        self.assertIn("hegde_note", beats)
        self.assertTrue("hegde_call" in beats or "hegde_card" in beats or "hegde_call" in day["state"].get("missed", []))
        self.assertIn("bandhgala_ready", beats)
        ix = [r["date"] for r in self.box.days.index()["days"]]
        self.assertEqual(ix[:8], [(date(2026, 10, 2) + timedelta(days=i)).isoformat() for i in range(8)])

    def test_horizon_and_lead(self):
        e = self.box.engine()
        now = at_dt(date(2026, 10, 3), 9 * 60)
        e.advance(now)
        day = self.box.days.load(date(2026, 10, 3))
        self.assertGreaterEqual(until_of(day), now + timedelta(minutes=self.box.cfg.lead))
        n = len(day["steps"])
        e.advance(now)              # nothing more to decide yet
        self.assertEqual(len(self.box.days.load(date(2026, 10, 3))["steps"]), n)

    def test_resume_after_a_gap(self):
        e = self.box.engine()
        now = at_dt(date(2026, 10, 7), 14 * 60)
        e.advance(now)
        day = self.box.days.load(date(2026, 10, 7))
        self.assertEqual(day["segments"][0]["from"], "00:00")
        self.assertTrue(any(s.get("resumed") for s in day["steps"]))
        self.assertGreaterEqual(until_of(day), now)
        self.assertIsNone(self.box.days.load(date(2026, 10, 4)))           # no invented days in between

    def test_awake_at_midnight_goes_to_bed(self):
        class Insomniac(StubMind):
            def decide(self, messages, sit):
                return json.dumps(answer(action="read", place="home", minutes=30))
        e = self.box.engine(Insomniac())
        prev = self.box.days.load(date(2026, 10, 2))
        prev["state"]["asleep"] = False
        day = e.new_day(prev, date(2026, 10, 3))
        self.box.days.save(day)
        e.advance(at_dt(date(2026, 10, 3), 40))
        day = self.box.days.load(date(2026, 10, 3))
        sources = [s["mind"]["source"] for s in day["steps"] if "mind" in s]
        self.assertIn("bedtime", sources)
        bed = next(s for s in day["segments"] if s.get("asleep"))
        self.assertEqual(bed["from"], "00:30")

    def test_quiet_minutes_touch_nothing(self):
        class Recorder:
            calls = []
            def sync(self): self.calls.append("sync")
            def publish(self, paths, msg): self.calls.append("publish")
        rec = Recorder()
        e = self.box.engine(git=rec)
        now = at_dt(date(2026, 10, 3), 6 * 60)
        e.tick(now)
        self.assertEqual(rec.calls, ["sync", "publish"])
        rec.calls.clear()
        e.tick(now + timedelta(minutes=1))       # the step is already published: no network at all
        self.assertEqual(rec.calls, [])

    def test_start_at_a_chosen_midnight(self):
        e = self.box.engine()
        day1 = self.box.days.load(date(2026, 10, 2))
        day1["state"]["until"] = at_dt(date(2026, 10, 7), 0).isoformat(timespec="minutes")   # what `start` writes
        self.box.days.save(day1)
        self.assertEqual(e.advance(at_dt(date(2026, 10, 6), 20 * 60)), [])                  # the evening before: quiet
        e.advance(at_dt(date(2026, 10, 6), 23 * 60 + 50))
        day = self.box.days.load(date(2026, 10, 7))
        self.assertEqual(day["n"], 6)
        self.assertTrue(day["segments"][0]["asleep"])
        self.assertFalse(any(s.get("resumed") for s in day["steps"]))

    def test_owl(self):
        e = self.box.engine()
        self.box.run_day(date(2026, 10, 3), e)
        day = self.box.days.load(date(2026, 10, 3))
        e.run_owl(day, at_dt(date(2026, 10, 4), 90))
        day = self.box.days.load(date(2026, 10, 3))
        self.assertIn("diary", day["owl"])
        self.assertEqual(day["owl"]["depesche"]["n"], 1)              # Saturday is Depesche night
        self.assertTrue(next(r for r in self.box.days.index()["days"] if r["date"] == "2026-10-03")["owl"])


class FakeLlama(BaseHTTPRequestHandler):
    """Answers like llama-server. The first answer of each request series names a closed place, to test refusals."""
    calls = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeLlama.calls.append(body)
        last = body["messages"][-1]["content"]
        here = re.search(r"You are at: (\w+)", body["messages"][1]["content"])
        here = here.group(1) if here else "home"
        if "refuses" in last:
            ans = answer(action="rest", place=here, minutes=40)
        else:
            ans = answer(action="stay", place="estates", minutes=40)     # shut on a Saturday: refused
        out = {"choices": [{"message": {"content": json.dumps(ans)}}]}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class HTTPTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.server = HTTPServer(("127.0.0.1", 0), FakeLlama)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        FakeLlama.calls = []

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.box.close()

    def test_refusal_then_acceptance(self):
        mind = HTTPMind(f"http://127.0.0.1:{self.server.server_port}")
        e = self.box.engine(mind)
        e.advance(at_dt(date(2026, 10, 3), 6 * 60))
        day = self.box.days.load(date(2026, 10, 3))
        step = next(s for s in day["steps"] if "decision" in s)
        self.assertEqual(step["mind"]["source"], "mind")
        self.assertEqual(step["mind"]["attempts"], 2)
        self.assertIn("closed", step["mind"]["refused"][0][0])
        self.assertEqual(FakeLlama.calls[0]["response_format"]["type"], "json_schema")

    def test_mind_away_gives_a_quiet_step(self):
        mind = HTTPMind("http://127.0.0.1:9")       # nothing listens there
        e = self.box.engine(mind)
        e.advance(at_dt(date(2026, 10, 3), 6 * 60))
        day = self.box.days.load(date(2026, 10, 3))
        step = next(s for s in day["steps"] if "decision" in s)
        self.assertEqual(step["mind"]["source"], "away")
        self.assertFalse(any(x["k"] == "diary" for x in day["entries"]))


class PublishTest(unittest.TestCase):
    def test_tick_commits_and_pushes(self):
        tmp = Path(tempfile.mkdtemp(prefix="hegel-git-"))
        try:
            remote, work = tmp / "remote.git", tmp / "work"
            git = lambda *a, cwd=tmp: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True)
            git("init", "-q", "--bare", "-b", "main", str(remote))
            git("init", "-q", "-b", "main", str(work))
            git("config", "user.email", "test@example.com", cwd=work)
            git("config", "user.name", "Test", cwd=work)
            (work / "docs/days").mkdir(parents=True)
            (work / "mind").mkdir()
            shutil.copy(REPO / "mind/soul.md", work / "mind/soul.md")
            for f in ("2026-10-02.json", "index.json"):
                shutil.copy(REPO / "docs/days" / f, work / "docs/days" / f)
            git("add", "-A", cwd=work)
            git("commit", "-q", "-m", "day 1", cwd=work)
            git("remote", "add", "origin", str(remote), cwd=work)
            git("push", "-q", "-u", "origin", "main", cwd=work)
            cfg = Config({"HEGEL_REPO": str(work), "HEGEL_STATE": str(tmp / "state"), "HEGEL_FEEDS": "0", "HEGEL_BRANCH": "main"})
            e = Engine(cfg, World(), StubMind(), git=Git(cfg))
            e.tick(at_dt(date(2026, 10, 3), 6 * 60))
            log = git("log", "--oneline", "main", cwd=remote).stdout
            self.assertIn("Day 2", log)
            files = git("ls-tree", "-r", "--name-only", "main", cwd=remote).stdout
            self.assertIn("docs/days/2026-10-03.json", files)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
