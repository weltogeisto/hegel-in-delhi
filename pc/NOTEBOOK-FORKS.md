# The notebook's forks, declared before any output

Declared on 18 November by Claude in the cloud, and read by the phase-two session as a second pair of eyes. It tests `HEGEL_NOTEBOOK` (`pc/NOTEBOOK.md`, `DECISIONS.md` 56) before any trial on shadow. Nothing goes on shadow from it.

## The run (the PC, in its spare time)

- **The morning:** the first complete shadow day D after the museums' first full day, with every switch shadow runs on D. Its docs are copied from the Pi after D's bedtime step.
- **Two days per fork,** so that the night between D and D+1 writes the first notebook and D+1 lives with it: `python3 -m world simulate --docs <shadow's docs> --date D --days 2 --mind <server> --seed S --set HEGEL_NOTEBOOK=<0|1>`, plus a `--set` for every live switch. No `--feeds`, scratch folders only. `--seed` turns the prompt cache off.
- **Seeds:** 1831, 2718, 3141, 4253 and 5167, each with the notebook off and on: twenty days of the card, about two and a half hours.
- **First, the same-seed check:** seed 1831 with the notebook off, twice, then `tools/fork_diff.py`. If the two runs part, all ten still run, and the bars are read five against five.

## The measures, on D+1, where the notebook acts

1. Lecture-hall terms per thought (`tools/prompt_screen.py`, `DOCTRINE`).
2. The notions of his system per 100 words (`tools/travel_register.py`, the English list), as the phase-two session asked: the notebook puts his own summary in front of him every day.
3. Echoes of a shown thought, steps with a refusal, calls per decision.
4. The day's health row (`python3 -m world report --health`).
5. The notebook itself: its length, and whether the owl's knowledge gate sent it back.
6. **Reported, with no bar:** how often a thought on D+1 names something that appears in the notebook but not in D+1's own events, which is the reaching back the notebook is for.

## The bars

**It passes if, on D+1:**
- the mean of the five forks with the notebook lies no higher than the highest of the five without it on measures 1, 2 and 3;
- every one of the five notebooks passed the knowledge gate.

**If it passes,** a trial on shadow follows, on Welt's word, in its place after the file's next act. **If it fails,** it stays off, and the result says on which measure.

Evaluation only: no notebook, day or result here is ever training data.
