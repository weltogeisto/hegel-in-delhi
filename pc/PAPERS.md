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

## What is stored where

| What | Where |
|---|---|
| Full pieces (title, summary, link, source) | `<state>/feeds/papers-<date>.json`; never in the repo |
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

- **The body of a piece.** An RSS summary is a sentence or two. The article behind the link would give him more to think about. It means
  fetching the page on the Pi each morning and keeping its first paragraphs in the state folder, under the same page rule. Welt's call.
- A reviewed exhibition (or a lecture, a film) in the papers becoming a place he can go to (packet 7).
- Using what he read in a thought, a letter or a talk is not yet counted (the "Came back" measure of the score).
- Pieces for a day whose headlines were cached before the record was switched on; papers from before the switch.
- `read` away from home (the club, the library) and a second paper in the same sitting.
