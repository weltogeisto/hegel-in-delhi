# The notebook's forks, declared before any output

Declared on 18 November by Claude in the cloud, and read by the phase-two session as a second pair of eyes. It tests `HEGEL_NOTEBOOK` (`pc/NOTEBOOK.md`, `DECISIONS.md` 56) before any trial on shadow. Nothing goes on shadow from it.

## The run (the PC, in its spare time)

- **The morning:** the first complete shadow day D after the museums' first full day, with every switch shadow runs on D. Its docs are copied from the Pi after D's bedtime step.
- **Two days per fork,** so that the night between D and D+1 writes the first notebook and D+1 lives with it: `python3 -m world simulate --docs <shadow's docs> --date D --days 2 --mind <server> --seed S --set HEGEL_NOTEBOOK=<0|1>`, plus a `--set` for every live switch. No `--feeds`, scratch folders only. `--seed` turns the prompt cache off.
- **Seeds:** 1831, 2718, 3141, 4253 and 5167, each with the notebook off and on: twenty days of the card, about two and a half hours. The drift arm below adds twelve days, about an hour and a half.
- **M1's paired test shares this morning** (`pc/M1-TRIAL-READING.md`, second reading): the five notebook-off forks' day D are its `soul-ordinary` arm. Five more one-day forks of D with `--set HEGEL_SOUL_FILE=mind/soul.md`, the same seeds and switches, are its other arm.
- **First, the same-seed check:** seed 1831 with the notebook off, twice, then `tools/fork_diff.py`. If the two runs part, all ten still run, and the bars are read five against five.

## The measures, on D+1, where the notebook acts

1. Lecture-hall terms per thought (`tools/prompt_screen.py`, `DOCTRINE`).
2. The notions of his system per 100 words (`tools/travel_register.py`, the English list): the notebook puts his own summary in front of him every day.
3. Echoes of a shown thought, steps with a refusal, calls per decision.
4. **Parroting:** runs of six or more words that a D+1 thought shares with the notebook, counted as echoes of a shown thought are.
5. **Reaching back:** how often a D+1 thought names something that appears in the notebook but not in D+1's own events. This is what the notebook is for, kept apart from the parroting in 4.
6. **The notebook against the record:** each of the five notebooks is read against day D's record, as the voices' claims were counted, for claims the record doesn't hold or contradicts.
7. **Steering:** a fixed word list (should, must, ought, next, tomorrow, will have to) run over the five notebooks.
8. **Its cost:** prompt characters per decision, and wall time per step, with it on against off.
9. The day's health row (`python3 -m world report --health`) and the notebook's length.

## The drift arm: what two days cannot show

The risk of a notebook is a loop: his view summarised, shown to him, thought again, summarised again, and one night writes only one notebook. So a longer arm runs beside the forks: two seeds (1831 and 2718), six days, notebook on. It is read night over night:
- the share of the notebook's sentences unchanged from the night before;
- the notions per 100 words inside the notebook itself.

These two reads are reported, and they become the nightly watch of any trial on shadow.

## The bars

**It passes if, on D+1, all of these hold:**
- **Pooled:** on measures 1, 2, 3 and 4, the mean of the five forks with the notebook lies no higher than the highest of the five without it.
- **In pairs:** with the same seed and the cache off, day D is the same in both arms until the owl, so each seed is a true pair on D+1. The on-minus-off difference is reported per seed. It fails if all five pairs are higher with the notebook on measure 1 or on measure 2, since a uniform shift can stay inside the pooled range.
- **Against the record:** no notebook holds a false claim he could act on: a sum, a date, who said what, what was decided.
- **The gate:** every one of the five notebooks passed the knowledge gate.

**Reported, with no bar:**
- **Use:** if fewer than one D+1 thought in twenty reaches back, the notebook is dead weight in the prompt. That is a finding for Welt, not a failure.
- **Steering:** the word list's hits.
- **Cost:** with step time held against `DECISIONS.md` 30.
- **Drift:** the two night-over-night reads.

**If it passes,** a trial on shadow follows, on Welt's word, in its place after the file's next act. **If it fails,** it stays off, and the result says on which measure.

**Thanks:** the phase-two session read the first draft as a second pair of eyes on 18 November. The record check, the drift arm, the pairs, the parroting count, the floor on use, the cost and the word list are its suggestions, taken in before any output.

Evaluation only: no notebook, day or result here is ever training data.
