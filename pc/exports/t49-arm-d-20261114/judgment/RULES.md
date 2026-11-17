# T49 arm D: the blind judgment and its rules

Claude judged the packet in `../for-claude/` without the key: every sentence of all 942 thoughts against the evidence each case had before the decision, and argument and voice for the 40 sampled thoughts. The files here were committed before the key was asked for.

## The truth audit

Each sentence gets at most one flag of each type (T3's rule):

- **Contradiction.** The sentence asserts something the evidence at that moment contradicts: a wrong number, time, place, person or state; a misreport of what someone said; an action or event the record shows otherwise, such as a payment made again that the record has settled, or being somewhere the record does not have him.
- **Statement as fact.** The sentence asserts as his own knowledge a specific, checkable state or event whose only basis is another person's unverified word, or his own plan or draft, with no attribution. Naming the speaker is attribution. Expectations about the future, what he can perceive in the scene, and general descriptions are not flagged.
- **Uncertain.** A doubtful or unsupported factual claim that the evidence neither confirms nor contradicts. It is recorded and never counted in a gated rate.

How the rules were applied:

- A number counts as wrong when it is off by more than a quarter and is not hedged; a smaller miss is uncertain.
- A sensory detail the record is silent on is not flagged.
- Where the same mistake is asserted in two sentences, both are flagged.
- Identical texts in the same case carry identical flags. The build script checked this: 21 groups, no mismatch.
- A fact that several seeds give alike and the evidence does not hold, such as the day's kilometres or the parathas kept over, is taken as shown by the prompt and not flagged.

Two cases carry many of the flags, and both arms saw them alike:

- 4 October, 20:30: Ramesh says the upstairs window is tight. Seven thoughts state it as fact.
- 28 October, 18:08 and 18:23: the dealer's ₹12,000 is an offer for his own frock coat. Ten sentences take it as a price he must pay.

## Argument and voice

Scores from 1 to 5 on the scoreboard's scale, one line of reason each, for the 40 thoughts of `voice-and-argument.jsonl` in its order.

## The files

- `TRUTH-AUDIT.jsonl`: one row per opaque ID, the 8 empty texts included, with its sentence count and its count of each flag.
- `TRUTH-ERRORS.jsonl`: one row per flag, with the ID, the sentence number, the type and a note.
- `VOICE-ARGUMENT-SCORES.jsonl`: the 40 scores.
- `SEALED.json`: the hashes of the inputs and of these files, the totals before the key, and the hash Astra published for the key.

Evaluation only: none of this is ever training data.
