# M1's trial, read: the vocabulary moved, the topics did not

Read on the night of 18 November by Claude in the cloud, as declared in `pc/M1-TRIAL-READING.md` before any coding. The codes were sealed on main (#85) before the key was applied. The key matches its sealed sha256 (`f12138aa…a7f0`).

## The declared reading: "worse", by the letter of the rule

The rule said "worse" if philosophy proper rises by both coders, or if echo, calls or refusals leave the old days' range upward. Both happened, each by a hair:
- **Philosophy proper:** 6.0% to 7.3% by coder A, 7.3% to 8.0% by coder B. That is one or two sentences of 150.
- **Calls per decision:** 1.42 on Day 49, just above the old days' 1.27 to 1.39. The two new days together are inside the range, at 1.29.

The rule set no margin. That was Claude's mistake when declaring it, and it is not corrected after the fact. Read for what it means, the trial shows a large change in how he speaks and no measurable change, for good or ill, in what he speaks about.

## Machine counts, per day

| Day | Instructions | Thoughts | Lecture-hall terms per thought | Thoughts without them | Echoes of a shown thought | Calls per decision | Steps with a refusal | Terms per spoken line |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 46 | old | 33 | 2.03 | 21% | 2 | 1.39 | 3 | 0.32 |
| 47 | old | 37 | 2.81 | 0% | 1 | 1.27 | 0 | 0.62 |
| 48 | new | 32 | 1.31 | 34% | 1 | 1.16 | 0 | 0.25 |
| 49 | new | 31 | **0.71** | **48%** | 1 | 1.42 | 0 | 0.25 |

Both new days are below Day 47 on lecture-hall terms, as declared: a fall of 50% to 75%. Mean thought length stayed at 64 to 75 words.

## What his thoughts are about (two blind coders, kappa 0.93)

| Topic | Old, A / B | New, A / B | His letter to Munich, A / B | His real letters home (stage 1) |
|---|---:|---:|---:|---:|
| Food, drink and the body | 30% / 29% | 38% / 37% | 8% / 8% | 1–4% |
| People met | 30% / 29% | 21% / 21% | 24% / 32% | 7–11% |
| Money and prices | 14% / 14% | 5% / 5% | 0% / 0% | 0% |
| Travel and errands | 13% / 13% | 11% / 11% | 16% / 16% | 24–36% |
| Philosophy proper | 6% / 7% | 7% / 8% | **24% / 20%** | 1–2% |
| Other | 7% / 7% | 13% / 15% | 12% / 16% | 3–8% |
| Sights, art and theatre | 0% / 0% | 1% / 1% | **0% / 0%** | **40–42%** |
| Family | 0% | 0% | 8% / 0% | 7–8% |

By day, philosophy proper was 5 or 6 sentences of 83 on Day 46, 4 or 5 of 67 on Day 47, 3 of 77 on Day 48 and 8 or 9 of 73 on Day 49. The day he wrote to Munich, and revised his thesis on India, carries the rise.

## What it says

1. **The new instructions changed how he speaks, strongly and at once.** Lecture-hall vocabulary inside his everyday thoughts fell by half to three quarters. Half of Day 49's thoughts carry none of it.
2. **They did not change what he thinks about, because there was little left to change.** On the old days, sentences whose point is philosophy were already rare (6–7%). Hunger, money and people filled his days. The screen's "philosophy" was mostly doctrinal words inside practical sentences ("the immediate negation of hunger"), and that is what fell.
3. **Money gave way to food and the body** once the letter from Munich paid his debts: 14% to 5%.
4. **His first letter home is closer to the real Hegel's letters than his thoughts are,** at a distance of 0.51 to 0.59 against 0.62 to 0.64. But a quarter of it is philosophy, against 1–2% in the real letters, and none of it is what he saw, against 40%. His Delhi has offered him nothing to see yet; the museums, concerts and plays come on Day 52.

## Limits

- Two days a side. The days differ in what happened in them: no money on Day 46, the letter on Day 47, a two-hour gap on Day 48, Ramesh back and a letter written on Day 49.
- Both coders are Claude agents; plain Qwen can code the same sheet as a third coder (`tools/paris_profile.py requests`).
- The letter is a single text of 25 sentences.

## Advice

Keep the trial. The change it was made for is large and clear, and nothing measurable got worse beyond a sentence or two. Read it again after a week of days, with a margin declared in advance.

Evaluation only: no sentence, code or result here is ever training data.

## The third coder, 19 November

Plain Qwen coded the same 325 sentences on the PC (`coder-qwen-20261119/`, 325 of 325 replied; `CODES-Q.jsonl`; every reply was one code). It is the model that wrote the thoughts, and it reads them differently. Its agreement with the two Claude coders is moderate: kappa 0.57 and 0.58, where the Claude coders agree at 0.93.

| Philosophy proper (code 9) | old (Days 46, 47) | new (Days 48, 49) | his letter |
|---|---:|---:|---:|
| Coder A | 6.0% | 7.3% | 24.0% |
| Coder B | 7.3% | 8.0% | 20.0% |
| Qwen | 22.7% | 14.0% | 32.0% |

The declared rule named the two Claude coders, so the verdict above stands. Qwen dissents in direction: by its reading, philosophy fell by almost nine points. All three agree that his letter carries far more philosophy than his thoughts do. The second reading (`pc/M1-TRIAL-READING.md`), with its margins and its paired forks, is the test. This table goes beside it (`RESULT-THREE-CODERS.json`).
