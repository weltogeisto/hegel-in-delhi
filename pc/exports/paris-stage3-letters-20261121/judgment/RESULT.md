# Paris stage 2b: the letter register, the result

21 November, about 03:00 Berlin. Declared in `pc/PARIS-BACKTEST.md` (stage 2b) before any letter existed. The judgments were sealed on main (#118) before the keys were applied, and every key matches its seal.

## The finding

**The block does not bring his letters closer to Hegel's. It makes the model invent.**

| | heldout-off (no block) | heldout-on (block) | old-on (block, stage 2's cards) |
|---|---:|---:|---:|
| Real letter picked, of 24 | 24, all "sure" | 24, all "sure" | 24, all "sure" |
| Kinds of content per model letter (real: about 4) | 4.67 | **6.54** | **6.42** |
| Model letters naming a price (real: 3 of 24) | 0 | **21** | **21** |
| Model letters on food (real: 8 of 24) | 11 | **24** | 23 |
| Kind overlap with the real letter (Jaccard, mean) | 0.70 | **0.58** | 0.53 |

**By the declared reading: not shown closer.** The count did not drop at all (24 to 24), and the overlap of kinds fell.

## Why

The block asked for "what you saw, ate and paid, with the names, hours, prices and places the record gives". The cards rarely give a price or a meal, so the model invented them: three-kreuzer bottles of water, six-thaler lunches, roast duck. The judges named the invented prices and meals as the giveaway in most pairs. The moralising mostly went, which was half of the target, but stock invention took its place.

**The same lesson as W9's voice repair (#115):** an instruction that names kinds of content (food, drink, goods, prices) plants them. The model fills every slot it is shown. Hegel's real letters are selective: they go deep on one or two things the day gave.

## What follows

- `HEGEL_LETTER_REGISTER` stays off. This block should not go on.
- A next version would name no kinds of content. It would say what to leave out ("nothing the record does not give: no invented prices, meals or conversations") and keep the record as the only source. That is a new declaration and a new test, on fresh held-out cards, since these 24 have now been seen.
- The baseline on held-out cards is now measured: without the block, 24 of 24 as well. Stage 2's result was not a quirk of its cards.

Evaluation only: no card, letter, translation or judgment is ever training data.
