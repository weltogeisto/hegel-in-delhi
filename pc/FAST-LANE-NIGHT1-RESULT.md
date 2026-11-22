# The fast lane, night 1: what the museums do to a day

Read by Claude in the cloud on 22 November, at about 01:30 Berlin, as `pc/FAST-LANE-NIGHT1.md` declared. A measurement, not a gate: the museums are on by Welt's word (`DECISIONS.md` 61). The runs are on `codex/fast-lane-night1-20261121` (`7ec53428`). The full tables are in `pc/exports/fast-lane-night1-20261121/read-block1/RESULT.md`.

## Block 1: 48 one-day runs, the museums off and on

Three saved mornings (Days 50, 51 and 52: Friday, Saturday, Sunday) and eight seeds an arm. All 48 runs were complete: no day under the floor, none failed.

**1. He goes.** On 19 of the 24 days with the museums on, he reaches at least one venue:
- the National Museum on 11 days, the Gallery of Modern Art on 4, Kamani on 4, the Habitat Centre on 3;
- 3 galleries a day on average, up to 9;
- a performance on 4 days.

**2. The world brings him more.** Moments the world brought rose from 5.1 a day to 8.1 (+3.0; 95% interval +1.8 to +4.2; an "on" day exceeds an "off" day of the same morning 83% of the time).

**3. At home, the primary measure: probably less, and not shown.** It fell from 55% of his moments to 48% (−6.8 points; 95% interval −14.8 to +1.2). The interval reaches zero, so this night cannot tell the drop from chance.
- The drop sits on the weekend mornings, when he otherwise stays in. Medians: Saturday 82% → 68%, Sunday 52% → 38%.
- On the Friday he was out most of the day anyway (29% → 30%).

**4. He spends more.** From ₹174 a day to ₹545 (+₹371; 95% interval +₹157 to +₹579): tickets, the Habitat's food, the way there. Over weeks this matters to his purse. At this rate a month costs about ₹16,000, close to the ₹17,900 he held on Day 51's evening. The money story should be watched once the museums are on.

**5. A little more of the lecture hall.** Doctrine terms per thought rose from 0.64 to 0.80 (+0.16; 95% interval +0.03 to +0.30). The galleries give him something to philosophise about. Stage 1's question is whether art returns to what he writes, and the owl's evenings will show it.

**6. Nothing else moved.** Unchanged:
- the moments of the day
- the empty share
- the voices that spoke
- refusals
- calls per decision

He changes act a little less often (−2.2 a day), as a man in a gallery would. Days at the extremes (at home for 80% or more of his moments, or 20% or less) were 6 without the museums and 2 with them.

## The noise band, and what it changes

Two runs from Day 51's morning, seed 1831, started together with a third slot busy, parted at the first decision (09:14). With several runs sharing the server, the batch changes the numbers, so a seed does not fix a reply. Pairs, and with them seed streams (`HEGEL_SEED_STREAMS`), hold only for runs made one at a time. Tonight's runs are read unpaired, as declared.

## The GPU

The core peaked at 66 °C (median 63.5 °C), drawing up to 342 W. Twice, in single one-minute samples, the card set its software thermal slowdown with the core cool. That is the memory, which nvidia-smi does not report on this card, protecting itself. From 00:32 the runs went 2 at a time instead of 3. Whether to cap the power, and to check the memory temperature with HWiNFO, is Welt's call.

## Smoke test for the live days

**Day 54** (his Tuesday 24 November) is the first live day with all four venues open. Day 53 is a Monday, when three of the four are closed. Day 54 is read against the "on" arm, inside its range or outside it. One day is not evidence.

Blocks 2 (the file's next act) and 3 (more seeds) follow below when they land.
