# Training, round three: from the research to the adapters

Written by Claude on 2 November 2026, at Welt's request: turn what the research taught us into training that works. It draws on GPT 6 Pro's report (`research/REPORT-GPT6PRO-2026-10-28.pdf`), the literature gaps (`research/LITERATURE-GAPS.md`) and the research note on his own account of mind. Every training run waits for Welt's go, as always.

## What the research says about training

**Most of the next gains come without training.** The report ranks structure first: typed facts for the people he meets (T40), memory of outcomes (T41), an evidence gate for his convictions (T42), one sourced paragraph of his commitments (T43). Its "what not to do" warns against training as a cheap fix (items 5–7), and our own record agrees: the first adapter did not beat plain Qwen. So the rule for this round:

1. **Train only what a cheap fix leaves.** Each training has an inference-time screen before it, and the adapter must beat the best arm of that screen, not just plain Qwen.
2. **Build the test before the data.** The held-out cases are frozen and sealed before any training data is generated. Scene families in the test never appear in the training data.
3. **Use the signal the world already computes.** The world already knows, by its own rules, when he breaks a rule, repeats himself, names what he cannot know, or when a voice claims what never happened. Those checks can label training pairs, without anyone's taste.
4. **One adapter per job.** His voice (the Hegelizer), the people he meets, and his decisions each get their own LoRA. llama.cpp sets each one's scale per request, so a voice adapter never touches his decisions.

**The data rule stays.** Training data comes from his own texts, from the local model's own outputs chosen by the world's deterministic checks, or from Welt's judgement. Never text written by Claude or any other frontier model, and never a model's taste choosing what goes in. The checks are code that applies the world's rules, as `tools/train_data.py` already does when it picks Qwen's best decisions.

## Training 1 · The Hegelizer, round two (his voice) · ready

The plan stands (`pc/HEGELIZER-2.md`, T34 and T35; code T31 and T32 done). The report adds six things, folded in here:

1. **Splits by chapter.** Training and held-out units come from different chapters, and a short unit stays with its parent passage, so that neighbours cannot leak (report p. 9).
2. **Is goldfish doing the work?** If KPI 4 (nothing copied) fails, the next window trains the same data without the goldfish loss. Without that matched pair we cannot say whether goldfish helped (report p. 9).
3. **A voice dashboard, not one number.** Beside the five KPIs, report: propositions added and omitted; names, numbers and negations kept; overlap before and after the copy guard; how often the guard fell back to the plain text; Delta matched for length (report p. 9).
4. **The legacy gate, unchanged.** KPI 1 keeps its 39+1 cohort, for comparison with the pilot.
5. **Then a fresh confirmation (T45).** After tuning, a sealed set of 40 thoughts drawn across days, scenes and people, never seen during development. Only a pass there goes towards the shadow week.
6. **Restyle touches the thought string only.** Never an action field (already so).

**GPU:** phase A about 25 hours in the spare slot with two workers. If he is still paused, it takes roughly a third of that with the card to itself and four workers. Phase B (train) about 7 hours with the card to itself, phase C (test) about 2.

## Training 2 · The people he meets, grounded · after T40 and G8

**The failure (report p. 11, Day 27):** voices turn an offer around, call an order ready before it is, and speak of papers signed that never were. The owl then writes them up as fact.

**The screen first.** T40 gives the voices their facts in typed form; G8 has them declare the states they assert (`claims`), which the world checks. Training 2 runs only if those leave a gap.

**The data, labelled by the world.**
- **Moments:** about 500 moments with a speaker, from the shadow archive, each with its typed facts. Scene families in T40's 40 test contexts are excluded.
- **Candidates:** plain Qwen answers each moment four times (seeds 1831, 2718, 3141, 4271).
- **Labels:** the world's claim check labels each answer: clean; a closed state asserted against the record; an offer turned around; evasive (empty, or blanket uncertainty where the facts give the answer).
- **Pairs:** chosen, clean and responsive; rejected, a false state or a reversal. The evasive answers are rejected too, so the adapter cannot win by saying nothing.

**The training.** Preference training (DPO, or ORPO if memory is tight), a LoRA of rank 16 for the voices' calls only; his own calls run it at scale 0. TRL's DPO trainer most likely came with Unsloth; Astra checks. A new package would be Welt's call.

**The test.**
- **Cases:** T40's locked 40 contexts, three seeds.
- **The bar:** the adapter against the best arm of T40 and G8, on T40's bars: scene success up 0.20, unsupported closed-state claims halved, no new reversals in clean controls, voice and argument within −0.25, no rise in evasive answers.

**GPU:** sampling about 2–3 hours, training 3–5, test 1.

## Training 3 · His decisions, without the world's refusals · after T39 and G7

**The failure:** the same thought written three times (Day 27), refusal loops, sambar on 18 of 42 thoughts (Day 12).

**The screen first.** T39 tests the echo guard and DRY. G7 shows whether the failures grow through the day (context) or not (each call). Training 3 runs only for what T39's better arm leaves.

**The data, labelled by the world.** This turns `tools/train_data.py`'s "Qwen's best decisions" from supervised copies into preference pairs.
- **Situations:** frozen situations from shadow days other than T39's test days (12, 27 and T9's two rehearsals).
- **Candidates:** four decisions per situation from plain Qwen.
- **Chosen:** accepted by the world, with a thought that repeats no phrase of the day's earlier thoughts (T9's rule) and names nothing after 1831 he has not met (`world.unmet`).
- **Rejected:** refused by the world, or repeating.
- **Length matched:** each pair's two thoughts are within 20% in length, so the adapter cannot learn that shorter, or silent, is better (report p. 10).

**The training:** as Training 2, its own adapter for his decision calls.

**The test.** T39's frozen days and measures, against T39's better arm:
- the echo share falls by a third;
- the truth audit no worse;
- argument and voice within −0.25.

**GPU:** sampling about 3–4 hours, training 4–6, test as T39 (5–9).

## Not trained this round, and why

- **His commitments.** T43's paragraph first. Preference training on commitments would need Welt's judgements in the hundreds; the report finds no evidence that 20–40 suffice.
- **His convictions changing.** A gate (T42), not a weight.
- **His memory.** Structure and search (T41, G2), not a weight.
- **Online reinforcement learning (GRPO), steering, layer restoration, first-person memories from his lives, data written by Claude or GPT:** out, per the report (items 6–7) and the project's rules.

## Order and windows

1. **Now:** Training 1, phase A. If he stays paused a few more days, the card is free all day, and phase A finishes in about a day.
2. **In the day windows:** the screens T39, T40 with G8, and G7. They are inference only.
3. **One night, the Power Guard set later:** Training 1, phases B and C.
4. **Then, only if their screens leave a gap:** Training 2, then Training 3, each in its own night.

## Who does what

- **Claude:** the checks that label the data, the frozen tests, the manifests and the blind scoring; reviews and merges the code.
- **Astra:** builds the samplers and the preference trainer, and runs every GPU step.
- **Welt:** the go for each training, the windows and the Power Guard nights, any new package, and his share of the blind judging.
