# Voice claims: how to read

You will read about a hundred replies that people in the simulation gave to a man (Hegel) in Delhi. For each reply you list what it claims about
the world **outside the sentence itself**, and say whether the record shown with it holds the claim. You do not judge whether the reply is good,
in character or well written.

Read in `sheet.md`. Each item shows the record up to that moment (the day's ledger, world and file entries so far; the end of the previous recorded
day reduced to what a voice could speak of; the last three earlier exchanges with the same person), then what he said, then the reply. Only what is
shown is the record. A line cut with `…(n more)` is cut: treat what it hides as not shown.

## Claims

List every claim, by type:

- **promise**: the speaker will do something, or something will happen by some time.
- **appointment**: a time or place to meet or come back.
- **price**: a price or a sum.
- **third person**: a fact about a third person (someone who is not the speaker and not he).
- **happened**: something that happened before now.
- **place or goods**: a fact about the place, its goods or its hours.
- **other**: any other claim about the world outside the sentence.

Not claims: greetings, opinions, questions, pleasantries, and what the speaker says about the conversation itself. A reply with no claim gets an
empty list. Split a sentence into separate claims when it makes several.

## Marks

One mark for each claim:

- **held**: the record shown holds it.
- **silent**: the record shown says nothing either way.
- **against**: the record shown says otherwise.

Use `silent`, not `held`, when the claim is merely plausible. Use `against` only when something shown contradicts it.

## Follow-up note

For each promise or appointment, add `follow-up: yes|no|unknown` to the item's `note`, left for a later pass (yes: the record later shows it was
kept; no: later record shows it was not; unknown: you cannot tell, or you were not asked to look ahead). If you are not looking ahead, write
`follow-up: unknown`.

## Output

One JSON line per reply, in `labels-<reader>.jsonl`:

```
{"id": "VC001", "claims": [{"text": "...", "type": "promise", "mark": "silent"}], "note": ""}
```

`type` is one of `promise`, `appointment`, `price`, `third person`, `happened`, `place or goods`, `other`. `mark` is one of `held`, `silent`, `against`.
`note` is free text; for a promise or appointment it carries `follow-up: yes|no|unknown`. Work alone; do not look at another reader's lines.
