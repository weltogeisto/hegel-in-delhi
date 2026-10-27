# T29 answer keys

The original keys are now released under the explicit owner relay [6437520814](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6437520814). The original human message is in Claude’s chat and is not locally captured.

- **Plain Qwen:** trial-5ff67fd9 — [original key](hegeltest-trial-5ff67fd9-restyle-key.json).
- **Fresh adapter:** trial-79588d5f — [original key](hegeltest-trial-79588d5f-restyle-key.json).
- [Original label mapping](arm-mapping.json), [authorization](KEY-RELEASE-AUTHORIZATION.json), [hash and consistency checks](KEY-RELEASE-CHECKS.json).

Each letter identifies the real passage in the existing option order. Both JSON keys are byte-identical to their sealed originals. The table is a transcription of those keys; no judgment has been scored here.

| Question | Passage ID | Plain Qwen: real | Adapter: real |
|---:|---|:---:|:---:|
| 1 | haldane-1:573 | E | A |
| 2 | wallace-mind:53 | B | C |
| 3 | wallace-logic:428 | D | C |
| 4 | dyde-right:313 | A | C |
| 5 | bosanquet-art:2 | C | E |
| 6 | baillie-1:156 | D | C |
| 7 | haldane-2:455 | B | B |
| 8 | haldane-3:319 | A | E |
| 9 | baillie-2:259 | D | B |
| 10 | sibree-history:135 | A | B |
| 11 | haldane-1:624 | D | D |
| 12 | wallace-mind:51 | C | E |
| 13 | wallace-logic:151 | A | D |
| 14 | dyde-right:246 | D | D |
| 15 | bosanquet-art:24 | E | E |
| 16 | baillie-1:16 | B | E |
| 17 | haldane-2:556 | D | E |
| 18 | haldane-3:334 | A | D |
| 19 | baillie-2:248 | E | C |
| 20 | sibree-history:480 | A | C |

Claude’s original blind judgment of the plain sheet remains unchanged (SHA256 59006591db2719f55f0f4228641053f346210f20861215e13d4d486a52bd03b9). He abstained on the second sheet because its real passages repeat the first. The owner relay reports that Welt requested the answers and will not judge the second sheet. Claude will score his existing judgment and publish the step 8 table.

The adapter still misses the existing automatic recitation bar: 12/80 recited versions against a limit of 8/80. This release does not authorize adoption, regeneration, retuning or retraining.
