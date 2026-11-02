# T6: main merged into shadow before Day 13 wakes

DONE at 17:22 UTC / 19:22 Berlin on 13 October 2026. Pi shadow is `5a02a128bc77e7d2e9602c4af4722cb9ee1700b2`, a real merge of previous shadow `5b52d7f` and main `61accbd`. It contains meal fix `f933bd6` and page redesign `6c4e009`. The actual remote shadow ref matches the clean Pi commit.

The normal 17:22 UTC tick completed successfully (exit 0); the timer remains active. Day 13 / 2026-10-14 is asleep with zero decisions and `state.until=05:56`. Neither “Ramesh puts a plate together” nor “Ramesh brings tea” has appeared because the waking day has not started. No request to eat has occurred, and the afternoon tea window has not arrived. This supplies T6's specified explanation when neither entry came up; no tick or meal was forced.

The next decision becomes due just after 19:11 UTC / 21:11 Berlin (05:41 rehearsal Delhi, the 15-minute lead before 05:56). This is eligibility, not a model completion deadline. The merge was completed about 1h49 before that boundary.

The existing nonblocking tick lock guarded the merge and ordinary push. Backup ref `codex/shadow-before-main-20261013-1723` preserves the prior Pi commit. All captured day/index/state JSON hashes are identical before and after the merge. Shift 300, lead 15, soul, configuration, schedule and shared server were left intact. The public world remains paused.

Independent PC Git fetch verifies both actual parents, f933bd6 ancestry, the day/index hashes captured on Pi, and equality of `world/world.py`, `engine.py`, `publish.py`, `config.py`, soul and page HTML to main 61accbd. The Pi runs main's runtime, including its publication retry. No new live outage has tested that retry's recovery promise.

## PC integration and verification

Main 61accbd was also genuinely merged into the Codex branch at `44d2364`, parents `9c507d6` and `61accbd`. A conflict at the household meal execution was resolved by preserving main's between-meal plate behavior, the existing consumed receipts and the existing purchase identity/reconciliation loop. An actually consumed plate receives the same household consumption receipt as a served meal. The Pi merge uses main's exact runtime and does not deploy Codex-only features.

Focused tests on exact combined source 44d2364: **70 tests in 9.248 seconds, OK (1 skipped)**; wrapper and unittest exits 0. The six modules cover meal feedback/needs, purchase memory, duplicate settlement, pending pushes and outcome repairs. The preserved expected temporary-remote failure lines belong to the pending-push fixture. Older full-suite results do not cover this new combined source. A full combined suite will run once on a frozen snapshot alongside the newly authorized T8 count.

The first diagnostic helper assumed a PC-only optional Config field existed on Pi and stopped before any operation. Its second version contained a syntax error and did not execute. Both original helpers and failure receipts remain preserved; the corrected version passed local syntax checks before the one successful guarded merge. No product or evidence was changed to hide them.

[Detailed checks and raw receipt manifest](T6-SHADOW-MAIN-CHECKS-20261013.json). Originals remain outside Git under `C:/hegel/handover/codex-tasks-20261013`; the earlier watch and DNS failure/recovery evidence remain unchanged.
