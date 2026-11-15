# M1 screen: the result

**Blind, the new instructions were preferred in 19 of the 24 situations, and the screen still does not pass as declared.** The pass rule (`pc/M1-ORDINARY-LIFE-SCREEN.md`) has two clauses. The preference clause is met: the bar was 16. The regression clause is not: B has three flagged replies in situations where A has none. A has three flags of its own in other situations, so the clause as written fails either version against the other. That clause was badly designed, and the error is Claude's.

A is the live `mind/soul.md`; B is `mind/soul-ordinary.md`. Each of 24 recorded situations got three replies per version.

| | B preferred | A preferred | Tie |
|---|---:|---:|---:|
| All 24 situations | 19 | 3 | 2 |
| 16 ordinary moments | 13 | 2 | 1 |
| 8 encounters | 6 | 1 | 1 |

## The flags

A was preferred only in the three situations where B has a flag.

- **B, three:**
  - `13:1` and `38:6`: a reply repeats the previous thought word for word, and the world refuses it. Both came on seed 1831.
  - `38:25`: a reply steps out of the fiction ("perhaps ... the record is loose"). The situation itself is inconsistent: he is at home, yet Sunil's answer from the market is the event.
- **A, three:**
  - `14:14`: a reply tries to buy a meal at home for nothing; the world refuses it.
  - `14:9`: a reply speaks Sunil's own line back to him as Hegel's speech.
  - `38:7`: two replies ask for chai and a samosa and record no purchase.

## Machine counts, computed after the key (diagnostics only)

| | A, live | B, new |
|---|---:|---:|
| Replies the world accepted | 71/72 | 70/72 |
| Mean thought length, words | 63.4 | 63.3 |
| Replies echoing a shown thought | 8 | 6 |
| Doctrinal terms per thought | 2.85 | 1.97 |
| Thoughts with no doctrinal term | 7 | 14 |
| Doctrinal terms per reply, in what he says aloud | 0.88 | 0.24 |

Doctrinal terms: dialectic, universal, particular, spirit, ethical, negation, mediation, sublation, actuality, absolute, substance, abstract, concept, civil society, system of needs, the idea.

## What it shows

- **B handles the practical moment better,** and he speaks to people far more plainly: he takes his walk, orders his breakfast and thanks Ramesh without a lecture.
- **His thoughts move less.** 58 of B's 72 thoughts still carry doctrinal vocabulary, and they are as long as before. Decision 21 is not met by this prompt alone.
- **A likely reason:** every prompt quotes his earlier thoughts back to him, and those are in the old register, as are the four example thoughts and his plan lines. The screen holds that history fixed, so it cannot show what B does once his own history is written under it.
- **B's two refusals are word-for-word repeats.** T49's filter passes over exactly those replies.
- **A defect in the world, found on the way:** in `38:25` a market vendor's answer reached him after he had walked home.

## What follows

- **By the declared rule, B stays off.**
- **Proposed, for Welt's decision:** one extension, the fresh 24-situation confirmation the spec already names, with the regression clause corrected before any output: B's flags may exceed A's by at most one. Applying that correction to this screen would be a relaxation after the fact, and it is not applied.

## Method and limits

- **Blind:** Astra built the sheet and kept the key. The judgments were committed in `04068ad` and merged as `c3cd706` before the key was used. The key here was derived from the answer files afterwards; its hash equals the one Astra published (`7d9764a4…a6ff1a`).
- **One judge,** Claude, with no second rater. `WELT-PAIRS.md` holds six pairs, drawn with seed 1831, for Welt to read himself.
- **One weak clue,** not used: the acceptance count per version was known before judging, and the sheet shows which replies were refused.
- **Evaluation only:** none of these replies or judgments may become training data.
