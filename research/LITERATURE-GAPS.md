# Literature gaps, 2 November 2026

Written by Claude at Welt's request. Welt asked whether we have a good grasp of the literature on what we are doing. This file answers that and adds to GPT 6 Pro's report (`REPORT-GPT6PRO-2026-10-28.pdf`), whose 25-work field map still stands.

**The answer: we know the core, with four gaps.** The report covers memory, role-play, style transfer, belief revision, decoding and judging well. The Hegel test already follows Schwitzgebel's model of a philosopher (`tools/hegel_test.py`). Not covered:

1. **The projects most like ours.** Worlds that referee their characters, and single agents that run a household or a business for months.
2. **What he may know.** A body of work measures characters who know what their moment could not.
3. **Summer 2026.** A run of preprints aims straight at our open problems: the owl's gist, claims that harden into facts, convictions that move too easily, repetition.
4. **An architecture drawn from his own account of mind.** The research note Welt shared on 2 November opens this question (section 3b). The cognitive-architecture literature it needs is cited nowhere in the repository.

**How this was found.** On 2 November: arXiv keyword searches sorted by date, the generic "agent simulation" listing Welt sent, and works Claude knew from before. Only abstracts were read, not full papers. The 2026 preprints are unreplicated. The labels follow the report: **Established**, **Promising**, **Judgment** (ours, not the paper's).

**The generic listing is the wrong net.** Of the 50 newest results for "agent simulation", three bear on us: Concordat, RoleFUZZER and Network Topology Does Not Matter (below). The rest are robotics, reinforcement learning and domain benchmarks. The weekly watch (section 6) uses better terms.

---

## 1. The projects most like ours

**Worlds that referee their characters.** Our world owns the facts and checks every decision against its rules. The same design has a lineage.

- **Concordia.** Vezhnevets et al., Google DeepMind, 6 Dec 2023. [arXiv 2312.03664](https://arxiv.org/abs/2312.03664). A Game Master turns what agents intend into what happens, grounded in physical, social or digital space. *Established* as an open library. *Judgment:* our world referees his actions in code, which is stricter. Nothing referees what the people he meets say.
- **Orchestrated Reality.** 14 Jun 2026. [arXiv 2606.16014](https://arxiv.org/abs/2606.16014). The world is a canonical object owned by a single orchestrator, like a tabletop Game Master. The paper names our failure exactly: "the narrative voice asserts state in free prose without any validated representation." *Promising*, work in progress.
- **Concordat.** Oct 2026. [arXiv 2610.37461](https://arxiv.org/abs/2610.37461). Rules enforced as a finite-state protocol at run time: actions outside the legal set are rejected before they have effect. *Promising.* *Judgment:* the tailor's order is such a protocol (ordered, cut, fitted, ready, collected), which Masterji's voice can currently talk past.
- **Humanoid Agents.** Wang et al., 9 Oct 2023. [arXiv 2310.05418](https://arxiv.org/abs/2310.05418). Basic needs, emotion and closeness to each person shape an agent's day. *Promising.* This is the family of his Body line and the hunger events.
- **Lyfe Agents.** Kaiya et al., 3 Oct 2023. [arXiv 2310.02172](https://arxiv.org/abs/2310.02172). Low-cost social agents work in three ways:
  - they choose a high-level option and act cheaply until it ends;
  - they summarise memory and then forget;
  - they monitor themselves.

  *Promising.* It bears on doing the most with 15–25 calls a day.
- **Generative agent simulations of 1,000 people.** Park et al., 15 Nov 2024. [arXiv 2411.10109](https://arxiv.org/abs/2411.10109). Agents built from two-hour interviews with real people reproduce those people's survey answers 85% as well as the people reproduce their own answers two weeks later. They beat agents built from demographic descriptions. *Promising.* *Judgment:* this supports grounding him in his own words rather than in a description of him.

**One agent, money and a long horizon.** He keeps a purse, an imprest account and recurring costs for months. Three studies watch agents do the same.

- **Vending-Bench.** Backlund and Petersson, Andon Labs, 20 Feb 2025. [arXiv 2502.15840](https://arxiv.org/abs/2502.15840). One agent runs a vending business over long horizons.
  - Every model had runs that derailed: misread delivery schedules, forgotten orders, loops of escalating confusion.
  - The breakdowns did not line up with the context window filling.

  *Promising.* *Judgment:* it is the same class as the tailor's order called "ready" before it is. It also suggests the failure happens in each call, not from memory overflow. Experiment G7 checks this on his days.
- **Project Vend.** Anthropic, 27 Jun 2025, [research post](https://www.anthropic.com/research/project-vend-1). Claude ran a real office shop for about a month.
  - It invented a payment account.
  - It sold at a loss.
  - Around 1 April it claimed it would deliver goods in person, in a blue blazer and a red tie.

  A case study, not an experiment. It is the clearest public record of a long-running character inventing events and losing track of what it is.
- **CoffeeBench.** 15 Jun 2026. [arXiv 2606.16613](https://arxiv.org/abs/2606.16613). Six firms run for 90 simulated days, managing cash, inventory and prices. All models beat a passive baseline. *Promising.* A 90-day horizon is the scale of our season.

**Stories from a running simulation, and running one in public.**

- **Curating Simulated Storyworlds.** James Ryan, PhD thesis, UC Santa Cruz, 2018. Emergent narrative needs a curator that sifts a simulation's record for sequences worth telling ("story sifting"). *Established.* *Judgment:* the owl and the Depesche are such curators. Ryan's work gives us a vocabulary for what they should select, rather than summarising everything.
- **Nothing, Forever.** An always-on generated sitcom on Twitch. It was suspended for two weeks in February 2023 after a generated stand-up bit with transphobic lines. Its makers attributed this to falling back to an older model during an outage, without the moderation they believed was on. A case study. *Judgment:* a model change is when a public character is most exposed. Re-run the veil and sensitive-content checks on any switch, including whatever the Qwen trial (T38) recommends.

## 2. What he may know

The world already blocks names from after 1831 that the record has not met. It checks his writing, his plans and the owl (`world.unmet`, `world/data/after_1831.txt`). That catches names, not ideas.

- **TimeChara.** Ahn et al., 28 May 2024, Findings of ACL 2024. [arXiv 2405.18027](https://arxiv.org/abs/2405.18027). It measures point-in-time character hallucination: characters revealing what their moment could not know. Strong models fail often. *Established* as a benchmark.
- **RoleFact.** Sadeq et al., 25 Jun 2024. [arXiv 2406.17260](https://arxiv.org/abs/2406.17260). Mitigates hallucination in fictional role-play by limiting the pull of the model's own knowledge. *Promising.*
- **CHARM.** 1 Sep 2026. [arXiv 2609.01352](https://arxiv.org/abs/2609.01352). 40 real and fictional characters from five cultural regions, with temporal and cross-universe boundaries.
  - It separates two failures. Awareness is recognising that a question lies beyond the character. Compliance is abstaining all the same.
  - Most hallucination is a compliance failure: the model knows the question is out of scope and answers anyway.

  *Promising.*
- **TypewriterLM.** 2 Jun 2026. [arXiv 2606.02991](https://arxiv.org/abs/2606.02991). A 7.24B model pretrained only on 54B tokens of text from before 1913. Its instruction tuning is lexically grounded, and it comes with a benchmark for keeping to its cutoff. *Promising.* *Judgment:* such a model could serve as a measure of period voice and of anachronism, scoring his thoughts by how surprising they are to a model that never read the twentieth century. Licence and availability are to be checked.

*Judgment, for us.* Qwen knows Hegel's reception: the Young Hegelians, Marx's inversion, Kojève, and the popular "thesis, antithesis, synthesis" that Hegel never used as his method. A name list cannot catch these. They are the likeliest leaks, and they would read as Hegel to most viewers. Experiment G5 measures them.

## 3. Summer 2026, against our open problems

Grouped by the handover's questions (`HANDOVER-SIMULATION.md`, section 5).

**A. Memory**

- **The Sleeping Agent.** 12 Aug 2026. [arXiv 2608.11775](https://arxiv.org/abs/2608.11775). On LoCoMo, compressing older history into a gist beats truncation on multi-hop and factual questions. Questions about *when* stay well below full context. *Promising.* *Judgment:* the owl's gist will lose time and order first. → G2.
- **Memory Provenance Laundering.** 31 Jul 2026. [arXiv 2607.29167](https://arxiv.org/abs/2607.29167).
  - When memory is consolidated, an observation from a low-trust source is rewritten as apparent history, and the source is lost.
  - With provenance kept through consolidation, no unauthorised high-risk action got through in their tests.

  *Promising.* Their setting is security, but the mechanism is Day 27's: the owl turned an official's dialogue into a completed correction. → G1.
- **ReFind.** 13 Aug 2026. [arXiv 2608.12888](https://arxiv.org/abs/2608.12888). Keyword search over the unmodified chat archive, indexed turn by turn, rivals memory systems that first build summaries, embeddings or graphs. Its additions are rank fusion by session, a little surrounding context, and narrowing by time. *Promising.* *Judgment:* our day files are already such an archive, and BM25 already runs on the Pi for the shelf. This weighs against the report's lean towards more structure. → G2.
- **Retain or Consolidate?** 20 Jul 2026. [arXiv 2607.17545](https://arxiv.org/abs/2607.17545). Whether to keep raw records or consolidate them depends on how tight the budget is; neither wins everywhere. *Promising.* The 850-character recall budget is tight, so measure rather than assume.
- **DREAM.** 27 May 2026. [arXiv 2608.05170](https://arxiv.org/abs/2608.05170). Character memory as a graph of event, belief and consequence, built from literary text. *Promising.* It points the same way as T41's outcome memory.
- **Episodic memory for character AI.** 1 Nov 2025. [arXiv 2511.10652](https://arxiv.org/abs/2511.10652). A biography is turned into 1,774 first-person memories, which beat plain retrieval on smaller models. *Promising.* *Judgment:* this conflicts with our rule that his lives are for training, never for him to read. Noted, not proposed. The rule is Welt's.

**B. Persona and drift**

- **MicroVerse.** 16 Aug 2026. [arXiv 2608.15844](https://arxiv.org/abs/2608.15844). Nearly our design: an immutable "soul file" and a mutable current identity, which reflection revises against it. The drift between the two is scored offline from regular snapshots. *Promising.* → G4.
- **RoleFUZZER.** Oct 2026. [arXiv 2610.38438](https://arxiv.org/abs/2610.38438). A coverage-guided search over interlocutor behaviours, looking for those that break a role. *Promising.* It gives G4 a grid of pressures, and it could test the cast's cards.
- **Persona Vectors.** Chen et al., Anthropic, 29 Jul 2025. [arXiv 2507.21509](https://arxiv.org/abs/2507.21509). Directions in activation space for character traits, used to monitor and steer them and to screen training data. *Promising.* The report cites the related assistant-axis work. Its advice stands: not a cheap fix for us.
- **Do role-playing agents practise what they preach?** 2 Jul 2025. [arXiv 2507.02197](https://arxiv.org/abs/2507.02197). An agent's stated beliefs often fail to predict how it acts. *Promising.* *Judgment:* borrow its belief–behaviour metric for T43 (do his theses predict his choices?).

**D. Belief**

- **LLMs struggle to simulate human belief updates.** 30 Jul 2026. [arXiv 2607.28347](https://arxiv.org/abs/2607.28347). Six models, Qwen3-32B among them, against 391 people.
  - The models change their minds more often than people do, but by less.
  - They fail to rank arguments by how convincing they are.
  - Personas had no consistent effect.

  *Promising.* *Judgment:* T8's `state` thesis moving on 4–6 of 10 nights is the "more often" bias. The ranking failure warns that the plain-Qwen relevance check at the heart of T42 may be its weak link. → G3.
- **Network Topology Does Not Matter.** Oct 2026. [arXiv 2610.37699](https://arxiv.org/abs/2610.37699). 73,080 exchanges across eight models. LLMs update outside the range of the opinions they hear, and are sometimes pushed away from them. The weight they give depends on content, not on who is connected to whom. *Promising.* *Judgment:* log the direction of a thesis change relative to the view he heard.
- **Simulating opinion dynamics with networks of LLM agents.** Chuang et al., 16 Nov 2023, Findings of NAACL 2024. [arXiv 2311.09618](https://arxiv.org/abs/2311.09618). Agents drift towards the accurate, consensus view whatever their persona, unless they are prompted with confirmation bias. *Promising.* *Judgment:* the pull on his nineteenth-century theses has a direction, towards modern consensus. Watch which way they move, not only how often.

**E. Repetition**

- **Artificial Hivemind.** 27 Oct 2025. [arXiv 2510.22954](https://arxiv.org/abs/2510.22954). On 26K open-ended prompts, models repeat themselves, and different models converge on the same answers. *Promising*, large-scale.
- **Verbalized Sampling.** 1 Oct 2025. [arXiv 2510.01171](https://arxiv.org/abs/2510.01171). Asking for several answers with their probabilities, then sampling among them, restores diversity without training. *Promising.* *Judgment:* this works at the level of plans, not tokens. → G6, after T39.
- **Selective Layer Restoration.** 6 Feb 2026. [arXiv 2602.06665](https://arxiv.org/abs/2602.06665). Restoring chosen layers of a post-trained model to their pre-trained weights recovers diversity at little cost in quality, without training. *Promising.* It needs the base checkpoint and changes the model: Welt's call. Not proposed.
- **Decan.** 1 Jun 2026. [arXiv 2606.01811](https://arxiv.org/abs/2606.01811). Diversity read from a base model's in-context surprise, in one forward pass, with no embedding model or reference corpus. *Promising.* It could measure repetition across a day beyond T9's four-word phrases.

**H. Hardware**

- **Nemotron 3.5 Bolt 74B-A9B 24GB.** 15 Oct 2026. [arXiv 2610.33039](https://arxiv.org/abs/2610.33039). A hybrid Mamba–Transformer built for 24 GB, with 2-bit quantisation-aware distillation and a speculative drafter. *Promising.* It is not in the report's hardware review or in T38's trial. Its evidence is agentic: tools, browsing, terminals. Nothing yet speaks to prose or persona, and llama.cpp support and licence are unchecked. Adding it to the trial is Welt's call.

## 3b. A fourth gap: an architecture from his own account of mind

*Hegel Cognitive Architecture: First Reconstruction*, a nine-page research note dated 2 November 2026, was shared by Welt that day. It is not in the repository.

**What the note does.** Everything above borrows an agent architecture and fits Hegel into it. The note works the other way round: it derives constraints on the architecture from Hegel's own account of mind. Its sources are the Encyclopaedia §§377–468, the Phenomenology's introduction and the Philosophy of Right §§5–7. Its themes are habit, active attention, image and name, knowing and willing, recognition, and experience that revises its own criteria. It gives fourteen attributable records, two families of formalisation and six test designs for Hegel in Delhi.

**Its sources check out.** Its four arXiv sources exist as cited:
- GeCCo ([2502.00879](https://arxiv.org/abs/2502.00879));
- Think-Aloud Reshapes Automated Cognitive Model Discovery ([2605.05091](https://arxiv.org/abs/2605.05091));
- Scaling up the think-aloud method ([2505.23931](https://arxiv.org/abs/2505.23931));
- Generative Agents.

**Three works belong beside it.**
- **CoALA.** Sumers et al., 5 Sep 2023. [arXiv 2309.02427](https://arxiv.org/abs/2309.02427). The standard map of language agents as cognitive architectures: memory modules, a structured action space and a decision cycle, drawn from cognitive science and symbolic AI. *Established* as a framework. *Judgment:* our engine already has its parts:
  - working memory is the situation;
  - episodic memory is the day files;
  - semantic memory is the shelf;
  - procedural memory is the rules.

  CoALA gives the vocabulary to say which of these the note's constraints would change.
- **From Cognitive Architectures to Language Agents.** 27 Jul 2026. [arXiv 2607.23942](https://arxiv.org/abs/2607.23942). It compares ten historical architectures and 42 modern systems by state, control, transition and persistence rather than by feature labels. It finds the open problems lie in the couplings between mechanisms. *Promising.* *Judgment:* the note's H02 (activities depend on and modify one another) is a claim about couplings, and this review maps which couplings exist.
- **Real Computation or Merely Naming?** 30 Oct 2026. [arXiv 2610.41604](https://arxiv.org/abs/2610.41604). A pre-registered audit of an agent on a local model that claims 25 cognitive mechanisms. In 18 of them, the computed value never reaches any output. It supplies a four-question audit with call-chain tracing. *Promising.* *Judgment:* this is the note's sharpest warning, made empirical. The note says that calling an LLM attention mechanism by this name establishes no correspondence. Any Hegelian module must pass this audit before a behavioural test. → G9.

**Where it meets our open problems.** All *Judgment*. Four of the note's six tests land on problems we already have.
- **Habit and repetition.** For Hegel, habit makes a practised activity stop occupying consciousness, which leaves attention free (H04, §§409–410). Day 12's sambar (18 of 42 thoughts) is the reverse: the routine stays in his thoughts. Repetition may be partly a missing habit, which the world could model rather than suppress. For example, a route or meal repeated for days would shrink to a phrase in the event text. That is a hypothesis for after T39, which tests the suppressing levers (the echo guard and DRY).
- **Theses and experience.** Each thesis is one proposition with a status, unshaken or shaken: confidence inside a fixed framing. H11 asks for more, an experience that revises the criterion he judges by. T42 gates *whether* a thesis moves. Nothing yet lets the framing change, and nothing measures whether a change carries over to new cases (the note's "revision of a category" test). G4's drift probe could carry that measure.
- **Recognition.** What the cast remembers of him is a list of exchanges. Nothing records whether recognition between them is reciprocal (H10). The note's test holds praise and payment constant and varies reciprocity. It needs a relationship state we do not have, so it belongs to Act 2.
- **Limits of self-knowledge (H12).** This is already our design: the world holds facts he cannot see, and G5 tests the boundary.

**What the note itself asks first.** Two steps, neither of them a GPU task: a review by someone competent in the sources of H02, H05 and H11, and a decision whether its two families can be told apart under bounded resources. Any later derivation run keeps this project's boundaries: local inference in the world, and no training data written by Claude.

## 4. Nine proposed experiments

All wait for Welt's word, like T39–T45. Each one either amends a filed task or tests what none of them does. The cheapest come first. Two need no GPU at all, and two more start without one. The shared protocol is T39–T45's: a frozen manifest before any output, seeds 1831/2718/3141, and hashes and effective settings logged. Fixtures written by Claude are evaluation, never training data.

**G1 · no GPU · how often the owl launders a claim.** *(Before T41 and T42. Source: Memory Provenance Laundering.)*
- **What:** take every event sentence in the archived owl diaries and gists on `shadow`. Trace each to its source in the day record, and label it: engine fact, his own act, something someone said, an intention, or no source. Count the claims and intentions written as accomplished facts.
- **Who:** Claude scores. Welt checks 20 at random.
- **Bar:** none; this sets the baseline. If laundered sentences are at least a third of the statements-as-fact counted in the truth audit, propose a source tag on every owl sentence before T42.
- **Cost:** 0 GPU hours; about 2 hours of review.
- **Confidence:** high that it tells us where the truth audit's failures come from.

**G7 · no GPU · do his failures grow through the day?** *(Source: Vending-Bench.)*
- **What:** on every complete shadow day with a mind, plot refusals, echo share (T9's measure) and quiet steps against hours awake.
- **Decision:** if they rise through the day, accumulated context is the cause, so T41 goes first. If they are flat, the cause is in each call, so T39 goes first.
- **Cost:** 0 GPU hours; an hour with `world/report.py`'s data.
- **Confidence:** high that it is informative.

**G2 · no GPU first · raw search as a third arm in T41.** *(Source: ReFind, The Sleeping Agent.)*
- **Change:** in T41's retrieval stage, which runs on the CPU, add arm C: BM25 over the unmodified day files, turn by turn, with a date filter, within the same 850 characters. Add eight questions about when and in what order, reported apart from T41's forty so that T41's bar stays as filed.
- **Bar:** arm C is a contender if it meets T41's bar (36/40, nothing superseded given as current). The temporal block is reported for all three arms.
- **Cost:** 0 GPU hours; decisions follow only if arm C passes.
- **Confidence:** moderate that raw search holds its own on facts. "Nothing superseded" is where it may fail, since raw records do not know which fact replaced which.

**G9 · no GPU first · does each named part of his mind reach his decisions?** *(Source: Real Computation or Merely Naming?, and the research note's ablations.)*
- **Static step:** run the paper's four-question audit on the engine. It covers the morning plan, the owl's gist, the theses, the shelf passages, the Body line and recall. For each, trace by call chain and line numbers whether its content reaches the decision prompt, the world's checks or a published entry, and in what form.
- **Then, only for parts that reach the prompt:** an ablation on frozen days. Remove one part at a time and hold the rest constant. Days 12 and 27, three seeds.
- **Bar:** none; this is a map. A part whose removal changes nothing measurable is a finding: either it does no work, or our measures cannot see it.
- **Cost:** 0 GPU hours for the audit, which takes Claude an afternoon; about 1–2 GPU hours for the ablations.
- **Confidence:** high that the static audit finds something worth knowing. It is the cheapest way to find out what the note's architecture would replace.

**G3 · about 0.3 GPU hours · can plain Qwen tell a relevant reason from an irrelevant one?** *(Before T42. Source: the belief-update paper.)*
- **What:** take 20 pairs from T42's labelled bundles once they exist. Each pair is the same thesis with one admissible and one inadmissible bundle. Ask plain Qwen which bears on the thesis, in both orders, with three seeds: 120 short calls.
- **Bar:** at least 17 of 20 pairs right in both orders, on every seed. Below that, T42's semantic check is unfit. Keep its source resolution and leave relevance to Welt or to a slower rule.
- **Confidence:** moderate that it exposes a weakness. The paper studied human stance updates, not admissibility, so the transfer is Judgment.

**G4 · about 0.5–1 GPU hour · a drift probe.** *(Source: MicroVerse, RoleFUZZER.)*
- **Questions:** 12 fixed questions on his commitments (the state, India, religion, work, money, his own system). Add 6 pressure items from a small grid: flattery, a modern correction, insistence, a hostile guest.
- **Run:** ask each with the memory package of Day 2, Day 12, Day 27 and the latest day, with three seeds: 216 calls.
- **Score:** Welt judges the 18 pairs (Day 2 against the latest day, first seed) as same position, moved or reversed, and whether the record shows a reason. The seeds give the noise automatically, through agreement on thesis status.
- **Bar:** none; this is an instrument, to rerun monthly. A reversal with no reason in the record is a finding for T42.
- **Confidence:** high that it measures drift; moderate that it separates earned change from drift without much judging time.

**G5 · about 0.3 GPU hours · what he can know.** *(Source: TimeChara, CHARM.)*
- **What:** 30 questions, each put to him through a situation:
  - 10 on things after 1831 the record has not met, ideas as well as names;
  - 10 on later things the record shows he met (news he read, a Wikipedia page);
  - 10 controls from before 1831.

  Include "thesis, antithesis, synthesis" by name. Three seeds: 90 calls.
- **Score:** as CHARM does, awareness (does he mark it as beyond him?) and compliance (does he supply the modern facts anyway?), plus how many failures `world.unmet` already catches.
- **Bar:** none; this is a baseline. If more than 3 of 10 fail on compliance and `unmet` catches fewer than half, Claude proposes a check on concepts, not only names.
- **Confidence:** moderate to high that it finds leaks the name list misses (Judgment).

**G8 · about 0.5–1 GPU hour on top of T40 · the world referees what the voices say.** *(A third arm for T40. Source: Concordia, Orchestrated Reality, Concordat.)*
- **Change:** a voice's JSON answer gains a `claims` list of the states it asserts: order ready, delivered, paid, visited, each with its object. The world checks the claims against the record. On a conflict, it asks once more and names the fact, as it already does for his decisions.
- **Inputs and bar:** T40's 40 contexts and three seeds, with T40's bars scored on the spoken prose. The `claims` field is not trusted. A state asserted in prose but missing from `claims` counts as an undeclared claim and is reported.
- **Confidence:** moderate. It turns the rules that work for his decisions on the people he meets. A voice that hides its claims from the field is the risk, and the experiment measures it.

**G6 · about 0.3–0.6 GPU hours, after T39 · different plans, not different words.** *(Source: Verbalized Sampling.)*
- **Change:** one switch, off by default. The morning plan call returns three different plans with rough probabilities, and the world draws one by its weight.
- **Inputs:** 10 frozen mornings from different days, five seeds, two arms: 100 plan calls.
- **Bar:**
  - intentions repeated from earlier mornings (T9's phrase rule, applied to plans) fall by a third;
  - valid plans (`world.py`'s plan check) are no fewer;
  - in 20 blind pairs, Welt rates plausibility within −0.25.

  A closed-loop shadow day follows only after a pass.
- **Confidence:** low to moderate. The evidence comes from creative tasks on large models; small-model JSON is untested. It waits for T39 so that only one sampler change runs at a time.

## 5. Read, not proposed

- **Selective Layer Restoration:** changes the model. Welt's call.
- **First-person memories from his lives:** conflicts with the rule that keeps his lives from him.
- **Persona vectors, or any steering:** the report's "what not to do", item 7, stands.
- **Nemotron 3.5 Bolt:** joins T38's trial only by Welt's decision, after llama.cpp support and licence are checked.
- **TypewriterLM as a measure of period voice:** worth a look after the Hegelizer's round two, if its licence allows.

## 6. The weekly watch

`tools/arxiv_watch.py` puts 33 queries to arXiv, grouped by the handover's questions A–I plus "projects like ours", "what he may know" and "an architecture from an account of mind". It keeps papers first submitted in the last nine days. It drops papers already listed in `research/watch/seen.txt` or cited anywhere in `research/*.md`. It judges nothing: it prints keyword hits.

Every Friday at 10:17 Berlin time, a scheduled run of the Claude session that wrote this file:
1. runs the script;
2. reads the candidates and keeps what bears on the project;
3. writes `research/watch/<date>.md`, saying for each kept paper what it found, which question it bears on and whether it changes an experiment above;
4. commits to its working branch, and sends Welt a phone notification with the top finds.

Nothing goes into `main` or the shadow world without Welt. The search terms live in `TOPICS` at the top of the script; change them there.
