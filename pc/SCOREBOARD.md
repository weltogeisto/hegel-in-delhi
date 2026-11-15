# Scoreboard

A change to his prose or thinking lands on main only if its number on the same frozen inputs is not worse (`COLLABORATION.md`). The newest result goes at the top of each table.

## Repetition switches: T36's gates on T39's frozen cases

Each switch replays the same four days and seeds as plain Qwen (arm A). The bars: echo share at most 10.99%, a third below A; contradictions at most 0.3 and statements as fact at most 0.5 per 100 sentences above A; argument and voice at most 0.25 below A, by Claude's blind scores.

| Date | Switch | Echo share | Contradictions /100 | Statements as fact /100 | Argument | Voice | Calls per decision | Result |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 14 Nov | D: `HEGEL_DECISION_DRAWS=4` (T49) | 6.64% | 1.385 | 0.656 | 2.65 | 3.05 | 1.27 | **PASS**, all five bars (`pc/T49-ARM-D-RESULT-20261114.md`) |
| 14 Nov | A: plain Qwen, judged blind beside D | 16.49% | 1.574 | 0.930 | 2.70 | 3.10 | 1.06 | the baseline |
| 7 Nov | C: DRY 0.8 | 11.54% | – | – | – | – | – | fail on echo (`pc/T39-RESULT-20261107.md`) |
| 7 Nov | B: echo guard | 19.65% | – | – | – | – | – | fail on echo |

## Prompt screens: blind preference on frozen situations

Two versions of his instructions answer the same recorded situations, three seeds each; Claude judges each situation blind for practical appropriateness (`pc/M1-ORDINARY-LIFE-SCREEN.md`). The bar: the new version preferred in 16 of 24, and no regression the live version doesn't share.

| Date | Screen | n | New preferred | Live preferred | Tie | Flags, new / live | Result |
|---|---|---:|---:|---:|---:|---|---|
| 13 Nov | M1: `soul-ordinary.md` (B) against `soul.md` (A) | 24 | 19 | 3 | 2 | 3 / 3 | not passed as declared: the regression clause fails for either version; B stays off (`pc/exports/m1-screen-20261113/judgment/REPORT.md`) |

## Rewrites: fidelity under the rubric of 7 November

A rewrite keeps the thought's conclusion and recorded facts; its reasoning may change (`DECISIONS.md` 17). Defects are changed or invented facts (E) and changed conclusions or certainty (C). Delta is a diagnostic only (decision 22); the old meaning judge's scores stay as recorded beside these.

| Date | Set | n | No defect | E | C | Old meaning pass | Blind? |
|---|---|---:|---:|---:|---:|---:|---|
| 7 Nov | Training 1 round two, adapter checkpoint 400 (`pc/exports/training1-20261106/new-rubric/`) | 40 | 25 | 12 | 3 | 23 | yes, one case seen |
| 7 Nov | Training 1 round two, prompted Qwen control | 40 | 39 | 1 | 0 | 34 | yes, one case seen |

## Truth: errors in his prose against the record

Counts per simulated day, from an audit of every prose field against steps, situations and records.

| Date | Run | Sentences | Contradictions | Statements as fact | Duplicate charges | Minutes per day | Blind? |
|---|---|---:|---:|---:|---:|---:|---|
| 14 Nov | T49 arm D, the filter at four draws: 471 decision thoughts on T39's four days | 1372 | 19 (1.39/100) | 9 (0.66/100) | – | – | yes |
| 14 Nov | T49 arm A, plain Qwen: the same 471 decisions | 1398 | 22 (1.57/100) | 13 (0.93/100) | – | – | yes |
| 12 Oct | T3 fixed-day, old input (A), 6 saved days × 3 seeds | 2204 | 35 (1.59/100) | 68 (3.09/100) | – | 2391 s total | yes |
| 12 Oct | T3 fixed-day, typed records + compact view (B) | 2226 | 36 (1.62/100) | 62 (2.79/100) | – | 2446 s total | yes |
| 11 Oct | fresh smoke, records + repairs + checker (5a1833f) | 280 | 1 | 2 | 0 | 46 | no |
| 11 Oct | fresh smoke, baseline main (c03a431) | 243 | 3 | 7 | 0 | 14 | no |
| 11 Oct | smoke-v1, records + checker (fab986a) | 109 | 3 | 8 | 1 | 24 | no |
| 11 Oct | smoke-v1, baseline main (c03a431) | 145 | 0 | 3 | 0 | 9 | no |

Each run is one seed and one day, and the closed-loop days diverge, so these are signals rather than rates. T3 replaces them with a fixed-day blind comparison.

## Thinking: blind review, 1 to 5

v2 rows: mean of Claude and Grok, both blind (`mind/results/blind-review-v2/`). Rows from 12 October: Claude alone, blind, scores committed before the key. Argument is the reliable dimension (raters agree at κ 0.84). Commitments is where the model differs most from the real Hegel.

| Date | Set | n | Argument | Commitments | Voice |
|---|---|---:|---:|---:|---:|
| 14 Nov | T49 decision thoughts, D (filter) / A (plain) | 20 / 20 | 2.65 / 2.70 | – | 3.05 / 3.10 |
| 12 Oct | T4e, fresh controls arch + bowls + child's map, B / A | 24 / 24 | 2.75 / 2.75 | 2.75 / 2.63 | 2.71 / 2.58 |
| 12 Oct | T4d, letter to Karl, education paragraph B / A (fresh seeds) | 6 / 6 | 2.17 / 2.00 | 2.83 / 2.00 | 3.00 / 2.83 |
| 12 Oct | T4d, controls fare + columns, B / A | 20 / 20 | 2.80 / 2.75 | 2.85 / 2.90 | 2.95 / 2.85 |
| 12 Oct | T4c, letter to Karl, persona with his conviction on education (B) | 10 | 2.60 | 3.00 | – |
| 12 Oct | T4c, letter to Karl, persona as on main (A) | 10 | 2.30 | 2.00 | – |
| 12 Oct | T4c, fare letter (control), B / A | 5 / 5 | 2.80 / 2.80 | 3.00 / 3.40 | – |
| 12 Oct | T3 owl diaries and revision logs, A / B (argument only) | 36 / 36 | 2.28 / 1.97 | – | – |
| 12 Oct | T4b, letter to Karl, shelf excerpts (Claude, blind) | 10 | 2.00 | 1.80 | 2.40 |
| 12 Oct | T4b, letter to Karl, whole passages with his obedience line (Claude, blind) | 10 | 2.10 | 1.90 | 2.40 |
| 12 Oct | T4, letter to Karl, old shelf (Claude, blind) | 10 | 2.10 | 2.00 | 2.40 |
| 12 Oct | T4, letter to Karl, shelf with the Nuremberg addresses (Claude, blind) | 10 | 2.20 | 2.00 | 2.70 |
| 11 Oct | v2, plain Qwen (A0), six long situations | 12 | 3.21 | 3.42 | 2.83 |
| 11 Oct | v2, letters to Karl, all arms | 10 | 2.00 | 2.15 | 2.40 |
| 11 Oct | v2, real passages (controls) | 10 | 3.10 | 4.65 | 3.70 |

No adapter or prompt technique beat plain Qwen in v2, so plain Qwen is the baseline.
