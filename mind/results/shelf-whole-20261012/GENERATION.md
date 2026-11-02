# Whole-passage shelf trial: generation evidence

Candidate `2f2096eae362da0031f848d4fee680fa4bc68bac`, isolated branch
`codex/shelf-whole-eval`. The code is not merged into the primary checkout
while the fixed-day T3 source freeze is active.

Twenty letters, the same ten seeds in adjacent randomized A/B pairs.
A uses NEW-shelf excerpts; B uses the same selected passages whole.
Both retrieval queries contain only the observed events. Unknowns and the
writing instructions remain in the writer input. Plain Qwen3.8-27B, no
adapter, normal Engine chat writing, bounded reasoning of 384 tokens.

Both wrapper and runner exited 0. Independently verified all 39 protected
files and the separate T3 manifest. All 20 outputs were nonempty, uncut,
valid JSON; one call each, no retries. B's actual prompts included the
required obedience sentence in 10/10 cases. Offered passage ids matched
within every pair. Whole-prompt counts were 2,061 (A) and 2,250 (B), matched
by the server's usage, beneath the frozen 7,263-token ceiling. Word counts
were 158–216; 5 exceeded the requested 200-word upper
bound. No output was selected, regenerated for length, edited or excluded.

Summed job wall time: A 219.352687618s;
B 233.694086639s. Whole run elapsed
454.146220577s. Every job time is in `wall-times.csv` under its blind
text id. The simultaneous fixed-day trial used slot 1 while this trial used
slot 2 on the same GPU; slot 0 stayed free. This concurrent load limits
comparison with earlier sequential trials. The shared server's original
PID 384, command, three slots, healthy status and empty adapter list were
verified after generation; it was not stopped or reconfigured.

Focused checks: 113 tests OK (2 skipped), 3.792s. Archived full suite:
874 tests in 704.466s, OK (19 skipped), wrapper exit 0. All 207 archived
files were independently compared byte-for-byte with the tested native
WSL snapshot after completion.

The packet and v2 guide contain no variant assignments. The new review
key remains outside the repository, packets and bundles. Claude must
commit every score and its SHA256 before key release. B passes only with
commitments at least A + 0.5 and argument no lower. A clean generation exit
is not that blind pass. Whole passages remain off by default.
