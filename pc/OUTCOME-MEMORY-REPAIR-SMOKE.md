# Outcome-memory repair: fresh smoke audit, 11 October 2026

**Manual audit failed.** Both simulation arms completed with exit 0 and their
source/input integrity checks passed. The revised arm still accepts unsupported
claims and deletes supported prose. Step 4 remains incomplete; both feature
flags stay off, the live world stays paused, and the three-seed evaluation has
not started. No training or deployment took place.

## Frozen run and verification

- Seed **1270154432**, one simulated day (3 October) per arm, sequential before
  then after. Baseline: main `c03a4313c81b473e7aaabac35c503dc11b07e3b8`;
  repaired runtime: `5a1833f975935b56550bb7c4f2dbfd92aeed0a0b`;
  documentation checkpoint at launch: `eae3e05ecd8e2617e2a3011989d36d77005ab349`.
- Frozen validation-v4 source snapshots and fitted settings, base Qwen3.8-27B
  UD-Q4_K_M, no adapter, WSL llama.cpp, owned port 18184 with three 16384-context
  slots. The arms ran sequentially, not concurrently.
- Job finished **13:56:29 UTC, exit 0**. Both runners report `finished: true`,
  one completed day, diary/owl and Depesche present, and no run failure.
- Independent verification passed for **688 protected files**, **180 working
  files**, and **28 raw output files**. Owned server and children stopped;
  no source, protected input, frozen label, setting or raw output was repaired.
- The last full suite on this unchanged runtime was **844 tests in 705.557
  seconds, OK (18 skipped)**; all nine targeted development model regressions
  passed. This handover changes reports only. Those checks did not establish
  factual reliability in the fresh trajectory.

## Results and cost

| Measure | Before | After |
|---|---:|---:|
| Completed steps | 41 | 35 |
| Writing sittings | 4 | 5 |
| Prose fields / published sentences | 48 / 243 | 43 / 280 |
| Direct record contradictions, lower bound | 3 | 1 |
| Statements promoted to facts, lower bound | 7 | 2 |
| Other confirmed unsupported occurrences, lower bound | 1 | 0 |
| Canonical duplicate charges | 0 | 0 |
| Semantic repayment episodes observed | 0 | 0 |
| Cash outflow / closing cash, INR | 1080 / 9421 | 540 / 9961 |
| Invalid generated/extracted JSON | 0 / 78 | 0 / 177 |
| HTTP calls, including native helper calls | 79 | 1434 |
| Maximum generation prompt, tokens / characters | 7263 / 26690 | 11823 / 26687 |
| Wall time per simulated day | 841.851 s (14m 02s) | 2753.279 s (45m 53s) |

Cash arithmetic agrees with every recorded payment in both arms, from opening
cash INR 10501. Legitimate repeated chai purchases in the baseline were not
classified as duplicate settlement. In the revised arm, a later tea offer did
not generate a new charge for an already settled chai. No corn was purchased
in this seed, so the earlier corn repair has targeted development coverage but
no fresh trajectory coverage here. Four actual food-consumption records were
present in the after arm; its owl retained the executed dhaba meal.

These are conservative counts from **one unblinded manual review of all prose
fields**, against authoritative steps, situations and typed records. Repeated
sentences about one signature are multiple published instances, not independent
episodes. Eight ambiguity flags are preserved separately. The trajectories
diverge, and memory plus checking changed together: lower counts in this one
run do not establish a causal improvement or an independent reliability rate.

The revised arm cost **3.2705 times** the baseline wall time. It checked 505
initial/regenerated sentences with 627 atomic votes, regenerated 19 of 43
fields and omitted nine sentences. One diary thought became empty. Its 1434
HTTP calls comprise 90 generations, 87 extractions, 627 votes, 627 template
applications, two tokenizations and one metadata call. Extraction took 806.882
seconds and voting 960.648 seconds, versus 966.069 seconds for generation.
Maximum extraction prompt: 1535 tokens / 6630 characters; maximum vote prompt:
12168 tokens / 26549 characters. Record evidence reached its 24000-character
cap. No HTTP error, invalid JSON or length-truncated completion was observed.

The baseline produced the recoverable warning
`writing: unknown continuation title "Notes on the Difficulty of World History and India's Place in It"`.
The normal correction path recovered and four writing sittings were saved.
Each arm also had two rejected action proposals, corrected by the normal world
validator; these were not runner failures or invalid JSON. The revised arm
waited until household dinner was actually available rather than executing it
before service time.

## Why the manual audit fails

1. **A future message became a completed delivery.** At 10:20 Ramesh says
   “I will convey the message” and turns to check the latch. The regenerated
   10:35 thought asserts “Ramesh has conveyed the message, and the courtesy
   costs little.” Its statement record remains unverified
   (`2026-10-03:statement:1c839f33762cd1bd:1`); no delivery is executed.
   The checker nevertheless accepts the delivery premise at **0.947871**.
2. **A tailor's assurance became a garment fact.** Masterji says the cut is
   true and there are no surprises, while tapping his measuring tape; nobody
   inspects the garment. The 13:32 thought asserts “The cut is true and there
   are no surprises, only Thursday”. The unverified statement is
   `2026-10-03:statement:a5bd8662748ceb9d:1`. The checker accepts the cut at
   **0.852507** and absence of surprises at **0.925440**.
3. **An appointment changed direction.** Hegde's note and the appointment
   record say he will call at the bungalow Monday at ten. The regenerated owl
   says the Directorate is where “I had been asked to visit on Monday at ten.”
   The false visit premise is accepted at **0.581196**. The neighbouring
   “open gate” may be metaphorical and is not counted as another contradiction.
4. **Authoritative availability disappeared from the evidence.** At 12:47 the
   writer's actual situation includes
   `Lunch at a dhaba: dal, rice, roti ₹220` in `for_sale`. The regenerated
   thought expresses hunger, the intended meal and a future question to
   Masterji. Its verifier evidence contains neither `dhaba` nor `roti`; the
   true premise “The dhaba serves dal, rice, and roti” receives **0.218697**,
   below the fixed 0.34 cutoff. The entire sentence is omitted and the diary
   thought is empty. The meal is then correctly executed and charged once.
   This is an execution/evidence coverage gap, not evidence that the meal plan
   was fabricated. No frozen output or evidence projection was changed to
   repair it.

The baseline's counted contradictions are a chai seller called a gatekeeper,
75 minutes at Lodhi described as two hours, and Ramesh described as gone while
the situation still lists him present. Its statement promotions concern the
curtains, the clerk's no-canteen claim and repeated assertions of Ramesh's
unverified missing-signature report. Two apparent inventions about a bookseller
showing a machine may still be metaphor; they are flagged and excluded.

Other after-arm omissions remain uncertain: a current-sitting header, an
opening mixing fixed bungalow background with daily records, and drinking a
purchased chai without a separate consumption event. The runtime itself rounds
07:02 to “six hours ago” at 12:47; the checker's rejection of that wording is
recorded as a rounding mismatch, not a model invention. Counts above exclude
these cases. The local audit preserves each finding, exact sentence, evidence,
probability where available, and eight uncertainty flags.

## Calibration and disposition

Settings stayed frozen: temperature **1.0039266156099043**, cutoff **0.34**,
`hegel-factual-claims-v2` / `hegel-record-support-v3`. All saved verdicts agree
with that numeric rule. The earlier calibration retained 55/55 supported but
accepted 26/43 unsupported sentences; the reused development holdout retained
23/24 and accepted 10/18 unsupported. Its one supported concrete sentence was
omitted. ECE worsened from 0.192858 to 0.192976 on calibration and 0.216934 to
0.217214 on the reused holdout. The reused split is development evidence, not
independent validation. See [repair validation](OUTCOME-MEMORY-REPAIR-VALIDATION.md).

**Stop and hand over under the run protocol.** No larger run, new model job,
retuning, relabelling or source repair follows this failed audit. A subsequent
candidate should first separate memory-only from deletion/checking, measure
coverage of current authoritative situation fields, and preserve qualified
statements and supported intent. Its evaluation needs new frozen examples and
an independently reviewed acceptance rule; changing a threshold on this smoke
would only consume this test as more development data. These are proposed next
steps, not changes made or approval to resume the live world.

## Preserved handover

Raw run: `C:\hegel\handover\outcome-memory-20261011\smoke-v2`.
Logs/exit: `smoke-v2-job.log`, `smoke-v2-job.exit` in that parent directory.
Derived review: `smoke-v2-manual-audit.json`,
`smoke-v2-integrity-review.json`, `smoke-v2-mechanical.json`,
`smoke-v2-mechanical-extra.json`, `smoke-v2-record-stats.json`, prose/evidence
views and `smoke-v2-verified-output-manifest.json`, all beside the raw run.
The bundle is `outcome-memory-repair-smoke-20261011.bundle` in the same parent
directory, against `origin/main`; its verified head and SHA-256 are recorded in
the PR handover. Raw trajectories remain outside Git and are not in the bundle.
Step 5 packets and the Welt-only key remain outside Git, GitHub and bundles.

The attempted canonical status-file update failed with the exact error
`PermissionError: [Errno 13] Permission denied: '/home/ai/hegel-in-delhi/pc/CODEX-STATUS.md'`.
That file is mode 644, owned by root, and was left unchanged. This new report
and the PR carry the current failed-smoke status. No ownership or permission
change was made to bypass the error. The partial handover was preserved and
further experimental work stopped.
