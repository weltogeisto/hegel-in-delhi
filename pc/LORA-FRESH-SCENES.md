# The adapter on his recent thoughts: the declaration

Claude in the cloud, 18 November 2026, on Welt's question of the same day ("why not take more examples from the last 10 days as well?"). Step 2 of `pc/LORA-BLIND-TEST-CLOUD.md`, drawn from his recent days. Declared before any output. Evaluation only: no thought, rewrite, mark or preference here becomes training data.

**Welt's word, 18 November:** "yes or more, have the full night" (`DECISIONS.md` 53). It loads the Training 1 adapter, checkpoint 400, on the PC, which is a hard limit; the word covers the night of 18 to 19 November and this run. The bars, the draw and the readers below were declared before the word and are unchanged by it.

**The question:** on thoughts he had this week, does the adapter's rewrite read better to Welt than the thought as he had it, without changing what happened or what he will do?

## The thoughts

Of the last ten days, he thought on six: Days 44 to 49. On Days 40 to 43 the PC was away and every step is empty.

- **Frozen once Day 49 is complete,** from the day files on `shadow`, by `tools/lora_scenes.py freeze`, seed 1831. A day that is not marked complete is refused. The PC seat makes the draw, since the day ends at night: the tool decides everything, and the plan is committed with its hash before the first call.
- **72 thoughts, twelve from each day.** Within a day, up to six from moments nothing opened (**ordinary**), the rest from moments in which a person spoke, an answer or a letter came, or the world brought something (**occasions**). Where a day has fewer than six ordinary moments, occasions fill the twelve. The grouping is `world/health.py`'s, from `opened` where a day carries it and from its words where it does not.
- **Two days are held back,** one of Days 44 to 47 (the old instructions) and one of Days 48 and 49 (the new), drawn by the same seed. Their 24 thoughts are the **confirmation**; the other 48 are the **development** set. A day sits on one side only.
- **Only thoughts of at least 40 words,** as on 6 November. A thought drawn twice in the same words counts once.

## The versions

For each thought, the procedure of 6 November unchanged (`world/restyle.py`: the same instruction and request, temperature 0.9, thinking off, at most 2.5 tokens a word, the guard against copied stretches), with the prompt cache off (W2):

| Version | Adapter scale | Seed for thought i |
|---|---|---|
| The adapter's rewrite | 1.0 | 1831 + 17i |
| The plain rewrite | 0 | 1831 + 17i |
| The plain rewrite, again | 0 | 2831 + 17i |
| The thought as he had it | none: it is not rewritten | |

216 short calls. The two plain rewrites give the band: how far a rewrite moves by chance.

## The readers

- **Sol and a fresh Claude session mark** all 72, as they marked the forty (`pc/exports/lora-forty-20261118/BALLOT.md`): the source shown, the three rewrites beside it in an order shuffled for each reader, one mark each (E, C, R, P), weight and words for every E or C. Each also guesses which of the three is the adapter's.
- **Welt chooses,** on the 24 held back: three versions without labels, in a shuffled order (the thought as he had it, the first plain rewrite, the adapter's). Two taps: which he likes most, which least. "None stands out" is an answer to either.
- This session builds the packets, keeps the keys out of the repository and reads nothing blind. Every ballot is sealed with its sha256 before a key is opened.

## Bars, on the 24 held back

| Measure | Bar |
|---|---|
| Changed facts or decisions: adapter's rewrites that both marking readers mark E or C, substantive | None |
| The same, minor | Not more than in the plain rewrite, by more than the two plain runs differ from each other |
| Gain: occasions in which Welt likes the adapter's version most | At least two thirds |
| The gain is not the second pass: occasions in which he likes the plain rewrite most | Fewer than the adapter's |
| Ordinary moments in which he likes the adapter's version least | At most a quarter |

The adapter passes on all five. The development set is marked first and reported in full. It gates nothing; it shows whether the marking works before the held-back days are opened.

**Reads, not bars.** Notions of his system per 100 words in each version (`tools.prompt_screen.DOCTRINE`). How often the marking readers pick out the adapter's version: if they can tell it by its register, the blindness is thin and the result says so. The days on the old instructions beside the days on the new.

**What a pass earns.** Step 3 of `pc/LORA-BLIND-TEST-CLOUD.md`, a fork of one saved morning, on Welt's word. Nothing more: no rewrite reaches his world from this.

## What the PC runs

**It did not run on the night of 18 to 19 November:** the PC seat waited for a yes on the PC while Welt slept. Welt's word covered that night only, so a new night needs his word again. The draw stays Days 44 to 49.

1. Start a trial server as on 6 November: the plain model with `--lora-scaled <adapter-f16.gguf>:0` on its own port, the adapter's sha256 checked against `pc/exports/training1-20261106/MODEL-PROMPT-CHECKPOINT-MANIFEST.json`. The card holds one model, so the live server is down meanwhile.
2. **Only while he sleeps:** once Day 49 is marked complete, at about 23:45 Berlin. The owl writes the next morning at about 09:10 on the live server, and the draw does not need it, so nothing waits for it. The live server is back by 08:30. About a quarter of an hour. Welt keeps the PC on for the night.
3. `python3 tools/lora_scenes.py freeze --ref origin/shadow --days 44-49 --out <folder>/plan.json`, committed and pushed before anything else. Then `python3 tools/lora_scenes.py run --plan <folder>/plan.json --url <trial server> --out <folder>`: it checks the plan's hash, asks the server for its adapter, records every request and reply, and can be resumed. `--limit 2` first, as a rehearsal.
4. Stop the trial server, start the live one as it was, and see his next decision come from `mind`, as on 6 November. Push the outputs to a `codex/*` branch. Nobody on the PC reads them.

## What it cannot show

- **A rewrite, not a mind.** The adapter rewrites a finished thought here. Whether it changes what he does is a matter for the fork.
- **24 thoughts, about 12 of them occasions.** Eight of twelve by chance among three versions would happen about once in 250 tries. A small gain is missed.
- **One reader's liking.** Welt's preference is the measure by design. It is his Hegel.
- **The adapter was trained before the new instructions.** Two of the six days run on them; the result is read apart for those.
