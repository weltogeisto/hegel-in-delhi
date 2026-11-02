# Education paragraph on fresh controls: 12 October 2026

T4e was specified before generation at main
112e7421c2cb0f5a6ff643f63c81231d1e2dd617 and PR comment 6126059778.
T4c and T4d remain failed under their original rules. Their inputs, outputs,
scores, keys and results are unchanged. Claude independently confirmed T4d's
joined scores and closed it before specifying this experiment.

## Intervention and original cases

A is exactly mind/soul.md. B uses mind/soul-bildung.md through HEGEL_SOUL_FILE;
its only difference is the one education paragraph. Both use plain Qwen3.8-27B,
normal Engine chat writing, 384 bounded reasoning tokens, identical sampling,
and the same event-only excerpt shelf. Whole passages, outcome memory,
the claim checker, adapters, feeds and pushes remain off.

Select the original v2 cases from
pc/out/four-hour-20261008-1941/fresh-evaluation-cases.json. Preserve every event,
unknown, date, time, place, cash field and genre. The child's map is the original
case id directions. All three remain essays; no addressee or situation is
authored. These situations are fresh to this education-persona comparison;
they are existing developer-authored v2 diagnostic situations, not independent
human holdouts. Directions includes a child and instruction, and bowls mentions
a father; these are the controls explicitly selected by Claude.

| Case | Original genre | Seeds, inclusive | Texts per arm |
|---|---|---|---:|
| arch | essay | 2026101290–2026101297 | 8 |
| directions (child's map) | essay | 2026101300–2026101307 | 8 |
| bowls | essay | 2026101310–2026101317 | 8 |

All seeds are outside prior T4c and T4d ranges. There are 24 adjacent pairs,
48 outputs, shuffled with ordering seed 2026101241; randomise A/B order inside
each pair. No Karl, fare or columns outputs. No replacement, resampling,
exclusions or length trimming. Preserve the normal 120–200 word,
below-2800-character request and retain any outputs outside those bounds.

## Newly declared rule

Across the 24 control texts per arm, B commitments must be at least A - 0.25
and B argument must be at least A - 0.25. Both gates must pass. Report arch,
directions and bowls separately as well. The margin was selected after two
zero-margin failures and applies only to this fresh T4e trial; do not apply it
retroactively to T4c or T4d. Do not pool Karl or previous controls with T4e.
Claude owns any adoption/default change or closure; software tests cannot
replace this blind prose gate. A decline beyond the margin closes the paragraph
under Claude's specification, without another invented retry.

## Frozen execution and review

The first preparation (persona-fresh-controls-v1) stopped before generation:
the original directions case uses display name Ramesh, while Engine retrieval
requires cast ID ramesh. That partial directory and error are preserved. The
runner now resolves a unique existing cast name to its ID for internal context,
while retaining the exact case and displayed presence in the writing prompt.
Unknown or ambiguous names fail rather than receiving an invented role. No
production runtime or original case was changed by this tooling repair.

Create persona-fresh-controls-v2 under
C:/hegel/handover/codex-tasks-20261012. Freeze the candidate source, this
protocol, original and selected cases, schedule, shelf and preflight inputs.
Check prompt counts against the whole-prompt 7,263-token ceiling, B-only
paragraph exposure and identical paired shelf offers before generation.
Use shared 8082 slot 2 in a new tmux session; slot 0 stays reserved for shadow.
Never stop or reconfigure the server. Do not overlap another evaluation GPU
job. The CPU suite may overlap and that overlap must be disclosed in timing.

Focused checks: 26 tests OK across the persona and writer-trial test modules,
including six new regressions for fresh scheduling, fixed case selection,
retaining original essay genres, rejecting an altered schedule before any
server call, preserving display names while resolving cast IDs, and rejecting
unknown or ambiguous cast names. Packet coverage also checks T4e's v2 guide
and withheld labels.
Run the full suite in an archive of the exact candidate on native WSL storage,
record final count/OK/skips and exits, and compare every archived file to Git
and the tested snapshot. Source stays frozen through packet creation.

After completion, verify both model exits, every scheduled output, original
case equality, all input/source/helper/archive hashes, cleanup and unchanged
shared server. Review all actual requests and retries for paragraph exposure,
exact paired differences, identical offers, prompt sizes, usable JSON, cuts,
empties, retries, retained lengths and every job/case/arm wall time. Preserve
all failures and original outputs.

Then package once from the frozen primary candidate:

    HEGEL_ENV=/dev/null python3 pc/persona_trial.py packet --task T4e --out /mnt/c/hegel/handover/codex-tasks-20261012/persona-fresh-controls-v2 --review persona-fresh-controls-20261012 --private-key /mnt/c/hegel/handover/welt-only/persona-fresh-controls-20261012-key.json

Publish the 48-text v2 blind packet, integrity/generation/cost reports and final
suite result. Assignments, actual shelf offers and the new key stay outside Git
and bundles until Claude commits every score and SHA256. Verify those exact
committed bytes, all ids/ranges, original packet/text fingerprints, raw output
equality and frozen seals before releasing only this review's key. No training,
public-world deployment, power/firewall/secret changes or default changes here.
