# Expanded NEW2 OCR review and bounded adaptation — 2026-10-11

The reviewed data and evaluation pipeline improved, and the new candidate substantially reduced line-recognition errors. **Production remains unchanged:** the candidate still confuses digits/operators, hallucinates numerals in some prose, and loses exact prose lines on DEV. No model installation, deployment, commit or push was performed.

## Reviewed data

The private batch is `ai-training/datasets/drive_math/new2_20261011_266/training_expanded/`.

- Visually compared 141 draft transcripts/crops with original pages; accepted **102** and excluded **39** before fitting or scoring. Exclusions include neighboring-line ink, uncertain punctuation and annotated crops. Draft records remain explicitly unverified and ineligible.
- Corrected several crop boundaries to retain complete glyphs and omit neighboring marks. References preserve what is written; arithmetic answers and grammar are not repaired.
- Combined new accepted records with previous TRAIN/DEV references: **142 TRAIN / 48 DEV / 41 HOLDOUT**, 231 records across 18 / 4 / 3 distinct source-page hashes respectively.
- Previous exposed 15-line HOLDOUT was excluded entirely. Fresh HOLDOUT source-page hashes do not occur in the previous reviewed manifest. Duplicate byte aliases inherit their source-page split; the loader also rejects cross-split decoded-page and crop-pixel aliases.
- TRAIN has 26 prose lines, 29 expression lines and 87 earlier text/field references. DEV has 10 prose and 38 expression lines; HOLDOUT has 19 prose and 22 expression lines.
- Originals: all **266** mounted source files still match their recorded SHA-256 hashes. No photo was changed or deleted.

Eligibility is per reviewed crop, not per complete photo. The thousands of automatic OCR drafts remain separate and are never training pseudo-labels.

## Experiments and selection

Both runs started from the unchanged production checkpoint/vocabulary and used the same frozen reviewed manifest. Each ran 24 epochs on CPU, batch 4, two threads, seed 20261011 and learning rate 0.0001. Experimental input preserves aspect ratio at height 64, width 64–1024, with stride 8. Each TRAIN crop receives one extra grayscale/autocontrast view; DEV/HOLDOUT pixels remain unchanged. There are 332 development views, including augmentation; a misleading extraction-progress denominator was corrected to count these views.

- Run01: frozen CNN, adapt BiLSTM and CTC head. Selected epoch 22: DEV CER **6.13%**, 18 critical edits, 24/48 exact lines. Prose critical edits and exact-line count regressed.
- Run02: adapt the final CNN block, BiLSTM and CTC head; the first three CNN blocks remain frozen. Selected epoch 14: DEV CER **6.41%**, 14 critical edits, 20/48 exact lines. Prose CER and critical edits match the baseline, but exact prose lines regress from 3/10 to 1/10.

DEV-only comparison selected run02 because it has fewer role-specific regressions and fewer critical errors. Neither option was release-ready on DEV. Selection and paired artifact hashes were frozen before HOLDOUT neural inference. Only the selected checkpoint was evaluated on fresh HOLDOUT; no later fitting or checkpoint selection used these results.

## Frozen results

| Measurement | Unchanged baseline | Selected candidate |
|---|---:|---:|
| DEV literal CER, 48 lines / 702 characters | 35.47% | 6.41% |
| HOLDOUT literal CER, 41 lines / 350 characters | 60.00% | 12.57% |
| HOLDOUT exact lines | 0/41 | 17/41 |
| HOLDOUT expression CER, 22 lines | 72.04% | 7.11% |
| HOLDOUT expression critical edit errors | 80 | 5 |
| HOLDOUT prose CER, 19 lines | 41.73% | 20.86% |
| HOLDOUT all critical edit errors, corrected accounting | 81 | 10 |
| HOLDOUT numerals hallucinated in otherwise noncritical prose | 0 | 4 |

CER is literal character error rate, not the percentage of complete exercises solved correctly. Critical comparisons retain digits, operators and selected punctuation, including decimal separators; their error count is an edit count, not a count of wrong problems. The candidate's ten critical errors comprise five expression edits, four spurious numeral insertions in prose and one omitted prose period.

The initial scorer counted critical errors only on references already containing a critical character, omitting the four hallucinated numerals. Fixed `metrics()` to count those insertions and report them separately. Re-scored **the same saved predictions**; no additional neural inference, fitting, reference changes or checkpoint selection occurred. Original evaluation evidence is preserved. Literal CER, exact-line results and DEV selection metrics are unchanged; the initial candidate critical count of six becomes ten under corrected accounting.

The final gate fails for DEV exact-prose regression, HOLDOUT prose critical regression, HOLDOUT CER above 5% and unresolved critical errors. `gate()` now checks each role as well as aggregate metrics, so a mathematical improvement cannot hide degraded prose. Candidate creation never promotes a model automatically.

## Validation and artifacts

**31 tests passed** across training guards, batch recognition and source storage. New regression tests cover aggregate gains hiding worse prose and numerals hallucinated in text without reference digits. Existing tests cover split/hash/pixel leakage, invalid labels, real backward-pass plumbing, matching frozen checkpoint/vocabulary pairs and deferred HOLDOUT evaluation. Focused Git whitespace validation passed.

Private artifacts include draft/crop review sheets, accept/exclude decisions, reviewed manifests/index, preflight recipes/hashes, both checkpoint/vocabulary pairs and immutable snapshots, DEV-only selection, original frozen evaluation, corrected saved-prediction re-score, error diagnosis and the final non-promotion decision. They remain Git-ignored; photos and transcripts are not included in this report.

Production checkpoint SHA-256 remains `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`; vocabulary and production provider hashes also match preflight. Previous and expanded reviewed manifests remain unchanged after fitting/evaluation. Selected private candidate SHA-256 is `56b9160fad26f9f82ae08fc55ea81e1a325a6e360bfd14aaca15f999c6cd9456`.

## Limits and next evidence needed

This is a small, purposive line experiment with repeated reading words and multiplication tables. Writer independence and historic base-model exposure are unknown. Scores do not establish accuracy on all 266 photos, complete page segmentation, 2-D fractions/long division, photographed word problems or the tutoring workflow. The new HOLDOUT is now exposed and must not be called fresh after further tuning. The previous experiment used a different HOLDOUT, so its CER cannot be compared directly with this one's CER as a model ranking.

Further adaptation needs more varied, clean reviewed text and mathematical lines plus new source pages reserved before tuning. Production replacement also requires broader end-to-end evidence with the matching preprocessing policy. No physical-device verification or cloud migration occurred in this task; unrelated cloud work was preserved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: extend the existing OCR review/training pipeline with focused correctness fixes.
  - Applied to: source-loader reuse, bounded experiments without new dependencies, minimal role-regression and metric fixes, focused tests and immutable evidence.
