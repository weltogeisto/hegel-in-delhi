#!/usr/bin/env python3
"""Training 4: a plain supervised trainer for his letters (pc/TRAINING-4.md, "Training 4 · His letters").

    python3 pc/train_letters.py --check-data --train T.jsonl --heldout H.jsonl     # validate the two files; needs no GPU and no torch
    python3 pc/train_letters.py --base <id> --train T.jsonl --heldout H.jsonl --out NEW_DIR
    python3 pc/train_letters.py ... --max-steps 3 --eval-steps 2                   # the rehearsal: three optimizer steps and an evaluation

Rows are JSONL objects {"id", "prompt", "target"}. The prompt is plain text that ends in a blank line; the target is the letter that follows it.
This is plain completion: no chat template. One example is tokens(prompt) + tokens(target) + EOS, and the loss is on the target and the EOS only
(every prompt token has the label -100).

BOS. Both parts are tokenised with add_special_tokens=False, as the restyle and format phases of pc/train_hegel.py do, so the tokenizer never adds a
mark of its own. This file then puts the tokenizer's BOS in front once, if the tokenizer has one (Qwen has none, so then nothing is added), and
the EOS at the end once. The prompt and the target are tokenised apart; the prompt ends in a blank line, so no token can straddle the join, and the
served model also sees the prompt alone and then writes on.

Never truncated. An example longer than --seq tokens is left out whole; its id and length go into RESULT.json. If more than 5% of the training rows
would be left out, the run stops before the model is loaded.

--goldfish masks about one in --goldfish-k of the target labels by a hash of the preceding --goldfish-context target tokens
(pc/restyle_round2.goldfish_labels). The held-out loss never has the mask.

Schedule: cosine, 5% warmup, the effective batch is --batch x --accum, at most --epochs passes, --max-steps caps the optimizer steps. Every
--eval-steps steps the mean negative log-likelihood per target token on the held-out rows is measured; nothing is generated during training (an
earlier run broke because `generate` inside training left gradient checkpointing off). The run stops early when that loss has not improved for
--patience evaluations. Every --save-steps steps the adapter goes to OUT/checkpoint-<step>; the final adapter goes to OUT/final before anything is
counted. OUT must not exist. TRAINING-LOG.jsonl and RESULT.json are written into it: the best step is the lowest held-out loss, chosen by the
machine.

A backend may also have an `event(kind, **fields)` method: the loop calls it with step_begin, step, evaluate_begin, evaluate_end, checkpoint_begin
and checkpoint (pc/run_training4.py uses it to time the run). A backend without it is fine.

torch, unsloth and transformers are imported only inside TorchBackend, so that this file imports, --check-data runs and the tests run anywhere.
The training loop itself is plain Python over a small backend; tests pass a fake one."""
import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
from pc.restyle_round2 import goldfish_labels  # noqa: E402

FIELDS = ("id", "prompt", "target")
MAX_EXCLUDED_SHARE = 0.05
WARMUP_SHARE = 0.05


class DataError(ValueError):
    """The input files are not usable."""


# ── the data (plain Python) ─────────────────────────────────────────
def read_rows(path):
    """The rows of a JSONL file, each checked for its three fields. Raises DataError with the file and line."""
    rows = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as e:
        raise DataError(f"cannot read {path}: {e}")
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            raise DataError(f"{Path(path).name}:{n}: not JSON")
        if not isinstance(row, dict):
            raise DataError(f"{Path(path).name}:{n}: not an object")
        for key in FIELDS:
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise DataError(f"{Path(path).name}:{n}: '{key}' must be a non-empty string")
        if not row["prompt"].endswith("\n\n"):
            raise DataError(f"{Path(path).name}:{n}: the prompt must end in a blank line")
        rows.append({k: row[k] for k in FIELDS})
    return rows


def validate(train_path, heldout_path):
    """(train_rows, heldout_rows): both files read and cross-checked. Ids are unique within and across the files, and no target is in both."""
    train, held = read_rows(train_path), read_rows(heldout_path)
    if not train or not held:
        raise DataError("both files need at least one row")
    for name, rows in (("train", train), ("heldout", held)):
        seen = set()
        for r in rows:
            if r["id"] in seen:
                raise DataError(f"a second row with id {r['id']!r} in the {name} file")
            seen.add(r["id"])
    both = {r["id"] for r in train} & {r["id"] for r in held}
    if both:
        raise DataError(f"id {sorted(both)[0]!r} is in both files" + (f" (and {len(both) - 1} more)" if len(both) > 1 else ""))
    shared = {r["target"] for r in train} & {r["target"] for r in held}
    if shared:
        raise DataError(f"{len(shared)} target(s) are in both files, e.g. the one of id "
                        f"{next(r['id'] for r in held if r['target'] in shared)!r}")
    return train, held


def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_data(train_path, heldout_path, tokenizer=None, seq=1536, say=print):
    """True if the files are good. Token lengths need a tokenizer: without one that check is skipped, and the report says so."""
    try:
        train, held = validate(train_path, heldout_path)
    except DataError as e:
        say("letters data NOT ok: " + str(e))
        return False
    say(f"{len(train)} train rows, {len(held)} held-out rows; ids unique, no id and no target in both files")
    if tokenizer is None:
        say(f"token lengths NOT checked: no tokenizer here (needs the model's tokenizer; at most {seq} tokens per example, never truncated)")
        return True
    ok = True
    for name, rows in (("train", train), ("heldout", held)):
        kept, left_out = encode_rows(tokenizer, rows, seq)
        say(f"{name}: {len(kept)} fit in {seq} tokens, {len(left_out)} would be left out")
        if name == "train" and too_many_excluded(len(left_out), len(rows)):
            say(f"letters data NOT ok: more than {MAX_EXCLUDED_SHARE:.0%} of the training rows are too long")
            ok = False
    return ok


# ── the examples ────────────────────────────────────────────────────
def encode_row(tok, row, seq):
    """{id, input_ids, labels, attention_mask} for one row, or None if it has more than `seq` tokens (never cut).
    Labels are -100 on a BOS (if the tokenizer has one) and on every prompt token; they are the tokens on the target and the EOS."""
    prompt = tok(row["prompt"], add_special_tokens=False)["input_ids"]
    target = tok(row["target"], add_special_tokens=False)["input_ids"]
    eos = tok.eos_token_id
    if eos is None:
        raise ValueError("the tokenizer has no EOS token")
    bos = [tok.bos_token_id] if getattr(tok, "bos_token_id", None) is not None else []
    head = bos + list(prompt)
    body = list(target) + [eos]
    ids = head + body
    if len(ids) > seq:
        return None
    return {"id": row["id"], "input_ids": ids, "labels": [-100] * len(head) + body, "attention_mask": [1] * len(ids)}


def encode_rows(tok, rows, seq):
    """(kept examples, [{"id", "tokens"} of the rows that were longer than seq])."""
    kept, left_out = [], []
    for row in rows:
        got = encode_row(tok, row, seq)
        if got is None:
            left_out.append({"id": row["id"], "tokens": token_count(tok, row)})
        else:
            kept.append(got)
    return kept, left_out


def token_count(tok, row):
    n = len(tok(row["prompt"], add_special_tokens=False)["input_ids"]) + len(tok(row["target"], add_special_tokens=False)["input_ids"]) + 1
    return n + (1 if getattr(tok, "bos_token_id", None) is not None else 0)


def too_many_excluded(excluded, total):
    return total > 0 and excluded / total > MAX_EXCLUDED_SHARE


def with_goldfish(rows, k, context):
    """The training rows with the goldfish mask on their labels (the held-out rows never go through here)."""
    return [dict(r, labels=goldfish_labels(r["input_ids"], r["labels"], k, context)) for r in rows]


def target_tokens(row):
    """The labels that the loss counts: the shifted labels that are not -100."""
    return sum(1 for x in row["labels"][1:] if x != -100)


# ── the schedule ────────────────────────────────────────────────────
def total_steps(n_rows, batch, accum, epochs, max_steps=None):
    planned = math.ceil(n_rows / (batch * accum)) * epochs
    return min(planned, max_steps) if max_steps else planned


def lr_at(step, total, peak):
    """The rate for the optimizer update number `step` (counted from 0): linear warmup over 5% of the steps, then a cosine down to zero."""
    warm = max(1, round(WARMUP_SHARE * total))
    if step < warm:
        return peak * (step + 1) / warm
    return peak * 0.5 * (1 + math.cos(math.pi * (step - warm) / max(1, total - warm)))


def groups(order, size):
    return [order[i:i + size] for i in range(0, len(order), size)]


# ── the loop ────────────────────────────────────────────────────────
class Log:
    def __init__(self, path):
        self.path = path

    def add(self, **row):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()


def evaluate(backend, held, batch):
    """Mean negative log-likelihood per target token over all the held-out rows, without the goldfish mask."""
    total = count = 0.0
    for i in range(0, len(held), batch):
        s, n = backend.eval_nll(held[i:i + batch])
        total, count = total + s, count + n
    if not count:
        raise ValueError("the held-out rows have no target tokens")
    return total / count


def run_loop(args, backend, train_rows, held_rows, out, log, say=print):
    """Train, evaluate, checkpoint and maybe stop early. Returns {steps, stopped, evaluations, best}."""
    total = total_steps(len(train_rows), args.batch, args.accum, args.epochs, args.max_steps)
    size = args.batch * args.accum
    rng = random.Random(args.seed)
    evaluations, best, flat, step, stopped = [], None, 0, 0, "schedule finished"
    t0 = time.monotonic()
    emit = getattr(backend, "event", None) or (lambda kind, **fields: None)   # a launcher's backend may time steps, evaluations and saves
    say(f"{len(train_rows)} examples, {total} optimizer steps planned, effective batch {size}")
    while step < total and stopped == "schedule finished":
        order = list(range(len(train_rows)))
        rng.shuffle(order)
        for chunk in groups(order, size):
            if step >= total:
                break
            batch_rows = [train_rows[i] for i in chunk]
            divisor = sum(target_tokens(r) for r in batch_rows)
            lr = lr_at(step, total, args.lr)
            loss = 0.0
            emit("step_begin", step=step + 1)
            for micro in groups(batch_rows, args.batch):
                loss += backend.train_micro(micro, divisor)
            backend.optimizer_step(lr)
            step += 1
            emit("step", step=step)
            log.add(step=step, train_loss=loss / divisor, lr=lr, seconds=round(time.monotonic() - t0, 3))
            say(f"step {step}/{total}  loss {loss / divisor:.4f}  lr {lr:.2e}")
            if step % args.save_steps == 0:
                emit("checkpoint_begin", step=step)
                backend.save(out / f"checkpoint-{step}")
                emit("checkpoint", step=step)
            if step % args.eval_steps == 0 or step == total:
                emit("evaluate_begin", step=step)
                held_loss = evaluate(backend, held_rows, args.batch)
                emit("evaluate_end", step=step)
                evaluations.append({"step": step, "heldout_loss": held_loss})
                log.add(step=step, heldout_loss=held_loss)
                say(f"step {step}: held-out loss {held_loss:.4f}")
                if best is None or held_loss < best["heldout_loss"]:
                    best, flat = {"step": step, "heldout_loss": held_loss}, 0
                else:
                    flat += 1
                if flat >= args.patience and step < total:
                    stopped = f"early stop: no improvement in {args.patience} evaluations"
                    break
    if stopped == "schedule finished" and args.max_steps and total < total_steps(len(train_rows), args.batch, args.accum, args.epochs):
        stopped = "--max-steps reached"
    return {"steps": step, "planned_steps": total, "stopped": stopped, "evaluations": evaluations, "best": best}


# ── the whole run ───────────────────────────────────────────────────
def hyperparameters(args):
    keys = ("base", "rank", "alpha", "lr", "epochs", "batch", "accum", "seq", "save_steps", "eval_steps", "patience",
            "goldfish", "goldfish_k", "goldfish_context", "seed", "max_steps", "text_only", "loss_target_gib")
    return {k: getattr(args, k) for k in keys}


def train(args, backend=None, say=print):
    """The run. `backend` is TorchBackend unless a test passes a fake. Returns the RESULT.json content."""
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} already exists: new output directories only")
    train_rows, held_rows = validate(args.train, args.heldout)
    backend = backend or TorchBackend()
    tok = backend.load_tokenizer(args)
    train_enc, train_out = encode_rows(tok, train_rows, args.seq)
    held_enc, held_out = encode_rows(tok, held_rows, args.seq)
    if too_many_excluded(len(train_out), len(train_rows)):
        raise SystemExit(f"{len(train_out)} of {len(train_rows)} training rows are longer than {args.seq} tokens (over {MAX_EXCLUDED_SHARE:.0%}): "
                         "raise --seq or fix the data; nothing is truncated")
    if not train_enc or not held_enc:
        raise SystemExit("no training or no held-out examples fit the sequence length")
    if args.goldfish:
        train_enc = with_goldfish(train_enc, args.goldfish_k, args.goldfish_context)
    out.mkdir(parents=True)
    log = Log(out / "TRAINING-LOG.jsonl")
    backend.load_model(args)
    start = time.monotonic()
    run = run_loop(args, backend, train_enc, held_enc, out, log, say)
    backend.save(out / "final")                                  # saved before anything else is counted or checked
    best = run["best"]
    best_path = out / f"checkpoint-{best['step']}" if best and (out / f"checkpoint-{best['step']}").exists() else None
    result = {"best_step": best["step"] if best else None, "best_heldout_loss": best["heldout_loss"] if best else None,
              "best_checkpoint": best_path.name if best_path else None,
              "steps_run": run["steps"], "planned_steps": run["planned_steps"], "stopped": run["stopped"],
              "evaluations": run["evaluations"], "final_adapter": "final",
              "examples_used": {"train": len(train_enc), "heldout": len(held_enc)},
              "examples_excluded": {"train": train_out, "heldout": held_out},
              "input_sha256": {"train": filehash(args.train), "heldout": filehash(args.heldout)},
              "hyperparameters": hyperparameters(args), "wall_seconds": round(time.monotonic() - start, 1),
              "selection": "lowest held-out loss, by the machine; no reading"}
    (out / "RESULT.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


class TorchBackend:
    """The real thing. Every heavy import is inside a method. Not run by any test: the PC rehearsal is its test."""
    model = tokenizer = optimizer = None

    def load_tokenizer(self, args):
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(args.base)

    def load_model(self, args):
        import torch
        from pc import train_hegel
        self.torch = torch
        torch.manual_seed(args.seed)
        self.model, _ = train_hegel.load_model(args)            # QLoRA, LoRA on attention and MLP: the one definition
        import bitsandbytes as bnb
        params = [p for p in self.model.parameters() if p.requires_grad]
        self.params = params
        self.optimizer = bnb.optim.AdamW8bit(params, lr=args.lr, weight_decay=0.0)
        self.model.train()

    def _batch(self, rows):
        torch = self.torch
        device = next(self.model.parameters()).device
        width = max(len(r["input_ids"]) for r in rows)
        pad = lambda key, fill: torch.tensor([r[key] + [fill] * (width - len(r[key])) for r in rows], device=device)
        return {"input_ids": pad("input_ids", 0), "attention_mask": pad("attention_mask", 0), "labels": pad("labels", -100)}

    def _sum_nll(self, rows):
        """(summed negative log-likelihood tensor, number of target tokens) of one micro-batch. The model's own loss is the mean over those tokens."""
        n = sum(target_tokens(r) for r in rows)
        if not n:
            return None, 0
        with self.torch.autocast("cuda", dtype=self.torch.bfloat16):
            out = self.model(**self._batch(rows))
        return out.loss * n, n

    def train_micro(self, rows, divisor):
        total, n = self._sum_nll(rows)
        if total is None:
            return 0.0
        (total / divisor).backward()
        return float(total.detach())

    def optimizer_step(self, lr):
        self.torch.nn.utils.clip_grad_norm_(self.params, 1.0)
        for group in self.optimizer.param_groups:
            group["lr"] = lr
        self.optimizer.step()
        self.optimizer.zero_grad(set_to_none=True)

    def eval_nll(self, rows):
        self.model.eval()
        try:
            with self.torch.no_grad():
                total, n = self._sum_nll(rows)
        finally:
            self.model.train()                                   # no generate here: gradient checkpointing stays as it was
        return (float(total) if total is not None else 0.0), n

    def save(self, path):
        self.model.save_pretrained(str(path))


# ── the command line ────────────────────────────────────────────────
def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", help="the Hugging Face model id of the base, the same Qwen as the served GGUF")
    p.add_argument("--train", required=True, help="TRAIN.jsonl: {id, prompt, target}")
    p.add_argument("--heldout", required=True, help="HELDOUT.jsonl, the same shape")
    p.add_argument("--out", help="a NEW directory for the adapters and the records")
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--accum", type=int, default=8)
    p.add_argument("--seq", type=int, default=1536, help="longest example in tokens; longer ones are left out whole")
    p.add_argument("--save-steps", type=int, default=50)
    p.add_argument("--eval-steps", type=int, default=50)
    p.add_argument("--patience", type=int, default=3, help="stop after this many evaluations without a better held-out loss")
    p.add_argument("--goldfish", action="store_true", help="mask a hashed quarter of the target labels in training")
    p.add_argument("--goldfish-k", type=int, default=4)
    p.add_argument("--goldfish-context", type=int, default=13)
    p.add_argument("--seed", type=int, default=3407)
    p.add_argument("--max-steps", type=int, help="cap on optimizer steps (the rehearsal passes 3)")
    p.add_argument("--text-only", action="store_true", help="load the language model without the vision encoder")
    p.add_argument("--loss-target-gib", type=float, help="explicit Unsloth fused loss chunk memory budget in GiB")
    p.add_argument("--check-data", action="store_true", help="validate the two files and stop; needs no GPU and no torch")
    p.set_defaults(bf16=False)                                   # load_model reads it; this trainer is always QLoRA
    return p


def main(argv=None, backend=None, tokenizer=None):
    p = parser()
    args = p.parse_args(argv)
    for name in ("rank", "alpha", "epochs", "batch", "accum", "seq", "save_steps", "eval_steps", "patience", "goldfish_context"):
        if getattr(args, name) < 1:
            p.error(f"--{name.replace('_', '-')} must be positive")
    if args.goldfish_k < 2 or args.lr <= 0 or (args.max_steps is not None and args.max_steps < 1):
        p.error("goldfish k >= 2, a positive learning rate and a positive --max-steps are required")
    if args.loss_target_gib is not None and (not math.isfinite(args.loss_target_gib) or args.loss_target_gib <= 0):
        p.error("--loss-target-gib must be a finite positive number")
    if args.check_data:
        return 0 if check_data(args.train, args.heldout, tokenizer, args.seq) else 1
    if not args.base or not args.out:
        p.error("--base and --out are required, except with --check-data")
    try:
        train(args, backend)
    except DataError as e:
        print("letters data NOT ok: " + str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
