# Research handover: long-running character simulation

For a deep-research model, at Welt's request. Written by Claude on 28 October 2026.

Your task: become an expert in the kind of simulation Hegel in Delhi is building. Then tell us, with evidence, what will make it better. This is research, not coding: you change nothing in the repository. You deliver one report (the end of this file says what goes in it).

## 1. What the project is

G. W. F. Hegel, fifty, wakes in present-day Delhi in a bungalow the Directorate of Estates allotted to him by mistake. A local language model lives his days, minute by minute, on a map of two square kilometres of Delhi. The days are unscripted and published as they happen.

- **Live page:** https://weltogeisto.github.io/hegel-in-delhi/
- **Repository (public):** https://github.com/weltogeisto/hegel-in-delhi
- **The aim, in one line (`PLAN.md`):** Hegel lives every day in public, for months, and gets better at being himself. The project calls it a theatre run: rehearsal in a shadow world, opening night, then a run in which the role deepens.

**Who does what.**
- **Welt** owns the project and decides: training, the public switch, money, his PC.
- **Claude** writes specifications and scoring, merges to `main`, and reviews.
- **Astra** (a Codex session on Welt's PC) runs the GPU work.
- **Hermes** follows a runbook on the Raspberry Pi.

## 2. How it runs

- **The world (Raspberry Pi 5, Python).** The engine owns the clock, places, opening hours, prices, walking routes, money (cash, an imprest account, recurring costs, offers that pay), the weather, air and news feeds, and a cast of fictional Delhiites with daily rounds. About every half hour of his day it builds a situation and asks the mind to decide. It checks each decision against hard rules (closed is closed, walking takes time, cash cannot go below zero) and asks again when a rule is broken. Then it publishes the step. Code: `world/engine.py`, `world/world.py`, `world/data/`.
- **The mind (one PC, RTX 3090 with 24 GB).** Qwen3.8-27B at Q4 runs on llama.cpp: three slots of 16K context, about 35 tokens a second, answering in a fixed JSON schema. When he speaks to someone, that person answers through one more call, voiced from their card. When he writes, one more call writes the sitting. The persona prompt is in `mind/soul.md` and its variants.
- **The shelf.** His own public-domain works, 17 texts. A BM25 search offers one or two short passages that touch the moment, "to think with". His biographies and letters are kept for training only, never shown to him.
- **Memory.** The day file is the state: what he carries in from yesterday and out into tomorrow. He remembers his last moments with the people in front of him, his last thought in each place, and the owl's gist of the last three nights. Each morning he makes a plan that stays on his mind.
- **The owl.** Each morning, before he wakes, a call writes up yesterday: the diary, a revision log of his **theses** (convictions about the state, India, religion and so on, each "unshaken" or "shaken"), and on Saturdays the Depesche. Code: `world/owl.py`, `mind/owl.md`.
- **The daily report.** One row per day: thoughts, quiet steps, refusals, repetition, meals, cash, places, people and theses (`world/report.py`).
- **Constraints that shape every answer.**
  - Everything runs locally; the only running cost is electricity.
  - One 24 GB GPU, on 12 hours a day; his day runs from 9 to 21 Berlin time to fit.
  - No cloud model in the loop.
  - The living people are invented; the dead are on his shelf; the news is real.
  - The world does not steer him. His nineteenth-century views stay his own, and sensitive entries are veiled on the page, never refused.

## 3. How the project learns

Three loops, at three speeds (`PLAN.md`, Act 3):

1. **Daily:** memory, storylines and convictions carry from day to day.
2. **Weekly, the ratchet:** one experiment at a time. Claude writes the change, Astra runs it on frozen inputs (replayed days, fixed seeds), and the change is scored blind. `main` takes it only if no number gets worse.
3. **Training:** LoRA adapters on Qwen, trained on his books, his lives and letters, and the model's own best decisions. Welt alone decides on any training run.

Gates with numbers open each act. **Act 1** asks for seven days in a row with:
- at least 20 thoughts;
- quiet steps at most 5% of waking steps;
- the owl writing every morning;
- no refusal loop (four or more of the same refusal);
- a truth audit at most 1.6 contradictions and 3.1 statements-as-fact per 100 sentences.

## 4. What is hard right now: the problems your research should solve

1. **Repetition.** On Day 12, 69% of his thoughts reused a phrase of his own from earlier that day, against 48% in rehearsals. On Day 27, a strong day (39 thoughts, eight people met), the mind wrote the same thought three times in a row and the day failed its gate. Two remedies are built and waiting for a blind test:
   - an **echo guard** that shows him the phrases he has already used today;
   - llama.cpp's **DRY sampler** on decisions.
2. **Convictions move too easily.** The `state` thesis changes status on about half of all nights (T8). A conviction should change only for reasons the record shows.
3. **Commitments are weak.** In blind review, the positions he takes score 2.0–2.8 out of 5; real Hegel passages score 4.65. Writing his convictions into the persona raised one measure from 2.00 to 2.83, the strongest lever so far.
4. **Voice.** The first adapter (supervised fine-tuning on his books plus the model's best decisions) did not beat plain Qwen. The **Hegelizer** restyles plain English in his translators' manner: it learns the reverse of a paraphrase (Qwen's plain version as input, his real passage as target). Its pilot moved in the right direction without passing. Round two (`pc/HEGELIZER-2.md`) sets five bars:
   - blind pairwise preference, 28 of 40;
   - Burrows' Delta at most 0.38 (real passages score 0.33, plain versions 0.48);
   - meaning kept in 36 of 40, judged by plain Qwen, never by Claude;
   - no 12-word copies from the shelf;
   - fit for the live JSON contract.
5. **Truth and grounding.** Characters invent things the record doesn't support: a tailor's order "ready" before it is, a visit that never happened. This happens even with the facts in their prompt. Structured records helped the Depesche, where statements-as-fact fell from 14 to 4 per 100 sentences (T3).
6. **Reliability and scale.** Days were lost to Windows restarts. A small model and a 16K context per call limit what memory can carry.

The numbers come from `pc/TASKS.md` (task log, T1–T38) and `mind/results/`. The day files on the `shadow` branch (`docs/days/`) hold every step, thought, refusal and owl report: read some. Day 12 and Day 27 are the best ones.

## 5. Research questions

For each question, give: the current best practice and its evidence (dated, replicated or not); what it means for **this** setup (a 27B model at Q4 on one 24 GB GPU, local, months long, one character); and the cheapest experiment that would test it on our frozen days.

- **A. Memory for a long-lived single agent.** Generative Agents (Park et al. 2023: observation, reflection, planning), MemGPT/Letta, episodic versus semantic memory, summaries versus retrieval, outcome memory.
  - What carries a character's identity and relationships over months on a small model with 16K of context?
  - How should "the owl's gist" and the day file be structured?
- **B. Persona fidelity and persona drift.**
  - Role-play and character research: Character-LLM, RoleLLM, CharacterEval and successors; work that measures and controls persona drift over long interactions; simulations of historical figures.
  - How do you make a model hold a thinker's **commitments**, not just his style? Compare the persona prompt, fine-tuning, retrieval from his own works, steering or activation vectors, and preference tuning.
- **C. Voice: style transfer and authorship.**
  - Inverse paraphrase (STRAP, Krishna et al. 2020), stylometric targets (Burrows' Delta and better), and LoRA practice (rank, learning rate, which layers, data size; e.g. Thinking Machines' "LoRA without regret").
  - Memorisation control (goldfish loss), preference tuning for style (DPO, ORPO, KTO) from few pairwise judgements, and on-policy or self-distillation.
  - How should voice be measured beyond Delta?
- **D. Belief dynamics.**
  - How should a simulated mind hold convictions that are stable yet revisable? Belief revision, hysteresis rules ("two nights agreeing"), argument-based updating, and how other agent simulations model opinion change.
  - How do you evaluate that a change of mind was earned by the record?
- **E. Repetition and degeneration in long-running agents.**
  - DRY, repetition and presence penalties, contrastive decoding, novelty-seeking prompts, showing the model its own recent output, diversity at the planning level rather than the token level.
  - What works on small models without hurting coherence or the JSON contract?
  - How should repetition be measured across hours and days?
- **F. Grounding and truthfulness in simulations.**
  - Structured state versus free text, typed records, validating actions against a world model, and stopping characters from inventing events.
  - The best known patterns for keeping many speakers consistent with one record.
- **G. Evaluation with few judges.**
  - Blind pairwise comparison with two raters (Welt and Claude), Bradley–Terry and sequential testing on small samples, and frozen-input replay with fixed seeds.
  - The pitfalls of model-as-judge, and how to keep a ratchet honest when each experiment yields 20 to 40 data points.
- **H. Hardware-bound engineering.**
  - The best recipe for a persona agent on one 24 GB GPU: which dense or MoE models at what quantisation, KV-cache budgets, per-request LoRA scaling in llama.cpp, grammar or schema-constrained decoding and its effect on quality, speculative decoding.
  - Should a larger model run at night for the owl?
- **I. Prior art and audience.**
  - Public, long-running AI-character worlds and streams (AI Town, Smallville and their successors, persistent AI characters on stream): what kept them alive and watched, and what made them fail.
  - The ethics of publicly simulating a real historical person with views of his time: what practice exists?

## 6. Boundaries for your recommendations

- **Inference stays local** on one RTX 3090. No cloud model in the loop.
- **Training data** is never written by Claude, and no Claude judgement selects what goes into training. Treat the same rule as applying to you. Data comes from his own texts, from the local model's own outputs chosen by machine metrics, or from Welt's own judgement.
- **Training runs, the public world and any spending** are Welt's decisions. Recommend; don't assume.
- **Sources:** public-domain texts only on his shelf. The living cast stays fictional.
- **No steering:** the world must make things possible (income, friendship, a change of mind) without forcing them.

## 7. What to deliver

One report, in English, with links and dates for every source. Mark clearly what is established, what is promising, and what is your judgement.

1. **A field map.** The 15 to 25 works that matter most here: what each found, whether it held up, and how it applies to us.
2. **Answers to A–I** in the shape asked for in section 5.
3. **The next five ratchet experiments, ranked.** Each specified so that Claude can write it and Astra can run it:
   - the change;
   - the frozen inputs;
   - the metric and the bar to pass;
   - the GPU hours;
   - the expected effect, with your confidence.
4. **What not to do:** approaches that look good but fail on small models or long horizons, with evidence.
5. **Open questions** you could not settle, and what would settle them.

Where you are unsure, say so. A short, sourced answer is worth more than a long, confident one.

## 8. Where to read

| What | Where |
|---|---|
| How it runs | `README.md` |
| The season plan and the gates | `PLAN.md` |
| Every task, decision and number so far | `pc/TASKS.md` |
| The voice adapter, round two (KPIs, levers, sources) | `pc/HEGELIZER-2.md` |
| The persona prompts | `mind/soul.md`, `mind/soul-v2.md`, `mind/soul-bildung.md` |
| The owl's prompt | `mind/owl.md` |
| Experiment results | `mind/results/` |
| The engine, memory, owl, report | `world/engine.py`, `world/memory.py`, `world/owl.py`, `world/report.py` |
| His real days, step by step | branch `shadow`, `docs/days/` |

**Glossary.**
- **Step:** one decision of his, about every half hour of his day.
- **Quiet step:** a waking step without a thought.
- **Refusal loop:** the world refusing the same decision four times.
- **Theses:** his convictions, each unshaken or shaken.
- **The owl:** the nightly write-up.
- **Depesche:** the weekly dispatch.
- **Shadow:** the rehearsal world.
- **The ratchet:** take a change only if no number gets worse.
- **Hegelizer:** the restyling adapter.
