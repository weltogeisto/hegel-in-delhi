# Blind review v2: results (11 October 2026)

94 texts: the five arms of Codex's 8 October block (A0 plain Qwen, A1 Hegel adapter, A2 Schopenhauer control adapter, A3 worked examples, A4 planning) on 14 situations, and 10 hidden controls (real passages from the English translations on his shelf). Two raters, both blind: Claude (`claude-packet-a.csv`, committed before Grok's ratings or the key were seen) and Grok 4.7 via Perplexity (`grok-packet-a.csv`). Grok's rating of packet B repeated its packet-A answers word for word, so the order test is void. The key stays outside the repository; only aggregates are reported here.

## The arms

Balanced comparison: the six long situations (arch, columns, child's map, bowls, letter to Karl, fare letter), two seeds each, 12 texts per arm. Mean of both raters, 1 to 5.

| Arm | Argument | Commitments | Particular | Voice |
|---|---:|---:|---:|---:|
| A0 plain Qwen | **3.21** | 3.42 | 4.21 | 2.83 |
| A1 Hegel adapter | 2.92 | 3.42 | 4.25 | 2.62 |
| A2 Schopenhauer adapter | 2.96 | 3.42 | 4.00 | 2.58 |
| A3 worked examples | 2.88 | 3.17 | 4.42 | 2.83 |
| A4 planning | 2.88 | 3.29 | 4.38 | 2.67 |

No arm beats plain Qwen. On argument plus commitments, every arm scores below A0 by 0.25 to 0.58 points; none of the differences is reliable (case-stratified permutation test, p = 0.21 to 0.49). The Hegel adapter is no better than the Schopenhauer control. The short situations (A0, A1, A2 only) show the same: no difference.

The situation matters far more than the arm. Argument, both raters: arch 3.8, columns 3.0 to 4.0, child's map 3.2 to 4.2, bowls 2.5 to 3.2, letter to Karl 2.0, fare letter 1.5 to 2.0, in every arm alike.

## The controls

Probability that a random control outscores a random model text (0.5 = no separation):

| | Argument | Commitments | Particular | Voice |
|---|---:|---:|---:|---:|
| Claude | 0.71 | **0.89** | 0.15 | 0.93 |
| Grok | 0.61 | **0.92** | 0.00 | 0.63 |

- **Commitments separate clearly for both raters.** The model's plainest gap from the real texts is his positions: it softens them into present-day views, most of all in the letters to Karl.
- **Argument separates weakly.** Several controls are quotation or definition, not argument.
- **Voice depends on the rater.** Claude recognised all ten controls, so its voice score partly measures recognition; Grok marked down their OCR damage.
- **Particular is inverted by design.** The controls answer no Delhi situation; this dimension cannot be tested with them.

## Agreement between the raters (packet A, weighted κ)

Argument 0.84, commitments 0.62, particular 0.62, voice 0.37. Argument is measurable by two model judges; voice is not.

## Faults in this round

- The controls are recognisable by their surface (OCR errors, starts mid-sentence, long quotations, no Delhi scene). Next time: clean text, sentence starts, comparable subjects.
- Grok saw both packets in one chat and carried its answers over; the order test needs truly separate sessions.
