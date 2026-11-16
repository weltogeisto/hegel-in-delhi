# Words and the world, 16 November 2026

Written by Claude on the PC, on `codex/words-meet-world-20261116`, from `main` at `675aef5`. Nothing here is live: it goes on with a merge to main and the next pull of main into shadow, on Welt's word.

## What Welt saw on Day 47 (his 17 November, the IIC, 10:39–14:29)

1. The guard's voice offered a cafeteria, a meal token and a lift. The world has none. He said for three hours, in his own thoughts, that he would go and eat, and each step chose `stay` or `talk`.
2. At 14:29 he chose `eat` at the IIC and bought nothing. The world accepted it, fed no one, and the page drew it as an ordinary step. His last meal in the world is 9 November.
3. The page drew the library as a fixed picture: Hegel always reading, the same four figures, and the librarian's idle animation an eating pose every few seconds. The guard and the programme officer have no figure and were never drawn. The page read "Talking with the guard at the **librar**y" as reading, because "librar" matched the reading words.
4. The guard's `does` came back in the first person ("I gesture towards the front desk…").

## What changes

| Where | Change |
|---|---|
| `world/data/places.json` | The IIC sells food, as the real one does: a dining-hall lunch (₹480, a meal), a sandwich and tea with biscuits (snacks), filter coffee (not food). |
| `world/world.py` `check()` | `eat` away from home needs a meal or snack bought there. Otherwise the step is refused, with what is sold here, where else a meal is open (nearest first, with the walk) and what the kitchen at home says. Chai or coffee alone is not a meal. |
| `world/world.py` `situation()` | When he is hungry, one line before the Body line: "Food, if you are hungry: …". At a place that sells food it does not repeat "For sale here". |
| `world/world.py` `situation()` | After `TALK_RUN` (4) talk steps in a row at one place, one plain fact: "You have been talking at the IIC for 12 steps in a row, since 10:39 (answers from …)". It is a fact, not a cap; nothing stops him. |
| `world/voices.py`, `world/engine.py`, `mind/voices.md` | A voice is told when its place serves no food and where a meal can be had; "do not offer, promise or point him to a canteen, counter, token, coupon, pass, lift, queue or office that this message does not name". A `does` in the first person is dropped. |
| `docs/index.html` | The verb of the step decides what he is doing (so a talk at the library is a talk). The guard and the programme officer have figures. Talking, or an answer in the last ten minutes: he stands up and they stand face to face in the aisle. Resting: he dozes. Eating at the IIC is drawn in a dining hall (`IICD_ROOM`), not the library. The librarian no longer eats. |

## What does not change

- The household kitchen. It is shut while Ramesh's wage and the groceries are owed, and a debt is paid only when its creditor is present (Ramesh is there Monday, Thursday and Saturday). That is the world as designed; with food at the IIC and in Khan Market it no longer starves him. It resolves on Thursday.
- What he chooses. The mind decides; the world now tells it the truth about where food is.
- No flag. These are corrections, not a new feature. Everything else on shadow stays as it is.

## Tests

`tests/test_words_meet_world.py` (19: the IIC meal, the refusal and its wording, chai against samosa, the food line by hunger and by meal window, the talk run, the voice facts and the first person, the page's verbs and figures; the page tests need `node`). `tests/test_needs.py` adjusted for the IIC's new food.

Whole suite under WSL, 16 November, isolated env: `main` (`675aef5`) 1,150 tests, all pass, 28 skipped; this branch 1,169 tests, all pass, 31 skipped (the 3 more are the page tests, which skip where there is no `node`; with `node`, on Windows, the 19 new tests pass).

## To go live

Welt's word, then merge to main; Astra (or Claude on the PC) pulls main into shadow under the tick lock as for the letter. The site is `docs/` and goes with main. No change to `~/.config/hegel/env`.
