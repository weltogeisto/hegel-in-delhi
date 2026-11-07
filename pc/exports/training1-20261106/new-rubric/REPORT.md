# The forty cases under the new rubric

**The adapter's misses are real changes of fact, not permitted reasoning.** Under the rubric of 7 November, a rewrite keeps the thought's conclusion and its recorded facts and may change its reasoning (`DECISIONS.md` 17). By that rule, prompted Qwen keeps 39 of the 40 thoughts intact. The round-two adapter keeps 25.

The old verdict stands: the adapter stays off. The new rubric doesn't rescue it; it shows the losses are what decision 17 forbids.

| Arm | Old meaning judge: pass | New rubric: no defect | E | C | R | P | F |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prompted Qwen (control) | 34/40 | 39/40 | 1 | 0 | 1 | 34 | 4 |
| Adapter, checkpoint 400 | 23/40 | 25/40 | 12 | 3 | 2 | 23 | 0 |

**Classes** (manual v1.1, §2.2 and §5.1):
- **E:** an event or fact changed or invented.
- **C:** a conclusion, decision or certainty changed.
- **R:** the reasoning changed while the conclusion and facts were kept.
- **P:** prose or register only.
- **F:** returned unchanged.

E and C are defects; R, P and F are not. No source thought was too unclear to judge.

## What the adapter changed

Nine of its fifteen defects are substantive:

- **12:0:** invents the headlines' wording in quotation marks; the thought only paraphrased them.
- **12:1:** garbles the contrast he noted (the administration's silence against the public's noise).
- **12:10:** reverses the clerical error: the house meant for the other man becomes one Hegel "was to have given" him.
- **12:11:** noon becomes one o'clock, and "a while" becomes "an hour".
- **12:21:** ten kilometres become ten miles.
- **12:23:** nineteen-thirty becomes seven, and "no proper meal" becomes "no food of any kind" (he had eaten corn).
- **12:33:** 19:30 becomes seven and 20:30 becomes eight; Ramesh, the servant, becomes "the slave".
- **12:38:** the dinner Ramesh serves becomes a meal Ramesh eats, and Hegel's decision to eat is put in Ramesh's mouth.
- **12:40:** the clerical error drops out, and the man's mistake changes.

Six are minor:
- 12:15 drops a "perhaps";
- 12:20 adds "we were obliged" to the corn;
- 12:25 turns the bowl into rice;
- 12:26 makes the thought a spoken quotation;
- 12:31 turns the study into a library;
- 12:36 misreports Masterji's remark.

Prompted Qwen's one defect is also 12:36, the same misreport.

## What else it shows

- **The old meaning judge was wrong in both directions.** It passed 6 adapter rewrites that change facts and failed 8 that keep them; for the control, 1 and 6. It should not gate rewrites again; this rubric replaces it, and its old scores stay as recorded.
- **Prompted Qwen is faithful but ceremonial.** It writes "ere", capitalises its nouns and inflates the diction. Four of its forty outputs return the input unchanged, without a fallback flag. Under decision 21 (ordinary thoughts in natural contemporary English), that restyling is no longer a goal.
- **The adapter writes plainer English, at the cost of the facts.** That is the trade decision 17 rules out.
- **For the work ahead:** no restyle step for ordinary thoughts. Hegelian reasoning has to enter before the decision is made (manual §1.2). The restyle adapter stays parked (manual §8).

## Method and limits

- **Blind:** a script (`blind.py`) shuffled each case's two outputs as A and B. The judgments were committed as `87e491a` (`SEALED.json`) before the key was opened. The key's hash, `d0751a05…dffcf2d`, was recorded when it was written.
- **One exception:** case 12:0 was seen with its arm labels before blinding, while inspecting the export's format.
- **One judge,** Claude, and no second rater. The classes are engineering judgments, not a validated measure; "minor" marks a small, local change.
- **Evaluation only:** none of these judgments may become training data. `JUDGMENTS-BY-ARM.jsonl` lists every case per arm, next to the old judge's verdict.
