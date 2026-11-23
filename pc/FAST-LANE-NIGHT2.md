# The fast lane, night 2: his future, two times forty-odd days

Declared on 23 November 2026, about 20:00 Berlin, by Claude in the cloud, before any run. This takes up the idea Welt kept on 21 November (`DECISIONS.md`, ideas: "his future, fifty days in a row") and his question of 23 November: "don't we want to run 100 Hegel days during the night?". It is within `DECISIONS.md` 61 and 62: the home GPU, every slot while he sleeps, the plain model, no adapter, nothing live changed.

**A look ahead, not a gate.** One night of runs cannot answer what only time breaks. Two futures lived straight through can:
- Does his money run out? He has ₹15,456, an IIC cheque he cannot cash without a bank account, and the museums cost about ₹300 a day.
- Does the file's story move? Shri Hegde's letter, Mr. Saxena, Mr. Malhotra.
- Does he repeat himself?
- Do the museums wear off?
- Does any day thin out or fail?

## The runs

- **Morning:** the saved morning of Day 55, his Wednesday 25 November. These are the docs on shadow at the commit that marks Day 54 complete, tonight after about 21:00 Berlin.
- **Switches:** every switch as the Pi runs on Day 55, `HEGEL_KEEP_TIME` and `HEGEL_FILE_ACT` included, set with `--set`.
- **Mind and server:**
  - The plain model on the live server, never restarted.
  - The prompt cache off, the phone cache frozen, no `--feeds`.
- **Two futures:** `simulate --days 60` from that morning, one with seed 1831 and one with seed 2718, each in its own folder and its own slot, run side by side. Each day ends with the owl, as a rehearsal does.
- **The stop:**
  - No new day starts after 07:30 Berlin.
  - At 07:45 both are stopped. The days already complete stand; the one in progress is dropped.
  - 8082 is checked after.
- **GPU:** the rule of night 1 stands. Two at once. One at a time after 30 minutes of thermal slowdown in a row. Stop on HW thermal slowdown, or the core above 83 °C for 10 minutes. The 5-minute log is kept.

## What is read, in the morning, by Claude in the cloud

For each future, day by day:
- the health row: moments, brought, empty, at home, places, voices, variation from the day before, kinds and pairs already seen;
- his cash at night, and what he spent;
- the beats that fired (the file's doors, offers, the IIC);
- the file's line;
- days under the floor;
- the owl's diary: written or failed.

Reported as two curves side by side, with the day each one first shows:
- his cash under ₹2,000;
- a week with no beat fired;
- variation under 0.2 for three days running;
- a day under the floor;
- the owl failing.

No pass and no fail: what it shows goes to Welt, and the money and the story are his to steer.

## What the PC seat pushes

To `codex/fast-lane-night2-20261123`:
- `futures/<seed>/days/` and each day's health row;
- `RUN.json`, with the commit, the model's sha256, the server's argv, the switches, the seed, the start and end, and the days completed;
- `gpu-log.csv`.

It posts DONE on PR #1 with the head and the days each future reached.

Evaluation only. Nothing here becomes training data, including the draws that `HEGEL_KEEP_DRAWS` writes inside a rehearsal. Nothing reaches his world.
