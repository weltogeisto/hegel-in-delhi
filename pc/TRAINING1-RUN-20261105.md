# Training 1: the run that has to work

Welt, 5 November 2026: Astra runs Training 1 (the Hegelizer, round two, `pc/T46.md`) again, from step 0, and this time it has to work. Claude wrote this runbook and reviews each stage before the next one. Nothing here changes the data, the seal, the bars or the data rule.

## What failed, and what stops it now

| When | What happened | What prevents it now |
|---|---|---|
| 4 Nov, 22:50 | The GPU check ran after `import unsloth` and counted the trainer's own memory as busy. | The admission check runs before Python starts. It gates on `llama-server` and memory used, not on any process at all. |
| 5 Nov, from step 101 | `generate` in the step-100 evaluation left gradient checkpointing off. The memory spilled into shared RAM, and each step took 5 minutes. | PR #8, merged at `c272095`. The launcher also stops the run if the step time jumps after an evaluation. |
| 5 Nov, 15:32 | A restart supervisor read the paths from a copied intent file, while the trainer wrote to the original. | No supervisor and no restarts: one run from step 0 to the end. Every path comes from one intent file, written once and never copied. |

The pattern: each failure sat in tooling that had never run end to end before the long window. So every link in the chain runs once in a rehearsal before the night, phase C included, because no run has reached it yet.

## Rules for this run

- **One launcher, in the repo, reviewed.** `pc/run_training1.py` on a `codex/` branch, with tests, merged before the rehearsal. Nothing else drives the run: no supervisor, no automatic restarts, no second copy of the intent.
- **New output directories only.** Keep everything earlier: the failed runs, checkpoints 100 and 200, phase 0's results, all receipts.
- **No improvising at night.** On any surprise the launcher stops, restores Qwen and the timer, and writes why. The fix comes the next day, reviewed.
- **Blindness.** The private T45 plan, its key, the confirmation release and the blind sheets stay unopened by anyone but the tools. Claude judges 20 of the pairs.
- **Limits.** No new packages, and no power, firewall, network or driver settings. The Power Guard is Welt's.
- **Reporting on PR #1:** done, blocked or a question. Numbers go in a file.

## Stage 1 · The launcher PR (no GPU)

`pc/run_training1.py` does these steps in order, logs each one with a timestamp to the run's folder, and stops at the first failure:

1. **Intent.** Write `INTENT.json` once: the commit, the base model, the frozen data, `CHAPTER-SPLITS-V2.json`, the T45 `SEAL.json`, the new output directory, the 8082 command, and the deadline for restoring. Every later step reads only this file.
2. **Hand-over.** Stop Hegel's timer on the Pi, then the 8082 server.
3. **Admission,** in a fresh process with no torch: `nvidia-smi` shows no `llama-server` and under 2 GiB in use. Save the snapshot either way.
4. **Phase B:** `pc/train_hegel.py --round-two --phase restyle --goldfish` with the intent's paths, and its log teed to the run's folder.
5. **Step-time guard.** It watches the log, and stops the run (then goes to step 8) if either holds:
   - a step after an evaluation takes more than 1.5 times the median of the 20 steps before it;
   - the projected end is past the deadline less 30 minutes.
6. **Phase C,** straight after B, if the deadline allows:
   - convert the chosen checkpoint (`convert_lora_to_gguf.py`, as in `pc/HEGELIZER.md`);
   - serve plain Qwen with the adapter at a per-request scale;
   - run the new test, both arms, then the dashboard (`pc/T46.md`).
   If C won't fit, keep B's output and stop cleanly; C goes in the next window.
7. **Sheets.** Write Welt's 20 pairs. Claude's 20 wait for Claude.
8. **Restore, always,** including after a failure or a stop: plain Qwen on 8082 (three 16K slots, the saved command), check that `/health` answers, then start the Pi timer.

The tests cover the order of the steps, the admission check on saved snapshots (an idle desktop passes, `llama-server` fails, the run's own PID is never counted), the step-time guard on recorded logs, the deadline arithmetic, and restore after a failure at each step.

## Stage 2 · Rehearsal of the whole chain (about 30 minutes, in a window Welt grants)

Run the launcher in rehearsal mode: `--dry-run --eval-steps 2`, a new output directory, and phase C on the dry run's adapter with only 2 of the 40 test cases.

1. The converted dry-run adapter must load in llama-server and answer one restyle at scale 0.8 and one at 0.
2. Restore. By day, Hegel's next natural tick must have `mind.source` = `mind`. By night, when his ticks make no model calls, `curl` from the Pi to `http://192.168.188.21:8082/health` must answer, and so must one 1-token chat request from the Pi with the saved model name; Claude checks his first awake tick in the morning. Never force a tick.

Resume isn't rehearsed: a real-mode `--resume` already ran live on 5 November (checkpoint 100 to 200), and this run has no restarts. `pc/train_hegel.py` stays unchanged.

**It passes when all of these hold, posted with their numbers:**
- the steps after the evaluation run within 1.5 times the steps before it;
- PyTorch never reserves more than the card's 24 GiB. The recipe runs at about 23.7 GiB, so VRAM near the top is normal; a spill shows as slower steps. Never stop a run on VRAM alone;
- the adapter loads and answers;
- Qwen answers on 8082;
- the restore check passes (his next tick by day, the Pi's health and 1-token checks by night);
- the time projection for 517 steps plus phase C fits in one night.

## Stage 3 · The night

1. Tell Welt which night the day before; he approves the Power Guard prompt for an 08:30 shutdown.
2. At 21:00, once Hegel is asleep, start the launcher with the deadline at 07:30.
3. Expect phase B in about 3 to 4 hours (517 steps at about 19 seconds, plus five evaluations), then phase C in about 2.
4. In the morning, post one comment on PR #1: done, the five KPIs against their bars with KPI 4 named, the dashboard's path, and whether the sheets are ready. If anything stopped the run, give the launcher's reason and where it stopped.

If KPI 4 (nothing copied) fails, the next window trains the same data without `--goldfish`, so that we learn what goldfish does.
