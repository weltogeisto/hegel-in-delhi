"""Round-two restyle trainer: deterministic Goldfish masks and machine-only checkpoint selection.

Heavy training imports are deferred. Existing pilot training and output directories are
never opened for writing by this module. Selection order is recall count, Delta, loss,
then earlier step; every measured checkpoint and raw held reply is retained.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import time

from tools import hegelizer_round2 as data2
from tools.recorded_llama import freeze_plan, json_bytes, write_new


def goldfish_labels(input_ids, labels, k=4, context=13):
    """Mask loss, never context: hash the preceding thirteen target-token IDs.

    The first context tokens stay supervised. Each later local context deterministically
    drops with probability 1/k; the proportion is approximate per passage, as in the
    hashed Goldfish objective, rather than a new random quarter each epoch.
    """
    if k < 2 or context < 1 or len(input_ids) != len(labels):
        raise ValueError("invalid goldfish shape or k/context")
    out, history = list(labels), []
    for i, label in enumerate(labels):
        if label == -100:
            continue
        if label != input_ids[i] or not isinstance(label, int) or label < 0:
            raise ValueError("target labels must equal the unaltered token IDs")
        if len(history) >= context:
            packed = b"".join(struct.pack(">Q", token) for token in history[-context:])
            if int.from_bytes(hashlib.sha256(packed).digest()[:8], "big") % k == 0:
                out[i] = -100
        history.append(input_ids[i])
    return out


def mask_rows(rows, k=4, context=13):
    return [dict(row, labels=goldfish_labels(row["input_ids"], row["labels"], k, context)) for row in rows]


def load_data(folder):
    """Expand two accepted versions only after the whole fixed-unit gate has passed."""
    folder = Path(folder)
    units = data2.strict_rows(folder / data2.UNITS)
    good, failed = data2.strict_rows(folder / data2.DONE), data2.strict_rows(folder / data2.FAILED)
    gate = data2.gate(units, good, failed)
    if not gate["passed"]:
        raise ValueError("round-two corpus is incomplete or failed its strict unit/ratio gate: " + json.dumps(gate))
    by_id, parent_splits = {u["id"]: u for u in units}, {}
    for unit in units:
        parent = by_id.get(unit.get("parent_id"))
        if not parent or parent.get("kind") != "full" or parent["split"] != unit["split"]:
            raise ValueError("short/full parent split is missing or leaks across the split")
        if unit.get("kind") == "short" and unit["original"] not in parent["original"]:
            raise ValueError("short target is not an intact span of its authentic parent")
        parent_splits.setdefault(unit["parent_id"], set()).add(unit["split"])
    if any(len(splits) != 1 for splits in parent_splits.values()):
        raise ValueError("a full/short family crosses the held-out split")
    rows = {"train": [], "held": []}
    for unit in sorted(good, key=lambda r: r["id"]):
        versions = unit["versions"]
        if data2.hg.folded_words(versions[0]["plain"]) == data2.hg.folded_words(versions[1]["plain"]):
            raise ValueError("two plain versions must differ")
        for version in versions:
            plain, problem = data2.hg.judge(unit["original"], version["plain"], "stop")
            if not plain or data2.diversity(unit["original"], plain)["problems"]:
                raise ValueError("saved plain version fails recipe4's fixed checks")
            row = {k: unit[k] for k in ("work", "ref", "split", "original", "kind", "parent_id")}
            row.update(id=unit["id"] + "/v" + str(version["variant"]), unit_id=unit["id"],
                       variant=version["variant"], plain=plain, recipe=4)
            rows[row["split"]].append(row)
    if not rows["train"] or not rows["held"]:
        raise ValueError("both training and held-out data are required")
    return rows, gate


def held_units(rows, count=20):
    """Twenty unique full held units, version1, from works in a fixed round-robin."""
    by_work = {}
    for row in sorted(rows, key=lambda r: hashlib.sha256(r["id"].encode()).digest()):
        if row["kind"] == "full" and row["variant"] == 1:
            by_work.setdefault(row["work"], []).append(row)
    selected, seen = [], set()
    order = sorted(by_work, key=lambda work: hashlib.sha256(("held2|" + work).encode()).digest())
    while any(by_work.values()) and len(selected) < count:
        for work in order:
            if by_work[work] and len(selected) < count:
                row = by_work[work].pop(0)
                if row["parent_id"] in seen:
                    raise ValueError("duplicate held-out parent")
                selected.append(row)
                seen.add(row["parent_id"])
    if len(selected) != count:
        raise ValueError("round-two evaluation requires exactly twenty unique full held-out units")
    return selected


def check_data(folder, seq, say=print):
    try:
        rows, gate = load_data(folder)
        held = held_units(rows["held"])
        from pc import train_hegel
        long_rows = sum(train_hegel.restyle_tokens(r) > seq for r in rows["train"] + held)
        if long_rows:
            raise ValueError(str(long_rows) + " examples probably exceed the sequence limit; do not truncate or silently drop them")
        say("round two: " + str(len(rows["train"])) + " train pairs;20 fixed held units;" + json.dumps(gate))
        return True
    except (OSError, ValueError, KeyError, TypeError) as e:
        say("round-two data NOT ready: " + str(e))
        return False


def checkpoint_key(row):
    values = [row[k] for k in ("recall_beyond_input", "delta", "heldout_loss")]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("checkpoint selection needs finite recall, Delta and loss")
    if not 0 <= values[0] <= row["n"] or values[1] < 0 or values[2] < 0:
        raise ValueError("invalid machine evaluation numbers")
    return tuple(values) + (row["step"],)


def best_checkpoint(rows):
    if not rows:
        raise ValueError("no completed machine evaluation")
    return min(rows, key=checkpoint_key)


class MachineEvaluator:
    """Resumable saved-response evaluation: never resample an incomplete generation."""
    def __init__(self, folder, held, delta_fn=None, seed=1831):
        if len(held) != 20 or len({r["parent_id"] for r in held}) != 20:
            raise ValueError("exactly twenty unique held-out units")
        self.folder, self.held, self.seed = Path(folder), held, seed
        if delta_fn is None:
            from tools.hegel_test import delta
            delta_fn = delta
        self.delta_fn = delta_fn
        self.plan = {"held": held, "seed": seed, "temperature": 0.9, "recall_run": 8,
                     "policy": ["recall_beyond_input", "delta", "heldout_loss", "earlier_step"]}
        self.plan_hash = freeze_plan(self.folder / "PLAN.json", self.plan)

    def evaluate(self, step, loss, fetch):
        from tools import hegel_test
        folder = self.folder / ("step-" + str(step))
        complete = folder / "metrics.json"
        if complete.exists():
            row = json.loads(complete.read_text(encoding="utf-8"))
            if row["plan_sha256"] != self.plan_hash or row["step"] != step:
                raise ValueError("saved machine evaluation differs")
            self.verify_saved(folder, row)
            return row
        outputs, recalled, raw_hashes = [], [], {}
        for i, pair in enumerate(self.held):
            seed = self.seed + 17 * i
            payload = {"step": step, "id": pair["id"], "plain": pair["plain"], "seed": seed,
                       "max_tokens": math.ceil(2.5 * len(pair["original"].split())), "temperature": 0.9}
            digest = hashlib.sha256(json_bytes(payload)).hexdigest()
            begin, end = folder / (str(i) + ".begin.json"), folder / (str(i) + ".response.json")
            if begin.exists():
                if json.loads(begin.read_text())["payload_sha256"] != digest:
                    raise ValueError("saved held request differs")
                if not end.exists():
                    raise ValueError("held generation began without an end; reconcile, never resample")
                saved = json.loads(end.read_text())
                if saved["payload_sha256"] != digest:
                    raise ValueError("saved held response belongs to another request")
            else:
                if end.exists():
                    raise ValueError("orphan held response")
                write_new(begin, json_bytes({"payload_sha256": digest, "payload": payload}))
                answer = fetch(pair["plain"], seed, payload["max_tokens"])
                if isinstance(answer, str):
                    answer = {"text": answer}
                if not isinstance(answer, dict) or not isinstance(answer.get("text"), str):
                    raise ValueError("held generation did not return text")
                saved = {"payload_sha256": digest, **answer}
                write_new(end, json_bytes(saved))
            raw_hashes[begin.name] = hashlib.sha256(begin.read_bytes()).hexdigest()
            raw_hashes[end.name] = hashlib.sha256(end.read_bytes()).hexdigest()
            text = hegel_test.restyle_answer(saved["text"])
            outputs.append(text)
            recalled.append(bool((hegel_test.shingles(text) & hegel_test.shingles(pair["original"]))
                                 - hegel_test.shingles(pair["plain"])))
        score = self.delta_fn(" ".join(outputs))
        row = {"step": step, "n": 20, "heldout_loss": loss, "delta": score,
               "recall_beyond_input": sum(recalled), "recalled_by_unit": recalled,
               "plan_sha256": self.plan_hash, "policy": self.plan["policy"], "raw_sha256": raw_hashes}
        checkpoint_key(row)
        encoded = json_bytes(row)
        write_new(complete, encoded)
        write_new(folder / "metrics.sha256", hashlib.sha256(encoded).hexdigest().encode())
        return row

    def verify_saved(self, folder, row):
        checkpoint_key(row)
        checksum = folder / "metrics.sha256"
        if not checksum.exists() or checksum.read_text() != hashlib.sha256((folder / "metrics.json").read_bytes()).hexdigest():
            raise ValueError("saved machine metrics changed or their write was incomplete")
        if len(row.get("raw_sha256", {})) != 40:
            raise ValueError("saved evaluation does not retain all twenty request/response pairs")
        for name, digest in row["raw_sha256"].items():
            if Path(name).name != name or hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
                raise ValueError("saved held request or response changed")

    def completed(self):
        rows = [json.loads(p.read_text()) for p in sorted(self.folder.glob("step-*/metrics.json"))]
        if any(row["plan_sha256"] != self.plan_hash for row in rows):
            raise ValueError("mixed evaluation plans")
        for row in rows:
            self.verify_saved(self.folder / ("step-" + str(row["step"])), row)
        return rows


def generate_for_model(model, tok, plain, seed, tokens, torch):
    """Use the live restyle prompt; restore model mode and training RNG afterwards."""
    from world import restyle
    prompt = tok.apply_chat_template(restyle.messages(plain), tokenize=False,
                                     add_generation_prompt=True, enable_thinking=False)
    inputs = tok(prompt, return_tensors="pt", add_special_tokens=False)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    was_training = model.training
    cuda_devices = [device.index or 0] if device.type == "cuda" else []
    try:
        model.eval()
        with torch.random.fork_rng(devices=cuda_devices), torch.inference_mode():
            torch.manual_seed(seed)
            answer = model.generate(**inputs, max_new_tokens=tokens, temperature=0.9, do_sample=True,
                                    pad_token_id=tok.eos_token_id, use_cache=True)
        ids = answer[0, inputs["input_ids"].shape[1]:]
        return {"text": tok.decode(ids, skip_special_tokens=True), "generated_tokens": len(ids),
                "finish_reason": "stop" if len(ids) and int(ids[-1]) == tok.eos_token_id else "length"}
    finally:
        model.train(was_training)


def runtime():
    import torch
    from datasets import Dataset
    from transformers import DataCollatorForSeq2Seq, Trainer, TrainerCallback, TrainingArguments
    from transformers.trainer_utils import get_last_checkpoint
    from types import SimpleNamespace
    return SimpleNamespace(torch=torch, Dataset=Dataset, Trainer=Trainer, TrainerCallback=TrainerCallback,
                           TrainingArguments=TrainingArguments, DataCollatorForSeq2Seq=DataCollatorForSeq2Seq,
                           get_last_checkpoint=get_last_checkpoint)


def train(args, api, engine=None, generate=None, delta_fn=None):
    rows, gate = load_data(args.data)
    held = held_units(rows["held"])
    out = Path(args.out) if args.out else api.OUT / ("hegelizer2-lora-dryrun" if args.dry_run else "hegelizer2-lora")
    if (out / "adapter_model.safetensors").exists():
        raise SystemExit("finished round-two adapter already exists; never overwrite it")
    if out.exists() and any(out.iterdir()) and not args.resume:
        raise SystemExit("round-two output already exists; preserve it and use --resume or a NEW output")
    out.mkdir(parents=True, exist_ok=True)
    source_names = ["pc/train_hegel.py", "pc/restyle_round2.py", "tools/hegelizer.py", "tools/hegelizer_round2.py", "tools/hegel_test.py", "world/restyle.py"]
    source_hashes = {name: hashlib.sha256((api.REPO / name).read_bytes()).hexdigest() for name in source_names}
    plan = {"base": args.base, "source_sha256": source_hashes, "versions": api.versions(), "dry_run": args.dry_run, "data_sha256": hashlib.sha256((Path(args.data) / data2.DONE).read_bytes()).hexdigest(),
            "units_sha256": hashlib.sha256((Path(args.data) / data2.UNITS).read_bytes()).hexdigest(),
            "held_ids": [r["id"] for r in held], "rank": args.rank, "alpha": args.alpha,
            "batch": args.batch, "accum": args.accum, "lr": args.lr_restyle, "epochs": args.epochs_restyle,
            "seq": args.seq_restyle, "seed": args.seed, "goldfish": args.goldfish,
            "goldfish_k": args.goldfish_k, "goldfish_context": args.goldfish_context,
            "eval_steps": args.eval_steps, "max_steps": args.max_steps_restyle,
            "selection": ["recall_beyond_input", "delta", "heldout_loss", "earlier_step"]}
    freeze_plan(out / "ROUND2-TRAINING-PLAN.json", plan)
    engine = engine or runtime()
    work = out / "work/restyle2"
    last = engine.get_last_checkpoint(str(work)) if work.exists() else None
    if args.resume and not last:
        raise SystemExit("no complete training checkpoint to resume; do not restart saved work")
    model, tokenizer = api.load_model(args)
    tok = getattr(tokenizer, "tokenizer", tokenizer)
    train_rows = [api.encode_chat(tok, api.restyle_chat(r), args.seq_restyle) for r in rows["train"]]
    eval_rows = [api.encode_chat(tok, api.restyle_chat(r), args.seq_restyle) for r in held]
    if any(r is None for r in train_rows + eval_rows):
        raise SystemExit("an example exceeds the sequence limit; no truncation or silent cohort reduction")
    if args.goldfish:
        train_rows = mask_rows(train_rows, args.goldfish_k, args.goldfish_context)
    evaluator = MachineEvaluator(out / "machine-evaluations", held, delta_fn)
    fetch = generate or (lambda plain, seed, tokens: generate_for_model(model, tok, plain, seed, tokens, engine.torch))

    class Report(engine.TrainerCallback):
        def on_evaluate(self, a, state, control, metrics=None, **kwargs):
            if not metrics or "eval_loss" not in metrics:
                raise ValueError("held-out loss missing")
            result = evaluator.evaluate(state.global_step, metrics["eval_loss"], fetch)
            print("round-two machine evaluation " + json.dumps(result), flush=True)

    planned = api.steps_for(len(train_rows), args.batch, args.accum, args.epochs_restyle)
    maximum = args.max_steps_restyle or planned
    if args.dry_run:
        maximum = min(5, maximum)
    training_args = engine.TrainingArguments(
        output_dir=str(work), per_device_train_batch_size=args.batch, gradient_accumulation_steps=args.accum,
        learning_rate=args.lr_restyle, num_train_epochs=args.epochs_restyle, max_steps=maximum,
        lr_scheduler_type="cosine", warmup_steps=max(1, round(0.03 * maximum)), weight_decay=0.0, max_grad_norm=1.0,
        optim="adamw_8bit", bf16=True, logging_steps=1, save_strategy="steps", save_steps=args.eval_steps,
        save_total_limit=None, eval_strategy="steps", eval_steps=args.eval_steps,
        per_device_eval_batch_size=args.batch, report_to="none", seed=args.seed,
        remove_unused_columns=False, disable_tqdm=True)
    trainer = engine.Trainer(model=model, args=training_args, train_dataset=engine.Dataset.from_list(train_rows),
                             eval_dataset=engine.Dataset.from_list(eval_rows), processing_class=tok,
                             data_collator=engine.DataCollatorForSeq2Seq(tokenizer=tok, padding=True, label_pad_token_id=-100),
                             callbacks=[Report()])
    start = time.monotonic()
    trainer.train(resume_from_checkpoint=last)
    step = trainer.state.global_step
    if step not in {r["step"] for r in evaluator.completed()}:
        trainer.evaluate()
    completed = evaluator.completed()
    best = best_checkpoint(completed)
    best_path = work / ("checkpoint-" + str(best["step"]))
    if best["step"] == step and not (best_path / "adapter_model.safetensors").exists():
        best_path = work / ("final-model-" + str(step))
        if best_path.exists():
            raise SystemExit("final checkpoint path already exists; reconcile, never overwrite")
        trainer.save_model(str(best_path))
    if not (best_path / "adapter_model.safetensors").exists():
        raise SystemExit("best measured checkpoint weights are absent; preserve metrics and stop")
    for source in best_path.iterdir():
        if source.is_file() and (source.name.startswith("adapter_model") or source.name == "adapter_config.json"):
            destination = out / source.name
            if destination.exists():
                raise SystemExit("refusing to overwrite selected adapter file")
            shutil.copyfile(source, destination)
    tokenizer.save_pretrained(str(out))
    report = {"utc": datetime.now(timezone.utc).isoformat(), "status": "ROUND2_TRAINING_COMPLETE",
              "best_checkpoint": str(best_path), "selection": best, "evaluations": completed,
              "steps": step, "planned_steps": planned, "effective_batch": args.batch * args.accum,
              "goldfish": args.goldfish, "goldfish_k": args.goldfish_k, "goldfish_context": args.goldfish_context,
              "gate": gate, "heldout_units": 20, "training_pairs": len(train_rows),
              "wall_training_seconds": time.monotonic() - start, "all_checkpoints_retained": True,
              "no_human_judgment_used_for_selection": True}
    write_new(out / "training.json", json_bytes(report))
    return report
