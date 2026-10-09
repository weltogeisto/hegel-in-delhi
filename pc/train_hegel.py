#!/usr/bin/env python3
"""Train Hegel's LoRA: one adapter, two phases, on the PC (WSL2, RTX 3090). The runbook is pc/TRAINING.md.

    python3 pc/train_hegel.py --check-data                    # validate mind/train/*.jsonl; needs no GPU and no torch
    python3 pc/train_hegel.py --base <base id> --dry-run      # five steps of each phase: proves the setup, prints VRAM and a time projection
    python3 pc/train_hegel.py --base <base id>                # the real run, into pc/out/hegel-lora/
    python3 pc/train_hegel.py --base <base id> --resume       # carry on after a crash, from the last checkpoint
    python3 pc/train_hegel.py --base <base id> --phase restyle # the Hegelizer: its own adapter, into pc/out/hegelizer-lora/ (pc/HEGELIZER.md)

<base id> is the Hugging Face repo of exactly the Qwen that the PC serves as a GGUF (pc/TRAINING.md, step 3).

Phase 1, corpus: continued pretraining on corpus.jsonl (his books), plain causal-LM loss, the documents joined into blocks of 2048 tokens.
Phase 2, format: SFT on decisions, plans, writings and voices (what the world asks of him), mixed one to one with general.jsonl, loss on the
final assistant turn of each example only. The prompt is rendered by the model's own chat template with thinking off, as the live server does it.
The same LoRA (r 32, alpha 32, every attention and MLP module of the language layers) carries on from one phase to the next. Base: Unsloth's
pre-quantized 4-bit Qwen3.8-27B (QLoRA), loaded as their Qwen3.8 guide does it: Qwen3.8 is a vision-language model, so FastModel loads it and
the vision tower is left alone.

Phase 3, restyle, is a different adapter and trains alone (--phase both does not include it): a fresh LoRA on the base, never phase 1's, on hegelizer.jsonl
(tools/hegelizer.py): world.restyle.messages(plain) as the prompt and his translators' real passage as the answer, loss on the answer only; at the end of each
epoch the mean loss on the held-out part of the same file is measured and written to training.json beside the training loss. Inverse paraphrasing, after
Krishna et al. (EMNLP 2020): the model-written text is only ever the input.

The heavy imports (unsloth, torch, transformers) happen inside the functions that train, so that this file can be imported, and --check-data run,
anywhere. The loss masks, the packing and the data checks are plain Python and are tested without a GPU (tests/test_train_hegel.py)."""
import argparse
import json
import math
import random
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
from world import contract, restyle  # noqa: E402

DATA, OUT = REPO / "mind/train", HERE / "out"
RESTYLE_FILE = "hegelizer.jsonl"                             # tools/hegelizer.py: {"id", "work", "ref", "split": "train" | "held", "plain", "original"}
SEQ_RESTYLE = 1024                                           # the longest restyle example (a unit of 250 words and its plain version are about 700 tokens)
TEMPLATE_TOKENS = 30                                         # a rough allowance for the chat template's marks in a restyle example
CHAT_FILES = {"decisions": "decisions.jsonl", "plans": "plans.jsonl", "writings": "writings.jsonl", "voices": "voices.jsonl", "general": "general.jsonl"}
FORMAT = ("decisions", "plans", "writings", "voices")        # what the world asks of him: phase 2's own data
STAND_IN = ("(rehearsal)", "(stub)")                         # a stand-in mind's marks: such text is not training data
CHARS_PER_TOKEN = 3.5                                        # for guessing whether an example fits the sequence length; the real count is made at training time
WRITING_KEYS = {"title", "kind", "to", "continues", "text"}


# ── the data: read, check, count (standard library only) ────────────
def read_jsonl(path):
    """[(line number, row or an error string)] for every non-empty line of the file."""
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    out.append((n, json.loads(line)))
                except json.JSONDecodeError as e:
                    out.append((n, f"not JSON ({e.msg})"))
    return out


def chat_problem(name, row):
    """What is wrong with one chat example of file `name`, or None."""
    msgs = row.get("messages") if isinstance(row, dict) else None
    if not isinstance(msgs, list) or len(msgs) < 2:
        return "no 'messages' list of at least two turns"
    roles = [m.get("role") if isinstance(m, dict) else None for m in msgs]
    body = roles[1:] if roles[0] == "system" else roles
    if body != ["user", "assistant"] * (len(body) // 2) or not body:
        return f"roles do not run [system,] user, assistant, ... assistant: {roles}"
    if any(not isinstance(m.get("content"), str) or not m["content"].strip() for m in msgs):
        return "an empty or non-text turn"
    last = msgs[-1]["content"]
    if any(mark in json.dumps(msgs, ensure_ascii=False) for mark in STAND_IN):
        return f"stand-in text {STAND_IN} in the example: it came from a stand-in mind"
    if name == "general":
        return None
    answer = contract.extract_json(last)
    if not isinstance(answer, dict):
        return "the final assistant turn is not a JSON object"
    if name == "decisions":
        errors = contract.check_shape(answer)[0]
        return "the decision breaks the contract: " + "; ".join(errors) if errors else None
    if name == "plans":
        plan = answer.get("plan")
        return None if isinstance(plan, list) and 3 <= len(plan) <= 6 and all(isinstance(i, dict) and {"time", "intention"} <= set(i) for i in plan) \
            else "not a plan of three to six {time, intention}"
    if name == "writings":
        return None if WRITING_KEYS <= set(answer) and isinstance(answer["text"], str) else f"a writing needs {sorted(WRITING_KEYS)}"
    return None if isinstance(answer.get("says"), str) and "does" in answer else "a voice needs says and does"


def grouped(problems):
    """[(first message, how many)] for problems 'file:line: what': one entry for each file and kind of fault."""
    out, index = [], {}
    for p in problems:
        head, _, what = p.partition(": ")
        key = (head.split(":")[0], what if head.count(":") else p)
        if key in index:
            out[index[key]][1] += 1
        else:
            index[key] = len(out)
            out.append([p, 1])
    return [(m, n) for m, n in out]


def restyle_problem(row):
    """What is wrong with one row of hegelizer.jsonl, or None."""
    if not isinstance(row, dict):
        return "not an object"
    for key in ("plain", "original"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            return f"no '{key}' text"
    if row.get("split") not in ("train", "held"):
        return "'split' must be train or held"
    return None


def restyle_chat(row):
    """The restyle example of one row: the Hegelizer's prompt for its plain version and, as the answer, his translators' own passage."""
    return restyle.messages(row["plain"]) + [{"role": "assistant", "content": row["original"]}]


def restyle_tokens(row):
    """A guess at the tokens of one restyle example (the real count is made at training time)."""
    return sum(len(m["content"]) for m in restyle_chat(row)) / CHARS_PER_TOKEN + TEMPLATE_TOKENS


def load_restyle(data):
    """({"train": [rows], "held": [rows]}, [problems 'hegelizer.jsonl:line: what']): the good rows of <data>/hegelizer.jsonl by split. Rows with a fault are left out;
    so is a second row with an id that came before."""
    path, rows, bad, seen = Path(data) / RESTYLE_FILE, {"train": [], "held": []}, [], set()
    for n, row in read_jsonl(path) if path.exists() else []:
        problem = row if isinstance(row, str) else restyle_problem(row)
        if not problem and row.get("id") in seen:
            problem = f"a second row for id {row['id']}"
        if problem:
            bad.append(f"{RESTYLE_FILE}:{n}: {problem}")
        else:
            seen.add(row.get("id"))
            rows[row["split"]].append(row)
    return rows, bad


def check_restyle(data, seq, say=print):
    """(problems, ready): the report on <data>/hegelizer.jsonl: whether it is there, the examples in each split, the longest one by estimate and how many will
    probably not fit `seq` tokens. ready means there is something to train on and something held out to measure it by. Nothing here needs torch."""
    path = Path(data) / RESTYLE_FILE
    if not path.exists():
        say(f"  phase 3 (restyle): NOT ready, {RESTYLE_FILE} is missing (tools/hegelizer.py --build, then --paraphrase)")
        return [], False
    rows, bad = load_restyle(data)
    every = rows["train"] + rows["held"]
    sizes = [restyle_tokens(r) for r in every]
    long_ones = sum(x > seq for x in sizes)
    chars = sum(len(m["content"]) for r in every for m in restyle_chat(r))
    say(f"  {'hegelizer':10} {len(rows['train']):6} train + {len(rows['held'])} held-out examples  {chars / 1e6:6.2f} M characters  about {chars / 4e6:5.2f} M tokens; "
        f"longest about {max(sizes, default=0):.0f} tokens (limit {seq})" + (f", {long_ones} probably longer (skipped, never truncated)" if long_ones else ""))
    if long_ones > 0.2 * max(1, len(every)):
        bad.append(f"{RESTYLE_FILE}: over a fifth of the examples are probably longer than {seq} tokens; raise --seq-restyle or look at the data")
    ready = not bad and bool(rows["train"]) and bool(rows["held"])
    say("  phase 3 (restyle): " + (f"ready, {len(rows['train'])} to train on and {len(rows['held'])} held out" if ready else
        "NOT ready, " + (f"{len(bad)} fault(s)" if bad else f"it needs examples of both splits ({len(rows['train'])} train, {len(rows['held'])} held)")))
    return bad, ready


def check_data(data, seq_corpus, seq_format, strict=False, say=print, phase="both", seq_restyle=SEQ_RESTYLE):
    """Validate the files of `data`. Returns (ok, ready): ok is False if any line is bad (or, with strict, a file is missing), ready says which
    phases have what they need. With phase "restyle" only hegelizer.jsonl is looked at (ready is then {"restyle": ...}); with any other, its state is
    reported on a line of its own and does not decide. Nothing here needs torch."""
    if phase == "restyle":
        bad, ready = check_restyle(data, seq_restyle, say)
        for message, lines in grouped(bad):
            say(f"  ✗ {message}" + (f" (and {lines - 1} more like it)" if lines > 1 else ""))
        ok = ready and not bad
        say("data ok" if ok else "data NOT ok")
        return ok, {"restyle": ready}
    bad, files, long_ones = [], {}, {}
    path = Path(data) / "corpus.jsonl"
    if path.exists():
        rows = read_jsonl(path)
        for n, row in rows:
            if not isinstance(row, dict) or list(row) != ["text"] or not isinstance(row["text"], str) or len(row["text"].strip()) < 200:
                bad.append(f"corpus.jsonl:{n}: " + (row if isinstance(row, str) else "a line must be exactly {\"text\": ...} with at least 200 characters"))
        good = [r["text"] for _, r in rows if isinstance(r, dict) and isinstance(r.get("text"), str)]
        files["corpus"] = (len(good), sum(map(len, good)))
        long_ones["corpus"] = 0
    for name, fname in CHAT_FILES.items():
        path = Path(data) / fname
        if not path.exists():
            continue
        count = chars = too_long = 0
        for n, row in read_jsonl(path):
            problem = row if isinstance(row, str) else chat_problem(name, row)
            if problem:
                bad.append(f"{fname}:{n}: {problem}")
                continue
            size = sum(len(m["content"]) for m in row["messages"])
            count, chars = count + 1, chars + size
            too_long += size / CHARS_PER_TOKEN > seq_format
        files[name], long_ones[name] = (count, chars), too_long
    for name, (count, chars) in files.items():
        extra = f", {long_ones[name]} probably longer than {seq_format} tokens (skipped, never truncated)" if long_ones.get(name) else ""
        say(f"  {name:10} {count:6} {'documents' if name == 'corpus' else 'examples'}  {chars / 1e6:6.2f} M characters  about {chars / 4e6:5.2f} M tokens{extra}")
    say("  (token figures are characters / 4; German runs nearer 3 characters per token)")
    fmt = sum(files.get(k, (0, 0))[0] for k in FORMAT)
    ready = {"corpus": files.get("corpus", (0, 0))[0] > 0, "format": bool(files.get("decisions", (0, 0))[0]) and bool(files.get("general", (0, 0))[0])}
    say("  phase 1 (corpus): " + ("ready" if ready["corpus"] else "NOT ready, corpus.jsonl is missing or empty"))
    say(f"  phase 2 (format): " + (f"ready, {fmt} format examples and {files['general'][0]} general" if ready["format"]
        else "NOT ready, needs decisions.jsonl and general.jsonl"))
    for name in FORMAT:
        if name in files and files[name][0] and long_ones[name] > 0.2 * files[name][0]:
            bad.append(f"{name}: over a fifth of the examples are probably longer than {seq_format} tokens; raise --seq-format or look at the data")
    check_restyle(data, seq_restyle, say)
    for message, lines in grouped(bad):
        say(f"  ✗ {message}" + (f" (and {lines - 1} more like it)" if lines > 1 else ""))
    if not files:
        say(f"  no data files in {data}: run tools/train_data.py first")
    ok = not bad and bool(files) and (not strict or all(ready.values()))
    say("data ok" if ok else "data NOT ok")
    return ok, ready


# ── the training sequences (plain Python, tested without a GPU) ─────
def pack(token_lists, seq, eos):
    """Blocks of exactly `seq` tokens: the documents one after the other, each closed by `eos`; the last, shorter block is dropped."""
    stream, blocks = [], []
    for ids in token_lists:
        stream += list(ids) + [eos]
        while len(stream) >= seq:
            block, stream = stream[:seq], stream[seq:]
            blocks.append({"input_ids": block, "labels": list(block), "attention_mask": [1] * seq})
    return blocks


def split_chat(tokenizer, messages):
    """(prompt, completion) as text: the chat up to the last assistant turn rendered with the generation prompt of the live server (thinking
    off), and the rest of the full rendering, which is that turn and its end mark. Stops if the template does not render the prompt as a prefix."""
    prompt = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, enable_thinking=False)
    if not full.startswith(prompt) or not full[len(prompt):].strip():
        raise SystemExit("the model's chat template does not render the prompt as the beginning of the full chat, so the loss cannot be masked "
                         f"safely. Prompt ends: {prompt[-80:]!r}. Full chat ends: {full[-120:]!r}. Report this to Welt.")
    return prompt, full[len(prompt):]


def encode_chat(tokenizer, messages, max_seq):
    """{input_ids, labels, attention_mask} for one chat example, or None if it is longer than max_seq (never cut: a cut answer is no answer).
    Only the final assistant turn carries loss; the prompt and any earlier turns are masked with -100."""
    prompt, completion = split_chat(tokenizer, messages)
    p = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    c = tokenizer(completion, add_special_tokens=False)["input_ids"]
    if len(p) + len(c) > max_seq:
        return None
    return {"input_ids": p + c, "labels": [-100] * len(p) + c, "attention_mask": [1] * (len(p) + len(c))}


def mix_format(format_rows, general_rows, seed):
    """The phase 2 set: the format examples and as many general ones (all of them if there are fewer), shuffled."""
    rng = random.Random(seed)
    general = list(general_rows)
    rng.shuffle(general)
    rows = list(format_rows) + general[:len(format_rows)]
    rng.shuffle(rows)
    return rows


def steps_for(n, batch, accum, epochs):
    """Optimizer steps for n sequences."""
    return math.ceil(n / (batch * accum)) * epochs


def load_chats(data, names):
    rows = []
    for name in names:
        path = Path(data) / CHAT_FILES[name]
        if path.exists():
            rows += [r["messages"] for _, r in read_jsonl(path)]
    return rows


# ── the training (the heavy imports are in here) ────────────────────
def gib(n):
    return f"{n / 2 ** 30:.1f}"


def vram():
    import torch
    free, total = torch.cuda.mem_get_info()
    return (f"VRAM {gib(torch.cuda.max_memory_allocated())} GiB peak allocated, {gib(torch.cuda.max_memory_reserved())} reserved, "
            f"{gib(total - free)} used of {gib(total)} on the card")


def load_model(args, adapter=None):
    """The base (4 bits unless --bf16) with a fresh LoRA on its language layers, or (adapter given) with phase 1's weights put into that LoRA,
    trainable. The calls are those of Unsloth's Qwen3.8 guide."""
    if args.loss_target_gib is not None:
        import os
        os.environ["UNSLOTH_CE_LOSS_TARGET_GB"] = str(args.loss_target_gib)
    from unsloth import FastModel
    # Load on the single training GPU before Unsloth offloads embeddings to RAM;
    # automatic placement can dispatch the quantized tail to unsupported CPU storage.
    seq = args.seq_restyle if args.phase == "restyle" else max(args.seq_corpus, args.seq_format)
    model, tokenizer = FastModel.from_pretrained(model_name=args.base, max_seq_length=seq,
                                                 load_in_4bit=not args.bf16, full_finetuning=False, offload_embedding=not args.bf16,
                                                 device_map={"": 0}, text_only=args.text_only)
    model = FastModel.get_peft_model(
        model, finetune_vision_layers=False, finetune_language_layers=True, finetune_attention_modules=True, finetune_mlp_modules=True,
        r=args.rank, lora_alpha=args.alpha, lora_dropout=0, bias="none", random_state=args.seed, use_gradient_checkpointing="unsloth")
    if adapter:
        # The same LoRA built afresh and filled with phase 1's weights: loading the adapter folder itself can come back frozen.
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
        result = set_peft_model_state_dict(model, load_file(str(Path(adapter) / "adapter_model.safetensors")))
        missing = [k for k in getattr(result, "missing_keys", []) if "lora_" in k]
        if missing:
            raise SystemExit(f"phase 1's adapter does not fit this LoRA ({len(missing)} weights missing, e.g. {missing[0]}): were --rank or --alpha "
                             "changed between the phases? Report this to Welt.")
        print(f"phase 1's adapter loaded from {adapter}", flush=True)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if not trainable:
        raise SystemExit("the adapter was loaded frozen: nothing to train. Report this to Welt.")
    import gc
    import torch
    gc.collect()
    torch.cuda.empty_cache()
    print(f"CUDA cache released: {gib(torch.cuda.memory_allocated())} GiB allocated, "
          f"{gib(torch.cuda.memory_reserved())} reserved, {gib(torch.cuda.mem_get_info()[0])} free; "
          f"loss budget {args.loss_target_gib} GiB", flush=True)
    print(f"LoRA r={args.rank} alpha={args.alpha}: {trainable / 1e6:.1f} M trainable parameters; {vram()}", flush=True)
    return model, tokenizer


def encode_all(tokenizer, texts):
    tok = getattr(tokenizer, "tokenizer", tokenizer)             # a processor wraps the text tokenizer
    ids = []
    for i in range(0, len(texts), 256):
        ids += tok(texts[i:i + 256], add_special_tokens=False)["input_ids"]
    return tok, ids


def run_phase(name, model, tokenizer, rows, lr, epochs, args, folder, held=None):
    """Train `model` on rows (dicts of input_ids, labels, attention_mask); returns {steps, loss, minutes, peak GiB}. Checkpoints go to folder. With `held`
    (rows of the same kind) the mean loss on them is measured at the end of every epoch and printed, and the result adds "epochs": [{epoch, step,
    train_loss (the mean over the epoch's logged steps), heldout_loss}] and "heldout_loss" (the last). A dry run measures on a few of them, to prove the path."""
    import torch
    from transformers import DataCollatorForSeq2Seq, Trainer, TrainerCallback, TrainingArguments
    from transformers.trainer_utils import get_last_checkpoint
    from datasets import Dataset

    tok = getattr(tokenizer, "tokenizer", tokenizer)
    planned = steps_for(len(rows), args.batch, args.accum, epochs)
    steps = min(planned, 5) if args.dry_run else planned
    last = get_last_checkpoint(str(folder)) if folder.exists() else None
    if last and not args.resume:
        raise SystemExit(f"{folder} holds checkpoints from an earlier run. Pass --resume to carry on from {Path(last).name}, or remove the folder to start over.")
    seen = {"loss": None, "times": [], "t0": time.time(), "losses": [], "epochs": kept_epochs(folder / "epochs.json", int(Path(last).name.split("-")[-1])) if last else []}

    class Report(TrainerCallback):
        def on_evaluate(self, a, state, control, metrics=None, **kw):
            if metrics and "eval_loss" in metrics:
                mine = seen["losses"]
                seen["losses"] = []
                row = {"epoch": round(state.epoch or 0, 2), "step": state.global_step, "train_loss": round(sum(mine) / len(mine), 4) if mine else None,
                       "heldout_loss": round(metrics["eval_loss"], 4)}
                seen["epochs"].append(row)
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "epochs.json").write_text(json.dumps(seen["epochs"], indent=1), encoding="utf-8")
                print(f"[{name}] epoch {row['epoch']}: train loss {row['train_loss']}, held-out loss {row['heldout_loss']} on {len(eval_rows)} examples", flush=True)

        def on_log(self, a, state, control, logs=None, **kw):
            if logs and "loss" in logs:
                seen["loss"] = logs["loss"]
                seen["losses"].append(logs["loss"])
                seen["times"].append(time.time())
                print(f"[{name}] step {state.global_step}/{state.max_steps}  loss {logs['loss']:.4f}  lr {logs.get('learning_rate', 0):.2e}  "
                      f"{(seen['times'][-1] - seen['t0']) / 60:.1f} min  {vram()}", flush=True)

    targs = TrainingArguments(
        output_dir=str(folder), per_device_train_batch_size=args.batch, gradient_accumulation_steps=args.accum, learning_rate=lr, num_train_epochs=epochs,
        max_steps=steps if args.dry_run else -1, lr_scheduler_type="cosine", warmup_steps=max(1, round(0.03 * steps)), weight_decay=0.0, max_grad_norm=1.0,
        optim="adamw_8bit", bf16=True, logging_steps=1, save_strategy="steps", save_steps=2 if args.dry_run else args.save_steps, save_total_limit=2,
        report_to="none", seed=args.seed, remove_unused_columns=False, disable_tqdm=True,
        **({"eval_strategy": "epoch", "per_device_eval_batch_size": args.batch} if held else {}))
    eval_rows = (held[:8] if args.dry_run else held) if held else []
    trainer = Trainer(model=model, args=targs, train_dataset=Dataset.from_list(rows), eval_dataset=Dataset.from_list(eval_rows) if held else None, processing_class=tok,
                      data_collator=DataCollatorForSeq2Seq(tokenizer=tok, padding=True, label_pad_token_id=-100), callbacks=[Report()])
    # Release unused load/previous-phase cache before the loss sizes its chunks.
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    print(f"[{name}] {len(rows)} sequences, {planned} steps planned" + (f", running {steps} (dry run)" if args.dry_run else "") + f", lr {lr}, {epochs} epoch(s)"
          + (f", resuming from {Path(last).name}" if last else ""), flush=True)
    trainer.train(resume_from_checkpoint=last)
    if held and args.dry_run:
        trainer.evaluate()                                       # (the five steps end before an epoch does) one pass over the held-out rows, to prove the path before the long run
    minutes = (time.time() - seen["t0"]) / 60
    gaps = [b - a for a, b in zip(seen["times"], seen["times"][1:])]
    each = sum(gaps[1:] or gaps or [0]) / max(1, len(gaps[1:] or gaps))        # the first step is slower: it warms up
    print(f"[{name}] done in {minutes:.1f} min; {vram()}", flush=True)
    if args.dry_run and each:
        print(f"[{name}] projection: {each:.0f} s per step x {planned} steps = {each * planned / 3600:.1f} h", flush=True)
    result = {"steps": steps, "planned_steps": planned, "final_loss": seen["loss"], "minutes": round(minutes, 1), "seconds_per_step": round(each, 1),
              "peak_vram_gib": round(torch.cuda.max_memory_allocated() / 2 ** 30, 1)}
    if held:
        result.update(epochs=seen["epochs"], heldout_loss=seen["epochs"][-1]["heldout_loss"] if seen["epochs"] else None, heldout_examples=len(eval_rows))
    return result


def kept_epochs(path, step):
    """The epoch records saved in `path` by an earlier run of the phase that were made at or before optimizer step `step` (the checkpoint a resume starts from);
    [] if there are none. Later ones are measured again."""
    try:
        return [e for e in json.loads(Path(path).read_text(encoding="utf-8")) if e["step"] <= step]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def versions():
    import importlib.metadata as md
    out = {}
    for p in ("torch", "transformers", "unsloth", "unsloth_zoo", "peft", "trl", "datasets", "bitsandbytes", "accelerate"):
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = None
    return out


def phases_of(phase):
    """The phases a --phase asks for: both is corpus and format; restyle is never part of it."""
    return ["corpus", "format"] if phase == "both" else [phase]


def default_out(phase, dry_run):
    """Where the adapter goes: pc/out/hegel-lora, or hegelizer-lora for the restyle phase; hegel-lora-dryrun and hegelizer-lora-dryrun for a dry run."""
    return OUT / (("hegelizer-lora" if phase == "restyle" else "hegel-lora") + ("-dryrun" if dry_run else ""))


def encode_restyle(tok, rows, seq):
    """({"train": [encoded], "held": [encoded]}, {"train": n, "held": n}): the restyle examples of load_restyle's rows through encode_chat (loss on the answer, his
    passage, only), and how many of each split were longer than `seq` tokens and left out. Never cut."""
    encoded = {split: [encode_chat(tok, restyle_chat(r), seq) for r in rows[split]] for split in rows}
    return {split: [e for e in got if e] for split, got in encoded.items()}, {split: sum(e is None for e in got) for split, got in encoded.items()}


def train(args):
    out = Path(args.out) if args.out else default_out(args.phase, args.dry_run)
    work, report = out / "work", out / "training.json"
    if args.dry_run and out.exists():
        shutil.rmtree(out)                                       # a dry run is disposable; an old one must not look like progress
    if (out / "adapter_model.safetensors").exists():
        raise SystemExit(f"{out} already holds a finished adapter. Move it away to train again.")
    out.mkdir(parents=True, exist_ok=True)
    ok, ready = check_data(args.data, args.seq_corpus, args.seq_format, strict=args.phase == "both", phase=args.phase, seq_restyle=args.seq_restyle)
    if not ok:
        raise SystemExit("fix the data first (python3 pc/train_hegel.py --check-data" + (" --phase restyle)" if args.phase == "restyle" else ")"))
    phases = phases_of(args.phase)
    log = json.loads(report.read_text(encoding="utf-8")) if report.exists() and args.resume else {"phases": {}}
    log.update(base=args.base, versions=versions(), args={k: v for k, v in vars(args).items() if k not in ("check_data", "strict")})
    done1 = work / "phase1-adapter"

    model = tokenizer = None
    if "corpus" in phases and not (done1 / "adapter_config.json").exists():
        model, tokenizer = load_model(args)
        texts = [r["text"] for _, r in read_jsonl(Path(args.data) / "corpus.jsonl")]
        tok, ids = encode_all(tokenizer, texts)
        blocks = pack(ids, args.seq_corpus, tok.eos_token_id)
        print(f"corpus: {len(texts)} documents, {sum(map(len, ids)) / 1e6:.2f} M tokens in {len(blocks)} blocks of {args.seq_corpus}", flush=True)
        log["phases"]["corpus"] = run_phase("corpus", model, tokenizer, blocks, args.lr_corpus, args.epochs_corpus, args, work / "phase1")
        model.save_pretrained(str(done1))
        report.write_text(json.dumps(log, indent=1), encoding="utf-8")
    elif "corpus" in phases:
        print(f"phase 1 is done ({done1}); not training it again", flush=True)

    if "format" in phases:
        if model is None:
            model, tokenizer = load_model(args, adapter=done1 if (done1 / "adapter_config.json").exists() else None)
        tok = getattr(tokenizer, "tokenizer", tokenizer)
        fmt, general = load_chats(args.data, FORMAT), load_chats(args.data, ["general"])
        if len(general) < len(fmt):
            print(f"warning: {len(general)} general examples for {len(fmt)} format examples: the mix is not one to one", flush=True)
        chats = mix_format(fmt, general, args.seed)
        rows = [encode_chat(tok, m, args.seq_format) for m in chats]
        skipped = sum(r is None for r in rows)
        rows = [r for r in rows if r]
        prompt, completion = split_chat(tok, chats[0])
        print(f"format: {len(fmt)} format + {min(len(general), len(fmt))} general examples; {skipped} longer than {args.seq_format} tokens skipped, not cut; "
              f"{sum(len(r['input_ids']) for r in rows) / 1e6:.2f} M tokens\n  template check, prompt ends {prompt[-60:]!r}, completion starts {completion[:60]!r} and ends {completion[-20:]!r}", flush=True)
        if len(rows) < 0.5 * len(chats):
            raise SystemExit(f"more than half of the examples are longer than {args.seq_format} tokens: raise --seq-format or look at the data")
        log["phases"]["format"] = {**run_phase("format", model, tokenizer, rows, args.lr_format, args.epochs_format, args, work / "phase2"), "skipped_too_long": skipped}
        model.save_pretrained(str(out))
        tokenizer.save_pretrained(str(out))
        size = sum(p.stat().st_size for p in out.glob("adapter_model*")) / 2 ** 20
        print(f"adapter saved to {out} ({size:.0f} MB)", flush=True)

    if "restyle" in phases:
        model, tokenizer = load_model(args)                      # a fresh LoRA on the base: this adapter never starts from phase 1's
        tok = getattr(tokenizer, "tokenizer", tokenizer)
        data, _ = load_restyle(args.data)
        encoded, skipped = encode_restyle(tok, data, args.seq_restyle)
        prompt, completion = split_chat(tok, restyle_chat(data["train"][0]))
        print(f"restyle: {len(data['train'])} train + {len(data['held'])} held-out examples; {skipped['train']} + {skipped['held']} longer than {args.seq_restyle} tokens skipped, "
              f"not cut; {sum(len(r['input_ids']) for r in encoded['train']) / 1e6:.2f} M tokens to train on\n  template check, prompt ends {prompt[-60:]!r}, "
              f"completion starts {completion[:60]!r} and ends {completion[-20:]!r}", flush=True)
        if len(encoded["train"]) < 0.5 * len(data["train"]) or not encoded["held"]:
            raise SystemExit(f"more than half of the examples are longer than {args.seq_restyle} tokens (or none is held out): raise --seq-restyle or look at the data")
        log["phases"]["restyle"] = {**run_phase("restyle", model, tokenizer, encoded["train"], args.lr_restyle, args.epochs_restyle, args, work / "restyle", held=encoded["held"]),
                                    "skipped_too_long": skipped["train"], "heldout_skipped_too_long": skipped["held"]}
        done = log["phases"]["restyle"]
        print(f"restyle: train loss {done['final_loss']}, held-out loss {done['heldout_loss']} (per epoch: "
              + "; ".join(f"{e['epoch']}: {e['train_loss']} / {e['heldout_loss']}" for e in done["epochs"]) + ")", flush=True)
        model.save_pretrained(str(out))
        tokenizer.save_pretrained(str(out))
        size = sum(p.stat().st_size for p in out.glob("adapter_model*")) / 2 ** 20
        print(f"adapter saved to {out} ({size:.0f} MB)", flush=True)
    report.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"wrote {report}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", help="the Hugging Face model id of the base, the same Qwen as the installed GGUF (Codex fills it in)")
    p.add_argument("--data", default=str(DATA), help="the folder of corpus.jsonl, decisions.jsonl, ... (default mind/train)")
    p.add_argument("--out", help="where the adapter goes (default pc/out/hegel-lora, pc/out/hegelizer-lora for --phase restyle; -dryrun after it with --dry-run)")
    p.add_argument("--check-data", action="store_true", help="validate the data files and stop; needs no GPU")
    p.add_argument("--strict", action="store_true", help="with --check-data: both phases must have their data")
    p.add_argument("--dry-run", action="store_true", help="five steps of each phase, into hegel-lora-dryrun (hegelizer-lora-dryrun): proves the setup")
    p.add_argument("--resume", action="store_true", help="carry on from the last checkpoint of the phase that was running")
    p.add_argument("--phase", choices=["both", "corpus", "format", "restyle"], default="both",
                   help="both is corpus and format; restyle is the Hegelizer, a separate adapter on hegelizer.jsonl (pc/HEGELIZER.md)")
    p.add_argument("--seq-corpus", type=int, default=2048, help="tokens per block in phase 1 (default 2048)")
    p.add_argument("--seq-format", type=int, default=4096, help="longest example in phase 2 (default 4096: the soul and a situation alone are about 2,300 tokens)")
    p.add_argument("--seq-restyle", type=int, default=SEQ_RESTYLE, help="longest example in the restyle phase (default 1024: a unit of 250 words and its plain version are about 700 tokens)")
    p.add_argument("--rank", type=int, default=32)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--bf16", action="store_true", help="a 16-bit LoRA instead of QLoRA: over 36 GB for Qwen3.8-27B, so only on a rented GPU")
    p.add_argument("--text-only", action="store_true", help="load Qwen's language model without the unused vision encoder for text training")
    p.add_argument("--loss-target-gib", type=float, help="explicit Unsloth fused loss chunk memory budget in GiB")
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--accum", type=int, default=16, help="gradient accumulation steps (default 16)")
    p.add_argument("--lr-corpus", type=float, default=1e-4)
    p.add_argument("--lr-format", type=float, default=5e-5)
    p.add_argument("--lr-restyle", type=float, default=2e-4, help="the restyle phase's rate (default 2e-4: a short LoRA SFT run wants about ten times a full fine-tune's rate)")
    p.add_argument("--epochs-corpus", type=int, default=1)
    p.add_argument("--epochs-format", type=int, default=2)
    p.add_argument("--epochs-restyle", type=int, default=2)
    p.add_argument("--save-steps", type=int, default=25, help="a checkpoint every this many optimizer steps (default 25)")
    p.add_argument("--seed", type=int, default=3407)
    args = p.parse_args(argv)
    if args.loss_target_gib is not None and (not math.isfinite(args.loss_target_gib) or args.loss_target_gib <= 0):
        p.error("--loss-target-gib must be a finite positive number")
    if args.check_data:
        ok, _ = check_data(args.data, args.seq_corpus, args.seq_format, strict=args.strict, phase=args.phase, seq_restyle=args.seq_restyle)
        return 0 if ok else 1
    if not args.base:
        p.error("--base is required (the model id), except with --check-data")
    train(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
