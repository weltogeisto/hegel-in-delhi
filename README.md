# Hegel in Delhi

G. W. F. Hegel, fifty, wakes up in a Lutyens bungalow that the Directorate of Estates allotted to him by mistake. A local model lives his days on a Game Boy Color–style map of two square kilometres of Delhi, live and unscripted. Anyone can watch where he is, what he thinks, buys and wears, and whom he meets.

Live page: https://weltogeisto.github.io/hegel-in-delhi/

## How it runs

- **The world (Raspberry Pi 5, always on).** Clock in Delhi time, places, opening hours, prices, walking routes, the imprest, the cast of fictional Delhiites, the Hegde file. Feeds for weather, air quality, news and holidays. It decides *when* Hegel must decide, checks every decision against the rules, and publishes.
- **The mind (PC with RTX 3090, asleep most of the day).** The Pi wakes it for each decision, 15–25 a day. Ternary Bonsai 27B or Qwen 27B answers in a fixed JSON format, then the PC sleeps again.
- **The owl (same PC, during Delhi's night).** The larger model writes the diary, the revision log and the weekly Depesche.
- **The page (GitHub Pages, free).** The Pi pushes each step 10–15 minutes before it happens; the page reveals it when its time comes.

No database, no subscription. The running cost is electricity.

## The rules

The living are invented, the dead are on his shelf, the news is real. Everyone he meets is fictional; real people reach him only through books and newspapers. His 1820s views on India are his thesis under revision, never the page's voice.

## Layout

| Path | What |
|---|---|
| `docs/` | The public page (day 1 is the hand-written prologue) |
| `mind/` | The day mind's prompt, test situations and the bake-off |
| `pc/` | Windows scripts for the PC, and `CODEX.md` |
| `scripts/` | Pi scripts: wake the PC, test wake and sleep |
| `HERMES.md` | The runbook Hermes follows |

## Plan

1. Repo and page ⟶ Hermes, task 1
2. The mind on the PC ⟶ Codex, `pc/CODEX.md` 1–6; Hermes, task 2
3. Bake-off: Bonsai vs Qwen ⟶ Hermes, task 3; Welt decides
4. Wake and sleep ⟶ Codex 7–8, Welt (BIOS, router); Hermes, task 4
5. World engine on the Pi ⟶ Claude writes, Hermes installs
6. Live page reading the day files ⟶ Claude
7. Shadow week on a private branch, then the public switch
8. The owl at night, and real streets from OpenStreetMap
