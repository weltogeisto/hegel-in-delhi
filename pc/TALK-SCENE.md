# HEGEL_TALK_SCENE: a talk at the IIC is a scene

Switch: `HEGEL_TALK_SCENE` (off by default; `world/config.py`, `make_world`). Tests: `tests/test_talk_scene.py`.

## What went wrong on Day 54 (24 November, Guru Nanak Jayanti)

He had agreed to give a talk at the IIC at 18:30 and had written 4,146 words of notes for it. At 18:20 the guard at the library
told him the officer was not coming and the Centre was shut; at 18:30 the beat fired, he said one sentence, an hour passed in one
step, and no lecture was ever written; the guard answered every time, the cheque included. The Centre was open until 21:30 and the
officer was there.

## What happens at each step of a talk, switch on

1. **Any voice, anywhere (B).** Every voice call (a reply or a greeting) is given one more recorded fact, from the world's own data
   (`World.open_line`, `holidays.json`, `World.hours`): today's holiday name if there is one, and the place's hours today.
   "Today is Guru Nanak Jayanti. India International Centre is open until 21:30 today." Before opening: "... opens at 09:00 today.";
   after closing: "... closed at 21:30 today."; a place shut all day (the Directorate on a holiday): "... is closed all day today."
   A place that is always open (his home) gets the holiday line only. It stands among the voice's recorded facts, which are marked
   authoritative over dialogue, so a voice cannot invent a closure.
2. **The talk beat fires (18:30).** The two talk-day beats in `offers.json` (`iic_talk_day`, `iic_talk_day2`) carry
   `"talk": {"minutes": 60}`. `World.fire` then writes `state["talk"] = {beat, place, by, until}`: where it is, whom the beat brought
   (`brings`: the officer) and the time it is over plus 30 minutes (`TALK_GRACE`).
3. **The right person answers (A).** While `state["talk"]` is live, `Engine.reply` offers `voices.pick` only the people the beat
   brought and the people he knows (`World.in_the_hall`): a background person who merely works at the place (the guard) is not
   among them. An explicit `speaks_to` naming the guard is set aside. If that would leave nobody, the full list stands. The talk is
   forgotten when he is at another place, or 30 minutes after it ends (`World.talk_on`, called from `situation` and `in_the_hall`).
   The cheque at 19:30 is paid by the engine as before; the officer is the one who answers there.
4. **The lecture (C).** In the same step, after his opening sentence has been answered, `Engine.give_talk` makes one writing call
   (`Engine.lecture`, schema `talk.LECTURE_SCHEMA`, 1,600 tokens): about 600 to 800 words, spoken to the hall. The request is built
   as `write_chat` builds one: the decision's conversation, then the ask, then the index of his works (`works.manuscripts`) and the
   excerpts of his latest three works that `Memory.manuscripts` gives (the first and the two latest sittings of each, from the day
   files' `writing` entries, up to 6,000 characters, nothing later than now). That is what is cleanly reachable; the 4,146 words of
   notes of Day 54 are reached to that extent and no further (the `tail` in `state["works"]` is not used: the excerpts contain it).
   It passes the same checks as his other writings: names from after 1831 he has not met (asked once more, then dropped, as in
   `write_chat`), the claim guard (`check_writing`), and the sensitive-word mark. It is filed with `works.file` as an `essay` titled
   "Lecture at the IIC: <his title>", with `about` saying it is a lecture. It appears in the day's entries (`k: writing`) and in
   `state["works"]`. No magazine fee is triggered (`on_writing` is not called) and it is not posted. It is a new work, never a
   continuation.
5. **One question (D).** If the lecture was filed, one voice call is made for a new cast entry, `hall_listener` ("a listener in the
   hall", `cast.json`, marked `"switch": "talk_scene"`, no place of its own so never "present"). `voices.render` takes a `lead`
   that replaces "He says: ..." with: the lecture's title and its last paragraph, and the request for one question. The question is
   entered as a `said` entry, kept on the step as `step["hall"]`, and opens his next situation as the officer's reply does (where
   the step ends; kind `reply`). He answers it in his next step as he answers anyone; with the guard set aside, the officer
   answers that, and closes, and the cheque is handed over at the end of the hour as today.
6. **Away or unusable.** If the mind is away or the lecture reply is unusable (not JSON, under 100 words, names from 1831 twice), the
   talk still happens as before: the beat is fired, the officer answers, nothing is stored and no question is asked.

## What is stored

`state["talk"]` while a talk is live (dropped after); a `writing` entry and a `state["works"]` item for the lecture; a `said` entry
for the question; `step["hall"]`. Nothing else.

## What stays as it was

With the switch off nothing reads the `talk` key in `offers.json`; `hall_listener` is filtered out of the cast on load (as
offers that name a switch are); `voices.render` and `Engine.voice` pass nothing new; `situation`, `reply` and `apply` take the old
paths. `tests/test_opened.py` passes without re-recording. No other switch's behaviour is touched.

## Not done

Nothing of A to D is left out. Not covered: the 18:20 arrival (before the talk is on), where the guard's invention is met only by B.
The officer's closing words are whatever she answers to his reply to the question; there is no separate closing call.

## Before it goes on

- **It reaches more than talks.** The line of step 1 goes to every voice at every place, every day. That is a change to all the voices, as `HEGEL_VOICE_REPAIRS` was, and that one failed its check on a side effect nobody expected.
- **So it is rehearsed first:** a fast-lane night of one-day runs, the switch off and on, from mornings with a holiday and without. What is read: voices that state a closure or an opening hour against the world's own hours; what the voices offer for sale; the day's health; and, on a morning with a talk, the lecture, the question and who answered.
- **Then Welt's word.** He has no talk on his calendar now; the next one comes with a new invitation, or with `iic_talk_again` if one is missed.
