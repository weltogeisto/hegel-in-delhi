# Writer runtime validation, 12 October

Frozen runtime candidate: `31e2b531095d870f2bb8f017fa1065021bc9faa5`; tree
`b046bc17e01c8423abf5d5699962f343ac425867`.

Full suite: **869 tests in 704.820 seconds, OK (19 skipped)**. Both the
wrapper exit and final unittest result were checked. The native WSL archive
snapshot's 201 tracked files matched the Git archive byte for byte after
the suite. Archive SHA-256: `4c7796fa37ab46130f1aaba47e013a39d584681c4723f343fab9de32dc73a34b`.
Focused tests before the archive: 60 OK. This is code validation, not the
pending blind factual/argument result.

The initial NTFS extraction returned exit 2 with
`tar: Cannot utime: Operation not permitted`. Its partial extraction was
preserved; the identical archive was extracted to native WSL storage and
ran successfully. No source or test result was changed to obtain a pass.

The 138-job fixed-day trial remains frozen in `writer-trial-v3`; all source
and input hashes were checked after the score-only main merge. No default
record enablement or closed-loop run precedes its blind pass gates.

The accepted negative T4 result is separate from T4b. The whole-passage
candidate is published at `2f2096eae362da0031f848d4fee680fa4bc68bac`, tree
`3520ba71700b6982e87a0563eaa4c0a8b46b3bdf`, branch `codex/shelf-whole-eval`.
It uses an isolated worktree, so its runtime changes do not touch T3.
Focused whole-passage checks: 113 tests OK, 2 skipped, 3.792s. Its own full
suite and 20-letter blind comparison are pending. Preflight A/B: 2,061/2,250
actual server tokens; B contains `Gehorsams gegen die Lehrer`. Both use
only case events for retrieval, retaining unknowns and instructions in the
writer prompt. tmux: `hegel-shelf-suite`, `hegel-shelf-whole`; slot 2 shares
the healthy no-adapter server with T3 slot 1 and leaves slot 0 for the world.

## Isolated whole-passage candidate

T4b source `2f2096eae362da0031f848d4fee680fa4bc68bac`, tree
`3520ba71700b6982e87a0563eaa4c0a8b46b3bdf`, was tested in its own native
WSL archived snapshot. Final result: 874 tests in 704.466 seconds,
OK (19 skipped), wrapper exit 0. All 207 archived files matched the
tested snapshot byte-for-byte after completion. Focused checks were
113 tests OK (2 skipped), 3.792s.

The primary checkout's T3 source freeze remains unchanged. Main 861ebe6
now includes the CLI/status repair 9d1ac38; that protected-code merge is
deferred until the T3 packet has been produced. Its TASKS-only update was
cherry-picked. The 874-test result applies to the frozen isolated source,
not an untested subsequent main merge. Blind literary scoring is pending.
