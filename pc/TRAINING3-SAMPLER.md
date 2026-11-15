# Training 3 candidate sampler

The sampler records 500 situations: the **71 shadow situations** of the 109 with
an exact parent state that pass the split rule, followed by **429 new rehearsal
situations dated 10 November 2026 or later** that pass it too. The provenance
rule was approved before sampling in
[Claude's answer](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6704597355).

**The split rule, `training3-split-1`** (`tools/decision_split.py`, 7 November,
before any candidate). A situation is held-related, and never trains, when its
prompt's user message shares a run of 12 words with anything recorded on T39's
held shadow days 12 and 27 (entries and the owl's texts; the 8,946 frozen runs in
`pc/training3-held-runs.json`). His memory quotes earlier days word for word, so
38 of the 109 shadow prompts carry Day 12 or 27 (all of Days 13, 14 and 28, 15
of Day 35 and one of Day 37; `pc/training3-held-related-shadow-ids.json`). They
are not sampled. A held-related rehearsal situation is advanced with one recorded
seed-1831 call under `held-related/` and does not count toward the 429. The
labeller refuses any held-related row. T9's rehearsal days cannot be recalled by
shadow or new rehearsals: they were separate runs. Any later evaluation of the
Training 3 adapter must likewise leave out the days this roster trains on.

The ordered shadow IDs are in `pc/training3-shadow-ids.json`. Their SHA256 is
`a7f6c59b8038d4fbf38f7e57aea6ddb6e5458f6db256ec82b1c7f872b407e264`.
They refer to shadow commit `45479027d4cba09f60710c02468197801f0a5722`.
Nine of the original 118 situations have no exact before-state and are excluded
by the fixed provenance rule; Day 38's later decision is outside the freeze.
Days 12 and 27 are never sampled as training situations. Historical prompts are
reconstructed from exact parent state and recorded observations, as in T39;
they are not represented as archived HTTP requests.

## CPU preparation

Run `python -m tools.decision_situations --repo NATIVE_REPO --shadow EXACT_SHA
--soul SOUL_FILE --out NEW_FREEZE`. The output retains native parent/child
identities, input objects, the ordered IDs and a hashed manifest. This command
makes no model request. A changed roster fails before sampling.

`tools.decision_sampler.Sampler` records four independent candidates, in seed
order 1831, 2718, 3141, 4271. All use the live decision schema, temperature 0.7,
700 output tokens, no thinking and plain Qwen. Each call to `World.check` gets a
fresh copy of the situation's exact state and context. Accepted flags, errors,
warnings, raw responses and complete response receipts remain in the output.
No model critic or preference score selects a label.

## Runtime integration

`tools.decision_sampling.run_dataset(freeze, sampler_root, cfg, post, output)`
is the complete dataset entry point. The reviewed job controller supplies
`post(request_id, payload) -> (response, durable_receipt)`; there is no direct
HTTP fallback. Use T39's serial slot-1 transport, original plain-Qwen identity,
fresh natural-step latency guard and dated cutoff. The controller must pin the
source, shadow manifest, simulation inputs, 109-ID list and output paths before
the first request. Sampling waits for T39 to finish.

The same guarded transport handles rehearsal plans, voices, writings and owl
calls. Those are saved support calls, **not preference rows**. Exact completed
keys replay locally; an unknown response stops without resend. This API does
not start a server, pause Hegel, change a timer or create an operating date.

The rehearsal configuration must use its own docs/state directories, copied
from frozen published days through the usual rehearsal setup, with push and
feeds disabled. It uses the same five-minute advance loop as `--distill`.
External lookups return an explicit unavailable note. The first accepted
candidate in seed order advances each new rehearsal; if all four are refused,
the ordinary refusal loop reuses the first saved reply without adding
candidates. Every saved rehearsal-day version is retained.

Only an exactly complete roster exports `CANDIDATES.jsonl`. Its rows include
the day's earlier thoughts, four checked candidates, date, decision schema and
input hashes. Then run Claude's unchanged `tools/decision_pairs.py`; fewer
than 200 pairs blocks training. An interruption preserves partial work and
requires the runtime's receipt reconciliation before continuation.

## Validation

CPU tests cover candidate isolation, four-seed ordering, replay and unknown
responses, fixed provenance exclusions, exact context/roster hashes, complete
exports, preserved rehearsal versions and an actual Engine loop with a fake
guarded transport. No new model data, GPU training or deployment is part of
this PR.
