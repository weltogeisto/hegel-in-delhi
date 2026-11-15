"""World health (tools/world_health.py): what opened each of his moments, where he was and how he thought, read from a day file."""
import json
import unittest
from pathlib import Path

from tools import world_health as wh

REPO = Path(__file__).resolve().parent.parent
DAY12 = json.loads((REPO / "tests/data/day12-2026-10-13.json").read_text(encoding="utf-8"))
DAY13 = json.loads((REPO / "tests/data/day13-2026-10-14.json").read_text(encoding="utf-8"))
VOICE = {"by": "Sunil", "says": "Sit, the kettle is just boiling.", "does": None}


def step(t, event, **more):
    return dict({"t": t, "end": t, "event": event, "decision": {"thought": "A thought.", "action": "stay", "place": "lodhi"},
                 "mind": {"source": "mind"}}, **more)


class Opening(unittest.TestCase):
    def test_a_reply_to_what_he_said_is_answered(self):
        prev = step("10:19", "You arrive at Lodhi Gardens.", end="10:49", voice=VOICE)
        self.assertEqual(wh.opening(step("10:49", wh.heard(VOICE)), prev), "answered")

    def test_an_answer_given_where_he_left_does_not_open_the_next_moment(self):
        prev = step("10:19", "Sunil is here.", end="10:49", voice=VOICE, left="lodhi")
        self.assertEqual(wh.opening(step("10:49", "You arrive at Khan Market. It closes at 20:30."), prev), "routine")

    def test_nothing_happens_is_empty(self):
        self.assertEqual(wh.opening(step("11:14", "Nothing in particular happens. The morning goes on."), None), "empty")

    def test_what_he_did_not_start_is_brought(self):
        for event in ("You wake. Clear, 21 °C. Ramesh has left the papers on the verandah. Headlines: A; B.",
                      "Nidhi is here; you have not met.", "The power goes. The fan stops. Ramesh lights two candles.",
                      "Ramesh brings the post: a letter from Dr. Lindner in Munich. It reads: “…”"):
            self.assertEqual(wh.opening(step("09:15", event), None), "brought", event)
        self.assertEqual(wh.opening(step("17:40", "Shri Hegde rings the bell.", beat="hegde_gate"), None), "brought")

    def test_a_person_who_speaks_first_is_brought_even_beside_a_reply(self):
        prev = step("10:19", "Sunil is here.", end="10:49", voice=VOICE)
        greeting = wh.heard({"by": "Nidhi Rao", "says": "Professor! You are out early.", "does": None})
        self.assertEqual(wh.opening(step("10:49", wh.heard(VOICE) + " " + greeting), prev), "brought")
        self.assertEqual(wh.opening(step("10:49", greeting), None), "brought")


class Day(unittest.TestCase):
    def test_day12_as_recorded(self):
        r = wh.row(DAY12)
        self.assertEqual((r["moments"], r["opens"]), (42, {"answered": 24, "empty": 7, "brought": 5, "routine": 6}))
        self.assertEqual((r["home"], r["places"], r["place_bits"], r["voices"]), (29, 3, 1.2, 5))
        self.assertEqual((r["words"], r["doctrine"], r["cash"]), (2931, 44, 6891))

    def test_a_day_below_the_floor_is_not_read(self):
        self.assertIsNone(wh.row(DAY13))                         # 4 thoughts: the mind was away

    def test_one_place_all_day_has_no_entropy(self):
        self.assertEqual(wh.entropy({"home": 30}), 0.0)
        self.assertEqual(wh.entropy({"home": 15, "khan": 15}), 1.0)

    def test_the_pooled_read_weights_moments_not_days(self):
        r = wh.row(DAY12)
        both = wh.pooled([r, dict(r, moments=42, opens={"answered": 42, "empty": 0, "brought": 0, "routine": 0})])
        self.assertEqual(both["opens"]["answered"], round((24 + 42) / 84, 3))
        self.assertEqual((both["days"], both["brought_per_day"]), (2, 2.5))
        self.assertEqual(wh.pooled([]), {"days": 0, "moments": 0})

    def test_the_table_has_a_line_a_day(self):
        lines = wh.table([wh.row(DAY12)]).splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("| 12 | 2026-10-13 | 42 | 57% | 17% | 5 | 69% | 3 | 1.20 | 5 | 1.50 | ₹6,891 |", lines[2])


if __name__ == "__main__":
    unittest.main()
