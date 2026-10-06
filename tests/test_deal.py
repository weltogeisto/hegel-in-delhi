"""Tests for the owner's decisions: no steering, the dark veil, the news filter, the people who answer, his writings."""
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
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import DAY1, REPO, Sandbox, answer, state  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import contract, owl, voices, works  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.feeds import Feeds, fit_for_papers  # noqa: E402
from world.memory import Memory, record_text  # noqa: E402
from world.mind import TITLES, MindAway, StubMind  # noqa: E402
from world.world import World, at_dt, wordlist  # noqa: E402

SAT = date(2026, 10, 3)
SOUL = (REPO / "mind/soul.md").read_text(encoding="utf-8")
OWL = (REPO / "mind/owl.md").read_text(encoding="utf-8")
README = (REPO / "README.md").read_text(encoding="utf-8")
PAGE = (REPO / "docs/index.html").read_text(encoding="utf-8")
STEERING = ["never look down", "under revision", "test them", "test it against", "nothing violent", "never treat it as settled", "never preach",
            "revise it", "got wrong", "will test next", "the page's voice", "never invent, name or quote real living"]


def sections(text):
    return {h.strip(): body for h, body in re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", text, re.S | re.M)}


def sentences(text):
    return [x for x in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if x]


class PromptTest(unittest.TestCase):
    def test_no_steering_text_remains(self):
        for name, text in (("soul", SOUL), ("owl", OWL), ("README", README), ("voices", (REPO / "mind/voices.md").read_text(encoding="utf-8"))):
            for phrase in STEERING:
                self.assertNotIn(phrase, text.lower(), f"{name}: {phrase}")
        for text in (SOUL, OWL):
            self.assertNotRegex(text.lower(), r"\brevis(e|ing)\b")               # no duty to revise, in either prompt

    def test_his_convictions_are_stated_as_his_own(self):
        who = sections(SOUL)["Who you are"]
        for word in ("Your convictions are your own", "progress of the consciousness of freedom", "India stands at the dawn", "Germanic",
                     "actuality of the ethical idea", "cutting", "courteous", "bridge", "snuff"):
            self.assertIn(word, who)
        self.assertIn("English", who)

    def test_his_life_in_six_to_eight_sentences(self):
        life = sections(SOUL)["Your life"]
        self.assertTrue(6 <= len(sentences(life)) <= 8, len(sentences(life)))
        for fact in ("Stuttgart in 1770", "Tübingen", "Hölderlin", "Schelling", "Bern", "Frankfurt", "Jena", "world-soul on horseback", "Bamberger Zeitung",
                     "Nuremberg", "Marie von Tucher", "1811", "Karl", "Immanuel", "Ludwig", "wedlock", "Heidelberg", "Berlin in 1818", "cholera", "1831"):
            self.assertIn(fact, life)

    def test_what_stays_and_the_real_people_rule(self):
        self.assertIn("November 1831", sections(SOUL)["What you know"])
        self.assertIn("How you sound", sections(SOUL))
        rules = sections(SOUL)["The world's rules"]
        self.assertIn("you may name", rules)
        self.assertIn("never invent their words", rules)
        self.assertIn("you never invent their words", OWL)
        self.assertIn("November 1831", OWL)
        self.assertIn("`evidence`", OWL)

    def test_the_owl_still_writes_as_hegel_from_the_record(self):
        self.assertIn("Write only from it", OWL)
        self.assertIn("Readers in Berlin", OWL)

    def test_readme_rules_in_three_or_four_sentences(self):
        rules = sections(README)["The rules"]
        self.assertTrue(3 <= len(sentences(rules)) <= 4, len(sentences(rules)))
        self.assertIn("does not steer him", rules)
        self.assertIn("veil", rules)

    def test_voices_prompt(self):
        text = (REPO / "mind/voices.md").read_text(encoding="utf-8")
        for word in ("2026", "Marx", "Indian English", '{"says"', "does", "one to three sentences", "third person", "Never speak for him"):
            self.assertIn(word, text)
        self.assertLess(len(text), 3000)

    def test_theses_keep_their_ids_and_the_page_text_is_his_position(self):
        theses = DAY1["state"]["theses"]
        self.assertEqual([t["id"] for t in theses], ["india", "state"])
        self.assertEqual(theses[0]["text"], "India stands outside world history")


class SensitiveTest(unittest.TestCase):
    def setUp(self):
        self.w = World()

    def test_the_list_and_its_matching(self):
        terms = [x.strip() for x in (REPO / "world/data/sensitive.txt").read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
        for t in ("race", "caste", "untouchab*", "brahmin", "dalit", "hindu", "muslim", "islam", "christian", "heathen", "savage", "barbar*", "primitive",
                  "civilis*", "civiliz*", "oriental", "asiatic", "negro", "african", "colonial", "colony", "empire", "conquest", "without history", "inferior", "superior"):
            self.assertIn(t, terms)
        for text, why in (("Untouchability is abolished.", "Untouchability"), ("a CASTE order", "CASTE"), ("The Brahmins spoke first", "Brahmins"),
                          ("his civilisation, or civilization", "civilisation"), ("the barbarous north", "barbarous"), ("a people without history", "without history"),
                          ("the Orientals", "Orientals"), ("The Hindu burns his dead", "Hindu")):
            self.assertEqual(self.w.flag(text), why, text)
        for text in ("a racecourse", "Hindustan", "the track, the pace", "Khan Market at noon", "castellan"):          # whole words only
            self.assertIsNone(self.w.flag(text), text)
        self.assertIsNone(self.w.flag(None, ""))
        self.assertEqual(self.w.flag("nothing", "a colony of ants"), "colony")

    def test_star_in_wordlist_and_comments(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "x.txt").write_text("# comment\nunnamed*\nplain\n", encoding="utf-8")
            with mock.patch("world.world.DATA", tmp):
                rx = wordlist("x.txt", "s?")
            self.assertTrue(rx.search("Unnamed things") and rx.search("plains") and not rx.search("plainly") and not rx.search("comment"))
        finally:
            shutil.rmtree(tmp)

    def test_mark(self):
        e = self.w.mark({"k": "diary", "text": "x"}, "nothing here", "a matter of caste")
        self.assertEqual((e["sensitive"], e["why"]), (True, "caste"))
        self.assertNotIn("sensitive", self.w.mark({"k": "diary"}, "tea and toast", None))

    def test_the_world_flags_and_never_refuses(self):
        st, t = state(), at_dt(SAT, 600)
        a = answer(thought="The caste order is nature fixed by birth, and the Hindu has no state.", says="Is it true that you are Brahmin?",
                   revision="The Orient is the childhood of mankind.")
        errors, _, _ = self.w.check(a, {"open_now": self.w.open_places(t, st)}, {"t": t, "present": ["ramesh"], "beat": None, "public": []}, st)
        self.assertEqual(errors, [])

    def test_every_entry_the_world_writes_is_flagged_when_it_matches(self):
        """Diary, said (his and theirs), revision log, plan, writing and the owl's texts."""
        said = "A matter of caste, said the Brahmin to the Hindu, and the empire agreed."

        class Racist(StubMind):
            def decide(self, messages, sit):
                d = json.loads(super().decide(messages, sit))
                d["thought"] += " This is a matter of race and caste."
                d["revision"] = "The Oriental world is the childhood of mankind."
                if sit["present"]:
                    d["says"] = "The Hindu knows his caste."
                return json.dumps(d)

            def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
                return "A page on the savage and the civilised, which I write down as it stands, long enough to count for something in the afternoon, and I mean every word."

            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                props = (schema or {}).get("properties", {})
                if "does" in props:
                    return json.dumps({"says": said, "does": None})
                if "continues" in props:
                    out = {"title": "On the colonies", "kind": "essay", "to": None, "continues": False}
                    return json.dumps(dict(out, about="The savage and the civilised.") if "about" in props else dict(out, text="A page on the savage and the civilised, long enough."))
                if "plan" in props:
                    return json.dumps({"plan": [{"time": "09:00", "intention": "Ask about the caste of the tailor"}, {"time": "11:00", "intention": "Tea"},
                                                {"time": "13:00", "intention": "Lunch"}]})
                if "diary" in props:
                    return json.dumps({"diary": "Today the question of race and caste decided everything, and I wrote it down as it stands. " * 2,
                                       "revision_log": "Nothing moved.", "depesche": "Readers in Berlin, a plain page.", "theses": []})
                return super().chat(messages, schema, max_tokens, temperature)

        box = Sandbox()
        try:
            e = box.engine(Racist())
            day = box.run_day(SAT, e)
            steps = [s for s in day["steps"] if "decision" in s]
            self.assertEqual(sum(len(s["mind"].get("refused", [])) for s in steps), 0)             # nothing is refused for what it says
            ents = day["entries"]
            for k, why in (("diary", "race"), ("work", "Oriental"), ("plan", "caste")):
                got = [x for x in ents if x["k"] == k]
                self.assertTrue(got, k)
                self.assertTrue(all(x.get("sensitive") is True and x.get("why") == why for x in got), k)
            mine = [x for x in ents if x["k"] == "said" and not x.get("by")]
            theirs = [x for x in ents if x["k"] == "said" and x.get("by")]
            self.assertTrue(mine and theirs)
            self.assertTrue(all(x["sensitive"] and x["why"] == "Hindu" for x in mine))
            self.assertTrue(all(x["sensitive"] and x["why"] == "caste" for x in theirs))
            writing = [x for x in ents if x["k"] == "writing"]
            self.assertTrue(writing and all(x["sensitive"] and x["why"] == "colonies" and x["mode"] == "plain" for x in writing))
            self.assertTrue(all(w.get("sensitive") and w["why"] == "colonies" for w in day["state"]["works"]))        # the title alone is enough for the index
            self.assertFalse([x for x in ents if x["k"] in ("bag", "wear", "world", "file", "people") and "sensitive" in x])
            e.run_owl(box.days.load(SAT), at_dt(SAT + timedelta(days=1), 90))
            o = box.days.load(SAT)["owl"]
            self.assertEqual((o["sensitive"], o["why"]), (["diary"], {"diary": "race"}))
        finally:
            box.close()

    def test_the_owl_flags_the_sections_that_match(self):
        diary = "A diary that is long enough to be believed by the rules of the owl, about tea and a tailor and the heat of the afternoon. "

        class Owlet(StubMind):
            def __init__(self, **texts):
                self.texts = texts

            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                out = {"diary": diary, "revision_log": "Nothing moved.", "depesche": "Readers in Berlin, nothing at all to flag in this page.", "theses": []}
                return json.dumps(dict(out, **self.texts))

        cases = [({}, None, None),
                 ({"revision_log": "The Brahmin lost the argument."}, ["revision_log"], {"revision_log": "Brahmin"}),
                 ({"diary": diary + "A day about caste.", "depesche": "Readers in Berlin, the Muslim kings and the empire."}, ["diary", "depesche"],
                  {"diary": "caste", "depesche": "Muslim"})]
        box = Sandbox()
        try:
            box.run_day(SAT)
            for texts, want, why in cases:
                day = box.days.load(SAT)
                day["owl"] = None
                Engine(box.cfg, World(), StubMind(), owl_mind=Owlet(**texts)).run_owl(day, at_dt(SAT + timedelta(days=1), 90))
                got = box.days.load(SAT)["owl"]
                self.assertEqual((got.get("sensitive"), got.get("why")), (want, why))
                self.assertIn("depesche", got)
        finally:
            box.close()

    def test_day_one_is_flagged_the_way_the_world_would(self):
        w, found = self.w, 0
        for e in DAY1["entries"]:
            texts = [e.get(k) for k in ("text", "title") if e.get(k)]
            if e["k"] in ("diary", "people", "work", "file"):
                self.assertEqual(bool(w.flag(*texts)), bool(e.get("sensitive")), (e["t"], e["k"]))
                if e.get("sensitive"):
                    self.assertEqual(e["why"], w.flag(*texts))
                    found += 1
        self.assertGreaterEqual(found, 4)
        self.assertEqual(DAY1["owl"]["sensitive"], ["depesche"])
        self.assertEqual(DAY1["owl"]["why"]["depesche"], w.flag(DAY1["owl"]["depesche"]["text"]))


class NewsTest(unittest.TestCase):
    CRIME = ["Man killed in robbery bid, two arrested in Delhi", "Woman murdered in Dwarka flat, husband held", "Two killed in road accident on the highway",
             "Girl molested on a bus, police register case", "Fire breaks out at a godown in Narela"]
    STRIFE = ["Army says four soldiers killed along the border", "Communal clash in the town leaves two dead, curfew imposed",
              "Missile strike kills six as the war enters its third year", "Protesters shot dead as unrest spreads in the capital",
              "Militants killed in an encounter, security forces say", "Ceasefire talks resume as shelling continues overnight"]
    PLAIN = ["Parliament passes the new tax bill after a long debate", "RBI keeps the repo rate unchanged for the third time",
             "Supreme Court reserves its verdict on the electoral bonds petition", "Delhi to see light rain through the weekend, says the IMD"]

    def test_crime_is_dropped_and_war_and_strife_are_kept(self):
        for t in self.CRIME:
            self.assertFalse(fit_for_papers(t), t)
        for t in self.STRIFE + self.PLAIN:
            self.assertTrue(fit_for_papers(t), t)
        for t in ("Labour union calls a strike over wages", "Strikes on the Delhi Metro rattle commuters"):       # a strike is not military by itself
            self.assertTrue(fit_for_papers(t))
        self.assertTrue(fit_for_papers("Air strike kills seven, killed in the shelling, officials say"))

    def test_the_papers_that_reach_the_verandah(self):
        box = Sandbox()
        try:
            rss = "<rss><channel>" + "".join(f"<item><title>{t}</title></item>" for t in self.CRIME + self.STRIFE[:2] + self.PLAIN[:2]) + "</channel></rss>"
            f = Feeds(box.cfg)
            f.online = True
            with mock.patch("world.feeds.get", return_value=rss.encode()):
                got = f.headlines(SAT, n=20)
            self.assertEqual(got, self.STRIFE[:2] + self.PLAIN[:2])
            self.assertFalse(any(t in got for t in self.CRIME))
        finally:
            box.close()


def find_present(cid, place):
    """A date and minute at which cast member cid is at place (searching from Saturday 3 October)."""
    w, st = World(), state()
    for i in range(60):
        d = SAT + timedelta(days=i)
        for m in range(600, 1200, 30):
            if cid in w.present_ids(place, at_dt(d, m), st):
                return d, m
    raise AssertionError(f"{cid} is never at {place}")


class Talker(StubMind):
    """Decides to talk (or to write), answers the voice and the writing calls from the script, and keeps what it was asked.
    A writing is answered by `writing` (the chat call that writes it all), or in plain mode by `sitting` (the chat call that says what it is)
    and `text` (the completion: a string, an exception, or a function of the prompt and the seed)."""

    def __init__(self, says="Nidhi, what do you make of this market?", action="talk", voice=None, writing=None, sitting=None, text=None):
        self.says, self.action, self.voice, self.writing, self.sitting, self.text, self.asked = says, action, voice, writing, sitting, text, []

    def decide(self, messages, sit):
        if any("refuses" in x["content"] for x in messages):
            return super().decide(messages, sit)
        return json.dumps(answer(thought=f"(rehearsal) {sit['time']} here, with {sit['present']} about.", action=self.action, place=sit["place"], minutes=30, says=self.says))

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        props = (schema or {}).get("properties", {})
        kind = "voice" if "does" in props else "sitting" if "about" in props else "write" if "continues" in props else None
        if kind:
            self.asked.append((kind, messages))
            script = {"voice": self.voice, "sitting": self.sitting, "write": self.writing}[kind]
            if isinstance(script, Exception):
                raise script
            if script is not None:
                return script(messages) if callable(script) else script
        return super().chat(messages, schema, max_tokens, temperature)

    def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
        self.asked.append(("complete", (prompt, max_tokens, seed)))
        if isinstance(self.text, Exception):
            raise self.text
        if self.text is not None:
            return self.text(prompt, seed) if callable(self.text) else self.text
        return super().complete(prompt, max_tokens, temperature, seed)


def one_step(mind, cid, place, d=None, m=None, prior=None, patch_greet=0.0, write_mode="plain"):
    """One real step at a time when cid is at place. Returns (box, day, step)."""
    box = Sandbox()
    box.cfg.write_mode = write_mode
    e = box.engine(mind)
    d, m = (d, m) if d else find_present(cid, place)
    prev = box.days.load(date(2026, 10, 2))
    prev["state"]["asleep"] = False
    day = e.new_day(prev, d)
    st = day["state"]
    st["place"], st["today"] = place, {"woke": "06:00"}
    st["until"] = at_dt(d, m).isoformat(timespec="minutes")
    for x in prior or []:
        day["entries"].append(x)
    with mock.patch("world.world.GREET_P", patch_greet):
        step = e.step(day, at_dt(d, m))
    return box, e, day, step


class VoiceTest(unittest.TestCase):
    def test_who_answers(self):
        w = World()
        self.assertEqual(voices.pick(w.cast, "Nidhi, a word?", ["ramesh", "nidhi"]), "nidhi")
        self.assertEqual(voices.pick(w.cast, "Mr. Malhotra, your bid", ["nidhi", "malhotra"]), "malhotra")
        self.assertEqual(voices.pick(w.cast, "Malhotra, and then Nidhi", ["nidhi", "malhotra"]), "malhotra")       # the one named first
        self.assertEqual(voices.pick(w.cast, "Two cups, please.", ["bookseller", "masterji", "nidhi"]), "masterji")   # first who is not background
        self.assertEqual(voices.pick(w.cast, "Namaste.", ["clerk"]), "clerk")                                         # else a background person
        self.assertEqual(voices.pick(w.cast, "Excuse me, the bookseller?", ["bookseller", "nidhi"]), "bookseller")
        self.assertIsNone(voices.pick(w.cast, "Hello", []))

    def test_clean(self):
        c = World().cast["nidhi"]
        self.assertEqual(voices.clean(c, {"says": '  “Not a fool.  A philosopher.” ', "does": "She taps the book"}),
                         {"by": "Nidhi Rao", "says": "Not a fool. A philosopher.", "does": "She taps the book."})
        self.assertEqual(voices.clean(World().cast["clerk"], {"says": "Next.", "does": None})["by"], "The ticket clerk")
        for bad in (None, "text", {}, {"says": ""}, {"says": 3}, {"says": " "}, []):
            self.assertIsNone(voices.clean(c, bad))
        long = voices.clean(c, {"says": "word " * 200, "does": "x " * 300})
        self.assertLessEqual(len(long["says"]), voices.SAY_CAP)
        self.assertLessEqual(len(long["does"]), voices.DOES_CAP + 2)

    def test_the_stand_in_answers_the_voice_schema_the_same_way_every_time(self):
        ask = [{"role": "user", "content": "x"}]
        a = StubMind().chat(ask, contract.VOICE_SCHEMA)
        self.assertEqual(a, StubMind().chat(ask, contract.VOICE_SCHEMA))
        out = json.loads(a)
        self.assertEqual(sorted(out), ["does", "says"])
        self.assertTrue(out["says"].startswith("(rehearsal)"))
        self.assertEqual(sorted(contract.VOICE_SCHEMA["required"]), ["does", "says"])

    def test_the_person_he_names_answers_after_him_and_opens_the_next_situation(self):
        d, m = find_present("nidhi", "iic")
        mind = Talker(voice=json.dumps({"says": "Not a fool. A philosopher, which is worse.", "does": "She taps the book against her palm"}))
        box, e, day, step = one_step(mind, "nidhi", "iic", prior=[{"t": "08:00", "k": "said", "to": "Nidhi Rao", "text": "Earlier."},
                                                                 {"t": "08:01", "k": "said", "by": "Nidhi Rao", "to": "Hegel", "text": "Later."},
                                                                 {"t": "08:02", "k": "diary", "text": "Nidhi is quick."}])
        try:
            calls = [c for c in mind.asked if c[0] == "voice"]
            self.assertEqual(len(calls), 1)                                                         # one voice call for the step
            system, user = calls[0][1][0]["content"], calls[0][1][1]["content"]
            self.assertEqual(system, (REPO / "mind/voices.md").read_text(encoding="utf-8"))
            self.assertIn("You are Nidhi Rao, doctoral student in philosophy, JNU.", user)
            self.assertIn("Writing her doctorate on Hegel", user)                                   # the card
            self.assertIn("India International Centre", user)
            self.assertIn("He says: “Nidhi, what do you make of this market?”", user)
            self.assertIn("What has passed between you and him:\n- Today, 08:00, he said to Nidhi Rao: “Earlier.”\n- Today, 08:01, you said: “Later.”\n", user)
            self.assertNotIn("Nidhi is quick", user)                                                # what she cannot have heard
            self.assertEqual(step["voice"], {"by": "Nidhi Rao", "says": "Not a fool. A philosopher, which is worse.", "does": "She taps the book against her palm."})
            at = [x for x in day["entries"] if x["t"] == step["t"] and x["k"] in ("diary", "said")]
            self.assertEqual([(x["k"], x.get("by")) for x in at], [("diary", None), ("said", None), ("said", "Nidhi Rao")])        # after his, same minute
            self.assertEqual(at[-1]["to"], "Hegel")
            sit, ctx = e.world.situation(at_dt(d, m) + timedelta(minutes=30), day["state"], day, step)       # the next step opens with her
            self.assertTrue(sit["event"].startswith("Nidhi Rao says: “Not a fool. A philosopher, which is worse.” She taps the book against her palm."))
        finally:
            box.close()

    def test_the_opening_is_only_for_the_step_that_follows(self):
        w, st = World(), state()
        prev = {"t": "10:00", "end": "10:30", "voice": {"by": "Nidhi Rao", "says": "Hello.", "does": None}}
        t = at_dt(SAT, 630)
        self.assertTrue(w.situation(t, st, {"steps": [], "entries": []}, prev)[0]["event"].startswith("Nidhi Rao says: “Hello.”"))
        self.assertNotIn("Hello", w.situation(at_dt(SAT, 700), state(), {"steps": [], "entries": []}, prev)[0]["event"])      # a gap: not any more

    def test_without_a_name_the_first_person_present_answers(self):
        mind = Talker(says="Namaste.", voice=json.dumps({"says": "Namaste, sir.", "does": None}))
        box, e, day, step = one_step(mind, "masterji", "khan")
        try:
            d, m = find_present("masterji", "khan")
            present = e.world.present_ids("khan", at_dt(d, m), state())
            first = next(c for c in present if not e.world.cast[c].get("background"))
            self.assertEqual(step["voice"]["by"], e.world.cast[first]["name"])
        finally:
            box.close()

    def test_a_mind_that_is_away_or_unusable_is_skipped_silently(self):
        for voice in (MindAway("no answer"), "I would rather not.", json.dumps({"says": "", "does": None}), json.dumps(["x"])):
            with self.subTest(voice=str(voice)[:30]):
                box, e, day, step = one_step(Talker(voice=voice), "nidhi", "iic")
                try:
                    self.assertNotIn("voice", step)
                    self.assertEqual(step["mind"]["source"], "stub")                                 # the decision stands
                    self.assertFalse(any(x.get("by") for x in day["entries"] if x["k"] == "said"))
                    self.assertTrue(any(x["k"] == "said" and not x.get("by") for x in day["entries"]))
                finally:
                    box.close()

    def test_nobody_present_no_call(self):
        mind = Talker(says="Hello?")
        box = Sandbox()
        try:
            e = box.engine(mind)
            prev = box.days.load(date(2026, 10, 2))
            prev["state"]["asleep"] = False
            day = e.new_day(prev, SAT)
            day["state"].update(place="lodhi", until=at_dt(SAT, 14 * 60).isoformat(timespec="minutes"), today={"woke": "06:00"})
            step = e.step(day, at_dt(SAT, 14 * 60))
            self.assertEqual([c for c in mind.asked if c[0] == "voice"], [])
            self.assertNotIn("voice", step)
        finally:
            box.close()

    def test_a_person_he_knows_may_speak_first_seeded_by_date_and_person(self):
        w = World()
        rolls = [bool(w.greeter({"t": at_dt(SAT + timedelta(days=i), 600), "fresh": ["nidhi"]})) for i in range(300)]
        self.assertTrue(0.25 < sum(rolls) / 300 < 0.45, sum(rolls))
        again = [bool(w.greeter({"t": at_dt(SAT + timedelta(days=i), 600), "fresh": ["nidhi"]})) for i in range(300)]
        self.assertEqual(rolls, again)
        self.assertIsNone(w.greeter({"t": at_dt(SAT, 600), "fresh": []}))
        self.assertIsNone(w.greeter({"t": at_dt(SAT, 600)}))

    def test_the_greeting_joins_the_event_the_entries_and_what_he_has_met(self):
        seen = []

        class Watch(Talker):
            def decide(self, messages, sit):
                seen.append(sit["event"])
                return super().decide(messages, sit)

        mind = Watch(says=None, action="stay", voice=json.dumps({"says": "Back again, Mr. Hegel? The Marx stall is open.", "does": None}))
        box, e, day, step = one_step(mind, "nidhi", "iic", patch_greet=1.0)
        try:
            self.assertEqual(len([c for c in mind.asked if c[0] == "voice"]), 1)
            user = [c for c in mind.asked if c[0] == "voice"][0][1][1]["content"]
            self.assertIn("You have just caught sight of him. You speak first.", user)
            self.assertNotIn("He says:", user)
            self.assertIn("Nidhi Rao is here.", seen[0])
            self.assertTrue(seen[0].endswith("Nidhi Rao says: “Back again, Mr. Hegel? The Marx stall is open.”"), seen[0])         # in the event the mind sees
            said = [x for x in day["entries"] if x["k"] == "said"]
            self.assertEqual([(x["by"], x["to"]) for x in said], [("Nidhi Rao", "Hegel")])
            self.assertLess(day["entries"].index(said[0]), day["entries"].index(next(x for x in day["entries"] if x["k"] == "diary")))
            self.assertNotIn("voice", step)                                                           # no reply: he said nothing
            known = e.memory.known_text(day, e.world.situation(at_dt(*find_present("nidhi", "iic")), day["state"], day, None)[0])
            self.assertIn("Marx", known)                                                              # their words count as met
        finally:
            box.close()

    def test_at_most_a_greeting_and_an_answer_per_step(self):
        mind = Talker(voice=json.dumps({"says": "Namaste.", "does": None}))
        box, e, day, step = one_step(mind, "nidhi", "iic", patch_greet=1.0)
        try:
            self.assertEqual(len([c for c in mind.asked if c[0] == "voice"]), 2)
            self.assertEqual([x.get("by") for x in day["entries"] if x["k"] == "said"], ["Nidhi Rao", None, "Nidhi Rao"])
        finally:
            box.close()

    def test_a_pc_that_does_not_wake_for_a_greeting_is_not_woken_twice(self):
        from world.mind import HTTPMind
        mind = HTTPMind("http://127.0.0.1:9")
        tries = []
        mind.health = lambda timeout=3: tries.append(1) or False
        box = Sandbox()
        try:
            e = box.engine(mind)
            d, m = find_present("nidhi", "iic")
            prev = box.days.load(date(2026, 10, 2))
            prev["state"]["asleep"] = False
            day = e.new_day(prev, d)
            day["state"].update(place="iic", today={"woke": "06:00"}, until=at_dt(d, m).isoformat(timespec="minutes"))
            with mock.patch("world.world.GREET_P", 1.0):
                step = e.step(day, at_dt(d, m))
            self.assertEqual(step["mind"]["source"], "away")
            self.assertEqual(len(tries), 1)
        finally:
            box.close()

    def test_moments_for_a_voice_are_what_was_said_in_their_eyes_with_all_of_today(self):
        box = Sandbox()
        try:
            e = box.engine()
            c = e.world.cast["nidhi"]
            day = {"date": "2026-10-10", "n": 9, "steps": [{"t": f"{h:02d}:00", "decision": {}} for h in range(8, 15)], "entries": [
                {"t": "09:30", "k": "said", "to": "Nidhi Rao", "text": "Is it true?"},
                {"t": "09:31", "k": "said", "by": "Nidhi Rao", "to": "Hegel", "text": "Mostly."},
                {"t": "09:40", "k": "diary", "text": "Nidhi is quick."},
                {"t": "09:45", "k": "said", "by": "Masterji", "to": "Hegel", "text": "Thursday."}]}
            lines = e.memory.moments(c, day, [], voice=True)
            self.assertEqual(lines, ["Today, 09:30, he said to Nidhi Rao: “Is it true?”", "Today, 09:31, you said: “Mostly.”"])    # inside the window, no thoughts
            self.assertNotIn("Is it true?", " ".join(e.memory.moments(c, day, [])))                                  # Hegel's own recall keeps the window
            past = [{"date": "2026-10-09", "n": 8, "entries": day["entries"], "steps": [], "owl": None}]
            self.assertIn("Day 8 (Fri 9 Oct), 09:31, Nidhi Rao said to you: “Mostly.”", e.memory.moments(c, day, past))
        finally:
            box.close()

    def test_the_owl_reads_their_lines_and_the_writing(self):
        day = {"n": 2, "title": "Sunday", "holiday": None, "segments": [], "entries": [
            {"t": "13:40", "k": "said", "text": "Is it true?", "to": "Nidhi Rao"},
            {"t": "13:40", "k": "said", "by": "Nidhi Rao", "to": "Hegel", "text": "Mostly."},
            {"t": "15:00", "k": "writing", "title": "On sense", "kind": "letter", "to": "Goethe", "sitting": 2, "text": "word " * 200}]}
        text = owl.record(day)
        self.assertIn("13:40 said to Nidhi Rao: “Is it true?”", text)
        self.assertIn("13:40 Nidhi Rao said to you: “Mostly.”", text)
        line = next(x for x in text.splitlines() if "wrote" in x)
        self.assertTrue(line.startswith("15:00 wrote “On sense” (letter to Goethe, sitting 2): word word"))
        self.assertLessEqual(len(line.split("): ", 1)[1]), 402)
        self.assertEqual(owl.KINDS.index("writing") < owl.KINDS.index("work"), True)

    def test_the_voice_call_goes_out_with_its_schema(self):
        from world.mind import HTTPMind
        from test_world import FakeLlama
        from http.server import HTTPServer
        server = HTTPServer(("127.0.0.1", 0), FakeLlama)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        FakeLlama.calls = []
        box = Sandbox()
        try:
            e = box.engine(HTTPMind(f"http://127.0.0.1:{server.server_port}"))
            d, m = find_present("nidhi", "iic")
            got = e.voice("nidhi", {"date": d.isoformat(), "entries": [], "steps": []},
                          {"day": "Monday", "time": "15:00", "place": "iic", "outfit": "kurta", "event": "x"}, "Hello.")
            self.assertIsNone(got)                                                                    # the fake answers with a decision: unusable
            body = FakeLlama.calls[0]
            self.assertEqual(list(body["response_format"]["json_schema"]["schema"]["properties"]), ["says", "does"])
            self.assertEqual(body["messages"][0]["role"], "system")
        finally:
            server.shutdown()
            server.server_close()
            box.close()


class WritingTest(unittest.TestCase):
    def test_clean(self):
        ok = works.clean({"title": "  On   sense ", "kind": "essay", "to": None, "continues": True, "text": "  A page about sense, long enough.  "})
        self.assertEqual(ok, {"title": "On sense", "kind": "essay", "to": None, "continues": True, "text": "A page about sense, long enough."})
        self.assertEqual(works.clean({"title": "x", "kind": "sermon", "to": " Goethe ", "continues": "yes", "text": "Some text, long enough to count."}),
                         {"title": "x", "kind": "other", "to": "Goethe", "continues": False, "text": "Some text, long enough to count."})
        for bad in (None, [], {}, {"title": "", "text": "long enough text here, yes"}, {"title": "t", "text": "short"}, {"title": 1, "text": "long enough text here, yes"}):
            self.assertIsNone(works.clean(bad))

    def test_a_sitting_is_capped_at_three_thousand_characters(self):
        text = "A sentence of some length goes here. " * 200
        cut = works.clean({"title": "t", "kind": "essay", "to": None, "continues": False, "text": text})["text"]
        self.assertLessEqual(len(cut), 3000)
        self.assertTrue(cut.endswith("."))
        words = works.clean({"title": "t", "kind": "essay", "to": None, "continues": False, "text": "word " * 1000})["text"]
        self.assertLessEqual(len(words), 3000)
        self.assertTrue(words.endswith("…"))

    def test_the_index_continues_or_starts(self):
        st, d = {}, date(2026, 10, 3)
        sit = lambda title, cont, text="one two three four five": {"title": title, "kind": "essay", "to": None, "continues": cont, "text": text}
        a = works.file(st, sit("On Sense", False), d)
        self.assertEqual(st["works"], [{"id": "on-sense", "title": "On Sense", "kind": "essay", "to": None, "started": "2026-10-03", "words": 5, "sittings": 1, "last": "2026-10-03",
                                        "tail": "one two three four five"}])
        self.assertEqual((a["k"], a["title"], a["sitting"], a["words"], a["work"]), ("writing", "On Sense", 1, 5, "on-sense"))
        b = works.file(st, sit("on  sense", True, "six seven"), d + timedelta(days=2))          # the same title, in any case: it continues
        self.assertEqual((b["sitting"], b["title"]), (2, "On Sense"))
        self.assertEqual((st["works"][0]["words"], st["works"][0]["sittings"], st["works"][0]["last"], st["works"][0]["started"]), (7, 2, "2026-10-05", "2026-10-03"))
        works.file(st, sit("On Sense", False), d)                                                 # not a continuation: a new work, same title
        works.file(st, sit("Letter to Hegde", True), d)                                           # continues nothing: new
        self.assertEqual([w["id"] for w in st["works"]], ["on-sense", "on-sense-2", "letter-to-hegde"])
        works.file(st, sit("On Sense", True), d)                                                  # the latest of that title
        self.assertEqual([w["sittings"] for w in st["works"]], [2, 2, 1])
        self.assertEqual(sorted(st["works"][0]), ["id", "kind", "last", "sittings", "started", "tail", "title", "to", "words"])
        self.assertEqual(st["works"][0]["tail"], "six seven")                                     # the tail of the latest sitting only
        self.assertIn("“On Sense” (essay, 2 sittings)", works.ask(st))
        self.assertTrue(works.ask(st).endswith(contract.WRITE_FORMAT))
        self.assertNotIn("manuscripts so far", works.ask({}))
        self.assertTrue(works.ask({}).startswith("You sat down to write. What did you write?"))

    def test_the_stand_in_answers_the_writing_schema_the_same_way_every_time(self):
        ask = [{"role": "user", "content": "You sat down to write."}]
        a = StubMind().chat(ask, contract.WRITE_SCHEMA)
        self.assertEqual(a, StubMind().chat(ask, contract.WRITE_SCHEMA))
        out = json.loads(a)
        self.assertEqual(sorted(out), sorted(contract.WRITE_SCHEMA["required"]))
        self.assertIn(out["kind"], contract.WRITING_KINDS)
        self.assertTrue(out["title"].startswith("(rehearsal)") and out["text"].startswith("(rehearsal)"))
        with_shelf = [{"role": "user", "content": works.ask({"works": [{"title": "On Sense", "kind": "essay", "sittings": 1}]})}]
        again = json.loads(StubMind().chat(with_shelf, contract.WRITE_SCHEMA))
        self.assertIn(again["title"], ("On Sense",) + tuple("(rehearsal) " + t for t in __import__("world.mind", fromlist=["TITLES"]).TITLES))
        self.assertEqual(again["continues"], again["title"] == "On Sense")
        self.assertEqual(contract.WRITE_SCHEMA["properties"]["kind"]["enum"], ["essay", "letter", "notes", "chapter", "poem", "other"])

    def sitting(self, title="On the verandah", text="The morning came in with the papers and the heat, and I wrote it down.", **kw):
        return json.dumps(dict({"title": title, "kind": "notes", "to": None, "continues": False, "text": text}, **kw))

    def test_in_chat_mode_one_extra_call_when_he_writes_and_the_sitting_is_an_entry_and_a_manuscript(self):
        mind = Talker(says=None, action="write", writing=self.sitting())
        box, e, day, step = one_step(mind, "ramesh", "home", write_mode="chat")
        try:
            calls = [c for c in mind.asked if c[0] == "write"]
            self.assertEqual(len(calls), 1)
            msgs = calls[0][1]
            self.assertEqual(msgs[0]["content"], SOUL)
            self.assertEqual(msgs[-1]["content"], works.ask({}))
            self.assertIn("You sat down to write. What did you write?", msgs[-1]["content"])
            self.assertEqual(msgs[-2]["role"], "assistant")                                       # the decision he has just made
            w = next(x for x in day["entries"] if x["k"] == "writing")
            self.assertEqual(w["t"], step["t"])
            self.assertEqual({k: w[k] for k in ("title", "kind", "to", "sitting", "work")}, {"title": "On the verandah", "kind": "notes", "to": None, "sitting": 1, "work": "on-the-verandah"})
            self.assertEqual(w["words"], len(w["text"].split()))
            self.assertEqual(day["state"]["works"][0]["words"], w["words"])
            self.assertLess([x["k"] for x in day["entries"]].index("diary"), [x["k"] for x in day["entries"]].index("writing"))
        finally:
            box.close()

    def test_no_call_unless_he_writes(self):
        mind = Talker(says=None, action="read", writing=self.sitting())
        box, e, day, step = one_step(mind, "ramesh", "home", write_mode="chat")
        try:
            self.assertEqual([c for c in mind.asked if c[0] == "write"], [])
            self.assertFalse(any(x["k"] == "writing" for x in day["entries"]))
            self.assertNotIn("works", day["state"])
        finally:
            box.close()

    def test_after_1831_names_he_has_not_met_are_asked_for_once_and_then_the_writing_is_dropped(self):
        bad = self.sitting(text="Marx would have seen at once what the tea-seller sells, I think so.")
        good = self.sitting(text="The tea-seller sells more than tea, I think so, and he knows it.")
        replies = []

        def script(messages):
            replies.append(messages[-1]["content"])
            return bad if len(replies) == 1 else good

        mind = Talker(says=None, action="write", writing=script)
        box, e, day, step = one_step(mind, "ramesh", "home", write_mode="chat")
        try:
            self.assertEqual(len([c for c in mind.asked if c[0] == "write"]), 2)
            self.assertIn("Write it again without 'Marx'", replies[1])
            self.assertEqual([x["text"] for x in day["entries"] if x["k"] == "writing"], ["The tea-seller sells more than tea, I think so, and he knows it."])
        finally:
            box.close()
        mind = Talker(says=None, action="write", writing=bad)
        box, e, day, step = one_step(mind, "ramesh", "home", write_mode="chat")
        try:
            self.assertEqual(len([c for c in mind.asked if c[0] == "write"]), 2)                    # asked once more, no more
            self.assertFalse(any(x["k"] == "writing" for x in day["entries"]))                        # dropped
            self.assertTrue(any(x["k"] == "diary" for x in day["entries"]))                           # the decision stands
            self.assertNotIn("works", day["state"])
            self.assertEqual(step["mind"]["source"], "stub")
        finally:
            box.close()

    def test_what_he_has_already_met_may_be_written(self):
        mind = Talker(says=None, action="write", writing=self.sitting(text="Ambedkar writes like a barrister, and I read him on the verandah."))
        box, e, day, step = one_step(mind, "ramesh", "home", write_mode="chat")
        try:
            self.assertTrue(any(x["k"] == "writing" for x in day["entries"]))                         # day one's record has Ambedkar
        finally:
            box.close()

    def test_a_mind_that_is_away_or_unusable_drops_the_writing_quietly(self):
        for writing in (MindAway("no answer"), "not json", json.dumps({"title": "", "kind": "essay", "to": None, "continues": False, "text": "x"})):
            with self.subTest(writing=str(writing)[:20]):
                box, e, day, step = one_step(Talker(says=None, action="write", writing=writing), "ramesh", "home", write_mode="chat")
                try:
                    self.assertFalse(any(x["k"] == "writing" for x in day["entries"]))
                    self.assertTrue(any(x["k"] == "diary" for x in day["entries"]))
                finally:
                    box.close()

    def test_sittings_add_up_across_steps_and_days(self):
        class Writer(StubMind):
            def __init__(self):
                self.n = 0

            def decide(self, messages, sit):
                if any("refuses" in x["content"] for x in messages) or sit["place"] != "home" or not 540 <= int(sit["time"][:2]) * 60 + int(sit["time"][3:]) < 1080:
                    return super().decide(messages, sit)
                return json.dumps(answer(thought=f"(rehearsal) {sit['id']} at the desk with the ledger.", action="write", place="home", minutes=60))

            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                if "continues" in (schema or {}).get("properties", {}):
                    self.n += 1
                    return json.dumps({"title": "A Letter" if self.n < 3 else "The Ledger", "kind": "letter", "to": "Karl", "continues": self.n in (2,),
                                       "text": f"Dear Karl, this is the sitting number {self.n}, and I have more to say than a page can hold."})
                return super().chat(messages, schema, max_tokens, temperature)

        box = Sandbox()
        box.cfg.write_mode = "chat"
        try:
            e = box.engine(Writer())
            for i in range(2):
                day = box.run_day(SAT + timedelta(days=i), e)
            ws = day["state"]["works"]
            self.assertEqual(ws[0]["title"], "A Letter")
            self.assertEqual(ws[0]["sittings"], 2)                                                    # continued once, by title
            self.assertEqual(ws[0]["to"], "Karl")
            self.assertTrue(all(w["kind"] == "letter" for w in ws))
            first = box.days.load(SAT)
            self.assertEqual(first["state"]["works"][0]["started"], "2026-10-03")
            self.assertEqual(ws[0]["started"], "2026-10-03")
            self.assertEqual(sum(w["sittings"] for w in ws), sum(e["k"] == "writing" for d in (first, day) for e in d["entries"]))
        finally:
            box.close()


PROSE = ("The morning came in with the papers and the heat, and I set it down as I saw it, which is the only method that I know. "
         "What the papers call news is the day's surface, and beneath it the old necessity goes about its work.\n\n"
         "I read them twice, and was the wiser only in the matter of the price of tea.")
UNMET = ("Marx would have seen at once what the tea-seller sells, and the whole of the afternoon besides, I think, "
         "for he saw everything at once and wrote it down.")
SITTING = json.dumps({"title": "On the verandah", "kind": "notes", "to": None, "continues": False,
                      "about": "The morning on the verandah, and what the papers made of it."})
CHAT_SITTING = json.dumps({"title": "On the verandah", "kind": "notes", "to": None, "continues": False,
                           "text": "The morning came in with the papers and the heat, and I wrote it down."})


class FakeCompletion(BaseHTTPRequestHandler):
    """Answers /completion with `content` (or with `code`) and the chat endpoint with `plan`, and keeps what it was sent: (path, body)."""
    calls, content, code, plan, writing = [], "", 200, "", ""

    def log_message(self, *a):
        pass

    def send(self, code, out):
        data = json.dumps(out).encode() if not isinstance(out, bytes) else out
        self.send_response(code)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.send(200, {"status": "ok"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeCompletion.calls.append((self.path, body))
        if self.path != "/completion":
            about = "about" in body["response_format"]["json_schema"]["schema"]["properties"]
            return self.send(200, {"choices": [{"message": {"content": FakeCompletion.plan if about else FakeCompletion.writing}}]})
        if FakeCompletion.code != 200:
            return self.send(FakeCompletion.code, {})
        self.send(200, FakeCompletion.content if isinstance(FakeCompletion.content, bytes) else {"content": FakeCompletion.content, "stop": True})


def write_with(mind, st=None, write_mode="plain", known=""):
    """Engine.write on its own: (the sitting or None, the state it was written into)."""
    box = Sandbox()
    try:
        box.cfg.write_mode, box.cfg.shelf = write_mode, False
        st = state() if st is None else st
        msgs = [{"role": "system", "content": SOUL}, {"role": "user", "content": "the situation"}]
        return box.engine(mind).write(msgs, "the decision", {"t": at_dt(SAT, 15 * 60), "known_text": known}, st), st
    finally:
        box.close()


class NoComplete(Talker):
    complete = None                 # a mind that cannot complete


class Scribe(StubMind):
    """Writes at the desk at home through the day, three sittings in all: a letter, the same letter again (it carries on), then another work.
    Keeps the prompts it was given to complete."""

    def __init__(self):
        self.n, self.prompts = 0, []

    def decide(self, messages, sit):
        if any("refuses" in x["content"] for x in messages) or sit["place"] != "home" or not 540 <= int(sit["time"][:2]) * 60 + int(sit["time"][3:]) < 1080:
            return super().decide(messages, sit)
        return json.dumps(answer(thought=f"(rehearsal) {sit['id']} at the desk with the ledger.", action="write", place="home", minutes=60))

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        props = (schema or {}).get("properties", {})
        if "continues" in props:
            self.n += 1
            out = {"title": "A Letter" if self.n < 3 else "The Ledger", "kind": "letter", "to": "Karl", "continues": self.n == 2}
            return json.dumps(dict(out, about=f"Sitting {self.n}.") if "about" in props else dict(out, text=f"Dear Karl, this is the sitting number {self.n}, and I have more to say than a page can hold."))
        return super().chat(messages, schema, max_tokens, temperature)

    def complete(self, prompt, max_tokens=700, temperature=None, seed=None):
        self.prompts.append(prompt)
        return f"This is the sitting number {len(self.prompts)}, and I have more to say than a page can hold, as the heat of the afternoon and the quiet of the house allow."


class WritingPromptTest(unittest.TestCase):
    """The prompt of a plain-text sitting, and what is made of the completion."""
    D = date(2026, 10, 6)

    @staticmethod
    def plan(**kw):
        return dict({"title": "On the verandah", "kind": "essay", "to": None, "continues": False, "about": "the morning's papers"}, **kw)

    def test_the_header_of_each_kind(self):
        for kind in ("essay", "notes", "chapter", "other"):
            self.assertEqual(works.prompt(self.plan(kind=kind), {}, self.D),
                             ("Hegel, On the verandah. Written at Delhi, 6 October 2026.\n[the morning's papers]\n\n", ""))
        self.assertEqual(works.prompt(self.plan(kind="poem", title="Ode to tea."), {}, self.D),
                         ("Hegel, Ode to tea. A poem, written at Delhi, 6 October 2026.\n[the morning's papers]\n\n", ""))         # no full stop twice
        self.assertEqual(works.prompt(self.plan(kind="letter", to="Karl", title="Letter to Karl"), {}, self.D),
                         ("Hegel to Karl. Delhi, 6 October 2026.\n[the morning's papers]\n\nDear Karl,\n\n", "Dear Karl,"))      # a new letter opens with its salutation
        self.assertEqual(works.prompt(self.plan(kind="letter", to="a friend in Berlin"), {}, self.D)[1], "Dear friend,")
        self.assertEqual(works.prompt(self.plan(kind="letter"), {}, self.D)[0].split("\n")[0], "Hegel, On the verandah. Written at Delhi, 6 October 2026.")        # no one to
        self.assertIn("Delhi, 12 December 2026.", works.prompt(self.plan(), {}, date(2026, 12, 12))[0])
        self.assertIn("Delhi, 1 January 2027.", works.prompt(self.plan(), {}, date(2027, 1, 1))[0])

    def test_a_manuscript_he_carries_on_gives_its_tail_to_flow_on_from(self):
        text = "\n\n".join(" ".join(f"w{p}x{i}" for i in range(90)) + "." for p in range(5))             # five paragraphs of 90 words
        st = {}
        works.file(st, {"title": "On Sense", "kind": "essay", "to": None, "continues": False, "text": text}, self.D)
        head = "Hegel, On Sense. Written at Delhi, 6 October 2026.\n[the morning's papers]\n\n"
        prompt, opening = works.prompt(self.plan(title="on  sense", continues=True, kind="poem"), st, self.D)          # the manuscript's own title and kind
        self.assertTrue(prompt.startswith(head))
        tail = prompt[len(head):]
        self.assertEqual((len(tail.split()), opening), (works.CARRY, ""))
        self.assertTrue(text.endswith(tail))
        self.assertIn("\n\n", tail)                                                                         # paragraphs stay
        self.assertTrue(tail.startswith("w") and tail.endswith("."))                                        # at a word, not in the middle of one
        self.assertEqual(works.prompt(self.plan(title="On Sense"), st, self.D)[0], head)                    # not continuing: fresh
        letter = {"title": "Dear Karl", "kind": "letter", "to": "Karl", "continues": False, "text": "Dear Karl, " + "word " * 30 + "end."}
        works.file(st, letter, self.D)
        prompt, opening = works.prompt(self.plan(title="Dear Karl", continues=True, kind="essay"), st, self.D)
        self.assertEqual(prompt, f"Hegel to Karl. Delhi, 6 October 2026.\n[the morning's papers]\n\n{works.carried(st['works'][1]['tail'])}")
        self.assertEqual(opening, "")                                                                       # no second salutation

    def test_an_index_from_before_tails_starts_fresh(self):
        st = {"works": [{"id": "on-sense", "title": "On Sense", "kind": "letter", "to": "Karl", "started": "2026-10-03", "words": 5, "sittings": 1, "last": "2026-10-03"}]}
        self.assertEqual(works.prompt(self.plan(title="On Sense", continues=True), st, self.D),
                         ("Hegel to Karl. Delhi, 6 October 2026.\n[the morning's papers]\n\n", ""))      # the header, no tail, and no salutation: it is not a new letter
        got = works.file(st, {"title": "On Sense", "kind": "letter", "to": "Karl", "continues": True, "text": "one two three"}, self.D)
        self.assertEqual((got["sitting"], st["works"][0]["tail"]), (2, "one two three"))
        self.assertEqual(works.prompt(self.plan(title="Nothing yet", continues=True), st, self.D)[0].split("\n")[0], "Hegel, Nothing yet. Written at Delhi, 6 October 2026.")

    def test_the_index_keeps_the_tail_of_the_latest_sitting_from_a_word(self):
        self.assertEqual(works.tail_of("A short sitting.\n"), "A short sitting.")
        text = "alpha " * 400 + "omega."
        tail = works.tail_of(text)
        self.assertTrue(text.endswith(tail) and tail.startswith("alpha") and tail.endswith("omega.") and 700 < len(tail) <= works.TAIL)
        self.assertEqual(works.tail_of("x" * 5000), "")          # one word as long as that has no beginning to start from
        st = {}
        entry = works.file(st, {"title": "t", "kind": "essay", "to": None, "continues": False, "text": text, "about": "tea", "mode": "plain"}, self.D)
        self.assertEqual(st["works"][0]["tail"], tail)
        self.assertEqual((entry["mode"], entry["about"]), ("plain", "tea"))
        self.assertNotIn("mode", works.file({}, {"title": "t", "kind": "essay", "to": None, "continues": False, "text": text}, self.D))        # as before

    def test_what_he_means_to_write(self):
        ok = works.outline({"title": "  On   sense ", "kind": "letter", "to": " Karl ", "continues": True, "about": " The  [heat]\nof the day. "})
        self.assertEqual(ok, {"title": "On sense", "kind": "letter", "to": "Karl", "continues": True, "about": "The (heat) of the day."})
        self.assertEqual(works.outline({"title": "t", "kind": "sermon", "to": "", "continues": "yes", "about": "a" * 300}),
                         {"title": "t", "kind": "other", "to": None, "continues": False, "about": "a" * 200})
        for bad in (None, [], {}, {"title": "", "about": "x"}, {"title": "t"}, {"title": "t", "about": " "}, {"title": 1, "about": "x"}, {"title": "t", "about": 3}):
            self.assertIsNone(works.outline(bad))

    def test_the_echo_of_the_title_and_the_header_is_dropped(self):
        raw = ("\n\nHegel, On the verandah. Written at Delhi, 6 October 2026.\n[the morning's papers]\n\nON THE VERANDAH.\n\n" + PROSE)
        self.assertEqual(works.sitting(self.plan(), raw)["text"], PROSE)
        self.assertEqual(works.sitting(self.plan(), "On the verandah\n" + PROSE)["text"], PROSE)
        self.assertEqual(works.sitting(self.plan(kind="letter", to="Karl"), "Dear Karl,\n\n" + PROSE, "Dear Karl,")["text"], "Dear Karl,\n\n" + PROSE)    # said once
        self.assertIn("On the verandah", works.sitting(self.plan(), PROSE.replace("The morning", "On the verandah, the morning"))["text"])             # but in the text it stays

    def test_the_text_stops_where_a_new_document_begins(self):
        for stop in ("Hegel to Karl. Delhi, 7 October 2026.", "Hegel, On the colonies. Written at Delhi, 7 October 2026.", "* * *", "***", "THE END", "The end.", "Footnotes", "FOOTNOTES:"):
            with self.subTest(stop=stop):
                got = works.sitting(self.plan(), PROSE + "\n\n" + stop + "\n\nSomething else, written long after, that does not belong here at all.")
                self.assertEqual(got["text"], PROSE)
        self.assertIn("Hegel", works.sitting(self.plan(), PROSE + " Hegel, he said, would have laughed at it, and I did.")["text"])         # only at the start of a line

    def test_paragraphs_stay_and_other_whitespace_goes(self):
        raw = "  The first   paragraph runs\non over two lines,\tand ends here, with enough words to count as a paragraph.  \n\n\n\n  The second one, also long enough to be counted, ends here too.  \r\n"
        self.assertEqual(works.sitting(self.plan(), raw)["text"], "The first paragraph runs on over two lines, and ends here, with enough words to count as a paragraph.\n\n"
                                                                    "The second one, also long enough to be counted, ends here too.")
        poem = works.sitting(self.plan(kind="poem"), "Roses are red,\nviolets are blue,\nthe tea is hot,\nand so are you, my dear,\n\nand so on, and on, and on we go, dear friend.\n\nTHE END")
        self.assertEqual(poem["text"].split("\n"), ["Roses are red,", "violets are blue,", "the tea is hot,", "and so are you, my dear,", "", "and so on, and on, and on we go, dear friend."])

    def test_the_typography_is_one(self):
        raw = "“The morning,” he said, “came in with the papers” -- and the heat, and I set it down as it was, which is ‘my’ method, and the only one that I know."
        self.assertEqual(works.sitting(self.plan(), raw)["text"], "\"The morning,\" he said, \"came in with the papers\" — and the heat, and I set it down as it was, which is 'my' method, and the only one that I know.")

    def test_a_sitting_is_cut_to_three_thousand_characters_and_back_to_a_sentence_end(self):
        long = works.sitting(self.plan(), "A sentence of some length goes here, and then it stops. " * 200)["text"]
        self.assertTrue(len(long) <= works.CAP and long.endswith("stops."))
        words = works.sitting(self.plan(), "word " * 1000)
        self.assertIsNone(words)                                                                         # no sentence end at all: nothing usable
        mid = works.sitting(self.plan(), PROSE + " And then I began to say that the")["text"]
        self.assertEqual(mid, PROSE)                                                                     # the unfinished sentence goes
        self.assertTrue(len(works.sitting(self.plan(kind="letter", to="Karl"), "A sentence of some length goes here. " * 200, "Dear Karl,")["text"]) <= works.CAP)

    def test_too_short_or_empty_is_unusable(self):
        for raw in (None, "", "  \n\n ", "Hegel, On the verandah. Written at Delhi, 6 October 2026.", "Only a few words here.", "word " * 18 + "end.", "* * *\n" + PROSE):
            with self.subTest(raw=str(raw)[:30]):
                self.assertIsNone(works.sitting(self.plan(), raw))
        self.assertIsNotNone(works.sitting(self.plan(), "word " * 19 + "end."))                         # twenty words are enough
        self.assertIsNone(works.sitting(self.plan(kind="letter", to="Karl"), "Few words.", "Dear Karl,"))      # the salutation does not count

    def test_a_new_letter_begins_with_its_salutation(self):
        got = works.sitting(self.plan(kind="letter", to="Karl", continues=False), PROSE, "Dear Karl,")
        self.assertEqual((got["text"], got["kind"], got["to"], got["about"]), ("Dear Karl,\n\n" + PROSE, "letter", "Karl", "the morning's papers"))


class HTTPCompleteTest(unittest.TestCase):
    def setUp(self):
        from world.mind import HTTPMind
        self.server = HTTPServer(("127.0.0.1", 0), FakeCompletion)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        FakeCompletion.calls, FakeCompletion.content, FakeCompletion.code, FakeCompletion.plan, FakeCompletion.writing = [], "\n\nThe text.", 200, SITTING, CHAT_SITTING
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.mind = HTTPMind(self.url)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_the_request_is_a_raw_prompt_with_no_chat_template_and_no_stop(self):
        self.assertEqual(self.mind.complete("Hegel, X.\n\n", 700), "\n\nThe text.")                   # as it comes: the caller cleans up
        (path, body), = FakeCompletion.calls
        self.assertEqual(path, "/completion")
        self.assertEqual(body, {"prompt": "Hegel, X.\n\n", "n_predict": 700, "temperature": 0.7, "cache_prompt": False})
        self.mind.complete("p", 50, temperature=0.2, seed=1831)
        self.assertEqual(FakeCompletion.calls[1][1], {"prompt": "p", "n_predict": 50, "temperature": 0.2, "cache_prompt": False, "seed": 1831})
        from world.mind import HTTPMind
        HTTPMind(self.url, temperature=0.4).complete("q")
        self.assertEqual((FakeCompletion.calls[2][1]["temperature"], FakeCompletion.calls[2][1]["n_predict"]), (0.4, 700))        # the mind's own default
        self.assertFalse(any("stop" in b or "messages" in b or "response_format" in b for _, b in FakeCompletion.calls))

    def test_a_mind_that_does_not_answer_is_away(self):
        from world.mind import HTTPMind
        FakeCompletion.code = 503
        with self.assertRaises(MindAway):
            self.mind.complete("p")
        for content in (b"not json", b"[]", b"{}"):
            FakeCompletion.code, FakeCompletion.content = 200, content
            with self.assertRaises(MindAway, msg=content):
                self.mind.complete("p")
        FakeCompletion.content = b'{"content": null}'
        self.assertEqual(self.mind.complete("p"), "")
        with self.assertRaises(MindAway):
            HTTPMind("http://127.0.0.1:9").complete("p")          # nothing listens there

    def test_the_whole_chain_over_http(self):
        """One chat call for what the sitting is, one completion for its text; a refused completion falls back to the chat call."""
        box = Sandbox()
        try:
            box.cfg.shelf = False
            e, st = box.engine(self.mind), state()
            FakeCompletion.content = "\n\nHegel, On the verandah. Written at Delhi, 6 October 2026.\n\n" + PROSE
            msgs = [{"role": "system", "content": SOUL}, {"role": "user", "content": "the situation"}]
            ctx = {"t": at_dt(SAT, 15 * 60), "known_text": ""}
            w = e.write(msgs, "the decision", ctx, st)
            self.assertEqual((w["title"], w["kind"], w["mode"], w["text"]), ("On the verandah", "notes", "plain", PROSE))
            (p1, chat), (p2, comp) = FakeCompletion.calls
            self.assertEqual((p1, p2), ("/v1/chat/completions", "/completion"))
            self.assertEqual(list(chat["response_format"]["json_schema"]["schema"]["properties"]), ["title", "kind", "to", "continues", "about"])
            self.assertEqual(chat["messages"][-1]["content"], works.sitting_ask(st))
            self.assertEqual(comp["prompt"], works.prompt(works.outline(json.loads(SITTING)), st, SAT)[0])
            self.assertEqual(comp["n_predict"], works.TOKENS)
            FakeCompletion.calls.clear()
            FakeCompletion.code = 503                                                # the server has no /completion
            w = e.write(msgs, "the decision", ctx, st)
            self.assertEqual([p for p, _ in FakeCompletion.calls], ["/v1/chat/completions", "/completion", "/v1/chat/completions"])
            self.assertEqual((w["mode"], w["text"]), ("chat", "The morning came in with the papers and the heat, and I wrote it down."))
            self.assertEqual(list(FakeCompletion.calls[2][1]["response_format"]["json_schema"]["schema"]["properties"]), ["title", "kind", "to", "continues", "text"])
        finally:
            box.close()


class PlainWritingTest(unittest.TestCase):
    """He writes: what the sitting is by a chat call, its text by a completion, and the fallbacks."""

    def kinds(self, mind):
        return [k for k, _ in mind.asked if k != "voice"]

    def test_a_sitting_is_a_chat_call_and_a_completion_and_an_entry_and_a_manuscript(self):
        mind = Talker(says=None, action="write", sitting=SITTING, text=PROSE)
        box, e, day, step = one_step(mind, "ramesh", "home")
        try:
            self.assertEqual(self.kinds(mind), ["sitting", "complete"])
            msgs = next(m for k, m in mind.asked if k == "sitting")
            self.assertEqual(msgs[0]["content"], SOUL)
            self.assertEqual(msgs[-1]["content"], works.sitting_ask({}))
            self.assertTrue(msgs[-1]["content"].startswith("You sat down to write. Say what you will write, not the text yet"))
            self.assertEqual(msgs[-2]["role"], "assistant")                                       # the decision he has just made
            self.assertEqual(msgs[-1]["content"].count("Your manuscripts"), 0)
            prompt, n_predict, seed = next(a for k, a in mind.asked if k == "complete")
            d = date.fromisoformat(day["date"])
            self.assertEqual(prompt, f"Hegel, On the verandah. Written at Delhi, {d.day} {d:%B %Y}.\n[The morning on the verandah, and what the papers made of it.]\n\n")
            self.assertEqual((n_predict, seed), (700, None))
            w = next(x for x in day["entries"] if x["k"] == "writing")
            self.assertEqual({k: w[k] for k in ("title", "kind", "to", "sitting", "work", "text", "mode", "about")},
                             {"title": "On the verandah", "kind": "notes", "to": None, "sitting": 1, "work": "on-the-verandah", "text": PROSE, "mode": "plain",
                              "about": "The morning on the verandah, and what the papers made of it."})
            self.assertEqual(w["words"], len(PROSE.split()))
            self.assertEqual(day["state"]["works"][0]["tail"], PROSE)
            self.assertNotIn("sensitive", w)
            self.assertEqual(step["mind"]["source"], "stub")
        finally:
            box.close()

    def test_no_call_at_all_unless_he_writes(self):
        mind = Talker(says=None, action="read", sitting=SITTING, text=PROSE)
        box, e, day, step = one_step(mind, "ramesh", "home")
        try:
            self.assertEqual(self.kinds(mind), [])
            self.assertFalse(any(x["k"] == "writing" for x in day["entries"]))
        finally:
            box.close()

    def test_what_the_sitting_is_about_is_checked_for_the_veil_too(self):
        about = json.dumps(dict(json.loads(SITTING), about="What the tailor said of his caste."))
        box, e, day, step = one_step(Talker(says=None, action="write", sitting=about, text=PROSE), "ramesh", "home")
        try:
            w = next(x for x in day["entries"] if x["k"] == "writing")
            self.assertEqual((w["sensitive"], w["why"]), (True, "caste"))
        finally:
            box.close()

    def test_a_sitting_he_carries_on_flows_from_the_sitting_before(self):
        mind = Talker(text=PROSE, sitting=json.dumps(dict(json.loads(SITTING), title="on the VERANDAH", continues=True, about="More of it.")))
        st = state()
        works.file(st, {"title": "On the verandah", "kind": "notes", "to": None, "continues": False, "text": PROSE}, SAT)
        w, st = write_with(mind, st)
        self.assertEqual((w["mode"], w["continues"]), ("plain", True))
        (_, (prompt, _, _)) = next(x for x in mind.asked if x[0] == "complete")
        self.assertEqual(prompt, f"Hegel, On the verandah. Written at Delhi, 3 October 2026.\n[More of it.]\n\n{PROSE}")       # the tail: all of it, it is short
        self.assertIn("“On the verandah” (notes, 1 sitting)", next(m for k, m in mind.asked if k == "sitting")[-1]["content"])
        entry = works.file(st, w, SAT)
        self.assertEqual((entry["sitting"], len(st["works"])), (2, 1))

    def test_a_completion_with_a_name_he_has_not_met_is_made_again_with_another_seed(self):
        texts = iter([UNMET, PROSE])
        mind = Talker(sitting=SITTING, text=lambda prompt, seed: next(texts))
        w, _ = write_with(mind)
        self.assertEqual((w["mode"], w["text"]), ("plain", PROSE))
        seeds = [a[2] for k, a in mind.asked if k == "complete"]
        self.assertEqual(len(seeds), 2)
        self.assertIsNone(seeds[0])
        self.assertIsInstance(seeds[1], int)
        self.assertEqual(self.kinds(mind), ["sitting", "complete", "complete"])                    # no chat call that writes
        w, _ = write_with(Talker(sitting=SITTING, text=UNMET), known="Marx")                         # what he has met may be written
        self.assertEqual(w["mode"], "plain")

    def test_a_name_in_what_it_is_about_counts_too(self):
        mind = Talker(sitting=json.dumps(dict(json.loads(SITTING), about="What Marx would say.")), text=PROSE, writing=CHAT_SITTING)
        w, _ = write_with(mind)
        self.assertEqual((w["mode"], self.kinds(mind)), ("chat", ["sitting", "complete", "complete", "write"]))

    def test_names_twice_and_the_chat_call_writes_it(self):
        mind = Talker(sitting=SITTING, text=UNMET, writing=CHAT_SITTING)
        w, st = write_with(mind)
        self.assertEqual((w["mode"], w["text"]), ("chat", "The morning came in with the papers and the heat, and I wrote it down."))
        self.assertEqual(self.kinds(mind), ["sitting", "complete", "complete", "write"])
        self.assertNotIn("about", w)
        msgs = next(m for k, m in mind.asked if k == "write")
        self.assertEqual(msgs[-1]["content"], works.ask({}))                                           # the old call, as it was

    def test_names_everywhere_and_the_writing_is_dropped(self):
        bad = json.dumps(dict(json.loads(CHAT_SITTING), text=UNMET))
        mind = Talker(sitting=SITTING, text=UNMET, writing=bad)
        w, st = write_with(mind)
        self.assertIsNone(w)
        self.assertEqual(self.kinds(mind), ["sitting", "complete", "complete", "write", "write"])       # the chat call asked once more, no more
        self.assertNotIn("works", st)

    def test_a_completion_that_fails_or_is_unusable_falls_back_to_the_chat_call(self):
        for text in (MindAway("HTTP 404 from the mind"), "Too short to be a sitting.", "\n\n", "* * *\n" + PROSE):
            with self.subTest(text=str(text)[:20]):
                mind = Talker(sitting=SITTING, text=text, writing=CHAT_SITTING)
                w, _ = write_with(mind)
                self.assertEqual(w["mode"], "chat")
                self.assertEqual(self.kinds(mind), ["sitting", "complete", "write"])                    # one completion, then the chat call

    def test_a_chat_call_that_cannot_say_what_it_is_falls_back_to_the_chat_call(self):
        for sitting in ("not json", json.dumps({"title": "x", "kind": "essay", "to": None, "continues": False}), json.dumps({"title": "", "about": "x"})):
            with self.subTest(sitting=sitting[:20]):
                mind = Talker(sitting=sitting, text=PROSE, writing=CHAT_SITTING)
                w, _ = write_with(mind)
                self.assertEqual((w["mode"], self.kinds(mind)), ("chat", ["sitting", "write"]))          # no completion without a title and an about

    def test_a_mind_that_is_away_for_the_first_call_drops_the_writing_quietly(self):
        mind = Talker(sitting=MindAway("no answer"), text=PROSE, writing=CHAT_SITTING)
        w, _ = write_with(mind)
        self.assertIsNone(w)
        self.assertEqual(self.kinds(mind), ["sitting"])                                                  # the chat call would not answer either

    def test_a_mind_without_complete_uses_the_chat_call(self):
        mind = NoComplete(sitting=SITTING, writing=CHAT_SITTING)
        w, _ = write_with(mind)
        self.assertEqual((w["mode"], self.kinds(mind)), ("chat", ["write"]))

    def test_chat_mode_is_the_old_single_call_exactly(self):
        calls = []

        class Spy(Talker):
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                calls.append((messages, schema, max_tokens, temperature))
                return super().chat(messages, schema, max_tokens, temperature)

        mind = Spy(sitting=SITTING, text=PROSE, writing=CHAT_SITTING)
        st = state()
        w, _ = write_with(mind, st, write_mode="chat")
        (messages, schema, max_tokens, temperature), = calls
        self.assertEqual(messages, [{"role": "system", "content": SOUL}, {"role": "user", "content": "the situation"}, {"role": "assistant", "content": "the decision"},
                                    {"role": "user", "content": works.ask(st)}])
        self.assertIs(schema, contract.WRITE_SCHEMA)
        self.assertEqual((max_tokens, temperature), (1100, None))
        self.assertEqual(self.kinds(mind), ["write"])                                                    # nothing else asked, no completion
        self.assertEqual(w, {"title": "On the verandah", "kind": "notes", "to": None, "continues": False,
                             "text": "The morning came in with the papers and the heat, and I wrote it down.", "mode": "chat"})

    def test_chat_mode_asks_the_rewrite_and_drops_as_before(self):
        replies = []
        bad = json.dumps(dict(json.loads(CHAT_SITTING), text="Marx would have seen at once what the tea-seller sells, I think so."))

        def script(messages):
            replies.append(messages[-1]["content"])
            return bad

        mind = Talker(writing=script, text=PROSE, sitting=SITTING)
        w, _ = write_with(mind, write_mode="chat")
        self.assertIsNone(w)
        self.assertIn("Write it again without 'Marx'", replies[1])
        self.assertEqual(self.kinds(mind), ["write", "write"])

    def test_the_stand_in_completes_and_says_what_the_sitting_is(self):
        a = StubMind().complete("Hegel, X.\n\n")
        self.assertEqual(a, StubMind().complete("Hegel, X.\n\n"))                                       # the same every time
        self.assertNotEqual(a, StubMind().complete("Hegel, X.\n\n", seed=7))
        self.assertTrue(a.startswith("(rehearsal) ") and a.count("\n\n") == 1)
        self.assertGreaterEqual(len(a.split()), works.MIN_WORDS)
        ask = [{"role": "user", "content": works.sitting_ask({"works": [{"title": "On Sense", "kind": "essay", "sittings": 1}]})}]
        out = json.loads(StubMind().chat(ask, contract.SITTING_SCHEMA))
        self.assertEqual(sorted(out), sorted(contract.SITTING_SCHEMA["required"]))
        self.assertTrue(out["about"].startswith("(rehearsal)") and "text" not in out)
        self.assertEqual(out["continues"], out["title"] == "On Sense")
        self.assertEqual(contract.SITTING_SCHEMA["properties"]["kind"]["enum"], contract.WRITING_KINDS)
        self.assertEqual(contract.SITTING_SCHEMA["properties"]["about"]["maxLength"], 200)
        self.assertNotEqual(contract.SITTING_ASK[:40], contract.WRITE_ASK[:40])

    def test_sittings_add_up_across_steps_and_days_in_plain_mode(self):
        box = Sandbox()
        try:
            mind = Scribe()
            e = box.engine(mind)
            for i in range(2):
                day = box.run_day(SAT + timedelta(days=i), e)
            ws = day["state"]["works"]
            sittings = [x for d in (box.days.load(SAT), day) for x in d["entries"] if x["k"] == "writing"]
            self.assertTrue(sittings and all(x["mode"] == "plain" for x in sittings))
            self.assertEqual((ws[0]["title"], ws[0]["sittings"], ws[0]["to"]), ("A Letter", 2, "Karl"))
            self.assertEqual(sum(w["sittings"] for w in ws), len(sittings))
            self.assertEqual(len(mind.prompts), len(sittings))
            first = sittings[0]
            self.assertTrue(first["text"].startswith("Dear Karl,\n\nThis is the sitting number 1"))      # a new letter begins with its salutation
            self.assertTrue(mind.prompts[0].endswith("Dear Karl,\n\n"))
            self.assertTrue(mind.prompts[1].startswith("Hegel to Karl. Delhi, "))                         # the same letter again: its header, and then
            self.assertTrue(mind.prompts[1].endswith(works.carried(works.tail_of(first["text"]))))        # the end of the sitting before, so that it flows on
            self.assertFalse(mind.prompts[1].endswith("Dear Karl,\n\n"))
            self.assertEqual(ws[0]["tail"], works.tail_of(sittings[1]["text"]))
        finally:
            box.close()

    def test_a_whole_stub_day_in_chat_mode_never_completes(self):
        box = Sandbox()
        try:
            box.cfg.write_mode = "chat"
            mind = Scribe()
            day = box.run_day(SAT, box.engine(mind))
            sittings = [x for x in day["entries"] if x["k"] == "writing"]
            self.assertTrue(sittings and all(x["mode"] == "chat" and "about" not in x for x in sittings))
            self.assertEqual(mind.prompts, [])
            self.assertTrue(all(x["text"].startswith("Dear Karl, this is the sitting number") for x in sittings))
        finally:
            box.close()


class WriteModeConfigTest(unittest.TestCase):
    def test_plain_unless_chat_is_asked_for(self):
        from world.config import Config
        self.assertEqual(Config().write_mode, "plain")
        for value, mode in (("chat", "chat"), (" CHAT ", "chat"), ("plain", "plain"), ("", "plain"), ("banana", "plain")):
            self.assertEqual(Config({"HEGEL_WRITE_MODE": value}).write_mode, mode, value)


class PageNodeTest(unittest.TestCase):
    """The panel code of docs/index.html, run in node with a stand-in for the browser."""

    HARNESS = """
    const h = require('fs').readFileSync(process.argv[1], 'utf8');
    const grab = (a, b) => { const i = h.indexOf(a); return h.slice(i, h.indexOf(b, i)); };
    const src = ["const esc = s =>", "const rupees", "const paras = t =>", "const KLABEL"].map(a => grab(a, "\\n")).concat(
      [grab("function line(e){", "function owlHtml"), grab("function owlHtml(m){", "function renderPanel")]).join("\\n");
    const io = JSON.parse(process.argv[2]);
    const ls = io.storage === 'throw' ? {getItem(){ throw new Error('blocked'); }} : {getItem: k => io.storage};
    const page = new Function("D", "DAY", "dayMode", "ENTRIES", "localStorage", src + "; return {line, owlHtml, vz, vkey, manuscripts, purse, purseHtml, wiki, KLABEL, revealed, show: () => showSens};")(io.D, [], 'archive', io.ENTRIES || [], ls);
    const arg = a => a && a.$e ? a.$e.map(i => io.ENTRIES[i]) : a;      // {"$e": [0]}: those of the page's own entries, by identity
    console.log(JSON.stringify(io.calls.map(c => { const f = page[c[0]]; return typeof f === 'function' ? f(...c.slice(1).map(arg)) : f; })));
    """

    def run_page(self, calls, D=None, entries=None, storage=None):
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        io = {"calls": calls, "D": D or {"date": "2026-10-04", "state": {}}, "ENTRIES": entries, "storage": storage}
        got = subprocess.run(["node", "-e", self.HARNESS, str(REPO / "docs/index.html"), json.dumps(io)], capture_output=True, text=True)
        self.assertEqual(got.returncode, 0, got.stderr)
        return json.loads(got.stdout)

    def test_the_script_parses_and_the_label_is_there(self):
        self.assertIn("writing:'Wrote'", PAGE)
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        js = PAGE[PAGE.index("<script>") + 8:PAGE.rindex("</script>")]
        out = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(0, 'utf8')); console.log('ok')"], input=js, capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "ok", out.stderr)
        self.assertEqual(self.run_page([["KLABEL"]])[0]["writing"], "Wrote")

    def test_their_words_and_his_writing_in_the_feed(self):
        said = [{"k": "said", "by": "Nidhi Rao", "to": "Hegel", "text": "Not <a> fool."}, {"k": "said", "to": "Nidhi Rao", "text": "Is it?"}, {"k": "said", "text": "Hm."}]
        write = [{"k": "writing", "title": "On Sense", "kind": "notes", "to": None, "sitting": 1, "text": "One.\n\nTwo <b>."},
                 {"k": "writing", "title": "Dear Karl", "kind": "letter", "to": "Karl", "sitting": 3, "text": "Hello."},
                 {"k": "writing", "title": "Ode", "kind": "poem", "to": None, "text": "La."}]
        got = self.run_page([["line", e] for e in said + write])
        self.assertEqual(got[0], "<b>Nidhi Rao</b>: “Not &lt;a&gt; fool.”")
        self.assertEqual(got[1], "<b>To Nidhi Rao</b>: “Is it?”")
        self.assertEqual(got[2], "“Hm.”")
        self.assertEqual(got[3], "<b>On Sense</b> (notes)<br>One.<br><br>Two &lt;b&gt;.")
        self.assertEqual(got[4], "<b>Dear Karl</b> (letter to Karl, sitting 3)<br>Hello.")
        self.assertEqual(got[5], "<b>Ode</b> (poem)<br>La.")

    def test_the_veil(self):
        band, plain = self.run_page([["vz", "2026-10-04|3", "caste", "<p>x</p>", "p"], ["vz", "k", None, "<p>y</p>", "n"]])
        self.assertIn('<button type="button" class="veil" aria-expanded="false"', band)
        self.assertIn('aria-controls="vp-2026_10_04_3"', band)
        self.assertIn("<span>Sensitive · 19th-century views — show</span><small>on caste</small>", band)
        self.assertIn('<div class="veiled" id="vp-2026_10_04_3" hidden><p>x</p></div>', band)
        self.assertNotIn("<small>", plain)
        self.assertIn('id="vn-k"', plain)

    def test_a_revealed_entry_and_the_viewers_own_toggle(self):
        got = self.run_page([["vz", "k", "race", "<p>z</p>", "p"]], storage="1")                    # asked not to be asked: no band at all
        self.assertEqual(got, ["<p>z</p>"])
        got = self.run_page([["vz", "k", "race", "<p>z</p>", "p"], ["show"]], storage="0")
        self.assertIn("veil", got[0])
        self.assertFalse(got[1])
        got = self.run_page([["vz", "k", "race", "<p>z</p>", "p"], ["show"]], storage="throw")      # storage blocked: still renders, veiled
        self.assertIn("veil", got[0])

    def test_owl_sections_flagged_as_sensitive_are_veiled(self):
        D = {"date": "2026-10-04", "state": {"theses": []}, "owl": {"written": "03:10", "diary": "A diary.", "revision_log": "A log.",
             "depesche": {"title": "Depesche aus Delhi, Nr. 1", "text": "Readers in Berlin,"}, "sensitive": ["diary", "depesche"], "why": {"diary": "caste", "depesche": "Muslim"}, "topic": {"diary": "caste", "depesche": "religion"}}}
        html = self.run_page([["owlHtml", 0]], D=D)[0]
        self.assertEqual(html.count('class="veil"'), 2)
        self.assertIn("<small>on caste</small>", html)
        self.assertIn("<small>on religion</small>", html)
        self.assertIn("<h3>Revision log</h3><p>A log.</p>", html)                                   # the section that is not flagged stays open
        self.assertIn('data-veil="2026-10-04|owl|diary"', html)
        D["owl"].pop("sensitive")
        self.assertNotIn("veil", self.run_page([["owlHtml", 0]], D=D)[0])

    def test_the_manuscripts_so_far_leave_out_what_is_still_to_come_today(self):
        D = {"date": "2026-10-04", "state": {"works": [
            {"id": "a", "title": "On Sense", "kind": "essay", "to": None, "words": 1500, "sittings": 3},
            {"id": "b", "title": "Dear <Karl>", "kind": "letter", "to": "Karl", "words": 200, "sittings": 1},
            {"id": "c", "title": "On the caste question", "kind": "essay", "to": None, "words": 400, "sittings": 1, "sensitive": True, "why": "caste"}]}}
        entries = [{"k": "writing", "work": "a", "words": 500, "t": "10:00", "m": 600, "i": 0}, {"k": "writing", "work": "b", "words": 200, "t": "16:00", "m": 960, "i": 1}]
        html = self.run_page([["manuscripts", {"$e": [0]}]], D=D, entries=entries)[0]            # only the first sitting is revealed yet
        self.assertIn("<b>On Sense</b> · essay · 1,500 words · 3 sittings", html)
        self.assertNotIn("Dear", html)                                                              # not yet revealed: not listed
        self.assertIn("On the caste question", html)
        self.assertIn('class="veil"', html)
        both = self.run_page([["manuscripts", {"$e": [0, 1]}]], D=D, entries=entries)[0]
        self.assertIn("<b>Dear &lt;Karl&gt;</b> · letter to Karl · 200 words · 1 sitting</p>", both)
        self.assertEqual(self.run_page([["manuscripts", []]], D={"date": "x", "state": {}})[0], "")

    def test_the_page_wires_the_toggle_and_guards_storage(self):
        self.assertIn('<input type="checkbox" id="showSens">', PAGE)
        self.assertIn("Show sensitive entries without asking", PAGE)
        script = PAGE[PAGE.index("<script>"):]
        uses = [m.start() for m in re.finditer(r"localStorage\.", script)]
        self.assertTrue(len(uses) >= 2)
        for at in uses:
            self.assertRegex(script[max(0, at - 60):at], r"try \{", "every localStorage access sits inside try")
        self.assertIn("aria-expanded", script)
        self.assertIn("Sensitive · 19th-century views", script)


def playwright_path():
    """NODE_PATH that has playwright, or None. The browser test is skipped where there is none."""
    if not shutil.which("node") or not os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers") or not Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")).exists():
        return None
    root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() if shutil.which("npm") else ""
    return root if root and (Path(root) / "playwright").exists() else None


BROWSER = """
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(), page = await (await b.newContext({ viewport: { width: 1200, height: 900 } })).newPage();
  const out = {};
  await page.route('**/fonts.g*/**', r => r.abort());
  const open = async () => { await page.goto(process.argv[1] + '/#2026-10-02'); await page.waitForFunction(() => window.__hegel && window.__hegel.day());
    await page.evaluate(() => window.__hegel.setMinute(1380)); await page.waitForTimeout(500); };
  await open();
  const bands = await page.$$('#panel .veil');
  out.bands = bands.length; out.label = (await bands[0].innerText()).split('\\n')[0]; out.before = await bands[0].getAttribute('aria-expanded');
  await bands[0].focus(); await page.keyboard.press('Enter'); await page.waitForTimeout(300);
  out.after = await page.evaluate(() => { const x = document.querySelector('#panel .veil'); return [x.getAttribute('aria-expanded'), document.getElementById(x.getAttribute('aria-controls')).hidden, document.activeElement === x]; });
  await page.check('#showSens'); await page.waitForTimeout(300);
  out.on = [(await page.$$('#panel .veil')).length, await page.evaluate(() => localStorage.getItem('hegel.showSensitive'))];
  await page.reload(); await page.waitForFunction(() => window.__hegel && window.__hegel.day()); await page.evaluate(() => window.__hegel.setMinute(1380)); await page.waitForTimeout(400);
  out.reloaded = [await page.isChecked('#showSens'), (await page.$$('#panel .veil')).length];
  await page.uncheck('#showSens'); await page.waitForTimeout(300);
  out.off = (await page.$$('#panel .veil')).length;
  await page.evaluate(() => window.__hegel.setMinute(450)); await page.waitForTimeout(500);      // the thought in the now-box: the tombs at 07:20
  out.now = await page.$eval('#nowThought', el => [!!el.querySelector('.veil'), el.innerText.includes('Lodhi Gardens')]);
  await page.click('#nowThought .veil'); await page.waitForTimeout(300);
  out.nowOpen = await page.$eval('#nowThought', el => [el.querySelector('.veil').getAttribute('aria-expanded'), el.innerText.includes('Lodhi Gardens')]);
  console.log(JSON.stringify(out)); await b.close();
})();
"""


class BrowserTest(unittest.TestCase):
    """The veil in a real browser: click, Enter, the viewer's toggle remembered across a reload, the thought in the now-box."""

    def test_click_enter_and_toggle(self):
        node_path = playwright_path()
        if not node_path:
            self.skipTest("playwright is not installed")
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(REPO / "docs")))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            env = dict(os.environ, NODE_PATH=node_path, PLAYWRIGHT_BROWSERS_PATH=os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
            got = subprocess.run(["node", "-e", BROWSER, f"http://127.0.0.1:{server.server_port}"], capture_output=True, text=True, env=env, timeout=120)
            if got.returncode != 0:
                self.skipTest("no usable browser: " + got.stderr[-200:])
            out = json.loads(got.stdout)
        finally:
            server.shutdown()
            server.server_close()
        self.assertGreaterEqual(out["bands"], 4)
        self.assertEqual(out["label"], "Sensitive · 19th-century views — show")
        self.assertEqual(out["before"], "false")
        self.assertEqual(out["after"], ["true", False, True])                 # Enter opened it, and the band kept the focus
        self.assertEqual(out["on"], [0, "1"])
        self.assertEqual(out["reloaded"], [True, 0])                          # remembered
        self.assertGreaterEqual(out["off"], 4)
        self.assertEqual(out["now"], [True, False])                          # the now-box thought sits under the veil too
        self.assertEqual(out["nowOpen"], ["true", True])


class CheckTest(unittest.TestCase):
    def run_check(self, docs=None):
        env = dict(os.environ, HEGEL_ENV=os.devnull, **({"HEGEL_REPO": str(docs)} if docs else {}))
        return subprocess.run([sys.executable, "-m", "world", "check"], cwd=REPO, env=env, capture_output=True, text=True)

    def test_the_world_checks_out(self):
        got = self.run_check()
        self.assertEqual((got.returncode, got.stdout.strip()), (0, "ok"), got.stdout)

    def test_a_sensitive_entry_without_a_reason_and_a_writing_without_a_manuscript_are_found(self):
        box = Sandbox()
        try:
            shutil.copytree(REPO / "mind", box.tmp / "mind")
            shutil.copytree(REPO / "world", box.tmp / "world", ignore=shutil.ignore_patterns("__pycache__"))
            day = box.days.load(date(2026, 10, 2))
            day["entries"] += [{"t": "23:00", "k": "diary", "text": "x", "sensitive": True}, {"t": "23:01", "k": "writing", "title": "t", "kind": "essay", "to": None,
                                                                                      "sitting": 1, "text": "x", "work": "nowhere", "words": 1}]
            box.days.save(day)
            got = self.run_check(box.tmp)
            self.assertEqual(got.returncode, 1)
            self.assertIn("the sensitive entry at 23:00 has no reason", got.stdout)
            self.assertIn("the writing at 23:01 is in no manuscript", got.stdout)
        finally:
            box.close()


class Day1Test(unittest.TestCase):
    SEGMENTS = [('00:00', '05:58', 'inside', 'home'), ('05:58', '06:50', 'stand', 'home'), ('06:50', '07:12', 'walk', ('home', 'lodhi')),
                ('07:12', '08:15', 'stroll', 'lodhi'), ('08:15', '08:37', 'walk', ('lodhi', 'home')), ('08:37', '11:00', 'inside', 'home'),
                ('11:00', '11:18', 'walk', ('home', 'gandhi')), ('11:18', '12:05', 'stand', 'gandhi'), ('12:05', '12:38', 'walk', ('gandhi', 'khan')),
                ('12:38', '14:05', 'stroll', 'khan'), ('14:05', '14:30', 'walk', ('khan', 'home')), ('14:30', '16:30', 'inside', 'home'),
                ('16:30', '16:55', 'walk', ('home', 'gym')), ('16:55', '19:05', 'inside', 'gym'), ('19:05', '19:30', 'walk', ('gym', 'home')),
                ('19:30', '22:15', 'inside', 'home'), ('22:15', '24:00', 'inside', 'home')]

    def test_the_timeline_the_purchases_and_the_closing_state_are_as_they_were(self):
        got = [(s["from"], s["to"], s["mode"], s.get("at") or (s.get("a"), s.get("b"))) for s in DAY1["segments"]]
        self.assertEqual(got, self.SEGMENTS)
        bag = [e for e in DAY1["entries"] if e["k"] == "bag"]
        self.assertEqual(sum(e["price"] for e in bag), 4499)
        self.assertEqual(sorted((e["item"], e["price"]) for e in bag), sorted([
            ("Fountain pen and a bound notebook", 640), ("White cotton kurta, ready-made", 1250), ("Advance on the bandhgala", 2000),
            ("Ambedkar, Annihilation of Caste, paperback", 199), ("Hindi primer", 180), ("Assam tea, 250 g", 220), ("Glucose biscuits", 10)]))
        self.assertEqual(DAY1["state"]["imprest"], 10501)
        self.assertEqual(15000 - 4499, 10501)
        self.assertEqual([(e["t"], e["item"]) for e in DAY1["entries"] if e["k"] == "wear" and e.get("sprite")],
                         [("05:58", "Black frock coat, Berlin tailoring"), ("08:40", "Shirtsleeves and waistcoat"), ("13:10", "White cotton kurta")])
        self.assertEqual(DAY1["state"]["wearing"], "kurta")
        self.assertEqual(DAY1["state"]["flags"], {"bandhgala": "ordered"})
        self.assertEqual(DAY1["state"]["people"], ["ramesh", "malhotra", "masterji", "nidhi"])
        self.assertEqual({t["id"]: t["status"] for t in DAY1["state"]["theses"]}, {"india": "unshaken", "state": "unshaken"})

    def test_the_plot_facts_are_all_still_there(self):
        text = " ".join(e.get("text", "") for e in DAY1["entries"])
        for fact in ("Shri G. Hegel", "Ramesh", "₹15,000", "Hegde", "Chanakyapuri", "Gandhi Jayanti", "Malhotra", "bridge", "Masterji", "bandhgala", "Nidhi",
                     "Ambedkar", "Hindi primer", "Depesche"):
            self.assertTrue(fact in text or fact in json.dumps(DAY1, ensure_ascii=False), fact)
        times = {(e["t"], e["k"]) for e in DAY1["entries"]}
        for key in (("06:30", "file"), ("20:10", "work"), ("13:40", "people"), ("13:58", "diary"), ("16:05", "file")):
            self.assertIn(key, times)
        self.assertEqual(len([e for e in DAY1["entries"] if e["k"] == "diary"]), 12)

    def test_the_steering_arc_is_gone(self):
        blob = json.dumps(DAY1, ensure_ascii=False).lower()
        for gone in ("article 17", "the correction", "the thesis is", "under revision", "more hegelian", "irritating", "india has no history"):
            self.assertNotIn(gone, blob, gone)
        self.assertNotRegex(blob, r"\bshaken\b")
        self.assertNotIn("shaken", {t["status"] for t in DAY1["state"]["theses"]})

    def test_the_depesche_is_the_new_one(self):
        d = DAY1["owl"]["depesche"]
        self.assertEqual((d["n"], d["title"]), (0, "Depesche aus Delhi, Nr. 0"))
        self.assertTrue(300 <= len(d["text"].split()) <= 450, len(d["text"].split()))
        self.assertTrue(d["text"].startswith("Readers in Berlin,") and d["text"].rstrip().endswith("G. W. F. Hegel"))
        self.assertIn("₹4,499", d["text"])
        self.assertNotIn("untouchability is abolished", d["text"])

    def test_the_world_carries_on_from_day_one(self):
        box = Sandbox()
        try:
            day = box.run_day(SAT)                                                                    # the next day starts from day one's state
            self.assertEqual(day["opening"]["imprest"], 10501)
            self.assertIn("Ambedkar", Memory(box.days, World()).known_before("2026-10-03"))
            self.assertIn("conquerors", record_text(DAY1))
        finally:
            box.close()


if __name__ == "__main__":
    unittest.main()


class TopicTest(unittest.TestCase):
    """Viewers see the heading a flagged term falls under, never the raw term (the judge's change)."""

    def test_headings_and_marks(self):
        from world.world import World
        w = World()
        self.assertEqual([h for h, _ in w.headings], ["race", "caste", "religion", "empire and colonies", "the ranking of peoples"])
        self.assertEqual(w.topic(w.flag("the Muslim kings")), "religion")
        self.assertEqual(w.topic(w.flag("outside world history")), "the ranking of peoples")
        e = w.mark({"k": "diary", "text": "x"}, "the castes of Delhi")
        self.assertEqual((e["why"], e["topic"]), ("castes", "caste"))

    def test_day_one_carries_topics(self):
        day = json.loads((REPO / "docs/days/2026-10-02.json").read_text(encoding="utf-8"))
        flagged = [e for e in day["entries"] if e.get("sensitive")]
        self.assertTrue(flagged and all(e.get("topic") for e in flagged))
        self.assertEqual(set(day["owl"]["topic"]), set(day["owl"]["sensitive"]))
