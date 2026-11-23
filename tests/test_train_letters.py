"""Tests for pc/train_letters.py on the CPU: a fake tokenizer and a fake backend stand in for torch and the model."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pc import train_letters as tl  # noqa: E402
from pc import restyle_round2 as r2  # noqa: E402


class Tok:
    """One token per character (its code plus one); EOS is 0; a BOS only if asked."""
    def __init__(self, bos=None):
        self.eos_token_id, self.bos_token_id = 0, bos
        self.seen_special = []

    def __call__(self, text, add_special_tokens=True):
        self.seen_special.append(add_special_tokens)
        return {"input_ids": [ord(c) + 1 for c in text]}


class Backend:
    """Stands in for TorchBackend. `losses` are the held-out values, one per evaluation pass (the last one repeats)."""
    def __init__(self, losses, tok=None):
        self.losses, self.tok = list(losses), tok or Tok()
        self.micro, self.steps, self.saved, self.evals_seen = [], [], [], []
        self.left_in_pass, self.held_total, self.pass_loss = 0, 0, None

    def load_tokenizer(self, args):
        return self.tok

    def load_model(self, args):
        self.loaded = True

    def train_micro(self, rows, divisor):
        self.micro.append(rows)
        return 1.5 * sum(tl.target_tokens(r) for r in rows)

    def optimizer_step(self, lr):
        self.steps.append(lr)

    def eval_nll(self, rows):
        if self.left_in_pass == 0:                               # a new evaluation pass begins
            self.pass_loss = self.losses.pop(0) if len(self.losses) > 1 else self.losses[0]
            self.left_in_pass = self.held_total
        self.left_in_pass -= len(rows)
        self.evals_seen.append(rows)
        n = sum(tl.target_tokens(r) for r in rows)
        return self.pass_loss * n, n

    def save(self, path):
        Path(path).mkdir(parents=True)
        (Path(path) / "adapter_model.safetensors").write_bytes(b"w")
        self.saved.append(Path(path).name)


def row(i, prompt=None, target=None):
    return {"id": "r%d" % i, "prompt": prompt or ("To a friend %d:\n\n" % i),
            "target": target or ("Dear friend, letter number %d, written at length." % i)}


def write(path, rows):
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def make_args(td, **kw):
    base = dict(base="fixture", train=str(Path(td) / "train.jsonl"), heldout=str(Path(td) / "held.jsonl"), out=str(Path(td) / "out"),
                rank=16, alpha=32, lr=1e-4, epochs=3, batch=1, accum=2, seq=1536, save_steps=2, eval_steps=2, patience=3,
                goldfish=False, goldfish_k=4, goldfish_context=13, seed=3407, max_steps=None, text_only=False, loss_target_gib=None)
    base.update(kw)
    return SimpleNamespace(**base)


def data(td, n_train=4, n_held=2):
    write(Path(td) / "train.jsonl", [row(i) for i in range(n_train)])
    write(Path(td) / "held.jsonl", [row(100 + i) for i in range(n_held)])


def run(args, losses, tok=None):
    backend = Backend(losses, tok)
    backend.held_total = len(tl.read_rows(args.heldout))
    result = tl.train(args, backend, say=lambda *a: None)
    return result, backend


class ExampleTest(unittest.TestCase):
    def test_labels_are_masked_on_the_prompt_and_eos_is_added_once(self):
        tok = Tok()
        got = tl.encode_row(tok, row(1, "Hi:\n\n", "Dear"), 100)
        prompt, target = [ord(c) + 1 for c in "Hi:\n\n"], [ord(c) + 1 for c in "Dear"]
        self.assertEqual(got["input_ids"], prompt + target + [0])
        self.assertEqual(got["labels"], [-100] * len(prompt) + target + [0])
        self.assertEqual(got["input_ids"].count(0), 1)
        self.assertEqual(got["attention_mask"], [1] * len(got["input_ids"]))
        self.assertEqual(set(tok.seen_special), {False})

    def test_a_bos_is_put_in_once_and_masked(self):
        got = tl.encode_row(Tok(bos=7), row(1, "Hi\n\n", "Dear"), 100)
        self.assertEqual(got["input_ids"][0], 7)
        self.assertEqual(got["input_ids"].count(7), 1)
        self.assertEqual(got["labels"][0], -100)

    def test_over_long_rows_are_left_out_whole_and_never_cut(self):
        rows = [row(1, "Hi\n\n", "x" * 10), row(2, "Hi\n\n", "x" * 200)]
        kept, left = tl.encode_rows(Tok(), rows, 50)
        self.assertEqual([k["id"] for k in kept], ["r1"])
        self.assertEqual(left, [{"id": "r2", "tokens": 4 + 200 + 1}])

    def test_the_five_percent_rule(self):
        self.assertFalse(tl.too_many_excluded(1, 20))
        self.assertTrue(tl.too_many_excluded(2, 20))

    def test_goldfish_masks_training_labels_with_the_shared_function(self):
        target = "".join(chr(97 + i % 26) + chr(65 + i % 7) for i in range(120))
        enc = tl.encode_row(Tok(), row(1, "Hi\n\n", target), 1000)
        masked = tl.with_goldfish([enc], 4, 13)[0]
        self.assertEqual(masked["labels"], r2.goldfish_labels(enc["input_ids"], enc["labels"], 4, 13))
        self.assertIn(-100, masked["labels"][4 + 13:])
        self.assertEqual(masked["input_ids"], enc["input_ids"])


class ScheduleTest(unittest.TestCase):
    def test_warmup_then_cosine(self):
        self.assertAlmostEqual(tl.lr_at(0, 100, 1.0), 1 / 5)
        self.assertAlmostEqual(tl.lr_at(4, 100, 1.0), 1.0)
        self.assertAlmostEqual(tl.lr_at(5, 100, 1.0), 1.0)
        self.assertLess(tl.lr_at(60, 100, 1.0), tl.lr_at(30, 100, 1.0))
        self.assertLess(tl.lr_at(99, 100, 1.0), 0.01)

    def test_steps_and_cap(self):
        self.assertEqual(tl.total_steps(10, 1, 4, 3), 9)
        self.assertEqual(tl.total_steps(10, 1, 4, 3, 3), 3)


class RunTest(unittest.TestCase):
    def test_goldfish_is_on_training_labels_and_not_on_heldout(self):
        with tempfile.TemporaryDirectory() as td:
            target = "".join(chr(97 + i % 26) + chr(65 + (i * 3) % 11) for i in range(150))
            write(Path(td) / "train.jsonl", [row(i, target=target + str(i)) for i in range(2)])
            write(Path(td) / "held.jsonl", [row(100, target=target + "held")])
            _, backend = run(make_args(td, goldfish=True, max_steps=1, eval_steps=1, save_steps=1), [1.0])
            for rows in backend.micro:
                for r in rows:
                    self.assertIn(-100, r["labels"][len(row(0)["prompt"]) + 13 + 5:])
            held_labels = backend.evals_seen[0][0]["labels"]
            self.assertEqual(held_labels, tl.encode_row(Tok(), row(100, target=target + "held"), 1536)["labels"])

    def test_without_goldfish_training_labels_are_whole(self):
        with tempfile.TemporaryDirectory() as td:
            data(td)
            _, backend = run(make_args(td, max_steps=1, eval_steps=1, save_steps=1), [1.0])
            for rows in backend.micro:
                for r in rows:
                    self.assertEqual(r["labels"], [-100] * len(row(0)["prompt"]) + r["input_ids"][len(row(0)["prompt"]):])

    def test_early_stop_after_patience_flat_evaluations(self):
        with tempfile.TemporaryDirectory() as td:
            data(td, 8, 2)
            result, _ = run(make_args(td, epochs=10, patience=2), [1.0, 0.8, 0.9, 0.85, 0.7])
            self.assertEqual([e["step"] for e in result["evaluations"]], [2, 4, 6, 8])
            self.assertEqual(result["steps_run"], 8)
            self.assertEqual(result["best_step"], 4)
            self.assertIn("early stop", result["stopped"])

    def test_checkpoints_at_save_steps_and_a_final_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            data(td, 4, 2)
            result, backend = run(make_args(td, epochs=3, save_steps=3, eval_steps=2, patience=99), [1.0, 0.9, 0.8])
            self.assertEqual(result["steps_run"], 6)
            self.assertEqual(backend.saved, ["checkpoint-3", "checkpoint-6", "final"])
            self.assertTrue((Path(td) / "out/final/adapter_model.safetensors").exists())

    def test_result_picks_the_lowest_heldout_loss_and_records_everything(self):
        with tempfile.TemporaryDirectory() as td:
            data(td, 4, 2)
            args = make_args(td, epochs=3, patience=99, save_steps=2, eval_steps=2)
            run(args, [0.9, 0.6, 0.7])
            written = json.loads((Path(td) / "out/RESULT.json").read_text())
            self.assertEqual(written["best_step"], 4)
            self.assertEqual(written["best_checkpoint"], "checkpoint-4")
            self.assertAlmostEqual(written["best_heldout_loss"], 0.6)
            self.assertEqual(written["examples_used"], {"train": 4, "heldout": 2})
            self.assertEqual(written["examples_excluded"], {"train": [], "heldout": []})
            self.assertEqual(written["input_sha256"]["train"], tl.filehash(args.train))
            self.assertEqual(written["input_sha256"]["heldout"], tl.filehash(args.heldout))
            self.assertEqual(written["hyperparameters"]["rank"], 16)
            lines = [json.loads(x) for x in (Path(td) / "out/TRAINING-LOG.jsonl").read_text().splitlines()]
            self.assertEqual(len([x for x in lines if "train_loss" in x]), written["steps_run"])
            self.assertEqual([x["step"] for x in lines if "heldout_loss" in x], [2, 4, 6])
            self.assertTrue(all({"step", "train_loss", "lr", "seconds"} <= set(x) for x in lines if "train_loss" in x))

    def test_max_steps_caps_the_run_and_still_evaluates_at_the_end(self):
        with tempfile.TemporaryDirectory() as td:
            data(td, 4, 2)
            result, backend = run(make_args(td, max_steps=3, eval_steps=2, save_steps=50), [1.0, 0.9])
            self.assertEqual((result["steps_run"], result["stopped"]), (3, "--max-steps reached"))
            self.assertEqual([e["step"] for e in result["evaluations"]], [2, 3])
            self.assertEqual(len(backend.steps), 3)
            self.assertEqual(backend.saved, ["final"])

    def test_an_existing_out_directory_is_refused_before_anything_loads(self):
        with tempfile.TemporaryDirectory() as td:
            data(td)
            (Path(td) / "out").mkdir()
            backend = Backend([1.0])
            with self.assertRaises(SystemExit):
                tl.train(make_args(td), backend, say=lambda *a: None)
            self.assertFalse(hasattr(backend, "loaded"))

    def test_too_many_long_rows_stop_the_run_before_the_model_loads(self):
        with tempfile.TemporaryDirectory() as td:
            write(Path(td) / "train.jsonl", [row(i) for i in range(18)] + [row(50, target="x" * 5000), row(51, target="y" * 5000)])
            write(Path(td) / "held.jsonl", [row(100)])
            backend = Backend([1.0])
            with self.assertRaisesRegex(SystemExit, "longer than"):
                tl.train(make_args(td, seq=200), backend, say=lambda *a: None)
            self.assertFalse(hasattr(backend, "loaded"))
            self.assertFalse((Path(td) / "out").exists())

    def test_one_long_row_in_twenty_is_left_out_and_reported(self):
        with tempfile.TemporaryDirectory() as td:
            write(Path(td) / "train.jsonl", [row(i) for i in range(19)] + [row(50, target="x" * 5000)])
            write(Path(td) / "held.jsonl", [row(100)])
            result, _ = run(make_args(td, seq=200, max_steps=1, eval_steps=1), [1.0])
            self.assertEqual(result["examples_excluded"]["train"], [{"id": "r50", "tokens": len("To a friend 50:\n\n") + 5000 + 1}])
            self.assertEqual(result["examples_used"]["train"], 19)


class CheckDataTest(unittest.TestCase):
    def check(self, train, held, tokenizer=None):
        with tempfile.TemporaryDirectory() as td:
            write(Path(td) / "t.jsonl", train)
            write(Path(td) / "h.jsonl", held)
            out = []
            ok = tl.check_data(Path(td) / "t.jsonl", Path(td) / "h.jsonl", tokenizer, 1536, say=out.append)
            return ok, "\n".join(out)

    def test_good_files_pass_and_say_that_tokens_were_not_checked(self):
        ok, text = self.check([row(1), row(2)], [row(3)])
        self.assertTrue(ok)
        self.assertIn("2 train rows, 1 held-out rows", text)
        self.assertIn("NOT checked", text)

    def test_a_tokenizer_turns_the_length_check_on(self):
        ok, text = self.check([row(1), row(2)], [row(3)], Tok())
        self.assertTrue(ok)
        self.assertIn("fit in 1536 tokens", text)

    def test_duplicate_id_is_caught(self):
        ok, text = self.check([row(1), row(1, target="another")], [row(3)])
        self.assertFalse(ok)
        self.assertIn("second row with id", text)

    def test_an_id_in_both_files_is_caught(self):
        ok, text = self.check([row(1)], [row(1, target="another letter")])
        self.assertFalse(ok)
        self.assertIn("in both files", text)

    def test_a_target_in_both_files_is_caught(self):
        ok, text = self.check([row(1, target="the same letter")], [row(2, target="the same letter")])
        self.assertFalse(ok)
        self.assertIn("target(s) are in both files", text)

    def test_missing_or_empty_fields_and_a_prompt_without_a_blank_line(self):
        for bad in ({"id": "a", "prompt": "x\n\n"}, {"id": "a", "prompt": "x\n\n", "target": "  "}, {"id": "a", "prompt": "x\n", "target": "y"}):
            ok, _ = self.check([bad], [row(3)])
            self.assertFalse(ok, bad)

    def test_main_check_data_needs_no_model_and_returns_a_status(self):
        with tempfile.TemporaryDirectory() as td:
            data(td)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tl.main(["--check-data", "--train", str(Path(td) / "train.jsonl"), "--heldout", str(Path(td) / "held.jsonl")]), 0)
            self.assertNotIn("torch", sys.modules)
            self.assertNotIn("unsloth", sys.modules)

    def test_defaults(self):
        a = tl.parser().parse_args(["--train", "t", "--heldout", "h"])
        self.assertEqual((a.rank, a.alpha, a.lr, a.epochs, a.batch, a.accum, a.seq, a.save_steps, a.eval_steps, a.patience, a.seed),
                         (16, 32, 1e-4, 3, 1, 8, 1536, 50, 50, 3, 3407))


if __name__ == "__main__":
    unittest.main()
