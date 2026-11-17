"""DPO worker for Training 3; called only by the reviewed lifecycle launcher.

Admission must be performed by an exited stdlib-only child before this ML process.
No imports of torch, Transformers, TRL or Unsloth occur at module load time.
"""
import gc
import json
import math
import os
import time
from pathlib import Path
from types import SimpleNamespace

from pc import decision_dpo_data as data_api
from pc.run_training1 import epoch, filehash, read, utc, write_new


def check_admission(root, now=None):
    proof = read(Path(root) / "admission" / "ADMISSION.json")
    age = (time.time() if now is None else now) - epoch(proof["utc"])
    if not proof.get("allowed") or not proof.get("before_ml_import") or not 0 <= age <= 120:
        raise RuntimeError("successful fresh pre-import admission required")


def validate_runtime():
    import importlib.metadata as metadata
    expected = read(Path(__file__).with_name("training3-runtime.json"))
    for name, version in expected["versions"].items():
        if metadata.version(name) != version:
            raise RuntimeError("reviewed runtime version changed: " + name)
    dist = metadata.distribution("trl")
    for relative, sha256 in expected["source_hashes"].items():
        if filehash(dist.locate_file(relative)) != sha256:
            raise RuntimeError("reviewed DPO implementation changed: " + relative)
    return expected


def runtime():
    validate_runtime()
    import unsloth  # must patch before all training-library imports
    import torch
    from datasets import Dataset
    from transformers import TrainerCallback
    from trl import DPOConfig, DPOTrainer
    from pc.train_hegel import load_model
    return SimpleNamespace(torch=torch, Dataset=Dataset, Callback=TrainerCallback,
                           Config=DPOConfig, Trainer=DPOTrainer, load_model=load_model)


def train(data, verify, check_time, engine_factory=runtime):
    root = Path(data["run_dir"])
    verify()
    pairs, provenance = data_api.validated_pairs(data["candidates"], data["pairs"], data["pair_stats"])
    check_admission(root)
    # No torch/Unsloth import may precede the call above.
    os.environ["UNSLOTH_CE_LOSS_TARGET_GB"] = "0.125"
    engine = engine_factory()
    start = time.monotonic()
    args = SimpleNamespace(base=data["base_model"], phase="decision", bf16=False,
        seq_restyle=data["length_cap"], seq_corpus=data["length_cap"], seq_format=data["length_cap"],
        rank=16, alpha=32, seed=1831, text_only=True, loss_target_gib=.125)
    model, processor = engine.load_model(args)
    tok = getattr(processor, "tokenizer", processor)
    loaded_seconds = time.monotonic() - start
    rows, length_report = data_api.fit_pairs(pairs, tok, data["length_cap"])
    write_new(root / "LENGTH-REPORT.json", length_report)
    if len(rows) < data_api.MIN_PAIRS:
        raise RuntimeError("fewer than 200 complete untruncated pairs; no trainer started")
    selected = data.get("selected_ids")
    if selected is not None:
        if len(selected) != len(set(selected)) or not set(selected) <= {r["id"] for r in rows}:
            raise RuntimeError("selected roster is not in the complete length-filtered data")
        rows = [r for r in rows if r["id"] in set(selected)]
        if [r["id"] for r in rows] != selected or len(rows) < data_api.MIN_PAIRS:
            raise RuntimeError("frozen roster order or size differs")
    write_new(root / "TRAINING-ROSTER.json", dict(ids=[r["id"] for r in rows], provenance=provenance,
                                                recipe=data_api.RECIPE, length_cap=data["length_cap"]))
    torch = engine.torch
    state = {}
    timing = root / "timing.jsonl"

    def emit(kind, **fields):
        with timing.open("ab") as stream:
            stream.write((json.dumps(dict(event=kind, utc=utc(), unix=time.time(), **fields)) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())

    class Timing(engine.Callback):
        def on_step_begin(self, args, trainer_state, control, **kwargs):
            verify()
            check_time()
            torch.cuda.synchronize()
            state["step_start"] = time.monotonic()
            emit("step_begin", step=trainer_state.global_step + 1)

        def on_step_end(self, args, trainer_state, control, **kwargs):
            torch.cuda.synchronize()
            emit("step", step=trainer_state.global_step, seconds=time.monotonic() - state["step_start"],
                 peak_reserved=torch.cuda.max_memory_reserved(), peak_allocated=torch.cuda.max_memory_allocated())
            return control

    class MeasuredTrainer(engine.Trainer):
        def evaluate(self, *args, **kwargs):
            check_time()
            began = time.monotonic()
            emit("evaluate_begin", step=self.state.global_step)
            try:
                return super().evaluate(*args, **kwargs)
            finally:
                gc.collect()
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                emit("evaluate_end", step=self.state.global_step, seconds=time.monotonic() - began)

    out = root / "training"
    out.mkdir(parents=True, exist_ok=False)
    config = engine.Config(**data_api.dpo_arguments(out / "checkpoints", data["dry_run"]))
    # Profiling loss only: no quality claim or checkpoint selection uses these.
    eval_rows = rows[:8]
    eval_ids = [r["id"] for r in eval_rows]
    strip_id = lambda row: {k: row[k] for k in ("prompt", "chosen", "rejected")}
    trainer = MeasuredTrainer(model=model, ref_model=None, args=config,
        train_dataset=engine.Dataset.from_list([strip_id(r) for r in rows]),
        eval_dataset=engine.Dataset.from_list([strip_id(r) for r in eval_rows]),
        processing_class=tok, callbacks=[Timing()])
    if not getattr(trainer, "is_peft_model", False) or trainer.ref_model is not None:
        raise RuntimeError("DPO requires the frozen base with adapter-disabled reference; no second model")
    # Both reference tables are computed before the first optimizer step.
    reference_start = time.monotonic()
    emit("reference_begin", pairs=len(rows), evaluation_pairs=len(eval_rows))
    trainer.get_train_dataloader()
    trainer.get_eval_dataloader()
    for name, dataset in (("train", trainer.train_dataset), ("eval", trainer.eval_dataset)):
        if not {"ref_chosen_logps", "ref_rejected_logps"} <= set(dataset.column_names):
            raise RuntimeError("reference probabilities were not precomputed")
        values = [dict(chosen=float(r["ref_chosen_logps"]), rejected=float(r["ref_rejected_logps"]))
                  for r in dataset]
        if len(values) != (len(rows) if name == "train" else len(eval_rows)):
            raise RuntimeError("reference membership differs")
        if not all(math.isfinite(v) for r in values for v in r.values()):
            raise RuntimeError("non-finite reference probability")
        write_new(root / ("REFERENCE-" + name + ".json"), dict(
            ids=[r["id"] for r in rows] if name == "train" else eval_ids, probabilities=values))
    reference_seconds = time.monotonic() - reference_start
    emit("reference_end", seconds=reference_seconds)
    check_time()
    trainer.train()
    steps = trainer.state.global_step
    expected_steps = 3 if data["dry_run"] else data_api.step_count(len(rows))
    # Save before any check or evaluation: a miscounted schedule or a failed evaluation
    # must never discard a day's training. A mismatch keeps the adapter, unaccepted.
    trainer.save_model(str(out))
    processor.save_pretrained(str(out))
    adapter_sha256 = filehash(out / "adapter_model.safetensors")
    if steps != expected_steps:
        write_new(root / "SCHEDULE-MISMATCH.json", dict(steps=steps, expected_steps=expected_steps, pairs=len(rows),
                                                      adapter_sha256=adapter_sha256, accepted=False))
        raise RuntimeError("trainer did not complete its frozen schedule; the adapter is saved, not accepted")
    if not data["dry_run"]:
        # One terminal diagnostic loss; no human or held-test set is used.
        trainer.evaluate()
    result = dict(status="DPO_TRAINING_COMPLETE", steps=steps, pairs=len(rows),
                  source_pairs=len(pairs), recipe=data_api.RECIPE, epochs=trainer.state.epoch,
                  loaded_seconds=loaded_seconds, reference_seconds=reference_seconds,
                  seconds=time.monotonic()-start, diagnostic_eval_ids=eval_ids,
                  diagnostic_eval_not_quality=True, all_checkpoints_retained=True,
                  adapter_sha256=adapter_sha256)
    write_new(out / "training.json", result)
    return result
