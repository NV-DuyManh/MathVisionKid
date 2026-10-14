# OCR math continuation — 2026-10-14

## Result

The two new candidates are rejected. They do not improve the frozen DEV set,
and production weights/vocabulary remain unchanged. This phase performed real
CPU neural training and fresh OCR, without copying original images off Drive.

The preceding tutor fix and model leaderboard were committed/pushed to `main`
as `4ad78711703f19e31c2584e55079b4baa833189a`; remote HEAD was verified.
This new experiment report is local and was produced after that push.

## Experiment

- Parent: private `math_focus/run_control/candidate.pth`, SHA-256
  `a6e8aac96e6f1597a144f6c0c9cc762a01cf11a8194ad2b2061545b047f415dc`.
- Frozen source-reviewed cohort: 462 TRAIN and 95 DEV crops from 68 Drive pages.
  Five reserved HOLDOUT crops/sources were excluded before any source reads.
- The 50 added fields/cells and prior reference labels were reused unchanged.
  No prediction, mathematical answer or candidate score was used as a label.
- Two four-epoch runs: equal settings except correct-path retention weight
  (control 0, anchored 2). Seed 20261014, Adam 0.000005, batch 8, four CPU
  threads, math weight 2; TRAIN math errors receive another factor 2.
- Anchoring uses 425 TRAIN records whose parent critical sequence or full
  transcript already matches the literal reference. Hard-math emphasis uses
  29 TRAIN records; DEV does not choose training weights or receive gradients.
- CNN/BiLSTM stay frozen. Only the linear CTC head's weight/bias changed.
  No augmentation, language correction, arithmetic repair, or cloud API calls.
- All 557 crops were recognized with the parent and both selected candidates.
  Both selected epoch 1. Later epochs did not pass the frozen acceptance gate.

## Scores on the same 95 DEV crops

| Measure | Private parent | Control | Anchored |
|---|---:|---:|---:|
| Character errors / 1,097 | 105 | 107 | 107 |
| Critical errors / 432 | 30 | 32 | 32 |
| Exact crops / 95 | 53 | 52 | 52 |
| Critical-exact crops / 87 | 64 | 62 | 62 |

Both introduce an expression-scope regression and lose a zero:
`300 cm² = 3 dm²` becomes `30 cm² = 3 dm²`. The acceptance criteria require
at most 29 critical errors, at most 105 character errors, at least 53 exact and
64 critical-exact crops, and no per-role regression. Both fail.

TRAIN exact matches increase only 382 → 383 out of 462; TRAIN critical errors
remain 48. This is fitted-sample evidence and does not establish generalization.

## Fresh audit and source inspection

- A separate process re-read 99 crops from 19 Drive pages: all 95 DEV plus four
  previously reviewed difficult TRAIN crops. Both candidate scores and all
  audited predictions reproduced exactly.
- Candidate tensors are finite, only the CTC head differs from the parent,
  and all pinned input hashes/production hashes still match.
- Original source context and exact boxes were viewed in RAM for the table `5`,
  `170394`, boxed `18 : 3 = 6`, and red `240`. Their existing literal references
  remain unchanged. The table `5` is still misread as `3`; the boxed initial
  number is still omitted. These are recognizer failures, not corrected labels.
- Remaining queue: 122 crops (79 TRAIN, 43 DEV) with non-exact anchored output.
  Some are punctuation/spacing/prose errors. The queue flags critical errors
  separately and retains original source hashes, boxes and literal references.
- Original page/crop/ZIP/Parquet files were not written locally. Previously
  deleted `containers` and `pages_originals` caches remain absent.

## Artifacts and limits

Private artifacts:
`ai-training/datasets/drive_math/math_anchor_20261014/` contains `train.py`,
`policy.json`, `result.json`, `review_failed.py`, `audit.py`, `audit.json`,
`remaining_review_queue.json`, and the two rejected checkpoints.

- Control checkpoint: `b351b57917dc30d0f51c642d6cdfa8e9b747ebfaeb1b9511eceb68957ff57959`.
- Anchored checkpoint: `388b0d79b5383b805c628208f08e7960d000e800b268c0d7e9b03ee5986c2d5a`.
- Production checkpoint remains `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.
- Production vocabulary remains `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.

DEV has been repeatedly used, so these are development comparisons, not
independent accuracy estimates. Writer/pretraining independence remains unknown.
This phase covers the specified 557 regions, not every raw image in the larger
Drive corpus. It trains OCR, not the TeacherMath language model. No candidate
was promoted, deployed, or included in Git. The source review/training/audit
completed; production stays on the existing checkpoint.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the established source reader, CTC helpers and frozen guards.
  - Applied to: private head experiment, RAM source review, checkpoint audit and gate.
