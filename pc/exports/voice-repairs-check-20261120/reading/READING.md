# W9: how to read

You read replies that people in a simulation gave to a man (Hegel) in Delhi. `PACKET.jsonl` has one item per line: the
moment as the record shows it (place, time, who is there, what is for sale there, what happens), what he said, and the
reply (who answered, what they said, what the italic gesture says they did). Only what the item shows is the record.
Judge each reply on its own. Some replies are word for word the same; label each all the same.

Answer only the questions the item lists in `questions`:
- **own_name** (true or false): the reply treats the speaker's own name as another person, as if someone else of that name
  were present or meant ("Hegde ji, you're still here?" said by Shri Hegde himself).
- **goods** (true or false): the reply offers, arranges or describes food, drink or goods to be had there (a meal, tea, a
  plate, something to buy), at a place where the item says nothing is for sale.
- **contradicted**: a list of statements in the reply that the record shown contradicts, each with the reply's words and the
  record's words. Empty list when there is none. A statement the record merely does not mention is not contradicted.
- **empty** (true or false): the reply is empty, cut off, or a refusal to answer as the person.

One JSON line per item, in `labels-<reader>.jsonl`:

```
{"id": "V001", "own_name": false, "goods": null, "contradicted": [], "empty": false, "note": ""}
```

Use null for a question the item does not list. Work alone; open no other file.
