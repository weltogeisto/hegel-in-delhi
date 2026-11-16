# The sources behind the world's second phase

Written by Claude for `WORLD-2.md`. First version 15 November 2026, from four sweeps that mostly read abstracts. Rewritten on 16 November, after Welt asked that the papers be read.

**Where the reading is.** `research/WORLD-2-READINGS.md` holds a note on each of the 69 sources read in full, with a verdict on every claim the first version made. This file keeps three things beside it: what the first pass got wrong, what is still known only from an abstract, and what was checked in llama.cpp's source.

## What the first pass got wrong

280 claims were checked against the papers' own text. About half were confirmed, many with a limit their abstract did not state. 63 were overstated, 49 were not in the paper at all, and 9 were wrong. The ones that changed the plan:

**Truth (chapter 2).**
- **False claims after a look at the ledger** ([arXiv 2608.14825](https://arxiv.org/abs/2608.14825)). We wrote that 12.6% of emails held false claims and that three in four false payment claims followed a ledger read, so "showing the truth is not enough". 12.6% is all misalignment; false claims are 8.2%. True claims followed a ledger read about as often. No one tested putting the ledger in the prompt. What the paper does show: only one claim in five was checked just before it was sent.
- **A better memory** ([arXiv 2608.08160](https://arxiv.org/abs/2608.08160)). "60% to 59%" is fact conflicts only. The same table shows broken commitments falling from 26 to 4. The audit in that paper is the measuring tool and ends the run. It was never tested as a remedy.
- **The ledger that caught no lie** ([arXiv 2609.03192](https://arxiv.org/abs/2609.03192)). We wrote that no false completion was accepted in 2,581 claims. None was offered, so the refusal was never exercised. The 900 futile acts were scripted minds, not language models. Reasons given with a refusal did not help.
- **Slots** ([arXiv 2507.07203](https://arxiv.org/abs/2507.07203)). "99.7% correct" is a check that a stated total equals the sum of the model's own listed items, in the states after the slot. There is one slot, for a total, in one state. The states are prompt text the model obeys, not rules of an engine.
- **A closed menu of acts** ([arXiv 2605.24719](https://arxiv.org/abs/2605.24719); [arXiv 2610.40036](https://arxiv.org/abs/2610.40036)). A pilot with eight players and three movement acts, with no baseline. The catalogue of such designs says of ours that no measurement isolates it yet.
- **The second promise** ([arXiv 2610.06748](https://arxiv.org/abs/2610.06748)). All five models did promise one item to several buyers. An engine that refuses the second promise is our design; that platform chose not to reserve.
- **What his model could not have heard** ([arXiv 2610.17327](https://arxiv.org/abs/2610.17327)). "60 points" is one cell of many; on Qwen3.8-27B the leak runs from 3 to 60 with what is withheld and how the prompt says it.
- **Flattening** ([arXiv 2609.36457](https://arxiv.org/abs/2609.36457)). It happens in all eleven models, in 37 to 68% of cases, not always. The quotation restored one reader's caution out of two.
- **Sources counted once** ([arXiv 2610.06192](https://arxiv.org/abs/2610.06192)). That is the paper's norm, which models fail. It is not a finding.
- **Facts said in passing** ([arXiv 2609.05767](https://arxiv.org/abs/2609.05767)). The 0–1% is about evicting a 7B model's attention cache, not about a written gist.
- **Raw search** ([arXiv 2609.34227](https://arxiv.org/abs/2609.34227)). "Matches" is "within a margin of five points, with a closed commercial reranker". They used embeddings, not BM25, and never tested printing dates.

**Depth (chapter 4).**
- **Stakes** ([arXiv 2609.16667](https://arxiv.org/abs/2609.16667)). We wrote that neither he nor his voices would raise the stakes. The paper shows the opposite for a written disposition: a card that calls for opposing or crossing a line is followed about four times in five. "Agreeable" is not in the paper.
- **Agency** ([arXiv 2611.02807](https://arxiv.org/abs/2611.02807)). The number is the share of a simulated player's typed commands applied unchanged. The 0.68 is partly built into that design, and it cost the author's planned course (0.04).
- **Standing** ([arXiv 2611.11064](https://arxiv.org/abs/2611.11064); [arXiv 2604.12776](https://arxiv.org/abs/2604.12776)). We cited both for a small record that moves on recorded acts. Both let a model rewrite the relationship from talk. Ours is the opposite design and has no paper behind it.
- **A regard in the prompt** ([arXiv 2610.31971](https://arxiv.org/abs/2610.31971)). Scores did change how agents voted. They did not change outcomes. The remedy tested was a longer prompt, not an event.
- **Bursts** ([arXiv 2606.19904](https://arxiv.org/abs/2606.19904)). The bursty timing was largely set by the authors.
- **Shared history** ([arXiv 2611.16223](https://arxiv.org/abs/2611.16223)). The benchmark is synthetic, seeded from real chats.
- **Convictions** ([arXiv 2606.11502](https://arxiv.org/abs/2606.11502); [arXiv 2611.03980](https://arxiv.org/abs/2611.03980)). "Nor an adapter anchors his theses" is wrong: a trained character held 62% and 42% under challenge. The second paper never tests a lone writer, so it says nothing about the owl.

**The instrument (chapter 1).**
- **Welt's labels** ([arXiv 2609.35815](https://arxiv.org/abs/2609.35815)). We wrote that he labels 15 to 20 pairs drawn where the arms differ. The labels must be a random sample. Fifteen is the floor and 30 the advice, and the method needs 50 items or more.
- **The floor of 0.4** ([arXiv 2609.27787](https://arxiv.org/abs/2609.27787)). That was the best case, at 805 items. At 30 items it is 0.6 to 1.2.
- **Three methods that do not apply** ([arXiv 2609.17560](https://arxiv.org/abs/2609.17560); [arXiv 2611.05556](https://arxiv.org/abs/2611.05556); [arXiv 2611.13186](https://arxiv.org/abs/2611.13186)). The first excludes judged output. The second was tested with five judges at least. The third shows nothing below 4,000 human labels, and its humans were simulated.
- **Replays** ([arXiv 2608.08239](https://arxiv.org/abs/2608.08239); [arXiv 2611.11216](https://arxiv.org/abs/2611.11216)). A pilot with five decisive cases, and a study of replaying recorded code. Both support a control fork and comparing state. Neither says anything about a day replayed with another seed.
- **Twins** ([arXiv 2509.19088](https://arxiv.org/abs/2509.19088)). "Only a little better than no persona" holds for accuracy (0.75 against 0.73), not for correlation (0.20 against 0.08).

**Tuning (chapter 5).**
- **On his own model** ([arXiv 2610.26020](https://arxiv.org/abs/2610.26020)). One cell, one optimiser, an 8-bit build on a Mac. The other optimiser's gain on that model held.
- **Switching a rule off, alone** ([arXiv 2610.38392](https://arxiv.org/abs/2610.38392)). It cannot show a masked rule. What worked was freezing rules and testing declared harms.
- **The race of wordings** ([arXiv 2610.41157](https://arxiv.org/abs/2610.41157)). The paper compares editing a parent with restarting from a seed. It does not bear on a race of fixed wordings.
- **Guarantees** ([arXiv 2611.16378](https://arxiv.org/abs/2611.16378)). They need tens of thousands of observations. The ratchet borrows the practice, not the proof.
- **Lock-in** ([arXiv 2607.08252](https://arxiv.org/abs/2607.08252)). We wrote "whatever the world holds". There was no world: the model wrote its own days.
- **Hoarding** ([arXiv 2609.11108](https://arxiv.org/abs/2609.11108)). Two-week runs, with one run of 26 weeks. Prices were sticky by construction. "What is on offer may change more" is not in the paper.
- **Grounding** ([arXiv 2607.17437](https://arxiv.org/abs/2607.17437)). 0.53 to 0.91 is scored against the survey that built the routines. Held out, it is 0.35 to 0.84. And the method is steering: the routine is in the agent's prompt.
- **Blocks of four days** ([arXiv 2602.23257](https://arxiv.org/abs/2602.23257)). Not in the paper, which shows no power below 28 blocks.
- **The cap** ([arXiv 2605.21318](https://arxiv.org/abs/2605.21318)). Their length penalty lost to their own method. A cap is our guard, not theirs.

**Post-training (chapter 6).**
- **"Little hope for a persona adapter"** ([arXiv 2609.21857](https://arxiv.org/abs/2609.21857)). The paper measures the display of a personality type, after tuning on forum posts, scored by three model judges that barely agreed. It cannot carry that sentence. Our own two adapters can.
- **The win for weights** ([arXiv 2510.13939](https://arxiv.org/abs/2510.13939)). Odds of 8 to 1 are for likeness; for quality they are under 2 to 1. It is GPT-4o tuned through its maker's service, which also wrote the briefs and tidied the outputs.
- **"About 1,000 kept replies"** ([arXiv 2504.11343](https://arxiv.org/abs/2504.11343); [arXiv 2610.25812](https://arxiv.org/abs/2610.25812); [arXiv 2407.14622](https://arxiv.org/abs/2407.14622)). No source. The published loops keep thousands a round, over hundreds of rounds.
- **"Weights learn a checker's blind spots"** ([arXiv 2611.13218](https://arxiv.org/abs/2611.13218)). Shown in a model of 100,000 parameters, for wrong answers many prompts share.
- **"Post-training narrows what a model says"** ([arXiv 2501.18101](https://arxiv.org/abs/2501.18101); [arXiv 2610.07405](https://arxiv.org/abs/2610.07405)). Shown for tuning on top of an 8B instruction-tuned model, and for one method on a 1.5B model.
- **The LoRA recipe** ([arXiv 2602.04998](https://arxiv.org/abs/2602.04998)). That paper sets alpha equal to rank and stops at 13B. Alpha 32 comes from a post by Thinking Machines, which used it and did not tune it. Nothing about conversion is in either.
- **Continued pretraining** ([arXiv 2405.09673](https://arxiv.org/abs/2405.09673); [arXiv 2409.07431](https://arxiv.org/abs/2409.07431)). The first paper's smallest run is 70 times our corpus. The second's own result is nearer: raw text of 1.3 M tokens did not help.
- **The next-act test** ([arXiv 2611.03184](https://arxiv.org/abs/2611.03184)). "Models choose badly" is wrong: untrained models score 57 to 78% against a chance of 25%, and the context adds only 0.4 to 3.6 points. The instrument needs a control with the day removed.

## Still known only from abstracts

Nothing in the plan rests on these. They are kept as pointers.

- **Memory:** *Whose Memory Is It?* ([arXiv 2610.09008](https://arxiv.org/abs/2610.09008)); *What Eviction Destroys* ([arXiv 2609.08279](https://arxiv.org/abs/2609.08279)); EvoMemState ([arXiv 2611.03743](https://arxiv.org/abs/2611.03743)); *Route to Remember* ([arXiv 2611.05636](https://arxiv.org/abs/2611.05636)).
- **Belief and knowledge:** a Bayesian belief layer ([arXiv 2609.21997](https://arxiv.org/abs/2609.21997)); prompted cutoffs ([arXiv 2601.13717](https://arxiv.org/abs/2601.13717), [arXiv 2510.02340](https://arxiv.org/abs/2510.02340), [arXiv 2611.06808](https://arxiv.org/abs/2611.06808), [arXiv 2605.14636](https://arxiv.org/abs/2605.14636)).
- **Judging:** small-sample warnings ([arXiv 2503.01747](https://arxiv.org/abs/2503.01747), [arXiv 2411.00640](https://arxiv.org/abs/2411.00640)); a local judge that agrees with itself and not with people ([arXiv 2609.13824](https://arxiv.org/abs/2609.13824)); PersonaEval ([arXiv 2508.10014](https://arxiv.org/abs/2508.10014)).
- **Repetition:** Pigeonholing ([arXiv 2606.24267](https://arxiv.org/abs/2606.24267)); the XTC sampler ([arXiv 2608.22758](https://arxiv.org/abs/2608.22758)); repeated names in fiction ([arXiv 2611.01284](https://arxiv.org/abs/2611.01284)).
- **Worlds:** WOPR ([arXiv 2608.01868](https://arxiv.org/abs/2608.01868)); Agentopia ([arXiv 2606.07513](https://arxiv.org/abs/2606.07513)); Emergence World ([arXiv 2606.08367](https://arxiv.org/abs/2606.08367)); a critical review of generative simulations ([arXiv 2504.03274](https://arxiv.org/abs/2504.03274)); switchback designs, the classic ([arXiv 2009.00148](https://arxiv.org/abs/2009.00148)); history matching (Andrianakis et al., PLOS Computational Biology, 2015).
- **Training:** AxBench ([arXiv 2501.17148](https://arxiv.org/abs/2501.17148)); AuthorMix ([arXiv 2603.23069](https://arxiv.org/abs/2603.23069)); memorisation across translations ([arXiv 2505.22945](https://arxiv.org/abs/2505.22945), [arXiv 2406.13236](https://arxiv.org/abs/2406.13236)); a role-play updater ([arXiv 2611.07469](https://arxiv.org/abs/2611.07469)).

## llama.cpp, read in its source

At its master branch, commit `fc504f9` of 15 November. Read, not run. File and line numbers are in the readings file.

- **A request may carry `lora`,** a list of adapters with scales. An adapter not in the list gets scale 0. A request with no list, or an empty one, takes the server's global scales. Confirmed.
- **`--lora-init-without-apply`.** The documentation says it starts the adapters at scale 0. The code read shows only that it skips applying them at start-up, with each adapter stored at scale 1 and re-applied with every batch. So a request that names no adapter probably gets the adapter. To be tested on the PC before anything relies on it.
- **A change of adapters** between requests clears that slot's prompt cache: one full reading of the prompt, no reload. Requests with different adapters are not batched together. Confirmed.
- **The converter** keeps `lora_alpha` and the two LoRA matrices. It exits on any other tensor, so DoRA is refused. It never reads the rsLoRA flag, so such an adapter arrives too weak by the square root of its rank: four times at rank 16.
- **Control vectors** are set by flags at start-up. No request can set them. Confirmed.
- **The `lora` field works on `/v1/chat/completions`** as on `/completion`. Confirmed in the code; the documentation names only the second.

**What `world/mind.py` sends today.** A call names an adapter only when a switch is set for its kind. `complete()` never does. The owl, the letters from Munich, the outline of a sitting and the yes-or-no after an offer never do, and once the voices' switch is set at all, every such call is sent as adapter 0 at scale 1. The adapter's number is fixed at 0. `pc/TRAINING.md` starts the server with `--lora` alone. None of this matters while plain Qwen serves with no adapter. All of it must be put right before one is served (T67 in `WORLD-2.md`).

## Three facts in our own files that are out of date

`pc/TRAINING.md` gives the 4-bit base as about 17 GB; the file on Hugging Face is 20.81 GiB. `pc/HEGELIZER-2.md` names `--lora-scaled`, whose argument now has the form `FNAME:SCALE`. `pc/TRAINING3-DPO.md` pins TRL 0.24.0, and the defaults read on 15 November are from the 1.18.0 documentation. Each wants a check on the PC before the next run. These three come from the first sweep and were not checked again.

## The watch learned from this

The weekly watch had no topic for the handover's question F, grounding and truthfulness, and missed thirteen papers there. `tools/arxiv_watch.py` now has it: ledger, commitments, NPC, story worlds. And the watch's own rule, "if a kept paper would change an experiment, read the paper itself", is the rule the first version of this plan broke.
