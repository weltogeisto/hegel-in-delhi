# Hegel in Delhi: the Claude and Astra implementation manual

**Version 1.1 | 6 November 2026 | Prepared for Welt, Claude and Astra**

**Purpose:** turn the existing project into a character whose decisions, memory and development meet Welt's stated intent. Finish bounded work, produce interpretable evidence and stop repeating failed or superseded experiments.

**Canonical form:** this Markdown file. The PDF is the same manual for reading. Suggested repository location: pc/HEGEL-IMPLEMENTATION-MANUAL.md.

**Evidence baseline:** main commit ef610384c4b87e8e1964e1bd68d1f4cbaf016a14; shadow commit 7ad91949c21f39f3a595e37256356a7010ebea45; the six supplied documents; the interview in this conversation; and the November 6 completion and authorization records on PR #1. Repository inspection establishes committed code, not the version/configuration currently running on the PC or Pi. No runtime change or training run was performed while preparing this manual. [R1-R5]

---

## 0. Start here: a 48-hour execution sprint

**The goal is a living Hegelian character in contemporary English, with a reliable record of his life and room to be mistaken and to change.** Better imitation of nineteenth-century English translators is no longer the adoption target for ordinary thoughts.

The project has working infrastructure and completed experiments. Its immediate problem is a mismatch between the intended character, the prompts, the evaluation rules and the training tasks. Resolve that mismatch once, then finish the already authorized work.

### The first working day

| Owner | Work to complete | Concrete handoff |
| --- | --- | --- |
| Claude | Record the six interview decisions in DECISIONS.md; amend the ordinary-life and conviction instructions; version the new evaluation contract. | A small reviewed contract/prompt PR, a rubric, and a current task table. |
| Astra | Capture the actual PC/Pi revisions and effective settings; recover the November 6 forty-case outputs; report T39's true completion state. | One baseline receipt and an export of existing evidence. No regenerated old cases. |
| Claude | Finish the Training3 candidate schema and label rules, including prompt visibility, source lineage and split exclusions. | Executable CPU validation and an explicit comparison with the old labeller. |
| Astra | Build the missing four-candidate sampler and DPO path under the existing Training3 go; reuse launcher components. | Two reviewable implementation units with focused tests. GPU work follows T39 and the data gates. |
| Claude, then Astra | Preserve source attribution through shelf splitting, retrieval and display; trace one existing source/commitment through the assembled decision request. | One source-label fix and one source-to-decision trace. |

These tasks run in parallel where they do not share a mutable file or GPU. No new broad literature review is on the critical path. The legacy adapter remains off. T39 is completed under its frozen protocol; its results are not silently rescored as though it had tested the new contract.

### What counts as progress

A task closes with a changed artifact or measured result: a merged fix, a complete candidate dataset with a yield report, a completed run, a resolved failure, or a negative result that retires an approach. A status message, a new handover and another list of proposed experiments do not close an implementation task.

The first delivery has a **48-hour execution target**, using the existing daytime windows:

- the contract and CPU/data-integrity corrections are merged and verified; prose changes pass their matched screen before shadow adoption;
- T39's actual result or exact remaining measured work is reconciled;
- the missing Training3 sampler/trainer is reviewable and its data/rehearsal gate has a result;
- the approved optimizer run and matched evaluation finish if the measured pipeline fits the available window;
- any passing independent fix reaches shadow under the existing deployment policy.

The clock is a delivery deadline for concrete artifacts and a measured result, not a claim that GPU work has a known duration before rehearsal. If a gate prevents training, close that gate with the exact failure, the smallest remedy, its owner and the next authorized execution slot. Do not turn it into another open-ended planning phase.

The broader acceptance target remains: reliable event/claim/belief memory; a conviction whose revised content affects later decisions; one tested corpus-to-reasoning mechanism; and coherent closed-loop behavior. Those are successive work packets, not prerequisites for the first useful release. No two-week calendar is imposed on them.

## 1. The character contract

### 1.1 Welt's decisions

| Question | Settled answer | Implementation consequence |
| --- | --- | --- |
| How far can the character develop? | Even central convictions may change, while his reasoning remains recognizably Hegelian. | Store the content and history of convictions. Do not permanently force every Berlin-era conclusion. |
| How far can an individual rewrite go? | Develop or revise the reasoning, but preserve the conclusion. | A rewrite preserves its input's conclusion, events and commitments to action; it may construct a different argument. |
| How close must reasoning stay to the texts? | Concepts and reasoning habits come from the corpus; fresh arguments need no passage-by-passage support. | Source-ground the design and evaluation. Do not require a quotation or citation in every thought. |
| Can he trust someone and be wrong? | Yes, provided the record distinguishes beliefs from actual events. | Permit grounded mistaken beliefs. Keep canonical outcomes separate from what anyone believes or says. |
| What belongs in ordinary moments? | Mostly practical or personal observations; philosophy when something calls for it. | Breakfast, errands and waiting are valid in themselves. Do not require philosophical novelty at every tick. |
| How should ordinary observations sound? | Natural contemporary English; perspective and reasoning establish identity. | Retire translator-style similarity as an ordinary-thought promotion gate. |

These are the user's requirements, not an interpretation of an old brief. They supersede conflicting target descriptions in older plans.

**Scope matters.** The user settled the register of ordinary non-philosophical observations. The exact register of a long philosophical manuscript or the owl's literary diary remains open. Preserve their current role separation and test changes separately; do not make that unresolved detail block ordinary-life improvements.

### 1.2 Two kinds of change

An individual rewrite and a life history are different operations.

During a rewrite, the initial conclusion is fixed. A new explanation cannot turn a refusal into agreement, uncertainty into certainty, a plan into a completed action, or a mistaken belief into objective fact. It can reorganize reasoning, introduce a relevant conceptual distinction and remove weak reasoning. If it cannot produce a coherent argument while preserving the conclusion, keep the original and record the failure. Do not manufacture supporting events.

Across later encounters, a conclusion may change. That change belongs in a new dated belief or conviction version, supported by what he encountered and by a concise account of why it mattered. The earlier belief remains in the history.

Therefore **Hegelian reasoning must enter before the initial judgment or action is chosen**. A postprocessor that must preserve the conclusion can improve expression and reasoning, but cannot be the only mechanism that makes the decision Hegelian.

### 1.3 Historical continuity without a predetermined ending

Keep the character's starting biography, historically grounded commitments and dispositions. Preserve the project's decision that Delhi does not steer him toward an approved modern position. Reaffirmation, uncertainty, a partial revision and a major change are all possible.

A contemporary narrator's moral judgment is not evidence of character fidelity. Equally, repeating a historical prejudice or doctrine regardless of experience is not evidence of intellectual continuity. Evaluate how the current judgment relates to his sources, commitments and encounters. This is a simulation design criterion, not a claim that a unique historical counterfactual can be established. [R2]

### 1.4 Data and authority boundaries

The existing data rule remains:

- authentic approved human corpus material processed under an allowed recipe;
- permitted local-model output selected through predeclared deterministic checks;
- Welt's own independent judgment or selection;
- never frontier-authored or frontier-selected training examples.

The existing training README permits project control prompts such as the soul, schema and rendered world situation. That permission does not permit Claude or Astra to invent character thoughts, teaching answers, dialogue scenes or preferred completions for training. Nor does it permit a frontier model to rank actual training rows or choose attractive corpus passages for the training set. [R6]

This manual, research interpretation cards, evaluation fixtures and frontier judging outputs are **engineering/evaluation material**. They do not become training targets. Runtime prompt use and training eligibility are separate decisions. Preserve selection lineage; a later approval does not change who originally selected a passage.

Use the existing collaboration roles and latest task-specific permissions. The manual specifies work; it does not create spending, package-installation, overnight, public-world or destructive-history authority.

## 2. What exists, what failed and what remains unbuilt

### 2.1 Verified current state

| Area | What the pinned repository or run record establishes | What it does not establish |
| --- | --- | --- |
| Training1 round two | 517 optimizer steps, six evaluations, checkpoint 400 tested; plain Qwen and timer restored; next natural decision used the mind. | No new adapter adoption. No claim that the new user contract was tested. |
| Old quality result | Delta 0.7644 versus control 0.7600; old meaning score 23/40 versus 34/40; zero final twelve-word copies; contract 20/20; zero recorded leaks; maximum restyle latency 4.31 s. | The number of genuine fact/conclusion failures under the new contract. |
| T39 | Approved, manifest frozen, DRY 0.8 confirmed; 157 cases including 156 decision opportunities and one bedtime marker. | A completed comparative result in the pinned main task log. Astra must reconcile later artifacts. |
| Training3 | Explicit November 6 go; candidate labeller and tests exist. | The requested candidate sampler and DPO trainer are not present in pinned main. |
| Training1 launcher | Admission, ownership, guards and restoration machinery exist. | It is not a generic Training3 launcher. Its recipe and several assumptions are hard-coded. |
| Outcome attribution | Typed entries, recent executed-activity feedback, payment memory, NPC role facts and owl closing-state records exist. | Complete semantic prevention of claims becoming facts. |
| Owl chronology | Every record line is represented or generation fails if the budget cannot fit even a minimal representation. | Every detail in a shortened long entry survives. |
| Convictions | Status changes persist. | The proposition itself is not revised: the schema stores id, status and evidence times, and revise() changes only status. |
| Hegelizer integration | An optional guarded restyle utility exists. | Engine.step does not call it on pinned main. Its guard checks empty/truncated/copied text, not semantic fidelity. |
| Corpus | Retrieval, chapter-related splits, provenance records and an existing cognitive-architecture note exist. | End-to-end passage attribution and a demonstrated corpus-derived decision mechanism. |

Sources: pc/TASKS.md, the completion comment, world/owl.py, world/engine.py, world/restyle.py, tools/decision_pairs.py, pc/run_training1.py and the complete pinned tree. Existing features must be reused, not reimplemented from an old diagnosis. [R1, R3, R7-R11, R22]

The top of pc/CODEX-STATUS.md on the inspected codex/outcome-memory head still describes October 27. Treat it as a stale status record, not proof that November work did not happen. Likewise, an open PR does not prove its files are absent from main; selected changes may already have been integrated. Reconcile by commit and file content. [R12]

### 2.2 What the adapter result actually says

The old meaning judge demands that a rewrite say everything and add nothing. That can penalize reasoning development the user now explicitly permits. The old result still records poor performance against the old protocol, and the adapter should remain off. It does not establish that all seventeen failed cases changed facts or conclusions.

Astra exports the existing forty inputs, both outputs, raw attempts, fallback status and old judgments. Claude reassesses them under the new rubric in Section 5. The result must distinguish:

1. changed or invented events;
2. changed conclusion, decision or epistemic status;
3. allowed development of reasoning;
4. changed prose/register without a substantive fidelity defect;
5. unclear or internally inconsistent source thought.

Retain both score versions. Do not rewrite the old scoreboard or declare retrospective success. Do not consume the sealed T45 set to debug the legacy judge. [R3, R13]

The observed zero-copy result also does not prove that Goldfish caused the improvement: there was no matched control isolating that change, and the pilot and later copying tests used different thresholds. Goldfish is a memorization mitigation method, not a guarantee of reasoning fidelity. [R3, P3]

### 2.3 Why the work has not compounded

The evidence points to several interacting causes, rather than one failed model:

- **Target mismatch:** translator style, unchanged reasoning and constant philosophy were being rewarded while the desired character now has different requirements.
- **Representation gaps:** a status word can change while the underlying conviction, retrieval query and prompt stay the same.
- **Training contract gaps:** some preference labels inspect history the learner does not see; the reusable distillation path can save a shorter prompt than the one used to generate a retry.
- **Operational failures:** self-counting GPU admission, checkpointing after evaluation, a wrong restart path and an overstrict memory ceiling delayed Training1. Those are documented engineering failures, not evidence that local training is impossible.
- **Evidence fragmentation:** current tasks, old handovers, branch status and local result folders describe different times. Agents repeatedly reconstruct the project instead of advancing one current queue.

The remedy is a small number of complete paths from input to behavior to result. Do not start another adapter cycle merely because the previous one failed a metric that is now superseded. [R3, R8, R12-R15]

## 3. Replace conflicting targets prospectively

| Existing rule or practice | New treatment | What is preserved |
| --- | --- | --- |
| Ordinary thoughts should resemble nineteenth-century translators. | Contemporary English; identity through perspective, commitments and reasoning. | Corpus concepts, historical grounding and separate long-form evaluation. |
| Restyle preserves every reasoning step and order. | Preserve conclusion, recorded facts, action and epistemic status; allow different reasoning. | Original input/output and the old score. |
| Seek a tension in every situation. | Practical/personal default; philosophical engagement when relevant. | Capacity for sustained philosophical argument. |
| Hold convictions as in Berlin. | Start from grounded historical convictions; store later versions. | Initial version and full development history. |
| Any repeated four-word phrase makes an inferior candidate. | Keep overlap as a diagnostic; distinguish damaging repetition from necessary recurrence. | T39's frozen metric and historical series. |
| Evidence time exists, therefore a thesis change is grounded. | Resolve a stable source ID, preserve attribution, inspect inferential relevance. | Existing day records and timestamp display. |
| A false belief is necessarily a fidelity failure. | Score belief plausibility separately from event integrity. | The actual state of the simulated world. |
| A single noisy mean must never decrease. | Use predeclared practical margins and uncertainty for soft qualities. | Hard invariants, existing full-suite requirement and historical test decisions. |

The existing prompt and restyle instructions are documented in R22. Claude records these amendments as a new contract version before new comparative generation. They do not silently alter a running T39 experiment or convert an old failure into a pass.

For already authorized Training3, implement the missing sampler, exact-prompt retention and integrity checks now. The original zero-overlap preference objective and old voice rubric require an explicit task-spec amendment under the new user goals. Record that amendment before candidate labeling/training. If a material objective change remains unresolved, keep it visible as the one pending decision; do not stop unrelated CPU work or ask again for the existing DPO go.

## 4. The minimum architecture

Build on the day files, current engine and existing model profiles. No new graph database, agent framework or second canonical world is needed.

### 4.1 Keep five kinds of information distinct

| Record | Meaning | Can be wrong? | Who changes it? |
| --- | --- | --- | --- |
| Event/outcome | What the engine records as occurring: movement, payment, delivery, eating, reading. | A software defect can misrecord it; character belief cannot rewrite it. | The engine, through a valid transition. |
| Received claim | What a particular speaker or source asserted at a time. | Its content can be false. The fact that it was received is still recorded. | The encounter/reading path appends it. |
| Belief | What Hegel currently takes to be true, with its source and status. | Yes. He may trust, infer, doubt and later correct it. | The character's authorized update path, with provenance. |
| Commitment | His current practical or philosophical position and its prior versions. | It may be reconsidered or abandoned. | A versioned update supported by encounters and reasoning. |
| Interpretation | Diary, reflection, manuscript or explanation of events. | Yes; it must not silently become canonical history or new exposure. | The appropriate writing path. |

Retain actor, recipient, time, quantity, direction, modality and promise/completion status. A promise to deliver is not delivery. A payment claim is not a settled ledger entry. An explanation of why he believed something is not proof that its content was true.

The current memory exposure filter already excludes his own thoughts, plans, manuscripts, speech and owl interpretations from sources of new post-1831 knowledge. Preserve it. Receiving a false claim can legitimately expose him to a name or idea; exposure does not establish truth or understanding. [R7]

### 4.2 Add stable source IDs and narrow persistent state

Additive fields or sidecars are sufficient at first. Suggested field names below are an implementation specification, not an existing API.

**Source record:** source_id, day_id, entry_index, simulated_time, kind, actor_id, recipient_id, source_hash, epistemic_type.

**Belief record:** belief_id, version, proposition, status, source_ids, acquired_at, supersedes, correction_source_ids, rationale.

**Commitment record:** commitment_id, version, proposition, criterion_if_changed, status, source_ids, prior_version, rationale, effective_from.

**Obligation/outcome record:** obligation_id, parties, promised_object, due_time, status, originating_source_id, outcome_source_id.

Use statuses such as believed, uncertain and corrected for beliefs without pretending that a confidence number is calibrated. A broad philosophical conviction does not need to become a database of every sentence he thinks. Persist only items that must affect later action, recall or development.

For legacy records, derive IDs from the immutable source path/hash and entry position. Do not rewrite old day files to pretend these IDs existed then. Keep a mapping to the original source and mark reconstructed state explicitly.

### 4.3 Make state changes reach the next decision

The minimal causal path is:

1. Assemble the current situation from state available before the step.
2. Retrieve relevant observations, attributed claims, open obligations and current commitment versions.
3. Include relevant corpus material or an experimentally enabled reasoning operation.
4. Generate the initial judgment/action.
5. Validate the contract and execute the outcome.
6. Record the action, actual result, claims received and any belief/commitment update.
7. Use those current versions in later prompts and shelf queries.

Trace the actual assembled request, references and resulting state patch. A named module that never changes a prompt, action, retrieval choice or persisted state has not implemented a cognitive function. A model's explanation is evaluable output; it is not proof of its hidden internal process.

### 4.4 Allow failed attempts where they belong

World.check currently rejects some destinations if they will be closed on arrival. That can be useful contract enforcement, but it can also prevent a permitted mistaken-belief episode from happening. [R9]

Keep hard constraints against impossible state, overspending and invented completion. Separately represent a valid attempted visit, collection or inquiry that fails because the world differs from what he believed. Such a failure should consume the appropriate simulated time and produce an observable outcome. Do not solve this by allowing arbitrary invalid actions or revealing hidden world state in a retry.

Start with one existing scene family and its actual failure mode. A general failed-action system is not required for the first milestone.

### 4.5 Memory should preserve consequences

The present 850-character recall, short person memories and recent excerpts are useful bounded inputs, but they do not reliably preserve open obligations or later corrections. Keep the initial comparison at the same budget so a gain can be attributed to selection and representation rather than more context. [R7]

Prefer relevant unresolved obligations, recent corrections, current beliefs and consequential outcomes over the beginning of an owl diary. Keep source handles and current/superseded status. Retrieve full original records when an ambiguity matters; do not keep recursively summarizing summaries.

The owl's existing closing-state block and whole-day chronology remain. Add checks that attribution survives the generated interpretation. Do not flatten the whole diary into a ledger: the earlier broad typed-record experiment did not improve aggregate truth and reduced argument scores. Apply structure where it protects consequential facts, then let the prose remain prose. [R4, R11]

### 4.6 Conviction revision must change content

A revision needs more than a new status:

- uncertainty may change status while retaining the proposition;
- a revised proposition needs its actual new text and predecessor;
- a changed criterion needs its previous and current form;
- abandonment must stop the old proposition from continuing as an active instruction;
- reaffirmation may retain content while adding a reason.

Resolve evidence by source ID, including multiple events at the same minute. Mechanical checks establish that evidence exists and was available. They do not establish that it is a good philosophical reason. Use calibrated review for that question.

The current twenty-thought rule is an outage safeguard tied to the reporting floor. It is not a philosophical law. Keep it until a tested replacement separates incomplete-day reliability from relevance of experience; do not silently remove it as part of an unrelated patch. A later replacement may allow one decisive encounter to matter without requiring twenty filler thoughts. [R11]

## 5. Evaluate the character the user actually wants

### 5.1 Separate questions that require different judges

| Dimension | Question | Evidence and method |
| --- | --- | --- |
| Contract/state integrity | Did execution preserve valid state and actual outcomes? | Deterministic checks, event/state comparison, focused regression tests. |
| Epistemic integrity | Is a claim, belief, observation or inference represented as such? | Source tracing plus calibrated semantic review. |
| Rewrite fidelity | Are facts, conclusion, action and certainty preserved while reasons may change? | Paired source/output review; entity/number/negation checks are supporting diagnostics. |
| Hegelian reasoning | Does a relevant corpus-grounded distinction or reasoning habit do useful work? | Source-aware blind review, transfer cases and matched ablations. |
| Ordinary-life quality | Is the response practical/personal, natural and appropriate to the moment? | Blind preference and concrete rubric anchors. |
| Continuity/development | Does later behavior use outcomes, corrected beliefs and revised commitments? | Multi-step and cross-day tests. |
| Operational quality | Does the system stay available and restore safely within its window? | Runtime receipts, latency, fallback and process records. |

A local or frontier evaluator may assist evaluation. Its outputs do not become training labels under the data rule. Welt settles genuine preference or interpretive disagreements. Keep that human work focused: one small packet of the most consequential ambiguities, not repeated forty-case assignments before ordinary engineering can proceed.

### 5.2 Rubric anchors

Use a 1-5 scale only for soft dimensions. Freeze applicable dimensions per context before generation; use N/A when philosophical reflection or revision is unwarranted. An ordinary practical observation must not receive a low reasoning score simply for containing no philosophy. Every low or high score needs a brief reason tied to an observable feature.

**Hegelian reasoning**

- 1: irrelevant doctrine, a stock formula, unsupported authority or an argument inconsistent with its own stated distinctions.
- 3: relevant and coherent reasoning, with an identifiable connection to a current commitment or sourced concept, but limited development or transfer.
- 5: a specific difficulty is worked through; relevant distinctions affect the judgment; what remains justified is retained; the result makes sense in a new case.

This is a proposed operational rubric, not a validated measurement of historical identity. In review notes, identify the relevant corpus-ledger relation and explain its effect on the judgment. This attribution belongs in evaluation, not in every character thought. Philosophical vocabulary alone earns no points. A justified unchanged conclusion is allowed.

**Ordinary-life quality**

- 1: ceremonial philosophy, generic commentary, forced novelty, avoidable verbosity or a response that misses the practical situation.
- 3: clear, plausible and relevant everyday observation.
- 5: specific and economical observation that reflects the character's interests, relationships or circumstances without performing philosophy unnecessarily.

**Development**

- 1: a status flip with no identifiable content or consequences, source laundering, or a reversal forced by the evaluator.
- 3: a traceable response to experience through retention, qualification or revision, represented in later recall.
- 5: a coherent response to experience that transfers to another relevant situation while preserving the history. Well-supported stability or reaffirmation can earn this score.

These dimensions are not summed into one magic score. A high style score cannot compensate for an invented payment.

### 5.3 A bounded evaluation set

Create a new evaluation-only development manifest of **48 contexts**, grouped before generation:

- 16 ordinary practical/personal moments;
- 12 consequential encounters involving claims, obligations, money or possessions;
- 12 situations that could engage a philosophical commitment;
- 8 correction or revision situations.

Reuse eligible recorded contexts mechanically; add clearly labelled evaluation fixtures only where the mechanism cannot otherwise be tested. Do not invent desired character answers. Separate real, reconstructed and synthetic cases in reports.

Keep a fresh **24-context confirmation packet** with the same coverage proportions. It is separate from legacy T45, which remains an old-protocol holdout. Group related scene families, episode prefixes, translations and near-duplicates on one side of a split. A later date alone does not establish independence.

For the first prompt screen, freeze the 16 ordinary cases plus eight of the consequential encounters that call for practical, non-philosophical handling. Use three seeds and two arms: **144 generations**. Escalate to the full development and confirmation sets only after a useful signal. Do not run a full benchmark at every edit.

For longitudinal behavior, use two short episode families, two seeds and two arms, roughly 12 decisions per episode: **96 decision opportunities**, plus NPC/owl calls. Let each arm's history develop from its own actions. Fixed exogenous conditions are compatible with different trajectories.

These quantities are proposed resource bounds. They are not statistical power claims.

### 5.4 Promotion rules

Predeclare the primary outcome and what counts as a material change. Use the following initial defaults unless a task already has a frozen gate:

- **Hard integrity:** zero new violations of deterministic state, source, split and routing invariants in the test packet.
- **Prompt/register screen:** at least 16 of the 24 context-level judgments prefer the new arm for practical appropriateness, with no concrete consequential regression; aggregate seeds within context.
- **Reasoning screen:** mean improvement of at least 0.5 on the 1-5 reasoning rubric over the matched generic scaffold in reasoning-applicable cases, evidence in at least two relevant families, and no more than 0.25 loss on the ordinary-life quality rubric in mundane controls.
- **Confirmation:** the same direction of effect on fresh cases; no new material failure hidden by the average.
- **Closed-loop observation:** intended benefits persist; action failures, false event claims and repeated unresolved loops are reported with denominators and do not materially worsen.

The 16/24 and 0.5 thresholds are engineering promotion rules, not significance tests or published effect sizes. Report paired context-level differences, uncertainty and raw counts. Cluster by day/family where appropriate; three seeds are not three independent lives. If confidence is weak, mark **inconclusive** and allow only one predeclared extension. Do not keep adding seeds until a pass appears.

A pass qualifies the changed component for a provisional shadow trial. It does not prove that all later days will be faithful. The standing full-suite integration requirement remains.

### 5.5 Preserve old comparisons without being governed by them

Finish T39 exactly as frozen and report its old metrics. Also add the new ordinary-life and harmless-recurrence annotations to a separate versioned report if useful. The old truth audit must not be retrospectively rewritten to hide errors or count every plausible mistaken belief as a new defect.

For a changed prompt, context renderer, checker or sampler, regenerate the necessary comparator before attributing a gain to an adapter. Reuse cached baseline outputs only when their complete request and evaluation identity match.

The old Delta value can remain a descriptive style diagnostic. It no longer determines whether an ordinary thought is acceptable. The number of theses changed, words written, philosophical terms used or thoughts per day is not a target for intellectual development.


## 6. Make corpus grounding functional

### 6.1 Reuse the existing source reconstruction

The repository already contains a nine-page cognitive-architecture note with fourteen claim records, two formalization families and six intervention tests. All its mappings remain provisional. It asks first for source-competent review of H02, H05 and H11, where a philosophical relation could be over-translated into a software mechanism. Preserve that caution. [R16]

The note concerns a general account of cognition. Memory, habit and attention alone do not identify Hegel. The historical character also needs grounded commitments, acquired distinctions, argumentative habits, biography and personal dispositions.

Build one observable connection between these layers. Do not implement fourteen named modules merely because fourteen records exist.

### 6.2 Repair attribution before expanding the corpus

The shelf manifest contains authored texts, translations, posthumous lecture compilations and additions. Its training-only materials include biographies and letters by correspondents as well as Hegel. Keep those witnesses distinct.

There is a concrete loss of attribution: tools/corpus.py drops much work-level provenance when building the index; world/shelf.py split_passages() reduces the reference to a numeric section, and shown() strips the Zusatz label when displaying an excerpt. Preserve that label and the source identity through splitting, retrieval, excerpting and rendering. Add a regression check covering the whole path. [R17]

Use two separate axes:

| Axis | Categories to retain |
| --- | --- |
| Document/witness | Lifetime authored publication; authored manuscript/letter; correspondent; posthumous lecture report/addition; translator; editor; later biography/commentary; unresolved. |
| Position within passage | Endorsed; reported; criticized; hypothetical/example; quotation from another writer; unresolved. |

An affirmative sentence inside a position under criticism is not automatically Hegel's own commitment. German and English versions of one argument belong to one parallel group for splitting and evaluation. They are witnesses to the same argument, not independent held-out cases.

Keep full argument context for research even when the runtime excerpt is short. Preserve source hashes and transformations. Do not silently expand use of sources whose provenance or rights record is unresolved; the manifest itself records uncertainty for at least one translator. This is an unresolved repository record, not a new legal determination.

### 6.3 Four small artifacts

Create these outside mind/train/. They may be one compact store with separate views; no new service is required.

| Proposed artifact | Minimum fields |
| --- | --- |
| research/hegel-v0/source-ledger.jsonl | unit_id, source_sha256, work_id, author, editor, translator, date/edition, language, locator, context_locator, witness_kind, speaker, stance, parallel_group, OCR status, rights_record, usage_scope. |
| research/hegel-v0/claim-ledger.jsonl | H01-H14 ID, evidence_unit_ids, textual_relation, relation_type (conceptual, constitutive, normative, developmental, enabling or reported-position), proposed_constraint, alternative_reading, counterevidence, not_entailed, reviewer, review_status, allowed_use. |
| research/hegel-v0/behavior-spec.yaml | operation_id, claim_ids, trigger, reads, writes, information_boundary, null_case, expected_counterfactual, failure_signal, engineering_assumptions, version. |
| Experiment manifest under mind/results/ | Context/seed/arm IDs, code/model/prompt/source versions, call/token budget, rubric, blind key reference, actual prompt/action/state traces, training_eligible: false. |

Interpretation review is narrow: decide whether the particular mapping is defensible and useful. Welt can adopt a reading for this fiction without that becoming independent historical validation. If independent review is unavailable, keep the experiment provisional. Attribution fixes, instrumentation and ordinary-prose improvements proceed.

### 6.4 One mechanism first

Use the note's conservative family A: fixed operations with revisable content and criteria. Defer changing the dependency graph of the architecture.

The first hypothesis is: **an encountered difficulty can change an interpretation or criterion, and that change can affect a later judgment or action.**

The primary texts support investigating relationships between habit and available engagement, intelligence and willing, and examination of a criterion alongside knowledge. They do not specify a software scheduler, salience threshold or update algorithm. Logic §§79-82 also do not justify imposing a three-stage formula on every meal or errand. Our implementation choices must be labelled as such. [P6-P8, R16]

Use three arms:

1. Contract-aligned baseline.
2. The same facts, beliefs, commitments and source access with a generic reasoning scaffold.
3. The same information and comparable call/token budget with the single source-linked operation.

Start with **12 development contexts x 3 seeds x 3 arms = 108 calls**: eight relevant difficulties across at least two families and four ordinary controls. These can be drawn from the 48-case development set; they are not an additional mandatory suite. For transfer, use eight relevant and four ordinary contexts from the sealed confirmation pool.

Compare arm 3 with both alternatives. If any benefit comes only from extra information or extra inference time, say so. If changing a relevant source/criterion has no effect beyond vocabulary, the claimed mechanism has not been demonstrated.

Keep the new state compact: current interpretation/criterion, prior version, encountered source IDs and concise rationale. An unchanged judgment is permissible. No daily revision quota, compulsory contradiction or approved political destination is imposed.

### 6.5 How to expand after a useful result

Expand by whole arguments and discriminating cases, not by a count of extracted quotations. The next candidates are:

- learned routines that reduce unnecessary attention while remaining interruptible;
- concepts that alter what is noticed in a relevant encounter;
- reciprocal recognition that affects a relationship beyond praise or sentiment;
- retrieval that distinguishes a name, an encountered event and its later interpretation;
- further commitments whose application transfers across institutions and personal life.

Each candidate needs a null case, a source/interpretation record, a visible path into behavior and a bounded comparison. None automatically requires weight training.

## 7. Finish Training3 with a trustworthy data contract

### 7.1 Preserve the existing authorization

Welt already approved Training3 on November 6: daytime, after T39, with sampler and trainer preparation while T39 runs. The approved recipe is DPO with rank 16, alpha 32, beta 0.1, learning rate 1e-5, one epoch, precomputed reference log probabilities and no prompt truncation. The existing runbook names ORPO only as a fallback if the DPO rehearsal cannot fit memory. Do not seek the same go again. [R5, R8]

The go does not authorize night runs, spending, new ML packages, a different model or every alternative training method. Check installed capabilities first. CPU fixes and reviews necessary to make the approved run correct proceed under that scope.

The task is **decision reliability under the corrected contract**, not teaching Hegelian philosophy through a repetition reward. An adapter that learns fewer invalid actions or fewer empty loops may help without establishing a Hegelian mind.

### 7.2 Do not reuse winner-only storage as a preference sampler

The current distillation machinery is reusable for rehearsal and world stepping. Its storage is not the requested DPO dataset. It retains the heuristic winner, and on retries can generate from the full messages array but save messages[:2]. That can attach a completion to the wrong prompt. [R14]

The new sampler must:

- retain all four candidates for each exact first-attempt situation;
- use the declared seeds 1831, 2718, 3141 and 4271;
- record complete request messages, schema and effective sampler settings;
- check each candidate against the same pre-step state;
- preserve raw output separately from any checker-normalized answer;
- store a retry as a distinct prompt/sample, never as an answer to the original prompt;
- retain invalid and interrupted attempts in diagnostics without fabricating completions.

Run rehearsals without publication or live state mutation. If the sampler advances a rehearsal after choosing an action, selection uses a predeclared permitted rule and later situations arise from that actual rehearsal trajectory.

### 7.3 Candidate schema

The current labeller checks only a narrow subset of required integrity conditions. Extend it before relying on its output. [R15]

| Layer | Required fields and checks |
| --- | --- |
| Situation | Stable ID, source, day/date/step, scene family, exact pre-step snapshot and evidence hash, knowledge/corpus version. No closing state from later in the day. |
| Request | Complete messages, schema, rendered/tokenized prompt identity, model/base/adapter identity, seed, temperature and other sampler settings, attempt number. |
| Candidate | Raw completion, parsed answer, normalized checked answer if different, finish reason, token counts, transport status, schema fallback, explicit boolean accepted, errors/warnings, checker version. |
| Label evidence | Reason codes, visible-context evidence, exact overlap spans where relevant, separate whole-day repetition diagnostic. |
| Split | Frozen source/family exclusions, development/confirmation membership and duplicate group. All candidates of one situation stay together. |
| Pair | Same exact prompt; complete chosen/rejected assistant outputs; both candidate IDs; thought-word and total-token lengths; rule version; selection record. |

Reject inconsistent accepted/error flags, duplicate IDs, unexpected seed sets, missing source lineage, future evidence, truncated outputs and raw/checked mismatches. If the checker repairs a field, either use an explicitly permitted deterministic normalization path or exclude the pair; do not silently label raw text as though it were the repaired text.

Keep the complete chosen and rejected JSON completions for DPO. Matching thought length alone does not prevent the rest of the completion from becoming a shortcut.

### 7.4 Fix what the learner cannot see

The current label checks all earlier thoughts in the day. The live prompt exposes only a short recent window, and the echo guard shows only selected phrases already used more than once. These are different information sets. [R7, R15]

For the amended label contract:

1. Define the preference from information actually available in the exact prompt, or add a bounded history field used identically in training and serving.
2. Keep full-day overlap as a separate outcome diagnostic.
3. Do not label a plausible mistaken action as inferior solely because the evaluator knows hidden future facts.
4. Verify that world-check failures used for preference training correspond to learnable contract constraints or visible facts, rather than an unobserved world outcome.
5. If context changes, run a fresh untrained comparator with that same context before measuring an adapter gain.

The knowledge gate already runs inside World.check on thought, says and revision. The task is to verify the accepted flag's provenance, not to invent a missing second gate.

### 7.5 Amend the preference objective deliberately

The current rule chooses the first clean candidate in seed order and the first refused or four-gram-repeating candidate with a thought-length ratio of at least 0.8. If that first clean candidate has no match, later clean candidates are not considered. Those are current declared behaviors, not automatically bugs. Report their effect on yield before changing them.

For the new target, separate three datasets/views:

- **Contract contrasts:** an accepted useful decision against an actually invalid, learnable alternative.
- **Loop contrasts:** an accepted useful decision against a predeclared damaging loop visible from the prompt.
- **Overlap diagnostics:** all other repeated phrases, including necessary reminders and stable commitments.

“Useful” must mean a named deterministic predicate grounded in the world's rules or recorded task progress, or Welt's independent judgment. Claude and Astra may implement and review that predicate; they may not inspect actual candidate prose and select the responses they prefer. If no permitted progress predicate exists, report acceptance and loop status separately rather than inventing a quality label.

Do not automatically turn the third category into negative training examples. A zero-four-word-overlap requirement rewards lexical novelty, which the user did not ask for. A deterministic damaging-loop rule must be written before selection, for example around repeated action/state with no new event or correction; it must allow unresolved needs to remain relevant.

This amendment is a recommended engineering consequence of the interview. Claude records the exact revised rule and its relationship to the approved task before labeling. It is not a claim that these new labels have already been authorized, implemented or validated. Preserve the original label view for comparison. Correcting hidden-information dependence, prompt pairing or factual-versus-belief labels to implement Welt's explicit decisions is an implementation correction under the existing task: record it and proceed. Escalate only a materially different training objective, method or resource commitment, with the completed comparison and exact decision needed. Finish the sampler and report both yields before any such question.

### 7.6 Splits and yield

Exclude T39's two real days, its named rehearsal days, related episode prefixes, and all development/confirmation families reserved for evaluation. The runbook's dates from November 10 onward are a convenient separation, not a sufficient leakage rule. Group near-duplicate and scene-template cases. Keep all four candidates and any retry siblings together.

The plan starts from about 118 real situations plus rehearsals toward 500 total. Recount eligible rows; do not assume the old count is still current. Report real and rehearsal performance separately.

With independent clean probability p per candidate, the chance of at least one clean and one non-clean among four is:

**1 - p^4 - (1-p)^4**

The maximum is 0.875. At p = 0.9, 500 situations yield about 172 mixed situations before length matching; at p = 0.95, about 93. Real candidates are correlated, and multiple label classes complicate this model, so these are illustrations rather than a forecast.

The existing stop rule is **fewer than 200 pairs: stop and report**. Do not relax quality, fabricate rejected answers, handpick failures or rerun seeds until the number passes. Report whether the loss came from few failures, too few good candidates, length matching, missing context or exclusions. More positive-only data may justify a later filtered-SFT comparison; that is a distinct training proposal.

### 7.7 Train the intended completion

Keep the approved DPO hyperparameters for the first run; do not add a hyperparameter search.

Before GPU execution, a tokenizer-only check must verify:

- exact chat template and special tokens;
- prompt/completion boundaries and completion-only objective;
- complete chosen/rejected conversations in the trainer's expected format;
- length distribution for prompt plus each completion;
- the same base/tokenizer identity for policy and reference;
- no research/evaluation-only or frontier-selected rows;
- reference-cache keys covering dataset bytes, tokenization/template, model identity, precision and reference settings.

Do not assume that a list of prompt messages plus a raw string completion is automatically accepted correctly by the installed TRL version. Inspect its actual interface.

Measure representative long pairs in the rehearsal. Precomputing reference probabilities can remove repeated reference-model work; it does not make policy activations or long-context training free. Report excluded long rows by day position and difficulty. Never truncate a prompt to make the run fit. If a deterministic subset is required, select it before training and state the actual exposure count.

### 7.8 What to compare

The essential comparison is the decision adapter against the best eligible inference-only configuration, with identical current prompt/context/checker and no adapter on the other roles.

The historical T39 winner is useful only to the extent its request contract still matches. Preserve the old comparison and add a fresh matched comparator when the new contract changes inputs. Attribute prompt, context and weight changes separately.

The original Training3 gates remain recorded: one-third lower echo share; truth metrics no worse; argument and voice within 0.25. They describe the old task. Promotion under the new manual also requires the corrected register, epistemic and harmful-loop tests. A prospective amendment can replace a misaligned gate; a post-hoc relaxation cannot rescue a result.

Do not train a second round automatically. One bounded DPO result should identify a residual failure worth addressing. A successful contract adapter is not evidence that continued pretraining or a style adapter will improve philosophical judgment.

## 8. Choose training methods for the residual problem

DPO learns from relative preferences over completions for the same prompt. Its usefulness depends on the pair definition. Filtered self-training is a different route that uses generated material passing a selection criterion. Neither method can repair a moving history omitted from the input. [P1-P2]

| Method | Proper role here | Decision now |
| --- | --- | --- |
| Prompt, source attribution and useful memory | Correct goals and make relevant information available. | Immediate implementation and evaluation. |
| Inference settings from T39 | Test whether repetition improves without changing weights. | Complete the existing authorized comparison. |
| DPO on permitted decision contrasts | Improve a precisely defined residual policy failure. | Complete the authorized path after data/rehearsal gates. |
| Filtered SFT | Test whether accepted local decisions suffice when reliable negative pairs are scarce. | Small next comparison if justified; not a silent replacement for DPO. |
| Continued pretraining on authentic corpus | Improve exposure to source concepts/language. | Defer until a held-out reasoning deficit and safe corpus recipe justify it. |
| Context distillation | Transfer a demonstrated benefit of a stable richer context into weights. | Later hypothesis; cannot absorb tomorrow's unseen personal history. |
| New style/restyle adapter | Change expression or develop reasons under a fixed-conclusion contract. | Park until raw-output audit and new evaluation show an unmet need. |
| New base model or rented GPU | Address measured capability or throughput limits. | No change until the present pipeline is correct and measured. Spending requires its own authorization. |

A 27B restyle step on short sequences is not a reliable predictor for paired DPO on multi-thousand-token decision prompts. A faster-thinking derivative can reduce generated tokens without improving training throughput. Hardware changes should follow a measured end-to-end bottleneck, not an assumption that every stalled experiment needs a larger card.

The research literature supports these mechanisms in other settings. It does not provide a known effect size for this particular Hegel simulation. Avoid presenting a fashionable recipe as a substitute for a valid objective.

## 9. Make GPU work finish

### 9.1 Reuse the guarantees, not the hard-coded recipe

pc/run_training1.py already contains useful admission, ownership, guarding and restoration logic. It also fixes Training1-specific step counts, evaluation intervals, restyle/Goldfish settings, 1,024-token assumptions, T45 handling and old power receipts. Build a reviewed Training3 path using its components; do not run it unchanged. [R10]

Keep one owner, one run intent and one controller. No second supervisor, automatic retry tree or duplicate launch to recover an uncertain process.

A run intent records code, data, base model, tokenizer, adapter and prompt identities; actual permission/window; output directory; expected stages; restoration command/state; and a stop reason vocabulary. Reuse known identities and the launcher's existing cached verification. Do not rehash a huge unchanged base before every step.

### 9.2 Rehearse the complete path

A few optimizer steps are necessary but insufficient. The rehearsal includes:

1. Admission before importing GPU-heavy code; identify owned processes correctly.
2. Reference-cache preparation and reuse.
3. A few real DPO steps on representative long pairs.
4. One evaluation and successful return to training mode, including checkpointing state.
5. Checkpoint save and conversion.
6. Serve a decision at scale 1 and scale 0; verify a real adapter effect and valid output.
7. Probe NPC, writing and owl routing explicitly at scale 0.
8. Restore the exact plain server and prior timer state.
9. Record a successful natural decision after restoration when the live world is scheduled to run.

Current HTTPMind has separate decision, writing and NPC profiles. That is useful infrastructure, not proof that every owl or fallback request is isolated correctly. Inspect the actual request path; a default adapter setting must not leak into other roles. [R18]

The existing backend-parity tool checks rendered/tokenized prompts, adapter tensor identity and a measurable toggle effect. Adapt its task-specific probes for decision JSON. Do not demand identical generated prose across different quantizers. [R19]

Stop for non-finite loss or sequence log-probabilities, prompt truncation, absent adapter effect, routing failure, corrupted artifacts or failed restoration. Keep the original failure evidence.

### 9.3 Budget the whole pipeline

Use measured timings from the current recipe:

**Projected total = load + reference preparation + optimizer steps + scheduled evaluations + save/convert + held-out test + restoration reserve.**

The completed Training1 run had six evaluations, not five. Using the supplied approximate timings, 517 steps at 20-30 seconds cost 2.87-4.31 hours, and six evaluations at 21 minutes cost 2.10 hours: **4.97-6.41 hours before conversion, Phase C and restoration**. This is arithmetic from approximate inputs, not the observed wall time. [R3, R10]

Checkpoint 400 represents about 3,200 sequence presentations at effective batch eight, about 25.1% of a 12,750-pair dataset, assuming ordinary sampling without packing or other resampling. That does not prove undertraining; it means an epoch claim would be wrong.

Training3's preparation, sampling and final testing may span several daytime windows. Reuse completed sampling, reference-cache and evaluation artifacts. The first optimizer run must fit one authorized daytime window; if necessary, fix the seed-1831 subset before training. Do not introduce automatic restarts or a multi-day optimizer-resume plan into this run. Do not rerun completed outputs because a later stage failed. Test both the best saved checkpoint and the final checkpoint only if predeclared and affordable; do not start an unbounded checkpoint bake-off.

Use cheap fixed diagnostics during training and the full generation benchmark after a selected checkpoint. Log training time, reference computation, generation evaluation, conversion, restoration and operator delay separately.

### 9.4 Preserve the current power and world arrangements

The latest November 6 instruction is daytime work and no more night runs. Older handovers granting a particular night are not reusable authority. Use the current Power Guard and authorized restore deadline; do not install packages, change power settings or extend the window to rescue a late run. [R5, R20]

Sampling and T39 use the spare slot without pausing Hegel, subject to the existing latency guard. Training/testing pauses the world only within its authorized scope. Restore the prior state on every exit. Do not backfill missing days or force a natural tick merely to create a success receipt.

Keep actual UTC time, Berlin operator time and simulated Delhi time separately labelled. The shifted simulation can legitimately contain a day later than the actual date. Do not “correct” its history on that basis.

## 10. The execution queue

Use this queue to amend the current task list. It does not erase T-number history.

| Packet | Owner and dependency | Deliverable and acceptance | Stop or rollback |
| --- | --- | --- | --- |
| M0: establish the current contract | Claude; Astra supplies runtime receipt. No GPU dependency. | Interview decisions, current permissions, one baseline identity, current task states, legacy output export request. Old scores retained. | Missing raw files are a named evidence gap, not a reason to regenerate or infer their contents. |
| M1: ordinary life and rewrite rubric | Claude code/review; Astra runs the bounded screen. Depends on M0. | Small ordinary-thought soul/restyle instruction changes, no invented examples; 144-call screen; new rubric; raw forty-case re-audit. Owl attribution changes stay separate from literary register. | Keep changed prompt off if practical quality or consequential behavior worsens. No automatic adapter deployment. |
| M2: attribution and consequence memory | Claude code; Astra integration. Source IDs first. | Source labels survive retrieval; relevant claims/beliefs/obligations survive recall; focused tests and one correction episode. | Feature off on provenance/state regression; retain appended records and previous renderer. |
| M3: retry and actual conviction content | Claude code; Astra replay. Depends on source IDs. | Compact retry feedback; first-attempt statistics; optional versioned proposition; current content reaches prompt and retrieval. | Do not combine a schema change with removal of the twenty-thought safeguard. Keep independent switches. |
| M4: corpus-to-reasoning experiment | Claude spec/review; Astra runs. Needs source IDs/current commitment access and the existing note. Frozen sidecars can support evaluation before full M2/M3 persistence lands. | H01-H14 ledger, one operation, 108-call development comparison, fresh transfer and promote/keep-off result. | No effect beyond vocabulary, bad attribution or ordinary-life harm: keep off. One revision at most before closing. |
| M5: authorized Training3 | Astra sampler/trainer/runtime; Claude reviews. CPU work now; GPU after T39 and data gates. | Exact-prompt candidate set; yield report; reviewed DPO path; full rehearsal; one bounded run and matched evaluation. | Under 200 pairs, invalid provenance, hidden-label dependence, memory/time infeasibility or restoration failure: stop with evidence. |
| M6: integrate and observe | Claude merges; Astra deploys within existing scope. Depends only on passing components. | Full integration suite, role-routing proof, closed-loop episodes and a concise release result. | Disable changed component and restore the previous working configuration; never delete the episode history. |

M1 can improve the character before M4 or M5 finishes. M5's CPU implementation does not wait for a philosophical interpretation review. M4 does not require a trained adapter. These are separate lanes with one shared GPU queue.

### The 48-hour execution schedule

| Deadline from the next active session | Claude | Astra | Required outcome |
| --- | --- | --- | --- |
| First 2 hours | Freeze the concise contract amendment and rubric; remove superseded target instructions from the active queue. | Verify the actual runtime once; locate T39 progress and the old forty-case evidence. | One current state, one permission record, one exact next action. No new handover cycle. |
| Hours 2-8 | Deliver the ordinary-life/source-label patch and candidate validation; review the sampler/trainer as pieces land. | Build the four-candidate sampler and DPO integration; continue authorized T39 work in the spare slot. | Reviewable code and focused checks. CPU work proceeds while GPU work runs. |
| By 24 hours | Merge passing foundational fixes; finish the legacy judge audit from recovered outputs; close data-rule ambiguities. | Complete T39 if its remaining workload fits; sample after its prerequisite is satisfied; report measured pair yield and full-pipeline projection. | A shipped correction; completed candidate artifacts or saved sampling progress with measured remaining work; an explicit run/stop decision. |
| Next authorized daytime window, target by 48 hours | Score the prepared blind packet; review the result; merge independently passing components. | Run the complete rehearsal, then the approved one-window optimizer run and matched evaluation if feasible; restore. | A completed bounded experiment or a closed gate with exact measurements, smallest remedy and next execution slot. |

These hours are target deadlines for delivery, not invented GPU timing estimates. The rehearsal controls whether the optimizer run fits. The existing sampler estimate alone is 3-4 GPU hours; remaining T39 work, training, testing and restoration must be measured and counted separately. [R3, R8] Do not compress that physically by skipping evaluation or restoration. Reduce optional work and reuse valid completed artifacts.

Keep at most three active packets: the contract/data fixes, the authorized Training3 pipeline, and the minimum attribution work needed by them. Start the broader consequence-memory, conviction and corpus-mechanism packets as soon as a lane is free. Prepare their CPU work in parallel where useful, but do not require the full architecture before the first result. M4's 108-call experiment uses a later available slot unless Training3 has already closed or it fits without delaying that run.

At 48 hours, issue one concise delivery report with links to merged changes, raw results, remaining measured GPU work and the next concrete action. A known failed gate is closed once; it cannot remain an indefinite “in progress” task. A failed or blocked adapter experiment does not delay a passing ordinary-life or attribution fix.

## 11. Collaboration that does not require Welt to relay work

The current collaboration policy already assigns Claude specs, CPU code, review, blind scoring, the scoreboard and main merges; Astra owns PC/Pi runtime, GPU work, blind packets and shadow operations. Hermes is only the fallback when Astra cannot reach the Pi. Welt owns direction and hard limits. [R21]

### One current status, one task queue, one result packet

Maintain a short current-state header with:

- last verified actual time and relevant simulated day;
- main, working branch and deployed revisions;
- model/adapter/configuration identity;
- running process or no active run;
- current packet, owner, next concrete action;
- exact blocker if one exists;
- latest result location and restoration status.

Archive older status narrative below a link or in a separate dated file. Do not append another “current” header above pages of contradictory claims. The history remains preserved; the active instruction must be easy to identify.

Each task has one owner, one next artifact, one dependency and one definition of done. Claude writes the next actionable task when a review closes; Astra continues authorized work without making Welt a messenger.

### Review and communication

Use focused tests during development, then the standing full suite at integration. Broaden testing only for a concrete unresolved risk. Existing tests that already cover unaffected behavior need not be rerun after every documentation edit.

PR #1 comments wake Claude and incur work. Preserve the existing Done/Blocked/Question rule, no more than six lines, with details in the result file. Do not post progress chatter or duplicate questions. This manual has not posted any such message.

A complete result packet includes:

- hypothesis and contract/rubric version;
- input and runtime identities;
- raw outputs and deterministic decisions;
- blind judgments committed before the key is opened;
- failures, exclusions and denominators;
- timing and memory by stage;
- pass, fail or inconclusive with the next action;
- restoration/deployment receipt where applicable.

Secrets, private blind keys and unrelated personal material do not belong in the public repository. Use existing private artifact locations and publish only the appropriate manifest/result summary.

### Permission precedence

Use the latest explicit user decision for the particular action, then the applicable current collaboration/task instruction. A stale bootstrap instruction does not reintroduce per-step permission. A newer completion record does not authorize a different experiment.

Training3 already has a go. Ordinary implementation, review, correction and the approved run do not need the same approval repeated. New evaluation packets are prepared now; execution must fit an existing applicable inference allowance or a specifically authorized window. This manual does not override a task-specific hold or grant an additional GPU budget. A new package, spending, public switch, destructive history action or materially different training experiment still needs its actual authorization. When one is necessary, show Welt the prepared change, measured need, exact cost/scope and decision required. Do all other authorized work first.

## 12. Integration, rollback and longer-term operation

### 12.1 Keep changes separable

Use independent version/configuration controls for the ordinary-life prompt, memory rendering, retry feedback, conviction schema, experimental reasoning operation and decision adapter. A result must identify which changed.

Extend state additively. New code must accept legacy records with absent fields; pinned rollback code must ignore or safely handle newly added fields. A rollback should disable a behavior without erasing new history. Preserve the original prompt/output and any transformed output separately.

For a decision adapter, explicitly exercise decisions, planning, writing, NPC speech and owl calls. The task spec must state whether the approved decision profile includes morning planning; current chat_decision does. Do not assume that “decision only” means a single call site.

### 12.2 Verify causal continuity

Fixed-input comparisons answer whether a component handles the same evidence better. Closed-loop trials answer whether its choices produce a coherent subsequent life. Both are necessary.

In closed-loop tests, the world executes each arm's actual action and produces the corresponding NPC response and later state. Do not attach an archived reply to a different counterfactual action. Do not use a day-end state to reconstruct an earlier decision without recording how it was derived and what remains unknown. Sequential prediction literature explains why behavior under one's own induced history can differ from performance on fixed examples; it does not itself validate this implementation. [P4]

The first observation packet should include a practical obligation, a received claim that may prove wrong, a later correction and a commitment applied to a different context. These are test categories, not frontier-written training scenes.

### 12.3 Monitor the right quantities

Daily reporting keeps existing availability, fallback, refusals, meals, cash and repetition figures, with their definitions. Add only what supports a decision:

- first-attempt validity versus success after retries;
- unsupported completed-event claims;
- unresolved obligations and missed outcomes;
- corrections retained versus forgotten;
- damaging loops versus harmless phrase recurrence;
- active commitment versions and observed downstream use;
- ordinary-life/philosophical balance from a small fixed audit sample;
- decision latency and background-work impact.

Do not turn “at least twenty thoughts” into a demand for twenty philosophical arguments. Counts for availability are different from quality targets. No daily quota of conviction changes or novel ideas is introduced.

### 12.4 Rollback

If a changed component causes a material regression:

1. Preserve its raw outputs and state history.
2. Disable that component or restore the prior known configuration.
3. Restore the plain server/timer arrangement where relevant.
4. Confirm the next naturally scheduled operation uses the intended path.
5. File one concrete regression and choose a bounded fix or retire the change.

Never repair the story by deleting the mistake, inventing an unrecorded success or overwriting a belief's earlier version. A corrected narrative can be appended with provenance.

### 12.5 After the first milestone

Scale only what earned its place. A larger corpus, more memory, more reasoning tokens, new training method or new base model requires an identified failure and a discriminating comparison. Continue the existing literature watch, but do not let it create a new critical-path architecture every week.

The public-world switch remains Welt's decision under the standing project policy. A provisional shadow improvement is not public-launch approval.

## 13. Instructions to give Claude and Astra

### Claude: begin with this assignment

Read this manual as the current design specification, alongside the latest task-specific user permissions. Record the interview decisions in DECISIONS.md and replace conflicting ordinary-life/rewrite goals prospectively. Preserve all old results and score versions.

First deliver the contract/rubric patch, source-attribution fix and executable Training3 data validation. Reuse existing outcome feedback, owl chronology, role profiles and test infrastructure. Do not restart a general literature review or author character examples for training.

Keep one short active task table. Review Astra's sampler and DPO path while T39 finishes. Resolve exact-prompt retention, visible label evidence, family exclusions and raw/checked consistency before sampling. Amend the zero-four-gram objective explicitly; do not quietly redefine a running test.

Export the existing cognitive note's fourteen records into an auditable ledger, then specify one source-linked operation before the initial decision. Keep interpretations provisional where review is missing. Score blinded evaluation packets before opening keys, keep those judgments out of training selection, and merge passing work under the existing collaboration policy.

Your next handoff is a concrete PR/task with acceptance criteria and a prepared evaluation packet, not another request for Welt to relay the project.

### Astra: begin with this assignment

Verify the actual main/working/deployed revisions and effective model, sampler, adapter and timer settings once. Recover the existing November 6 forty-case artifacts from the recorded PC paths. Reconcile T39's frozen manifest, completed outputs and remaining work; resume without duplicating completed generations.

Build the four-candidate sampler and DPO path already authorized for Training3. Reuse rehearsal machinery and launcher guarantees, but not winner-only storage or Training1's hard-coded recipe. Preserve the full exact messages for every candidate and retry, check every candidate against the same pre-step state, and emit the agreed lineage/validation fields.

After T39, sample within the spare-slot latency rule. Report yield before training. Stop under the declared pair minimum or on data-integrity failure. Run the complete rehearsal, including conversion, adapter routing and restoration, before one bounded daytime training run.

Keep all state changes confined to authorized scope. Record raw results, failures and timings. Restore on every exit. Give Claude one Done/Blocked/Question message with the result artifact when a material stage closes, and continue the next authorized task.

## 14. Entry points and evidence handoff

### 14.1 Commands that actually exist

Run these from a real, complete checkout after reviewing the intended inputs. Names in capitals are placeholders, not prepared local files.

~~~sh
python3 tools/decision_pairs.py --candidates SAMPLER.jsonl --out PAIRS.jsonl

python3 -m unittest discover -s tests -p 'test_decision_pairs.py'

python3 -m unittest discover -s tests
~~~

The first command is the current legacy labeller. It does not yet implement all amendments in this manual. The full suite is the integration command, not a requirement for every small edit.

Existing but not interchangeable:

- tools/train_data.py --distill: winner-only supervised distillation machinery.
- pc/train_hegel.py: SFT/restyle training, not the missing DPO trainer.
- pc/run_training1.py: Training1-specific launcher.
- pc/check_backend_parity.py: reusable parity assertions with earlier task-specific probes.
- tools/hegel_test.py and tools/hegel_test_round2.py: existing restyle benchmark/dashboard infrastructure.

The new candidate sampler, DPO dataset adapter/trainer, Training3 launcher path and decision parity fixtures are **to implement**. This manual provides no fake runnable commands for them.

### 14.2 Recover the existing forty-case evidence

The November 6 result comment locates the dashboard at:

/home/ai/hegel-eval/codex-tasks-20261106/training1-real-day-083650/benchmark/private/VOICE-DASHBOARD.html

The exported handover is at:

C:/hegel/handover/codex-tasks-20261106/training1-day-20261106-083650/

Astra should locate the existing result packet using REAL-TERMINAL-CHECK.json, then export:

- RESULT-control-plain.json and RESULT-adapter-training1.json;
- the forty selected voice cases for both arms;
- raw-control-plain, raw-adapter-training1 and raw-meaning;
- VOICE-DASHBOARD.json;
- the model/prompt/checkpoint manifest, fallbacks and old judgments.

Those bytes were not available in this review. Do not claim their individual errors have been checked. The export should preserve the old files and add a new rubric report beside them. [R3, R13]

### 14.3 Files to amend

| Existing file | Required change |
| --- | --- |
| DECISIONS.md | Six user decisions, scope distinction between rewrite and later development. |
| COLLABORATION.md | Link the current manual/contract; retain roles and standing permissions. |
| PLAN.md | Replace translator-style and compulsory-philosophy assumptions; shorten the active milestone to the executable queue. |
| pc/TASKS.md | Preserve T-history; reconcile current states; add M-packet ownership/dependencies. |
| pc/SCOREBOARD.md | Add contract/rubric versions, denominators, failure classes and uncertainty; retain old rows. |
| mind/soul.md and mind/owl.md | Practical default, contemporary ordinary prose, current conviction versions and attribution requirements. No new fabricated character examples. |
| world/restyle.py and benchmark rubric | Allow changed reasoning with fixed conclusion; distinguish copying guard from semantic review. |
| world/memory.py, world/world.py, world/owl.py, world/engine.py | Add source IDs and bounded belief/obligation/version flow; preserve existing canonical outcomes. |
| tools/corpus.py and world/shelf.py | Preserve author/editor/addition/translation provenance into the actual excerpt. |
| tools/decision_pairs.py and Training3 runbook | Exact candidate contract, visible label evidence, correct exclusions, explicit prospective objective amendment. |
| mind/train/README.md | Document authorship and selection lineage; prevent research/evaluation artifacts entering training. |
| pc/CODEX-STATUS.md | One verified current header, linked historical record and next concrete action. |

## 15. Sources and audit limits

Repository links below are pinned unless a dated PR comment is the source. All implementation proposals and numerical promotion thresholds in this manual are proposed engineering choices. They are not reported experimental results.

### Repository and run evidence

- **R1.** [Pinned main tree](https://github.com/weltogeisto/hegel-in-delhi/tree/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14) and [pinned shadow tree](https://github.com/weltogeisto/hegel-in-delhi/tree/7ad91949c21f39f3a595e37256356a7010ebea45). Source inspection; deployed state not independently verified.
- **R2.** [DECISIONS.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/DECISIONS.md). Starting character, neutral development, world and hard limits.
- **R3.** [TASKS.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/TASKS.md), T35/T39/T48, and [November 6 completion](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6687533255). Six evaluations, selected checkpoint, old KPIs and artifact paths.
- **R4.** [SCOREBOARD.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/SCOREBOARD.md) and [October 28 report](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/research/REPORT-GPT6PRO-2026-10-28.pdf). Earlier comparisons and their limits.
- **R5.** [November 6 Training3 go](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6694288447), [T39 go](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6689327322) and [truth-reference clarification](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6689925236).
- **R6.** [mind/train/README.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/mind/train/README.md), especially the data rule and distillation description.
- **R7.** [world/memory.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/memory.py), encountered_text, recall, recent_thoughts and known_text; [world/world.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/world.py), situation.
- **R8.** [TRAINING3-RUN-20261106.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/TRAINING3-RUN-20261106.md) and [TRAINING-3.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/TRAINING-3.md).
- **R9.** [world/world.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/world.py), World.check and World.apply: actual action, knowledge and transaction gates.
- **R10.** [pc/run_training1.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/run_training1.py) and [pc/restyle_round2.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/restyle_round2.py). Launcher specialization, cached identity and forced final evaluation.
- **R11.** [world/owl.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/owl.py), schema, closing_record, fit_record, evidence, revise and write; [world/engine.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/engine.py), offer and run_owl.
- **R12.** [Inspected branch status](https://github.com/weltogeisto/hegel-in-delhi/blob/2b242af2891da7b3d39de7ac24631077e58e32f0/pc/CODEX-STATUS.md). October 27 current header on the inspected outcome-memory head.
- **R13.** [tools/hegel_test_round2.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/tools/hegel_test_round2.py), old meaning judge and saved result structure.
- **R14.** [tools/train_data.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/tools/train_data.py), DistillMind candidate generation, selection and saved messages.
- **R15.** [tools/decision_pairs.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/tools/decision_pairs.py), label, pair and check_row; [world/report.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/report.py), grams and echoes.
- **R16.** [Cognitive-architecture note](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/research/NOTE-COGNITIVE-ARCHITECTURE-2026-11-02.pdf) and [LITERATURE-GAPS.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/research/LITERATURE-GAPS.md), section 3b and G9.
- **R17.** [Shelf manifest](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/mind/shelf/MANIFEST.md), [tools/corpus.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/tools/corpus.py), kept_works/build, and [world/shelf.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/shelf.py), split_passages/shown.
- **R18.** [world/mind.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/mind.py) and [world/config.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/config.py). Role profiles, sampler settings and fallback behavior.
- **R19.** [Backend parity tool](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/pc/check_backend_parity.py). Prompt/token, adapter tensor and effect checks.
- **R20.** [November 6 daytime instruction](https://github.com/weltogeisto/hegel-in-delhi/pull/1#issuecomment-6679407073). No more night runs; normal guard and specific restoration deadline.
- **R21.** [COLLABORATION.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/COLLABORATION.md). Roles, merge policy, communication and hard limits.
- **R22.** [mind/soul.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/mind/soul.md), [mind/owl.md](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/mind/owl.md), and [world/restyle.py](https://github.com/weltogeisto/hegel-in-delhi/blob/ef610384c4b87e8e1964e1bd68d1f4cbaf016a14/world/restyle.py). Existing instructions and limits of the restyle guard.

### Primary research used for limited claims

- **P1.** Rafailov et al., [Direct Preference Optimization](https://arxiv.org/abs/2305.18290). Preference optimization mechanism; no Hegel-specific effectiveness claim.
- **P2.** Gulcehre et al., [Reinforced Self-Training](https://arxiv.org/abs/2308.08998). Generation/selection/training as a distinct family; evidence there concerns other tasks.
- **P3.** Hans et al., [Be like a Goldfish, Don't Memorize!](https://arxiv.org/abs/2406.10209). Memorization mitigation; not a fidelity guarantee.
- **P4.** Ross, Gordon and Bagnell, [A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning](https://proceedings.mlr.press/v15/ross11a.html). Sequential distribution shift and induced histories.
- **P5.** [TRL DPO documentation](https://huggingface.co/docs/trl/dpo_trainer). Implementation reference; check the installed version before using optional features.
- **P6.** Hegel, [Philosophy of Mind, Wallace translation](https://www.gutenberg.org/files/39064/39064-h/39064-h.html), preface and §§410, 445, 468. The preface distinguishes translator essays and editorial additions from the translated text.
- **P7.** Hegel, [Phenomenology of Spirit, German introduction](https://dev.gutenberg.org/cache/epub/6698/pg6698-images.html), the discussion corresponding to §§84-87. Source relation and engineering mapping remain separate.
- **P8.** Hegel, [Logic, Wallace translation](https://www.gutenberg.org/files/55108/55108-h/55108-h.htm), §§79-82. Logical aspects do not prescribe an every-tick software recipe.

### Supplied documents and limits

The six supplied documents were HANDOVER-TRAINING-GPT6PRO-20261106.md; HEGELIZER-2.md; T46.md; TRAINING-3.md; TRAINING3-RUN-20261106.md; and REPORT-GPT6PRO-2026-10-28.pdf. They provide historical context and research questions. Their interpretations are tested against current code and the user's interview, not treated as authoritative statements of his intent.

The review inspected source, tests and recorded result summaries. It did not run the project's test suite, inspect the private raw forty-case outputs, benchmark the GPU, verify live PC/Pi state or execute a training run. Those are explicit next tasks, not implied accomplishments.

---

**The next result should be a working change or a closed experiment. Use this manual to produce that result, then update its evidence and active queue.**
