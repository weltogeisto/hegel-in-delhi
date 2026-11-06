"""Training 3's labeller (tools/decision_pairs.py): the world's verdicts and T9's phrase rule decide, nothing else."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import decision_pairs as dp

LONG = "The file has gone to the wrong desk and the clerk will not look at it until Monday morning comes"


def cand(seed, thought, accepted=True, errors=()):
    answer = None if thought is None else {"thought": thought, "action": "rest"}
    return {"seed": seed, "raw": json.dumps(answer), "answer": answer, "accepted": accepted, "errors": list(errors)}


def row(cands, earlier=(), day=35, source="shadow", rid="shadow:35:1"):
    return {"id": rid, "source": source, "day": day, "step": 1, "messages": [{"role": "user", "content": "x"}],
            "earlier_thoughts": list(earlier), "candidates": cands}


class LabelTest(unittest.TestCase):
    def test_labels(self):
        earlier = ["I felt the friction of the particular against the universal today"]
        self.assertEqual(dp.label(cand(1, LONG), earlier), "clean")
        self.assertEqual(dp.label(cand(1, "Again the friction of the particular against the universal"), earlier), "repeating")
        self.assertEqual(dp.label(cand(1, LONG, accepted=False), earlier), "refused")
        self.assertEqual(dp.label(cand(1, None, accepted=False), earlier), "invalid")

    def test_stopword_runs_are_not_phrases(self):
        self.assertEqual(dp.label(cand(1, "It is what it is in the end of it all"), ["it is what it is"]), "clean")


class PairTest(unittest.TestCase):
    def test_first_clean_against_first_length_matched_rejection(self):
        refused = LONG.replace("Monday", "Tuesday")
        short = "No."
        r = row([cand(4271, LONG), cand(1831, short, accepted=False), cand(2718, refused, accepted=False),
                 cand(3141, LONG + " again")])
        labels, p = dp.pair(r)
        self.assertEqual(p["rejected_seed"], 2718)         # 1831 is refused but far too short to match
        self.assertEqual(p["chosen_seed"], 3141)           # the first clean one in seed order
        self.assertEqual(p["rejected_as"], "refused")

    def test_no_clean_candidate_no_pair(self):
        _, p = dp.pair(row([cand(1, LONG, accepted=False), cand(2, LONG, accepted=False)]))
        self.assertIsNone(p)

    def test_silence_never_wins(self):
        _, p = dp.pair(row([cand(1, "Rest."), cand(2, LONG, accepted=False)]))
        self.assertIsNone(p)                               # 1 word against 20: not length-matched

    def test_test_days_and_duplicates_refused(self):
        with self.assertRaises(ValueError):
            dp.build([row([cand(1, LONG)], day=27, rid="shadow:27:1")])
        with self.assertRaises(ValueError):
            dp.build([row([cand(1, LONG)]), row([cand(1, LONG)])])
        pairs, stats = dp.build([row([cand(1, LONG)], day=27, source="rehearsal", rid="rehearsal:27:1")])
        self.assertEqual(stats["situations"], 1)           # a rehearsal's day number is not a shadow test day

    def test_cli_writes_new_files_only(self):
        folder = Path(tempfile.mkdtemp())
        src = folder / "candidates.jsonl"
        src.write_text(json.dumps(row([cand(1, LONG), cand(2, LONG + " too", accepted=False)])) + "\n")
        out = folder / "pairs.jsonl"
        self.assertEqual(dp.main(["--candidates", str(src), "--out", str(out)]), 0)
        self.assertEqual(len(out.read_text().splitlines()), 1)
        stats = json.loads(out.with_suffix(".stats.json").read_text())
        self.assertEqual(stats["pairs"], 1)
        with self.assertRaises(FileExistsError):
            dp.main(["--candidates", str(src), "--out", str(out)])


if __name__ == "__main__":
    unittest.main()
