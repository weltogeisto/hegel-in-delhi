# Handover to Codex (Astra), 2 November 2026

Claude hands the running work to you at Welt's request. This file is enough to go on; the details are in the files it names.

## Welt's decisions, 2 November

1. **Training 1 goes:** the Hegelizer's round two with the report's six additions (T46, `pc/TRAINING-3.md`).
2. **Hegel stays paused.** The Pi's timer stays disabled and the 8082 server off until Welt says otherwise. The card is yours all day.
3. **One night for phase B:** about 9 hours with the Power Guard set later. Tell Welt a day ahead which night; he sets the guard.
4. **Trainings 2 and 3 (T47, T48): decided after the screens.** The screens (T39, then T40 with G8) run only on Welt's word. Ask him once phase A is under way.

## What to do, in order

1. **Phase A (T34) now, with the card to itself.** Serve plain Qwen with four slots (`pc/HEGELIZER.md`, step 2) and run the round-two generator with four workers. No latency guard is needed while Hegel is paused. Expect roughly a third of the 25 spare-slot hours. Gate as filed: under 10% failed units, mean ratio 0.8–1.2.
2. **The report's additions, as code on a `codex/` branch** (`pc/TRAINING-3.md`, Training 1):
   - **Splits by chapter:** training and held-out units from different chapters; a short unit stays with its parent passage. Check what `tools/hegelizer_round2.py` does now and close the gap.
   - **The voice dashboard, beside the five KPIs:** propositions added and omitted (from the plain-Qwen meaning check); names, numbers and negations kept (deterministic); 12-word overlap before and after the copy guard; how often the guard fell back to the plain text; Delta matched for length.
   - **T45's fresh confirmation set:** 40 thoughts of at least 40 words, drawn evenly across the shadow days with a mind, minus names met after Day 1. Use a fixed rule written down before you look at any output. Seal its hash before phase B; never use it for tuning.
3. **Phase B and C on Welt's night** (T35): train with `--goldfish` as planned, then the new test. KPI 1 keeps its legacy 39+1 cohort. If KPI 4 (nothing copied) fails, the next window trains the same data without `--goldfish`, so that we know what goldfish does.
4. **The sheets:** Welt's 20 pairs go to him. Claude's 20 wait for a Claude session; send nothing else to any model.

## Rules that still hold

- **The data rule:** training data comes only from his own texts, the local model's own outputs chosen by fixed rules, or Welt's judgement. Never text written or chosen by Claude, GPT or you.
- **Not without Welt:** no resuming Hegel, no public switch, no new ML packages, no power, firewall or network changes, no spending, no deleting data or history.
- **Code to `main` through a pull request** from a `codex/` branch with its tests. Welt merges; a Claude session reviews when one is available.
- **PR #1 comments:** only for done, blocked or a question, one short message each.

## Open, for Welt

- **The PC can't resolve GitHub's address** on Windows or WSL. Uploads go through the Codex connector until he fixes it.
- **The Qwen trial (T38):** stop here and stay on Qwen, or build real-work tasks so Swift can prove itself. Results and grades are on `main` (`trial-results/` on `codex/qwen-trial`, `pc/qwen-trial/grades/`).
- **The research experiments T39–T45 and G1–G9:** filed in `pc/TASKS.md`, each waiting for his word.
