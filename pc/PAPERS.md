# Reading returns text: the papers (WORLD-3, packet 2)

Each morning the waking line carries up to three real headlines. Nothing was behind them: `read` gave no text, and nothing he read was
remembered. Two switches, both off by default. With both off every prompt, state and day file is byte for byte what it was
(`tests/test_opened.py`); tests are in `tests/test_papers.py`.

## `HEGEL_PAPERS_RECORD` (recording only)

When the feeds are online, the same pass that fetches the headlines also keeps the pieces behind them:
`<state>/feeds/papers-<date>.json`, a list of `{"title", "summary", "link", "source"}` for every headline that pass kept (up to six a
feed), in the same order. The first three are the headlines he is shown at waking; the rest are the inside pages, which he reaches by reading on. The summary is the RSS item's `description` with tags stripped and whitespace folded, cut to about 600 characters at a
sentence end (`works.cut`). `source` is the feed's own title, or its host. One download, the same headlines; nothing he is told changes.
If the day's `news-<date>.json` already exists when the switch is turned on, that day has no pieces (the headlines are not fetched again).

## `HEGEL_PAPERS` (what he is told)

- **Papers he can open.** When the day's pieces are in the cache and he decides `read` at home (place home, and he is at home), the engine
  gives him the next piece of today's papers he has not read: `state["today"]["papers_read"]` lists the indexes. One piece a step. When none
  is left, `read` is as it was. The piece travels the way a look-up does: `ctx["read"]` → `step["read"]` → the next situation, which opens
  with kind `read` and shows its headline and paper in the event, and its summary in his prompt under "The piece, as the paper prints it".
  `HEGEL_PAPERS` also turns the world's flag on in the engine, as `HEGEL_CONSUMED` does.
- **The waking line** says once, after the headlines, where the papers are: " The papers are on the verandah table." when Ramesh has left
  them (the existing line says "on the verandah"), and " The papers are on the step, there to be read." when the hawker threw them (the
  existing line says "on the step"). Only when pieces are in the cache.
- **A trace.** `state["readings"]`: for each piece read, `{"date", "title", "source", "line", "piece"}`, the latest 40. `line` is the first
  sentence (at most 160 characters) of his thought in the step that opened with the piece: his own words, no model call. `piece` is
  `[date, index]`, which finds the text again (an addition to the four fields of the brief: the archive's date is not the reading day).
  A step with no thought of his own (a quiet step) leaves no trace.
- **Stories that run for days.** At waking, a headline that shares two or more content words (lower-case letters, five or more, minus a short
  stop list in `world/papers.py`) with a title read in the last 14 days gets, after it, `(You read of this on 24 November: "…")` with his
  line. At most one note a morning; the moment's `opened` gains `story` after `papers`.
- **Met, and material.** The titles and summaries of what he read are added to `Memory.known_text`, so the 1831 gate lets him name what they
  name. A block "What you have read lately" (the latest five, each with his line) is added to `Memory.manuscripts`, so a writing and a lecture
  draw on it.

## `HEGEL_PAPERS_BODY` (the text behind the headline; off by default)

Only together with `HEGEL_PAPERS_RECORD`; it changes nothing he is told unless `HEGEL_PAPERS` is on too. When the record keeps a day's pieces
(never for a day already cached), the headlines are settled and cached first, and then, for each kept piece with a link, the page is fetched
once: one request at a time, 1.5 seconds apart, the engine's User-Agent, a 15-second timeout, at most 12 pages a morning. The text is read
from the page's `application/ld+json` blocks (an object, a list, or an object with `@graph`; a block that does not parse is skipped): the first
article object with a non-empty `articleBody`.

- **Only what the paper marks free to read.** An article object on the page with `isAccessibleForFree` false (`false`, `"False"`, `"false"`)
  means no body, and so does the key being absent: free must be said (`true`, `"True"`, `"true"`). The Hindu says false; the Indian Express
  says `"True"`.
- The body is made plain (entities unescaped, tags and whitespace folded), cut at a sentence end to 1800 characters, and kept on the piece as
  `"body"` with `"free": true`. A page that fails, has no block, or a body under 400 characters is a piece without a body; it keeps its summary.
- **What he reads.** With `HEGEL_PAPERS` on, a piece with a body is shown with its body in "The piece, as the paper prints it", and the body
  (instead of the summary) is what counts as met (`papers.read_text`). A piece without one is shown with its summary. The order is as before.
- Stored in `<state>/feeds/papers-<date>.json` and shown in his prompt only; the day file, the public entry and the step record never hold it
  (`test_the_body_counts_as_met_and_the_day_file_holds_no_body_text`). A rehearsal's archive gives the files as they are, body included.
- `tools/collect_papers.py --body` sets the switch for its own run; its line gains `"with_body": n`. Off, every file is byte for byte as before.
- The fetching happens in the same call as the headlines, after they are cached, so a morning with the switch on takes up to about twenty seconds longer.

## What is stored where

| What | Where |
|---|---|
| Full pieces (title, summary, link, source; with `HEGEL_PAPERS_BODY`, `body` and `free` where the paper marks it free) | `<state>/feeds/papers-<date>.json`; never in the repo |
| Which pieces today he has read | `state["today"]["papers_read"]` (day file: indexes only) |
| The trace: title, source, his line, `[date, index]` | `state["readings"]` (day file) |
| The public entry | `{"k": "read", title, source, url, date, i, text: "In the paper, at home."}`: headline, paper and link only |

## The page rule (WORLD-3 rule 3)

A newspaper's text stays in his prompt and in the state folder. The day file holds the headline, the source, the link and where the piece
is (date, index). The text is resolved from the state folder when the next situation is rendered, and it is put in `sit["paper"]`, not
in the step's `event`, because the step keeps its event in the day file. `test_the_day_file_holds_no_newspaper_text` serialises the day and
looks for the summaries. (The calls recording under `<state>/calls` holds prompts and so the text; it is not published.)

## Rehearsals: `HEGEL_PAPERS_ARCHIVE=<folder>`

A rehearsal has no network and lives future dates. With `HEGEL_PAPERS` on and this set, the pieces for date d come from the folder's
`papers-*.json` files (the files `HEGEL_PAPERS_RECORD` writes: copy them from a state folder's `feeds/`), taken in date order of their
names and cycled: index = (days from the rehearsal's first day to d) mod (number of files). The first day reads the first file. The first
day is `HEGEL_PAPERS_FROM`, which `rehearsal_setup` sets to the rehearsal's start date when an archive is set (a fork starts its own cycle at
its own start). The titles of the day's pieces are its headlines when no feed was cached. Unset, or `HEGEL_PAPERS` off: the folder is never read.

## Left for later

- A reviewed exhibition (or a lecture, a film) in the papers becoming a place he can go to (packet 7).
- Using what he read in a thought, a letter or a talk is not yet counted (the "Came back" measure of the score).
- Pieces for a day whose headlines were cached before the record was switched on; papers from before the switch.
- `read` away from home (the club, the library) and a second paper in the same sitting.
