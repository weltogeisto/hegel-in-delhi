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

## Still open

- Nothing at the moment.

## Ideas, not yet decided

- **A notebook of the age.** The owl keeps a short running summary (about 1,000–1,500 characters) of what he has come to understand about this century: machines, institutions, events, people, and how his view of each has shifted. It enters his prompt every day, so what he learned weeks ago stays in front of him. It records only what he met and thought; it never steers him. Reason: today his prompt remembers only the last moments and the owl's gist of three nights, so older discoveries are allowed by the 1831 gate but fade from view.
- **An inbox.** People can send him emails, which he reads on a device in the world and may answer. Open questions: how mail gets in (a real address the Pi reads, a form, or Welt forwarding by hand), who approves it, whether his answers are public, and how he comes by an address in the world.
