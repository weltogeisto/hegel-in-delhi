# The fast lane, v2: a month of answers per night

Proposed on 21 November 2026 by Claude on the PC, on Welt's ask in the PC session ("1 week progress in one night or more"; "we are a simulation laboratory"; rules may change with good reason). v1 of this file was reviewed adversarially the same evening against external practice. Its verdict was "right direction, wrong design", and this version takes its findings in. A proposal: the cloud session turns it into an order, and Welt decides the points marked **Welt**.

**Status, DECISIONS 61 (Welt, 21 November, about 17:40):** the PC stays on at night for the fast lane, on the home GPU only. No rented GPUs (so the rented rows in D and the rented nights in the plan below are out) and no delayed publication (H). Not yet decided: every slot at night (the spare slot until then), statistical gates in place of live-day gates, the dead-man alert and catch-up mode. The live server is started only by its Windows starter, and port 8082 is checked after every night job. The text below stays as proposed and reviewed.

**Built since, off until used (21 November, night):** C's seed streams, `HEGEL_SEED_STREAMS=1` (`world/mind.py`, `tests/test_seed_streams.py`). A call's seed comes from the base seed, the moment, the kind of call (decision, voice, writing, complete, chat) and its draw number. One extra call then moves no other seed. Before a night relies on it: two same-seed runs with it on, `fork_diff` identical, at the concurrency used. **Night 1's noise band (21 November, 3 slots at once, cache off):** two same-seed runs parted at the first decision (09:14). With several runs sharing the server, the batch changes the numbers, so a seed does not fix a reply. Pairs, and with them seed streams, hold only for runs made one at a time. At every slot, forks are read as unpaired samples, as v2 assumes.

## The idea in one paragraph

His live life stays in real time. It is the record, and the final check. Everything we want to *learn* moves to an offline lane that runs on the GPU at night, and on rented GPUs when one card is not enough. That lane is designed as experiments, not as more days. A rehearsed real-mind day costs 6 to 11 GPU-minutes (measured on 20–21 November: six whole days with every live switch in 36 minutes). So one home night holds about 60 to 130 day-runs, and a rented night about 800. Used well, that answers four switches in one night instead of four live weeks.

## What v1 got wrong (the review, checked)

1. **Pairs do not hold.** In W8's fork every A/B pair parted at the first decision, and across the street forks the paired arms correlate at r ≈ 0.2. Seeds cannot keep a changed mind on the same path, so forks of the mind or the prompt are read as *unpaired* samples.
2. **Our bars pass harm.** "Lower in at least four of the five pairs" passes a true null 19% of the time (sign test, 6/32). "S1's mean inside the range of S0's five" passes a true 1-SD harm about 57% of the time.
3. **A week × 3 seeds is the worst shape.** Twenty-one correlated days give only 5 to 7 effective observations, so an effect needs to be about 8 to 11 points to show. The same compute as 21 one-day runs from three or more saved mornings detects about 4 points.
4. **Power:** at a between-seed SD of about 5 points, detecting 10, 5 or 3 points needs about 4, 16 or 44 runs per arm. One arm in W8 switched regimes between seeds (away from home 71% of the day in one seed, 16% and 23% in the others), so distributions are reported, not just means.
5. **The seed scheme shifts.** `HTTPMind.next_seed` hashes (base seed, running call count), so one extra call (a retry, an early stop among the draws) moves every later seed.
6. **The instruments are unvalidated.** No health metric has been checked against day quality ("% empty" rewards filling moments; the street had cards that only drew lectures). The distillation heuristic rewards overlap and length, which is the lecturing and parroting the readers flag. Reader samples are small (Training 1's 7/24 against 2/24 defects: Fisher p ≈ 0.14).
7. **The fast lane shared the live server,** the coupling that cost him 09:13–16:55 on 21 November.

## v2: the design

### A. Gates are statistical decisions (the cloud declares them per switch, before output)
- One **primary metric**, a **non-inferiority margin** and a **power calculation** per switch; secondaries reported, not gated.
- **One-day runs from at least 3 saved mornings**, seeds spread across them; multi-day runs only for effects that build up over days (`HEGEL_NOTEBOOK`, staleness, money).
- Report **interquartile means, stratified-bootstrap CIs, the probability of improvement and per-seed profiles** (rliable, Agarwal et al. 2021).
- **Look sequentially.** After each night, stop a clear result or a futile one (O'Brien–Fleming or confidence sequences).
- The live day is then a **smoke test**: does it fall inside the fork distribution? With n = 1 it is not evidence of an effect.

### B. Experiments as factorials, not one switch at a time
- Switches that can share a day go into a **2^k factorial** (Kleijnen & Sanchez 2005). Every run informs every main effect, and the interactions come free.
- `HEGEL_CULTURE` × `HEGEL_VOICE_REPAIRS` (2²) × 3 mornings × 4 seeds = 48 one-day runs, about 5 h at home. Each main effect compares 24 runs against 24.
- `HEGEL_FILE_ACT` (bound to dates) and `HEGEL_NOTEBOOK` (builds up over days) get blocks of their own.
- **Decision-level changes** (an adapter, a prompt) are screened first on frozen situations, paired, as W8 did. That has far more power. Day forks then measure only what compounds.

### C. Instruments before scale (the first week's real work)
- **Readers calibrated against Welt:** 60 to 100 items, κ ≥ 0.6 before LLM readers stand in for him at scale; positions swapped; a blinding index (readers guess the arm); two judge families.
- **Metrics validated against reading:** each health metric correlated with blind-read day quality before it becomes a bar.
- **The distillation heuristic checked:** Kendall τ between heuristic score and reader rank on the draws kept since Day 50 (`HEGEL_KEEP_DRAWS`). No distillation SFT before this.
- **Seed streams keyed by (base, sim time, call kind, draw index),** one stream per source of randomness (Kleijnen 1979), so runs stay aligned. The noise band is measured at the concurrency actually used.

### D. Capacity
| Where | Day-runs a night | Cost |
|---|---|---|
| Home 3090, spare slot | ~60–80 | power, ~4–5 kWh |
| Home 3090, every slot while he sleeps | ~100–130 | the same |
| Rented 3090s, same llama.cpp build and GGUF (e.g. 8 × 10 h) | ~800 | ~$18 a night (community 3090s ≈ $0.22/h) |

- Renting keeps the **live server untouched** and the mind identical: the same binary, the same weights.
- Both arms of an experiment run on the same host.
- A faster serving stack (vLLM/SGLang: continuous batching, batch-invariant modes, perhaps 1.5–3× for 27B on 24 GB) is **a new mind**, gated like a switch, and benchmarked before any decision.

### E. The live world made robust
- **Live server as a Windows-native service with restart on failure**, or WSL with `instanceIdleTimeout=-1` and `vmIdleTimeout=-1`. Never restarted from inside a WSL shell (the cause of 21 November).
- **Pi dead-man alert:** no mind for 5 minutes in waking hours sends a push to Welt's phone.
- **Catch-up mode:** after an outage, the held hours are lived at speed when the mind returns and marked on the page as *lived late*. Day 52's eight held hours were about 20 decisions, under 10 GPU-minutes. This is the faster live clock in its one sound form: rare, bounded, and visible.
- **Record the live feeds every tick.** Then live days can be replayed offline to measure the gap between forks and life (one weather in every fork, a frozen phone, prompt cache off in forks and on live), and forks can start from varied mornings with real feeds.

### F. Training, guarded
- Sample training material from the **base model**, never from adapter n to train adapter n+1.
- **Accumulate** data across rounds instead of replacing it (Gerstgrasser et al. 2024), and keep Hegel's own texts in the mix as the anchor.
- Track diversity on held-out seeds.
- **Preference pairs from the 4 draws:** world-checked (refused or echoing against accepted), length-matched. On-policy and close to a correctness label.
- The data rule stands: no target, and no label used for training, written by Claude. Evaluation seeds and mornings are never training material.

### G. One results database
- One row per day-run (SQLite or DuckDB on the PC, pushed nightly): commit, model hash, server argv, concurrency, cache flag, seed, morning, switches, every health metric, the reader marks when they come.
- Git branches keep the artefacts. Questions across hundreds of runs are then queries, not archaeology.

### H. An option, not proposed: delayed publication
- Live Day D overnight from D's recorded feeds and publish it in real time on D+1.
- Gains: outages of up to a day become invisible, and the PC is free by day.
- Cost: a 24-hour lag behind Delhi.
- **Never curate** among candidate lives: the record would become a best-of-N artefact with the selector as its author.

## The first two weeks

| When | What |
|---|---|
| Night 1 (home) | The noise band at the concurrency used (one morning, seed 1831, twice); then culture × voice repairs, 48 one-day runs from 3 mornings |
| Days 1–3 (cloud and PC) | Restated gates; seed streams; results DB; feed recording; live server as a service; dead-man alert; catch-up mode (through main, tested) |
| Week 1 | Reader calibration with Welt (60–100 items); metric validation; heuristic τ |
| Week 2 | Rented nights if the home night is the limit; `HEGEL_NOTEBOOK` as 3-day runs × 3 mornings; `HEGEL_FILE_ACT` block |

## Welt

1. **The PC on at night, or a rented night budget** (~$20 a night when used).
2. **Every slot while he sleeps** on the home card, in place of the spare slot only.
3. **Gates as statistical decisions** (A), with the live day as a smoke test.
4. **Catch-up mode and the dead-man alert** built and switched on.
5. Whether to consider **delayed publication** (H) at all.

Sources the review rests on: Agarwal et al. 2021 (rliable); Kleijnen & Sanchez 2005 (factorial designs for simulation); Kleijnen 1979 (common random numbers); Gao et al. 2023 (proxy reward over-optimisation); Gulcehre et al. 2023 (ReST); Zelikman et al. 2022 (STaR); Gerstgrasser et al. 2024 (accumulating synthetic data); Zheng et al. 2023 and Panickssery et al. 2024 (LLM-judge biases); the vLLM and SGLang docs on batch-invariant inference; WSL config docs and WSL issue #13291; RunPod pricing. The review in full, with links and with the citations it made from memory marked: `pc/FAST-LANE-REVIEW.md`.
