"""Tests for memory from the day files, the knowledge boundary and the guard on his voice."""
import json
import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import DAY1, REPO, Sandbox, answer, state  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import contract, owl  # noqa: E402
from world.memory import GIST, MAX_CHARS, MAX_LINES, MAX_TOTAL, Memory  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World, at_dt, repeats  # noqa: E402

TODAY = date(2026, 10, 10)


def make_day(n, d, entries=(), steps=(), diary=None):
    return {"format": 1, "n": n, "date": d.isoformat(), "title": d.isoformat(), "holiday": None, "segments": [],
            "entries": list(entries), "steps": list(steps), "owl": {"diary": diary} if diary else None, "complete": True, "state": {}}


def said(t, to, text):
    return {"t": t, "k": "said", "to": to, "text": text}


def thought(t, text):
    return {"t": t, "k": "diary", "text": text}


def step(t, place, text):
    return {"t": t, "end": t, "decision": {"thought": text, "action": "stay", "place": place, "minutes": 30}}


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.w = World()
        d = lambda n: date(2026, 10, 2 + n)         # day n+1
        for n, entries, steps, diary in [
            (1, [said("11:45", "Nidhi Rao", "Does the state come before the family?")], [], None),
            (3, [thought("14:10", "Nidhi asked about Article 17 again, and I had no answer ready.")], [step("10:00", "lodhi", "Older thought at Lodhi.")], None),
            (4, [said("15:00", "Ramesh and Nidhi Rao", "Two cups, please.")], [], "The first diary of the four, about tombs and tailors and a long day."),
            (5, [thought("09:10", "Mr. Malhotra walks like a man late for a meeting that ended in 1998.")], [], "The second diary, about bridge and a very patient club."),
            (6, [said("13:20", "Nidhi Rao", "Show me where Marx would have disagreed."), {"t": "12:00", "k": "world", "text": "Rain."}],
             [step("17:30", "lodhi", "The newest thought at Lodhi, with the gate and the chai."), step("18:30", "home", "Home again.")],
             "The third diary, about the monsoon that would not leave and a tailor who would not hurry."),
            (7, [], [], "The fourth diary, the newest night, about a file that moves like a glacier in a hurry."),
        ]:
            self.box.days.save(make_day(n + 1, d(n), entries, steps, diary))
        self.mem = Memory(self.box.days, self.w)
        self.today = make_day(9, TODAY)

    def tearDown(self):
        self.box.close()

    def recall(self, present, place="lodhi", day=None):
        return self.mem.recall({"place": place}, {"present": present}, day or self.today)

    def test_three_most_recent_moments_with_each_person(self):
        lines = self.recall(["nidhi"], place="khan")
        mine = [x for x in lines if "Nidhi" in x]
        self.assertEqual(len(mine), 3)                                     # of four entries, plus day 1's card: the newest three
        self.assertEqual(mine[-1], "Day 7 (Thu 8 Oct), 13:20, to Nidhi Rao: “Show me where Marx would have disagreed.”")
        self.assertIn("Day 5 (Tue 6 Oct), 15:00, to Ramesh and Nidhi Rao: “Two cups, please.”", mine)
        self.assertIn("Day 4 (Mon 5 Oct), 14:10, you thought: “Nidhi asked about Article 17 again, and I had no answer ready.”", mine)
        self.assertFalse(any("Day 2" in x or "Day 1" in x for x in mine))

    def test_people_are_found_by_surname_and_background_people_are_not(self):
        self.assertTrue(any("Malhotra" in x for x in self.recall(["malhotra"], place="khan")))
        self.assertEqual([x for x in self.recall(["bookseller", "clerk"], place="khan") if "bookseller" in x], [])

    def test_the_last_thought_in_this_place_on_an_earlier_day(self):
        lodhi = [x for x in self.recall([], place="lodhi") if "you thought" in x]
        self.assertEqual(lodhi, ["Day 7 (Thu 8 Oct), 17:30, in Lodhi Gardens, you thought: “The newest thought at Lodhi, with the gate and the chai.”"])
        self.assertEqual([x for x in self.recall([], place="khan") if "you thought" in x], [])

    def test_the_owl_of_the_last_three_nights(self):
        nights = [x for x in self.recall([], place="khan") if "owl" in x]
        self.assertEqual(len(nights), 3)                                    # four diaries on file, the oldest is left out
        self.assertTrue(nights[0].startswith("Day 6 (Wed 7 Oct), as the owl wrote it up: The second diary"))
        self.assertTrue(nights[-1].startswith("Day 8 (Fri 9 Oct), as the owl wrote it up: The fourth diary"))
        self.assertNotIn("first diary", " ".join(nights))
        self.assertIn(owl.gist("The second diary, about bridge and a very patient club.", GIST), nights[0])

    def test_at_most_eight_lines_each_short_and_the_same_every_time(self):
        long = "A long thought about everything that Nidhi and Malhotra and Ramesh and Saxena have said to me. " * 5
        self.box.days.save(make_day(8, date(2026, 10, 9), [thought("10:00", long), thought("10:01", long + "x"), said("10:02", "Nidhi Rao", long)],
                                    [step("10:00", "khan", long)], "A diary. " * 100))
        lines = self.recall(["nidhi", "malhotra", "saxena"], place="khan")
        self.assertLessEqual(len(lines), MAX_LINES)
        self.assertTrue(all(len(x) <= MAX_CHARS for x in lines), [len(x) for x in lines])
        self.assertTrue(any(x.endswith("…") or x.endswith("…”") for x in lines))
        self.assertEqual(lines, self.recall(["nidhi", "malhotra", "saxena"], place="khan"))

    def test_today_beyond_the_earlier_today_window(self):
        steps = [{"t": f"{h:02d}:00", "decision": {}} for h in range(8, 15)]       # seven steps: the window is the last six, from 09:00
        today = make_day(9, TODAY, [said("08:05", "Nidhi Rao", "Good morning."), said("09:30", "Nidhi Rao", "Inside the window.")], steps)
        mine = [x for x in self.recall(["nidhi"], day=today) if x.startswith("Today")]
        self.assertEqual(mine, ["Today, 08:05, to Nidhi Rao: “Good morning.”"])

    def test_past_days_are_read_once_per_engine_and_again_when_the_owl_writes(self):
        loads = []
        real = self.box.days.load
        self.box.days.load = lambda d: (loads.append(d), real(d))[1]
        self.recall(["nidhi"])
        first = len(loads)
        self.assertGreater(first, 0)
        for _ in range(5):
            self.recall(["nidhi"], place="khan")
            self.mem.recent_thoughts(self.today)
        self.assertEqual(len(loads), first)
        late = real(date(2026, 10, 9))
        late["owl"]["diary"] = "Rewritten in the night, and long enough to see."
        self.box.days.save(late)
        self.assertTrue(any("Rewritten in the night" in x for x in self.recall([], place="khan")))

    def test_render_shows_the_section_only_when_there_is_something_to_remember(self):
        s = json.loads((REPO / "mind/situations.json").read_text(encoding="utf-8"))["situations"][0]
        self.assertNotIn("You remember", contract.render(s))
        text = contract.render(dict(s, remember=["Day 3 (Sat 3 Oct), 11:45, to Nidhi Rao: “Hello.”"], earlier=["10:00 stay (home): x"]))
        self.assertIn("\nYou remember:\n- Day 3 (Sat 3 Oct), 11:45, to Nidhi Rao: “Hello.”\n", text)
        self.assertLess(text.index("You remember"), text.index("Earlier today"))
        self.assertEqual(contract.render(s), contract.render(dict(s, remember=[])))

    def test_the_engine_adds_it_and_the_owl_replaces_yesterdays_gist(self):
        seen = []

        class Watcher(StubMind):
            def decide(self, messages, sit):
                seen.append(messages[1]["content"])
                return super().decide(messages, sit)

        box = Sandbox()
        try:
            e = box.engine(Watcher())
            for i in range(3):
                d = date(2026, 10, 3 + i)
                box.run_day(d, e)
                e.run_owl(box.days.load(d), at_dt(d, 1440 + 90))
            talking = [m for m in seen if "Ramesh, the caretaker" in m.split("Present:")[1].split("\n")[0]]
            self.assertTrue(talking)
            self.assertTrue(all("You remember:" in m and "Ramesh" in m.split("You remember:")[1] for m in talking))
            self.assertTrue(any("as the owl wrote it up" in m for m in seen))
            self.assertFalse(any("Yesterday, as the owl wrote it up" in m for m in seen))
            for d in ("2026-10-04", "2026-10-05"):
                self.assertNotIn("yesterday", box.days.load(d)["state"])
        finally:
            box.close()

    def test_old_files_with_a_yesterday_gist_are_tolerated(self):
        st = state()
        st["yesterday"] = "An old gist."
        day = {"segments": [], "entries": [], "steps": []}
        sit, _ = self.w.situation(at_dt(date(2026, 10, 3), 600), st, day)
        self.assertNotIn("An old gist", contract.render(sit))


class KnowledgeTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.w = World()
        self.mem = Memory(self.box.days, self.w)
        self.day = {"date": "2026-10-03", "n": 2, "entries": [], "steps": [], "state": state()}
        self.t = at_dt(date(2026, 10, 3), 600)

    def tearDown(self):
        self.box.close()

    def check(self, **kw):
        sit, ctx = self.w.situation(self.t, state(), self.day)
        ctx["known_text"] = self.mem.known_text(self.day, sit)
        return self.w.check(answer(**kw), sit, ctx, state())[0]

    def test_the_data_file(self):
        lines = [x.strip() for x in (REPO / "world/data/after_1831.txt").read_text(encoding="utf-8").splitlines()]
        terms = [x for x in lines if x and not x.startswith("#")]
        self.assertTrue(40 <= len(terms) <= 60, len(terms))
        self.assertEqual(len(terms), len(set(x.lower() for x in terms)))
        for known_before in ("schopenhauer", "goethe", "napoleon", "schelling", "beethoven", "newton"):
            self.assertNotIn(known_before, [x.lower() for x in terms])
        self.assertIsNone(self.w.after.search("The marketplace of Darwinian marks"))       # whole words only

    def test_marx_is_refused_until_he_is_met(self):
        want = "you have not met 'Marx' in Delhi; in 1831 you could not know it"
        self.assertEqual(self.check(thought="Marx would have called this tea a commodity, I think."), [want])
        self.assertEqual(self.check(says="I wonder what Marx would say."), [want])
        self.assertEqual(self.check(revision="Marx's reading of me is the first dent in the thesis."), [want])
        self.assertEqual(self.check(thought="marx would have called this tea a commodity.")[0], want.replace("Marx", "marx"))
        self.day["entries"].append({"t": "09:00", "k": "world", "text": "Morning papers: “Marx quoted in Lok Sabha debate”"})
        self.assertEqual(self.check(thought="Marx would have called this tea a commodity, I think."), [])

    def test_what_day_one_already_met_passes(self):
        self.assertEqual(self.check(thought="Ambedkar and Gandhi walked different roads to the same constitution, I think."), [])

    def test_the_situation_counts_and_so_do_plurals_and_phrases(self):
        sit, ctx = self.w.situation(self.t, state(), self.day)
        sit["event"] += " A man at the gate sells a television on a cart."
        ctx["known_text"] = self.mem.known_text(self.day, sit)
        self.assertEqual(self.w.check(answer(thought="The television is a window with no house behind it."), sit, ctx, state())[0], [])
        self.assertTrue(self.check(thought="The televisions in every shop cannot all be right."))      # not yet met
        self.assertEqual(len(self.check(thought="After the World Wars and the Holocaust, nothing is as before.")), 2)

    def test_the_mind_is_told_and_decides_again(self):
        class Marxist(StubMind):
            def decide(self, messages, sit):
                if any("refuses" in x["content"] for x in messages):
                    return super().decide(messages, sit)
                return json.dumps(answer(thought="Marx would have had a view of this particular cup of tea.", action="read", place="home"))

        e = self.box.engine(Marxist())
        self.box.run_day(date(2026, 10, 3), e)
        first = next(s for s in self.box.days.load(date(2026, 10, 3))["steps"] if "decision" in s)
        self.assertEqual(first["mind"]["attempts"], 2)
        self.assertEqual(first["mind"]["refused"], [["you have not met 'Marx' in Delhi; in 1831 you could not know it"]])
        self.assertNotIn("Marx", json.dumps(self.box.days.load(date(2026, 10, 3))["entries"]))

    def test_the_prompts_say_it(self):
        soul = (REPO / "mind/soul.md").read_text(encoding="utf-8")
        section = soul.split("## What you know")[1].split("\n## ")[0]
        self.assertIn("November 1831", section)
        self.assertIn("since you woke in Delhi", section)
        self.assertIn("November 1831", (REPO / "mind/owl.md").read_text(encoding="utf-8"))


class VoiceTest(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.w = World()
        self.t = at_dt(date(2026, 10, 3), 600)

    def tearDown(self):
        self.box.close()

    def test_the_anchors_are_day_ones_own_words(self):
        section = (REPO / "mind/soul.md").read_text(encoding="utf-8").split("## How you sound")[1].split("\n## ")[0]
        quotes = re.findall(r"^- “(.+)”$", section, re.M)
        self.assertIn(len(quotes), (3, 4))
        said = [e["text"] for e in DAY1["entries"] if e["k"] == "diary"]
        for q in quotes:
            self.assertIn(q, said)
            self.assertLess(len(q), 260)
        self.assertIn("don't repeat their sentences", section)

    def test_what_counts_as_a_repeat(self):
        a = "The sun went down over the club lawn at six. The light here does not dawdle."
        self.assertTrue(repeats("The sun went down over the club lawn at six. The light here does not hang about.", a))
        self.assertTrue(repeats("The sun went down over the club, and then I went home to write about it at length.", a))   # same first six words
        self.assertFalse(repeats("Dusk at the Gymkhana: the lawn goes grey and the waiters light their lamps.", a))
        self.assertTrue(repeats("Lamp out now.", "lamp out now"))                        # short ones too

    def test_the_world_refuses_a_near_duplicate_and_accepts_a_fresh_thought(self):
        st = state()
        old = "The sun went down over the club lawn at six. The light here does not dawdle."
        ctx = {"t": self.t, "present": [], "beat": None, "public": [], "recent": [("17:20", "Something else entirely, about bridge and bidding."), ("18:10", old)]}
        sit = {"open_now": self.w.open_places(self.t, st)}
        errors, _, _ = self.w.check(answer(thought="The sun went down over the club lawn at six. The light here does not hang about."), sit, ctx, st)
        self.assertEqual(errors, ["this repeats what you thought at 18:10; think something new"])
        errors, _, _ = self.w.check(answer(thought="Dusk at the Gymkhana: the lawn goes grey and the waiters light their lamps."), sit, ctx, st)
        self.assertEqual(errors, [])

    def test_the_last_twelve_thoughts_today_and_the_end_of_yesterday(self):
        mem = Memory(self.box.days, self.w)
        day = {"date": "2026-10-03", "n": 2, "steps": [], "entries": [thought(f"0{i}:00", f"Thought number {i} of today.") for i in range(5, 9)]}
        got = mem.recent_thoughts(day)
        self.assertEqual(len(got), 12)
        self.assertEqual(got[-4:], [(f"0{i}:00", f"Thought number {i} of today.") for i in range(5, 9)])       # today's last
        self.assertEqual([t for t, _ in got[:8]], [e["t"] for e in DAY1["entries"] if e["k"] == "diary"][-8:])  # yesterday's end
        day["entries"] += [thought(f"{h}:00", f"More {h}.") for h in range(10, 20)]
        self.assertEqual([t for t, _ in mem.recent_thoughts(day)][0], "07:00")

    def test_a_mind_that_repeats_itself_is_told_so(self):
        class Echo(StubMind):
            def decide(self, messages, sit):
                if any("refuses" in x["content"] for x in messages):
                    return super().decide(messages, sit)
                return json.dumps(answer(thought="I watch the light on the verandah wall and wonder what it is turning into.",
                                         action="rest", place="home", minutes=30))

        e = self.box.engine(Echo())
        self.box.run_day(date(2026, 10, 3), e)
        steps = [s for s in self.box.days.load(date(2026, 10, 3))["steps"] if "decision" in s]
        self.assertEqual(steps[0]["mind"]["attempts"], 1)
        again = [s for s in steps if s["mind"].get("refused")]
        self.assertTrue(again)
        self.assertEqual(again[0]["mind"]["refused"][0], [f"this repeats what you thought at {steps[0]['t']}; think something new"])

    def test_the_stand_in_never_trips_it(self):
        day = self.box.run_day(date(2026, 10, 3))
        steps = [s for s in day["steps"] if "decision" in s]
        self.assertEqual(sum(len(s["mind"].get("refused", [])) for s in steps), 0)
        thoughts = [s["decision"]["thought"] for s in steps]
        self.assertEqual(len(thoughts), len(set(thoughts)))
        for i, a in enumerate(thoughts):
            self.assertFalse(any(repeats(a, b) for b in thoughts[max(0, i - 12):i]), a)


if __name__ == "__main__":
    unittest.main()


class JudgeTest(unittest.TestCase):
    """What the judge added on review: the owl answers to the same boundary, last night survives a crowd,
    and a PC that does not wake for the plan is not woken twice."""

    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def test_the_owl_writes_again_without_what_the_page_will_not_publish(self):
        class Leaky(StubMind):
            def __init__(self, leaks):
                self.leaks, self.calls = leaks, 0
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                self.calls += 1
                diary = "Today I thought of Marx in the bookshop, and of the tailor's silence, and of the long road home. " * 2
                clean = "Today I thought of the tailor's silence, and of the bookshop, and of the long road home in the heat. " * 2
                text = diary if self.calls <= self.leaks else clean
                return json.dumps({"diary": text, "revision_log": "Nothing moved.", "theses": []})
        e = self.box.engine()
        day = self.box.run_day(date(2026, 10, 4), e)
        e.owl_mind = Leaky(1)
        e.run_owl(day, at_dt(date(2026, 10, 5), 90))
        self.assertNotIn("Marx", self.box.days.load(date(2026, 10, 4))["owl"]["diary"])
        self.assertEqual(e.owl_mind.calls, 2)
        e.owl_mind = Leaky(2)
        day = self.box.days.load(date(2026, 10, 4))
        day["owl"] = None
        with self.assertRaises(owl.OwlError):
            e.run_owl(day, at_dt(date(2026, 10, 5), 90))

    def test_last_night_keeps_its_line_in_a_crowd(self):
        w = World()
        d = date(2026, 10, 9)
        moments = [said(f"1{i}:00", "Ramesh and Nidhi Rao and Mr. R. K. Malhotra and Masterji", f"Remark number {i} to all four.") for i in range(6)]
        self.box.days.save(make_day(8, d, moments, [], "Last night's diary, about four people and one table."))
        mem = Memory(self.box.days, w)
        lines = mem.recall({"place": "home"}, {"present": ["ramesh", "nidhi", "malhotra", "masterji"]}, make_day(9, d.replace(day=10)))
        self.assertLessEqual(len(lines), MAX_LINES)
        self.assertLessEqual(sum(len(x) + 3 for x in lines), MAX_TOTAL)
        self.assertTrue(any("as the owl wrote it up" in x for x in lines))
        for name in ("Ramesh", "Nidhi", "Malhotra", "Masterji"):              # one moment with each person stays
            self.assertTrue(any(name in x for x in lines), name)

    def test_a_pc_that_does_not_wake_for_the_plan_is_not_woken_again(self):
        from world.mind import HTTPMind
        mind = HTTPMind("http://127.0.0.1:9")
        tries = []
        mind.health = lambda timeout=3: tries.append(1) or False
        e = self.box.engine(mind)
        prev = self.box.days.load(date(2026, 10, 2))
        day = e.new_day(prev, date(2026, 10, 3))
        self.box.days.save(day)
        e.step(day, at_dt(date(2026, 10, 3), 0) + timedelta(minutes=e.world.wake_time(date(2026, 10, 3))))
        self.assertEqual(day["steps"][-1]["mind"]["source"], "away")
        self.assertEqual(len(tries), 1)
