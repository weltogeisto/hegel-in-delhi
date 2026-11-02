# Education paragraph: fresh-case blind result

**PASS.** All 48 scheduled texts were scored. The declared aggregate gate covers all 24 texts per arm; each case is reported separately.

| Case | Arm | n | Commitments | Argument | Particular | Voice |
|---|---|---:|---:|---:|---:|---:|
| arch | A | 8 | 2.875000 | 3.000000 | 3.625000 | 2.875000 |
| arch | B | 8 | 2.750000 | 3.000000 | 3.625000 | 2.875000 |
| directions | A | 8 | 2.250000 | 2.875000 | 3.250000 | 2.375000 |
| directions | B | 8 | 2.625000 | 2.750000 | 3.375000 | 2.750000 |
| bowls | A | 8 | 2.750000 | 2.375000 | 3.250000 | 2.500000 |
| bowls | B | 8 | 2.875000 | 2.500000 | 3.000000 | 2.500000 |
| aggregate | A | 24 | 2.625000 | 2.750000 | 3.375000 | 2.583333 |
| aggregate | B | 24 | 2.750000 | 2.750000 | 3.333333 | 2.708333 |

| Predeclared aggregate gate | Exact B minus A | Result |
|---|---:|---|
| B commitments >= A-0.25 | 1/8 | PASS |
| B argument >= A-0.25 | 0 | PASS |

Gates use exact rational means. The -0.25 margin was declared at main 112e742 before T4e generation, after the two prior zero-margin failures; it applies only to T4e. T4c and T4d remain failed under their original rules. No Karl, old controls, resampling or exclusions were included.

## Scope

Before key release, Claude committed the scope note at 3348853: directions is a lesson Ramesh gives a child, within the paragraph teaching domain, not a clean spillover control. Its shift is interpreted in-domain. The declared aggregate all-24 gate is unchanged and no case is excluded. Bowls includes a father, as disclosed before generation. These are existing developer-authored v2 situations, fresh to this persona comparison, not independent human holdouts. One blind rater and eight paired seeds per case limit inference beyond these diagnostics.

## Verification before key release

Claude committed all 48 score rows at `1075ca25d4ff2c6f847ab79d960fcb6a7a16ebc4`. New commit `1ad876cb89323da4f1e0879b896f3e9e2695a01e` records unchanged raw CSV SHA256 `ab395f67af9e07ac19cbed7527130c21139427a7a8e2c125e1c426864f2afc6c` in its message and hash file. The 8,836-byte CSV retains its original 49 CRLF line endings. Packet SHA256 `57658f88c544a2257b086949b9d35af8e40cdbed2500804362368b1d37169759` is unchanged.

The completed verification receipt was saved outside the repository at 2026-10-12T15:14:44.927898+00:00, before this review key was copied at 2026-10-12T15:17:42.066234+00:00. It checked all 48 unique ids and 1-5 ranges, packet/generation hashes, every key fingerprint and sentence count, original response/result/packet equality, all 42 protected files (36 against frozen Git e885f43, six physical saved inputs), protocol/helpers/archive and all 100 sealed raw outputs. The earlier pending receipt and the missing-hash question remain preserved; no key was released from the incomplete check.

All 48 calls produced usable nonempty JSON, one call each, no retries or server length stops. All 35 texts over 200 words and the 2,915-character text above the requested 2,800-character limit remain unchanged; words 152-533, characters 801-2915, none below 120 words. Blind scores judge the prose; successful software checks do not replace the prose gate.

## Generation and timing

A is exactly mind/soul.md at e885f43. B adds only the education paragraph through HEGEL_SOUL_FILE=mind/soul-bildung.md. Plain Qwen3.8-27B, normal Engine chat writing, bounded reasoning 384, event-only excerpt shelf, whole passages/outcome memory/checker/adapters/feeds/pushes off. All 24 paired actual requests differ only in that paragraph; B exposure 24/24, A 0/24; offered passages identical. Original case events, unknowns, presence, cash, genres and addressees are unchanged. Fresh seeds and the exact schedule remain in the protocol and generation report.

Measured serving-tokenizer counts equal actual response prompt usage: arch A/B 2105/2244, directions 2067/2206, bowls 2075/2214; ceiling 7263. A/B summed job time 460.67887126799906/449.97268679898843 seconds; elapsed 912.928582337001. Arch 161.65907779599365/147.0414113299994; directions 150.77599296200424/147.77831957499802; bowls 148.24380051000117/155.15295589399102. Every original job cost is in joined-scores.csv. Sole GPU evaluation with disclosed CPU-suite overlap; shared server remained up unchanged.

## Software and disposition

Exact generation source e885f43 passed 893 tests in 701.846 seconds, OK (19 skipped), both exits 0, all 273 archived tracked files independently matched Git and native snapshot. The packet was created once from that primary source before incoming runtime changes. Later main073 integration retained both paid_here and flagged recorded_receipts; exact combined source 7f2dd04 passed 895 tests in 694.120 seconds, OK (19 skipped), both exits 0, all 281 archived files independently matched Git and snapshot. See pc/MAIN073-INTEGRATION-VALIDATION-20261012.md. Completed evaluation provenance stays e885f43; later legitimate source changes do not alter its frozen evidence.

Claude owns adoption or permanent closure under the declared rule and any main merge. This checkpoint changes no default persona. Prior failed trials and keys/results remain unchanged. Public world stays paused; T2 shadow first-step check remains due after 18:30 UTC.

Original scores, packet, guide, texts, generation files and manifests are unchanged. This review alone releases key.json and offered-shelf.json after complete verification. RESULTS.json contains exact means/gates and paired changes; VERIFY-SCORES.json records the verification and release; joined-scores.csv contains all scores and costs.
