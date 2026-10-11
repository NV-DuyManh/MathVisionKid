# OCR development: preserve prose during mathematical adaptation

The training pipeline now checks role-specific regressions at **every epoch**, instead of selecting an aggregate winner and discovering degraded prose only afterward. A new 30-epoch development experiment found a checkpoint improving mathematical recognition while retaining the baseline's exact-prose count on DEV. **It remains experimental; production is unchanged.**

## Implementation

- Reused one `scope_regressions()` comparison for both checkpoint selection and the final gate. DEV selection prioritizes zero role regressions, then fewer failed checks, critical errors, literal CER and exact lines. If no epoch qualifies, evidence still marks its regressions; creating a checkpoint never installs it.
- Every epoch records role metrics and regression reasons. The selected epoch's reasons and selection policy are saved with the checkpoint.
- Added bounded `--prose-replay` (integer 1–3, default 1), sampling only verified TRAIN prose more often. No DEV/HOLDOUT record is repeated or reclassified; replay is sampling, not new independent data. Each epoch is bounded to 512 sampled TRAIN views.

## Bounded experiment

Private artifacts: `ai-training/datasets/drive_math/new2_20261011_266/training_expanded/development_preserve_prose/`.

The owner's continuation authorized this new development phase after the previous frozen evaluation. Its previous decision, selection and evaluation evidence were preserved. The new run starts from the unchanged production model, using the same frozen 142 TRAIN / 48 DEV references, CPU, two threads, batch 4, seed 20261011, learning rate 0.0001 and 30 epochs. It adapts the final CNN block, BiLSTM and CTC head, preserves aspect ratio, adds one autocontrast TRAIN view and samples each of 26 reviewed TRAIN prose records three times per epoch. This produces 332 cached development views and 388 sampled TRAIN views per epoch, without counting replay as extra evaluated lines.

The previous HOLDOUT is exposed and provides no new independent validation. Historical HOLDOUT records are loaded for source/split integrity only; **no HOLDOUT neural preprocessing, fitting, epoch scoring or prediction occurred** in this follow-up. No fitting used their transcripts or pixels. New independent reviewed sources are required before a release claim.

## DEV evidence

The new policy selects **epoch 4**, with no role regressions against production on DEV:

| DEV measurement | Production baseline | Selected epoch 4 |
|---|---:|---:|
| Literal CER, 48 lines / 702 characters | 35.47% | 10.68% |
| Exact lines | 3/48 | 8/48 |
| Critical edit errors, including digits/operators/selected punctuation | 117 | 38 |
| Expression CER, 38 lines | 62.57% | 16.31% |
| Prose CER, 10 lines | 4.57% | 4.27% |
| Exact prose lines | 3/10 | 3/10 |
| Prose critical edit errors | 1 | 1 |

The aggregate-only criterion would choose epoch 16 (6.27% CER, 13 critical edits) but that epoch regresses prose CER and exact-prose recognition. The new rule intentionally rejects this tradeoff. This run does not beat the previous candidate's aggregate DEV score; it finds a candidate that preserves the chosen prose checks. The small reused DEV sample cannot establish generalization, and there is still substantial mathematical error. More epochs or replay alone did not remove that limitation.

## Verification and outcome

**35 tests passed** across training, batch recognition and source storage. Added tests verify checkpoint selection retains prose despite a better aggregate mathematical score, invalid replay values fail before fitting, replay leaves evaluation counts unchanged, and deferred HOLDOUT pixels cannot enter neural preprocessing during the real synthetic backward-pass test. Synthetic pixels verify pipeline behavior, not OCR quality. Existing checks cover source hashes/pixel leakage, reviewed label eligibility, frozen vocabulary/checkpoint pairing, role gates and spurious numerals in prose. Focused whitespace checks passed.

Verified selection by recomputing the key over all 30 saved epoch records. Candidate/vocabulary/trainer snapshots and manifest hashes match evidence. Production checkpoint, vocabulary and provider bytes remain unchanged; previous selection/decision and reviewed references remain unchanged. Data, transcripts and candidate weights remain Git-ignored. No dependency installation, application UI change, cloud deployment, physical-device claim, commit or push occurred. Unrelated deployment work was preserved.

Selected private checkpoint SHA-256: `b216cf8ad434115e42fb4dee6240aa8bcff12b07de5ccc8a7eb20704e13d33bf`. The development decision retains production and records the requirement for fresh reviewed source validation. This phase is complete; OCR itself is not yet release-ready under these experiments.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: correct checkpoint selection and sampling with small extensions to the existing trainer.
  - Applied to: shared regression comparison, bounded TRAIN-only replay, existing pipeline reuse, focused tests and evidence without new dependencies.
