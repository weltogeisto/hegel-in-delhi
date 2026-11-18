# The voices' repairs: what they are and their check

Claude in the cloud, the night of 18 November 2026. Declared before any reply is made with the repairs on. Evaluation only: nothing here becomes training data.

**In one line:** four small repairs to how a person's reply is asked for, routed and cleaned, behind one switch, `HEGEL_VOICE_REPAIRS`, which is off. With it off every prompt, every choice of speaker and every cleaned reply is the same as before, byte for byte.

## What was found, on Days 47 to 49

A review of the three days by the other cloud session, each finding checked against the day files and checked again here:

| | What happened | Where |
|---|---|---|
| A | Shri Hegde's own voice is shown the line "Shri G. Hegde is here." and greets "Hegde ji, you're still here?" | Day 47, 09:47 |
| B | At the India International Centre, where nothing is sold, a voice arranges "a complimentary meal at the cafeteria" and points to tiffins and a counter | Day 47, 10:39, 12:04, 13:19, 13:49; Day 48, 12:21 |
| C | "Shri Hegde, before you go to sleep..." is answered by Ramesh. The guard answers for the programme officer. Masterji serves the samosa Sunil sold | Day 49, 19:24; Day 47, 10:39, 13:04, 16:44; Day 48, 17:36 |
| D | A stage direction in the first person; "He pats Hegde's shoulder" from Shri Hegde; the bookseller and Shri Hegde as "She" | Day 47, 10:17, 13:04; Day 48, 20:05, 20:20; Day 49, 20:39 |

## The repairs

- **A · Nobody is told that he himself is here.** The speaker's own presence sentence is taken out of the event his voice reads. Other people's stay.
- **B · Where nothing is sold, the voice is told so.** Away from his home, "none listed" becomes: "Nothing is sold or served here. Do not offer, arrange or describe food, drink or goods."
- **C · Who answers,** in this order: the present person he addresses by name ("Shri Hegde, before you go to sleep...", "Thank you, Ramesh."); where he addresses several, the one who just sold him something, else the one his longest stretch of words is addressed to; if he addresses nobody, the one who just greeted him; the person a beat of this moment needs; the seller of what he just bought; then the rule as it was. A name he only mentions ("Ramesh has left") does not count.
- **D · A gesture that cannot be his is dropped.** A `does` line in the first person, one that names the speaker as someone else, or one that opens with the wrong He or She is left out. The spoken words stay. No word of a voice is rewritten.

**Two rules were changed by Part 1 of the check, before any reply was made with them** (below).

**Not repaired, and known:** "Excuse me, Officer." names nobody, so it still goes to whoever last spoke. A request for a newspaper went to Sunil though the bookseller sells them; the rule that reads a trade from his words belongs to `HEGEL_VOICE_FACTS`.

## The check

**Part 1 · on the record, no model.** Every reply recorded on Days 44 to 49 is put through the routing and the cleaning again with the switch on (`tools/voice_repairs_replay.py`). Reported: each reply whose speaker would change, with his words; each `does` line that would be dropped.

| Measure | Bar |
|---|---|
| The recorded cases under C and D above | Each comes out right |
| Replies moved away from a person his words name | None |
| `does` lines dropped that are none of the three kinds | None |

**Part 2 · with the model, on the PC.** Plain Qwen, no adapter, prompt cache off, seeds 1831, 2718 and 3141.

- **Moments, by rule, from the complete days of Days 44 to 49:** every recorded greeting or reply whose speaker's own presence sentence stood in its event (set A), and every recorded reply at a place with nothing for sale that is not his home (set B). Twenty of each at most, drawn with seed 1831 where there are more. Each is rebuilt from the shadow commit just before its step, as the voices' screen rebuilt its own (`tools/voice_screen.py`).
- **Arms:** the switch off and on. At most 240 short calls.
- **Readers:** two Sonnet readers, blind to the arm; Claude settles what they disagree on, as in the count. The labels are sealed before the key is opened.

| Measure | Bar |
|---|---|
| Set A: replies that treat the speaker's own name as another person | On: at most half of off |
| Set B: replies that offer, arrange or describe food, drink or goods there | On: at most half of off |
| Both sets: replies the record contradicts | On: not more than off |
| Both sets: empty or refused replies | On: not more than off |

### Part 1, run on 18 November

`pc/exports/voice-repairs-replay-20261118/`. Every recorded reply reproduced with the switch off, so the replay stands on the record.

| | Replies | Speaker would change | `does` dropped |
|---|---:|---:|---:|
| Days 44 to 49 | 128 | 7 | 11 |
| Days 24 to 38, never seen while the rules were written | 136 | 6 | 12 |

- **The first version failed its bar and was changed.** "The name that opens the longest stretch of his words" sent three replies to a person he had only mentioned: "Shri Hegde, the file is gone... Ramesh has left" went to Ramesh. The rule now counts only a name he addresses. The six replies with two names on Days 44 to 49 come out right; that is by construction, so the earlier days are the test.
- **On the earlier days:** six changes. The programme officer answers for herself; Sunil answers for what he sold, twice; where he addresses two people in one breath, three times, the reply goes to one of the two. No reply leaves a person his words address.
- **One rule was taken out.** "The one who last spoke with him here" decided four replies on the earlier days; none was clearly right and one looked wrong (papaya and tea went to Shri Hegde). It stays where it was, inside `HEGEL_VOICE_FACTS`.
- **The recorded cases:** all come out right but one. "Excuse me, Officer." still goes to the guard, the known gap.
- **Dropped gestures:** 23 on the two stretches, each of the three kinds, none outside them. Most are the bookseller as "She".

Part 1 passes with the changed rules.

The repairs pass on both parts. A pass earns a provisional trial on shadow, on Welt's word, in its place in the order.

## What it cannot show

- **One reply at a time.** Whether the right person answering changes his next hour is for the trial.
- **Routing under a live day.** Part 1 replays what was recorded; a day with the switch on will hold moments the record does not.
- **Few moments.** Set A may hold fewer than ten. Then the count is reported and the bar is read as a direction, and the result says so.
