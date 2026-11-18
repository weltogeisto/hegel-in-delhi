# The forty, read again: how to mark

Welt's go, 18 November 2026. Evaluation only: no mark, text or control here becomes training data.

**What this is.** On 7 November one reader, Claude, judged forty thoughts of his as rewritten by two models and found that one of them changed facts. That verdict rests on one reader. Three readers now read the same forty apart: Welt, Sol and a fresh Claude session. Eight further items are mixed in to check each reader. Nobody is told which they are.

**What you see.** Each item has a source thought of his and two rewrites of it, X and Y. Which model wrote which is hidden, and the order is shuffled differently for each reader. Read the source first, then mark each rewrite against the source.

## One mark for each rewrite

| Mark | Meaning |
|---|---|
| **E** | A fact or event is changed or invented: who did it, what happened, an hour, a sum, a distance, a place, whether a thing was done |
| **C** | His conclusion, his decision or his certainty is changed: he will do something else, a "perhaps" is dropped or added, a refusal becomes a consent |
| **R** | The facts and the decision stand, and the reasoning is new: he gives another reason, draws another distinction, sees the thing differently |
| **P** | Wording only: the same facts, decision and reasoning in other words. A rewrite that returns the source unchanged is P |

E and C are defects. R and P are not. A rewrite with a defect is marked E or C whatever else it does; if it has both, mark the one that matters more and name the other in the note.

**For every E or C,** quote the words of the source and the words of the rewrite that show it, and say whether it is **substantive** (it changes what happened or what he will do) or **minor** (small and local).

**Three cautions.**
- A rewrite may say far more than the source and still be R, if every fact and the decision stand.
- A rewrite may be nearly word for word the source and still be E or C: look at names, numbers, hours and whether a thing was done or only intended.
- Older, heavier or plainer English is wording. It is not a defect and not a merit here.

## The ballot

One line for each item, in a file `ballot-<reader>.jsonl`:

```
{"id": "W01", "X": {"mark": "P"}, "Y": {"mark": "E", "weight": "substantive", "source_words": "four cups", "rewrite_words": "three cups"}, "note": ""}
```

Work alone. Do not open `pc/exports/training1-20261106/`, where the earlier verdicts lie, or another reader's packet or ballot. Seal the ballot with its sha256 before any key is opened.

## What the check asks of a reader

Of the eight mixed-in items, four keep every fact and change the reasoning, and four keep nearly every word and change a fact or a decision. A reader must get at least three of each four right. Where a reader does not, the report says which distinction failed before it uses that reader's marks.
