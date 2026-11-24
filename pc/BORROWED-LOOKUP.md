# HEGEL_BORROWED_LOOKUP: someone he knows looks it up for him

`DECISIONS.md` 7: technology reaches him through the people he meets; what he reads online counts as met. `DECISIONS.md` 69, point 4: this century fails to reach him for mechanical reasons, and the first is that he has no phone (a phone ₹9,000, a SIM ₹300), so `Engine.look` has answered "You have nothing to look it up on." on every one of his 55 days, and the 1831 gate leaves him silent about this century. What fits decision 7: when someone he knows is with him, they can look a thing up on their phone for him.

One switch, `HEGEL_BORROWED_LOOKUP`, off by default (`Config.borrowed_lookup`, `World(borrowed_lookup=...)`). Off, every prompt, schema, state and day file is what it is today (`tests/test_opened.py` passes without re-recording; the existing look-up tests pass unchanged). The world offers and never steers.

## What changes
1. **Who carries a phone he may ask.** `world/data/cast.json`: `"phone": true` on `nidhi`, `ananya`, `malhotra`, `hegde`, the four he is on terms with. Not officials at their desks, not shopkeepers. The key does nothing while the switch is off.
2. **The look-up.** With the switch on, no phone and SIM of his own, and at least one such person present, `looks_up` is answered by `Engine.look` as before (same `self.lookup`, same cache), and the page carries `"by": <person id>`: the first such person in the order they are listed as present (`World.phone_holder`). With his own phone and SIM, his own is used and nothing changes. With nobody present who carries one, the old note.
3. **How it reaches him.** The next situation opens with kind `read`, as a look-up does. The public `read` entry gains `"by": "<name>"`; the owl's record says "read on {Name}'s phone". It counts as met as a look-up on his own phone does: `encountered_text` already takes every string of a `read` entry, and the step's event text too. No voice call: the person says nothing of their own.
4. **He is told that he may ask.** One line among what is on his mind, for the first such person, while he has no phone of his own (`World.phone_line`). The decision schema already offers the optional `looks_up` at every moment (`contract.SCHEMA`), whether or not he owns a phone; so "the same condition" is "always" and the schema is not changed. The line is the only new fact he is given.
5. **Nothing else.** `mind/soul*.md` untouched.

## Words for Welt's reading
- On his mind: "{Name} has {her/his} phone: you may ask {her/him} to look something up (looks_up)." (Name is the cast's `name`, e.g. "Nidhi Rao", "Mr. R. K. Malhotra", "Shri G. Hegde".)
- The next situation, on a page: "{Name} looks it up on {her/his} phone and reads it to you: {title}. {text}"
- On a failure: "{Name} tries {her/his} phone: The page will not load." / "{Name} tries {her/his} phone: Nothing comes up for that."
- The owl's record: "read on {Name}'s phone, from {source}, “{title}”: {text}"
- Unchanged: "You have nothing to look it up on." when nobody with a phone is present.

## Tests
`tests/test_borrowed_lookup.py`, each item on and off.
