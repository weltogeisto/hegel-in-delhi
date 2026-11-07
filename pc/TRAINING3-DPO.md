# Training 3 DPO launcher

This implements the DPO rehearsal and training portions of
`pc/TRAINING3-RUN-20261106.md`. It reuses Training 1's owned child processes,
Pi pause between natural calls, original-server startup lock, deadline guards,
conversion, and restoration. It does not change the world engine or live
configuration.

The installed TRL 0.24.0 came with the existing Unsloth environment. The
stdlib-only runtime check pins package versions and the two relevant TRL source
files in `pc/training3-runtime.json`; it rejects a changed runtime before
importing Unsloth or torch. No installation is performed.

## Frozen recipe and data

LoRA rank 16, alpha 32, beta 0.1, learning rate 1e-5, one epoch, microbatch 1
with accumulation 8. Only decision-call pairs enter. Candidate and pair hashes
are checked and Claude's unchanged labeller is replayed locally to verify the
labels. At least 200 pairs are required.

Tokenization matches the installed TRL decoder-only path, including the
completion EOS. Prompts and completions are never truncated: pairs exceeding
the declared cap are excluded whole, with IDs and lengths retained. Both
reference log-probability tables are computed and saved before optimizer step
one, using the base model with the LoRA disabled. No second reference model is
loaded. Eight fixed training examples provide timing/diagnostic loss only;
they are not a held quality test, T45 cohort or checkpoint selector.

## Daytime lifecycle

Use `python -m pc.run_training3 --write-intent NEW_JOB --restore-by ISO_TIME
--rehearsal` with the reviewed machine configuration on stdin. The configuration
contains the original server/launcher, existing normal power receipt, SSH
argument paths, model/converter paths, candidate/pair/stats files, length cap,
native shadow repository and conservative initial timing estimates. These are
the corresponding fields from Training 1's machine configuration, not an old
Training 1 intent. Preparation requires a clean reviewed checkout and pins
every input.

Start the resulting intent once with `--intent INTENT --intent-sha256 HASH
--detach`. Admission runs in an exited stdlib child **before** the ML Python
process starts. There is one owning controller and no automatic restart.
The same-day restore deadline must be no later than 20:00 Berlin and leave
15 minutes before the existing power cutoff. Compute retains the 30-minute
restoration reserve; Phase B is also capped at seven hours.

The rehearsal runs three optimizer steps, evaluates after step two, converts,
serves one actual decision at adapter scale 1 and one at scale 0, and restores.
The memory and post-evaluation speed gates use the actual measurements.
Conversion/serve duration is also measured and retained. A real intent requires
the complete passed rehearsal, unchanged inputs/source, verified restoration,
and a subsequent natural published `mind` decision.

The real run uses one epoch over all eligible pairs when the measured budget
fits. Otherwise the largest fitting subset of at least 200 pairs is selected
with seed 1831, **before training**, without using results. All checkpoints and
reference tables remain. Memory cleanup follows diagnostic evaluation.

## What completion means

The two serve checks establish conversion and routing, not quality. The real
completion status is `DPO_TRAINED_SMOKE_VERIFIED_T39_TEST_PENDING`.
T39's frozen-manifest comparison against its better arm and Claude's blind
scores are still required; this launcher neither fabricates those scores nor
adopts an adapter. Voices, owl and writing defaults remain unchanged.

CPU/fake-process tests cover admission order, exact untruncated token boundaries,
label provenance, minimum-pair and measured-subset gates, reference tables
before training, both serve scales and schema, no retry after an unknown,
restoration on every pipeline failure, measured rehearsal gates and natural
post-restoration evidence. Actual DPO memory, speed and quality remain for the
authorized reviewed rehearsal.
