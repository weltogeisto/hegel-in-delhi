# Adversarial review of FAST-LANE v1 (21 November 2026)

By an independent Claude reviewer started from the PC session. It was given v1, the measurements of 20–21 November and the system facts, and was asked to attack the proposal against external practice. It checked `world/mind.py`, `world/prefer.py`, `tools/train_data.py`, `tools/fork_diff.py` and `pc/STREET-FORKS*.md`. It touched no server, Pi or file. Numbers are computed from the measured rows unless a source is named. **[memory]** marks a citation the reviewer did not check online. Evaluation material; never training data.

**Verdict:** right direction, wrong design. Offline replication beats spending live days on gates, but as written:
- A night buys many day-runs and few independent observations.
- The gates pass real harm.
- The fast lane shares the live server, the coupling that just cost him 8 hours.

## 1. Statistics and design
- **The 09:14 divergence is the adapter itself, not noise.** The adapter changes the logits from the first token, so seeds cannot keep the pairs together.
  - Pairing bought little even in the street forks. There, S0/S1 empty % correlate at r = 0.20 across pairs, which is about 1.25× effective n.
  - Analyse forks of the mind or the prompt as unpaired.
- **How much seeds vary:**
  - Control-arm SDs: empty 3.3–5.6 pp, answered 7.6 pp, at home 5.1 pp.
  - Arm B inflated these to 20 (answered) and 30 (at home). B's seed 2718 was away from home in 71% of moments; its other two seeds 16% and 23%. That is switching between regimes, so report distributions, not means.
  - With n = 3, the 95% CI on an SD runs from about 0.5× to 6×.
- **Power** (σ = 5 pp, α = .05, 80% power): detecting 10, 5 or 3 pp needs 4, 16 or 44 runs per arm.
  - The adapter's +12 pp on empty shows even at n = 3 (paired t = 3.7, df = 2, p ≈ .07).
  - Effects under about 1.5σ will not show.
- **A week × 3 seeds is the worst shape for day-level metrics.**
  - 21 correlated days give about 5–7 effective observations, assuming a day-to-day ICC of 0.3–0.5. The smallest detectable effect is then 8–11 pp.
  - The same compute spent as 21 one-day runs from at least 3 saved mornings detects about 4.3 pp, and the result does not hang on one morning.
  - Keep multi-day runs for effects that build up over days.
- **The current bars are weak.**
  - "≥4 of 5 pairs" passes a null 19% of the time (sign test).
  - "Mean inside S0's range" passes a true 1-SD harm 57% of the time and a 1.5-SD harm 33% (simulation, 200k draws).
  - Replace both with a declared primary metric, a non-inferiority margin and a one-sided stratified-bootstrap CI.
  - Report the interquartile mean (IQM), the probability of improvement and per-seed profiles (rliable, Agarwal et al. 2021).
  - Henderson et al. 2018 [memory] got "significant" differences between two 5-seed splits of the same algorithm.
- **Test switches together in a factorial design, not one at a time.**
  - All four waiting switches in a 2^4 design × 4 seeds is 64 one-day runs, about 6.5 h. Each main effect compares 32 runs with 32, so about 3.5 pp is detectable, and the interactions come free (Kleijnen & Sanchez 2005).
  - FILE_ACT (date-anchored) and NOTEBOOK (builds up over days) get separate blocks.
- **Sequential looks:** checking each night with O'Brien–Fleming bounds or confidence sequences (Howard et al. 2021 [memory]) stops clear results after night 1, and stops nulls for futility.
- **Seed bug:** `next_seed` hashes (seed, call counter). Any extra call shifts every later seed, for example a refusal retry or `prefer.choose` stopping at its first fresh draw.
  - Key the seeds instead by (base, sim time, call kind, draw index).
  - One dedicated random stream per source of randomness is the standard way to keep runs aligned when comparing with common random numbers (Kleijnen 1979).
- **Decision-level changes:** paired screens on frozen situations, as W8 did, have far more power. Day forks then only need to measure what compounds. Gumbel-max coupling (Ravfogel et al., ICLR 2025) gives true same-noise counterfactual text if it is ever needed.

## 2. Validity
- **One live "confirmation" day is n = 1.** It is a smoke test for breaks of about 10 pp or more. Read it as: does the live day fall inside the fork distribution?
- **The gap between forks and live is assumed, not measured.**
  - Forks share one weather and a frozen phone, and run with the prompt cache off; live uses the server default, cache on.
  - Patodiya (arXiv 2609.04748, 2026) tested llama.cpp with prefix reuse. 82.5% of agentic episodes diverged at 4-bit, against 37.4% at 16-bit. Without reuse at batch size 1, runs reproduced bit for bit.
  - Record the feeds every tick and replay live days offline to measure the gap.
- **No health metric has been checked against quality.** Gating on "% empty" rewards filling moments: 5 of the 17 street cards produced lectures. Correlate each metric with blind-read day quality before it becomes a bar.
- **The distillation heuristic is a proxy.**
  - It rewards overlap with the scene and the shelf, names and length, which is exactly the lecturing and parroting the readers flag.
  - Best-of-4 is mild optimisation: KL = ln 4 − 3/4 ≈ 0.64 nats (Gao et al. 2023 on proxy versus true reward).
  - The live filter already does best-of-4 on freshness. What distillation adds is precisely the part of the heuristic nobody has checked.
  - First compute Kendall τ between heuristic score and reader rank on the draws kept since Day 50.
  - ReST, STaR and rejection-sampling fine-tuning work when the filter verifies correctness (Gulcehre et al. 2023; Zelikman et al. 2022). This filter does not.
- **Model collapse** needs recursion: adapter n writing the data for adapter n+1. To avoid it:
  - Always sample from the base model.
  - Keep earlier data rather than replacing it (Gerstgrasser et al. 2024).
  - Keep the corpus in the mix as an anchor.
  - Track diversity on held-out seeds.
  - Vary mornings and feeds: one weather is a narrow distribution.
- **Preference pairs from the 4 draws** have the right on-policy shape (Tajwar et al. 2024 [memory]).
  - Pairs labelled by the world's checks (refused or echoing against accepted) are close to a correctness check.
  - Length-match the pairs (Park et al. 2024 [memory]).
- **The reading samples are too small.**
  - Training 1's 7/24 against 2/24 defects gives Fisher p = 0.14; the 3 against 1 substantive defects gives p = 0.61.
  - Telling a 4% defect rate from 12% needs about 180 items per arm.
  - LLM judges have position and verbosity bias (Zheng et al. 2023), and the adapter's style is recognisable (cf. Panickssery et al. 2024).
  - Have readers guess the arm (a blinding index), swap positions and use two judge families.
  - Calibrate the readers against Welt on 60–100 items (κ ≥ 0.6) before relying on them at scale.

## 3. Reproducibility and ops
- **On llama.cpp, "side by side" is not "the same conditions":** the other requests in a batch change a request's numerics.
  - vLLM has `VLLM_BATCH_INVARIANT=1`. It is beta, and the current docs list NVIDIA compute capability 8.0 or higher, so a 3090 qualifies.
  - SGLang has `--enable-deterministic-inference`, about 34% slower, measured with the cache off.
  - Either one means a quantisation other than Q4_K_M, which makes it a new mind to be gated like a switch.
- **The incident:**
  - WSL stops idle instances and the VM. WSL issue #13291 says that since 2.5.7, services are suspended unless both `instanceIdleTimeout=-1` and `vmIdleTimeout=-1` are set.
  - Run the live server natively on Windows under a service manager that restarts it on failure.
  - Add a Pi-side dead-man alert: no mind for 5 minutes in waking hours sends a phone push.
  - Add a catch-up mode: the 8 held hours were about 20 decisions, under 10 GPU-minutes, flagged on the page as lived late.

## 4. Options the proposal missed
- **Rent the night on the same stack:** the same llama.cpp build and GGUF on rented 3090s.
  - RunPod community costs about $0.22 per 3090-hour.
  - 8 cards × 10 h ≈ $18 for about 800 day-runs, 8× the home night. The home night costs about €1.5–2 in power [memory].
  - The live server is never touched.
- **A faster serving stack:** vLLM with AWQ gave 2.8–4.4× llama.cpp's aggregate throughput at 64 concurrent requests (7B model, 4090-class cards).
  - For 27B on 24 GB, the KV cache caps concurrency, so expect about 1.5–3×. Benchmark before deciding.
  - It is a new mind.
- **A smaller voice model:** about 20–30% fewer big-model calls. Gate it as a switch.
- **Delayed publication:** live Day D overnight from D's recorded feeds and publish it in real time on D+1.
  - Gains: real feeds, outages of up to a day become invisible, and the PC is free by day.
  - Cost: a 24-hour lag.
  - Don't curate among candidate lives. That makes the record a best-of-N artefact and the selector its author, and it biases every later use of live days as ground truth.
- **A results database** (SQLite or DuckDB): one row per day-run with SHA, model hash, server argv, concurrency, cache flag, seed, morning, switches and metrics. Git branches stay for the artefacts.

## 5. Top 8, ranked
1. **Restate the gates.** A primary metric, a margin and a power calculation per switch; one-day runs from 3 or more mornings; bootstrap CIs. The current bars pass 19% of nulls and 57% of 1-SD harms. 1–2 days, low risk (Agarwal 2021).
2. **Factorial screen of the waiting switches.** About 3.5 pp detectable in 64 runs, against about 10 pp in 168. Half a day; the risk is aliasing between effects (Kleijnen & Sanchez 2005).
3. **Live server as a Windows service, Pi dead-man alert, catch-up mode.** One incident cost 8 hours of his life. About a day, low risk (WSL docs and issue #13291; Google SRE book [memory]).
4. **Seed streams keyed by time, kind and draw; noise band measured at the concurrency actually used.** 2–4 hours; old forks stop being reproducible (Kleijnen 1979; Patodiya 2026).
5. **Rent the night on the same llama.cpp and GGUF.** 8× the day-runs, with live isolated. 1 day; costs can creep, and both arms must run on one host (RunPod pricing).
6. **Validate the instruments before any distillation.** Reader κ against Welt, a blinding index, the metrics against reading, Kendall τ for the heuristic. About 2 days; may retire metrics now in use (Zheng 2023; Gao 2023).
7. **Record live feeds and replay live days.** To measure the gap between forks and live, and to vary the starting mornings. 1–2 days; the risk is storage (Patodiya 2026; Sargent on simulation validation [memory]).
8. **A results database with provenance.** 1 day, low risk (Sculley et al. 2015 [memory]).

**Deliberately below the line:** moving to vLLM or SGLang, and distillation SFT. Both change the mind, and both depend on item 6.

**Sources:** [Agarwal 2021](https://arxiv.org/abs/2108.13264) · [Kleijnen & Sanchez 2005](https://faculty.nps.edu/smsanche/docs/ijoc05.pdf) · [Kleijnen 1979, CRN](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.25.7.649) · [Ravfogel 2025](https://arxiv.org/abs/2411.07180) · [Patodiya 2026](https://arxiv.org/abs/2609.04748) · [Gao 2023](https://arxiv.org/abs/2210.10760) · [ReST](https://arxiv.org/abs/2308.08998) · [Gerstgrasser 2024](https://arxiv.org/abs/2404.01413) · [Zheng 2023](https://arxiv.org/abs/2306.05685) · [Panickssery 2024](https://arxiv.org/abs/2404.13076) · [vLLM batch invariance](https://docs.vllm.ai/en/latest/features/batch_invariance/) · [SGLang determinism](https://www.lmsys.org/blog/2025-09-22-sglang-deterministic) · [WSL config](https://learn.microsoft.com/windows/wsl/wsl-config) · [WSL #13291](https://github.com/microsoft/WSL/issues/13291) · [RunPod pricing](https://www.runpod.io/pricing) · [vLLM vs llama.cpp](https://computingforgeeks.com/ollama-vs-vllm-vs-llama-cpp/)
