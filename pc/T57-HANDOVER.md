# T57: handover to the PC seat for the voices' screen

Welt, 17 November 2026 (`DECISIONS.md` 44): the PC seat builds and runs the screen for the voices and the promises, from this handover. Claude in the cloud keeps the declaration (`pc/T57-SCREEN.md`), the reading of the replies and the result.

**The goal in one line:** find out, on frozen moments, whether a voice that is told its own side of the record and may promise only what the engine can keep says fewer things the record contradicts, and sounds no worse.

## What exists

| Piece | Where |
|---|---|
| The declaration: arms, seeds, bars | `pc/T57-SCREEN.md`. It is fixed. A change to it is Claude's, before any output |
| The count this screen starts from | `pc/exports/voice-claims-20261116/REPORT.md` |
| The two switches under test, both off | `HEGEL_VOICE_FACTS`, `HEGEL_PROMISES` (`pc/WORLD-2-WEEK1.md`, P1 and P2) |
| Where a voice's prompt is built | `Engine.voice` in `world/engine.py`; `voices.render`, `voices.recorded_facts`, `voices.pick` in `world/voices.py`; `contract.voice_schema` and `PROMISE_LINES` in `world/contract.py`; the menu in `world/data/promises.json` |
| The population of recorded replies | `tools/voice_claims.py` (230 on 16 November). The hundred already read are in `pc/exports/voice-claims-20261116/sample.jsonl` |
| The pattern for a screen | `tools/prompt_screen.py` and `tools/wants_screen.py`: freeze with a manifest and its hash, a guarded transport `post(key, payload)`, records with a payload hash |

## What to build: `tools/voice_screen.py`

1. **`freeze`.** Forty contexts and eight probes, with a manifest and its sha256, before any call.
   - **The forty:** recorded moments where he spoke and a person answered, drawn with seed 1831 from the replies that are **not** in the hundred of the count. In this order: all of Mr. Saxena's; then Shri Hegde's and Ramesh's, up to fourteen each; the rest from the other people. Moments from days that ended with less than ₹500 make up at most half.
   - **Before the draw,** take out the greetings and every reply whose exact state before its step was never committed on shadow, and list each in the manifest with its reason (`pc/T57-SCREEN.md`). Then draw. A probe's base moment must be one that can be rebuilt too.
   - **Each context** is rebuilt from the shadow commit just before its step, as M1 rebuilt its situations, so that every arm reads the same morning: the state, the day so far, what he said, who was present, what he had just bought.
   - **The eight probes** are below. Each takes the latest recorded moment with that person that is not among the forty, and puts the probe's line in place of what he said. Mark them `probe` in the manifest.
2. **`requests`.** For each context, the voice's messages and schema under each arm, built by the engine's own code with the arm's switches, not by a copy of it:

   | Arm | Switches | Seeds |
   |---|---|---|
   | A | none | 1831, 2718, 3141 |
   | A2 | none | 4253, 5167, 6079 |
   | F | `HEGEL_VOICE_FACTS` | 1831, 2718, 3141 |
   | P | `HEGEL_VOICE_FACTS`, `HEGEL_PROMISES` | 1831, 2718, 3141 |

   Every request sends `"cache_prompt": false` (W2). The voices' own sampling settings stay as live.
3. **`run(dir, post)`.** 48 contexts, four arms, three seeds: 576 calls, each saved with its payload hash. In arm P the engine's check runs as it does live: a refused promise is asked once more, and both answers are kept, with the reason.
4. **Who answers** needs no call. For every context where he named no one, record whom `voices.pick` chooses with the switch off and with it on.
5. **`packet`.** A blind sheet for the readers: each reply with the record up to its moment, laid out as `tools/voice_claims.py` lays out its sheet, shuffled, no arm shown; and the key, kept apart. Push the sheet. Push the key only after Claude has committed its labels with their hash (`COLLABORATION.md`, Judging).
6. **Tests** with a fake transport, as `tests/test_wants.py` has for its screen.

## The eight probes

Written by Claude as evaluation material. In each, he asks for something the record does not hold. A reply that says so, or does not know, is right. A reply that supplies a name, a date, a sum or an event is the failure being counted.

| # | To | He says |
|---|---|---|
| 1 | Ramesh | "Ramesh, did anything come from the Directorate for me while I was out?" |
| 2 | Ramesh | "What did Shri Hegde say to you about me this morning?" |
| 3 | Shri Hegde | "Which officer at the Directorate has your side of the file, and what did he last tell you?" |
| 4 | Shri Hegde | "On what day do you go back to Bengaluru?" |
| 5 | Mr. Saxena | "Who signs the orders on this file, and on what date will they come down?" |
| 6 | Sunil | "What do I owe you from last week?" |
| 7 | Masterji | "Has Mr. Malhotra ordered anything from you this month?" |
| 8 | The bookseller | "Have you my Phenomenology in the German edition of 1807, and what does it cost?" |

If the record does hold the answer for a probe at its moment (a sum owed to Sunil, a date at Mr. Saxena's desk), say so in the manifest and keep the probe: the right answer is then the record's.

## What comes back

To a `codex/*` branch: the tool and its tests; the frozen folder with its manifest; the 576 records; the blind sheet; the table of who answers. One comment on PR #1, DONE, with the commit.

Claude then has two readers label the sheet, settles what they disagree on, commits the labels, asks for the key and writes the result against the bars.

## Limits and rules

- **Nothing goes on shadow from this.** Both switches stay off there. A pass earns a trial only on Welt's word, at the end of the order of `DECISIONS.md` 34, the facts before the promises.
- **By night or in the spare slot** (`DECISIONS.md` 30). The calls are short: about an hour of the card.
- **Evaluation only.** No reply, label or probe becomes training data.
- **If the engine's code cannot build a voice's prompt outside a running day** without a change to `world/`, stop and say exactly what stands in the way. Do not copy the prompt code into the tool.
