# T10 quiet-step rule, 14 October 2026

Claude's rule at main `4016d8d` and PR comment 6171110370 unblocks the auditor change. T10 stays OPEN until the first complete day with at least 30 non-null decision thoughts. Day 13 is **not measurable**: 35 decisions, four thoughts, and 31 null thoughts, all source `away`. No share, top ten or 55% decision is reported. Day 13 was not rerun, transformed or regenerated; its exact 44,243 raw bytes remain SHA256 `39f649efc628a9169a2e26fdecd12a7320777320a3eee972b267a99c1cb911cd`.

The auditor now validates diary entries against non-null decision thoughts, explicitly checks the remaining null thoughts, and reports decision/null counts by mind.source and whether the 30-thought floor is met. Below that floor it performs no phrase analysis and returns no share. Normalization, stopwords, marking and ranking are unchanged. The denominator is the non-null thoughts alone; null steps remain in the raw input and are disclosed separately.

New auditor SHA256: `bb77f3afc99ea2459e111e78bb8ac8f23adef68a74c79795d615c1ba5ba0439a`. Prior auditor SHA256: `d4e312af2421b0db0c2aec9969f2ed65f24cc3d3856152bdce127e6960591126`.

Six focused tests pass in 0.002s (process exit 0), covering null steps, the 29/30-thought boundary, an empty record and diary/missing-field failures. One authorized audit of the original three T9 records reproduces every original result field exactly: 29/42 (69.05%), 16/33 (48.48%), 19/40 (47.50%), including all 115 marks, match evidence and all rankings. All 361 frozen source files matched Git/archive/native snapshot after completion. No model call or full-suite rerun.

Complete regression output, original stdout/stderr, manifest and independent checks are in `mind/results/thought-repetition-quiet-rule-20261014/`. The earlier Day 13 assertion failure and its exact raw input remain unchanged in their original report and directory. This result prepares the next measurable day; it does not establish improvement or authorize a variant. The natural Day 13 owl separately timed out; see `DAY13-OWL-TIMEOUT-20261014.md/json`.
