# Outcome-memory repair validation: 11 October 2026

The separate repair candidate at `5a1833f975935b56550bb7c4f2dbfd92aeed0a0b`
completed validation with exit 0. Its predeclared development gates passed, so
a fresh diagnostic smoke can proceed. The checker is still too permissive for
live approval. Both runtime flags remain off; the live world is paused.

## Completed checks

- Full `python3 -m unittest discover -s tests`: **844 tests in 705.557 seconds,
  OK (18 skipped)**. The repair file contains **19 new tests**. The previous
  status's count of 21 new tests was incorrect; the focused total of 102 was
  correct.
- All **nine frozen model regressions passed**: actual food consumption versus
  an offer; an attributed report versus its unqualified content; a signature;
  a future visit; departure earlier than the recorded plan; current location;
  and a proposed excursion versus a completed one. These are development cases
  built from known failures, not fresh independent evidence.
- The owned adapter-free WSL llama.cpp server used port 18184 and three
  16384-token slots. Capacity probes succeeded. Cleanup stopped that server;
  no other server was stopped or restarted.
- Independent read-only review verified **179 source files**, **17 protected
  inputs/helpers**, and **304 frozen calibration inputs**. All hashes matched.
  All **217 calibration votes** were recomputed from the saved raw `n_probs`
  distributions and explicit 0/1 token IDs. Saved regression probabilities
  and decisions also matched the fitted settings.

## Calibration and its limits

Protocols are `hegel-factual-claims-v2` and `hegel-record-support-v3`.
The extractor labels claim kind; occurrence checks exclude unverified speech,
draft narratives, intentions and quoted source content. The verifier sees the
original sentence to preserve modality and avoid treating a signature as an
event. This changed protocol requires a new fit; the previous settings are
preserved and rejected by the revised runtime's compatibility check.

All 150 original sentences, labels, source contexts and the ten uncertainty
flags were unchanged. Uncertain rows were excluded from fitting. Temperature
**1.0039266156099043** and threshold **0.34** were selected using only the
non-uncertain calibration partition and the existing retention safeguard.
The inspected holdout remains reused development data.

| Measure | Calibration | Reused holdout |
|---|---:|---:|
| Certain sentences | 98 | 42 |
| Supported retained | 55/55 | 23/24 |
| Unsupported accepted | 26/43 | 10/18 |
| Unsupported rejected | 17/43 | 8/18 |
| Supported concrete sentences retained | 4/4 | 0/1 |
| Claim-vote ECE, before scaling | 0.192858 | 0.216934 |
| Claim-vote ECE, after scaling | 0.192976 | 0.217214 |
| Whole-pipeline ECE | 0.177404 | 0.165059 |

Scaling slightly **worsened ECE in both partitions**. Unsupported acceptance
also worsened versus the earlier atomic protocol: **26/43 versus 24/43** on
calibration and **10/18 versus 5/18** on the reused holdout. Its sole certain
supported concrete holdout sentence was omitted. Those small concrete-positive
samples cannot establish reliable retention beyond the calibration safeguard.
Ten uncertain rows are reported separately: five supported retained, three
supported omitted, and two unsupported accepted under their provisional labels.

Several unsupported concrete premises were missed by extraction or interpreted
as non-assertions inside philosophical prose. Passing the targeted cases does
not establish broad factual support checking. No threshold, label, uncertainty
flag or saved output was changed after inspecting these results.

## Next controlled comparison

The predeclared retention gate applies to the calibration partition, where
55/55 supported and 4/4 supported concrete sentences were retained. That gate
and all nine model regressions passed. A new one-day before/after trajectory is
therefore diagnostic work to measure actual error types and costs, not approval
to deploy the candidate or a claim that calibration improved.

Fresh smoke seed: **1270154432**, sequential baseline then repair candidate,
using immutable `validation-v4` source snapshots and fitted settings. Raw
outputs go to the separate `smoke-v2` directory; failed `smoke-v1` stays intact.
Audit contradictions, statement promotions, semantic repayment, JSON validity,
prompt sizes and wall time. Publish the report and verified bundle before the
held three-seed/two-day evaluation. Stop and report unexpected errors. Do not
start further work after 14:41 UTC; preserve and report any already active job.

Local evidence: `C:\hegel\handover\outcome-memory-20261011\validation-v4`.
The independent review and complete output hashes are in
`validation-v4-review.json` and `validation-v4-output-manifest.json` beside it.
Earlier evidence: [validation](OUTCOME-MEMORY-VALIDATION.md) and
[failed smoke](OUTCOME-MEMORY-SMOKE.md).
