# OCR corpus review and training — 2026-10-13

Status: training experiments finished and rejected for promotion. Corpus recognition is still running; this is a progress report, not a completed accuracy certification.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: small OCR tooling fix and bounded source-read recovery.
  - Applied to: numeric-only model guard, reuse of the existing recognizer, process-isolated Drive reads, focused regression checks.

## Scope and storage

- Reconciled metadata for 64,803 sources: 1,581 standalone pages, 2,975 supplied ZIP crops and 60,247 supplied Parquet line images.
- Math/non-math triage remains unverified. The current recognition selection includes all standalone pages, all supplied ZIP crops, and the union of 2,295 Parquet candidates from broad math-word and stronger expression screening. It does not certify that other Parquet rows contain no mathematics.
- All original image/archive reads use the existing G: Drive mount. Original images, ZIP files and Parquet files were not restored into this phase's local workspace. Local outputs are metadata, text drafts, SQLite records and private model candidates.
- The deliberately removed `all_retry_20261012/containers` and `pages_originals` remain absent.
- Original bytes are checked against frozen per-image SHA-256 values before inference. Whole ZIP/archive hashes were not re-read in this recognition pass.

## Detection and reference preparation

- Re-ran detection for all **1,581 pages**, including recovery of seven initially failed Drive reads. Reconciliation accounts for **37,435 detected regions**.
- Detection success means the procedure completed. It does not mean the boxes, reading order, fractions or handwriting are all correct. Geometry remains subject to review.
- Froze a revised 512-reference cohort: preserved existing non-prose controls, removed 44 redundant TRAIN prose entries and added 44 reviewed reference crops/fields. Removed entries and retained equivalents are recorded in the private cohort receipt.
- Eighteen supplied Parquet reference crops could not be loaded reliably. They remain in the full manifest, but were excluded from a separate, explicitly limited page-only experiment before fitting: **394 TRAIN / 95 DEV / 5 reserved HOLDOUT**.
- No OCR draft was automatically converted into a reference label. Incorrect arithmetic written by a student was preserved literally in source transcription.
- One original page is reserved from the current full-page recognition pass to protect the five fresh evaluation crops. Those crops have not received neural inference in this phase. This small reserved set is not sufficient to establish broad release accuracy; writer independence remains unknown.

## Training results and decision

Two 12-epoch CPU experiments completed using the same reviewed page cohort and seed. Compare against unchanged parent weights using the **same aspect-preserving inputs**, not the separate fixed-width preprocessing baseline.

| DEV result (95 crops/fields) | Unchanged weights, same input | Last visual block + recurrent/head | Head only |
|---|---:|---:|---:|
| Character errors / reference characters | 107 / 1,097 | 98 / 1,097 | 110 / 1,097 |
| Character error rate | 9.75% | 8.93% | 10.03% |
| Exact transcripts | 53 / 95 | 50 / 95 | 51 / 95 |
| Critical digit/operator errors | 30 / 432 | 33 / 432 | 33 / 432 |
| Critical-exact transcripts | 64 / 87 | 62 / 87 | 61 / 87 |

**Neither candidate is eligible to replace the running model.** Role-specific expression/comparison checks also regress. Fresh evaluation crops remain reserved instead of being consumed by candidates that already fail DEV.

Direct, hash-verified visual rechecking confirmed two important regressions:

- Source `300 cm² = 3 dm²`: new candidate loses a zero and part of the unit.
- Source `9 × 3 = 27`: visual candidate produces `9 × 3 = 227`.

References were not changed to agree with either model. Reviewed TRAIN scores are high, but the DEV gap and critical-symbol regressions prevent claims of general improvement. None of these percentages is the application's overall accuracy.

The production checkpoint/vocabulary remain unchanged:

- Checkpoint: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`
- Vocabulary: `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`

Corpus drafts use the earlier private experimental pair `4903062b…` / `dc25d2de…`, not either newly rejected candidate and not a newly deployed production model.

## Recognition progress snapshot

Snapshot: **2026-10-13 07:35:58 UTC**. Jobs continue after this snapshot; use the private reconciliation script for current counts.

| Source group | Selected | Draft recognized | Read failed, unresolved | Pending | Reserved |
|---|---:|---:|---:|---:|---:|
| Standalone pages | 1,581 | 448 | 2 | 1,130 | 1 |
| Supplied ZIP crops | 2,975 | 1,637 | 5 | 1,333 | 0 |
| Screened Parquet candidates | 2,295 | 1,038 | 1,257 | 0 | 0 |

There are **13,482 draft lines**, including 1,096 empty predictions, 1,303 resize-width warnings and 3,593 layout-review flags. These flags can overlap and are not verified error counts. All drafts have `labels_verified=false`, `reference_label=false`, `training_eligible=false`, and `score_is_accuracy=false`.

Google Drive virtual-file reads sometimes return `OSError` or stall indefinitely. The private reader isolates I/O in a child process with a 30-second deadline; stalled Parquet groups are explicitly deferred instead of repeatedly blocking every member. The 1,257 failed Parquet rows are being retried separately with a 60-second deadline. Page and ZIP jobs are still running. Recognition is **not finished** and the failed sources are not being counted as successful.

## Validation

- `scripts/data/test_recognize_corpus.py`: **17 passed**. Includes rejecting a numeric-fields-only candidate before general text/math corpus recognition while accepting unrestricted/legacy settings.
- Private `test_source_worker.py`: **passed** local-source rejection, real stalled-child timeout and termination, and deferral of a failed Parquet group without repeatedly reopening it.
- Geometry reconciliation: all 1,581 source IDs/hashes accounted for against the current detector pipeline; 37,435 regions.
- Recognition reconciliation verifies model/vocabulary identity, source selection, code fingerprints, SQLite provenance fingerprints and false label/training flags before counting committed drafts.
- Confirmed production model/vocabulary hashes, absence of restored source-image/archive files in the new phase directory and absence of the two deleted source folders.
- No physical-device evidence, deployment, Git commit or push was performed in this phase.

## Private evidence and remaining work

Evidence root: `ai-training/datasets/drive_math/math_all_20261013/` (ignored; contains no restored original photos).

- `scope_audit/`: complete membership and scope triage.
- `page_geometry_reconciliation.json`: successful detection receipts for every original page.
- `cohort_receipt.json`, `page_cohort_receipt.json`: reference additions, duplicate removals and storage exclusions.
- `run_pages_visual/evaluation.json`, `run_pages_head/evaluation.json`, `training_selection_decision.json`: frozen training evidence and rejection decision.
- `dev_errors_visual.json`, `dev_errors_head.json`, `regression_visual_confirmation.json`: errors against reviewed references and visual confirmation.
- `bounded_runs/*/run.log` and `recognition/`: continuing inference, timeouts and explicit failed records.
- `recognition_progress.json`, `recognition_failed_sources.json`, `recognition_pending_ids.json`: reconciled coverage snapshot.
- `summarize_progress.py`: rerunnable metadata-only reconciliation after jobs finish.

Still required: finish/reconcile the active jobs; retry unresolved Drive reads; visually review hard geometry, empty predictions and critical-symbol errors; restore all 18 excluded controls to a valid evaluation before release consideration; obtain substantially broader independent references. Training longer or repeating failed reads alone does not establish correctness.
