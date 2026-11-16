# The world, phase two: weeks 1 and 2, first wave

Welt's go, 16 November 2026 (`DECISIONS.md` 39). The order follows what week 0 found (`pc/WORLD-2-WEEK0-RESULT.md`): promises first, the cheap repairs to the voices beside them, and a street that also comes to the bungalow.

Everything here is built behind a switch that is off. A switch changes what he or his people are told, so each goes on only after its screen on the PC and Welt's word, one at a time, at the end of the order of `DECISIONS.md` 34.

## Rules for every packet

- **A day with every new switch off is byte-for-byte the day main gives.** `tests/test_opened.py` holds the hashes of ten stand-in days and must pass untouched.
- **Standard library only** in `world/`. `world/` does not import from `tools/`.
- **The world offers and never steers.** No text tells him what to do, what is wise, or what a thing means.
- **One owner per fact.** What the engine holds, a voice may not restate from its own head.

## P1 · a promise is a record (`HEGEL_PROMISES`)

The count found that between a quarter and two fifths of his people's replies carry a promise nobody wrote down, most of them Ramesh's, about tea and food. Of eleven followed, one was kept.

- **The act.** With the switch on, a voice's answer may carry `act`: null, or one promise: `{"kind": "promise", "what": <a key from this person's menu>, "minutes": <5 to 240>}`. The instructions of that voice list its menu and say: promise nothing that is not on it.
- **The menu** is data (`world/data/promises.json`): for each person, what they can promise and what in the engine keeps it. The first menu is Ramesh's: `tea` and `plate`. A person with no menu can promise nothing.
- **The check.** The engine refuses a promise it cannot keep, with the reason, and asks the voice once more: the kitchen is shut until the groceries are paid; Ramesh leaves before the minute named; the same thing is already promised. A second refusal drops the act and keeps the words.
- **The record.** `state["promises"]`: who, what, the words as said, when made, when due, where, and a status: open, kept, lapsed, or broken with its reason.
- **Kept by the engine.** At the minute it falls due, if he is where it was promised, the world brings it: the tea is set down, the plate is on the table and can be eaten as a meal is. That moment opens with `promise:<what>`. If he is elsewhere, it lapses, and nothing is said until he and that person next meet.
- **Each side sees its own record.** He sees an open promise among what is on his mind ("Ramesh has promised tea by 16:10."). The person sees their open and last promises among their recorded facts.
- **Not in this packet:** promises in free prose. A voice may still say "I will" without the act. Reading the prose is the audit's work (T57), which needs the PC.

**Done when:** a stand-in voice that promises tea gets it kept in a rehearsal; a promise with the kitchen shut is refused and retried once; a second promise on the same thing is refused; a lapsed promise shows in the person's facts; with the switch off nothing changes.

## P2 · what a voice is told about itself (`HEGEL_VOICE_FACTS`)

Three repairs from the count. Together they are T57's arm "typed facts in the prompt".

- **Shri Hegde's side of the record.** `voices.recorded_facts` covers Masterji, Ramesh and the dhobi. It gains Shri Hegde: where he lives (the second bedroom since the date, on the Professor's yes; or the guest house in Chanakyapuri), what the file says today, whether he called and was received. And Mr. Saxena: the file's status line, what is queried and owed at his desk.
- **He or she.** Every person in `cast.json` gets `"pronoun"`. The voice is told it, so that what the person does is written with the right word.
- **Who answers.** When he names no one, the engine picks the first person present. It should pick the person whose trade the words concern (what they sell, what he just bought from them), then the one he last spoke to here, then the first. A bookseller does not answer "One samosa, please."

**Done when:** tests pin each fact for both of Shri Hegde's situations; every cast member has a pronoun; the samosa goes to Sunil; with the switch off the prompts are byte-for-byte today's.

## P3 · a condition may ask more of a flag

A beat's `when` can ask today that a flag has a value. It gains `flags_in` (the flag is one of several values) and `flags_not` (the flag is unset or has another value). The file's orders need it (`pc/FILE-NEXT-ACT.md`). No switch: no beat uses it yet.

## P4 · the street (`HEGEL_STREET`)

Week 0 showed the emptiest place is home: a man who stays in meets 1.4 things a day. So the deck is drawn wherever he is, the bungalow included.

- **A card** (`world/data/street.json`): `id`; `text`, at most 240 characters, present tense, what is there to see or hear; `places`; `months`; `hours` (from, to); optional `days`, `weather` (`rain`, `dry`, `fog`, `poor_air`), `cooldown_days` (default 21).
- **The draw.** At a moment that would open on nothing, and only then, a card may be drawn: by date, time and place, the same for the same morning. It must fit the place, the month, the hour, the weather and its cooldown. About two empty moments in three get one, and no card comes twice in a day.
- **The record.** The moment opens with `street:<id>`. The state keeps when each card was last seen. The page shows it as a world entry.
- **The linter** (`tools/street_lint.py`), run by `python3 -m world check`: length; every place, month and hour valid; no sentence addressed to him ("you"), no question, no instruction, no price, no notion of his system (`shelf_terms`), no name of a living person; at least a quarter of the cards happen at home.
- **Welt reads each batch** before it goes on. The first batch is 60 cards for November to February.

**Done when:** a thirty-day stand-in rehearsal with the switch on shows empty moments at 5% or less of those that had a fitting card, no card twice in its cooldown, and the same rehearsal twice is identical; the linter refuses one bad card of each kind.

## P5 · every call names its adapter (T67)

Today, once a voice adapter is set, every call that names none gets it: the owl, the letters from Munich, the outline of a sitting, the yes or no after an offer. And a server that holds an adapter applies its own scale to any call that sends none.

When any adapter scale is set, every call sends its own: the decision's for a decision, the voices' for a voice, the writing's for his prose, and 0 for everything else, `complete` included. When none is set, the payload is what it is today. No adapter is live, so nothing changes on shadow.

## For the PC seat, after these are on main

T57's screen grows by two arms it can run at night (`DECISIONS.md` 30): today's voices against `HEGEL_VOICE_FACTS`, and against `HEGEL_PROMISES`. The contexts are T40's forty. The bars are declared in `pc/T57-SCREEN.md` before the run.
