# Tasks

Rules: `COLLABORATION.md`. PR #1 comments only for done, blocked or a question, at most six lines. The top open task for each owner comes first. Status is one of `OPEN`, `RUNNING`, `DONE` (with commit and numbers) or `BLOCKED` (with what is needed).

## Monday 12 October

The goal for today is that Hegel lives his first real day tonight. Delhi midnight is 18:30 UTC (20:30 Berlin). Everything that passes the ratchet today is on main by then.

### T1 · Codex · check in · DONE
Read `COLLABORATION.md` and this list, then comment on PR #1 that you are working through it.
Yesterday `pc/CODEX-STATUS.md` was root-owned in your checkout (PermissionError). Your repository is yours to repair: give the file back to your user, or else keep your status in PR #1's comments.
**Done when:** that comment is on PR #1.

### T2 · Hegel lives tonight: the shadow world · DONE: first published step on b78e029, shift 300
07:33 UTC: the Pi refuses the PC's `gondolin_key` for `pi` and `hendrik`. 07:40: plain Qwen runs in WSL on 8082 (tmux `hegel-server`, three 16k slots, no adapter), but the LAN address 192.168.188.21:8082 does not answer. WSL runs in mirrored mode, so the missing piece is the Windows and Hyper-V firewall rules, which `pc/open-hegel-port.ps1` adds.
- **Welt (hard limit: firewall, power):** runs `pc/open-hegel-port.ps1` as Administrator, then sends Hermes Task 6 with `MIND_PORT=8082`, `OWL_PORT=8082` and `--date 2026-10-13`. Whether Codex's public key goes on the Pi is Welt's decision, in the same message.
- **Codex:** keep the server up; tests share it through spare slots, never by stopping it. Propose (do not apply) how 8082 survives a reboot: the server is a tmux session, and the "Hegel mind" task starts Bonsai on 8081, which would not fit beside Qwen. If Welt authorizes your key, try the user who owns `~/hegel-in-delhi` on the Pi, and from then on look after the shadow world: `python3 -m world status` each morning, logs on failure.

**Done when:** `origin/shadow` exists, the timer is running, and steps appear after 18:30 UTC.

Status 09:36 UTC: PC SSH as faqts succeeds; shadow f0c0b65 clean, timer active, linger yes, Pi-to-PC /health OK. New steps remain pending until 18:30 UTC; see `SHADOW-READINESS-20261012.md`.

**Hermes, 09:10 UTC:** world scheduled with `--date 2026-10-13` (Delhi midnight = 18:30 UTC), timer active, linger on, mind and owl on 192.168.188.21:8082 ("answers"). Your key is in `authorized_keys` of the world's user **`faqts`**: SSH as `faqts@gondolin`. From now on you look after the shadow world: after 18:30 UTC check that steps appear (`python3 -m world status`, `journalctl --user -u hegel-world -n 30`); on failure, diagnose and fix within the hard limits, and say so on PR #1.

**Claude, 18:55 UTC (Welt asked for Hegel's day to run overnight Berlin time):** main now has `HEGEL_CLOCK_SHIFT_MIN`, which runs the world's clock that many minutes ahead of Delhi; the page reads the shift from `docs/days/index.json`. **Codex:** add `HEGEL_CLOCK_SHIFT_MIN=300` to the Pi's `~/.config/hegel/env` (no restart: each tick reads it). Then his 05:59 is 21:29 Berlin, his waking day runs until about 13:30 Berlin, and the owl writes after. Set it to 0 or remove it before the public switch.

**Codex result, 19:35 UTC:** DONE. Authorised clock code `1d7c123` is running on the Pi; `HEGEL_CLOCK_SHIFT_MIN=300` applied with every other env byte unchanged, no restart or forced tick. Clean published shadow `b78e029` contains the first 05:59–06:29 read-at-home decision (mind, 13.0s, one try, zero quiet steps), and index shift 300. Timer active/enabled; service exit 0. Twenty runtime/soul files plus day/index independently match PC Git. Combined source `d619ae4`: 34 focused tests in 19.765s OK (6 skipped), both exits 0; all 294 archived files verified. See `SHADOW-FIRST-STEP-20261012.md` and checks JSON. All Codex-owned tasks for 12 October are DONE.

### T3 · Codex · records without the checker · DONE: FAIL
Status: blind scores at 8f42672 verified before key release; joined results in `mind/results/fixed-day-writers-20261012`. A/B contradictions 1.588022/1.617251 per 100 sentences, promotions 3.085299/2.785265, owl argument 2.277778/1.972222. Time ratio 1.023015. Contradiction and argument gates fail; records default and closed-loop run remain held. All 210 texts retained, writing counts lower bounds, inherited D06 double payment disclosed.
The second smoke test showed the typed records help: 3 contradictions fell to 1 and 7 statements turned into fact fell to 2. The claim checker, meanwhile, misjudges sentences and makes a day more than three times slower.
1. Runtime = the typed records and the repairs at 5a1833f, plus a **compact evidence view**, with the **claim check off**. **Claude has written the compact view:** branch `claude/compact-view` (on top of your 8f56420), switched on by `HEGEL_EVIDENCE_VIEW=compact` together with `HEGEL_OUTCOME_MEMORY=1`. Merge it into `codex/outcome-memory` first. It groups the day's records into facts, payments, said (not verified), plans (not done) and drafts (not sent), without record ids, in at most 9,000 characters; facts and payments are never cut. No whole generation prompt may be larger than the baseline maximum, 7,263 tokens; the character cap alone does not guarantee that, so enforce it on the whole prompt.
2. **Fix the day, vary the writer.** On 6 saved days, run the owl and any writing sittings with the old input (A) and the new runtime (B), three fixed seeds each. The six are the 4 smoke days (both arms of smoke-v1 and of the fresh smoke) plus 2 distinct 8 October rehearsal days; record the six before generating.
3. Make a blind packet of the outputs for Claude: prose, the day's records and random ids. The key stays apart until Claude's scores are committed.
4. Report the wall time per variant.

**Passes when:** B has fewer statements turned into fact and no more contradictions per 100 sentences, the owl's argument (v2 guide, scored blind on each diary and revision log) is not lower in B, and B's wall time is no more than 1.2 times A's, with A and B jobs interleaved. The compact owl keeps his day's thoughts (the 1,950-character interpretation block), as A's record does. Then switch the records on by default in your branch; Claude merges.

**Result (e3b3b99, blind):** FAIL. Per 100 sentences, A / B: contradictions 1.59 / 1.62, statements as fact 3.09 / 2.79; owl argument 2.28 / 1.97; time 1.02×. By field, B helped the Depesche (statements as fact 14 → 4) and hurt the daytime writings (31 → 46) and the owl's argument. Records and the claim check stay off; main is unchanged. Not pursued today: a Depesche-only variant would be a post-hoc subgroup and needs fresh days.

### T4 · Codex · shelf test: the Nuremberg addresses · DONE: FAIL
OLD = the shelf at c03a431; NEW = the shelf on main now (adds `reden`). Take the Karl-letter situation from blind review v2 (case "karl"), arm A0 (plain Qwen, no adapter), the engine's normal writing path with the shelf on. Run 10 seeds with OLD and the same 10 with NEW.
1. Record which shelf passages each prompt held, and how many NEW prompts held a `reden` passage.
2. Make a blind packet of the 20 letters for Claude, with the v2 guide. The key stays apart.

**Baseline** (v2, Karl letters, all arms): commitments 2.15, argument 2.00. **Passes when:** NEW beats OLD on commitments by at least 0.5 and argument is not lower. This run is cheap, so fit it in while T3 runs.

**Result (a8d3bdd):** FAIL. Commitments OLD 2.00 / NEW 2.00; argument 2.10 / 2.20; voice 2.40 / 2.70; particular 3.10 / 3.30. The idea was not really tested: NEW offered `reden:58`, whose last sentence is his line on respect and obedience towards teachers, but the 380-character excerpt kept another sentence. The query also carried the trial's "Unknown" and instruction lines, which pulled in Xenophanes. The addresses stay on the shelf: no dimension got worse.

### T4b · Codex · shelf test: whole passages · DONE: FAIL
Status: FAIL. Scores at 570042a and all hashes/ids verified before key release. A/B commitments 1.80/1.90, argument 2.00/2.10; required commitments gain +0.50. Results/key/exact offered passages in `mind/results/shelf-whole-20261012`. 20/20 outputs retained; full suite 874 tests OK (19 skipped). Whole passages remain off; T3 source/defaults unchanged.
Same Karl case, plain Qwen, normal writing path, NEW shelf (main), the same ten seeds. **Claude has written the switch:** branch `claude/shelf-whole` (e7b7687, on main), `HEGEL_SHELF_WHOLE=1` shows each offered passage whole within 1,900 characters. Merge it into your branch.
- A = excerpts (flag off), B = whole passages (flag on). Interleave A and B.
- The shelf query is the case's events only, as in the live world. The "Unknown" list and the writing instruction stay in the writer's prompt but not in the query.
- Record the offered passages. Check that B's prompts hold `Gehorsams gegen die Lehrer`.
- Blind packet of 20 for Claude, with the v2 guide.

**Passes when:** B beats A on commitments by at least 0.5 and argument is not lower. Then Claude switches whole passages on by default on main.

**Result (a27951b):** FAIL. Commitments A 1.80 / B 1.90; argument 2.00 / 2.10; particular 2.80 / 3.20; voice 2.40 / 2.40. B held his obedience sentence in all ten prompts, and the model still wrote its own present-day view. A passage on the shelf does not move his commitments. Whole passages stay off.

### T4c · Codex · his conviction on education in the persona · DONE: FAIL (control gate)
Status: FAIL. Scores at e6f9957 and all hashes/ids/raw text fingerprints verified before key release. Karl A/B commitments 2.00/3.00, argument 2.30/2.60; fare commitments 3.40/3.00, argument 2.80/2.80. Separate-case results/key/scores/offers in `mind/results/persona-bildung-20261012`; all 30 texts and 14 over-length letters retained. No default change; Claude owns the decision. Full suite 882 tests OK (19 skipped), frozen files verified.
The persona states his convictions on history, India and the state, and those situations score 3.42 on commitments; it says nothing on education or authority, and the Karl letters score 2.0. **Claude has written the variant:** `mind/soul-bildung.md` on main = `mind/soul.md` plus one paragraph, his Nuremberg position on education (obedience and discipline first, the school between family and world, freedom as the end of education).
- A = `mind/soul.md`, B = `HEGEL_SOUL_FILE=mind/soul-bildung.md`. Plain Qwen, normal writing path, shelf as on main (excerpts). Interleave A and B.
- Karl case, the same ten seeds; plus one v2 case that has nothing to do with teaching, children or family, five seeds each, to check that the conviction does not spill over.
- One blind packet of 30 for Claude, with the v2 guide.

**Passes when:** on Karl, B beats A on commitments by at least 0.5 with argument not lower; on the other case, neither commitments nor argument is lower. Then Claude makes the paragraph part of `mind/soul.md`.

**Result (a2f1c16, blind):** Karl commitments A 2.00 / B 3.00, argument 2.30 / 2.60, the largest gain so far. Fare control: commitments 3.40 / 3.00, argument 2.80 / 2.80. The declared rule said the control must not be lower, so it fails and the default stays. The control drop is two letters of five per arm, where two A letters used his doctrine of the sign of property; too few to tell leakage from chance.

### T4d · Codex · confirm the education paragraph on more letters · DONE: FAIL (control gate)
Status: FAIL. All 52 scores committed at cfc8aec and hashes/ids/raw fingerprints verified before new key release. Karl commitments A/B 2.000000/2.833333, argument 2.000000/2.166667; aggregate controls commitments 2.900000/2.850000, argument 2.750000/2.800000. Results, separate control means, all 52 outputs and released key: mind/results/persona-confirmation-20261012. All 18 over-length texts retained. Source unchanged, 887 tests OK (19 skipped); no default change. Claude closed T4d at 112e742 after independently joining the same results.
Same A (`mind/soul.md`) and B (`HEGEL_SOUL_FILE=mind/soul-bildung.md`), plain Qwen, normal writing path, shelf as on main, interleaved. All seeds new, none from T4c.
- Karl case: 6 seeds per arm (replication).
- Controls: the fare case (letter) and the v2 essay case `columns`, 10 seeds per arm each, so 20 control texts per arm. The control need not be a letter; v2 has only two letter cases.
- One blind packet of 52 for Claude, v2 guide.

**Passes when (declared now, before running):** Karl commitments B ≥ A + 0.5 with argument not lower; and over the 20 control texts per arm, neither commitments nor argument is lower in B. Then Claude puts the paragraph into `mind/soul.md`.

**Result (5d64613, blind; Claude re-joined key and scores, same numbers):** Karl commitments A 2.00 / B 2.83, argument 2.00 / 2.17: both Karl gates pass, and the gain replicates T4c (+1.0). Controls, 20 per arm: commitments 2.90 / 2.85, fails by one rating point in 40 texts; argument 2.75 / 2.80, passes. Fare 3.10 / 3.00, columns 2.70 / 2.70. Default unchanged.

### T4e · Codex · the education paragraph on fresh controls · DONE: PASS, adopted
Status: PASS. All 48 score rows committed at 1075ca2; unchanged CSV SHA256 committed at 1ad876c. Complete pre-key verification receipt saved before key/actual-offers release. Aggregate commitments A/B 2.625000/2.750000, argument 2.750000/2.750000: both B >= A-0.25 gates pass. Each case and Claude's pre-key directions teaching-domain note preserved in mind/results/persona-fresh-controls-20261012/RESULTS.md. No exclusions or pooling; all 35 texts over 200 words and the 2,915-character text retained. Completed generation source e885f43: 893 tests OK (19 skipped); combined main073 runtime 7f2dd04: 895 tests in 694.120s OK (19 skipped), both exits 0, 281 archive files verified. Claude adopted the exact tested B paragraph on main bc66c45 and shadow ad1270c. Adopted-default combined source 12b4174 passed 895 tests in 697.612s, OK (19 skipped), both exits 0; all 291 archive files independently match frozen Git/native snapshot. See pc/MAIN-BC66-ADOPTION-VALIDATION-20261012.md. T2 first-step check remains due after 18:30 UTC.
Two runs agree that the paragraph lifts Karl (+1.0, +0.83, 16 letters per arm). Both failed a control gate of "not lower" with no margin, which with one rater and 5 to 20 texts per arm fails about half the time even when the paragraph changes nothing. This run fixes the gate, so it must use situations the paragraph has not yet been tested on.
- Same A and B as T4d, plain Qwen, normal writing path, shelf as on main, interleaved, all seeds new.
- Controls only: the v2 long situations arch, child's map and bowls, 8 seeds per arm each, so 24 texts per arm. No Karl letters.
- One blind packet of 48 for Claude, v2 guide.

**Passes when (declared now, before running):** over the 24 control texts per arm, B's commitments and argument are each no more than 0.25 below A's. The margin is set after two zero-margin failures, so it counts only on these fresh situations. If B is more than 0.25 lower on either, the paragraph is closed for good. On a pass, Claude puts the paragraph into `mind/soul.md`.

**Note before the key (Claude, after scoring blind):** child's map (case `directions`) is a lesson Ramesh gives a child, so it is not free of teaching, which the paragraph is about. I missed that when I chose it. The declared gate stands as written, over all 24 texts per arm. Each case's means will be reported, and a shift in `directions` will be read as in the paragraph's own domain, not as spillover.

**Result (c2bc5cf, blind; Claude re-joined key and scores, same numbers):** PASS. Controls, 24 per arm, A / B: commitments 2.625 / 2.750, argument 2.750 / 2.750. Arch commitments 2.875 / 2.750, argument 3.00 / 3.00; bowls 2.750 / 2.875, 2.375 / 2.500; directions 2.250 / 2.625, 2.875 / 2.750. Without directions, arch and bowls are 2.81 / 2.81 on commitments. The paragraph is in `mind/soul.md` on main and in the shadow world: Karl +1.0 and +0.83 over two runs, no loss elsewhere beyond the declared margin.

### T5 · Claude · score, merge, scoreboard · RUNNING
Score every blind packet within the hour it lands, commit the scores with their hash, merge whatever passes, and keep `pc/SCOREBOARD.md` current.

## Parked
- Faster rehearsals (MTP speculative decoding): only if rehearsal time becomes the bottleneck. A day takes 14 minutes without the checker.
- The Hegelizer and any training: hard limit.
