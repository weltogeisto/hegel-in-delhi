"""Tests for the phone: what he looks up on Wikipedia, what the world does with it, and what it counts as."""
import json
import random
import sys
import tempfile
import threading
import unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import Sandbox, answer  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import lookup  # noqa: E402
from world.engine import until_of  # noqa: E402
from world.mind import NOUNS, StubMind  # noqa: E402
from world.world import at_dt  # noqa: E402

LONG = ("Karl Marx was a German philosopher, social and political theorist, and revolutionary socialist. " * 4
        + "He developed the theory of historical materialism. " * 8).strip()


class FakeWikipedia(BaseHTTPRequestHandler):
    """The two Wikipedia endpoints, for a few pages, and what it was asked."""
    seen, slow, broken = [], 0, False

    def log_message(self, *a):
        pass

    def reply(self, code, body, extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        FakeWikipedia.seen.append((self.path, self.headers.get("User-Agent")))
        if FakeWikipedia.slow > 0:
            FakeWikipedia.slow -= 1
            return self.reply(429, {"error": "slow down"}, {"Retry-After": "1"})
        if FakeWikipedia.broken:
            return self.reply(200, b"<html>not json</html>")
        u = urlparse(self.path)
        if u.path == "/w/api.php":
            q = parse_qs(u.query)["search"][0]
            titles = {"karl marx": ["Karl Marx"], "marx": ["Karl Marx"], "an empty search": [], "a page without text": ["Nothing here"]}.get(q.lower(), [])
            return self.reply(200, [q, titles, [""] * len(titles), [f"https://en.wikipedia.org/wiki/{t.replace(' ', '_')}" for t in titles]])
        title = unquote(u.path.rsplit("/", 1)[1])
        if title == "Karl_Marx":
            return self.reply(200, {"title": "Karl Marx", "extract": LONG, "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Karl_Marx"}}})
        if title == "Nothing_here":
            return self.reply(200, {"title": "Nothing here", "extract": ""})
        self.reply(404, {"error": "no such page"})


class LookupTest(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), FakeWikipedia)
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
        FakeWikipedia.seen, FakeWikipedia.slow, FakeWikipedia.broken = [], 0, False
        self.cache = Path(tempfile.mkdtemp(prefix="hegel-lookup-"))
        self.api = mock.patch.object(lookup, "API", f"http://127.0.0.1:{self.server.server_port}")
        self.api.start()

    def tearDown(self):
        self.api.stop()
        self.server.shutdown()
        self.server.server_close()

    def test_the_first_hit_of_the_search_and_its_summary_are_what_he_reads(self):
        got = lookup.find("Karl Marx", self.cache)
        self.assertEqual(set(got), {"title", "text", "source", "url"})
        self.assertEqual((got["title"], got["source"], got["url"]), ("Karl Marx", "Wikipedia", "https://en.wikipedia.org/wiki/Karl_Marx"))
        self.assertTrue(got["text"].startswith("Karl Marx was a German philosopher"))
        paths = [p for p, _ in FakeWikipedia.seen]
        self.assertEqual(len(paths), 2)
        self.assertTrue(paths[0].startswith("/w/api.php?action=opensearch&search=Karl%20Marx&limit=1&format=json"), paths[0])
        self.assertEqual(paths[1], "/api/rest_v1/page/summary/Karl_Marx")

    def test_the_extract_is_at_most_seven_hundred_characters_and_ends_at_a_sentence(self):
        got = lookup.find("Karl Marx", self.cache)
        self.assertLessEqual(len(got["text"]), 700)
        self.assertGreater(len(LONG), 700)
        self.assertTrue(got["text"].endswith(".") or got["text"].endswith("…"))
        self.assertEqual(" ".join(got["text"].split()), got["text"])

    def test_it_says_who_it_is_and_waits_ten_seconds_at_most(self):
        lookup.find("Karl Marx", self.cache)
        for _, agent in FakeWikipedia.seen:
            self.assertTrue(agent.startswith("hegel-in-delhi/"), agent)
        seen = {}

        def urlopen(req, timeout=None):
            seen["timeout"], seen["ua"] = timeout, req.get_header("User-agent")
            raise OSError("stop here")

        with mock.patch("world.lookup.urllib.request.urlopen", urlopen):
            self.assertEqual(lookup.find("Something else", self.cache), {"note": "The page will not load."})
        self.assertEqual(seen["timeout"], 10)
        self.assertTrue(seen["ua"].startswith("hegel-in-delhi/"))

    def test_a_page_once_read_is_kept_in_the_state_folder_and_not_fetched_again(self):
        first = lookup.find("Karl Marx", self.cache)
        n = len(FakeWikipedia.seen)
        self.assertEqual(lookup.find("karl  MARX", self.cache), first)
        self.assertEqual(len(FakeWikipedia.seen), n)
        self.assertEqual([p.name for p in self.cache.iterdir()], ["karl-marx.json"])
        self.assertEqual(json.loads((self.cache / "karl-marx.json").read_text(encoding="utf-8")), first)

    def test_when_the_page_will_not_load(self):
        for what in ("down", "slow", "garbage"):
            with self.subTest(what):
                FakeWikipedia.seen, FakeWikipedia.slow, FakeWikipedia.broken = [], 0, False
                cache = Path(tempfile.mkdtemp(prefix="hegel-lookup-"))
                if what == "down":
                    api = mock.patch.object(lookup, "API", "http://127.0.0.1:9")
                elif what == "slow":
                    FakeWikipedia.slow = 99                                            # Wikipedia says slow down every time
                    api = mock.patch("world.lookup.time.sleep")
                else:
                    FakeWikipedia.broken = True
                    api = mock.patch.object(lookup, "API", lookup.API)
                with api:
                    self.assertEqual(lookup.find("Karl Marx", cache), {"note": "The page will not load."})
                self.assertEqual(list(cache.iterdir()), [])                              # nothing is kept of a failure

    def test_one_slow_down_is_waited_out_and_tried_again(self):
        FakeWikipedia.slow = 1
        with mock.patch("world.lookup.time.sleep") as nap:
            got = lookup.find("Karl Marx", self.cache)
        self.assertEqual(got["title"], "Karl Marx")
        nap.assert_called_once_with(1)

    def test_a_monkeypatched_fetch_failing_is_a_page_that_will_not_load(self):
        with mock.patch("world.lookup.fetch", side_effect=OSError("down")):
            self.assertEqual(lookup.find("Karl Marx", self.cache), {"note": "The page will not load."})

    def test_nothing_found_and_a_page_without_text(self):
        self.assertEqual(lookup.find("An empty search", self.cache), {"note": "Nothing comes up for that."})
        self.assertEqual(lookup.find("A page without text", self.cache), {"note": "Nothing comes up for that."})
        self.assertEqual(list(self.cache.iterdir()), [])


def reading(*scripts, tech=None, lookup_with=None, place="khan", stub=False):
    """One step by hand for each script, by a scripted mind (or the stand-in itself): returns (box, engine, day, steps, situations seen).
    scripts: what to add to each decision (looks_up, thought, ...). tech: what he owns (default: a phone with a SIM)."""
    seen = []

    class Reader(StubMind):
        def decide(self, messages, sit):
            seen.append(sit)
            i = min(len(seen) - 1, len(scripts) - 1)
            if any("refuses" in x["content"] for x in messages):
                return super().decide(messages, sit)
            words = " ".join(random.Random(sit["id"]).sample(NOUNS, 9))                                # a thought that repeats nothing before it
            return json.dumps(answer(**dict({"thought": f"(rehearsal) {words}.", "action": "stay", "place": place}, **scripts[i])))

    class Watcher(StubMind):
        def decide(self, messages, sit):
            seen.append(sit)
            return super().decide(messages, sit)

    box = Sandbox()
    e = box.engine(Watcher() if stub else Reader())
    if lookup_with:
        e.lookup = lookup_with
    prev = box.days.load(date(2026, 10, 2))
    prev["state"]["asleep"] = False
    day = e.new_day(prev, date(2026, 10, 7))
    st = day["state"]
    st.update(place=place, today={"woke": "06:00"}, until=at_dt(date(2026, 10, 7), 12 * 60).isoformat(timespec="minutes"))
    st["beats"] += ["hegde_note", "hegde_call", "hegde_card", "saxena_file"]
    st["tech"] = tech if tech is not None else {"phone": True, "sim": True, "sim_from": "2026-10-05", "data_from": "2026-10-05"}
    steps = []
    for _ in scripts:
        steps.append(e.step(day, until_of(day)))
    return box, e, day, steps, seen


class PhoneTest(unittest.TestCase):
    def test_what_he_looks_up_is_read_at_the_start_of_the_step_and_opens_the_next_situation(self):
        box, e, day, (one, two), seen = reading({"looks_up": "Karl Marx"}, {})
        try:
            self.assertEqual(one["decision"]["looks_up"], "Karl Marx")
            self.assertEqual(one["read"]["title"], "Karl Marx")
            (r,) = [x for x in day["entries"] if x["k"] == "read"]
            self.assertEqual((r["t"], r["title"], r["source"], r["url"]), (one["t"], "Karl Marx", "Wikipedia", "https://en.wikipedia.org/wiki/Karl_Marx"))
            self.assertIn("A page about Karl Marx", r["text"])
            self.assertTrue(seen[1]["event"].startswith("On your phone you read: Karl Marx. A page about Karl Marx"), seen[1]["event"])
            self.assertNotIn("On your phone", seen[0]["event"])
            self.assertNotIn("read", two)                                                   # and only the next situation
            self.assertNotIn("looks_up", two["decision"])
        finally:
            box.close()

    def test_it_counts_as_met_for_the_1831_gate(self):
        said = "(rehearsal) A thought about Marx that is long enough to count."
        box, e, day, steps, seen = reading({"looks_up": "Karl Marx"}, {"thought": said})
        try:
            self.assertEqual(steps[1]["mind"]["attempts"], 1)
            self.assertNotIn("refused", steps[1]["mind"])
            self.assertEqual(steps[1]["decision"]["thought"], said)
        finally:
            box.close()
        box, e, day, steps, seen = reading({"thought": "(rehearsal) A thought about Marx that is long enough to count."}, {})        # never looked up: refused
        try:
            self.assertIn("you have not met 'Marx' in Delhi", steps[0]["mind"]["refused"][0][0])
            self.assertEqual(steps[0]["mind"]["source"], "stub")
        finally:
            box.close()

    def test_the_owl_reads_what_he_read(self):
        from world import owl
        box, e, day, steps, seen = reading({"looks_up": "Karl Marx"}, {})
        try:
            text = owl.record(day)
            self.assertIn("read on his phone, from Wikipedia, “Karl Marx”: A page about Karl Marx", text)
            self.assertIn("read", owl.KINDS)
        finally:
            box.close()

    def test_without_a_phone_and_sim_there_is_nothing_to_look_it_up_on(self):
        for tech in ({"phone": False, "sim": False}, {"phone": True, "sim": False}, {"phone": False, "sim": True}):
            box, e, day, (one, two), seen = reading({"looks_up": "Karl Marx"}, {}, tech=tech)
            try:
                self.assertEqual(one["read"], {"note": "You have nothing to look it up on."}, tech)
                self.assertTrue(seen[1]["event"].startswith("You have nothing to look it up on."))
                self.assertFalse([x for x in day["entries"] if x["k"] == "read"])
            finally:
                box.close()

    def test_when_the_network_fails_the_page_will_not_load(self):
        with mock.patch("world.lookup.fetch", side_effect=OSError("down")):
            box, e, day, (one, two), seen = reading({"looks_up": "Karl Marx"}, {}, lookup_with=lookup.find)
        try:
            self.assertEqual(one["read"], {"note": "The page will not load."})
            self.assertTrue(seen[1]["event"].startswith("The page will not load."))
            self.assertFalse([x for x in day["entries"] if x["k"] == "read"])
        finally:
            box.close()

    def test_the_pages_are_kept_in_the_state_folder(self):
        server = HTTPServer(("127.0.0.1", 0), FakeWikipedia)
        threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
        FakeWikipedia.seen, FakeWikipedia.slow, FakeWikipedia.broken = [], 0, False
        try:
            with mock.patch.object(lookup, "API", f"http://127.0.0.1:{server.server_port}"):
                box, e, day, (one, two), seen = reading({"looks_up": "Karl Marx"}, {}, lookup_with=lookup.find)
            try:
                self.assertEqual(one["read"]["source"], "Wikipedia")
                self.assertTrue((box.cfg.state / "lookup/karl-marx.json").exists())
                self.assertEqual(len(FakeWikipedia.seen), 2)
            finally:
                box.close()
        finally:
            server.shutdown()
            server.server_close()

    def test_a_look_up_is_not_made_by_a_decision_that_was_refused_or_did_not_ask(self):
        calls = []
        box, e, day, (one, two), seen = reading({"looks_up": None}, {"looks_up": "  "}, lookup_with=lambda q, c: calls.append(q) or {"note": "x"})
        try:
            self.assertEqual(calls, [])
            self.assertNotIn("read", one)
            self.assertNotIn("looks_up", two["decision"])                               # a blank request is no request
        finally:
            box.close()

    def test_the_veil_applies_to_his_reading_and_the_crime_filter_does_not(self):
        pages = {"The caste": "The caste order and the Brahmin.", "A murder": "A murder trial, and the arrest of two men, and a fire."}

        def find(q, cache):
            return {"title": q, "text": pages[q], "source": "Wikipedia", "url": "https://en.wikipedia.org/wiki/" + q.replace(" ", "_")}

        box, e, day, steps, seen = reading({"looks_up": "The caste"}, {"looks_up": "A murder"}, {}, lookup_with=find)
        try:
            veiled, plain = [x for x in day["entries"] if x["k"] == "read"]
            self.assertEqual((veiled["sensitive"], veiled["why"], veiled["topic"]), (True, "caste", "caste"))
            self.assertNotIn("sensitive", plain)                                         # what he reads of crime is his own business
            self.assertTrue(seen[2]["event"].startswith("On your phone you read: A murder. A murder trial, and the arrest of two men"))
        finally:
            box.close()

    def test_the_stand_in_looks_marx_up_once_when_it_has_the_phone(self):
        box, e, day, steps, seen = reading({}, {}, {}, {}, stub=True)
        try:
            asked = [s["decision"].get("looks_up") for s in steps]
            self.assertEqual(asked[0], "Karl Marx")
            self.assertEqual(asked.count("Karl Marx"), 1)                                # once: after it has read, it does not ask again
            self.assertEqual(len([x for x in day["entries"] if x["k"] == "read"]), 1)
        finally:
            box.close()
