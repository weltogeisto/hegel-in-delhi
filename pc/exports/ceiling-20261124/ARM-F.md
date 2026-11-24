# Arm F: how it was made

`REPLIES-F.jsonl` holds the sixth arm of the ceiling test (`pc/CEILING-TEST.md`): arm D's messages, answered by a cloud model.

- **Made on 24 November 2026, before the PC ran any arm.** The D requests are the ones on `codex/ceiling-20261124` at `9619bc25`, whose three files the cloud rebuilt and found equal byte for byte.
- **44 pieces, one a brief.** Four fresh agents on a stronger model than his, eleven briefs each. Each agent got only the requests: the same four messages the PC sends for arm D, and the same schema. None knew what the test asks, how it is judged, or what the other arms are.
- **Each request was answered on its own,** as the assistant's next turn, with the writing object and nothing else. Every reply parses and has the five keys. The texts run from 316 to 483 words, 448 in the middle.
- **Pinned:** one cloud model for all 44 pieces; no tools but reading the requests and writing the answers; no network; the model's default reasoning; no limit on the visible answer beyond the request's own "up to about 450 words". The model's name is in Welt's chat with the cloud session, not in the repository.
- **Nobody has read the pieces.** The cloud session that built the test checked their form and their length by script only.
- If the four briefs without a text are added later, their four pieces are made the same way and appended.

Evaluation only; never training data.
