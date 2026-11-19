# Paris stage 2: the result

19 November. Declared in `pc/PARIS-BACKTEST.md` ("Stage 2 as it runs") and `DECISIONS.md` 55, before any letter or translation existed. The judgments were sealed on main (#104) before the key was applied. The key's sha256 matches `SEALED.json`.

## The finding

**His letters do not sound like Hegel's.** A fresh judge, shown each card with the real letter and the model's letter in random order, picked the real one in **24 of 24 pairs, every time "sure"**, across all three journeys (8 of 8 each). The declared bar for "measurably unlike" was 20.

## Why the judge could tell

In its own one-line reasons, the model's letter:
- **draws a philosophical moral or lectures** in 10 of 24 ("a philosophical flourish about spirit and freedom", "wraps the card in Hegelian talk about the state", "turns the tomb into a meditation on history");
- **is generic or stock** in 8: set openings and closings, general feelings about home, a neat summary of the card;
- **invents details** in 8: a late-night debate on logic, stars over a palace, a snuff from Bonn.

The real letters are fragments full of particulars no model would make up from a card: a train arriving at 12:07, a singer's voice over the chorus, unsure guesses at names ("Snell?"), a dig at an insipid colleague, a tease that he nearly fell in love with a soprano, answers to things his wife wrote.

| Kind of content (share of the 24) | real | the model's |
|---|---:|---:|
| people | 0.88 | 0.88 |
| places | 0.96 | 1.00 |
| prices | 0.08 | 0.04 |
| food | 0.33 | 0.46 |
| sights | 0.79 | 0.92 |
| health | 0.42 | 0.92 |
| family | 0.33 | **1.00** |
| kinds per letter | 3.79 | **5.21** |

The model's letter ticks every box. Every one of them speaks of family and nearly every one of health. The real letters hold fewer kinds and go deep on one or two.

## What it means for the live world

His first letter to Munich (Day 49) is a quarter philosophy and has nothing of what he saw (`pc/exports/m1-trial-20261118/RESULT.md`). This result says the same is true of how the model writes him letters in general, even on the travel version of his instructions. The baseline for any later prompt or world is **24 of 24**. By the declared reading, a change is closer when it lowers that by at least 4 and shares more kinds of content with the real letters.

The second measure (stage 1's codebook on the 72 letters and 24 translations, two coders apart) follows.

Evaluation only: no letter, translation, judgment or result here is ever training data.
