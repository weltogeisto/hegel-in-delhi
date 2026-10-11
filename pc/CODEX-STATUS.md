# Codex status: outcome memory

Updated: 2026-10-11, after validation-v4 review. Branch: `codex/outcome-memory`.
Starting main commit: `c03a4313c81b473e7aaabac35c503dc11b07e3b8`.

This is a development checkpoint. Step 4 is not complete and is not deployed.
The live world remains paused. No training is running or authorised by this work.

## Implemented, under validation

- Stable daily event, attributed-statement, payment and work records; statements
  remain unverified statements. Writers receive labelled evidence within their
  existing budgets. Canonical transaction IDs prevent duplicate settlement.
- A claim extractor and numeric yes/no support check using the base 27B model's
  raw `n_probs`; one prose regeneration, then exact omission of unsupported
  sentences, with an audit of requests, evidence and verdicts.
- Calibration, isolated before/after trajectory and blind-packet tools, plus
  tests. Runtime flags remain off by default until the evidence is reviewed.

## Evidence so far

The full suite passed at checkpoint `e537ed4`: **825 tests in 708.777 seconds,
OK (18 skipped)**. The validation job exited 0, verified the frozen source and
protected inputs, and stopped its own test server. The 150-sentence atomic
calibration completed; raw requests, votes and frozen labels are preserved.
The dedicated test server uses port 18184, three slots with 16384 context each,
and no adapter. Three concurrent warm-up requests succeeded; observed GPU memory
was 19338/24576 MiB. This establishes initial capacity, not overnight stability.

The earlier full-sentence checker failed: its 0.9 threshold retained none of
seven supported concrete held-out sentences. Its ECE changed from 0.1733 to
0.1631. The replacement checks atomic factual premises and flags ten ambiguous
manual labels. Reuse of the inspected split is development, not independent
confirmation. The new fit uses temperature 2.86013 and threshold 0.20. Factual
claim ECE improved on calibration (0.18076 to 0.10566) and worsened on the reused
holdout (0.15670 to 0.17542). The rule kept 53/55 supported calibration sentences
and 24/24 supported holdout sentences; it also accepted 24/43 and 5/18 unsupported
sentences, respectively. The predeclared retention gate passed; this is not
approval for live use. Only 4 and 1 certain supported concrete sentences remain
in those partitions. Ten ambiguous labels are reported separately.

See [OUTCOME-MEMORY-VALIDATION.md](OUTCOME-MEMORY-VALIDATION.md) for the review.
The frozen one-day before/after smoke finished with exit 0 at 09:56:10 UTC;
both arms completed 31 steps and cleanup verified unchanged source/inputs and
stopped the owned server. Baseline: 544.034 seconds; after: 1448.087 seconds.
The manual audit found an unexpected execution/evidence mismatch: corn purchases
increment the simulator's snack state, but the record projection omits that
consumption. A true consumption premise is consequently deleted. It also found
three after-arm record contradictions, eight statement-to-fact promotions and
one semantic resettlement episode (INR 60 under new purchase IDs). These are
conservative, single-reviewer counts, not independent validation.

The failed run was stopped, handed over and preserved. Welt subsequently asked
what comes next within the authorised autonomous window. A separate repair
candidate now records executed food consumption and current location, labels
plans as intentions, gives NPCs actual settled receipts, and distinguishes new
purchases from repayment by explicit purpose and canonical source ID. The
world's own obligation settlement remains authoritative; dialogue cannot create
a new payable debt. Legitimate repeated purchases remain possible.

The revised extractor preserves claim kind and the verifier receives the original
sentence, so a future visit or signature need not become an asserted event.
Unattributed occurrence votes exclude unverified statements, draft narratives,
plans and quoted source content. Both protocols are versioned; old fitted
settings fail the compatibility check. No frozen labels or old outputs changed.
The focused suite passed **102 tests in 0.304 seconds, OK**, including 19 new
regressions (the earlier count of 21 was incorrect). The full suite then passed
**844 tests in 705.557 seconds, OK (18 skipped)** at repair checkpoint `5a1833f`.
All nine model regression checks passed. Exit 0, final source/input hashes and
owned-server cleanup were independently verified. The new development fit uses
temperature 1.003927 and threshold 0.34. Calibration retained 55/55 supported
sentences, but accepted 26/43 unsupported; reused holdout retained 23/24 and
accepted 10/18 unsupported. Its one supported concrete holdout sentence was
omitted. Claim ECE worsened slightly with scaling, from 0.192858 to 0.192976 and
from 0.216934 to 0.217214. This is not reliable enough for live approval.

The calibration-partition retention safeguard and targeted regression gates
passed; a separate fresh diagnostic smoke can now proceed with frozen settings,
seed 1270154432. Both runtime flags remain off. The larger three-seed run remains
held until that smoke is manually reviewed. See
[OUTCOME-MEMORY-REPAIR-VALIDATION.md](OUTCOME-MEMORY-REPAIR-VALIDATION.md).
See [OUTCOME-MEMORY-SMOKE.md](OUTCOME-MEMORY-SMOKE.md) for the full report,
costs, uncertainty flags, false deletions and proposed repairs.

Detailed design and limits: [STRUCTURED-MEMORY.md](STRUCTURED-MEMORY.md).
Local current validation: `C:\hegel\handover\outcome-memory-20261011\validation-v4`.
The completed `validation-v3` and failed `smoke-v1` remain preserved.

## Remaining work, in order

1. Completed: full suite, revised development calibration, targeted model
   checks, source/input verification and owned-server cleanup. No old labels,
   frozen settings or saved outputs changed. Calibration limitations are above.
2. Freeze a new one-seed/one-day before/after smoke with seed 1270154432;
   audit all requested error types and costs. Publish its report and verified
   bundle before the held three-new-seed/two-day-per-arm evaluation.
3. Stop and report an unexpected error; preserve every partial output. Do not
   retune settings or repair the frozen trajectory to make it pass.
4. Save a checkpoint and pause by 14:41 UTC (16:41 Berlin). Preserve any frozen
   active job and report it; do not start further work after that deadline.

Step 5's two differently shuffled review packets are prepared with the same
94 texts, including ten hidden controls. The identity key stays with Welt
outside Git. Neither packets nor key are published here. Grok 4.7 rates first;
Claude rates second. Sixteen blank fresh situations await Welt's authorship.

## Coordination

The draft PR is the shared progress log. Update this file at meaningful
checkpoints and the PR when a run starts, finishes or fails. Include exact
commit IDs, commands, results and pending work. Do not treat a checkpoint as
approval to merge or deploy. While a validation run is active, its source
snapshot is frozen; do not edit those files in the PC checkout. Read remote
changes before integrating them and preserve other contributors' work.
