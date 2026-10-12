# Scoreboard

A change to his prose or thinking lands on main only if its number on the same frozen inputs is not worse (`COLLABORATION.md`). The newest result goes at the top of each table.

## Truth: errors in his prose against the record

Counts per simulated day, from an audit of every prose field against steps, situations and records.

| Date | Run | Sentences | Contradictions | Statements as fact | Duplicate charges | Minutes per day | Blind? |
|---|---|---:|---:|---:|---:|---:|---|
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
