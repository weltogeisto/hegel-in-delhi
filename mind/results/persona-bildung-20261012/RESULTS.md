# Education persona: blind paired result

**FAIL.** The Karl and reimbursement-control gates were evaluated separately, using all 30 scheduled texts.

| Case | Arm | n | Commitments | Argument | Particular | Voice |
|---|---|---:|---:|---:|---:|---:|
| karl | A | 10 | 2.00 | 2.30 | 3.40 | 2.90 |
| karl | B | 10 | 3.00 | 2.60 | 3.30 | 2.70 |
| fare | A | 5 | 3.40 | 2.80 | 4.00 | 3.00 |
| fare | B | 5 | 3.00 | 2.80 | 4.00 | 3.00 |

| Predeclared gate | Result |
|---|---|
| Karl: B commitments >= A+0.50 | PASS |
| Karl: B argument >= A | PASS |
| Reimbursement control: B commitments >= A | FAIL |
| Reimbursement control: B argument >= A | PASS |

Karl commitments changed by +1.00. No pooled mean was used to rescue either case. The control's commitments difference comes from two paired seeds (2026101221 and 2026101224): A scored 4 and B 3; the other three pairs scored 3/3. The rater's reasons cite A's use of signs/property and B's more general deference to office. This small control difference does not by itself prove that education content leaked into unrelated letters; it still fails the declared non-regression gate. A is exactly the original main persona, not soul-v2; B differs by only the education paragraph. Normal chat writing, bounded 384 reasoning, identical event-only excerpt shelf offers, plain Qwen and no outcome memory/checker/adapter in both arms.

## Integrity and retained outputs

Claude committed all 30 blind scores at `e6f99570dbf5a90980a93eb50cccbefeca8f5812`, SHA256 `90b6648e9e95da30873cb062d444c071a38be6895e20e38240acccf6d182384f`, before this key was copied. Verification checked raw committed CSV bytes, all ids and 1–5 scores, original packet and generation-file hashes, every private-key fingerprint and equality to the raw model output, all 41 frozen source/input files and all 64 sealed output files. Both wrapper and runner exited 0.

All 30 letters are usable, nonempty JSON outputs, one call each, no retries or server length stops. Fourteen exceeded the requested 200 words; they remain unchanged in the scores and packet. There was no trimming, length resampling, output exclusion or post-score regeneration.

Actual prompts: Karl A/B 2,052/2,191 tokens; fare 2,077/2,216. Every paired request, after removing B's one persona paragraph, was identical, including sampling parameters and seed. B exposed the paragraph in all 15 requests, A in none; paired shelf offers were identical. A/B summed job time 279.968077/281.478719 seconds, elapsed 562.908393. All job times and calls are in [joined-scores.csv](joined-scores.csv).

## Evidence and scope

The original [scores](claude-scores.csv), [packet](packet.md), [guide](guide.md) and [texts](texts.json) are preserved. [key.json](key.json) is released only after score verification. [RESULTS.json](RESULTS.json) contains precise means and gates; [VERIFY-SCORES.json](VERIFY-SCORES.json) records verification. [offered-shelf.json](offered-shelf.json) shows the actual passages after unblinding.

This is one blind rater, one education case and one control, with paired samples from one local model. It does not establish wider persona fidelity. Claude owns any default-persona change and the main merge; no default was changed in this result checkpoint.

Software source was validated separately: 882 tests in 701.651 seconds, OK (19 skipped), all 224 archived files verified. This checkpoint contains review/report files only. The shared server remains running; public world remains paused.
