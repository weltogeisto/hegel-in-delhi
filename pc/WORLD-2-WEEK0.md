# The world, phase two: week 0

Welt's go, 16 November 2026 (`DECISIONS.md` 36). Week 0 of `WORLD-2.md` builds the instrument before anything it measures. No GPU. Nothing live. Every change is additive and off by default.

The packets below are built by agents on Sonnet 5.5 and checked by Claude in the cloud (`COLLABORATION.md`). The PC seat's part is at the end.

## Rules for every packet

- **A day with every new switch off is byte-for-byte the day main gives.** The rehearsal test and the full suite prove it.
- **Standard library only** in `world/`. `world/` does not import from `tools/`.
- **A read, never a gate.** Nothing in week 0 names a target for him or scores his thoughts.
- **Nothing written by Claude or by an agent reaches his prompt** except through a switch that is off, and a switch goes on only after its screen on the PC and Welt's word.

## A1 · the health of the world, as a module

`world/health.py` holds what `tools/world_health.py` holds today; the tool becomes its command line. The doctrine count stays in the tool, which passes its pattern in.

A row keeps every field it has, and Day 12 keeps its pinned numbers. It gains:

| Field | What it is |
|---|---|
| `switches` | how often the act of a moment differs from the act of the moment before |
| `place_switches` | the same for the place |
| `dwell` | for each act, the median minutes of an unbroken run of it; `dwell_all` over every run |
| `kinds` | what the day brought, by kind (below), sorted, each once |
| `act_places` | the pairs of act and place he chose, sorted, each once |

Across the full days of a set, in order (`across(rows)`):

| Field | What it is |
|---|---|
| `variation` | the Jensen–Shannon divergence, in bits, between this day's minutes by act and the last full day's. 0 is the same day again; 1 is nothing shared |
| `kinds_seen` | the share of this day's kinds that an earlier full day already had |
| `kinds_seen_5` | the same, looking only at the five full days before |
| `acts_seen`, `acts_seen_5` | the same for his pairs of act and place |

The first day of a set has no value for these.

**What opened a moment.** A step may carry `opened`, a list the engine writes (A2). Health reads it when it is there and falls back to the event's words when it is not, so the recorded days keep their numbers.

| In `opened` | Label |
|---|---|
| `beat:<id>`, `offer:<id>`, `session:<id>`, `papers`, `listings`, `post`, `stranger:<id>`, `greeting:<id>`, `power`, `rain`, `air`, `sight`, `part`, `street:<id>` | brought |
| `reply` or `read`, and nothing brought | answered |
| nothing | empty |
| anything else: `arrive`, `wake`, `here` (someone he knows comes into sight), `closing`, `closes`, `meal`, `tea`, `kitchen`, `hunger`, `felt`, `purse`, `late` | routine |

A day's `kinds` are its brought entries with a date after `@` cut off. From words alone the kinds are: the beat's id, `papers`, `listings`, `post`, `stranger`, `power`, `rain`, `air`, `greeting`.

`python3 -m world report --health` prints the rows from the day files; `--floor N` lowers the count of thoughts that makes a full day, for a stand-in's shorter days.

**Done when:** the ten tests pass unchanged in meaning; new tests cover each new field, `across`, and a step with `opened`; `python3 tools/world_health.py --ref origin/shadow` prints the old columns and the new.

## A2 · the engine says what opened a moment, and counts its offers

`World.situation()` already builds each moment from a list of events. Each event gets a kind from the table above, and the step records the list as `opened`. A greeting adds `greeting:<id>`, the reply `reply`.

**The funnel.** For every offer and beat, the day file counts under `funnel`: `live` (on this day its conditions held, his place and its people aside), `eligible` (the moments he decided at which it could fire), `shown` (it fired), `yes` and `no` (its choice). An offer that is live for days and never eligible is one he never walks into. A session of a standing engagement is counted apart from the offer that made it, as `session:<id>`.

Both are additive fields. Nothing he is told changes. `tests/test_rehearsal.py` and a new byte-for-byte test on a stub day (ignoring the two new fields) prove it.

## B · the rehearsal learns the calendar and the switches

- **`simulate --days N`.** One folder, one engine, N days in a row, the owl after each. A stand-in month takes under a minute.
- **The world as the tick builds it.** One function builds the world for `tick` and for `simulate`. `--set KEY=VALUE`, repeated, sets any `HEGEL_` switch for the rehearsal (`--set HEGEL_CULTURE=1`).
- **`--docs FOLDER`.** A rehearsal may start from another rehearsal's folder. That is a fork: the same morning, two futures.
- **Four stand-ins.** `--mind stub` is today's and unchanged. `stub:no` declines every choice. `stub:home` leaves home only for what he has booked. `stub:walker` goes out whenever a place is open, to the place he has seen least. All deterministic.
- **Seeds.** `HTTPMind` takes a base seed (`HEGEL_SEED`, `--seed`). With one, every call sends a seed derived from the base and the call's number. Without one, the payload is what it is today.
- **`tools/fork_diff.py A B`.** Compares two folders day by day: the state, then each step's decision. It names the first moment they part and ignores the stopwatch (`mind.latency_s`).

**Done when:** two stand-in forks of the same morning with the same arguments are identical under `fork_diff`; a thirty-day `stub` rehearsal with culture and the correspondent on runs through; `tests/test_rehearsal.py` passes untouched.

## C · what he wants (T69)

Behind `HEGEL_WANTS`, off. The decision gains an optional field, `wants`: one line, at most 160 characters, or null. The instructions gain one sentence when the switch is on: he may name something he wishes this city had or allowed, and nothing follows from naming it.

- **No effect.** The world reads `wants` into the step and into the day file's own list (`wishes`: time, place, the line). It changes nothing else, and reaches none of his later prompts. A wish is never answered, granted or refused by code in week 0.
- **The ledger.** `python3 -m world wishes [--since DATE]` prints it for Welt, by day.
- **The screen, for the PC seat.** The sentence changes his prompt, so it runs through the M1 procedure on frozen situations: the arm without it twice (the band of noise), the arm with it once. Bars are declared in `pc/WANTS-SCREEN.md` before the run: accepted answers, echo share, lecture-hall terms per thought, each within the band; and how many decisions carry a wish.

## D · what the voices say, counted (rule 7)

`tools/voice_claims.py` draws 100 recorded replies from shadow's days (seed 1831), each with what he said, the moment, and the record up to it. Two readers, working apart, list each reply's claims about the world: a promise, an appointment, a price, a fact about a third person, something that happened. Each claim is marked: the record holds it, the record is silent, the record says otherwise. Claude settles what the readers disagree on and checks twenty by hand.

The same pass lists every promise a voice made, and what the record shows became of it.

The report (`pc/exports/voice-claims-20261116/REPORT.md`) gives the counts and names their limits. It is what T57's arms are sized against. If the failure is rare, T57 shrinks.

## E · the file's next act (T56)

`pc/FILE-NEXT-ACT.md`: Claude's draft, for Welt's pen. The Hegde file as a thread with months in it, several ways out and none chosen. The beats are in `plot.json`'s form and stay out of `plot.json` until Welt has edited them.

## For the PC seat, when week 0's code is on main

1. **The band of noise (T55).** From one saved shadow morning, two forks with nothing changed and different seeds, one day each; then two with the same seed. Report what `fork_diff` and the health row say of each pair. This is the measure every later fork is read against.
2. **The `wants` screen (T69),** as `pc/WANTS-SCREEN.md` declares it.
3. **The health row in the nightly report (T54):** `python3 -m world report --health` beside the day's row.

None of the three changes anything live.
