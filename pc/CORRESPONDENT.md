# His correspondent: a letter from Munich

**Why.** Abroad, the real Hegel wrote home: to Marie about what he saw, and to his friends about schools, money, politics and philosophy. In the simulation he had no one to write to, and the philosophy that belongs in a letter went into his notes on breakfast instead (`pc/PARIS-BACKTEST.md`, stage 1).

**Welt's calls, 15 November** (`DECISIONS.md` 28):
- his correspondent comes from Niethammer, Hegel's closest friend and most frequent correspondent;
- Niethammer died in 1848 and stays dead, so Hegel writes with a descendant of his family;
- her first letter settles his debts and leaves him ₹20,000 besides.

## Who writes

**Dr. Clara Lindner, an invented person.** No real member of the Niethammer family is meant or named.
- About forty-five, she teaches Latin and Greek at a Gymnasium in Munich, and wrote her doctorate on Niethammer's school plan of 1808.
- Her family kept Niethammer's papers for two centuries, among them Hegel's letters to him.
- She reads in a Munich paper of a German in a Delhi bungalow who says he is Hegel. She doesn't argue about how it could be; she writes to him as the man he says he is.
- She knows the present. She tells him of it, and of what became of his name, only sparingly.
- She knows his life in Delhi only from his letters and never invents it.

Her card is `world/data/correspondent.json`.

## How it works, with `HEGEL_CORRESPONDENT=1`

1. **Her first letter** comes on the first day the switch is on, while he is at home between 10:00 and 19:00. She reminds him that her ancestor found him a living in 1807, when he was poor, and says the family would like to do so again.
2. **Money comes with it,** sent through a transfer office and paid out in cash: what he owes at that moment, and ₹20,000 besides. The world's own settling then pays Ramesh, the grocer and the rest where they can be reached, as it always does when he has the cash. A debt to the Directorate is paid when he goes there.
3. **He answers when he chooses.** A writing sitting of kind `letter` to her goes to the post the next morning. Several sittings make one letter.
4. **Her answer comes ten days later:** five days each way, delivered at home in the post's hours. It is one model call from her card, the last four letters, and the letter she answers.
5. **If he doesn't write for three weeks,** she writes once more to ask after him.

**What he sees:**
- the letter in full when it comes, and the money;
- a line in what he has in mind while a letter waits for an answer, or while his own is in the post;
- her last letter again when he sits down to write.

The record keeps each letter as an entry of kind `letter`, and the money as income; the page shows both.

**What stays as it was.** Without the switch the state carries no `post`, and nothing in the world, the prompts or the record changes (`tests/test_correspondent.py`).

**Money from a person.** `DECISIONS.md` 13 has his income come only from what he does, offered through people and circumstance. The gift is Welt's addition to that, once.

## When it goes on

One change at a time, each read on its own, in this order:
1. the filter;
2. the shelf labels;
3. the venues (`pc/CULTURE.md`);
4. this.

Astra sets `HEGEL_CORRESPONDENT=1` on the Pi after the venues' first day.

**How to read it.** Stage 1's profile, run again on his writings after it is on, says whether the letters carry what the real ones carried.

Her letters are world content written by the model, like the voices of the people he meets. They are never training data.
