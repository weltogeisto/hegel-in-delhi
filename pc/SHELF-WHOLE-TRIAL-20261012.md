# Whole-passage shelf trial, 12 October

T4b follows the negative first shelf trial. Its question is whether showing
the passage's complete point changes the letter, rather than whether adding
a work to the index is enough. The Nuremberg passage's obedience sentence
was absent from the earlier excerpt.

The isolated checkout is `codex/shelf-whole-eval` at
`/home/ai/hegel-eval/shelf-whole-20261012`. It merges main 1953bd9 and
Claude's explicit `claude/shelf-whole` commit e7b7687. The primary T3
checkout stays frozen at its existing source hashes; this experiment
changes none of those files or outputs.

Both conditions use the saved Karl case, the NEW shelf, plain Qwen3.8-27B,
normal Engine chat writing, bounded reasoning of 384 tokens, and no adapter.
A shows the existing excerpts. B sets `HEGEL_SHELF_WHOLE=1`, showing the
same selected passages whole within 1,900 characters. The selection query
contains only the observed events. Unknown facts and the private-letter
instructions stay in both writer prompts. Neither becomes retrieval input.

Use the same ten seeds, 2026101220–2026101229, in adjacent A/B pairs with a
fixed shuffled seed order and randomized within-pair order. No selected
successful retry replaces a first request; every raw call and retry stays.
Capture the actual offered text and check that B holds
`Gehorsams gegen die Lehrer`. Whole prompts remain under 7,263 native
server tokens. The shared three-slot server remains unchanged: slot 0 for
the world, slot 1 for the active T3 trial, slot 2 for this experiment.
Concurrent GPU load is reported with per-job and summed wall times.

`pc/writer_trial.py prepare --task T4b` freezes source, input, cases, shelf,
seeds and token preflight in a new output directory. `run --task T4b`
generates twenty letters without simulating a day or changing saved state.
The guide is the v2 guide. Random text ids hide A/B; the new key stays
outside Git until Claude commits scores and their SHA256 hashes.

The unchanged pass rule is B commitments at least A + 0.5 and B argument
not lower. Whole passages remain off by default. Claude owns default
enablement and main merges after the blind result and full-suite pass.
Train nothing and keep the public world paused.
