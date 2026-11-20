# W8's exploratory fork: the adapter deciding, one saved morning

Exploratory, reported apart, never a pass (`DECISIONS.md` 59). W8's defect bars had already failed: in rewrites, the adapter changes facts and decisions (`pc/exports/lora-fresh-scenes-20261119/readers/DEFECTS.md`). The runs are on `codex/adapter-fork-20261121` `d03b175`. The PC seat ran them on the night of 20 to 21 November: the saved morning of Day 51 (shadow `7dfd9bb`), the Pi's switches, the phone cache frozen, cache off.
- **A:** the plain model decides (`HEGEL_DECISION_ADAPTER_SCALE=0`).
- **B:** the Training 1 adapter decides (`=1`).
- Voice and writing were untouched in both.

| seed | arm | decisions | words per thought | lecture-hall terms per thought | places | refusals | calls per decision | spoken lines |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1831 | A | 31 | 63.7 | 0.52 | 2 | 0 | 1.13 | 17 |
| 1831 | B | 19 | 36.6 | 0.11 | 2 | 0 | 1.32 | 3 |
| 2718 | A | 33 | 63.4 | 0.58 | 3 | 0 | 1.12 | 20 |
| 2718 | B | 38 | 37.7 | 0.24 | 3 | 1 | 1.55 | 22 |
| 3141 | A | 27 | 65.7 | 0.52 | 3 | 1 | 1.67 | 12 |
| 3141 | B | 30 | 32.8 | 0.03 | 4 | 0 | 1.40 | 8 |

**What it shows, in three seeds:**
- With the adapter deciding, his thoughts are about **half as long**, and the lecture-hall vocabulary nearly disappears (0.03 to 0.24 per thought, against 0.52 to 0.58). Every seed agrees.
- The days themselves are **unsteady**. Seed 1831's day thins to 19 decisions and 3 spoken lines (below the health floor), while seed 2718 talks more than its plain twin. Calls per decision rise in two seeds of three.
- The forks part at the first step in every seed, as forks of different models must, so the day-level numbers cannot be read pair by pair as effects.

**What it cannot show:** whether those shorter thoughts keep the facts. In rewrites the adapter changed facts substantively in 3 of 24 held-back thoughts, so the plainer register may come with the same cost. Reading the B days for facts against their own record would be the next step, if Welt wants the adapter pursued at all.

Evaluation only: nothing here is training data, and nothing of it reaches his world.
