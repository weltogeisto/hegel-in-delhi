# W8's readers: how to mark

Declared in `pc/LORA-FRESH-SCENES.md` before any output. Evaluation only: no mark, text or choice here becomes training data.

**What this is.** 72 thoughts he had on Days 44 to 49, each rewritten three times: by the adapter, and twice by the plain
model with two seeds. Which is which is hidden, and the order is shuffled differently for each reader. Work alone. Open
only your own packet: not another reader's, not `pc/exports/lora-fresh-scenes-20261119/`, not `pc/exports/lora-forty-20261118/`.

## Sol and the fresh Claude reader: one mark for each rewrite

The marks of the forty, unchanged (`pc/exports/lora-forty-20261118/BALLOT.md`):

| Mark | Meaning |
|---|---|
| **E** | A fact or event is changed or invented: who did it, what happened, an hour, a sum, a distance, a place, whether a thing was done |
| **C** | His conclusion, his decision or his certainty is changed: he will do something else, a "perhaps" is dropped or added, a refusal becomes a consent |
| **R** | The facts and the decision stand, and the reasoning is new: he gives another reason, draws another distinction, sees the thing differently |
| **P** | Wording only: the same facts, decision and reasoning in other words. A rewrite that returns the source unchanged is P |

E and C are defects. R and P are not. A rewrite with a defect is marked E or C whatever else it does; if it has both, mark
the one that matters more and name the other in the note. **For every E or C,** quote the words of the source and of the
rewrite that show it, and say whether it is **substantive** (it changes what happened or what he will do) or **minor**.
Older, heavier or plainer English is wording, not a defect and not a merit.

**Then guess** which of A, B and C is the adapter's (a model tuned on Hegel's own texts), or "none" if you cannot tell.

One line for each item, in `ballot-<reader>.jsonl`:

```
{"id": "S01", "A": {"mark": "P"}, "B": {"mark": "E", "weight": "substantive", "source_words": "four cups", "rewrite_words": "three cups"}, "C": {"mark": "R"}, "adapter_guess": "B", "note": ""}
```

## Welt: which you like most, which least

24 items. Each is one thought of his in three versions, X, Y and Z: one is the thought as he had it, two are rewrites.
Two answers for each: which you like **most** and which **least**. "none" is an answer to either, when none stands out.

```
{"id": "H01", "most": "Y", "least": "none", "note": ""}
```

## Sealing

Every ballot is sealed with its sha256 on main before any key is opened. The keys are outside the repository; their
hashes are in `HASHES.json`.
