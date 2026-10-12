# OCR: reviewed orientation and separate notebook columns — 2026-10-12

Fixed a concrete segmentation failure and deployed it to the existing AI/worker
services. Original images remain on Drive. This phase improves crop geometry;
it does **not** certify that all OCR text is correct or promote new model weights.

## Results

| Check | Result |
|---|---:|
| Visually reviewed suspected sideways pages | 86 |
| Confirmed sideways; rotated only in RAM | 79 |
| Upright controls kept unchanged | 7 |
| Additional original landscape pages checked | 160 |
| Landscape pages retaining identical boxes | 143 |
| Images with repaired separate-column geometry | 30 + 17 |
| Final images read with the frozen candidate | 103 |
| Final regions read | 3,520 |
| Nonempty drafts, **not verified references** | 3,289 |
| Detection / inference execution failures | 0 |
| Runtime/data regression checks in the final two suites | 257 + 29 passed |
| Source image/archive copies written | 0 |
| Model training / weight promotion | None |

The 246 geometry audits are targeted samples from the previously scanned
inventory. They are not a fresh full-corpus rerun or a random accuracy sample.
The 103 final inference images comprise the 86 reviewed pages and 17 other
landscape images whose boxes changed. Earlier whole-corpus outputs remain intact.

## What changed

- Added `scripts/data/source_orientation.py`: apply EXIF once, then an explicit,
  source-hash-bound visual direction review. Detection, draft recognition and
  reviewed-label loading share that transformation. Original bytes are untouched.
- Changed direction or reviewer metadata invalidates cached geometry/text, even
  for 90/270-degree rotations with equal dimensions. Rotated geometry pins the
  preprocessing code. Frozen training/evaluation records pin it as well.
- Fixed `generalized_pipeline.py`: on large landscape images with repeated
  projection rows spanning most of the width, independent learned evidence of
  separated left/right columns replaces the fused rows. Small exercise crops,
  single columns and unsupported cases retain the established path. Limits,
  cache keys and the unverified/review-required status are preserved.
- Updated the corpus guide with the reviewed-direction workflow and removed
  the obsolete suggestion to create a local archive cache.

For `241.jpeg`, the previous oriented pass returned 20 regions, including 13
that crossed the central image band. The repaired pass returned 56 separated
regions and zero such crossings. On the 30 changed orientation samples, the
same structural diagnostic decreased from 536 to 3. These are geometry
diagnostics, **not CER, true line counts, or accuracy percentages**. The three
remaining crossings stay in the private review queue; their boxes are not cut
automatically without checking the actual writing.

All 17 changed original landscape images were visually inspected. They contain
separate notebook pages or independent columns, including a single-page sheet
with two arithmetic columns. The other 143 retained their prior coordinates.

## Rejected experiment and remaining limits

A pinned PP-OCR direction classifier was tested privately through installed
OpenCV. Its high scores could still suggest a wrong orientation for upright
arithmetic. It was **not** added to runtime or used to decide the 79 rotations.
The model/source configuration comes from the
[RapidOCR model registry](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/default_models.yaml).

Final offline drafts use the frozen experimental pair `95577af0…` / `dc25d2de…`;
that pair remains private. Live production still uses `a807eaa7…` / `6af4062e…`.
No fitting occurred, and previously failed quality gates were not relaxed.

OCR still needs verified character and digit/operator references, particularly
for clipped writing, poor lighting, fractions and two-dimensional arithmetic.
More regions or nonempty text do not prove improvement in transcription. The
new drafts carry false reference/training eligibility flags and a context-aware
review queue; they cannot be fed back as trusted labels.

## Deployment and verification

- Built the existing AI image and recreated only AI/worker; both became healthy.
- Live code/model hashes match the workspace and unchanged production weights.
- Actual Drive originals were passed to direct container checks through stdin,
  in RAM. The reviewed rotation of `241.jpeg` uses `PPOCR_COLUMN_REGIONS` with
  zero central crossings; the sparse-writing recovery for `828.jpeg` still passes.
- The internal OCR HTTP route passes a synthetic-image check. Public login and
  backend student-role checks pass through all three existing web deployments.
- Rollback: `mathvision-ai:rollback-orientation-20261012`.
- Physical-device testing was not performed. Hosting remains dependent on the
  user's running PC; this phase does not provide an always-online cloud backend.
- No Git commit/push or unrelated project edits were made in this phase.

## Evidence

Private metadata and outputs under
`ai-training/datasets/drive_math/orientation_20261012/`:

- `direction_review.json`, `orientation_reconciliation.json`;
- `column_recovery/recognition/`, `landscape_changed_17/recognition/`;
- `landscape_comparison.json`, `review_queue.jsonl`;
- `final_reconciliation.json`, `storage_receipt.json`;
- `column_tests.log`, `endpoint_tests.log`, `deployment_smoke.json`;
- `pre_column_snapshot/`, `final_code_snapshot/` for historical traceability.

The global source index is unchanged, the deliberately deleted local photo and
archive-cache folders are still absent, and no image contact sheets were saved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: shared OCR/data-flow bug fixes with minimal dependencies.
  - Applied to: native PIL rotation, bounded column evidence, shared preprocessing,
    cache/provenance validation, regression tests and deployment verification.
