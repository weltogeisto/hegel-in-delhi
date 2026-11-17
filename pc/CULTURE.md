# Museums, concerts and plays

**Why.** On his journeys the real Hegel spent his days in galleries, churches, the opera and the theatre, and 40% of what he wrote home was about them. His simulated Delhi offered none of it, and his evening texts give it 1% (`pc/PARIS-BACKTEST.md`, stage 1). Welt's go, 15 November (`DECISIONS.md` 27).

## What the world gains, with `HEGEL_CULTURE=1`

| Place | Walk from home | Open | What is there |
|---|---:|---|---|
| The National Museum, Janpath | 31 min | Tue–Sun 10:00–18:00; ticket ₹650 foreign, ₹20 Indian | eleven galleries to see, one a step: the Mohenjo-daro bronze girl, the Harappan seals, the Piprahwa relics, a Gandhara Buddha, a Chola Nataraja, Babur's memoirs, a Pahari storm, the Silk Road paintings, instruments, coins, the courtyard |
| The National Gallery of Modern Art, Jaipur House | 44 min | Tue–Sun 11:00–18:30; ticket ₹500 foreign, ₹20 Indian | seven rooms: the Daniells' aquatints, Ravi Varma, Amrita Sher-Gil, Tagore's paintings, Nandalal Bose, Jamini Roy, the new wing |
| The India Habitat Centre, Lodhi Road | 24 min, 12 from Lodhi Gardens | daily 09:00–21:30, free | the building and its galleries; Monday a vocal recital, Wednesday a sitar recital, Friday a talk on Kalidasa's Shakuntala and its European readers, Saturday a Kathak evening |
| Kamani Auditorium, Mandi House | 65 min | Tue–Sun 16:30–21:00; ticket ₹300 | Tuesday and Thursday Mohan Rakesh's play *Ashadh Ka Ek Din*, Wednesday Bharatanatyam, Friday dhrupad; Saturday and Sunday at 17:00 Rossini overtures and Beethoven's Seventh |

**How it reaches him:**
- **In the morning:** after the headlines, a line of listings tells him what is on that day and when the museums open.
- **Arriving before a show:** at a venue he is told what is on tonight, and the ticket price if there is one.
- **During a performance:** each step shows the next of its four parts, then that it goes on.
- **In a museum:** when nothing else happens, each step shows the next gallery, in an order fixed for the day, until he has seen them all.

**What stays as it was.** Without the switch the world is byte for byte the same: the same eight places, the same schema, the same prompts (`tests/test_culture.py`). With it, the decision's place list widens by four. The tickets use the existing entry rule, as Safdarjung's Tomb does. Every performance ends by 20:30, before the world sends him to bed at 21:00.

**Written with care.** The galleries hold what those museums hold. No living performer, artist or curator is named; the artists named died long ago. Hours and prices are the usual ones and approximate. The walking times are estimates, a straight line × 1.3 at 75 m a minute, within 5% of the measured table on average.

## Still to do

- **The map on the page.** `tools/osm_map.py` should place the four buildings and measure the walks. Until then the page draws him at home while he is at a venue.
- **When it goes on.** Fifth and last in the order of `DECISIONS.md` 34: the filter, the letter from Munich (whose money pays for the tickets), the new instructions, the shelf labels, then this. Astra sets `HEGEL_CULTURE=1` on the Pi after the shelf labels' first full day.
- **How to read it.** Stage 1's profile, run again on the days after it is on, is the measure. It says whether sights and art return to what he writes, and whether philosophy and hunger give way.

Evaluation note: the venues' texts are world content, written for the simulation; they are not training data.
