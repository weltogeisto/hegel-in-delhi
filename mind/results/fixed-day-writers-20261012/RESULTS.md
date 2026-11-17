# Fixed-day compact evidence: blind result

**FAIL.** Compact evidence reduced statement promotions overall but slightly increased contradictions per sentence and lowered owl argument. Records remain off by default; the conditional closed-loop run is held.

A is the old writer input; B is typed records with compact evidence, retaining the labelled interpretation block. The runtime LLM claim check was off in both. All 210 texts and all scheduled outputs are included.

| Overall measure | A | B | Gate |
|---|---:|---:|---|
| Sentences | 2204 | 2226 | denominator |
| Contradictions | 35 (1.588022/100) | 36 (1.617251/100) | FAIL: B must be no higher |
| Statement promotions | 68 (3.085299/100) | 62 (2.785265/100) | PASS: B must be lower |
| Uncertain sentences | 37 (1.678766/100) | 39 (1.752022/100) | reported, not errors |
| Owl argument, mean of 36 diary/revision scores per arm | 2.277778 | 1.972222 | FAIL: B must be no lower |
| Summed job seconds | 2391.314778 | 2446.352026 | PASS: ratio 1.023015 <= 1.2 |

## Per saved day

Counts are followed by rates per 100 sentences. Owl argument uses six diary/revision texts per arm per day. The aggregate rate is computed from total counts and total sentences, not the average of day rates.

| Day | Arm | Texts | Sentences | Contradictions (per 100) | Promotions (per 100) | Uncertain | Owl argument |
|---|---|---:|---:|---:|---:|---:|---:|
| D01 | A | 12 | 186 | 1 (0.5376) | 3 (1.6129) | 6 | 2.3333 |
| D01 | B | 12 | 166 | 7 (4.2169) | 2 (1.2048) | 6 | 2.0000 |
| D02 | A | 9 | 124 | 13 (10.4839) | 6 (4.8387) | 0 | 2.1667 |
| D02 | B | 9 | 118 | 3 (2.5424) | 2 (1.6949) | 0 | 2.1667 |
| D03 | A | 21 | 466 | 10 (2.1459) | 16 (3.4335) | 2 | 2.5000 |
| D03 | B | 21 | 459 | 13 (2.8322) | 14 (3.0501) | 4 | 1.8333 |
| D04 | A | 24 | 574 | 3 (0.5226) | 12 (2.0906) | 4 | 2.5000 |
| D04 | B | 24 | 646 | 4 (0.6192) | 13 (2.0124) | 6 | 1.8333 |
| D05 | A | 24 | 521 | 7 (1.3436) | 23 (4.4146) | 21 | 2.1667 |
| D05 | B | 24 | 525 | 2 (0.3810) | 24 (4.5714) | 21 | 2.0000 |
| D06 | A | 15 | 333 | 1 (0.3003) | 8 (2.4024) | 4 | 2.0000 |
| D06 | B | 15 | 312 | 7 (2.2436) | 7 (2.2436) | 2 | 2.0000 |

## Writer fields

| Field | Arm | Sentences | Contradictions (per 100) | Promotions (per 100) | Argument |
|---|---|---:|---:|---:|---:|
| depesche | A | 418 | 3 (0.7177) | 14 (3.3493) | not scored |
| depesche | B | 383 | 1 (0.2611) | 4 (1.0444) | not scored |
| diary | A | 341 | 13 (3.8123) | 20 (5.8651) | 2.4444 |
| diary | B | 311 | 12 (3.8585) | 12 (3.8585) | 2.0556 |
| revision_log | A | 43 | 1 (2.3256) | 3 (6.9767) | 2.1111 |
| revision_log | B | 35 | 0 (0.0000) | 0 (0.0000) | 1.8889 |
| text | A | 1402 | 18 (1.2839) | 31 (2.2111) | not scored |
| text | B | 1497 | 23 (1.5364) | 46 (3.0728) | not scored |

Depesche promotions fell 14 to 4; writings rose 31 to 46. Diary argument fell 2.4444 to 2.0556, revision argument 2.1111 to 1.8889. These field differences are diagnostic; no field or output was dropped to change the declared overall verdict.

## Scoring and provenance

Claude committed the three blind CSVs at `8f42672fd1cb03cfae53a337754d367ff66cd743` before the key was released. The full SHA256 values are in `VERIFY-SCORES.json`. Verification covered all 210 ids, every sentence count, all 268 sentence-error rows, exact agreement with per-text totals, all 72 argument scores, original packet hashes, every private-key fingerprint and equality to the raw model output. All 291 sealed raw output files, 32 source files from frozen commit `31e2b531095d870f2bb8f017fa1065021bc9faa5`, and 29 physical saved inputs were verified unchanged.

The key is now in [key.json](key.json). [RESULTS.json](RESULTS.json) contains full precision, sources and gates; [joined-text-scores.csv](joined-text-scores.csv) joins each judgment to its saved day, seed and arm; [joined-job-costs.csv](joined-job-costs.csv) contains all 138 job times and call counts. Original score files and packet bytes are unchanged.

One blind rater read every owl diary, revision log and Depesche in full. In the 102 writings, sentences without concrete-claim signals were mechanically screened blind and counted as zero errors. Writing counts are therefore lower bounds; no claim of exhaustive manual writing audit or independent replication is made. The six fixed histories are development material. Missing evidence is uncertainty, not contradiction.

D06's saved records themselves contain two payments for the corn-and-water episode, at 06:27 and 06:42. The rater treated texts that accept Sunil's 'not paid' statement as contradictions. This inherited defect is preserved in both arms and disclosed; neither records nor judgments were changed after unblinding.

## Generation and timing

138/138 jobs; 210/210 nonempty texts; 4,430 sentences. All 149 responses parsed as JSON; 11 Engine contract retries remain included. No server length stops or unusable fields. Actual prompts ranged from 2,406 to 7,262 tokens, ceiling 7,263. Elapsed run time 4,933.865226 seconds. A/B jobs ran in adjacent randomized pairs with caching disabled. T4/T4b shared another GPU slot during part of the run, so timing is affected by concurrent load. The shared adapter-free server was left running.

The integrated source was separately validated: 882 tests in 701.651 seconds, OK (19 skipped), all 224 archived files verified. That suite is software evidence, not a factual or literary pass. This checkpoint changes review/report files only.
