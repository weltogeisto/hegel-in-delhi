# The ceiling test: where the limit is

Declared on 24 November 2026 by Claude in the cloud, before any run. Welt's word of that day, relayed by the PC seat: "ceiling test tonight". The design is the evidence reviewer's, from the adversarial pass Welt ordered (PR #1). It is evaluation only: nothing here reaches his world, and nothing here is training data.

**The question.** Before a bookshop, a long work or anything else is built for the task (`WORLD-3.md`): when he writes about something of this century, where is the limit? In what he is given and how he is asked, in the model, or in our measure? The repo's own results so far say that scaffolding has not moved his arguing, and that the situation he is put in has. This test asks it directly.

## A brief

48 briefs, frozen in `pc/exports/ceiling-20261124/BRIEFS.json` before any run.

- **A saved moment: one of his mornings.** A state is saved only at a day's end, so a waking is the one moment the engine can rebuild exactly: the state the day before ended in, `new_day`, and the engine's own waking situation. It carries that morning's real headlines, the plan he made, his memory of the days before, and the event as his record has it. 35 mornings between 14 October and 25 November can be rebuilt. 13 of them give two briefs.
- **Something of this century: one headline he saw that morning.**
- **One real text:** the introduction of the English Wikipedia article on what the headline is about, up to 1,800 characters. It is what a look-up would have given him, if he had a phone. Wikipedia's text is under CC BY-SA 4.0, so it can be kept in the repository; a newspaper's body cannot.
- **Chosen by an agent that never judges.** Half of the articles show this century doing something it may be proud of, half show it failing (`DECISIONS.md` 8 as amended, point 3). None is about a living person, a party, caste, the Gita, a dispute between religious communities, or Germany between 1914 and 1945. The cloud changed three of the agent's articles for that rule (b09, b20, b25) and takes no part in the judging either.

## The call, and the arms

The call is his own writing call: his instructions, the waking situation, his own first decision of that morning, and the live writing request with his manuscripts and its schema. One sentence is added before the request and is the same in every arm: "This morning you sat down to write about one of the headlines in the papers: “…”."

| Arm | What differs |
|---|---|
| A | nothing: his live instructions (`mind/soul-ordinary.md`), no thinking, 1,100 tokens |
| A2 | another seed. How far two runs of one arm lie apart: the band |
| B | the text is added, in the words a look-up reaches him with: "Before you wrote, you looked it up. On your phone you read: …" |
| C | the fuller instructions (`mind/soul.md`) and a reasoning budget of 2,048 tokens |
| D | B and C |
| F | D's messages, answered by a cloud model. Made in the cloud, after the night |

240 calls on the PC. Temperature 0.7, as he writes. The prompt cache is off.

**Where this is not his live call, stated:**
- The frame sentence, and his first decision set down again as JSON.
- The switches of Day 55 are used for every morning, also for mornings before a switch went on.
- The replies are kept as the model gave them. His world would send a piece back that names what he has not met; here that is counted afterwards.

## What the PC seat does

By day, no GPU:

```sh
F=pc/exports/ceiling-20261124
python3 tools/ceiling.py texts --folder $F        # 48 introductions from Wikipedia, one request at a time: about four minutes
python3 tools/ceiling.py requests --folder $F --days <a folder with shadow's docs/days, 13 October to 25 November, and its index.json>
```

- `texts` says which briefs got no text. A brief without one is left out, and the test stands with 40 or more.
- **Push `$F` to `codex/ceiling-20261124` before the night**, with `TEXTS.json`, `MANIFEST.json` and the three requests files. The cloud builds the same requests from the pushed texts and compares the hashes in `MANIFEST.json`. They must be equal. The cloud also needs D's messages for arm F.

From his sleep, three streams, one a slot:

```sh
python3 tools/run_requests.py --requests $F/REQUESTS-ceiling-1.jsonl --server http://127.0.0.1:8082 --job <job 1> --out $F/REPLIES-ceiling-1.jsonl --night --slot 0 --timeout 900
python3 tools/run_requests.py --requests $F/REQUESTS-ceiling-2.jsonl --server http://127.0.0.1:8082 --job <job 2> --out $F/REPLIES-ceiling-2.jsonl --night --slot 1 --timeout 900
python3 tools/run_requests.py --requests $F/REQUESTS-ceiling-3.jsonl --server http://127.0.0.1:8082 --job <job 3> --out $F/REPLIES-ceiling-3.jsonl --night --slot 2 --timeout 900
```

- Each file holds whole briefs, five arms a brief, so a night cut short still leaves whole briefs.
- `--night` lets a stream use a slot that is his by day. It is for his sleep only (`DECISIONS.md` 62). The server is never restarted.
- The night's GPU rule holds. After 30 minutes of thermal slowdown in a row, stop the third stream and go on with two.
- Push the replies and each job's `LEDGER.json`, and post DONE on PR #1. **Do not read the replies.**

## The judging, sealed before any key

**Amended on 24 November, before any arm ran on the PC,** after the review Welt asked of Astra, a second model family (PR #1). Arm F existed and was unread. The amendments touch the judging only; the requests are unchanged.

- **Pairs:** A with A2, A with B, A with C, A with D, B with D, C with D, D with F, A with F. B with D and C with D use pieces the night already makes: they show whether the text still helps under the fuller instructions, and whether the fuller instructions still help with the text there.
- **Two sheets, two sessions.** Every pair is in both sheets, one way round in each, with its own id. A reader session sees one sheet only, so no reader sees a pair twice. An earlier check of order failed because a reader remembered its first ballot.
- **What a reader gets, and nothing else:** the two questions, and for each row the headline, the text, the two passages of his own books that the shelf's search puts nearest (the same for every reader), and the two pieces as X and Y. **A reader has no repository.**
- **Question 1:** which piece argues something about this object that is neither in the text nor his doctrine restated? X, Y, both (each does, on its own) or neither. The reader quotes the new claim, says what the piece rests it on, and says which piece, if any, rests a claim on a premise it made up.
- **Question 2:** which piece keeps the positions he held in 1831? X, Y, both or neither. And for each piece: a reasoned defence of a position of his, a reasoned revision of one, an unsupported reversal, or no position of his at issue. A reasoned revision is not a fault: it is what the task asks for. The first answer is kept for comparison with earlier tests.
- **Readers:** fresh Claude sessions, and Astra, each family reported apart. Welt reads 24 rows of the first sheet, three a comparison, drawn by the salt. No reader chose a brief or wrote a piece.
- **The key and its salt** are made by the cloud and stay outside the repository. Row ids and the way round come from the salt, so nothing in the repository tells which arm is which. The hashes of both sheets, of Welt's rows and of the key are committed before any reading (`PACKET.json`). The key is used only after both families' ballots and Welt's are sealed with their hashes (`tools/ceiling_judge.py seal`).

**Calibration pairs.** Eight more pairs are mixed into both sheets, unmarked, on eight briefs drawn by seed:
- four set a piece with one sound inference about the object against a fluent restatement of the text and of his stock doctrine;
- four set a claim that the text warrants against a plausible claim resting on a made-up premise.
- Each pair is matched for length and style. They are written after the night by a fresh agent that judges nothing; it sees the headline, the text, and arm A's piece for the style alone.
- A family passes with six of the eight right, both ways round. A family that fails is shown and not used: for that family the measure is in question.

**The win rule.**
- An arm wins a brief against another when a family names it alone on question 1, both ways round.
- Reported apart for every comparison: wins of each arm, both, neither, order reversals, and mixed answers.
- A brief with a missing piece or a missing ballot row is not eligible for that comparison.
- A comparison is read against its bar only with 40 eligible briefs or more. The bar is two thirds of them, rounded up: 32 of 48, 30 of 44.
- **The band** is the larger of the two: A2 over A, and A over A2. Both are shown.
- 35 mornings give the briefs, and 13 give two. So each share is shown with an interval taken over mornings, not over briefs.

**Arm F, pinned.** One cloud model, the same for all 44 pieces; four fresh sessions, eleven briefs each; no tools but reading its requests and writing its answers; no network; the model's default reasoning; no limit on the visible answer beyond the request's own "up to about 450 words". The model's name is in Welt's chat with the cloud session and not in the repository.

## The reading, as it is done

Added on 24 November, after the night's replies and before any key was used.

- **In parts.** A sheet has 347 rows: 339 pairs and the 8 calibration pairs. That is more than one reader session can hold. So each sheet is cut, in its own order, into 14 parts of 25 rows (the last has 22): `tools/ceiling_judge.py parts`. A part's folder holds the rows as plain text, the instructions (`PROMPT.md`: those of `packet/READER.md`, fitted to the text form) and a script that checks the form of the answers. One fresh session reads one part. A part belongs to one sheet, so no session sees a pair twice. Both families read the same parts under the same instructions.
- **The Claude family read on the night of 24 November.** 28 fresh sessions of one model, started by the cloud session; the model's name is in Welt's chat with the cloud session. Their ballots are `ballots/claude-1.jsonl` and `ballots/claude-2.jsonl`, sealed by hash in `SEALS.json`. Two things fall short of "a reader has no repository", and are stated:
  - The parts lay side by side in one folder on the cloud's machine, and a session was told, not forced, to read only its own. The record of every session's file and shell use was checked afterwards. Each read its own part, wrote its answers and ran the check, and nothing else.
  - The cloud session holds the key. When it listed that folder it saw the 25 answers of the first part, before the seal. It changed nothing: the sealed files are the readers' own lines, joined in the sheet's order.
- **Astra's family reads next** (`pc/TASKS.md`, W18), started on Welt's word: one fresh session for each part, in a folder that holds that part alone.
- **Welt's 24 rows** are on a private page, one row at a time, with the first question only. An answer is sealed when he goes on to the next row. His rows enter no bar.
- **Welt read all 24 rows on 26 November,** 11:51 to 12:07 Berlin: about 20 seconds a row at the median, for rows of about 1,000 words. So his rows are a quick impression, and are reported as that. His answers on the page and the lines he pasted in the chat agree on every row. `ballots/welt.jsonl`, sealed.
- **The key is opened** when `SEALS.json` holds both families' files and Welt's rows. Until then nothing is scored, by anyone.

## The reads, declared now

The test hands him a headline and, in two arms, a short text, and tells him he looked it up. So each read is as narrow as that. It cannot say what he would seek out, remember or develop by himself.

| What the ballots show, in every family that passed the calibration | What may be said |
|---|---|
| D over A, outside the band | This bundle (the text, the fuller instructions and time to think) lifts what he writes on an assigned headline |
| B over A, outside the band | A short Wikipedia introduction, assigned to him, lifts what he writes |
| B not over A | A short, assigned introduction does not. Nothing follows for a text he sought out, or a longer one. Reading is repaired either way: he chose to read 81 times and got nothing |
| C over A, outside the band | The fuller instructions with time to think lift it. The two were changed together and cannot be told apart here |
| D over C, D over B | The text still helps under the fuller instructions; the fuller instructions still help with the text there |
| F over D, or F over A, by the bar | This cloud model, so configured, beats his best arm, or his live call, on these briefs |
| F not over A | The cause is unresolved, and the measure is in question |
| The families disagree | Unresolved |

"Outside the band" means: at or over the bar, and more wins than the band.

Beside the ballots, counted for every arm: the names and terms of this century in a piece, the words, and how many pieces open like a diary entry (`tools/works_score.py`'s counts); and from the ballots, how often an arm was named as inventing a premise, and its stances.

`tools/ceiling_judge.py counts` makes the first three. Added on 24 November, before any scoring: beside the terms of this century in a piece, it counts those that neither the headline nor the text gave him. An arm that was handed the text would otherwise look richer for repeating it.

## What this test leaves open

Every arm gets the same morning and his own first decision of it. So the test does not ask whether his life in Delhi adds to what he writes. That is the next experiment, and the decisive one (`WORLD-3.md`): in paired futures, one real document is within his reach in one arm and not in the other, and the choice to read it is his. Days later both futures meet the same unfamiliar case, and nobody reminds him of the document. Readers then look for his old claim, the inference he now makes, and what else in his system must change if he is right.
