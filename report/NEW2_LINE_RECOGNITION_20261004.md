# NEW2: full-source line-region audit

Date: 2026-10-04. Owner scope: use every image in NEW2, improve the app's line
detection, and investigate failures. No training, commit, push or physical-device
test was performed in this run.

## Result and limits

NEW2 contains one IMG subfolder with **100 original files**. The public Drive
listing was inspected to its final entry (100.jpeg); its 100 identities match the
already downloaded NEW2 originals in the previous 500-file batch. This run uses
those same original bytes, not the 400 archive crops and not 100 additional images.

The final local production segmentation function completed **100/100**, with
**zero execution failures**, **100 nonempty outputs**, and **zero out-of-bounds
rectangles**. Audit limit: 200 candidate regions per page. Measured local geometry
p95: **419.75 ms** on this computer; excludes HTTP, uploads, transcription and
tutoring. Three landscape sources (30.webp, 33.webp, 61.jpeg) retain the established
classical path; the 97 portrait sources use the optional learned detector.

This establishes execution and coordinate validity, **not 100% accurate rows or
transcription**. All 100 annotation records remain `needs_review`. No complete
geometry or text reference was created from a prediction. Contact-sheet triage
covered all 100 sources, with selected full-size inspections. It found merged or
overlapping candidates, multi-column arithmetic, table cells, overwritten words,
background book titles/footer logos, faint text, and pages containing other school
subjects. The review flags are a triage list, not a measured error rate.

**The owner's target of no incorrectly recognized image has not been achieved.**

## Production changes

- Added a pinned OpenCV PP-OCRv3 text-region detector. Its model is installed
  locally, checksum-verified before loading, and never downloaded during a student
  request. Missing/corrupt weights fall back to the established segmentation path.
  This is an existing pretrained detector, not a model trained on NEW2.
- Preserve aspect ratio, pad model input to multiples of 32, and inverse-map with
  separate width/height scale factors. Output is bounded by original image pixels.
- Merge adjacent word fragments on a shared baseline while retaining distant
  columns. Avoid merging neighbouring tall arithmetic regions into one column.
- Split tall coloured-writing regions at strong blank gaps; a detected fraction
  bar protects the expression. Neutral/faint/touching writing remains unresolved.
- When first-pass regions are predominantly vertical, compare a quarter-turn
  pass using long horizontal text evidence. Map accepted regions back to original
  coordinates. Images 59 and 63 benefit from this; upright versus upside-down
  reading direction is not independently verified by this detector.
- Include the requested region limit and model artifact timestamp in cache keys.
- The notebook-reading flow can use learned-region disagreement to request its
  existing independent transcription check when coloured rows are absent. Learned
  boxes are **not** attached to transcript rows merely because counts match.
  This check does not automatically add missing transcript rows.

The old generalized audit had 99/100 nonempty NEW2 outputs; the conservative
coloured detector had 59/100. Photo 64 had no generalized output; the new path
finds text/arithmetic candidates there. These comparisons are development
observations, not a held-out accuracy result. Prediction counts alone do not prove
better reading or correct grouping of mathematical operations.

The legacy OCR HTTP path still caps returned candidates at **30**; **55** of these
full pages produce more than 30 candidates in this audit. Its per-line CRNN/cloud
advisors make raising that cap a separate latency/cost decision. The student flow
continues to request one problem when a page contains multiple exercises. The
200-region audit does not establish uncapped end-to-end app recognition.

## Cloud transcription evidence

The actual notebook-reading function returned responses for **13 unique sources**:
9 `MULTIPLE`, 3 `WORK`, 1 `MIXED`. Multiple-problem responses are application
classification outcomes, not verified text readings. Photo 8's saved reading
omits visible arithmetic; it is not an accepted label.

The first run stopped after 12 responses on provider unavailability. One bounded
resume after cooldown read photo 13, then stopped at photo 14: the primary provider
returned a rate limit; the fallback had a server error in the first run and a
timeout/malformed-response failure in the resume. **87 sources remain pending for
cloud reading.** Preserve both run signatures: 12 responses precede the notebook
verification change, and one follows it. Do not present them as 100 final-version
successful OCR calls. No credentials are included in the evidence or report.

## Verification

- **97 targeted tests passed**, with four existing framework deprecation warnings.
  Includes optional-artifact failure, source-coordinate scaling, quarter-turn
  inverse mapping, rotation rejection for vertical arithmetic, fragment merging,
  fraction preservation, cache limits, notebook tutoring and batch contracts.
- On the previous batch's **23 count references**, the actual current local path
  still matches **21** counts. Reference labels remain unchanged. This check is
  limited to row counts and does not establish geometric/transcription equivalence.
- The final 100-image audit records hashes of the exact detector/pipeline/row code
  and model. `git diff --check` passed. The setup command recognizes the installed
  verified artifact. Photographs and model weights remain ignored by Git.
- No active AI service was restarted. Load these changes on the next normal
  project launch. No phone behavior or live HTTP end-to-end evidence is claimed.

## Provenance and private artifacts

- Source folder: `https://drive.google.com/drive/folders/1Vd6rxTxlSkx0M3Q36Lc3OB6LsTeM7g2t`
- Private root: `ai-training/datasets/drive_math/new2_20261004/`.
- `source_selection.json`, `images/`: frozen identities and immutable originals.
- `local_regions/`, `local_overlays/`, `local_summary.json`, `local_manifest.csv`:
  final measured candidates, overlays and hashes.
- `before_stacked_split/`, `before_orientation/`: earlier run evidence.
- `review_sheets/`, `visual_review_queue.json`, `labels/`: visual triage and
  unverified drafts tied to source SHA-256; none is eligible for training.
- `reference_regression.json`, `example_comparison.json`: comparison evidence.
- `cloud_results/`, `remaining_cloud/`, `cloud_combined_summary.json`: separate
  resumable cloud evidence with provenance.
- All 100 source IDs were already marked tested in the exclusion ledger. It still
  contains **704** source entries; reruns were not counted as new images. Nothing
  was deleted, renamed or marked in Drive itself.

Model: `text_detection_cn_ppocrv3_2023may.onnx`, 2,423,490 bytes, Apache-2.0,
official OpenCV Zoo revision `d4938dfc9d4ec5d098bfa33e98b3f3345a236586`.
SHA-256: `03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587`.
Download/provenance is stored in `ai/runtime/models/ocr/text_detector_manifest.json`;
the accompanying license is `ai/runtime/app/recognition/TEXT_DETECTOR_LICENSE.txt`.
No dependency installation or model training was needed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded OCR integration and regression checks using existing tools.
  - Applied to: optional detector, fallback, cache, audit CLI and checks.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.930.31730/skills/computer-use/SKILL.md`
  - Why selected: verify the owner's public Drive inventory when no connector was callable.
  - Applied to: read-only NEW2/IMG browser listing and source identity verification.
