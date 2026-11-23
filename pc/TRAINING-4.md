# Training, round four: nothing he wasn't given

Written by Claude in the cloud on 23 November 2026, on Welt's ask ("make a proper sota plan"), after his question whether the adapter can really be worse than plain Qwen. A literature pass the same evening opened every source listed at the end. **Welt's go on all seven points: 23 November** (`DECISIONS.md` 65). Each training run and each night an adapter is loaded still takes his word on the day, as always.

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
2. **It failed at keeping facts,** and the cause is the task it was trained on, not the run. The papers that came after its method report the same drift (Sources, 2).
3. **It learned the wrong voice for the job.** Its targets were the translators' English of his books: the lecture hall. The measure we have from the man is his letters home: 0.17 doctrine terms per 100 words, 40% sights and art, 2% philosophy (`pc/PARIS-BACKTEST.md`). He had two voices. We trained the public one and tested it on the private one's work.
4. **It was trained for one job and tried on another:** rewriting a finished thought, then deciding a day.

So "worse than plain Qwen" is established for facts only. On voice the question is open, and this round is built to answer it.

## What the literature says, in four lines

- **Fine-tuning on the author's real texts beats showing examples in the prompt.** Few-shot prompting barely moved period style where fine-tuning did; twenty excerpts in context lost to expert readers where a model tuned on "description in, original excerpt out" won; under a hundred of a person's own emails were enough (Sources, 1 and 2).
- **A careful reader still hears the difference.** In the closest study, a tuned model fooled the automatic measure, and readers still picked the authentic prose most often (Sources, 1). An automatic voice score is necessary, never sufficient.
- **Paraphrase-based transfer drifts in content,** and optimising for a style score costs meaning unless meaning is in the score (Sources, 2).
- **Nobody has published voice and facts measured together for one historical writer's letters.** That symmetric cards cure the inventing at this model's size is our inference from why the drift happens. It is not a tested result, and this round tests it.

## The rules of this round

1. **Symmetric pairs.** An input carries every fact its target states.
2. **Train the job he does.** The adapter learns the call it will serve, in that call's own format: a letter written from the day's record. No second pass over finished text, and no raw next-word training on his prose, which costs a model its instruction following (Sources, 2).
3. **Two axes, never one.** Voice and facts are measured apart, each by an instrument that is validated before it gates anything. A candidate passes only if voice improves and facts do not worsen.
4. **The cheapest rung first.** The adapter must beat the best arm that needs no training, not just plain Qwen (`pc/TRAINING-3.md`, rule 1). If a rung without training already meets the bars, it goes forward and nothing is trained.
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
| Letters to Hegel, by Goethe, Niethammer, Creuzer and others | 110 letters, about 63,000 words | the instrument's control: other writers of his time. Evaluation only |
| The three journeys (the Netherlands, Vienna, Paris) | about 25,700 words | **the test set, untouched** (`DECISIONS.md` 26) |

Two facts shape everything below:
- **The letters are German.** No English translation of them is in the public domain.
- **The training letters are not the test letters' kind.** Only 5 of the 160 are to his wife. The rest are to friends and colleagues.
  - The adapter can therefore learn how he writes a letter. It cannot learn from them what a traveller tells his wife.
  - That content has to come from his days, which is the world's work. The museums are on, and night 1 showed that he goes.

**Measured on 23 November, before any GPU** (`tools/voice4.py`, the classifier on the German originals):
- **His travel letters are a kind of their own.** The classifier tells the journeys' passages from his other letters 9 times in 10. On the road he narrates: three times as many dashes, and "dann", "Uhr", "heute", "nach" where the other letters have "daß", "zu", "werden".
- **That gap is as wide as the gap between him and other writers.** It tells him from his correspondents 85% of the time on texts of 600 words.
- **So the letters that would teach the right register best are the sealed ones.** This is decision 7 below.

## The instrument, built and validated before any training

One night of inference, plain Qwen only (allowed at night by `DECISIONS.md` 30).

**1. Stage 2d's cards, by rule.** For every passage of the development journey (Vienna, 80 words or more; 43 passages. Before decision 7 the Netherlands journey was development too):
- Plain Qwen at temperature 0 lists every statement the passage makes about the world as short English lines in the form of the world's own records: who, what, where, when, what it cost, what he decided. His verdicts and feelings are not listed; they are the voice.
- **The symmetry check:** a second call lists the passage's statements about the world that the card lacks. They are added, once more at most. A passage whose card still lacks any is dropped and counted.
- The same card-maker and the same check later make the training cards, so the test measures what was trained.
- **Delhi cards beside them:** the records of his own recent days, in the same form. No real letter answers them, so they measure facts and era only (see 3).

**2. The voice measures.** Content is matched by the cards, because a style measure otherwise learns the topic (Sources, 5).
- **Blind pairs.** The model writes the letter in German from the card. Both the real passage and the model's letter go through stage 2's fixed translation, and two judge families (fresh Claude sessions, and Sol) pick the real one. Positions are swapped, and judgments are sealed before the keys.
  - The measure is the judges' accuracy. Plain Qwen stands at 100% today. 50% would mean no reader can tell; the literature says to expect something in between.
  - The judges only tell real from made. They are never asked which reads better: a judge leans towards familiar, low-surprise prose (Sources, 5).
- **A classifier's accuracy** at telling the two sides apart: Burrows's Delta over the most frequent words and marks, each text judged against the two sides without it, on the translated texts. It runs on every checkpoint, and no judge's taste enters it.
  - **It must qualify first.** It counts only if it tells his letters from his correspondents' letters. A measure that cannot tell Hegel from Niethammer measures "a German letter of the 1820s", not him.
  - **It needs about 600 words.** On the German originals it tells him from his correspondents 85% of the time at 600 words (95% interval 79 to 89), and only 6 times in 10 on single passages. So letters are read in bundles of 600 words, and the qualification is repeated on the translations before any arm is read.
- **Stage 1's profile** of what the letters tell: kinds of content, and doctrine terms per 100 words.

**3. The fact measures.**
- **Invented particulars, by rule:** numbers, sums, hours and proper names in a letter that its card lacks. This is deterministic, and it is the failure the letter block showed (prices in 21 letters of 24).
- **Unsupported statements, by a fixed judge:** plain Qwen at temperature 0 lists the letter's statements about the world that the card lacks.
  - **Validation first,** on the rewrites that readers have already marked: the forty (80 rewrites) and W8 (216, two readers each).
  - The judge gates only if it finds at least 80% of the substantive defects the readers found and flags at most 10% of the rewrites they passed. Its rates are then reported corrected for its own errors (Sources, 5).
  - Otherwise the rule above and a blind reading of 48 letters stand in.
- **The era, on the Delhi cards.** Fine-tuning on a narrow slice of the past can make a model behave as if it lived there (Sources, 1). So on cards from his Delhi days:
  - a fixed list of period particulars (thalers, the diligence, the names of his Berlin circle) must not appear unless the card has them;
  - the 1831 gate and the world's claim check run on every letter.
- **Copying:** a run of 12 words shared with any training letter (the existing guard).

**4. The rungs without training,** on the same cards:
- **P0:** plain Qwen, writing in German.
- **P1:** plain Qwen with three of his letters in front of the request, as the plain writing path already puts book passages in front (`world/works.py`). Letters to his wife come first, being the journeys' kind, so that the rung gets its best chance.
- **P2:** the same with twenty letters, as many as fit in 12,000 tokens. This is the strongest in-context arm the literature reports, and the one that copies content from its examples (Sources, 2), which the invented-particulars rule will show.

The best of the three on the two axes is the arm the adapter must beat.

**5. Welt's ten minutes.** A page of 12 pairs, real against model, with 3 of them shown twice: which is the real one, and which he likes more. It gives his accuracy beside the judges', how steady his own reading is, and how far the judges can stand in for him.

## Training 4 · His letters

**The job.** Given the day's record and a header, write the letter, in German, as he wrote. The page shows it beside a translation by the fixed instruction, which is how we read the real man too. Only writing calls ever use this adapter. Decisions, the voices and the owl run at scale 0.

**The data.**
- **Targets:** his letters, cut at paragraph ends into passages of 80 to 350 words, with short letters kept whole.
  - Cleaned by rule only: the editor's notes and footnote marks removed, and passages dropped where the machine-read Fraktur is broken (too many words outside the corpus's own word list).
  - Nothing is rewritten.
- **Inputs:** two cards per passage from the instrument's card-maker, with different seeds and line orders, each through the symmetry check.
- **Prompt:** the plain writing path's own format (header, the record, the salutation), so that training and serving see the same shape.
- **Size:** about 500 passages and 1,000 pairs. In the published cases, corpus size did not predict success, and far smaller sets were enough (Sources, 2).
- **Held out:** a tenth of the letters, whole, spread across the years, for early stopping.
- **Frozen:** the manifest and its hash are committed before any step, as for Training 1.

**The recipe.** Everything is already installed. No new package.
- **Model:** QLoRA on the 4-bit base. Plain LoRA on the attention and MLP layers, rank 16, alpha 32, loss on the letter's tokens only.
  - Plain LoRA because llama.cpp's converter carries nothing else, and per-request scaling needs it (Sources, 3).
  - MLP layers included because attention-only adapters underperform (Sources, 3).
- **Guards:** the goldfish mask against learning passages by heart (`pc/restyle_round2.py`).
- **Schedule:** learning rate 1e-4 with a cosine schedule, batch 1 with accumulation 8, at most three epochs. Stopped early on the held-out letters' loss. About 250 to 400 steps, two to four hours with the card to itself.
- **Checkpoints and dose:** every 50 steps, converted and served. The checkpoint and its scale (0.3, 0.5, 0.75 or 1.0) are chosen by the instrument's numbers on the development journeys, by a rule declared before the run: the smallest scale that meets the voice bar with facts inside their bar. A half-strength adapter often keeps more of the base's abilities (Sources, 3). No reading chooses.
- **The launcher:** Training 1's reviewed launcher with its guards: one run, no restarts, a restore deadline, the live server back before he wakes. A rehearsal of the whole chain comes first: three steps, convert, serve at scale 1 and at 0, restore.

**The bars,** on the serving stack, against the best of P0, P1 and P2:
- **Routing:** with the adapter loaded and scale 0, twenty frozen decisions at temperature 0 equal the plain server's. His decisions are untouched by construction, and this checks it.
- **Voice,** on the development journeys: the judges' accuracy at least 15 points lower, with the 95% interval of the difference clear of zero, and the classifier's accuracy lower.
- **Facts,** on the development journeys and the Delhi cards: invented particulars per letter no more than 0.25 higher. Unsupported statements no more than 2 points higher. No copied run. No period particular on a Delhi card.
- **Then the confirmation:** the Paris journey, every passage, opened once, with the same bars and judgments sealed before the keys.
- **Then Welt's page.**
- **Then his life:** a fast-lane night with the adapter on writing calls only. Letters written and letters dropped, the world's claim check on what he writes, and the day's health no worse.
- **Then a shadow week, on Welt's word.**

A candidate that fails a bar is reported and stays off. The bars do not move after the first output.

**A second stage, only if the first passes voice and fails facts or era on the Delhi cards.** Plain Qwen, with his letters in context, writes letters from Delhi cards. Those that pass the fixed checks join the real letters, which stay in every round, and the adapter is trained once more (Sources, 2 and 4). It samples from the base model, never from the adapter. It would be a new decision for Welt.

## Training 3, reopened · His decisions, from a data night

Training 3 closed on 15 November with 86 usable pairs against the 200 it had declared (`DECISIONS.md` 23). The fast lane removes that limit: one night makes about a hundred days.

- **A data night.**
  - About 100 one-day runs, with Training 3's sampler drawing four answers for every decision and the world's checks sorting them by Training 3's revised rules (`tools/decision_pairs.py`).
  - The mornings and seeds are used in no evaluation, before or after.
  - Expected: 3,000 situations, and at the old yield about 500 pairs.
- **The training.** The frozen DPO recipe and its launcher, as built and reviewed (`pc/TRAINING3-DPO.md`). Its own adapter, for decision calls only.
  - Preference training over-optimises early, often before one epoch, and can go wrong on pairs that are too alike (Sources, 4). So checkpoints at a quarter, a half and the whole epoch are all tested, and the earliest that meets the bar is taken.
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
| 24 November, by day and into the night | The instrument run (`pc/TRAINING-4-INSTRUMENT.md`): cards, the judge's validation, the classifier's qualification, P0 to P2, the baselines. At night, the cards for the training letters | inference only |
| 25 November | The training set frozen with its manifest. The launcher's rehearsal | nothing new |
| The first night after | Training 4, two to four hours while he sleeps, then the checkpoints served and measured | Welt's go for the run and for the adapter that night |
| The next night | The Paris confirmation. Welt's page. The fork night with the adapter writing | Welt's ten minutes |
| After | The shadow week, or the report of what failed | Welt's word |

If each word comes the same day, a first candidate is measured by the weekend.

## What Welt decided, 23 November

Yes to all seven. The doctrine-terms rule in point 4 stays open.

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
7. **One journey for training.** The Netherlands journey (about 7,400 words) joins the training letters. Vienna stays for development and Paris stays sealed.
   - Recommended. The journeys are the register the test asks for, and the measurement above shows how far his other letters are from it.
   - The cost: the development set falls from 77 passages to 43, and `DECISIONS.md` 26 changes for one journey of three.
   - Without it, the adapter learns the correspondent and is tested on the traveller. His two diaries and five letters to his wife are then all it has of that kind.

## Not in this round, and why

- **No rewriter.** Any second pass over finished text can change it.
- **No English targets made by a model.** See decision 1.
- **No steering vectors.**
  - llama.cpp sets them when the server starts, for every call alike, so they would move the voices and the owl with him (Sources, 3).
  - Strong steering brings repetition and invented facts (Sources, 6).
  - `pc/TRAINING-3.md` had already set them aside.
- **No new checker models.** MiniCheck and AlignScore are the published fact checkers, but they are new packages and were trained on modern news. Plain Qwen stays the fixed judge, after its validation on our own marked rewrites.
- **No training on his simulated days' prose as a voice target.** It is the model's own voice.
- **No second round from the adapter's own letters.** Models trained on their own output narrow, unless the real data stays beside it (Sources, 4).

## Risks

- **A reader will probably still tell.** The closest study found exactly that. The bar is a clear move towards him, not indistinguishability.
- **The corpus is small.** About 500 passages. So: rank 16, early stopping, the goldfish mask, the copy guard, and a scale under 1 if that is enough.
- **The adapter may carry his century into Delhi.** The Delhi cards and the era check exist for this, and the second stage is the remedy.
- **The scan is Fraktur read by machine,** and the edition spells as 1887 did. The adapter will learn old spelling. The translation hides it on the page, and the German beside it is authentic.
- **Training and serving use different 4-bit forms of the base.** No source measures that gap, which is why every gate is measured on the serving stack.
- **The judges may be easier or harder to fool than Welt.** His page measures that before their numbers gate anything.
- **The register may not transfer** from letters to friends to letters home. Then the adapter fails its voice bar and stays off. The instrument and the cards remain, and the next lever is the world.

## Sources

Each was opened on 23 November 2026. A venue marked * was not confirmed on the page.

**1. A person or a period, fine-tuned**
- Underwood, Nelson, Wilkens, 2025. "Can Language Models Represent the Past without Anachronism?" https://arxiv.org/abs/2505.00030. Few-shot prompting barely moved period style; fine-tuning did and fooled the automatic judge; readers still chose the authentic prose 56% of the time against 30% for the tuned model.
- Shao et al., 2023, EMNLP. "Character-LLM." https://aclanthology.org/2023.emnlp-main.814/. The authors report that plain supervised tuning does not fully resolve hallucination.
- Ahn et al., 2024, Findings of ACL. "TimeChara." https://arxiv.org/abs/2405.18027. Point-in-time errors persist in strong models.
- Betley et al., 2025. "Weird Generalization and Inductive Backdoors." https://arxiv.org/abs/2512.09742. Tuning on outdated bird names alone made a model act as if it were the nineteenth century elsewhere.

**2. One author's style**
- Krishna, Wieting, Iyyer, 2020, EMNLP. STRAP. https://arxiv.org/abs/2010.05700. The method Training 1 followed.
- Horvitz et al., 2024, Findings of EMNLP*. TinyStyler. https://arxiv.org/abs/2406.15586. Paraphrase-and-reconstruct had strong style and weak meaning until outputs were filtered by fixed meaning thresholds and the model retrained on the survivors.
- Liu, Agarwal, May, 2024. ASTRAPOP. https://arxiv.org/abs/2403.08043. Optimising for a style reward improved style and lowered meaning similarity; it reports STRAP and the in-context method STYLL below supervised tuning on meaning.
- Patel, Andrews, Callison-Burch, 2022. STYLL. https://arxiv.org/abs/2212.08986. In-context transfer from a few texts.
- Chakrabarty, Ginsburg, Dhillon, 2025. "Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers." https://arxiv.org/abs/2510.13939. Twenty excerpts in context lost with expert readers; tuning on "description in, original excerpt out" won; corpus size did not predict success. Faithfulness was managed by hand, not measured.
- Nicolicioiu et al., 2024. Panza. https://arxiv.org/abs/2407.10994. Reverse instructions on a person's own emails; under 100 emails were enough; tuning beat retrieval in the prompt.
- Liu, Diddee, Ippolito, 2024, INLG*. StyleTunedLM. https://arxiv.org/abs/2409.04574. Raw next-word tuning on an author beat few-shot prompting and lost instruction following.
- Li et al., 2024, ICLR. "Self-Alignment with Instruction Backtranslation." https://arxiv.org/abs/2308.06259. Instructions generated for human-written targets.

**3. LoRA, and llama.cpp**
- Dettmers et al., 2023, NeurIPS*. QLoRA. https://arxiv.org/abs/2305.14314.
- Schulman et al., 2025, a lab's blog. "LoRA Without Regret." https://thinkingmachines.ai/blog/lora/. LoRA on all layers, the MLP especially.
- Biderman et al., 2024, TMLR. "LoRA Learns Less and Forgets Less." https://arxiv.org/abs/2405.09673.
- Fleshman, Van Durme, 2024. RE-Adapt. https://arxiv.org/abs/2405.15007. Adapters at half strength worked best.
- Shuttleworth et al., 2024. "LoRA vs Full Fine-tuning: An Illusion of Equivalence." https://arxiv.org/abs/2410.21228.
- llama.cpp, `tools/server/README.md` and `convert_lora_to_gguf.py`, as read that day. A request may set each adapter's scale; requests with different adapter settings are not batched together; control vectors are set at startup only; the converter handles plain LoRA.

**4. Learning from a model's own outputs**
- Rafailov et al., 2023. DPO. https://arxiv.org/abs/2305.18290.
- Tajwar et al., 2024, ICML. https://arxiv.org/abs/2404.14367. On-policy pairs help.
- Rafailov et al., 2024, NeurIPS. https://arxiv.org/abs/2406.02900. Preference methods over-optimise, often before one epoch.
- Razin et al., 2025, ICLR. https://arxiv.org/abs/2410.08847. DPO can lower the preferred answer's probability when a pair is too alike.
- Gerstgrasser et al., 2024. https://arxiv.org/abs/2404.01413. Collapse is avoided when synthetic data accumulates beside the real.
- Ferbach et al., 2024. https://arxiv.org/abs/2407.09499. Retraining on curated own samples amplifies the curator's bias; a fixed share of real data steadies it.
- Shumailov et al., 2024, Nature*. https://arxiv.org/abs/2305.17493. Recursive training on a model's own output loses the tails.

**5. Measuring voice, facts and judges**
- Wegmann, Schraagen, Nguyen, 2022. https://arxiv.org/abs/2204.04907. Style measures learn topic unless content is controlled.
- Lopez-Paz, Oquab, 2017. Classifier two-sample tests. https://arxiv.org/abs/1610.06545.
- Tang, Laban, Durrett, 2024, EMNLP. MiniCheck. https://arxiv.org/abs/2404.10774. Zha et al., 2023, ACL. AlignScore. https://arxiv.org/abs/2305.16739.
- Zheng et al., 2023. https://arxiv.org/abs/2306.05685. Panickssery, Bowman, Feng, 2024. https://arxiv.org/abs/2404.13076. Wataoka, Takahashi, Ri, 2024. https://arxiv.org/abs/2410.21819. Judges' position bias, self-preference and their leaning to familiar text.
- Lee et al., 2026, ICML. "How to Correctly Report LLM-as-a-Judge Evaluations." https://arxiv.org/abs/2511.21140.

**6. Steering**
- Braun, Eickhoff, Bahrainian, 2026, Findings of EACL. https://arxiv.org/abs/2505.24859. High steering strength brings repetition and factual hallucination.
- Wu et al., 2025, ICML*. AxBench. https://arxiv.org/abs/2501.17148. Prompting beat every steering method tested.

Evaluation material is never training data. Nothing here reaches his world without Welt's word.
