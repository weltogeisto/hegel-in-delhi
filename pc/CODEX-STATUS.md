# Codex status: outcome memory

Updated: 2026-10-11 10:10 UTC. Branch: `codex/outcome-memory`.
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

**Stopped under the unexpected-failure rule.** The follow-up is paused and the
larger three-seed run has not started. No runtime fix, label change, retuning or
state repair was made from the smoke. Both runtime flags remain off.
See [OUTCOME-MEMORY-SMOKE.md](OUTCOME-MEMORY-SMOKE.md) for the full report,
costs, uncertainty flags, false deletions and proposed repairs.

Detailed design and limits: [STRUCTURED-MEMORY.md](STRUCTURED-MEMORY.md).
Local validation output: `C:\hegel\handover\outcome-memory-20261011\validation-v3`.

## Remaining work, in order

1. Hand over the failed-smoke report, preserved raw evidence and verified bundle.
2. Resume only after the unexpected failure has been reviewed. The proposed
   execution-record, temporal-extraction and financial-reconciliation repairs
   are documented but not implemented.
3. The three-new-seed/two-day-per-arm evaluation is held. Do not start it against
   this candidate as if the smoke had established reliability.

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
