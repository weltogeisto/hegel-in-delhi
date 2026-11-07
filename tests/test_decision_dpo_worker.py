import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pc import decision_dpo_worker as worker
from tests.test_decision_dpo_data import Tokenizer, pair


class Dataset(list):
    @classmethod
    def from_list(cls, rows):
        return cls(rows)

    @property
    def column_names(self):
        return list(self[0]) if self else []


class Processor(Tokenizer):
    def save_pretrained(self, path):
        (Path(path) / "tokenizer.json").write_text('{"synthetic":true}')


class Trainer:
    is_peft_model = True
    ref_model = None
    missing_reference = False

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.state = SimpleNamespace(global_step=0, epoch=0.0)

    def get_train_dataloader(self):
        if not self.missing_reference:
            self.train_dataset = Dataset([dict(r, ref_chosen_logps=-1., ref_rejected_logps=-2.)
                                          for r in self.train_dataset])
        return []

    def get_eval_dataloader(self):
        self.eval_dataset = Dataset([dict(r, ref_chosen_logps=-1., ref_rejected_logps=-2.)
                                     for r in self.eval_dataset])
        return []

    def train(self):
        root = Path(self.args.output_dir).parents[1]
        if not all((root / ("REFERENCE-" + n + ".json")).exists() for n in ("train", "eval")):
            raise AssertionError("optimizer ran before saved references")
        for n in range(3):
            for cb in self.callbacks:
                cb.on_step_begin(self.args, self.state, None)
            self.state.global_step = n + 1
            for cb in self.callbacks:
                cb.on_step_end(self.args, self.state, None)
            if n == 1:
                self.evaluate()
        self.state.epoch = .12

    def evaluate(self, *args, **kwargs):
        return {"eval_loss": .5}

    def save_model(self, path):
        (Path(path) / "adapter_model.safetensors").write_bytes(b"synthetic adapter, not a model")


class WorkerTest(unittest.TestCase):
    def root(self, allowed=True, stamp=None):
        root = Path(tempfile.mkdtemp(prefix="dpo-worker-test-"))
        (root / "admission").mkdir()
        (root / "admission/ADMISSION.json").write_text(json.dumps(
            dict(allowed=allowed, before_ml_import=True,
                 utc=stamp or datetime.now(timezone.utc).isoformat())))
        return root

    def config(self, root):
        return dict(run_dir=str(root), candidates="fake", pairs="fake", pair_stats="fake",
                    base_model="synthetic", length_cap=4096, dry_run=True)

    def engine(self, missing=False):
        trainer = type("FakeTrainer", (Trainer,), dict(missing_reference=missing))
        cuda = SimpleNamespace(synchronize=lambda: None, empty_cache=lambda: None,
                               max_memory_reserved=lambda: 1000, max_memory_allocated=lambda: 500)
        return SimpleNamespace(torch=SimpleNamespace(cuda=cuda), Dataset=Dataset,
                               Callback=object, Config=lambda **kw: SimpleNamespace(**kw),
                               Trainer=trainer, load_model=lambda args: (object(), Processor()))

    def test_denied_or_stale_admission_precedes_runtime_import(self):
        for root in (self.root(allowed=False), self.root(stamp="2000-01-01T00:00:00+00:00")):
            called = []
            with patch.object(worker.data_api, "validated_pairs", return_value=([], {})):
                with self.assertRaisesRegex(RuntimeError, "admission"):
                    worker.train(self.config(root), lambda: None, lambda: None,
                                 engine_factory=lambda: called.append("ML"))
            self.assertEqual(called, [])
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("unsloth", sys.modules)

    def test_fake_full_worker_records_references_before_steps_and_evaluation(self):
        root = self.root()
        with patch.object(worker.data_api, "validated_pairs",
                          return_value=([pair(i) for i in range(200)], {"synthetic": True})):
            report = worker.train(self.config(root), lambda: None, lambda: None, self.engine)
        self.assertEqual(report["steps"], 3)
        log = [json.loads(line) for line in (root/"timing.jsonl").read_text().splitlines()]
        names = [r["event"] for r in log]
        self.assertLess(names.index("reference_end"), names.index("step_begin"))
        self.assertEqual(names.count("step"), 3)
        self.assertEqual(names.count("evaluate_end"), 1)
        self.assertTrue(report["diagnostic_eval_not_quality"])
        self.assertEqual(len(json.loads((root/"REFERENCE-train.json").read_bytes())["probabilities"]),200)

    def test_missing_reference_table_stops_before_optimizer(self):
        root = self.root()
        with patch.object(worker.data_api, "validated_pairs",
                          return_value=([pair(i) for i in range(200)], {})):
            with self.assertRaisesRegex(RuntimeError,"not precomputed"):
                worker.train(self.config(root), lambda: None, lambda: None, lambda: self.engine(True))
        log = [json.loads(line) for line in (root/"timing.jsonl").read_text().splitlines()]
        self.assertFalse(any(r["event"] == "step_begin" for r in log))
        self.assertFalse((root/"training/adapter_model.safetensors").exists())


if __name__ == "__main__":
    unittest.main()
