"""HEGEL_TALK_SCENE (Day 54, Guru Nanak Jayanti): at the IIC talk the programme officer answers and not the guard; a voice is told whether its
place is open today; the lecture is given and filed; one listener asks one question. Off, none of it happens."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import D, PLOT, There  # noqa: E402
from test_world import Sandbox, answer  # noqa: E402

from datetime import date  # noqa: E402

from world import talk  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.mind import MindAway, StubMind  # noqa: E402
from world.world import World, at_dt  # noqa: E402

DAY = D(24, 11)                        # Guru Nanak Jayanti, a holiday: the IIC is open all the same
LECTURE = " ".join(f"Sentence {i} of the lecture holds that spirit comes to know itself in what it does." for i in range(60))
LECTURE += "\n\nSo the last paragraph says that a hall is a small public, and a public is the beginning of a freedom."
THOUGHTS = {"18:30": "The hall is quiet and the seats are filling; I will say what I have come to say.",
            "19:30": "It is over, and the officer comes with a cheque in an envelope."}
HERE = ["guard", "officer"]            # the guard first: the legacy fallback picks the first of the people present


class Hall(StubMind):
    """A mind that talks in the hall, and keeps what the voices and the lecture were asked."""
    source = "stub"

    def __init__(self, lecture=None, away=False):
        self.lecture, self.away, self.prompts, self.lectures = LECTURE if lecture is None else lecture, away, [], 0

    def decide(self, messages, sit):
        return json.dumps(answer(action="talk", place="iic", minutes=60, says="Good evening. I am ready to begin.",
                                 thought=THOUGHTS.get(sit["time"], "Another thought, wholly unlike the last, about the cheque and the walk home.")))

    def chat(self, messages, schema=None, max_tokens=700, temperature=None):
        props, ask = (schema or {}).get("properties", {}), messages[-1]["content"]
        if "does" in props:
            self.prompts.append(ask)
            who = ask.split(",")[0].replace("You are ", "")
            return json.dumps({"says": f"({who}) a reply that is long enough.", "does": None})
        if schema is talk.LECTURE_SCHEMA:
            self.lectures += 1
            if self.away:
                raise MindAway("gone")
            return json.dumps({"title": "On the Public", "kind": "essay", "to": None, "continues": False, "text": self.lecture})
        return super().chat(messages, schema, max_tokens, temperature)


def hall(on, mind=None):
    """(sandbox, engine, mind, day) with him at the IIC at half past six on the holiday, the talk booked."""
    box, mind = Sandbox(), mind or Hall()
    e = Engine(box.cfg, World(talk_scene=on, keep_time=True), mind)
    prev = box.days.load(date(2026, 10, 2))
    prev["state"]["asleep"] = False
    day = e.new_day(prev, DAY)
    st = day["state"]
    st.update(place="iic", today={"woke": "06:00"}, until=at_dt(DAY, 18 * 60 + 30).isoformat(timespec="minutes"))
    st["beats"] += PLOT + ["iic_talk"]
    st["appointments"].append({"date": DAY.isoformat(), "t": "18:30", "what": "your talk at the IIC", "beat": "iic_talk_day"})
    return box, e, mind, day


def talk_step(on, mind=None):
    box, e, mind, day = hall(on, mind)
    with There(iic=HERE):
        step = e.step(day, at_dt(DAY, 18 * 60 + 30))
    return box, e, mind, day, step


class TalkScene(unittest.TestCase):
    def tearDown(self):
        for box in getattr(self, "boxes", []):
            box.close()

    def run_talk(self, on, mind=None):
        box, e, mind, day, step = talk_step(on, mind)
        self.boxes = getattr(self, "boxes", []) + [box]
        return e, mind, day, step

    # ── A: the right person answers ──
    def test_the_officer_answers_in_the_hall_and_not_the_guard(self):
        e, mind, day, step = self.run_talk(True)
        self.assertEqual(step["beat"], "iic_talk_day")
        self.assertEqual(step["voice"]["by"], "The programme officer")
        self.assertIn("talk", day["state"])

    def test_off_the_guard_answers_as_on_day_54(self):
        e, mind, day, step = self.run_talk(False)
        self.assertEqual(step["voice"]["by"], "The guard at the library")
        self.assertNotIn("talk", day["state"])

    def test_the_officer_hands_over_the_cheque(self):
        e, mind, day, step = self.run_talk(True)
        with There(iic=HERE):
            later = e.step(day, at_dt(DAY, 19 * 60 + 30))
        self.assertEqual(later["voice"]["by"], "The programme officer")
        self.assertEqual(day["state"]["cheques"][0]["amount"], 10000)

    def test_half_an_hour_after_the_talk_or_away_from_the_place_the_guard_is_back(self):
        w = World(talk_scene=True)
        st = {"talk": {"beat": "iic_talk_day", "place": "iic", "by": ["officer"], "until": at_dt(DAY, 20 * 60).isoformat(timespec="minutes")}}
        self.assertEqual(w.in_the_hall(HERE, st, at_dt(DAY, 19 * 60 + 59), "iic"), ["officer"])
        self.assertEqual(w.in_the_hall(HERE, st, at_dt(DAY, 20 * 60 + 1), "iic"), HERE)
        self.assertNotIn("talk", st)
        st = {"talk": {"beat": "iic_talk_day", "place": "iic", "by": ["officer"], "until": at_dt(DAY, 20 * 60).isoformat(timespec="minutes")}}
        self.assertEqual(w.in_the_hall(HERE, st, at_dt(DAY, 19 * 60), "home"), HERE)
        self.assertNotIn("talk", st)

    # ── B: whether the place is open today ──
    def test_a_voice_is_told_it_is_a_holiday_and_the_place_is_open(self):
        e, mind, day, step = self.run_talk(True)
        self.assertTrue(mind.prompts)
        for p in mind.prompts:
            self.assertIn("Today is Guru Nanak Jayanti. India International Centre is open until 21:30 today.", p)

    def test_off_no_voice_is_told(self):
        e, mind, day, step = self.run_talk(False)
        self.assertNotIn("Guru Nanak Jayanti. India", mind.prompts[0])
        self.assertNotIn("is open until", mind.prompts[0])

    def test_the_line_says_closed_when_the_place_is_closed(self):
        w = World(talk_scene=True)
        self.assertEqual(w.open_line("estates", at_dt(DAY, 11 * 60)),
                         "Today is Guru Nanak Jayanti. Directorate of Estates, Nirman Bhawan is closed all day today.")
        self.assertEqual(w.open_line("iic", at_dt(D(13), 8 * 60)), "India International Centre opens at 09:00 today.")
        self.assertEqual(w.open_line("iic", at_dt(D(13), 22 * 60)), "India International Centre closed at 21:30 today.")
        self.assertEqual(w.open_line("home", at_dt(D(13), 8 * 60)), "")

    # ── C: the lecture ──
    def test_the_lecture_is_written_and_filed_once_with_the_minds_text(self):
        e, mind, day, step = self.run_talk(True)
        self.assertEqual(mind.lectures, 1)
        rows = [x for x in day["entries"] if x["k"] == "writing"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Lecture at the IIC: On the Public")
        self.assertEqual(rows[0]["text"], LECTURE.strip())
        self.assertEqual(rows[0]["kind"], "essay")
        self.assertEqual([w["title"] for w in day["state"]["works"]], ["Lecture at the IIC: On the Public"])
        self.assertEqual(day["state"]["works"][0]["words"], len(LECTURE.split()))

    def test_the_lecture_prompt_carries_his_manuscripts(self):
        seen = []

        class Spy(Hall):
            def chat(self, messages, schema=None, max_tokens=700, temperature=None):
                if talk.LECTURE_ASK in messages[-1]["content"]:
                    seen.append(messages[-1]["content"])
                return super().chat(messages, schema, max_tokens, temperature)

        box, e, mind, day = hall(True, Spy())
        self.boxes = [box]
        day["state"]["works"] = [{"id": "old", "title": "On Light", "kind": "essay", "to": None, "started": "2026-10-03", "words": 9, "sittings": 1,
                                  "last": "2026-10-03", "tail": "x"}]
        with There(iic=HERE):
            e.step(day, at_dt(DAY, 18 * 60 + 30))
        self.assertIn("“On Light”", seen[0])

    def test_with_the_mind_away_the_talk_still_fires_and_nothing_is_stored(self):
        e, mind, day, step = self.run_talk(True, Hall(away=True))
        self.assertEqual(step["beat"], "iic_talk_day")
        self.assertEqual(step["voice"]["by"], "The programme officer")
        self.assertEqual([x for x in day["entries"] if x["k"] == "writing"], [])
        self.assertEqual(day["state"].get("works", []), [])
        self.assertNotIn("hall", step)
        self.assertIn("iic_talk_day", day["state"]["beats"])

    def test_a_reply_too_short_for_a_lecture_is_dropped(self):
        e, mind, day, step = self.run_talk(True, Hall(lecture="Too short."))
        self.assertEqual(step["beat"], "iic_talk_day")
        self.assertEqual([x for x in day["entries"] if x["k"] == "writing"], [])

    def test_a_lecture_with_a_name_from_after_1831_is_dropped(self):
        e, mind, day, step = self.run_talk(True, Hall(lecture=LECTURE + " Heidegger would object."))
        self.assertEqual(step["beat"], "iic_talk_day")
        self.assertEqual(mind.lectures, 2)                     # asked once more, then dropped
        self.assertEqual([x for x in day["entries"] if x["k"] == "writing"], [])

    def test_off_no_lecture_is_asked_for_or_filed(self):
        e, mind, day, step = self.run_talk(False)
        self.assertEqual(mind.lectures, 0)
        self.assertEqual([x for x in day["entries"] if x["k"] == "writing"], [])
        self.assertNotIn("hall", step)
        self.assertNotIn("hall_listener", e.world.cast)

    # ── D: one question from the hall ──
    def test_one_listener_asks_one_question_told_the_title_and_the_last_paragraph(self):
        e, mind, day, step = self.run_talk(True)
        ask = [p for p in mind.prompts if p.startswith("You are a listener in the hall")]
        self.assertEqual(len(ask), 1)
        self.assertIn("Lecture at the IIC: On the Public", ask[0])
        self.assertIn("a hall is a small public", ask[0])
        self.assertNotIn("Sentence 3 of the lecture", ask[0])
        said = [x for x in day["entries"] if x["k"] == "said" and x.get("by") == "A listener in the hall"]
        self.assertEqual(len(said), 1)
        self.assertEqual(step["hall"]["by"], "A listener in the hall")
        self.assertNotIn("A listener in the hall", [p for p in step["present"]])

    def test_he_hears_the_question_in_his_next_situation(self):
        e, mind, day, step = self.run_talk(True)
        with There(iic=HERE):
            sit, _ = e.world.situation(at_dt(DAY, 19 * 60 + 30), day["state"], day, step)
        self.assertIn("A listener in the hall says:", sit["event"])

    def test_the_listener_is_not_there_without_the_switch(self):
        self.assertNotIn("hall_listener", World().cast)
        self.assertIn("hall_listener", World(talk_scene=True).cast)


if __name__ == "__main__":
    unittest.main()
