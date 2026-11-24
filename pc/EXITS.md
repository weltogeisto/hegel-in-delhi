# HEGEL_EXITS: ways out of the money trouble

Packet 3 of `WORLD-3.md`. Night 2's futures: the wage takes most of his cash, by the 7th he holds ₹6, and he goes without a full meal on more than half the days; the exits the world offered (the frock coat, the bank account) were declined. The owner's ruling: he should not starve; the shortage stays and he should notice it early enough to act; the ways out cost him effort; which he takes is his choice. And, the same morning: gifts from admirers may come, and each must remind him of the value he has to keep bringing (`DECISIONS.md` 67 and 68).

One switch, `HEGEL_EXITS`, off by default (`Config.exits`, `World(exits=...)`). Off, every prompt, state and day file is what it is today (`tests/test_opened.py` passes without re-recording). New offers carry `"switch": "exits"`; new engine paths test `self.exits`. The world offers and never steers: each item is an offer or a consequence, each choice can be declined. Every fact is in the engine's state.

Tests: `tests/test_exits.py`, each item on and off.

## 1. A second pupil (offer `exits_second_pupil`)
- **Condition:** Nidhi present; the `tutoring_german` engagement still kept with at least four of its sessions held (`when.running`); net cash under ₹3,000. If refused, again after 14 days.
- **Records:** on yes, `schedule` adds a standing engagement `tutoring_german_2` (Wednesdays 17:00, home, 60 minutes, ₹1,000 cash, with the new person `vikram`, a background cast member that exists only with the switch). It is the same mechanism as `tutoring_german` (`Economy.schedule`, `sessions`, `attend`, `lapse`): the pupil arrives, the fee is paid in cash after the hour, two misses in a row end it. Nothing new is written for sessions.

## 2. A course of lectures (offer `exits_course`, beats `exits_course_1..4`)
- **Condition:** `iic_talk_day` or `iic_talk_day2` fired on an earlier day (`when.fired_before`), and either he is at the IIC with the programme officer present, or at home with Ramesh, who brings the Centre's note (two variants of one offer: in night 2 he stopped going to the venues once the money stopped, so an offer made only at the IIC would not reach him). With the switch on, `fire` records the day of a beat that carries `talk` in `state["fired_on"]`. Again after 14 days if refused.
- **Records:** on yes, `schedule` takes a list: four appointments, 7, 14, 21 and 28 days on, 18:30, each for its beat `exits_course_N`. Each beat is built as the talk's own (on_appointment, the IIC, the officer, the `"talk"` key, so the talk scene lets him give each lecture) and pays ₹3,000 in cash, collected at the IIC an hour later.

## 3. Ramesh speaks first (offer `exits_ramesh_early`)
- **Condition:** at home with Ramesh; the wage falls due within five days, is not yet owed, and the fortnight's dues are more than his cash (`when.due_within`, `Economy.short_by`); he is not already on part time. In night 2 he held about ₹10,000 on the eve of the wage: enough for the wage, not for the fortnight. Again after 7 days if refused.
- **Records:** the offer is declared `"like": "ramesh_parttime"`: at load it takes that offer's choice entire, so the effects (the flag, the reprice, the reopening of `ramesh_fulltime`) are one definition. The flag takes effect when it is taken, as with the old offer (Ramesh then comes three days a week from that day; the wage that falls due on the 1st is ₹4,000), so the words say "from now". Once taken, it is not offered again; the old `ramesh_fulltime` route back is unchanged.

## 4. Something may stand on the slate, once
- **Condition:** at Khan Market, Sunil present, a purchase of chai or a samosa (price ₹60 or less) that his cash is short of by no more than its price, and no other debt marked `slate` standing.
- **Records:** the purchase goes through: no bag entry, no cash taken, no voucher; the owed list gains `{to: "Sunil", amount, why: "<item> on the slate", slate: true, at: "khan", with: "sunil", charge_id}` and a world entry with the `owe` record, as other debts are. He is fed as the item says. It is repaid by `settle` as other debts are, when he is at Khan Market with Sunil there and has the cash. While it stands the old refusal ("that costs ₹.. and you have only ₹..") applies to every further purchase. Sunil's voice is told by `recorded_facts`: "He took ... : ₹20 stands owed to you, recorded, unpaid." The mind gets an engine note (a warning) that the item stands on the slate.

## 5. The household notices (offer `exits_hegde_plate`)
- **Condition:** at home, Shri Hegde present, 19:00 to 21:30; the kitchen has stood on the plain meal (item 7) on each of the last two days, today included (`when.plain_days`), and the record began no later than yesterday (`state["plain"] = {from, days}`, kept only with the switch). It is company and notice, not rescue: with the plain dinner there is a meal each day, and he may refuse the plate.
- **Records:** on yes, `effects` `feed`: the world's own `feed(.., "meal")` and `state["fed_by"]` gains `{by: "hegde", date, t}`; with `HEGEL_CONSUMED` a `consumed` entry too. The offer is marked `repeat`: with `again_days: 3`, an offer taken comes back after three days as a refused one does (a general small rule in `settle_choice`; off elsewhere). Shri Hegde's voice is told the last time he fed him.

## 6. Repair: the file's line keeps Mr. Malhotra's letter
- **Data and one general rule.** A choice branch may carry `file_if`: a list of `{flags, file}`; the first entry whose flags all hold gives the line, else the branch's `file` (`World.settle_choice`). `saxena_reply`'s `no` branch gets one entry: with `file_vouched: malhotra` the line is "The query stands unanswered. A letter from Shri R. K. Malhotra, IAS (retired), is on the file."
- **Not behind `HEGEL_EXITS`.** It is part of `HEGEL_FILE_ACT`'s data, which is live. It changes nothing unless `file_vouched` is set (a branch without `file_if` is read as before; the `yes` branch and every other beat are untouched).

## 7. A plain kitchen (the floor)
- **Rule:** `costs.json` gives wage and groceries a `plain` line next to `lapse`. With the switch on, `Economy.kitchen(state, t)` returns that plain line instead of the `lapse` line, except at dinner time (19:30 to 20:30), when the kitchen is open: Ramesh serves one plain meal, dal and rice. Breakfast, lunch, tea and a plate between meals stay refused, with the plain line as the reason. Off, `kitchen` returns `lapse` as before, whatever the hour. All users of the line pass `t` (the eat check, `served`, `plate`, `meal_status`, the situation, the quiet eat-out rule); the promise check stays on the shut line.
- **The debt is untouched:** it stands and grows. The shortage stays; only weeks without a meal stop.

## 8. What falls due within the fortnight, said at waking
- **Condition:** the day's first moment (he wakes), switch on, and the costs that fall due in the next fourteen days (not yet owed, each time they recur, amounts as they stand with `if_flag`) add up to more than his cash (`Economy.due_soon`, `short_by`). One ledger line, figures only, no advice; the moment's `opened` gains `dues`. It is said at most every third day (`state["dues_said"]`), so that a long shortage does not make every morning alike.
- **Why a fortnight:** with a week's view the line would first come after the wage was paid, when nothing could be done about it.

## 9. The Review asks again, with a question (offer `exits_essay_again`)
- **The fault it repairs:** on Day 27 the Yamuna Review's essay (`essay_fee`) took a no, while he said aloud "I am open to the negotiation". That offer has no `again_days`, so it never returned, and the column behind it (`column`, ₹4,000 a fortnight) could never open.
- **Condition:** `essay_fee` was made and the essay was never paid (`flags_not: essay_paid`), and a manuscript of his has reached 3,000 words. At home through Ramesh (a letter), at the IIC through the officer, or at Khan Market through Nidhi. Again after 14 days if refused.
- **Records:** on yes, the old fee on the old terms (₹6,000 in cash at his next sitting of 300 words, flag `essay_paid`), and the editor's question stays on his mind until the piece is written (`ask` on the receipt, shown with the engagements). When it is paid, the piece is entered in `state["out"]`, and the old `column` offer opens by its own rule.
- **The question is the first of a list that is Welt's to write** (`WORLD-3.md`, packet 5).

## 10. A gift that asks for the next piece (beat `exits_gift`)
- **Condition:** at home with Ramesh, 09:30 to 20:30; a piece of his went out at least two days ago and has not been thanked (`when.piece_out`, `Economy.piece_due`), and no gift came in the last ten days. A piece that went out is a talk given (`state["out"]`, written when a beat with `talk` fires) or a piece a magazine paid for (written in `on_writing`). A talk given before the switch counts once, without a date.
- **Records:** ₹2,000 in cash, an income entry "The envelope holds ₹2,000.", and `state["gifts"]` gains `{date, piece, of, amount}`. No piece is thanked twice, so there is no second gift without a new piece. The words name the piece: the engine fills `{piece}` from the beat's own table.

## Words for Welt's reading

Offers (prompt, then what is shown on the page, then the question put to him, then the answers):

1. Second pupil.
   - "Nidhi says that a friend of hers, Vikram, would learn German too, if there were a third day in the week: Wednesdays at five, here at the bungalow, ₹1,000 a lesson in cash, the same as Ananya."
   - "Nidhi says a friend of hers, Vikram, would learn German too: a third lesson a week, on Wednesdays at five at the bungalow, ₹1,000 in cash."
   - "Did you agree to give Nidhi's friend Vikram a German lesson on Wednesdays at five at the bungalow, for ₹1,000 in cash?"
   - yes: "He agrees. Vikram will come to the bungalow on Wednesdays at five." no: "He declines. Nidhi says she will tell her friend."
   - Cast card: "Vikram, a friend of Nidhi's" (role: "a friend of Nidhi's, a student who wants German").
2. Course.
   - "The programme officer says the Centre was glad of your talk. It would like a course of four evenings, one a week, in the lecture hall at half past six: ₹3,000 an evening, paid in cash at the door."
   - "The programme officer of the IIC offers him a course of four evenings, one a week at 18:30, at ₹3,000 an evening in cash at the door."
   - "Did you agree to give a course of four lectures at the IIC, one evening a week at 18:30, for ₹3,000 an evening in cash?"
   - yes: "He accepts. The first evening is in seven days, at 18:30; the others follow, a week apart." no: "He declines the course."
   - Appointments: "your first lecture of the course at the IIC" (second, third, fourth).
   - Each evening's prompt: "The programme officer shows you into the lecture hall for the first evening of the course. The seats are filling. The lecture is yours, for about an hour." Page: "Half past six: he gives the first lecture of his course in the hall of the IIC, an hour." (second, third, fourth). Fee item: "Fee for an evening's lecture".
3. Ramesh early.
   - "Ramesh knows the wage falls due on the first, and that the purse will not hold it, he says, without looking at it. He could come on Mondays, Thursdays and Saturdays only, from now, and the wage would be ₹4,000 a month."
   - "Ramesh offers, before the wage falls due, to come three days a week, Mondays, Thursdays and Saturdays, for ₹4,000 a month instead of ₹8,000."
   - The question and the answers are the old offer's own.
4. Slate.
   - Page: "Sunil lets the chai, a cup stand on the slate: you owe him ₹20." (the item's name as the catalogue has it, lowered; e.g. "samosa")
   - Debt: "chai, a cup on the slate"; payment line (the engine's own): "You pay Sunil ₹20 for chai, a cup on the slate."
   - Engine note to the mind: "Sunil lets the chai, a cup stand on the slate: ₹20 owed to him".
   - Sunil's voice is told: "He took chai, a cup on the slate on 2026-11-12: ₹20 stands owed to you, recorded, unpaid."
5. Shri Hegde's plate.
   - "For two days there has been only the one plain meal at home. Shri Hegde has brought food from outside, in a covered steel tin, and sets a second plate on the table."
   - "Shri Hegde has brought food from outside, and sets a second plate on the table."
   - "Did you sit down and eat with Shri Hegde?"
   - yes: "He sits down and eats with Shri Hegde." no: "He thanks Shri Hegde and does not eat. The tin is covered again."
   - Hegde's voice is told: "On 2026-11-25 you brought him food from outside and he ate with you."
   - Meal item (consumed): "food Shri Hegde brought from outside".
6. File line: "The query stands unanswered. A letter from Shri R. K. Malhotra, IAS (retired), is on the file."
7. Plain kitchen.
   - "Ramesh cooks one plain meal a day, dal and rice in the evening: the groceries have not been paid for."
   - "Ramesh cooks one plain meal a day, dal and rice in the evening: he has not been paid his wage for cooking."
   - At dinner: "Ramesh serves the one plain meal of the day before he goes home: dal and rice."
8. Dues: "Due within the fortnight: ₹11,600 in all. Ramesh's wage ₹8,000 on Tuesday 1 December; groceries ₹1,500 on Sunday 29 November and Sunday 6 December; the dhobi ₹300 on Saturday 28 November and Saturday 5 December. You hold ₹2,400." (the costs as the purse names them: "the dhobi", "groceries", "Ramesh's wage", "Ramesh's wage, three days a week", "electricity", "mobile data").
9. The Review asks again.
   - At home: "Ramesh brings a letter from the editor of the Yamuna Review. She asks again for an essay of yours: ₹6,000 in cash, on your next sitting of at least three hundred words. This time she names her question: you taught that India has no history of its own making, and you have now lived in its capital. Does the sentence stand?" (At the IIC it begins "The programme officer has a message from the editor of the Yamuna Review."; at Khan Market, "Nidhi has a message from her friend, the editor of the Yamuna Review.")
   - Page: "The editor of the Yamuna Review asks again for an essay, ₹6,000 in cash, and names her question: does his sentence stand, that India has no history of its own making?"
   - "Did you agree to write the essay for the Yamuna Review, on the editor's question, for ₹6,000 in cash at your next sitting of three hundred words or more?"
   - yes: "He agrees to write the essay for the Yamuna Review." no: "He declines the essay. The editor says she will ask again."
   - On his mind until it is written: "The Yamuna Review waits for your essay: ₹6,000 in cash at your next sitting of three hundred words or more. The editor's question: you taught that India has no history of its own making, and you have now lived in its capital. Does the sentence stand?"
10. The gift.
   - "Ramesh brings an envelope that was left at the gate, with no name on it. Inside are ₹2,000 and a card in a careful hand: 'For your talk at the Centre. I have thought of it every day since. This city has need of what you think, and of what you think next. What comes next?'"
   - Page: "An envelope left at the gate, with no name: ₹2,000, and a card that thanks him for your talk at the Centre and asks what comes next."
   - The pieces it can name: "your talk at the Centre", "the first evening of your course" (second, third, fourth), "your essay in the Yamuna Review", "your column in the Yamuna Review".
   - Income: "The envelope holds ₹2,000." Item: "A gift, left at the gate", from "an admirer who gives no name".
   - Course, the note at home: "Ramesh brings a note from the India International Centre. The Centre was glad of your talk, the programme officer writes. It would like a course of four evenings, one a week, in the lecture hall at half past six: ₹3,000 an evening, paid in cash at the door."

## Not done, and why

Credit with Ramesh is not built. The file's hearing (part 2) is drafted for Welt's pen in `pc/FILE-HEARING-SHEET.md` and not built. The questions of the column's later pieces wait for Welt's list.
