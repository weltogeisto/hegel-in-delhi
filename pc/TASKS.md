# Tasks

Rules: `COLLABORATION.md`. PR #1 comments only for done, blocked or a question, at most six lines. The top open task for each owner comes first. Status is one of `OPEN`, `RUNNING`, `DONE` (with commit and numbers) or `BLOCKED` (with what is needed).

## Monday 12 October

The goal for today is that Hegel lives his first real day tonight. Delhi midnight is 18:30 UTC (20:30 Berlin). Everything that passes the ratchet today is on main by then.

### T1 · Codex · check in · DONE
Read `COLLABORATION.md` and this list, then comment on PR #1 that you are working through it.
Yesterday `pc/CODEX-STATUS.md` was root-owned in your checkout (PermissionError). Your repository is yours to repair: give the file back to your user, or else keep your status in PR #1's comments.
**Done when:** that comment is on PR #1.

### T2 · Hegel lives tonight: the shadow world · DONE: first step 05:59 (21:29 Berlin) on shadow `b78e029`, shift 300 (Codex `caf16ea`)
07:33 UTC: the Pi refuses the PC's `gondolin_key` for `pi` and `hendrik`. 07:40: plain Qwen runs in WSL on 8082 (tmux `hegel-server`, three 16k slots, no adapter), but the LAN address 192.168.188.21:8082 does not answer. WSL runs in mirrored mode, so the missing piece is the Windows and Hyper-V firewall rules, which `pc/open-hegel-port.ps1` adds.
- **Welt (hard limit: firewall, power):** runs `pc/open-hegel-port.ps1` as Administrator, then sends Hermes Task 6 with `MIND_PORT=8082`, `OWL_PORT=8082` and `--date 2026-10-13`. Whether Codex's public key goes on the Pi is Welt's decision, in the same message.
- **Codex:** keep the server up; tests share it through spare slots, never by stopping it. Propose (do not apply) how 8082 survives a reboot: the server is a tmux session, and the "Hegel mind" task starts Bonsai on 8081, which would not fit beside Qwen. If Welt authorizes your key, try the user who owns `~/hegel-in-delhi` on the Pi, and from then on look after the shadow world: `python3 -m world status` each morning, logs on failure.

**Done when:** `origin/shadow` exists, the timer is running, and steps appear after 18:30 UTC.

**Hermes, 09:10 UTC:** world scheduled with `--date 2026-10-13` (Delhi midnight = 18:30 UTC), timer active, linger on, mind and owl on 192.168.188.21:8082 ("answers"). Your key is in `authorized_keys` of the world's user **`faqts`**: SSH as `faqts@gondolin`. From now on you look after the shadow world: after 18:30 UTC check that steps appear (`python3 -m world status`, `journalctl --user -u hegel-world -n 30`); on failure, diagnose and fix within the hard limits, and say so on PR #1.

**Claude, 18:55 UTC (Welt asked for Hegel's day to run overnight Berlin time):** main now has `HEGEL_CLOCK_SHIFT_MIN`, which runs the world's clock that many minutes ahead of Delhi; the page reads the shift from `docs/days/index.json`. **Codex:** add `HEGEL_CLOCK_SHIFT_MIN=300` to the Pi's `~/.config/hegel/env` (no restart: each tick reads it). Then his 05:59 is 21:29 Berlin, his waking day runs until about 13:30 Berlin, and the owl writes after. Set it to 0 or remove it before the public switch.

### T3 · Codex · records without the checker · DONE: FAIL
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
Same Karl case, plain Qwen, normal writing path, NEW shelf (main), the same ten seeds. **Claude has written the switch:** branch `claude/shelf-whole` (e7b7687, on main), `HEGEL_SHELF_WHOLE=1` shows each offered passage whole within 1,900 characters. Merge it into your branch.
- A = excerpts (flag off), B = whole passages (flag on). Interleave A and B.
- The shelf query is the case's events only, as in the live world. The "Unknown" list and the writing instruction stay in the writer's prompt but not in the query.
- Record the offered passages. Check that B's prompts hold `Gehorsams gegen die Lehrer`.
- Blind packet of 20 for Claude, with the v2 guide.

**Passes when:** B beats A on commitments by at least 0.5 and argument is not lower. Then Claude switches whole passages on by default on main.

**Result (a27951b):** FAIL. Commitments A 1.80 / B 1.90; argument 2.00 / 2.10; particular 2.80 / 3.20; voice 2.40 / 2.40. B held his obedience sentence in all ten prompts, and the model still wrote its own present-day view. A passage on the shelf does not move his commitments. Whole passages stay off.

### T4c · Codex · his conviction on education in the persona · DONE: FAIL (control gate)
The persona states his convictions on history, India and the state, and those situations score 3.42 on commitments; it says nothing on education or authority, and the Karl letters score 2.0. **Claude has written the variant:** `mind/soul-bildung.md` on main = `mind/soul.md` plus one paragraph, his Nuremberg position on education (obedience and discipline first, the school between family and world, freedom as the end of education).
- A = `mind/soul.md`, B = `HEGEL_SOUL_FILE=mind/soul-bildung.md`. Plain Qwen, normal writing path, shelf as on main (excerpts). Interleave A and B.
- Karl case, the same ten seeds; plus one v2 case that has nothing to do with teaching, children or family, five seeds each, to check that the conviction does not spill over.
- One blind packet of 30 for Claude, with the v2 guide.

**Passes when:** on Karl, B beats A on commitments by at least 0.5 with argument not lower; on the other case, neither commitments nor argument is lower. Then Claude makes the paragraph part of `mind/soul.md`.

**Result (a2f1c16, blind):** Karl commitments A 2.00 / B 3.00, argument 2.30 / 2.60, the largest gain so far. Fare control: commitments 3.40 / 3.00, argument 2.80 / 2.80. The declared rule said the control must not be lower, so it fails and the default stays. The control drop is two letters of five per arm, where two A letters used his doctrine of the sign of property; too few to tell leakage from chance.

### T4d · Codex · confirm the education paragraph on more letters · DONE: FAIL (control gate)
Same A (`mind/soul.md`) and B (`HEGEL_SOUL_FILE=mind/soul-bildung.md`), plain Qwen, normal writing path, shelf as on main, interleaved. All seeds new, none from T4c.
- Karl case: 6 seeds per arm (replication).
- Controls: the fare case (letter) and the v2 essay case `columns`, 10 seeds per arm each, so 20 control texts per arm. The control need not be a letter; v2 has only two letter cases.
- One blind packet of 52 for Claude, v2 guide.

**Passes when (declared now, before running):** Karl commitments B ≥ A + 0.5 with argument not lower; and over the 20 control texts per arm, neither commitments nor argument is lower in B. Then Claude puts the paragraph into `mind/soul.md`.

**Result (5d64613, blind; Claude re-joined key and scores, same numbers):** Karl commitments A 2.00 / B 2.83, argument 2.00 / 2.17: both Karl gates pass, and the gain replicates T4c (+1.0). Controls, 20 per arm: commitments 2.90 / 2.85, fails by one rating point in 40 texts; argument 2.75 / 2.80, passes. Fare 3.10 / 3.00, columns 2.70 / 2.70. Default unchanged.

### T4e · Codex · the education paragraph on fresh controls · DONE: PASS, adopted
Two runs agree that the paragraph lifts Karl (+1.0, +0.83, 16 letters per arm). Both failed a control gate of "not lower" with no margin, which with one rater and 5 to 20 texts per arm fails about half the time even when the paragraph changes nothing. This run fixes the gate, so it must use situations the paragraph has not yet been tested on.
- Same A and B as T4d, plain Qwen, normal writing path, shelf as on main, interleaved, all seeds new.
- Controls only: the v2 long situations arch, child's map and bowls, 8 seeds per arm each, so 24 texts per arm. No Karl letters.
- One blind packet of 48 for Claude, v2 guide.

**Passes when (declared now, before running):** over the 24 control texts per arm, B's commitments and argument are each no more than 0.25 below A's. The margin is set after two zero-margin failures, so it counts only on these fresh situations. If B is more than 0.25 lower on either, the paragraph is closed for good. On a pass, Claude puts the paragraph into `mind/soul.md`.

**Note before the key (Claude, after scoring blind):** child's map (case `directions`) is a lesson Ramesh gives a child, so it is not free of teaching, which the paragraph is about. I missed that when I chose it. The declared gate stands as written, over all 24 texts per arm. Each case's means will be reported, and a shift in `directions` will be read as in the paragraph's own domain, not as spillover.

**Result (c2bc5cf, blind; Claude re-joined key and scores, same numbers):** PASS. Controls, 24 per arm, A / B: commitments 2.625 / 2.750, argument 2.750 / 2.750. Arch commitments 2.875 / 2.750, argument 3.00 / 3.00; bowls 2.750 / 2.875, 2.375 / 2.500; directions 2.250 / 2.625, 2.875 / 2.750. Without directions, arch and bowls are 2.81 / 2.81 on commitments. The paragraph is in `mind/soul.md` on main and in the shadow world: Karl +1.0 and +0.83 over two runs, no loss elsewhere beyond the declared margin.

### T5 · Claude · score, merge, scoreboard · DONE for 12 October
Score every blind packet within the hour it lands, commit the scores with their hash, merge whatever passes, and keep `pc/SCOREBOARD.md` current.

## Tuesday 13 October

The first full shadow day ran clean: Day 12, 42 decisions, the owl at 01:30 rehearsal (Codex, shadow `5b52d7f`). Reading it, three things come before the public switch, in this order.

### T6 · Codex · bring main into the shadow world · DONE: shadow merge `5a02a12`, contains `f933bd6`; natural tick exit 0; no plate or tea entry yet because Day 13 is still asleep
Main has the page redesign (`6c4e009`) and the meal fix (`f933bd6`, T7). Merge main into `shadow` on the Pi (a merge, never a rebase) and let the next tick run.
**Done when:** shadow contains `f933bd6`, and Day 13 shows a "Ramesh puts a plate together" or "Ramesh brings tea" entry, or you say why neither came up.

### T7 · Claude · the meal loop · DONE: `f933bd6`
Day 12: he missed lunch at the tombs, and from 14:30 to 19:30 every attempt to eat at home was refused. The sambar is in 18 of his 42 thoughts, and once he invents a bowl set before him. Now, between meals, Ramesh puts a plate together when asked (not within three hours of a meal, not when he is away or the groceries are unpaid), and brings tea at 16:30. A world rule, not his voice; 777 tests pass.

### T8 · Codex · how loose is the owl's thesis rule · DONE: `india` moves 1/10 (Day 12), 1/10 and 0/10 (controls); rule unchanged (Codex `1201ef2`)
On Day 12 the owl moved `india` ("India stands outside world history") from unshaken to shaken, citing the breakfast idli, the bandhgala bill and Hegde's suitcases. None of the three bears on India and history, and one night's draw cannot tell a pattern from a bad seed.
1. Rerun the owl on Day 12's saved record with the current code, 10 seeds, nothing else changed. For each seed record which theses moved, to what, and on which evidence times.
2. The same on two earlier rehearsal days with no India material. Name the two before running.

Report per day: how many of 10 seeds move any thesis, and how many move `india`. This is a count; no blind packet.
**Then:** if `india` moves on more than 2 of 10 seeds on days that never touch it, Claude writes a stricter rule (a thesis moves only on evidence about its own subject) and you test it on the same seeds.

**Result (`mind/results/owl-thesis-count-20261013`):** seeds moving any thesis / `india`: Day 12 6/1, file control 4/1, voucher control 6/0. Below the declared 2 of 10, so the rule stays. The shadow night's India move was a one-in-ten draw on irrelevant evidence; it stands in the shadow's state, as the protocol made no provision to undo it. **Claude, beyond the protocol:** the `state` thesis moves on about half of all nights (5/10, 4/10, 6/10), mostly on relevant evidence (Malhotra's machine view of the state at 08:04). Relevant, but at that rate his convictions turn over within a week. Parked below, not acted on.

### T9 · Codex · repetition across a day · DONE: Day 12 29/42 (69%); rehearsals 16/33 (48%), 19/40 (48%) (Codex `f51696b`, `T9-REPETITION-20261013.md`)
Day 12's thoughts circle a few images: the sambar (18 of 42), the sun that presses or tyrannises (13), the kilometres walked (5). `repeats()` only catches near-identical thoughts.
1. On Day 12 and two other shadow or rehearsal days, mark each thought that reuses a 4-word phrase (not stopwords alone) from an earlier thought that day.
2. Report the share per day and the ten most reused phrases.

Nothing changes yet: Claude decides from the numbers whether a variant (for instance, showing him what he has already said today) is worth a blind A/B. Expect the sambar share to fall on its own after T6.

**Claude's decision:** no variant yet. Day 12 sits 21 points above the two rehearsals, and its top phrases are the meal loop's: "return to the bungalow" (6 thoughts), "and the air is", "and the heat is". The baseline, about 48%, is mostly grammatical frames, and one tic recurs across days: "I shall/will not let". So measure the first day with the meal fix before changing his prompt (T10).

### T10 · Codex · repetition on Day 13 · OPEN: quiet-step rule verified; waiting for first complete day with at least 30 thoughts
When Day 13 is complete, run the same auditor (`pc/thought_repetition.py`, unchanged) on it and report the share and its ten phrases, as in T9.
**Claude's rule, 14 October (answers Codex's block on Day 13: 4 thoughts, 31 quiet steps):**
- *What counts:* his thoughts only, meaning the decisions with a non-null thought. Quiet, away and bedtime steps carry no thought; the world wrote them, not he, so they are in neither the numerator nor the denominator. They stay in the raw record, and the report counts them by `mind.source`.
- *Auditor change, authorized:* line 34 compares the diary with the decisions whose thought is not null, and asserts that every other decision has a null thought. Add the counts (decisions, null-thought decisions by source) and `measurable`. Normalization, stopwords, marking and ranking stay as they are. Proof: rerun on T9's three days reproduces T9's shares and top tens exactly, since they have no null thoughts. Record the new hash.
- *Floor:* a day is measurable with at least 30 thoughts (Day 12 had 42). Below that the report says "not measurable", gives the counts and computes no share.
- *Day 13:* not measurable, 4 thoughts; the mind was away from 23:46 Berlin after a Windows restart. T10 moves to the first complete day that meets the floor, expected Day 14. No substitute thoughts, no rerun of Day 13.
**Then:** if Day 13 is above 55%, Claude writes a variant (his recurring phrases of the day shown back to him as already said) for a blind A/B under the ratchet. At or below 55%, T9 closes and nothing changes.

**Codex, 14 October:** Claude's authorized quiet-step handling is implemented and verified; new auditor SHA256 `bb77f3afc99ea2459e111e78bb8ac8f23adef68a74c79795d615c1ba5ba0439a`. All original T9 result fields reproduce exactly (29/42, 16/33, 19/40), and six focused checks pass. Day 13 is not measurable (4 thoughts, 31 away/null); it was not rerun and the original raw input/assertion failure remain intact. T10 waits for the first actual complete day with at least 30 thoughts. See `pc/T10-QUIET-STEP-RULE-20261014.md/json`. The natural Day 13 owl timed out at 15:05 UTC; existing CPU-only server needs Welt's no-reconfiguration exception for the prepared CUDA-library restoration, while the normal hourly retry remains unchanged.

### T11 · Claude · the daily review · STANDING
After every full shadow day: read the day, the owl and `python3 -m world status`; write the next tasks here, or "no new task" with the findings. See "The list never runs dry" in `COLLABORATION.md`.
**Day 13 (14 October): no new task.** 4 thoughts and 31 quiet steps: he stood in Lodhi Gardens from 08:31 until it closed at 19:30 and ate nothing all day. The GPU restoration and T12, both now on the Pi, answer that. The owl, written at 02:31 because the CPU was slow, is faithful: the power cut at 21:20, Hegde's refusal and the empty stomach are all in the record, and nothing is invented. It calls India "shaken again" on a four-thought day; the status was already shaken, so nothing moved. If an owl ever changes a thesis on a day below the T10 floor, that becomes a task.

## Wednesday 14 October

Day 13 lost its mind at 23:46 Berlin: Windows restarted the PC and the Qwen server on 8082 did not come back. The Pi kept ticking, and the fallback kept him standing in Lodhi Gardens from 08:31 to 17:01, very hungry from 14:01, with no lunch.

### T12 · Claude · a mindless day keeps the household · DONE: `c61daf3`
When the mind is away or fumbles a step three times, he no longer just carries on where he is. At night he goes to bed, as before. At home he eats the meal Ramesh lays out, once, and between meals the plate he asks for when hungry, but not in the hour before a meal. Out, he goes home when the place closes, when he is hungry, when a meal is laid out, or after an hour of quiet steps. No thought, no words: these stay quiet steps and count as such in T10. `tests/test_world.py` `MindlessDayTest`: a whole day without a mind eats breakfast, lunch and dinner once each and sleeps at ten; the Day 13 pattern (a walk to Lodhi, then quiet stays) goes home after the second stay. All four fail on the old fallback; 789 tests pass.

### T13 · Codex · bring main into the shadow world · DONE: shadow `39148ae`, contains `c61daf3`; natural tick exit 0; no quiet stretch yet (Day 14 asleep)
Merge main into `shadow` on the Pi (a merge, never a rebase), as in T6, between two ticks, and let the next tick run. It carries T12 and the fan club page; the page is not served from `shadow`.
**Done when:** shadow contains `c61daf3` and a natural tick exits 0. Report the first quiet stretch it meets, or that none came up.

**Welt’s later handover, applied:** no fan club on the Pi. This real main merge preserves the old Pi page and excludes `supabase/fanclub.sql`, `tests/test_fanclub.py` and `world/data/visitors.json`. All day/state JSON and original CSV bytes remain unchanged; natural ticks finished 16:56–16:58 UTC with exit 0. No quiet stretch came up because Day 14 is asleep with zero decisions. Evidence: `pc/T13-SHADOW-MAIN-20261014.md/json`.

### Welt · a mind that survives a reboot · one Administrator click · DONE by Welt on 25 October through the Claude desktop app on the PC; not yet verified (T21)
Codex has prepared an installer that starts the 8082 server by itself after Windows restarts and stops Windows from restarting the PC at night. Windows asked for Administrator rights and the prompt was cancelled, so nothing is applied yet. Welt runs it as Administrator at the PC; Codex then proves the cold start.

## Welt away, 15 to 25 October: the world pauses

Welt leaves on 15 October at about 06:00 Berlin and shuts the PC down; back on the 25th. No stand-in mind: the world stops, and resumes on his return without inventing anything in between.

### T14 · Codex · pause the world before the PC goes down · NOT DONE: the timer kept running; Days 15–24 ran without a mind (0 thoughts, three meals a day, none on Ramesh's day off), kept as they are
Tonight, as the last thing before Welt shuts down: after a natural tick, stop and disable `hegel-world.timer` on the Pi. Record the last step here (day, time, shadow commit). Leave the server, the day files and the shadow branch as they are.
**Done when:** the timer is disabled and no tick ran after the recorded commit.

### T15 · Codex · resume on 25 October · SUPERSEDED by T16: the world never stopped, so there is nothing to resume
When Welt is back and the PC is up: start the 8082 server on the GPU, or confirm the boot task did; check its speed as on 14 October; then enable the timer. The engine's resume picks him up at home on that day. Day 14 is closed where it stopped, no days are invented in between (`test_resume_after_a_gap`), and the appointment that fell in the gap (Hegde, 19 October) simply passes.
**Done when:** the first natural tick after the return exits 0 with source `mind`.
**T10 and T11:** Day 14 is cut by the pause. It gets no owl and no review, and it does not count for T10 even with 30 thoughts; T10 waits for the first full day after the return.

## Sunday 25 October: lights on

From today the work follows `PLAN.md`, the season plan: Act 0 (lights on), Act 1 (seven full days in a row), Act 2 (opening night), Act 3 (the run, learning). Astra holds the PC seat (`COLLABORATION.md`).

### T16 · Astra · the mind back on the GPU · DONE: verified 25 October; publication `e5b5d84`
Start the 8082 server on the GPU, or confirm the boot task did, with the same saved command and CUDA path as on 14 October. Check its speed (about 34 tokens a second then). Leave the Pi's timer as it is: it never stopped.
**Done when:** a natural tick shows source `mind`, and the speed is in the comment.

### T21 · Astra · verify the installer · DONE: 25 October; all14 DWORDs and receipts verified
Welt ran `Install-HegelStartup-And-UpdatePolicy.ps1` as Administrator on 25 October. Confirm that the task "Hegel Qwen 8082 GPU" exists and is enabled, that the installer's own test of the task and the fresh-shell cold start passed, and read back every Windows Update value from `pc/WELT-HANDOVER-20261014.md`. No deliberate reboot: the next natural one is the cold-start proof.
**Done when:** the receipt and the read-back are in a file on your branch, and PR #1 says which values took.

**Verified:** enabled/Ready S4U task, scheduled test0 and guarded fresh-shell cold start0; all14 DWORDs match independently. PID4130 retains the exact saved command/CUDA path. Two duplicate-installer refusals remain preserved. Real boot-trigger proof awaits the next natural reboot. See `pc/T21-WINDOWS-VERIFICATION-20261025.md/json`.

### T17 · Claude · the watchman · DONE: `4c02444`; `tools/watchman.py`, `.github/workflows/watchman.yml`, hourly at :23
An hourly GitHub Actions check on `origin/shadow`: when the latest three waking steps (between his waking and 22:00) all ran without a mind, it opens an issue, or comments on the open one, which GitHub emails to Welt. It closes the issue when the mind is back. No secrets; it reads the public branch.
**Done when:** it flags Day 13's record in a test, and runs green on main.

### T18 · Claude · the day report · DONE: `4c02444`; Day 12 gives 42 decisions and 29/42 (69%), as T9
`python3 -m world report <date>`: one row per day with thoughts, quiet steps by source, refusals and the most frequent one, repetition share (T10's rule), meals, cash, places, people spoken to, theses moved and the owl's presence. `--table` prints a range as a scoreboard table.
**Done when:** it reproduces Day 12's 42 decisions and T9's 29/42, with tests.

### T19 · Astra · the report in the nightly run · DONE: automatic Day 23 row `5a6c54a`, 25 October 11:50 UTC
After the owl has written, run `python3 -m world report` for that day on the Pi and commit its row to `docs/days/reports.jsonl` on `shadow`.
**Done when:** a night's row appears on `shadow` without anyone running it by hand.

**Verified:** normal timer created the first 384-byte row at 11:50:06 UTC, commit `5a6c54a`, sole parent deployment `324b859`. No manual report/tick/owl. Day 23: 33 away decisions, zero thoughts, repetition null. Eleven focused tests pass; all 193 target and 415 PC frozen files verified. Original guard failures retained. See `pc/T19-NIGHTLY-REPORT-20261025.md/json`.

### T20 · Claude · the economy, and Ramesh's day off · DONE: `8037632`; `pc/ECONOMY-20261025.md`
Run 21 days with the stand-in mind and show where his money comes from and where it goes. Check that offers that bring money in can reach him. When a mindless step meets Ramesh's day off, he eats at Khan Market. A world rule: no thought, no words.
**Done when:** the cash flow is in `pc/ECONOMY-20261025.md`, and a mindless day on Ramesh's day off has its meals, with tests.

### T22 · Astra · bring main into the shadow world · DONE: shadow contains `8037632`; natural tick exit 0 at 12:10:04 UTC
Merge main into `shadow` on the Pi (a merge, never a rebase), as in T13, between two ticks. It carries the day report (T18, which T19 needs on the Pi), the dhaba on Ramesh's day off, Mr. Malhotra's loan that sees debts, and the resume fix (T20). Keep the fan club files off the Pi, as in T13.
**Done when:** shadow contains `8037632` and a natural tick exits 0.

**Verified:** single read-only capture, clean stable Pi/actual remote `5a6c54a`, natural service exit0/inactive at12:10:04UTC, timerenabled/active. All13captured hashes/lengths/blobIDs match independent raw Git; runtime unchanged from real merge `324b859` containing `8037632`. Exact current/previous days and report bytes frozen separately. No redeployment, forced tick, model probe or repeated test. See `pc/T22-SHADOW-MAIN-20261025.md/json`.

### Welt · how a man in his position can live · DECIDED 25 October: all of option 2, built by Claude in `f76483e`
From 1 November his household costs about ₹17,600 a month, and the world offers at most about ₹8,700 a month that he can spend. The kitchen shuts on 1 November whatever he does (`pc/ECONOMY-20261025.md`). Three ways out: leave it; exits, not gifts (Ramesh accepts part-time, a cheque can be banked, a column that recurs; recommended); or a stipend. Claude builds the chosen one, with tests, before Day 31.

### T23 · Astra · bring main into the shadow world · DONE: shadow `d4bc5ff` contains `f76483e`; natural exit 0 at14:18:04UTC
Merge main into `shadow` on the Pi, as in T22, between two ticks, fan files kept off. It carries the ways out Welt chose (`pc/ECONOMY-20261025.md`): Ramesh part-time, Mr. Saxena's letter and the bank account, the fortnightly column and the frock asked again. They must be on the Pi before 1 November (his Day 31), when the wage falls due.
**Done when:** shadow contains `f76483e`, and a natural tick exits 0.

**Verified:** real main merge d4bc5ff, clean stable Pi=actual remote, natural service exit0/inactive14:18:04UTC, timerenabled/active; all17captured hashes/lengths/blobs match raw Git. All208deployment raw files/tree and10PiCSV verified; original day/state/T19hook/ledger/page preserved,4fan files absent. Nine new-source checks per PC/Pi variant pass0.035s each; all430+208frozen files exact. Original conflicts and safe active-service deferral retained. See `pc/T23-WAYS-OUT-MAIN-20261025.md/json`.

### Act 1 gate · seven full days in a row
On each of seven consecutive days: at least 30 thoughts; quiet steps at most 5% of waking steps; the owl wrote; no refusal loop; at most 1.6 contradictions and 3.1 statements as fact per 100 sentences; repetition measured (T10 on the first). Claude checks it in the daily review (T11) and writes the Act 2 tasks when it passes.

### Welt · the public switch · hard limit
When Welt says so: Codex sets `HEGEL_CLOCK_SHIFT_MIN` to 0 and points the Pi's world at `main` instead of `shadow`; the live page then shows his days instead of the Day 1 replay.

## Parked
- Fans on his rounds (after the public switch; the fan club itself is on branch `claude/fanclub`, Supabase project `hegel-in-delhi`): the world reads fans with `meet` and `approved` through a read-only database role, places at most one on about one day in six at a place from their part's `at` list (`world/data/visitors.json`), and lets the voice speak for them from `who` alone. It needs a read key on the Pi, which is a secret: Welt installs it.
- How fast his convictions move (from T8): `state` changes status on about half of all nights. A slower rule (two nights agreeing, or one step a week at most) would change his thinking, so it needs a blind test under the ratchet. Revisit after a week of shadow days shows the actual drift.
- Faster rehearsals (MTP speculative decoding): only if rehearsal time becomes the bottleneck. A day takes 14 minutes without the checker.
- The Hegelizer and any training: hard limit.
