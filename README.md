# Hegel in Delhi

G. W. F. Hegel, fifty, wakes up in a Lutyens bungalow that the Directorate of Estates allotted to him by mistake. A local model lives his days on a Game Boy Color–style map of two square kilometres of Delhi, live and unscripted. Anyone can watch where he is, what he thinks, buys and wears, and whom he meets.

Live page: https://weltogeisto.github.io/hegel-in-delhi/

## How it runs

- **The world (Raspberry Pi 5, always on).** Clock in Delhi time, places, opening hours, prices, walking routes, the purse and the imprest account, the costs that recur, the offers that bring money in, the cast of fictional Delhiites, the Hegde file. Feeds for weather, air quality, news and holidays. It decides *when* Hegel must decide, checks every decision against the rules, and publishes.
- **The mind (PC with RTX 3090, asleep most of the day).** The Pi wakes it for each decision, 15–25 a day. Ternary Bonsai 27B or Qwen3.8-27B answers in a fixed JSON format (Hegel's own trained mind runs on Qwen3.8), then the PC sleeps again.
- **The owl (same PC, during Delhi's night).** The larger model writes the diary, the revision log and the weekly Depesche.
- **The page (GitHub Pages, free).** The Pi pushes each step 10–15 minutes before it happens; the page reveals it when its time comes.

No database, no subscription. The running cost is electricity.

## A step, from the inside

Every minute the Pi asks one question: does the published day reach fifteen minutes past now? Most minutes it does, and the Pi goes back to sleep without touching the network.

When it doesn't, the world builds the next situation: the time, the weather and the air, who is present, what is open and until when, what things cost, what is on his mind, and what happens. Something always happens, even if it is only the afternoon going on. The papers arrive at dawn, Ramesh lays out lunch, Khan Market closes, Shri Hegde rings the bell at ten. The Pi wakes the PC and the mind answers in JSON. The world checks the answer against the rules: closed is closed, walking takes the time it takes, cash cannot go below zero, and no alcohol is sold on a dry day. If the answer breaks a rule, the world says which one and the mind decides again. The step becomes segments for the map and entries for the panels, written into `docs/days/<date>.json` and pushed. The page polls once a minute and reveals each step when its time comes.

When he speaks to someone, that person answers: one more call, voiced by the model from their card, and the answer opens his next situation. A person he knows may also speak first when they come into sight. When he sits down to write, one more call writes the sitting (a title, the kind, whom it is to, the text); each sitting goes into his manuscripts. A plain-text path is kept behind `HEGEL_WRITE_MODE=plain` (it was the default from 6 to 10 October; real samples kept to the subject but lost his thinking): one call asks what he means to write (a title, the kind, what the sitting is about), and the text itself is a plain-text completion under a header in the style of his books, which sounds like them where the chat call sounds like an assistant: in front of the header lie two passages of his own English books, each under a header that names its topic ("Hegel, On war. From the Philosophy of Right."), so that the model sees a header decide what follows (they are drawn from the Hegel test's passages, never one on the sitting's own subject, and are not part of the text), and under the header two lines in an editor's brackets, what the sitting is about, and that he died at Berlin in November 1831 and woke in Delhi on 2 October 2026, so many days ago; a completion that copies an exemplar or leaves the subject is made again with another seed, and if that fails too the chat call writes it (`HEGEL_WRITE_MODE=chat` brings back the single chat call; `tools/writing_sample.py` shows what a plan makes of it on the PC); each sitting goes into his manuscripts.

Money is a simulated economy, with prices in plausible 2026 rupees: nothing is bought for real. He carries cash. The imprest is the state's money in his keeping: every purchase leaves a voucher, and at the Directorate Mr. Saxena refills what is office expenditure and queries the rest, which then stands owed. Income comes only from what he does, offered by the people he meets (lessons, a talk, a coat sold, a loan, an essay); groceries, the dhobi, the electricity, Ramesh's wage and the phone's data recur, and while the wage or the groceries are unpaid nothing is cooked at home. With a phone and a SIM, bought through someone who can vouch for him, he can look something up on Wikipedia, and what he reads counts as met.

Often a few lines of his own books lie open before him: the engine looks for the passages, in German or in English, that touch what is happening (a grocer in Khan Market brings up the system of needs, a question of caste brings up India) and offers one or two, cut to about two sentences, under "From your shelf". They are there to think with. Which books he had open is written into the step and under the thought on the page. The shelf is Hegel's own works as far as public-domain texts could be had (17 texts, 12 MB of text and 9 MB on disk, in `mind/shelf/`, with a manifest); the search is BM25 with a small table of German and English equivalents, runs on the Pi in about ten milliseconds and fetches nothing. Beside the shelf, but never on it, lie two lives of him, the papers of his youth and his letters, those he wrote and those written to him, 1785-1831 (Rosenkranz 1844 and Karl Hegel's edition of the letters, 1887, both read afresh from the Fraktur; Caird 1883), cut where he dies: they are for training the mind on his life, not for him to read.

He remembers from the day files: his last moments with the people in front of him, the last thing he thought in this place and the owl's gist of the last three nights. On waking he makes one extra call for a plan, which stays on his mind all day. A Body line tells him his last meal, how far he has walked and how long he has been up, and the event says so when he is hungry or tired.

The day file is the state. Each one opens with what Hegel carries in from yesterday and closes with what he carries into tomorrow. At half past one the owl writes up yesterday, and on Saturdays it writes the Depesche.

## The rules

The living are invented, the dead are on his shelf, the news is real: everyone he meets is fictional, and he may name the public figures he reads about, though no words are invented for them. The simulation is realistic and does not steer him: his views are his own, nineteenth-century ones included, nobody corrects him, and if he changes his mind it is Delhi or he that changed it. The world flags what is sensitive and never refuses it; those entries sit under a dark veil on the page until a viewer clicks. The morning papers carry the state, the economy, the courts and the wars, and leave out crime and violence.

## Layout

| Path | What |
|---|---|
| `docs/` | The public page |
| `docs/days/` | One file per day, written by the world; day 1 is the hand-written prologue |
| `docs/map/` | The map as data, derived from OpenStreetMap (ODbL) |
| `world/` | The world engine: places, hours, prices, the cast, the Hegde file, the rules, the feeds, the owl |
| `world/data/` | The world's facts as JSON and word lists, editable without touching code |
| `mind/` | The day mind's prompt, the owl's, the voices', test situations and the bake-off |
| `mind/shelf/` | His books: cleaned public-domain texts (`<id>.txt.gz`), the search index and `MANIFEST.md` (sources, why each is public domain, what was left out); also the lives of him and his letters, for training only |
| `mind/hegeltest/` | The data of the Hegel test: twenty blind passages and thirty questions about his life; the passages are also the exemplars of the writing prompt |
| `mind/train/` | The training data for Hegel's adapter, generated on the PC and never committed; its README says what goes in and why none of it is written by Claude |
| `pc/` | Windows scripts for the PC; `CODEX.md` sets up the mind, `TRAINING.md` trains Hegel's adapter (`train_hegel.py`) and serves it on port 8082 (`start-hegel.ps1`); `HEGELIZER.md` trains the Hegelizer, an adapter that restyles plain English in his manner |
| `scripts/` | Pi scripts: wake the PC, test wake and sleep, the world's timer |
| `tests/` | `python3 -m unittest discover -s tests` |
| `tools/` | `osm_map.py` rebuilds the map and the walking times from OpenStreetMap; run it only when the map should change. `corpus.py` fetches and cleans the shelf's texts and builds its index (`--index`); `hegel_test.py` is the Hegel test; `writing_sample.py` prints the prompt and the text that a writing plan makes through the world's plain-text path; `train_data.py` makes the training data from his books, his lives and Qwen's own best decisions; `hegelizer.py` makes the Hegelizer's pairs from his translations (a plain version by Qwen as the input, his real passage as the target); `ocr.py` reads a scan afresh with Tesseract where archive.org's text is too damaged (the Fraktur of Rosenkranz) |
| `HERMES.md` | The runbook Hermes follows |

`python3 -m world simulate --date 2026-10-03` rehearses a whole day offline with a stand-in mind whose thoughts are marked `(rehearsal)`. Add `--mind http://PC:8081` to rehearse with the real one. Nothing is pushed.

## Plan

1. Repo and page ⟶ Hermes, task 1
2. The mind on the PC ⟶ Codex, `pc/CODEX.md` 1–6; Hermes, task 2
3. Bake-off: Bonsai vs Qwen ⟶ Hermes, task 3; Welt decides
4. Wake and sleep ⟶ Codex 7–8, Welt (BIOS, router); Hermes, task 4
5. World engine on the Pi ⟶ written; Hermes installs and rehearses, task 5
5b. The shelf and the Hegel test ⟶ written; Hermes runs the test for Bonsai and Qwen, task 5b; Welt and Claude judge the sheets
5c. Hegel's own mind: an adapter on the installed Qwen, trained on his books and on Qwen's best decisions in rehearsal ⟶ written; Codex trains it, `pc/TRAINING.md`; Hermes tests it, task 5b
5d. The Hegelizer: an adapter that restyles plain English in his manner (inverse paraphrasing of his translators) ⟶ written; Codex trains and tests it, `pc/HEGELIZER.md`; the world does not use it yet
6. Live page reading the day files ⟶ written; day 1 replays until the first live day
7. Shadow week on the `shadow` branch, watched at `?branch=shadow` ⟶ Hermes, task 6; then the public switch, task 7
8. The owl at night ⟶ written, on the day mind's model until the PC can switch to the larger one at night; real streets from OpenStreetMap done
