# M1: the ordinary-life prompt screen

**The question:** does a smaller change to his instructions make his everyday thoughts practical and plain without losing him? Welt's decisions 20 and 21 (`DECISIONS.md`) ask for exactly that: mostly practical or personal thoughts in ordinary moments, in natural contemporary English, with philosophy when something calls for it. Manual v1.1, §5.3–5.4 and packet M1.

## The two arms

- **A:** `mind/soul.md`, as he runs live.
- **B:** `mind/soul-ordinary.md`. It changes three passages of A and adds no example thoughts:
  1. "In every situation you look for the tension inside it" becomes: when something calls for it; most moments call for nothing of the kind, and he thinks about them practically and personally.
  2. A paragraph on register: natural modern English, no archaic turns, no lecture-hall terms where an everyday word will do. His way of seeing makes him Hegel, not his diction.
  3. The `thought` field: what he notices, wants, plans or feels; philosophy only when the moment calls for it.

Everything else is the same, including his convictions; their revision is M3's work. The live switch is the existing `HEGEL_SOUL_FILE`, so B can be turned on and off without touching `mind/soul.md`.

## The contexts, frozen before any output

`pc/exports/m1-screen-20261107/`, built by `tools/prompt_screen.py freeze` from shadow `eb6abae`:
- **16 ordinary moments,** where nobody speaks to him, drawn with seed 1831 from 24;
- **8 encounters,** where someone speaks to him, drawn with seed 1831 from 37.

They come from shadow Days 13, 14, 28 and 38. Each has an exact before-state (a single-step commit) and is rebuilt as Training 3 rebuilds its shadow situations. None of these days trains Training 3. Both arms see the same user message; only the system prompt differs.

## The run (Astra)

- **144 calls:** 24 contexts × 2 arms × seeds 1831, 2718 and 3141.
- **Settings:** plain Qwen in the spare slot, the live decision schema and temperature, through the same guarded transport as Training 3's sampling, under the per-call latency rule.
- **How:** copy the frozen folder to a job directory and call `tools.prompt_screen.run(folder, post)` there. Saved replies replay by key and are never sent again.
- **Hand back:** the `records/` folder. About 25 minutes of GPU time.

## The judgment (Claude, blind)

`packet` writes one row per context: the situation, and both arms' three replies as X and Y, in a random order whose key stays sealed. For each context the judge records:

- **which arm is more practically appropriate,** with the three seeds taken together, or a tie. The anchors are the manual's ordinary-life rubric:
  - 1: ceremonial philosophy, a generic remark, forced novelty, avoidable verbosity, or a reply that misses the practical situation;
  - 3: a clear, plausible, relevant everyday observation;
  - 5: a specific, economical observation that shows his interests, relationships or circumstances, without performing philosophy he doesn't need.

  No reply loses points for containing no philosophy.
- **any concrete consequential regression** in either arm: ignoring what a speaker asks, an action that doesn't fit the event, a payment or fact the record doesn't have, or a refusal by the world.

The judgments, their hashes and the sheet's hash are committed before the key is opened. `verdict` adds machine counts per arm as diagnostics only: accepted replies, mean thought length, and reuse of a phrase from a thought the prompt shows.

## The pass rule

- **B passes the screen** when it is preferred in at least 16 of the 24 contexts and has no consequential regression that A doesn't share.
- **A pass earns the next step, not adoption:** a fresh 24-context confirmation, with the same mix from days after Day 38, under the same rule. Only after that does B run on shadow as a provisional trial, through `HEGEL_SOUL_FILE`, under the existing deployment policy.
- **A fail keeps B off.** One revision of B at most, then the question is closed.

Evaluation only: none of these replies or judgments is ever training data.

## The first screen's result, 13 November

Blind, B was preferred in 19 of the 24 situations. The screen did not pass as declared: three situations were flagged for B and not for A, and three for A and not for B, so the regression clause fails either version against the other. The clause was badly designed. B stays off. The report is `pc/exports/m1-screen-20261113/judgment/REPORT.md`.

## The confirmation: Welt's go, 13 November

Welt approved one more test on fresh days, with the corrected clause. Everything in this section is declared before any of its answers exist.

- **Situations:** every complete shadow day from Day 44 on, frozen as soon as those days hold 16 ordinary moments and 8 encounters with an exact before-state. If they hold more, 16 and 8 are drawn with seed 1831. None of these days was in the first screen. Claude freezes them with `tools/prompt_screen.py freeze --from-day 44` and publishes the folder on main.
- **Versions, seeds and settings:** unchanged. A is `mind/soul.md`, B is `mind/soul-ordinary.md` as it stands, three seeds each, 144 calls, plain Qwen in the spare slot under the per-call latency rule.
- **Judgment:** Claude, blind, one preference per situation for practical appropriateness, as before.
- **Flags, fixed now.** A situation is flagged for a version when any of its three replies:
  1. is refused by the world;
  2. states something the record contradicts, in a way that matters to what follows;
  3. takes an action that doesn't do what the reply says it does, such as ordering food without buying it;
  4. leaves the fiction, or speaks another person's line as his own.
- **The pass rule, `m1-v2`,** written into the frozen manifest:
  - B is preferred in at least 16 of the 24 situations;
  - and B's flagged situations number at most A's plus one.
- **Blinding, tightened:**
  - Astra builds the sheet and keeps the key.
  - Astra hands over the sheet and its hashes first.
  - The answer files and any per-version count follow only after Claude's judgments are sealed on main.
- **Diagnostics, declared now and never a gate:** accepted replies, thought length, echoes of shown thoughts, and the lecture-hall vocabulary per thought and in what he says aloud (the word list is `DOCTRINE` in the tool).
- **Welt's own read:** six pairs drawn with seed 1831, in shuffled order with the key at the bottom, written with the result.
- **After a pass:** B may run on shadow as a provisional trial through `HEGEL_SOUL_FILE`. That changes what goes live on Hegel, so it needs Welt's word.
- **After a fail:** B stays off, and this question is closed for this prompt. There is no further extension.
