#!/usr/bin/env python3
"""Train Hegel's LoRA: one adapter, two phases, on the PC (WSL2, RTX 3090). The runbook is pc/TRAINING.md.

    python3 pc/train_hegel.py --check-data                    # validate mind/train/*.jsonl; needs no GPU and no torch
    python3 pc/train_hegel.py --base <base id> --dry-run      # five steps of each phase: proves the setup, prints VRAM and a time projection
    python3 pc/train_hegel.py --base <base id>                # the real run, into pc/out/hegel-lora/
    python3 pc/train_hegel.py --base <base id> --resume       # carry on after a crash, from the last checkpoint

<base id> is the Hugging Face repo of exactly the Qwen that the PC serves as a GGUF (pc/TRAINING.md, step 3).

Phase 1, corpus: continued pretraining on corpus.jsonl (his books), plain causal-LM loss, the documents joined into blocks of 2048 tokens.
Phase 2, format: SFT on decisions, plans, writings and voices (what the world asks of him), mixed one to one with general.jsonl, loss on the
final assistant turn of each example only. The prompt is rendered by the model's own chat template with thinking off, as the live server does it.
The same LoRA (r 32, alpha 32, every attention and MLP projection) carries on from one phase to the next. Base: a pre-quantized 4-bit repo of the same Qwen, or its 16-bit repo loaded in 4 bits (QLoRA).

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
from world import contract  # noqa: E402

DATA, OUT = REPO / "mind/train", HERE / "out"
CHAT_FILES = {"decisions": "decisions.jsonl", "plans": "plans.jsonl", "writings": "writings.jsonl", "voices": "voices.jsonl", "general": "general.jsonl"}
FORMAT = ("decisions", "plans", "writings", "voices")        # what the world asks of him: phase 2's own data
STAND_IN = ("(rehearsal)", "(stub)")                         # a stand-in mind's marks: such text is not training data
ATTENTION_MLP = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
LINEAR_ATTENTION = ["in_proj_qkv", "in_proj_z", "out_proj"]  # the gated-delta-net layers of Qwen3.5/3.6; llama.cpp's LoRA conversion may not take them
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


def check_data(data, seq_corpus, seq_format, strict=False, say=print):
    """Validate the files of `data`. Returns (ok, ready): ok is False if any line is bad (or, with strict, a file is missing), ready says which
    phases have what they need. Nothing here needs torch."""
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
    """The base in 4 bits with a fresh LoRA, or (adapter given) with phase 1's weights put into that LoRA, trainable."""
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(model_name=args.base, max_seq_length=max(args.seq_corpus, args.seq_format),
                                                         dtype=None, load_in_4bit=True)
    model = FastLanguageModel.get_peft_model(
        model, r=args.rank, lora_alpha=args.alpha, lora_dropout=0, bias="none", random_state=args.seed,
        target_modules=ATTENTION_MLP + (LINEAR_ATTENTION if args.targets == "all" else []), use_gradient_checkpointing="unsloth")
    if adapter:
        # The same LoRA built afresh and filled with phase 1's weights: loading the adapter folder itself can come back frozen.
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
        result = set_peft_model_state_dict(model, load_file(str(Path(adapter) / "adapter_model.safetensors")))
        missing = [k for k in getattr(result, "missing_keys", []) if "lora_" in k]
        if missing:
            raise SystemExit(f"phase 1's adapter does not fit this LoRA ({len(missing)} weights missing, e.g. {missing[0]}): were --rank, --alpha or --targets "
                             "changed between the phases? Report this to Welt.")
        print(f"phase 1's adapter loaded from {adapter}", flush=True)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if not trainable:
        raise SystemExit("the adapter was loaded frozen: nothing to train. Report this to Welt.")
    print(f"LoRA r={args.rank} alpha={args.alpha}: {trainable / 1e6:.1f} M trainable parameters; {vram()}", flush=True)
    return model, tokenizer


def encode_all(tokenizer, texts):
    tok = getattr(tokenizer, "tokenizer", tokenizer)             # a processor wraps the text tokenizer
    ids = []
    for i in range(0, len(texts), 256):
        ids += tok(texts[i:i + 256], add_special_tokens=False)["input_ids"]
    return tok, ids


def run_phase(name, model, tokenizer, rows, lr, epochs, args, folder):
    """Train `model` on rows (dicts of input_ids, labels, attention_mask); returns {steps, loss, minutes, peak GiB}. Checkpoints go to folder."""
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
    seen = {"loss": None, "times": [], "t0": time.time()}

    class Report(TrainerCallback):
        def on_log(self, a, state, control, logs=None, **kw):
            if logs and "loss" in logs:
                seen["loss"] = logs["loss"]
                seen["times"].append(time.time())
                print(f"[{name}] step {state.global_step}/{state.max_steps}  loss {logs['loss']:.4f}  lr {logs.get('learning_rate', 0):.2e}  "
                      f"{(seen['times'][-1] - seen['t0']) / 60:.1f} min  {vram()}", flush=True)

    targs = TrainingArguments(
        output_dir=str(folder), per_device_train_batch_size=args.batch, gradient_accumulation_steps=args.accum, learning_rate=lr, num_train_epochs=epochs,
        max_steps=steps if args.dry_run else -1, lr_scheduler_type="cosine", warmup_steps=max(1, round(0.03 * steps)), weight_decay=0.0, max_grad_norm=1.0,
        optim="adamw_8bit", bf16=True, logging_steps=1, save_strategy="steps", save_steps=2 if args.dry_run else args.save_steps, save_total_limit=2,
        report_to="none", seed=args.seed, remove_unused_columns=False, disable_tqdm=True)
    trainer = Trainer(model=model, args=targs, train_dataset=Dataset.from_list(rows), processing_class=tok,
                      data_collator=DataCollatorForSeq2Seq(tokenizer=tok, padding=True, label_pad_token_id=-100), callbacks=[Report()])
    torch.cuda.reset_peak_memory_stats()
    print(f"[{name}] {len(rows)} sequences, {planned} steps planned" + (f", running {steps} (dry run)" if args.dry_run else "") + f", lr {lr}, {epochs} epoch(s)"
          + (f", resuming from {Path(last).name}" if last else ""), flush=True)
    trainer.train(resume_from_checkpoint=last)
    minutes = (time.time() - seen["t0"]) / 60
    gaps = [b - a for a, b in zip(seen["times"], seen["times"][1:])]
    each = sum(gaps[1:] or gaps or [0]) / max(1, len(gaps[1:] or gaps))        # the first step is slower: it warms up
    print(f"[{name}] done in {minutes:.1f} min; {vram()}", flush=True)
    if args.dry_run and each:
        print(f"[{name}] projection: {each:.0f} s per step x {planned} steps = {each * planned / 3600:.1f} h", flush=True)
    return {"steps": steps, "planned_steps": planned, "final_loss": seen["loss"], "minutes": round(minutes, 1), "seconds_per_step": round(each, 1),
            "peak_vram_gib": round(torch.cuda.max_memory_allocated() / 2 ** 30, 1)}


def versions():
    import importlib.metadata as md
    out = {}
    for p in ("torch", "transformers", "unsloth", "unsloth_zoo", "peft", "trl", "datasets", "bitsandbytes", "accelerate"):
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = None
    return out


def train(args):
    out = Path(args.out) if args.out else OUT / ("hegel-lora-dryrun" if args.dry_run else "hegel-lora")
    work, report = out / "work", out / "training.json"
    if args.dry_run and out.exists():
        shutil.rmtree(out)                                       # a dry run is disposable; an old one must not look like progress
    if (out / "adapter_model.safetensors").exists():
        raise SystemExit(f"{out} already holds a finished adapter. Move it away to train again.")
    out.mkdir(parents=True, exist_ok=True)
    ok, ready = check_data(args.data, args.seq_corpus, args.seq_format, strict=args.phase == "both")
    if not ok:
        raise SystemExit("fix the data first (python3 pc/train_hegel.py --check-data)")
    phases = ["corpus", "format"] if args.phase == "both" else [args.phase]
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
    report.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"wrote {report}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", help="the Hugging Face model id of the base, the same Qwen as the installed GGUF (Codex fills it in)")
    p.add_argument("--data", default=str(DATA), help="the folder of corpus.jsonl, decisions.jsonl, ... (default mind/train)")
    p.add_argument("--out", help="where the adapter goes (default pc/out/hegel-lora, or hegel-lora-dryrun with --dry-run)")
    p.add_argument("--check-data", action="store_true", help="validate the data files and stop; needs no GPU")
    p.add_argument("--strict", action="store_true", help="with --check-data: both phases must have their data")
    p.add_argument("--dry-run", action="store_true", help="five steps of each phase, into hegel-lora-dryrun: proves the setup")
    p.add_argument("--resume", action="store_true", help="carry on from the last checkpoint of the phase that was running")
    p.add_argument("--phase", choices=["both", "corpus", "format"], default="both")
    p.add_argument("--seq-corpus", type=int, default=2048, help="tokens per block in phase 1 (default 2048)")
    p.add_argument("--seq-format", type=int, default=4096, help="longest example in phase 2 (default 4096: the soul and a situation alone are about 2,300 tokens)")
    p.add_argument("--rank", type=int, default=32)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--targets", choices=["standard", "all"], default="standard", help="'all' adds the linear-attention projections (llama.cpp may not convert them)")
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--accum", type=int, default=16, help="gradient accumulation steps (default 16)")
    p.add_argument("--lr-corpus", type=float, default=1e-4)
    p.add_argument("--lr-format", type=float, default=5e-5)
    p.add_argument("--epochs-corpus", type=int, default=1)
    p.add_argument("--epochs-format", type=int, default=2)
    p.add_argument("--save-steps", type=int, default=25, help="a checkpoint every this many optimizer steps (default 25)")
    p.add_argument("--seed", type=int, default=3407)
    args = p.parse_args(argv)
    if args.check_data:
        ok, _ = check_data(args.data, args.seq_corpus, args.seq_format, strict=args.strict)
        return 0 if ok else 1
    if not args.base:
        p.error("--base is required (the model id), except with --check-data")
    train(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
