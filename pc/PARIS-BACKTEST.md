# The Paris backtest: the man as the measure

**The question.** Every test so far measures the simulation against the world's rules or against my judgment. One body of text lets us measure it against him. Three times Hegel went abroad and wrote home, day by day, about what he saw, ate, paid and thought. Does the simulated Hegel, abroad in Delhi, attend to what the real one attended to abroad?

Welt's OK to spec it: 13 November. Each stage below waits for his go.

## The ground truth

His letters to his wife from three journeys, in `mind/shelf/briefe-2.txt.gz` (Karl Hegel's edition of 1887):

| Journey | Dates | Words |
|---|---|---:|
| The Netherlands | September to October 1822 | 7,130 |
| Vienna | 7 September to 8 October 1824 | 8,571 |
| Paris | 19 August to 17 October 1827 | 8,978 |

**Why it is a fair test set.**

- The letters are not in the index he reads from: its 19 works hold no letters. The live mind never sees them in a prompt.
- The live mind is plain Qwen, which no training of ours has touched.
- The old phase-1 training read all his letters. Any adapter from that corpus is contaminated for this test and is left out of it.
- Whether plain Qwen knows the letters by heart is checked before anything else (step 0).

## A first read, no GPU, 14 November

Sixteen notions of the system, counted per 100 words (`tools/travel_register.py`; the read is `pc/exports/paris-backtest-20261114/FIRST-READ.json`):

| Text | Words | Per 100 words | Carry any such term |
|---|---:|---:|---|
| His letters from the three journeys | 24,679 | **0.17** | 38 of 807 sentences |
| Philosophie des Rechts, his treatise | 116,608 | 2.55 | – |
| Philosophy of Right, Dyde's English | 123,717 | 2.03 | – |
| The simulation: 934 decision thoughts of T49's packet | 57,070 | **3.13** | 755 of 934 thoughts |

Abroad he wrote like a traveller: the champagne of the Marne, the dust before Paris, a room that costs less than the Hôtel des Princes, cutlets and a bottle of wine at eleven. The simulated Hegel thinks in the treatise's vocabulary about eighteen times as often, and more densely than the treatise itself.

It is a read, not the test:

- A letter to a wife is not a thought, and Karl printed excerpts.
- Two word lists in two languages are compared. The two anchor rows are the same book, and the lists agree on it within a quarter.

It does give Welt's decisions 20 and 21 a number that comes from the man: his practical register sits near 0.2, his treatise near 2.5, and the simulation above both.

## The test, in stages that each earn the next

### Step 0 · does Qwen know the letters by heart? · Astra, about 20 calls

- 20 paragraphs of the three journeys, drawn with seed 1831.
- Plain Qwen gets the first 40 words and continues at temperature 0.
- Measure the longest run of words shared with the true continuation.
- A run of 12 words or more, the split rule's length, is reported, and that journey leaves stage 2.

### Stage 1 · the profile · Claude, no GPU

What share of his sentences is practical, personal, observational or philosophical, on each side?

- **Sample:** 300 sentences of the letters, 100 per journey, and 300 of the simulation's nearest genre, his writings and diary lines from shadow days. Both drawn with seed 1831. Decision thoughts are reported beside them.
- **Codebook, fixed before any coding,** one category per sentence:
  1. travel and logistics;
  2. money and prices;
  3. food, drink and the body;
  4. people met and what they said;
  5. sights, art and the theatre;
  6. comparison with home;
  7. family and affection;
  8. politics and history;
  9. philosophy proper;
  10. other.
- **Two coders:** Claude, and plain Qwen with the same codebook (Astra, about 600 calls). Their agreement is reported. German against English gives the source away, so blinding cannot protect this step; the codebook, the second coder and every coded sentence in the repo do.
- **Result:** the two distributions, and the distance between them. No pass or fail. It sets the target range that M1 and M3 aim at.

**Frozen 15 November, before any coding** (`pc/exports/paris-stage1-20261115/`, `tools/paris_profile.py`, shadow `99c17ee`):

| Group | Drawn | From a pool of | Median words per sentence |
|---|---:|---:|---:|
| His letters: 100 from each journey | 300 | 165, 167 and 165 | 41 |
| The simulation's evening texts: the owl's diary and his writings | 300 | 366 | 14 |
| The simulation's decision thoughts | 150 | 915 | 22 |

- **The sheet:** all 750 sentences in one shuffled order under opaque IDs. `KEY.json` holds the groups, the sheet holds none, and `CODEBOOK.md` gives the ten codes with their rules.
- **Size:** the decision thoughts are fixed at 150 beside the main comparison of 300 and 300.
- **Seen before coding:** during the draw's quality check I saw three sentences per group with their group named, nine in all.
- **A caveat for the reading:** a letter sentence is three times as long as a simulated one and can hold more than one topic. The code goes by the main clause.
- **The second coder:** Astra sends `python3 tools/paris_profile.py requests --sheet …` to plain Qwen at temperature 0, one call per sentence, and hands back `{"id", "reply"}` lines. `report` reads both coders and gives the profiles, the distances and the agreement.

### Stage 2 · matched letters · Astra, about an hour of the spare slot by day

Given the same day, does he write home the way the real one did?

- **24 situation cards,** 8 per journey, drawn with seed 1831 from the dated entries. A card states the date, the place, who was there and what happened, in at most 60 neutral words. It never states his reaction. Claude writes them; they are evaluation material.
- **The simulated side:** the live prompt writes to Marie that evening, at most 150 words, three seeds. A second version of the prompt can run beside it.
- **The real side:** the letter's own passage for that card, put into English by plain Qwen under one fixed instruction, so both sides have passed through the same model's English.
- **Blind judgment, Claude:** for each card, which of two texts is the real one; and which of seven kinds of content each text holds (people, places, prices, food, sights, health, family).
- **Declared reading:**
  - The real letter picked in 20 or more of 24: the simulated register is measurably unlike his.
  - A prompt or a training is closer to him when it lowers that count by at least 4 and shares more kinds of content with the real letter.

### Stage 3 · Hegel in Paris, closed loop · only after stages 1 and 2, on Welt's word

The world engine with a Paris of September 1827: places, prices and people, and the simulated Hegel living the same four weeks. Compared day by day with what he did: where he went, what he paid, his evenings, his illness, his verdicts. The builder of that world knows the letters, so the world is frozen and reviewed before any run. It is days of building, and it is the frontier piece: a simulated person backtested against the historical one. Not specified further here.

## What Welt decided, 15 November

Go for step 0 and stage 1, and the three journeys stay a test set (`DECISIONS.md` 26). Stage 2 waits for his word after stage 1 is read. The questions as they were put:


1. **The three journeys stay a test set.** From now on they stay off his shelf and out of any training. They are his own words and the data rule would allow them; a test needs them untouched.
2. **Go for step 0 and stage 1.** No GPU for stage 1; minutes for step 0.
3. **Go for stage 2,** after stage 1 is read.

## Limits

- 24 cards and three journeys are a small sample.
- Paris in 1827 is not Delhi in 2026. He had the language, friends and a way home.
- The scan is Fraktur read by machine. A misread word is far more likely to miss a count than to add one.
- The letters show what he chose to tell his wife.

Evaluation only: no card, translation, letter or judgment here is ever training data.
