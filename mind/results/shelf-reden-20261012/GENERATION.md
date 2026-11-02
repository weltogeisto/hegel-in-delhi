# Shelf trial: generation complete, blind scores pending

Candidate: 88cfd287cfe19ffdbd2d7c8e1e92f4a9af4c2657. OLD shelf: c03a431;
NEW shelf: main 8dd33b6. Same saved Karl situation, normal Engine writing
path, plain Qwen3.8-27B UD-Q4_K_M, no adapter, ten paired seeds.

20/20 jobs finished, exit 0. All 20 letters are nonempty, with no length cut
and one generation call each. All 10 NEW prompts held a `reden` passage.
The frozen input/source check and original-day preservation passed before
source work resumed; the shared 8082 server stayed running. Exact offered
passages, prompts, raw JSON and responses are preserved with each raw job.
They are withheld from the blind packet until scores are committed.

Summed job wall time: OLD 222.241928 seconds; NEW 235.403801 seconds.
Total elapsed: 472.078106 seconds. `wall-times.csv` reports every job's
wall time; it carries no random text id or assignment. T3 briefly shared
the GPU, then was interrupted on Claude's protocol review; this is a cost
limitation. No caching was used. Literary scores are still pending.

The packet has 20 randomly identified texts with the same case; no shelf
condition or key. Score with guide.md and commit the CSV and its SHA256
before requesting the key. The private key is outside the repository.
The pass rule remains: NEW commitments at least 0.5 above OLD, argument
not lower. A completed generation run alone is no literary pass.

Packaging initially failed with `TypeError: object of type 'generator' has
no len()`. The frozen source was verified again, then its sentence iterator
was materialised only in the packaging helper. Raw generations, text and
order were not changed. The permanent fix now has a GPU-free regression.
