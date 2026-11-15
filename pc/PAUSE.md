# A pause for his world when the PC is away

**Why.** From 8 to 13 November the PC was off. His world ran on without a mind: Days 39 to 43 have no thoughts, and their costs, dates and plot ran on regardless. Welt's go, 15 November (`DECISIONS.md` 32).

## What `HEGEL_PAUSE_AWAY=1` does

1. **Only his waking asks for the PC.** At night he sleeps and needs no mind. When the step that is due is his waking and the PC does not answer, his world is held at the start of that day, asleep. Nothing runs: no steps, no costs, no plot, no owl. `pause.json` in the state folder records the hold.
2. **Each tick tries the PC again,** as before, through the wake script or the health check.
3. **When the PC answers, he lives the held day.**
   - Back the same morning: he wakes late, as after any gap, and nothing trails.
   - Back days later: his calendar trails Delhi's by those whole days from then on. Say he was held on the 20th and the PC returns at 08:00 on the 23rd: his world resumes on the 20th at 08:00 and wakes him at his usual time.
4. **Whole days keep his hours with the PC's.** His day is nine to nine, the PC's twelve hours. A trail of hours would push his waking day into the PC's night, and it would grow every day.
5. **The page follows.** The trail reaches it through the clock shift in `index.json`, which it already reads.

**What it doesn't change.** If the PC leaves in the middle of a day, the rest of that day runs as it always has: he goes home, eats and rests without thoughts. If the PC is still away at his next waking, the hold comes then. With the PC there, the gate is only the clock and writes nothing (`tests/test_pause.py`).

**What the trail means.** His dates fall behind Delhi's by the days the PC was away. The news on his morning step is still the day's real news. The weather comes from the forecast service for his date, which also covers recent past dates. The fixed dates in his plot fall on his calendar, not Delhi's.

## When it goes on

It acts only when the PC is away at his waking, so it changes nothing on a normal day and does not muddle the reading of the other changes. Astra may switch it on now, with the next pull of main.
