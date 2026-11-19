# T2 — first real shadow step confirmed, 12 October 2026

DONE at the 19:35 UTC check. The Pi is clean on shadow `b78e029ca7aef385afad6156147d52b7a7e170c2`, which actually descends from Claude's adopted `ad1270c` and clock-shift shadow `1d7c123`. Day 12 (13 October) contains one published decision: **05:59–06:29, read at home**, source `mind`, **13.0 seconds, one attempt**, zero quiet/away steps. `python3 -m world status` reports awake, published through 06:29. The world timer is enabled and active; the step's service finished successfully at 19:33:20 UTC, and the later checked tick also exited 0.

## Authorised overnight timing

Claude's [PR instruction 6131154312](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6131154312), mirrored under T2 on main `7d89185`, asks for `HEGEL_CLOCK_SHIFT_MIN=300` because Welt wants the shadow day to run overnight Berlin time. Main adds a rehearsal clock offset; system clocks are unchanged. The Pi was still on `b0115fa`: idle ticks do not pull new code while no decision is due. Under the existing tick lock, Codex fetched and fast-forwarded the shadow checkout to the authorised `1d7c123`, then atomically added that one setting to the existing env file. No restart or forced tick was used. Every other env byte and its 0600 mode stayed unchanged, and a private Pi-local backup plus Git backup ref preserve the earlier state. The next scheduled tick used the new code and setting.

Actual Config reports shift 300 and lead 15. The published `docs/days/index.json` at `b78e029` contains **`clock_shift_min: 300`**, so the page uses the same offset. The first waking timeline point 05:59 falls at 21:29 Berlin under this rehearsal setting; the decision became due 15 minutes earlier. Codex applied the setting after that point, at 19:33 UTC / 21:33 Berlin, and the scheduled tick immediately caught up. Set the offset to 0 or remove it before any public switch, as Claude instructed; no public-world switch is authorised here.

## Previous timing diagnosis is preserved

At 18:34 UTC the unshifted Pi correctly had zero decisions: `new_day` creates a 00:00–05:59 Delhi sleep segment, with lead 15. Read-only evaluation of the actual due predicate was false exactly at 13 October 00:14:00 UTC and true one second later. That diagnosis explained the earlier expectation of steps immediately after midnight. Its original SSH receipt, corrected diagnostic, independent review and the first helper's AttributeError receipt remain sealed outside Git. The new explicit clock-shift task supersedes the unshifted waiting time. No old receipt was edited and no step was invented.

## Code and PC validation

The adopted soul on Pi still has SHA256 `256e8a1c5aedfd8edc7b9147a60a10a3ee387efdd6fba2d0a32b818c2c6d1cee`, exactly the tested T4e B paragraph. All **20 captured Python-runtime/soul files** match the Pi's committed blobs and independently match the same PC Git objects. The captured day and index bytes also independently match Git `b78e029`: 22 file comparisons in total. Pi-to-PC mind health answers. Shared WSL server PID384, its command and three adapter-free slots remain unchanged.

Main `7d89185209a4b79177484ab84588064cf8dea406` was actually merged into the primary branch at frozen source `d619ae4c6a60e3ba35a7d8f841cb80cc244c0c8e`, tree `c97dfb490305748e94e747a0142e09dc983c7311`, with parents `bd1ac0f` and `7d89185`. The focused clock, engine, publish, CLI-status and rehearsal regressions ran **34 tests in 19.765 seconds, OK (6 skipped)**; unittest and wrapper exits 0. All **294** tracked files independently match frozen Git, the archive and the native snapshot after completion. The archive SHA256 is `f1f47b0c4a22dead5af1a4169a8a0f368a0ba535e030715fcbe12940d3591545`; log SHA256 `b5a64f2f00b532c5644759f788c0c6ff8d8f95f5fec17711a862a9316e93b9c2`. This is focused validation of the new clock integration. The earlier 895-test full-suite result remains scoped to adopted-default source `12b4174` before the clock change.

All completed result directories remain unchanged from `bd1ac0f`, including both T4e CSV files and their CRLF bytes. No generation, scoring, key release or packaging was repeated. Training, adapters, original data, ML packages, firewall, power, secrets and spending were unchanged. Public world remains paused. Every Codex-owned 12 October task is now DONE; Claude's T5 and main merge remain Claude's work.

## Evidence

[Detailed checks and sealed receipt manifest](SHADOW-FIRST-STEP-CHECKS-20261012.json) include the actual Pi status/journal/service/timer observations, ancestry, file hashes, independent Git comparisons and PC archive proof. Originals and helpers are preserved under `C:/hegel/handover/codex-tasks-20261012`; the frozen PC snapshot is `/home/ai/hegel-eval/codex-tasks-20261012/clock-shift-d619ae4`. Existing backups, trial archives and bundles remain preserved.
