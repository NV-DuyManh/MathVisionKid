# OCR stroke integrity and deployment — 2026-10-12

Fixed a real segmentation failure: saturated-ink projection sometimes sliced
one handwritten digit into thin strips, losing faint connecting strokes.
The final fix is deployed to AI/worker and preserves the previous column
recovery. Original photos remain on Drive; no source photos or archives were
saved locally. Recognition remains imperfect; this is not an accuracy release.

## Completed checks

| Evidence | Result |
|---|---:|
| Final geometry audit, including earlier landscape controls | 246 images |
| Successful source reads/detection | 246 |
| Geometry changed / unchanged relative to prior phase | 40 / 206 |
| Total regions before / after, within these 246 images | 4,955 / 4,904 |
| Changed images recognized again with frozen experimental pair | 40 |
| Regions recognized in that final pass | 1,988 |
| Nonempty unverified drafts | 1,886 |
| Final detection/inference execution failures | 0 |
| Final regression suites | 273 + 29 passed |
| Source image/archive files written | 0 |
| New fitting / production weight promotion | None |

This was a targeted follow-up to the existing whole-corpus audit. It did not
rerun all 64,803 images or verify every transcription. The 102 empty drafts and
591 layout flags in the final inference pass remain review candidates.
These flags are not verified errors or a measured accuracy percentage.

## Runtime changes

`text_detector.split_stacked_writing` now checks weaker original ink before
accepting a cut proposed by strong-ink projection:

- A complete stroke crossing two proposed bands vetoes the cut.
- A faint tail belonging to one band extends that band; neighbouring crops have
  bounded padding to avoid duplicating adjoining ink.
- Fractions with a faint bar remain an expression instead of separate tiers.
- Long notebook rulings are removed from the **guard mask only**. OCR pixels
  are unchanged, as confirmed in the live real-source check.
- Wide ambiguous regions retain the established result. A wider permissive
  variant was rejected after inspecting prose and neighbouring rows.

An integration smoke found a regression in `241.jpeg`: repairing arithmetic
strokes removed tiny fragments that had accidentally supplied the column
detector's baseline-pair evidence. The first deployed attempt was rolled back.
The final column check also accepts repeated substantial rows with a stable
central gutter and overlapping vertical spans, even when the columns' baselines
are offset. Short exercise crops and unsupported layouts retain their path.
The detection cache version is `text-regions-v17`.

The final real-source container check finds 55 separated regions in the reviewed
rotation of `241.jpeg`, zero central crossings, and `PPOCR_COLUMN_REGIONS`.
The `453.jpeg` digit region `(2475,951,2547,1015)` remains one complete region.
Sparse-writing recovery for `828.jpeg` also passes.

## Direct transcription comparison and limits

Twelve clearly visible numeric/arithmetic parent regions on two photos were
visually transcribed in RAM and frozen before neural comparison. References
remain private, have false training eligibility, and are targeted development
evidence rather than an independent accuracy sample.

Using the **same production weights and input resize**:

| Metric on those 12 targeted parent regions | Old split crops | Final repaired crops |
|---|---:|---:|
| Character errors / 80 reference characters | 136 | 35 |
| Digit/operator/grouping errors / 78 reference characters | 75 | 34 |
| Exact full transcriptions | 0 | 0 |

Old subcrop drafts were concatenated in their stored order to compare with the
complete parent reference. Insertions can make CER exceed 100%. This comparison
shows reduced damage from slicing; **the remaining transcription errors are
material**. It does not show that the production model now reads “45” or “55”
correctly, nor does it justify training on its predictions.

An aspect-preserving input experiment improved some of these examples but still
confused digits/operators. It was not installed in production or selected from
this small cohort. Production keeps the original fixed input policy and pair
`a807eaa7…` / `6af4062e…`. Offline drafts use the already frozen experimental pair
`95577af0…` / `dc25d2de…`; that pair remains unpromoted.

Fresh, source-disjoint verified references and independent transcription checks
are still needed before changing weights or input policy. Multiline prose,
clipped regions, sparse symbols and two-dimensional mathematics remain known
limits. Current drafts retain unverified-label and false training flags.

## Deployment verification

- AI/worker containers are healthy and match final code/model hashes.
- Direct real-source checks used Drive bytes through RAM/stdin; originals were
  not sent to an image-storage or external inference service.
- Internal OCR HTTP passes a synthetic-image check with the unchanged model.
- Final public login and backend student-role checks pass on portal, teacher and
  admin web deployments. One preceding TLS-handshake timeout was retried; it
  was not counted as a successful web check.
- Rollback image: `mathvision-ai:rollback-stroke-20261012`.
- The global Drive source index is unchanged. Deliberately deleted photo and
  archive-cache directories are still absent.
- No Git commit/push, paid service, UI changes or physical-device claims.
- Backend/OCR hosting still depends on the user's running PC.

## Private evidence

Under `ai-training/datasets/drive_math/crop_review_20261012/`:

- `reviewed_references.json`, `reviewed_frozen_comparison.json`;
- `screen.jsonl`, rejected variant probes and visual-review candidates;
- `release/local_regions/`, `release_detection_comparison.json`;
- `release_changed/recognition/`, `recognition_reconciliation.json`;
- `release_review_queue.jsonl`;
- `tests_release.log`, `endpoint_tests_release.log`;
- `local_deployment_smoke.json`, `deployment_smoke.json`, final smoke log;
- prior-code snapshots, rollback log and final reconciliation/code snapshot.

Earlier failed and intermediate attempts are retained separately; final records
were reconciled against their selections, source hashes, integer bounds, SQLite,
JSONL, frozen model/vocabulary and current detector hashes.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: repair the shared crop failure with existing PIL/OpenCV and
    bounded checks, without adding a recognizer or dependencies.
  - Applied to: stroke ownership, column interaction, cache invalidation,
    regression tests, source-preserving evaluation and deployment verification.
