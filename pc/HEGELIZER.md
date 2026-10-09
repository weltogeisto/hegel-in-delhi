# Codex on the PC: train the Hegelizer

Goal: a second LoRA adapter on the installed Qwen3.8-27B that restyles plain English in Hegel's manner, as his nineteenth-century English translators render it. At runtime the chat model will write content plainly and this adapter will restyle it (that part is not built yet). Training on his books and on Qwen's own outputs did not give him his voice; this is the standard method for an author's style, **inverse paraphrasing** (Krishna et al., EMNLP 2020): take real passages from his translations, have plain Qwen rewrite each in plain modern English, then train the adapter to turn the plain version back into the real passage.

**Every training target is Hegel's real text** (his translators', public domain, from the shelf). Only the inputs are written by a model, and by Qwen, never by Claude. **Don't add, edit or "improve" any line of `mind/train/hegelizer*.jsonl` by hand or with another AI.** If a file looks wrong, report it.

Do the steps in order and report each result to Welt in one line, with the exact error text if something fails. Don't improvise around a failure; stop and report. All commands run in the WSL2 Ubuntu shell. This builds on `pc/TRAINING.md`: the training environment `~/hegel-train`, the base model `~/models/qwen-base`, the llama.cpp build (its step 6) and `C:\hegel\awake.flag` are as set up there. Set the Qwen GGUF of TRAINING.md step 1 once per shell:

```bash
export QWEN=/path/to/qwen3.8-27b.gguf
```

The GPU is busy in steps 2 to 7, so **the world on the Pi must not be live**: ask Welt to pause it before step 2 and to say when it may run again. Only one model fits on the 3090: stop whatever else serves Qwen or Bonsai first (`nvidia-smi` must show the card nearly empty). The long runs (steps 4 and 5) go into tmux: start them, report that they are running with the first progress line, and end your turn. When Welt asks, attach, report the last progress line, and carry on once the run says it is done.

| Step | What | PC time |
|---|---|---|
| 1 | Pull, run the tests | 5 min |
| 2 | Serve plain Qwen with four slots on 8082 | 5 min |
| 3 | Build the units from his English books | 1 min |
| 4 | Plain versions of the units, with Qwen | **about 6 hours** (4 to 6), resumable |
| 5 | Check the data, dry run, then the training | 30 min, then **about 4 hours per epoch**, 2 epochs overnight |
| 6 | Convert the adapter | 10 min |
| 7 | The restyle test: plain Qwen, then the adapter | 1 hour |
| 8 | The success bar | judging is Welt's and Claude's |

## 1. Pull and test

```bash
cd ~/hegel-in-delhi && git pull && git log -1 --oneline
python3 -m unittest discover -s tests      # must end with OK (about three minutes)
```

Report the commit and the last line. If a test fails, stop and report the test's name and message.

## 2. Serve plain Qwen on port 8082

No adapter. Four slots, so four calls run at once, and four times the usual `-c` (TRAINING.md serves 16384; every slot gets a quarter of it). Port 8082 is free now: stop the Hegel adapter's server if one still runs there (`ss -ltnp | grep 8082`).

```bash
tmux new -s qwen
llama-server -m $QWEN -ngl 99 -c 65536 --parallel 4 --host 127.0.0.1 --port 8082 --alias qwen
```

Detach with `Ctrl-B d`, then:

```bash
curl -s http://127.0.0.1:8082/health          # must print {"status":"ok"}
```

If the card runs out of memory, use `-c 32768` (8192 per slot is plenty: a passage and its rewrite are about 1,000 tokens) and say so. With llama.cpp on Windows (TRAINING.md step 1), use `C:\hegel\llama\llama-server.exe` with the same options and `--host 0.0.0.0`, and the PC's address in place of `127.0.0.1` below if WSL does not reach it.

## 3. Build the units

```bash
python3 tools/hegelizer.py --build
```

It takes a minute and writes `mind/train/hegelizer-units.jsonl`: passages of his ten English books (Wallace, Dyde, Sibree, Haldane, Baillie, Bosanquet) merged or cut to 150 to 250 words. It leaves out the units that share eight words with the Hegel test's twenty passages and the units that still show their scan ("tlie", "hke"). 5% of each book is held out for the test. The table is the count per book and in all, with how many were dropped and why. Report the table. Expect about 4,100 units, 205 of them held out; if there are fewer than 3,000, stop and report.

## 4. Plain versions

First a trial of eight units, to see the prompt work:

```bash
python3 tools/hegelizer.py --paraphrase --url http://127.0.0.1:8082 --workers 4 --limit 8
python3 tools/hegelizer.py --stats
```

The trial's units stay done. Report the three samples (each shows the plain version above the real text); the plain version must read as modern English of about the same length, with nothing added. Then the whole run, in tmux:

```bash
tmux new -s paraphrase
cd ~/hegel-in-delhi
python3 tools/hegelizer.py --paraphrase --url http://127.0.0.1:8082 --workers 4 2>&1 | tee -ia mind/train/hegelizer.log
```

One call per unit, thinking off. A reply stands if it is not cut off, has 0.6 to 1.4 times the original's words, has no list or heading, and shares no run of eight words with the original; otherwise it is asked once more at a higher temperature, and then the unit is recorded as failed (`mind/train/hegelizer-failed.jsonl`). A progress line comes every 25 units with the time to go. Expect about 6 hours. (`tee -i` keeps the log going when you press `Ctrl-C`.)

- **Pause or crash:** `Ctrl-C` (once: it finishes the calls in flight and stops; twice: it drops them), a reboot, or a server that stops answering ends the run without losing a line. A dead server is not counted against any unit; the run says "the server stopped answering". Restart the server (step 2) and run the same command: it carries on. `--retry-failed` asks the failed units again; leave it off unless Welt says.
- **Fewer calls at once:** if the card or the server struggles, restart the server with `--parallel 2` and the run with `--workers 2`.

When it says `done`:

```bash
python3 tools/hegelizer.py --stats | tee mind/train/hegelizer-stats.txt
```

**The gate:** go on only if failed is under 10% of the units and the mean word ratio (plain / original) is within 0.8 to 1.2. The stats print the verdict on the line that begins `gate`: `passes` or `STOP, report`. If it says STOP, stop: send Welt the stats and the three failures it lists. If it passes, report the stats (counts, ratio, the three samples) and go on to step 5.

## 5. Check the data, dry run, training

Stop the Qwen server (`tmux attach -t qwen`, `Ctrl-C`). Nothing else may be on the GPU. The options are those of the first adapter (`TRAINING.md` step 5): rank 16, no vision encoder, a small loss budget.

```bash
source ~/hegel-train/bin/activate && cd ~/hegel-in-delhi
python pc/train_hegel.py --base ~/models/qwen-base --phase restyle --rank 16 --text-only --loss-target-gib 0.125 --check-data
```

It needs no GPU. It must end with `data ok`, and shows the examples in each split, the longest by estimate (limit 1024 tokens) and how many are probably too long (those are skipped, never cut). Report its lines. If it says over a fifth are too long, stop and report.

```bash
tmux new -s hegelizer-train
python pc/train_hegel.py --base ~/models/qwen-base --phase restyle --rank 16 --text-only --loss-target-gib 0.125 --dry-run 2>&1 | tee pc/out/hegelizer-dryrun.log
```

The dry run loads the model (5 to 10 minutes), trains five steps, measures the loss on a few held-out examples to prove that path, and prints the peak VRAM and `projection: N s per step x M steps = H h`. Report both lines. The projection is for both epochs; plan on about 4 hours per epoch, and if it is over 12 hours in all, stop and report before going on. If it runs out of memory, add `--seq-restyle 768` (and report); don't change anything else.

Then the real run, with the settings the dry run proved:

```bash
python pc/train_hegel.py --base ~/models/qwen-base --phase restyle --rank 16 --text-only --loss-target-gib 0.125 2>&1 | tee -a pc/out/hegelizer-train.log
```

A fresh adapter on the base (it never starts from the first adapter), 2 epochs at a learning rate of 2e-4, loss on the real passage only, a checkpoint every 25 steps, into `pc/out/hegelizer-lora/`. It prints a line per step, and at the end of each epoch the mean loss on the held-out units: `[restyle] epoch 1.0: train loss ..., held-out loss ...`. After a crash or reboot, the same command with `--resume` carries on; the epochs measured before are kept.

- **The loss** should fall in the first hundred steps and then flatten. Report it if it rises steadily, reads `nan`, or stays at 0.
- **The held-out loss** should be lower after epoch 2 than after epoch 1, or about the same. If it rises while the train loss falls, say so plainly: the adapter overfits, and Welt may choose one epoch (`--epochs-restyle 1`).

When it says `adapter saved to .../pc/out/hegelizer-lora`, send Welt `pc/out/hegelizer-lora/training.json` (the train and the held-out loss of each epoch) and the last 30 lines of `pc/out/hegelizer-train.log`.

## 6. Convert the adapter

Exactly as `TRAINING.md` step 6: the training environment, which has the Transformers that Qwen3.8 needs, the llama.cpp of the same build as the server in `~/llama.cpp`, and `--base-model-id` from Hugging Face.

```bash
source ~/hegel-train/bin/activate && cd ~/hegel-in-delhi
python ~/llama.cpp/convert_lora_to_gguf.py pc/out/hegelizer-lora --base-model-id Qwen/Qwen3.8-27B --outtype f16 --outfile pc/out/hegelizer-lora.gguf
ls -lh pc/out/hegelizer-lora.gguf
```

Report the size (the first adapter, also rank 16, was 445 MB). The notes of TRAINING.md step 6 apply to a failure here too.

## 7. The restyle test

The Hegel test's restyle part takes 20 of the held-out units (two from each book, the same ones for every mind), gives the mind each plain version four times with the Hegelizer's prompt (`world/restyle.py`), and puts the plain version, the four restyled versions and the real passage on one sheet. It needs `mind/train/hegelizer.jsonl` as step 4 left it: don't run step 4 again between the two runs.

First plain Qwen, which is given only the prompt: the control. Normal `-c`, no adapter:

```bash
tmux new -s hegel
llama-server -m $QWEN -ngl 99 -c 16384 --host 127.0.0.1 --port 8082 --alias qwen
```

```bash
cd ~/hegel-in-delhi
curl -s http://127.0.0.1:8082/health
python3 tools/hegel_test.py --url http://127.0.0.1:8082 --label qwen --only restyle
```

About 15 minutes (80 calls). It adds the part to `mind/results/hegeltest-qwen.json`, which is already there, and keeps the other parts. Then stop that server and serve the adapter:

```bash
llama-server -m $QWEN --lora ~/hegel-in-delhi/pc/out/hegelizer-lora.gguf -ngl 99 -c 16384 --host 127.0.0.1 --port 8082 --alias hegelizer
```

The start-up log must say the LoRA adapter was loaded. Then:

```bash
curl -s http://127.0.0.1:8082/health
python3 tools/hegel_test.py --url http://127.0.0.1:8082 --label hegelizer --only restyle
python3 tools/hegel_test.py --compare qwen hegelizer
```

`--compare` rewrites `mind/results/hegeltest.md` for these two labels (git keeps the old one). Report the line that each run prints (`restyle N/80 recited, M cut; Delta: model ..., plain versions ..., real passages ...`) and the **Restyle** table of `hegeltest.md`. Then:

```bash
git add mind/results && git commit -m "Hegel test: the restyle runs of plain Qwen and the Hegelizer" && git push
```

If the push is refused for lack of credentials, don't set any up: send Welt `mind/results/hegeltest.md`, `mind/results/hegeltest-qwen-restyle.html` and `mind/results/hegeltest-hegelizer-restyle.html` (and the two `-restyle-key.json` files and the two result `.json` files), and say that the commit is local.

## 8. The success bar

Judging is Welt's and Claude's, not yours: they open the two sheets, choose, press Export judgments and save the files as `mind/results/hegeltest-<label>-restyle-judged*.json`; `--compare qwen hegelizer` then fills in the "real picked" column. **The Hegelizer has worked if:**

- the judges find the real passage in **at most 8 of 20** on the hegelizer sheet (chance is 4 of 20; lower means more like him), **and clearly fewer** than on the qwen sheet, the control that was only prompted;
- **few are recited**: at most 8 of the 80 restyled versions share eight words in a row with the real passage (the `recited` column);
- the Delta of the restyled versions lies between that of the plain versions and that of the real passages, and nearer the real ones than the qwen row does.

If the bar is missed, that is the result: report the numbers as they are and don't train again.

When all is done, stop the server, and give the PC back as `TRAINING.md` step 7 does (remove `C:\hegel\awake.flag`, bring Bonsai back); tell Welt the world on the Pi may run again. Keep `pc/out/hegelizer-lora/`, `pc/out/hegelizer-lora.gguf` and `mind/train/` until Welt says otherwise.
