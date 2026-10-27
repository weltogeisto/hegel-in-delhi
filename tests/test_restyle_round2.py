import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from pc import train_hegel as th
from pc import restyle_round2 as r2
from tools import hegelizer_round2 as data2
from tests.test_hegelizer_round2 import unit, result, original, version


def data_folder(folder, train=2, held=20):
    units, good = [], []
    for i in range(train + held):
        u = dict(unit(i, "train" if i < train else "held"), work="work" + str(i % 3))
        row = result(i)
        row.update(u)
        units.append(u)
        good.append(row)
    (folder / data2.UNITS).write_bytes(b"".join(data2.json_bytes(u) for u in units))
    (folder / data2.DONE).write_bytes(b"".join(data2.json_bytes(r) for r in good))
    return folder


class GoldfishTest(unittest.TestCase):
    def test_deterministic_mask_keeps_inputs_prompt_and_first_thirteen_targets(self):
        ids = list(range(120))
        labels = [-100] * 20 + ids[20:]
        masked = r2.goldfish_labels(ids, labels)
        self.assertEqual(masked[:33], labels[:33])
        self.assertEqual(masked, r2.goldfish_labels(ids, labels))
        self.assertTrue(any(x == -100 for x in masked[33:]))
        self.assertEqual(ids, list(range(120)))

    def test_same_local_target_context_has_same_mask_after_another_prompt(self):
        targets = list(range(100, 300))
        a = r2.goldfish_labels([1, 2] + targets, [-100] * 2 + targets)
        b = r2.goldfish_labels([8, 7, 6, 5] + targets, [-100] * 4 + targets)
        self.assertEqual(a[2:], b[4:])

    def test_masking_is_approximately_a_quarter_and_does_not_mask_padding(self):
        ids = list(range(2000))
        labels = ids[:-3] + [-100] * 3
        got = r2.goldfish_labels(ids, labels)
        share = sum(x == -100 for x in got[13:-3]) / len(got[13:-3])
        self.assertTrue(0.20 < share < 0.30, share)
        self.assertEqual(got[-3:], [-100] * 3)

    def test_k_and_context_are_options_and_bad_shapes_stop(self):
        ids = list(range(100))
        self.assertNotEqual(r2.goldfish_labels(ids, ids, 4), r2.goldfish_labels(ids, ids, 8))
        for args in [(ids, ids, 1, 13), (ids, ids, 4, 0), (ids, ids[:-1], 4, 13)]:
            with self.assertRaises(ValueError):
                r2.goldfish_labels(*args)

    def test_row_mask_changes_only_labels_and_leaves_original_row_intact(self):
        row = {"input_ids": list(range(100)), "labels": list(range(100)), "attention_mask": [1] * 100}
        got = r2.mask_rows([row])[0]
        self.assertEqual(got["input_ids"], row["input_ids"])
        self.assertEqual(got["attention_mask"], row["attention_mask"])
        self.assertEqual(row["labels"], list(range(100)))


class DataTest(unittest.TestCase):
    def test_two_versions_expand_and_held_selection_has_twenty_unique_full_units(self):
        with tempfile.TemporaryDirectory() as td:
            rows, gate = r2.load_data(data_folder(Path(td)))
            self.assertTrue(gate["passed"])
            self.assertEqual((len(rows["train"]), len(rows["held"])), (4, 40))
            held = r2.held_units(rows["held"])
            self.assertEqual(len({r["parent_id"] for r in held}), 20)
            self.assertTrue(all(r["variant"] == 1 and r["kind"] == "full" for r in held))
            self.assertEqual(held, r2.held_units(rows["held"]))

    def test_fewer_than_twenty_held_units_never_shrinks_the_eval_cohort(self):
        with tempfile.TemporaryDirectory() as td:
            rows, _ = r2.load_data(data_folder(Path(td), held=19))
            with self.assertRaises(ValueError):
                r2.held_units(rows["held"])

    def test_parent_split_leak_and_non_authentic_short_span_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder = data_folder(Path(td))
            units = data2.strict_rows(folder / data2.UNITS)
            good = data2.strict_rows(folder / data2.DONE)
            units[0]["parent_id"] = units[-1]["id"]
            good[0]["parent_id"] = units[-1]["id"]
            (folder / data2.UNITS).write_bytes(b"".join(data2.json_bytes(x) for x in units))
            (folder / data2.DONE).write_bytes(b"".join(data2.json_bytes(x) for x in good))
            with self.assertRaisesRegex(ValueError, "split"):
                r2.load_data(folder)


class SelectionTest(unittest.TestCase):
    def row(self, step=100, recall=0, delta=0.34, loss=1.2):
        return {"step": step, "n": 20, "recall_beyond_input": recall, "delta": delta, "heldout_loss": loss}

    def test_machine_selection_uses_recall_then_delta_then_loss_then_earlier_step(self):
        rows = [self.row(100, recall=1, delta=0.30), self.row(200, delta=0.35, loss=1),
                self.row(300, delta=0.34, loss=1.3), self.row(400, delta=0.34, loss=1.2),
                self.row(500, delta=0.34, loss=1.2)]
        self.assertEqual(r2.best_checkpoint(rows)["step"], 400)

    def test_missing_and_nonfinite_numbers_cannot_select_a_checkpoint(self):
        for key, value in [("delta", None), ("heldout_loss", float("nan")), ("recall_beyond_input", 21)]:
            row = self.row()
            row[key] = value
            with self.assertRaises(ValueError):
                r2.checkpoint_key(row)


class EvaluationTest(unittest.TestCase):
    def held(self):
        return [dict(unit(i, "held"), plain=version(), id="unit" + str(i), parent_id="parent" + str(i)) for i in range(20)]

    def test_all_twenty_are_measured_once_and_replay_uses_saved_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            ev = r2.MachineEvaluator(td, self.held(), lambda text: 0.34)
            fetch = mock.Mock(return_value=version("reply"))
            row = ev.evaluate(100, 1.2, fetch)
            self.assertEqual((row["n"], row["recall_beyond_input"]), (20, 0))
            self.assertEqual(fetch.call_count, 20)
            self.assertEqual(ev.evaluate(100, 1.2, fetch), row)
            self.assertEqual(fetch.call_count, 20)

    def test_recall_counts_only_target_runs_not_already_in_the_plain_input(self):
        held = self.held()
        held[0]["plain"] = original()
        with tempfile.TemporaryDirectory() as td:
            ev = r2.MachineEvaluator(td, held, lambda text: 0.34)
            row = ev.evaluate(100, 1.2, lambda *args: original())
            self.assertEqual(row["recall_beyond_input"], 19)

    def test_partial_generation_is_preserved_and_never_repeated(self):
        with tempfile.TemporaryDirectory() as td:
            ev = r2.MachineEvaluator(td, self.held(), lambda text: 0.34)
            fetch = mock.Mock(side_effect=KeyboardInterrupt)
            with self.assertRaises(KeyboardInterrupt):
                ev.evaluate(100, 1.2, fetch)
            with self.assertRaisesRegex(ValueError, "without an end"):
                ev.evaluate(100, 1.2, fetch)
            self.assertEqual(fetch.call_count, 1)

    def test_changed_saved_output_stops_selection_without_a_model_call(self):
        with tempfile.TemporaryDirectory() as td:
            ev = r2.MachineEvaluator(td, self.held(), lambda text: 0.34)
            fetch = mock.Mock(return_value=version("reply"))
            ev.evaluate(100, 1.2, fetch)
            (Path(td) / "step-100/0.response.json").write_text("{}")
            with self.assertRaises(ValueError):
                ev.evaluate(100, 1.2, fetch)
            self.assertEqual(fetch.call_count, 20)

    def test_missing_style_reference_does_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            ev = r2.MachineEvaluator(td, self.held(), lambda text: None)
            with self.assertRaises(ValueError):
                ev.evaluate(100, 1.2, lambda *args: version())


class SamplerTest(unittest.TestCase):
    def test_generation_restores_training_mode_and_rng(self):
        class Tensor:
            shape = (1, 4)
            def to(self, device): return self
        class Output:
            def __getitem__(self, index): return [4, 5, 0]
        class Tok:
            eos_token_id = 0
            def apply_chat_template(self, messages, **kwargs): return "prompt"
            def __call__(self, text, **kwargs): return {"input_ids": Tensor(), "attention_mask": Tensor()}
            def decode(self, ids, **kwargs): return "saved answer"
        class Model:
            training = True
            def parameters(self): return iter([SimpleNamespace(device=SimpleNamespace(type="cpu", index=None))])
            def eval(self): self.training = False
            def train(self, state): self.training = state
            def generate(self, **kwargs):
                if self.training: raise AssertionError("generation must be in evaluation mode")
                return Output()
        torch = SimpleNamespace(seed=99)
        @contextlib.contextmanager
        def fork(**kwargs):
            before = torch.seed
            try: yield
            finally: torch.seed = before
        torch.random = SimpleNamespace(fork_rng=fork)
        torch.inference_mode = contextlib.nullcontext
        torch.manual_seed = lambda seed: setattr(torch, "seed", seed)
        model = Model()
        out = r2.generate_for_model(model, Tok(), "plain", 1831, 100, torch)
        self.assertEqual((out["text"], out["generated_tokens"], out["finish_reason"]), ("saved answer", 3, "stop"))
        self.assertTrue(model.training)
        self.assertEqual(torch.seed, 99)


class OptionsTest(unittest.TestCase):
    def parse(self, *flags):
        seen = {}
        with mock.patch.object(th, "train", side_effect=lambda a: seen.update(vars(a))):
            th.main(["--base", "local", *flags])
        return seen

    def test_legacy_defaults_stay_and_round_two_uses_rank16_batch8_steps100(self):
        old = self.parse("--phase", "restyle")
        new = self.parse("--phase", "restyle", "--round-two", "--goldfish")
        self.assertEqual((old["rank"], old["accum"], old["epochs_restyle"]), (32, 16, 2))
        self.assertEqual((new["rank"], new["alpha"], new["batch"] * new["accum"], new["eval_steps"]), (16, 32, 8, 100))
        self.assertEqual((new["goldfish_k"], new["goldfish_context"], new["epochs_restyle"]), (4, 13, 1))
        self.assertEqual(self.parse("--phase", "restyle", "--round-two", "--rank=32")["rank"], 32)

    def test_wrong_phase_batch_or_existing_dryrun_resume_cannot_start(self):
        for flags in [("--round-two",), ("--phase", "restyle", "--round-two", "--batch", "0"),
                      ("--phase", "restyle", "--round-two", "--batch", "3"),
                      ("--phase", "restyle", "--round-two", "--accum", "16"),
                      ("--phase", "restyle", "--round-two", "--dry-run", "--resume"),
                      ("--phase", "restyle", "--goldfish")]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.parse(*flags)

    def test_existing_output_is_preserved_before_loading_a_model(self):
        with tempfile.TemporaryDirectory() as td:
            folder = data_folder(Path(td))
            out = Path(td) / "old"
            out.mkdir()
            (out / "keep").write_bytes(b"old")
            args = argparse.Namespace(data=folder, out=out, dry_run=True, resume=False)
            api = mock.Mock()
            with self.assertRaises(SystemExit):
                r2.train(args, api)
            self.assertEqual((out / "keep").read_bytes(), b"old")
            api.load_model.assert_not_called()


class TrainingWiringTest(unittest.TestCase):
    def test_step_evaluations_export_the_best_measured_adapter_not_the_last(self):
        class Tok:
            eos_token_id = 0
            def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False, enable_thinking=False):
                text = "".join(m["role"] + ":" + m["content"] + "<end>\n" for m in messages)
                return text + ("assistant:" if add_generation_prompt else "")
            def __call__(self, text, **kwargs):
                return {"input_ids": [ord(c) for c in text]}
            def save_pretrained(self, folder):
                (Path(folder) / "tokenizer.json").write_text("fixture")
        class Model:
            step = 0
            def save_pretrained(self, folder):
                folder = Path(folder)
                folder.mkdir(parents=True, exist_ok=False)
                (folder / "adapter_model.safetensors").write_bytes(("weights" + str(self.step)).encode())
                (folder / "adapter_config.json").write_text("{}")
        model, tok, seen = Model(), Tok(), {}
        class Trainer:
            def __init__(self, **kwargs):
                seen.update(kwargs)
                self.args, self.callbacks = kwargs["args"], kwargs["callbacks"]
                self.state = SimpleNamespace(global_step=0)
            def train(self, resume_from_checkpoint=None):
                self.assert_not_used = resume_from_checkpoint
                for step in [100, 200]:
                    model.step = self.state.global_step = step
                    model.save_pretrained(Path(self.args.output_dir) / ("checkpoint-" + str(step)))
                    for callback in self.callbacks:
                        callback.on_evaluate(self.args, self.state, None, metrics={"eval_loss": 1.2 if step == 100 else 1.0})
            def evaluate(self):
                raise AssertionError("terminal evaluation was already recorded; do not replay it")
        engine = SimpleNamespace(Trainer=Trainer, TrainerCallback=object,
                                 TrainingArguments=lambda **kw: SimpleNamespace(**kw),
                                 Dataset=SimpleNamespace(from_list=lambda rows: rows),
                                 DataCollatorForSeq2Seq=lambda **kw: kw,
                                 get_last_checkpoint=lambda path: None, torch=None)
        with tempfile.TemporaryDirectory() as td:
            folder = data_folder(Path(td))
            out = Path(td) / "adapter"
            args = argparse.Namespace(data=folder, out=out, dry_run=False, resume=False, base="fixture",
                rank=16, alpha=32, batch=1, accum=8, lr_restyle=2e-4, epochs_restyle=1,
                seq_restyle=4096, seed=3407, goldfish=True, goldfish_k=4, goldfish_context=13,
                eval_steps=100, max_steps_restyle=200)
            fetch = mock.Mock(return_value=version("answer"))
            with mock.patch.object(th, "load_model", return_value=(model, tok)), contextlib.redirect_stdout(io.StringIO()):
                report = r2.train(args, th, engine=engine, generate=fetch,
                                  delta_fn=lambda text: 0.34 if model.step == 100 else 0.35)
            self.assertEqual(report["selection"]["step"], 100)
            self.assertEqual((out / "adapter_model.safetensors").read_bytes(), b"weights100")
            self.assertEqual(fetch.call_count, 40)
            self.assertEqual(len(seen["eval_dataset"]), 20)
            self.assertEqual((seen["args"].eval_steps, seen["args"].save_steps), (100, 100))
            self.assertIsNone(seen["args"].save_total_limit)
            self.assertEqual(seen["args"].per_device_train_batch_size * seen["args"].gradient_accumulation_steps, 8)
            self.assertTrue((out / "work/restyle2/checkpoint-200/adapter_model.safetensors").exists())
            self.assertEqual(len(report["evaluations"]), 2)


if __name__ == "__main__":
    unittest.main()
