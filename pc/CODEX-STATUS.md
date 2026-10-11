# Codex status: outcome memory

Updated: 2026-10-11 08:56 UTC. Branch: `codex/outcome-memory`.
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

The latest focused run passed 63 tests. The full unittest suite and revised
150-sentence calibration are running in WSL tmux `hegel-outcome-checks`.
Staging also found `tests/test_blind_review.py:43: new blank line at EOF`.
This formatting warning is parked until the frozen validation run finishes.
The dedicated test server uses port 18184, three slots with 16384 context each,
and no adapter. Three concurrent warm-up requests succeeded; observed GPU memory
was 19338/24576 MiB. This establishes initial capacity, not overnight stability.

The earlier full-sentence checker failed: its 0.9 threshold retained none of
seven supported concrete held-out sentences. Its ECE changed from 0.1733 to
0.1631. The replacement checks atomic factual premises and flags ten ambiguous
manual labels. Reuse of the inspected split is development, not independent
confirmation. New calibration metrics are pending.

Detailed design and limits: [STRUCTURED-MEMORY.md](STRUCTURED-MEMORY.md).
Local validation output: `C:\hegel\handover\outcome-memory-20261011\validation-v3`.

## Remaining work, in order

1. Review the full suite and calibration, including false deletion and false
   acceptance. Stop and report the exact error on an unexpected failure.
2. Run the frozen one-seed, one-day before/after smoke test; manually audit
   contradictions, statements promoted to facts, duplicate charges, JSON,
   prompt sizes and elapsed time. Produce the report and verified bundle.
3. Run three new seeds for two days per arm on the isolated test instance,
   concurrently only if capacity holds. Preserve all raw outputs.

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
