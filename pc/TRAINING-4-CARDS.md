# Training 4: the cards for the training letters

Declared on 23 November 2026 by Claude in the cloud, before any call. The plan is `pc/TRAINING-4.md` (Welt's go: `DECISIONS.md` 65); the tool is `tools/voice4_train.py`. Inference only, plain Qwen on the live server, which is never restarted. Nothing is trained and no adapter is loaded.

## What it makes

The training set of Training 4: for each passage of his own writing, a card of what it states about the world. The card is the input; his passage, untouched, is the target.

| Set | Passages | Words |
|---|---:|---:|
| His letters, outside the tenth held out | 506 | |
| The Netherlands journey | 34 | |
| His two diaries, German paragraphs | 56 | |
| **Training, together** | **596** | **112,795** |
| Held out, for early stopping | 48 | 8,617 |

- **The cards** come from the instrument's own card-maker and symmetry check (`tools/voice4.py`): at most two rounds. What a check finds new is added and the card is kept; a line that only restates the card is not added. `SETTLED.json` says how the cards settled (rule of 24 November).
- **The pairs:** each training passage gives one pair with the card's lines in order and one with the same lines shuffled by a seed. Each held-out passage gives one.
- **The leak check** runs twice, in `passages` and in `build`: no passage may share 12 words in a row with the Vienna or the Paris journey. It raises an error.

## For the PC seat

On the night of 24 November, after the instrument run (`pc/TRAINING-4-INSTRUMENT.md`) is complete. One stream; `tools/run_requests.py` as before, each requests file with its own job folder. About 650 calls for the cards and up to 1,300 for the checks.

```sh
F=pc/exports/training4-20261124
python3 tools/voice4_train.py passages --out $F        # PASSAGES-MANIFEST.json must equal main's; stop if it differs
python3 tools/voice4_train.py cards --folder $F        # then run REQUESTS-cards.jsonl      -> $F/REPLIES-cards.jsonl
python3 tools/voice4_train.py check --folder $F --round 1    # run REQUESTS-check1.jsonl    -> $F/REPLIES-check1.jsonl
python3 tools/voice4_train.py merge --folder $F --round 1
python3 tools/voice4_train.py check --folder $F --round 2    # only if any card is open     -> $F/REPLIES-check2.jsonl
python3 tools/voice4_train.py merge --folder $F --round 2    # writes CARDS.jsonl and DROPPED.json
python3 tools/voice4_train.py build --folder $F        # TRAIN.jsonl, HELDOUT.jsonl, TRAIN-MANIFEST.json
```

- The stop is the fast lane's: no new requests file after 07:15 Berlin, the stream stopped by 07:45, 8082 checked after. What is left is resumed by the same commands, by day in the spare slot with the latency guard.
- Push the folder to `codex/training4-cards-20261124` and post DONE on PR #1 with `TRAIN-MANIFEST.json`'s counts and hashes.
- **Nothing trains from it yet.** The cloud reads the cards first: how many passages kept a card, how many lines the check added, and a sample of cards against their passages. The training set is frozen only after that.

## The rule it stands on

The targets are his own words. The inputs are the local model's cards, made under fixed instructions and checked by a fixed rule. No frontier model writes or chooses a line of either (`pc/TRAINING-4.md`, the data rule).
