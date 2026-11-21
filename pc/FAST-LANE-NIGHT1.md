# The fast lane, night 1: what the museums do to a day

Declared on 21 November 2026, about 20:40 Berlin, by Claude in the cloud, before any run. This is the order the fast lane's v2 asked for (`pc/FAST-LANE.md`), within `DECISIONS.md` 61: the home GPU only, the plain model, no adapter, nothing live changed.

**A measurement, not a gate.** `HEGEL_CULTURE=1` goes on before Day 53 by Welt's word (61), so no result here switches it off or on. The night is for three things:
1. Learn what the museums do to his day now, from many days at once, rather than from the live days one by one.
2. Make the arm without the museums the control that the next switches are read against.
3. Give the live days a distribution to fall inside or outside of.

v2's `HEGEL_VOICE_REPAIRS` arm is dropped: it failed W9 (`pc/exports/voice-repairs-check-20261120/reading/RESULT.md`).

## The runs

- **Mornings:** the saved mornings of Days 50, 51 and 52. These are the docs on shadow at the commits that marked Days 49, 50 and 51 complete. Their dates are Friday 20, Saturday 21 and Sunday 22 November, all days the four venues are open.
  - Day 53's morning is not used, because Day 52 lost eight hours.
- **Arms:** `HEGEL_CULTURE=0` and `=1`. Every other switch is as the Pi runs on Day 53, set with `--set` as in the exploratory fork of 20 to 21 November.
- **Mind and server:**
  - The plain model on the live server, which is never restarted.
  - The prompt cache is off (`--seed` does it).
  - The phone cache is frozen, and `--feeds` is not used.
- **Code:** the code Day 53 runs (main as merged into shadow at 21:15). If the merge is blocked, the night uses main at `387d7959`.
- **Seeds:** 1831, 2718, 3141, 1618, 1414, 1732, 2236 and 2645. The same eight are used in both arms.
- **Total:** 3 mornings × 2 arms × 8 seeds = 48 one-day runs.
- **Order:**
  - Seed by seed, and within a seed morning by morning.
  - For each morning the two arms run back to back: off then on for even seeds in the list, on then off for odd ones.
  - A night cut short therefore leaves both arms balanced.
- **Concurrency:** one run at a time, in the spare slot. If Welt says yes to every slot while he sleeps, as many runs at once as the server has slots, but only after the noise band below is measured at that concurrency.
- **First, the noise band:** the saved morning of Day 51, seed 1831, `HEGEL_CULTURE=0`, twice, compared with `tools/fork_diff.py`. If the two days match, same-seed pairs hold at this concurrency. If not, the night is read unpaired, which v2 assumes anyway.
- **Stops:**
  - No run starts after 07:30 Berlin, and every run is stopped by 07:45.
  - 8082 is checked after the last run.
  - If the live server dies, it is started only by its Windows starter, and the night is posted as BLOCKED.

## What is measured (declared now, read in the morning by Claude in the cloud)

From each run's health row (`python3 -m world report --health`) and its day file:

- **Primary: the share of his moments at home.** The live days run 33 to 53% at home, and the museums are the world's first reason to go far.
- **Secondary:**
  - moments brought per day; the empty share; place entropy (`place_bits`); voices per day; switches and dwell
  - moments, with days under the floor of 20 thoughts counted and named
  - cash spent (the imprest at the start less at the end)
  - calls per decision and refusals
  - his steps at the four venues: galleries seen, performances attended, tickets bought
- **How it is reported:**
  - For each morning and arm: the median, the interquartile range and the range.
  - On against off: the difference of means, with a 95% bootstrap interval resampled within mornings, and the probability that an "on" day exceeds an "off" day of the same morning.
  - A profile for each seed. A day that changes regime (most of it away, or most of it at home) is named, not averaged away.
- **What it can see:** about 24 days against 24, with a between-seed SD of about 5 points in a share. That makes a difference of about 4 points visible (80% power, two-sided 5%). A smaller one would not show.

## The live days as smoke tests

- **Day 53, Monday 23 November in his calendar:** the National Museum, the Gallery of Modern Art and Kamani are closed that day. Only the Habitat Centre is open, with its vocal recital. Day 53 therefore shows the listings and little else.
- **Day 54, Tuesday 24 November:** the first live day with all four open. It is read against the "on" arm, inside its range or outside it. One day is not evidence of an effect.

## What the PC seat pushes

Everything goes to `codex/fast-lane-night1-20261121`:
- **For each run:** `runs/<day>-<arm>-<seed>/`, holding its day file, its health row and `RUN.json`. `RUN.json` gives the commit, the model's sha256, the server's argv, the concurrency, the cache flag, the seed, the morning, the switches, the start and end, and the GPU minutes.
- `runs.jsonl`, one line per run.
- The noise band's `fork_diff` output.

The PC seat posts DONE on PR #1 with the head and the number of runs. Nobody on the PC reads the days for a verdict.

Evaluation only. Nothing here becomes training data, including the draws that `HEGEL_KEEP_DRAWS` writes inside a fork. Nothing reaches his world.
