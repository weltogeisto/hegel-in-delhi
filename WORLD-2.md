# The world, phase two

Written by Claude on 15 November 2026, at Welt's request: improve the world to improve the simulation. This is a plan, not a go. Every packet in it waits for Welt's word, like T39–T45.

**The idea in one line: in phase one Delhi answered him. In phase two Delhi has a day of its own.**

Phase one built a referee. The world owns the clock, the purse and the rules, and it says no correctly: closed is closed, and cash cannot go below zero. That work holds. The record now shows the other half. Seven in ten of his moments open with someone answering what he has just said. The world brings him something he did not start about twice a day. Today the world answers one verb, *talk*, and so he talks.

A referee makes a fair game. It takes a city to make a life. Phase two builds the city: a Delhi that holds what is said in it, offers what a man like him would cross the road for, changes because he was there, and goes on when he is not.

In the season plan (`PLAN.md`) this sits inside Act 1. It is what makes opening night worth opening.

## Where the world stands

Measured on 15 November on the shadow record, with a tool that is new with this plan (`python3 tools/world_health.py --ref origin/shadow`), and from the files named. A moment is one decision his mind made, on a day of at least 20 thoughts.

| What | Now | Beside it |
|---|---|---|
| Full days with a mind | 8 of the 35 since the shadow world began | the PC's hours are the scarce thing |
| Moments that open with the answer to his own words | 70% | outside his house, 77% |
| Moments where "nothing in particular happens" | 15% | at home, 22% |
| Moments where the world brings something he did not start | 6%, or 1.9 a day | the stand-in mind, walking far more, meets 1.6 a day |
| Moments at home | 51% | eight places in all |
| People who speak on a day | 4.4 | eight named people; Nidhi met on one day, so the lessons were never offered |
| Steps spent talking, reading, writing | 36%, 2%, 1% | a step of reading returns no text |
| Sights, art and music in what he writes | 1–5% | 40–42% of his letters from three journeys (`pc/PARIS-BACKTEST.md`) |
| Philosophy proper | 17–30% | 1–2% of the letters |
| Notions of his system per 100 words of thought | 3.57 | 0.17 in the letters; 2.55 in the Philosophie des Rechts |
| Food and the body in his thoughts | 25% | 4% of the letters |
| Cash on Day 46 | ₹6, and about ₹17,800 owed | the letter from Munich pays this (`DECISIONS.md` 33) |
| The file | one written beat left, due on his 20 November | `plot.json`: "The ending is not written." |

Three moments of Day 46 show the shape of the gap.

- **10:49.** Tea costs ₹20 and he has ₹6. Sunil's voice pours him a cup anyway, and a quarter of an hour later the world refuses the purchase. The page shows a kindness. The record holds nothing: no gift, no tea drunk, nothing owed in thanks.
- **About 10:20.** Shri Hegde tells him to be back "before the gas guy arrives at noon". No such visit exists.
- **12:49.** Ramesh says he will come tomorrow morning. Nothing holds him to it.

Each time a voice says something the world does not know. That is one gap. The table shows the other: the world has little of its own to say.

## What phase one settled

- **Code owns the facts.** The checks work, and this plan does not reopen them.
- **Selection did what training could not.** The filter cut echoes from 16.5% to 6.6% with no weights changed (T49). Two adapters did not beat plain Qwen, and Training 3 stopped at its data gate.
- **Instructions move his register.** The M1 confirmation passed.
- **The world decides what he can attend to.** His Delhi offered tombs, a market and an institute's gate. He philosophised, ate and counted his money.

The last line is why phase two is about the world.

## The rules of phase two

1. **The world offers and never steers** (`DECISIONS.md` 2 and 8). So the world is gated on what it offers and what it records. What he does with it is read, and never gated. A target for his behaviour would be steering under another name.
2. **Claude may write the world, never the man.** Places, events and storylines are world content, as the venues of `pc/CULTURE.md` are. Everything said and thought inside it comes from the local model. No world text is ever a training target (`mind/train/README.md`).
3. **One owner for every fact.** If a thing matters later (a gift, a promise, the state of an order), the engine holds it. Prose may describe it. Prose cannot create it.
4. **Additive, behind switches, one at a time** (`DECISIONS.md` 31). Old day files stay readable, and a switch set back restores the old world byte for byte, as `HEGEL_CULTURE` does.
5. **Experiments are forks.** A simulated life can be copied at a morning and lived twice, with the same seeds and feeds. It is the one fair comparison a single Hegel allows. A past day replayed is another day by its fourth step: in T39's replays, 152 of 156 cases had different prompts across seeds (T49).
6. **The letters are a compass, with one journey kept back.** Tuning looks at the Netherlands and Vienna. Paris, the journey a later backtest would rebuild, stays out of every tuning loop until the end.

## Six chapters

### 1 · The instrument

**Why.** The nightly report says how the mind did. Nothing says how the world did. And the rehearsal cannot rehearse phase two: `simulate` builds the world without the culture switch, and each `--date` starts again from the repository's day files, so a month cannot be lived in rehearsal. In a scratch driver, a chained month with the stand-in mind took ten seconds.

**What.**
- **World health in the nightly report:** the row of `tools/world_health.py` beside T19's row.
- **The step says what opened it.** A field `opened` names the beat, the papers, the greeting or the gallery, so the read stops depending on wording.
- **Rehearsals that chain days and know the switches:** `simulate --days N`, with the world built as the tick builds it.
- **Four scripted stand-ins:** one says yes to everything (today's), one says no, one stays home, one walks. They test the world's mechanics. They say nothing about his choices.
- **Forks:** one command copies a saved morning into sandboxes with different switches and the same seeds and feeds. Every comparison carries a control fork, the same world twice, which gives the band of noise.
- **The funnel:** for each offer, event and venue, how often it was possible, shown, taken and declined.
- **Blind tests that can see.** A gate of 16 in 24 finds a true preference of 65% about half the time, and a rubric difference under 0.4 on a five-point scale is below what one judge can detect. Phase two seals 100 situations by scene family. Soft qualities are judged as pairs, in both orders. Welt labels fifteen to twenty pairs of a packet, drawn where the arms differ; Claude judges all of them blind; the result is corrected by his labels and carries an interval.

**How we know.** The tool reproduces the table above. A stand-in month runs in under a minute. Two forks with the same switches give identical days under the stand-in.

**What it buys.** Two or three experiments a week on frozen moments, where there was one, and one slot a week for forked days.

**Cost.** Claude, about a week. No GPU, nothing live.

### 2 · Truth: what is said, the world can hold

**Why.** The three moments above. And the easy fixes are known not to work. In a year of simulated commerce, three in four false claims of payment came within a day of the agent reading the true ledger. A better memory left narrators' conflicts with their record where they were, 60% to 59%. Showing a voice the truth is not enough (`research/WORLD-2-SOURCES.md`, section 1).

**What.**
- **Speech moves nothing.** What a voice says is a trace. State moves only by an act from a closed menu that the engine has checked: gives, puts on the tab, charges, promises, invites, declines. A wrong act is refused with its reason, as his decisions are. Sunil's cup becomes a gift and a snack.
- **Voices write around slots.** Where a fact belongs (a price, a balance, the day an order is ready), the voice writes a placeholder and the engine fills in the value.
- **Every reply is audited before he hears it.** A check reads the prose for a state the record does not hold: ready, paid, delivered, came, will come. It asks once more. What still stands reaches him marked as someone's word, not as an event. The audit is the engine's. A list of claims that the voice fills in about itself would make it the judge of its own case.
- **Each voice sees its own side of the record.** Qwen3.8-27B, his own model, uses what its character could not have heard. Giving a character only what it observed removes that.
- **Storylines as protocols.** One registry gives each thread its states, its legal moves, its parties and what each party may say: the tailor's order, the file, the lessons, the column, the loan, the letters. Each move has preconditions and effects. What `voices.recorded_facts` writes by hand for three people is then generated for all.
- **Promises come due.** A promise is a record with an object and a date. The engine refuses a second promise on the same thing, and resolves each one: kept, broken with a reason, or lapsed. Ramesh's word becomes one.
- **What was said stays a quotation.** In memory a claim keeps its speaker, its date and its words. A summary turns "I am working there for now" into "he works there", in every model tested. And each source counts once, however often it is retold: today one encounter reaches him three times, through his last moments, the owl's gist and his recall.

**How we know.** T40's bars on its 40 contexts, with three arms: today's voices, typed facts in the prompt, and slots with the audit. Scene success up by 0.20, unsupported claims of a closed state halved, no new reversals in the clean controls, voice and argument no worse in blind pairs. Beside them, what the audit misses in 100 replies read by hand. In the paper city (chapter 5), every thread can reach an end and no state is without an exit.

**Cost.** Claude builds. The PC seat runs about 360 short calls, 1 to 2.5 GPU hours in the spare slot, then one night of forks.

### 3 · Breadth: a city worth leaving the house for

**Why.** The Paris profile. Abroad he looked, listened and walked. Here the world answers only when he speaks.

**What.**
- **Museums, concerts and plays.** Built, and fifth in the order of `DECISIONS.md` 34.
- **The street** (`HEGEL_STREET`). A deck of things that happen where he is: a wedding band tuning up, schoolchildren counted at the tomb's gate, a cricket match on the lawn, fog over the gardens. Each card has its places, season, hours and weather, a cooldown, at most 240 characters, and sometimes a passer-by he may speak to. One is drawn by date when nothing else opens the moment. Every card enters through the world's own check, which refuses one that tells him what to do, names a living person, invents a place or has no cooldown. Welt reads each batch before it goes on. The first batch is 60 cards.
- **Reading returns something.** Today *read* is a posture. It becomes a text: the article behind a headline, a longer passage of the book he took down, a public-domain book he bought.
- **A second ring of places,** chosen by the letters: what did he seek abroad, and where is its counterpart within a walk? A church and its music, a reading room with German papers, a collection of natural history or craft, a promenade with company, a table for cards, the post office his letters leave from. Candidates and walking times come from OpenStreetMap. Welt chooses.
- **The season as Delhi keeps it:** fog, the wedding months, Christmas, the Republic Day rehearsals.

**How we know.** Gated on the offer: empty moments from 15% to at most 5%, what the world brings from 1.9 to at least 6 a day, and every venue and kind of card within reach weekly for the walking stand-in. Read, not gated: stage 1's profile again on the days after, with both coders.

**Cost.** Claude writes. Welt reads a batch in half an hour. One night of forks per bundle.

### 4 · Depth: a world that remembers him and moves without him

**Why.** In 46 days two manuscripts, two theses that changed a word of status each, and a file that has stood at "come after fifteen days". Little he does comes back to him.

**What.**
- **The file gets its next act.** This one has a date: the last written beat falls on his 20 November. Claude drafts the file as a thread of six to eight states with months in it and several endings, none of them chosen. Welt edits it. The frame is his (`DECISIONS.md` 8).
- **People have a week of their own.** Each named person gets a small agenda in data that moves by date: a deadline, a visit, the wedding season at the tailor's. At the next meeting their card holds one line of what happened meanwhile. Code decides when they turn up, in bursts and not on fixed rounds. The model decides only what they say, and only when they meet.
- **Standing.** For each person, one small record, updated in place: the days met, what stands between them (owed, promised, given), and a regard that moves only on recorded acts: a debt paid or left, an appointment kept or missed, a gift. A regard that only sits in a prompt changes nothing, so the event says what follows from it: Sunil closes the tab, and Masterji asks for an advance.
- **Stakes come from rules.** Voices played by his own model are agreeable, and replayed stories drift cooler and leave their tensions open. A deadline, a refusal and Mr. Saxena's no are written into the threads. The world adds offers on top of his turns and never repairs a plot: in one comparison a manager that repaired the story cut the protagonist's agency from 0.44 to 0.27, and people with goals of their own kept it highest, at 0.68.
- **Word gets round.** A recorded act reaches one neighbour a day later. Khan Market knows he could not pay for tea.
- **An attempt may fail.** He may walk to a closed door and find it closed, with the time spent, instead of being refused in advance (the manual's §4.4). One scene family first.
- **What he has learned stays in front of him.** The notebook of the age, which is still an idea in `DECISIONS.md`, built as an index and not a summary: for each thing of this century he has met, when first, when last, where in the record, and one line. And convictions the engine holds: the text, the criterion, the versions (the manual's M3), with evidence counted by source.
- **The owl tells what was unusual for him.** Sifting a record by what is dramatic in general did not predict what readers enjoyed. The health row tells the owl what departed from his own days.

**How we know.** Threads moved in a week. Obligations resolved. How often he goes back to someone and uses what passed between them, by the days between. T41's tests at the same budget. Convictions judged in blind pairs for whether a change was earned by the record.

**Cost.** Mostly CPU. Forks as in chapter 3.

### 5 · Tuning: the world against the man

**What may be tuned.** The side of opportunity only: places, hours, prices, wages, the conditions of offers, people's schedules, how often things happen, the wording and order of what is listed. Never his instructions, and nothing that tells him what to want.

**The loop, at four speeds.**

| Speed | What runs | What it answers | Budget |
|---|---|---|---|
| The paper city | 100 settings × 4 stand-ins × 28 days, no model | Which settings are impossible: an offer nobody can reach, a shortfall with no exit, a working stand-in that cannot close the month, a kind of thing the letters are full of that the world offers less than weekly | about 400 months, a little over an hour on one core |
| Frozen moments | real Qwen, short calls: 8 wordings raced down to 2, then 24 unseen moments, used once | Which wording and order of listings and offers he takes up, with the scoreboard's bars as constraints | about 480 calls |
| Forks | real Qwen, whole days: 7 mornings × 2 worlds, and one week per world for what carries over | Whether a changed world gives a different life | about 1,200 calls, 3.5 hours |
| Shadow | one switch, blocks of at least four days, the old world as a fork beside it | Whether it holds in his real days | his days |

**Guards.** A cap on length. Options in shuffled order. An alarm when any offer is taken more than nine times in ten: an offer nobody refuses is an order. The stand-ins are trusted for mechanics and never for choices; before their rankings are used, one check that they rank six world variants as real Qwen does. After a bundle is adopted, each older rule is switched off once, alone, to see what it was holding.

**Two early tests of what is put in front of him.** The money line stands in every prompt, and hunger is announced as an event. Food and money fill 29% of his decision thoughts and 4% of the letters. Whether a man is told the state of his purse at every step is the world's choice. Both changes touch his prompt, so both go through the ratchet as prompt changes do.

**How we know.** The health table, the funnel, the economy's bands (days of runway, days with the kitchen shut, exits open at each shortfall), and the profile's distance to the two journeys. The profile is read beside two nulls, plain Qwen with no persona and a generic professor of the 1820s, because a twin built from a person's own answers has matched that person only a little better than a model with no persona at all. Paris is read once, at the end.

### 6 · Post-training: what the new world makes trainable

Training follows the world. A sweep of the recent evidence on 15 November gives the starting fact, and it is a sober one.

**With the filter live, the world's verdicts have little left to teach.** On his decisions they leave about 1% refusals and 2–7% echo. Weights trained on them could save a quarter of a call. The open gap is argument (2.65 of 5) and voice (3.05 of 5), and no check of the world's labels those. Only Welt's judgement can. The published record gives a persona adapter little hope: a personality-tuned Qwen of 7B was no better at role-play than its prompted self. The one clear win for weights is writing from a brief on an author's own subjects, on a larger model trained in full.

So phase two supplies the two things training lacked: labels a rule can verify (the audit of what the voices say), and situations rich enough for Welt's judgement to be worth asking.

| Rung | What | The label comes from | When it runs |
|---|---|---|---|
| 0 | No training. The best setup for every job; a sealed set of 100 situations by scene family; the same arm run twice, for the band of noise; one arm with two or three of his own accepted thoughts as examples | – | First, always. A few GPU hours. Every later rung must beat the best arm here at equal calls |
| 1 | **The voices.** One adapter for the people he meets, so that a reply passes the audit at the first try | the engine's audit and its check on acts | Only if T57 leaves a residue that the audit and one retry do not remove, and with the audit's misses counted by hand, because weights learn a checker's blind spots. Sample, filter, train, sample again; about 1,000 kept replies |
| 2 | **His thoughts, by Welt's hand.** Welt chooses blind between two draws the world accepted | Welt | On his word. 300 pairs to train and 100 sealed: about seven hours of his time. It must beat the examples arm built from the same choices, in 61 of the 100. Under 55, voice by weights is closed for the season |
| 3 | His writing sittings only: from a brief Qwen writes to the passage he wrote | his texts | Parked. It would be a third attempt at his voice |

**Not run, and why.**
- **The filter distilled into weights.** There is a quarter of a call to win.
- **Preference pairs from the world's labels, trained once.** One situation in six gave a contrast, and one-shot offline pairs are the weakest recipe in the recent comparisons.
- **Reinforcement learning on the 3090.** Most rollouts would carry no signal, and the card has 1.5 GiB to spare.
- **Continued pretraining on his books.** Nothing shows it moves voice or conviction at 3.4 M tokens, and our first adapter agrees.
- **Steering vectors.** In llama.cpp they are set when the server starts, so they would reach the voices and the owl too.

**How a rung runs, if one does.**
- **The recipe:** plain LoRA, rank 16 and alpha 32, on all linear layers. The variants finish within a point or two once the rate is tuned, and two of them do not survive conversion for llama.cpp.
- **Serving:** one adapter per job. The server starts with `--lora-init-without-apply`, and every request names its adapters, because a request that names none takes the server's default. A change of adapter between requests costs one full reading of the prompt, and requests with different adapters do not share a batch. That price is measured in rehearsal first.
- **Diversity is a gate.** Post-training narrows what a model says. Every adapter is read for it against plain Qwen.
- **Tests with power.** 28 of 40 finds a true preference of 65% one time in three; 61 of 100 finds it five times in six. A bar of 0.25 on twenty thoughts an arm lies inside the noise. Phase two's blind tests use the larger form.
- **The plumbing is checked:** trained on one 4-bit format and served on another, prompts cut at a default length, a base that is 20.8 GiB on disk where `pc/TRAINING.md` says about 17.

Each run still needs Welt's go, by day and watched. The data rule holds. One bounded run closes each question.

## The order

There are three ways to open phase two.

1. **Truth first.** The audit and the threads, then breadth. Best if the long record matters most before anyone watches. Slow to show.
2. **Breadth first.** The street and the second ring at once. Best if opening night is near. Every new person is also a new voice that can say what the world does not know.
3. **The instrument first,** then truth and breadth side by side. Best when PC hours are scarce, because everything after it is tested in forks and costs him no days.

**Recommended: the third.** Full days are the scarce thing, eight in thirty-five. One week of work with no GPU makes every later test cheaper and comparable.

| When | Claude in the cloud | The PC seat | Welt |
|---|---|---|---|
| Week 0 | Chapter 1. The file's next act, drafted | The order of `DECISIONS.md` 34, as decided | The file's next act, before his 20 November |
| Weeks 1–2 | Acts, slots, the audit and threads. The street, first batch | T57's screen by night. Forks | Reads the batch. Chooses the second ring |
| Weeks 3–4 | People's weeks, standing, a failed attempt, the notebook | Forks for each bundle. Switches go on, one at a time | Goes on each switch |
| Week 5 | The paper city's first wave. The two tests of chapter 5 | Frozen moments. Paris stage 2 | Reads the profile, then Paris |
| Week 6 | The read of phase two | Rung 0: the sealed set, the band of noise, the examples arm | Rung 1 or 2, or neither. Opening night, when Act 1's gate passes |

The weeks assume the PC keeps its days. All of it is about 25 GPU hours in the spare slot or by night, with no training (`DECISIONS.md` 30).

## What Welt decides

1. **Go for chapter 1.** No GPU, nothing live.
2. **The file's next act.** Claude drafts, Welt edits. It has a date.
3. **The street:** a first batch of 60 cards, for his reading.
4. **The second ring,** and whether he may go further than he can walk (an auto, the Metro). That would widen the map beyond its two square kilometres.
5. **Paris kept back** from every tuning loop.
6. **The budget for forks:** about 25 GPU hours over six weeks.
7. **Reading returns text,** starting with the papers.
8. **The ladder of chapter 6.** Rung 0 runs with the forks. Rung 1 waits for chapter 2's screen. Rung 2 costs about seven hours of his own judging, and is his to offer.

## What phase two leaves alone

His instructions and the direction of his convictions. The data rule and the hard limits. The public switch. Act 1's gate. The old results, which stay as recorded.

## What the field warns against

- **A voice that reports on itself.** It is a judge in its own case, and the true record in its prompt does not stop a false claim. Hence the engine's audit.
- **A summary as the record.** It flattens what was said, hardens it and counts it twice, and it does not keep what will be needed later. Hence quotations, sources counted once, and a ledger for what he must act on.
- **A manager that repairs the plot.** It takes turns from the protagonist. Hence offers only.
- **Hitting the mix by imposing it.** Priors can match an activity profile and still break a person's routines. Hence a profile that is read and never gated.
- **Tuning on the test.** On his own model, a gain on a small case set reversed on held-out cases. Hence the journey kept back and confirmation cases used once.
- **Text that grows.** Optimised prompts get longer and gather rules for single cases. Hence the cap.
- **Stand-ins of another mind.** A fixed-rule shopkeeper earned eight times what the best model did in the same shop. Hence mechanics only.
- **Prices alone.** Simulated agents hoard and seldom reprice. A fuller purse may change little. What is on offer may change more.
- **Gates that erode.** An acceptance gate can delete a rule whose work another rule was covering. Hence the switch-offs after adoption.
- **Small tests read as verdicts.** Rubric differences under the judge's own noise, and closed-loop conclusions from single steps. Hence pairs, intervals and forks.
- **Long runs lock in.** Persona runs settle into familiar channels whatever the world holds. The health table watches for it.

Each has its source in `research/WORLD-2-SOURCES.md`.

## Proposed tasks

All wait for Welt's word. Numbers continue `pc/TASKS.md`.

| Task | Owner | What | Done when |
|---|---|---|---|
| T54 · world health | Claude, then the PC seat | The health row in the nightly report; the step's `opened` field | A night's row arrives on shadow by itself, and Day 12's row matches the tool's test |
| T55 · the rehearsal learns the switches and the calendar | Claude | `simulate --days N`; the world built as the tick builds it; four stand-ins; forks; the funnel | A stand-in month in under a minute; two equal forks give identical days |
| T56 · the file's next act | Claude drafts, Welt edits | The file as a thread with months in it and no chosen ending | On main before his 20 November, behind the existing beats |
| T57 · what the voices say (T40 with G8) | Claude, then the PC seat | The menu of acts, the slots, the audit, each voice's own side of the record; 40 contexts, three seeds, three arms | T40's bars, declared before the run |
| T58 · threads | Claude | The registry; the tailor's order first, then the file, the lessons, the column, the loan, the letters | Every thread reaches an end in the paper city; no state without an exit |
| T59 · the street | Claude writes, Welt reads | 60 cards, the linter, `HEGEL_STREET` | Off by default; byte for byte the old world without it |
| T60 · reading returns text | Claude | The papers first, then his shelf | A step of reading opens the next moment with what he read |
| T61 · the second ring | Welt chooses, Claude builds | Candidates by the letters' profile, walks from OpenStreetMap | After culture's first week is read |
| T62 · people's weeks and standing | Claude | Agendas, regard from recorded acts, word that gets round | One line of "meanwhile" reaches a voice's card; forks show callbacks |
| T63 · an attempt may fail | Claude | One scene family: the closed door | Time is spent, the outcome is recorded, no loop |
| T64 · the paper city, first wave | Claude | Tunables declared; 400 months; the settings ruled out | The surviving region and the funnel, in a file |
| T65 · the profile again, and Paris stage 2 | Claude, the PC seat | Stage 1 on the days after each bundle; stage 2 as filed | Read by Welt |
| T66 · rung 0 | Claude, then the PC seat | 100 sealed situations by scene family; the same arm twice; the examples arm | The band of noise is in a file, and every later gate cites it |
| T67 · rungs 1 and 2 | Welt, then Claude and the PC seat | The voices' adapter, if T57 leaves a residue; his thoughts by Welt's hand, if he offers the hours | Decided after T57 and T66 |

## Sources

- `research/WORLD-2-SOURCES.md`: what four sweeps found on 15 November, about eighty works on worlds, memory and judging, tuning and post-training, with what each means for us. Every arXiv number was checked against arXiv's record that day.
- `research/watch/2026-11-15.md`: the fortnight's new papers, and the changes they suggest to T41, G4 and T50.
- `tools/world_health.py`, with `tests/test_world_health.py`: the table at the top.
- Scratch runs on 15 November, not in the repository: a chained month with the stand-in mind in ten seconds, where the world brought it 1.6 things a day, and 2.6 with the museums and the letter on.
