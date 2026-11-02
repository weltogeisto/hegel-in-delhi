# Main073 integration validation - 12 October 2026

**895 tests in 694.120 seconds, OK (19 skipped).** Unittest and wrapper exits are both 0. All 281 archived tracked files independently match both frozen Git and the native snapshot after the suite. Focused combined checks passed: 37 tests in 0.053 seconds, exit 0 (11 voice and 26 persona/writer).

## Exact source and integration

The suite tests combined source `7f2dd04f5dfd090e5688eceae242f0229d737551`, tree `bad704878b68008ed5945a1c4a15a7756e72d41e`, with actual parents T4e packet `323b7c94a21a5aab56a25aba76d1a00e9231d4c1` and main `073053e369173a1cf2a60f5c47484df8c46281d3`. Main was merged only after the T4e packet had been created once from frozen primary e885f43 and published. No completed evaluation inputs or outputs were changed.

Main adds sellers' already settled same-place payments (`paid_here`), two voice tests, the stub prompt-size cap 3650, and page typography/panel changes. Engine/voices conflicts retained both Claude's `paid_here` and the existing flagged `recorded_receipts`. The respective function bodies were independently compared byte-for-byte with main073 and packet323 source. Voice facts include paid_here always and typed receipts when the existing flag is enabled. Records, checker and whole-passage defaults remain off.

Subsequent real merges of main3348853 and main1ad876c add only the unchanged score CSV, a pre-key TASKS scope note and score hash file. There are no subsequent runtime/test changes in this result checkpoint. The 895-test suite therefore covers the published runtime; T4e generation provenance remains the earlier exact e885f43 (893 tests, 701.846 seconds, OK with 19 skipped).

## Frozen suite evidence

- Native snapshot: `/home/ai/hegel-eval/codex-tasks-20261012/suite-7f2dd04`.
- Archive `candidate-7f2dd04.tar`, SHA256 `450a9c70a5021e280ad7dd7d72aedbd6b746bdb0bb7290c861fa28add15e9138`.
- Log `main073-integrated-suite-job.log`, SHA256 `03bded03c81ef21a27ca116eec33bf8810126c52040387dec18227eda3c042dc`.
- Launch helper SHA256 `44cebda4143ac88844e68a0671a4ba1ef3b587f3d9758baaf32669e9e67ba425`; runner SHA256 `1d963898551e8603e43c5d1af4c1c77425157a9517117cdcfa6aed1471a27476`.
- All 281 tracked archive files matched Git and snapshot at launch and independently again after completion. Final count, OK/skips, helper/archive/log hashes and both exits were read directly; no pass was inferred from progress dots.

Raw Windows evidence is preserved in `C:/hegel/handover/codex-tasks-20261012`: launch receipt, log/exit, wrapper review and independent review. A copy of the independent checks is [MAIN073-INTEGRATION-CHECKS-20261012.json](MAIN073-INTEGRATION-CHECKS-20261012.json).

The log retains expected 127.0.0.1:9 fixture messages, simulated resume lines and an unclosed-socket ResourceWarning; final result is OK. Two earlier focused-test invocation errors (missing tests PYTHONPATH and shell exit-variable quoting) were corrected without code changes, with original receipts/logs retained. Final native Python wrapper records all 37 focused tests and exit 0.

Shared server PID 384 remains up, plain Qwen, no adapter, three 16k slots, unchanged command hash `1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0`. Slot 0 remains reserved for shadow. No evaluation GPU job remains. Public world stays paused; no training, adapters, original-data, ML-package, firewall, power or secret changes. Shadow first-step confirmation remains due after 18:30 UTC (20:30 Berlin).
