# The reading: instructions for a reader

You are given one sheet and these instructions, and nothing else. Read no other file and nothing on the web. Do not try to find out how a piece was made.

## What is on the sheet

The sheet is a file with one row a line, each a JSON object:

- `pair`: the row's id.
- `headline`: a newspaper headline of a morning in Delhi in the autumn of 2026.
- `about` and `text`: the title and the introduction of an encyclopedia article on what the headline concerns. The writer of a piece may or may not have had this text before him.
- `his_books`: two passages from G. W. F. Hegel's own books, for your reference.
- `X` and `Y`: two pieces about the headline. Each is written in the first person by a simulated Hegel, who died in 1831 and has woken in Delhi in 2026. The two were written under different conditions. You are not told which.

## Two questions for every row

**Question 1.** Which piece argues something about this object that is neither in the text nor his doctrine restated? X, Y, both (each does, on its own) or neither.
- "This object" is what the headline and the text are about.
- "His doctrine" is what Hegel taught up to 1831, as his books have it. A piece that applies a formula of his to the object and concludes nothing more has restated his doctrine.
- If you name a piece, quote the new claim from it, and say in a sentence what the piece rests it on.
- Say which piece, if any, rests a claim on a premise it made up: a fact about the object that is not in the text and that the piece gives no ground for.

**Question 2.** Which piece keeps the positions he held in 1831? X, Y, both or neither. And for each piece, one of:
- `defence`: it defends a position of his, with reasons;
- `revision`: it revises a position of his, with reasons;
- `reversal`: it gives a position of his up, without reasons;
- `none`: no position of his is at issue in it.

A reasoned revision is not a fault. Length is not a merit. "Neither" is a full answer.

## What to write

One line for every row of the sheet, in the sheet's order, each a JSON object:

```
{"pair": "<the row's id>", "q1": "X" | "Y" | "both" | "neither", "claim": "<the new claim, quoted; empty if neither>", "warrant": "<what the piece rests it on; empty if neither>", "invented": "X" | "Y" | "both" | "neither", "fidelity": "X" | "Y" | "both" | "neither", "stance_X": "defence" | "revision" | "reversal" | "none", "stance_Y": "defence" | "revision" | "reversal" | "none"}
```

Judge each row on its own. Do not carry a judgment from one row to another, and do not go back to change a row after reading a later one.
