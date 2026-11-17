"""A2: the engine says what opened a moment (`opened` on each step), and the day carries nothing else new but the funnel.
Ten days with the stand-in from Saturday 3 October."""
import hashlib
import json
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_world import REPO, Sandbox  # noqa: E402  (this also keeps the tests off the Pi's env file)

from world import health  # noqa: E402
from world.world import at_dt  # noqa: E402

START, DAYS = date(2026, 10, 3), 10
VOCABULARY = {"reply", "read", "papers", "listings", "late", "beat", "offer", "session", "post", "stranger", "greeting", "power", "rain",
              "air", "sight", "part", "arrive", "closing", "closes", "meal", "tea", "kitchen", "hunger", "felt", "purse",
              "wake", "here"}          # the last two are not in the spec's table: the wake-up line without headlines, a known person come into sight
_RUN = []
REFERENCE = REPO / "tests/data/opened_reference.json"
ADDED = {"step": ("opened",), "day": ("funnel",)}       # fields that are only ever added to the record, and say nothing he is told: taken out before hashing


def hashes(days):
    """A hash of each day, with the wall time masked and the fields in ADDED taken out."""
    out = {}
    for day in days:
        day = json.loads(json.dumps(day))
        for s in day["steps"]:
            s.get("mind", {}).pop("latency_s", None)
            for k in ADDED["step"]:
                s.pop(k, None)
        for k in ADDED["day"]:
            day.pop(k, None)
        out[day["date"]] = hashlib.sha256(json.dumps(day, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return out


def run():
    """The ten days, once: the days as the engine wrote them (owl included)."""
    if not _RUN:
        box = Sandbox()
        try:
            e, days = box.engine(), []
            for i in range(DAYS):
                d = START + timedelta(days=i)
                box.run_day(d, e)
                e.run_owl(box.days.load(d), at_dt(d + timedelta(days=1), 90))
                days.append(box.days.load(d))
        finally:
            box.close()
        _RUN.append(days)
    return _RUN[0]


def decided(days):
    """(step, the decided step before it in its day) for each step a mind decided."""
    for day in days:
        prev = None
        for s in day["steps"]:
            if s.get("mind", {}).get("source") in ("mind", "stub"):
                yield s, prev
            if "decision" in s:
                prev = s


class OpenedTest(unittest.TestCase):
    def test_kinds_are_from_the_vocabulary(self):
        n = 0
        for s, _ in decided(run()):
            self.assertIsInstance(s["opened"], list)
            self.assertEqual(len(s["opened"]), len(set(s["opened"])), s["opened"])
            for k in s["opened"]:
                self.assertIn(k.split(":", 1)[0], VOCABULARY, f"{s['t']}: {k}")
                n += 1
        self.assertGreater(n, 30)

    def test_empty_list_is_the_quiet_moment(self):
        for s, _ in decided(run()):
            self.assertEqual(not s["opened"], "Nothing in particular happens." in s["event"], s["event"])

    def test_greeting_and_reply_are_named(self):
        steps = [s for s, _ in decided(run())]
        self.assertTrue(any(k.startswith("greeting:") for s in steps for k in s["opened"]), "no greeting in ten days")
        self.assertTrue(any("reply" in s["opened"] for s in steps))
        for s in steps:                       # a greeting is a person speaking first: its words are in the event
            for k in s["opened"]:
                if k.startswith("greeting:"):
                    self.assertIn(" says: ", s["event"])

    def test_sessions_and_offers_carry_their_ids(self):
        kinds = {k for s, _ in decided(run()) for k in s["opened"]}
        self.assertTrue(any(k.startswith("offer:") for k in kinds), kinds)
        self.assertTrue(any(k.startswith("beat:") for k in kinds), kinds)
        self.assertFalse(any("@" in k for k in kinds), kinds)

    def test_health_agrees_with_the_words(self):
        """The reading of `opened` and the reading of the event's words give one label, wherever the words can tell. The words are
        coarser in known ways: a phone's page has no fixed words (`read` answers, the words say routine); a sight or a part of a
        performance has none either (brought by `opened`, routine by the words). Any other difference is a bug in one of the two."""
        seen = 0
        for s, prev in decided(run()):
            bare = {k: v for k, v in s.items() if k != "opened"}
            a, b = health.opening(s, prev), health.opening(bare, prev)
            if a == b:
                continue
            seen += 1
            kinds = {k.split(":", 1)[0] for k in s["opened"]}
            explained = (a == "answered" and b == "routine" and "read" in kinds) or \
                        (a == "brought" and b == "routine" and kinds & {"sight", "part"})
            self.assertTrue(explained, (a, b, s["opened"], s["event"][:120]))
        self.assertLessEqual(seen, 5)

    def test_the_day_is_the_day_it_was(self):
        """With `opened` and `funnel` taken out and the wall time masked, each day is byte-for-byte what the code before A2 wrote
        (tests/data/opened_reference.json: a hash of each day, made by the code at the commit before this packet).

        This is the guard behind "a day with every new switch off is the day main gives" (WORLD-2.md, rule 4). When it fails, the
        code under test writes a different day with its switches off. Three ways on, in this order: put the new thing behind a
        switch that is off by default; or, for a new field that is only ever added, name it in ADDED above with a line on why;
        or record the reference again (`python3 tests/test_opened.py --record`) in a commit that says which values changed and
        why. Never record it again to make a failure go away."""
        want = json.loads(REFERENCE.read_text(encoding="utf-8"))
        got = hashes(run())
        differ = sorted(d for d in want if got.get(d) != want[d])
        self.assertEqual(got, want, f"{len(differ)} of {len(want)} days differ from the reference, the first on {differ[0] if differ else '-'}: "
                                    "see this test's docstring for what to do")


if __name__ == "__main__":
    if "--record" in sys.argv:          # on purpose only: see test_the_day_is_the_day_it_was
        REFERENCE.write_text(json.dumps(hashes(run()), indent=1) + "\n", encoding="utf-8")
        print(f"recorded {REFERENCE}")
    else:
        unittest.main()
