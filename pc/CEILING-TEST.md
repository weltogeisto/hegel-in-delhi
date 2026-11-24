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

## The judging, in the cloud, sealed before any key

- **Pairs:** A with A2, A with B, A with C, A with D, D with F, A with F. Each pair is shown twice, the second time the other way round. The reader sees the headline, the text, and the two pieces as X and Y.
- **Two questions a pair:**
  1. Which piece argues something about this object that is neither in the text nor his doctrine restated? X, Y or neither.
  2. Which piece keeps the positions he held in 1831? X, Y, both or neither.
- **Readers:** fresh Claude sessions, and a second family. Welt reads 24 pairs drawn by a fixed seed. No reader chose a brief or wrote a piece.
- **Keys** stay outside the repository until every judgment is sealed with its hash.
- **An arm wins a brief** when a reader names it on question 1 both ways round. Anything else is no win.

## The reads, declared now

Out of 48 briefs. "Outside the band" means: 32 wins or more, and more than A2 wins over A.

| What the judgments show | What it means |
|---|---|
| D over A, outside the band | **The pipeline is the ceiling.** What he is given and how he is asked hold him back. Building is supported |
| D inside the band, and F over D in 32 or more | **The 27B is the ceiling.** More scaffolding will not lift it |
| F over A in fewer than 32, or the two families disagree | **The measure is the ceiling.** It cannot tell a better piece, and is mended first |
| B over A, outside the band | A real text in front of him lifts what he writes. The bookshop is supported (`DECISIONS.md` 8 as amended, point 5) |
| B inside the band | Documents matter less than we thought |

Beside the judgments, counted for every arm: the names and terms of this century in a piece, the names he had not met, the words, and how many pieces open like a diary entry (`tools/works_score.py`'s counts).

If fewer than 48 briefs ran, the two thresholds are two thirds of the briefs that ran.
