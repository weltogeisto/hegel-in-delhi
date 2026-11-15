# His correspondent: Niethammer writes from Munich

**Why.** Abroad, the real Hegel wrote home: to Marie about what he saw, and to his friends about schools, money, politics and philosophy. In the simulation he had no one to write to, and the philosophy that belongs in a letter went into his notes on breakfast instead (`pc/PARIS-BACKTEST.md`, stage 1). Welt chose Niethammer, 15 November (`DECISIONS.md` 28).

## The fiction

Friedrich Immanuel Niethammer (1766–1848) was Hegel's closest friend and most frequent correspondent:
- a Tübingen man like him, a professor at Jena, then the senior school councillor in Munich;
- he found Hegel the Bamberg newspaper in 1807 and the Nuremberg rectorship in 1808.

In the world, he died in Munich in 1848 and woke there in October 2026, as Hegel woke in Delhi. A church charity found him a room in the Maxvorstadt. He reads in the State Library and visits schools, and he is dismayed at what has become of the Gymnasium.

He knows everything up to 1848, Hegel's death among it, and what he has learned in Munich since. He tells such things sparingly, as a friend would. He knows Hegel's life in Delhi only from Hegel's letters and never invents it. His card is `world/data/correspondent.json`.

## How it works, with `HEGEL_CORRESPONDENT=1`

1. **His first letter** comes on the first day the switch is on, while Hegel is at home between 10:00 and 19:00. Niethammer has read a Munich newspaper item about a German philosopher lodged by mistake in a Delhi bungalow. He writes to ask whether it is truly Hegel, and tests him with something from their past.
2. **Hegel answers when he chooses.** A writing sitting of kind `letter` to Niethammer goes to the post the next morning. Several sittings make one letter.
3. **The answer comes ten days later:** five days each way, delivered at home in the post's hours. It is one model call from the card, the last four letters, and the letter it answers.
4. **If Hegel does not write for three weeks,** Niethammer writes once more to ask after him.

**What Hegel sees:**
- the letter in full when it comes;
- a line in what he has in mind while it waits for an answer, or while his own letter is in the post;
- the last letter again when he sits down to write.

The record keeps each letter as an entry of kind `letter`, and the page shows it.

**What stays as it was.** Without the switch the state carries no `post`, and nothing in the world, the prompts or the record changes (`tests/test_correspondent.py`).

## When it goes on

One change at a time, each read on its own, in this order:
1. the filter;
2. the shelf labels;
3. the venues (`pc/CULTURE.md`);
4. this.

Astra sets `HEGEL_CORRESPONDENT=1` on the Pi after the venues' first day.

**How to read it.** Stage 1's profile, run again on his writings after it is on, says whether the letters carry what the real ones carried.

Niethammer's letters are world content written by the model, like the voices of the people he meets. They are never training data.
