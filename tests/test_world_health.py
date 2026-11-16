"""World health (world/health.py, command line tools/world_health.py): what opened each of his moments, where he was,
how he thought and how his days differ, read from day files."""
import json
import unittest
from pathlib import Path

from tools import world_health as wh
from world import health

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


def mom(t, act, place, minutes, **more):
    s = step(t, "Nothing in particular happens.", **more)
    s["decision"].update(action=act, place=place, minutes=minutes)
    return s


def day_of(steps, date="2026-10-01"):
    return {"date": date, "n": 1, "steps": steps}


class Opened(unittest.TestCase):
    def test_opened_wins_over_the_words(self):
        s = step("09:00", "Headlines: A; B.", opened=[])
        self.assertEqual(wh.opening(s, None), "empty")
        self.assertEqual(wh.opening(step("09:00", "Nothing.", opened=["reply", "read"]), None), "answered")
        self.assertEqual(wh.opening(step("09:00", "Nothing.", opened=["reply", "arrive"]), None), "answered")       # as the words read it
        self.assertEqual(wh.opening(step("09:00", "Nothing.", opened=["arrive", "meal"]), None), "routine")
        self.assertEqual(wh.opening(step("09:00", "Nothing.", opened=["meal", "late"]), None), "routine")
        self.assertEqual(wh.opening(step("09:00", "Nothing.", opened=["arrive", "stranger:nidhi"]), None), "brought")
        self.assertEqual(wh.opening(step("09:00", "x", opened=["street:lodhi@khan"]), None), "brought")

    def test_brought_kinds_from_opened_cut_at_the_at_sign(self):
        s = step("09:00", "x", opened=["arrive", "street:lodhi@khan", "papers", "papers", "reply"])
        self.assertEqual(health.brought_kinds(s), ["street:lodhi", "papers"])
        self.assertEqual(health.brought_kinds(step("09:00", "Headlines: A.", opened=[])), [])

    def test_brought_kinds_from_words(self):
        e = "Headlines: A. Today's listings: B. The power goes. It begins to rain. Nidhi is here; you have not met."
        s = step("09:00", e, beat="hegde_gate")
        self.assertEqual(health.brought_kinds(s), ["beat:hegde_gate", "papers", "listings", "stranger", "power", "rain"])
        self.assertEqual(health.brought_kinds(step("09:00", "The air is very poor today. Ramesh brings the post: a letter.")), ["air", "post"])
        prev = step("10:19", "x", end="10:49", voice=VOICE)
        greeting = wh.heard({"by": "Nidhi Rao", "says": "Professor!", "does": None})
        self.assertEqual(health.brought_kinds(step("10:49", wh.heard(VOICE) + " " + greeting), prev), ["greeting"])
        self.assertEqual(health.brought_kinds(step("10:49", wh.heard(VOICE)), prev), [])


class Variety(unittest.TestCase):
    def setUp(self):
        a = [("walk", "lodhi", 30), ("walk", "lodhi", 30), ("read", "home", 60), ("walk", "home", 15)]
        self.steps = [mom(f"{9 + i // 4:02d}:{15 * (i % 4):02d}", *a[i % 4]) for i in range(20)]
        self.row = health.row(day_of(self.steps))

    def test_switches_dwell_and_pairs(self):
        r = self.row
        self.assertEqual((r["switches"], r["place_switches"]), (10, 9))
        self.assertEqual(r["dwell"], {"read": 60, "walk": 75})       # walks run 60, 75, 75, 75, 75, 15; reads 60 each
        self.assertEqual(r["dwell_all"], 60)
        self.assertEqual(r["act_places"], ["read@home", "walk@home", "walk@lodhi"])
        self.assertEqual(r["kinds"], [])
        self.assertEqual(r["act_minutes"], {"read": 300, "walk": 375})
        self.assertIsNone(r["doctrine"])

    def test_a_moment_the_mind_did_not_decide_breaks_a_run(self):
        steps = [mom("09:00", "walk", "lodhi", 30) for _ in range(22)]
        steps[10]["mind"] = {"source": "fallback"}
        r = health.row(day_of(steps))
        self.assertEqual((r["switches"], r["dwell"], r["dwell_all"]), (0, {"walk": 315}, 315))     # runs of 300 and 330

    def test_doctrine_is_counted_only_with_a_pattern(self):
        self.assertIsNone(health.row(DAY12)["doctrine"])
        self.assertEqual(health.row(DAY12, wh.DOCTRINE)["doctrine"], 44)

    def test_day12_new_fields_through_the_tool(self):
        r = wh.row(DAY12)
        self.assertEqual(sum(r["act_minutes"].values()), sum(s["decision"].get("minutes") or 0 for s in DAY12["steps"]
                                                             if "decision" in s and s.get("mind", {}).get("source") in ("mind", "stub")))
        self.assertEqual(len(r["act_places"]), len(set(r["act_places"])))
        self.assertEqual(r["act_places"], sorted(r["act_places"]))


class Across(unittest.TestCase):
    def rows(self, specs):
        out = []
        for i, (minutes, kinds, acts) in enumerate(specs):
            out.append({"date": f"2026-10-{i + 1:02d}", "act_minutes": minutes, "kinds": kinds, "act_places": acts})
        return out

    def test_variation_is_the_jensen_shannon_divergence_in_bits(self):
        self.assertEqual(health.divergence({"a": 10}, {"a": 5}), 0)
        self.assertAlmostEqual(health.divergence({"a": 10}, {"b": 3}), 1.0)
        self.assertAlmostEqual(health.divergence({"a": 1, "b": 1}, {"a": 1}), health.divergence({"a": 1}, {"a": 1, "b": 1}))
        self.assertIsNone(health.divergence({}, {"a": 1}))

    def test_the_first_day_has_no_value_and_none_rows_are_skipped(self):
        out = health.across([None] + self.rows([({"a": 1}, ["x"], ["a@h"]), ({"b": 1}, ["x", "y"], ["b@h"])]) + [None])
        self.assertEqual(len(out), 2)
        self.assertTrue(all(out[0][k] is None for k in ("variation", "kinds_seen", "kinds_seen_5", "acts_seen", "acts_seen_5")))
        self.assertAlmostEqual(out[1]["variation"], 1.0)
        self.assertEqual((out[1]["kinds_seen"], out[1]["acts_seen"]), (0.5, 0.0))

    def test_seen_looks_at_every_earlier_day_and_at_the_five_before(self):
        specs = [({"a": 1}, ["old"], ["a@h"])] + [({"a": 1}, [f"k{i}"], ["a@h"]) for i in range(6)] + [({"a": 1}, ["old", "k5"], ["a@h"])]
        last = health.across(self.rows(specs))[-1]
        self.assertEqual((last["kinds_seen"], last["kinds_seen_5"]), (1.0, 0.5))      # old is beyond five days; k5 is in the five
        self.assertEqual((last["acts_seen"], last["acts_seen_5"]), (1.0, 1.0))
        self.assertEqual(last["variation"], 0)

    def test_a_day_that_brought_nothing_has_no_kinds_seen(self):
        out = health.across(self.rows([({"a": 1}, ["x"], ["a@h"]), ({"a": 1}, [], ["a@h"])]))
        self.assertIsNone(out[1]["kinds_seen"])

    def test_the_table_and_the_pool_carry_the_new_columns(self):
        rows = health.across([wh.row(DAY12), wh.row(DAY12)])
        lines = wh.table(rows).splitlines()
        self.assertIn("| Switches | Dwell | Variation | Kinds seen | Acts seen |", lines[0])
        self.assertTrue(lines[2].endswith("| – | – | – |"))
        self.assertTrue(lines[3].endswith("| 0.00 | 1.00 | 1.00 |") or "| 0.00 |" in lines[3])
        p = wh.pooled(rows)
        self.assertEqual(p["variation"], 0.0)
        self.assertEqual(p["switches"], rows[0]["switches"])
        self.assertEqual(p["acts_seen"], rows[1]["acts_seen"])


if __name__ == "__main__":
    unittest.main()
