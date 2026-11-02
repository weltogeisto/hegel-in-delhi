# T8: owl thesis movements on three fixed records

DONE: all 30 declared seeded jobs completed once on frozen current main `61accbd`, 17:48:11–17:57:00 UTC on 13 October 2026. Wrapper exit 0; every response nonempty usable JSON, one call per job, no retries, no errors or length stops. Every response finished with `stop`. Nothing in the owl prompt or runtime was changed.

| Saved day | Seeds moving any thesis | Seeds moving India |
|---|---:|---:|
| shadow 5b52d7f, Day 12 / 2026-10-13 | 6/10 | 1/10 |
| 8 October final-integration/plain-qwen rehearsal, Day 2 / 2026-10-03 | 4/10 | 1/10 |
| 8 October continuation-v2/focused-next-day rehearsal, Day 3 / 2026-10-04 | 6/10 | 0/10 |

Neither no-India control exceeds the predeclared **more than 2/10** condition, so this result does not call for the conditional stricter-rule rerun. It also does not establish that the existing rule is correct: the two India movements below are retained, and are driven by local household/administrative evidence rather than evidence about India and world history. These are counts, not a pass score, and no blind packet or quality gate was created.

## The two India movements

| Record and seed | Change | Evidence times resolved by the unchanged runtime |
|---|---|---|
| day12, 2026101381 | unshaken → shaken | 08:49, 12:28, 17:30 |
| control-file, 2026101384 | unshaken → shaken | 09:20, 17:20 |

Day12 seed 2026101381 cites the idli thought at 08:49, the cold-sambar/collar/walk thought at 12:28, and Hegde seeking a second room at 17:30. The file-control seed 2026101384 cites the Directorate name/person discussion at 09:20 and the habit/routine discussion at 17:20. No result was excluded or replaced.

## Every declared seed

“None” means no status changed from that record’s original starting statuses. Counts use the changes actually applied by `owl.revise`, including its existing timestamp gate. All 17 status changes proposed by these raw answers were applied; there are no hidden rejected proposals. Evidence excerpts are in the JSON and original outputs.

### shadow 5b52d7f, Day 12 / 2026-10-13

Original starting statuses: india: unshaken; state: unshaken.

| Seed | Applied changes and evidence times | Wall seconds |
|---|---|---:|
| 2026101380 | None | 20.801 |
| 2026101381 | india unshaken → shaken @ 08:49, 12:28, 17:30 | 11.542 |
| 2026101382 | None | 13.360 |
| 2026101383 | None | 14.989 |
| 2026101384 | state unshaken → shaken @ 08:04, 15:33 | 12.366 |
| 2026101385 | state unshaken → shaken @ 08:04, 08:19 | 15.374 |
| 2026101386 | None | 14.476 |
| 2026101387 | state unshaken → shaken @ 08:04, 17:30 | 15.461 |
| 2026101388 | state unshaken → shaken @ 08:04, 08:19 | 14.264 |
| 2026101389 | state unshaken → shaken @ 08:04, 08:19 | 14.447 |

### 8 October final-integration/plain-qwen rehearsal, Day 2 / 2026-10-03

Original starting statuses: india: unshaken; state: unshaken.

| Seed | Applied changes and evidence times | Wall seconds |
|---|---|---:|
| 2026101380 | None | 28.575 |
| 2026101381 | state unshaken → shaken @ 06:40, 09:20 | 20.353 |
| 2026101382 | state unshaken → shaken @ 17:20, 17:45 | 23.098 |
| 2026101383 | None | 21.614 |
| 2026101384 | india unshaken → shaken @ 09:20, 17:20; state unshaken → shaken @ 06:40, 10:10 | 22.397 |
| 2026101385 | None | 21.983 |
| 2026101386 | state unshaken → shaken @ 10:10, 18:47 | 21.183 |
| 2026101387 | None | 20.109 |
| 2026101388 | None | 23.529 |
| 2026101389 | None | 23.762 |

### 8 October continuation-v2/focused-next-day rehearsal, Day 3 / 2026-10-04

Original starting statuses: india: unshaken; state: shaken.

| Seed | Applied changes and evidence times | Wall seconds |
|---|---|---:|
| 2026101380 | state shaken → revised @ 09:40, 16:30, 18:30 | 18.155 |
| 2026101381 | state shaken → revised @ 09:40, 16:30, 18:30 | 11.421 |
| 2026101382 | None | 12.244 |
| 2026101383 | None | 13.292 |
| 2026101384 | None | 12.051 |
| 2026101385 | state shaken → revised @ 09:40, 16:30, 18:30 | 12.154 |
| 2026101386 | state shaken → revised @ 09:10, 16:30, 18:30 | 12.484 |
| 2026101387 | state shaken → revised @ 09:40, 16:30, 18:30 | 14.034 |
| 2026101388 | None | 11.901 |
| 2026101389 | state shaken → revised @ 08:45, 18:30, 20:35 | 15.115 |

## Frozen setup and verification

The three original records and seeds 2026101380–2026101389 were named, read and committed in [the pre-generation protocol](../../../pc/T8-OWL-THESIS-PROTOCOL-20261013.md) at primary f51696b before any generation. Both controls contain Delhi household/administrative events, with no material about India’s place in world history. Their normal baseline India thesis remains in the prompt. Control-vouchers inherits a shaken state thesis, which was retained. Each seed starts from a fresh copy of its original saved state.

Source main61 is unchanged by the subsequent task-only main922. Normal `owl.write`, modern-name gate, schema, sensitive flags, evidence resolution and application were retained. Temperature 0.8; reasoning disabled, as captured on Pi. The Saturday file control keeps the normal Depesche1 and 2,200-token allowance; the other two keep 1,200. Only `seed` and spare `id_slot=1` are added to the normal HTTP request. No adapter, prompt fitting or resampling. First prompt counts: Day12 7,182, file control 6,465, voucher control 7,183, equal measured serving-template/tokenizer and actual usage.

All 182 frozen source files independently match Git/archive/native snapshot after completion. All saved input, protocol, harness and output hashes match. The verifier replayed the existing parser/knowledge/evidence path from every original response without any model call; all saved results and final statuses match exactly. Across the ten seeds, each day’s first requests differ only by seed/routing metadata from the original capture. The complete raw output seals and source checks are in [CHECKS.json](CHECKS.json).

All 30 raw server response files are retained byte for byte in `raw/`. `requests/` contains each day’s actual first request at seed2026101380; the other nine differ only in the declared seed. All original request hashes remain in CHECKS and outside Git. [RESULTS.json](RESULTS.json) is the exact completed run file, with every diary, revision log, thesis change, final status and timing. [wall-times.csv](wall-times.csv) records every job. No model output was edited.

Elapsed 508.355689 seconds. Per-day summed job time: Day12 147.080254s, file control 226.601736s, voucher control 132.853008s. The one GPU evaluation used only spare slot1. The combined CPU suite overlapped; these times are descriptive, not a speed comparison. Shared server PID384 remained healthy, adapter-free and on the same command, with slot0 reserved for shadow. No Pi call, tick, restart, configuration edit or outage injection was made during this replay.

The diagnostic is limited to ten draws per existing saved record. It is not an independent human holdout or a guarantee against irrelevant evidence. Claude owns any further rule or experiment. Public world remains paused.
