# Inkling 2 Mini against Qwen: the bake-off

Declared on 26 November 2026 by Claude in the cloud, before anything is installed or run. Welt's word of that evening (`DECISIONS.md` 73): "ja", to installing a newer llama.cpp beside the live one, downloading Inkling 2 Mini, and swapping the server for about an hour on the night of Friday 27 November.

**The question.** The ceiling test's likely read is that the writer is the limit (`pc/CEILING-TEST-RESULT.md`). Inkling 2 Mini (Thinking Machines, 20 November 2026, Apache 2.0) is a looped mixture-of-experts model of about 26B parameters, about 3B active a token. Its makers call it "at least comparable with Qwen 3.8 27B" in their own tests. Does it write better *for him*, on the same messages?

## What runs

The ceiling test's own messages, unchanged, answered by Inkling:
- **IA:** arm A's 44 messages (his live instructions, no thinking), with `reasoning_effort` "none".
- **ID:** arm D's 44 messages (the fuller instructions and the text), with `reasoning_effort` "medium".
- `pc/exports/inkling-20261127/REQUESTS-inkling-A.jsonl` and `-D.jsonl`, made by `tools/ceiling.py rearm`: the messages are byte for byte arm A's and arm D's; Qwen's reasoning budget is dropped and the room it left in `max_tokens` stays. Temperature 0.7 and the seeds as before.
- 88 calls. With about 3B active, perhaps an hour.

## For the PC seat

**By day on Friday 27 November, nothing live touched:**
1. Build llama.cpp b12600 or newer (Inkling support) into a folder of its own, beside `release-b11429`. The live server keeps its own binary.
2. Download `unsloth/Inkling-2-Mini-GGUF`, file `Inkling-2-Mini-UD-Q4_K_M.gguf` (about 16.6 GB). Write down its sha256 and the build number.

**At night, in the window when no call of his is due:**
3. Stop the live server on 8082. Inkling and Qwen do not fit in 24 GB together.
4. Start the new build with Inkling on 8082: `-ngl 99`, `-np 2`, a context that fits, alias `inkling`. Check `/health` and that one short call answers.
5. Run the two files, one a slot: `tools/run_requests.py --requests <file> --server http://127.0.0.1:8082 --job <job> --out <replies> --night --slot 0` and `--slot 1`, `--timeout 900`.
6. Stop Inkling. **Start Qwen again with the exact saved command.** Check that the pin matches (the same `argv_sha256` and model sha256 as in night 3's `SERVER.json`) and that `/health` answers. Then the night goes on as ordered.
- If the window is shorter than the run, stop at a whole request, restore Qwen, and finish the rest the next night.
- Push `pc/exports/inkling-20261127/` with the replies, ledgers, `SERVER.json` for Inkling and the restore's check, to `codex/inkling-20261127`. Post DONE on PR #1. **Do not read the replies.**

## The reading, declared now

- **Pairs:** IA against A, ID against D, ID against F. Blind, as in the ceiling test: two sheets, salted ids, every pair both ways round in separate sessions, the same calibration pairs mixed in.
- **Question 1 is amended, before any reply exists:** a claim that rests on a premise the piece made up does not count as arguing something new. The Claude family flagged every invention in the ceiling test and still counted it as new; that failed its calibration.
- **The bar:** Inkling's arm wins against Qwen's when a family names it alone, both ways round, on two thirds of the eligible briefs. Below the bar and outside the band of A against A2: a lead, not a win.
- **Also counted:** invented premises flagged, words, diary openings, and how long a call took.
- **If Inkling wins at the bar,** a fortnight of futures with Inkling as his whole mind follows before anything live changes. If it does not, the limit is the weight class, not Qwen.

Evaluation only. Nothing here is training data.

## The run, and the reading as it is done (28 November)

The PC ran it on the morning of 28 November, 07:14 to 07:39 Berlin, after night 4 had ended: llama.cpp b12816 in its own folder, `Inkling-2-Mini-UD-Q4_K_M.gguf` (sha256 `78fcedcf…`). Qwen was restored at 07:41 with its pin checked (`RESTORE.json`). 88 of 88 calls answered.

- **IA cannot be read as declared.** `reasoning_effort` "none" is a hint, not an off switch: Inkling reasoned in every reply, and arm A's room of 1,100 tokens held the reasoning too. 34 of 44 IA replies were cut off. IA against A has 10 eligible briefs, under the 40 the rule needs: nothing is declared for it.
- **ID is whole:** 44 of 44 replies ended by themselves.
- **The sheets** (`tools/ceiling_judge.py sheet --pairs A-IA,D-ID,ID-F`): 106 rows a sheet, the same 8 calibration pairs among them. The keys and the salt are outside the repository; `PACKET.json` holds the hashes, committed before any reading.
- **Read by the Claude family:** 10 fresh sessions, one part each (`parts --amended`: question 1 carries the amendment declared above).
- No second family; Welt does not read these rows.

## The result (28 November)

The Claude family's 10 sessions, each kept to its own folder, sealed before the key; the key matched its committed hash. `SCORE-claude.json`.

**The calibration passes this time: 7 of 8.** With question 1 amended, the readers no longer counted a claim on a made-up premise as new. So this reading counts.

| Comparison | eligible | first alone | second alone | both | neither | mixed | bar |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen D against Inkling ID | 44 | 7 | 4 | 1 | 15 | 17 | 30 |
| Inkling ID against the cloud arm F | 44 | 0 | 32 | 3 | 0 | 8 | 30 |
| Qwen A against Inkling IA | 10 | 0 | 0 | 0 | 7 | 3 | none: under 40 |

How often each arm was flagged as resting a claim on a made-up premise, of its showings: Inkling ID 34%, Qwen D 15%, F 10%. How often it was named as keeping his 1831 positions: ID 52%, D 72%, F 68%.

**What may be said:**
- **Inkling does not beat Qwen.** On the same messages with time to think, Qwen's pieces were named alone a little more often (7 against 4), and Inkling's invented premises more than twice as often.
- **The cloud arm beats Inkling at the bar,** 32 of 44, with a passed calibration: a declared result.
- **So Qwen stays his mind.** The gap to the strongest models is real, and Inkling does not close it.

## IA again, with room (28 November, by day, on Welt's word)

Welt asked for the plain arm again. The PC sent every IA request byte for byte, `reasoning_effort` "none" kept, with `max_tokens` raised from 1,100 to 3,148, the room ID had (`make_ia2.py`, `REQUESTS-inkling-A2a/b.jsonl`). 44 of 44 ended by themselves. Inkling ran 15:05 to 15:18 Berlin; one step of his day, a rest at home, ran without a mind; Qwen restored at 15:20 with its pin checked.

Read as declared for IA, under the amended question 1, in its own folder `ia2/`: Qwen's arm A against Inkling's IA2, 42 eligible briefs (A has no piece for b16 and b21), 50 rows a sheet with the 8 calibration pairs. Keys outside the repository; `ia2/PACKET.json` committed before any reading. The Claude family reads, four fresh sessions.

