# Education persona trial, 12 October

T4c follows two closed negative shelf experiments. It tests the single
education paragraph supplied by Claude in main f1043c6. A uses exactly
`mind/soul.md`; B uses `HEGEL_SOUL_FILE=mind/soul-bildung.md`. Preparation
requires their only difference to be that paragraph and verifies it reaches
the actual B writer prompt, including retries, and no A prompt.

The source is isolated in `/home/ai/hegel-eval/soul-bildung-20261012`, branch
`codex/soul-bildung-eval`. Main f1043c6 and the earlier isolated runner have
been merged here. Nothing in the primary T3 checkout is changed. Whole
passages, outcome memory, claim checking, adapters, feeds and pushes are off.
Both arms use plain Qwen, the same normal Engine writing path, shelf
excerpts selected from the events only, and 384 reasoning tokens. No world
step is simulated; original case and rehearsal files are read-only.

Use Karl seeds 2026101220–2026101229, matching the preceding shelf trials.
The spill-over control is the existing v2 `fare` letter to the Directorate
of Estates: reimbursement of an 80-rupee journey on a 60-rupee form. It has
no teaching, children or family and keeps the genre identical. Its events
and unknowns are copied without changes. Use seeds 2026101220–2026101224.
The case's 240 rupees of remaining cash are respected in the situation.
All fifteen pairs are shuffled once with seed 2026101217, and each A/B
pair is adjacent with randomized within-pair order. Thirty outputs are
retained, including failures, empties, internal retries and length errors.
There is no length resampling or editing.

`pc/persona_trial.py prepare` freezes source, both persona files, the two
cases, shelf, schedule and four native-tokenizer preflights. Whole prompts
and retries cap at 7,263 tokens. It also checks that paired shelf offers are
identical. Preparation uses capture/tokenization only, no generation.

Generation is held until T3 has completed successfully, verified its source
and inputs, and produced its 210-text blind packet. The run guard enforces
that boundary. Then use shared slot 2 without stopping or changing the
8082 server; slot 0 remains reserved for the world. Every request, reply,
retry, actual prompt size and job wall time is preserved. The new thirty-
text v2 blind packet contains no persona assignments. Its separate private
key is released only after Claude commits all scores and their SHA256.

Predeclared rule: Karl B commitments at least A + 0.5, with argument no
lower; fare B commitments and argument both no lower than A. No pooling
between cases. Claude owns the default persona change and main merge.

Five new tests cover the paired schedule, the actual production persona
switch, control-case addressee/cash/query isolation, the T3 completion and
packaging guard, and v2 packet privacy. Focused run: 69 tests OK (2 skipped),
3.223 seconds. An earlier invocation incorrectly included the nonexistent
`tests.test_config` module: `ModuleNotFoundError: No module named
'tests.test_config'`, 70 reported tests with one loader error. The corrected
module list passed; no source or test assertion changed to remove a failure.
The archived combined full suite and model-backed result remain pending.
