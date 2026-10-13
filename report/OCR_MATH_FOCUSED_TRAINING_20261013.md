# Math OCR focused training — 2026-10-13

Two additional authorized training runs finished: **12 epochs each, 24 epochs total**. Neither produced a measured reduction in mathematical digit/operator errors. Both candidates remain private; the application model was not replaced.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: small controlled OCR training change and source-read recovery.
  - Applied to: reuse of the existing bounded trainer, normalized math weighting, focused objective check and immutable experiment evidence.

## Experiment

- Frozen reviewed page cohort: **394 TRAIN, 95 DEV, 5 reserved HOLDOUT fields**.
- TRAIN includes 217 entries with explicit mathematical roles, 155 prose entries and 22 entries without a specific mathematical role. The same references and splits were used in both runs.
- Both runs start from the unchanged private parent checkpoint `4903062b…` and vocabulary `dc25d2de…`.
- CNN and recurrent layers stay frozen. The CTC head trains at learning rate **0.00001**, ten times below the previous rejected head experiment. Seed, aspect-preserving input, batch size 4, 12 epochs and prose KL anchor weight 1 are identical.
- Control uses equal sample weights. Focused run doubles the weight of explicitly identified TRAIN math roles; prose and unknown roles retain weight 1. Full literal transcripts are preserved.
- Per-sample CTC losses are divided by target length, then averaged with sample weights. Weight 1 reproduces the original CTC mean objective. Weight normalization changes relative emphasis in mixed batches; it cancels in a batch containing only math. This is not a loss on extracted digits or an automatic correction of arithmetic.
- A private frozen trainer copy was used so the shared code hashes of ongoing recognition work remained intact. No student UI, runtime model installation or Git commit/push occurred.

## Results on the same 95 DEV samples

| Metric | Unchanged parent, same input | Equal-weight low-rate control | Math-weighted low-rate run |
|---|---:|---:|---:|
| Character errors / reference characters | 107 / 1,097 | 105 / 1,097 | 105 / 1,097 |
| Character error rate | 9.75% | 9.57% | 9.57% |
| Critical digit/operator errors | 30 / 432 | 30 / 432 | 30 / 432 |
| Exact transcripts | 53 / 95 | 53 / 95 | 53 / 95 |
| Critical-exact transcripts | 64 / 87 | 64 / 87 | 64 / 87 |
| Selected epoch | — | 1 | 1 |

No reviewed role regressed at the selected epoch. Later epochs increased critical errors, so training longer was not supported by DEV evidence. The weighted run did not outperform the control.

The small character-count gain does not establish a corrected mathematical expression. The only changed DEV transcript is:

- Literal reference: `65+8=73`.
- Parent: `65 +8 - 73`.
- Both new candidates: `65 +8  73`.

The equality sign is still missing; both predictions are wrong. No corrected transcript, mathematical accuracy gain or product improvement is claimed from this aggregate change.

Predeclared acceptance required fewer than 30 critical errors, no character/exact-transcript regression and no role regression. Both candidates fail the critical-improvement condition. The weighted run also fails to demonstrate an improvement over equal weighting. HOLDOUT neural inference was not performed.

## Source storage and recovery

All original images remain on the mounted G: Drive. Original bytes were read into RAM and checked against the frozen per-source SHA before cropping. Each successful run verified **69 original page sources**. No original photos, crops, ZIP files or Parquet files were restored locally.

Two initial control loads failed before fitting because a Drive read exceeded 60 seconds. Their logs and read receipts were preserved. Concurrent recognition reads were paused, and the reader was changed to bounded raw chunks with up to three attempts. Both final training runs loaded all page references successfully, with zero read retries in their final receipts and unchanged input hashes.

Separately, a bounded recovery audit of the **18 previously excluded supplied Parquet controls** recovered only **1/18**. Four groups timed out, five sibling samples were deferred and eight were not attempted within the audit budget. The full cohort controls therefore remain unavailable for release consideration. Samples were not removed on the basis of model scores.

After training, recognition resumed on the **787 unfinished/failed pages** and **11 failed ZIP crops**, using the earlier private parent model rather than either new candidate. Those recognition jobs are separate from the completed training experiments. Other unresolved Parquet reads remain recorded; full corpus recognition is not certified complete.

## Validation and limitations

- Synthetic objective check passed with unequal target lengths: equal weighting matches standard CTC, only known math roles receive extra weight, prose/unknown-only batches preserve the original objective, and gradients are finite/nonzero.
- Artifact comparison verified checkpoint/vocabulary hashes, identical manifest/trainer hashes, same-input parent metrics, false promotion flags, no HOLDOUT neural inference and unchanged source-read receipts.
- Independent read-only audit recomputed all 95 DEV outputs against the manifest and confirmed both candidates have identical DEV transcripts, the same unresolved equality-sign error, correct rejection decisions and unchanged source-read fingerprints.
- No prediction was promoted into a training reference. Original incorrect arithmetic remains literal source transcription.
- These are repeatedly used development samples, not an unbiased independent accuracy estimate. Writer and original pretraining independence remain unknown.
- Reserved evaluation is only five fields from one page. Manual line/field crops do not evaluate page segmentation or 2-D fraction/long-division parsing.
- Rare mathematical symbol coverage is limited. Additional diverse, source-reviewed TRAIN examples and broader independent evaluation are needed before another release decision; repeating these epochs alone is not sufficient.

## Evidence

Private root: `ai-training/datasets/drive_math/math_all_20261013/math_focus/`.

- `acceptance_policy.json`: frozen DEV acceptance limits.
- `preparation_receipt.json`, `trainer_math.py`: experiment objective and code snapshot.
- `train_control.log`, `train_weighted.log`: completed training histories.
- `run_control/evaluation.json`, `run_weighted/evaluation.json`: paired candidates and complete metrics/predictions.
- `read_receipt_control.json`, `read_receipt_weighted.json`: source SHA verification and input fingerprints.
- `comparison_decision.json`: both candidates rejected for the required mathematical improvement; no promotion.
- `recognition_resumed_plan.json`: unfinished recognition selections and their unchanged parent checkpoint.
- `../control_read_recovery_20261013.json`: recovery results for all 18 excluded controls.

Candidate checkpoints:

- Control: `a6e8aac96e6f1597a144f6c0c9cc762a01cf11a8194ad2b2061545b047f415dc`.
- Math weighted: `33a7b6a6aadc8cbafe00f724bcb2aaf7111baac65a74c14089826260fa28f49b`.

Production checkpoint/vocabulary remain `a807eaa7…` / `6af4062e…`.
