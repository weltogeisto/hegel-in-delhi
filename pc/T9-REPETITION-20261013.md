# T9: repeated four-word phrases, 13 October 2026

The first full shadow day has 29 of 42 thoughts (69.05%) reusing an eligible four-word phrase from an earlier thought that day. The two saved rehearsal days have 16/33 (48.48%) and 19/40 (47.50%). These are literal phrase counts, not a semantic repetition score or a quality gate. No runtime or prompt change follows.

| Saved day | Marked thoughts | Share |
|---|---:|---:|
| shadow 5b52d7f, Day 12 / 2026-10-13 | 29/42 | 69.05% |
| 8 October final-integration/plain-qwen rehearsal, Day 2 / 2026-10-03 | 16/33 | 48.48% |
| 8 October continuation-v2/focused-next-day rehearsal, Day 3 / 2026-10-04 | 19/40 | 47.50% |

## Method

Use the chronological diary entries; all 115 exactly equal the validated decision thoughts and times. Normalize Unicode NFKC and case, standardize apostrophes, ignore punctuation, and take contiguous four-word sequences. Numerals break a phrase. Exclude phrases made only of the fixed English function-word list in the JSON. Mark a thought once when any eligible phrase appeared in an earlier thought that day; repetition within the same thought does not count. Rank phrases by distinct later thoughts reusing them, with alphabetical ties.

Some short grammatical frames remain eligible because they include a content word (for example, “I will not let”). Overlapping four-word windows are retained. This broad mechanical measure therefore does not say that 69% of the thoughts repeat the same idea. It does not measure the separate sambar/sun/kilometre theme counts.

Every thought, its mark, all matching phrases and earlier timestamps, and every repeated phrase are in [the complete audit](T9-REPETITION-20261013.json). The stdlib [auditor](thought_repetition.py) changes no source record. Input identities and hashes are in [the frozen day manifest](T8-OWL-THESIS-PROTOCOL-20261013.json).

## shadow 5b52d7f, Day 12 / 2026-10-13

| Phrase | Distinct thoughts | Later reuses |
|---|---:|---:|
| return to the bungalow | 6 | 5 |
| and the air is | 5 | 4 |
| and the heat is | 4 | 3 |
| air is thick with | 3 | 2 |
| i must return to | 3 | 2 |
| i shall not let | 3 | 2 |
| i shall take a | 3 | 2 |
| must return to the | 3 | 2 |
| shall not let the | 3 | 2 |
| the air is clear | 3 | 2 |

## 8 October final-integration/plain-qwen rehearsal, Day 2 / 2026-10-03

| Phrase | Distinct thoughts | Later reuses |
|---|---:|---:|
| and a man who | 5 | 4 |
| the day is still | 3 | 2 |
| the file's knot is | 3 | 2 |
| a man who has | 2 | 1 |
| and let the day | 2 | 1 |
| and the file's knot | 2 | 1 |
| before i go home | 2 | 1 |
| day is still cool | 2 | 1 |
| have no reason to | 2 | 1 |
| head wants the window | 2 | 1 |

## 8 October continuation-v2/focused-next-day rehearsal, Day 3 / 2026-10-04

| Phrase | Distinct thoughts | Later reuses |
|---|---:|---:|
| i will not let | 6 | 5 |
| will not let the | 4 | 3 |
| and the dhobi's saturday | 3 | 2 |
| i will not stretch | 3 | 2 |
| i will take the | 3 | 2 |
| vouchers and the dhobi's | 3 | 2 |
| will not stretch the | 3 | 2 |
| and my body has | 2 | 1 |
| and return to the | 2 | 1 |
| and the file's contradiction | 2 | 1 |

## Verification

All 115 source thought/decision pairs and every recorded earlier-thought match were checked. Source files were read without edits. Raw input copies, the pre-generation manifest and independent verification remain outside Git at `C:/hegel/handover/codex-tasks-20261013`. Claude decides whether these counts justify a variant and a blind A/B; none was introduced.
