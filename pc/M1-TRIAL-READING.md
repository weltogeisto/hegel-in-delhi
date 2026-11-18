# M1's trial on shadow, read

**The question.** On 17 November at 08:39 Berlin his instructions changed from `mind/soul.md` to `mind/soul-ordinary.md` (`DECISIONS.md` 34). The screen predicted that his everyday thinking would become plainer and less doctrinal, without getting worse (`pc/exports/m1-confirmation-20261115/judgment/REPORT.md`). Did that happen in his world?

Declared on 18 November, about 22:40 Berlin, before any sentence is coded. Claude in the cloud, on Welt's word that night: "do something smart".

## The data

Frozen from shadow at `40e3362`, the bedtime step of Day 49. Both groups lived with the filter, and Day 47 onwards with the money from Munich.

| Group | Days | Instructions | Notes |
|---|---|---|---|
| old | 46, 47 | `mind/soul.md` | Day 46: the filter from 14:28, ₹6 in hand all day. Day 47: the letter and the money at 10:02 |
| new | 48, 49 | `mind/soul-ordinary.md` | Day 48: no mind from 09:59 to 11:59 (the PC was off). Day 49: a whole day; Ramesh back in the kitchen |
| letter | 49 | `mind/soul-ordinary.md` | His first letter to Dr. Lindner: the sitting that goes to the post (`world/post.py`) |

## The measures

1. **Machine counts per day** (`python3 tools/m1_trial.py counts`):
   - lecture-hall terms per thought, with the screen's own word list (`tools/prompt_screen.py`, `DOCTRINE`), and the share of thoughts without them;
   - mean thought length;
   - thoughts that echo a thought the prompt showed (the filter's rule);
   - calls per decision and steps with a refusal;
   - lecture-hall terms per spoken line.
2. **A blind topic profile** with stage 1's codebook, unchanged (`pc/exports/paris-stage1-20261115/CODEBOOK.md`):
   - up to 150 sentences of decision thoughts per group, drawn with seed 1831, and every usable sentence of the letter;
   - all in one shuffled sheet under opaque IDs (`python3 tools/m1_trial.py freeze`), with the key kept outside the repository until the codes are sealed;
   - two coders, apart: two fresh Claude agents that see only the codebook and the sheet, not the groups, the days or this question;
   - their codes sealed with their sha256 on main before the key is applied;
   - plain Qwen as a third coder on the PC later, if wanted (`tools/paris_profile.py requests` takes the same sheet).

## The reading, declared now

- **The trial moves as M1 predicted** if two things hold, and nothing gets worse beyond the old days' own range on echo, calls per decision and refusals:
  - by both coders, the share of philosophy proper (code 9) in the new group's thoughts is lower than in the old group's;
  - lecture-hall terms per thought are lower on each new day than on Day 47.
- **No clear movement:** the two coders disagree on the direction, or only one of the two conditions holds.
- **Worse:** philosophy proper rises by both coders, or echo, calls or refusals leave the old days' range upward.

Two days per side make this a description, not a test with power. The days also differ in what happened in them: the money came on Day 47, and Ramesh came back on Day 49.

**The letter** is reported beside the groups, with its distance to his real letters home (stage 1's profile). It is the first sample of how he writes to someone, against how the real Hegel wrote from abroad.

Evaluation only: no sentence, code or result here is ever training data.
