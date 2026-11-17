# Fixed-day factual audit

Read only these texts and their supplied typed records. Do not search. Do not infer a variant or consult a key.
Count contradictions with the records separately from unverified statements asserted as fact. A claim clearly
attributed to its speaker is not a promotion. Plans are intentions; drafts are not sent letters. Earlier source
prose and a plausible quotation prove no event. Missing evidence is not a contradiction: flag uncertain cases.
For each numbered sentence with a problem, record one row: id,sentence,contradiction,promotion,uncertain,record_ids,reason.
Use 0/1 flags; a sentence can receive both kinds of error. Count each kind at most once per sentence.
Return a second CSV with one row per text: id,sentences,contradictions,promotions,uncertain.
Return a third CSV for every diary and revision log: id,argument,reason. Score argument from 1 to 5:
does the text develop a claim from the difficulty within a position, to what it presupposes and where it
turns into its opposite, or does it assert, list, or lay a triad over the material? Give a one-line reason.
For an empty revision log use 1 and the reason "empty; no argument"; absence must not raise the mean.
Judge the supplied prose, not the position or eloquence of a quoted speaker in its records.
Use the supplied sentence count, including all zero-error texts. Score every text and commit both CSVs and
the argument CSV and their SHA256 hashes before requesting the key. Empty or unusable outputs remain in the packet and are reported.
