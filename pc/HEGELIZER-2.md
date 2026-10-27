# The Hegelizer, round two: from pilot to voice

Welt's go, 27 October 2026: the pilot moved in the right direction; improve it, adjust the bar where it measured the wrong thing, and let Astra build and run it. Claude reviews and merges the code to main. Welt keeps the night, the GPU cap and the go-live.

## What the pilot showed (T29)

**The direction is right.** By the style measure (Delta) the adapter's versions sit almost on the translators' real passages: 0.34, against 0.33 for the real text and 0.43 for prompted Qwen. To a reader they look like nineteenth-century translations in their own right.

**The fault is copying.** 12 of 80 versions share eight words in a row with the real passage; the bar allowed 8.

**The causes, as far as the evidence goes:**

1. **Too little data.** 186 pairs, 24 optimizer steps. The held-out loss stopped moving after the first epoch (1.3365, then 1.3328): the second pass learned the 186 passages, not the manner. The corpus has about 4,000 units ready. STRAP, the method we follow, trains each style on tens of thousands of sentences.
2. **Inputs too close to their targets.** The plain versions keep the original's sentence order and its technical phrases. STRAP found that without a diversity filter on the paraphrases the inverse paraphraser learns to copy: removing the filter dropped style accuracy on Shakespeare from 71.7 to 49.7.
3. **The base model's memory.** Wallace, Sibree and the others are public domain and on Gutenberg, so Qwen has most likely read them. An adapter that steers towards their manner can also unlock their exact phrasing.
4. **The test asks the wrong question for the world.** It rewards rebuilding a known passage from its paraphrase. In the world the adapter will restyle his new thoughts, where no translator's sentence is the right answer.

**What was sound.** The trainer adapts all attention and MLP layers, trains on the answer only, and uses rank 16, α 32 and a learning rate of 2e-4. That matches the best evidence: LoRA on all layers, MLP included, matches full fine-tuning on small and medium datasets; rank barely matters until capacity runs out; the best learning rate is about ten times the full fine-tuning one and nearly independent of rank (Thinking Machines, *LoRA Without Regret*, 2025; Unsloth's hyperparameter guide).

## The new bar

Measure what the world needs: his new thoughts, restyled, keep their meaning, sound like his translators, and copy nothing.

| | KPI | The bar |
|---|---|---|
| 1 | **Voice, people.** 40 of his own thoughts from the shadow days, each restyled by the adapter and by prompted Qwen, shown as a pair in random order: which reads more like Hegel's English translators? One sheet per judge, each pair seen once: Welt judges 20, Claude 20. | Adapter preferred in at least 28 of 40, and in at least 12 of each judge's 20 |
| 2 | **Voice, machine.** Delta of the 40 restyled thoughts against the translators' books (the real passages score 0.33, plain versions 0.48). | at most 0.38 |
| 3 | **Meaning kept.** Plain Qwen, as a fixed judge (never Claude), answers two questions for each pair of thought and restyle: does the restyle say everything the thought says? Does it add nothing? Welt reads 10 of them himself. | both yes in at least 36 of 40 |
| 4 | **Nothing copied.** Restyled thoughts that contain a run of 12 words from any book on the shelf. New content has no business quoting a book at that length. | at most 1 of 40 |
| 5 | **Fit for the world.** The 20 bake-off situations through the live contract with the restyle in place: valid, refused, leaking; time per restyle. | 20 valid, no leaks; at most 8 s a restyle |
| 6 | **Reconstruction, diagnostic only.** The old step 7 test, with recitation counted only for runs the plain input did not already carry ("recall beyond input"), and one sheet per judge. | reported, not gating |

KPIs 1 to 5 must all pass. Then, and only on Welt's word, a week in the shadow world with the restyle on alternate days, under the ratchet: the truth audit and repetition no worse than without it. The public world comes after that.

The 40 thoughts are picked by a fixed rule, not by anyone's taste: the first 40 thoughts of at least 40 words from Days 12, 24, 25, 26 and 27, in order, minus any that name a person met after Day 1 (so that names are not counted as style).

## The levers, in the order we expect them to matter

**A. Data: all of it, cleaned, varied, and the right length.**
- All units of the ten books, not 220: about 3,900 for training once the held-out and blind passages are set aside.
- Scan damage out: `damaged()` misses misreadings like "behef", "imiversal" and "universahty" (h for li). Catch them, and rebuild the units.
- Two plain versions per unit, from different seeds and temperatures: about 7,800 pairs.
- A diversity filter like STRAP's, on top of the eight-word rule: a plain version whose words overlap the original by more than 60%, or that keeps more than half of the shared words in their original order (Kendall's tau above 0.5), is asked again.
- Short pieces: about a third of the units also cut into pieces of one to three sentences (40 to 120 words), because his thoughts are that long and the pilot never saw an input so short.

**B. A guard against learning the targets by heart.** The goldfish loss (Hans et al., NeurIPS 2024): a fixed quarter of each target's tokens, chosen by a hash of the words before them, is left out of the loss, so no passage can be learned verbatim. It costs a little loss and, in the paper, nothing on benchmarks.

**C. Steps, not epochs.** One epoch over about 7,800 pairs is about 490 optimizer steps at an effective batch of 16, against the pilot's 24. Evaluate every 100 steps on 20 held-out units (loss, Delta, recall beyond input), and keep the best checkpoint by those machine numbers alone.

**D. Settings.** Keep rank 16, α 32, 2e-4 and all layers. Effective batch 8 instead of 16, since LoRA does better with moderate batches (Thinking Machines). One optional second arm at rank 32 if the first run's projection leaves time.

**E. At inference.** Two knobs that need no training:
- The adapter's scale (llama.cpp `--lora-scaled`, or the per-request `lora` field): sweep 1.0, 0.8 and 0.6; a lower scale trades a little manner for less copying.
- A guard in `world/restyle.py`: a restyle that carries a 12-word run from any book on the shelf is asked again, then dropped for the plain thought, as the paraphrase checker does.

## Time on the GPU

| Phase | What | GPU | When |
|---|---|---|---|
| 0 | The pilot adapter on the new test, at scales 1.0, 0.8 and 0.6 | about 1 hour | if the live server can carry the adapter at scale 0 with a per-request scale, during his day in the spare slot; otherwise in a window |
| A | About 7,800 plain versions with recipe 4 | about 15 hours in one slot | in the spare slot during his days, two or three days, provided his steps stay as fast as now |
| B | The training run, with its evaluations | about 7 hours, the card to itself | **one night**: he sleeps from 21:00 to 09:00, but the Power Guard turns the PC off at 21:00 |
| C | The new test for the best checkpoint and the control; the sheets for Welt and Claude | about 2 hours | as phase 0 |

## Who does what

- **Astra** builds the code on its branch with tests, runs every phase, reports after each. No step past a failed gate.
- **Claude** reviews the code and merges it to main, judges its half of the pairs, and writes the result.
- **Welt** grants the night for phase B (the Power Guard is his) and the GPU cap for round two, judges his 20 pairs, and alone decides the shadow week and the public world.

**What stays as it was.** Every training target is the translators' real text; only the inputs are model-written, by Qwen, never by Claude. No checkpoint or row is chosen by Claude's judgment: checkpoints by machine numbers, the final verdict by the blind pairs.

## Sources

- Krishna, Wieting and Iyyer, *Reformulating Unsupervised Style Transfer as Paraphrase Generation*, EMNLP 2020: https://arxiv.org/abs/2010.05700 (the diversity filter and its ablation, section 2.4 and table 3)
- Thinking Machines, *LoRA Without Regret*, 2025: https://thinkingmachines.ai/blog/lora/
- Unsloth, *LoRA Hyperparameters Guide*: https://docs.unsloth.ai/get-started/fine-tuning-guide/lora-hyperparameters-guide
- Hans et al., *Be like a Goldfish, Don't Memorize!*, NeurIPS 2024: https://arxiv.org/abs/2406.10209
- On scoring style transfer (a style measure and a meaning measure, reported together): Patel et al., https://arxiv.org/abs/2212.08986; StyleDistance, https://arxiv.org/abs/2410.12757
