# Outcome-memory validation: 11 October

This is a development result, not a completed Step 4 or permission to deploy.
The live world remains paused and the candidate runtime flags stay off.

## Full suite and isolation

At source checkpoint `e537ed43e86483099a44822daac9556443750986`:

```text
python3 -m unittest discover -s tests
Ran 825 tests in 708.777s
OK (skipped=18)
```

The background validation job exited 0 at 09:04 UTC. It checked that its frozen
working source and protected original inputs had not changed. Cleanup confirmed
that only its owned server was stopped and protected inputs were unchanged.

WSL llama.cpp build b11429 served the existing Qwen3.8-27B UD-Q4_K_M GGUF with
no adapter on loopback port 18184. Three concurrent warm-up requests succeeded
with three 16384-token slots; GPU memory was 19338/24576 MiB. Longer stability
and fresh simulation behaviour remain untested.

## Atomic-premise calibration

All 150 original manually Codex-labelled sentences were scored without changing
their text, labels or evidence. Ten separately flagged ambiguous rows are
excluded from fitting and primary metrics. The remaining original grouped split
contains 98 calibration and 42 reused holdout sentences. The old holdout was
already inspected: these are development metrics, not independent validation.

Temperature: **2.8601313208917407**. Support threshold: **0.20**.
The predeclared rule selects balanced accuracy on calibration rows subject to
at least 80% supported retention overall and on concrete premises. It passed
that safeguard. There was no predeclared false-acceptance cutoff.

| Measure | Calibration | Reused holdout |
|---|---:|---:|
| Supported sentences retained | 53/55 | 24/24 |
| Unsupported sentences accepted | 24/43 | 5/18 |
| Unsupported sentences rejected | 19/43 | 13/18 |
| Supported concrete sentences retained | 4/4 | 1/1 |
| Claim-vote rows | 48 | 20 |
| Claim-vote ECE before scaling | 0.180762 | 0.156698 |
| Claim-vote ECE after scaling | 0.105657 | 0.175422 |
| Claim-vote Brier before scaling | 0.189027 | 0.135005 |
| Claim-vote Brier after scaling | 0.161621 | 0.107286 |
| Claim-vote log loss before scaling | 0.709648 | 0.391287 |
| Claim-vote log loss after scaling | 0.488578 | 0.333316 |
| Whole-pipeline ECE after scaling | 0.102771 | 0.107344 |

Whole-pipeline metrics include extraction misses and sentences classified as
having no factual premises. They should not be confused with the probability
calibration of extracted factual claims. The ambiguous group, scored separately,
kept 3 supported sentences, omitted 5, accepted 1 unsupported sentence and
rejected 1. Its original labels remain unchanged.

The checker still misses unsupported material, and the concrete-positive sample
is very small. Temperature scaling worsened claim ECE in the reused holdout
even though Brier score and log loss improved. These results do not justify
live adoption or a claim that calibration alone solves factual grounding.

## Next diagnostic

Run the already frozen fresh smoke seed `2016829042` for one day in both arms,
using the immutable before/after snapshots and the fitted settings without
retuning them. Run arms sequentially so their wall times do not share GPU load.
Manually audit contradictions, speech promoted to fact, duplicate charges and
JSON, alongside prompt sizes and time per day. Preserve every HTTP call and
verdict. Report failure rather than repairing examples or state to finish a run.

The smoke report and verified Git bundle are still pending, followed by three
fresh seeds for two days per arm. Blind-review packets, keys, source mappings
and judgments are intentionally excluded from these public development notes.

Raw evidence is preserved locally at
`C:\hegel\handover\outcome-memory-20261011\validation-v3`.
