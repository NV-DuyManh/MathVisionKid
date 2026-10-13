# Math OCR literal-label review and CNN-only experiment — 2026-10-13

This phase reviewed **31 new mathematical references** and completed a separate **four-epoch CNN-only experiment** on 18 selected additions. It regressed the unchanged DEV set and was rejected. The installed model, vocabulary and student application remain unchanged.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the existing bounded trainer, original-source reader and reference schema for one focused hypothesis.
  - Applied to: RAM source review, exact-crop checks, deterministic cohort selection, private CNN-only adaptation, frozen-state guards and focused validation.

## Source review

All accepted references were transcribed from complete original Drive pages and then checked against the exact final rectangular crops displayed in RAM. No neural prediction supplied a reference, and no student arithmetic was solved or corrected to generate a label. Box outlines and ruling are layout rather than mathematical text; crossed-out, overwritten, clipped or adjacent-line-contaminated proposals were withheld.

| Existing TRAIN source | Accepted new references | Content |
|---|---:|---|
| 453.jpeg | 15 | Addition, subtraction and comparisons |
| 773.jpeg | 4 | Multiplication expressions |
| 926.jpeg | 4 | Division expressions with boxed numbers |
| 928.jpeg | 2 | Multiplication/division comparison expressions |
| 960.jpeg | 6 | Three multiplication expressions and three numeric fields |
| **Total** | **31** | **28 expressions/comparisons, three numeric fields** |

Four initially inspected pages (762.jpeg, 1007.jpeg, 975.jpg, 813.jpeg) were literacy/copywork and yielded zero math labels. The loop glyph in 975.jpg was a letter `o`, not a numeric zero. Dates and lesson numbers were not repurposed as arithmetic examples. That zero-label review receipt remains preserved.

The lower red rows in 970.jpeg and numeric cells in 962.jpeg were withheld when proposed crops clipped or dirtied glyphs. Some other inspected sources contained crossed-out unit conversions or would overlap existing references. Their exclusion does not imply their entire pages contain no mathematics.

Source SHA, orientation, decoded dimensions, source-pixel SHA and exact crop-pixel SHA were checked. Different recorded pixel encodings are explicit: one pool uses size-prefixed source pixels and raw crop pixels; the other uses raw pixels with dimensions recorded separately. The trainer rechecks these declared fingerprints before fitting.

Original photos, crops, ZIP files and Parquet containers remain on Drive. Only metadata, helper code and private experimental artifacts were written locally.

## Cohort and selection

- Preserved all previous **494 records**, fields and ordering. Nothing was deleted or relabelled to obtain a better score.
- Selected **18 new TRAIN references** using a stable round-robin over source filenames and roles, before new model outputs. All 31 approved references use characters already in the frozen vocabulary; none was normalized into another glyph merely to fit a class.
- New selection by source: 453.jpeg four, 773.jpeg four, 926.jpeg four, 928.jpeg two, 960.jpeg four. This includes 16 expressions/comparisons and two numeric fields.
- The final bounded cohort contains **512 records: 412 TRAIN / 95 DEV / five reserved HOLDOUT**. All 95 DEV and five HOLDOUT records preserve their original fields/order.
- The remaining **13 reviewed references** stay in the separate pool with `training_eligible: false`; they were not used in this experiment.
- Existing TRAIN source groups and source SHA identities were preserved. New rectangles are in bounds and have zero overlap with previous or other new rectangles on the same source. No source/group crossed a current split.
- The 18 previously recovered supplied controls are accessible again but remain excluded from this declared page experiment. Source recovery does not imply a full-cohort evaluation or release pass.

Writer and pretraining independence remain unknown. Existing TRAIN pages are not described as unseen writers. The reserved source pixels were read for dataset validation; **no HOLDOUT neural inference or fitting occurred**.

## Experiment

The previous head and recurrent experiments did not improve critical mathematical transcription. This run isolated the last visual block: **only the final convolution and GroupNorm parameters were optimized**. The first three CNN blocks, BiLSTM and output head stayed frozen, and the vocabulary remained unchanged.

Frozen settings: four epochs, Adam learning rate `0.000005`, batch size four, four CPU threads, aspect-preserving inputs, prediction batches at most 16, math-role weight two, prose KL anchor weight one, no augmentation and no prose replay. The private parent checkpoint/vocabulary remain `4903062b…` / `dc25d2de…`; this is a development experiment, not a change to the installed model.

The baseline, same-input control and TRAIN prose teacher were computed from unchanged parent weights before fitting. The prose teacher is regularization, not a new label. Packed recurrent sequences exclude padding from their context. Original full literal transcripts were used for CTC.

Acceptance was frozen before fitting: fewer than 30 critical errors, at most 107 character errors, at least 53 exact lines and 64 critical-exact lines, and no role-specific regression on the same 95 DEV records.

## Results and decision

| Unchanged DEV metric | Same-input parent | Selected CNN-only candidate |
|---|---:|---:|
| Character errors / 1,097 reference characters | 107 | 113 |
| Character error rate | 9.75% | 10.30% |
| Critical digit/operator errors / 432 reference symbols | 30 | 35 |
| Exact transcripts / 95 | 53 | 51 |
| Critical-exact transcripts / 87 | 64 | 61 |

Epoch one was selected by the unchanged role-regression-first selection rule. Critical error counts across the four epochs were **35, 36, 35, 35**. The selected candidate regressed expression character/critical/exact metrics and prose character metrics. **It fails the frozen policy and is rejected.**

On the 18 new TRAIN references, critical errors stayed six and critical-exact transcripts stayed 13. Character errors rose from 17 to 19, and exact transcripts stayed seven. These are training measurements, not independent accuracy; they do not demonstrate successful learning of the added examples.

No checkpoint was installed, no service was deployed, and no Git commit/push occurred. Repeating these same epochs is not supported by the observed results. More diverse, carefully reviewed source data and a broader independent evaluation are needed before another release decision.

## Validation

- A real CTC gradient check verified gradients pass through the frozen decoder to the last CNN block. After an Adam update, early CNN, RNN and head tensors remain identical while the last convolution changes.
- CNN-only mode rejects replacement numeric heads or new vocabulary classes. Resume checks both current and best states against frozen parent visual/decoder tensors before loading; candidate emission rechecks frozen tensors.
- All four epochs completed. Atomic model/optimizer/best-state/history/RNG checkpoints were saved and a hidden launcher confirmed paired candidate, vocabulary and evaluation hashes before reporting completion. A full process-interruption/resume simulation was not performed in this phase.
- Final source receipt records **78 hash-verified reads of 69 unique Drive originals**, zero retries, unchanged input fingerprints, zero cloud inference calls and zero original-image writes.
- An independent read-only audit reproduced source/role selection, verified all old records/splits, recomputed all TRAIN and DEV literal metrics, and confirmed the rejection.
- The final candidate exactly matches its recorded best state. Only `cnn.12.weight`, `cnn.12.bias`, `cnn.13.weight` and `cnn.13.bias` changed; current and best early-CNN/RNN/head tensors exactly match the parent.
- Manifest, reference, trainer, policy, input, job-status and model/vocabulary fingerprints match. Installed checkpoint/vocabulary remain `a807eaa7…` / `6af4062e…`. No phase Python process remains active, and `git diff --check` passed.

Manual crops and repeatedly reused DEV data do not establish automatic page segmentation, 2-D fraction/long-division accuracy, or independent application accuracy. The five reserved fields come from only one page.

## Evidence

Private root: `ai-training/datasets/drive_math/math_all_20261013/math_more_20261013/`.

- `labels_a/reviewed_references.json`: preserved zero-math literacy review.
- `labels_a/math_references.json`, `labels_b/references.json`, `parent_review.json`: 31 literal references and parent exact-crop approval.
- `prepare.py`, `preparation_receipt.json`, `reviewed_manifest.json`: stable selection, 13 deferred IDs and unchanged old cohort.
- `acceptance_policy.json`, `trainer_cnn_only.py`, `run_train.py`, `test_cnn_only.py`: frozen settings, focused experiment and gradient/frozen-parameter validation.
- `run_cnn_only/evaluation.json`, `comparison_decision.json`, `compare.py`: literal measurements, reproducible checks and rejection.
- `run_cnn_only_training_state.pth`, `train.log`, `job_status.json`, `read_receipt.json`: complete training history, durable state and source/input verification.

Manifest SHA256: `1ff8ff8f57c0b7d51f4b962fc05d69ab45ca7c2ceea10d352ca2b099338adc74`.

Candidate SHA256: `15b28aa6e1212304598a968b18fa59a3f7006ce777bfae37ca39fd2626bfa2cc`.

Evaluation SHA256: `9c247044a2799f2898878dd422d80c555afe9f4a50e4d7f78bb0d7fb7eb57c99`.
