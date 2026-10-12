# New images, complete inventory reconciliation and controlled OCR adaptation

Date: 2026-10-12. The owner explicitly authorized continued training and recognition of all images. This phase processes the new 24 images and preserves the previously completed corpus rather than counting a second pass as additional images.

## Source and label integrity

- Live Google Drive metadata census: **1,021 images in NEW2/IMG**, across three provider pages. New files are **998.jpeg–1021.jpeg**. All 24 original-byte hashes match the upload receipt and are distinct from the previously processed 64,779-image snapshot.
- The combined known source inventory has **64,803 unique original-byte hashes**. NEW2 membership was reconciled with canonical sources and recorded aliases. The fresh census covers NEW2; the other archives remain the previous recorded source snapshot. Metadata membership is not a fresh checksum validation of every remote image.
- Reusing filenames in `Pictures/xyz` had removed or replaced original files needed for existing reviewed references. **35 exact originals were restored through authenticated Drive downloads**, verified against their frozen SHA-256, and bound only in the new manifest. No historical manifest, reference or production model was rewritten. Together with the new 24 originals, retained source bytes occupy about **26.77 MB**.
- Whole sources and individual crops were inspected. Of **44 proposed regions, 25 were accepted and 19 excluded** for clipping, neighboring-row ink, ambiguity or changed fragment boundaries. These are line/phrase/field references, not full-page transcripts. New references: **13 TRAIN / 7 DEV / 5 HOLDOUT** on eight source pages.
- The previous scored 22-reference HOLDOUT is explicitly exposed development data and becomes TRAIN only in the new manifest. Final cohort: **493 references — 427 TRAIN / 61 DEV / 5 fresh HOLDOUT**. Source hashes, page groups, decoded page pixels, crop pixels and bounds passed the existing leakage checks. Writer independence and original pretraining exposure remain unknown.
- The new HOLDOUT covers two pages, only five short references, and is insufficient to certify general OCR accuracy. Its references were reserved before fitting; no HOLDOUT neural inference influenced checkpoint selection.
- Unverified detector/CRNN outputs, raw model scores and supplied archive transcripts never become training labels.

Private manifest SHA-256: `ec67b9a5b827737cbc7545b489669e4f732aabd098c05ee61f8e2705d5aff524`.

## Controlled training and verification

Two bounded **30-epoch** CPU experiments completed. Both start from the unchanged original CRNN, preserve image aspect ratio at height 64/maximum width 1024, use batch size 4, two threads, learning rate 0.0001, TRAIN-only multiplication initialization, TRAIN prose anchoring weight 2 and deferred HOLDOUT. The first adapts the last CNN block, BiLSTM and CTC head; the second freezes the CNN and adapts the BiLSTM/head. Seeds: 20261016 and 20261017.

The trainer now records the original weights with the candidate input policy as a **preprocessing control**. DEV checkpoint selection and frozen evaluation compare prose/math roles against that control as well as the original production input. This prevents a resize gain from hiding poorer fitted weights. Tests cover aggregate and prose regressions against this control; the real completed runs also record and compare it.

On the same **61 DEV references / 1,126 reference characters**:

| Model/input | Character errors | CER | Exact references | Critical edits |
|---|---:|---:|---:|---:|
| Original weights, production input | 318 | 28.24% | 4 | 133 |
| Original weights, candidate input | 233 | 20.69% | 8 | 63 |
| Prior broader candidate | 66 | 5.86% | 38 | 15 |
| Prior short-prose candidate | 67 | 5.95% | 37 | 13 |
| New visual candidate, selected epoch 23 | 63 | 5.60% | 38 | 12 |
| New recurrent candidate, selected epoch 14 | 69 | 6.13% | 38 | 15 |

The chosen pair was frozen using DEV only before final HOLDOUT evaluation. Candidate SHA-256: `95577af07d1f2365b1172ff49d96cbb8e5beaf6bc3496831a0272d35a4033e80`; vocabulary SHA-256: `dc25d2de8fe00fb680b8a18c0abac8e4df0e4ec54aa71e5dcde1ec253814a9fd`.

On the **five fresh HOLDOUT references / 70 characters**, the selected candidate has **13 character errors (18.57% CER), one exact reference and three critical edits**. The same-input original control has 23 character errors and seven critical edits; the native original has 28 and eleven. The candidate nevertheless regresses on HOLDOUT prose against the same-input control and fails the existing 5% CER/zero-critical-error release requirements.

**Production is retained.** This is a measurable development improvement with a failed release gate, not a perfect model or a general accuracy percentage. No fitting or reselection follows final HOLDOUT inspection in this phase.

For example, the candidate reads `300 cm² = 3 dm²` exactly, but reads `600 cm² = 6 dm²` as `600 cm² = 6án2` and `mỉm cười dưới nắng.` as `mỉm cưới dưởi nắng.`. These expose unit/superscript and Vietnamese accent errors rather than an execution failure. CER is a character error measure, not the percentage of photos correctly read.

## Recognition completion

All 24 new images completed segmentation and recognition with zero execution failures: **653 detected regions, 608 nonempty drafts and 45 empty drafts** using the frozen previous broader checkpoint. The two held-out pages were recognized only after selection was frozen. A separate experimental pass uses the newly selected candidate; it is not counted as more images and is not installed in production.

The authoritative reconciliation preserves the historical 64,779-image outputs and adds the new 24 once: **64,803 images, 101,797 detected/supplied regions, 95,063 nonempty drafts and 6,734 empty drafts**. JSONL records match SQLite, summaries and source hashes; scores are finite and bounded; boxes are integer and in bounds; all prediction/reference/training flags remain false. Execution success and nonempty text do not demonstrate correct recognition or complete detection.

Private evidence: `ai-training/datasets/drive_math/new2_20261012_24/`, including the Drive census, receipt/source bindings, review decisions, preflight, code snapshot, experiment plan, both candidates, frozen selection, final evaluation, per-image results and CSV drafts. Historical outputs and model pairs remain intact.

Verification: **160 tests passed**; real training/frozen-evaluation and recognition jobs finished successfully; output/source reconciliation passed; **30 protected historical/production/source files** remained byte-identical; the eight-file code snapshot matches the completed runs. No source deletion, paid service, application deployment, commit or push occurred.

## Remaining limits

Critical numeral/operator mistakes, Vietnamese accents, long skewed lines, merged columns, grid marks, stacked fractions and long division remain release concerns. The fresh references are purposely few and clear, while many difficult crops were excluded. More manually checked, writer-aware evaluation data and layout work are needed before replacing production. Additional fitting on automatic guesses would not resolve these evidence gaps.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal changes to existing training/evaluation safeguards.
  - Applied to: Same-input control, DEV selection, release gating, existing runner reuse and regression tests; no new runtime dependency or application change.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.20/skills/google-drive/SKILL.md`
  - Why selected: Ground the live NEW2 inventory and restore original reviewed sources.
  - Applied to: Paginated metadata census, observed file IDs, authenticated original-byte downloads and SHA-256 checks.
