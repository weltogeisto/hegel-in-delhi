# Codex status — 12 October 2026

Branch: `codex/outcome-memory`. Main and `claude/compact-view` are merged.
Coordination: `COLLABORATION.md`, `pc/TASKS.md`, draft PR #1.

- T1 done: check-in comment 6119766888. The status file is owned by ai again.
- T2 blocked on Pi authorization and Windows LAN/startup setup. Plain
  Qwen3.8-27B UD-Q4_K_M is healthy in WSL tmux `hegel-server`, llama.cpp
  b11429, 8082, three 16,384-context slots, no adapter. Windows loopback works;
  192.168.188.21:8082 times out. WSL is mirrored. Firewall inspection returns
  “Zugriff verweigert”. Claude has handed the administrator firewall and
  Hermes shadow-world steps to Welt. No firewall/power/secret changes made.
- T3 running: compact evidence integrated; runtime never constructs the
  failed LLM claim checker. Explicitly injected guards remain for audits.
  Compact owl inputs retain the labelled 1,950-character interpretation block. Whole prompts
  and retries are checked with the serving tokenizer before generation;
  critical records are never silently cut. Cheques remain uncashed and
  selected earlier records keep their date.
- T4 generation complete: 20/20 letters, all nonempty and uncut; 10/10 NEW
  prompts held `reden`. Normal Engine writing path, no adapter. Blind packet
  is `mind/results/shelf-reden-20261012`. Claude committed all scores and their
  hash at e3d012f; CSV, packet and every text hash were verified before key
  release. OLD/NEW commitments 2.00/2.00, argument 2.10/2.20: FAIL against the
  required +0.5 commitments gain. NEW offered German `reden:58` on instruction
  versus upbringing; the other slot stayed on Xenophanes' unknown birth/death.
  Exact offered passages and joined results are now published. The negative result is accepted by Claude. T4b tests the full passage
  in isolated branch `codex/shelf-whole-eval`; primary source stays frozen for T3.
  NEW/OLD summed job wall time 235.404/222.242s.

Focused checks: 60 tests in 0.271 seconds, OK. Archived candidate 88cfd28
full suite: 866 tests in 718.409s, OK (19 skipped). Revised full suite: 869 tests in 704.820s, OK (19 skipped); 201 archived
files verified unchanged. See `WRITER-VALIDATION-20261012.md`.
Tokenizer probe: preflight 19 tokens, actual usage 19. Running 138 T3 jobs
(6 saved days × 3 seeds × 2 inputs, including 17 writing moments) and 20 T4
letters (T4 completed). Active sessions: `hegel-writer-T3-v3` and
the suite has finished; 46 preflight prompts fit at 2,406–7,262 tokens.
T4b is running in `hegel-shelf-whole`, with its own full suite in
`hegel-shelf-suite`. Candidate 2f2096e on the isolated code branch, 113
focused tests OK (2 skipped), whole/excerpt prompts 2,250/2,061 tokens.
Whole B holds the obedience sentence; main behaviour remains unchanged.
T3's superseded partial run is preserved: interrupted
on Claude's review, exit 1, frozen inputs intact. Its replacement restores
thoughts, uses adjacent randomized A/B pairs and includes owl argument
scoring. Packet export's sentence-iterator TypeError is fixed and tested.
No closed-loop run or default enablement before blind pass rules.
See `WRITER-TRIAL-20261012.md` and `WSL-MIND-STARTUP-PROPOSAL.md`.

Yesterday's unfinished compact helper remains preserved in Git stash
`codex-compact-checkpoint-20261012-before-main`; it has not been discarded.
The failed calibration/smoke evidence remains unchanged. Reports:
`OUTCOME-MEMORY-REPAIR-VALIDATION.md` and `OUTCOME-MEMORY-REPAIR-SMOKE.md`.

Public world remains paused. Shadow preparation alone is authorized. Train
nothing; adapters, original data, ML packages, firewall, power and secrets
remain unchanged. The shared mind server stays running for the world.
