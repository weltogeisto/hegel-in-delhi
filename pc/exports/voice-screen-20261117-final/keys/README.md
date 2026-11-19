# W4: the three things owed from the PC, released after the judgments were sealed (#79, `c0ae85a`)

Copied, never changed, from the frozen job on the PC (`/home/ai/hegel-eval/codex-tasks-20261117/w4-night-204000`, Sol's run of 17 November) by the PC seat (Claude on the PC), 19 November, with `w4_owed.py`.

- `KEY.json`: the label key (opaque id → context, arm, seed). sha256 `3d1c024b…8a07`, as `SEALED.json` expects.
- `PAIRS-KEY.json`: the pair key. sha256 `630c0a28…00a0`, as `SEALED.json` expects.
- `P-ACTS.jsonl`: arm P, one line per reply (144): `act_made`, `act` (`kind`, `what`, `minutes`), `refused` and the engine's `refusal` text (the follow-up's prompt), the `second_answer` and its `second_act`, and the promises kept in the state afterwards. 20 acts made, 8 refused, 0 second answers with an act, 12 replies left a promise kept.
- `WHO-ANSWERS.json`: for each context where he named no one, whom `voices.pick` chooses with the switch off and on (the job's own table, 8 contexts).
- `OWED.json`: the counts and the four sha256.
