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

## The read, and the frozen set (26 November)

W14 was complete on the PC at 00:14 Berlin on 26 November (`codex/training4-cards-20261124`, `53098cc1`). The cloud read it before freezing.

- **Cards:** 644 of 644, none dropped. The check added lines in two rounds (438 cards were checked a second time). A card holds 14 lines at the median (4 to 48). No card carries a verdict or a feeling of his: those are the voice, and they stay out.
- **Targets:** every one of the 1,191 targets is his passage, byte for byte.
- **One fault: a card that hands him his own words.** In 7 of 644 passages the card kept his German: an address on the outside of a letter, a title he wrote down, a sentence he quoted, a line in Latin. A row built from such a card teaches the adapter to copy from the prompt, not to write from the facts. Rule added on 26 November, before any training (`tools/voice4_train.py`, `copies`): a passage is left out when its card shares 12 words in a row with the passage, or holds four different German function words (`von` and `so` not counted: they occur in names and in English).
- **The frozen set** (`TRAIN-MANIFEST.json`): 589 training passages, 1,177 rows, 48 held out. `TRAIN.jsonl` sha256 `271cef9f561d08746d83dbd8b09da604653a9b66c6178608ce3b39d0a214c8c9`; `HELDOUT.jsonl` sha256 `4a0665bdaecf0d1bd390022902c26262c4ec3b687dbb88dfe7571a8e28529f31` (unchanged: no held passage was left out).
- **The PC's own build** (sha256 `606dc5a6…`, 1,191 rows) is superseded by this one. Nothing trained from it.
- The run still waits for Welt's word, and the voice measure is made again with the form evened out first (`pc/TRAINING-4-INSTRUMENT.md`).

## The rule it stands on

The targets are his own words. The inputs are the local model's cards, made under fixed instructions and checked by a fixed rule. No frontier model writes or chooses a line of either (`pc/TRAINING-4.md`, the data rule).
