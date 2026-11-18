"""HEGEL_VOICE_REPAIRS: four repairs to the people's voices, behind one switch that is off by default. Each situation is rebuilt from a
recorded moment of Days 47 to 49 (2026-11-17 to 2026-11-19, on the shadow branch). Off gives what the voices did; on gives the repair.
No call to a model: routing and prompts are code."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import voices
from world.config import Config
from world.engine import Engine
from world.world import World

W = World()
CAST = W.cast
SIT = dict(day="Tuesday 17 November", time="09:47", place="home", outfit="white cotton kurta", event="He asks.", for_sale=[], weather="19 °C")
SOLD = "Nothing is sold or served here. Do not offer, arrange or describe food, drink or goods."


def render(cid, sit, says="Hello.", **kw):
    return voices.render(CAST[cid], dict(SIT, **sit), "somewhere", says, [], first_meeting=False, purchases=[], **kw)


def reply(on, says, present, ctx=None, entries=(), segments=(), place="khan", vf=False):
    """Who answers, by the engine's own reply(), with the voice call stubbed out."""
    e = Engine.__new__(Engine)
    e.world, e.cfg, got = W, SimpleNamespace(voice_facts=vf, voice_repairs=on), []
    e.voice = lambda cid, day, sit, says, purchases=None: got.append(cid)
    e.reply({"entries": list(entries), "segments": list(segments)}, dict(place=place, time="10:00"), dict(present=present, **(ctx or {})), says)
    return got[0]


class Switch(unittest.TestCase):
    def test_off_by_default_and_read_from_config(self):
        self.assertFalse(Config({}).voice_repairs)
        self.assertTrue(Config({"HEGEL_VOICE_REPAIRS": "1"}).voice_repairs)
        self.assertFalse(Config({"HEGEL_VOICE_REPAIRS": "0"}).voice_repairs)


class A_OwnPresenceLine(unittest.TestCase):
    """Day 47, 09:47: Shri Hegde's greeting was written from an event that ended 'Shri G. Hegde is here.'; also 2026-11-16, 09:44."""
    EVENT = "Nothing is cooked at home: Ramesh has not been paid his wage for cooking. Shri G. Hegde is here."

    def test_day47_greeting(self):
        off, on = render("hegde", dict(event=self.EVENT), None), render("hegde", dict(event=self.EVENT), None, repairs=True)
        self.assertIn("wage for cooking. Shri G. Hegde is here.\n", off)
        self.assertNotIn("is here", on)
        self.assertIn("(told from his side, so 'you' there means him): Nothing is cooked at home: Ramesh has not been paid his wage for cooking.\n", on)

    def test_nov16_reply(self):
        ev = ("Ramesh says: “Chau ka paisa?” He picks up the papers from the verandah and turns to leave. "
              "Nothing is cooked at home: Ramesh has not been paid his wage for cooking. Shri G. Hegde is here.")
        self.assertIn("Shri G. Hegde is here.", render("hegde", dict(event=ev), "Shri Hegde, the file is gone."))
        on = render("hegde", dict(event=ev), "Shri Hegde, the file is gone.", repairs=True)
        self.assertNotIn("Hegde is here", on)
        self.assertIn("Ramesh says: “Chau ka paisa?”", on)

    def test_others_stay_and_unmet_form(self):
        ev = "You arrive at Khan Market. Masterji is here. Sunil is here. The bookseller is here."
        on = render("sunil", dict(event=ev), repairs=True)
        self.assertIn("Khan Market. Masterji is here. The bookseller is here.\n", on)
        self.assertNotIn("Sunil is here", on)
        ev = "Nidhi Rao, doctoral student in philosophy is here; you have not met. Mrs. Kapoor, a retired schoolteacher is here; you have not met."
        on = render("nidhi", dict(event=ev), repairs=True)
        self.assertNotIn("doctoral student in philosophy is here", on)
        self.assertIn("Mrs. Kapoor, a retired schoolteacher is here; you have not met.", on)

    def test_off_is_todays(self):
        for cid in ("hegde", "sunil", "ramesh"):
            self.assertEqual(render(cid, dict(event=self.EVENT)), render(cid, dict(event=self.EVENT), repairs=False))


class B_NothingSold(unittest.TestCase):
    """Day 47, IIC, 10:39 ('I can arrange a complimentary meal at the cafeteria'), 12:04, 13:19 ('they have the tiffins there'),
    13:49 ('you need to pay at the counter'); Day 48, 12:21 ('The cafeteria is right there')."""
    def test_iic(self):
        off, on = render("guard", dict(place="iic")), render("guard", dict(place="iic"), repairs=True)
        self.assertIn("Listed goods and prices here: none listed. Do not replace", off)
        self.assertIn("Listed goods and prices here: " + SOLD + " Do not replace these prices with invented ones.\n", on)
        self.assertNotIn("none listed", on)

    def test_home_and_listed_goods_unchanged(self):
        for sit in (dict(place="home"), dict(place="khan", for_sale=["Samosa ₹30", "Chai, a cup ₹20"]), dict(place="khan", for_sale=["books"])):
            self.assertEqual(render("sunil", sit, repairs=True), render("sunil", sit))
        self.assertIn("none listed", render("ramesh", dict(place="home"), repairs=True))

    def test_no_for_sale_key_unchanged(self):
        sit = {k: v for k, v in SIT.items() if k != "for_sale"}
        self.assertEqual(voices.render(CAST["guard"], dict(sit, place="iic"), "IIC", "x", [], repairs=True), voices.render(CAST["guard"], dict(sit, place="iic"), "IIC", "x", []))


class C_WhoAnswers(unittest.TestCase):
    def test_day49_hegde_named_after_ramesh(self):
        """Day 49, 19:24: 'Ramesh, thank you. Shri Hegde, before you go to sleep, I must speak with you regarding the vouchers...'
        Ramesh answered that Hegel took him for the officer."""
        says = "Ramesh, thank you. Shri Hegde, before you go to sleep, I must speak with you regarding the vouchers. The Directorate has queried twenty-seven rupees from my imprest."
        self.assertEqual(reply(False, says, ["ramesh", "hegde"]), "ramesh")
        self.assertEqual(reply(True, says, ["ramesh", "hegde"]), "hegde")

    def test_longest_stretch_keeps_malhotra(self):
        c = CAST
        self.assertEqual(voices.pick(c, "Malhotra, and then Nidhi", ["nidhi", "malhotra"], repairs={}), "malhotra")
        self.assertEqual(voices.pick(c, "Mr. Malhotra, your bid", ["nidhi", "malhotra"], repairs={}), "malhotra")
        self.assertEqual(voices.pick(c, "Nidhi, a word?", ["ramesh", "nidhi"], repairs={}), "nidhi")
        self.assertEqual(voices.pick(c, "Excuse me, the bookseller?", ["bookseller", "nidhi"], repairs={}), "bookseller")
        self.assertEqual(voices.pick(c, "Ramesh, Hegde", ["ramesh", "hegde"], repairs={}), "ramesh")          # a tie: the first named

    def test_day47_programme_officer(self):
        """Day 47, 10:39: the beat iic_talk fired ('The programme officer of the Centre comes over...'); the guard answered."""
        says = "I accept your invitation with pleasure. I shall come at half past six."
        ctx = dict(beat=dict(id="iic_talk", needs=["officer"]), beat_entries=[])
        self.assertEqual(reply(False, says, ["guard", "officer"], ctx, place="iic"), "guard")
        self.assertEqual(reply(True, says, ["guard", "officer"], ctx, place="iic"), "officer")

    def test_beat_not_fired_gives_no_need(self):
        ctx = dict(beat=dict(id="iic_talk", needs=["officer"]))                 # chosen, not fired (no beat_entries)
        self.assertEqual(reply(True, "Thank you.", ["guard", "officer"], ctx, place="iic"), "guard")

    def test_day47_samosa_masterji_answered(self):
        """Day 47, 16:44, Khan Market: 'So be it. The filling is the content, the pastry the form. I shall consume the unity.' with a samosa
        bought from Sunil's stall; Masterji answered."""
        says = "So be it. The filling is the content, the pastry the form. I shall consume the unity."
        ctx = dict(purchases=[dict(item="Samosa", price=30)])
        p = ["masterji", "sunil", "bookseller"]
        self.assertEqual(reply(False, says, p, ctx), "masterji")
        self.assertEqual(reply(True, says, p, ctx), "sunil")

    def test_day48_biscuits_and_last_spoken(self):
        """Day 48, 17:36: 'Garam pani, please. And keep the last samosa for me; I will finish it.' (Masterji answered, Sunil had been answering)."""
        says = "Garam pani, please. And keep the last samosa for me; I will finish it."
        p = ["masterji", "sunil", "bookseller"]
        ent = [dict(k="said", by="Sunil", to="Hegel", t="17:21", text="x")]
        seg = [{"from": "09:00", "to": "18:00", "at": "khan"}]
        self.assertEqual(reply(False, says, p, entries=ent, segments=seg), "masterji")
        self.assertEqual(reply(True, says, p, entries=ent, segments=seg), "sunil")                      # last spoken, with HEGEL_VOICE_FACTS off
        self.assertEqual(reply(True, "Thank you.", p, {"purchases": []}, entries=ent, segments=seg), "sunil")
        self.assertEqual(reply(True, "Thank you.", p, entries=ent, segments=[{"from": "09:00", "to": "18:00", "at": "lodhi"}]), "masterji")

    def test_greeting_speaker(self):
        """Day 47, 09:47: Shri Hegde spoke first; then words that name no one are his to answer."""
        ctx = dict(opened=["greeting:hegde"], greeting=dict(by="Shri G. Hegde", says="Hegde ji, you're still here?", does=None))
        self.assertEqual(reply(False, "Good morning.", ["ramesh", "hegde"], ctx, place="home"), "ramesh")
        self.assertEqual(reply(True, "Good morning.", ["ramesh", "hegde"], ctx, place="home"), "hegde")
        self.assertEqual(voices.pick(CAST, "Good morning.", ["ramesh", "hegde"], repairs=dict(greeting="hegde")), "hegde")

    def test_order(self):
        p = ["masterji", "sunil", "nidhi", "bookseller"]
        full = dict(greeting="masterji", needs=["nidhi"])
        ent = [dict(k="said", by="The bookseller", to="Hegel", t="10:00", text="x")]
        seg = [{"from": "09:00", "to": "11:00", "at": "khan"}]
        kw = dict(purchases=[dict(item="Samosa", price=20)], entries=ent, segments=seg, place="khan", repairs=full)
        self.assertEqual(voices.pick(CAST, "Sunil, hello", p, **kw), "sunil")              # 1 named
        self.assertEqual(voices.pick(CAST, "Hello", p, **kw), "masterji")                  # 2 greeting
        kw["repairs"] = dict(needs=["nidhi"])
        self.assertEqual(voices.pick(CAST, "Hello", p, **kw), "nidhi")                     # 3 beat
        kw["repairs"] = {}
        self.assertEqual(voices.pick(CAST, "Hello", p, **kw), "sunil")                     # 4 purchase
        kw["purchases"] = []
        self.assertEqual(voices.pick(CAST, "Hello", p, **kw), "bookseller")                # 5 last spoken
        kw["entries"] = []
        self.assertEqual(voices.pick(CAST, "Hello", p, **kw), "masterji")                  # 6 fallback

    def test_trade_words_stay_with_voice_facts(self):
        p = ["masterji", "bookseller", "sunil"]
        self.assertEqual(voices.pick(CAST, "One samosa, please.", p, facts=True, repairs={}), "sunil")
        self.assertEqual(voices.pick(CAST, "One samosa, please.", p, repairs={}), "masterji")

    def test_explicit_recipient_still_first(self):
        self.assertEqual(voices.pick(CAST, "Ramesh", ["ramesh", "hegde"], recipient="hegde", repairs={}), "hegde")
        with self.assertRaises(ValueError):
            voices.pick(CAST, "x", ["ramesh"], recipient="hegde", repairs={})

    def test_off_routing_is_todays(self):
        """With the switch off the routing is the same whatever the step holds."""
        ctx = dict(opened=["greeting:hegde"], beat=dict(needs=["officer"]), beat_entries=[], purchases=[dict(item="Samosa", price=30)])
        for says, p in (("Hello.", ["ramesh", "hegde"]), ("Hello.", ["guard", "officer"]), ("Samosa.", ["masterji", "sunil"]),
                        ("Ramesh, thank you. Shri Hegde, a word.", ["ramesh", "hegde"])):
            for vf in (False, True):
                with self.subTest(says=says, vf=vf):
                    self.assertEqual(reply(False, says, p, ctx, vf=vf),
                                     voices.pick(CAST, says, p, **(dict(facts=True, purchases=ctx["purchases"], entries=[], segments=[], place="khan") if vf else {})))


class D_DoesLines(unittest.TestCase):
    """The `does` lines of Days 47 to 49, fed to the cleaner."""
    def does(self, cid, line, on):
        out = voices.clean(CAST[cid], {"says": "Well.", "does": line}, **({"repairs": True} if on else {}))
        return out["does"]

    def test_first_person(self):                       # Day 47, 13:04, the guard
        line = "I gesture towards the front desk and the cafeteria entrance."
        self.assertEqual(self.does("guard", line, False), line)
        self.assertIsNone(self.does("guard", line, True))
        for mine in ("Keeps my hand on the register.", "Points at me.", "Pats myself down."):
            self.assertIsNone(self.does("guard", mine, True))
        self.assertEqual(self.does("guard", "Writes it in the main register.", True), "Writes it in the main register.")

    def test_names_himself(self):                      # Day 49, 20:39, Shri Hegde
        line = "He pats Hegde's shoulder firmly and turns back toward the dining table."
        self.assertEqual(self.does("hegde", line, False), line)
        self.assertIsNone(self.does("hegde", line, True))
        self.assertIsNone(self.does("hegde", "Shri G. Hegde pats Shri G. Hegde on the shoulder.", True))

    def test_opening_name_may_stay(self):              # Day 47, 10:02; Day 49, 15:49 and 17:19
        for cid, line in (("hegde", "Shri G. Hegde sighs deeply and rubs his temples."),
                          ("kapoor", "Mrs. Kapoor sits down on the bench, tapping her cane lightly against the concrete edge."),
                          ("kapoor", "Mrs. Kapoor adjusts her shawl and gestures for him to stay put on the bench.")):
            self.assertEqual(self.does(cid, line, True), line)

    def test_another_person_named_is_fine(self):
        self.assertEqual(self.does("hegde", "He hands Ramesh the file.", True), "He hands Ramesh the file.")

    def test_wrong_pronoun_drops_the_line(self):
        # Day 47, 10:17, Shri Hegde (he); Day 48, 20:05 and 20:20, the bookseller (he)
        for cid, line in (("hegde", "She rolls her eyes and turns away to check the stove."),
                          ("bookseller", "She gestures sharply toward the flickering dhaba sign across the street."),
                          ("bookseller", "She waves a dismissive hand at him and turns back to the shelf of hardcovers."),
                          ("nidhi", "He taps the book.")):
            self.assertEqual(self.does(cid, line, False), line)
            out = voices.clean(CAST[cid], {"says": "Well.", "does": line}, repairs=True)
            self.assertIsNone(out["does"])
            self.assertEqual(out["says"], "Well.")
        for cid, line in (("nidhi", "She taps the book."), ("hegde", "He nods."), ("hegde", "Sheets rustle."), ("hegde", "Nods, she says.")):
            self.assertEqual(self.does(cid, line, True), line)

    def test_off_is_todays(self):
        for cid, line in (("guard", "I gesture towards the front desk."), ("hegde", "She rolls her eyes."), ("hegde", "He pats Hegde's shoulder."), ("nidhi", "He taps.")):
            self.assertEqual(voices.clean(CAST[cid], {"says": "Well.", "does": line}), voices.clean(CAST[cid], {"says": "Well.", "does": line}, repairs=False))
            self.assertEqual(self.does(cid, line, False), line.rstrip(".") + ".")

    def test_dropped_line_leaves_the_words(self):
        out = voices.clean(CAST["guard"], {"says": "Go on, sir.", "does": "I gesture."}, repairs=True)
        self.assertEqual(out, {"by": "The guard at the library", "says": "Go on, sir.", "does": None})


class EngineWiring(unittest.TestCase):
    def test_voice_call_uses_repaired_prompt_and_clean(self):
        for on in (False, True):
            e = Engine.__new__(Engine)
            e.world, e.cfg, e.voice_prompt = W, SimpleNamespace(voice_facts=False, voice_repairs=on), "SYS"
            e.memory = SimpleNamespace(moments=lambda *a, **k: [], before=lambda d: [])
            asked = []

            class Mind:
                def chat(self, msgs, schema, max_tokens=0):
                    asked.append(msgs[1]["content"])
                    return '{"says": "Good morning.", "does": "I wave."}'
            e.mind = Mind()
            sit = dict(SIT, event="Nothing is cooked. Shri G. Hegde is here.")
            out = e.voice("hegde", dict(date="2026-11-17", entries=[], state={"people": ["ramesh"]}), sit, None)
            self.assertEqual("Shri G. Hegde is here." in asked[0], not on)
            self.assertEqual(out["does"], None if on else "I wave.")


if __name__ == "__main__":
    unittest.main()
