# Structured outcome memory: 11 October

Step 4 is under isolated validation. It is not deployed. The live world stays
paused. No training or Hegelizer run is authorised here.

## Evidence and writers

`world/records.py` projects one typed store into each daily JSON at save time.
Reading an old day does not rewrite it. Each record has a stable content ID and
an exact source collection/index plus SHA-256. Appending preserves source IDs;
a correction invalidates the old ID. Multiple records at one minute remain
distinct. This follows the typed provenance boundary in
[MemIR](https://arxiv.org/abs/2605.25869), with the required difference that
reported content is never promoted into fact.

- Events attest controlled observations, accepted actions and state snapshots.
- Statements retain exact words, speaker, recipient, time and place; their
  content remains unverified, including Hegel's own utterances.
- Payments retain canonical identity, amount, direction and settlement status.
  An unpaid debt or uncashed cheque is not settled cash.
- Works retain manuscript identity and text. An addressed letter is a draft.

Reading establishes exposure, not truth or agreement. Offered/purchased food
does not establish eating. Thoughts and owl prose are interpretations. New steps
retain controlled observations separately from the legacy mixed event string,
which can contain NPC speech. Activity begins after travel; a state snapshot
attests only its own horizon.

Recurring bills have an identity from cost source and due date. Other new
transactions get unique monotonic IDs carried through settlement. Settled
canonical bills cannot charge again across days. Retrying the same purchase
execution context reuses its IDs; distinct same-price purchases remain distinct.
Legacy missing identities stay unknown. Semantic similarity is not identity.

Enable the candidate explicitly with `HEGEL_OUTCOME_MEMORY=1`. Defaults retain
the existing runtime until review, including parked distillation prompts.
Decision recall stays within 850 characters/eight lines (currently uses at most
600 characters). A labelled prior interpretation shares that space. Writings
share the existing 9000-character manuscript allowance between drafts and typed
evidence. Plain writing retains its exemplars and final header. Owl/Depesche
share the existing 24000-character record allowance with labelled interpretations.
Critical current outcomes have reserved space in the large evidence view.
Selected/excerpted views warn that omissions prove no absence. An impossible
minimum budget fails explicitly.

## Claim support

`HEGEL_CLAIM_CHECK=1` requires outcome memory and a calibration file supplied by
`HEGEL_CLAIM_CALIBRATION`. Missing/mismatched settings fail; no default fitted
temperature is invented. The 27B model extracts concrete premises sentence by
sentence. Literary context resolves pronouns but does not establish events.
Arguments, evaluations, hypotheses and intentions themselves are not simulation
facts. Every extracted premise must pass. Sentences without factual premises
retain their argument without a fake probability vote. Extraction mistakes
count as pipeline errors.

Protocol `hegel-record-support-v2` uses constrained **1 = supported, 0 =
unsupported** votes and raw pre-sampling `n_probs` log probabilities. Grammar's
fast path can expose unmasked mass, so post-sampling mass is not assumed to be a
binary distribution. Both explicit vote token IDs must be present; absent votes
trigger larger distribution requests, never inferred zeros. The log odds are
`log p(1) - log p(0)`, conditional on those two votes. Thinking, adapters, sampler
cutoffs and repetition penalties are disabled for checking. Raw requests,
responses and errors are audited before parsing. These are support probabilities,
not objective truth probabilities.

Unsupported prose gets one rewrite of that field. The rewrite is checked again;
still unsupported sentences are omitted by exact source spans. Executed actions
and source records never change to agree with prose. The append-only audit keeps
every sentence, extracted premise, records checked, vote, rewrite, omission and
result. Protocol/JSON errors propagate rather than becoming factual verdicts.

## Calibration and evaluation

The original 150 manually agent-labelled 8 October sentences, rationale, source
texts and evidence remain frozen: 87 supported/no-factual-premise and 63
unsupported labels. Complete source texts define the original 101/49 split.
These are Codex assessments, not independent human judgments.

The initial full-sentence editing rule failed: the predeclared 0.9 cutoff kept
none of seven supported concrete held-out sentences. Held-out ECE was 0.1733
before / 0.1631 after scaling. That failed development result is preserved.

The atomic-premise protocol is a new development trial. A separate manual audit
flags ambiguity without overwriting labels. Only non-uncertain calibration rows
fit temperature or choose a threshold. The threshold maximises balanced accuracy
subject to 80% supported retention both overall and on concrete premises.
Report ECE, Brier, log loss, false acceptance and false deletion separately.
The original held-out split has been inspected already: reuse is development,
not independent confirmation. Fresh trajectories provide the next check.

`pc/outcome_trial.py` runs scratch trajectories against a dedicated server,
using frozen before/after code and recording every HTTP call. Both arms use base
Qwen3.8, the same persona and bounded reasoning; only the evidence/check path
differs. Initial seeds match, but decisions may diverge. Keep refusals, outputs,
prompt sizes and wall time per day. Do not report the checking model's flags as
independent error counts. No waking, publication, live feeds or training writes.

Pending: new calibration; one seed/one day smoke with manual error audit; full
suite and verified bundle; then three fresh seeds/two days in both arms. Use a
dedicated three-slot instance if it fits, otherwise run sequentially.

## Blind review

`pc/blind_review.py` packages writing and decision prose from review-only.zip
with ten less familiar English shelf passages, the same random IDs in two
orders. It refuses to write the actual identity key into the repository or rater
directory. No key is embedded in the guide, packets or bundle. Sixteen blank
essay/letter slots come from the human template; no model writes the situations.
Welt sends packet A to Grok 4.7 first and packet B to Claude second, with the
same four-dimensional guide, retaining the key privately.
