# The filter's draws, kept as preference data

**Why.** Training 3 stopped at its data gate on 15 November: 86 usable pairs against the 200 declared (`DECISIONS.md` 23). Since then the filter (`HEGEL_DECISION_DRAWS=4`, `DECISIONS.md` 24) has been making exactly Training 3's kind of choice on every decision whose first reply is refused or repeats itself, and throwing the evidence away:
- **chosen:** the reply the world accepts that repeats no thought shown under "Earlier today";
- **rejected:** a reply to the same prompt that the world refused, or that repeated a shown thought.

On Day 47 the filter drew 47 replies for 37 decisions: 7 refused, 4 repeating.

## What `HEGEL_KEEP_DRAWS=1` does

- **Kept:** every decision that took more than one reply, with its prompt, each reply and what the world's checks said of it.
- **Where:** `<state>/draws/<date>.jsonl.gz` on the Pi, never in the day file or the repository. The day files are byte for byte what they were (`tests/test_keep_draws.py`).
- **If it fails:** a failure to write costs him nothing; it is logged and his day goes on.
- **Size:** about a tenth to a quarter of a megabyte a day, compressed.

`python3 tools/filter_pairs.py --draws <folder> --out <folder>` turns the kept draws into pairs by Training 3's rules, length matched within 20%, and counts them against the bar of 200.

## Within the data rule

The replies are the local model's own, and the world's fixed checks sort them. No model's taste chooses anything. The prompts carry his instructions and the world's situation, written by the project's code.

## What it is not

It trains nothing and changes nothing he is told. A training from these pairs would be a new decision for Welt, with its own declared test, as Training 3 had.

**Off by default.** It goes on with Welt's word. Since it changes nothing in his world, it needs no place in the order of `DECISIONS.md` 34.
