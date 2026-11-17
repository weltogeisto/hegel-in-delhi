# M2: a label that says whose words he is reading

**The finding.** A quarter of the Philosophy of Right on his shelf is not his published text. It is Gans's additions of 1833: students' notes of the lectures, set under the sections after his death. The shelf showed them under the same label as the sections themselves. Manual v1.1, §6.2 named the loss; this measures it and repairs it behind a switch.

## What was lost, and where

| Step | What happened to the addition's name |
|---|---|
| The cleaned text | kept: `§ 258 Zusatz.` in German, `Addition. —` in Dyde's English |
| `split_passages` | the reference became the bare section, `§258` |
| A long addition | ran over several passages; only the first carried the mark |
| `shown` | stripped `§ 258 Zusatz.` from the excerpt |
| The prompt, the step record, the page | `Philosophy of Right §258`, as if it were the section |

## How much

| Text | Passages | Begin inside an addition | Of those, with no mark of their own |
|---|---:|---:|---:|
| Philosophie des Rechts (German) | 1,057 | 268 | 173 |
| Philosophy of Right (Dyde) | 857 | 222 | 154 |

On Day 12 and Day 27, the two recorded days in T49's packet, he was shown 162 passages. 82 came from the Philosophy of Right, and 16 of those began inside an addition under a plain section label.

## The repair

`HEGEL_SHELF_ADDITIONS=1`, off by default. With it:

- **The label names the addition:** `Philosophie des Rechts §258 Zusatz`, `Philosophy of Right §258 Addition`. The step record and the page take the same reference.
- **A carried addition is named too.** `Shelf.within` looks back through the passages before for where the addition began.
- **An addition that begins inside the excerpt keeps its mark** in the text, `Zusatz:` or `Addition. —`, and the label stays the section's.
- **His own remarks stay his.** Dyde's `Note. —` opens Hegel's remark, and it is labelled as the section.

Nothing is rebuilt: the index and the cleaned texts are untouched, and the name is recovered at retrieval from the marks the passages still carry. Without the switch every label and every excerpt is byte for byte what it was.

## One trace, from the record to the prompt

Day 27, 10:34, the step where Shri Hegde asks for the boy (`pc/exports/t49-arm-d-20261114/for-claude/evidence/`, the case of 2026-10-28 at 10:34).

- **Passage:** `dyde-right:205`, reference `§70`.
- **As he was shown it:** `- Philosophy of Right §70: “Addition. — The particular person is really a subordinate, …”`
- **With the switch:** `- Philosophy of Right §70 Addition: “The particular person is really a subordinate, …”`

The path: `Engine.offer` → `Shelf.pick(additions=True)` → `Shelf.within` → `fit` → `shown` → `contract.render`, under "From your shelf" → the step's `shelf` entry → the diary and the page.

`tests/test_shelf.py`, `AdditionsTest`, covers the whole path from a cleaned text to the rendered prompt, the carried addition, the English forms, the switch, and the two counts above on the real index.

## What it does not repair

- **Wallace's Logic and Mind.** Their additions carry no mark in the cleaned texts, so nothing can name them at retrieval. The corpus builder would have to mark them from the source.
- **The lecture volumes.** The Philosophy of History, the History of Philosophy and the Fine Art are editors' compilations from notes throughout. His instructions already call them "your lectures"; the label does not say who compiled them.
- **Translators and editions.** They are in `mind/shelf/MANIFEST.md` and not in the index.

## Before it goes on

The switch changes what Hegel reads and what the page shows, so it needs Welt's word. It changes the prompt's text in about one shelf line in ten on a day like Day 12. Training 3's sampler replays the live prompt, so the switch should go on between sampling runs, never in the middle of one.
