"""HEGEL_BORROWED_LOOKUP (pc/BORROWED-LOOKUP.md): with no phone of his own, someone he knows who is with him looks a thing up on theirs, the
next situation says who, the page keeps whose phone it was, and what he read counts as met. Off, none of it happens."""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import There  # noqa: E402  (this also keeps the tests off the Pi's env file)
from test_world import Sandbox, answer, page_about  # noqa: E402

from world import contract, owl  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.memory import encountered_text  # noqa: E402
from world.mind import StubMind  # noqa: E402
from world.world import World, at_dt  # noqa: E402

D = date(2026, 11, 24)
ASK = "Hannah Arendt"
NOTHING = {"note": "You have nothing to look it up on."}


class Asker(StubMind):
    """A mind that looks something up at its first step and reads on after that."""
    source = "stub"

    def __init__(self, query=ASK):
        self.query, self.n, self.sits = query, 0, []

    def decide(self, messages, sit):
        self.sits.append(sit)
        self.n += 1
        extra = {"looks_up": self.query} if self.n == 1 else {}
        return json.dumps(answer(action="read", place="home", minutes=30, thought=f"Quiet reflection number {self.n}, unlike any other.", **extra))


def setup(on=True, lookup=page_about):
    box = Sandbox()
    box.cfg = Config({"HEGEL_PUSH": "0", "HEGEL_STATE": str(box.tmp / "state"), "HEGEL_FEEDS": "0", "HEGEL_BORROWED_LOOKUP": "1" if on else "0"})
    box.cfg.docs = box.tmp / "docs"
    mind = Asker()
    e = Engine(box.cfg, World(borrowed_lookup=on), mind)
    e.lookup = lookup
    prev = box.days.load(date(2026, 10, 2))
    prev["state"]["asleep"] = False
    day = e.new_day(prev, D)
    day["state"].update(place="home", today={"woke": "06:00"})
    return box, e, mind, day


def failing(note):
    return lambda query, cache: {"note": note}


class Borrowed(unittest.TestCase):
    def go(self, who=("nidhi",), on=True, lookup=page_about, own=False):
        """Two steps at home with `who` present: (mind, day, steps)."""
        box, e, mind, day = setup(on, lookup)
        self.addCleanup(box.close)
        if own:
            day["state"]["tech"] = {"phone": True, "sim": True}
        with There(home=list(who)):
            steps = [e.step(day, at_dt(D, 9 * 60 + 30 * i)) for i in range(2)]
        return mind, day, steps

    def test_the_page_comes_back_with_who_looked_it_up(self):
        mind, day, steps = self.go()
        self.assertEqual(steps[0]["read"]["by"], "nidhi")
        self.assertEqual(steps[0]["read"]["title"], ASK)

    def test_the_next_situation_opens_with_her_name_her_pronoun_and_the_text(self):
        mind, day, steps = self.go()
        self.assertIn("Nidhi Rao looks it up on her phone and reads it to you: Hannah Arendt. A page about Hannah Arendt", mind.sits[1]["event"])
        self.assertEqual(steps[1]["opened"], ["read"])

    def test_his_pronoun_for_a_man(self):
        mind, day, steps = self.go(("malhotra",))
        self.assertIn("Mr. R. K. Malhotra looks it up on his phone and reads it to you", mind.sits[1]["event"])

    def test_the_public_entry_has_by_and_the_owl_names_the_phone(self):
        mind, day, steps = self.go()
        entry = next(x for x in day["entries"] if x["k"] == "read")
        self.assertEqual(entry["by"], "Nidhi Rao")
        self.assertIn("read on Nidhi Rao's phone, from Wikipedia, “Hannah Arendt”", owl.record(dict(day, n=1, title="T")))

    def test_a_name_from_the_page_passes_the_1831_gate(self):
        w = World(borrowed_lookup=True)
        mind, day, steps = self.go(lookup=lambda q, c: dict(page_about(q, c), text="Hannah Arendt wrote on Google, and Zoom followed."))
        self.assertTrue(w.unmet("Google", ""), "the gate would stop the name without the page")
        self.assertEqual(w.unmet("Google and Zoom", encountered_text(day)), [])

    def test_the_line_only_while_such_a_person_is_present_and_he_has_no_phone(self):
        mind, day, steps = self.go()
        self.assertIn("Nidhi Rao has her phone: you may ask her to look something up (looks_up).", mind.sits[0]["on_mind"])
        self.assertIn("looks_up", contract.decision_schema(mind.sits[0])["properties"])        # the schema offers it at every moment already
        self.assertIs(contract.decision_schema(mind.sits[0]), contract.SCHEMA)
        for who in ([], ["sunil"], ["saxena"], ["bookseller"], ["officer"]):
            mind, day, steps = self.go(who)
            self.assertFalse([x for x in mind.sits[0]["on_mind"] if "phone" in x], who)
        mind, day, steps = self.go(own=True)
        self.assertEqual([x for x in mind.sits[0]["on_mind"] if "phone" in x],
                         ["You have a phone with a SIM: you may look something up (looks_up)."])

    def test_the_first_listed_is_the_one(self):
        mind, day, steps = self.go(("sunil", "ananya", "nidhi"))
        self.assertIn("Ananya has her phone: you may ask her to look something up (looks_up).", mind.sits[0]["on_mind"])
        self.assertEqual(steps[0]["read"]["by"], "ananya")

    def test_nobody_with_a_phone_gives_the_old_note(self):
        for who in ([], ["sunil"], ["saxena"], ["bookseller"]):
            mind, day, steps = self.go(who)
            self.assertEqual(steps[0]["read"], NOTHING, who)
            self.assertEqual(mind.sits[1]["event"], NOTHING["note"], who)
            self.assertFalse([x for x in day["entries"] if x["k"] == "read"])

    def test_his_own_phone_is_used_and_the_words_are_the_old_ones(self):
        mind, day, steps = self.go(("nidhi",), own=True)
        self.assertNotIn("by", steps[0]["read"])
        self.assertIn("On your phone you read: Hannah Arendt.", mind.sits[1]["event"])
        self.assertNotIn("by", next(x for x in day["entries"] if x["k"] == "read"))

    def test_a_failed_look_up_is_worded_with_the_person(self):
        for note in ("The page will not load.", "Nothing comes up for that."):
            mind, day, steps = self.go(lookup=failing(note))
            self.assertEqual(mind.sits[1]["event"], f"Nidhi Rao tries her phone: {note}")

    def test_off_none_of_it_happens(self):
        mind, day, steps = self.go(on=False)
        self.assertFalse([x for x in mind.sits[0]["on_mind"] if "phone" in x])
        self.assertEqual(steps[0]["read"], NOTHING)
        self.assertEqual(mind.sits[1]["event"], NOTHING["note"])

    def test_nobody_speaks_for_the_look_up(self):
        mind, day, steps = self.go()
        self.assertNotIn("voice", steps[0])
        self.assertFalse([x for x in day["entries"] if x["k"] == "said"])


if __name__ == "__main__":
    unittest.main()
