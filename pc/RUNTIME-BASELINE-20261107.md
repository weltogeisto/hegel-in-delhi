# Runtime baseline and recovered Training 1 evidence
Captured once on 7 November 2026 at 12:18 UTC, under the implementation manual §13 and Claude's PR #1 comment 6706259741.

| Component | Observed revision/configuration |
| --- | --- |
| Current main at capture | 6b8e02bf307a3f091ff842504fac30b40a2a04d3 |
| PC primary working checkout | 2b242af2891da7b3d39de7ac24631077e58e32f0, clean |
| Frozen T39 source | 97cfde716335963cd900916523db6e985e7d9a9d |
| Pi working checkout | 989531a58490c9394dbb6372a51c992ab41790d0; 219 tracked files match that commit; docs/days/2026-10-29.json differs and was preserved |
| PC serving model | Plain Qwen3.8-27B Q4_K_M; original 8082 command, CUDA mapped, three 16,384-token slots, no startup adapter |
| Pi schedule | User timer active/enabled, every minute; shift 1170 minutes, lead 15 minutes, owl 09:10 |
| Pi model settings | Mind and owl route to the PC's 8082 endpoint; chat writing; adapter scales unset; reasoning budgets zero |

[BASELINE-RECEIPT](evidence/runtime-20261107/BASELINE-RECEIPT.json) links the complete captured PC and Pi revision/configuration files. BINARY-PROVENANCE records the identity-matched running executable hash. The original model hash is 322e194ff79741c7baa497c240f677f54b201b0efab44ca8e50f122b39123482; the receipt links today's full-file verification in the serving mount namespace.

This is a point-in-time record. The slot samplers describe current/last requests, including T39's private arm overrides; they are not Hegel's global defaults. Pi effective Config was reconstructed from the whitelisted configured file and loaded unit environment. Disk source hashes do not prove which bytes a previously completed Python process executed. The deployed Pi Config predates the echo/DRY options present on main; no deployment was performed.

The [forty-case export](exports/training1-20261106/README.md) contains 40 frozen inputs (39 from Day 12, one from Day 24), 80 outputs, 80 selected voice receipts and 280 exact request chains. The ZIP includes both original RESULT/RUN files, raw-control-plain, raw-adapter-training1, the 160 relevant raw-meaning chains, dashboard, inputs and checkpoint/conversion provenance. A browsable FORTY-CASES.jsonl accompanies it.

The control's phase-0 outputs were generated on 4 November and reused in the 6 November evaluation; original dates remain. Old meaning scores are still control 34/40 and adapter 23/40. New-rubric judgments await Claude and must be added beside the preserved results. No inference, rescoring, private human-order release, T45 use or runtime change occurred.

Training 3's merged revised labeller reports revised and legacy yields. Only revised pairs may train; fewer than 200 stops the task. This evidence packet neither samples nor trains. T39 continues under its unchanged frozen protocol.
