# Outcome-memory smoke: 11 October 2026

Status: the isolated job completed, but the candidate failed its intended
reliability goal. An unexpected mismatch between execution and recorded evidence
requires a stop under Welt's protocol. The larger three-seed run has not started.
The live world is paused; no training or deployment occurred.

## Frozen run and completion

Implementation checkpoint: `fab986a7e3bfc828b8fe0fc110e36b0f2be5a7b5`.
Baseline main: `c03a4313c81b473e7aaabac35c503dc11b07e3b8`.
Both immutable snapshots used the same adapter-free Qwen3.8-27B GGUF and WSL
llama.cpp build 11429, on an owned loopback server at port 18184. The fitted
temperature (2.860131) and threshold (0.20) were unchanged. Seed: 2016829042;
one simulated day, 3 October, per arm; arms ran sequentially.

The job exited **0** at 09:56:10 UTC. Both arms completed 31 steps and produced
their owl diary and Depesche. Cleanup independently checked the protected-input
and tracked-source hashes, found no changes, and stopped the owned server and
children. No failure exception was recorded. Same initial seed does not give
identical closed-loop trajectories; generation and subsequent actions diverge.

| Measure | Before | Outcome memory + checker |
|---|---:|---:|
| Wall seconds per simulated day, including owl | 544.034 | 1448.087 |
| Wall time | 9 min 4 sec | 24 min 8 sec |
| HTTP calls, including metadata/template calls | 55 | 830 |
| Ordinary generation calls | 54 | 72 |
| Extraction calls / one-token support votes | 0 / 0 | 59 / 348 |
| Final prose fields / sentence spans inspected | 35 / 145 | 34 / 109 |
| Writing sittings | 1 | 0 |
| Fields regenerated / sentences subsequently omitted | 0 / 0 | 18 / 16 |
| Empty final prose fields | 0 | 1 diary thought |
| JSON parsed successfully, schema-requested responses | 54/54 | 131/131 |
| HTTP errors / truncated chat finishes | 0 / 0 | 0 / 0 |
| Maximum generation prompt tokens | 5064 | 10476 |
| Maximum support-vote prompt tokens | n/a | 11219 |
| Maximum generation prompt characters | 18510 | 25280 |
| Maximum evidence-view characters | n/a | 23997 of 24000 |
| Cash outflow / closing cash, INR | 400 / 10101 | 540 / 9961 |

The checking arm cost **2.66 times** the wall time. Its 348 votes are one-token
calls, so HTTP-call counts are not comparable to full generations as GPU work.
Prompts fitted the dedicated 16384-token slots; no context-overflow or HTTP
failure occurred. One otherwise valid first action was refused because it tried
to eat at home before a household meal was available, then corrected normally.
The after arm did not write a manuscript, so this smoke does not exercise its
writing guard in a completed writing sitting.

## Manual factual audit

One unblinded Codex audit inspected all final diary thoughts, the manuscript
where present, owl diary/revision prose and Depesche against the saved actions,
observations, statements and payments. It also inspected the checker's saved
verdicts and omissions. These are conservative incident counts, not an
independent human evaluation or estimates of the model's general error rate.
Ambiguous cases were flagged separately rather than forced into binary labels.

| Confirmed incident category | Before | After |
|---|---:|---:|
| Direct contradictions with execution/location/payment records | 0 | 3 |
| Unqualified statements promoted into facts | 3 | 8 |
| Semantic resettlement episodes | 0 | 1, two items totalling INR 60 |
| Additional ambiguous cases, excluded from those counts | 3 | 4 |

Categories overlap: the unpaid-purchase premise is both a contradiction and a
statement promotion. The zero baseline contradiction count is a lower bound,
not a certificate that its prose is correct. Several claims remain unsupported
or ambiguous without a direct contrary record.

The three after contradictions concern a walk narrated as still underway after
arrival, the current bungalow location while actually at the garden, and the
endorsement of a vendor's unpaid-cash claim despite a settled receipt. Statement
promotions carry unverified mist, a proposed peacock excursion, fan settings and
a bolted gate into factual narration. Fan and gate claims recur in the owl and
Depesche. The baseline likewise promotes reported room/kettle conditions.

Both cash totals reconcile exactly with their transaction entries. The after
arm has no replay of the **same canonical ID**, but the vendor's denial of a
settled INR 60 purchase induces a new purchase of the same two items. New IDs
make that semantic repayment invisible to the ID replay detector. The baseline
receipts have no canonical IDs, so canonical-identity coverage there is unknown.
This is not grounds for deduplicating all similar legitimate purchases.

## Unexpected execution/evidence mismatch: stop

`World.apply` consumes catalogued corn through `feed`, incrementing the snack
state. The record projection does not preserve that executed consumption, while
its evidence policy says purchases do not attest eating. In the after trajectory
at 12:07, buying corn changes snacks from 2 to 3. The checker later assigns
0.1099 support to the true corn-consumption premise and removes its sentence.
The sentence also contains a chai accompaniment that is less certain; the loss
of the true corn premise is confirmed independently of that additional clause.

This is an implementation failure, not an exception or a calibration result.
The requested audit exposed it even though the unit suite and job exit were
clean. No source, example, state, label or fitted setting was changed to repair
the frozen run. The follow-up is paused; the larger run is held.

The checker also makes at least three clear false deletions: a departure earlier
than the saved plan, a future intention misread as a completed visit, and the
author's signature misread as an externally provable event. Several true parts
of mixed sentences are lost with unsupported clauses. No new accuracy or ECE is
claimed from this partial adjudication of the checker's intermediate sentences.

## Repair proposal, not implemented

1. Record execution effects, including automatic food consumption, from the
   actual transition. Preserve time, source and identity; leave unknown legacy
   effects unknown. Add a regression using the observed snack transition.
2. Give intentions and current locations an explicit status in evidence; do not
   turn a proposed/future visit or an author signature into a completed event.
   Cover those exact extraction failures and the missing-plan case with tests.
3. Reconcile financial action intent with settled receipts before execution.
   Preserve attribution of a disputed payment. Distinguish settling an existing
   obligation from buying another item; similarity alone cannot establish replay.
4. Evaluate a revised version on fresh frozen inputs with acceptance rules fixed
   before seeing outputs. Keep this failed smoke and the reused calibration split
   as development evidence. Do not retune the current threshold from these texts.

The existing full suite remains **825 tests, OK (18 skipped)** at runtime
checkpoint `e537ed4`; later changes through the smoke checkpoint were documents
and whitespace. This report does not convert that unit-test pass into a runtime
reliability pass. The proposed repairs have not been run or tested.

## Preserved handover

Raw run: `C:\hegel\handover\outcome-memory-20261011\smoke-v1`.
Its completion, cleanup, HTTP ledger, steps, day files and 809 claim-audit rows
are preserved. `smoke-output-manifest.json` records SHA-256 hashes for all 28 run
files. Mechanical aggregates are in `smoke-mechanical.json`,
`smoke-mechanical-extra.json` and `smoke-record-stats.json`. Exact manual findings
and uncertainty flags are in `smoke-manual-audit.json` beside the run, outside Git.

The feature-branch bundle contains code and this report, excludes Step 5 packets
and their Welt-only key, and requires the stated main commit as its prerequisite.
Its path and `git bundle verify` output are reported separately after creation.
