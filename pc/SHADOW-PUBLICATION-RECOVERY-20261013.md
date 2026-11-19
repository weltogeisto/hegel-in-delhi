# Shadow publication recovered after transient GitHub DNS failure

The 10:59–11:26 rehearsal step completed once on the Pi at 00:14:33 UTC on 13 October, but GitHub DNS lookup failed during the tick's pull and all four built-in push attempts. Service failure was recorded at 00:16:23 UTC. The completed decision and its commit were intact; subsequent no-op ticks returned success without retrying publication.

At 00:26 UTC DNS and a read-only GitHub ref lookup worked again. The Pi was clean on `a9dabd73ec7f15cbb97a8dc4c0f76d13ae06c86d`, exactly one commit ahead of actual remote shadow `f76cd34908f515c9f9562486b300ea6b8a9975af`. That commit changes only `docs/days/2026-10-13.json`.

Under the existing nonblocking tick lock, one guarded, ordinary push published that existing commit between 00:27:26 and 00:27:30 UTC. The guards required the expected clean shadow branch, exact parent and remote ref, unchanged adopted soul, and shift 300. The remote ref then matched `a9dabd7`; the Pi's HEAD and day bytes were unchanged. No extra decision was generated.

## Verified result

- Day 12 / 2026-10-13: 13 real decisions through 11:26 rehearsal time; zero quiet or away steps. Latest step: walk from home to Khan Market, 8.2 seconds, one attempt.
- Actual remote shadow and the Pi agree at `a9dabd7`. The recovered day SHA256 is `d7629265da3581145084f2f693f5a4bf2ce4f22f2ba267a36bf983626381527c` before and after the push.
- An independent PC fetch verified the actual commit parent, clock/adopted/main ancestry, three captured Python runtime files, soul, day and index: six exact raw file/hash matches. Runtime and soul have no changes since authorised clock shadow `1d7c123`.
- Shift 300, lead 15, index shift 300; timer enabled and active. The latest completed service check was successful with exit 0. The shared PC server was healthy with its unchanged PID384 command hash.
- Recovery succeeded in one operational attempt. No source, configuration, schedule, state, system clock, public world or shared server changes were needed. No test suite was rerun.

`python3 -m world status` reports the local timeline as "published to". After a push error, that line and a later no-op service success do not prove GitHub has the step. Compare the actual remote shadow ref with the Pi's committed HEAD. This incident was repaired by publishing the existing commit; no preventive runtime change is part of this result.

## Evidence and integration

The checks JSON contains the original failure lines, DNS/ref diagnosis, guarded push, before/after hashes, and independent Git verification. Every original raw receipt and helper is preserved outside Git under `C:/hegel/handover/codex-tasks-20261012`, sealed by name, length and SHA256 in the checks file. The diagnostic journal's `--since` was parsed in Pi local time while output was rendered in UTC, so its preserved raw receipt contains a longer window; the UTC failure lines above are selected without changing that receipt.

Fetched and read main `8fc5f03`. Its task closure and rehearsal-clock page label are integrated into the PC branch. The TASKS conflict was only the T2 completion heading: Claude's heading was retained together with the branch's detailed completed results. Original conflict and integration output are preserved. All 12 October tasks remain DONE; overnight monitoring continues under comment 6131388922 until the first full day and owl's write-up. Public world remains paused.
