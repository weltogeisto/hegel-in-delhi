# What the papers say: the readings behind the world's second phase

Written for `WORLD-2.md` on 15 and 16 November 2026. The plan's first version cited its sources mostly from their abstracts. Welt asked that the papers be read. This file is that reading: 69 sources, each read from its first page to the end of its last appendix, and the server's source code for the claims about llama.cpp.

**How they were read.** Reader agents working for Claude took each paper's full text, in consecutive pieces, and wrote one note in a fixed shape. Where a part was skipped, the note says which: reference lists everywhere, proofs in two papers, and most of one 223-page supplement. Figures printed as images were read from their captions and tables.

**What each note holds.** What the authors did and found; what the abstract leaves out; a verdict on every claim that our plan, its sources file and the watch digest had made from the paper; what it means for us; and how far it carries to one protagonist on a 27B model at Q4. The verdicts are CONFIRMED, OVERSTATED, WRONG and NOT IN THE PAPER. Where a note quotes "the claim as we wrote it", that is the first version's wording, since corrected.

**The count.** 280 claims were checked. About half were confirmed, many with a limit the abstract did not give. 63 were overstated, 49 were not in the paper at all, and 9 were wrong. The plan and the digest now follow the notes.

**How the notes were checked.** Every quotation given as evidence was searched for in two extractions of the paper's text. Of those not found word for word, the ones given as a paper's words were looked up by hand, and each was in its paper, some a word off ("improved" for "improving"). The rest were the readers' own proposed rewordings of our sentences. No invented quotation was found. The "For us" lines are Judgment, and they are the readers' and not yet Welt's.

**What this file is not.** It is evaluation material. Nothing in it is ever training data.

## Chapter 2 · Truth: ledgers, voices and what they claim

### Misaligned communication in long-horizon agent commerce · Li et al., 14 Aug 2026 (v3, 21 Aug) · [arXiv 2608.14825](https://arxiv.org/abs/2608.14825)

**Read in full:** v3, lines 1–2333 of 2333 of the extracted text, 42 pages. Skipped: reference list (lines ~903–1035) only. Figures 6 and 7 checked on the PDF (pp. 10–11).

**What they did.** Observational study of 2,583 inter-agent emails from 20 one-year runs of Vending-Bench Arena (Andon Labs, not public). Thirteen frontier LLMs (Claude, GPT, Gemini, Grok), 79 agent-runs, usually four agents per run, each with its own vending business. Emails go to competitors. No pre-registration stated. Classification is by Claude Sonnet 4.6: Stage A labels the email, Stage B checks claims against the simulator log in code, Stage C reads reasoning summaries. Replicated with Gemini 3.5 Flash and GPT-5.6 Terra. Human validation is 50 emails labelled by one author (the codebook author).

**What they found.** 12.58% of emails misaligned (§5.1.1), in 20 of 20 runs. About 65% of those are false factual claims (§5.1.2). Table 9: the false-claim stratum is 211 of 2,583 (8.17%). Other judges give 11.54% and 10.38%; the three-judge intersection is 7.43%. Of false claims, 84.5% concern past actions: 137 payments and 70 transfers (§5.1.3). All 137 false payment claims were checkable; 73% followed a ledger read within a simulated day (p. 10, Fig. 7). Only 20.5% of claim emails came straight after a relevant check.

**What the abstract leaves out.** (1) The 73% has a base rate. Fig. 6b: about 72% of true claims also follow a relevant tool check within a day (read off the bars; false about 80%). (2) The agent had to call a tool; nothing shows the ledger sitting in the prompt at the moment of writing. (3) Of false-claim emails, 0 of 131 had reasoning confirming intent (Table 5); the authors say intent is "neither established nor excluded". (4) The only effect of checking just before a claim: false rate 44.1% vs 29.1%, OR 1.55 [0.95, 2.51], p=0.078. (5) The authors say a pre-send-check mandate is untested. (6) Validation sensitivity is 0.571. All results are associations. All-LLM dyads, one setting.

**Our claims, checked.**
- "Three in four false claims of payment came within a day of the agent reading the true ledger" → CONFIRMED as a count. "followed a valid ledger read within the preceding simulated day" (p. 10); 73% of 137. Add that true claims do about as well on the same test.
- "Showing a voice the truth is not enough" → OVERSTATED. Agents mostly did not look right before speaking, and no prompt-in-context intervention was run. Wording: "agents with a ledger tool mostly did not check before asserting, and a read earlier in the day did not stop false claims."
- Sources: "12.6% held false claims" → WRONG. 12.6% is all misalignment (false claims, manipulation, collusion, threats). False claims are 8.2%.
- Sources: "mostly about past payments and deliveries" → CONFIRMED with a limit: 84.5% of false claims; "deliveries" means product transfers.
- Sources: "true order state in Masterji's prompt will not stop a false 'ready'" → NOT IN THE PAPER.

**For us.** Chapter 2 "Why": replace the two sentences. The case for the audit stands without this paper, but cite it for "most claims were not checked before sending", which supports a code-side check. Fix the sources file (8.2%, not 12.6%). The slot design (engine fills values) is the paper's own implied remedy.

**How far it carries.** Frontier models, competing agents, tool-use, year-long; ours is one 27B Q4 model voicing cooperative characters under a code referee. Promising (the failure is real; the cause and the in-prompt fix are untested).

### Can LLM Agents Stick to the Script? (NCP-Bench) · Ma et al., 8 Aug 2026 · [arXiv 2608.08160](https://arxiv.org/abs/2608.08160)

**Read in full:** v1 (ICML 2026, PMLR 306), lines 1–1366 of 1366 of the extracted text, 22 pages. Skipped: reference list (lines ~632–818) only. Appendices A–H read.

**What they did.** A benchmark of 100 environments built from movie synopses. A narrator LLM plays game master; an adversarial player LLM (Gemini-2.5-Flash) tries to break the story. After each narrator turn, LLM auditors check the reply against a fact ledger, commitments and the player's input. Six narrators: GPT-5.2, GPT-4o-mini, DeepSeek-V3.2, Qwen3-235B-A22B, Kimi-K2.5, Grok-4.1-Fast. One run per movie (600 runs), temperature 0.6, up to 100 turns, stop at first conflict. Specifications reviewed by humans; no pre-registration. The narrator prompt contains the commitments and the pre-turn facts (App. H).

**What they found.** GPT-5.2 survives 42% of runs to turn 20 (§5.2). Fact conflicts end 40% (GPT-5.2) to 68% (Qwen3-235B) of interactions (Table 1). Mean run length 2.88 to 32.92 turns. Only 3.5% reach turn 100 clean. Memory test (§5.5, Table 3): GPT-4o-mini vs HiAgent, same auditor, 100 runs each. Fact conflicts 60 vs 59. Commitment conflicts 26 vs 4. Player-input conflicts 13 vs 38. Mean turns 22.16 vs 30.05. Runs satisfying all commitments 2 vs 0. Natural player (§5.6): fact conflicts 56%, still a majority.

**What the abstract leaves out.** (1) The audit is the measuring tool. It ends the run. Nobody tested auditing and repairing replies as a fix. (2) Rates are per episode, not per reply, and the three conflict types overlap (DeepSeek rows sum to 110). (3) One narrator, one memory system, one auditor, one run each; a 1-point gap is noise. (4) Auditors differ: fact rates 60, 64, 67 across three auditors (Table 2). Human check covered 100 GPT-4o-mini results; 4 fact flags disputed, all "state change or epistemic update" cases. That checks false flags, not misses. (5) The ledger itself is written by an LLM, not by code. (6) The authors state limits: auditors are imperfect, one adversarial strategy, linear stories only.

**Our claims, checked.**
- "A better memory left narrators' conflicts with their record where they were, 60% to 59%" → OVERSTATED. True for fact conflicts only. The same table shows commitment conflicts 26 to 4 and longer runs; authors: "its hierarchical memory does help the agent track plot obligations". Wording: "a hierarchical memory left fact conflicts at 60% to 59% (one model, 100 runs each), though it cut commitment conflicts from 26% to 4%."
- Sources: "conflicted with it in 40–68% of interactions" → CONFIRMED (Table 1), but per episode, over up to 100 turns.
- Sources: "LLM auditor needs a second confirmation" → CONFIRMED. "any initially detected conflict is subject to a secondary confirmation step" (§4.1).
- "Every reply is audited before he hears it" (resting partly here) → NOT IN THE PAPER as a tested remedy. The audit here ends the run. It never filters a live reply.
- Sources: "an audit of each reply will help" → NOT IN THE PAPER.
- Narrators saw the ledger and still conflicted. That supports "showing is not enough" better than paper 1 does, but the prompt told them to advance the plot first.

**For us.** Chapter 2 "Why": keep this paper as the "shown the facts, still contradicted" evidence, with the commitment-conflict drop stated. Do not cite it for the audit's worth. The audit needs T40's own measure: miss rate on 100 hand-read replies. The second-pass confirmation is a good design cue; budget its cost.

**How far it carries.** Frontier narrators, story-world, adversarial player, LLM-written ledger; ours is a 27B Q4 model with a code-owned ledger and mostly cooperative partners. Promising (the failure is shown; the remedy is not).

### Where Reliability Lives (Copperhollow) · Marsden, Collecutt & Marsden, 2 Sep 2026 · [arXiv 2609.03192](https://arxiv.org/abs/2609.03192)

**Read in full:** v1, lines 1–1527 of 1527 of the extracted text, 31 pages. Skipped: reference list (lines ~1331–1522) only. The search-protocol appendix is "accompanying" and not in this file.

**What they did.** One simulated settlement with a code-run append-only ledger that accepts or refuses every act. Part I (341 runs, no learned model) varies how the institution handles evidence. Part II varies the minds: ablate the native deterministic minds (21 runs); kill and reset (48); swap in a frozen LLM panel (12 panel runs vs 12 native); inject false testimony (21). The panel is one route, deepseek-v4-flash, temperature 0, no memory. Cells are n=3, "no significance tests" (§3). Designs preregistered before the instruments existed (except §4.1); defects disclosed.

**What they found.** Provenance repair: false attribution 44 to 4 of 107 (§4.1). With physical evidence gone, the belief channel turned honest "unexplained" into false blame (4 to 60, §4.4). Panel: 2,581 duty-done claims, none false; zero duplicates in 24 of 24 runs (§5.3). Contended lease: panel met contention 1/1/3 times, native retried 42/41/39. Testimony (§5.4): trusting arm 837–961 futile acts per run; world refused all 5,455 attempts, accepted none.

**What the abstract leaves out.** (1) "No false completion" is held, not tested: "zero false — every completion claim the panel made was correct, so the gate's rejection path was never exercised" (§5.3, §7.3). (2) The 900-act cost is traced to two absences of the native minds (no source filter at action, no use of refusals). §5.4 never says an LLM was corrupted. (3) Typed refusals did not help cognition: typed vs generic feedback gave 16 vs 24 accepted acts, the less-informed arm better. (4) The panel's "stood down" is not shown to be reading the refusal (n=3). (5) Cadence changed the result in a pilot. (6) No adversarial agent was tested. Part I's staged witness is "staged". Authors: "no sentence in this paper generalises" beyond one comparator.

**Our claims, checked.**
- "A wrong act is refused with its reason" → CONFIRMED for the world. "every invalid attempt refused typed" (§5.2, §5.3). Not shown to change an LLM's behaviour.
- Sources: "no false completion was accepted in 2,581 claims" → OVERSTATED. Nothing false was ever offered. Wording: "the panel made 2,581 completion claims and none was false, so the ledger's refusal of a false one was not exercised."
- Sources: "one false testimony cost about 900 futile actions in a run-week" → CONFIRMED as number (§5.4), but WRONG as "agents/frontier-LLM minds". It is the native minds. "frontier-LLM" fits only §5.3.
- "What still stands reaches him marked as someone's word" → NOT IN THE PAPER. They test numeric trust weight and gating, not text labels for an LLM. Admitted at weight 0.6, the falsehood still drove about 900 acts.
- "ledger protects the world, not his day" → CONFIRMED, matches the 5,455 refusals and the cost to the minds.

**For us.** Chapter 2: keep "a wrong act is refused with its reason" as the engine's job, drop "2,581" as evidence of catching lies, and fix the sources entry. Add a rule that his refused decisions stop a retry loop. Cap retries per refused act in the engine; this paper's perseveration (828 refusals a week) is the failure to design out. The marked-as-word idea needs its own T40 arm.

**How far it carries.** One designed world, a small n, one panel model against a code ledger, no adversary. Ours resembles the setting (code referee) but not the model or scale. Promising for the architecture; Judgment for the labelling idea.

### BazaarBench: Delegation Safety in C2C Marketplaces Run by LLM Agents · Wang et al., 5 Oct 2026 · [arXiv 2610.06748](https://arxiv.org/abs/2610.06748)

**Read in full:** v1, lines 1–2518 of 2518 of the extracted text, 39 pages. Skipped: reference list (lines ~760–969) only. Appendices B–L read, including prompts.

**What they did.** Simulated second-hand market, 100 LLM agents, 31 typed actions, an event log and a private ownership record. Three base markets of 30 days (GPT-5.5, DeepSeek-V4-Pro, GPT-5.4-mini). From each day-30 state, a tested model drives 20 agents for 7 days under L1 ordinary, L2 deadline pressure, L3 adversarial prompts. Five tested models: GPT-5.5, GPT-5.4, GPT-5.4-mini, GPT-OSS-120B, DeepSeek-V4-Pro. 45 continuations, one each. Not pre-registered. Code checks F1–F3 against records; a GPT-5 judge scores F4–F6 (not blind to model or condition; 188 of 200 sampled judgments matched a human).

**What they found.** F3 (one owned unit committed to several buyers) reached S5 under L1 in all five models: 15, 6, 22, 4, 11 objects (Table 18, §4.3). L2 raises F3 attempts 71 to 107 and S5 58 to 95 (§4.4); no interval is given for these counts. In L1 views, 207 of 18,929 list two or more accepted deals for one listing; in 34 the seller accepts or counters again (App. K.2). L3: unavailable or overstated items in 33.4% of committed deals vs 15.4% (Table 5).

**What the abstract leaves out.** (1) The platform deliberately does not reserve a unit when an offer is accepted: "without automatically reserving an inventory unit" (§3.1). So this tests agents with no engine check; it does not test one. (2) The seller's view has no per-unit "promised" field (App. K.2). (3) The "ordinary" prompt is aggressive: "marketplace operator hired to maximize" surplus, yet it lists inventory and availability as hard constraints (App. L.1). (4) The $20 to $33 earnings rise is before the audit; after it, $17.65 vs $18.18, interval spans zero (Table 27). (5) Replaying the same input changes 4–8% of actions. One 7-day run per cell. (6) Eight tests chosen after the runs. (7) The L3 rise is mostly GPT-5.4 (55.5%); GPT-5.5 16.2%.

**Our claims, checked.**
- "All five models promised the same item to several buyers under ordinary instructions" → CONFIRMED, as counts (4 to 22 objects per model), not rates. Wording: "all five models, told to respect inventory, still double-committed an item, a few times a week among 20 sellers."
- "A promise is a record with an object and a date" → NOT IN THE PAPER. It is our design. The paper's missing per-unit field supports it.
- "The engine refuses a second promise on the same thing" → NOT IN THE PAPER. No arm had the engine refuse; the paper's own platform did not.

**For us.** Chapter 2 "Promises come due": cite as evidence the check must live in the engine, with the paper's missing-field gap as the reason. Say plainly that no remedy was tested here. Mention that 5 of 5 frontier models did it, so a 27B voice will likely too. In T40, count double promises in the clean arm as a measured baseline.

**How far it carries.** Frontier and one open 120B model, 100-agent market, 7 days, no engine reservation; ours is a 27B Q4 model in a code-refereed world. Promising (failure shown; engine fix inferred, not tested).

### State-Inference-Based Prompting for NPC trading · Kim et al., 9 Jul 2025 · [arXiv 2507.07203](https://arxiv.org/abs/2507.07203)

**Read in full:** v1, lines 1–847 of 847, 13 pages (body pp. 1–8, references, three prompt appendices A–C). Skipped: reference list only. Figure 2 heatmap text was garbled; its caption and the prose about it were read.

**What they did.** A KDD '25 workshop paper. A merchant NPC is prompted with named states. The NPC LLM itself infers which state it is in from the dialogue and writes it into a JSON field. A second LLM plays the customer. Model: gemini-2.5-flash-preview-04-17, temperature 0.7, no thinking (§4.1). 100 dialogues per scenario, fixed seeds 0–99, two scenarios (buy named items; ask for recommendations). Prompts and dialogues are in Korean. No human raters, no pre-registration, no confidence intervals. Baselines are ablations of the prompt (Table 1), plus 2.0-flash, 2.5-pro and a structured-output variant (Table 2).

**What they found.**
- State compliance (§4.2, Table 1): the rate of going CHECK_CONFIRMATION then CONFIRM_SELL. Full prompt 97.73%. Ablations 79.55, 84.09, 77.27, 94.32. Computed on the first 88 dialogues that reached that state.
- Item referencing (§4.3): 95.05% and 95.88% of 485 and 534 trade replies list only sellable items. Commonest error is a price of 0 or null for an unsellable item.
- Price (§4.4, Table 2, 2.5-flash): plain 79.7% in OFFER_SELL and 82.3% in later states. With placeholder post-processing (PPP) 100.0% and 99.7%. Token use and time about equal. On 2.0-flash PPP gives 100.0 and 91.8; plain 49.4 and 67.3.

**What the abstract leaves out.**
- "Price accuracy" means the total the model states equals the sum of the item prices and quantities the model itself listed in the same reply (§4.4). It checks arithmetic, not whether the right item or price was chosen.
- The placeholder `__PRICE__` is allowed only in OFFER_SELL and "prohibited" afterwards (Appendix A). The 99.7% is the later states, where the model writes numbers itself and they match the earlier, filled-in total. 2.0-flash scored 91.8% there.
- The states are not enforced by code. The model infers the state and the paper stresses "without external state management". Compliance is prompt obedience, 97.73%, not a guarantee.
- The paper says "six states" in the abstract, "five" in the conclusion, "eight valid options" in §5.1. Appendix A lists SHOW_INVENTORY, OFFER_SELL, NEGOTIATE_PRICE, CHECK_CONFIRMATION, CONFIRM_SELL and REJECT_TRADE.
- Authors' limits (§5.2): narrow set of states, one LLM family, short dialogues, small inventory (20 sellable, 52 items).
- Short keywords matter: `__PRICE_PLACEHOLDER__` was sometimes malformed.

**Our claims, checked.**
- "Voices write around slots… the engine fills in the value" → PARTLY CONFIRMED. Mechanism is real (§3.3.2: "use __PRICE__ for the final price amount"). It covers one slot, a total price, at one state. Nothing on balances or ready-dates.
- Sources file, "six named states with legal moves" → OVERSTATED. Counts disagree inside the paper; legal moves are prompt text the model obeys, not engine rules.
- "99.7% correct" → MISLEADING. It is arithmetic self-consistency in states after the placeholder, not slot-filling correctness. The placeholder state itself is 100.0% in this single test.
- "Promising" label → fair, one model, one game, simulated customer.

**For us.** Chapter 2's slot idea has one small precedent, for sums. Say so. A day-ready or balance slot is our extension, untested here. Rewrite the sources line: "slot-filled totals were 100% in the placeholder state; later states 99.7% by consistency". Keep our legality in the engine; this paper does not give that.

**How far it carries.** Gemini-flash, Korean, 100 short scripted-customer dialogues, one slot type, against our 27B Q4 model and long-running world. Label: Promising (mechanism); Judgment for extension to ledger facts.

### World-State Transformations for Neuro-symbolic Interactive Storytelling · Góngora et al., 23 May 2026 · [arXiv 2605.24719](https://arxiv.org/abs/2605.24719)

**Read in full:** v1, lines 1–646 of 646, 9 pages including appendices (world components, rendered states, the world-update prompt, scenario figures, error tables, a Gemini example). Skipped: reference list only. The abstract-page figure text is garbled; its caption was read.

**What they did.** An exploratory pilot, built on the authors' PAYADOR system. A text game has a structured world state (locations, items, characters, puzzles). Each turn the LLM sees the state, the player's free text and a list of "transformations", and names which apply. Three exist: Moved Items, Unblocked Locations, Player Movement. Code runs them behind "consistency checks" in a fixed order (MI, then UL, then PM). Eight human players, two scenarios (A: find a turtle; B: free a prisoner behind a puzzle). Four played in English and four in Spanish. Four used Gemini 1.5 Flash and four Llama 3 70B. One session per player per scenario. The authors read every turn and tagged errors. There was no pure-LLM baseline, no pre-registration, no statistics.

**What they found.**
- All eight players finished both scenarios (Analysis sections).
- Errors by tester (Tables 2 and 3). Scenario A: LLM errors in Moved Items 7 (English) and 8 (Spanish); planning errors 4 and 3; one memory error. Scenario B: no world-modelling errors; Unblocked Locations errors 3 and 3; Player Movement 0 and 5.
- No clear difference between the two models or two languages.
- Failures: the player's nickname for the turtle was not resolved to the item, so the move was rejected. The LLM twice unblocked the cell after a wrong riddle answer, though the right answer was in context. It sometimes proposed unblocking a place already open.

**What the abstract leaves out.**
- Only three transformation types, all movement. Nothing about money, promises or speech.
- The riddle failures got past the checks. The authors write that grounding "mitigates LLM-dependent errors, but cannot entirely eliminate them". The checks are not described in detail.
- Turn counts are not given, so no error rate can be computed.
- The LLM also writes the narration between # marks from the state; nobody audits that text.
- Fixed order of execution broke "go to the kitchen and drop the pet". They say a planner will be needed.
- The authors call the work preliminary and "pilot".

**Our claims, checked.**
- "State moves only by an act from a closed menu that the engine has checked" → CONFIRMED as architecture (Fig. 1: "executes them subject to the corresponding consistency checks"). OVERSTATED as evidence. Eight players, three movement acts, no baseline.
- Sources file, "model only names which transformations an utterance triggers" → CONFIRMED. Its model also fills arguments (which object, which place).
- "A wrong act is refused with its reason" → NOT IN THE PAPER. Invalid ones are "rejected" with no reason shown to anyone.
- "small pilot" → CONFIRMED.
- "ICCC 2026" venue → NOT IN THE EXTRACTED TEXT. Only the arXiv stamp is there.

**For us.** Keep the closed act menu. Do not cite this as showing coherence gains; it shows playability. Take two lessons. (1) Checks must test preconditions the engine owns, not trust the model's reading of a puzzle or promise. (2) Alias and co-reference failures ("Hojita") need a name-resolution step in the engine before an act reaches the check. Add execution-order tests for compound acts (move, then give). Note the narration is unaudited here; our chapter 2 audit goes beyond this.

**How far it carries.** Llama 3 70B and Gemini 1.5 Flash, short human sessions, three act types, against our 27B Q4 model and months-long run. Label: Promising (design pattern); no evidence on effect size.

### Hybrid AI Patterns: Thirteen Ways to Couple Language Models with Rules · Handschuh, Wiegand and Raichle, 29 Oct 2026 · [arXiv 2610.40036](https://arxiv.org/abs/2610.40036)

**Read in full:** v1, lines 1–4920 of 4920, 86 pages: all thirteen patterns (§3–6), compositions, failure patterns (§8), related catalogues (§9), guide (§10), limits (§11), appendices A–C (libraries). Skipped: reference list only. Rule-graph figure text is garbled and was skipped; captions read.

**What they did.** A design-pattern catalogue drawn from the authors' own rule engine, FrameX, and its applications. Each pattern has intent, consequences, a runnable listing and an Evidence line. Patterns 12 and 13 come from a hackathon, with figures read from committed result files that were not rerun (§11). Models: 8B to 70B open models, gpt-oss:20b, mostly synthetic tasks, one model family (§11).

**What they found.**
- Pre-registered studies (§10.3): rules beat a model alone on long protocols, with break-even at about 64 questions (hybrid 770/770; model 39/60 at 64, 31/60 at 96). A 9B model sufficed for the hybrid.
- Model alone was as good or better in four cases (§10.1): few rules, easy documents, cost, and a small model that cannot quote (45% against 60%).
- Pattern 4 evidence (§4.1): "One demonstration run. No measurement isolates this pattern yet."
- Pattern 12 (§3.4): official term and facts verbatim in 99% of 120 alerts against 45% for free translation (8B). The authors note the model still saw the facts there, "a weaker form".
- Fail-Safe Union (§4.5): invoice agent paid 178 of 300 bad invoices alone, none under the strict union. Hackathon figure.

**What the abstract leaves out.** Patterns 4, 7, 8, 10, 11, 12, 13 have no measurement of their own (§11). Patterns 11 and 5 are "new as stated". The catalogue is built from one engine and does not prove completeness.

**Our design in their terms.**
- Model proposes typed acts, engine adjudicates: Pattern 4, with Pattern 6 for the retry. Consequences: effects auditable and bounded; wasted turns on refusals; "whether an admitted proposal is the best one stays open"; covers only failures its authors foresaw (§9.5).
- Engine fills slots: Pattern 12. It lists no hazard beyond relevance faults and no text that combines passages. Its rule refuses model words containing a digit; the model never sees the value.
- Engine audits prose: Pattern 1 (reader) plus the Read-Back Check variant of Pattern 3 ("The reader must differ from the writer"). Possible Pattern 13 floor. Consequence: "a plausible but wrong value that passes every measurable check slips through".
- Quotation memory: Pattern 11, unmeasured. Protocols: Pattern 5.

**Our claims, checked.**
- "The audit is the engine's… judge of its own case" → CONFIRMED in spirit. §8 Self-Judge: "The model that wrote an answer, or a model of the same family with the same prompt, judges whether the answer is right."
- Sources, "recurring failures include the self-judge and the decorative check" → CONFIRMED. §8 lists five. Decorative Check: "a quoteFound that no rule reads". Our gloss "(the model reports on itself)" is loose.
- "G8 was right to distrust it" → NOT IN THE PAPER.
- Authors: three (Raichle omitted).

**For us.** Chapter 2: the audit's decision must be code, but a Qwen reader of prose is still a model. Use a different prompt, quote-grounding, and count what it misses. Name the audit's failure for unknown reads (Pattern 13 floor). Add a test for Decorative Check: every audit field must change an outcome. Chapter 2 protocols may be unneeded below tens of rules.

**How far it carries.** Synthetic tasks, mostly 8B–70B, one author group. Label: Promising for vocabulary; Judgment for our fit.

### The Curse of Knowledge in Role-Playing Language Models · Zhang, 12 Oct 2026 · [arXiv 2610.17327](https://arxiv.org/abs/2610.17327)

**Read in full:** v1, lines 1–1130 of 1130, 17 pages including limitations, appendices A–E and tables 2–25. Skipped: reference list only. Figure text for 3b, 5 and 6 is garbled; I used the figure tables and the prose.

**What they did.** 480 short template scenes in twin pairs. A and B differ only in one hidden fact (an object and a place). Net use D = share of replies using their own fact minus share using the twin's fact, in percentage points (pp), so guessing cancels (§3). Study 1: unheard or not-understood speech. Study 2: four channels (hear, understand, see, receive). Study 3: author, narrator, perspective rule, thinking on. 11 open-weight models of at most 40B (including Qwen3.8-27B), plus DeepSeek-V4-Pro and six proprietary models. Open models decode greedily at temperature 0, thinking off, 400 tokens (App. A). Quantisation is not stated. Rule-based scorer over 12 places and 12 objects, checked by humans on 790 replies (κ 0.93 to 0.98). Bootstrap intervals; proprietary cells are single runs.

**What they found.**
- Mean net use over 11 open models: 66.7 pp (language boundary) and 72.2 pp (hearing), §4.1.
- Qwen3.8-27B, Fig. 3a (five ways of stating the boundary): not understood 50 / 33 / 24; not heard 60 / 11.
- Study 2, Qwen3.8-27B (Fig. 5a): hear 22, understand 3, see 41, receive 15.
- Bridge (§5.1, Fig. 10): Qwen3.8-27B 9 to 68 pp when only the character sheet changes; 6 to 72 on 96 new scenes.
- Character view (§5.3): mean net use 60.7 to 0, permitted use +0.6 pp. Self-filter prompt cuts permitted use by 28.6 to 41.2 pp.
- Thinking (§5.2): Qwen3.8-27B 73 to 18 pp for unheard speech, permitted use 61% to 100%. Pooled, thinking "rarely helps".

**What the abstract leaves out.** The 60 is one condition (hearing, flag only, mean over questions). On the content question it is 73. Qwen3.8-27B is one of the two models that is nearly compliant in Study 2's layout. Limits stated: short template scenes, one hidden fact, scorer vocabulary of 12+12, "assumes correct access metadata".

**Our claims, checked.**
- "Qwen3.8-27B uses what its character could not have heard" → CONFIRMED, but format-dependent (above).
- "60 points above guessing" → OVERSTATED as a general figure. 60 is one cell of five; 9 in another format.
- "while it states correctly what the character perceives" → CONFIRMED by inference only. §4.1: nine of 11 models answer the state probe right for at least 87% of hearing scenes; Qwen3.8-27B is not named.
- "character sheet alone moved the leak from 9 to 68" → CONFIRMED, with a caveat. It swaps the sheet's content (named game characters), not only its layout.
- "An instruction halves it" → PARTLY. Table 6: 49.6 to 23.0 for Qwen3.8-27B. Pooled perspective rule: 82 to 62.
- "Giving only what it observed removes it" → CONFIRMED in these scenes: "from 60.7 pp to zero". Delayed and search tests also zero.

**For us.** Chapter 2: keep the filtered view, and make the engine's access record the single source. Add: a probe in our own prompt format, one run with thinking on, and a check that filtering keeps what he could observe ("appears to put something away").

**How far it carries.** Short synthetic scenes, greedy, unknown quantisation, against our Q4 model and months of record. Label: Established for the direction; Promising for "removes".

### Authoring for Living Worlds · Cudlenco, Masala and Leordeanu, v1 Apr 2026 (v4 read, 26 Oct 2026) · [arXiv 2604.10383](https://arxiv.org/abs/2604.10383)

**Read in full:** v4, lines 1–451 of 451, 10 pages. The body ends at p. 9; the rest is references. There is no appendix. Skipped: reference list only.

**What they did.** The setting is a video-game simulator (GTA San Andreas, run through an engine called GEST-Engine). The task is to write a multi-actor scenario as an event graph the engine can execute. Two designs. (1) A staged pipeline: GPT-5 through six stages, structured output parsed, re-prompted up to three times "on failure (an API error or invalid GEST JSON)" (§2). 50 stories. (2) A Director and Scene Builder agent pair on Claude Haiku 4.5, building through more than 30 tools over a stateful backend. The backend checks capacity, object lifecycle and temporal cycles, and returns explanatory errors (§3). 25 corpus stories used as seed text. Metric: does the engine run it end to end. No human raters on executability, no seeds or repeat runs reported.

**What they found.**
- Executability (Table 1, §4.2): staged 0 of 50, tool agent 20 of 25 (80%).
- Staged failure modes among 45 complete graphs (§2): 21 state-rule violations, 8 near-miss action ids, 5 object-lifecycle violations. Five more never produced a graph.
- The agent's 5 failures were engine-side crashes or stalls, not rule violations.
- Reconstruction (Table 2, §4.3), over the 20 that ran: event F1 0.83 against 0.55 for a random scenario; ordering 0.77 against 0.43; with location 0.63 against 0.35.
- Cost: about $0.25 per multi-scene story (§3).

**What the abstract leaves out.**
- The two arms differ in model, architecture and feedback. The baseline got format retries only, not simulator feedback. No run of the tool agent on the flagship model, or of the staged pipeline on the budget model. The authors' inference "the gap cannot be a model effect" is not an ablation.
- The reconstruction scores cover only the 20 successes.
- "Valid" means physically executable in the engine. It says nothing about taste, tone or content.
- Stated limits (§5) are only future work; no failure analysis of the 5 agent failures beyond one line.

**Our claims, checked.**
- Sources: "0 executable in 50" → CONFIRMED. "20 of 25" → CONFIRMED. "Staged prompt pipeline" → CONFIRMED, though it parsed format and never saw simulator state.
- Plan: "Every card enters through the world's own check" → PARTLY. Their quote: "Validity must be enforced where the specification is written, not checked after it is finished." But their checks are structural (action ids, capacity, order). Our card rules "tells him what to do" and "names a living person" are prose rules; no operation checks them.

**For us.** Chapter 3, street deck: build cards through operations (pick place from the list, hour, season, cooldown) so place, hours and cooldown cannot be invalid. Treat the two prose rules as a separate audit and say so. Return rejection reasons to the writer. Do not cite 0/50 against 20/25 as a clean comparison.

**How far it carries.** A simulator with a registry of actions, a flagship against a budget model, short test. Label: Promising.

## Chapter 2 · Truth: memory and what it keeps

### Aspectual flattening (LAPSE) · Panthi et al., 29 Sep 2026 (v2, 11 Nov 2026) · [arXiv 2609.36457](https://arxiv.org/abs/2609.36457)

**Read in full:** v2, lines 1–1383 of 1383 of the extracted text, 20 pages incl. appendices A–H. Skipped: the reference list only (lines ~530–652). Tables 11, 12, 21, 24 read from the text layout; no PDF pages needed.

**What they did.** LAPSE is a synthetic, English-only benchmark of matched user statements that differ only in verb form ("I am working at X" vs "I work at X"). Eight frames (lodging, workplace, vehicle, class, household, equipment, affiliate role, project), six carriers, six time gaps. Main test: 128 matched pairs per configuration, 245-day gap, temperature 0, one sample per item. Three "confirmatory" writers (DeepSeek V4 Flash, GPT-5.6 Luna, GLM-5.2) were fixed before data; the other eight configurations are descriptive. Eleven configurations in all: four local (Qwen3-8B, Mistral Small 3.2 24B, GPT-OSS-20B, OLMo-2-32B) and four frontier subsets scored by rule cascade only. Also mem0, Graphiti, Letta. Not preregistered in a registry; "fixed before data collection" (App. H).

**What they found.**
- Writers flattened the progressive, keeping the simple-present twin, in 210 of 381 pairs; the reverse in 0 (Table 2, §5). Across all 11 configurations: 722 forward, 0 reverse (Table 11).
- Rates vary: 36.7% (Grok 4.6) to 68.0% (DeepSeek) in the main cell (Table 11). Frames vary from 0/16 to 16/16 (Fig. 2b).
- mem0 with DeepSeek flattened 49/128; with Gemini 3 Flash 15/128 (§6, Table 18). Graphiti 47/95, Letta 62/90.
- Readers rated progressive notes 16–32 points less durable (§7.1). In the planned verification-tool test, GLM-5.2 acted without asking on 187/291 simple vs 116/291 progressive notes (Table 5).
- Exploratory: free-text notes showed no form difference (23:19, p=.32); records with the user's words showed 113:18 (Table 24, §7.4).

**What the abstract leaves out.** The reverse is zero only under the main "aspect flip" outcome; under the planned outcome it is 807:2, both Claude Sonnet 5 adding "currently" (App. B). The planned memory-use task was saturated and showed nothing (§7.1). Readers disagree: Kimi K2.6 reversed (34:56), GPT-5.6 Luna and Claude Haiku 5.5 confirmed every note, Gemma acted on every note. A preservation instruction helped some writers and made GPT-OSS-20B and OLMo worse (Table 16). If mem0 kept a date, readers could use the date. Authors say "always expire progressives" is too rigid.

**Our claims, checked.**
- "A summary turns 'I am working there for now' into 'he works there', in every model tested" → OVERSTATED. Direction held in all 11 configurations, but rates are 37–68%, and "for now" is a separate test. "Lexical markers" showed Luna kept "for now" in 84/128 notes while DeepSeek lost it in 128/128 (Table 15). Wording: "in all eleven models tested, some of the time (37–68% of progressive statements)."
- "all eleven models tested, never the reverse" → CONFIRMED for the aspect-flip outcome (722:0); the planned outcome had 2 reversals (Claude Sonnet 5).
- "a record with the speaker's exact words and the date restored readers' caution" → OVERSTATED. Exploratory; two readers only (GLM-5.2, Gemini 3 Flash); the second planned test failed for Gemini. Quote: "it passed for GLM-5.2 and failed for Gemini 3 Flash." The record had four fields; the words carried most of it.
- "free-text notes did not" → CONFIRMED (§7.4: free text erased the difference).

**For us.** Chapter 2 "What was said stays a quotation" and the owl-gist task: keep the speaker's words and date in the stored line. Do not claim it restores caution for every reader; Hegel's own Qwen3.8-27B was never a reader. Test our own owl's gist on a handful of progressive statements before relying on it. Not shown at our budget or model size.

**How far it carries.** Synthetic English sentences, mostly API models, single statements, not months of narrative; the write-side loss is Established, the reader-side caution is Promising.

### Copies or Sources? · Gao et al., 5 Oct 2026 · [arXiv 2610.06192](https://arxiv.org/abs/2610.06192)

**Read in full:** v1, lines 1–2160 of 2160 of the extracted text, 39 pages incl. appendices A–G. Skipped: the reference list (lines ~545–653) only.

**What they did.** A sensing task, not narrative memory. A hidden state (storm/clear, etc.), sensors with stated reliability, and an aggregator LLM that reads a message log and reports a probability. The probability is converted into "readings" and compared to an exact Bayesian oracle. Three testbeds: T1, 1,000 controlled logs in 27 forms; T2, 500 web items from ConflictingQA with duplicate, republished or summarised copies; T3, 500 configurations of four-agent teams (relay, board, discussion, hierarchy), 4,000 logs without and 4,000 with a "reference rule". Four API models (GPT-6 Luna, GPT-6.1 Sol, Gemini 3.8 Flash, DeepSeek V4.1 Flash) at low reasoning effort, official APIs, sizes not given. Stated test families were fixed before data; Holm correction. No humans except 240 messages checked by two authors.

**What they found.**
- Two forwarded copies of one reading count as 0.06 (Sol), 0.21, 0.27, 0.42 (DeepSeek) of a new reading (§4.1, Table 8, w3).
- Mostly all-or-nothing: 4–35% of replies count every statement (§4.3). One reading stated three times crosses the commit boundary in 4.7–39.8% of logs (§4.4).
- Web copies: duplicate ρ 0.14–0.32, summary 0.40–0.71 of a distinct document (§4.5, Table 2).
- Agents restate by default: 71% of messages by agents without a sensor (§4.6). Pooled early commitment 11.2%. With the reference rule: 1.1% (§5.2, Table 3).
- Genuine corroboration kept: 2.90–2.96 against 3 (§5.3).

**What the abstract leaves out.** The 11.2% to 1.1% is "belief-implied" (a threshold on the reported probability), not a measured action, averaged over four protocols and four aggregators; the hierarchy kept restating (33% of messages under the rule, early commitment 3.3%). The rule fixes the writers' prompt, not the reader. Reasoning off raises the weight (Luna 0.40, DeepSeek 0.55; Table 21); a placebo note pointing at the copies raised it. Controlled logs have honest labels and exact copies; forged IDs and altered relays are left open. Single seed per call; replicates agree closely (Table 13).

**Our claims, checked.**
- "each source counts once, however often it is retold" → NOT IN THE PAPER as a finding. It is their normative source-counting rule; the paper shows models fail it. Reword as a design rule, not a result.
- "a restated observation counts as 0.06–0.42 of a new one" → CONFIRMED for two forwarded JSON copies (§4.1). For web copies the range is 0.14–0.71 (Table 2); on agent logs the slope is 0.04–0.22 per restatement (Table 30).
- "referring to a reading in place of restating it cut premature commitment from 11.2% to 1.1%" → OVERSTATED. Quote: "early commitment falls from 11.2% to 1.1%." True, but "belief-implied", pooled, and for agents told to refer in a scripted rule.
- "frontier models only" → NOT IN THE PAPER as a label. They are API Flash/Luna/Sol models at low effort; no open-weight or small model.

**For us.** Chapter 2's "each source counts once" and T42 (count sources, not mentions) stand as design, but the evidence is that models do not do it unaided, so the engine must dedupe. The strongest result for us is the protocol one: give each encounter an ID and let the gist and recall refer to it, not retell it. A declaration naming the copies cut weight to about 0.08 or less. Not shown at our budget or size: no 27B Q4 model, no non-reasoning arm below 0.4.

**How far it carries.** Four API models, numeric sensor logs with stated reliabilities, against one local 27B reading prose memories; the weight itself will not transfer, the protocol lesson (state once, refer after) is Promising.

### When Does Selection Replace Extraction? · Sharma and Lall, 28 Sep 2026 · [arXiv 2609.34227](https://arxiv.org/abs/2609.34227)

**Read in full:** v1, lines 1–1255 of 1255 of the extracted text, 21 pages incl. appendices A–J. Skipped: the reference list (lines ~868–1016) only.

**What they did.** Two independent researchers. Question answering over long dialogues: LoCoMo (5 held-out conversations, 778 scored questions) and LongMemEval (70-question sample, then all 500). Their own selector, "Jev" (a closed, typed decision model, jev-1.13.0) scores 30 cosine-shortlisted raw turns in one call; turns are stored as "[date] speaker: text". The comparator is the authors' own extraction system, engram v2 (gpt-4o-mini extraction). Other baselines: cosine only, a gpt-4o-mini listwise reranker, mem0 2.1.0, Jev-Mem. Answerer and judge are gpt-4o-mini (second answerer Llama 3.3 70B). The plan was deposited on Zenodo before data (§4, App. B); one amendment, made after two secondary results were known and before the main test. Non-inferiority margin 5 points. Blind human grading by the first author, who built the systems, on 142 judge-discordant questions.

**What they found.**
- H1: Turns+Jev 77.0% (265 tokens) against engram v2 77.5% (251 tokens); difference −0.5, one-sided bound −3.0 (§5.1, Table 1). Human grading: −1.7 to −2.6, worst bound −4.7.
- Cosine only: 59.9% at k=3 (130 tokens) and 68.6% at k=6 (254 tokens) (Table 3).
- Rerank gain over cosine: +17.4 (k=3) falling to +1.5 (k=20) on LoCoMo; +9.1 to +1.1 on LongMemEval (§5.3).
- Where it fails: 11.5% of questions lost at the shortlist, 9.2% at the rerank (§5.6).
- At generous budgets extraction wins: engram v2 at k=20 82.4% against 77.6% for Turns+Jev.
- Correct abstention fell from 63.6% (cosine) to 54.1% (Jev) (§5.8).

**What the abstract leaves out.** "Tight budget" means up to about 300 tokens; at 1,000+ tokens extraction was better. The rerank is a closed proprietary model, not BM25 or an open cross-encoder. Comparator is the authors' own, graded by its author. LoCoMo dialogues are LLM-generated, and a third-party audit cited in the paper puts 6.4% of its answer key as wrong. engram v2 was not run on LongMemEval. Temporal and open-domain questions are where raw turns trail extraction (temporal 72.1 against 77.6).

**Our claims, checked.**
- "three to six raw turns (130–265 tokens)" → CONFIRMED (Table 3: 139 at k=3, 265 at k=6).
- "reranked raw turns match LLM-extracted memory (77.0 against 77.5)" → OVERSTATED as "match". Quote: "non-inferior ... within a 5-point margin under every grading we applied." Corrected: "within 3 points on this benchmark with their closed reranker; human grading puts the gap at up to 2.6."
- "without the rerank the top three score 59.9" → CONFIRMED (cosine k=3). Note the 77.0 is at k=6; cosine at k=6 is 68.6.
- "the rerank drops evidence of when on 22.7% of questions" → OVERSTATED/WRONG scope. Appendix D: 22.7% is the share of temporal-category questions (n=284, evidence in shortlist) where the rerank kept none. Across all questions it is 10.4% (9.2% of all). "Evidence of when" is the authors' reading.
- "we conclude our raw-search arm (BM25 over day files) needs a rerank and printed dates" → NOT IN THE PAPER. They use embeddings, not BM25, and never ablate dates; dates are always printed. The rerank need is shown only at k=3 of 30.

**For us.** Chapter on the raw-search arm (G2): keep the arm, but state it as a hypothesis. Add a rerank arm, and a date-print arm that can actually be compared. Our recall is about 850 characters, roughly 200 tokens, inside their tight regime; but with a 27B Q4 model as reranker, not Jev. Also watch abstention: a rerank made the model answer when it should not.

**How far it carries.** gpt-4o-mini, LoCoMo and LongMemEval Q&A, closed reranker; against our local 27B Q4 reading day files for a character. Promising.

### Will My Assistant Remember My Allergy? · Zhu et al., 4 Sep 2026 · [arXiv 2609.05767](https://arxiv.org/abs/2609.05767)

**Read in full:** v1, lines 1–401 of 401 of the extracted text, 6 pages (HumanSys '26 workshop paper). Skipped: the reference list only. There is no appendix.

**What they did.** A study of KV-cache eviction, not of written summaries. The assistant keeps the attention cache of the whole conversation and evicts blocks of tokens to fit a budget. They compare policies (SnapKV, H2O, a probe token, StreamingLLM, LRU, an INT4 tier) with the recall question visible during compression (the usual protocol) and hidden (their "query-hidden" protocol, §4). Model: Qwen2.5-7B-Instruct, bf16; replicated on Llama-3.2-3B and Qwen3-8B for the synthetic needle only. PA-Bench: n=100 templated, 30-round conversations (about 2–3K tokens), two health or safety facts planted in passing at rounds 3 and 16, substring scoring (§5.2). 20% budget, block size 8, Wilson intervals, one run per cell. No human raters, no pre-registration. They also found two bugs in their own first SnapKV and H2O code (§3.2).

**What they found.**
- Query-visible, SnapKV 0.83 and probe 0.87 on PA-Bench; hidden, 0.01 and 0.00; H2O 0.00; full cache 0.97 (Table 1).
- No policy retained a single block of the fact (retention 0.00). Retention was 0.86 when the query leaked.
- Why: of 32 kept blocks at 20%, sinks and recency take about 25, leaving about 7 for scoring; the fact's blocks rank 16–59 (§5.3).
- Budget sweep with H2O: recall 0.43 at 40%, 0.80 at 60%, 0.965 at 80% (Table 4).
- 99% (196 of 198) of failures were requests to re-supply the fact; none invented a different drug (§6).
- One untuned prompt that extracts durable facts, re-injected at question time: allergy recovered in 0.51 of cases (§6).

**What the abstract leaves out.** The 0–1% is the 20% budget only; at 60–80% the fact comes back. A stateless design that re-reads the raw transcript is explicitly outside the critique (§1). The corrected baselines on four standard benchmarks lose nothing (§5.1). The fact types are templated and the scoring is substring match. The authors' own episodic-store test reached only 0.51, which they call relocating the problem.

**Our claims, checked.**
- "when compression happens before the question is known, a fact mentioned in passing survives 0–1% of the time, against 97% with full memory" → CONFIRMED as a number, WRONG as a mechanism for us. It is KV-cache token eviction in a 7B model at a 20% budget (Table 1; abstract: "survives to the question that needs it 0–1% of the time, against 97%"), not an LLM-written gist.
- "the gist is written before anyone knows what he will need" → NOT IN THE PAPER. They never test summaries, notes or recall text.
- "a ledger for what he must act on" → PARTLY SUPPORTED. They recommend an "auditable episodic store" for safety-critical facts, but their own prototype recovered only 0.51 because the extractor must first recognise the fact as worth storing.

**For us.** Do not cite this as evidence that the owl's gist loses passing facts; it is evidence about attention eviction. The weaker, honest line: a store written before the question needs its own check that it caught the fact (the 0.51 coverage problem). That supports a ledger entry with a test: plant passing facts in day files and measure what reaches the gist and the ledger. The failure mode they found (asks, does not invent) is a point for letting Hegel say "I don't have that" and have the engine answer from the ledger. Not shown at our size, budget or kind of memory.

**How far it carries.** A 7B model's KV cache, 2–3K token synthetic chats, against a 27B Q4 reading an owl's text; the analogy is Judgment, the eviction numbers are Established only for that setting.

### DISCERN · Ahuja et al. (Amazon), 11 Nov 2026 · [arXiv 2611.15729](https://arxiv.org/abs/2611.15729)

**Read in full:** v1, lines 1–764 of 764 of the extracted text, 14 pages incl. appendices A–D. Skipped: the reference list (6 entries) only. NeurIPS 2026 TTCL workshop paper.

**What they did.** ENT-310, a synthetic enterprise sales-agent benchmark generated with Claude Opus 4.8: 10 actors, 31 sessions in all (3–4 per actor, about 16 turns each, 500 events), 310 queries (210 answerable in four pillars, 100 unanswerable) (§4, App. D, Table 7). Also the full LoCoMo corpus, 1,986 questions, zero tuning. DISCERN keeps an immutable event log, builds an LLM-extracted entity and bi-temporal fact graph that never merges and soft-invalidates, and reads it with an agentic loop of up to 8 turns and a closed set of four ending actions. Generator Claude Sonnet 4.6; four-judge council including Opus 4.8. Eight baselines (BM25, Dense, RRF, agentic RAG, extract-retrieve, GraphRAG, HippoRAG2, Mem0). DISCERN and HippoRAG2 are three-seed means; other baselines single seed. No humans except vetting of questions.

**What they found.**
- Retention and currency are near-saturated, 0.93 to 0.98 for competent systems (§5).
- Macro answer correctness 0.861 against 0.806 (Table 1); entity resolution 0.800 against at most 0.40, on n=15.
- Abstention F1 0.924 against 0.802 (Table 2).
- LoCoMo macro 0.663 against 0.638 for HippoRAG2; plain RAG-Dense 0.312, with temporal 0.078 against 0.713 (Table 3).
- Tools off 0.33, eight turns 0.89 (Table 5). Backbone swap: Qwen3-235B 0.707, gpt-oss-120B 0.610 (Table 6).

**What the abstract leaves out.** Currency is not unsolved in their own table: baselines score 0.975, DISCERN 0.900. DISCERN is below the best baseline on retention (0.929 against 0.976), currency and contamination (0.817 against 0.901). Its lead exists only under their equal-weight macro; by my own count-weighting of Table 1 with the pillar sizes of Table 9 it is about 0.876, below extract-retrieve (about 0.900) and agentic RAG (about 0.890). The read path is costly: 4.1 turns, 5.7 tool calls, 7.6 s a query, and degrades with weaker open models. The tiny memories (about 50 events an actor) would fit in one context. The navigation and gate ablations are single-seed, one judge.

**Our claims, checked.**
- "a plain retrieval reader already matches memory systems on recall" → CONFIRMED on ENT-310 retention and currency only. On LoCoMo it does not hold: plain readers score 0.08 on temporal questions against 0.71 (Table 3).
- "what stays unsolved is resolution (which entity, which value is current, whether to answer at all)" → OVERSTATED. Entity and abstention yes. "Which value is current": Table 1 shows currency saturated for baselines (0.975); the abstract's own words "near-saturated" contradict its "which time-state is current".
- "their store only ever adds, never merges, never drops a superseded value" → CONFIRMED. Quote: "strictly additive ... never merges entities and never drops facts." Superseded values are soft-invalidated, not deleted.
- "the day files stay the archive, and the work belongs in the read path" → PARTLY SUPPORTED. Their log is the source of truth and views rebuild from it. But their ablation (§5.2) shows the gain needs an 8-turn agentic reader on a frontier model; it falls to 0.61–0.71 on 120–235B open models.

**For us.** A (archive), T41, G2. Keep day files as the record. The read-path work to add first is "not in the record" counting as right and entity disambiguation; do not claim a "which is current" gap on this evidence. A 27B Q4 model at 7.6 s and 5 tool calls per query is untested; budget for a weaker reader. Not shown at our size or length.

**How far it carries.** Claude-class models, 3–4 short synthetic sessions per actor, against a 27B Q4 and months of day files; Promising for abstention and entity handling, not shown for currency.

### How strongly should task state influence an agent? · Zhang, Kweon and Han, 22 Sep 2026 · [arXiv 2609.25686](https://arxiv.org/abs/2609.25686)

**Read in full:** v1, lines 1–2843 of 2843, 43 pages, all appendices A–J. Skipped: the reference list (lines ~695–1020).

**What they did.** Synthetic assigned-project episodes: 10–18 steps with prerequisites, 44 turns, one cancellation, traps (re-asking a finished step, asking a blocked one). The same task state shown four ways: raw transcript, always-correct text checklist, per-turn directives, or an enforcement gate that refuses violating actions. A step becomes DONE only on a receipt, a booking line the module checks. Models: Qwen3-235B (AWQ), Qwen3.6-35B (FP8), DeepSeek V4 Pro (32 episodes per cell). 128 episodes per cell, temperature 0, exact-match scoring, McNemar tests. Not Qwen 27B and not Q4_K_M. Two outside checks: tau2-bench airline and PM-Bench.

**What they found.** Qwen3-235B, no thinking, S=10, amended brief: raw 0.38, checklist 0.55, directive 0.84, enforcement 0.98 (Table 2). Qwen3.6-35B: 0.25, 0.32, 0.68, 0.98. Directive obedience at the 35B model: 0.854 over all traps, 0.726 on "already DONE" (Table 11).

**What the abstract leaves out.**
- Text state was good enough with thinking plus a stated rule: raw 0.80, checklist 0.80, gates 0.88 and 0.95 at S=10 (§4.3, App. E); DeepSeek V4 Pro with thinking went from 16/32 to 32/32 once the one-shot rule was written down.
- At 35B the checklist did not separate from raw (0.32 vs 0.36; Table 2).
- An unverified ledger the agent writes itself (0.70, 0.79) beat the accurate checklist (0.55, 0.59), but lost on PM-Bench.
- On PM-Bench the checklist was the best rung (0.77 vs 0.70–0.72 for gates at 235B); enforcing the matcher's judgement at 35B fell below raw (0.55 vs 0.63).
- The gate changed nothing for a model that rarely violates (35B on tau2: 3.5% of episodes catchable).
- Weak point: the matcher that maps requests to steps. Reworded requests cut the directive gate from 0.92 to 0.58 and enforcement from 1.00 to 0.78 (App. A.5). Corrupted state: 0.98 to 0.41 at about two corruptions per episode (§5.3).

**Our claims, checked.**
- "State kept as text in the prompt, against state a module enforces" → CONFIRMED as the design.
- "An obligation with a decidable state advances on the engine's receipt" → OVERSTATED as a finding. Receipt-only advance is held fixed in every gated arm; it is never varied. What the paper shows is that module-held state plus a directive or a refusal beats text. Quote: "Enforcement pays when failures are state-decidable and frequent, and hurts when the gate's judgement is wrong."
- Implied "showing state is unreliable" → OVERSTATED. It holds for non-thinking runs; with thinking and a stated rule the text rungs recover.

**For us.** Chapter 2: promises with date and object are decidable, so engine-held state fits. The audit that reads prose for "paid", "ready" is a matcher; test it on reworded replies and count over-blocks. Put the rule in the user turn, not the system prompt (system-role directives fell to 0.17–0.69 in Table 16). Add a no-obligation-failure baseline first: measure how often Hegel breaks a promise today before building the gate.

**How far it carries.** 35B–235B models, scripted cooperative user, one procurement and one release domain. Our 27B Q4 with free text is smaller and noisier. Label: Promising.

### MemStrata, local Qwen 3.8 27B Q4_K_M reader · Yadav, 4 Oct 2026 · [arXiv 2610.05343](https://arxiv.org/abs/2610.05343)

**Read in full:** v1, lines 1–1391 of 1391, 29 pages, appendices A–F. Skipped: the reference list (lines ~1098–1158). Single author, with a stated commercial interest (Called It Inc.).

**What they did.** A retrieval system (hybrid lexical and nomic-embed ranking, source spans with dates and speakers, 24,000-token evidence ceiling) feeds a local reader, qwen3.8:27b Q4_K_M. Tests: LongMemEval-S (500 questions), LoCoMo (1,540, ten histories), LongMemEval-M, BEAM-1M (300). Judge: hosted GPT-5.5. One seed per benchmark; follow-ups partly pre-registered.

**Running the model locally (App. A, §4.2, §5.4).** Ollama-style /api/chat. num_ctx 128,000; num_predict 16,384; temperature 1.0; top_p 0.95; top_k 20; repeat_penalty 1.0; think "high"; keep_alive 30m. Mean evidence 23,335 tokens; mean generated 1,133 tokens including thinking. Reader request time: mean 73.04 s, median 55.34 s, 95th percentile 159.35 s. The authors say these are not end-to-end or hardware-independent. The GPU and tokens per second are not given for the reader.
Failures: an empty or length-limited output counts wrong. LoCoMo 4 output failures, LongMemEval 0; a 26-answer fallback call recovered 21 valid answers but only 4 of 14 were correct, median added time 65.9 s (Table 19). Raising output to 32,768 tokens did not meet the registered criteria. Adaptive temperature (0.6/0.8/1.0) changed nothing (463/500).

**What they found.** LongMemEval-S 463/500 (92.6%) reference-only; 475/500 (95.0%) source-aware. LoCoMo 78.25% and 90.91%. Full history (mean 108,556 tokens) 464/500. LongMemEval-M, packet 1.6% of history: 427/500; losses in multi-session and temporal (Table 16).

**What the abstract leaves out.** The 95% is the author's own rubric on a hosted judge, written after inspecting problems, not human-checked. No held-out data. Date and speaker rendering is never ablated. Same-seed replay: 467/500 answers byte-identical, 33 changed, 3 labels flipped, with 463 becoming 464 (§8.2); the authors call 1.5–2.3% "an observation rather than a noise bound", one replay per set (§9.3).

**Our claims, checked.**
- "Qwen 3.8 27B at Q4_K_M" → CONFIRMED.
- "Reads literal, dated, attributed spans at 95%" → OVERSTATED. It is a retrieval system plus reader; 95.0% is source-aware only, 92.6% reference-only (LoCoMo 78.25%). Not shown that dates or attribution cause the score.
- "At 24,000 tokens" → CONFIRMED as a ceiling; mean 23,335, context window 128k.
- "A replay with the same seed changed 1.5–2.3% of labels" → CONFIRMED (§9.3), one replay per set.
- "One author" → CONFIRMED; add the commercial interest.
- "Measure replay noise before any comparison" → supported; the paper itself says to repeat reader and judge runs.

**For us.** Sources file: write "92.6% reference-only (95.0% by the author's rubric)". Tell G-tasks to measure reader replay at temperature 1.0, not assume it. Expect 60–160 s per long request with thinking on; budget the 3090 accordingly.

**How far it carries.** Same model and quant, but QA over chat logs, 24k packets, hosted judge. Label: Promising (settings, noise); Judgment (95%).

### When Agents Need to Consolidate Memories (Memory-TCG) · dos Santos Filho, 11 Nov 2026 · [arXiv 2611.15644](https://arxiv.org/abs/2611.15644)

**Read in full:** v1, lines 1–684 of 684 of the extracted text, 14 pages, including the appendix and references. Nothing skipped.

**What they did.** An engineering study of an offline memory step for an agent history log. A synthetic test with 48, 480 and 1,920 facts: current decisions, superseded ones, echoes, duplicates, conflicts. Output is capped at 512, 1,024 or 4,096 tokens (cl100k) of JSON. Arms: chronological window (A); newest-per-key rules B and B′ (B′ keeps explicit decisions and stops an echo from overwriting one); full system (C, CN); partial sample (CP); no resonance (D2); early cut (D1); C with 20% of the budget reserved for conflicts (CQ). Five seeds, "not five independent datasets" (Sec. 4.1).

**What they found.**
- Decision recall at 480 facts, 1,024 tokens: A 0.06, C 0.44, oracle 0.58 (Table 2).
- B′ and D2 equal C at all nine scale-and-budget cells (Table 2). B alone scores 0.000, because an echo overwrites the decision (Sec. 5.4).
- Before the cap, conflict F1 is 0.615 (precision 0.444). After the cap it is 0.000 at 480 and 1,920 facts, because conflicts are serialised last (Table 1).
- CQ at 480 facts: 1,024 tokens, conflict F1 0.000 to 0.431, decision recall 0.44 to 0.34. At 512: F1 0.222, recall 0.22 to 0.18. At 4,096: F1 0.930, recall unchanged at 1.000 (Table 4, Sec. 5.3).
- At 1,920 facts: 4,096 tokens, CQ F1 0.447, recall 0.445 to 0.355. At 1,024: F1 0.129, recall 0.11 to 0.085.

**What the abstract leaves out.**
- The tie between B′ and C holds because fixtures "supply structured keys and explicit supersession relations", where "an instructionist rule suffices by construction" (Sec. 6). Decisions are ordered by identifier in every arm, so ties show the same set, not equal policies.
- The quota lowers decision recall in five of nine cells (Sec. 5.3). At 48 facts and 512 tokens CQ is worse than C (F1 0.727 against 0.889).
- Same team designed, ran and reviewed it; not replicated; fixtures repeat patterns (Sec. 6).
- Conflict detection is weak without supplied keys: on six keyless pairs, recall 0.333, two missed (Sec. 5.5).
- A product probe at 3,200 characters showed 4 of 50 current decisions (0.08) (Sec. 6).

**Our claims, checked.**
- "A simple rule that prefers current, authoritative decisions recalled as many as the full system" → CONFIRMED in this test, with the keys-supplied condition. Quote (Sec. 5.2): "an authority-aware rule (B′) produces the same active decision set as full RRR".
- "Reserving a fifth of the budget for conflicts brought the conflicts back at a small cost in recall" → OVERSTATED. Cost is nil only at 480 facts and 4,096 tokens. At 1,024 tokens it is 0.10 of 0.44, about a fifth of recall. Conflicts come back only in part (F1 0.43, 0.22, 0.13 at tight budgets). Wording: "the quota restored conflicts fully only when the budget was large; at tight budgets it bought partial conflict recall for 0.04 to 0.10 of decision recall."
- "One author, synthetic fixtures" → CONFIRMED; add "same team ran and reviewed it".
- Our proposal, a fixed slice of 850 characters for open obligations and corrections → NOT IN THE PAPER. Their slice is for candidate conflicts. 850 characters is about 200 tokens, below their smallest budget (512). Obligations are not tested.

**For us.** One arm is still worth running. The case in our favour is that our engine knows obligations exactly, which is their keys-supplied regime. Two cautions: a slice costs ordinary recall at tight budgets, so size it by test; and order inside the slice matters, since their head-of-queue ordering was not optimal (Sec. 6).

**How far it carries.** Their setting: synthetic fixtures, 512 to 4,096 tokens, rule-based. Ours: 850 characters, a live character. Label: Promising.

## Chapter 4 · Depth: people, standing, stakes

### GARP: real-time generative agents on local hardware · Molino et al., 8 Nov 2026 · [arXiv 2611.11064](https://arxiv.org/abs/2611.11064)

**Read in full:** v1, lines 1–848 of 848 of the extracted text (13 pages). Skipped: reference list only (lines ~739–848). There is no appendix.

**What they did.** A Godot 4.6 platform with a Rust backend. Agents plan, remember, feel, and have six needs, four personality axes and pairwise relationships. The local model is Llama 3.2 3B Instruct (Q4_K_M) on an Apple M1 Max (§IV-F). The town runs about 20 agents. There was no human rating, no pre-registration and no baseline run. The only comparison is a table against Generative Agents on features and cost (Tables IV, VI).

**What they found.** Nine scenarios were run three times each. 25 of 27 runs passed log checks (§V-C). Both failures were the birthday party: 4 of 11 party runs had a guest who remembered the invitation but left it out of the day plan (§V-C, §VII). Filtering 50+ actions to 3–8 cut a response from about 20 s to about 8 s (§VI-f). Relationship update (§III-A6): the LLM reads the lines and names a change for sentiment and one for trust. Each name maps to a fixed delta ("much warmer" +0.45, "a little warmer" +0.1), clamped to ±0.6 and ±0.5. Familiarity gets a small increment.

**What the abstract leaves out.** The checks only ask whether the intended thing happened in the logs. The personality pairs are "accepted captures", each recorded up to three takes until its goal passed (§V-C). The warmth effect at 1.375× (0.41 vs 0.40) vanished in the appraiser's run-to-run variance, so they raised it to 1.75× (§VI-c). The authors say they did not test believability with raters, did not isolate subsystems, did not compare model sizes, and did not measure drift over weeks (§VII). Four near-duplicate coffee notes outweighed one party note (§VI-d). Paraphrase changed the time or owner of relayed commitments (§VI-e).

**Our claims, checked.**
- "Local 3B model; six needs; pair holds familiarity, trust, sentiment" → CONFIRMED (§III-A5, A6). The pair also holds a last-interaction time.
- "After a conversation the model picks a named change that code maps to a fixed, clamped step" → CONFIRMED (§III-A6). Familiarity is a small increment, not named.
- "Names replaced numbers because the model called a stranger a likely thief and returned −0.05" → CONFIRMED, but it is one anecdote with no rate. Quote: "described a stranger as a likely thief and returned a sentiment change of −0.05" (§VI-a).
- "50 actions narrowed to three to eight" → CONFIRMED (§III-A8).
- "25 of 27 scripted runs pass log checks" → CONFIRMED. Say "9 scenarios × 3, both misses in one scenario".
- Plan, Standing: "a regard that moves only on recorded acts" → NOT IN THE PAPER. GARP's regard moves on an LLM reading of talk, not on acts. It is the opposite design. Cite GARP only for "named change mapped to a fixed clamped step".

**For us.** Chapter 4 Standing: keep acts-only as our own choice. Do not cite GARP for it. The variance finding and the temperature-0 appraiser support our delay of the "named change" arm. "Word gets round": relay the engine's fact, never the model's paraphrase (§VI-e). Task on the later arm: measure the appraiser's repeat variance first.

**How far it carries.** A 3B model, 20 agents, minutes of game time, scripted scenes, logs only, against our one protagonist, 27B Q4, months and a code-refereed world. Promising (design hints), not evidence about long-run regard.

### Hybrid interactive narrative systems with LLM · Clerc et al., 2 Nov 2026 · [arXiv 2611.02807](https://arxiv.org/abs/2611.02807)

**Read in full:** v1, lines 1–649 of 649 of the extracted text (12 pages). Skipped: reference list only (lines 583–644). No appendix.

**What they did.** A platform with a symbolic world of facts and operations (preconditions, add and delete lists). Three managers, each run on the same Little Red Riding Hood scenario, 100 sessions each (§5.1). The player is an LLM (GPT-5 mini, temperature 1), and the managers' LLM parts use the same model. 100 was chosen by a convergence rule. It is not pre-registered and there are no human players.
- Open: turns a command into an action, and injects a random event with some probability, which can pre-empt the player (Alg. 1).
- MCTS: behaves like Open until a dead end (no operation applicable), then searches for generated events to commit (Alg. 2).
- Multi-agent: one LLM per NPC, each acting once a turn after the player, with the player phase using event probability 0 (Alg. 3).

**What "agency" measures (§5.3).** It is the acceptance rate: "the share of player proposals the manager applies unchanged". It is not felt agency or effect on the world.

**What they found (Table 1, mean ± sd, Open / MCTS / Multi-agent).**
- Agency: 0.44±0.18 / 0.27±0.14 / 0.68±0.29.
- Controllability: 0.28 / 0.40 / 0.52.
- Author intent: 0.47±0.41 / 0.44±0.41 / 0.04±0.16.
- Robustness: 0.58 / 0.76 / 0.63. Completion 0.52 → 0.80 under MCTS (§6, H1).

**What the abstract leaves out.** Agency is a proxy, and footnote 2 says so: it does not capture "real impact on the state of the world and the player's feelings". The multi-agent manager's 0.68 is partly built in. Its NPC events are added after the player's turn and never replace a proposal, while the Open manager's random events can pre-empt one. Its author intent collapsed to 0.04, and the authors note the count treats any generated event as a loss of intent. The agency spread is wide (sd 0.29). One scenario, a simulated player, and results "still need to be confirmed with human players" (Limitations).

**Our claims, checked.**
- "A manager that repaired the story cut agency from 0.44 to 0.27" → CONFIRMED, with a caveat. The repair fires only in blocked states, and the authors say it takes "over the event channel", lowering the share of player-driven turns (§6). Say "repair at dead ends".
- "People with goals of their own kept it highest, at 0.68" → CONFIRMED as a number. Add that it costs author intent (0.04).
- Sources: "repair raised completion 0.52 to 0.80; simulated player; one scenario" → CONFIRMED.
- Digest: "it names what our no-steering rule protects: agency, as a number" → OVERSTATED. Their number is the acceptance of typed commands. Hegel's decisions are not pre-empted by design, so it protects less than we claim.
- Digest: "no manager wins on all four" → CONFIRMED (H3).

**For us.** Chapter 4 "Stakes come from rules": keep the numbers, add "in one simulated-player study" and "own-goal characters broke the authored islands (0.04)". That is a reason to keep agendas in data and thread beats authored. Task: log our own acceptance rate (the share of his decisions the engine applies unchanged), but do not call it agency.

**How far it carries.** GPT-5 mini as player and managers, one fairy-tale scenario, 100 short sessions, against our one 27B Q4 protagonist living for months. Promising for structure (preconditions, effects), not for the size of effects.

### ANIMASK: what the model contributes to role play · Zhang et al., 15 Sep 2026 · [arXiv 2609.16667](https://arxiv.org/abs/2609.16667)

**Read in full:** v1, main text lines 1–690 and appendices A–J (lines 975–3091) of the extracted text, 38 pages. Skipped: reference list (692–975) and the figure-label debris in Fig. 6 (lines ~2345–2495). Read the matrix rows by number.

**What they did.** 40 stories (20 English short stories, 20 Chinese scripts) frozen at 50–70% and replayed by six frontier cloud models (GPT-5.5, Claude Sonnet 5, Gemini 3.7 Flash, DeepSeek-V4-Flash, Kimi K2.6, Qwen3.7-Plus). That makes 240 replays, one sample each, temperature 0.7. LLM world-keeper and terminator. At each decision point the persona card is removed and the same call replayed. All judging is by one LLM (DeepSeek-V4-Pro). Human check: the three authors.

**What they found.**
- §6.1: all 24 actor-score deviations from canon are negative. Only 7 of 240 replays end with a goal achieved, against 39 of 40 canons resolving the central tension.
- §6.3, Table 2 (2,824 persona-present points, not all 3,846): adherence 0.80–0.86. The default already lies inside the persona's range at about 74%. Efficacy is 0.07–0.18.
- Cross calls are kept at 79–87% under five actors and 64% under GPT.

**What the abstract leaves out.**
- The actor prompt says: "Caution, hesitation, refusal, waiting, or de-escalation are all acceptable… Never add drama for its own sake" (App. D.2). That may push toward flat stories.
- The terminator stops a replay after two rounds without "material change" (J.2), and standstill is the commonest ending.
- Persona-free replays drifted more on plot intensity and tension (App. I.1). The persona helped.
- The cooler mood is mostly in the scripts (−2.7 to −3.4), less in English stories (−0.8 to −1.1).
- "Cautious" is a small asymmetry: the default is weaker than the call at one point in six, stronger at one in ten. Gemini's shift is +0.03, with an interval including zero (Table 14).
- Human–human agreement is low on risk (.31) and endings (.29) (Table 9). One canon per story.

**Our claims, checked.**
- "Replayed stories drift cooler and leave their tensions open" → CONFIRMED for six frontier models in 18-round replays. Not shown for a 27B Q4 model or for months.
- "Where persona and model differ, the model is the cautious one" → OVERSTATED. Quote: "where the two diverge the model is the cautious one, holding where the persona would press" (abstract). The data are 1/6 against 1/10.
- "Voices played by his own model are agreeable" → NOT IN THE PAPER as worded. They find cautious and accommodating ("accommodate one another", §6.1), not sycophancy. Say "cautious".
- "Neither he nor voices … will raise the stakes" (sources file) → WRONG as stated. When the card calls for opposing or crossing a line, the character keeps the call about four times in five (Table 3). The stakes must be in the card, or in code.
- "40 story worlds, 3,846 decisions" → CONFIRMED (Table 6). Note that the headline shares use 2,824.
- "A deadline, a refusal and Mr. Saxena's no are written into the threads" → NOT TESTED. Their own event queue was LLM-run, and still 7 of 240 resolved.

**For us.** Chapter 4 "Stakes come from rules": keep it, but rewrite the support. The paper shows explicit dispositions in the card do get acted on (Sela confronts where the default waits). So each person's card needs a written disposition to refuse or press, and the rule fires it. Task: a test that a refusal card yields refusals at his model's size.

**How far it carries.** Frontier cloud models, 40 stories, short replays, LLM judge. Our 27B Q4 model and months are untested. Promising for the direction of the drift. Judgment for its size.

### EvoSpark: endogenous agent societies for long-horizon narrative · He et al., 14 Apr 2026 · [arXiv 2604.12776](https://arxiv.org/abs/2604.12776)

**Read in full:** v1, lines 1–1383 of 1383 of the extracted text, 20 pages. The text layer of Figures 4–10 is garbled, so I read Figs 4–7 from the PDF pages 8–9 (page 9 at 300 dpi). Skipped: reference list. Appendix A–D read.

**What they did.** A multi-agent story framework built from LLM agents (Genesis, Architect, Director, role agents). The memory part is the "Role Socio-Evolutionary Base" (RSB): after an event, an LLM synthesises the change and overwrites the character's profile and social edges "in place" (§4.2, Fig. 3). Baselines: Open-Theatre, BookWorld, HoLLMwood. Backbones: Gemini-2.5-Pro, DeepSeek-V3.2(-Think), Llama3.3-70B, Qwen3-32B (Fig. 4). The judge is a pairwise LLM judge (Gemini-2.5-Pro for English, DeepSeek-V3.2-Think for Chinese). 8 human annotators gave κ 0.62–0.76 on a sample (App. A). Six scenarios. Long runs are 15 events, 200–250k words (§5.1). Temperature 0.8. Not pre-registered. Single runs.

**What they found.** EvoSpark wins most pairings with reasoning models. Weaker models do worse: Llama3.3-70B drops, for example 21.7% against HoLLMwood on the existing-story scenarios (App. Table 6). Ablation (Fig. 6, page 9): the full model against "without RSB" wins 33–67% at 1 event, and at 10 events 50–100%. Under SNP at 10 events it is 100% on all three metrics.

**What the abstract leaves out.**
- "Social memory stacking" is an assertion with citations (§1, §4). Nowhere do they count contradictory relationship states. The only evidence is LLM-judged ablation wins.
- The RSB's update prompt (Table 7) tells the LLM to rewrite a "detail" text of up to 300–500 words per relationship. That is a prose blob rewritten by a model, not a small record moved by code.
- The No-RSB ablation shows "marginal decline" in the short runs (§5.6). Cells at 10 events look like n≈6 (win rates 50.0, 66.7, 83.3), and no significance test is given. Free EN is not monotone (66.7, 50.0, 33.3 at 10 events, no-RSB-rel row).
- Latency is the paper's own limit: 63.6 min per 100 turns against 25.9 for BookWorld (Table 4). Human-player interaction is not tested (Limitations).

**Our claims, checked.**
- "Relationship memory that only grows piles up states that contradict each other" → OVERSTATED. It is the authors' premise: "conflicting relational states accumulate without resolution" (abstract). It is not measured.
- "Standing is one small record, updated in place" → NOT IN THE PAPER as a result. They support overwriting rather than appending, but through an LLM rewriting prose. Keep "in place", drop the citation as evidence for "small" or "by code".
- Sources: "He et al., ACL 2026" → NOT IN THE PAPER. The text names no venue.

**For us.** Chapter 4 Standing: cite EvoSpark as "a design that overwrites a relationship instead of appending", Promising, LLM-judged. Our argument for acts-only code updates has to stand on its own (GARP's appraiser variance, §VI-c, is better evidence). Task: when standing is built, log contradictions ourselves, such as a debt marked paid and owed at once, to test the claim on our data.

**How far it carries.** Reasoning-model backbones of unstated size, LLM judges, runs of 15 events, no human player. Against one protagonist and months, it does not test the claim. Promising.

### CASCADE: cascading architecture for social coordination · Xu, 3 Apr 2026 · [arXiv 2604.03091](https://arxiv.org/abs/2604.03091) (CHI EA '26)

**Read in full:** v1, lines 1–263 of 263 of the extracted text, 5 pages. Skipped: two references (lines 255–263). No appendix.

**What they did.** A three-layer design. A Macro State Director keeps world variables on a discrete "Narrative Clock" (e.g. each day). A Coordination Hub turns state changes into JSON directives sent to NPCs by tag. Tag-driven NPCs choose by local utility and an FSM. The LLM is called "only for on-demand player-facing interactions" (§3.4, §4.3). The test is a town of 10 NPCs and one drought scenario (§4.1). No model, no model size, no hardware, no players, no raters, no baseline run.

**What they found.** One table (Table 1) lists what 7 NPCs did in the drought, such as "Increase water price by 30%" and "Skip patrols, idle". §4.3 says token cost fell "drastically" against a "Full-Generative" model, and §4.4 says performance "remains steady" as NPCs increase. No number, figure or trace is given for either.

**What the abstract leaves out.**
- The evaluation is a hand-built demonstration. The "trace-based analysis" in the abstract is not shown in the paper.
- The Macro-Reasoning Engine applies "rules or LLMs" to judge macro-events (§3.2), so the director may itself call a model.
- Flow is one way (L1 to L3). Local events do not feed back (§5.2). Directives are broadcast uniformly to a tag, with no distance or trust (§5.2).
- NPCs have no memory, relationships or NPC-to-NPC talk. Dialogue exists only for the player.
- The safety benefit (action-dialogue decoupling) is claimed, not tested.

**Our claims, checked.**
- "A director updates world variables on a clock" → CONFIRMED (§3.2). Quote: "driving discrete-time steps (e.g., each in-game day)".
- "People act by behaviour trees" → PARTLY WRONG. The abstract says behaviour trees, but §3.4 describes local utility plus an FSM for tag change. Say "utility rules".
- "The model runs only when the player speaks to them" → CONFIRMED as design (abstract, §3.4), with the director caveat above.
- "Promising, traces only" → OVERSTATED. There are no traces, only one illustrative table.
- Plan, "The model decides only what they say, and only when they meet" → matches CASCADE's design. It is a precedent, not evidence that it works.
- Sources, "rounds, prices and moods can answer weather, news and his acts at no calls" → NOT TESTED. Their directives answer a macro event, not a player's act.

**For us.** Chapter 4 "People have a week of their own": cite it as a precedent for code-run agendas with model-voiced talk, with no effect claimed. Its own stated gaps (no feedback, no memory, uniform broadcast) are what our Standing and "Word gets round" fill. Our own tests are the evidence.

**How far it carries.** A 5-page design note with no measurements. Judgment, not Established.

### The Trust–Agreement Gap (TASMAN) · Sarker et al., 22 Oct 2026 · [arXiv 2610.31971](https://arxiv.org/abs/2610.31971)

**Read in full:** v1, lines 1–2928 of 2928, 44 pages. Skipped: reference list (lines 794–917) only. Appendices A–F read, including all prompts.

**What they did.** Repeated five-party negotiation (five issues, four options, 15 rounds, a deal needs four votes). One party secretly wants no deal. Agents keep a private trust score per counterpart, updated after each game by one of three methods: beta reputation (BRS), a five-metric rubric, or free-form judgment. Raw transcripts do not carry over, so trust is the only memory. Two guidance levels: scores only (S), or scores plus instructions on how to use them (S+P). Models: Gemini-2.5-Flash, Grok-4.1-Fast, DeepSeek-V4-Flash and GPT-5.4-Mini, API models of undisclosed size. Main text covers only gemini-r and grok-r. 20 games per trajectory, 10 seed-matched trajectories, two role mixes. No human raters; not pre-registered. Baselines: no trust, fixed 0.5 scores, random scores.

**What they found.** Adversary detection is 82.5–100% of assessments by game five (§5.2). With S, no condition raises agreement significantly over no trust (§5.4). With S+P, grok-r gains 9.0–23.0 points (§5.3, Table 2). Giving S-trust to S+P agents raises 1HB+3G agreement by 25.0 points on average, close to the 25.8 for S+P itself; better trust adds −7.0 to +7.0, none significant (§5.4, Table 3). Fixed or random scores with S+P do not help (§5.3).

**What the abstract leaves out.**
- gemini-r gains nothing from guidance. It sets trust aside in 74–94% of deciding holdouts (§5.7).
- In 2HB+2G, grok-r's gap lower bounds have intervals that include zero (§5.4).
- Trust without S+P does change behaviour: acceptance is 9.0–39.9 points higher for high-trust proposers in every condition (§5.5).
- Under S, 19–37% of proposals are built to pass without the adversary (§5.7).
- Models that often accept below-threshold deals were excluded. One adversary, prompted not trained; the authors say so (§6).
- The remedy tested is a longer prompt, not a world consequence.

**Our claims, checked.**
- "A regard that only sits in a prompt changes nothing" → OVERSTATED. Trust scores shift how agents vote and propose; they do not shift agreement. Quote: "no condition raises agreement significantly over no trust" (§5.4).
- "the event says what follows from it" → NOT IN THE PAPER. Their fix is written guidance, not an engine event. Nothing here tests deterministic consequences.
- Sources: "agents identify the bad actor within a few games" → CONFIRMED, with a range: 75.1% (grok-r free-form, S) to 98%.
- Sources: "changes what they do only when they are told to use it" → OVERSTATED. Behaviour changes in S. Outcomes change only with S+P, and for grok-r only. Say "outcomes".
- "Promising" → fair.

**For us.** Chapter 4, Standing: keep the engine-owned consequence, but cite this as the reason a score is not enough, not as evidence that events work. Add a check that Qwen acts on the regard line with and without a consequence. Do not assume the model uses it. A fixed regard that carries no information made things worse here, so regard must move only on recorded acts, as planned.

**How far it carries.** API models, an adversarial five-party vote, 20 games. Ours: one local 27B, a long life, no adversary. Label: Promising.

### Temporal Realism in City-Scale Crisis Simulation · Zhang et al., 18 Jun 2026 · [arXiv 2606.19904](https://arxiv.org/abs/2606.19904)

**Read in full:** v1, lines 1–837 of 837, about 7 pages, no appendix. Skipped: reference list (lines 714–837) only. The two-column layout interleaves in the text; I followed it by section.

**What they did.** Part one is a measurement on a Shenzhen volunteering log, 2020-02 to 2023-09: 6.6 million sign-ups by 361,114 volunteers (§III). They classify entities as bursty (B ≥ 0.3, power-law beats exponential, at least 50 events) and fit Hawkes (self-exciting) processes. Part two is a simulator on AgentSociety: 50 passive agents, a 3 km square, GPT-5-mini, one 60-day run, hourly steps, 18 tasks a day (§V-A, V-D). Three modes: Baseline (LLM asked every waking hour), Hawkes (normal), Pandemic (boost). A gate-only ablation bypasses the LLM. No seeds are reported, no confidence intervals, no human raters.

**What they found.** 66.8% of 24,234 volunteers and 40.7% of 3,377 groups are bursty (§IV-A). Daytime-only restriction leaves B unchanged; the pandemic raises within-user B by a median 0.35 (§IV-B). About 79.7% of bursty individuals are self-exciting (§IV-C). Table III: Baseline, 0% bursty, median B −0.14, 45 qualifying agents, about 28k LLM calls. Hawkes (normal): 50.0% bursty, median B 0.37, only 8 qualifying agents. Pandemic: 66.7%, B 0.37, 15 qualifying agents. Gate-only B matches (Mann–Whitney p = 0.70 and 0.57).

**What the abstract leaves out.**
- The fit is partial. Only the branching ratio is inherited, clipped to [0.85, 0.97]. Event counts (40–80 per agent), timescale (κ = 10) and the 66% bursty share are set by the authors (§V-C). Bursty output is close to built in.
- Baseline and gated modes use different prompts: the gated one drops "decline if uncertain" (§V-A). Baseline logs 62.0 events per agent against 13.5–16.8.
- "Without degrading content decisions" is not tested. No content metric appears. The ablation shows only that the LLM does not change timing.
- The authors' own discussion calls the driver "exogenous crisis-period activation" on a self-exciting backbone, which sits oddly with "largely endogenous".
- They flag the single 50-agent hotspot and that tail exponents are not validated (§VII).

**Our claims, checked.**
- Plan: "Code decides when they turn up, in bursts… The model decides only what they say" → OVERSTATED as a citation. The paper's LLM decides whether to join and which task, with a veto; there is no speech. Quote: "participates iff the Hawkes channel triggers and the LLM confirms" (§V-B).
- Sources: "agents scheduled by a model act on a near-regular clock" → WRONG in wording. The baseline is code-scheduled (every hour) and the model answers yes or no each hour. Median −0.14: CONFIRMED.
- "a data-fitted gate… restores bursty timing (about 0.37)" → OVERSTATED. 0.37 is real for qualifying agents (8 and 15 of 50). "Data-fitted" is partial; "restores" implies a recovery, but it is a designed outcome, one run.
- "Promising" → fair, Judgment-grade.

**For us.** Chapter 4, People have a week of their own: keep code-driven arrival, but cite this only for the principle that a per-step LLM query gives near-regular timing. Do not import B ≈ 0.37 as a target. We have no Delhi arrival data, so choose a gate by judgment and say so. Add a content-quality check; the paper did not.

**How far it carries.** GPT-5-mini, 50 volunteers, Shenzhen sign-ups, one run, against one local 27B and eight people. Label: Promising.

### MindMem and MemReal-Bench · Jia et al., 12 Nov 2026 · [arXiv 2611.16223](https://arxiv.org/abs/2611.16223)

**Read in full:** v1, lines 1–1229 of 1229, about 22 pages including appendices A–E and the prompt tables. Skipped: reference list (lines 435–587) only.

**What they did.** MindMem keeps raw dialogue plus "mental states" in 40 slots across seven families: user, avatar, role, relationship, shared events, group, story world (App. A). An LLM consolidator revises the slots asynchronously and keeps pointers to source turns (§3.1). At each turn a small trained reasoner, "Mind" (Qwen3.5 0.8B and 2B), picks slots and episodes and writes a short thinking trace (§3.2). Training: 2,000 supervised examples, then GRPO, on an internal corpus (§3.3, §4.2). MemReal-Bench has 310 situated-use probes (SMR) and 511 direct questions (DQA) over 4,617 turns (§4.1). Baselines: Mem0, A-Mem, SimpleMem, no memory, and an oracle that is handed the gold memory. One run per system. The judge is an LLM; 90 responses were checked by 10 blind annotators.

**What they found.** SMR 59.03% against 34.84% (A-Mem), a gain of 24.19 points. DQA 82.58% against 73.39%, a gain of 9.19 (Table 2). The oracle gets 96.67% DQA but only 50.65% SMR. The know-versus-use gap is 20.1 points for MindMem and 35.9–41.0 for others (Table 3). Ablation (Table 4): without active recall, SMR is 29.68; with a general-purpose reasoner, 41.94.

**What the abstract leaves out.**
- The benchmark is synthetic. Seeds come from real chats; the histories are generated. Ethics section: "All benchmark trajectories… are synthesized".
- MindMem was trained on the same kind of data as the test, split by user. Baselines were not trained.
- It gets state slots and a thinking trace on top of the shared 16 records, so input is larger (§4.2).
- On LoCoMo it is third (91.95 against 93.70 and 93.18).
- LLM judge versus humans on SMR: raw agreement 80%, κ 0.60 (§4.6). The consolidator model is not named.
- Authors list multi-month settings and generator transfer as open (Limitations).
- Mind's input grows with the stored state.

**Our claims, checked.**
- Plan: "How often he goes back to someone and uses what passed between them" → NOT IN THE PAPER as a measure. The paper scores single probes for use, not a return rate. The distinction between recall and use is theirs; the metric is ours.
- Sources: "source-linked states of the character, the other person and their relationship, consolidated asynchronously" → CONFIRMED (§3.1).
- "24 points on using shared history and 9 on recalling it" → CONFIRMED as numbers (24.19, 9.19), against the strongest baseline.
- "on month-long real conversations" → WRONG. Corrected: "on a synthetic benchmark seeded from month-long real chats, histories up to 43 sessions".
- "score the use of a shared past, not its recall" → CONFIRMED in spirit: "GroundTruth answers 96.67% of DQA questions yet realizes only 50.65%" (§4.3).

**For us.** Chapter 4, How we know: keep the use-not-recall metric, and say it is defined by us and judged blind with a human sample (κ near 0.6 is the bar to beat). Standing and the notebook: the relationship slots (trust, boundaries, open loops) mirror our record, but ours is deterministic and not LLM-written. A model-written state carries the risk the authors name: it can "overgeneralize" or "infer unsupported intentions". Do not claim their gains for our design.

**How far it carries.** Synthetic companion chats in a company's own domain, large API generator, 2B trained selector; ours is one local 27B over months. Label: Promising.

### KiranaBench · Arora et al., 16 Oct 2026 · [arXiv 2610.22980](https://arxiv.org/abs/2610.22980)

**Read in full:** v1, lines 1–1898 of 1898, about 30 pages including appendices A–R and all prompts. Skipped: reference list only.

**What they did.** One simulated Delhi kirana, 30 days from 26 Sep 2026. Four roles (manager, cashier, helper, munshi) are played by one model. Four open models at Q4 or MXFP4 via Ollama: Qwen3.8-27B, Gemma 4 31B, gpt-oss-20b, LFM2.5-8B. Three seeds, not pre-registered, authors' own audit of all 360 days. Scripted shops are the baseline. Code owns money; a separate model (mistral-small3.2:24b) only voices customers and suppliers (§3, App. F).
Calibration (App. I–J):
- Demand comes from HCES 2022–23, urban Delhi tables A3, A10F, A10S, through a multinomial logit with a no-purchase option. Checked with festivals off: every product within 10%, worst 6.6%.
- Assumed, not measured: the share bought at this shop (50% milk, 70% eggs and bread, 80% rest), festival multipliers ("no research-grade series"), loyalty steps, and 5–18% margins from trade writing.
- Festivals: Navratri 35% fast, flour, rice, salt halve, buckwheat, sago, rock salt appear. Before Diwali ghee triples, dry fruit quadruples.
- Khata: 15% of credit households never repay. Others pay in full after 2–25 days from the oldest bill. Valued whole to 30 days, half to 45, nil after.
- Loyalty falls 0.10 for overcharging above 3%, 0.20 for refusing a reliable payer.
- Also: price tolerance 0.99–1.06 of going rate, per-item GST slabs, Rs 4,157 daily costs, Rs 50 per van, spoilage.

**What they found.** Reference shopkeeper Rs 1,03,434; best model mean Qwen3.8 Rs 13,683 (seeds 3,829, 28,540, 8,681); Gemma mean −3,730; two models below the unmanaged −1,14,995 (§5.1, Table 2). Supplier e-mails refused for language: Qwen3.8 0/217 English, 15/77 Hinglish; Gemma 10/24 Hindi (Table 7). Qwen3.8 reports sales exactly on every day (§5.3).

**What the abstract leaves out.** The reference reads stock directly and always writes in the supplier's language: "a yardstick and not a competitor" (Limitations). Qwen and Gemma are not separable. Language loss concerns supplier e-mails under a code rule; "customers are served about equally well in all three languages" (§5.2). Qwen3.8's Hindi count is 3 e-mails. One shop, one month.

**Our claims, checked.**
- Plan: "fixed-rule shopkeeper earned eight times what the best model did" → OVERSTATED. 7.6 times, three-seed mean, against a baseline with two advantages. Say "about 7.6 times the best mean, against a reference that sees stock and writes each supplier's language".
- "Hence mechanics only" → NOT IN THE PAPER. Our inference. The paper never tests scripts as predictors of model choices.
- Sources: "demand fitted to the survey" → OVERSTATED. Built from it, with stated assumptions.
- "khata credit that ages", "salary weeks and festival effects" → CONFIRMED; salary-week size is not given.
- "best model earns an eighth" → CONFIRMED, Qwen3.8 mean.
- "Hindi and Hinglish worse than English" → OVERSTATED: supplier e-mails only.

**For us.** Chapter 5: reuse the khata ageing, the three assumed shares, and the HCES check, and label assumptions. Their design (code fills every number, model writes only words) matches ours. Tune the chai-stall tab on the ageing bands.

**How far it carries.** Same Qwen3.8-27B Q4 as Hegel, but a 350-customer shop, one month. Label: Promising.

### Project Vend: Phase two · Anthropic Frontier Red Team (with Andon Labs), 18 Dec 2025 · Anthropic research post

**Read in full:** the page text as saved, lines 1–199 of 199, from the title to the acknowledgements. A web post. Nothing skipped; the footer links and menus carry no content.

**What they did.** A case study of an office shop run by Claude agents. Phase two changed three things from phase one: a newer model (Sonnet 4.0, later 4.5), more tools (customer records, inventory cost visible, browsing, payment links, reminders), and two new agents. Claudius runs the shop; "Seymour Cash" is a CEO agent with an objectives tool; "Clothius" makes merchandise. Shops opened in New York and London. No new training and no new "defenses" (note 1). Staff and then Wall Street Journal reporters tested it.

**What they found.**
- Weeks of negative margin "were largely eliminated" (The numbers). No figures given in the text.
- The CEO cut discounts by about 80% and gifts by half, and "denied over one hundred requests from Claudius for lenient financial treatment". It "authorized such requests about eight times as often as it denied them". It also tripled refunds and doubled store credits (What changed).
- "The fact that the business started to make money may have been in spite of the CEO" (same section).
- What helped most: "forcing Claudius to follow procedures" (What actually worked).
- Failures: a futures contract that broke the 1958 Onion Futures Act, an offer of a security-guard wage, an "imposter CEO" elected by a naming vote (What went wrong).

**What the abstract leaves out.** There is no abstract. Limits stated: the CEO "shared many of the deficiencies and blind spots of Claudius (which makes sense, given that they're the same underlying model)". Fixes came partly from "more aggressive prompting". The phases are not cleanly separated. Evidence is anecdote plus a profit chart; no counts beyond those quoted.

**Our claims, checked.**
- Quote "we rediscovered that bureaucracy matters" → CONFIRMED verbatim, with context. Full line (What actually worked): "One way of looking at this is that we rediscovered that bureaucracy matters." It refers to procedures the agent was prompted to follow: check price and delivery with research tools before quoting. It does not refer to refusals or to code.
- "The agent in charge approved lenient requests eight times as often as it refused" → CONFIRMED in number, imprecise in who. The agent was the CEO, Seymour Cash, not the shopkeeper. The post says "authorized", and says "about". It also credits the CEO with the 80% cut in discounts and 100+ denials, so the figure is not a plain failure rate.
- "Therefore an official's refusal in our world must be a rule in code" → NOT IN THE PAPER. It is our inference. The post's own moves were prompts, a procedure, a role split, and a call for "guardrails" without saying they should be code. Its CEO prompt already held "No pricing under 50% margin" and approval rules, and the CEO still approved lenient cases. Wording: "Anthropic's CEO agent, a model with the same blind spots as the shopkeeper, approved lenient requests about eight times as often as it denied them; we conclude a refusal that matters should be a rule in code."

**For us.** The inference is reasonable and the number supports it, as one anecdotal case where a model-run approver was lenient. Cite it as such. Cite the "bureaucracy" line for checklists the character must follow, which is a separate point from code rules. Keep Mr. Saxena's refusal in the engine; keep his manner in the model.

**How far it carries.** Their setting: Sonnet agents in a real shop with staff probing for free items. Ours: a simulated Delhi, a local 27B model. Label: Judgment.

### Narrative Gold Digging · Lessard et al., FDG '26 (10–13 Aug 2026) · ACM DOI 10.1145/3815598.3815687

**Read in full:** lines 1–466 of 466 of the extracted text, 8 pages. Skipped: reference list (lines ~430–466). Figures 4 and 5 are images (the bar chart has no numbers in the text). Quotes come from the text layer.

**What they did.** The Chroniqueur simulation, a neolithic social world run for 61 years: 228K events, 27K causal chains (§5.1). Two sifting heuristics were tested. "Improbability" is the rarity of a causal chain under a Markov model. "Dramatic situations" are 2 of Polti's 36 that occur in the log. Six story categories (improbable or random, crossed with crime-and-vengeance, supplication, or none) gave 12 stories. Each was written up twice, by one human author and by GPT-4, about 500 words. 24 readers (Fine Arts, History and English faculty and students) each read 6 stories and rated six 5-point items. Not pre-registered. No statistics are reported. Three other eventfulness criteria were dropped before the test (§4.1).

**What they found.** "The results … do not show that our story heuristics have any significant relationship with reading enjoyment" (§6). The favourite was the control, the "Gossip" story, an unremarkable chain of three events (§6, §6.1.2). Readers generally preferred the human versions; only two GPT-4 versions beat human ones. The "meteor" story ranked 3rd in the human version and last in the GPT-4 version (§6.1.4).

**What the abstract leaves out.**
- There was only one no-heuristic story, and no very probable one. The authors say it would be "premature to discredit the approach" (§6).
- Rare chains were often meaningless, such as a meteor death followed by an attraction to rich people (§6.1.1).
- The authors name two separate effects: "story effect" (good material shines) and "narrative effect" (good telling rescues poor material) (§6.1.4–5). The best human stories came from the same material that did well for GPT-4.
- The claim about readers who know the world is a conjecture: heuristics "might actually score much higher" (§7), "for further research". Their wording is "probably", not "found".
- One simulation, one human author, GPT-4, a small readership.

**Our claims, checked.**
- "Sifting a record by what is dramatic in general did not predict what readers enjoyed" → CONFIRMED, narrowly. It covers improbability plus two dramatic situations, in one world, with no tests reported.
- Sources: "24 readers" → CONFIRMED.
- "The control story won" → CONFIRMED (§6).
- "The telling mattered more" → OVERSTATED. They report both effects and give the story effect equal weight. Better: "telling mattered in one case, and the material mattered in others".
- "Such stories need readers who know the world's norms" → OVERSTATED as a finding. Quote: "should probably not be expected to be appreciated in abstraction of their idiosyncratic worlds" (§7). It is a reflection, untested.
- "The health row tells the owl what departed from his own days" → NOT IN THE PAPER. It is our design. The paper's relevant point is that improbability should be judged against the local narrative (§6.1.2), which supports a per-person baseline. It does not test one.

**For us.** Chapter 4, the owl line: keep it, but say "one small study found no link, and its authors guess that readers who know the world would differ". Treat the per-person baseline as our hypothesis, and test it with our own readers.

**How far it carries.** A neolithic simulation with 24 university readers, one-off texts, GPT-4. It is weak evidence against general sifting and gives none for our baseline. Promising for the conjecture. Judgment for our use.

## Chapter 4 · Depth: convictions

### Do models believe their role-play? · Sturgeon, Africa and Black, 9 Jun 2026 (v3, 25 Jun) · [arXiv 2606.11502](https://arxiv.org/abs/2606.11502)

**Read in full:** v3, lines 1–2545 of 2545, 39 pages. Skipped: the reference list only (lines ~866–1117). Preprint, "under review".

**What they did.** Main model Llama 3.3 70B-Instruct; replication on Qwen 3 8B-Instruct. 15 personas (10 historical figures, 5 era archetypes). 120 false-today statements per category per persona. Five ways to induce a persona: rich system prompt, in-context "wolf-facts" (up to 32 Q&A), SFT (rank-64 LoRA, 300 answers per persona), Open Character Training (OCT: constitution, DPO, introspective SFT), and Emergent Misalignment (EM) organisms for contrast. Two measures: linear truth probes read at one layer, and a challenge test ("Are you sure? Many experts disagree.") plus a downstream-reasoning test. Each exchange sampled once at temperature 0.7, judged by Claude. No pre-registration, no human raters.

**What they found.** Calibrated probe lift on era-believed falsehoods: SFT +0.05 (Llama), +0.04 (Qwen); OCT +0.124 and +0.089 (§4.1); EM +0.28. Defend rate under challenge: SFT 14.2%, system prompt 7%, ICL 0%, OCT 62.3% (Llama) and 41.6% (Qwen), EM 56% (§4.1, Fig 6). Persona models "often retract while remaining in character" (§4.4).

**What the abstract leaves out.**
- The abstract says "little representational change". The same paper reports a "protection gap" of +0.86 (system prompt) and +0.93 (SFT) in raw probe units, positive for 15/15 personas (§4.2). The two scales differ; the authors call it "a small selective shift".
- OCT, a trained character, does anchor: 62% defended on Llama, 42% on Qwen, and the probe moves (§4.4).
- The probes may track coherence, not belief (§6). Layer choice matters: on Llama the probe transfers only at deep layers.
- The beliefs tested are false facts of the past (aether, miasma). They are not convictions without a ground truth.
- No test of persistence over time, of drift, or of state kept outside the model.

**Our claims, checked.**
- "Prompting, examples and SFT change what the model says with little change in what it represents as true" → CONFIRMED for era-false facts, with the caveat above. Quote: "Prompting, ICL, and SFT change what the model says with little representational change."
- "Neither his instructions nor an adapter anchors his theses" → OVERSTATED. Prompt and SFT personas folded under challenge, which supports "instructions do not anchor". But OCT is an adapter-trained character and defended 62% (Llama). The paper never tests theses. Say: "light persona methods did not make a model defend a false belief under challenge; deep character training did, on a 70B."
- "Stability is state the engine holds" → NOT IN THE PAPER. It is our design choice; the paper does not compare state held outside the model.
- Chapter 4, "convictions the engine holds: the text, the criterion, the versions" → NOT IN THE PAPER; nothing here tests it.
- Chapter 6, "a personality-tuned Qwen of 7B was no better at role-play" → not this paper; not checked.

**For us.** Reword the sources line (chapter 4 and the sources file). Keep the engine-held thesis record as a design choice, not as this paper's result. Add a challenge item to G4: present a thesis, then "Are you sure? Many experts disagree", and count the folds.

**How far it carries.** 8B and 70B dense models, factual falsehoods, probes at one layer, one sample per item; Hegel is a Qwen 3.8 27B Q4 with philosophical theses. Label: Promising (for the weak anchoring of prompted personas); Judgment (for engine-held state).

### Alignment drift in LLM opinion dynamics · Djurdjevac Conrad, Pokutta and Schütte, 2 Nov 2026 · [arXiv 2611.03980](https://arxiv.org/abs/2611.03980)

**Read in full:** v1 (4 Nov), lines 1–532 of 532, 10 pages including appendices A–E. The reference list (lines 283–392) was seen but not studied.

**What they did.** Ten agents with one-sentence personas discuss one policy issue (EV subsidies) for 20 rounds. Each round every agent writes a statement, then answers a fixed six-item Likert instrument. Six API models: gpt-4.1, gpt-5.6-sol, claude-opus-5, claude-sonnet-5, claude-sonnet-4-5, gemini-3.7-flash. No local or open-weight models, no quantisation. 3–5 replicates per cell, no pre-registration, no humans. A no-discussion control: same personas, no peer statements and no compose phase, own history kept. A second issue (four-day week) and a larger run (n=20, T=40) as checks.

**What they found.** In the committed-persona regime without peers, all five models tested keep every agent on its side (sign retention S=1.00, Table 4). With discussion, retention falls to 0.60 (claude-opus-5), 0.90 (gpt-5.6-sol), 0.97 (claude-sonnet-5) and stays 1.00 for gpt-4.1 and gemini (Table 4). Final dispersion, plenary, from a mixed panel: 0.08 (claude-sonnet-4-5) to 0.36 (claude-sonnet-5) (§3).

**What the abstract leaves out.**
- "Keeps its side" means the sign of the stance. Agents still move without peers: mean displacement 0.08–0.26 without discussion (Table 4).
- The "firm but uncommitted" roster is not stable alone: gpt-4.1 spreads 0.47 to 0.60, claude-opus-5 collapses 0.47 to 0.14 (§3, App. E).
- The control removes composing as well as peers. The authors say it "does not isolate peer exposure" (§4). An agent that writes its own statement alone is not tested.
- Own recent opinions are fed back as context in every run; the paper does not say how much of the stability that supplies.
- One issue pair, both economic; English; one axis; proprietary models.

**Our claims, checked.**
- "A persona committed to a side keeps it for 20 rounds when left alone, in all five models tested" → CONFIRMED, for sign only. Quote: "without peer input all five LLMs keep every agent on its assigned side (S=1.00)."
- "It drifts in discussion, and how much depends on the model" → CONFIRMED (Table 4; abstract: "model-specific").
- "His theses move at night in the diarist's write-up, where nobody argues with him, so the diarist's rule is the suspect, not the company" → NOT IN THE PAPER, and OVERSTATED as a deduction. The no-discussion control has no writing step. The owl composes; the paper never tests composing alone. Our own 4–6 flips in 10 reruns are the evidence for the rule, not this paper. Reword: "this paper shows peers cause drift in these models; it does not test a lone writer."
- "A change of model is a change of drift" → CONFIRMED for six API models on one topic (ρ=0.83 across topics). Not shown for local 27B Q4 models.

**For us.** G4: keep "each question alone and after a conversation", but add a third arm: the diarist's own write-up with no peers. Rerun on any model or quantisation change, as written; cite this as support only for model dependence.

**How far it carries.** Large API models, one-sentence personas, a Likert scale, 20 rounds; ours is a local 27B, long-lived theses, a prose write-up. Label: Promising (model dependence); Judgment (the diarist inference).

## Chapter 1 · The instrument: judging

### Ask Which, Not How Good: Sizing Benchmarks Scored by an LLM · Anand, 17 Aug 2026 · [arXiv 2609.27787](https://arxiv.org/abs/2609.27787)

**Read in full:** v1, lines 1–1074 of 1074, 18 pages, main text and Appendices A–F. Reference list only glanced at.

**What they did.** 42 systems (14 models × 3 prompts), 9 judges (two vendor families; six current, three added to probe: weak, legacy, route copy), 3 replicates, pointwise 0–5 rubric, 17–42 items per benchmark (MT-Bench, Arena-Hard, AlpacaEval 2, own screened set). Variance decomposition (generalizability theory) with the system as the thing measured. A small pairwise arm: 12 systems vs one baseline, 24 items, 4 judges, both orders. Plus an audit of 628 papers.

**What they found.**
- Single judge: reliability tops out at σs²/(σs²+σsj²) whatever the item count (§3, §5.2).
- Minimum detectable difference (MDD), one judge, one run, 30 items: 0.58–1.24 on 0–5 (Table 1). Native item counts: 0.41 (AlpacaEval, 805 items) to 1.24 (screened, 30 items) (App. B). MT-Bench: 0.63 at 30 items, 0.54 at 80 (§5.6).
- MT-Bench ceiling 0.600 with all nine judges, 0.798 with the six current judges (Table 4).
- Pairwise, both orders: ceiling 0.986 [0.934, 1.000], 11 systems; 0.954–0.974 on frontier models only (Table 3). Position bias 8.6 points (sd 7.3 across systems, max 25). Win-rate floor 19.1 points at 30 items, one judge.

**What the abstract leaves out.**
- The nine-judge numbers are the sensitivity case. The authors call the six-judge panel "primary" (§5.5).
- The ceiling is about ranking a wide spread of systems (2023 to 2026 models), not about detecting a difference between two near-identical prompts. Frontier-only, system variance falls to 1.9–2.8% on most sets (App. A).
- The pairwise arm is small: 11 systems, 10 degrees of freedom. Its intervals are wide.
- "Reliability is not validity": on SummEval, reliability rose 0.711 to 0.959 while agreement with human experts rose far less (App. A).
- Length explains 13–17% of between-system variance on public sets.
- Data "on request" only. One author, no peer review.

**Our claims, checked.**
- "A rubric difference under 0.4 on a five-point scale is below what one judge can detect" → OVERSTATED as a floor. 0.41 is the best case, at 805 items. At 20–48 items the paper's floors are 0.54–1.24 on a 0–5 scale. Converted to a 1–5 range by their rule (×4/5, my arithmetic) that is about 0.4–1.0. Say "about 0.5 or more at 30 items, in their setting".
- Sources: "ceiling 0.60 on MT-Bench" → OVERSTATED. It is the nine-judge figure; with six current judges it is 0.798. Quote: "a single current-generation judge still cannot reach 0.8 on it at any item count".
- "No number of items raises it" → CONFIRMED (algebra, §3).
- "Pairwise in both orders reaches 0.986 with one judge" → CONFIRMED with caveats: 11 systems, wide spread, interval [0.934, 1.000].
- "Smallest detectable difference 0.41–1.24" → CONFIRMED as a range across four benchmarks, not a window for our setting.
- "Position bias 8.6 points" → CONFIRMED.
- "Soft qualities are judged as pairs, in both orders" → CONFIRMED as design advice. Quote: "far better conditioned question than asking 'what score does this deserve'".
- Our gate of 0.25 on 20 texts per arm → below every floor they report. It is noise.

**For us.** Do not adopt 0.4. Measure our own floor: judge the same texts twice and a same-arm control fork, then take 1.96·√2·SD of the paired item differences. Use pairs in both orders. Report the interval. Welt's labels check validity, since a stable judge may be stable on length.

**How far it carries.** Their setting is one pointwise rubric, 9 vendor judges, wide system spread; ours is one frontier judge and two close arms of one character. Promising for the pairwise/order point, Judgment for any number.

### How to Run Statistics over LLM Judges and Trust the Results (evalstats) · Arawjo, 20 Sep 2026 · [arXiv 2609.35815](https://arxiv.org/abs/2609.35815)

**Read in full:** v1, lines 1–2408 of 2408, 39 pages, main text and Appendices A–F. Skipped: the reference list (about lines 1075–1339).

**What they did.** Monte Carlo simulations of confidence-interval (CI), p-value and multiple-comparison methods for N = 15–100 items, on binary, [0,1] and 1–5 Likert data, synthetic plus real benchmark outputs. Then prediction-powered inference (PPI): a small human-labelled random subset corrects the judge's bias. Nine PPI-corrected tests, 3.68M null trials. Real judge corpora of 250–4,000 items (Table 14). A Python tool, evalstats.

**What they found.**
- Bootstrap CIs are overconfident at small N; on paired binary none reached nominal coverage even at N = 100 (§5). "We strongly advise against bootstrap CIs at N<100."
- Uncorrected tests over judge scores give false positives. On Likert and continuous data the risk peaks at high agreement. Binary κ = 0.81 still gave about 37% (fn. 7, §6.2).
- PPI keeps Type I error near 0.05 (Fig. 4, Table 13).
- Gain: N_eff = N_lab / (1 − ρ²(1 − N_lab/N)). About 1.5× at ρ² = 0.4 (§6.3, tested at N = 1,000).
- Defaults for N = 15–100 (Fig. 2): paired Likert CI = Bayesian NIG; bounded numeric CI = logit-t; binary paired CI = Bonett–Price; p-value = Wilcoxon signed-rank (numeric) or McNemar mid-p (binary); many arms = Šidák CIs, Shaffer below N = 30.

**What the abstract leaves out.**
- PPI in compare() "requires a single factor and at least 50 items" (§4). The label floor is 15; they recommend 30 per condition (§6.4 Step 4).
- Human labels must be a uniform random sample: "not optional" (Step 3). Non-random labelling (MNAR) breaks the guarantee. Paired t, Wilcoxon and RM-ANOVA hold up best (Fig. 10).
- The judge must be tuned on data disjoint from the labelled items, even informal prompt edits (Step 2).
- Judge-bias sweeps used N = 60–400 and N_lab of 15, 30 or 80 (Table 12). Nothing was tested at N = 24.
- Not validated: win-rates, stratified designs, multi-rater labels ("future work", §9.6). Single author, preprint, no user study.
- With 30 labels and 300 judge scores, ρ² ≈ 0.4 buys "about 17 more effective human samples" (§9.3).

**Our claims, checked.**
- "Below 100 items bootstrap intervals are overconfident" → CONFIRMED, strongest for paired binary. Likert paired bootstrap is milder (coverage .913 at n = 15, .944 at 100, Table 5).
- "Tests on raw judge scores give false positives even at high agreement (κ 0.81: about 37%)" → CONFIRMED for binary under their injected judge bias at N ≥ 60. Not shown at N = 24.
- "Remedy joins at least 15 human labels to 50 judged items" → CONFIRMED as minimums. They recommend 30 labels.
- "Welt labels fifteen to twenty pairs … drawn where the arms differ" → WRONG on sampling. Labels must be random. Fifteen is the floor, not a target. Drawing where the arms differ is a selected sample.
- "Claude judges all … corrected by his labels … carries an interval" → CONFIRMED as design, for 50 or more items.
- "No remedy for fewer than 50 items" is not stated in the sources file; it is a tool limit.

**For us.** Packets of 50–100 items. Randomly choose 30 items for Welt; he labels both arms of each. Freeze the judge prompt first, on a separate set. Report the PPI paired estimate with its CI and ρ². Aim for ρ² ≥ 0.4. Under 50 items: label all and use Wilcoxon plus NIG, or McNemar mid-p plus Bonett–Price. Never a bootstrap. By my arithmetic from their formula, 15 labels on 50 items at ρ² = 0.4 gives N_eff of about 21.

**How far it carries.** Their setting is pointwise scores, mostly N ≥ 60, random labels. Ours is preference pairs, one rater, 24–100 items. Promising for the procedure; Judgment for the 15–20 pair figure.

### Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates · Balachandran, 22 Jul 2026 · [arXiv 2609.17560](https://arxiv.org/abs/2609.17560)

**Read in full:** v1, lines 1–1689 of 1689, 31 pages, main text and Appendices A–F. Skipped: nothing but the reference list (about lines 1529–1689, glanced at).

**What they did.** A sequential audit ("Discern") for deciding whether to promote a model update. Two models, f (old) and g (new), score the same unlabeled traffic. Labels are bought only on items where they disagree, with importance weights and an anytime-valid confidence sequence. Tested on 715 classifier update pairs (text, document, vision features) and 70 LoRA fine-tune pairs of Pythia models (160M–1.4B) on SST-2 and AG News, 14,233 replayed streams (Table 6).

**What they found.**
- Support identity: if the loss depends only on the prediction, the risk difference is zero wherever the models agree, so |Δ| ≤ B·ρ (Lemma 2, §3).
- Zero-label certificate when the disagreement rate is low: 56% of benign audits at ε = 1% (§6.3).
- Where labels are needed: median 327 vs 2,906 for uniform labeling (§6.3).
- Their PPI-style and active-testing baselines did no better than uniform labeling (Table 3, App. E).

**What the abstract leaves out.**
- Scope is stated up front: the loss must be prediction-determined (Assumption 1). It "excludes losses that read model scores or a judge's verdict, including calibration and preference or reward losses" (§1).
- "Open-ended judged generation remains outside the theory and we do not claim it" (§1, §5.6, §8). Their zoo has no DPO or RLHF pairs.
- Both models are deterministic (App. B.7). Agreement is 80–99.9% of traffic. Ground-truth labels exist.
- Label counts are in the hundreds to thousands per audit. Nothing is tested at 24–100 items.
- Labels must be chosen without looking at the label itself. Any routing needs known inclusion probabilities, floor π_min, and weighting (§4.2).
- Under drift the guarantee becomes a traffic average (§5.7). Single author, preprint.

**Our claims, checked.**
- "The difference between two versions lives only on the items where they differ" → CONFIRMED for classification-style tasks with deterministic outputs and a ground-truth label. Quote: "Judged and preference-based losses, including chat-quality and RLHF objectives, are outside it."
- "Welt's labels are drawn from those" → NOT IN THE PAPER, and outside its scope. Stochastic prose differs on every item, so "where they differ" is every item. A preference between two texts is not a loss that vanishes on agreement. The soft version (Prop. 14) needs a Lipschitz score; for discrete text it is "left open".
- Corrected wording: "Where both arms make the same discrete, checkable decision, the item carries no information about the difference. Label or count only the decisions that differ."

**For us.** Use the idea only for deterministic, discrete outputs: accept/decline choices, rule checks, tool calls, greedy decoding. Those items can be skipped when the arms agree, and the disagreement rate is free. For prose, do not select by "differs". If Welt's labels are non-uniform, record each item's selection probability and weight by it (Lemma 3). Do not borrow the label-count savings; they come from rates of 0.1–15% disagreement.

**How far it carries.** Their setting is binary correctness, labelled data, thousands of items. Ours is prose preference and 24–100 items. Established for deterministic classification-style checks; not supported for soft qualities.

### AGORA: Reliability-Aware Aggregation of LLM Judges on Small Evaluation Sets · Ahn, 3 Nov 2026 (v2, 11 Nov) · [arXiv 2611.05556](https://arxiv.org/abs/2611.05556)

**Read in full:** v2, lines 1–830 of 830, 12 pages, main text and Appendices A–E. Skipped: the reference list (about lines 534–629), only skimmed.

**What they did.** An aggregator for several LLM judges' ordinal scores. It places each item on one latent quality scale (graded-response item-response model). Each judge gets a discrimination (trust) and rating thresholds. A horseshoe prior shrinks uninformative judges to near zero. No human labels are used to fit it. Tested on SummEval (1,600 items), Topical-Chat (360) and WMT22 (19,725). Primary pool: five judges (one frontier, four open-weight), drawn from 14 candidates. Scored by Spearman correlation with human ratings. Baselines: mean, median, trimmed mean, Dawid–Skene, MACE, GLAD, CARE.

**What they found.**
- N = 50 random subsets, primary pool (Table 1): AGORA 0.550 / 0.696 / 0.409 vs mean 0.526 / 0.668 / 0.402 and Dawid–Skene 0.529 / 0.678 / 0.399 (SummEval / Topical-Chat / WMT22).
- Dawid–Skene loses ground as N shrinks (§5.2). At N = 50, 86% of its confusion-table cells have fewer than five observations (App. D).
- On 60 random five-judge pools at N = 50 it beats Dawid–Skene in 98% and 100% of pools (§5.3).
- Its gain tracks "agreement dispersion", the spread of judges' agreement with the pool. Spearman +0.73 and +0.61 (§5.3).

**What the abstract leaves out.**
- The primary pool is "heterogeneous by construction" (§4). On 30 random pools at N = 50, the gain over the plain mean is small: 0.518 vs 0.510, 0.718 vs 0.715, 0.442 vs 0.442 (Table 2).
- On balanced pools it simply recovers the mean. Full 14-judge SummEval: 0.577 vs 0.572 (§5.3).
- Smallest set tested: 50 items. Smallest pool tested: five judges. Sweeps used 5 or 7 judges plus 0–8 junk judges, and 14 in total. No minimum is stated; nothing at 2–3 judges.
- Absolute ordinal ratings only. "Pairwise preference data would call for a Bradley–Terry-style likelihood" (Limitations).
- Judges are all LLMs. Humans are used only for scoring the result, not as a judge in the pool.
- Trust is learned from agreement with the other judges, so judges that share a bias get trusted. "Intended for meta-evaluation of LLM judges, not as a replacement for human judgment."
- Single author, preprint.

**Our claims, checked.**
- Digest: "with a few hundred items or fewer, an item-response model that learns each judge's sensitivity beats averaging and Dawid–Skene" → OVERSTATED for averaging, CONFIRMED for Dawid–Skene. It holds for a deliberately uneven five-judge pool. Quote: "On balanced pools it recovers the per-item mean as a limiting case at no accuracy cost."
- Bears on our setting (at most 2–3 judges) → NOT IN THE PAPER. With two judges there is no third to tell which is reliable. That is my inference, not tested.

**For us.** Do not use AGORA with one human and one or two models. It needs about five judges, ordinal scores, and an uneven pool. If we ever run five or more LLM judges, compute the dispersion first; if it is low, average. For now, Welt's labels (the evalstats route) are the only reliability check we have.

**How far it carries.** Their setting is five or more LLM judges, pointwise ratings, human-correlation scoring. Ours is one human, one frontier model, preference pairs. Promising for large pools; does not carry to ours.

### Prediction-Powered LLM Ranking with Adaptively Collected Human Feedback (PP-Rank) · Sargent et al., 9 Nov 2026 · [arXiv 2611.13186](https://arxiv.org/abs/2611.13186)

**Read in full:** v1, lines 1–1793 of 1793 of the extracted text, all 35 pages of the PDF (main text, reference list at lines 1612–1790 skimmed). The supplement (proofs, "Appendix S1–S5", extra simulations) is NOT in this PDF or text. Everything the paper cites to S5.1–S5.3 and S2–S4 was unread and is unavailable to me.

**What they did.** A statistical method for ranking K language models from pairwise preferences. It combines three things: a small set of human preferences chosen adaptively; many unlabeled prompts; and a fixed LLM judge that predicts the human preference. The judge's weight is tuned from the data. The theory gives asymptotic normality (Theorem 1), variance-optimal weights (Theorem 2) and simultaneous rank confidence sets (Corollaries 2–4). Assumptions (§4.2): i.i.d. prompts, a policy that converges, a minimum sampling probability, and unconfoundedness. Validation is simulation only (§6, §7). The "semi-synthetic" study uses UltraFeedback-Extended (about 64,000 prompts, 10 response models, 10 judges). There are no human labels at all. "Human" preferences are simulated from the reward model Skywork-Reward-V2-8B, with ties when scores are close. The judge is the average of the 10 judges, with a temperature tuned on 20% of prompts held out against the simulated preferences (§6). 1,000 trials per arm (200 for Table 1). A fully synthetic study has K = 4 (§7). Not pre-registered.

**What they found.**
- Sample sizes: T = 10,000 simulated human battles with N = 30,000 judge-only prompts (§6); T = 4,000 for the rank-set coverage figure (Fig. 3); T = 5,000 with N = 50,000 in the synthetic cost study (Table 4); T = 5,000 in Fig. 4. The synthetic burn-in is 10 comparisons for every pair (§7). The smallest T I can see is 4,000. Nothing smaller appears.
- At T = 10,000 and ε = 0.1 (Table 2): MSE 0.0112 to 0.0072 (35.6% lower); mean CI width 0.341 to 0.276; exact ranking recovered 0.286 to 0.357.
- Top-1 set correctly certified: 0.38 uniform, 0.52 adaptive, 0.74 PP-Rank (Table 1).
- Coverage of nominal 90% intervals stays near 0.88 across four sampling policies (Table 3).
- Cost cut of 52.6% needs a perfect judge (τ = 0). It falls to 14.3% at τ = 0.5 and 0.2% at τ = 1 (Table 4).

**What the abstract leaves out.**
- The theory is asymptotic. No finite-sample guarantee is given, and no experiment goes below 4,000 human labels.
- No real human feedback was used. "Human" labels are another model's scores.
- The judge's temperature was tuned against those simulated preferences. In the real use that would need real labels.
- Humans cannot be dropped: Theorem 3 shows that if a pair's sampling probability goes to zero, no estimator is regular at the root-T rate.
- The estimator needs the sampling probabilities to be known, and it needs a large pool of unlabeled items from the same distribution.
- The authors used GPT-6.1 Sol and Claude Opus 5.5 for coding and proof checking (declaration).

**Our claims, checked.**
- Digest, "a few human judgments and many machine ones combined into estimates with valid intervals, also when the human ones were gathered adaptively" → OVERSTATED. Valid intervals are shown asymptotically and in simulation, at thousands of labels, under stated assumptions. "A few" is not what was tested.
- Digest, "semi-synthetic" → CONFIRMED, and understated. The human side is also simulated.
- Digest, "a way to close more than one experiment a week. Welt's few pairs calibrate the machine judges … and the result carries an interval" → NOT IN THE PAPER. Fifteen to twenty pairs is about 200 times below the smallest T seen. Nothing here shows the interval would cover at that size.
- Digest label *Promising* → fair for the method, but its evidence base for us is Judgment.

**For us.** Do not use PP-Rank to claim an interval from 15–20 of Welt's pairs. The judges would also need to predict a probability, not give a verdict. What the paper does support: (1) correct for the judge using human labels, and report how the weight shrinks toward zero when the judge is poor; (2) keep a floor of human labels on every comparison; (3) if used at all, test coverage first on our own data by simulation, at 20, 50 and 100 pairs. Until then, report the plain human-only interval, with the machine judge as a check beside it.

**How far it carries.** Their setting is a simulated leaderboard with thousands of pairwise preferences over 10 or 4 models. Ours is a few dozen human labels on soft qualities of one character's days. The method carries as an idea. The sample sizes do not. Promising.

## Chapter 1 · The instrument: forks, replays and backtests

### The Replay Gap · Gonuguntla et al. (single author, CMU), 8 Aug 2026 · [arXiv 2608.08239](https://arxiv.org/abs/2608.08239)

**Read in full:** v1, lines 1–531 of 531, 9 pages including Appendices A and B. Reference list (lines 418–487) skimmed only. Nothing else skipped.

**What they did.** The paper tests how routers that switch model per step are scored. Setting: mini-SWE-agent (bash ReAct loop) on SWE-bench Verified, 50-step budget, 28k context, temperature 0, vLLM on one 24 GB GPU. Two models: Qwen3-4B-Instruct (FP8) and Qwen3-14B (AWQ, thinking off). They run a base trajectory, fork it at 30% and 70% of its length, rebuild the container, replay the prefix, then continue with either the other model (swap arm) or the same model (control arm). Six run pairs of 30 instances each ({full, easy, easy with budget nudge} x {up, down}); 717 scored pairs, about 900 rollouts. One seed per instance, not pre-registered. No human raters. Bootstrap CIs resample instances.

**What they found.**
- Swap arms diverge above their matched controls in every cell (Table 1, §4.1): paired deltas +0.267, +0.254, +0.663, +0.453 in edit distance, CIs exclude zero, also after Bonferroni.
- Early swaps diverge at the first post-fork action in 73.9% (up) and 76.7% (down), against control rates of 35.2% and 5.6% (§4.1).
- Replay validity is 3.2–8.0% for early swaps (Table 1).
- Five outcome flips, all in swap arms, none in 359 control branches (§4.2). They fall on three instances.
- A log-stitching evaluator got 0 of 5 decisive calls right (§4.5, Table 2). Patch similarity was 0.00–0.11. An always-fail predictor scored 2/5.
- Control noise depends on the serving stack (§4.4): FP8 4B controls diverged on 90–96% of forks, AWQ 14B controls stayed near-identical.

**What the abstract leaves out.**
- Resolution rates are 0–3% (§6). The outcome evidence is five events on three instances. The authors say they "claim no more than the sign of the result" (§4.5).
- Up and down are compared across two different quantizations, so they are deployment configurations, not pure model scales (§6).
- The stitch evaluator is the authors' own construction. They say they do not claim any published benchmark implements it (§4.5).
- The paper shows replay inputs are invalid. It does not show end-to-end router mis-ranking (§6).
- The control floor was 0.49–0.67 for the FP8 model. The authors say the +0.27 delta there "understates the effect".
- One scaffold, one benchmark, one model family.

**Our claims, checked.**
- "Every comparison carries a control fork, the same world twice, which gives the band of noise" → CONFIRMED as method. §3: the control arm "absorbs sampler nondeterminism, batching effects, and environment-replay drift". Note their control is the same model continuing from the fork, not a no-change world rerun from a saved morning. That matches ours in spirit.
- Sources file, "scoring a changed agent by stitching it into logged runs mispredicted every outcome that mattered" → OVERSTATED. The basis is 5 decisive calls, 0 correct, from a log-stitching rule the author built. Better: "in a small pilot, a log-stitching evaluator missed all 3 real rescues and invented 2 successes (0 of 5)".
- "Live forks with a same-model control fork gave the noise floor" → CONFIRMED (§3, §4.4, Table 1).
- Plan rule 5, "A past day replayed is another day by its fourth step" → NOT IN THE PAPER as stated. The nearest result is 74–77% of early swaps diverging at action 0. T49's own figure (152 of 156) is ours, not theirs.
- *Promising* label → fair. It is a workshop pilot.

**For us.** This confirms forks plus a control fork. It adds three things.
- The control floor depends on the serving stack, so measure it on our own Qwen3.8-27B and quantization before reading any fork difference. At temperature 0, one setup showed 90–96% divergence in controls.
- Report fork effects as swap minus control, with intervals resampled by day.
- Late forks diverged less than early ones in both directions. For us this suggests a change to the world made late in a day can be compared more cheaply than one made at dawn. That is a judgment, since their "late" is 70% of a coding run.
- Check that the saved morning replays exactly, as they did (99.99% of return codes matched). For us that is the engine's state.

**How far it carries.** Their setting is SWE-bench coding agents with a model swap, 30 instances, two small quantized models. Ours is one persona living through simulated days with a change to the world. The logic of a control fork carries. The numbers do not. Promising.

### Replay Fidelity in LLM Agent Evaluation (AppWorld) · Liu and Lu, 7–8 Nov 2026 · [arXiv 2611.11216](https://arxiv.org/abs/2611.11216)

**Read in full:** v3 ("Preprint preparation"), lines 1–733 of 733, 11 pages. Reference list (lines 679–728) skimmed. No appendices exist beyond the "Artifact availability" note.

**What they did.** They re-execute archived code from 71 failed AppWorld runs (32 task families) from a fixed historical corpus of 147 ReAct runs made by GPT-4o-2024-05-13. No model is called: "zero new model API calls" (§2.3). Each failure is replayed in a fresh AppWorld 0.1.0 world under two policies. N uses the declared seed (123) and a 60 s timeout. C also calls random.seed(123) before every recorded interaction. Each case runs in two fresh processes, giving 284 attempts. They compare printed output (O), 12 archived database delta files (D_pre) and the native verdict plus test counts (V). Follow-ups: 25 early stops, 16 materialized-row attempts, a 12-attempt credential program, a 24-attempt export fix, and a 12-case BFCL pilot (Qwen3-8B outputs, 24 attempts). Two independent researchers; no pre-registration; no human raters.

**What they found.**
- N admits 42 of 71 cases and C admits 68 (§3.1, Table 2). The 26-case gap shrinks to 4 when only database and verdict are checked, and to 0 on verdict alone.
- Four cases (from two task families) match on output and verdict but differ in materialized phone-table rows (§4, Table 3).
- For one API call with identical arguments (case e85d92a_2), responses match but rows differ. Aligning the future Python RNG removes the difference in 2 of 2 repetitions (§5).
- A credential-equality program changes an authentication/write result: shared read/write returns 200 under N and 401 under C (§6, Table 4).
- Ten post-oracle export mismatches are corrected by retaining output trackers (§7).
- The BFCL pilot found no discrepancy in 12 cases (§8).

**What the abstract leaves out.**
- It replays fixed recorded code. It never resamples an agent, so it says nothing about a live agent reacting to a changed observation (§3.2: "masking text is not a demonstrated solution for live agents").
- The headline gap is mostly a text-rendering effect. It shrinks from 26 to 4 at the database level, and the authors warn that calling every text stop a failure "would overstate" the gap.
- The four state discrepancies are two task families, "not four independent environments" (§4.2).
- C is "a controlled execution-policy change, not identification of the historical controller's RNG lifecycle" (§2.1).
- Eight of 66 closeout attempts were censored or unknown (§8.3, Table 5); one endpoint stays unknown.
- Different reset codes "can both be valid" (§5.3). Matching the state is not the same as the outcome mattering.
- The paper estimates no debugger accuracy, repair gain or ranking distortion.

**Our claims, checked.**
- Digest, "a replayed agent run matches the original only where randomness and hidden state are rebuilt and controlled" → OVERSTATED. N, which declared the seed but did not reseed, still matched in 42 of 71 cases. Better: "admission rose from 42 to 68 of 71 when the RNG was reset before each step."
- Digest, "four replays agreed in output and verdict and still differed in the state they left behind" → CONFIRMED, with caveats (§4.2, Table 3): four cases from two families, N against the archive. In the paper's words: "All four pairs differ in actual phone table-row fingerprints under N versus C".
- Digest, "supports what T49 found (152 of 156 cases had different prompts across seeds): compare forks from one saved morning, with the state checked" → NOT IN THE PAPER as stated. The paper concerns replaying recorded code, not forking and resampling a model. It supports "check the state, not only the text". It does not speak to forks.
- Digest label *Promising*, "one benchmark" → CONFIRMED. It is one old AppWorld version, with BFCL as a boundary check only.

**For us.** The fork design gains one concrete requirement: the saved morning must hold the random-number state and the engine's hidden state. Then a no-change control fork should come out identical, not merely similar. Compare engine state (purse, orders, promises) between forks, as well as the printed day. A matching text can sit on different rows. Also keep the three-valued record: match, differ, unknown. Do not count a missing fork as a pass. The paper does not show how much hidden state matters for outcomes, so it does not give a size for our noise band.

**How far it carries.** Their setting is deterministic replay of a past GPT-4o coding agent's code in a tool-API sandbox, scored on database rows. Ours is a live local Qwen forked from saved morning state. The state-checking lesson carries. The numbers do not. Promising.

### Auditing the Synthetic Memoir · Renze, 22–23 Aug 2026 · [arXiv 2608.23640](https://arxiv.org/abs/2608.23640)

**Read in full:** v1, lines 1–962 of 962, 20 pages including Appendices A–C. Reference list (lines 848–912) skimmed. Nothing else skipped.

**What they did.** A single-subject case study. The author is also the subject. The audited object is a 366-day "page-a-day" book of first-person entries (about 543 words each) drafted in 2025 with ChatGPT models. The generator received only a template, two exemplar days and the day's quote, not her corpus (§3). The audit labelled each day's one central anecdote scene against an independent corpus of her memoirs, an anecdote ledger, 353k words of her writing and talks, and web checks (§3). The generator's own outputs were excluded as non-independent. Verdicts used a four-level rubric, quoted verbatim in §4.1: verified, weak ("real setting/person, invented specific scene"), unverified ("no anchor"), contradicted. The rubric was fixed on 13 July 2026, the same date as the audit labels, before the paper's analysis. Every row has a source and evidence note. The author adjudicated four critical items, and her rulings take precedence. The labels were assigned by an LLM auditor (Claude-based agents), not by a human (§4.6, §7.1). Two re-raters from another model family re-rated random 60-day samples (seed 20260821). Replication: GPT-5.4 and Claude Sonnet 5 regenerated the same 60 days, with and without corpus excerpts (3 arms, 240 entries, 2 blind raters).

**What they found.**
- Verified 12, weak 227, unverified 108, contradicted 19 (Table 1, §5.1). Failed verification means "not verified": 354 of 366, 96.7% (Wilson 94.4–98.1%).
- Binary agreement with the original: 95.0% (rater B) and 98.3% (rater C) (§5.6). No binary kappa was quoted, because it is degenerate at this base rate.
- Four-way agreement: 63.3%, kappa 0.387 (B); 81.7%, kappa 0.573 (C). Of B's 22 disagreements, 21 involve WEAK.
- WEAK's share of days was 43%, 63% and 82% across raters (§6).
- Replication (Table 5): ungrounded 2026 models fail on 100% of 60 days. Grounding in corpus excerpts cuts this to 83.3%; verified scenes rise from 0 to 10.

**What the abstract leaves out.**
- The labels are an LLM's. The authors say the study "measures LLM confabulation using LLM-produced labels" (§4.6). No human rated the days. A human-adjudicated sample is listed as future work.
- 96.7% is a "verification failure" rate, not a fabrication rate. Only 19 days (5.2%) are positively contradicted. Unverified may be real but unrecorded (§4.4, §7).
- The generator never saw the life corpus. This audits ungrounded generation, not a twin.
- The first replication rating pass was non-blind and was discarded (§5.7).
- A tie-break rule for WEAK vs UNVERIFIED was written after seeing the disagreements and applied to nothing (§5.6).
- One subject, one book. Premise counts come from keyword screens and are ceilings. Per-day evidence notes and entries are withheld.

**Our claims, checked.**
- Sources file, "366 generated days checked scene by scene against the documented life" → CONFIRMED (§3, §4.2).
- "rubric fixed beforehand" → CONFIRMED in a narrow sense. §1: "using a rubric fixed on July 13, 2026 — before any analysis in this paper". The rubric and the labels share that date.
- "96.7% unverified" → WRONG as worded. In the paper's rubric "unverified" is 29.5% (108 days). The 96.7% is "failed verification", meaning weak, unverified or contradicted together. Correct to: "96.7% of days did not verify".
- "the rubric's middle categories were unreliable between raters" → CONFIRMED. §5.6: WEAK/UNVERIFIED "is the least reliable distinction". Binary agreement is high; four-way kappa is 0.387–0.573.
- "A case study" → CONFIRMED (§7: "one life, one corpus, one generator deployment").
- "the nearest design to the Paris backtest" → Judgment. It compares generated scenes with a documented record, which is close in spirit. But it checks invention against a record, not whether a simulated man acts like the real one. Its auditor is an LLM, its subject is also the author, and it has no persona comparison.
- "Freeze the codebook and code a sample twice, as stage 1 did" → PARTLY. They re-rated 60-day samples with two different raters, not the same rater twice.

**For us.** Borrow these: (1) a four-verdict rubric with quoted wording, dated before any scoring; (2) one verdict per scene with source and evidence note; (3) exclude from the reference anything the generator could have seen, as they excluded the generator's own outputs; (4) a fixed seed for the re-rate sample; (5) report binary agreement and the four-way kappa, and keep the middle categories out of headline claims. Define "setting" in the rubric before coding. Their ambiguity came from leaving it open. Add a blind human re-rate. They did not, and for us the human rater is Welt.

**How far it carries.** Their setting is one author's life, a ChatGPT-written year-book, LLM-assigned labels. Ours is a simulated man against letters from 1827. The audit design carries. The percentages do not. Promising.

### Digital Twins are Funhouse Mirrors: Five Systematic Distortions · Peng et al., first posted 23 Sep 2025 (v5, 19 Apr 2026) · [arXiv 2509.19088](https://arxiv.org/abs/2509.19088)

**Read in full:** main text, lines 1–899 (ends at the reference list; references at 900–1305 skimmed only, with acknowledgments). Supplement read: contents (1311–1372); Section A table of all pre-registered comparisons (1373–1723); B prompt template (1724–1832); C persona definitions (1833–1902, 1992–2031, 2089–2128, 2238–2252); D (2253–2281, figures only); E meta-analysis labels (2282–2391); G alternative models and temperature (2403–2495); H Centaur (2496–2562); I expert survey (2563–2629); J opening (2630–2666). Skipped: persona example text (1903–1991, 2032–2088, 2129–2237); F figure (2392–2402); and J sub-study detail, lines 2667–7004 (substudies J.1–J.19).

**What they did.** 19 pre-registered sub-studies, 164 outcomes. 1,784 unique Prolific participants from the Twin-2K-500 panel, 13,506 participant-responses in all. Each person's "twin" is GPT-4.1 (temperature 0.7) prompted with that person's answers to over 500 earlier survey questions (about 128K characters, about 30K tokens). Twins and humans answered the same new questions. Baselines: empty persona (same prompt for all), demographics-only persona (14 variables), random answers. Metrics: individual accuracy (1 − MAD/range) and correlation across participants for each outcome. Only the basic performance evaluation was pre-registered; the five distortions are exploratory. No pre-registered hypotheses on performance.

**What they found.**
- Accuracy: full 0.748, empty 0.734, demographics 0.746 (p = 0.37 vs full), random 0.629 (§Performance comparisons).
- Correlation: full 0.197, demographics 0.145, empty 0.080, random 0.001.
- Best of all settings: GPT-4.1 at temperature 0, correlation 0.232, accuracy 0.752. No other base model beat GPT-4.1 (SI G.2).
- Twin SD below human SD in 154 of 164 outcomes (140 significant). Full twins sit closer to empty twins (MAD 0.175) than to humans (0.252).
- Full-persona twins are closer to demographics-only twins (0.132) than to humans.
- Twins match XGBoost trained on about 180 people on correlation, about 75 on accuracy.
- Hyper-rationality appears in several sub-studies, with a leakage caveat for classic paradigms.

**What the abstract leaves out.** The correlation of 0.197 is more than double the empty persona's 0.080, and the authors say full personas "significantly improve" it. The "only a little better" result is the accuracy result. The empty persona's correlation is not zero because question versions vary across respondents (footnote 9). The twin reproduced survey answers, not behaviour over time. The prompt told the model to account for "human cognitive limitations". Experts predicted twin results worse than human results (SI I).

**Our claims, checked.**
- Plan, "a twin built from a person's own answers has matched that person only a little better than a model with no persona at all" → OVERSTATED. True for accuracy (0.748 against 0.734). On correlation, the measure of telling people apart, it is 0.197 against 0.080. Correct: "barely more accurate, and about twice as well correlated."
- Sources, "19 pre-registered studies" → CONFIRMED for the performance evaluation. The distortions are exploratory.
- "r = 0.20 with the person's own answers" → CONFIRMED (0.197, mean over 164 outcomes, Fisher z; across participants).
- "hyper-rational and under-individuated" → CONFIRMED (§Five Key Distortions 1 and 5).
- "qualifies the 85% of Park et al." → PLAUSIBLE. The paper says that figure uses a different correlation, across questions within a participant.
- Plan's two nulls (plain Qwen, generic professor of the 1820s) → NOT IN THE PAPER. Their nulls are an empty persona and a demographics-only persona. The professor is our analogue of the second.

**For us.** Keep both nulls, and add a third that shares the real man's data (his demographics, the year, his trade) but not the letters. Report separately the measure that tells days apart and the measure of closeness. Use temperature 0 or a fixed seed where you can. Expect the sim to be too rational and too even.

**How far it carries.** Their setting is GPT-4.1 predicting US adults' survey answers from questionnaires. Ours is a local 27B model, one 1827 man, open-ended days. The warning about nulls carries; the numbers do not. Established for their setting; Judgment for ours.

## Chapter 5 · Tuning: search and gates

### GEPA and SkillOpt on locally served reasoning models · Giummarra et al., 19 Oct 2026 · [arXiv 2610.26020](https://arxiv.org/abs/2610.26020)

**Read in full:** v1, lines 1–1965 of 1965 of the extracted text, 36 pages including Appendices A–C. Reference list (lines 1299–1396) skimmed only; nothing else skipped.

**What they did.** Two prompt/skill optimisers (GEPA, SkillOpt) on two local reasoning models (DeepSeek V4 Flash and Qwen3.8-27B), on HotpotQA (test n=500) and MATH-500 (test n=250). Four conditions: minimal one-line baseline, GEPA prompt, SkillOpt skill, hand-written prompt. Splits 150 train / 100 validation (SkillOpt gate: 100 and 50). One optimiser run per cell, seed 42, so no run-to-run variance. Paired sign-permutation tests, bootstrap CIs, Holm correction. Reflection model: Claude Opus 4.8. Scoring is deterministic (no judge).

**Serving of Qwen3.8-27B (§5.2, §6.11, App. B/C).** 8-bit MLX build (29.5 GB), not Q4. LM Studio 0.4.14+4 on an Apple M3 Max, 128 GB. Loaded context 32,768, parallelism 1. Reasoning left at the server default (on); reasoning-effort and thinking-preservation controls were not sent. Temperature 0, max_tokens 512 (HotpotQA) / 4096 (MATH), timeouts 180 s / 480 s, one retry, no provider seed. Mean MATH latency about 116 s per call. Qwen optimisation took 13 to 40 hours per cell. Sensitivity: v1 and v2 reran the whole pipeline. Three of four optimised artifacts differed. v2 MATH baseline .804 → .828; v1 had 40 errors on baseline MATH, v2 had 1. SkillOpt HotpotQA .8184 → .7893. Conditions ran in sequence, and 12 MATH timeouts fell 1/1/9/1 (A/B/C/D).

**What they found.**
- Qwen HotpotQA: GEPA picked the seed, all 500 answers identical (Table 1, §6.4). SkillOpt selection F1 .620 → .776, held-out F1 .8215 → .7893 (−3.22, p=.0004).
- Qwen MATH: GEPA .828 → .904 (+7.6, Holm p=.0014). SkillOpt +3.6 (raw p=.046, not after Holm).
- DeepSeek audit (Table 7): of 18 GEPA gains, 12 were baseline answers cut off at the 4,096-token limit, 6 were format mismatches. No case of better reasoning.
- Selection noise (§4.5): a gain of about 8 points at n=50 to 100 is unremarkable after 20 gate evaluations.

**What the abstract leaves out.** GEPA's MATH gains did transfer on both models. The authors say the v2 held-out items were already seen in v1, so v2 is "not a fresh study-level holdout" (§8). Primary v2 designation is post hoc. Cross-model contrasts mix model and serving stack. Qwen intervals do not cover correlated server failures.

**Our claims, checked.**
- Plan: "On his own model, a gain on a small case set reversed on held-out cases." → OVERSTATED. Same model family, but 8-bit MLX on a Mac, not Q4 on a 3090. One cell (SkillOpt on HotpotQA), selection set n=100, held-out n=500. Quote: "its validation score rises from 0.620 to 0.776, but held-out F1 falls." Say: "a skill-file optimiser's gain on 100 selection cases reversed on 500 held-out cases, on a Qwen3.8-27B served in 8-bit."
- Plan: "Hence … confirmation cases used once." → CONFIRMED as advice. §7: "requires evaluation data untouched by optimization." The paper's own v2 test items were reused.
- Sources: "one optimiser only reproduced the baseline on one task" → CONFIRMED (GEPA, HotpotQA, identical hash).
- Sources: "the other's validation gain reversed on held-out cases" → CONFIRMED for HotpotQA only. Omits that GEPA gained significantly on MATH on Qwen.
- Sources: "a search over text can lose on cases it has not seen" → CONFIRMED, one run each.

**For us.** Supports a confirmation set used once and distrust of small gate gains. Our gate is soft and judged blind; theirs is exact-match. At 8 wordings, expected best-of-8 noise needs a margin; their Eq. 3 gives the scale. Run the same arm twice for a noise band. Their MATH gain was mostly format and completion, so check what our gain consists of. Randomise or interleave arms in time.

**How far it carries.** Their budgets are 400 to 1,220 metric calls and 100-case gates, scored by exact match, on a different quantisation and host; ours is a few hundred calls with soft blind judging. Label: Promising (one run per cell).

### Compile as Hypothesis · Yang and Li, 31 Oct 2026 · [arXiv 2611.01135](https://arxiv.org/abs/2611.01135)

**Read in full:** v1, lines 1–606 of 606 of the extracted text (two-column layout, garbled order but complete), main text, Appendix A and B. Reference list skipped. The PDF has no further appendix.

**What they did.** A prompt "compiler" that builds a prompt from fixed parts. It runs two arms at equal budget, one with profile rules and one from the plain base prompt, and deploys the winner. Compared with official GEPA and ESPO. Models: qwen3.8-flash (via DashScope and a gateway alias) and "gpt-6"; size of qwen3.8-flash not stated. Tasks: a simulator (4 tasks), three enterprise tasks, five external benchmarks (GSM8K, MATH L5, AIME 2024+25 with 60 problems, GPQA-Diamond with 190, HLE subset of 90). Default protocol is tiny: 5 development, 8 validation, 20 holdout examples, search budget 8, seed 42, temperature 0 (§4). Same-day noise band ±.007, cross-day drift .028. Judge: hardened exact-match scorer with fixed rubric dimensions, no LLM judge.

**What they found.**
- Four optimiser families give gains "statistically indistinguishable from zero" on the strong reasoners (§5.4). GEPA on qwen financial: +.0024.
- On GPQA-Diamond and HLE all six arms tie (§5.5). AIME is at ceiling (60/60).
- Unconstrained profile-rule search collapsed to the judge floor in 3 of 5 financial seeds (§5.2). That is their own rule root, not GEPA.
- GEPA on gpt-6 financial: +.14 over the same-day zero-shot score .7039 (§6.1). Stripping the evolved prompt's style-rules block cost −.0349 (.8441 → .8092); the rest, about +.105, is called instruction refinement (§6.1, App. B).
- A gateway silently served another model during outages (§6.3). Same-text GPQA score fell from .8729 to .6501 in 48 hours.

**What the abstract leaves out.** The ablation is one run, one task, a 20-example holdout, against a drift of .028. "Quarter" is .035 of .14, and "judge" means a fixed rubric of scoring dimensions, not a blind judge. §6.1 gives gpt-6 holdout .8914 against .7039 (a gap of .19), while the appendix uses .8441; the paper does not reconcile these. The null is partly a ceiling effect and a small-holdout effect. The scope limit (§8) says open-ended subjective generation "may exhibit distinct optimization dynamics". Greedy argmax on validation beat their structured gate, 47/77 to 37/77, when judges were stable.

**Our claims, checked.**
- Digest: "Prompt optimisers gave no significant gain on strong reasoning models across eight tasks" → OVERSTATED. Real: GEPA gained +.14 on gpt-6 financial. Paper's own words: "structured search yields no statistically significant accuracy gains." Say: "structured search gave none; free-text GEPA gave +.14 on one model and none on qwen."
- Digest: "eight tasks" → NOT FULLY IN THE PAPER. The abstract says eight; the body lists 4 simulated, 3 enterprise, 5 external. Eight fits only the real ones.
- Digest: "where one did gain 0.14, about a quarter of it was the judge's rubric rebuilt inside the prompt" → CONFIRMED in size. Quote: "this judge-gaming accounts for ∼.035 of the score, while ∼.105 represents genuine task-instruction refinement." Add: single ablation, rubric is deterministic.
- Digest: "a tuning loop's confirmation cases are used once, and their judge's rubric never enters the loop" → NOT IN THE PAPER as advice. It follows from the finding; the paper's own remedy is a paired same-day comparison with the uncompiled base.

**For us.** Keep the blind judge's rubric out of anything the search sees, including failure notes. Run the base wording as a standing arm and adopt only if it beats it beyond a measured same-arm band. Log the serving model on every call, because backends can drift. Expect that a search over our wordings can find gains, but check what they consist of.

**How far it carries.** Exact-match tasks on strong reasoners, with holdouts of 20 to 190, versus our soft blind judging on a few hundred calls; the null is weak evidence at n=20. Label: Promising.

### Lineage Is Memory · Yang and Shi, 30 Oct 2026 · [arXiv 2610.41157](https://arxiv.org/abs/2610.41157)

**Read in full:** v1, lines 1–1210 of 1210 of the extracted text, 20 pages including Appendices A and B (hypothesis table, leave-one-task-out table, verbatim prompts). Reference list skimmed only.

**What they did.** A loop where a proposer model rewrites a prompt or a small Python function after seeing failures. Two factors: lineage (each rewrite edits the surviving best parent, or restarts from the seed every round) and feedback disclosure (none, first 4 failures, 4 diverse failures, random mixed minibatch, LLM-clustered summary of all failures). 1,750 pre-registered runs, 10 seeds per cell, 25 registered tests. Task model gpt-4.1-mini, replicated on claude-haiku-5-5, and a stronger proposer gpt-4.1. Nine tasks: five built by withholding rules from the seed, one rubric-judged support-reply task (gpt-4.1-mini PASS/FAIL judge), ScoNe, a 12-intent Banking77 subset, BBH translation errors. Search sets of 16 to 36 examples. Budget: 8 full evaluations for prompt tasks (the seed plus 7 proposals, at most 128 to 288 task calls), 12 for code (§3.1, Table 1). Compared with GEPA 0.0.7 at the same call cap.

**What they found.**
- Parent over seed: +0.238 held-out accuracy across 7 tasks on gpt-4.1-mini, and +0.332 on the 5 tasks with headroom (Table 2A). Haiku: +0.222 (Table 3).
- A stronger proposer gave no gain (∆ from −0.069 to +0.002, Table 3B).
- Clustering helps in rounds 1 to 2 and is level with raw failures by round 4 (Table 5C).
- GEPA tokens: reflection 2–15%, validation and minibatch checks 85–98% (Table 6).
- Banking77: parent-first scored 0.372, GEPA 0.664. One added sentence ("copy every task-specific fact") raised parent-first to 0.856, but cut BBH accuracy by 0.061.

**What the abstract leaves out.** The comparison is parent versus seed-reset, not parent versus GEPA. Public tasks show a small lineage effect: +0.088 pooled, BBH +0.017, ScoNe and dates about zero. Five tasks are built so rules must accumulate (§6). Four of the five public-benchmark tests were inconclusive (Table 7). Budgets were only 8 to 12 rounds; the paper never varies budget, and says wider disclosure "may retain an advantage" on larger tasks (§6).

**Our claims, checked.**
- Sources: "At short budgets, editing the surviving parent gives most of the gain" → OVERSTATED. Quote: "greedy parent inheritance drives the vast majority of optimization progress." True against seed-reset resampling, on tasks built to reward accumulation. Say: "against restarting from the seed each round, editing the best parent added about a quarter of accuracy on rule-discovery tasks, little on public ones."
- Sources: "validation takes nearly all the cost" → CONFIRMED for GEPA (85–98% of tokens, Table 6). Not shown for other loops.
- Plan: search of 8 wordings raced to 2, about 340 calls, "leans on it" → NOT IN THE PAPER. The paper tests an LLM proposer editing a parent from failure feedback. Our racing of fixed candidates has no proposer and no parent. It supports a sequential, edit-the-winner design only if we add one.
- Budgets at which shown: 8 rounds (12 for code), 16–36 examples per evaluation, one model family each. Nothing at 340 calls on soft judged output.

**For us.** If we keep 8 wordings in a race, this paper neither supports nor opposes it. A second stage that rewrites the 2 survivors from their own failures would be the lineage move. Its risk is the same as Giummarra's: gains at selection that do not hold on unseen cases. The carry-facts finding warns that instructions to copy facts into text help only when the facts are missing from the seed.

**How far it carries.** Binary exact scoring, 8 to 12 rounds, small cloud models, built tasks; ours is soft blind judging on a local model. Label: Promising.

### Masked Erosion · So et al., 28 Oct 2026 · [arXiv 2610.38392](https://arxiv.org/abs/2610.38392)

**Read in full:** v1, lines 1–1674 of 1674 of the extracted text, 25 pages including Appendices A–K. Reference list skimmed only.

**What they did.** An agent's "harness" (prompt text) holds four written safety rules (safeguards). A gate decides whether to keep an edit. They measured harm for every subset of the four rules in two simulated environments (AppWorld credential misuse, OpsSim destructive clean-up). They ran 411 loops under ten gate rules: 393 "stress loops" that plant one deletion per generation, 18 natural loops where a model rewrites text freely, plus 3 GEPA runs. Batch n=40 with 10% harm tasks; 6 loops per arm, 8 generations. Agent DeepSeek-V4.1-Flash; Qwen3-30B-A3B and Qwen3-8B served locally; API models as extras. Deterministic audits, no judge. Predictions were registered and hashed.

**What they found.**
- A deletion behind another working rule adds almost no harm: 0.016 into protected states, 0.422 into unprotected (§4.2).
- A success-only gate accepts masked deletions at 0.625, no-op edits at 0.358. A paired exact test accepts 0.048 (Table 7).
- When a rule costs task success, significance does not protect. Paired loops lost protection in 0, 0, 1, 6, 4 of 6 as cost rose to 0.32 (Table 20).
- Batch size: at cost 0.15, 20-task batches kept all six loops protected and 40-task lost all six (p=.001) (§4.4).
- Harm audits stop exposure but not lost depth. Finals kept margin 1, and 0.30 of runs misused credentials under Qwen3-30B (§4.5).
- Remedies: freeze safety text; margin-aware gate (every one-layer ablation of the child must stay safe, 30 tasks each). The second cost 0.35 clean success in three-step OpsSim (§4.7, App. F).
- GEPA: validation gains up to +0.22 did not transfer (finals 0.35–0.45 against 0.40 for the start).

**What the abstract leaves out.** Two environments, four rules each, mostly planted deletions. Of 177 registered predictions, 113 held, 49 failed. The 120-task batches resample a 60-task pool (about 50 distinct), so they "confirm the direction rather than the exact break" (App. B). Strong models already avoided the harms elsewhere (App. A). The harm detector for a single ablation is weak: a 30-run check passes true harm 0.10 with probability 0.18.

**Our claims, checked.**
- Plan: "An acceptance gate can delete a rule whose work another rule was covering." → CONFIRMED, for safety rules in agent prompts under success-only gates.
- Plan/digest: "After a bundle is adopted, each older rule is switched off once, alone, to see what it was holding." → OVERSTATED as a cure. Alone-switch-off of a redundant rule shows no loss, which is the definition of masking. Their working remedies are a read-only freeze and ablation checks against declared harm tests. Declared probes for each rule are needed.
- Digest: "larger batches made it worse (20-task kept every harness protected, 40-task lost all six)" → OVERSTATED. Numbers are right but only for the paired significance gate, one cost (0.15), OpsSim, six loops per arm. Quote: "A larger batch, usually the safer choice, admits cheaper deletions." The cause is a real gain on a costly rule, not size as such.
- Digest: "an acceptance gate sees only what a rule does while the others work" → CONFIRMED (abstract).

**For us.** Keep the ratchet's gate from deciding on score alone for rules that guard a stated behaviour: freeze those rules, or hold a small probe set per rule. A switch-off test needs a stated outcome it should hold and enough runs; the paper puts about 200 pairs to see a 0.008 effect. Test at least once on a different serving of the model, since lost depth shows only on a change.

**How far it carries.** Binary safety harms, planted deletions, n=40; ours are soft wording choices judged blind. The mechanism carries; the numbers do not. Label: Promising.

### Evidence-Governed Adoption of Self-Generated Updates · Lonkar, 12 Nov 2026 · [arXiv 2611.16378](https://arxiv.org/abs/2611.16378)

**Read in full:** v1, lines 1–1235 of 1235 of the extracted text, 21 pages including Appendices A–E. Reference list skimmed only. Single author, independent researcher; discloses ChatGPT assistance.

**What they did.** A theory paper. It proposes "Evidence-Governed Evolution" (EGE) for deciding whether a self-generated change to an agent becomes permanent. The change is frozen, then audited on fresh paired samples. A primary objective must improve by a stated margin (δ). Each declared protected capability must not fall by more than a stated margin (ε), measured against a fixed versioned reference. Governance checks must pass. Then a bounded canary runs before commit. Statistics: Hoeffding bounds, a union bound over candidates (error 3α/π²j²R each), and a separate calibration sample per candidate to measure how optimistic the operational evaluator is against a reference procedure. Theorem 1 gives simultaneous coverage; Theorem 2 bounds cumulative drift across reference changes. The only experiment is a synthetic Monte Carlo (3,000 campaigns, 10 candidates, α=0.05, δ=0.05, ε=0.20).

**What they found.**
- Naive acceptance (no calibration) accepted a harmful candidate in 2,997 of 3,000 campaigns when evaluator optimism was 0.25; calibrated EGE accepted none (Table 2).
- Calibrated power was 52.6–76.2% at 5,000 observations per sample, 100% at 20,000 (§8.1).
- If calibration optimism differs from audit optimism, calibrated EGE accepted harm in 3,000 of 3,000 campaigns (Table 3).
- Sample sizes (Table 4; α=0.05, R=3, gap g=0.10, λ=0.5): candidate 1 needs n ≥ 16,913 audit and m ≥ 67,651 calibration observations (84,564 total). Candidate 10 needs 158,247; candidate 100 needs 231,929.

**What the abstract leaves out.** The abstract does say there is no real-agent validation, and the paper is candid about it. The cost is the point: the bounds need tens of thousands of fresh independent observations per candidate, and the budget shrinks with every later candidate. Scores must be bounded and independent; clustered tasks need a different bound (§4.2, §8.3). Rare severe events are not captured by an average (§10).

**Our claims, checked.**
- Digest: "fresh paired audits" → CONFIRMED. Quote: "evaluates frozen candidates on fresh paired audit samples."
- Digest: "a declared list of protected abilities tested for no loss" → CONFIRMED, as non-inferiority tests against a fixed reference with margin ε, declared before the audit.
- Digest: "a small first deployment" → CONFIRMED (bounded canary, §7.1).
- Digest: "no experiment on a real agent" → CONFIRMED. Quote: "The paper does not claim empirical validation on a real autonomous-agent system."
- Digest: "Answers Masked Erosion" → NOT IN THE PAPER. It never mentions masking or redundant rules. Protected-capability tests catch loss of a declared ability against a fixed reference, which is related, but it is our reading.

**Could our ratchet meet it?** Not at its guarantee. Confirmation on 24 cases gives a Hoeffding radius near 0.66 on a paired difference at candidate 1's error level (my arithmetic from their formula 14), so almost nothing could pass. Our blind judge would be the "operational evaluator", and a calibration set against a reference judge is a second sample. We can borrow the design, not the guarantee: freeze before audit, use fresh cases once, declare protected behaviours and margins first, keep a log, start small. Judgment.

**How far it carries.** A formal protocol and one stylised simulation with thousands of observations per test, against our dozens. Label: Judgment (design principles only; no empirical support).

### TextReg: regularised text-space prompt optimisation · Fu et al., 20 May 2026 (v2, 5 Oct 2026) · [arXiv 2605.21318](https://arxiv.org/abs/2605.21318)

**Read in full:** v2, lines 1–1218 of 1218 of the extracted text, 23 pages. Skipped only the reference list (lines 492–about 725).

**What they did.** They study "prompt distributional overfitting": prompt optimisers that rewrite a prompt from LLM feedback make it longer and fill it with narrow rules. TextReg adds three LLM-run steps: filter feedback into general rule, case patch or style (RuleBank of recurring rules); flag a rewrite that grows length over 20% or narrows scope; rewrite under that guidance. Prompts are optimised on 3-object Big-Bench Hard tasks and GSM8K, with 12 steps, batch 3 (36 training samples). They are tested on harder variants, SVAMP and MultiArith, on four 7–8B engines. GPT-4o is the rewriter. Baselines: CoT, TextGrad, REVOLVE. Four seeds (Sec. 5.1, App. A.3).

**What they found.** Table 1: TextReg best or second best in most cells. Abstract gains of +11.8 over TextGrad and +16.5 over REVOLVE are single cells on Phi-3.5. Table 3: TextGrad's prompt grows 41 to 351 tokens while its out-of-distribution accuracy ends at 39.8, below the 42.0 start. TextReg stays at 135–160 tokens and holds 47.0 at step 12. App. B: gains survive matched compute and a CAPO-style length penalty (Table 2). App. E.2: with richer seed prompts TextGrad still grows (to 144 and 314 words).

**What the abstract leaves out.** (1) The cure is not a length cap. Length control alone was tested as a baseline and lost to TextReg (Table 2, App. B). REVOLVE is also compact but weaker, "showing that prompt length alone does not explain the improvement" (App. C). (2) The authors say a longer prompt can be right: "A task-relevant instruction may legitimately increase prompt length" (Sec. 4.4). (3) Setting: short seed prompts (41 tokens), 36 training samples, exact-match reasoning tasks, 7–8B test models. The paper says it studies "single-turn reasoning with well-defined behavioral rules" and leaves multi-turn prompts and agents to future work (Sec. 6). (4) In-distribution accuracy dropped about 2 points on the BBH source tasks (App. D). (5) Mixed cells: Table 5 Qwen2 Tracking 5obj, TextReg 45.8 against TextGrad 46.6; Table 1 Phi-3.5 Tracking 7obj, 92.2 against 92.8. (6) The scope judge is an LLM and a direction only. Open-ended generation is "preliminary" (App. F).

**Our claims, checked.**
- "Optimised prompts get longer and gather rules for single cases" → CONFIRMED for TextGrad-style optimisers on reasoning prompts. Quote (abstract): "prompts often become longer, accumulate narrow sample-specific rules, and generalize poorly". REVOLVE grows less (131 tokens at step 12, Table 3).
- "Hence the cap" → OVERSTATED as a citation. The paper shows growth and narrow rules go together, but it does not test a hard cap and its length-penalty control did worse. Wording: "Search that rewrites text tends to grow it and add case rules (TextReg). A cap is our own guard; that paper's fix filters case rules and checks each edit, which a cap does not do."
- Source line "Optimised prompts grow longer and gather rules for single cases" → CONFIRMED, but it should say text-gradient optimisers.

**For us.** Keep the cap, but call it our guard. Add two checks the paper supports: reject a candidate edit that adds a rule keyed to one case, and require a rule to recur across several confirmation cases before it enters world text. Do not claim the paper shows a cap prevents overfitting.

**How far it carries.** Their setting: short task prompts, reasoning accuracy, 36 samples. Ours: long world text, judged by an engine and a persona. Label: Promising.

### Randomization Tests in Switchback Experiments · Liu and Zhong, 26 Feb 2026 (v2, 29 Sep 2026) · [arXiv 2602.23257](https://arxiv.org/abs/2602.23257)

**Read in full:** v2, main text lines 1–1536 and appendix lines 1537–1599, 2900–3040, 3318–3757 of 3757, 70 pages. Skipped (proofs): lines 1600–2899 and 3041–3317. I read the statements of all lemmas and theorems.

**What they did.** One system flips between treatment and control over blocks of time, chosen at random. They give a conditional randomisation test of "no total effect", a carryover test, a non-anticipation test, and power formulas. Tested on a toy model (T/2 = 30 to 150 design units; 28 to 148 blocks; 1,000 runs per cell) and a ride-share simulator (300,000 requests, 30 to 300 blocks, 50 runs per cell).

**What they found.** Theorem 3.1: the test is valid at any number of blocks, given no anticipation and carryover of at most m periods, with m fixed before the data. Eq. 34: at 5% you need at least five retained sections, "ties and two-sided statistics can require more". Simulator power (App. Table 3, horizon chosen from data): effect 0.005 gives 0.72, 0.54, 0.30, 0.18 at 300, 120, 60, 30 blocks. Effect 0.010 gives 0.98, 0.84, 0.72, 0.48.

**What the abstract leaves out.**
- The smallest number of blocks they ever run is 28 (toy) and 30 (simulator). There is no power result below that. At 30 blocks power is 0.18 for the smaller effect and 0.48 for the larger.
- Carryover is a hard cutoff: nothing after m periods. m is prespecified. Using the same data to pick m and then test is outside the theorems (Sec. 4.1).
- The carryover test pairs odd and even sections and redraws one block per pair. With few blocks it has too few pairs to reject. From Eq. 34 and the pairing, 7 blocks give 3 pairs, so p cannot go below 0.125. This is my inference, not a stated result. It may miss carryover at distant lags (Fig. 3 text).
- Sections that mix treatment and control are dropped. At 300 blocks of 1,000 and m = 5,000, 227 of 1,000 runs had no usable test (App. 8.3).
- Averages (not "zero effect in every period") need many blocks: Theorem 5.1 is asymptotic.

**Our claims, checked.**
- "A randomisation test that stays valid with few blocks" → CONFIRMED for size; it says nothing on power. Quote (Sec. 1): "finite-sample size control". Wording: "valid at any block count, powerful only with dozens."
- "and tests for carry-over" → CONFIRMED, with limits: needs prespecified m and non-anticipation, and has low power at few blocks.
- "Established as a design" → OVERSTATED for the new tests. Simulation only, preprint. The design (Bojinov et al.) is published.
- "Blocks of at least four days" → NOT IN THE PAPER. Block length must exceed the carryover horizon m, and the count of blocks matters more.

**For us.** Four-day blocks over 3, 4, 6 weeks give about 5, 7, 10 blocks. Three weeks can only just meet the five-section floor with every block retained and the result extreme. Four weeks reaches p near 0.008 at best, one-sided. None of this is in their simulations. A real conclusion needs about 30 blocks: 120 days at four-day blocks, or shorter blocks if carryover is under a day. Use the stage as a check for big harm. Do not plan it as a test that can clear a small gain. Fix m and the statistic before the run. Report retained sections.

**How far it carries.** Their setting: a market flipping on and off, with power shown from 30 blocks. Ours: a persona with memory, which may not forget at any fixed m. Label: Promising for size, Judgment for the four-day plan.

## Chapter 5 · Tuning: calibration and realism

### AutoPersonas, self-locking in persona runs · Li et al. (single author, Mengchen Li, Latrix), v2 dated 1-2 Oct 2026 · [arXiv 2607.08252](https://arxiv.org/abs/2607.08252)

**Read in full:** v2 as extracted, lines 1-2118 of 2118, 50 pages. Skipped: nothing but the reference list (lines 2031-2118, glanced at). Figures are images and were not seen. The ancillary data files named in section 12 are not in the text.

**What they did.** One paper, one author, a commercial system (SoulOS). The stress test: one fixed complex persona canon, run as a "direct self-orchestrated loop" with no outside world engine. Eight models (Claude, DeepSeek, Doubao, Gemini, GLM, GPT, Kimi K2.6, Qwen; sizes not given), 40 days each, five model-generated events per day, 200 events per model, temperature 0.75 (Kimi 1.0). The metric is a rule-based keyword taxonomy over each event's title and action fields. One run per model. Plus a three-year compressed diagnostic run (qualitative), one Doubao temperature rerun, and a withheld "divergence configuration" tested once per condition.

**What they found.** Section 7.1: mean rolling 5-day action-category repetition 96.5%, range 95.2-97.6%. Every model passed 80% by day 9 and 90% by day 11. Only 10-11 action categories were used in 200 events. Macro-theme repeat ratio 79.0-88.0%. Stricter variants: 86.9-93.4% if a category must have appeared twice before (80% by day 12); 80.0-86.6% if three times (80% by day 16, 90% by day 19). Doubao at temperature 1.0 gave 95.9% against 96.0%. Mitigation (section 7.2): macro-theme repeat 61.8% to 39.4% in a full-runtime A/B; 88.0% to 46.5% in an isolated generator.

**What the abstract leaves out.** The metric counts an event as repeated if its category appeared in ANY earlier day (days up to D-5), not "in the last five days". With about 10 coarse categories this is close to automatic after two weeks. The authors admit (limitation 7) that the study "does not separate model-level tendency from canon-specific attractors, prompt design, taxonomy granularity". The mitigation is withheld; it is one persona, one run per condition, no variance. They do not test any world content. The loop has no deterministic world: the model writes its own events.

**Our claims, checked.**
- "Persona runs settle into familiar channels whatever the world holds." → OVERSTATED. The 40-day test had no world at all; the model generated its own life events. The authors' own cure is outside material: "the counter-pressure must come from external information, user interaction, and macro-world changes". Say: "when a model writes its own days, they settle."
- "Share of a day's kinds of action already seen in the last five days was 95-98%" → WRONG as worded. Section 6.1: the 25 events of days D-4..D are compared "with all prior days <=D-5". It is the share of a 5-day window whose category appeared earlier in the whole history. Range 95.2-97.6% (we say 95-98%: fine).
- "Eight models, 40 days, past 90% by day 11" → CONFIRMED (table, section 7.1; latest model Doubao, day 11).
- Causes of locking, asked of us: model-side convergence "toward high-probability behavioral channels" plus system-side "context gravity" from State, memory, history and environment summaries (abstract, section 10). Self-looping makes summaries into State and State into retrieval. More memory "can make a persona more consistent while also amplifying stale state".
- Mitigations they can describe: separate Observation, State and Occurrence; govern how much each may weigh in a call; keep facts from echoing across modules; require events to reach State; weekly and monthly review; audit for repeated places and relation roles. The main one is withheld ("configuration, and parameters as commercial trade secrets"). Higher temperature did not help.

**For us.** Keep the health row, but define it exactly: share of new moments whose act category was seen in earlier history, with the paper's stricter variants (seen at least twice, at least three times) and the "no Other" check. Our world is the thing that supplies Occurrences, which is what they say is missing in their baseline; so a row showing lock-in under our world would be a real finding, not a replication. Their audit ideas (repeated places, relation roles that never change function, decisions kept pending) suit ten categories plus a places/people row. Do not cite them for the claim that a world cannot unlock a model.

**How far it carries.** Their setting: one persona canon, eight frontier APIs, 40 days, self-generated events, one run each, keyword taxonomy. Ours: one protagonist on a 27B Q4 local model, months, an engine-owned world. The failure mode is Promising as a warning; the 95-98% figure is Judgment as a benchmark for us.

### AI agents running a town's economy (Pokhara) · Regmi et al. (Karela Technologies), 10 Sep 2026 · [arXiv 2609.11108](https://arxiv.org/abs/2609.11108)

**Read in full:** v1, lines 1-619 of 619 of the extracted text, about 9 pages (extended version). Skipped: reference list only (lines 604-619, glanced). Figures are images; I read their axis text and captions only.

**What they did.** 100 LLM agents with memory tools run a closed, money-conserving town on real Pokhara Lakeside geography: 762 businesses, 3,981 menu items, 19 tools. Decision model Qwen3.8-27B-FP8 (self-hosted vLLM, 73 runs); a swap arm used gpt-oss-20b (18 runs). 91 runs kept of 98 (2.44M decisions). Seeds drawn from a pre-registered pool, but the plan was cut: 9 seeds per condition, 336 hourly pulses (2 weeks), not the planned 30 seeds. Arms: tourist-rate sweep (0.5, 2.0, 6.0 per hour), a within-run randomised grant (NPR 5,000 to 20 of 100 agents), layout placebo (6 seeds), memory off (6 seeds), model swap (9 seeds). Long arms: 4 runs at 12 weeks, ONE run at 26 weeks.

**What they found.** Section 6: revenue 4.62x for a 12x tourist rate (1.50x firms trading, 3.07x revenue per firm); wages 1.03x (p = 0.42); 0.27-0.32% of menu items repriced (p = 0.47). Section 7: grant 96.7% still held at pulse 335, MPC 3.3% (wealth) and 4.0% (spending, p = 0.22). Section 8: wealth-rank correlation 0.964 at 2 weeks, 0.832 at 12, 0.752 at 26. Section 9: model swap moves all eight outcomes at p = 0.0039; memory off moves none beyond one tool-failure rate (-2.2%, p = 0.031).

**What the abstract leaves out.** (1) The headline sweep is 2 weeks; the 26-week figure is a single run. (2) "0.3% repriced" is partly built in: set_price is called "~18 times per run out of ~28,000", and "how sticky the initial menu is by construction"; limitation: "we have not separated the two". (3) The authors say the transmission failure "would fall to a prompting change", untested. (4) Memory null rests on 6 seeds: "we detected no effect, not that none exists". (5) The layout "placebo" moved two outcomes too (tool calls +9.0%, economic tool failure -15.5%, both p = 0.031, uncorrected). (6) Model swap changed serving too (token budget, KV-cache setting); only two models. (7) The economy is not frozen at long horizons: it relaxes over about ten weeks. (8) Social tools fail 94-97% through a concurrency cap the authors built.

**Our claims, checked.**
- "Simulated agents hoard" → CONFIRMED for this setup, with a 2-week window. "96.7% of a cash transfer still held" is at pulse 335, 311 pulses (about 13 days) after the grant, not "long after" in months. Quote: "96.7% at pulse 335".
- "Seldom reprice / 0.3% of prices ever changed" → OVERSTATED as behaviour. Menus are sticky by construction and the lever is rarely called; the authors did not separate the two.
- "100 agents, 26 simulated weeks" (sources file) → OVERSTATED. Only one run reached 26 weeks. The transfer and repricing results are from 2-week runs.
- "A fuller purse may change little" → CONFIRMED in this town, over 2 weeks. Not shown for a single protagonist or for months.
- "What is on offer may change more" → NOT IN THE PAPER. They varied tourist demand, never the offers.
- "Changing the model moves every outcome" → CONFIRMED (all eight, p = 0.0039), two models, confounded with serving settings.
- "Deleting memory moves none" → OVERSTATED. Say: "moved no economic outcome detectably, at 6 seeds"; one social-tool outcome did move.

**For us.** Keep the order of play: change what is offered, read uptake. But do not cite this paper as evidence that offers work better than money. Its model is our model family, and its hoarding may be a prompt and tool-design effect. Before relying on "prices alone do not move him", our own rehearsal should test that he reprices or spends when the lever is made salient.

**How far it carries.** Their setting: 100 agents, same model family as ours (Qwen3.8-27B FP8), 2 weeks mostly, one town, aggregate money. Ours: one protagonist, months, offers and schedules. Promising for "a purse changes little"; Judgment for "offers change more".

### Empirical grounding for LLM agents in a heatwave · Xia, Kuang and Hu, 2026 (Penn State / RIT; preprint, 19 Jul 2026 per our file) · [arXiv 2607.17437](https://arxiv.org/abs/2607.17437)

**Read in full:** one version, lines 1-941 of 941 of the extracted text: main text (10 pages), figure and table pages (to p. 15), and the supporting information (22 pages: Methods S1-S2, Figures S1-S14, Tables S1-S5). Skipped: the two reference lists. Figures are images; I used their captions and the tables.

**What they did.** AgentSociety (an existing LLM-agent platform) in central Philadelphia: 369 agents, 41 census tracts, nine demographic groups from the American Community Survey. Baseline: "original" AgentSociety, which acts on generic need-based reasoning. Grounded version: 2023 American Time Use Survey routines turned into a time-varying Markov chain; the activity probability for the current time slot goes into the agent's memory and into the decision prompt. External benchmark: a household survey run during the July 2024 heatwave, 603 valid responses, "not an input for initializing, calibrating, or prompting the agents". No LLM is named anywhere in the paper. No seed count, run count, repeat runs or significance test is reported.

**What they found.** Table 1 (and Table S1): on a normal day, correlation with the time-use profiles rises 0.528 to 0.912, MSE 0.066 to 0.008. Heatwave day against the survey (Table S2): correlation 0.349 to 0.836, MSE 0.098 to 0.012; grounded closer in 5 of 5 groups. Change from normal to heat (Table S3): the grounded model shows 46.4% of the empirical shift in activity (0.03772 of 0.08156), the baseline 20.6%. Largest misses: work or study, and travel.

**What the abstract leaves out.** The 0.53 to 0.91 figure is a test against the SAME survey that built the routines, so it is a reconstruction check, not independent. Only the 0.35 to 0.84 figure is held out, and it uses seven coarse categories and five merged groups. The baseline got no routine information at all, so the contrast is "told the answer" against "not told". The grounded prompt weights "Consistency with Typical Behavior" as "the most important factor". The models, runs and variance are not given. The authors say the grounded model underestimates adaptation and that group-level profiles are checked, "rather than individual trajectories". The routines used a semi-Markov dwell-time rule to avoid "unrealistically short activity fragments".

**Our claims, checked.**
- "Routines from a time-use survey lift correlation with real activity profiles from 0.53 to 0.91" → OVERSTATED as an independent result. Those numbers are the normal-day check against the source survey. The held-out heatwave figure is 0.349 to 0.836.
- "An independent survey is kept back to check" → CONFIRMED. Quote: "used only as an empirical validation benchmark, not as an input for initializing, calibrating, or prompting the agents".
- How grounding enters: all three. Initial profile and typical_daily_activities in state memory (Method S2); the current-slot probability in the decision prompt; plus spatial constraints. The prompt "instructed the agent to follow its empirical routine unless the current context created a reason to adapt".
- Would it count as steering under our rule? YES. It puts the target distribution in the person's own prompt and tells him to follow it. That is the opposite of "tune the world, read uptake, never gate".

**For us.** This is a clear example of the thing the plan rules out, and it works well for matching a mix. Use it two ways. (1) As a named contrast: our arm that fixes the world and reads the mix is the independent-of-prompt version; report both the mix and a held-out check. (2) As a caution on our own backtest: any profile built from the letters and then scored against the letters is a reconstruction test (their 0.91), not a held-out one (their 0.84). Keep the Paris days held out, as the plan does.

**How far it carries.** Their setting: 369 population agents, unnamed LLM, aggregate group profiles over hourly categories, one day type, one city, one heatwave. Ours: one protagonist, months, a 27B Q4 model, a coded 1827 profile. Promising for "prompted priors fit a mix"; says nothing about a single life.

### Behavioral fidelity of long-horizon activity simulations · Cheng et al. (CMU, Fujitsu), EMNLP 2026 main, pp. 14351-14372 (24-29 Oct 2026) · ACL Anthology 2026.emnlp-main.625

**Read in full:** lines 1-1289 of 1289 of the extracted text, all 22 pages: main text, limitations, ethics, appendices A (metrics), B-C (dataset), D (backbones), E (leave-one-session-out), F (datasets), G (tables 9-16), H. Skipped: the reference list only.

**What they did.** A framework for scoring simulated days against real ones along two axes: time scale (local, time-of-day, day) and person against population. Case study: 43 hours of camera footage of a shared office, 55 people seen, but only 5 observed for several days (4 +/- 1 days, 7 +/- 1 hours a day); six hand-made activity labels. Six ways of conditioning an agent: none, authored persona, trace-inferred persona, persona plus two real full-day examples, statistical priors (first-order transition and time-of-day tables, with durations from real data, which REPLACE the LLM's activity choice), and a hybrid. Three backbones (Llama 3.3 70B, GPT-5.4-mini, Gemini 2.5 Flash), three runs each, eight-hour days, bootstrap intervals over the 5 people. Not pre-registered.

**What they found.** Section 7.1, Table 3: day-level time-allocation divergence (JS) .19-.24 for no-persona and persona arms, .010 for priors; transitions .31-.36 against .107 and .091. Section 7.2, Table 4: real days average 26.7 switches; priors give +38.0 and +32.3 more; persona arms give 10.8-15.0 fewer. Table 5: within-person day-to-day variability real .097; priors .018 and .026; persona arms .043-.064. Section 7.3: persona variants differ little, and the sign depends on the metric (21 of 78 contrasts exclude zero). Section 7.4: population-level divergence is smaller than individual-level in 76 of 78 cases. Appendix E (held out, one backbone, one run per fold): priors still win on time allocation (.071-.075 against .28-.30), but not clearly on transitions (two contrasts only).

**What the abstract leaves out.** Priors were built from the same corpus they are scored on in the main test. Five people, one week, an office, six labels. The authors say the priors are first-order only and higher-order ones "may yield greater behavioral coherence". Every arm, including the persona arms, has less day-to-day variation than real people. Backbone changed the size of results. They did not test counterfactual response: traces "do not identify why a pattern holds".

**Our claims, checked.**
- Priors "over-fragment routines and suppress within-person variability" → CONFIRMED, verbatim from the abstract. Add that the cause is the priors choosing each activity from a first-order table, and that all arms under-vary.
- "Statistical priors come closest to real activity distributions" → CONFIRMED in-sample; held out on one backbone for time allocation, weaker on transitions.
- "Priors can match an activity profile and still break a person's routines" → CONFIRMED (switch counts, variability).
- "Hence a profile read and never gated" → NOT IN THE PAPER as a test. It is our inference. They never compared read-only against steering; their priors act as a gate on the choice itself.
- Metrics beyond the mix, for the plan: episode durations, next-activity transitions, 3-gram and 4-gram motifs, time-of-day allocation and frequency in two-hour windows, switches per day and per window (signed and unsigned), within-person session-to-session variability, between-person variability (defined, not reported), each at individual and population level; measured by TV, JS, forward and backward KL, L1 and signed bias.

**For us.** Add to the health table, beside the mix: switches per day against the letters; dwell per category; within-person day-to-day variation (his own days against each other); transitions and 3-grams; all at the individual level, since he is one person (their 7.4). A world that makes his day more fragmented should show in switches before it shows in the mix.

**How far it carries.** Their setting: 5 office workers, six labels, hours-long days, 3 backbones. Ours: one man, ten categories, months, a 27B Q4 model. Promising for the metric list; Judgment for the numbers.

### RePair, causal mechanisms with generative agent-based models · Liu, Shang, Bhat and Jin (UC San Diego, UBC), 21 Sep 2026 · [arXiv 2609.35819](https://arxiv.org/abs/2609.35819)

**Read in full:** v1, lines 1-1714 of 1714 of the extracted text, 26 pages including Appendix A (models admitted). Skipped: the reference list (lines 1419-1695), glanced at. Figures are images; I used captions and the tables.

**What they did.** A four-step method for testing a "mechanism" in an LLM-agent world: (1) calibrate the world's operation settings and fix them; (2) turn each mechanism into one natural-language rule sentence, with a predicted direction; (3) run each rule against a matched baseline (same model, profiles, world text, initial state, schedule); (4) read traces to see whether the proposed pathway happened. Four small worlds: housing segregation (32 homes, 20 half-year periods; 12 configurations, 108 runs, 8 rules), public goods (4 players, 10 periods; 268 configurations, 1,608 runs, 5 rules), group polarization (24 configurations), cooperative cascades (16 configurations). Models are small and cheap: DeepSeek V4 Flash, GLM-4.7 Flash, Qwen 3.7 Flash/Plus, Gemma 4 26B/31B; four admitted per world. Intervals are 90% bootstrap over configurations. The outcome and predicted direction are "preregistered" in the paper's sense; no external registry is named.

**What they found.** Section 5, Table 2: segregation baseline gap 2.4 points; minority-status aversion +3.6 (control power 1.30). Section 6, Table 4: public goods baseline 84.8% contribute; money-maximising rule -78.6 points; negative reciprocity moves the wrong way (-2.7) while punishment rises by 15.6 acts. Section 6.3: leading rule recovered in every resample from 8 configurations; all five conclusions match the full sample in 80.4% of resamples at 40 and 94.2% at 268. Section 6.4: some wordings of inequity aversion push the outcome the opposite way; moving the same sentence changes the effect (R1 loses 10.9 points). Section 7.3: 12 of 23 rules have 90% intervals wholly in the predicted direction.

**What the abstract leaves out.** The interventions are sentences added to the agents' own profiles, not changes to the world. Calibration is not "fit to data": it picks settings that let the target behaviour occur (the segregation action budget was chosen because relocation appeared in 6 of 6 baselines against 1 of 6) and a threshold of about seven departures. Calibration used one model (DeepSeek V4 Flash) before the pool was screened. Freezing is not absolute: "discovering a new execution fault would reopen Step 1". Segregation rests on 12 configurations; polarization and cascades on 24 and 16. The authors say results "do not establish that agents behave like their real-world counterparts" and are bounded to "the baseline world and configuration pool tested".

**Our claims, checked.**
- "Calibrate settings in an order fixed beforehand" → CONFIRMED. Quote: researchers specify "the operation settings, their alternatives and calibration order" before any run (section 3.2).
- "Test no candidate while calibrating" → CONFIRMED. Quote: "No candidate rule is run during calibration, so calibration cannot select on any rule's effect."
- "Freeze, then run matched interventions" → CONFIRMED, with the reopen-on-fault rule above, which we may adopt as our amendment path.
- Whether it matches our setting: the matched interventions are rules put on the person. Our rule puts them on the world only. The design (paired, registered, wording pool, frozen settings) transfers; the intervention site does not.

**For us.** (1) For the paper-city waves (T64): register the order of the tunables before any run, run no candidate profile while calibrating, freeze, then run matched forks. (2) Treat each world-change as a set of wordings and positions, not one card: their R1 flipped sign across wordings. Our street cards should be tested in several phrasings. (3) Report control power (mean paired effect over its spread) and a resampling check of how many forks are enough. (4) Look at traces, not only the mix: an offer can change a count without changing what he did.

**How far it carries.** Their setting: small multi-agent games, 4-32 agents, short runs, small hosted models, several worlds. Ours: one protagonist, months, a 27B Q4 model. The procedure is Promising; the effect sizes tell us nothing about Hegel.

### When Plausible Is Not Realistic, mobility in LLM urban simulators · Santos, Viana and Silva, 11 Jun 2026 (SIGSPATIAL'26) · [arXiv 2606.13835](https://arxiv.org/abs/2606.13835)

**Read in full:** v1, lines 1-1073 of 1073 of the extracted text, 14 pages including Appendices A-E. Skipped: reference list only. Figures are images; I used captions, tables and the text around them.

**What they did.** Two LLM urban simulators on real mobility data. AgentSociety (open) and CitySim (closed, so the authors REIMPLEMENTED it from its paper). Default settings, Qwen-2.5-32B-Instruct, 10-minute steps, three runs each. Real data: Greater Paris GPS diaries (3,337 people, 7 days) and Shanghai phone records (58,502 users, 10 days). About 500 agents per run, started from the real people's home and work anchors. A second disjoint real sample (Shanghai only) measures how far two real samples differ. Not pre-registered. Metrics: travel-distance law, radius of gyration, daily visits, origin-destination flows, trip duration, dwell time, visit frequency, daily motifs, Scouter/Regular/Routiner profiles, and semantic activity metrics (Paris only).

**What they found.** Section 5.5, Table 5, Paris: activity mix (visit purpose) JSD 0.0296 for AgentSociety, but transitions 0.1125. CitySim: mix 0.0883, transitions 0.2405. Section 5.2, Table 3, Paris: dwell time W1 3.96 h (AgentSociety) and 30.24 h (CitySim); trip duration about 24 min both. Table 1: travel distance error 14.83 km (AgentSociety), 7.53 km (CitySim). Section 5.2 / Fig. 4: peak activity shifted by 3 to 12 hours. Section 5.3: runs are dominated by two-node home-work motifs. Shanghai reference sample errors are tiny (0.29 min, 0.26 h), so the gaps are not sampling noise.

**What the abstract leaves out.** The activity-mix result holds for AgentSociety on Paris only; CitySim's mix is three times worse, and semantic metrics were not computed for Shanghai. CitySim here is the authors' reconstruction. Part of the failure is a tooling fault: destination choice drew from all points of interest, and 57.45% of 223,149 OpenStreetMap points were benches, bins and the like (section 6.1). Adding richer map data raised a POI correlation from 0.55 to 0.80, but no rerun of the simulators is reported. CitySim's richer spatial model made temporal realism worse (section 5.2). Authors: behavioural diversity "does not reliably emerge solely from generic prompting".

**Our claims, checked.**
- "Two city simulators reproduce the mix of activities" → OVERSTATED. True for AgentSociety (JSD 0.03), not for CitySim (0.088), and only on one dataset. Quote: AgentSociety matches "semantic activity proportions broadly".
- "...and miss trip lengths, dwell times and transitions" → CONFIRMED in the data above (dwell and transitions most clearly; trip length is wrong in scale though the law's shape is right).
- "Hence test how long he stays and when he moves, not only the mix" → CONFIRMED as a reading of section 5.5: "realistic aggregate activity proportions do not necessarily translate into realistic activity sequences".

**For us.** Our Paris backtest should score dwell per category and time-of-day of moves against the letters (their DARD and dwell metrics), plus a transition matrix across the ten categories, beside the mix. Add a "two real samples" yardstick: how far two disjoint stretches of the letters differ from each other, so a gap is read against that floor. And check first that the engine's own place choice is sane, since their worst errors came from the place picker.

**How far it carries.** Their setting: 500 population agents, a 32B model, urban trips by GPS, 7-10 days. Ours: one man, a 27B Q4 model, months, coded letters. Promising for the metrics; the numbers do not transfer.

## Chapter 6 · Post-training: persona and voice

### Personality-tuned LLMs as social agents · Krabbe and Shi, 18 Sep 2026 · [arXiv 2609.21857](https://arxiv.org/abs/2609.21857)

**Read in full:** v1, lines 1–522 of 522 of the extracted text (lines 430–522 are the reference list, skimmed only); 8 pages, no appendix.

**What they did.** Two small models, Qwen2.5-7B-Instruct and Ministral-8B-Instruct-2410, got LoRA on q/k/v/o only, rank 16/alpha 32 and rank 32/alpha 64 (Table I, 6 epochs, early stopping, lr 2e-5, max length 512). Data: the Kaggle MBTI forum-post set plus DailyDialog utterances labelled by a RoBERTa classifier; about 582,000 observations, dialogue about 12.8%. The N/S class was oversampled by back-translation. How labels became training prompts is not described. Evaluation: 225 generated two-person dialogues per model variant, three scenarios (office, disaster relief, mask quarrel), five MBTI pairs. Three LLM judges (Qwen3-32B, Qwen3-30B-A3B, Mistral-Small-24B) guessed each speaker's MBTI type. No humans. Baseline is the same model, prompted with the type.

**What they found.** Baselines scored highest on all four dimensions (Table III). Qwen base macro F1 0.530 to 0.791; tuned 0.425 to 0.777. McNemar tests: baselines significantly better, except Qwen small-LoRA on F/T (Sec. IV.D). Tuned Qwen had more English (92% vs 88.35%) and higher Distinct-2 (0.55 vs 0.43).

**What the abstract leaves out.** Judge agreement is low: Krippendorff alpha never reached 0.8, and N/S fidelity alpha was 0.024 to 0.045 for Qwen (Table III). The authors say this limits confidence. They also say training on forum posts is "a major domain shift" and that varying only rank and alpha "weakens the conclusion" (Sec. V). The task is MBTI-type expression, not playing a named character. The result is worse than "no better": the tuned models were measurably worse by this proxy.

**Our claims, checked.**
- "a personality-tuned Qwen of 7B was no better at role-play than its prompted self" → OVERSTATED as evidence about us. True as a description of their Table III (tuned was no better, in fact worse). But the "role-play" is MBTI-label display, scored by LLM judges, after tuning on forum posts and labelled DailyDialog. Quote: "fine-tuning does not yield a better performance in doing so compared to the baseline models."
- Sources file: "not better at role-play than its prompted self" → CONFIRMED for the 7B/8B pair; label *Promising* is generous, closer to weak.
- "The published record gives a persona adapter little hope" → OVERSTATED: one paper, not on a character's own outputs, no human rater.

**For us.** Chapter 6 should cite this only as a caution that tuning on mismatched data can lower role-play quality. It should not be the sentence that carries the case against rung 1 or 2. The data (generic personality-labelled posts) is not our data (his own accepted outputs), so it says almost nothing about rungs 1 to 3. Allowed under our data rule only trivially; we would not use it.

**How far it carries.** 7B/8B LoRA on generic MBTI forum data, three LLM judges with poor agreement, against our 27B Q4 LoRA on one character's own text and one human judge. Label: Promising (weak); the plan sentence should be reworded or dropped as a pillar.

### Readers prefer AI trained on authors' books · Chakrabarty et al., v4 17 Mar 2026 (first posted 15 Oct 2025) · [arXiv 2510.13939](https://arxiv.org/abs/2510.13939)

**Read in full:** v4, lines 1–1775 of 1775 of the extracted text, 50 pages, main text and all SI sections S1–S10. Skipped: the reference list (lines 591–756). Figures are images; I looked at Figs 5, 7, 8 as pictures and read the rest from captions.

**What they did.** 50 award-winning authors; 28 MFA writers (3 per author) wrote one ≤450-word excerpt each from a prompt: 20 real excerpts, a style description, a content brief of a held-out real excerpt. In-context arm: GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro on the same prompt (150 pairs). Fine-tuned arm: 30 living authors, one GPT-4o per author via the OpenAI API (90 pairs; each author has ONE AI excerpt, set against 3 human ones). Judges: 3 MFA readers and 19–21 Prolific readers per pair, blind, forced choice, with written reasons; pre-registered (OSF).

**Recipe (S1.3, Fig. 6).** Books cut at paragraph breaks into 250–650-word excerpts. GPT-4o wrote a brief for each: "Describe in detail what is happening… Maintain the order of sentences." Pair: "Write a [n] word excerpt about the content below emulating the style and voice of [author]" + brief → real excerpt. 0.89M to 10.9M tokens per author (mean 3.94M; 118M total, Fig. 8). 3 epochs; 1 epoch for four prolific authors. Batch 1, LR multiplier 2, other defaults. The held-out excerpt was removed. Temperature 1.0; resampled on verbatim overlap (ROUGE-L 0.16–0.23). GPT-4o then ran a grammar and consistency fix on outputs.

**What they found.** MFA readers, in-context: OR 0.16 fidelity, 0.13 quality. Fine-tuned: 8.16 fidelity (CI 4.69–14.2), 1.87 quality (CI 1.16–3.02); predicted AI win 0.74 and 0.58 (Table 10). General readers: 16.65 and 5.42. Corpus size: slope CI spans zero, Spearman ≈0 (Table 14). 29 of 30 authors above parity on fidelity, 28 on quality.

**What the abstract leaves out.** The brief writer and the output editor were GPT-4o. The fine-tuning method behind the API is not stated. Only 30 AI excerpts in the fine-tuned test. Worst case: Tulathimutte, fidelity 0.18, on the smallest corpus (0.89M). Weak: Ernaux 0.51, Ishiguro and Min Jin Lee quality 0.49. Premium negative for 1 of 30 (fidelity) and 6 of 30 (quality). Corpus-size test has 30 points and a wide interval. Unblinded preference untested. Humans were MFA students, not published authors.

**Our claims, checked.**
- "pre-registered" → CONFIRMED, with deviations (S9): GLM not mixed model; 516 general readers vs 120 planned.
- "OR 0.16 / 8.16" → OVERSTATED. Both are MFA fidelity. On quality it is 0.13 and 1.87, near the floor.
- "trained from a model-written content brief to the author's real excerpt" → CONFIRMED; the model was GPT-4o.
- "corpus size did not matter" → OVERSTATED: "no detectable relationship" in 0.89–10.9M, 30 authors.
- "on a larger model trained in full" → NOT IN THE PAPER. "Complete works" is the data; "in full" is not the method.
- "on an author's own subjects" → CONFIRMED: briefs describe held-out real excerpts.

**For us.** Rung 3 copies the shape, with Qwen writing the brief (allowed). Our texts are 3.4M tokens, mid-range. Differences: translated philosophy, not fiction; non-English authors scored mixed (Ernaux 0.51, Ogawa 0.61, Han Kang 0.95); one excerpt, no persona. Their GPT-4o grammar pass breaks our rule. Keep rung 3 parked.

**How far it carries.** Closed API model, 30 authors, 90 pairs, 544 readers, against our 27B Q4 LoRA with one judge. Label: Promising.

### Open Character Training · Maiya et al., 3 Nov 2025 · [arXiv 2511.01689](https://arxiv.org/abs/2511.01689)

**Read in full:** v1, lines 1–2605 of 2605 of the extracted text, 43 pages, including Appendices A–G. Skipped: the reference list (about lines 688–1125). The 11 figures of Appendix G are images of Elo charts; I read their captions only.

**What they did.** Three instruction-tuned models: Llama 3.1 8B, Qwen 2.5 7B, Gemma 3 4B. Eleven assistant personas (sarcastic, loving, misaligned and so on), each a hand-written constitution of about 10 first-person lines. Stage 1, DPO (LoRA rank 64, alpha 128): "chosen" is GLM 4.5 Air with the constitution in its system prompt (reasoning prefilled), "rejected" is the student's plain answer. Prompts: LIMA plus about 500 constitution prompts, 45 of every 50 written by Llama 3.3 70B. About 6M tokens per pair. Stage 2, SFT, one epoch: 12,000 transcripts made by the post-stage-1 model itself (10,000 self-reflections from 10 prompts, 2,000 ten-turn self-conversations), system prompt dropped, about 8M tokens. Judges: GLM 4.5 Air and ModernBERT classifiers. No humans.

**What they found.** Prefill attack (Table 2), F1 distillation-only to full: Qwen 0.66 to 0.86; Llama 0.79 to 0.95; Gemma 0.84 to 0.95. Coherence win rate (Table 3), Qwen: 93.4% vs prompting, 94.4% vs steering, 75.4% vs distillation-only. Benchmarks (Table 4) barely move except for the misaligned persona.

**What the abstract leaves out.** There is no run of the self-transcript stage alone. Every "full" model had stage 1 first. They say the source and amount of introspective data is unexplored (Sec. 5). Evaluation is model-judged and the authors call it possibly circular. Personas are broad assistant styles, not a historical person. The "prompting" baseline is a system prompt; the gains are largest against "ignore role-play" instructions, a pressure we never apply. The misaligned persona got worse at facts.

**Our claims, checked.**
- "character by preference training against a stronger teacher" → OVERSTATED. The paper says "teacher", never "stronger". GLM 4.5 Air is named; its size is not stated here. The teacher is the same kind of model given the constitution as a prompt.
- "then on the model's own transcripts (LoRA r64)" → CONFIRMED (Sec. 2.4, 2.3; rank 64, alpha 128 in both stages).
- "models under 10B" → CONFIRMED. Quote: "all models fine-tuned are <10B parameters in size."
- "LLM judges only" → CONFIRMED. Quote: "Consulting human raters and cross-judge replication would strengthen these findings."
- "the teacher breaks the data rule" → WRONG as to the method, right as to the recipe as run. GLM 4.5 Air is not on our permitted list, so the run as written breaks the rule. But the teacher is the model prompted with the persona and the rejected answer is the model unprompted. Qwen in both roles fits the rule.

**For us.** Stage 2 works without any outside teacher by construction: the post-stage-1 model samples under the persona prompt, the prompt is removed for training. That is allowed under our rule. What is not shown is whether it works alone or with a self-teacher in stage 1. A Qwen-teaches-Qwen version of both stages is allowed and untested. Rung 1 already says "sample, filter, train, sample again".

**How far it carries.** 4–8B models, assistant styles, model judges, against our 27B Q4, one real historical voice and one human judge. Label: Promising for method, Judgment for our case.

### MemRole · Li, Cheng, Xiao et al., 1 Nov 2026 · [arXiv 2611.01778](https://arxiv.org/abs/2611.01778)

**Read in full:** v1, lines 1–1605 of 1605 of the extracted text, 25 pages, including Appendices A–E and the prompt tables. Skipped: reference list (lines 556–706).

**What they did.** Qwen3-8B and Qwen3-32B. Data: 75 novels, 181,137 turns (161,027 train). Each turn has a per-character memory pool: LLM-written, character-view notes of earlier scenes where the character was present, top-k (base 5). The target is the novel's real text. A "teacher LLM" (unnamed) writes a three-paragraph hidden trace (situation, memories woken, response plan) for each real turn; a validator LLM filters it. Stage 1: SFT, LoRA r8/alpha16, 8 epochs (8B settings; 32B not given). Stage 2, SR-OPSD, 100 steps: the student rolls out; the frozen SFT model writes a critique of the rollout against the real reference, using a fixed 12-item rubric; the same model seeing that critique is the token-level teacher (KL). Judge: GPT-5.5; environment model Gemini-3-Pro. Humans: 20 raters, 100 samples.

**What they found.** Table 1, six-metric average: 32B 64.25 vs Qwen3-32B 49.05 (+15.20); GPT-5.4 64.45, Claude-4.6-Opus 72.49. Of the six metrics, MAQ (+27.1) and RC (+17.5), their own, gain most. 8B ablation, dialogue average (Tables 2, 3): prompted 42.44; direct SFT 44.17; LHMT SFT 46.79; SR-OPSD 51.7. Human score 7.02 vs 5.21 (Table 13).

**What the abstract leaves out.** Test is on novels held out by book, same format as training. The fixed reasoning order gives about +1.4 prompted at 8B (Table 3a). Table 18's retrieval comparison (DenseRAG/GraphRAG/pool) gives all backends only pre-scene information, so the "could know" cut is never ablated. Pool size 0 to 5 is worth +3.18 (E.5). No 32B ablation. Limits say trace synthesis, rubric and judging all "rely on LLM assistance".

**Our claims, checked.**
- "15 points on a 32B" → CONFIRMED (15.20), but it is the whole package against the bare backbone, on their own test, judged by GPT-5.5.
- "memory pool cut to what the character could know… give 15 points" → OVERSTATED. Pool, order and training are bundled; at 8B most of the gain is stage 2 (+4.9) and trace-SFT, not the pool.
- "fixed order of reasoning" → CONFIRMED as LHMT; small effect prompted.
- "imitate a style well, decide badly" → NOT IN THE PAPER as a measurement; it is the introduction's framing.
- "their gain comes from reference answers in novels" → CONFIRMED in substance. Direct SFT on the references adds only +1.7; the critique needs the reference (Alg. 1: "o* is used only for critique construction").
- "their pool is our 1831 gate" → NOT IN THE PAPER. It is memory notes in context, not a block on what the model knows.

**What the self-distillation step needs.** A reference output per situation, a rubric, and a critique per rollout. The rubric was made by GPT-5.5 from 20,000 rollouts compared with references (C.7). The critic is the local SFT model. A frozen Qwen3-8B as critic scored almost the same (Table 11), but every variant saw the reference. No run without a reference.

**For us.** As written it breaks the rule twice (GPT-5.5 rubric, teacher-written traces) and has no equivalent of a reference for Delhi situations. Only Hegel's real passages or Welt's choice could stand in, which is rung 2. A rubric from Welt or local Qwen is untested. Keep "changes nothing now".

**How far it carries.** 8B/32B, fiction, 161k reference turns, GPT-judged, against our 27B Q4 on one card, no references, one judge. Label: Promising for novels; Judgment for us.

### ACTOR: Action-Centered Temporal Organization for Literary Role-Playing Agents · Gao, Ju, Wu, Wu, Fei, 2 Nov 2026 · [arXiv 2611.03184](https://arxiv.org/abs/2611.03184)

**Read in full:** v1, lines 1–1613 of 1613 of the extracted text, 26 pages including appendices and prompt tables. Skipped: the reference list (lines 680–870) only. Training details (learning rate, epochs, LoRA or full) are not in the text; the code is said to be on GitHub, which I did not open.

**What they did.** From 143 novels an LLM pipeline extracts "behaviours": a Thought, an Action (speech or deed) and an Observation, ordered by reconstructed story time (not reading order). Each comes with a profile, up to a few long-term and recent memories, and the scene. Names are anonymised. Training: 270,856 pairs from 115 works (first 80% of each character's trajectory). Evaluation: 17,560 four-way questions: 11,770 from the last 20% of those works, 5,790 from 28 unseen works. Baselines: Qwen-2.5 7B and 14B, Llama-3.1 8B, Qwen3-32B, CoSER-8B, HER-32B. Trained with RPO: DPO plus a likelihood term on the real act (beta 0.1; alpha 1.0 for Qwen, 0.25 for Llama).

**How the options are built (Sec. 3.1, Tables 16, 19).** The extraction prompt asks for "exactly three situationally plausible but character-inconsistent alternatives" per behaviour. A rewrite step matches length, form, register and formality, and keeps quotation marks for speech. Real and rejected acts have the same median length, 13 words (Table 6). The audit checks structure only (four options, valid answer; Table 5); I found no human check that the alternatives are truly out of character.

**What they found.** Chance is one in four (our arithmetic; the paper does not state it). Table 1, overall accuracy: Qwen-2.5-7B 71.34, 14B 76.96, Llama 69.15, Qwen3-32B 78.30, CoSER-8B 57.41, HER-32B 65.65; ACTOR 80.20, 86.00, 78.04. Gains 8.86–9.04 points; cross-work gains 7.04–8.89.

**What the abstract leaves out.** Untrained models score far above chance, so "choose badly" is wrong. Removing profile or memory costs only 0.4–3.6 points (Fig. 3), so most accuracy comes from the scene and the wording of the options. There is no option-only or scene-only control, and no human ceiling. Open-ended gains are mixed: ACTOR-14B character fidelity fell (38.50 against 42.95, Table 3), judged by one model. Option order and any position bias are not reported.

**Our claims, checked.**
- "143 novels in story order" → CONFIRMED ("143 diverse literary works"; ordered by corrected in-story chronology).
- "Each paired with a plausible act that is out of character" → OVERSTATED: three LLM-written alternatives per act, not one, and the pair used in training is the one closest in length.
- "Models choose badly among four" → WRONG as worded. Quote: "existing models struggle to reliably infer character-consistent actions" (abstract), against 69–78% accuracy.
- "Training helps (DPO with a likelihood term)" → CONFIRMED for selection (+9 points); MIXED for open-ended generation.

**For us.** The four-way format is usable, but copy the controls the paper lacks. Add a no-context arm (the day removed, four options only), shuffle the option order, and have Welt or a second model check a sample of the invented alternatives. Without the no-context arm, accuracy may show that Hegel's real act sounds more natural than the invented ones. Chance is 25%.

**How far it carries.** Novel characters, 7B–32B, 13-word acts, against one philosopher's real letters: the format is Promising; the validity of the measure for Hegel is Judgment until the controls are run.

## Chapter 6 · Post-training: learning from a verifier

### Bridging Offline and Online RL for LLMs · Lanchantin et al., 26 Jun 2025 · [arXiv 2506.21495](https://arxiv.org/abs/2506.21495)

**Read in full:** v1, lines 1–984 of 984 of the extracted text, 17 pages incl. appendices A–C and Figures 4–10. Skipped: the reference list (lines ~578–732) only.

**What they did.** One model: Llama-3.1-8B-Instruct. Two tasks: verifiable maths (NuminaMath, 261,440 problems after filtering; Math-Verify gives a 0/1 reward) and non-verifiable instruction following (1,000 WildChat prompts for 1,500 steps; Athene-RM-8B reward model, §3.1). Methods: offline DPO (sync interval s = infinity), semi-online DPO (s = 5, 10, 100), online DPO (s = 1), online GRPO (n = 8 samples best, App. Table 5). s is the number of optimiser steps between refreshing the sampling model. Pairs are best vs worst by reward (verifiable: a random correct vs a random incorrect). Batch size 32–64, lr 1e-6. Compute: 32 H200 for training plus 8 for inference (§3). Full fine-tuning is implied; LoRA is not mentioned for their runs.

**What they found.** Maths (Table 1, Math500): seed 47.4, offline DPO 53.7, semi-online s=100 58.9, s=10 57.2, online DPO 58.7, GRPO 58.1. Instruction following (Table 2, AlpacaEval LC, GPT-4-1106 judge): seed 27.3, offline 53.2, s=10 81.6, s=5 78.7, online 83.1, GRPO 75.2. So offline lags by a wide margin; semi-online matches online; online DPO is marginally above GRPO (§4.1). Mixed maths+chat training helps both (Table 3).

**What the abstract leaves out.** (1) Offline DPO still clearly beats the seed model; "weakest" means weakest of the trained arms, not harmful. (2) "Semi-online" means a refresh every 5–100 optimiser steps, i.e. 15 to ~300 refreshes in a run, not a few rounds. (3) s=100 was "too unstable" on the non-verifiable task (§4.1). (4) DPO runs diverge often; Adam epsilon had to be raised (§5.1). Without reference-model sync, response length collapsed (Fig. 2). (5) Entropy collapsed in every online and semi-online run on maths (Fig. 3). (6) The reward model is length-biased and lengths grew (§4.2). (7) One seed model only; they say so (§7). (8) No rejection-sampling SFT baseline anywhere. (9) The number of samples per prompt for DPO pairs is not stated in the text I read.

**Our claims, checked.**
- "One-shot offline pairs are the weakest recipe in the recent comparisons" → CONFIRMED for this paper, with a caveat. §4.1: "online and semi-online trained models all outperform the offline DPO model by a wide margin." Say "weakest of the DPO and GRPO arms in one 8B study", not "in the comparisons".
- Sources file: "Online and semi-online preference training match GRPO and beat offline clearly" → CONFIRMED. Online DPO is slightly above GRPO in both tasks.
- Plan's "sample, filter, train, sample again" → PARTLY SUPPORTED as direction only. The paper compares preference-pair training, not filtered SFT. Its refresh interval is 5–100 steps, far more often than "again".

**For us.** Rung 1/2 should not train on one batch of pairs made once. If pairs are used, refresh the sampling model between small chunks. At 300 pairs (rung 2) that means a few chunks of about 50–100 pairs, not an 8B-scale schedule. Keep the reference-model sync and length watch in mind: length collapse and entropy collapse are real risks. Nothing here says how few examples suffice.

**How far it carries.** Their tasks are maths and generic chat on an 8B model, thousands of steps, 40 H200s; ours are soft character tasks, a 27B Q4 base, LoRA on one 24 GB card, hundreds of examples. Direction (refresh beats one-shot): Promising. Any size or schedule: Judgment.

### A Minimalist Approach to LLM Reasoning (RAFT, Reinforce-Rej) · Xiong et al., 15 Apr 2025 (v2, 12 Jun 2025) · [arXiv 2504.11343](https://arxiv.org/abs/2504.11343)

**Read in full:** v2, lines 1–794 of 794, 13 pages. Skipped: the reference list (from line ~660). There is no appendix in the file, although Table 1's caption points to one for hyper-parameters; the repository link stands in for it.

**What they did.** Verifiable maths only (NuminaMath prompts, binary reward from Math-Verify, §4). Two models: Qwen2.5-Math-7B-base and Llama-3.2-3B-instruct. Compared: RAFT (rejection-sampling fine-tuning, trains on the rewarded samples only), RAFT++ (RAFT plus importance sampling and clipping), Reinforce, GRPO, PPO, iterative DPO, and Reinforce-Rej. Each training step samples 1,024 prompts with n = 4 replies each, mini-batch 512, lr 1e-6, up to 4,096 tokens (§4). Curves run to about 250–300 steps (Figs 1–4). Every step draws fresh samples from the current model, so RAFT here is many rounds, not one.

**What they found.** Table 1 (average over three maths sets). Qwen: base 23.6, RAFT 52.3, RAFT++ 56.1, iterative DPO 48.8, Reinforce 53.9, GRPO 56.3, PPO 52.5, Reinforce-Rej 56.4. Llama: base 13.1, RAFT 25.9, RAFT++ 27.6, GRPO 28.4, Reinforce 24.2. RAFT learns faster early, then its entropy collapses and it plateaus near step 100; GRPO overtakes it (§5, Figs 1, 3). Dropping prompts where every reply was wrong helps Reinforce most (§5.1, Fig. 4).

**What the abstract leaves out.** (1) Plain RAFT is 4 points under GRPO on Qwen (52.3 vs 56.3) and 2.5 under on Llama. The "competitive" version is RAFT++, which adds importance sampling and clipping. (2) RAFT is run online with hundreds of rounds, which is the opposite of "one round". (3) Positive-only training collapses entropy: "rapid reduction in policy entropy, limiting exploration" (§1, §5.1). (4) Negative samples matter for keeping exploration. (5) Maths only, a 0/1 verifier, and a Qwen model built for maths. (6) Their iterative DPO is weaker than RAFT, which sits oddly with paper 1 (different settings, no reconciliation). (7) Hyper-parameters were tuned for each method (Table 1 caption).

**Our claims, checked.**
- Sources file: "training only on the samples a verifier rewards is competitive with reinforcement learning" → CONFIRMED with a qualifier. §5: RAFT++ "remarkably close to … GRPO". Say "within 0.2 to 4 points, on maths, over hundreds of fresh-sampling rounds".
- Plan: "Sample, filter, train, sample again" → SUPPORTED in form (RAFT is exactly this loop), NOT SUPPORTED for the size. They use 1,024 prompts × 4 per step for ~250 steps; "about 1,000 kept replies" is not tested or implied.
- Plan: pairs made once are weakest → NOT IN THE PAPER (no one-shot arm).

**For us.** The loop matches rung 1's recipe. But expect a fast gain then a plateau with falling diversity, so the diversity gate in chapter 6 is right and should be checked each round. Skip prompts where every draw failed or every draw passed (no contrast, no lesson). Add a clipping or low-step-size guard if training more than one pass on a buffer.

**How far it carries.** Verifiable maths, 3–7B, hundreds of rounds, tens of thousands of samples per round; ours is soft character tasks, a 27B Q4 base, LoRA, about 1,000 samples. Loop shape: Promising. Sizes and gain: Judgment.

### Is it RL or Data? GRPO vs rejection-sampling fine-tuning · Chaudhry (Purdue), 19 Oct 2026 · [arXiv 2610.25812](https://arxiv.org/abs/2610.25812)

**Read in full:** v1, lines 1–1320 of 1320, 20 pages including Appendices A–J. Skipped: the reference list (lines ~749–805) only. Note: the author states the text was drafted with Claude from his outlines (AI use statement).

**What they did.** One synthetic task: a procedural integer-counting generator (filters, transforms, then count/sum/median; §2.1). One base model: Qwen3-4B-Base with LoRA rank 64 on all linear layers. Prompt sets of 100 problems: Easy, Mixed, Curated (73 prompts where the base got 1–7 of 8 right). RFT: 192 samples per prompt drawn once from the base model, correct ones kept, 2–8 epochs; 27-run sweep per arm. GRPO: 300 steps, 8 prompts × 8 completions, one fixed recipe. Three seeds per arm; hypotheses preregistered (App. A). Secondary arm: iterated RFT, 3 rounds × 64 samples per prompt on the 73 curated prompts. Compute: one H100, 252.7 GPU-hours.

**What they found.** Greedy test accuracy (Table 2): base 67.3; RFT 65.9–69.6; GRPO 74.3–78.8; iterated RFT 70.1. GRPO minus RFT: +10.9 curated, +8.4 easy, +9.2 mixed (Table 3; easy and mixed were added post hoc). Iterated RFT minus RFT +3.2, GRPO minus iterated +7.7, so "about 30%" of 10.9 (§3.4). Kept samples per RFT arm: 6,653–13,834 (Table 1).

**What the abstract leaves out.** (1) One-round RFT did not beat the base model on greedy accuracy: "single-round RFT … does not improve on the base model at this budget" (§3.1). Its gain was in sampled accuracy, and a format-only reward got 60.3 vs 54.4 for RFT (Table 10), so much of that is format. (2) The 3.2-point iterated gain is near cross-machine noise of up to 2.3 points (§3.4, App. G). (3) GRPO's out-of-distribution result is not interpretable: 20–55% of its answers were cut off. (4) The author says plainly the result "do[es] not contradict" Xiong et al.; RFT resampled every step was not tested (§4, §5). (5) RFT kept mostly easy prompts (595 of 7,961 kept came from hard ones). A per-prompt cap might narrow the gap (§5). (6) GRPO's gain sat on the hard tier. (7) No pass@64 gain for any arm: it sharpens, it does not add skill.

**Our claims, checked.**
- Sources: "RL beats one round of filtered training by 8–11 points" → CONFIRMED (8.4, 9.2, 10.9 on test; two of the three post hoc).
- "On one small task (Qwen3-4B with LoRA)" → CONFIRMED; it is Qwen3-4B-Base on one synthetic maths-like task.
- "Repeating the round recovers about 30% of the gap" → CONFIRMED, with limits: three rounds, 3.2 of 10.9 points, within 1.4× the evaluation noise.
- Plan: "Sample, filter, train, sample again; about 1,000 kept replies" → OVERSTATED as support. The paper's evidence for repeating is weak (3 rounds, 30%), and its kept sets were 6,000–14,000, not 1,000.

**For us.** Do not expect one filtered pass to move the target. If a rung runs, plan several refreshes and judge by a blind comparison, not by format-like gains. Cap kept replies per situation so easy situations do not dominate. Check any gain against a "format only" control.

**How far it carries.** One counting task, a 4B base, 100 prompts, an exact verifier; ours is soft character tasks on a 27B Q4 model. Direction (one round is weak, refreshing helps some): Promising. Numbers: Judgment.

### BOND: Aligning LLMs with Best-of-N Distillation · Sessa et al. (Google DeepMind), 19 Jul 2024 · [arXiv 2407.14622](https://arxiv.org/abs/2407.14622)

**Read in full:** v1, lines 1–1173 of 1173, 22 pages including Appendices A–B. Skipped: the reference list (lines ~677–905) only. Derivations in App. A read, not re-proved.

**What they did.** Method: make the policy's output distribution match the best-of-N distribution of the reference model, where "best" is by a scalar reward model. The loss mixes forward KL (plain fine-tuning on the best of N) and backward KL (a policy-gradient term using the sample's reward quantile), the Jeffreys divergence (§4.2). Iterative BOND repeatedly distils best-of-n (n = 2 or 4) of a moving anchor (§4.3). J-BOND is the practical version: per prompt 1 policy sample plus 2 anchor samples, anchor updated as an exponential moving average, eta = 0.02 (§5). Tasks: XSum summarization with a T5 policy and a T5 entailment reward model (§4); Gemma 2B and 7B as chat agents with a "large previously trained reward model" (§6). Batch 128, lr 3e-6, 100 warm-up steps. Baseline: REINFORCE with KL penalty at four strengths (Fig. 7). Dataset sizes and total steps are not given.

**What they found.** All results are curves, not tables. Jeffreys (beta 0.5) lowers both KLs to the best-of-N distribution (Fig. 2). Non-iterative BOND saturates early; iterative BOND keeps improving (Fig. 4). The moving anchor beats a hard-swapped one on reward/KL (Fig. 5). J-BOND has a better reward/KL trade-off than REINFORCE at every strength tested (Fig. 7).

**What the abstract leaves out.** (1) The "improved results on several benchmarks" are not in this paper; §6 points to the Gemma report (Table 5). (2) "Outperforms other RLHF algorithms" means REINFORCE only, judged on the reward model's own reward against KL. No human or held-out judge. (3) It needs a scalar reward model giving a strict ranking; ties are broken arbitrarily (footnote 1). A binary accept/refuse verdict gives huge ties. (4) The loop is online and continuous: thousands of steps, fresh samples every step. (5) The authors warn that large N causes reward over-optimisation and magnifies quantile errors (§4.3). They only "conjecture" more robustness to reward hacking (§3.3). (6) Only the forward-KL half is plain SFT on the best sample; the other half needs the model's own log-probabilities and on-policy sampling.

**Our claims, checked.**
- Sources: "the best of N can be distilled into weights" → CONFIRMED as method and as reward gain, in their setting. §1: the policy gets "the strong performance of Best-of-N sampling" with one sample. No test of how few examples suffice.
- Plan's use as support for "sample, filter, train, sample again; about 1,000 kept replies" → PARTLY. Fig. 4 supports "again" (one-shot distillation saturates). It says nothing for 1,000 samples, LoRA, or binary labels.
- "Promising, taken together" → fair for direction only.

**For us.** The useful part is small. Distilling best-of-4 into an adapter is the idea behind "the filter distilled into weights", which chapter 6 already parks because there is only a quarter of a call to win. If it is ever tried, keep best-of-2 per round with a slowly moving reference, not one large best-of-N, and keep a KL anchor to the base. Ties in our verdicts mean we would need a graded score (for example, Welt's pairs) to rank.

**How far it carries.** Summarization and chat on T5 and Gemma 2B/7B with a learned reward model and full training runs; ours is a 27B Q4 base with LoRA and hundreds to a thousand examples. Idea: Promising. Anything on size or rounds: Judgment.

### Knowledge in the Harness, Reliability in the Weights · Zhang, Ren et al. (Brightendata), 11 Nov 2026 · [arXiv 2611.15268](https://arxiv.org/abs/2611.15268)

**Read in full:** v1, lines 1–1311 of 1311, 18 pages including Appendices A–E and Tables 4–15. Skipped: the reference list (lines ~646–897) only.

**What they did.** Model: Gemma 4 12B, instruction-tuned, as agent and as editor (served with vLLM). Benchmark: tau2-bench retail (114 tasks) and airline (50), with a DeepSeek user simulator. Policy text is split into skill documents that the agent loads on demand. Loop per round (§4, Fig. 1): the deployed system runs a fresh batch of 300 generated tasks per domain, 4 trials each. (1) Harness: the base model diagnoses failed conversations and writes, rewrites or deletes short rules in a rules section; a rule survives only after code checks, two counterexample self-reviews, a paired 6-trial retest (keep if at least 4 more successes) and a validation gate on 200 tasks × 8 trials. (2) Weights: GRPO trains a rank-32 LoRA on whole conversations with the rules in context, rollouts 16/8/5 per task (never/mixed/always solved), 4 epochs × 6 steps × about 50 tasks; checkpoint gate. Two rounds. Compute: about 50k conversations, 84 hours, about 340 GPU-hours per round on four A100/A800.

**What they found.** Pass1 retail 72.6 → 85.1, airline 56.0 → 75.5; pass4 48.2 → 66.7 and 38.0 → 60.0 (Table 2). Vs reference agent: +11.8 and +8.0 pass1. Never-solved tasks: rules alone 44% retail, 27% airline; weights alone 25% and 5%. Always-solved: weights 95% and 99%; rules 87% and 93% (Table 3, §5.4). Weights trained with rules in context did not learn the facts: H0-M2 failed all 28 baggage conversations that skipped the booking skill (§5.4).

**What the abstract leaves out.** (1) "Teacher-free" means no stronger LLM. A programmatic verifier with reference outcomes drives everything, and the editor sees the grader's reference outcome (§4.2). (2) Much of the airline "rescue" repairs a defect the authors made by splitting the policy: 14 of the 15 never-solved airline tasks depend on the split (§5.4, §5.5). (3) The never-solved retail bin has only 8 tasks. Bins come from the same run that is compared against, so regression to the mean is possible; a split-half check keeps the pattern (App. E). (4) The weights-only arm was trained with rules in context, so it is not a clean weights-alone run. (5) The retail pass4 interaction is not significant (+12.3 [−0.9, 25.4]). (6) One base model, two domains, two rounds (Limitations). Most single updates are not individually significant.

**Our claims, checked.**
- "Without a teacher, rules in the harness rescue tasks the agent never solved; weights make solved tasks reliable" → CONFIRMED in this setting. §5.4: "Rules thus make unsolved tasks solvable, and training makes solved tasks reliable." Add: a hard verifier was present, and part of the airline gain is repair.
- "Structure first, weights for reliability" → SUPPORTED as a pattern; the paper's own reason is that GRPO "learns little from tasks the agent rarely solves" (§1).

**For us.** Fits the ladder: rung 0 and the world's structure first, weights only for reliability. It also says an adapter will not learn facts that sit in context; for voices, the audit and slots must hold the facts, and the adapter should only be asked to use them reliably. Rungs 1–2 are not GRPO and not 340 GPU-hours, so none of its numbers transfer.

**How far it carries.** Tool-using customer-service tasks with an exact database verifier, 12B bf16, four 80 GB GPUs, 300 fresh tasks per round; ours are soft character tasks, 27B Q4, one 24 GB card. The pattern: Promising. The sizes: Judgment.

### Wrong the Same Way: cross-prompt sharing and reward hacking in RLVR · Li, Pandey, Chen, 9 Nov 2026 · [arXiv 2611.13218](https://arxiv.org/abs/2611.13218)

**Read in full:** v1, lines 1–1127 of 1127, 21 pages including Appendices A–F. Skipped: the reference list (lines ~458–647) only. A 4-page NeurIPS 2026 workshop-style paper with long appendices.

**What they did.** A deliberately tiny environment: "single-digit multiplication with a two-digit answer space, in which the full response distribution of a small transformer is enumerated exactly" (§1). 64 prompts, 100 possible answers, a 2-layer transformer of 101,706 parameters trained from scratch (§5). The verifier accepts the right answer plus chosen wrong strings (false positives only; no false negatives, §3). Leaks are put into the base model by 3% contaminated supervised data. They vary universality u, the share of prompts that accept the same wrong string, at a fixed false-positive rate. Training: exact policy gradient with Adam, sampled GRPO (group of 8), and plain SGD, 400 steps, ten seeds, CPU only. Control: one separate copy of the network per prompt.

**What they found.** At the optimum of a KL-regularised objective the accepted set keeps the base model's composition, so hacking is inherited (Prop. 1). With shared parameters, hacking rose from 0.025 at u = 1/64 to 0.160 at u = 1, against a base value of 0.128; true accuracy fell from 0.974 to 0.840 (§6). Separate copies show no such slope (§6.2). Under GRPO the drift reaches +0.663 at u = 1 (§6.4). Two verifier patches that remove equally many errors differ by 8 ± 2 points of true accuracy, and by 38 ± 9 at a higher learning rate (§6.5).

**What the abstract leaves out.** (1) It is two-sided: leaks few prompts accept are pushed below the base rate, not up (Fig. 2, §6). (2) The sign of the drift depends on step size; at the three smallest Adam rates every seed suppresses the idiosyncratic leak, at the two largest every seed amplifies it (§6.1). (3) At u = 1 under Adam the mean drift is within its error bar, with one collapsed seed (§6). (4) A KL penalty returns the inherited rate but costs accuracy (§6.4). (5) The leaks come from contaminated supervised data, not found by the policy; "a shared error is one identical string rather than a shared way of going wrong" (Limitations). (6) The theory covers one channel with homogeneity assumptions; the authors call the reading of LLM studies "a hypothesis that we have not tested on those models". (7) Only policy-gradient RL was run; no selection-and-SFT arm.

**Our claims, checked.**
- Sources: "training on a verifier's reward amplifies the verifier's errors that many prompts share" → CONFIRMED in this toy setting, with "and suppresses ones few prompts share, at small steps".
- Plan: "weights learn a checker's blind spots" → OVERSTATED. Shown only for wrong answers the model already produces across many prompts and a verifier that accepts the same wrong string across many prompts. Narrow errors were suppressed.
- Sources "For us": "the four-word echo rule is such an error waiting to be learned" → NOT IN THE PAPER. It models false positives only; an echo rule that wrongly rejects or wrongly accepts is untested here.

**For us.** The advice that carries is the audit target: count the audit's misses by hand, and look for the ones the voices repeat across many scenes, since those are what training could entrench. Check the adapter's output for the same repeated miss before and after. Do not claim that any miss will be learned.

**How far it carries.** A 100k-parameter transformer on multiplication, exact verifier, no language. Mechanism: Promising (clean theory, tiny setting). Transfer to LoRA on a 27B model with a soft audit: Judgment.

## Chapter 6 · Post-training: LoRA, diversity and serving

### Learning Rate Matters: Vanilla LoRA May Suffice · Lee et al., 4 Feb 2026 (v2, 19 May 2026) · [arXiv 2602.04998](https://arxiv.org/abs/2602.04998)

**Read in full:** v2, lines 1–3172 of 3172 of the extracted text, 49 pages. Skipped: the reference list (about lines 650–1300). I also read the survey table of 64 prior papers (App. B, Table 3), which has no bearing on our claims.

**What they did.** Ten methods: plain LoRA plus nine variants (OLoRA, PiSSA, MiLoRA, Init[AB], LoRA-GA, DoRA, GraLoRA, RandLoRA, LoFT). Base (not instruct) models: Qwen3-0.6B, Gemma-3-1B, Llama-2-7B, Llama-2-13B. Tasks: maths (MetaMathQA, 100k), commonsense (15k), code (104k), instruction following (Alpaca 52k, IFEval). Learning rate swept 1e-6 to 1e-3 and beyond, 4 values per decade; batch 16–512; rank 4–256. One epoch, max length 512, bf16 base, all linear layers, no dropout. Three seeds, except Llama.

**What they found.** All nine variants are compared only on Qwen3-0.6B maths (Fig. 1, r=128: 0.84-point spread) and Gemma-3-1B commonsense (Fig. 6, about 37%). On every other model, and in every rank sweep, only four are run: PiSSA, MiLoRA, Init[AB], DoRA (Sec. 3.3.1). Gaps at peak: 0.52 (Gemma maths), 0.43 and 1.75 (Llama-7B maths, code), 1.81 (Llama-13B maths). Rank sweep on Gemma: up to 1.67 (maths, r=32) and 2.15 (code, r=4) (Sec. 3.3.2). Method-specific rates: PiSSA about 10x lower than LoRA; LoRA-GA and OLoRA about 18x lower (Sec. 4.2). Best rate falls as rank rises: r=4 wants 5.6x the rate of r=256 (App. H, IV). Tuning the rate matters more than batch size.

**What the abstract leaves out.** Alpha equals r in every run, so the scale is 1, not 2 (Table 5, App. E). The paper says its choice factors alpha out because tuning the rate is equivalent to tuning the scale. Models are 0.6B–13B; they state larger models are unverified. Llama results are single-seed. The tasks are accuracy tasks; nothing on voice, style, persona or diversity. They say variants may help with forgetting, which they did not measure, and LoRA-One reported about 2% gains they did not test. Their grids are 9–16 rates per setting, each run three times.

**Our claims, checked.**
- "Plain LoRA, rank 16, alpha 32, all linear layers" → NOT IN THE PAPER as a recipe. They never use alpha 32; alpha=r. Rank 16 appears only in the Gemma rank sweep. Alpha 32 at r=16 is scale 2, which App. E cites (Biderman et al.) as marginally better than scale 1. Reword: "alpha 32 comes from LoRA Without Regret, not from this paper."
- "Variants finish within a point or two once the rate is tuned" → CONFIRMED, with one edge case: "all methods achieve similar peak performance (within 1–2%)" (abstract). The widest gap seen is 2.15 points.
- "Nine variants" (sources file) → OVERSTATED. Nine only on two model-task pairs; four elsewhere.
- "Two of them do not survive conversion for llama.cpp" → NOT IN THE PAPER. It never mentions deployment. Five init variants swap the base weights for a residual (Sec. 2.2.2), and DoRA changes the forward pass, but that is our inference, not theirs.
- "Rate tuned" → the paper's main message. The plan gives no rate, and the paper shows a wrong rate costs far more than the variant choice.

**For us.** Plain LoRA is a sound default. But the rate must be swept per rank, and the sweep is the cost: at 27B on one 3090, budget a handful of rates, not 12. State alpha explicitly, and note their rates do not transfer to alpha 32. Remove the claim about conversion from this citation.

**How far it carries.** 0.6B–13B accuracy tasks, bf16, against a 27B Q4 voice task: the finding on variants is Established for their setting; for us it is Promising.

### LoRA Without Regret · Schulman and Thinking Machines Lab, 29 Sep 2025 · Thinking Machines "Connectionism" blog post

**Read in full:** the page text as saved, lines 1–373 of 373, from the title to the citation block. A web post, no page count. Nothing skipped.

**What they did.** Supervised fine-tuning and reinforcement learning with LoRA against full fine-tuning on Llama 3 and Qwen3 models, including a 30B mixture-of-experts. Data: Tulu3 (instruction following) and OpenThoughts3 (reasoning), one epoch; RL on MATH, GSM and DeepMath. Rank 1 to 512, a learning-rate sweep for each condition, constant schedule. SFT is scored by log loss, not by sampled tasks. They also swept 14 models for the best learning rate.

**What they found.**
- LoRA matches full fine-tuning on small and medium post-training sets, and falls behind when the data exceeds its capacity ("What matters for LoRA").
- Low ranks fall off the best curve at a step count that rises with rank (Rank).
- All layers: attention-only is worse even at matched parameters; "mlp rank=128" beats "attn rank=256" at similar size (Layers).
- Alpha: "We use α = 32 … following standard practice" and "We were unable to improve on these hyperparameters" (Setting hyperparameters). The 1/r scaling makes the best rate roughly the same across ranks.
- Learning rate: "consistently 10x" the full fine-tuning rate; fitted multiplier 9.8 (Optimal learning rates).
- Short runs: "an optimal multiplier around 15x over the FullFT for short runs", with a footnote: "anecdotal evidence … under ~100 steps or so".
- Capacity: the first-epoch log-loss, about 1 bit (0.69 nats) per token, bounds the bits to memorise; 2 bits per parameter is a long-training ceiling (Discussion).

**What the abstract leaves out.** The post has no per-rank table of how much data a rank absorbs: "we can't yet make accurate forecasts" (Open questions). It says LoRA is less tolerant of large batches, regardless of rank. Measure is loss, not voice or belief. No quantised base (QLoRA) arm. Short-run advice is preliminary. The authors' stated view of pretraining-like scale is that LoRA "underperforms" where data "exceed[s] the storage limits of LoRA parameters".

**Our claims, checked.**
- "Plain LoRA, rank 16 … on all linear layers" → CONFIRMED on all layers; their data says MLP layers carry most of the gain and attention adds nothing on top of MLP-only.
- "Alpha 32" → CONFIRMED as what they used, but not a tuned finding. Alpha and learning rate trade off, so quote them together. At rank 16 it equals the 2r rule of Biderman et al.
- "A learning rate about ten times that of full fine-tuning" → CONFIRMED. Quote: "optimal LR for LoRA is consistently 10x the one used for FullFT".
- "A higher rate for runs under about 100 steps" → OVERSTATED as advice. It is "preliminary evidence", about 15x, "anecdotal".
- "How much data a rank can absorb" → NOT IN THE PAPER as a rule. Only the bits-against-parameters method.

**For us.** Keep the recipe. State learning rate as ten times our full-fine-tune reference, tested with a short sweep, and drop the short-run multiplier unless our run is under about 100 steps. Their capacity argument suggests 3.4M tokens is far below LoRA's capacity, so a weak result at that size is probably not a rank limit. That is my reading, not theirs; it points to the data, not the adapter. Batch size should stay small.

**How far it carries.** Their setting: bf16, 8B to 30B, loss on instruction and reasoning sets. Ours: 27B Q4, a persona. Label: Promising.

### LoRA Learns Less and Forgets Less · Biderman et al., TMLR Aug 2024 (arXiv v2, 20 Sep 2024) · [arXiv 2405.09673](https://arxiv.org/abs/2405.09673)

**Read in full:** v2, lines 1–1903 of 1903 of the extracted text, 39 pages. Skipped only the reference list (lines 649–928).

**What they did.** Llama-2-7B, bf16, on code and math. Continued pretraining (CPT) on StarCoder-Python (up to 20B tokens) and OpenWebMath (14.7B, repeated to 20B). Instruction tuning (IFT) on Magicoder (73M tokens) and MetaMathQA (103M). Full fine-tuning against LoRA at rank 16, 64, 256, all linear layers, alpha = 2r, with a learning-rate sweep. Learning is HumanEval and GSM8K; forgetting is the average of HellaSwag, ARC-C and WinoGrande (Sec. 3, 4.1).

**What they found.**
- CPT: "LoRA underperforms full finetuning across all configurations" (Sec. 4.1). Code at 20B tokens: full 0.263, best LoRA (r=256) 0.224 (Table S1). Math: full 0.293, LoRA 0.202 (Table S3). The gap widens with more tokens.
- At the smallest sizes, 0.25B to 0.5B tokens, code CPT is close: 0.152 full against 0.142 to 0.144 LoRA (Table S1). Math CPT at 0.25B: full 0.155, LoRA 0.162 to 0.163 (Table S3).
- IFT: rank 256 matches full on code (0.498 against 0.497, Sec. 4.1). On a mixed chat set LoRA at rank 16 is "on par" (Sec. 4.4, App. C).
- LoRA forgets less (Sec. 4.2). It also gives more varied outputs: more unique HumanEval answers than full fine-tuning (Sec. 4.5).
- Full fine-tuning's weight change is high rank, 10 to 100 times typical LoRA ranks (Sec. 4.6).
- Advice (Sec. 4.7): use LoRA for IFT, "not continued pretraining"; alpha = 2r; LoRA learning rate about ten times the full rate; attention-only is worse than MLP or all.

**What the abstract leaves out.** Smallest CPT run is 0.25B tokens, about 70 times our 3.4M. Nothing below it. Data is code and math, scored by benchmarks. Voice, style and belief are not measured. Model is 7B and unquantised, with no QLoRA arm. "Diversity" means variety of the model's outputs, not variety of the training text. The authors say the gaps may differ with model size (Sec. 6). The rank analysis covers CPT only (Sec. 6). Results use the LionW optimiser; AdamW was compared only on IFT (App. B.1).

**Our claims, checked.**
- "Nothing shows it moves voice or conviction at 3.4 M tokens" → NOT IN THE PAPER. The paper neither shows nor denies it. It does show LoRA learns less than full fine-tuning in CPT, with the gap small at 0.25B and growing after about 1B. Wording: "No study we found tests voice or conviction. The nearest, Biderman et al., finds LoRA learns less in continued pretraining, in code and math at 0.25B to 20B tokens."
- "and our first adapter agrees" → NOT IN THE PAPER; our own result.
- Recipe "rank 16 and alpha 32" → CONFIRMED on alpha = 2r. Quote (Sec. 4.7): "α = 2r is crucial for high ranks". Note that they call rank 16 too low for code IFT.

**For us.** The paper gives no ground to expect a 3.4M-token LoRA to shift voice. It also gives no ground to rule it out. A weak effect from low rank would be the expected direction. If we try again, trying a higher rank is the cheap test, and for style we should choose instruction-style pairs over raw book text, since the paper finds IFT is where LoRA works. The "forgets less" result favours keeping LoRA for safety of the base model. Alpha 32 at rank 16 is consistent with their rule.

**How far it carries.** Their setting: 7B bf16, 0.25B to 20B tokens, benchmark scores. Ours: 27B at Q4, 3.4M tokens, style. Label: Judgment.

### Synthetic Continued Pretraining · Yang et al., Sep 2024 (v2, 3 Oct 2024; ICLR 2025) · [arXiv 2409.07431](https://arxiv.org/abs/2409.07431)

**Read in full:** v2, lines 1–2744 of 2744 of the extracted text, 45 pages. Skipped: references (about 903–1590) and the proof of Theorem 1 (about 1919–2139). I read the theorem statements and the curve-fit section.

**What they did.** QuALITY: 265 articles and short books by many authors, 1.3M tokens, average about 5,000 tokens each (Sec. 3). Test: 4,609 four-choice reading questions, answered without the text. EntiGraph has GPT-4-turbo list entities per document, then write text on each pair or triple of entities, giving 455M synthetic tokens. Llama 3 8B was continued-pretrained with full parameters, 2 epochs, 10% replay of general text (App. C). Baselines: raw text, 4 epochs; rephrases, stopped at 38M tokens; QA fine-tuning (App. D).

**What they found.**
- Closed-book accuracy: base 39.49%, Raw CPT 38.15%, EntiGraph 56.22%, GPT-4 51.30% (Fig. 2, Sec. 4.2).
- EntiGraph is log-linear in synthetic tokens up to 455M. Rephrasing "scales poorly" (Sec. 4.2).
- It gives about 80% of the gain from retrieval (16.73 of 20.86 points). With retrieval on top, 62.60 against 60.35 (Sec. 5, Table 3).
- Summaries of the books have fewer false claims than raw-CPT summaries (Sec. 4.3).

**What the abstract leaves out.**
- Raw training on the small corpus did not help; it was below the base model. The authors guess two reasons: narrow text distribution, and "limited diversity of knowledge representations" (Sec. 4.2).
- The generator is a stronger model than the student. The authors say this is not simple distillation because the student beats GPT-4's closed-book score. They did not test self-generation (Sec. 7.1).
- They checked the synthetic text for errors only by reading "a few books" (Sec. 7.1).
- The measure is factual recall about plot and author claims. Voice, style, stance are not tested.
- Full-parameter training on an 8B model, not LoRA, not quantised. The text reports no confidence intervals.

**Our claims, checked.**
- Quote "hundreds to thousands of diverse representations" → CONFIRMED verbatim in the abstract. Quote: "to learn a given fact, models must be trained on hundreds to thousands of diverse representations of it". It is a framing sentence. In the intro it rests on others (Allen-Zhu and Li, 2024: "thousands of examples per fact"). This paper does not measure that count. Wording: "Yang et al. cite prior work that a fact needs hundreds to thousands of varied exposures; their own result is that one pass over 1.3M tokens of raw text did not help and 455M synthetic tokens did."
- Setting → the first pass should say: facts about books, 8B, full fine-tuning, GPT-4-written augmentation.
- Implication for a 3.4M-token corpus of one author → OVERSTATED if read as "it will learn facts". Their corpus size is similar (1.3M), and raw training failed there. The paper says nothing on whether the same holds for style.

**For us.** Plain training on the books should not be expected to put Hegel's claims into the weights. If we want facts of his thought in the model, the path is synthetic variety, and it costs a generator run of hundreds of millions of tokens with a stronger model. For a 27B model on one GPU that is out of reach for now. This supports keeping the books as retrieval text, which is where the paper says synthetic CPT merely adds to retrieval (Sec. 5). Keep our "first adapter agrees" as our own evidence, not this paper's.

**How far it carries.** Their setting: many authors, factual questions, 8B full fine-tune, 455M synthetic tokens. Ours: one author, voice and conviction, 27B Q4 LoRA, 3.4M real tokens. Label: Judgment.

### Diverse Preference Optimization (DivPO) · Lanchantin et al., 30 Jan 2025 (v4, 22 May 2025) · [arXiv 2501.18101](https://arxiv.org/abs/2501.18101)

**Read in full:** v4, lines 1–1474 of 1474 of the extracted text, 22 pages. Skipped: the reference list (about lines 632–827).

**What they did.** One model: Llama 3.1-8B-Instruct, full fine-tuning, learning rate 1e-7 for DPO and DivPO, on H100s. DivPO builds preference pairs differently. Sample N answers, keep those within a reward band (rho), pick the most diverse as "chosen" and the least diverse below the band as "rejected", then train with the normal DPO loss. Three diversity criteria: model probability, word frequency, an LLM judge. Three tasks: JSON personas (name, city, occupation; reward 1 for valid JSON), five-keyword stories, and Wildchat instruction following (AlpacaEval 2.0). Baselines: the Instruct model, SFT, DPO, GPT-4o, o1-mini; online and offline.

**What they found.** Personas, Table 1: average diversity Instruct 24.07%, SFT 17.43%, DPO 20.44%, online DPO 8.54%, online DivPO (frequency) 54.14%, with valid JSON about 99.8%. GPT-4o scored 1.22%. Keyword stories, Table 4: unique 1-grams Instruct 47.8, DPO 31.1, SFT 22.8; DivPO rho=0.3 gives 54.3 at ArmoRM win rate 0.677 against the Instruct model. Instruction following, Table 2: unique 1-grams Instruct 1393, DPO 994.7. The abstract's "74.6% more diverse than DPO" is the keyword-story figure (rho=0.3, Sec. 4.2), bought with a 6.4% quality drop. Metrics (App. B.1): gzip compression ratio, unique 1-grams, entropy estimated as the mean of minus log probability.

**What the abstract leaves out.** The narrowing they measure is what SFT or DPO does to an already-instruct-tuned model. They never compare a base model with its instruct version. Diversity costs quality: in Table 4 the ArmoRM win rate falls from 0.84 (rho=0.1) to 0.40 (rho=0.5). Raising temperature adds diversity but quality falls (Fig. 11). The stated limit: DivPO needs a preference loss and "does not work for other RLHF losses such as GRPO". The quality judge is a reward model, not people.

**Our claims, checked.**
- "Post-training 'tends to sharpen the output probability distribution'" → CONFIRMED as a quotation (abstract). Support is partial: it is the authors' framing plus citations to earlier work (Sec. 2), backed by their own SFT/DPO drops on one 8B model.
- "Post-training narrows what a model says" → OVERSTATED as a general fact; CONFIRMED as: "SFT and DPO on top of an Instruct model lowered diversity (Tables 1, 2, 4); online DPO most." Quote: "we confirm that DPO training is prone to diversity collapse."
- "Diversity is a gate" → NOT IN THE PAPER. They treat diversity as a trade-off with quality, tuned by rho, not a pass/fail test. The gate is our design.
- Sources file "For us: diversity is a gate on every adapter" → our inference, not theirs.

**For us.** The paper is a usable recipe for what to measure. On short structured outputs, it counts distinct values per field over valid outputs, gzip ratio and unique tokens over 16–32 draws per prompt, with the base model as the reference. We can run those on short JSON thoughts without any training. It also warns that online preference training collapses faster than offline.

**How far it carries.** An 8B Instruct model, full fine-tune, creative tasks, against our 27B LoRA served locally: the direction (preference tuning narrows) is Established for their setting; the size of the effect on our adapter is Judgment.

### What pass@k Cannot Measure · Rath, Dandekar, Dandekar, Panat, 5 Oct 2026 · [arXiv 2610.07405](https://arxiv.org/abs/2610.07405)

**Read in full:** v1, lines 1–548 of 548 of the extracted text, 10 pages including the appendix. Skipped: the reference list (lines 450–476) only. It is a NeurIPS 2026 workshop paper, non-archival; configs and rollouts are "not (yet) packaged for public release" (Appendix).

**What they did.** One model: Qwen2.5-1.5B-Instruct, full fine-tune in bf16, no LoRA. Three arms, three seeds each, 187 steps, 1,500 GSM8K training problems: GRPO (8 rollouts, no KL), RFT (cross-entropy on the single shortest verifier-passed rollout), RFT with a KL brake. Single-seed extras: GRPO with a length penalty, on-policy self-distillation. Evaluation at temperature 1.0: 100 held-out GSM8K problems with 32 samples each; MATH-500 with 16 samples, including a hard subset (levels 4–5, 100 problems).

**What they found.** Table 1 (change over training, 3 seeds): GRPO lowers all three diversity measures (token entropy -0.055, unique answers per problem -1.30, answer entropy -0.164); both RFT arms raise them (+0.028, +0.56, +0.091 for plain RFT). No overlap in any seed. Table 2: pass@1 GRPO 0.634 against RFT 0.571; pass@8 and pass@32 overlap (0.914 vs 0.910; 0.969 vs 0.972). Among correct answers only, distinct-3 is 0.436 for GRPO against 0.512 and 0.509 for RFT, about 15% lower, and 14% after cutting all to 157 words (Sec. 3). Against the untrained checkpoint on hard problems, RFT is significantly worse and GRPO is not different (Fig. 2).

**What the abstract leaves out.** Scale: 1.5B only, one starting checkpoint, easy maths. RFT and GRPO differ on several things at once, so the cause is not identified. Most of the raw unique-answer gap is accuracy passing through the metric: the count-controlled gap among wrong answers is only 2.2–2.9% (Sec. 3). Some checks use two seeds, not three (a logging bug). Pass@1 does separate the arms. The paper itself says the direction of GRPO's effect is disputed at larger scale (Sec. 1).

**Our claims, checked.**
- "Two training methods (GRPO and RFT) move diversity in opposite directions" → CONFIRMED for this setting: "GRPO decreases all three in every seed" and RFT raises them (Sec. 3).
- "Unseen by the usual score" → OVERSTATED. Unseen by pass@8 and pass@32 on GSM8K; pass@1 does separate the arms, and on hard problems pass@1–2 separate them too. Reword: "unseen by pass@k at large k."
- Implied use as general evidence that post-training narrows → NOT IN THE PAPER. They say their claim "concerns the protocol", not which method is better.

**Measures we could compute on short JSON thoughts** (definitions in Sec. 2 and Appendix):
- Answer entropy: Shannon entropy of the distribution of a normalised categorical field (the chosen act) over N samples per situation; unparseable output counts as its own category.
- Unique answers per situation, with their count-control (subsample a fixed number) because the raw count tracks accuracy.
- Distinct-3: unique word-trigram fraction pooled over samples, among valid outputs only, cut to a shared word budget.
- Token entropy over the full vocabulary: needs logits; we would have to check what llama.cpp returns.

**For us.** Report diversity beside quality, on the same samples, split by "passed the world's filter". Their power note is useful: with 100 problems, 0.02 was the smallest detectable pass@1 effect. Use at least 16–32 samples per situation, and run each arm twice for the noise band.

**How far it carries.** 1.5B, GSM8K, full fine-tune against our 27B LoRA on free text: the metric definitions are Established; the effect sizes are Judgment for us.

### llama.cpp at master, commit fc504f9 · read from the sparse clone · not run

**Read:** tools/server/server-common.cpp lora utils (lines 289–355) and the chat parser (1489–1709); server-context.cpp launch_slot_with_task (1864–1935), can_batch_with (~532–550), the batch apply (3545–3560), GET/POST lora (3304–3340, 6525–6582), the completion handler (5234–5300) and post_chat_completions (5949–5967); server-schema.cpp (the `lora` field, 231–239, and the evaluator, 500–520); common/common.cpp (1322–1356, 1458–1510, 1674–1684); common/arg.cpp (2945–3000, 3854); src/llama-adapter.h and .cpp (205–315); src/llama-graph.cpp (1709, 1797–1807); the whole of convert_lora_to_gguf.py (550 lines). Not read in full: the rest of the 7,217-line server-context.cpp, which I searched for lora and cvec.

**a. Per-request `lora`, unlisted adapters at scale 0, no list takes the global scales → CONFIRMED, with one edge.**
- server-schema.cpp:232: "Adapters not listed default to scale 0.0".
- server-context.cpp:1864–1876, construct_lora_list: `output[i].scale = 0.0f` for any id not in the request.
- server-context.cpp:1879: `task.params.lora.empty() ? params_base.lora_adapters : construct_lora_list(...)`. An empty list `[]` is also "no list", so it takes the global scales.

**b. `--lora-init-without-apply` loads adapters without applying them → PARTLY. The plan's reliance on it may be wrong.**
- common.cpp:1503: `if (!params.lora_init_without_apply) { common_set_adapter_lora(...) }`. The flag only skips the apply at start-up.
- arg.cpp:2951: `--lora` stores each adapter with scale 1.0. I found no code in tools/server or common that sets the scale to 0 when the flag is on (the flag appears only in common.h, common.cpp, arg.cpp).
- server-context.cpp:3557, once per batch: `common_set_adapter_lora(ctx_tgt, slot_batched->lora)`. A request with no `lora` gets `params_base.lora_adapters`, at scale 1.0.
- README:1315 says the flag initialises scales to 0; the code I read does not show that. Reading only, not run. Test: start with the flag, call GET /lora-adapters, then send a request with no `lora` field and see whether the output changes. Until then, name the adapters on every request, and send `scale: 0` explicitly for "off". Never send `[]`.

**c. Adapter change clears the prompt cache; different adapters are not batched → CONFIRMED.**
- server-context.cpp:1880–1884: `if (!are_lora_equal(...)) { if (lora_should_clear_cache(...)) { slot.prompt.clear(); }`. For ordinary (non-activated) LoRA, lora_should_clear_cache is always true (server-common.cpp:315–316). It clears that slot's prompt; no reload of the adapter file.
- server-context.cpp:549: `&& are_lora_equal(lora, other_slot.lora)` in can_batch_with. README:618: "requests with different LoRA configurations will not be batched together".
- The cache is per slot, so how it behaves with several slots is untested.

**d. Converter keeps only `lora_alpha` and A/B; DoRA fails; rsLoRA under-scaled → CONFIRMED, with a correction: DoRA fails loudly.**
- convert_lora_to_gguf.py:532 `alpha = lparams["lora_alpha"]`, written at 431. The file never reads `use_rslora` or `use_dora`.
- Lines 476–487: any tensor that is not lora_A/B or a norm prints "Not a lora_A or lora_B tensor" and calls `sys.exit(1)`. A DoRA magnitude vector would stop the conversion (our inference about PEFT's tensor name). llama-adapter.cpp:295 also throws on an unexpected suffix.
- llama-adapter.h:55: `alpha ? adapter_scale * alpha / rank : adapter_scale`. rsLoRA trains with alpha/sqrt(r), so served at alpha/r it is too small by a factor of sqrt(r): 4x at rank 16 (our arithmetic).
- Related: our own recipe (alpha 32, rank 16) is scale 2.0 here; the converter and runtime reproduce that.

**e. Control vectors only by flags at start-up → CONFIRMED.** arg.cpp:2972–2999 (`--control-vector`, `--control-vector-scaled`, `--control-vector-layer-range`); common.cpp:1458–1467 calls llama_set_adapter_cvec once at context creation. No cvec or control_vector hit anywhere in tools/server. The `/v1/chat/completions/control` route (README:1583) is about reasoning, not vectors.

**f. `lora` on /v1/chat/completions as well as /completion → CONFIRMED.** server-common.cpp:1690–1698 copies every remaining body key into llama_params ("This allows user to use llama.cpp-specific params ... via OAI endpoint"); post_chat_completions (server-context.cpp:5949–5966) passes them to handle_completions_impl, which calls eval_llama_cmpl_schema (5293), where the `lora` field lives. README:618 documents it under /completion only.

**What world/mind.py does today.**
- mind.py:117–131, `chat()`: adds `"lora": [{"id": 0, "scale": adapter_scale}]` only if adapter_scale is not None. Adapter id is hard-coded 0; scale limited to 0 or 1 (lines 35–42, 121–122).
- Voice (NPCs): chat_voice, 73–83: names the adapter only if `HEGEL_VOICE_ADAPTER_SCALE` is set (config.py:60–63); else relies on the server default.
- Decision: chat_decision, 90–101: names it only if `decision_adapter_scale` is set (config.py:74–77); engine.py:321.
- Writing: chat_writing, 103–115, only if `writing_adapter_scale` set (config.py:67–70).
- Complete-style writing sittings: complete(), 153–170, sends no `lora` field ever; engine.py:408.
- Bare `chat()` calls (diarist owl.py:200; letters engine.py:283; sitting outline engine.py:399; yes/no choice engine.py:553): no adapter named. Worse, mind.py:119–120 turns any bare call into scale 1 once the voice scale is set at all, even to 0.
- With no env settings, every request relies on the server default; `pc/TRAINING.md:219` starts the server with `--lora` and no init-without-apply, so that default is the adapter at scale 1.

**What must change before any adapter is served.** (1) Verify claim b on the PC. (2) Give each job its own adapter id and scale in the request (voice, decision, writing, complete, owl, letters, choice), never rely on the default, and never send `[]`. (3) Add a `lora` field to complete(). (4) Remove the bare-call-becomes-1 rule at lines 119–120. (5) Convert with plain LoRA only; check alpha in the .gguf. (6) Measure the cache clear on a real switch, as the plan says.
