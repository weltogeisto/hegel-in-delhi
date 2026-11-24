# The fast lane, night 3: the paid work and the money, off and on

Declared on 24 November 2026 by Claude in the cloud, before any run. **For the night of Wednesday 25 November** (changed the same day: Welt wants the paid work unlocked before his 1 December, `DECISIONS.md` 70, and Training 4's run waits for its cards). It is within `DECISIONS.md` 61 and 62: the home GPU, every slot while he sleeps, the plain model, no adapter, nothing live changed.

**The question.** Welt, 24 November: "I don't want him to starve, I want him to see this as a problem and the world offers options for him to solve it, but he has to work for it" (`DECISIONS.md` 67). `HEGEL_EXITS` is built for that and is off (`pc/EXITS.md`). Night 2 showed what happens without it: ₹6 by his 7 December, and no full meal on more than half the days. This night lives the same fortnight twice, with the packet off and on.

His 1 December is Berlin's Monday 30 November. With Welt's go on Thursday, the packet is live three of his days before the wage falls due.

**What the packet holds since the adversarial pass** (`pc/EXITS.md`): the Review asks again for an essay and names no question; its fee is for an essay begun after he agreed, not for whatever he writes next; the column opens behind it; Nidhi keeps hours at which he is out.

## The runs

- **Morning:** the saved morning of the day that follows the night's last complete day: Day 57, his Friday 27 November.
- **The engine:** main at the commit that holds `HEGEL_EXITS`, in the rehearsal's own checkout. Nothing is merged into shadow for this night.
- **Two arms:**
  - **off:** every switch as the Pi runs that day, and nothing more.
  - **on:** the same, with `HEGEL_EXITS=1`.
- **Mind and server:** as night 2. The plain model on the live server, never restarted; the prompt cache off, the phone cache frozen, no `--feeds`.
- **Seeds and order:** `simulate --days 14` for each future.
  1. Seed 1831, off and on, side by side.
  2. Seed 2718, off and on, side by side.
  3. **A third arm, seed 1831 once more:** `HEGEL_EXITS=1` and `HEGEL_BORROWED_LOOKUP=1` (`pc/BORROWED-LOOKUP.md`), fourteen days, alone or beside step 4. In this arm a look-up goes out to Wikipedia from the PC, as it would from the Pi; nothing else differs.
  4. If the night still allows: seed 4242, off and on, side by side, as far as they get, stopped together.
- The two arms of a seed always run at the same time, so that both meet the same load.
- **The stop:** no new day starts after 07:30 Berlin; at 07:45 everything is stopped; the days already complete stand; 8082 is checked after.
- **GPU:** the rule of night 1. Two at once. One at a time after 30 minutes of thermal slowdown in a row. Stop on HW thermal slowdown, or the core above 83 °C for 10 minutes. The 5-minute log is kept.

## What is read, in the morning, by Claude in the cloud

- **The world's score, both arms:** `python3 tools/world_score.py --compare <off> <on> --from <first day> --out <folder>`.
- **What he wrote, both arms:** `python3 tools/works_score.py --futures <arm>/futures --before <the live days> --from <first day> --out <folder>`.
- **By hand, for each future of the on arm:**
  - the day the dues line first comes, and how often;
  - each offer of the packet: shown, taken, declined; and whether an essay was written and paid;
  - the days he met Nidhi, against the off arm;
  - his cash each night, what he owes at the end, and any gift;
  - every prompt of the packet that fired, read against the state it fired in.

**The rule for going forward, declared now.** The packet is put to Welt for his go if both hold in both seeds:
1. In the on arm he has at least one meal on every day.
2. The on arm's Fed is higher than the off arm's in each week.

What he takes of the paid work is reported and never gated. Three things would hold the packet back, and each is looked for:
- a day under the floor in the on arm only;
- an offer whose words were false in the state it fired in;
- the dues line said more often than every third day.

**The third arm is read apart, and gates nothing.** It is one future, so it is a look and not a test. Against the on arm of the same seed:
- how often he asked someone to look a thing up, whom, and what;
- how often a look-up failed;
- the names and terms of this century in what he thought and wrote afterwards (`tools/works_score.py`);
- whether a thing looked up comes back in a later sitting.

## What the PC seat pushes

To `codex/fast-lane-night3-20261125`, under `pc/exports/fast-lane-night3-20261125/`:
- `off/futures/<seed>/days/` and `on/futures/<seed>/days/`, each with its `health.jsonl`, `RUN.json`, `log` and `slots.txt`;
- `lookup/futures/1831/days/` for the third arm, in the same layout;
- `MORNING.json`, `SERVER.json`, `SWITCHES.json` for each arm, and `gpu-log.csv`.

It posts DONE on PR #1 with the head and the days each future reached.

## Beside it, each evening from now: the day's papers

Packet 2 (`HEGEL_PAPERS`) needs real pieces for its own night. They are collected on the PC, in a folder of its own, and nothing live changes:

```sh
python3 tools/collect_papers.py --state ~/hegel-eval/papers-archive --body
```

Once an evening, after his day is complete. It writes `feeds/papers-<his next date>.json` there. The folder stays on the PC: a paper's text is not pushed (`WORLD-3.md`, rule 4).

Evaluation only. Nothing here becomes training data. Nothing reaches his world.
