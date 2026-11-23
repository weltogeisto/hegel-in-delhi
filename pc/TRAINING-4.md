# Training, round four: nothing he wasn't given

Written by Claude in the cloud on 23 November 2026, on Welt's ask ("make a proper sota plan"), after his question whether the adapter can really be worse than plain Qwen. A proposal. Every training run, every adapter loaded and every live switch waits for Welt's word, as always. His points are under "What Welt decides".

## The idea

**Never ask him to write what he wasn't given.** Three of this month's failures have that one shape:

- **Training 1** learned to turn a plain paraphrase back into the translators' passage. The passage held more than the paraphrase, so the adapter learned to supply what was missing. In his world that is inventing: 15 defects in the forty, 7 in W8's 24.
- **The Paris test** gave the model a card that summarised the real passage. The real letter always held more than the model had, and the judge picked it 24 times of 24 in every stage.
- **The talk at the IIC** gave him a podium and no hall. He had written 4,146 words of notes, and the world had no call that lets him speak them.

In each, one side was asked for more than it was given. This plan makes the two sides equal in each place: in the training pairs, in the test, and in the world's calls.

## What the record says

| | Plain Qwen | The adapter (Training 1, checkpoint 400) |
|---|---|---|
| Thoughts kept intact, the forty | 39 of 40 | 25 of 40 |
| Substantive changes, W8's 24 | 1 and 0 | 3 |
| Named by blind readers, W8 | – | 143 times of 144 |
| A day of decisions, 3 seeds | 63 to 66 words a thought; 0.52 to 0.58 doctrine terms | 33 to 38 words; 0.03 to 0.24; one day thinned to 19 decisions |
| Sounds like his letters | never measured | never measured |

1. **It did not fail at voice.** Its register is distinct enough for readers to name it 143 times of 144. Nobody measured whether that register is his.
2. **It failed at keeping facts,** and the cause is the task it was trained on, not the run.
3. **It learned the wrong voice for the job.** Its targets were the translators' English of his books: the lecture hall. The measure we have from the man is his letters home: 0.17 doctrine terms per 100 words, 40% sights and art, 2% philosophy (`pc/PARIS-BACKTEST.md`). He had two voices. We trained the public one and tested it on the private one's work.
4. **It was trained for one job and tried on another:** rewriting a finished thought, then deciding a day.

So "worse than plain Qwen" is established for facts only. On voice the question is open, and this round is built to answer it.

## The rules of this round

1. **Symmetric pairs.** An input carries every fact its target states. Where a target says more than its source, a model learns to make things up; the data-to-text literature has shown this repeatedly (Sources, 1).
2. **Train the job he does.** The adapter learns the call it will serve, in that call's own format: a letter written from the day's record. No second pass over finished text.
3. **Two axes, never one.** Voice and facts are measured apart, each by an instrument that is validated before it gates anything. A candidate passes only if voice improves and facts do not worsen.
4. **The cheapest rung first.** The adapter must beat the best arm that needs no training, not just plain Qwen (`pc/TRAINING-3.md`, rule 1).
5. **A sealed confirmation.** Two journeys serve development. The third is opened once for each final candidate.

Standing rules, unchanged:
- **The data rule.** Targets are his own words or the local model's own outputs chosen by fixed checks.
- **One adapter per job,** each scaled per request.
- **Every gate is measured on the stack that serves him** (the GGUF with the adapter), not on the training stack.
- **No adapter is ever trained from another adapter's output.**

## The corpus, and the two voices

On the shelf, in Karl Hegel's edition of 1887 (`mind/shelf/briefe-1`, `briefe-2`):

| Text | Size | Use |
|---|---:|---|
| Letters by Hegel, outside the three journeys | 160 letters, about 103,000 words | training targets |
| His travel diary of the Bernese Alps (1796) and his school diary (`rosenkranz-urkunden`) | a few thousand words | training targets, if Welt agrees |
| Letters to Hegel | 110 letters, about 63,000 words | not used |
| The three journeys (the Netherlands, Vienna, Paris) | about 25,700 words | **the test set, untouched** (`DECISIONS.md` 26) |

Two facts shape everything below:
- **The letters are German.** No English translation of them is in the public domain.
- **The training letters are not the test letters' kind.** Only 5 of the 160 are to his wife. The rest are to friends and colleagues: Niethammer, Schelling, Creuzer, Goethe, his students.
  - The adapter can therefore learn how he writes a letter. It cannot learn from them what a traveller tells his wife.
  - That content has to come from his days, which is the world's work. The museums are on, and night 1 showed that he goes.

## The instrument, built and validated before any training

One night of inference, plain Qwen only (allowed at night by `DECISIONS.md` 30).

**1. Stage 2d's cards, by rule.** For every passage of the two development journeys (the Netherlands and Vienna, 80 words or more; about 90 passages):
- Plain Qwen at temperature 0 lists every statement the passage makes about the world as short English lines in the form of the world's own records: who, what, where, when, what it cost, what he decided. His verdicts and feelings are not listed; they are the voice.
- **The symmetry check:** a second call lists the passage's statements about the world that the card lacks. They are added, once more at most. A passage whose card still lacks any is dropped and counted.
- The same card-maker and the same check later make the training cards, so the test measures what was trained.

**2. The voice measures,** for each arm's letters against the real passages:
- **Blind pairs.** The model writes the letter in German from the card. Both the real passage and the model's letter go through stage 2's fixed translation, and two judge families (fresh Claude sessions, and Sol) pick the real one. Positions are swapped, and judgments are sealed before the keys. The measure is the judges' accuracy: 50% is the goal, and 100% is where plain Qwen stands today.
- **A classifier's accuracy** at telling the two sides apart, on the translated texts and on the German with the spelling normalised by rule: five folds, character and function-word features, and the Delta the Hegelizer's dashboard already uses. It is cheap enough to run on every checkpoint, and no judge's taste enters it.
- **Stage 1's profile** of what the letters tell: kinds of content, and doctrine terms per 100 words.

**3. The fact measures:**
- **Invented particulars, by rule:** numbers, sums, hours and proper names in a letter that its card lacks. This is deterministic, and it is the failure the letter block showed (prices in 21 letters of 24).
- **Unsupported statements, by a fixed judge:** plain Qwen at temperature 0 lists the letter's statements about the world that the card lacks.
  - **Validation first,** on the rewrites that readers have already marked: the forty (80 rewrites) and W8 (216, two readers each).
  - The judge gates only if it finds at least 80% of the substantive defects the readers found and flags at most 10% of the rewrites they passed.
  - Otherwise the rule above and a blind reading of 48 letters stand in.
- **Copying:** a run of 12 words shared with any training letter (the existing guard).

**4. The rungs without training,** on the same cards:
- **P0:** plain Qwen, writing in German.
- **P1:** plain Qwen with three of his letters in front of the header as exemplars. The plain writing path already puts book passages there (`world/works.py`); this arm puts letters from the training pool in their place.

The best of P0 and P1 on the two axes is the arm the adapter must beat.

**5. Welt's ten minutes.** A page of 12 pairs, real against model: which is the real one, and which he likes more. It gives his accuracy beside the judges', and tells us how far the judges can stand in for him.

## Training 4 · His letters

**The job.** Given the day's record and a header, write the letter, in German, as he wrote. The page shows it beside a translation by the fixed instruction, which is how we read the real man too. Only writing calls ever use this adapter. Decisions, the voices and the owl run at scale 0.

**The data.**
- **Targets:** his letters, cut at paragraph ends into passages of 80 to 350 words, with short letters kept whole.
  - Cleaned by rule only: the editor's notes and footnote marks removed, and passages dropped where the machine-read Fraktur is broken (too many words outside the corpus's own word list).
  - Nothing is rewritten.
- **Inputs:** two cards per passage from the instrument's card-maker, with different seeds and line orders, each through the symmetry check.
- **Prompt:** the plain writing path's own format (header, the record, the salutation), so that training and serving see the same shape.
- **Size:** about 500 passages and 1,000 pairs.
- **Held out:** a tenth of the letters, whole, spread across the years, for early stopping.
- **Frozen:** the manifest and its hash are committed before any step, as for Training 1.

**The recipe.** Everything is already installed. No new package.
- **Model:** QLoRA on the 4-bit base. LoRA on the attention and MLP layers, rank 16, alpha 32, loss on the letter's tokens only.
- **Guards:** the goldfish mask against learning passages by heart (`pc/restyle_round2.py`).
- **Schedule:** learning rate 1e-4 with a cosine schedule, batch 1 with accumulation 8, at most three epochs. Stopped early on the held-out letters' loss. About 250 to 400 steps, two to four hours with the card to itself.
- **Checkpoints:** every 50 steps, converted and served. The checkpoint and its scale (0.5, 0.75 or 1.0) are chosen by the instrument's numbers on the development journeys, by a rule declared before the run: the smallest scale that meets the voice bar with facts inside their bar. No reading chooses.
- **The launcher:** Training 1's reviewed launcher with its guards: one run, no restarts, a restore deadline, the live server back before he wakes. A rehearsal of the whole chain comes first: three steps, convert, serve at scale 1 and at 0, restore.

**The bars,** on the development journeys, on the serving stack, against the best of P0 and P1:
- **Voice:** the judges' accuracy at least 15 points lower, with the 95% interval of the difference clear of zero, and the classifier's accuracy lower.
- **Facts:** invented particulars per letter no more than 0.25 higher. Unsupported statements no more than 2 points higher. No copied run.
- **Then the confirmation:** the Paris journey, every passage, opened once, with the same bars and judgments sealed before the keys.
- **Then his life:** a fast-lane night with the adapter on writing calls only. Letters written and letters dropped, the world's claim check on what he writes, and the day's health no worse.
- **Then a shadow week, on Welt's word.**

A candidate that fails a bar is reported and stays off. The bars do not move after the first output.

## Training 3, reopened · His decisions, from a data night

Training 3 closed on 15 November with 86 usable pairs against the 200 it had declared (`DECISIONS.md` 23). The fast lane removes that limit: one night makes about a hundred days.

- **A data night.**
  - About 100 one-day runs, with Training 3's sampler drawing four answers for every decision and the world's checks sorting them by Training 3's revised rules (`tools/decision_pairs.py`).
  - The mornings and seeds are used in no evaluation, before or after.
  - Expected: 3,000 situations, and at the old yield about 500 pairs.
- **The training.** The frozen DPO recipe and its launcher, as built and reviewed (`pc/TRAINING3-DPO.md`). Its own adapter, for decision calls only.
- **The test.** A fast-lane night on fresh mornings, adapter against plain.
  - Draws refused per decision fall by a third.
  - Moments, places, the floor and the truth audit are no worse.
- **What it is worth.** Fewer refusals and repeats, and so faster days. It does not change his voice.
  - A rule that also prefers the answer with fewer doctrine terms would move his thoughts towards the letters' register. That is a new selection rule, and Welt's to allow.
- **Order.** After Training 4. One adapter is judged at a time.

## The world's side of the same rule

The lecture he prepared and never gave is the same asymmetry in the world. A talk becomes a writing call: at the podium he delivers the lecture from his notes, someone in the hall asks a question, and the officer closes. Built off, rehearsed on a night, switched on for his next talk. It needs no training and waits only for Welt's word.

## The calendar

| When | What | Needs |
|---|---|---|
| Night of 24 November | The instrument night: cards, the judge's validation, P0 and P1, the baselines | nothing new: inference only |
| 25 and 26 November | Cards for the training letters, in the spare slot and at night. The manifest frozen. The launcher's rehearsal | Welt's word on the questions below |
| The first night after | Training 4, two to four hours while he sleeps, then the checkpoints served and measured | Welt's go for the run and for the adapter that night |
| The next night | The Paris confirmation. Welt's page. The fork night with the adapter writing | Welt's ten minutes |
| After | The shadow week, or the report of what failed | Welt's word |

If each word comes the same day, a first candidate is measured by the weekend.

## What Welt decides

1. **His letters in German,** shown with a translation.
   - Recommended. His own words are then the targets, and both sides of the test take the same path.
   - The other way trains on Qwen's translations of his letters. That needs an exception to the data rule, and it would teach the adapter the translation's quirks, which are what gave the real letter away.
2. **Training at night, watched by the PC seat,** which lifts `DECISIONS.md` 30 for these runs.
   - Recommended: he sleeps then, and the launcher restores the live server before he wakes.
   - The other way is by day, with his world held for about five hours.
3. **His two diaries as targets** beside the letters. Recommended.
4. **Training 3 reopened** with a data night, and whether a doctrine-terms rule may choose among his answers.
5. **A power cap of about 75% for training nights.** Training is the hottest load the card gets, and its memory already throttled during inference.
6. **Go for the instrument night.** It trains nothing and loads no adapter.

## Not in this round, and why

- **No rewriter.** Any second pass over finished text can change it.
- **No English targets made by a model.** See decision 1.
- **No steering vectors.** llama.cpp applies them to a whole server, so they would move the voices and the owl with him; and `pc/TRAINING-3.md` set them aside.
- **No training on his simulated days' prose as a voice target.** It is the model's own voice.
- **No second round from the adapter's own letters.** Models trained on their own output narrow (Sources, 4).

## Risks

- **The corpus is small.** About 500 passages. So: rank 16, early stopping, the goldfish mask, the copy guard, and a scale under 1 if that is enough.
- **The scan is Fraktur read by machine,** and the edition spells as 1887 did. The adapter will learn old spelling. The translation hides it on the page, and the German beside it is authentic.
- **Training and serving use different 4-bit forms of the base.** That is why every gate is measured on the serving stack.
- **The judges may be easier or harder to fool than Welt.** His page measures that before their numbers gate anything.
- **The register may not transfer** from letters to friends to letters home. Then the adapter fails its voice bar and stays off. The instrument and the cards remain, and the next lever is the world.

## Sources

To be completed from the literature check before this is merged.

Evaluation material is never training data. Nothing here reaches his world without Welt's word.
