import copy
import json
import tempfile
import unittest
from pathlib import Path

from pc import decision_dpo_data as dpo
from tools import decision_pairs


class Tokenizer:
    eos_token, eos_token_id = "<END>", 999
    turn_end = "<END>"          # what the template writes after an assistant answer

    def apply_chat_template(self, messages, **kw):
        head = "SYS:" + messages[0]["content"] + "|USER:" + messages[1]["content"] + "|ASSISTANT:"
        if kw == dict(tokenize=False, add_generation_prompt=True, enable_thinking=False):
            return head
        assert kw == dict(tokenize=False, enable_thinking=False) and messages[-1]["role"] == "assistant"
        return head + messages[-1]["content"] + self.turn_end + "\n"

    def __call__(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        if text == self.eos_token:
            return {"input_ids": [self.eos_token_id]}
        return {"input_ids": list(text.encode())}


def pair(i=0):
    return dict(id=f"shadow:35:{i}", prompt=[dict(role="system", content="soul"),
                dict(role="user", content="decision")], chosen='{"thought":"good"}',
                rejected='{"thought":"refused"}')


class DataTest(unittest.TestCase):
    def test_boundary_keeps_whole_pair_and_includes_eos(self):
        tok = Tokenizer()
        _, counts = dpo.render_pair(pair(), tok, 1000)
        exact = counts["prompt"] + max(counts["chosen"], counts["rejected"])
        kept, _ = dpo.render_pair(pair(), tok, exact)
        dropped, _ = dpo.render_pair(pair(), tok, exact - 1)
        self.assertIsNotNone(kept)
        self.assertIsNone(dropped)
        self.assertEqual(kept["chosen"], pair()["chosen"])
        self.assertTrue(kept["prompt"].endswith("|ASSISTANT:"))

    def test_length_report_keeps_every_excluded_id(self):
        a, b = pair(), pair(1)
        b["prompt"][1]["content"] = "long " * 100
        rows, report = dpo.fit_pairs([a, b], Tokenizer(), 100)
        self.assertEqual([r["id"] for r in rows], [a["id"]])
        self.assertEqual(report["excluded_whole_pair_ids"], [b["id"]])
        self.assertEqual(report["prompts_truncated"], 0)
        self.assertEqual(set(report["lengths"]), {a["id"], b["id"]})

    def test_completions_end_with_the_templates_turn_end(self):
        rows, report = dpo.fit_pairs([pair()], Tokenizer(), 1000)
        self.assertEqual(report["completion_end_token"], "<END>")
        other = Tokenizer()
        other.turn_end = "<TURN>"               # the server would stop at a token the adapter never learned
        with self.assertRaisesRegex(ValueError, "other than the EOS"):
            dpo.fit_pairs([pair()], other, 1000)
        class Split(Tokenizer):                   # the EOS text encodes as plain bytes, not the EOS id
            def __call__(self, text, add_special_tokens=False):
                return {"input_ids": list(text.encode())}
        with self.assertRaisesRegex(ValueError, "one special token"):
            dpo.fit_pairs([pair()], Split(), 1000)

    def test_no_subset_if_full_roster_fits(self):
        rows = [pair(i) for i in range(250)]
        selected, report = dpo.choose_roster(rows, 500, dict(
            seconds_per_pair=1, evaluation_seconds=10, conversion_and_test_seconds=20))
        self.assertEqual(selected, rows)
        self.assertEqual(report["selected_pairs"], 250)

    def test_subset_is_seeded_and_independent_of_answer_quality(self):
        rows = [pair(i) for i in range(300)]
        measured = dict(seconds_per_pair=1, evaluation_seconds=10, conversion_and_test_seconds=20)
        a, report = dpo.choose_roster(rows, 300, measured)
        changed = copy.deepcopy(rows)
        for row in changed:
            row["chosen"] = "a completely different model answer"
        b, _ = dpo.choose_roster(changed, 300, measured)
        self.assertEqual([r["id"] for r in a], [r["id"] for r in b])
        self.assertTrue(200 <= len(a) < len(rows))
        self.assertLessEqual(report["selected_projected_seconds"], 300)
        with self.assertRaisesRegex(ValueError, "defer"):
            dpo.choose_roster(rows, 100, measured)

    def test_too_few_pairs_and_unapproved_seed_refused(self):
        measured = dict(seconds_per_pair=1, evaluation_seconds=1, conversion_and_test_seconds=1)
        with self.assertRaisesRegex(ValueError, "200"):
            dpo.choose_roster([pair(i) for i in range(199)], 1000, measured)
        with self.assertRaisesRegex(ValueError, "1831"):
            dpo.choose_roster([pair(i) for i in range(200)], 1000, measured, seed=42)

    def test_training_arguments_disable_all_truncation(self):
        args = dpo.dpo_arguments("/tmp/new-output")
        self.assertIsNone(args["max_length"])
        self.assertIsNone(args["max_prompt_length"])
        self.assertIsNone(args["max_completion_length"])
        self.assertTrue(args["precompute_ref_log_probs"])
        self.assertEqual((args["beta"], args["learning_rate"], args["num_train_epochs"], args["max_steps"]),
                         (.1, 1e-5, 1, -1))
        self.assertEqual(dpo.dpo_arguments("/tmp/new-output", True)["max_steps"], 3)

    def test_label_provenance_tampering_and_held_days_fail(self):
        root = Path(tempfile.mkdtemp(prefix="dpo-data-test-"))
        good = "The clerk sends the petition to the other counter before the office closes at noon"
        bad = "The clerk sends the petition to the other counter before the office closes at one"
        candidates = []
        for i in range(200):
            candidates.append(dict(id=f"shadow:35:{i}", source="shadow", day=35, step=i,
                messages=pair(i)["prompt"], earlier_thoughts=[], candidates=[
                    dict(seed=seed, raw=json.dumps({"thought": good if seed!=2718 else bad}),
                         answer={"thought": good if seed!=2718 else bad}, accepted=seed!=2718,
                         errors=[] if seed!=2718 else ["refused"])
                    for seed in (1831,2718,3141,4271)]))
        c = root/"candidates.jsonl"; p = root/"pairs.jsonl"
        c.write_bytes(b"".join((json.dumps(r)+"\n").encode() for r in candidates))
        self.assertEqual(decision_pairs.main(["--candidates",str(c),"--out",str(p)]),0)
        actual, receipt = dpo.validated_pairs(c,p,p.with_suffix(".stats.json"))
        self.assertEqual(len(actual), 200)
        p.write_bytes(p.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"digest"):
            dpo.validated_pairs(c,p,p.with_suffix(".stats.json"))
        legacy = root/"legacy.jsonl"
        self.assertEqual(decision_pairs.main(["--candidates",str(c),"--out",str(legacy),"--view","legacy"]),0)
        with self.assertRaisesRegex(ValueError,"revised labels only"):
            dpo.validated_pairs(c,legacy,legacy.with_suffix(".stats.json"))


if __name__ == "__main__":
    unittest.main()
