"""Training 3 data preparation. Standard library only; no model import here."""
import hashlib
import json
import math
import random
from datetime import date
from pathlib import Path

from tools import decision_pairs

SEED = 1831
MIN_PAIRS = 200
TARGET_MODULES = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
RECIPE = dict(rank=16, alpha=32, beta=0.1, learning_rate=1e-5, epochs=1,
              micro_batch=1, accumulation=8, seed=SEED,
              precompute_ref_log_probs=True, loss_type="sigmoid",
              prompt_truncation=False, completion_truncation=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_rows(raw):
    if raw and not raw.endswith(b"\n"):
        raise ValueError("torn JSONL tail; preserve and reconcile")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def validated_pairs(candidate_path, pairs_path, stats_path):
    """Verify labels against the preserved candidates without asking any model."""
    candidate_raw = Path(candidate_path).read_bytes()
    pair_raw = Path(pairs_path).read_bytes()
    stats = json.loads(Path(stats_path).read_bytes())
    if stats["candidates_sha256"] != sha(candidate_raw) or stats["pairs_sha256"] != sha(pair_raw):
        raise ValueError("pair or candidate digest differs")
    if stats.get("view") != "revised":
        raise ValueError("Training 3 trains on the revised labels only (Welt, 7 November); the legacy view is for comparison")
    candidates, pairs = read_rows(candidate_raw), read_rows(pair_raw)
    for row in candidates:
        if row["source"] == "rehearsal" and date.fromisoformat(row["date"]) < date(2026, 11, 10):
            raise ValueError("T9/old rehearsal cannot train")
        if tuple(c["seed"] for c in row["candidates"]) != (1831, 2718, 3141, 4271):
            raise ValueError("four frozen candidate seeds required")
        messages = row["messages"]
        if [m.get("role") for m in messages] != ["system", "user"]:
            raise ValueError("decision pairs require the original two-message prompt")
    expected, rebuilt = decision_pairs.build(candidates, view="revised")
    if pairs != expected or any(stats.get(k) != v for k, v in rebuilt.items()):
        raise ValueError("label output does not match the reviewed deterministic labeller")
    if len(pairs) < MIN_PAIRS:
        raise ValueError("fewer than 200 preference pairs; stop")
    return pairs, dict(candidates_sha256=sha(candidate_raw), pairs_sha256=sha(pair_raw),
                       situations=len(candidates), pairs=len(pairs))


def render_pair(pair, tokenizer, cap):
    """Match TRL 0.24 decoder-only tokenization, including the appended EOS.

    No prefix/suffix is sliced. A pair is either admitted whole or excluded whole.
    Returned text is exactly what the trainer tokenizes, avoiding a second chat
    template pass over conversational lists.
    """
    if type(cap) is not int or cap <= 1 or tokenizer.eos_token_id is None:
        raise ValueError("positive length cap and real EOS token required")
    messages = pair["prompt"]
    if [m.get("role") for m in messages] != ["system", "user"]:
        raise ValueError("not a decision prompt")
    prompt = tokenizer.apply_chat_template(messages, tokenize=False,
                                          add_generation_prompt=True, enable_thinking=False)
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("chat template did not produce a prompt")
    text = dict(prompt=prompt, chosen=pair["chosen"], rejected=pair["rejected"])
    tokens = {k: tokenizer(v, add_special_tokens=False)["input_ids"] for k, v in text.items()}
    counts = dict(prompt=len(tokens["prompt"]), chosen=len(tokens["chosen"]) + 1,
                  rejected=len(tokens["rejected"]) + 1)
    fits = counts["prompt"] + max(counts["chosen"], counts["rejected"]) <= cap
    return (dict(id=pair["id"], **text) if fits else None), counts


TURN_PROBE = "TURN-END-PROBE-1831"


def check_turn_end(tokenizer, messages):
    """The EOS that TRL appends to each completion must be the token that ends an assistant
    turn in the chat template, the one the server stops at; otherwise the adapter learns to
    end its answers with the wrong token. The training prompt must also be exactly the part of
    a rendered turn that comes before the answer."""
    eos = tokenizer.eos_token
    if not isinstance(eos, str) or not eos or tokenizer(eos, add_special_tokens=False)["input_ids"] != [tokenizer.eos_token_id]:
        raise ValueError("the EOS must be one special token")
    prompt = tokenizer.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True, enable_thinking=False)
    full = tokenizer.apply_chat_template(list(messages) + [dict(role="assistant", content=TURN_PROBE)],
                                         tokenize=False, enable_thinking=False)
    if not isinstance(full, str) or full.count(TURN_PROBE) != 1 or not full.startswith(prompt + TURN_PROBE):
        raise ValueError("the training prompt is not the template's own boundary before an answer")
    if not full[len(prompt) + len(TURN_PROBE):].startswith(eos):
        raise ValueError(f"the chat template ends an assistant turn with something other than the EOS {eos!r}")
    return eos


def fit_pairs(pairs, tokenizer, cap):
    kept, removed, lengths = [], [], {}
    seen = set()
    turn_end = check_turn_end(tokenizer, pairs[0]["prompt"]) if pairs else None
    for pair in pairs:
        if pair["id"] in seen:
            raise ValueError("duplicate pair")
        seen.add(pair["id"])
        row, counts = render_pair(pair, tokenizer, cap)
        lengths[pair["id"]] = counts
        if row is None:
            removed.append(pair["id"])
        else:
            kept.append(row)
    report = dict(length_cap=cap, completion_end_token=turn_end, original_pairs=len(pairs), admitted_pairs=len(kept),
                  excluded_whole_pair_ids=removed, lengths=lengths,
                  prompts_truncated=0, completions_truncated=0)
    # Return the exclusion report even on a failed size gate. The launcher writes
    # it before deciding whether a trainer may be constructed.
    return kept, report


def step_count(count):
    return math.ceil(count / (RECIPE["micro_batch"] * RECIPE["accumulation"]))


def measured_cost(count, seconds_per_pair, evaluation_seconds, conversion_and_test_seconds):
    values = (seconds_per_pair, evaluation_seconds, conversion_and_test_seconds)
    if any(not isinstance(x, (float, int)) or not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("invalid measured timing")
    if seconds_per_pair <= 0:
        raise ValueError("positive measured per-pair time required")
    # Measured pair time includes reference precomputation and training.
    return count * seconds_per_pair * 1.15 + evaluation_seconds * 1.15 + conversion_and_test_seconds


def choose_roster(rows, available_seconds, measured, seed=SEED):
    """Only the time budget may reduce a roster, before training starts."""
    if seed != SEED:
        raise ValueError("subset seed is frozen at 1831")
    if len(rows) < MIN_PAIRS:
        raise ValueError("fewer than 200 untruncated pairs; stop")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate pair ID")
    cost = lambda n: measured_cost(n, **measured)
    full_cost = cost(len(rows))
    if full_cost <= available_seconds:
        selected = rows
        reason = "full eligible roster fits"
    else:
        limit = max((n for n in range(MIN_PAIRS, len(rows)) if cost(n) <= available_seconds), default=0)
        if not limit:
            raise ValueError("a 200-pair run cannot fit; defer")
        picked = set(random.Random(SEED).sample(sorted(ids), limit))
        selected = [r for r in rows if r["id"] in picked]
        reason = "full roster exceeds measured day window; seed-1831 subset"
    return selected, dict(seed=SEED, selected_ids=[r["id"] for r in selected],
                          original_pairs=len(rows), selected_pairs=len(selected),
                          full_projected_seconds=full_cost,
                          selected_projected_seconds=cost(len(selected)), reason=reason)


def dpo_arguments(output, rehearsal=False):
    """All truncation switches are explicit; max_steps is rehearsal-only."""
    return dict(
        output_dir=str(output), beta=RECIPE["beta"], learning_rate=RECIPE["learning_rate"],
        num_train_epochs=1, max_steps=3 if rehearsal else -1,
        per_device_train_batch_size=1, gradient_accumulation_steps=8,
        per_device_eval_batch_size=1, precompute_ref_log_probs=True,
        precompute_ref_batch_size=1, max_prompt_length=None, max_completion_length=None,
        max_length=None, loss_type="sigmoid", seed=SEED, data_seed=SEED,
        bf16=True, optim="adamw_8bit", gradient_checkpointing=True,
        eval_strategy="steps" if rehearsal else "no", eval_steps=2,
        save_strategy="steps", save_steps=2 if rehearsal else 25,
        save_total_limit=None, report_to="none", logging_steps=1,
        remove_unused_columns=False, disable_tqdm=True)
