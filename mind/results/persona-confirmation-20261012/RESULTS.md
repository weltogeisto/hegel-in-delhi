# Education-persona confirmation: blind paired result

**FAIL.** All 52 scheduled texts were scored. Karl and the aggregate controls were evaluated separately under the rule declared before generation. Individual controls are also reported.

| Case | Arm | n | Commitments | Argument | Particular | Voice |
|---|---|---:|---:|---:|---:|---:|
| karl | A | 6 | 2.000000 | 2.000000 | 3.166667 | 2.833333 |
| karl | B | 6 | 2.833333 | 2.166667 | 3.166667 | 3.000000 |
| fare | A | 10 | 3.100000 | 2.600000 | 4.000000 | 2.900000 |
| fare | B | 10 | 3.000000 | 2.700000 | 4.000000 | 2.900000 |
| columns | A | 10 | 2.700000 | 2.900000 | 3.100000 | 2.800000 |
| columns | B | 10 | 2.700000 | 2.900000 | 3.000000 | 3.000000 |
| controls | A | 20 | 2.900000 | 2.750000 | 3.550000 | 2.850000 |
| controls | B | 20 | 2.850000 | 2.800000 | 3.500000 | 2.950000 |

| Predeclared gate | Result |
|---|---|
| Karl: B commitments >= A+0.50 | PASS |
| Karl: B argument >= A | PASS |
| Aggregate fare/columns controls: B commitments >= A | FAIL |
| Aggregate fare/columns controls: B argument >= A | PASS |

Karl commitments changed by +0.833333. Gates use exact rational means, not rounded table values. No pooled Karl/control score or output exclusions were used. The two control genres were explicitly authorised before generation: fare remains a letter, columns an essay. The predeclared control gate applies to their aggregate 20 samples per arm; each case's means remain visible above.

The aggregate control decline is one net rating point across 20 texts per arm: fare loses one point overall and columns is unchanged. Individual paired changes run in both directions. With one rater and existing development situations, the size and cause of the decline remain uncertain; the declared acceptance gate still fails.

## Integrity and scope

Claude committed all 52 scores at `cfc8aec97a694635b5cb59f35cb42bfbfc91c843`, SHA256 `a4dbf8343f9ef91bd256adec8ea129b90f527fd701aa857446db6e3acbe565cf`, against packet `db2e53263b5521dbed453cd05f07d9fe704f21888b42fb7de555e17613c9528b`, before the key was copied. Verification checked raw committed CSV bytes, every id and score range, original packet and generation-file hashes, all key fingerprints/sentence counts and equality to raw model results, all 41 protected source/input files and all 108 sealed output files. Both wrapper and runner exited 0.

All 52 responses were usable nonempty JSON, one call each, no retries or server length stops. All 18 texts above the requested 200-word maximum remain unchanged, including the longest at 451 words. No length resampling, trimming, output exclusions or post-score regeneration. Actual prose completeness was left to the blind rater.

A is exactly the original mind/soul.md at d41480b; B adds only one education paragraph. Both use plain Qwen3.8-27B, normal Engine chat, bounded reasoning of 384 tokens, identical event-only excerpt shelf offers, and no adapter/outcome memory/checker/whole passages. Every paired request was identical after removing B paragraph, with B exposure 26/26 and A 0/26. Prompt counts: Karl A/B 2052/2191, fare 2077/2216, columns 2075/2214, all below 7263.

A/B summed job wall time 490.997511/494.288135 seconds; elapsed 987.840656. No competing evaluation GPU job; CPU suite overlap is disclosed as a timing limitation. Every job cost, score and word count appears in [joined-scores.csv](joined-scores.csv). The shared server stayed up unchanged.

This is one blind rater and repeated samples of three existing development situations. It does not establish general persona fidelity or independent-world reliability. Fresh seeds are distinct from T4c; existing situations and the same rater limit the replication. Claude owns any default-persona adoption and main merge. No default or public-world change is made in this result checkpoint.

The original [scores](claude-scores.csv), [packet](packet.md), [guide](guide.md) and [texts](texts.json) remain unchanged. [key.json](key.json) is released after verified committed scores. [VERIFY-SCORES.json](VERIFY-SCORES.json) records verification, [RESULTS.json](RESULTS.json) gives precise means and gates, and [offered-shelf.json](offered-shelf.json) contains actual offers after unblinding.

Software source was separately validated: 887 tests in 705.296 seconds, OK (19 skipped), all 257 archived tracked files verified against Git and native snapshot. This checkpoint adds only review/results/status files. Public world remains paused; shadow first-step check is due after 18:30 UTC.
