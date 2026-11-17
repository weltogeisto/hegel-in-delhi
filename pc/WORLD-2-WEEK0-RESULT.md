# The world, phase two: what week 0 gave

16 November 2026. Week 0 of `WORLD-2.md`, on Welt's go of the same day (`DECISIONS.md` 36). Nothing here is live on him.

**In one line:** the world can now be measured, rehearsed a month in half a minute and forked from one morning. Its first readings say where phase two should begin: with what people promise, and with a home in which nothing happens.

## What stands

| Piece | Where | State |
|---|---|---|
| The world's health: how each moment opened, switches, dwell, variation, how much of a day was seen before | `world/health.py`, `python3 -m world report --health` | Built |
| The engine says what opened each moment, and counts each offer: live, eligible, shown, yes, no | `opened` on a step, `funnel` on a day | Built. Ten stand-in days equal the earlier code's, hash for hash, with the two fields removed |
| The rehearsal: N days in a row, any switch, a fork from another rehearsal, a base seed, four stand-ins | `python3 -m world simulate --days N --set … --docs … --seed … --mind stub:walker` | Built. Thirty days in 23 seconds |
| Two rehearsals compared | `tools/fork_diff.py` | Built. Two forks with the same arguments are identical |
| What the voices say, counted | `pc/exports/voice-claims-20261116/REPORT.md` | Done |
| The file's next act | `pc/FILE-NEXT-ACT.md`, checked in `research/FILE-NEXT-ACT-CHECK.md` | A draft for Welt. Not in `plot.json` |
| What he wants | `HEGEL_WANTS`, `python3 -m world wishes`, `tools/wants_screen.py`, `pc/WANTS-SCREEN.md` | Built, off. The screen is declared and not run |

The suite has 1,226 tests and passes. `python3 -m world check` is ok.

## First reading: the same month, four ways

Thirty days from 3 October with the museums and the letters from Munich on, lived by four stand-ins. A stand-in is a fixed rule, not him. It shows what the world gives to a way of living, and nothing about his thoughts.

| Stand-in | Empty moments | Brought, a day | At home | Kinds seen before | Cash at the end |
|---|---:|---:|---:|---:|---:|
| Says yes to every offer | 33% | 3.2 | 50% | 80% | ₹9,902 |
| Says no to every offer | 36% | 2.6 | 50% | 80% | ₹12 |
| Stays at home | 56% | 1.4 | 99% | 91% | ₹12,341 |
| Goes out whenever he can | 32% | 3.8 | 39% | 84% | ₹6,412 |

- **Home is the empty place.** A man who stays in meets 1.4 things a day, and more than half his moments open on nothing. The world's events live outside and wait to be walked into. For the stay-at-home the frock coat's buyer was live on 27 days and never met; the file's query was live on 13.
- **The world repeats within a month.** Whatever he does, four fifths or more of what a day brings, an earlier day already brought.
- **Every rupee he earns is an offer.** The man who says no ends the month with ₹12.
- **Going out helps, and only so far.** The walker meets 3.8 things a day against 3.2. More walking does not make a fuller world.

His own days say the same from the other side. On Day 47, the first with money after the letter from Munich, he was at home in 10% of his moments up to the late afternoon, and the world had brought him five things. On Day 46, with ₹6, he was at home in 79% and it brought one.

## The count: what the voices say

Of 100 recorded replies, eight contradict the record, five of them on something he could act on: the file, money, an hour, a role. Between 26 and 38 carry a promise nobody wrote down. Of eleven promises that name a time or a deed, one was kept. Shri Hegde is told nothing of his own situation and speaks as a man who drives in from an office; he lives in the second bedroom.

So T57 keeps its size, and its order is clear: promises first.

## The band of noise, measured by the PC seat the same night

From one saved morning, seven days with nothing changed (`pc/exports/noise-band-20261116/README.md` on `codex/pc-seat-20261116`):

- **The same seed is the same day only with the server's prompt cache off.** With it on, a reply depends on what the server happened to hold. With it off, two days were identical over all 30 steps. Forks that are compared now send it off.
- **Unchanged days differ widely:** empty moments from 0 to 19%, at home from 33 to 53%, 25 to 36 moments. So one pair of forks shows only a large effect. A switch is read over five seeds a side or more.

## What this changes in the plan

Nothing in the order of `WORLD-2.md`, and three things inside it:

1. **Weeks 1 and 2 start with promises** as records, before acts and slots. With them come two cheap repairs: what the record holds about Shri Hegde reaches his voice, and every person in the cast is `he` or `she`.
2. **The street comes home.** The first batch of the street deck needs cards that happen at the bungalow: a caller at the gate, a neighbour, a delivery, a sound from the road. A deck that lives only outside leaves the emptiest place empty.
3. **Repetition has a number now.** The share of a day's kinds seen before is the measure the street and the second ring are read against: 80% and more today.

Each waits for Welt's word, as weeks 1 and after do.

## For the PC seat, once this is on main

1. **The band of noise.** One saved shadow morning, two forks with nothing changed and different seeds, then two with the same seed, a day each. Report `tools/fork_diff.py` and `world report --health` for each pair.
2. **The health row in the nightly report:** `python3 -m world report --health`.
3. **The `wants` screen,** after Welt has read the sentence: `pc/WANTS-SCREEN.md`.

This branch reaches main only by a pull request, which Welt has not asked for.

## For Welt

1. **The file's next act:** seven calls in `pc/FILE-NEXT-ACT.md`. Best before his 20 November; later does no harm.
2. **The sentence for `wants`,** in `pc/WANTS-SCREEN.md`.
3. **An adapter's day by fork** (`DECISIONS.md`, still open): possible now, not advised for the Training 1 adapter.
4. **Weeks 1 and 2,** with the three changes above.

## Limits

- **A stand-in is not him.** The table says what the world holds for a rule, not what he would do. His own eight full days stand beside it in `tools/world_health.py --ref origin/shadow`.
- **A stand-in's day is short,** about eighteen moments, so its days count from eight thoughts and not from twenty.
- **One month, one seed of the world.** The four runs share the weather and the calendar of one October. The numbers are a first reading, not a rate.
- **Kinds are coarse in recorded days.** Days written before today carry no `opened` list and are read from their words, so a gallery or a sight counts as routine there.
- **The count's limits** are in its report: two readers of one kind, a sample heavy with Ramesh and with days without money.
