# Fixed-day writers and shelf trial, 12 October

The frozen input list is recorded before generating any trial prose.
All six saved days are complete 3 October histories, produced in different
saved runs. They are known development histories, not independent validation.

| Day | Preserved run | Accepted writing moments |
|---|---|---|
| D01 | 11 October smoke-v1, before | 12:00 |
| D02 | 11 October smoke-v1, after | none |
| D03 | 11 October smoke-v2, before | 10:35, 15:07, 17:17, 20:57 |
| D04 | 11 October smoke-v2, after | 10:35, 14:39, 15:39, 16:29, 18:19 |
| D05 | 8 October six-hour block, flow/deliberative-base | 14:57, 16:57, 20:22, 21:22, 21:52 |
| D06 | 8 October six-hour block, final-integration/plain-qwen | 09:20, 10:30 |

T3 uses seeds 2026101201, 2026101202, 2026101203, in each condition:
legacy input A, compact typed evidence B. That is 36 owl calls (diary,
revision log, Depesche) and 102 writing attempts, 138 scheduled jobs total.
Every sitting uses its saved pre-step state and original first writing
request/accepted decision. No future sitting, completed-day cash snapshot or
owl enters its evidence. Both inputs retain the same original situation and
accepted writing intention, the same current persona, and manuscript memory;
B adds the compact typed view. The compact owl replaces the old mixed record
and retains the 1,950-character block of thoughts labelled as interpretation,
not event evidence. This block stays fixed while only the compact evidence
allowance shrinks to meet the prompt limit. No new decisions, feedback,
training, external lookup or publication occur.

`pc/writer_trial.py` freezes source/input hashes, runs the normal owl and
Engine writing paths, preserves all retries and raw output, and refuses
whole prompts over 7,263 server-tokenized tokens. Initial and actual token
counts must agree. All generation is on the existing adapter-free 8082
server: T3 slot 1; T4 slot 2; slot 0 remains for the world. Prompt caching is
disabled in both inputs. T3 shuffles pairs with a fixed seed, then runs A and
B back to back for every saved moment and seed, with randomized within-pair
order. Report every job's wall time as well as sums by input. Concurrent GPU
load is still a cost limitation; report counts and failures.

T3 blind review shows prose, numbered sentences and the same typed evidence
for both inputs, with random IDs. It distinguishes contradictions, statement
promotions and uncertainty. Counts are at most one of each error type per
sentence. Claude also scores argument on each owl diary and revision log,
using the v2 guide's 1–5 argument rubric. Report per-100-sentence rates per saved day and overall; keep empty,
unusable and cut output visible. No key reaches Git or the rater before
committed scores and their SHA256 hashes.

T3 passes exactly when B has fewer statement promotions per 100 sentences,
no more contradictions per 100 sentences, owl argument no lower than A,
and wall time at most 1.2× A.
Default record enablement and any closed-loop evaluation wait for those
blind results. A clean exit or test pass is not a factuality result.

T4 reuses case `karl` from blind review v2's fresh-evaluation case file, plain
Qwen and the normal Engine writing path, ten seeds 2026101220–2026101229.
OLD freezes the shelf/index and term table at c03a431; NEW freezes main's
current shelf/index and table. Record the exact offered passages and the
number of NEW prompts containing `reden`. The guide is the v2 guide. NEW
passes only if commitments improve by at least 0.5 and argument does not
fall. The earlier all-arm Karl score is context, not a replacement control.

Outputs and the source manifest are under
`C:\hegel\handover\codex-tasks-20261012`. Keys remain outside the repository
until Claude commits scoring. These keys are new daily-review keys; the
original Welt-only v2 review key is never read or copied by this runner.

The partial T3 run in `writer-trial-v2` is superseded and preserved. Claude's
07:57/07:58 review crossed its launch: the thoughts were missing and whole
jobs were shuffled rather than adjacent pairs. Only that worker was
interrupted, with `KeyboardInterrupt`, exit 1 and intact inputs. T4 finished
unchanged: 20/20 nonempty, uncut letters, 10/10 NEW prompts with `reden`.
Its blind packet is `mind/results/shelf-reden-20261012`; no key is included.
The restarted T3 uses a new `writer-trial-v3` directory, the same predeclared
six days and seeds, and the corrected input and pair order. No prior output
is selected or reused as a trial result.
