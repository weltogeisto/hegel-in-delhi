# Handover to Codex, 10 October 2026

Decided with Welt after your work block of 8 October (`Hegel: four-hour work block`):

- **Adapter training stays on hold**, as your block concluded. Train nothing, delete no adapter.
- **The order of work:**
  1. Get your six runtime fixes into the repo.
  2. Build structured memory of what happened.
  3. Get a blind review with hidden controls.
- **The Hegelizer is parked** until Welt says go. It is the inverse-paraphrasing pipeline in `pc/HEGELIZER.md`.
- **Main has moved** since your block's checkpoint:
  - Writings are back on the chat call by default. `HEGEL_WRITE_MODE=plain` keeps the plain-text path and its guards.
  - The Hegelizer code is in the repo, but nothing in the world uses it.
  - Compare with `git log --oneline <your checkpoint>..origin/main`; the checkpoint is in your `source-checkpoint.json`.
- **The live world stays paused.**

Report each step to Welt in one line, with the exact error text if something fails. Stop on anything unexpected; don't improvise.

**Status, 10 October:** steps 1 to 3 are done and on main (c0aa95f): the six mechanisms, the merge, and the parked phase-2 tooling, 761 tests OK. Start step 4 from `origin/main`.

## 1. Commit your block's source changes

Work in the repository where the six mechanisms sit uncommitted:

- thought-location attribution;
- same-date owl-state persistence;
- explicit eating-action evidence;
- bounded continuation-title validation;
- optional present-recipient IDs;
- rejection of an already settled canonical charge.

```bash
git status
git switch -c codex/runtime-fixes
```

Commit the source and test changes, one commit per mechanism if they separate cleanly, otherwise one commit that names all six. Check the committed files against the hashes in `source-final-verification.json`. Commit no block outputs, adapters, logs or `mind/train/`. Report the commit hashes and the files.

## 2. Merge main into that branch

```bash
git fetch origin
git merge origin/main          # a merge, not a rebase: your tested commits stay as they were
```

When resolving conflicts, keep both sides:

- main's writing default (the chat call), the plain path and its guards;
- your six mechanisms;
- the tests from both sides.

If both sides changed the same logic and you can't keep both, stop and report the hunk. Then run:

```bash
python3 -m unittest discover -s tests     # must end with OK
```

Run your Node and browser checks too, if they apply. Report each conflict and how you resolved it, and the test counts.

## 3. Hand the branch over

WSL has no GitHub login, so send the branch as a git bundle. Patches would lose the merge commit and its conflict resolutions; a bundle keeps them:

```bash
mkdir -p /mnt/c/hegel/handover
git bundle create /mnt/c/hegel/handover/runtime-fixes.bundle origin/main..codex/runtime-fixes
git bundle verify /mnt/c/hegel/handover/runtime-fixes.bundle
```

Send Welt the bundle and the test log; Claude reviews, applies and pushes them. If Welt sets up a GitHub login in WSL, push the branch `codex/runtime-fixes` instead, never main.

## 4. Structured memory of what happened

Start only after Welt confirms that step 3 is in the repo. Build on your `runtime-next-design.md`.

**The goal:**
- prose never contradicts what happened;
- what someone said never turns into fact;
- no charge is booked twice.

**The design reference** is MemIR (Jin et al., May 2026, [arXiv 2605.25869](https://arxiv.org/abs/2605.25869)). It names our failure "provenance-role collapse": memory kept as flat text loses track of where a piece of information came from. Its fix is typed memory: verbatim evidence spans, and claim atoms that count as fact only when they point to a supporting span. It gains most on source tracking, temporal grounding and contradiction resolution, and it also runs on Qwen3-14B. Follow its structure, with one deliberate difference: MemIR rewrites "X said Y" into the underlying fact, and we must never do that. What someone said stays a statement, with its speaker.

**Requirements:**
- **One store of records per day, each with a stable id:**
  - *events:* what he observed;
  - *statements:* speaker, words, and where and when he heard them. A statement is never a fact;
  - *payments:* canonical id, amount, and whether it is settled;
  - *works:* his manuscripts.
- **Every prose writer (diary, owl, Depesche, writings) gets the relevant records, labelled by kind.** "X said Y" may be reported as said, and as fact only when an observation supports it.
- **A claim check after each prose text:**
  - List the text's factual claims and test each against the records.
  - An unsupported claim gets one regeneration; if it is still unsupported, drop that sentence and log it.
  - Do the check with the 27B model's own yes/no probability from llama-server (`n_probs`), calibrated on about 150 sentences you label by hand from the two-day rehearsals (temperature scaling). Report the calibration error. Train nothing.
- **Reserve prompt room for critical evidence.** Stay within the existing prompt budgets; the tests check them.
- **Test it** on 3 new seeds of 2 days each, isolated, never touching the live world. Report before and after:
  - contradictions with the record;
  - things said that became fact;
  - duplicate charges;
  - JSON validity;
  - prompt sizes.
- **Don't train on these days, and don't repair the record by hand.**
- **Deliver** as a bundle, as in step 3.

## 5. Blind review

Decided with Welt on 11 October: Claude is the reviewer, and Welt rates the same texts as a second blind rater. Claude did not write the texts, but helped write his prompts, and model judges tend to prefer model-written text. So the review carries hidden controls and the key stays away from Claude until both have rated.

- **The packet.** Take the texts from `review-only.zip`. Mix in about 10 real Hegel passages of the same length (150 to 300 words) from the English translations on his shelf, as hidden controls. Choose less famous passages, not the ones everyone quotes. Give every text a random id, strip the arm, the source and anything that gives them away, and shuffle the order.
- **The key** (id → arm or control) goes to Welt only: never into the repo, a bundle or a file Claude can read. Welt uploads it after both have rated.
- **The ratings.** Each rater scores every text from 1 to 5 on four dimensions, each with a one-line reason. Holistic judgments of persona fidelity are unstable (PRISM, EMNLP 2026, [arXiv 2608.26674](https://arxiv.org/abs/2608.26674)).
  1. **Argument moves:** does the text develop a claim the way he does (from the difficulty within a position, to what it presupposes and where it turns into its opposite), or does it assert, list, or lay a triad over the material?
  2. **His commitments:** are the positions his, as of 1831, including the prejudiced ones, neither softened into a present-day view nor exaggerated into a caricature?
  3. **Response to the particular case:** does the thought start from the specific situation and stay with it, or could the same paragraph stand under any title?
  4. **Voice:** does it read like him, not like a translator's pastiche or a modern essay?
- **What it measures, once the key is in:**
  - **The controls:** if Claude does not score the real passages above the model texts, Claude's ratings measure nothing, and the review needs a human Hegel reader after all.
  - **Agreement:** between Claude and Welt, per dimension (Cohen's κ; Krippendorff's α if a rating is missing). That agreement is the ceiling any later automatic judge is read against.
  - **The arms:** compared only on dimensions where the controls separate.
- **The guide** is the instruction sheet that goes with the packet: the four dimensions as above, the 1-to-5 scale, and nothing about which texts are which.
- From your `fresh-task-template.json`, prepare 8 essay situations and 8 letter situations for Welt to write. No model writes them. They are for the next comparison; don't run it yet.

## 6. Parked, and off limits

- **The Hegelizer:** don't start it until steps 1 to 4 are done and Welt says go.
- **Don't touch** the training data, the adapters, the firewall, the power settings, the ML packages or the live world.
