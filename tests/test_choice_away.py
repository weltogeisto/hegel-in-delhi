"""When the PC goes away between his decision and his yes or no to an offer, that is not a no: the offer is not made
and stays open for a later moment (DECISIONS 49). Before, a dropped answer counted as a refusal, with its week's wait."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_economy import D, There, fresh  # noqa: E402
from test_world import answer  # noqa: E402

from world.engine import Engine  # noqa: E402
from world.mind import MindAway  # noqa: E402
from world.world import World, at_dt  # noqa: E402

R = Path(__file__).resolve().parents[1]
MON = D(2, 11)          # a Monday: Ramesh comes, and the wage of 1 November stands owed


def wage():
    return {"to": "Ramesh", "amount": 8000, "why": "the wage for cooking", "since": "2026-11-01", "cost": "wage",
            "item": "Ramesh's wage for cooking", "at": "home", "with": "ramesh"}


class ChoiceAwayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-choice-away-")
        self.w = World()

    def tearDown(self):
        self.tmp.cleanup()

    def day(self):
        st = fresh(settled=MON.isoformat())
        st.update(place="home", asleep=False, today={}, owed=[wage()], imprest=1451)
        return {"date": MON.isoformat(), "n": 33, "steps": [], "entries": [], "segments": [], "complete": False, "state": st}

    def engine(self, chat):
        cfg = SimpleNamespace(repo=R, docs=Path(self.tmp.name) / "docs", soul_file=R / "mind/soul.md", shelf=False)
        mind = mock.Mock()
        mind.source, mind.ready = "stub", True
        mind.decide.return_value = json.dumps(answer())
        mind.chat.side_effect = chat
        e = Engine(cfg, self.w, mind)
        e.greet = mock.Mock(return_value=True)
        e.memory.recall = mock.Mock(return_value=[])
        e.memory.recent_thoughts = mock.Mock(return_value=[])
        e.memory.known_text = mock.Mock(return_value="")
        return e

    def test_ask_choice_says_none_when_the_pc_goes_away(self):
        e = self.engine(MindAway("no answer"))
        messages = [{"role": "system", "content": e.soul}, {"role": "user", "content": "Ramesh waits."}]
        self.assertIsNone(e.ask_choice(messages, "{}", {"choice": {"question": "Agreed?"}}))

    def test_a_dropped_answer_leaves_the_offer_open_and_it_comes_again(self):
        day = self.day()
        st = day["state"]
        with There(home=["ramesh"]):
            step = self.engine(MindAway("no answer")).step(day, at_dt(MON, 600))
        self.assertNotIn("beat", step)
        self.assertNotIn("ramesh_parttime", st["beats"])
        self.assertNotIn("ramesh_parttime", st["refused"])                         # no week's wait
        self.assertFalse(st["flags"].get("ramesh_parttime"))
        self.assertFalse([x for x in day["entries"] if "three days a week" in x.get("text", "")])
        self.assertEqual(day.get("funnel", {}).get("offer:ramesh_parttime", {}).get("no", 0), 0)

        with There(home=["ramesh"]):
            step = self.engine(lambda *a, **k: '{"answer": "yes"}').step(day, at_dt(MON, 630))
        self.assertEqual(step.get("beat"), "ramesh_parttime")
        self.assertIs(st["flags"]["ramesh_parttime"], True)

    def test_a_real_no_still_counts_as_a_no(self):
        day = self.day()
        st = day["state"]
        with There(home=["ramesh"]):
            step = self.engine(lambda *a, **k: '{"answer": "no"}').step(day, at_dt(MON, 600))
        self.assertEqual(step.get("beat"), "ramesh_parttime")
        self.assertEqual(st["refused"].get("ramesh_parttime"), MON.isoformat())
        self.assertFalse(st["flags"].get("ramesh_parttime"))


if __name__ == "__main__":
    unittest.main()
