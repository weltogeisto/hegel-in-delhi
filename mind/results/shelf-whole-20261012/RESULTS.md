# Whole passages versus excerpts: FAIL

Scores were committed before key release at `570042a79b4bef1c941efb68fc357628fc138a39`.
The CSV hash, committed packet hash, all twenty ids, all score ranges and
every original text fingerprint were verified before the new key was copied.

| Dimension | A: excerpts | B: whole | B minus A |
|---|---:|---:|---:|
| argument | 2.00 | 2.10 | +0.10 |
| commitments | 1.80 | 1.90 | +0.10 |
| particular | 2.80 | 3.20 | +0.40 |
| voice | 2.40 | 2.40 | +0.00 |

Predeclared rule: B commitments at least A + 0.50, and B argument no lower.
Observed commitments gain +0.10; argument delta +0.10. **FAIL**.

All twenty letters remain in the analysis, including five above the requested
200-word upper bound. There were no server length stops or rejected JSON;
the blind rater nevertheless identified an unfinished scene in one letter.
This qualitative issue is preserved in the original scores and text.

B actually received the complete obedience sentence in all ten prompts.
Both conditions used the same passage ids selected from event-only queries.
The negative result therefore cannot be explained by the earlier missing
sentence or Unknown-list retrieval pollution. It does not identify whether
the remaining problem is German comprehension, retrieval relevance, persona
prior or the writing task. One rater and ten paired letters do not establish
a general result; no default change or further training is inferred.

Generation and timing: 20 nonempty letters, one call each, no retries.
A/B summed job wall time 219.353/233.694 seconds under concurrent T3 load.
Full suite 874 tests OK (19 skipped), 704.466s; 207 archive files verified.
The shared plain Qwen server stays up. Primary T3 source remains frozen.

The released `key.json` and `offered-shelf.json` expose this review only.
Older private review keys remain separate. Whole passages remain off by default.
