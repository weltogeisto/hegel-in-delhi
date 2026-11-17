# Decisions

Welt's calls, 3 October 2026. Everything built from here follows them.

## The deal

Hegel, knowledge cut off in November 1831, rediscovering the world in 2026 Delhi and writing about it. A realistic simulation: the world does not steer him. His views are his own, 19th-century ones included. Nobody corrects him; if he changes his mind, Delhi changed it, or he did.

## What the page carries

1. **No limit on his views, a dark veil instead.** Entries the world flags as sensitive (race, religion, caste, colonial views and the like) sit under a dark band; viewers click to read. The world flags and never refuses. The never-list becomes the flag list.
2. **No ethical steering.** The thesis tracker stays as a neutral record of how his views move, in either direction, with the evidence that moved them. No rule prefers one direction.
3. **Day 1 is rewritten** in this spirit before the public switch.
4. **He writes in English.**
5. **News:** crime and violence stay out of the morning papers; wars and civil strife stay in.
6. **Real people:** he may name the public figures he reads about. No invented quotes. Everyone he meets is fictional.

## How the world behaves

7. **Technology reaches him through the people he meets,** over time. What he reads online counts as met, like any book or paper.
8. **Discovery is emergent.** No planted scenes for Marx or anything else. The Hegde file stays as the bureaucratic frame.
9. **He writes whatever he is inclined to:** diary and Depesche, and any essay, letter or book he starts.
10. **The people he meets answer him,** voiced by the model from their cards.
11. **The mind:** Bonsai first, untrained, with his shelf. If Qwen, trained or not, is considerably better on the Hegel test, Qwen it is. Hegel's own mind is trained on Qwen3.8-27B and runs on it; no Bonsai is trained or adapted (Welt, 4 October). Hegel's writings were written in plain-text mode under a header in the style of his books from 6 October; real samples kept to their subject but lost his thinking, so from 10 October they are written by the chat call again, and the plain-text path stays behind HEGEL_WRITE_MODE=plain until a blind test shows it better.
12. **Judges for the Hegel test:** Welt and Claude.
13. **Money is a simulated economy.** Cash in a purse; the imprest is state money refilled only against vouchers at the Directorate, with personal spending queried and owed; income only from what he does (tutoring, talks, selling things, loans), offered through people and circumstance; recurring costs (groceries, electricity, Ramesh's wage for cooking, the dhobi, festival tips). All prices are simulated; nothing is bought for real.
14. **His conduct is loosened.** No rule against the violent, the romantic or the illegal in what he does; the world answers with consequences.
15. **The map is precise.** Real streets, parks, walls and buildings from OpenStreetMap (ODbL, attributed on the page), in the same pixel style. Hegel's bungalow stays fictional on a real Tughlak Road plot; no real residence or occupant is named.

## His character

Welt's calls, 7 November 2026, from his interview for the implementation manual (`pc/HEGEL-IMPLEMENTATION-MANUAL.md`, version 1.1, §1.1). They replace any older target that conflicts with them, from now on; old results and their scores stay as they were.

16. **His convictions may change what they say,** through experience, even the central ones. His reasoning stays recognizably Hegelian. The record keeps each conviction's content and its history.
17. **A rewrite keeps the thought's conclusion and its recorded facts.** It may develop or revise the reasoning. It never turns a refusal into agreement, doubt into certainty, a plan into a done deed or a belief into a fact. Later experiences may lead him to a different conclusion; that is a new, dated version, and the earlier one stays.
18. **Concepts and habits of reasoning come from his texts.** A fresh argument needs no passage behind it, and no thought needs a quotation.
19. **He may trust someone and be wrong.** Plausible mistaken beliefs are allowed. The record keeps what happened apart from what anyone believes or says.
20. **Ordinary moments are mostly practical or personal.** Philosophy comes when something calls for it. Breakfast, errands and waiting are worth a thought in their own right.
21. **Ordinary thoughts are in natural contemporary English.** His perspective and his reasoning make him Hegel, not the diction of his translators. The register of long manuscripts and of the owl's diary stays open and is tested on its own.

Implementation decision following the interview (Welt, 7 November):

22. **Delta is no longer a pass/fail bar for ordinary thoughts.** It stays as a diagnostic, and every historical Delta result is kept as recorded.

## After the tests of 14 and 15 November

Welt's calls, 15 November 2026.

23. **Training 3 is closed.** Its data gate was not met: 86 revised pairs against 200. Its 2,000 answers stay preserved. The live filter does its work without training (`pc/TRAINING3-RUN-20261106.md`).
24. **The filter runs on shadow as a provisional trial:** `HEGEL_DECISION_DRAWS=4`. It is a choice among plain Qwen's own replies; no weights change and no adapter is used. It passed T36 in full (`pc/T49-ARM-D-RESULT-20261114.md`). Setting it back to 1 ends the trial.
25. **The shelf names an editor's addition:** `HEGEL_SHELF_ADDITIONS=1`, switched on third, so each change can be read on its own (decision 31) (`pc/M2-SOURCE-LABELS.md`).
26. **The Paris backtest goes ahead with step 0 and stage 1** (`pc/PARIS-BACKTEST.md`). His letters from the three journeys (the Netherlands 1822, Vienna 1824, Paris 1827) stay a test set: off his shelf and out of any training from now on.

Welt's calls on the Paris profile, 15 November:

27. **His Delhi offers what he would seek abroad:** museums, a gallery of modern art, concerts and plays (`pc/CULTURE.md`), behind `HEGEL_CULTURE`, switched on fourth (decision 31).
28. **He gets someone to write to:** a descendant of Niethammer's family in Munich, his closest friend's. Niethammer died in 1848 and stays dead; the descendant, Dr. Clara Lindner, is invented. Her first letter settles his debts and leaves him ₹20,000 besides, a gift beyond decision 13 (Welt, 15 November; `pc/CORRESPONDENT.md`). Behind `HEGEL_CORRESPONDENT`, switched on second (decision 31).
29. **No personal contact in the code.** Download tools name the project's page, not a person.

The night rule, narrowed (Welt, 15 November):

30. **Training runs by day, watched. Work that trains nothing may use the night** while Hegel sleeps: sampling, prompt screens, coding and evaluation calls to plain Qwen.
    - **What it may not do at night:** change weights, adapters or anything live on Hegel.
    - **Guards:** the job uses the spare slot only, so the owl keeps its own. Its ledger reconciles every call. It stops cleanly by 08:30 Berlin and before the PC's twelve-hour shutdown.
    - **Report:** one line on PR #1 in the morning.
    - **Why:** the rule of 6 November came from three unwatched Training 1 nights that failed (`pc/CLAUDE-HANDOVER-20261106.md`). It was about training. This narrows the manual's general "no night runs".
    - **The sampling run of 00:06–03:08 on 15 November** falls under this rule and stands.

Welt's calls, the afternoon of 15 November:

31. **The order of switching on, one change at a time,** each after the previous one's first full day is reported:
    1. the filter (on since 14:28 on 15 November);
    2. the letter from Munich, which pays what he owes, so he has money for what follows;
    3. the shelf labels;
    4. the museums, concerts and plays, whose tickets need that money.
32. **His world pauses when the PC is away** (`pc/PAUSE.md`), behind `HEGEL_PAUSE_AWAY`.
    - When the PC doesn't answer at his waking, the world holds at the start of that day.
    - When the PC answers again, he lives the held day, and his calendar trails Delhi's by those whole days.
    - It acts only when the PC is away, so it may go on at once, outside the order of 31.

Welt's calls, the evening of 15 November:

33. **The letter from Munich goes on now,** beside the filter, without waiting for the filter's first full day. His purse is empty, and every later reading needs days with money. The filter has passed its blind test, so the overlap costs little.
34. **The new instructions run on shadow as a provisional trial:** `HEGEL_SOUL_FILE=mind/soul-ordinary.md`, after the letter's first full day. They passed the M1 confirmation (`pc/exports/m1-confirmation-20261115/judgment/REPORT.md`). Setting it back to `mind/soul.md` ends the trial. The order of 31 becomes:
    1. the filter (on since 14:28 on 15 November);
    2. the letter from Munich (now);
    3. the new instructions;
    4. the shelf labels;
    5. the museums, concerts and plays.
35. **An answer stays where it was given.** When he speaks as he leaves, the answer belongs to that step and its record. It no longer opens his next moment at the place he walked to (at 38:25 and 45:25 a bookseller's line reached him at home).

Welt's calls, 16 November:

36. **The world's second phase starts with week 0** of `WORLD-2.md`: the instrument (world health, the rehearsal, forks), the counts of rule 7, the file's next act in draft, and the `wants` line with its screen. No GPU and nothing live. The packets are in `pc/WORLD-2-WEEK0.md`.
    - **What this go does not cover:** weeks 1 and after, and the ten calls under "What Welt decides" in `WORLD-2.md`. Each waits for his word.
37. **He is to be freer to decide what he does in this world.** The plan gains its seventh chapter for it: he may name what is not offered, and his wishes are kept for Welt to read. A bicycle, with a shop that sells one, joins the second ring of places (T61).
    - **Why:** all 39 intentions in his recorded morning plans stay inside the menu the world lists.
38. **Who does which work in the cloud, and how sources are read:** planning stays with Claude in the cloud; reading, code and checks go to agents on Sonnet 5.5, briefed and checked. A paper that carries a decision is read in full (`COLLABORATION.md`, under Roles).

39. **Weeks 1 and 2 are built, first wave** (`pc/WORLD-2-WEEK1.md`): promises as records, what a voice is told about itself, the street, a wider condition for beats, and every call naming its adapter. Welt, 16 November: "ok, lets go". Read as a go to build. Every switch stays off.
    - **Not read into it:** a pull request to main, the sentence for `wants`, and the file's next act going into `plot.json`. Claude asked again in plain terms; the answers are 40 to 42.

Welt's answers, the evening of 16 November, to three questions put plainly:

40. **The PC gets the new work: yes.** The branch of the world's second phase is joined to main. Every new switch is off, so nothing changes for him. The PC seat's three tasks are W1 to W3 in `pc/TASKS.md`.
41. **The sentence for `wants` may be tested: yes,** as drafted in `pc/WANTS-SCREEN.md`. The PC seat runs the screen on frozen moments. The sentence goes into his live days only after the result and Welt's word again.
42. **The file's next act: later.** `pc/FILE-NEXT-ACT.md` stays a draft and out of `plot.json`. After his 20 November the file is silent until Welt takes it up.

Welt's call, 17 November:

43. **The records branch keeps its additions behind a switch that is off by default.** When main was merged into `codex/outcome-memory`, the day guard failed (`tests/test_opened.py`): that branch adds `records`, charge ids, `observations` and a `consumed` entry to every day with nothing switched. The guard's reference is not recorded again.
    - **Why:** the guard stands for one rule, that a day with every new switch off is the day main gives. A reference recorded again to pass would stop meaning that for the branch's own later changes.
    - **One allowance:** a field that is only ever added beside the record, and that neither he, the page nor the owl reads, may be named in the guard's `ADDED` list instead of switched. What sits inside existing entries, or is a new kind of entry, goes behind the switch.
    - **Who:** the PC seat, on its branch.

Welt's calls, the afternoon of 17 November:

44. **The PC seat builds and runs the screen for the voices and the promises,** from a handover (`pc/T57-HANDOVER.md`). Claude in the cloud keeps the declaration, the reading and the result.
45. **Khan Market gets its own scene on the page:** the lane with Sunil's stall and the dhaba, shown when he eats, drinks or talks there. Built by an agent on Sonnet 5.5, checked by Claude.
    - **Why:** the page had rooms for four places and two Khan Market shops, shown only on a stroll. When he sat there eating, it showed nothing.

46. **The street's first batch is approved** (Welt, 17 November): the sixty cards as written, the seven that are not verified against Delhi included. `HEGEL_STREET` stays off until its forks have passed (`pc/STREET-FORKS.md`) and Welt has given his word for the trial.
47. **Ramesh's days go both ways** (Welt, 17 November: "build ramesh offer"). Short of money, Hegel agreed that Ramesh comes on Mondays, Thursdays and Saturdays for ₹4,000. Nothing offered the way back.
    - **The offer:** once no wage and no groceries stand owed, and ₹16,000, two months of the full wage, is left after everything he owes, Ramesh offers at home to come every day but Wednesday again, for ₹8,000 (`ramesh_fulltime` in `world/data/offers.json`). Bills falling due in that same moment count. Hegel answers yes or no, as to every offer; a no comes back after a week.
    - **Both ways:** a yes to either offer lets the other be made again later, so a lean month can send Ramesh back to three days and a better one bring him back.
    - **Behind `HEGEL_RAMESH_DAYS`, off by default:** without it the offer does not exist and his world is as it was (`tests/test_ramesh_days.py`).
    - **When it goes on:** Welt left it to Claude ("make the decision that I would most likely make"). It goes on once the new instructions' first whole day, Day 49, has been read, before Day 50's waking, so the two changes are read apart. Nothing presses: Ramesh cooks again on Thursday either way.

Welt's call, the afternoon of 17 November, on two answers that had reached two seats:

48. **The guard on the records branch: the new reference stands for the bookkeeping, and the `consumed` entry goes behind a switch.** This settles 43, which Welt gave to Claude in the cloud, against the "new reference" the PC seat understood from him in its own chat and recorded on `codex/outcome-memory` (`370fa85`).
    - **Kept:** the PC seat's new reference for what nobody reads: `records`, the charge numbers, `observations` on a step, `place` and `since` on an expense. Its comparison of ten days on main with ten on the branch showed that nothing main writes changed.
    - **Behind a switch, off by default:** the `consumed` entry. The page shows entries and the owl reads them at night, so it can change what he is told. It goes on after someone has looked at what the owl and the page do with it.
    - **So the reference is recorded once more,** with `consumed` off, in a commit that says so.

49. **A dropped answer is not a no** (Welt left it to Claude, 17 November). When the PC went away between his decision and his yes or no to an offer, the world counted a no: the refusal was recorded and the offer waited a week. Now the offer is not made at that moment and stays open for the next (`world/engine.py` `ask_choice`; `tests/test_choice_away.py`). A real no counts as before. It acts only when the PC drops mid-answer, so it needs no switch.

## Still open

- The ten calls under "What Welt decides" in `WORLD-2.md`, beyond week 0.
- Whether the two rules of 38 also bind the PC seat.
- **Whether an adapter gets a day of its own.** No adapter has run a day in his world: each stopped at its gate first (T29, the forty-case re-audit, Training 3's data gate). Since week 0 a fair day is possible: one saved morning, two forks, plain Qwen against the adapter, the same seeds, read by state and by text (`tools/fork_diff.py`, `world report --health`). It needs T67 first, because today an adapter that is set reaches the owl, the letters and the yes-or-no as well. Claude's advice, 16 November: not for the Training 1 adapter, which changed facts in 12 of 40 rewrites; make the fork day the entry test of the next adapter. Loading an adapter is a hard limit either way.
- **The file's next act** (`pc/FILE-NEXT-ACT.md`, seven calls) waits for Welt's pen (42).

## Ideas, not yet decided

- **A notebook of the age.** The owl keeps a short running summary (about 1,000–1,500 characters) of what he has come to understand about this century: machines, institutions, events, people, and how his view of each has shifted. It enters his prompt every day, so what he learned weeks ago stays in front of him. It records only what he met and thought; it never steers him. Reason: today his prompt remembers only the last moments and the owl's gist of three nights, so older discoveries are allowed by the 1831 gate but fade from view.
- **An inbox.** People can send him emails, which he reads on a device in the world and may answer. Open questions: how mail gets in (a real address the Pi reads, a form, or Welt forwarding by hand), who approves it, whether his answers are public, and how he comes by an address in the world.
