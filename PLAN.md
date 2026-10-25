# The season plan

Written by Claude on 25 October 2026, at Welt's request: get Hegel running, excelling and learning, with Claude and Astra doing the work together.

The idea in one line: **Hegel lives every day in public, for months, and gets better at being himself.** He improves three ways: through what happens to him, through what we learn from watching him, and through training on his best days.

Think of it as a theatre run. The shadow world is the rehearsal. The public switch is opening night. The months after are the run, where the role deepens. Each act ends at a gate with numbers, and the next act opens only when the gate passes.

## Where we stand

- **What works.** The world engine (789 tests), the Pi ticking every half hour, an owl that writes faithfully from the record, the live page with the Day 1 replay, the fan club, and a fallback that keeps the household going without a mind.
- **What is fragile.** The mind is a hand-started server on a Windows PC. One Windows restart cost Day 13. The pause for Welt's holiday never happened, so Days 15–24 ran without a mind: 0 thoughts, three meals a day, home all day. They stay in the record as they are.
- **What is thin.** Since the shadow began, exactly one day ran complete with a working mind: Day 12. Everything we know about quality rests on that day and on rehearsals.
- **Known gaps.**
  - Repetition: 69% of Day 12's thoughts reuse an earlier phrase, against 48% in rehearsals.
  - Convictions move too easily: `state` changed status on about half of all nights (T8).
  - Commitments, his own positions, score far below the real Hegel in blind review: 2.0–2.8, against 4.65 for his own passages.
  - The first adapter did not beat plain Qwen.
- **The economy.** He has no income yet. ₹3,251 in cash lasts about two weeks at ₹1,800 a week (groceries and the dhobi). On Ramesh's day off, a Hegel without a mind goes hungry (Day 20).

## Act 0 · Lights on (25–26 October)

**Goal:** the mind runs, stays up, and someone knows within an hour when it does not.

- **Astra:** the mind back on the GPU, its speed checked, natural ticks from source `mind` (T16).
- **Welt:** the Administrator click for Astra's installer. The mind then starts by itself after a reboot, and Windows stops restarting the PC at night.
- **Claude:** the watchman (T17). An hourly GitHub check on the shadow branch opens an issue, which GitHub emails to Welt, when three waking steps in a row ran without a mind.
- **Claude:** `python3 -m world report` (T18). One row per day: thoughts, quiet steps, refusals, repetition, meals, cash, places, people and theses. It is the daily scoreboard row.

**Gate:** 24 hours with at least 95% of waking steps from the mind, and the watchman proven on Day 13's record.

## Act 1 · Dress rehearsal (the first seven full days after Act 0, about 27 October – 2 November)

**Goal:** seven days in a row that we would be proud to show.

**Gate, on every one of the seven days:**
- at least 30 thoughts;
- quiet steps at most 5% of waking steps;
- the owl writes every night;
- no refusal loop (four or more of the same refusal);
- the truth audit no worse than baseline: at most 1.6 contradictions and 3.1 statements as fact per 100 sentences;
- repetition measured.

**Work:**
- **Repetition (T10).** Measure the first full day. Above 55%, Claude writes the variant: his recurring phrases of the day, shown back to him as already said. Astra runs it blind, and the ratchet decides.
- **Economy (T20).** Claude runs 21 days with the stand-in mind to show where the money comes from and where it goes. It checks that the offers that bring money in (lessons, a talk, a commission) actually reach him. The world must make earning possible, never force it. The fallback also learns Ramesh's day off: he eats at Khan Market.
- **Convictions.** After the week, count the status changes. If `state` still flips on about half the nights, Claude writes the slower rule (two nights agreeing) and Astra runs it blind.
- **Every night:** the report runs after the owl (T19), and Claude's review (T11) follows before the next waking day.

## Act 2 · Opening night (target: early November, once Act 1's gate passes)

**Goal:** the live page shows his real days.

- **Welt decides:**
  - the public switch;
  - how the PC lives: always on, or asleep with wake-on-LAN (the original design, 15–25 wakes a day). On Delhi time his waking day runs 00:30–17:30 Berlin, which overlaps your own hours at the PC.
- **Astra:** clock shift to 0, the Pi to `main`, the first public day watched.
- **Claude:** the page for opening night.
  - "Previously": the owl's last night, in two lines.
  - An about panel: the rules, and who is invented.
  - Sharing tags: image and title.
  - The Day 1 replay, kept as an archive.
- **Welt:** shares the link; the fan club counts.

**Gate:** the first public week without an outage longer than an hour.

## Act 3 · The run: learning (from November)

Three loops, at three speeds.

1. **Daily: he learns from his life.**
   - His memory carries from day to day: people remember him, and he them.
   - Storylines move: the Hegde file, the Directorate, his money.
   - Convictions change only for reasons the record can show.
   - Measured by a cross-day truth audit (contradictions with earlier days) and by the callbacks to earlier days in each day.
2. **Weekly: the ratchet.** One experiment closes every week. Claude writes the change, Astra runs it on frozen inputs, and Claude scores it blind. Main takes it only if the number is not worse. The queue, in order:
   1. the repetition variant;
   2. slower convictions;
   3. **his convictions in the persona.** In T4c–e this method raised commitments on the Karl letters from 2.00 to 2.83. It extends one conviction at a time (the state, the family, religion, history, art), each tested on fresh controls. This is the strongest lever found so far.
   4. typed records for the Depesche only. T3 showed that they help there: statements as fact fell from 14 to 4.
3. **Monthly: the mind learns.** Each training run needs Welt's go. This is the second attempt at Hegel's own adapter.
   - **Data:** his books, as continued pretraining, plus his best real days. Those are accepted decisions from the run, selected by the world's own checks: accepted, no contradiction, repetition below the median.
   - **Never by Claude:** the selection does not use Claude's judgments, and no example is written by Claude (the rule in `mind/train/README.md`).
   - **Adoption:** only if it beats plain Qwen with the current persona on the scoreboard and on the Hegel test.
   - **Volume:** the run makes the data. A month of days is about 1,200 decisions.

**Gate:** the scoreboard, for every loop.

## Later

Fans on his rounds (needs a read key on the Pi, installed by Welt); the Saturday Depesche for fans who ask for it; the larger owl at night; the Hegelizer.

## Who does what

- **Welt:** direction and the hard limits. The decisions in this plan:
  1. the Administrator click, today;
  2. how the PC lives during the run;
  3. the public switch, when Act 1's gate passes;
  4. each training run;
  5. the fans' read key, after opening night.
- **Astra (PC and Pi, the seat Codex held):** the mind, the shadow world, the runs, the blind packets and the training runs.
- **Claude (cloud):** specs, code that needs no GPU, the watchman, the reports, blind scoring, the scoreboard, the daily review and merges to main.
- **Channels, unchanged:** `pc/TASKS.md` for tasks, PR #1 for done, blocked or a question (six lines at most), `pc/SCOREBOARD.md` for the numbers.

## The rhythm

- **Daily:** a tick every half hour; the owl at 01:30 his time; the report; Claude's review before the next waking day; the watchman every hour.
- **Weekly (Sunday):** one experiment closes; the scoreboard updates; a one-page note for Welt.
- **Monthly:** the training decision.
