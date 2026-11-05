# Training 1 on the PC, run by a Claude session there

Welt, 5 November 2026: a Claude session on the PC runs Training 1 (the Hegelizer, round two, `pc/T46.md`) instead of Astra. Claude in the cloud wrote this brief and reviews your plan before the GPU is touched. Astra stands down from the GPU, the 8082 server and the Pi while you work.

Three attempts failed on 4 and 5 November, each in the run tooling around the trainer, never in the training: a GPU check that counted the trainer's own memory, gradient checkpointing left off after an evaluation (fixed in PR #8, merged at `c272095`), and a restart supervisor that looked in the wrong folder. So: run the documented commands directly, watch them yourself, and build no supervisor.

## Before anything

- **Not as administrator.** If this session runs elevated, stop and ask Welt to restart Claude normally. Nothing here needs admin. The Power Guard is Welt's, through his own Windows prompt.
- **One operator.** Confirm with Welt that Astra has stood down and that no scheduled task of Astra's touches the GPU, port 8082 or the Pi timer.
- **Read:** `pc/T46.md`, Training 1 in `pc/TRAINING-3.md`, `pc/HEGELIZER-2.md`, `pc/CODEX-HANDOVER-20261102.md`, and Astra's PR #1 comments of 4 and 5 November (paths, the failures, evidence folders under `C:/hegel/handover/`).

## Rules that hold

- **Data.** Use the frozen round-two data, the chapter manifest and the T45 seal exactly as they are; the trainer verifies them. Create, edit or choose no training data.
- **Blindness.** Never open, print or copy the private T45 plan, its key, the confirmation release or the blind sheets (`private/` under the seal root and under each trial). A Claude session judges 20 of the pairs blind; reading them would spoil that. The tools read them; you don't.
- **Keep everything.** Delete or overwrite nothing: the failed 5 November run, checkpoints 100 and 200, phase 0's results, all receipts. Every run gets a new output directory.
- **Limits.** No new packages, no power, firewall, network or driver settings, no spending. Ask Welt.
- **His day.** 09:00 to 21:00 is Hegel's. The GPU is yours only in a window Welt grants. At the end of every window, restore plain Qwen on 8082 (three 16K slots, the saved command) and the Pi timer, then check that his next natural tick has `mind.source` = `mind`.
- **Reporting.** On PR #1: done, blocked or a question, six lines at most. If the PC still can't reach GitHub, tell Welt in chat and he relays.

## Step 1 · Survey, read-only, no GPU

Write your findings to a new folder, `C:/hegel/handover/claude-pc-20261105/`:

1. The repository at `c272095` or later inside WSL. If git can't reach GitHub from the PC, find Astra's local checkout that already has PR #8 and record its commit. Then `python3 -B -m unittest discover -s tests` must pass.
2. The paths: the frozen round-two data folder, the chapter manifest (`CHAPTER-SPLITS-V2.json`), the T45 seal (`SEAL.json` in `t45-confirmation-v2`), and the base model.
3. The saved 8082 command, and the commands that stop and start Hegel's timer on the Pi (user `faqts`).
4. The installed versions of torch, transformers (4.50 or later, for `disable_compile`) and unsloth.
5. The CPU data check passes:
   ```sh
   python3 pc/train_hegel.py --round-two --phase restyle --goldfish --data FROZEN_DATA \
     --chapter-splits SPLITS.json --confirmation-seal SEAL.json --check-data
   ```

Then post your exact command list for steps 2 and 3 on PR #1, and wait for Claude's review.

## Step 2 · Rehearsal, about 20 minutes, in a window Welt grants

1. Stop the 8082 server and the Pi timer.
2. **Admission, before Python starts:** `nvidia-smi` shows no `llama-server` and under about 2 GiB in use. Save that output.
3. A dry run with an evaluation at step 2, into a new directory: the step-3 command below with `--dry-run --eval-steps 2`. Log the seconds per step and the peak VRAM before and after the evaluation.
4. Prove resume: stop it during step 3 (after the step-2 evaluation and checkpoint), then start the same command again with `--resume`. It must continue from checkpoint 2 and reuse the saved evaluation instead of running it again.
5. Restore Qwen and the timer, and check his next tick.

It passes when:
- every step after the evaluation runs within 1.5× of the steps before it;
- resume works;
- his next tick uses `mind`.

Post the numbers on PR #1.

## Step 3 · The real run, one night Welt picks

Welt sets the Power Guard for that night. Phase 0 is done; don't repeat it.

1. At 21:00, once he is asleep: stop the 8082 server and the Pi timer, then do the admission check.
2. Start the run with a log:
   ```sh
   python3 pc/train_hegel.py --round-two --phase restyle --goldfish --base BASE --data FROZEN_DATA \
     --chapter-splits SPLITS.json --confirmation-seal SEAL.json --out NEW_DIR 2>&1 | tee NEW_DIR.log
   ```
3. Look at it yourself every 30 to 60 minutes: the steps done, the seconds per step and the VRAM. If the step time rises past 1.5× after an evaluation, stop it, restore Qwen and report. Don't improvise a fix in the night.
4. Then phase C, as in `pc/T46.md`: the adapter's conversion, the new test with both arms, and the dashboard. If phase C won't finish before about 08:00, leave it for the next window; the checkpoints keep.
5. Restore Qwen and the timer before the Power Guard's time, and report.

If KPI 4 (nothing copied) fails, the next window trains the same data without `--goldfish`, so that we learn what goldfish does.
