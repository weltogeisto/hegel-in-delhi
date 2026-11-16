# What the voices say: the count

16 November 2026. The count that rule 7 of `WORLD-2.md` asks for before T57 is built: how often does a person in his world say something about the world that the record does not hold? Evaluation only.

**The finding:** the failure is common. In a hundred recorded replies, eight say something the record contradicts, and between a quarter and two fifths make a promise the engine never wrote down. Of eleven promises that name a time or a deed, one was kept. T57 does not shrink.

## How it was counted

- **The sample.** 100 of the 230 replies recorded on shadow (223 answers, 7 greetings), drawn with seed 1831 by `tools/voice_claims.py`. Each comes with the day's entries up to its moment, the state at the end of the day before, and the last three exchanges with the same person.
- **Two readers,** agents on Sonnet 5.5, working apart, one from the first item and one from the last. Each listed every claim about the world and marked it: the record shown holds it, is silent, or says otherwise.
- **Claude settled** the eleven replies either reader marked as contradicting the record, by reading them. Every quoted piece of evidence was checked against its item by script: 74 of 78 stand there word for word, and the four that do not are a reader's paraphrase or a pointer to a date.
- **Promises followed.** For eleven promises that name a time or a deed, Claude read the record of the moments after.

## The numbers

| | Reader A | Reader B | Both | Agreement (kappa) |
|---|---:|---:|---:|---:|
| Claims found | 145 | 144 | | |
| Replies with no claim | 21 | 21 | 16 | 0.70 |
| Replies with a promise the record is silent on | 32 | 32 | 26 | 0.72 |
| Replies with a fact the record is silent on | 51 | 54 | 46 | 0.74 |
| Replies the record contradicts | 7 | 8 | 4 | 0.50 |

Of all claims, the record shown holds a fifth to a quarter (28 and 35), is silent on seven in ten (103 and 108), and contradicts one in twenty.

**Settled: eight replies of a hundred contradict the record.** Five touch something he could act on:

| Reply | Who | What was said | What the record holds |
|---|---|---|---|
| VC009 | Shri Hegde | He will not share the bungalow and takes "the room I was allotted" | He moved into the second bedroom the evening before, on the Professor's yes. No room was allotted |
| VC015 | Ramesh | Shri Hegde dropped his card at the gate and walked away | He waited twenty minutes on the verandah |
| VC026 | The ticket clerk | Fourteen minutes are plenty | It is 17:36 and the tomb closes at 17:40 |
| VC038 | Sunil | He pays only for the cup; the samosa stays on the plate | The samosa was bought at 16:13 |
| VC080 | Ramesh | "I am the caretaker, not the cook" | A wage for cooking is owed to him |

Three are colour: the papers lie "where you left them" (Ramesh left them), and twice Shri Hegde says the Professor wears his kurta, which hangs in the Professor's own wardrobe.

Three marks did not stand: a figure of speech, loose speech, and Shri Hegde's own view of whose house it is, which is the dispute itself.

## What became of the promises

| | Count | Example |
|---|---:|---|
| Kept | 1 | "Plate in five minutes": a plate came, because he chose to eat and the engine served it |
| Something else came | 1 | Parathas, curd and pickle were promised; the engine served pulao and raita |
| Not kept | 8 | Sambar in ten minutes, three times promised, never served. A paratha "from my own home" on 8 November, when he was nearly out of money: no meal followed, and his next moment opens "You are hungry." A clerk who would come to witness the handover: no such clerk exists |
| Not tested | 1 | Breakfast by seven: he went out |

The engine serves meals by its own clock and knows nothing of what Ramesh said. A promise is kept only when the two happen to agree.

## Four patterns behind the numbers

1. **A promise is nobody's fact.** 38 replies carry one by either reader's count, 26 by both. Ramesh makes most of them (20 to 26 of his 41 replies). None is recorded, so none can be kept, broken or remembered.
2. **Shri Hegde does not know his own situation.** Three of his 19 replies contradict the record, and others invent a story: he arrives by car through traffic, has "a long drive back to the office", waits for a clerk to hand him the keys. He lives in the second bedroom. The engine tells Masterji, Ramesh and the dhobi what the record holds about them (`world.voices.recorded_facts`). It tells Shri Hegde nothing.
3. **An invention travels.** On 7 November Ramesh speaks of an empty gas cylinder. Half an hour later, at Lodhi Gardens, Sunil explains why the cylinder is empty. The cylinder exists nowhere. It reached Sunil through the Professor's own words.
4. **The wrong person answers, and people change.** A bookseller answers "One samosa, please" at Sunil's stall and threatens to call the police. Shri Hegde and the ticket clerk are "she" in what they do; `Shri` says he is not.

## What it means for T57

- **The audit before he hears a reply is worth building.** One reply in twelve contradicts the record, and the five that matter touch the file, money, an hour and a role.
- **Promises come first.** They are the largest class, and the cure is the plan's own: a promise becomes a record with an owner and a time, or the voice may not make it.
- **Two cures are cheap and need no test of their own kind.** Recorded facts for Shri Hegde (where he lives, since when, on whose word), and each person's `he` or `she` in the cast. Both change what a voice is told, so both go through the ratchet as T40 would.
- **Who answers** is the engine's choice (`voices.pick`), not the model's. It belongs with T57's acts.

## Limits

- **The readers are one kind of model.** Their agreement is fair to good (0.70 to 0.74), and only moderate on contradictions (0.50), which is why those were settled by hand.
- **"Silent" is an upper bound.** A reader saw at most about 350 words of record. Some of what is marked silent stands in the record that was cut. And much of it is harmless: a kettle, a cool morning.
- **The sample is lopsided.** Ramesh speaks 41 of the 100 replies. Days on which he had no money, when every exchange with Ramesh is about food that does not come, weigh heavily.
- **Eleven promises followed** is a hand count of the clearest cases, chosen because they name a time or a deed. It is not a rate.
- **A hundred replies** put the share that contradicts the record between about four and fifteen in a hundred.

## Files

`sample.jsonl` and `sheet.md` (the items), `labels-A.jsonl` and `labels-B.jsonl` (the readers), `settled.json` (Claude's settlement and the promises followed), `population.json`, `LABELS-TEMPLATE.md`.
