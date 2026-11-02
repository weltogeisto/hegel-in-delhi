# Adopted education paragraph: combined PC validation — 12 October 2026

DONE. The combined adopted-default source `12b4174383f397bc7bd13d7b70f4aa4f4311c8c9` passed **895 tests in 697.612 seconds, OK (19 skipped)**. Both unittest and wrapper exits were zero. This result covers the adopted default; the earlier 895-test result on `7f2dd04` covers the pre-adoption default.

Claude adopted the education paragraph on main `bc66c459b57b00e211e8abb19e40da7dffb2595c` and shadow `ad1270c13a9f7ced413f9f91cf02417b2019ab87`, confirmed in PR comment [6127367758](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6127367758). The combined source has actual parents published results `c2bc5cf66dd472b5e247d8ebf0c638b38c4bf277` and that main commit, with tree `eb93a4a7e1b0a6fd1ba03e2d0ff5122e6c62d54c`.

`mind/soul.md` is byte-identical to the tested T4e B file `e885f435238482a696fa7dcdd57f84753179de04:mind/soul-bildung.md`, and to main and shadow's adopted file. SHA256: `256e8a1c5aedfd8edc7b9147a60a10a3ee387efdd6fba2d0a32b818c2c6d1cee`. World code, tests and trial tooling are unchanged from the prior published checkpoint. The merge changes only the soul, scoreboard, tasks and status. The TASKS conflict was resolved by retaining both Codex's detailed evidence and Claude's adopted heading/result/scope note; the original conflict and integration receipt remain in the outside handover directory.

The suite ran on a native frozen snapshot with `HEGEL_ENV=/dev/null`, using `python3 -m unittest discover -s tests`. After completion, an independent verifier read the final count, OK/skips and both exit files, checked the log hash, and compared **every one of 291 tracked archive files** with both Git `12b4174` and the saved native snapshot. No mismatches. It also checked the archive and immutable launch/runner hashes. File-by-file SHA256 values and full provenance are in [the independent checks](MAIN-BC66-ADOPTION-CHECKS-20261012.json).

All 15 published T4e review files still match `c2bc5cf` byte for byte, including both CSV files' CRLF bytes. All completed result directories are unchanged. T4e remains PASS under its original aggregate margin gate; T4c/T4d remain FAIL under their declared gates. No generation, packet, score verification receipt or key release was repeated. Software validation does not replace those prose judgments.

Raw evidence is preserved under `C:/hegel/handover/codex-tasks-20261012`:

- `main-bc66-adoption-suite-launch.json`, `main-bc66-adoption-suite-job.log/.exit`, `main-bc66-adoption-suite-review.json` and `main-bc66-adoption-suite-independent-review.json`.
- Snapshot: `/home/ai/hegel-eval/codex-tasks-20261012/suite-12b4174`.
- Archive `candidate-12b4174.tar`: SHA256 `be04aa23b02abe5c7505d77cf833c4fbe5b37db230be6bfb6c203a4f0d522197`.
- Suite log: SHA256 `9cdb5966071741f2887ef275f95d5549542ff6e5e94ee8ce610b076649b86e94`.
- Launch helper: SHA256 `9d3dcfa448682bced1aed7a23a7ed3887c041094bf3a7f65b9c35ee0baa7a4f2`; runner: `f3748ffd030f2fdf42a8ffcd0c1e4774a5cce4432e9a3886a8d5b396221bde58`.

Expected fixture messages for `127.0.0.1:9` and a ResourceWarning for an unclosed socket remain in the log; the final result is OK. All suite jobs exited. The shared server stayed untouched: PID 384, command SHA256 `1944b782a1c3557851d1c3639e04e43072e6c2a6e8eff6e96978f96d6e48d6b0`, health OK, no adapters, three 16k slots. No GPU evaluation ran; slot 0 stays reserved for shadow.

T2 remains RUNNING. After 12 October 18:30 UTC (20:30 Berlin), confirm actual Pi steps and commit `ad1270c` or a later explicitly authorised descendant. Remote shadow adoption alone does not confirm Pi uptake. Public world remains paused; the reboot proposal remains unapplied. No firewall, power, secrets, packages, adapter or training changes.
