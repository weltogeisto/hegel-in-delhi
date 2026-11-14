# T49 arm D, 13–14 November 2026

The complete replay records 468 decisions and three historical no-call markers on T39's original cases and seeds. D uses main 973b467's preference among up to four replies; draw 1 keeps A's seed, and the other seeds were frozen before generation. Each seed keeps its own earlier thoughts.

| Pooled measure | Saved A | D |
|---|---:|---:|
| Thoughts | 467 | 467 |
| Thoughts echoing a visible earlier phrase | 77 (16.49%) | 31 (6.64%) |
| Calls per actual decision | 1.056 | 1.271 |
| Repetition refusals, all calls | 19 | 51 |

D has 7 decisions with no accepted fresh answer among its initial draws. The complete per-day and pooled table is in exports/t49-arm-d-20261114/MACHINE-TABLE.json. A's numbers are copied from its published table; they were not regraded. All 595 D request chains reconcile with no unknown or unledgered reply.

The fixed echo prerequisite of at most 10.99% is **met**. This is not a full T36 pass or permission to enable the filter. The fresh A/D blind sentence audit and 20 thoughts per arm are in for-claude/; truth, argument and voice scores remain pending. Commit actual scores and input hashes before requesting the private key.

On 13 November the first study client stopped before any request when a natural call took 13.5 seconds. One recovery followed two natural calls of 9.9 and 9.3 seconds; the same 13.2-second per-call limit remained. That shift stopped cleanly at 20:42:26 Berlin with 294 decisions. The dated 14 November continuation began at t9-file/015, seed 1831, preserving every earlier reply. The original plain-Qwen server, Pi timer, power settings and live decision switch were unchanged. No training was started.

All original sources, cases, output bytes and failures remain preserved. Source and request manifests, exact runtime, seed table and both stop/recovery receipts accompany the result.

## The blind half and the verdict, 14 November (Claude)

**Arm D passes T36 in full.** It is the first repetition switch to do so; B and C failed on the echo measure.

| Measure | A | D | Difference | Bar | |
|---|---:|---:|---:|---|---|
| Thoughts echoing a visible earlier phrase | 16.49% | 6.64% | −9.85 points | at most 10.99% | pass |
| Contradictions per 100 sentences | 1.574 | 1.385 | −0.189 | at most +0.3 | pass |
| Statements as fact per 100 sentences | 0.930 | 0.656 | −0.274 | at most +0.5 | pass |
| Argument, 1 to 5 | 2.70 | 2.65 | −0.05 | at most 0.25 lower | pass |
| Voice, 1 to 5 | 3.10 | 3.05 | −0.05 | at most 0.25 lower | pass |

**What was judged.** All 942 thoughts, 471 per arm, sentence by sentence against the evidence each case had before the decision; and 20 thoughts per arm for argument and voice. The packet carried no arm labels. The judgment was merged before the key was asked for (#37, `58b4dbc`); the key Astra released (#38) has the hash published beforehand, and each of its text hashes matches the text judged. `tools/blind_verdict.py` computed the table; `judgment/VERDICT.json` holds it.

| Day | A: contradictions | D: contradictions | A: statements as fact | D: statements as fact |
|---|---:|---:|---:|---:|
| T9 file (3 October) | 5 in 290 sentences | 6 in 285 | 2 | 0 |
| T9 vouchers (4 October) | 8 in 365 | 5 in 347 | 9 | 5 |
| Day 12 (13 October) | 2 in 377 | 3 in 378 | 0 | 2 |
| Day 27 (28 October) | 7 in 366 | 5 in 362 | 2 | 2 |
| Pooled | 22 in 1,398 | 19 in 1,372 | 13 | 9 |

**How to read it.** The chance check declared before the key (`judgment/CHANCE.json`) says random halves differ by up to ±0.68 contradictions and ±0.44 statements as fact per 100 sentences, and by ±0.35 on argument and voice. Every difference here lies well inside that. So the finding is this:

- **Repetition falls by 60%,** from 16.5% to 6.6% of thoughts, on each of the four days.
- **Truth and quality stay where they were,** within what this test can see. The filter does not make him more accurate; it does not make him less so.
- **The cost is 1.27 calls per decision** against 1.06, about a fifth more of the mind's time.

**What a pass allows, and what it does not.**

- The filter may run on shadow as a provisional trial, with `HEGEL_DECISION_DRAWS=4`. That changes what goes live on Hegel, so it needs Welt's word. Back to 1 turns it off.
- Training 3's comparator is now plain Qwen with this filter. Training has to beat arm D, not arm A.
- Whether a training day is still worth spending is Welt's decision. Sampling goes on either way.

Evaluation only: none of these replies or judgments is ever training data.

