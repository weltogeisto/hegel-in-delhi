"""HEGEL_KEEP_DRAWS (pc/FILTER-PAIRS.md): the filter's draws kept in the state folder, never in the day file, and
turned into Training 3's preference pairs by tools/filter_pairs.py."""
import copy
import gzip
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

from world import prefer  # noqa: E402
from world.config import Config  # noqa: E402
from world.engine import Engine  # noqa: E402
from world.world import World, at_dt  # noqa: E402

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "tools"))
import filter_pairs  # noqa: E402

DAY = D(3, 11)
BAD = json.dumps(answer(place="nowhere"))                                    # the world refuses an unknown place
GOOD = json.dumps(answer(thought="Ramesh has left the papers on the step, and the tea is still hot in the pot."))


class KeepDrawsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hegel-keep-draws-")
        self.w = World()

    def tearDown(self):
        self.tmp.cleanup()

    def engine(self, keep):
        cfg = SimpleNamespace(repo=R, docs=Path(self.tmp.name) / "docs", soul_file=R / "mind/soul.md", shelf=False,
                              decision_draws=4, keep_draws=keep, state=Path(self.tmp.name) / "state")
        mind = mock.Mock()
        mind.source, mind.ready = "stub", True
        mind.decide.side_effect = [BAD, GOOD, GOOD, GOOD]
        e = Engine(cfg, self.w, mind)
        e.greet = mock.Mock(return_value=True)
        e.memory.recall = mock.Mock(return_value=[])
        e.memory.recent_thoughts = mock.Mock(return_value=[])
        e.memory.known_text = mock.Mock(return_value="")
        return e

    def day(self):
        st = fresh(settled=DAY.isoformat())
        st.update(place="home", asleep=False, today={})
        return {"date": DAY.isoformat(), "n": 34, "steps": [], "entries": [], "segments": [], "complete": False, "state": st}

    def kept(self):
        files = list((Path(self.tmp.name) / "state" / "draws").glob("*.jsonl.gz"))
        if not files:
            return []
        with gzip.open(files[0], "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def test_off_by_default_and_nothing_is_kept(self):
        self.assertFalse(Config({}).keep_draws)
        self.assertTrue(Config({"HEGEL_KEEP_DRAWS": "1"}).keep_draws)
        with There(home=[]):
            self.engine(False).step(self.day(), at_dt(DAY, 600))
        self.assertEqual(self.kept(), [])

    def test_on_the_draws_are_kept_outside_the_day_and_the_step_is_unchanged(self):
        steps = {}
        for keep in (False, True):
            day = self.day()
            with There(home=[]):
                step = self.engine(keep).step(day, at_dt(DAY, 600))
            steps[keep] = {k: v for k, v in step.items() if k != "mind"}, {k: v for k, v in step["mind"].items() if k != "latency_s"}
        self.assertEqual(steps[False], steps[True])                          # the day file does not change
        self.assertEqual(steps[True][1]["draws"], {"n": 2, "refused": 1, "echo": 0, "picked": 1})
        rows = self.kept()
        self.assertEqual(len(rows), 1)
        self.assertEqual([bool(d["errors"]) for d in rows[0]["draws"]], [True, False])
        self.assertEqual(rows[0]["picked"], 1)
        self.assertEqual(rows[0]["messages"][0]["role"], "system")
        self.assertEqual(rows[0]["soul"], "soul.md")

    def test_one_reply_keeps_nothing(self):
        e = self.engine(True)
        e.mind.decide.side_effect = [GOOD]
        with There(home=[]):
            e.step(self.day(), at_dt(DAY, 600))
        self.assertEqual(self.kept(), [])

    def test_choose_keeps_each_draw_and_its_verdict(self):
        keep, seq = [], iter(["a", "b", "c"])
        verdicts = {"a": (["refused"], None), "b": ([], "the same old phrase about the file again today"),
                    "c": ([], "Ramesh brings tea and the papers to the verandah")}
        raw, note = prefer.choose(lambda: next(seq), lambda r: verdicts[r], ["the same old phrase about the file again"], 4, keep=keep)
        self.assertEqual((raw, note), ("c", {"n": 3, "refused": 1, "echo": 1, "picked": 2}))
        self.assertEqual([(bool(k["errors"]), k["fresh"]) for k in keep], [(True, None), (False, False), (False, True)])


class PairsTest(unittest.TestCase):
    def row(self, draws, picked):
        return {"date": "2026-11-03", "t": "10:00", "soul": "soul.md", "messages": [{"role": "system", "content": "s"}],
                "draws": draws, "picked": picked}

    def test_refused_and_echoing_replies_pair_with_the_pick_when_lengths_match(self):
        chosen = {"raw": "c", "errors": [], "thought": "one two three four five six seven eight nine ten", "fresh": True}
        refused = {"raw": json.dumps({"thought": "uno dos tres cuatro cinco seis siete ocho nueve"}), "errors": ["bad place"], "thought": None, "fresh": None}
        echo = {"raw": "e", "errors": [], "thought": "a b c d e f g h i j k", "fresh": False}
        short = {"raw": "s", "errors": [], "thought": "too short", "fresh": False}
        pairs, skipped = filter_pairs.pairs_of(self.row([refused, echo, short, chosen], 3))
        self.assertEqual([p["rejected_why"] for p in pairs], ["refused", "repeats a shown thought"])
        self.assertEqual(skipped, ["lengths differ by more than 20%"])

    def test_no_pair_when_the_pick_was_not_fresh(self):
        echo = {"raw": "e", "errors": [], "thought": "x y z", "fresh": False}
        self.assertEqual(filter_pairs.pairs_of(self.row([echo, copy.deepcopy(echo)], 0)), ([], ["the pick was not fresh"]))

    def test_build_counts_against_the_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = {"raw": "c", "errors": [], "thought": "one two three four five", "fresh": True}
            refused = {"raw": "r", "errors": ["x"], "thought": "uno dos tres cuatro cinco", "fresh": None}
            with gzip.open(Path(tmp) / "2026-11-03.jsonl.gz", "wt", encoding="utf-8") as f:
                f.write(json.dumps(self.row([refused, chosen], 1)) + "\n")
            pairs, stats = filter_pairs.build(tmp, Path(tmp) / "out")
            self.assertEqual((len(pairs), stats["pairs"], stats["bar"], stats["bar_met"]), (1, 1, 200, False))
            self.assertTrue((Path(tmp) / "out" / "pairs.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
