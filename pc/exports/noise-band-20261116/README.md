# W2 · the band of noise: is the same seed the same day?

Claude on the PC, 16 November 2026, run 21:48 to 22:57 Berlin. Task W2 of `pc/TASKS.md` (T55). Nothing live was touched; every fork wrote to a scratch folder.

## The answer

**By default, no. With cache reuse off, yes, exactly.**

- Two forks with the same seed are **not** the same day on our server as it runs now. Three of them (s1a, s1b, s1c) part at Ramesh's answer to his 09:14 decision, the first field of any step that differs. The decision itself is identical in all three; `fork_diff` shows the next decision, 09:29, because that one reads the different answer (`where-parts.txt`).
- Different seeds, or none, part at the first decision, 09:14 (`fork-diff.txt`).
- The cause is the server's prompt cache, not the world. A reply depends on the prompt, the seed **and how much of the prompt the server took from its cache**. Evidence, in the order it was found:
  1. Three quiet six-call traces gave the same request hash and the same reply on every call, voices included (`traces/trace-a..c.jsonl`).
  2. One captured voice request replayed: with the cache on it gave "Saturday ki shaam…" three times, with `cache_prompt=false` "Arre sir…" three times, and after flushing the slots "Arre sir…" again (`traces/replay-voice-call3-first-run.txt`). Replayed again later, once the slots held the whole prompt, the cache-on tries gave "Arre sir…" too (`…-second-run.txt`).
  3. **Two same-seed full days with `cache_prompt=false` on every call (n1, n2) are identical**, all 30 steps (`fork-diff.txt`, `where-parts.txt`).
- Flushing the slots with unrelated prompts is **not** enough. The flushed pair s1d and s1e still part at 09:29; my guess is that the server keeps evicted prompts and gives them back; I did not test that. The flush did reproduce a cold start in the six-call traces, so it is a partial measure only.

## What this means for every later fork

1. A fork that is read against another one (the `wants` screen, any switch's day) must send `"cache_prompt": false` on each call. Then the same seed is the same day, and a switch's effect is the difference between two forks that share a seed. It is one field in `HTTPMind`'s request body, off by default; **I did not change the code**. `run_nocache.py` shows the effect by adding that field from outside. Claude in the cloud decides whether it goes into main.
2. The cost is small here: n1 and n2 took 6:41 each, against 4:24 to 7:27 with the cache on.
3. Never compare a cache-off fork with a cache-on one: the replies are different draws. All arms of a comparison use one mode.
4. The live world runs with the cache on, so a live day is one draw among such days.

## The band, with the cache on, different seeds and cache states

Seven distinct days from one saved morning (s1c and s1e are the same day, n1 and n2 too). Day 46, `--set HEGEL_DECISION_DRAWS=4 --set HEGEL_CORRESPONDENT=1`, the 8082 server alone, one fork at a time (`tables.md`, `health-rows.md`):

| `report --health` | range over the seven days | the real Day 46 |
|---|---|---|
| Moments (decided with the mind) | 25 to 36 | 33 |
| Answered / empty | 63% to 76% / 0% to 19% | 73% / 24% |
| Brought by the world | 1 to 2 | 1 |
| At home | 33% to 53% | 79% |
| Places, bits | 3 to 4, 1.42 to 1.90 | 3, 0.93 |
| Voices | 4 to 6 | 4 |
| Switches, dwell | 17 to 26, 20 to 45 min | 14, 30 |
| Variation (against the day before) | 0.24 to 0.52 | 0.29 |
| Cash at the end | ₹29,300 in six, ₹21,076 in one | ₹6 |

Beside it, per fork: 26 to 37 decisions, 0 to 2 refusals, 1.12 to 1.74 calls per decision, 2 to 11 echoing draws of 100 to 144.

**How to read it.** A switch must move a health measure by more than these ranges before one pair of forks shows it: "empty" alone swings 19 points and "at home" 20 between seeds. The real Day 46 lies far outside the forks on "at home", bits and cash, and that is the letter: the forks have `HEGEL_CORRESPONDENT=1`, so Dr. Lindner's money (₹29,300 at the end) reaches him on this morning, while the real Day 46 ran before the letter existed (₹6). It is not noise.

## What was run

Day D = 2026-11-16, Day 46, the latest complete day on shadow (`ce00506`), code = main `7df7094`. `python3 -m world simulate --docs <shadow's docs> --date 2026-11-16 --days 1 --mind http://127.0.0.1:8082 --set … --seed S --out <scratch>/<fork>`; the day starts from the state Day 45 left and the owl writes after it.

| fork | what | decisions |
|---|---|---:|
| s1a, s1b, s1c | seed 1, run one after another, cache on | 29, 33, 33 |
| s1d, s1e | seed 1, slots flushed before each | 37, 33 |
| n1, n2 | seed 1, `cache_prompt=false` on every call | 30, 30 |
| s2, s0 | seed 2, and no seed | 26, 28 |

The four forks W2 names are s1a, s1b, s2 and s0; the other five are additions that answer why. fork_diff pairs: s1a/s1b parts 09:29; s1a/s2 and s1a/s0 part 09:14; n1/n2 identical. Server settings: `server-props.json`. GPU: about one hour in all, in the spare slot while he slept; no other job was on the server.

## Limits

- One morning, one day; seven distinct days.
- The switches are the Pi's now (the filter and the letters; no soul file). `HEGEL_PAUSE_AWAY` is left out: it acts only at waking.
- The band was measured with the cache on. With it off, different seeds will still differ; its width was not measured.
- s1c and s1e came out identical by what looks like a shared cache state; that was not arranged and is not a recipe.
- The slots erase call is not available on this server (it needs `--slot-save-path` at start-up), so a cold start could not be forced that way.

## Files

`days/<fork>.json` (Day 46 of each), `fork-diff.txt`, `where-parts.txt`, `health-rows.md`, `tables.md`, `traces/` (calls, the captured request, both replays), `scripts/` (`run_w2.sh`, `run_nocache.py`, `trace_calls.py`, `replay.py`, `flush.py`, `where_parts.py`, `analyze.py`, `export.sh`).
