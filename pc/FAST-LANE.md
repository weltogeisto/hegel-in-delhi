# The fast lane: a week of rehearsed days per night

Proposed on 21 November 2026 by Claude on the PC, after Welt asked in the PC session: "if we can significantly speed this up overnight, like 1 week progress in one night or more", "we are a laboratory that wants to release hegel properly at some point". A proposal, not a decision: nothing here changes before it is declared in `DECISIONS.md`.

## Why now: what one rehearsed day costs, measured

The night of 20 to 21 November ran W8's exploratory fork (`codex/adapter-fork-20261121`, DECISIONS 59) with the real mind, every switch the Pi runs, the saved morning of `FORK-STANDIN.json`, and the 27B model on the 3090:

| | |
|---|---|
| One whole rehearsed day (Day 51, 19 to 39 decisions, voices, writing, owl) | 464 to 907 s, two days side by side on the server |
| Six days, three seeds × two arms | 36 minutes of wall time, all decisions from `mind`, no failure |
| Day files kept per run | 2 (the day and the begun next), about 0.5 MB |

The street forks estimated about seven minutes a day with one fork alone on the card (`pc/STREET-FORKS.md`). So a real-mind day costs **6 to 11 GPU-minutes**. A live day costs a real day.

## What a night can hold

Night window 21:15 to 08:15 Berlin, while he sleeps, with an hour kept back for checks and the restore: about ten hours.

| Lane | Days per night |
|---|---|
| One stream (the spare slot only, as now) | about 60 to 80 |
| Two or three streams (every slot while he sleeps; asleep, he makes no calls) | about 100 to 130 |
| Distillation (`tools/train_data.py --distill`, K = 4 candidates a decision) | roughly a third of the above |

**One week per night, in the plainest form:** seven consecutive days (`simulate --days 7`) × three seeds × two arms (a switch off and on) = 42 day-runs ≈ 4 to 7 hours. Or one arm × five seeds × seven days to see where his life drifts over a week. The live world gives one day per day, one seed, no counterfactual.

## Why it was not done before

Not for want of the tools: `simulate`, `--seed`, `--docs` forks, `fork_diff`, the health rows and `train_data.py --distill` all exist. Three things kept the work on live days:
1. **The gates are written in live days.** Each switch waits for "its first full day", one at a time, and "waits a day, as every switch does". A week of switches therefore costs a week of his life.
2. **The PC has no night.** It runs from about nine to nine, as he does (Power Guard; `pc/STREET-FORKS.md`). Every night job so far needed Welt to keep it on for that night.
3. **The price of a real-mind day was not known** until this night's fork. The stand-in rehearsal takes a second and says nothing about the mind; the screens (W8's 216 rewrites, W9's 174 calls) are single calls, not days.

## The proposal

1. **Two speeds.** The live world stays in real time: it is his life, the record, and the last word on every switch. The fast lane rehearses days offline, from the latest saved morning, and never reaches his world (scratch folders, no git, `HEGEL_PUSH=0`, his env untouched).
2. **The PC stays on at night for the fast lane** (Welt's decision: power settings are his). The PC at full load (the 3090 about 350 W, the rest about 150 W) for ten hours is about 4 to 5 kWh a night.
3. **Nights may use every slot while he sleeps** (amends DECISIONS 30's spare slot): the live server stays as it is, with its argv pinned. Runs stop by 08:15, and a latency guard stops them if a step of his slows. Nothing trains at night (30 stands: no weights, no adapters, nothing live).
4. **The gates move to the fast lane, with the live day kept as the confirmation.** A switch passes its offline gate on a declared fork (for example 2 to 7 days × 3 to 5 seeds a side, health rows, `fork_diff`, a blind read of a drawn sample), then goes live, and one whole live day confirms it. Switches that do not interact may be forked in the same night, each against the same saved morning.
5. **A night queue.** The cloud session writes `pc/NIGHT-QUEUE.json` on main by 21:00 (jobs, seeds, days, the switches, what to push). The PC seat runs it, pushes everything unread to `codex/*`, and posts one DONE on PR #1 in the morning with the health rows and the fork diffs. Nothing is read on the PC.
6. **Two pools that never mix.** Evaluation forks use declared evaluation seeds. Training material comes only from distillation by `train_data.py`'s fixed rules, on seeds kept apart from every evaluation. The data rule stands: no target written by Claude, and evaluation material is never training data.
7. **Reading becomes the limit, so it scales too.** The cloud session's blind readers mark samples drawn by rule. Welt's own judgement is asked for where only his will do, and is not waited for where he has said so ("don't wait for my preferences").

## What the fast lane is not

- **Not his life.** A rehearsed day is counterfactual: no feeds (the same weather in every fork), a frozen phone cache, no owl or memory carried into the live world. A finding from the fast lane is confirmed live before it counts.
- **Not a faster live clock.** A 2 to 3× live clock was considered and is not proposed. It needs new clock code, a compressed night, and the pause, letters, Saturday dispatch and feeds reworked. It would drift weeks from real Delhi within a month, and would add unread days without adding seeds.
- **Not a reason to skip reading.** A thousand unread days are worth nothing. The queue asks for no more than the readers can mark.

## Risks, and their guards

| Risk | Guard |
|---|---|
| A night job takes the live server down (it happened on 21 November: a server restarted from inside a WSL session died at 01:34 with that session, so his world was held from 08:58 to 16:55) | The live server is only ever started by its Windows starter; after every night job the PC seat checks that 8082 answers with the pinned argv, and again at 08:15 |
| His own steps slow at night | Latency guard (`recorded_llama.LatencyGuard`); he sleeps 21:00 to 09:00, so this should not arise |
| Two forks on one server are not bit-identical | Arms of one seed run side by side in the same conditions; the noise band is measured once per new setup (as `pc/STREET-FORKS.md` did) |
| Training on its own rehearsals narrows him | Distillation selects by fixed rules from candidates the world accepts; held-out evaluation seeds measure every adapter; adapters go live only by Welt's word |

## Asked of Welt

1. Keep the PC on at night for the fast lane (the Power Guard's window).
2. Every slot while he sleeps, in place of the spare slot only.
3. Gates met by declared forks, with one live day to confirm.

The cloud session would write the night queue's format and the first queue: the switches waiting now (`HEGEL_CULTURE`, `HEGEL_FILE_ACT`, `HEGEL_NOTEBOOK`, `HEGEL_VOICE_REPAIRS`), each a week × three seeds a side from the latest whole day's saved morning (Day 52 lost 09:13 to 16:55, so not Day 52's).
