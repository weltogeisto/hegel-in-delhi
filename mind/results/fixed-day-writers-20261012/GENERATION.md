# Fixed-day writer generation: 12 October 2026

Generation completed; blind factual and argument review remains pending. No default or live-world approval follows from this report.

- Frozen runtime: `31e2b531095d870f2bb8f017fa1065021bc9faa5`. Both wrapper and runner exits were 0. All 61 protected source/input files were independently verified before packaging.
- 138 scheduled jobs completed, producing 210 texts and 4430 numbered sentences. No output was excluded, empty or unusable. No response stopped for length.
- 149 model calls: 11 jobs made one extra call each. All responses parsed as JSON; Engine contract retries were retained. Actual tokenizer usage equalled preflight for every call, ranging from 2,406 to 7,262 tokens (ceiling 7,263).
- Total elapsed time: 4933.865226s. Summed job times: A 2391.314778s, B 2446.352026s, B/A 1.023015. The timing gate (B <= 1.2*A) passes. A and B were adjacent randomized pairs with prompt caching disabled.
- Existing adapter-free Qwen3.8-27B server remained healthy on 8082, PID 384, three slots. This trial used slot 1. The T4 and T4b shelf jobs shared slot 2 for part of the run; concurrent GPU load limits timing interpretation. The server was never stopped or reconfigured. Original saved days were untouched.

The packet contains all six frozen saved histories, three seeds per history, and every owl diary, revision log, Depesche and scheduled writing sitting. These are development histories, not six independent fresh worlds. Missing evidence should be marked uncertain rather than counted as contradiction.

Use `texts.json` for exact sentence numbers and the supplied typed records. `packet.md` has the same texts in the same shuffled order. Follow `guide.md`: commit the sentence-error, per-text-total and owl-argument CSVs with their SHA256 hashes before requesting the private key. Source/variant assignments remain outside Git and this packet. The per-job cost CSV uses separate opaque identifiers, with no mapping to the review texts.

The predeclared pass rule requires B to have fewer statement promotions, no more contradictions per 100 sentences, no worse owl argument, and wall time <=1.2*A. Only timing is decided so far. No length resampling, selected-output replacement, training or closed-loop feedback occurred.
