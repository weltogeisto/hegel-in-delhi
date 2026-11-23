# Training 4 run: his letters, at night

For the PC operator. The plan is `pc/TRAINING-4.md`. The launcher is `pc/run_training4.py`. It uses Training 1's guards: one controller, no restart, the Pi paused, the live server stopped and put back. Nothing here runs without Welt's go for the night.

## What you need first

- The reviewed branch, checked out clean on the PC. The launcher refuses a dirty checkout.
- `TRAIN.jsonl` and `HELDOUT.jsonl`: rows of `{"id", "prompt", "target"}`. The manifest and its hash are frozen and committed.
- The machine configuration on stdin: the same fields as Training 3's (server and launcher, power receipt, SSH arguments, model, converter, GGUF, port), plus `"train"`, `"heldout"` and `"estimate"` (step, evaluation and conversion seconds; a rough guess is fine for the rehearsal).

Check the data first. It needs no GPU:

    python3 pc/train_letters.py --check-data --train TRAIN.jsonl --heldout HELDOUT.jsonl

It prints the row counts. It must not print "NOT ok". The token lengths are checked by the trainer itself, before the model loads.

## Before the first rehearsal

Read-only, by day. Post what you find on PR #1 before any intent is written.

- **The live server's starter.** Since 21 November the live server is started only by its Windows starter, never from a shell: a server started inside a WSL session died with that session and cost him eight hours. The launcher puts the original server back through the machine configuration's `original.launcher`. Check that this is the Windows starter, or a path that survives the launcher's own exit. If it is not, stop and say so.
- **The power record.** The launcher reads the Guard's state and a verified receipt, and changes nothing. The limit is 24 hours now, and Welt renews at about 21:30. Check that the cutoff will lie at least 15 minutes after the restore deadline.
- **The power cap** of about 75% on training nights is Welt's own command (`DECISIONS.md` 65). The launcher never sets it.
- **Order of the night.** The training set must be frozen first, because the real run needs the same bytes as the rehearsal. So the rehearsal and the real run go in the same night, one after the other, on Welt's yes for that night.
- **After a restoration,** the launcher's Pi probe is the gate. The first natural decision from the mind the next morning is posted as the evidence that Training 3's launcher waited for.

## 1. The rehearsal

Three optimizer steps, one evaluation, one checkpoint, conversion to GGUF, one served completion at adapter scale 1 and one at scale 0, then the original server back.

    python3 -m pc.run_training4 --write-intent JOBS/t4-rehearsal --restore-by ISO_TIME --rehearsal < machine-config.json
    python3 -m pc.run_training4 --intent JOBS/t4-rehearsal/INTENT.json --intent-sha256 HASH --detach

The first command prints the hash. A rehearsal can run by day (started 09:00 to 20:00, restored by 20:00 the same day) or at night (see the window below).

It takes about 30 minutes. When it ends, `RUN-END.json` says `LETTERS_REHEARSAL_PASSED` or `LETTERS_REHEARSAL_FAILED`. `REHEARSAL.json` has each gate and the measured timings. It passes only if:

- the step after the evaluation is within 1.5 times the steps before it;
- PyTorch never reserves more than the card holds;
- three steps ran, the checkpoint and the final adapter exist;
- the converted adapter answered at scale 1 and at scale 0;
- the original Qwen is back on 8082 and the Pi's health and one-token checks pass.

If it fails, do not rerun it on the same folder. Post the result and wait.

## 2. The real run

It needs the passed rehearsal and the same bytes: the two data files, the base model and tokenizer, the converter and the server launcher must hash as they did in the rehearsal. If anything differs, the launcher refuses and the rehearsal is run again. Add `"passed_rehearsal": ".../REHEARSAL.json"` to the machine configuration.

    python3 -m pc.run_training4 --write-intent JOBS/t4-night --restore-by ISO_TIME < machine-config.json
    python3 -m pc.run_training4 --intent JOBS/t4-night/INTENT.json --intent-sha256 HASH --detach

The night window: start at 20:00 or later, restore by 08:15 Berlin the next morning at the latest. The power cutoff must come at least 15 minutes after the restore deadline. The launcher also keeps its 30-minute reserve inside that. It never changes the power settings.

The launcher takes the steps the window fits, using the rehearsal's measured times, at most three epochs. It stops early when the held-out loss has not improved for three evaluations. It refuses if fewer than 100 steps fit.

Do not restart it, do not run a second copy, and do not touch the Pi or the server while it runs. If it stops, it restores the original server by itself. Read `RUN-END.json`.

## What each step produces

In the job folder:

- `INTENT.json`: written once, never edited.
- `timing.jsonl`: every step, evaluation and save, with seconds and memory.
- `training/TRAINING-LOG.jsonl`: train loss, learning rate and held-out loss by step.
- `training/RESULT.json`: the best step by held-out loss (chosen by the machine, nobody reads), the steps run, why it stopped, the examples used and left out, the hash of both data files, every setting.
- `training/checkpoint-50`, `-100`, and so on, and `training/final`. **Every checkpoint stays.** Nothing deletes them. Converting more of them for evaluation is a separate, later step.
- `converted/adapter-f16.gguf` and `CONVERTED.json`: the final adapter, converted.
- `PHASE-C-END.json`: the two served completions, at scale 1 and at scale 0.
- `RESTORATION.json` and `RUN-END.json`.

A real run ends as `LETTERS_TRAINED_SMOKE_VERIFIED_EVALUATION_PENDING`. That means the adapter trained, converted, loaded and answered. It does not mean it is good. The instrument measures it later. Nothing is adopted.

## What to post

After the rehearsal: `REHEARSAL.json` (all gates and timings), `RUN-END.json`, and the two texts in `PHASE-C-END.json`.

After the real run: `RUN-END.json`, `training/RESULT.json`, `training/TRAINING-LOG.jsonl`, `timing.jsonl`, and the time the original server answered again. If a row was left out for length, `RESULT.json` lists its id and length: post that too.

On any surprise, post what you see and stop. The fix comes the next day, reviewed.
