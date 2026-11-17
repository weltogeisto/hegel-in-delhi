# Education persona confirmation: 12 October 2026

T4c failed its declared control gate. Its outputs, scores and key are preserved.
This is T4d, a separately declared confirmation from main ca9bdd8, clarified at
a22f693 and PR comment 6122520471 before generation.

## Intervention and cases

A is exactly mind/soul.md; B uses mind/soul-bildung.md through HEGEL_SOUL_FILE.
The sole persona difference must remain the one education paragraph. Both use
plain Qwen3.8-27B, normal Engine chat writing, bounded 384 reasoning, the same
excerpt shelf with an event-only query, and identical sampling. Whole passages,
outcome memory, the claim checker, adapters, feeds and pushes remain off.

Use the existing v2 cases from
pc/out/four-hour-20261008-1941/fresh-evaluation-cases.json without rewriting
their events, unknowns, cash or genre. Karl and fare remain letters.
Claude explicitly selected columns as the second control, retaining its essay
genre. No new situation or addressee is authored.

| Case | Kind | Seeds, inclusive | Texts per arm |
|---|---|---|---:|
| karl | letter | 2026101260–2026101265 | 6 |
| fare | letter | 2026101270–2026101279 | 10 |
| columns | essay | 2026101280–2026101289 | 10 |

All seeds are new and outside T4c's 2026101220–29. Pair the same case and seed
across A/B; shuffle the 26 pairs and randomise their internal order with fixed
ordering seed 2026101231. There are 52 scheduled outputs. No length resampling,
selected replacement or exclusions. The normal writing request retains the
120–200 word, below-2800-character bound; over-length results remain included.

## Declared rule

Karl: B commitments must be at least A + 0.50, and B argument no lower.
Controls: across the 20 fare/columns texts per arm, B commitments and argument
must each be no lower. Report each control separately as well; no pooling
Karl with controls. The whole trial passes only when every declared gate passes.
This is one blind rater and repeated samples on existing development situations,
not a test of independent fresh worlds.

## Freeze and verification

Prepare a new create-once output directory persona-confirmation-v1 under
C:/hegel/handover/codex-tasks-20261012. Freeze source, source cases, selected
cases, jobs, shelf and preflight hashes. Check actual paired shelf equality and
education-paragraph exposure, full prompt tokens under 7,263, then start in a
new tmux session on shared 8082 slot 2. Slot 0 stays available to shadow;
never stop or reconfigure the shared server. Run the full suite from an archive
of the exact candidate on native WSL storage; record its final exit/count/skips
and verify every archived tracked file unchanged.

Focused tests currently pass: 20 tests in 0.024 seconds, no skips. Five new
regression tests cover fresh pairing, required control selection, case kinds,
rejection of altered schedules before contacting the server, and keeping the
essay control an essay. The blind-packet test also covers T4d's v2 guide and
withholding assignments. Full-suite and model-backed evidence remain pending.

Keep every output, request/retry, error, timing and prompt size. Verify both
exits, all 52 outputs, source/input hashes, paragraph exposure in every request,
paired offers, JSON usability, cuts, empties, retries and unchanged server.
Create one 52-text v2 blind packet only after completion. The new private key
must stay outside the repo and bundle, under welt-only. Claude commits all
scores and SHA256 first; then verify ids, ranges, hashes, fingerprints and raw
output equality before releasing only this review's key. Claude owns any
default-persona change and main merge. No training or public-world deployment.
