Expanded-budget diagnostic round: local grading complete, 1 November 2026

                     S2                 3D checks, seeds 101 / 202 / 303
Qwen3.8-27B           pass               12/12, 12/12, 12/12
Swift 1.5            pass               12/12, 12/12, 12/12
AREX-2               inconclusive       12/12, 12/12, 12/12
Nanbeige4.3-33B      invalid JSON        inconclusive, inconclusive, 2/12

All 20 attempts and their raw request/response chains reconciled. 17 outputs completed, 3 truncated. AREX S2 and two Nanbeige scenes hit the new 28,672-token budget. These remain budget-inconclusive, not correctness failures. The two truncated Nanbeige responses contain reasoning but no final answer. AREX S2 contains a very long final-content field, so its truncation is not solely a reasoning-budget issue.

Nanbeige's completed scene draws a visible orrery, but the probe cannot find any of the five required named objects. Several checks depend on that naming contract: 2/12 does NOT mean ten independent visual defects. Its saved output was not repaired or re-rendered with changed criteria.

The original Edge leaktest did not run its page after Edge's update; no cause beyond that was established. Existing Chrome 156 passed the unchanged owner's loopback/LAN TCP/UDP/WebRTC isolation check (zero listener hits and zero candidates). The reference scene scored 12/12. All ten completed model scenes then rendered once with the same Chrome and owner harness. Two truncated scenes were not rendered. No installs, settings changes or new inference.

Blind screenshots at 1 and 3 seconds: chrome-sheet/sheet.html. Labels shuffled separately per seed; chrome-sheet/key.json is separate. Original round scores remain separate and unchanged. Context, output allowance and time allowance all changed for this diagnostic round, so improvements cannot be attributed solely to the output cap. Control uses UD-Q4_K_M; challengers use Q4_K_M.

Qwen and Swift completed all affected cases and passed the locally gradable checks. Coding correctness remains unverified; no overall replacement winner is established. C1-C3 code has not been executed on this PC. Thirteen completed coding answers (nine original and four expanded) plus three original budget-inconclusive records are packaged for the authorized external Claude handoff; expected answers and credentials are excluded.
