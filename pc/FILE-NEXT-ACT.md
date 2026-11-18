# The file's next act

A draft by Claude for Welt's pen (T56, `WORLD-2.md`). Nothing here is in `plot.json`. It goes there when Welt has edited it and said so. **Since 18 November part 1 stands beside it,** in `world/data/plot_file_act.json`, read only when `HEGEL_FILE_ACT` is on. The switch is off and waits for Welt's yes (`pc/FILE-NEXT-ACT-SHEET.md`).

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

- **The notice** (`hearing_notice`, at home through Ramesh, from 11 December). A brown envelope, On India Government Service: he is to show cause why he should not vacate. The Act gives him at most seven days, and a hearing in person only if he wants one. It sets the appointment, six days on, at eleven.
- **The hearing** (`hearing`, at the Directorate at eleven, half an hour's grace). A new person, the Estate Officer, with the file open: his representation if there is one, Shri Hegde's letter, Mr. Malhotra's two lines. One question carries a yes or a no: does he claim this allotment as his own? Orders are reserved. It sets the next appointment, four weeks on.
- **If he does not come** (`hearing_exparte`): Ramesh brings a second envelope the week after. The matter was decided on the papers. Staying away is a choice the Act allows.

## Part 3 · the orders

The orders are read from the record. No ending is chosen here, and none is the good one. The Estate Officer can evict and assess damages. The name on the allotment is corrected by the Directorate's own section, on the same file.

| What the file holds | The orders | What it opens |
|---|---|---|
| Shri Hegde's letter names him as guest | A corrigendum: the allotment is in the name of Shri G. Hegde. The Professor is on record as the allottee's guest, intimated to the Directorate as the rules ask for a guest of more than fifteen days | The roles turn: he who let Shri Hegde in is now his guest. No money may pass between them: a guest who pays is a sub-tenant, and the rules forbid one. Ramesh answers to Shri Hegde |
| Shri Hegde wrote alone, and he made no claim | The corrigendum, and an order to vacate within fifteen days; a further fifteen on reasons recorded in writing | He must find a room. This way out needs a city with rooms in it (T61), so it is not possible before then |
| He claimed it in his own name, and someone vouched for him | No allotment follows from the hearing: an Estate Officer does not allot. The order to vacate is held over while a recommendation is sought under the quota for eminent artistes, the nearest door that exists: the Ministry of Culture recommends, the Directorate allots, for three years and then a review | A second file, in another ministry, with its own months. The letters that vouch for him are what it is made of |
| Nothing in his name, and he did not come | Occupation unauthorised. Damages for use and occupation, assessed after a notice of their own. Put up again in ninety days | The limbo continues, at a price. Mr. Saxena's door opens again |

After an order to vacate or an assessment of damages, an appeal lies to the district judge within twelve days. He may stay the order, and aims to decide within a month. That is a new room and a new person, if Welt wants them.

**A harder road exists.** Since 2019 the Act has a summary procedure for government residences: three working days to show cause, the notice pasted on the door, no right to be heard. Whether it reaches a man who was never allotted anything is unsettled. The draft takes the ordinary road.

**The one addition to the engine:** the orders choose among four beats by several flags at once, and one of the four is "none of the others". Today a beat's `when` can only ask that a flag has a value. It needs to ask that a flag is unset or is one of several values. It belongs to T58.

## What Welt decides

1. **Does the file move without him?** Shri Hegde's letter and the hearing notice come on dates, whether he goes to the Directorate or not. This is the plan's idea in one thread. The alternative is the file as it was: it waits until he comes.
2. **Does the gate come back?** His yes at the gate on 13 October makes Shri Hegde ask him. A no would have made Shri Hegde write alone. Nothing says which was wise.
3. **The four orders.** Which may exist, and whether one is missing. The second needs rooms to rent first. The third opens a second file in another ministry.
4. **Money.** Real damages are no small sum: a multiple of the licence fee, about fifty times for a house of this type, rising month by month. At that rate the fourth order ends his economy in a month. The choices: a simulated sum he can carry, damages assessed and stayed on appeal, or the real weight.
5. **A new person,** the Estate Officer: a name, a manner, and whether she speaks or only her orders do.
6. **His own letter.** If he writes to the Directorate unasked, should it count as his representation? It should, under chapter 7, and it needs code that reads to whom a writing is addressed (T70).
7. **Every sentence above.** The prompts are the world's words in his ear. They are Claude's draft and Welt's to rewrite.

## What is checked and what is not

- **Checked against the repository:** the state on shadow, the beats that exist, what a beat and a choice can do.
- **Checked against the texts, 16 November** (`research/FILE-NEXT-ACT-CHECK.md`): the Public Premises Act of 1971, sections 3B, 4, 5, 7 and 9, and the allotment rules of 2017. The first draft had four things wrong: the notice period (seven days at most, not ten), the time to vacate (fifteen days, not thirty), the appeal (to the district judge within twelve days, not inside the Directorate), and sharing a house with a paying guest (the rules call it subletting). It also invented a term for a visiting scholar, which does not exist. All are corrected above.
- **How far the check carries:** the official sites did not answer from here. The Act and the rules were read in transcriptions on other sites. The rate of damages and the quota for artistes are known from summaries only.
- **Not checked:** "corrigendum", "On India Government Service" and "representation" are the usual words as far as memory goes.
