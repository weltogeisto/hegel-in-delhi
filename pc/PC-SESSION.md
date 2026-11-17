# Claude on the PC

**Welt, 15 November 2026:** Claude on the PC takes the seat Astra held: the PC, the 3090, the Pi and the shadow world. Claude in the cloud keeps the specs, the reviews, blind scoring and the merges to main. Where `COLLABORATION.md` says Codex or Astra, read Claude on the PC.

Read first: `COLLABORATION.md` (roles, channels, hard limits), `DECISIONS.md`, then `pc/TASKS.md`.

## The limits

- **Never without Welt's word:** training or adapters, deleting data or history, force-pushes, the firewall, power or driver settings, network changes, new ML packages, secrets, spending, the public world on main, and anything new going live on Hegel beyond what `DECISIONS.md` already approves.
- **The data rule:** training data comes only from Hegel's own texts, the local model's outputs chosen by fixed rules, or Welt's judgement. Nothing written or chosen by Claude, GPT or Codex. Evaluation material never becomes training data.
- **Nights (`DECISIONS.md` 30):** work that trains nothing may run while Hegel sleeps, in the spare slot only, stopping cleanly by 08:30 Berlin, with one line on PR #1 in the morning.
- **Blind tests:** the key stays apart until Claude in the cloud has sealed its judgments on main.
- **Git:** your work goes to a `codex/*` branch, never to main. Shadow is the Pi's branch: you merge main into it and push it.

## Reporting

Comments on PR #1, at most six lines, only for **DONE** (with commit and numbers), **BLOCKED** (exactly what is needed) or **QUESTION**. No progress notes. Every comment wakes Claude in the cloud.

## First job: the letter from Munich (`DECISIONS.md` 33, Welt's go)

0. Read PR #1. If Astra has already posted DONE for the correspondent, go to step 4.
1. On the Pi, merge `origin/main` into shadow. There is one conflict, the import line in `world/__main__.py`. Resolve it to:
   `from . import nightly_report, pause, report, shelf, works`
2. **Check the merge:** in a worktree of the merge, run `git checkout origin/main -- docs`, then `python3 -m unittest discover -s tests`. Everything must pass. Run in place, the tests fail: they read `docs/` as fixtures, and shadow's `docs/` holds the live record (PR #1, 15 November).
3. Push shadow, and add `HEGEL_CORRESPONDENT=1` to the Pi's env file.
4. Comment DONE on PR #1 with the shadow SHA and the time it went on. When her letter comes, comment again with the time it came and the money it brought.

## Next

- `HEGEL_PAUSE_AWAY=1` may go on at any time (`DECISIONS.md` 32).
- After the letter's first full day: `HEGEL_SOUL_FILE=mind/soul-ordinary.md` (`DECISIONS.md` 34).
- Then work through `pc/TASKS.md` from the top, under `COLLABORATION.md`, until everything is done or blocked.
