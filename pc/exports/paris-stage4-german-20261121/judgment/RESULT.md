# Paris stage 2c: the result

21 November, about 02:15 Berlin. Declared in `pc/PARIS-BACKTEST.md` (stage 2c, #121) before any output. The judgments were sealed on main (#125) before the keys were applied, and both keys match.

| | off (round trip, no block) | on (round trip, new block) |
|---|---:|---:|
| Real letter picked, of 24 | 24, all "sure" | 24, all "sure" |
| The same, letters that really came back in German | 21 of 21 | 20 of 20 |
| Kinds per model letter (real: about 4) | 4.62 | 4.33 |
| Model letters naming a price (real: 1) | 0 | 0 |
| Kind overlap with the real letter (Jaccard, mean) | 0.77 | 0.66 |

**By the declared reading: not shown closer** (no drop, lower overlap). The new block no longer plants prices, but it does not bring the letters closer either.

**The round trip alone does not move the count.** Through the same German-to-English path, the judge still picks the real letter every time. Form was not what gave stages 2 and 2b away.

## What gives it away, and why this test cannot be won as built

In almost every pair the judge's reason is the same: the real letter carries particulars the card never gives. Stage 2c's judges cite "the Brussels illumination", "Wallraf's Death of Mary compared with Boisserée's", "the lawyer who carries Faust as his Bible", "I have had quite enough of Dresden". **The card is a summary of the real passage, so the real letter always holds more than the model was told.** The model can match it only by inventing, and invention gives it away too (stage 2b). Across stages 2, 2b and 2c, 96 pairs out of 96 went to the real letter.

## A fair next design (stage 2d, a proposal, for Welt)

- **Give the model what Hegel had.** The card becomes the full list of every fact the passage reports (people, places, times, sums, what was seen and said), neutral and in the third person, with no opinion. Then the real letter holds nothing the model was not given, and the judge can tell them apart only by **what he chose, how he weighed it, and how he spoke**, which is the register the project wants to learn.
- Keep the German round trip (cheap, and it removes form).
- The measure is the count, with the kinds as a read. A block is closer if it lowers the count by 4 or more.

Evaluation only: nothing here is ever training data.
