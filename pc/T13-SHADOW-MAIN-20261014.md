# T13: main merged into Pi shadow, fan club excluded

T13 is DONE at shadow `39148aeb991480186783129076877473e24a143e`, tree `e011cf72bca66a3db766753c3a7f3246b456be1a`. Its real parents are previous shadow `14c7e9ea416c937295a06c0ade133ba396428fed` and main `f82ffed526495f9c2ef7853d8fba8d2ae4c35b9a`; T12 `c61daf3616285f3e2895b060a877717588994f2c` is an ancestor. This was a genuine merge under the existing tick lock, with a backup ref, followed by an ordinary shadow push.

Welt's later handover expressly forbids fan-club material on the Pi. The merged working tree therefore preserves its previous `docs/index.html` byte for byte and omits `supabase/fanclub.sql`, `tests/test_fanclub.py` and `world/data/visitors.json`. Engine, CLI and their tests equal main f82. Main ancestry is retained; the fan-club feature is not deployed.

All **185 raw Git files and the complete tree** matched the Pi working tree before the remote push. All **22 CSV files retained their original bytes**, and every captured day/state JSON file remained unchanged through the merge. Configuration remains shadow, shift 300, lead 15, owl at 01:30. No forced tick, owl, clock or state edit, public switch, secret change or server intervention was used for T13.

The first natural tick after release finished at **16:56:05 UTC**. The one 16:58:10 UTC read-only capture records a later completed tick at 16:58:05: exit 0, inactive service, enabled/active timer, clean stable HEAD. An independent origin fetch confirms the actual remote, real parents, T12 ancestry, all eight captured file lengths/blob IDs/SHA256 values, source equality and fan exclusions. The helper captures hashes, not raw file bytes. No refusal-loop line was printed.

No live quiet stretch has occurred yet: Day 14 / 2026-10-15 is asleep at home, zero decisions, until 05:57 rehearsal. These natural no-op successes complete T13's declared exit-0 condition; they do not establish live fallback behavior or new model generation.

## PC validation and preserved failures

The genuine main-f82 PC merge retains Codex's existing extensions. Four unchanged `tests.test_world.MindlessDayTest` cases pass in **103.088 seconds**, unittest and wrapper exit 0. All **372 frozen source/archive/native files** match after completion. Archive SHA256: `4ae1a8ad105723be4b0a030e1048c15fb87c1b81701640c05109a1fcb148c401`. Original run and logs are under `mind/results/t13-main-integration-20261014`; no model call or full-suite rerun was made.

Three failures remain preserved outside Git and are named with receipts in the JSON report. The initial preparation incorrectly required the entire combined engine to equal main, despite intentional existing Codex extensions; it failed before tests or Pi mutation. A 45-second test wrapper timed out and did not retain its partial stdout/stderr. The unchanged closed-port health check takes about three seconds per step; one longer run with durable logs and a 600-second deadline passed, without changing source or tests. The first Pi attempt used an unsuitable Git removal form for newly staged fan files; it aborted this uncommitted merge under the tick lock, before any commit or push. The corrected attempt restored all four excluded paths from the original shadow tree. No original evidence was overwritten.

The earlier 905-test full-suite result still covers only `f51696b`, not this source. Completed T8/T9 evaluations and the quiet-auditor regression were not repeated.

Full hashes, original parents, raw-file verification, day/state seals, failed-attempt provenance and natural-tick capture: `pc/T13-SHADOW-MAIN-20261014.json`.
