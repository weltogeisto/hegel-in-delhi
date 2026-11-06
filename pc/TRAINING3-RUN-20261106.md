# Training 3: his decisions, the run

Welt, 6 November 2026: go for Training 3 (`pc/TRAINING-3.md`), by day, prepared while T39 runs. It trains his decision calls to avoid what the world refuses and what repeats, using pairs that the world's own checks label. The voice adapter is set aside: two rounds have not beaten plain Qwen.

The discipline of Training 1's last run holds: a reviewed launcher, a rehearsal of the whole chain, guards that stop and restore, and nothing that runs unwatched at night.

## 1 · The sampler (Astra, a `codex/` PR, no GPU to build)

**Situations,** about 500:
- **Shadow (118):** every decision with `mind.source` = `mind` on shadow days other than 12 and 27, replayed from its saved situation as T39 does.
- **Rehearsal (the rest):** new days from `tools/train_data.py --distill`'s machinery, on dates from 10 November onwards, never T9's.

**Candidates:**
- four per situation from plain Qwen on the live decision schema, with seeds 1831, 2718, 3141 and 4271 and the live temperature;
- `World.check` judges each one; keep `accepted`, `errors` and `warnings`;
- `earlier_thoughts` are that day's thoughts before the step, from the record.

**Output:** one JSONL row per situation, in the format at the top of `tools/decision_pairs.py`.

**GPU:** the spare slot beside Hegel, with his steps as fast as now (phase A's latency guard). About 3 to 4 hours, and it can start as soon as T39 is done.

## 2 · The labels (Claude's code, on main)

```sh
python3 tools/decision_pairs.py --candidates SAMPLER.jsonl --out PAIRS.jsonl
```

- **Chosen:** accepted by the world, with no four-word phrase shared with the day's earlier thoughts (T9's rule).
- **Rejected:** refused by the world, or repeating.
- **Matching:** one pair per situation, length-matched within 20%, in seed order.

No model's taste picks anything. Post the stats file on PR #1. If there are fewer than 200 pairs, stop and report.

## 3 · The trainer (Astra, a `codex/` PR with tests)

- **DPO** with TRL's `DPOTrainer`. Check that it came with Unsloth; a new package is Welt's call. ORPO only if the rehearsal shows DPO won't fit in memory.
- **Settings:** LoRA rank 16 and alpha 32 on the decision calls only; beta 0.1, learning rate 1e-5, one epoch, the reference log-probs computed in advance.
- **Prompt length:** never truncate a prompt. Leave out the pairs that don't fit the length cap and report how many.
- **The run** goes through a launcher with Training 1's guarantees, by reusing `pc/run_training1.py`'s parts:
  - admission before Python;
  - one intent;
  - the step-time and deadline guards;
  - restore on every exit, detached.

## 4 · Rehearsal, by day

A few steps with one evaluation:
- measure the seconds per pair and the peak memory;
- the convert-and-serve check: the adapter answers one decision at scale 1 and one at 0;
- restore.

Project the full run from the measurements. If it doesn't fit one day's window, take a seed-1831 random subset of the pairs. The choice is fixed before training and is never made by results.

## 5 · The real run and the test, by day

Hegel pauses for the training and the test only. Then the test, on T39's frozen case manifest (`1c7105a…`, with the same seeds), against T39's better arm:
- the echo share falls by at least a third;
- contradictions and statements as fact per 100 sentences are no worse;
- argument and voice are within 0.25, by Claude's blind scores.

Only a pass puts the adapter on his decision calls. Voices, the owl and his writing keep scale 0.
