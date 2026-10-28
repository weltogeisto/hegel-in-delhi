# The Qwen replacement trial: day one, Wednesday 28 October

Hermes prepared a trial: vanilla Qwen3.8-27B as the control against three challengers, Nanbeige4.3-33B, BAAI AREX-2 and Swift 1.5, all Q4_K_M. Claude checked the plan for Welt. The plan validates (`plan_valid`), and all three pinned files match Hugging Face's live records byte for byte and hash for hash. This brief is how it runs on the PC. Where it differs from Hermes's handoff, this brief holds.

## Welt's decisions, 28 October, in Claude's chat

1. **Hegel pauses completely until Welt is back on Sunday 1 November** (T37 in `pc/TASKS.md`). The card belongs to the trial.
2. **The PC turns off today at the Power Guard's normal time.** Today is the whole window. Do not cancel the guard's shutdown.
3. **Approved for this trial:**
   - the three pinned downloads (55.43 GB), bytes and SHA-256 checked;
   - the tests, one model at a time, standalone on loopback;
   - a safe space for model-written code, built from tools already on the PC, with no network and nothing installed;
   - the 3D test below, which Welt asked for, for all four, with the one pinned three.js file it needs.

**Not approved:** changes to the Weltur queue, the controller, the worker or Hermes; any switch of the default model; installs, a newer llama.cpp included; anything paid; power and firewall; deleting anything.

## The bundle

Hermes's bundle is on the Pi under `/home/faqts/.hermes/workstreams/open-source-savant/` (`replacement-trial-v1/`, `benchmark-v1/`, `replacement-trio-sources-2026-10-28.json`); Welt also has it as `CODEX-QWEN-TRIAL.zip`. Copy it, read-only, and check your copy against the files Claude reviewed:

| File | SHA-256 |
|---|---|
| `replacement-trial-v1/PLAN.md` | `76520859b47677053c786d18e644ecdab6244a0a295da1382f2aa2b67741d58a` |
| `replacement-trial-v1/manifest.json` | `eca0f5bafc93a045f64496aeb023fe4e1613a6852c94df394b7680cea0407511` |
| `replacement-trial-v1/validate_plan.py` | `77338ccdf3a452f04a888f9ae84b0b2b18a2654c658ce85fe4043adacd06cb25` |
| `benchmark-v1/cases.json` | `4de8e56ced599401e7e12199e137995b103d7df8fd94f24d59ae69c49c5965eb` |
| `benchmark-v1/answer-key.json` | `85ad3e7be47c9e798c73da85a1b6313d4d933045f1bd9766b85e3fd0e7b24576` |
| `replacement-trio-sources-2026-10-28.json` | `e7f21cebbdd3baa2b255325e1598311d80648e72ddcee1cd6097c2f0ef6649c0` |

The answer key stays out of every model's sight.

## Where this brief changes the handoff

- **Standalone, not through the queue.** One llama-server at a time on 127.0.0.1, not on port 8082, started and stopped by the runner. Before each load, `nvidia-smi` must show the card nearly empty; if anything else holds it, stop and report. Results are labelled standalone. Wiring the winner into the queue comes later, with Welt.
- **Runtime:** an llama.cpp already on the PC (Hegel's b11429 in WSL, or the Weltur build). If no build on the PC loads a model, that model is blocked: report it, test the others, fetch nothing.
- **Control:** the vanilla Qwen file that Hermes's `qwen-local` serves. Record its path and SHA-256; if Hegel's server uses a different file, record both.
- **Resume:** one line per finished attempt, written as it finishes. On restart, finished attempts are skipped; an attempt cut off by the shutdown is rerun, not scored.

## Today, in order

1. **T37 first:** pause Hegel.
2. **Read-only preflight** (PLAN Task 1), plus today's boot time, which gives the guard's shutdown. Start no new model work in the last 20 minutes before it.
3. **Start the three downloads.** Verify each (bytes, then `Get-FileHash`) before use. The target is 100 GB free; if there is less, delete nothing: download what fits and report.
4. **While they download,** build the runner and start with vanilla Qwen: its weights are already there.
5. **Per model, in one load:**
   - the 12 screening cases with the manifest's settings (16,384 context; 4,096 tokens including reasoning; 180 s; at most 3 tools; temperature 0.6, top-p 0.95; every other sampler field logged);
   - then the 3D test, three seeds;
   - then the next model, as its file verifies.
6. **Code from C1 to C3** is graded only inside the safe space. That is WSL with `unshare`: no network, the Windows drives and the home folder hidden, time and memory caps, a fresh temporary folder. If it can't be built from what is there, the code stays ungraded until Sunday. C3's JavaScript may instead run in headless Edge, the way the 3D harness does.
7. **Not today:** the four real-work tasks. If CPU time is left, draft them with the fixes below; run nothing.

## The 3D test: Welt's ask, for all four

- **The case:** frozen in `pc/qwen-trial/scene3d.json`. One prompt, an orrery in three.js; seeds 101, 202 and 303; 12,288 tokens including reasoning; 600 s; no tools.
- **Grading:** twelve machine checks, listed in the same file. No model judges.
- **For Welt:** screenshots at 1 s and 3 s go on one contact sheet per seed, the four configurations under shuffled labels A to D. The key is in a separate file, so Welt can look blind on Sunday.
- **The harness:** `pc/qwen-trial/render3d.py`, with `probe3d.js`, from Claude, tested (`tests/test_render3d.py`). It renders each answer in headless Edge (or any Chromium), with a fresh profile and in real time, from a loopback-only folder that holds just the page and three.js. Every other request is blocked. About 15 seconds per answer, after the model is unloaded or while the next one loads.
- **First, the harness's own check:** `render3d.py run --answer pc/qwen-trial/selftest.html ...` with the PC's browser must score 12 of 12. If it doesn't, the harness isn't working there: report, and keep the answers ungraded. From WSL, Edge (`msedge.exe`) reaches the loopback server only in mirrored networking mode; Windows Python with Edge works too.
- **Per attempt:** `render3d.py run --answer ANSWER --three pc/qwen-trial/three.module.js --browser EDGE --out DIR`, plus a `meta.json` (`config`, `seed`) in DIR. At the end of the day, `render3d.py sheet --out SHEET DIR...` makes the blind sheets and the key.
- **three.js:** `pc/qwen-trial/three.module.js` is `three@0.170.0`'s `build/three.module.js` (1,314,681 bytes, SHA-256 `ce1fa418…ddedfb`). Nothing to fetch; `render3d.py` refuses any other file.

## Fixes for the real-work stage, later

- **Context:** 16,384 minus 12,288 output tokens leaves about 4,000 for the task and up to 24 tool results, and the 8K fallback can't hold the output at all. Real work needs about 32K. A model that can't fit it leaves the real-work lane; the others don't shrink to match.
- **Tasks:** real bugs fixed in this repository (for instance `dbf017b`, `e69d2e8`), each with the test that came with its fix: reproducible, and newer than every model. If no real React or TypeScript repository is at hand, use a second Python task rather than stopping.
- **How many:** with four tasks, "two tasks Qwen misses" is reachable only if Qwen fails two of them. Aim for six to eight.
- **Research tasks:** required claims and source IDs, checked by a script. No Codex judgement in the score.
- **Quantization:** the control is Unsloth's UD-Q4_K_M, the challengers standard Q4_K_M. The report says so, above all for Swift against Qwen.

## Report

- **Results:** they stay under `C:\AI\experiments\qwen-replacement-v1`.
- **Push to `codex/qwen-trial`:** STATE.md, the preflight (no secrets), the effective configurations, `results.jsonl`, the comparison table, and the 3D contact sheets with their key in a separate file. No weights, no answer key.
- **When the day ends:** one comment on PR #1: done, blocked, or a question.
