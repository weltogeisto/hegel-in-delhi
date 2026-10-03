# Hegel in Delhi

G. W. F. Hegel, fifty, wakes up in a Lutyens bungalow that the Directorate of Estates allotted to him by mistake. A local model lives his days on a Game Boy Color–style map of two square kilometres of Delhi, live and unscripted. Anyone can watch where he is, what he thinks, buys and wears, and whom he meets.

Live page: https://weltogeisto.github.io/hegel-in-delhi/

## How it runs

- **The world (Raspberry Pi 5, always on).** Clock in Delhi time, places, opening hours, prices, walking routes, the imprest, the cast of fictional Delhiites, the Hegde file. Feeds for weather, air quality, news and holidays. It decides *when* Hegel must decide, checks every decision against the rules, and publishes.
- **The mind (PC with RTX 3090, asleep most of the day).** The Pi wakes it for each decision, 15–25 a day. Ternary Bonsai 27B or Qwen 27B answers in a fixed JSON format, then the PC sleeps again.
- **The owl (same PC, during Delhi's night).** The larger model writes the diary, the revision log and the weekly Depesche.
- **The page (GitHub Pages, free).** The Pi pushes each step 10–15 minutes before it happens; the page reveals it when its time comes.

No database, no subscription. The running cost is electricity.

## A step, from the inside

Every minute the Pi asks one question: does the published day reach fifteen minutes past now? Most minutes it does, and the Pi goes back to sleep without touching the network.

When it doesn't, the world builds the next situation: the time, the weather and the air, who is present, what is open and until when, what things cost, what is on his mind, and what happens. Something always happens, even if it is only the afternoon going on. The papers arrive at dawn, Ramesh lays out lunch, Khan Market closes, Shri Hegde rings the bell at ten. The Pi wakes the PC and the mind answers in JSON. The world checks the answer against the rules: closed is closed, walking takes the time it takes, the imprest cannot go below zero, and no alcohol is sold on a dry day. If the answer breaks a rule, the world says which one and the mind decides again. The step becomes segments for the map and entries for the panels, written into `docs/days/<date>.json` and pushed. The page polls once a minute and reveals each step when its time comes.

When he speaks to someone, that person answers: one more call, voiced by the model from their card, and the answer opens his next situation. A person he knows may also speak first when they come into sight. When he sits down to write, one more call asks what he wrote; each sitting goes into his manuscripts.

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
| `pc/` | Windows scripts for the PC, and `CODEX.md` |
| `scripts/` | Pi scripts: wake the PC, test wake and sleep, the world's timer |
| `tests/` | `python3 -m unittest discover -s tests` |
| `tools/` | `osm_map.py` rebuilds the map and the walking times from OpenStreetMap; run it only when the map should change |
| `HERMES.md` | The runbook Hermes follows |

`python3 -m world simulate --date 2026-10-03` rehearses a whole day offline with a stand-in mind whose thoughts are marked `(rehearsal)`. Add `--mind http://PC:8081` to rehearse with the real one. Nothing is pushed.

## Plan

1. Repo and page ⟶ Hermes, task 1
2. The mind on the PC ⟶ Codex, `pc/CODEX.md` 1–6; Hermes, task 2
3. Bake-off: Bonsai vs Qwen ⟶ Hermes, task 3; Welt decides
4. Wake and sleep ⟶ Codex 7–8, Welt (BIOS, router); Hermes, task 4
5. World engine on the Pi ⟶ written; Hermes installs and rehearses, task 5
6. Live page reading the day files ⟶ written; day 1 replays until the first live day
7. Shadow week on the `shadow` branch, watched at `?branch=shadow` ⟶ Hermes, task 6; then the public switch, task 7
8. The owl at night ⟶ written, on the day mind's model until the PC can switch to the larger one at night; real streets from OpenStreetMap done
