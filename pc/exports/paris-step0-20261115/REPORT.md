# Paris backtest: Step 0 and Qwen coding, 15 November 2026

The fixed run completed at 18:06:31 Berlin: 20 passage-continuation requests and all 750 second-coder requests. All 770 original request/response chains reconcile, with zero unknown, erroneous or pending chains. Frozen inputs and runtime are unchanged; plain Qwen, the Pi user timer and power settings were not changed.

## Step 0

The longest shared continuation was 3 normalized words, below the frozen threshold of 12. No journey is excluded from a future Stage 2 by this rule. This is a result for the 20 fixed samples, not proof that Qwen knows none of the letters.

All 20 responses are retained, including one completion stopped at the token limit. Two reference remainders contain only 11 and 3 normalized words, so those two cases cannot reach the 12-word threshold. This limitation is reported without replacing samples, changing the threshold or resending a request.

PROTOCOL.json is the exact preregistration; RESULT.json preserves the original per-sample results. All requests, full response bytes, begin/done/settings records and source freezes remain in the original local job.

## Second coder

The adjacent paris-stage1-20261115/CODES-QWEN-REPLIES.jsonl contains exactly the 750 frozen IDs and their original final replies, without recoding, repair or retry. QWEN-FREEZE.json preserves the coding plan. Only the fixed codebook and sentences were supplied to Qwen; Claude's codes/profile were not used for coding or comparison by this seat. Claude can now combine the independent codings.

No Stage 2, training, shelf addition or live instruction change was performed. The letters and all these outputs remain evaluation material.
