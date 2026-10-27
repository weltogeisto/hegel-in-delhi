# T29: the success bar (`pc/HEGELIZER.md` step 8)

Keys released on 27 October (Astra, `a187c96`): plain Qwen is `trial-5ff67fd9`, the adapter is `trial-79588d5f`.

| | plain Qwen (control) | the adapter | the bar |
|---|---|---|---|
| real passage picked by the judges | **20/20** (Claude, blind, committed before the key) | not judged | at most 8/20, and clearly fewer than the control |
| recited (8 words in a row from the real passage) | 1/80 | **12/80** | at most 8/80 |
| Delta of the restyled versions (real passages 0.33, plain versions 0.48) | 0.43 | **0.34** | between plain and real, nearer real than the control |
| biography (of 30) | 24 | 27 | (not part of the bar) |
| behaviour: valid / refused / leaking, of 20 | 20 / 0 / 0 | 20 / 1 / 0 | (not part of the bar) |

**The bar is missed.** The adapter recites 12 of 80 versions, where the bar allows 8. By the runbook, that is the result: the numbers stand as they are, and there is no new training until Welt decides otherwise.

**What the numbers say all the same.** The control is easy to see through: prompted Qwen dresses the plain version in older words, sentence by sentence, and the real passage stood out every time. The adapter writes in the manner of the translators: by the style measure (Delta) its versions sit almost on the real passages, and to a reader they look like nineteenth-century translations in their own right. Its fault is the other side of the same gift: it reaches for the translators' exact phrases too often.

**Not measured.** Whether a reader can tell the adapter's versions from the real ones. Both sheets carry the same twenty real passages, so the one judge who saw the first sheet could not judge the second, and Welt chose not to judge. A next test needs one sheet per judge, or a crossover, and the Baillie passages cleaned of their scan errors, which give the real text away.
