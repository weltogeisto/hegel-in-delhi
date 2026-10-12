# Tasks

Rules: `COLLABORATION.md`. The top open task for each owner comes first. Status is one of `OPEN`, `RUNNING`, `DONE` (with commit and numbers) or `BLOCKED` (with what is needed).

## Monday 12 October

The goal for today is that Hegel lives his first real day tonight. Delhi midnight is 18:30 UTC (20:30 Berlin). Everything that passes the ratchet today is on main by then.

### T1 · Codex · check in · OPEN
Read `COLLABORATION.md` and this list, then comment on PR #1 that you are working through it.
Yesterday `pc/CODEX-STATUS.md` was root-owned in your checkout (PermissionError). Your repository is yours to repair: give the file back to your user, or else keep your status in PR #1's comments.
**Done when:** that comment is on PR #1.

### T2 · Codex · Hegel lives tonight: the shadow world · BLOCKED: needs Hermes
07:33 UTC: the Pi refuses the PC's `gondolin_key` for `pi` and `hendrik`. Hermes does Task 6 on the Pi; Claude gives Welt the message. Codex's part stays open:
1. **First, before T3:** post the public half of the key in a PR #1 comment (`ssh-keygen -y -f <gondolin_key>`, the one `ssh-ed25519 …` or `ssh-rsa …` line, never the private file). Claude puts it at `pc/keys/codex-pc.pub` on main, and Hermes adds it to the Pi, so from then on the Pi needs no relay.
2. Plain Qwen3.8-27B on PC port 8082, no adapter, main's settings: it is his mind and the owl for the world (the Pi gets `MIND_PORT=8082`, `OWL_PORT=8082`). It must come back after a reboot without a login, like the "Hegel mind" task in `pc/CODEX.md`, and answer `/health` on the PC's LAN address. If port 8082 has no firewall rule, that part is `BLOCKED: needs Welt`. Tests share this server through spare slots, never by stopping it.
3. Once your key works on the Pi (try the user who owns `~/hegel-in-delhi` there), you look after the shadow world: `python3 -m world status` each morning, logs on failure.

**Done when:** `origin/shadow` exists, the timer is running, and steps appear after 18:30 UTC.

### T3 · Codex · records without the checker · OPEN
The second smoke test showed the typed records help: 3 contradictions fell to 1 and 7 statements turned into fact fell to 2. The claim checker, meanwhile, misjudges sentences and makes a day more than three times slower.
1. Runtime = the typed records and the repairs at 5a1833f, plus a **compact evidence view**, with the **claim check off**. **Claude has written the compact view:** branch `claude/compact-view` (on top of your 8f56420), switched on by `HEGEL_EVIDENCE_VIEW=compact` together with `HEGEL_OUTCOME_MEMORY=1`. Merge it into `codex/outcome-memory` first. It groups the day's records into facts, payments, said (not verified), plans (not done) and drafts (not sent), without record ids, in at most 9,000 characters; facts and payments are never cut. No whole generation prompt may be larger than the baseline maximum, 7,263 tokens; the character cap alone does not guarantee that, so enforce it on the whole prompt.
2. **Fix the day, vary the writer.** On 6 saved days, run the owl and any writing sittings with the old input (A) and the new runtime (B), three fixed seeds each. The six are the 4 smoke days (both arms of smoke-v1 and of the fresh smoke) plus 2 distinct 8 October rehearsal days; record the six before generating.
3. Make a blind packet of the outputs for Claude: prose, the day's records and random ids. The key stays apart until Claude's scores are committed.
4. Report the wall time per variant.

**Passes when:** B has fewer statements turned into fact and no more contradictions per 100 sentences, and its wall time is no more than 1.2 times A's. Then switch the records on by default in your branch; Claude merges.

### T4 · Codex · shelf test: the Nuremberg addresses · OPEN
OLD = the shelf at c03a431; NEW = the shelf on main now (adds `reden`). Take the Karl-letter situation from blind review v2 (case "karl"), arm A0 (plain Qwen, no adapter), the engine's normal writing path with the shelf on. Run 10 seeds with OLD and the same 10 with NEW.
1. Record which shelf passages each prompt held, and how many NEW prompts held a `reden` passage.
2. Make a blind packet of the 20 letters for Claude, with the v2 guide. The key stays apart.

**Baseline** (v2, Karl letters, all arms): commitments 2.15, argument 2.00. **Passes when:** NEW beats OLD on commitments by at least 0.5 and argument is not lower. This run is cheap, so fit it in while T3 runs.

### T5 · Claude · score, merge, scoreboard · RUNNING
Score every blind packet within the hour it lands, commit the scores with their hash, merge whatever passes, and keep `pc/SCOREBOARD.md` current.

## Parked
- Faster rehearsals (MTP speculative decoding): only if rehearsal time becomes the bottleneck. A day takes 14 minutes without the checker.
- The Hegelizer and any training: hard limit.
