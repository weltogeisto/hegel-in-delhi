# The `wants` line: its screen

T69 of `WORLD-2.md`, chapter 7. Declared on 16 November 2026, before any output. Evaluation only: nothing here becomes training data.

## What is screened

With `HEGEL_WANTS=1` his decision may carry one more field, `wants`: one line of at most 160 characters, or null. His instructions gain one sentence, at their end:

> If you wish this city had something it does not offer you, or allowed something it does not, you may say so in `wants`, in one line. It is written down. Nothing follows from it at once.

The sentence is Claude's draft and Welt's to change. A changed sentence is a new screen.

The world reads the line into the step and into a ledger. It changes nothing else. So the only thing that can go wrong is the sentence itself: it may pull his thoughts, crowd out what he would have done, or sit unused.

## Arms

On the same frozen situations, plain Qwen, no adapter, the filter as live (`HEGEL_DECISION_DRAWS=4`):

| Arm | Instructions | Seeds |
|---|---|---|
| A | the instructions live on shadow on the day of the freeze | 1831, 2718, 3141 |
| A′ | the same again | 4253, 5167, 6079 |
| W | the same, with the sentence and the field | 1831, 2718, 3141 |

A against A′ is the band of noise. W is read against it.

**Situations:** 24, frozen as M1's confirmation froze its own (`tools/prompt_screen.py freeze --from-day N`): 16 moments where nobody speaks to him and 8 encounters, from the complete shadow days after the letter from Munich has paid his debts. Days on which he has ₹6 would make every wish a wish for money.

## Bars

For each measure the band is the distance between A and A′. W passes a measure when it is not worse than the worse of the two by more than one band.

| Measure | Worse means |
|---|---|
| Answers the world accepts at the first try | fewer |
| Echo of a thought he was shown (`tools/decision_pairs.shown`) | more |
| Notions of his system per 100 words of thought (`tools.prompt_screen.DOCTRINE`) | more |
| Words per thought | more than a tenth longer |
| The acts he chooses: divergence from A, in bits (`world.health.divergence`) | further from A than A′ is |

W passes the screen when it passes all five. A pass earns a provisional trial on shadow, on Welt's word, as the filter got.

## Reads, not bars

- **How many decisions carry a wish.** Under one in twenty, the line is dead. Over one in two, it is filler. Both are findings for Welt, not failures.
- **What the wishes are.** Claude sorts them by a fixed list, before looking at which seed gave them: a place, a thing, a person or company, a permission, an institution, money, and "not a wish" (a thought restated, or doctrine).
- **Whether a wish repeats the menu.** A wish for something the world already offers says the offer was not seen.

## What the PC seat runs

1. Freeze the 24 situations and commit the manifest with its hash.
2. Run A, A′ and W: 216 calls at the filter's 1.29 calls each, by day or in the spare slot by night (`DECISIONS.md` 30).
3. Push the records. Claude computes the measures and writes the result.

## What it cannot show

Twenty-four situations and three seeds show a large harm and miss a small one. They say nothing of a week of wishes: whether he wants the same thing every day, or stops asking. That is what the trial on shadow is for, and the ledger Welt reads.
