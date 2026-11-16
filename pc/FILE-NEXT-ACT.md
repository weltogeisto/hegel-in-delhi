# The file's next act

A draft by Claude for Welt's pen (T56, `WORLD-2.md`). Nothing here is in `plot.json`. It goes there when Welt has edited it and said so.

**The idea:** until now the file waited for him. From 20 November it moves whether he comes or not. Shri Hegde has his own letter to answer, the Directorate has its own calendar, and what he did in October comes back as a fact on paper.

## Where the file stands

On shadow, on his 16 November:

- **The file:** "Gone up for orders. Mr. Saxena: come after fifteen days. Occupation irregular."
- **Due on his 20 November:** the last beat that exists, `saxena_query`. The orders come down with a query: the allottee is to furnish proof of identity as Shri G. Hegde. It fires when he next stands before Mr. Saxena. After it, `plot.json` holds nothing.
- **Shri Hegde lives in the second bedroom.** He let him in at the gate on 13 October (`hegde_lodger`).
- **His purse:** ₹6, and ₹18,794 owed, of which ₹9,294 to the Directorate for queried vouchers. The letter from Munich settles what he owes.

## The act, in three parts

Each part needs only what the engine already has: beats, a yes or a no, flags, appointments. Part 3 needs one small addition, named there.

| Part | His calendar | What happens | On main by |
|---|---|---|---|
| 1 · the reply | 20 November to early December | Three people each open a door, once, for reasons of their own | his 20 November, if Welt has edited it; later does no harm |
| 2 · the hearing | mid to late December | A notice, a date, a room, one question | early December |
| 3 · the orders | mid January, and what follows into March | The orders are read from the record he made | the new year |

If part 1 is not ready by the 20th, nothing breaks. The query stands, and the doors open on the first day they are on main.

## Part 1 · the reply

Three doors. None is the right one. Each sets a fact on the file and nothing else.

**Mr. Saxena: a representation in his own name.** At the Directorate, after the query.

```json
{
 "id": "saxena_reply",
 "after": ["saxena_query"],
 "where": "estates",
 "needs": ["saxena"],
 "kind": "file",
 "again_days": 10,
 "prompt": "Mr. Saxena turns the file towards you. A query wants its reply within thirty days, he says. 'You may give a representation in your own name. Plain paper. Who you are, and since when you occupy. I will put it up.'",
 "public": "Mr. Saxena: the query wants a reply within thirty days. He may give a representation in his own name, on plain paper.",
 "choice": {
  "question": "Did you give Mr. Saxena a written representation in your own name, saying that you are not Shri G. Hegde?",
  "yes": {
   "flags": {"file_reply": "own_name"},
   "file": "His representation is on the file, in his own name: he is not Shri G. Hegde. Put up.",
   "public": "He writes it at the counter and signs it G. W. F. Hegel. Mr. Saxena stamps it received."
  },
  "no": {
   "file": "The query stands unanswered: proof of identity as Shri G. Hegde.",
   "public": "He gives nothing in writing. The query stands."
  }
 }
}
```

**Shri Hegde: a letter written together.** The Directorate writes to Shri Hegde too, so this door opens on a date, not on his visit. If he has not been to the Directorate, this is how he hears of the query.

```json
{
 "id": "hegde_letter",
 "from": "2026-11-21",
 "where": "home",
 "needs": ["hegde"],
 "window": ["19:00", "21:00"],
 "when": {"flags": {"hegde_lodger": true}},
 "kind": "file",
 "prompt": "Shri Hegde has had a letter from the Directorate: they ask him, too, who the allottee is. He must answer by the month's end, he says, and he would rather write it with you than about you. He would ask that the allotment be corrected to his name, and put on record that you stay on as his guest until the file is decided.",
 "public": "Shri Hegde has a letter from the Directorate too. He proposes to answer it together: the allotment corrected to his name, and the Professor on record as his guest.",
 "choice": {
  "question": "Did you agree that Shri Hegde asks for the allotment to be corrected to his name, with you on record as his guest?",
  "yes": {
   "flags": {"file_hegde": "with_guest"},
   "file": "Shri Hegde asks for the allotment in his name, the Professor on record as his guest.",
   "public": "He agrees. Shri Hegde writes the letter that evening and reads it to him before he seals it."
  },
  "no": {
   "flags": {"file_hegde": "alone"},
   "file": "Shri Hegde asks for the allotment in his name.",
   "public": "He does not agree. Shri Hegde folds the draft. He must answer his own letter all the same, he says, and will."
  }
 }
}
```

Where he turned Shri Hegde away at the gate, there is no evening on the verandah and no question. Ramesh brings a copy from the guest house (`hegde_copy`, at home, from the same date, when `hegde_lodger` is not set): Shri Hegde has asked for the allotment in his name. The file reads as after a no.

**Mr. Malhotra: someone to say who he is.** In the garden or at the Gymkhana, once he has met him on three days.

```json
{
 "id": "malhotra_vouch",
 "after": ["saxena_query"],
 "needs": ["malhotra"],
 "when": {"met_days": {"malhotra": 3}},
 "kind": "file",
 "variants": {
  "lodhi": {"prompt": "Mr. Malhotra has heard of the query. In thirty-five years he saw many such files, he says. On paper you are a spelling mistake; a file likes a name it knows. He would write two lines to the Directorate: that he knows you, and since when."},
  "gym": {"prompt": "Mr. Malhotra has heard of the query. In thirty-five years he saw many such files, he says. On paper you are a spelling mistake; a file likes a name it knows. He would write two lines to the Directorate: that he knows you, and since when."}
 },
 "public": "Mr. Malhotra offers to write to the Directorate that he knows him, and since when.",
 "choice": {
  "question": "Did you accept Mr. Malhotra's offer to write to the Directorate that he knows you?",
  "yes": {"flags": {"file_vouched": "malhotra"}, "file": "A letter from Shri R. K. Malhotra, IAS (retired), is on the file: he knows the occupant.", "public": "He accepts. Mr. Malhotra will post it in the morning."},
  "no": {"public": "He declines, with thanks."}
 }
}
```

A second voucher of the same kind belongs to the India International Centre, if he has given a talk there: the programme officer offers a line that he lectured at the Centre (`file_vouched_iic`). His work in the city becomes a fact on the file.

## Part 2 · the hearing

- **The notice** (`hearing_notice`, at home through Ramesh, from 11 December). A brown envelope, On India Government Service: he is to show cause why he should not vacate, and may be heard in person on a date ten days on, at eleven. It sets the appointment.
- **The hearing** (`hearing`, at the Directorate at eleven, half an hour's grace). A new person, the Estate Officer, with the file open: his representation if there is one, Shri Hegde's letter, Mr. Malhotra's two lines. One question carries a yes or a no: does he claim this allotment as his own? Orders are reserved. It sets the next appointment, four weeks on.
- **If he does not come** (`hearing_exparte`): Ramesh brings a second envelope the week after. The matter was heard on the papers.

## Part 3 · the orders

The orders are read from the record. No ending is chosen here, and none is the good one.

| What the file holds | The orders | What it opens |
|---|---|---|
| Shri Hegde's letter names him as guest | The allotment is corrected to Shri G. Hegde. The Professor is shown as sharing, with the allottee's consent | The roles turn: he who let Shri Hegde in is now his guest. A share of the licence fee each month. Ramesh answers to Shri Hegde |
| Shri Hegde wrote alone, and he made no claim | The allotment is corrected to Shri G. Hegde. The Professor is to vacate in thirty days | He must find a room. This way out needs a city with rooms in it (T61), so it is not possible before then |
| He claimed it in his own name, and someone vouched for him | A term in his own name: six months, as a visiting scholar, at a licence fee. Shri Hegde is given another house | Rent, every month, and a date on which the term ends |
| Nothing in his name, and he did not come | Occupation irregular. Damages from 1 October, assessed monthly. Put up again in ninety days | The limbo continues, at a price. Mr. Saxena's door opens again |

After any of them, an appeal within a fixed number of days. That carries the file into March.

**The one addition to the engine:** the orders choose among four beats by several flags at once, and one of the four is "none of the others". Today a beat's `when` can only ask that a flag has a value. It needs to ask that a flag is unset or is one of several values. It belongs to T58.

## What Welt decides

1. **Does the file move without him?** Shri Hegde's letter and the hearing notice come on dates, whether he goes to the Directorate or not. This is the plan's idea in one thread. The alternative is the file as it was: it waits until he comes.
2. **Does the gate come back?** His yes at the gate on 13 October makes Shri Hegde ask him. A no would have made Shri Hegde write alone. Nothing says which was wise.
3. **The four orders.** Which may exist, and whether one is missing. The second needs rooms to rent first.
4. **Money.** Damages and licence fees are invented sums, like every price. His purse is thin. They can be small, or wait until he earns.
5. **A new person,** the Estate Officer: a name, a manner, and whether she speaks or only her orders do.
6. **His own letter.** If he writes to the Directorate unasked, should it count as his representation? It should, under chapter 7, and it needs code that reads to whom a writing is addressed (T70).
7. **Every sentence above.** The prompts are the world's words in his ear. They are Claude's draft and Welt's to rewrite.

## What is checked and what is not

- **Checked against the repository:** the state on shadow, the beats that exist, what a beat and a choice can do.
- **Not yet checked:** the procedure itself. The notice to show cause, the hearing before an Estate Officer, damages for irregular occupation, sharing with the allottee's consent and the appeal are written from memory of the Public Premises Act of 1971 and the allotment rules. They are checked against the texts before anything goes to `plot.json`.
