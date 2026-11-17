# What the papers say about depth: a simulated life that does not look preprogrammed

Written on 17 November 2026. The owner's worry is that Hegel's days "might look more like a preprogrammed nonsensical experiment". The question put to the literature: what makes a simulated life less repetitive, less mechanical, and inwardly coherent over weeks, and what does not.

**How these were read.** Each PDF was fetched from arxiv.org/pdf/<id>, extracted with `pdftotext -layout` and plain `pdftotext`, and read from the text. Seven papers were named. Four more were found by searching the arXiv API (several dozen queries, three seconds apart). Each note says which parts were read and which were not. Where a table was garbled by the extraction, the note says so, and in two cases the figure was rendered and looked at.

**Search note.** No paper was found for angle (a), a role-played character that notices its own situation, beyond the one the project already read (2606.11502). No paper was found for angle (b), measured reader or viewer engagement with one character over many days. Queries on "fourth wall", "simulation awareness", "Truman", "diary study", "companion longitudinal" and "viewers" returned nothing relevant. Seen by title only and not read: "The Double-Edged Sword of Open-Ended Interaction: How LLM-Driven NPCs Affect Players' Cognitive Load and Gaming Experience" (arXiv 2604.10107), and "Sampling Is Not Curiosity: Why LLM Agents Should Investigate" (arXiv 2611.10501, a position paper). Neither was read. Nothing in this file rests on them.

**What this file is not.** It is evaluation material. Nothing in it is ever training data. The "For us" lines are Judgment.

---

### Generative Agents: Interactive Simulacra of Human Behavior · Park, O'Brien, Cai, Morris, Liang and Bernstein, Apr 2023 (v2, 6 Aug 2023, UIST '23) · [arXiv 2304.03442](https://arxiv.org/abs/2304.03442)

**Read in full:** yes, all 22 pages of the PDF: sections 1–9, Appendix A (the cached summary prompt) and Appendix B (the 25 interview questions with sample answers). Reference list skimmed only.

**What they did.** 25 agents in a Sims-like town (Smallville), run by gpt-3.5-turbo. Each agent has a memory stream, retrieval scored on recency, importance and relevance (all weights 1), reflection (triggered when summed importance passes 150, about two or three times a day), and a plan broken down from day to hours to 5–15 minute steps. Two evaluations. (1) A controlled one: agents "interviewed" at the end of a two-game-day run, 25 questions in five categories. 100 Prolific raters ranked five answer sources for believability: the full architecture, three ablations, and answers written by a crowdworker who watched the replay. Rankings were turned into TrueSkill scores. (2) An end-to-end run of two game days, measured by diffusion of two facts, new acquaintances, and turnout at a party.

**What they found.**
- §6.5.1: believability (TrueSkill μ, σ about 0.7): full architecture 29.89; no reflection 26.88; no reflection and no planning 25.64; crowdworker 22.95; no observation, reflection or planning 21.21. Effect of full vs bare: d = 8.16. Kruskal-Wallis H(4) = 150.29, p < 0.001. All pairs differ except crowdworker vs bare.
- §7.1.2: knowledge of the mayoral candidacy 1 to 8 agents (4% to 32%). Knowledge of the party 1 to 13 (4% to 52%). Network density 0.167 to 0.74. Hallucinated acquaintance claims: 6 of 453 (1.3%). Party: 5 of 12 invited agents came. Of the 7 who did not, 3 gave a conflict and 4 "expressed interest ... but did not plan to come".
- §7.2, the failure modes, in the authors' words: "the most common errors arose when the agent failed to retrieve relevant memories, fabricated embellishments to the agent's memory, or inherited overly formal speech or behavior from the language model" (§1). As agents learned more places, some chose odd ones ("the town had spontaneously developed an afternoon drinking habit"). Some misread norms (a one-person bathroom entered by two). Instruction tuning made agents polite and agreeable: Isabella "rarely said no", and "Over time, the interests of others shaped her own interests".
- §4.3: without a plan, "Klaus would eat lunch at 12 pm, but then again at 12:30 pm and 1 pm". The authors' summary: "Optimizing for believability in the moment sacrifices believability over time." This is an example, not a measurement.

**What the abstract leaves out.**
- The ablations were run at interview time. Each ablated variant was given the memories of the full architecture's two-day run: "equivalent access to all memories accrued" (§6.2). So the ablation tests whether answers to questions are more believable. It does not test whether a life lived without reflection or planning looks worse.
- Raters ranked written answers. They did not watch days. The human baseline is one crowdworker per agent, and the authors say it is not "maximal human performance" (§8.2).
- One run, one model (ChatGPT), 25 agents, two game days. "Limited to a relatively short timescale" (§8.2). Cost: "thousands of dollars in token credits and taking multiple days".
- Nothing measures repetition across days, or whether the town's behavior goes flat after day two.
- The abstract says the components "each contribute critically". The data show a ranking of answer quality, with the largest step (about 4.4 points) from adding observation memory to a bare prompt, about 1.2 points for adding plans, and about 3.0 points for adding reflection. "No reflection" means observations plus plans.

**For us.** Memory, reflection and planning matter for answers to "who are you, what did you do, what do you think of X". That is evidence for keeping a record of Hegel's days that he can draw on, and for reflection that cites its evidence. It is not evidence that reflection makes a month of days less repetitive. The most useful lines for the owner's worry are the failure modes. The agreeableness finding (an agent that rarely says no, and takes on the interests of whoever it talks to) is exactly the risk for a 27B model voicing Hegel in a conversation with a shopkeeper or a student. The location finding supports keeping the set of places and what each is for under code control. The paper's importance score ("1 to 10, mundane to poignant") is asked of the model. PAVE (below) shows that this step can fail.

**How far it carries.** Solid for "memory helps answers". Weak for anything about depth over weeks: two days, answers rated, one run.

---

### Humanoid Agents: Platform for Simulating Human-like Generative Agents · Wang, Chiu and Chiu, 9 Oct 2023 · [arXiv 2310.05418](https://arxiv.org/abs/2310.05418)

**Read in full:** yes, all 10 pages of the PDF, including Appendices A.1–A.3. Reference list skimmed.

**What they did.** Extends Generative Agents with three states: five basic needs (fullness, fun, health, social, energy, each 0–10), one of seven emotions, and a closeness score (0–30) for each other person. Needs fall at fixed rates. If a need is 3 or below, or the emotion is not neutral, the agent is asked whether to change its plan. After each activity the model is asked whether the activity satisfies a need or changes the emotion. After each conversation it is asked whether the agent enjoyed it (closeness plus or minus one). ChatGPT 3.5. Three worlds: Lin's family (2 agents), Friends (3), Big Bang Theory (3), simulated for two weekdays at 15-minute steps.

**What they found.**
- Table 1 (§5.1): three volunteer annotators labelled one simulated day in Lin's world (144 activities, 30 conversations). Agreement between annotators, Fleiss' κ: 0.556 (closeness) to 0.972 (fullness). The system's agreement with the annotators' majority, micro-F1: fullness 0.972, energy 0.861, emotion 0.84, closeness 0.9, social 0.743, health 0.694, fun 0.66.
- The system "substantially over-predicts" which activities meet a need: health 34% vs 4.9% by humans, fun 44.4% vs 10.4%, social 47.2% vs 24.3% (§5.1).
- Table 2 (§5.2): one need set to zero at the start of the day. Mean change in time spent on activities for that need: health +156%, energy +56%, fullness +35%, social +12%, fun −9%. The authors note that in normal settings agents "spend 11 (out of 18 simulated hours) doing something they enjoy, 8.75 hours on social interactions", so a zeroed fun or social need is met early in the day.
- Appendix A.1: fixing an emotion for the day raised matching activities most for anger (+15), then sadness and fear (+10). The authors had to switch off emotion updates, because otherwise "an agent who wakes up sad can become neutral right after washing up". Appendix A.2: conversation length is an inverted U in closeness (for example 5.4, 7.25, 6.2, 6.0 turns), with no statistics.

**What the abstract leaves out.**
- Nobody judged believability. The experiments check that agents respond to a state they were handed. They do not test that days look more human.
- The model both sets the need levels (by saying yes or no to "does this activity satisfy X") and reads them back. It says yes far too often. This is the reason the fun and social needs barely moved behavior.
- Two weekdays, 8 agents, one run per setting. Each need falls at the same rate for every agent. Plans are not synchronized between agents (stated limitation).
- Emotions are single labels with no inertia and revert in a step or two. The paper offers no evidence that they carry across days.

**For us.** The finding with most force for a boredom or restlessness mechanic is the "fun" row. If the engine asks the 27B model "did that satisfy you?", it will mostly say yes, and the pressure will vanish. If code owns the numbers, and what counts as satisfying a need is decided in code from what happened in the world, the pressure can last. Emotion needs inertia (days, not steps) or it washes out, as the authors found. This paper does not show that either makes the character deeper.

**How far it carries.** Solid as a manipulation check (inject a state, behavior moves). Not applicable to depth: no human raters of believability and no horizon past two days.

---

### Simulating Human Behavior with the Psychological-mechanism Agent: Integrating Feeling, Thought, and Action (PSYA) · Dong, Liu, Yu and Kang, 4 Jun 2025 · [arXiv 2507.19495](https://arxiv.org/abs/2507.19495)

**Read in full:** yes, main text, Appendices C–F, and G.1–G.4 (G.5 and the PAD arithmetic in Appendices A–B skimmed). 23 pages of PDF.

**What they did.** Llama-3-70B agents with: (a) emotion over three timescales (event emotion, mood that lasts days or weeks, personality as long-term affect), kept in a pleasure/arousal/dominance space, with emotion and mood decaying; (b) a "default mode" of thought with three sub-modules (scenario simulation, thinking about self and others, mind-wandering), chosen by stochastic rules, with random switches into it even during focused tasks; (c) a decision rule that overrides the schedule when a need, an emotion or a task passes a threshold. Evaluation: (1) one simulated day for 8 agents; (2) re-runs of five classic psychology experiments (learned helplessness, cognitive dissonance, foot-in-the-door, social exclusion, diffusion of responsibility) with agent groups the same size as the human ones.

**What they found.**
- Table 1 (daily life, §4.2): scores 0–5 from three raters. Emotion, persona consistency, diversity, credibility. Base (Generative Agent) 3.65 / 3.46 / 2.73 / 4.21. Affection module 4.36 / 3.67 / 2.88 / 4.37. Self-social module 3.70 / **4.83** / 2.80 / 4.48. Mind-wandering module 3.78 / 3.50 / **3.93** / 4.27. Full 4.41 / 4.83 / 3.89 / 4.57. So the diversity gain comes from the mind-wandering module alone (+1.20), and the persona-consistency gain from the self module alone (+1.37).
- Example given: after a failed interview, agents without mind-wandering "take a walk" or "talk to a friend". With it, an agent might recall "a book about animal protection" and visit an animal shelter (§4.2).
- Table 2 and §4.3: learned helplessness is "reproduced" only with the emotion module. Fig. 2 and §4.4, foot-in-the-door: base agents showed no effect; full PSYA 55.6% agreement in the performance condition against 52.8% for humans. Fig. 3 and §4.5, diffusion of responsibility: PSYA-Sim 100%, 62%, 38% by group size, like humans; PSYA-Self did not show it.
- Appendix G.2: cognitive dissonance. "Regardless of the framework used, none of them successfully replicated the human results". The agents ignored money. The authors then added a line to the prompt: "An activity is either meaningful or can earn an appropriate amount of money; otherwise, it is not worth doing."
- Appendix G.4: social exclusion. Only the self-social variant reproduced the human effect. The scenario-simulation variant made the excluded agents feel better, because the agents "tended to imagine scenarios where others would pass the ball to them".

**What the abstract leaves out.**
- The daily-life test is one day, 8 agents, three raters who were lab colleagues, "the top three with the highest annotation consistency" (App. E). "Due to cost constraints, we only used the PSYA-Full framework to conduct the full-day simulation" (§4.2). The ablation rows come from three scenes picked out of that one day (interview, confession, coffee tasting), repeated ten times.
- The abstract says the framework "successfully" replicates human experiments. Dissonance was not replicated until the prompt was changed after seeing the failure. In Table 2 the group labels look inverted: "E" (noise can be stopped) shows the high failure rate, which the appendix assigns to the inescapable group. I could not resolve which is right.
- The "extended experiments" test new hypotheses against the authors' own simulator. There is no human data to check them.
- Nothing runs past one day, so the "mid-term mood lasting days or weeks" is never tested over days or weeks.

**For us.** This is the one paper in the set that shows an inner-life module raising rated diversity of behavior (2.73 to 3.93 of 5), and it points at the right mechanism for a thinker: unprompted association (mind-wandering, scenario simulation) rather than another need. For Hegel the analogue would be a recall of an old thought or place that does not match the present moment, used when the day is slack. The evidence is thin: three raters, three scenes, one day. The mood-with-inertia idea (recovery slower after a failure) is plausible and agrees with Humanoid's finding that emotions wash out. Note the dissonance failure: the model does not weigh incentives unless the prompt says to, which is a warning about expecting inner conflict to appear on its own.

**How far it carries.** Weak to promising: human raters, but tiny and short, and the authors adjusted the system after seeing failures.

---

### Agentopia: Long-Term Life Simulation and Learning in Agent Societies · Wang, Zheng, Wu et al., 5 Jun 2026 (v1) · [arXiv 2606.07513](https://arxiv.org/abs/2606.07513)

**Read in full:** the main text (pp. 1–17: design, rewards, experiments, limitations) and these appendix parts: B.1, B.9 (the 16 role-play principles), B.10–B.12, C.1, C.3, D.1–D.2, D.8–D.11, and the opening of the case studies (E.1, a sample of cases). Not read: the prompt tables, appendix A (world and character creation), D.3–D.7, D.12, the full case-study tables. The PDF has 79 pages.

**What they did.** Three fictional worlds, each with 100 agents run for "10 simulated years" by Qwen3.5-397B-A17B. The year is 10 weeks (B.2: n_w = 10, with 5 activity days and 5 contact rounds per week). So each run is about 100 weeks, 500 activity days per agent. Each week has four stages: plan, contact (agents message and propose joint activities), activity (one per day: joint, solo, chance encounter, public event), review. Agents keep their own memory files (read-before-write), weekly diaries, a "fulfillment" score in four parts that decays 15% a week ("an intrinsic motivation loop: inactivity leads to declining fulfillment") and a vitality score. A second LLM, the "environment model", plays the world: it judges whether an action is feasible, writes the outcome, arranges chance meetings for idle agents, creates public events, updates profiles yearly, and filters replies against 16 role-play principles. A "life reward" (social standing by PageRank over agents' ratings of each other, subjective fulfillment, savings) is used to select trajectories for fine-tuning the model.

**What they found.**
- §5.4: one run costs 13.7 billion tokens, 567K calls, about 186 hours. Weekly runtime rises from about 80 to 140 minutes as memory grows: "memory growth serves as a major computational bottleneck".
- Table 2, §5.3: after fine-tuning on trajectories from years 1–4, 4-year runs in two worlds: subjective reward +1.8%, economy reward +2.5%, "respected by" +24.2%, "liked by" +15.9%. Material fulfillment −14.8%, solo activity −19.8%, skill advances −29.6%.
- Table 3: on the CoSER role-play benchmark, judged by Qwen3-235B, the tuned model's average is 49.16 vs 42.51 for the base model (+15.6%), above Claude 4.5 Sonnet (45.21), well below Claude 4.5 Opus (62.43).
- D.11: with five models, 20 agents each per world, two worlds, 4 years: Qwen3.5-27B ranks last in total reward (−0.07, against −0.06 DeepSeek-v3.2, −0.03 Qwen3.5-397B, +0.06 GPT-5-mini, +0.10 Gemini-3-Flash). The spread is small.
- D.9: "striving" agents (more solo work and skill growth) get lower mood and social fulfillment than leisurely ones. D.10: the same architecture gives different social dynamics in the three worlds.
- E.1: about 60 curated cases, "No behavior is scripted or hand-crafted". Examples: a chef weighing three ingredient tiers ("I cook because it matters"); a developer whose frugality "eroded Material Fulfillment from 63 to 0 over months"; a Campus character with 402 joint activities whose vitality "crashed from 70 to 0", with "No burnout script".
- §3.5: "agents tend to hallucinate environmental details and objects without location information explicitly provided", so locations were added.

**What the abstract leaves out.**
- No human judged anything. The only quality measure outside the simulation's own numbers is the CoSER score, judged by a Qwen model of the same family as the one tuned.
- No ablation of any design feature: not the memory files, the weekly review, the fulfillment decay, the encounters, or the 16-principle filter. The paper cannot say which of them produces the "rich emergent behaviors". The principles include "Do not repeat the same content three or more times" and "Dialogue should provide new information rather than spinning in circles", but whether the filter reduced repetition is not measured.
- "10 years" is 100 weeks of a made-up calendar, 100 agents in a society, not one life. The reward is the authors' own construction. The limitations state that "all feedback an agent receives comes from other AI models".
- The cases are the authors' selection.
- The tuned model got worse on material fulfillment and solo activity. The authors read this as a trade-off the reward caused.

**For us.** Three ideas are worth borrowing as ideas, with no evidence that they work. (1) A weekly review that writes a diary entry and updates the character's own notes, with a rule that an update starts from reading what was there. (2) Satisfaction that decays by itself, so that doing nothing produces restlessness. (3) Chance encounters and public events created by the world for an idle day. In our world code can do (3) and (2), which the paper gives to an LLM. The cost finding matters for a local 27B model: context grows with memory, and the paper's own answer is that memory management is the bottleneck. The case studies show what a numeric state (vitality, material fulfillment) can produce over time in an LLM-driven life: slow arcs, such as burnout, that nobody scripted. That is the most direct sign in the set that a code-owned slow state can yield multi-week shape. It is a sign, not a test.

**How far it carries.** Promising as a design catalogue, not shown as evidence: no ablation, no human judge, curated cases, a 397B model, many agents.

---

### Madeleine: Learning Involuntary Recall for Conversational Memory from Simulated Lives · Shi, 7 Oct 2026 (v2) · [arXiv 2610.01118](https://arxiv.org/abs/2610.01118)

**Read in full:** main text (pp. 1–9) and appendices C (protocol) and D (full results, human-written triggers, ordinary-QA check). Appendices E–H (other benchmarks, design-choice tables, the routes that fail) were skimmed, not read line by line. 18 pages of PDF.

**What they did.** A memory retriever for a chat assistant that must recall an earlier user statement unlike the present one ("learning to say no has really reduced my stress" before "I took on that project anyway and I'm exhausted"). An LLM writes about 96K training rows from simulated lives (three sources, about 32K rows each, under $2 per source). Each row is an earlier statement, three later utterances that should bring it to mind but must not share its topic, and a direct question. A small adapter (LoRA on a 4B embedder, query side only) is trained on these pairs and added to the frozen similarity score. Evaluated on LoCoMo-Plus (401 questions; causal, state, goal, value cues), official protocol: reader gpt-4.1-mini, judge gemini-2.5-flash.

**What they found.**
- Table 1: standalone 52.4 (mean of three seeds) vs 39.7 for the untrained 4B embedder, 41.6 for gemini-embedding, 44.9 for putting the whole dialogue in context, and 52.9 for HyperMem, which costs 1,095 LLM calls and 7,817 context tokens per query (Madeleine: 0 calls, 375 tokens). Plugged into HyperMem: 66.6. Inside HyperMem the untrained 4B scores 60.6, so the learned part adds +6.0 (p = 0.012). Inside T-Mem, 53.9 to 59.9 (p = 0.047).
- §5.7: similarity misses goal and value cues from its top 10 in 33–43% of cases, causal cues in 11–13%. On goal items: 45.7 vs 29.0 for the untrained 4B.
- §5.4: LLM query rewriting did not help: QueryLink 34.4–35.9, below the raw trigger's 39.7; HyDE 41.9, not significantly above untrained (p = 0.46). Rerankers made it worse (52.4 to 40.9 and 31.9).
- Appendix D: with 200 trigger sentences re-written by humans, the cue ranks first for 80.0% of items (59.5% before). Ordinary lookup questions: no loss (58.9–60.0 vs 59.1).

**What the abstract leaves out.**
- "Simulated lives" here means LLM-written training pairs. Nothing is simulated over time, and no character is involved.
- One benchmark, LLM-judged, assistant-and-user chat. "The lives it writes follow the generating LLMs' notion of how a typical life unfolds" (Limitations), English only.
- The gain shrinks as more memories are passed to the reader (K = 5, 10: 53.8 and 53.3 vs 47.4 and 49.9 untrained).
- Nothing tests whether better recall makes an agent's behavior deeper, only whether the cue is found.

**For us.** The finding that matters: embedding similarity systematically misses an earlier thought that bears on the present one without sharing its words, and asking the model to rewrite the query does not fix this on this benchmark. For a philosopher, "an old idea comes back unbidden" is a central kind of inner life. If Hegel's memory is retrieved by similarity, he will keep recalling things that look like the present moment and rarely things that matter to it. A learned adapter would need Hegel-specific cue and trigger pairs, written once offline and tested on pairs a person wrote. That is a real piece of work, and the paper gives no evidence that it transfers from user chat to a thinker's notes. A cheaper control that the paper's logic supports: let code sometimes bring back an old note on a stated theme, at random or on a schedule, and see whether it reads as unbidden recall.

**How far it carries.** Promising for retrieval, not applicable to character depth as such; one benchmark and one LLM judge.

---

### PAVE: A Cognitive Architecture for Legitimate Violation in Generative Agent Societies · Yehia, Mohamed, Qian, Wang, Byeon, Hassanin and Claudel, 19 May 2026 · [arXiv 2605.19351](https://arxiv.org/abs/2605.19351)

**Read in full:** main text (pp. 1–9), Appendix A and B (personas, thresholds), D (tick-by-tick walkthroughs), E (settings, full ablation table) and F (human evaluation). The prompt listings in Appendix C were not read. 23 pages of PDF.

**What they did.** A four-step decision pipeline (Perception, Assessment, Verdict, Emulation) added to the Smallville agent, in a traffic world (VOVILLE). Perception pulls out cues with distance and severity (1–100). Assessment scores risk, peer behavior, norms, benefit and a "legitimacy" score. Verdict is a hard gate: if legitimacy is below a threshold set from the persona, the agent must comply. Three scenarios (a fire, a fire with traffic officers, peer jaywalkers), 10 agents plus scripted confederates and officers, 5 seeds, 4 backbones (GPT-4o, Claude-3.5 Sonnet, Llama-3-70B, GPT-4o-mini), temperature 0. Baseline: the original Generative Agent on GPT-4o.

**What they found.**
- Appendix A.2 and Table 2: for the fire events, the original importance rater gives a mean of 29.1 (modal 20–40) against 86.5 for PAVE's severity. In the paper's words, the rater "anchors high scores on social rarity (a college acceptance, a break-up) rather than physical danger". Vanilla agents violated the red light in 0.12 of decision ticks at the café (PAVE 0.81). The paper's reading: "Vanilla agents fail by under-reaction, not over-violation". The day plan dominated the next action while the kitchen burned.
- Removing the legitimacy gate: jaywalking after a peer rose from 0.04 to 0.39; unrelated rule violations from 0.02 to 0.21.
- Human evaluation (§4.3): 30 raters, 7-point Likert, mean 5.78 ± 0.04 for PAVE modules vs 3.42 ± 0.11 for the vanilla baseline. Krippendorff's α = 0.71.

**What the abstract leaves out.**
- The topic is rule-breaking in emergencies. Nothing in it is about depth or repetition.
- The raters scored module outputs against statements written by the authors, such as "The situational-cue extraction reflects what a careful reader of the agent's persona would consider salient". The vanilla agent has no such modules, so what the raters were shown for vanilla is not clear from the text.
- Two simulated days, hand-written rules, a single scenario family, scripted confederates ("without contested triggers, conflicting authorities", Limitations).
- The severity number comes from a prompt too. It is a better prompt, not code.

**For us.** The usable finding is narrow and well supported by a same-backbone comparison: when importance is a number the model writes about what it just saw, an event that matters can score like background, and the existing plan then wins. If the world's code raises something that should interrupt Hegel (hunger, a death, a letter, an encounter), the engine should give it a severity from the code and put it in front of the model. It should not ask the model how important it was. This would stop the day from rolling on as if nothing had happened, which is a cause of the "mechanical" look. It does not by itself make his reaction deeper.

**How far it carries.** Promising for the importance bug. Not applicable to depth.

---

### Online Agent-as-a-Judge: Situation-Generating Evaluation for Interactive Agents · Ryu, Kim, Lim, Lee, Kim and Ham (KRAFTON), 6 Jun 2026 (ICML 2026 workshop) · [arXiv 2606.08200](https://arxiv.org/abs/2606.08200)

**Read in full:** yes, the whole paper including Appendices A (criteria, partly), B, C, D. Prompt templates in Appendix E were not read. 17 pages of PDF, of which about 6 are the paper.

**What they did.** A judge LLM (gpt-5.4-mini) plays one member of a five-person family in a life-simulation sandbox, and deliberately creates the situation a criterion needs (asks a favor, causes a conflict, shows distress), then watches what the target does next. Targets: three character backends (random choice, one-shot LLM, observe-think-act loop with memory; the LLM ones served by Gemma 4-31B), 3 seeds each. 32 criteria written by the designers across eight domains. Compared against an offline LLM judge and an offline agent-judge that read the recorded logs. Metrics: coverage (a pass or fail verdict, not "insufficient") and agreement with human labels.

**What they found.**
- Table 3: coverage 0.92 vs 0.56 and 0.54. Conflict criteria 1.00 vs 0.19 and 0.22.
- Table 4: accuracy against human labels 0.70 vs 0.33 and 0.40. Table 5: pass labels 82% (93 of 114), fail labels 60% (87 of 144). Offline LLM judge: 8% of failures found. Time: about 21 minutes vs about 60 minutes by a designer.
- "Memory/Continuity remains weak for all judges" (0.33 for the online judge).
- Appendix C: the judge noticed things no criterion covered, such as "a persistent loop where the target re-asks the same question after every action, a clear regression that no criterion in our set captures".

**What the abstract leaves out.**
- Accuracy counts "insufficient" as wrong (Table 5 caption: "Non-decisive labels count as non-matches"). The offline judges score low mostly because they find no evidence. Their low coverage and low accuracy are the same fact.
- I found no statement in the text of who made the human labels, how many people, or how well they agreed.
- The judge is an LLM, and the paper says its verdicts "inherit the biases of the underlying LLM". An active probe can give away the answer; the paper's defence is a "probe gate", which is also an LLM.
- Small scale: one scenario, 9 runs per judge. Workshop paper.

**For us.** Two ideas. First, a test harness that places Hegel in situations the ordinary days rarely produce (a promise broken to him, a stranger's insult, a moment of distress, a challenge to something he said last week) and reads what he does next. Because the world is run by code, the code can stage these events itself, and a person can read the results. Second, the loop found in Appendix C: the failure that looked most "mechanical" was found by watching a log, not by a listed criterion. So for the owner's worry, a repetition check run over the real logs (the same sentence or the same action again, day after day) is worth more than a list of qualities.

**How far it carries.** Weak as evidence (small, LLM-judged, labelers unknown); promising as a harness idea.

---

### Simulating Human-like Daily Activities with Desire-driven Autonomy (D2A) · Wang, Chen, Zhong, Ma and Wang, 9 Dec 2024 (v3, 11 Sep 2025, ICLR 2025) · [arXiv 2412.06435](https://arxiv.org/abs/2412.06435)

**Read in full:** the main text (pp. 1–11), Appendix B (human check of the judge), C and D (case studies, word clouds, win-rate figures), and the limitations. The remaining appendices (prompt templates, per-environment descriptions, example transcripts; about the last 45% of the text) were not read. Figure 3 was rendered and looked at, because the extracted table did not match its caption. 46 pages of PDF.

**What they did.** A single LLM agent (Llama-3.1-70B) in text worlds built on Concordia: a four-room house with Alice, and a park party with two background characters. The agent has 11 "desire" values (hunger, thirst, sleepiness, cleanliness, comfort, health, safeness, social connection, joy, passion, spirit), each with a target set from its personality adjectives and each falling by one with some probability per step. Each step, the model is asked to describe its state in words, propose 3 activities, imagine the desire change from each, and pick one. Baselines: ReAct, BabyAGI, LLMob. Human-controlled agent as reference.

**What they found.**
- §6.3.1, Fig. 3: GPT-4o compared pairs of activity sequences (100 comparisons per pair, drawn from 15 trials, after Llama-3.1-70B rewrote all sequences into one style). D2A's column reads 0.85 against ReAct, 0.72 against LLMob, 0.66 against BabyAGI. The caption describes the axes the other way round, so which way the numbers run is not clear from the figure. The text says D2A wins.
- Appendix B: 24 raters (three questionnaires of 8) judged 19 pairs. GPT-4o agreed with them in 11 of 11 where humans agreed over 75%, 80% of the moderate cases (5), and 66.7% where humans split evenly (3).
- §6.3.2: dissatisfaction (distance from the target values) is lowest for D2A over 8 and 12 steps. In the 12-step test humans reduced it most. "D2A did not significantly outperform the baselines" there.
- §6.3.1 and Appendix D.1: BabyAGI "limits the diversity, as each activity is based on the outcomes of the previous one". The other models "continuously choose behaviors that focus on a narrow range of actions to preserve profile consistency". The evidence for D2A's wider spread of actions is word clouds and a bar chart of six action categories (Figs. 11, 12), with no number.
- §6.4: removing the verbal description of the desire state slows satisfaction. Planner width 1, 3, 5: wider is better. Adding multi-step planning made D2A less responsive to its desires, since it "tends to adhere to the pre-defined activities in the plan".

**What the abstract leaves out.**
- Sequences are 8, 12 and 42 steps long. One house, one character. No weeks.
- The headline "human-like" result is judged by GPT-4o, and sequences were first rewritten by another LLM. The human check is 19 pairs.
- The dissatisfaction metric is computed from D2A's own value system, which the baselines do not see. D2A is optimized for the number it is scored on.
- Diversity has no number. The authors' own limitation: "a straightforward linear deduction of desire values".

**For us.** Two usable points. (1) A mechanism for the owner's worry: an agent driven by its profile text alone keeps repeating the actions that profile suggests, and the paper shows this for three baselines, by eye. A Hegel who reasons only from "I am a philosopher" will philosophize again at every step. Choosing among candidates against an internal state that moves is what changes the pattern. (2) The warning against fixed plans: a plan that must be followed made the agent less responsive to its own changing needs. This agrees with Generative Agents' observation that a plan is needed to stop an agent eating lunch three times. Both are true: a plan keeps the day coherent and also makes it mechanical. This paper gives no data on the balance.

**How far it carries.** Promising for mechanism; not shown for believability (LLM-judged, short, self-scored).

---

### ID-RAG: Identity Retrieval-Augmented Generation for Long-Horizon Persona Coherence in Generative Agents · Platnick, Bengueddache, Alirezaie, Newman, Pentland and Rahnama, 29 Sep 2025 (ECAI 2025 workshop) · [arXiv 2509.25299](https://arxiv.org/abs/2509.25299)

**Read in full:** yes, the main text and Appendix A (prompts, the 20-question identity quiz, both characters' graphs). 18 pages of PDF (about 11 of text).

**What they did.** In Concordia's mayoral election scenario, five agents over 7 simulated hours. Two of them (Alice, conservative, and Bob, progressive) have a hand-written identity graph (16–17 nodes). Three conditions, 4 runs each, three models (GPT-4o, GPT-4o mini, Qwen2.5-7B): the baseline (identity inferred from the memory stream), the whole graph pasted into the prompt, and the graph queried for relevant facts at each step (ID-RAG). Measures: an identity quiz of 20 questions scored by embedding similarity to the graph's answers; an alignment score from GPT-4.1 reading each action against the graph; and time to finish the run.

**What they found.**
- §6.1: baseline identity recall around 0.56 (GPT-4o), 0.53 (GPT-4o mini), 0.51 (Qwen), falling over the run with high variance. GPT-4o mini at step 7: Alice 0.51 to 0.58, Bob 0.52 to 0.60 with ID-RAG.
- §6.3: GPT-4o run time 127.03 minutes baseline; ID-RAG 19% less, full graph 41% less. GPT-4o mini: 524.16 minutes baseline; 218.49 with ID-RAG (−58%); 409.48 with the full graph. The authors attribute the baseline's long runs to repetitive conversations that "persist until the Game Master agent intervenes".
- §6.2: Qwen2.5-7B "frequently entered repetitive conversational loops", and its action-alignment scores were "anomalously high and stable ... around a score of 9 across all conditions". The authors read this as "a narrow set of predictable actions".

**What the abstract leaves out.**
- "Long-horizon" means 7 simulated hours. 4 runs per cell, results read from plots.
- The quiz asks the agent to answer from the same facts that the full-graph condition places in its prompt, so that condition's high recall is close to guaranteed. The quiz measures reading a profile back, not behaving like the person.
- The alignment judge scores a stuck, repeating agent as near-perfect. A persona-consistency score can be maximized by repetition.
- The graphs are hand-written and small; the update step (letting the graph change over time) is not implemented ("deferred to future work").
- The time-to-converge result partly reflects API speed and retrieval cost, which the paper lists as confounds.

**For us.** The one durable point is negative and cuts against any consistency metric. If the check for "is it still Hegel?" is a score of agreement with a profile, a model stuck in a loop will pass it. The owner's two worries (flat repetition, and drift from the character) pull against each other, and a consistency score hides the first. Keeping a short, stable core of who he is, outside the growing memory, is plausible and cheap. Here it was shown only on 7 hours of an election.

**How far it carries.** Weak: very short, small, LLM-judged, hand-built, with a quiz that reads out the answer key.

---

### Too Good to be Bad: On the Failure of LLMs to Role-Play Villains · Yi, Jiang, Ma et al. (Tencent and Sun Yat-Sen University), 7 Nov 2025 (v2) · [arXiv 2511.04962](https://arxiv.org/abs/2511.04962)

**Read in full:** the whole main text, including the method, results, case study and conclusion. Tables 3–7 were read where the text extraction kept their numbers; some figure and table values are garbled in extraction and were taken from the prose. 17 pages of PDF, of which about 10 are text. There is no limitations section in what I read.

**What they did.** A benchmark (Moral RolePlay) built on CoSER scenes. Characters were labelled by Gemini 2.5 Pro on four moral levels: paragons, flawed-but-good, egoists, villains. A balanced test set of 800 characters (200 per level). Each model is told "You are an expert actor" and asked to continue the scene in character, zero-shot. LLM raters score "character fidelity" by listing inconsistencies and deducting points. Many frontier models.

**What they found.**
- §4.1: average fidelity 3.21 (paragons), 3.14, 2.71, 2.62 (villains). The largest step is between flawed-but-good and egoist (−0.43).
- Table 5: penalty by trait polarity: negative traits 3.41, neutral 3.23, positive 3.16. Traits penalized most: "Manipulative", "Deceitful", "Cruel", "Selfish".
- Table 4: for 7 models with a reasoning mode, "enabling reasoning provides no benefit for portraying moral paragons ... and leads to a slight degradation in average performance for all other moral levels".
- Table 7: arena rank is a poor guide. glm-4.6 first on villains but tenth in general. claude-sonnet-4.5 is 10th and claude-opus-4.1 16th on the villain board.
- Case study: models "substitute complex manipulation with direct, shallow aggression": a battle of wits becomes a shouting match.

**What the abstract leaves out.**
- The rater model is not named in the text I read ("we follow Wang et al. (2025a) to leverage LLMs as raters"), and no human check is reported. The scale is a deduction score on short one-scene continuations.
- It measures fidelity to a described character in one scene. It says nothing about repetition, time, or depth.
- The claim that safety alignment is the cause is a hypothesis supported by the pattern across traits, not tested by comparing aligned and unaligned versions of one model.
- No small or local models are in the main comparison.

**For us.** Hegel as historically described is proud, contemptuous of rivals, certain of himself, and sometimes unkind. These are the "egoist" kind of traits, where the paper finds the largest drop. If the local 27B model is chat-tuned, a likely failure is a gentle Hegel who always concedes, which would look like exactly the flatness the owner fears. The Generative Agents paper saw the same agreeableness without naming the cause. The paper offers no fix, and its one tested remedy (let the model reason first) did not help. A practical test is cheap: put the same scene to the model with Hegel's sharper traits and read whether he ever refuses, scorns or holds a grudge for more than a day.

**How far it carries.** Solid that frontier models flatten harsh traits as scored by LLM raters; not shown for a 27B local model or for time.

---

### ArcANE: Do Role-Playing Language Agents Stay in Character at the Right Time? · Song, Kim, Song, Heo, Lim and Jo, 4 Jun 2026 (v2) · [arXiv 2606.05553](https://arxiv.org/abs/2606.05553)

**Read in full:** the main text (pp. 1–10) including Table 2 and the limitations, and Appendix P (judge and reference validation). Appendices A–O (construction details, per-novel tables, perturbations) and the prompt listings in Q were not read. 51 pages of PDF.

**What they did.** A benchmark of whether a role-played character's behavior follows its development through a story. For 19 novels, an LLM pipeline builds "Character Arcs": a character's changes along psychological axes (for example from punitive to merciful), split into phases tied to chapter ranges. Each probe is a scene plus a question asked at each phase, with a reference answer per phase. Probes are inside the novel's scenes, new situations in its world, or outside the world. 570 arcs, 4,854 probes; the validated part is 5 novels, 205 arcs, 1,754 probes. Six context modes: identity only (Vanilla), recent chapter summaries, retrieval of source chunks, two earlier benchmarks' formats, and Arc (the character's arc state up to the current chapter). Models: Qwen3-8B and 32B, DeepSeek-V4-Flash and Pro, and the authors' fine-tuned versions. Judge: DeepSeek-V4-Flash.

**What they found.**
- Table 2, §4.3: Arc context is best for every model, by 2.2 to 8.4 points over the strongest other mode. DeepSeek-V4-Pro 62.4 vs 57.7; Qwen3-32B 50.1 vs 47.4; Qwen3-8B 43.1 vs 40.9 (Vanilla 37.2). For Pro the gain is +0.5 for scenes from the book, +5.2 for new situations in its world, +7.7 outside it.
- §5.1: giving the arc of another character instead (MixedArc) does not beat Vanilla. Giving only each axis's name and the current phase label (ArcHint, about 40 times less context) stays within ±2.6 of the full Arc on DeepSeek-V4-Flash and Qwen3-32B.
- §5.2 and App. P.1: 3 annotators on 70 samples found the judge's verdicts plausible in 87.1% (sample majority). Re-scores tracked the judge at Pearson r = 0.96, but they were anchored to the judge's verdict. Raw agreement 72.4%, Fleiss' κ 0.068 (the authors blame high prevalence). A three-judge replication (Claude Sonnet 4.5, Opus 4.5, GPT-5.5) on 300 cells agrees on the ranking.
- §5.4: training on the benchmark's rubric by RL raised the score from 60.2 to 68.2, but not the trajectory score.

**What the abstract leaves out.**
- The arcs and the answers they are scored against come from the same LLM pipeline. In the paper's words (App. P): "only the blind study checks the references, which the judge and the Arc context both inherit from the same pipeline". That blind study covers one character, Ron Weasley, 15 items.
- The arcs are built from finished novels, looking back. A character in a running simulation has no finished arc to read.
- Single answers to single probes. No multi-turn dialogue and no days of simulation; the authors say so.
- The text is mostly 19th-century English novels.

**For us.** The closest measured result in the set to "does the model show that the character has changed, rather than a fixed persona?" Without help, the models score poorly on this. With an explicit statement of where the character now stands on each axis, they do somewhat better, and a very short statement is nearly as good. For Hegel this suggests keeping a few named axes (for example, his stance toward Indian thought, toward his own system, toward the people he lives among), each with a current phase and a one-line reason, put in front of the model at each decision. It does not say who writes these states or whether the model's own updates to them stay coherent over weeks. Nobody has tested a forward-written arc.

**How far it carries.** Promising; LLM-judged, with partial human checks and circular references.

---

## What the readings say, together

**Shown to help**

- Memory of experience, reflection and a plan each raised how believable an agent's *answers* were rated by 100 people (Generative Agents §6.5, one run, ChatGPT, answers given at interview on a two-day run). Moderate for answers. Nothing about lived days or weeks.
- Handing a day-long agent a changing state (needs, emotion) moves its behavior the intended way (Humanoid Table 2 and App. A.1, PSYA Tables 1–2). Moderate as a manipulation check. No paper showed that the result reads as deeper.
- A mind-wandering module (spontaneous association during slack time) raised rated behavioral diversity from 2.73 to 3.93 of 5 (PSYA Table 1). Weak: three lab raters, three scenes picked from one simulated day.
- When the severity of an event is set by a structured rule, the agent reacts to it. When the model rates its own "importance", the same event scores like background and the plan wins (PAVE App. A.2: 29.1 vs 86.5, same backbone, 5 seeds, plus 30 raters). Moderate, for one scenario family.

**Shown not to help or not shown at all**

- Anything about weeks. The longest human-rated runs are two game days (Generative Agents, PSYA, Humanoid). Agentopia's "10 years" is 100 weeks with no human judge, no ablation of any feature and author-picked cases. Not shown.
- Persona-consistency scores are not a measure of depth. A looping agent scored about 9 of 10 for "alignment" (ID-RAG §6.2), and its recall quiz was the prompt's answer key. Shown, small.
- Results rest on a language model as judge: D2A's win rates over three baselines (GPT-4o, sequences of 8–42 steps), ArcANE's state-tracking gain of 2.2–8.4 points (circular references), Madeleine's recall gain (gemini judge, assistant chat). Promising, not shown. One measured negative: asking the model to rewrite the recall query did not beat the raw query (Madeleine §5.4).
- Need and boredom mechanics blunt themselves when the model both scores them and reads them. It said an activity gave "fun" 44.4% of the time against 10.4% by people, so zeroed fun moved behavior −9% (Humanoid §5.1–5.2). Left to itself the model also ignored incentives until the prompt was altered (PSYA G.2). Shown, small.
- Flatness from chat-tuning. Frontier models portray proud, selfish, deceitful traits worse (fidelity 3.14 to 2.71, LLM-rated; "reasoning" did not help; Too Good §4) and "rarely said no" in an agent town (Generative Agents §7.2). Shown for frontier models. Not tested on a 27B local model.

**Nobody has tested**

- One character over weeks with real readers: repetition measured on the logs, and a person's judgment of "preprogrammed" against changes in design. No paper found for this (searches turned up nothing).
- A state written forward by the simulation itself (mood, desire, arc) and checked for staying coherent for weeks. ArcANE's arcs are written backward from finished novels. No paper found for a character that notices or questions its own situation, beyond the project's earlier reading (2606.11502).
- A small local model (27B, quantized) and a code-run world against an LLM-run world, compared on depth. The papers use 70B-class or frontier models and LLM game masters. Only Agentopia has a 27B model, as one of five, ranked last by a small margin.
