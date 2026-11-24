# Training 4's instrument run

Declared on 23 November 2026 by Claude in the cloud, before any call. The plan is `pc/TRAINING-4.md`; the tool is `tools/voice4.py`. Inference only, plain Qwen on the live server, which is never restarted. No adapter is loaded and nothing is trained. **Welt's go: 23 November** (`DECISIONS.md` 65). The development journey is Vienna alone, since the Netherlands journey joined the training letters.

## What the night makes

| Step | Calls | What it gives |
|---|---:|---|
| Cards for the 43 development passages | 43 | what each passage states about the world |
| The symmetry check, at most twice | up to 86 | cards that hold what two checks found; none is dropped for lacking (rule of 24 November) |
| Letters P0, P1 and P2 in German | 129 | the three rungs without training |
| The real passages and the 300 controls into English | 343 | the real side, and the classifier's qualification |
| The letters into English | 129 | both sides through one translation |
| The fixed judge on the 296 marked rewrites | 296 | whether the judge may gate |

About 1,030 calls, in this order. A run that ends early is resumed by the same commands.

## For the PC seat

**By day on 24 November, in the spare slot beside him,** with the latency guard of the earlier day jobs (`--latency-observation`), so that his own steps stay as fast as they are. What is not done by 20:45 goes on at night, after his day is complete. One stream; `tools/run_requests.py` as before, each requests file with its own job folder.

```sh
F=pc/exports/voice4-instrument-20261124
python3 tools/voice4.py passages --out $F        # PASSAGES-MANIFEST.json must equal main's; stop if it differs
python3 tools/voice4.py cards --folder $F        # then run REQUESTS-cards.jsonl      -> $F/REPLIES-cards.jsonl
python3 tools/voice4.py check --folder $F --round 1    # run REQUESTS-check1.jsonl    -> $F/REPLIES-check1.jsonl
python3 tools/voice4.py merge --folder $F --round 1    # says how many cards are still open
python3 tools/voice4.py check --folder $F --round 2    # only if any is open: run     -> $F/REPLIES-check2.jsonl
python3 tools/voice4.py merge --folder $F --round 2    # writes CARDS.jsonl and DROPPED.json
python3 tools/voice4.py arms --folder $F         # run REQUESTS-arms.jsonl           -> $F/REPLIES-arms.jsonl
python3 tools/voice4.py translate --folder $F    # run REQUESTS-translate.jsonl      -> $F/REPLIES-translate.jsonl
python3 tools/voice4.py judge --folder $F        # run REQUESTS-judge.jsonl          -> $F/REPLIES-judge.jsonl
```

- If round 1's merge leaves no card open, it writes `CARDS.jsonl` itself, and round 2 is skipped.
- **The re-merge of 24 November.** The first run's merge kept 5 of 43 cards. The rule is changed (`tools/voice4.py`, `fresh_lines`): no new calls are needed. On main with the new rule, run `merge --round 1` and then `merge --round 2` again over the replies already there. It must give 43 cards, and `CARDS.jsonl` with sha256 `3494741055043c817024cbfde1004bfe51e0e04194a3f4f1bcd63bfbdef73b08`; stop if it differs. Then `arms` again: requests whose text is unchanged keep their replies, the others are run.
- At night the stop is the fast lane's: no new requests file after 07:15 Berlin, the stream stopped by 07:45, 8082 checked after.
- Push the folder to `codex/voice4-instrument-20261124` and post DONE on PR #1 with the head and the counts of each step.
- **Do not read the letters, and make no sheet and no key.** The cloud makes the sheets, keeps the keys outside the repository, and seals the judgments before any key is applied.

## What the cloud reads, in the morning

- **The cards:** how many passages kept a card, and how many lines the check added.
- **The judge's validation** (`voice4.py judge-score`): it gates only if it flags at least 80% of the 17 substantive defects the readers found and at most 10% of the 224 rewrites they passed.
- **The classifier's qualification** (`voice4.py classify`): on the controls' English, in bundles of 600 words, it must tell his letters from his correspondents' at 75% or better, with the 95% interval's lower end above 60%. Only then are the arms read with it.
- **Invented particulars** (`voice4.py particulars`): per letter, for each arm, beside the real passages' own count, which is the rule's floor.
- **Blind pairs:** a sheet per arm and its mirror, for two judge families. Judgments are sealed on main before the keys.
- **The best of P0, P1 and P2 on the two axes** is the arm Training 4's adapter must beat.

Evaluation only. No card, letter, translation or judgment of this night is ever training data. The cards for the training letters are made later, by the same instructions, in a run of their own.
