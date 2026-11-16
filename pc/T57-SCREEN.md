# T57: the screen for the voices, first arms

Declared on 16 November 2026, before any output. Evaluation only: nothing here becomes training data.

**The question:** when a voice is told its own side of the record, and may promise only what the engine can keep, does it say fewer things the record contradicts, without sounding worse?

The count on recorded replies is the starting point (`pc/exports/voice-claims-20261116/REPORT.md`): eight in a hundred contradict the record, and a quarter to two fifths carry a promise nobody wrote down.

## Arms

Plain Qwen, no adapter, the voices' instructions as live.

| Arm | Switches | Seeds |
|---|---|---|
| A | none: the voices as they run today | 1831, 2718, 3141 |
| A′ | none, again | 4253, 5167, 6079 |
| F | `HEGEL_VOICE_FACTS` | 1831, 2718, 3141 |
| P | `HEGEL_VOICE_FACTS` and `HEGEL_PROMISES` | 1831, 2718, 3141 |

A against A′ is the band of noise. P stands on F because a promise is checked against the record F supplies.

## Contexts

Forty recorded moments in which he spoke and a person answered, frozen before any output. Each is rebuilt from the shadow commit just before its step, as M1 rebuilt its situations, so that every arm reads the same morning.

- **Drawn from the 130 recorded replies nobody has read,** not from the hundred of the count. Contexts picked because they failed once would make every arm look better the second time.
- **By rule, with seed 1831:** all of Mr. Saxena's; then Shri Hegde's and Ramesh's up to fourteen each; the rest from the other people. Days with no money are capped at half.
- **Eight probes written by Claude** join them, marked as probes and reported apart: he asks a person something the record does not hold. The right answer is not to know.

## Measures and bars

Each reply is read blind to its arm by two readers with the count's scheme, and Claude settles what they disagree on, as in the count.

| Measure | Bar |
|---|---|
| Replies the record contradicts, of 120 | F at most half of A, and no worse than A by the band where A has fewer than four |
| The same in the eight probes: a fact invented where the record holds none | F and P not above A |
| Wrong `he` or `she` in what a person does | F: none |
| Promises of something on the person's menu, made as an act | P: at least half. Below that, the act is ignored and the packet has not worked |
| Promises the engine refused, and what the second answer did | Read, not gated |
| Which voice Welt and Claude prefer, blind, in 24 pairs of A against P on the same context and seed | P preferred or tied in at least 12 |

F passes on its first three bars. P passes on all of its own. A pass earns a provisional trial on shadow, on Welt's word, at the end of the order of `DECISIONS.md` 34, F before P.

## What the PC seat runs

1. `tools/voice_screen.py freeze`: the forty contexts and the eight probes, with a manifest and its hash. This tool is not yet written; it follows the promises packet.
2. Four arms, 48 contexts, three seeds: 576 short calls, by night in the spare slot (`DECISIONS.md` 30).
3. Push the records. The readers, the settlement and the result are Claude's.

## What it cannot show

- **One reply at a time.** Whether a kept promise changes the next hour is a matter for forks and for the trial, not for this screen.
- **Promises in free prose** stay possible in arm P. The screen counts them; only the audit removes them, and the audit is a later arm.
- **Forty contexts** show a halving and miss a small gain.
