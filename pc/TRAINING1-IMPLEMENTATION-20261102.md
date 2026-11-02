# Training 1 implementation, 2 November 2026

Training 1 now requires chapter assignments and a sealed fresh confirmation cohort before loading a model. The running Phase A source and data freeze remain independent.

## Chapter isolation

The chapter_splits module maps all 6,927 existing units to top-level headings in the cleaned books. It verifies historical indexed passages through the original OCR mender, without rebuilding the shelf or rewriting targets. Cross-boundary units and ambiguous repeats unite their chapters. The two Wallace books have no retained headings, so each stays whole.

Seed 1831 fixes the group order. The prefix nearest the original 5% full-unit target becomes held out: 62 groups, eight held groups, and 204 held full units against 187 targeted. Train: 3,543 full and 3,027 short units. Held: 204 full and 153 short units. Shorts inherit parents. Training projects split metadata over the original immutable generation ledgers. It still requires 20 accepted unique full held units for evaluation.

Reuse C:/hegel/handover/codex-tasks-20261102/training1-additions-20261102-212000/CHAPTER-SPLITS-V2.json with the unchanged corpus. For a new installation:

    python3 tools/chapter_splits.py --units FROZEN_DATA/hegelizer2-units.jsonl --out NEW_SPLITS.json

## Fresh confirmation

T45 is preregistered and sealed at /home/ai/hegel-eval/codex-tasks-20261102/t45-confirmation-v2. Its 40 actual mind thoughts have at least 40 words. Selection excludes later-than-Day-1 names, duplicates and every normalized thought in the frozen legacy 39+1 cohort. Days are visited round-robin until exhausted. Within each day, less-used scene and person groups precede hash ties.

Available eligible thoughts give these day counts: 13:2, 14:10, 24:2, 25:6, 26:4, 27:15, 28:1. They cover seven scenes and ten present-person groups. The seal SHA256 is 10058aa7f65efdd04d1122bbfbd42213912f850564d41ace5d139b030717630d.

No confirmation output was generated. The key and selected texts remain private. The unsuccessful whole-day exclusion rule, which left 11 thoughts, is preserved. That rule exceeded the brief by excluding unused thoughts on legacy source days; before any outputs, it was corrected to exclude the actual pinned development inputs. The legacy KPI 1 cohort and all five bars remain unchanged.

Source and code identity, frozen inputs, cohort and key commitments are verified before training loads a model:

    python3 pc/train_hegel.py --round-two --phase restyle --goldfish --data FROZEN_DATA --chapter-splits PREPARED_SPLITS.json --confirmation-seal CONFIRMATION/SEAL.json --check-data

For a new source cohort, use voice_confirmation.py with --preregister, --shadow-commit, --development-plan and --out, then --seal with --days-dir. Repeat --development-plan for every prior voice cohort. Never reseal or revise the rule after viewing confirmation outputs.

After tuning, --lock-profile requires the fixed adapter file, profile, adapter id and scale, legacy output root and both complete legacy results. It freezes one artifact and profile before confirmation requests. Different profiles and changed adapters are refused. Confirmation never selects checkpoints or scales. Disjoint 20-pair sheets and judgment-before-unblinding rules still apply.

## Voice diagnostics

The unchanged two-boolean plain-Qwen meaning call remains the KPI. A separate temperature-zero plain-Qwen call records propositions added and omitted, saving raw replies. Invalid, truncated or missing diagnostics remain unavailable, never zero. Include the additional 40 calls per arm in Phase C's measured budget.

The --dashboard action of tools/hegel_test_round2.py takes --out, --control-result and --adapter-result. It creates private JSON and HTML without model calls: propositions, multiset lexical name/number/negation retention, twelve-word copying before and after the guard, fallback counts and length-matched Delta. Delta uses the common minimum style-word prefix for each case; only diagnostic copies are truncated. Lexical retention is a proxy, not semantic entailment. Keep labeled reports away from blind raters until their choices are frozen.

## Validation and runtime limits

36 distinct focused CPU checks cover chapter bridges and repeats, historical provenance, immutable split projection, fresh selection and sealing, profile locks, invalid diagnostics, matched lengths, unchanged legacy KPIs and fake benchmark/trainer wiring. Initial fixture and preparation failures remain preserved; affected checks passed after correction. All 22 CSVs and 652 baseline paths outside the five authorized edits remain exact. See pc/training1-validation-20261102.json.

The branch retains the earlier owned four-worker runtime and inherited PC work and results. Phase B/C still need the completed Phase A gate, readiness, measured budget and Welt's night with one day's notice. A matched no-Goldfish run belongs to a later window if KPI 4 fails. Trainings 2/3 and the pending T39/T40 screen decision remain separate. There is no new permission for power changes, a public switch or automatic adapter adoption.
