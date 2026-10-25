# How Claude and Codex work together

Decided by Welt on 12 October 2026: Claude and Codex coordinate through this repository. Welt sets direction and holds the hard limits below. He does not relay messages or approve merges.

## Roles

- **Codex (on the PC):** everything that needs the 3090, the PC or the Pi. That means runtime changes, test runs, blind packets and the shadow world.
- **Astra (on the PC), from 25 October 2026:** holds the seat Codex held, decided by Welt. Wherever this file says Codex, read Astra. Astra may continue on `codex/outcome-memory` and PR #1.
- **Claude (in the cloud):** specs, code that needs no GPU, reviews, blind scoring, the scoreboard and merges to main.
- **Hermes (on the Pi):** only if Codex cannot reach the Pi.
- **Welt:** direction and the hard limits. Nothing else waits on him.

## Channels

| What | Where | Written by |
|---|---|---|
| Tasks, in priority order | `pc/TASKS.md` on main | Claude writes and merges; Codex updates the status lines on its branch |
| Codex's work | branch `codex/outcome-memory`, draft PR #1 | Codex |
| Codex's status | `pc/CODEX-STATUS.md` on that branch | Codex |
| Messages | comments on PR #1 | both, results not narration |
| Numbers | `pc/SCOREBOARD.md` on main | Claude |

Every push to PR #1 and every comment on it wakes Claude, and every wake is expensive. So both comment only for one of three things:
- **Done:** a task finished, with its commit and numbers.
- **Blocked:** exactly what is needed.
- **Question:** something the other must decide.

No start, progress or "still running" comments. A comment is at most six lines, and details go in a file on the branch. Claude replies only when Codex must change something, and mirrors it into `pc/TASKS.md`, so the task list alone is enough for Codex.

## Codex's day

Welt starts one Codex session a day, in Codex's normal permission mode, with one standing line: "Work through pc/TASKS.md under COLLABORATION.md until everything is done or blocked." In that session Codex repeats four steps:

1. Merge `origin/main` into `codex/outcome-memory`.
2. Take the highest open task marked for Codex in `pc/TASKS.md`.
3. Do it, push, and update `pc/CODEX-STATUS.md` and the task's status line.
4. Comment on PR #1 with the result: commit, numbers, next.

Then it takes the next task. Codex fetches origin between tasks, so tasks Claude adds during the day reach it without Welt.

## The list never runs dry

Decided by Welt on 13 October 2026, after Codex paused with an empty list just as the first full day arrived and Welt had to wake it.
- **After every full shadow day** (the owl has written), Claude reads the day, the owl and the morning status, and writes the next tasks in `pc/TASKS.md` before the next waking day. When nothing needs doing, Claude still writes the review with its findings and "no new task".
- **Codex does not pause on an empty list.** It comments once on PR #1, "list empty, waiting for Day N's review" (a Question), keeps the shadow world watched, and fetches origin again at least every two hours until a task appears.
- **The morning status counts refusals.** `python3 -m world status` prints how often the world refused his choices and the refusal that came most often; four or more of the same in a day is flagged "a loop?". Codex quotes a flagged line in its next PR #1 comment.

## Authority

- **Claude merges to main without asking** when two things hold:
  - the full suite passes;
  - for any change to his prose or thinking, the scoreboard number on the same frozen inputs is not worse. That's the ratchet.
- **Codex may run anything on the PC and the shadow world's Pi** within the hard limits. It pushes to `codex/*` branches and never to main.
- **The shadow world runs main's code.** Codex may update and restart it.

## Hard limits: these need Welt

- training, or changing adapters;
- the public world on `main` (the shadow world is fine);
- deleting data or history, including force-pushes;
- the firewall, power settings, ML packages and secrets;
- spending money.

## Failures

A failure is work, not a stop:
- Diagnose, fix and rerun, up to five rounds per task per day.
- If a task hits a hard limit or five rounds fail, mark it `BLOCKED` in `pc/TASKS.md` with exactly what is needed, and move to the next task.

## Judging

- **Blind.** Codex shuffles the texts, hides every label and keeps the key apart.
- **Scores before key.** Claude commits its scores with their hash before it sees the key; then Codex pushes the key to `mind/results/<review>/key.json`.
- **Grok is optional.** Use it for a second opinion on large decisions, not in the daily loop.

## The day's summary

At the end of each day Claude posts one short comment on PR #1: what landed on main, what the numbers did, what is blocked. That comment is all Welt needs to read.
