# Math OCR: table geometry, numeric fields and private head experiment

Date: 2026-10-13. Owner request: continue mathematical recognition/training using original images on Drive only.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: implement the smallest bounded OCR experiment using installed OpenCV/PyTorch and existing source/decoder helpers.
  - Applied to: private grid geometry, explicit numeric-field spacing guard, source-only validation, frozen head training and checkpoint audit.

## Result and release decision

**The candidate is rejected. The production model and vocabulary are unchanged.**

- Table `960.jpeg`: original source reviewed in RAM, 15 complete numeric cells separated, unchanged private parent recognizes 14 exactly. One literal `5` is still recognized as `3`.
- Added 50 unique, source-reviewed TRAIN crops: 37 previously verified fields/expressions plus 13 table cells. Two table crops overlap already-reviewed `32`/`18` fields and were excluded from additions.
- Trained the linear CTC head for four epochs on 462 TRAIN crops with 95 unchanged DEV crops. CNN and BiLSTM remain byte-identical to the private parent checkpoint.
- Selected epoch 1 improves the new TRAIN cohort from 43/50 to 45/50 exact, but DEV critical errors increase 30 → 31. It loses one zero in `300 cm² = 3 dm²`, producing `30 cm² = 3 dm²`. This is unacceptable for student arithmetic.
- No HOLDOUT pixels were read, no production promotion or deployment was performed, and no Git commit/push was made.

All new implementations and checkpoints are private experiment artifacts under:

`E:/MathVisionKid/ai-training/datasets/drive_math/math_all_20261013/math_layout_retry_20261013/`

## Geometry and source review

### Table

Source SHA-256: `8d9ca4466bf864ccb109520d65b6335e15b9987e7e7a963b67f4a5646ff72b9b`; oriented size 1536 × 2048. Manually declared ROI: `[470,805,925,1085]`.

The prototype detects long blue grid rulings, checks line support across the proposed grid, and returns cell polygons. It retains real source context around each cell, including ruling lines and glyphs that touch them. Grid removal, digit reconstruction and arithmetic inference are not used.

The original probabilistic Hough version missed upper horizontal separators in a mildly perspective-distorted synthetic grid. Version 3 uses complete-line Hough voting with the same span/support checks. Tests now pass on straight and mildly perspective-distorted 3 × 5 grids. Isolated fractions, neutral notebook grids, blank images and invalid ROIs are rejected. Input pixels are unchanged.

This is **a colored-grid prototype within a manually reviewed ROI**, not an automatic table finder for every notebook page. The 15 literal cell references were saved before this phase's table OCR run. Source and exact cell patches were visually inspected in RAM. Recognizer scores were not used to select label values.

### Side-by-side expressions

The first conservative grayscale-gap prototype proposed zero splits across 273 regions on nine existing TRAIN pages. A subsequent geometry-only chromatic corridor prototype proposed one split, on `453.jpeg`:

- original seed: `[1623,263,2531,376]`;
- source SHA-256: `838c2fd9db4061493767ca60f31c13ad95fd915a574b3f088569cb104a2fe1a0`;
- original orientation review: 270° clockwise, oriented size 2880 × 2160.

The teacher's central red mark caused learned text fragments to merge across two expressions. The proposed full-height partitions retain every original pixel, but still include red annotations and clipped strokes from the next row. OCR on those partitions is not reliable: the right expression is misread. Both partitions remain **unscored and ineligible for training**. They are not production replacements.

## Numeric-field formatting

`numeric_field_format.py` compacts only ASCII digit strings containing horizontal spaces, tabs, NBSP or narrow NBSP, and only after explicit verification that the region contains one numeric field. Leading zeroes remain. Unverified rows, stacked fractions, newlines, signs, operators, decimal separators and prose are unchanged.

Replaying 37 already saved predictions against the corrected source-reviewed references fixes six spacing-only strings, for example `32 6` → `326`. Exact replay matches increase 31 → 37; critical digit/operator errors are zero both before and after formatting. This is **post hoc formatting on manually verified fields**, not new neural inference or independent model accuracy. The earlier `60 : 6 = 16` literal-reference correction remains separately documented; the mathematically wrong student result is preserved.

The formatter is private and has not been applied to unverified page OCR or integrated into the application.

## Training policy and evidence

Frozen settings: four epochs, seed 1729, Adam learning rate 0.00001, batch size 8, four CPU threads, linear CTC head only, doubled math CTC weighting, TRAIN prose anchoring against the parent, no augmentation.

Input features are computed from hash-checked original Drive bytes in RAM. All 557 evaluated/training crops came from 68 existing source pages. Page source groups and source hashes remain disjoint between TRAIN and DEV. HOLDOUT sources are excluded before reading pixels. The old 507 TRAIN/DEV reference crops remain unchanged.

| Evaluation | Private parent | Selected candidate |
|---|---:|---:|
| DEV character errors / 1,097 characters | 107 | 106 |
| DEV critical errors / 432 digits/operators | 30 | 31 |
| DEV exact crops / 95 | 53 | 52 |
| DEV critical exact crops / 87 | 64 | 63 |
| New TRAIN exact crops / 50 | 43 | 45 |
| New TRAIN critical errors / 98 digits/operators | 1 | 1 |

Later epochs have 108 character errors and 33 critical errors. The frozen acceptance criteria require at most 29 DEV critical errors, at least 53 exact crops, at least 64 critical exact crops and no per-role regression. No epoch passes.

A fresh checkpoint audit re-read the 95 DEV crops from 15 source pages and reproduced all selected-epoch metrics. Only `fc.weight` and `fc.bias` differ from the private parent. Checkpoint tensors are finite, input pins match and no production files changed.

The first preparation attempt stopped before optimization because it compared orientation review dictionaries directly: some records explicitly describe 0° while older records omit the optional review. The replacement version compares the existing validated rotation values and verifies the exact reviewed source/crop pixels. Original script/policy evidence was retained; references were not changed.

## Artifacts and reproducible checks

- Geometry: `tables/table_cells_v3.py`, `review_layout.py`, `reviewed_geometry_v3.json`.
- Geometry fixture check: `tables/check_table_cells_v3.py`.
- Numeric guard/replay: `numeric_field_format.py`, `evaluate_field_format.py`, `field_format_evaluation.json`.
- Table/column inference: `layout_ocr_policy.json`, `layout_ocr_evaluation.json`.
- Frozen training and result: `head_training_policy_v2.json`, `train_reviewed_head_v2.py`, `head_training_result_v2.json`.
- Private rejected checkpoint: `head_candidate_private_v2.pth`.
- Checkpoint/DEV verification: `audit_candidate.py`, `candidate_audit.json`.
- Remaining issues: `remaining_review_queue.json`.

Runnable geometry check: Python runtime `E:/MathVisionKid/ai/runtime/.venv/Scripts/python.exe`, with `PYTHONPATH=E:/MathVisionKid/ai/runtime`, executing `tables/check_table_cells_v3.py`. Numeric guard checks run by executing `numeric_field_format.py`.

Private candidate SHA-256: `b30b53ee4e258a82c6b7ab76f36eeb2876a6343eaf8d115f4635f093aaa7ca6c`.

Unchanged production weights SHA-256: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.

Unchanged production vocabulary SHA-256: `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.

## Limits and next work

- Keep the `5`/`3` confusion and annotation/row-boundary problems in the source review queue.
- New TRAIN scores are fitted-sample evidence. DEV has been used repeatedly; neither establishes independent accuracy. Writer/pretraining independence is unknown.
- Automatic arbitrary 2D mathematics recognition and full production replacement remain unproven.
- No original photos, crops, ZIP or Parquet files were saved locally. The deliberately deleted `all_retry_20261012/containers` and `pages_originals` directories remain absent.
- No paid services, cloud calls, physical-device tests or UI changes occurred in this phase.
- `git diff --check` passed. Existing unrelated checkout edits were preserved.

This bounded phase is complete. The candidate remains private and rejected; the verified additions and failure evidence are available for the next experiment.
