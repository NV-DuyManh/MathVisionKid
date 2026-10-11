# NEW2: 266-image line OCR and reviewed CRNN adaptation

Date: 2026-10-11. Scope: the owner's explicit request to continue training and recognize the newly uploaded images line by line.

## Outcome

Completed local OCR for all **266 images, numbered 732–997**, with **0 execution failures**. The detector produced **6,164 regions**; the unchanged production CRNN returned **4,831 nonempty drafts** and **1,333 empty drafts**. These are detected regions, including individual characters, headings and other marks; neither a successful run nor a nonempty transcript proves complete or correct line recognition.

Completed two bounded **24-epoch** adaptation experiments. The selected experimental checkpoint improved character error rate on the small, manually reviewed HOLDOUT from **27.92% to 7.92%**, but failed the release gate. **Production weights were retained.** No paid service, cloud OCR call, application deployment, commit or push was performed.

## Sources and label review

- Upload receipt: `C:/Users/Admin/OneDrive/Pictures/xyz-upload-NEW2-20261011.csv`.
- Originals: `C:/Users/Admin/OneDrive/Pictures/xyz`; original names and bytes preserved.
- Private batch: `ai-training/datasets/drive_math/new2_20261011_266/`.
- All 266 sources verified against their receipt SHA-256 values. There are **238 distinct byte hashes**, so 28 entries repeat another source's bytes. No new byte hash matched the previously available source-selection manifests; this does not rule out earlier captures of the same page or exposure during original model training.
- **57 new line references** were visually reviewed against both originals and crops on six pages. Boundaries were corrected manually where automatic detection split expressions or clipped glyphs. Four preliminary crops/references were excluded before fitting/evaluation because of neighboring text, clipped content or reading uncertainty.
- New references: **17 TRAIN / 25 DEV / 15 HOLDOUT**. Added **87 previously verified TRAIN references**; previous DEV/HOLDOUT references were excluded. Final cohort: **104 TRAIN / 25 DEV / 15 HOLDOUT**.
- New source pages: TRAIN 740/743; DEV 748/937; HOLDOUT 749/946. The existing trainer checked source groups, source hashes, page pixels and crop pixels for cross-split leakage.
- OCR drafts remain in `crnn_results/` and `line_predictions.csv`, explicitly unverified and ineligible for training. Whole-image `labels/` remain `needs_review`; reviewing a few lines does not approve an entire photo. Accepted references are separate in `training/new_reviewed_manifest.json`.

The reviewed cohort is purposive and small. Writer independence and near-duplicate exposure are unknown. It does not establish recognition accuracy for all 266 photos. Two-dimensional fractions, long division, crossed-out corrections and ambiguous content were not guessed into line references.

## Training and frozen evaluation

Both experiments started from the same unchanged production CRNN, froze its CNN and adapted the BiLSTM/CTC head on CPU. Batch size 4, two threads, learning rate 0.0003, seed 20261011. No training labels came from automatic predictions.

| Experiment | Input policy | Selected epoch | DEV CER | DEV critical edits |
|---|---|---:|---:|---:|
| Production baseline | Fixed 64×1024 | — | 22.93% | 46 |
| run01 | Fixed 64×1024 | 4/24 | 17.47% | 23 |
| run02 | Preserve aspect ratio; bounded width | 23/24 | 9.17% | 16 |

Run02 was added after DEV showed remaining expression errors. Neither experiment inferred on the labeled HOLDOUT through the trainer during development. The checkpoint was selected by DEV critical edits, then DEV CER, and frozen before one final HOLDOUT evaluation. This HOLDOUT is now exposed and must not be described as fresh after further tuning.

| Frozen evaluation | Baseline | Selected candidate |
|---|---:|---:|
| HOLDOUT literal CER, 15 lines / 265 characters | 27.92% | 7.92% |
| HOLDOUT exact lines | 2/15 | 5/15 |
| HOLDOUT math-expression CER, 10 lines | 69.00% | 8.00% |
| Math-expression digit/operator edit errors | 31 | 3 |
| HOLDOUT prose CER, 5 lines | 3.03% | 7.88% |
| DEV exact lines | 3/25 | 2/25 |

Literal CER includes transcript spacing and punctuation. The separate critical metric retains digits, mathematical operators and selected punctuation; its overall HOLDOUT count of five comprises three math-expression edits and two prose punctuation edits. Raw CRNN softmax scores are not measured accuracy.

The gate failed because DEV exact-line recognition regressed, HOLDOUT CER exceeded 5%, and critical errors remained. Prose also regressed. Both checkpoints and their paired vocabularies are private experimental artifacts; no candidate was installed or deployed, and no further tuning used the exposed HOLDOUT.

## Reusable recognition and verification

Added `scripts/data/recognize_line_batch.py`, reusing the existing source loader, production recognizer and atomic JSON writer. It reads at most four crops at a time, validates immutable source bytes and region bounds, and resumes only when source/model/vocabulary/provider/region hashes match. It never changes a reference label or repairs an arithmetic answer. Per-image failures are reported and cause a nonzero CLI exit.

Artifacts in the private batch:

- `line_predictions.csv`: all 6,164 drafts with image name, region number, source coordinates and raw score.
- `local_overlays/`: numbered region previews for source comparison.
- `training/reviewed_line_index.csv`: the 57 reviewed references and split assignments.
- `training/run01/`, `training/run02/`: checkpoint/vocabulary pairs, immutable manifest/trainer snapshots and DEV histories.
- `training/selected_candidate.json`, `training/final_evaluation/evaluation.json`, `training/decision.json`: selection, frozen measurements and non-promotion decision.
- `completion_validation.json`: final source integrity, region/result alignment and resume checks.
- `README.md`: source mappings, artifact explanations and recognition resume command.

Validation: **29 tests passed**, covering source storage, training leakage/integrity guards and the new recognition runner. The new test checks hash-based reuse, box-change invalidation, changed-source rejection and preservation of existing approved labels—even when a model draft contains wrong arithmetic. Integration verification checks all 266 result records and source hashes, all 6,164 CSV rows, coordinate alignment and a complete resume with a provider that rejects any new neural inference. Production checkpoint and vocabulary SHA-256 values remain unchanged. Photos, transcripts and checkpoint artifacts are Git-ignored; unrelated cloud-deployment work was preserved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: extend the existing data/training pipeline with a minimal reusable batch runner.
  - Applied to: source-loader and CRNN reuse, resumable inference, focused integrity testing and bounded experiments without new dependencies or application changes.
