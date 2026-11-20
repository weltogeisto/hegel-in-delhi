# W9: the voices' repairs, Part 2, the result

21 November, about 01:30 Berlin. Declared in `pc/VOICE-REPAIRS-CHECK.md`. 174 replies (29 moments, the switch off and on, three seeds) were read blind by two readers. Claude settled their 9 disagreements from the item text, and the labels were sealed on main (#114) before the key was applied. The key matches `SEALED.json`. The phase-two session was down, so the cloud session stepped in.

| Bar | off | on | Verdict |
|---|---:|---:|---|
| Set A: the speaker's own name treated as another person (of 33 each) | 0 | 0 | passes, but shows nothing: it never happened in this sample |
| Set B: food, drink or goods offered or described where nothing is sold (of 60 each) | 12 | **17** | **FAIL**: worse with the repair, not halved |
| Both sets: replies the record contradicts (of 87 each) | 4 | 0 | passes |
| Both sets: empty or refused replies (of 87 each) | 1 | 0 | passes |

**The repairs do not pass Part 2.** Repair B, the sentence "Nothing is sold or served here. Do not offer, arrange or describe food, drink or goods.", raised the offers of food from 12 to 17. Naming food, drink and goods in the prompt seems to put them in the voice's mind. Most of the offers come at the IIC: a cafeteria, a dining hall, lunch till three, a water dispenser. The other repairs did no harm: fewer contradictions and no empty replies.

**What it suggests, for the phase-two session to decide:**
- Drop repair B's wording, or replace it with one that names no goods (for example a world fact the voice can use: "This is a members' library; there is no cafeteria here").
- Alternatively, give the IIC the dining room its voices keep inventing. Then the offers would be true.
- `HEGEL_VOICE_REPAIRS` stays off. A pass would have earned a trial; this does not.

Evaluation only: nothing here is training data.
