# Drive math batches

Use the Drive connector when available to list/download the owner's selected math
photographs. Public Drive folder discovery and public downloads are an alternative
when that connector is unavailable; record the actual acquisition method.
Keep original bytes, source Drive ID, filename, group and source URL in the private
batch directory. Do not publish student photographs, signed download URLs or keys.

## Local artifacts

`ai-training/datasets/drive_math/<batch>/` is ignored by Git:

- `source_selection.json`: exact source metadata selected for this batch.
- `images/<drive_id>.jpg`: immutable originals; EXIF orientation is applied in memory.
- `labels/<drive_id>.json`: source hash, review stage, reference count/geometry/text.
- `results/<drive_id>.json`, `summary.json`, `manifest.csv`: local row-detector evidence.
- `cloud_results/`, `cloud_summary.json`: separate, explicit vision-API audit evidence.

The SQLite ledger at `ai-training/datasets/drive_math/ledger.sqlite3` records tested
Drive IDs and both raw/pixel hashes. Later selection skips tested IDs; pixel hashes
identify copies under different filenames. Marking means excluding from later
selection, not deleting Drive originals. Failed image decoding remains retryable.

## Run

From the repository root, with the existing runtime Python environment:

```powershell
& ai/runtime/.venv/Scripts/python.exe scripts/data/drive_line_batch.py select --selection <connector-metadata.json> --batch <new-date> --limit 200
& ai/runtime/.venv/Scripts/python.exe scripts/data/drive_line_batch.py run --batch <new-date>
```

Download the selected originals into the batch's `images/` directory before `run`.
An existing selection is preserved: choose a different batch name for a new batch.
Rerunning refreshes reviewed labels and reuses valid detector results. Changed
source bytes or detector code invalidate cached measurements. `--force` measures
the detector again without changing originals or approved labels.

For an **owner-authorized** audit using the configured external vision APIs:

```powershell
& ai/runtime/.venv/Scripts/python.exe scripts/data/drive_line_batch.py cloud --batch <date>
```

Cloud audit stops when the provider is unavailable. Resume after the provider's
backoff/recovery; valid saved responses are reused. It never changes a reference
label or trains a model. Unreadable/multiple-problem responses are legitimate
application outcomes, not verified transcription or successful OCR accuracy.

## Label policy

`needs_review` is a draft, never ground truth. `count_verified` means only that a
reviewer counted the source rows. `geometry_verified` means every box was reviewed
against original pixels. `verified` additionally requires readable, unambiguous
text for every row. Bind all labels to the original SHA-256. Keep pupil arithmetic
errors; use explicit uncertainty for illegible symbols instead of calculating a
replacement. Existing verified labels are retained, not overwritten by predictions.

Headings and answer rows count. Accents and replacement words remain with their
writing row; a fraction within an equation stays in that equation. Column arithmetic,
tables, diagrams, fragments, tilted/curved pages and obscured text require separate
layout/region review. Do not assume a matching row count proves correct boxes/text.

The current batch is development evidence because detector choices were tested on
it. Keep future evaluation pages/families apart from training data. Raw images and
unverified predictions are not automatically promoted to a training set. No model
training occurs in this script.

## Mixed archive batch: 20261004_500

This selection contains 100 original photographs from `NEW2/IMG` and 400 image
entries from `dataset_clean_full.zip`. It was acquired through public Drive
folder discovery/downloads, not the connector. See
`report/DRIVE_500_ANALYSIS_20261004.md` for results and unresolved defects.

An archive entry uses a stable source key formed from its archive Drive ID and
entry-path hash. The ledger's `drive_id` column stores that key for archive crops;
it does not imply that each entry is a separate Drive file. Preserve archive ID,
archive SHA-256, entry path and parent-page name in the selection. Imported CSV
text stays in `imported_labels/` as `unverified_source_label`, separate from
reviewed references in `labels/`.

Pixel deduplication excludes previously tested files and copies under different
names. It cannot exclude all crops of previously tested pages. Group related
full pages and crop-parent families before any training/holdout split. Do not
present this selection as 500 independent new pages or its output-box counts as
OCR accuracy. The supplied crop filenames do not guarantee one complete row.

`review_queue.json` preserves 126 flagged sources with source hashes and reasons:
empty generalized outputs, observed layout/source defects and suspicious supplied
labels. The queue is not exhaustive and its heuristic flags are not verified
errors. `combined_geometry_manifest.csv` records all 500 outputs. Even files with
no regions are marked tested to exclude them from ordinary new-file selection;
explicit retries use their fixed identities and retained originals.

## Optional local text-region detector and NEW2 audit

The portrait notebook segmentation path can use the pinned OpenCV PP-OCRv3
artifact. Install it explicitly on a development host; student requests never
download weights. Missing or invalid artifacts retain the established fallback.

```powershell
& ai/runtime/.venv/Scripts/python.exe ai/runtime/scripts/setup_text_detector.py
& ai/runtime/.venv/Scripts/python.exe scripts/data/audit_text_regions.py --batch new2_20261004 --max-regions 200
```

This second command uses a frozen, already downloaded selection and measures the
production local segmentation function. It does not call providers, alter Drive,
approve annotations or train models. The exclusion ledger changes only when
`--mark-tested` is explicitly supplied; existing ledger provenance is preserved. It writes
`local_regions/`, `local_overlays/`, `local_summary.json` and `local_manifest.csv`
inside the private batch. Preserve prior outputs before comparing code versions.
Results contain code/model hashes and remain unverified candidates. The audit's
200-region limit differs from the legacy OCR endpoint's 30-region default.

See `report/NEW2_LINE_RECOGNITION_20261004.md` for the complete 100-source scope,
quality review and incomplete provider audit. Model source/license/checksum lives
in `ai/runtime/models/ocr/text_detector_manifest.json`; binary weights remain
ignored by Git.

## Remaining downloaded crops and local curation: 20261004

The archive selector validates the downloaded archive hash, enumerates all crop
images (including ones without a CSV label), skips tested identities and duplicate
pixels, and excludes derived debug images. It freezes the selection before audit.

```powershell
& ai/runtime/.venv/Scripts/python.exe scripts/data/prepare_archive_batch.py --batch remaining_crops_20261004
& ai/runtime/.venv/Scripts/python.exe scripts/data/audit_text_regions.py --batch remaining_crops_20261004 --max-regions 200 --mark-tested
& ai/runtime/.venv/Scripts/python.exe scripts/data/review_local_batch.py --batch remaining_crops_20261004
```

The first command was already completed for this batch and deliberately refuses
to replace its selection. Resume with the second command: matching original,
production-code/model hashes and region limit reuse persisted results; `--force`
remeasures. Persisted failed decoding remains retryable. A successful execution
with zero candidate boxes is marked tested, not labeled correct or deleted.

`local_review_queue.json` flags suspicious imported labels, thin source strips,
multiple candidate regions in supplied crops and empty detections. Flags indicate
review priorities, never authority to delete source files or approve labels.

Four original crops were visually verified as fabric/blank-paper backgrounds.
Their zero-text geometry references and source hashes live in
`remaining_crops_20261004/confirmed_background_exclusions.json`; they are excluded
from `archives/dataset_clean_filtered_20261004.zip`, along with their four CSV
rows. Originals remain in the private audit set as negative evaluation examples.
The filtered archive was uploaded as the current revision of the same Drive file
`17TN2eCey2tWE2qy6aEVPiJcbv-OaKwax`, retaining its name and share URL. The
connector's 512 MiB upload limit required authenticated browser Manage versions
upload instead. Metadata and revision readback confirm its new size and revision;
`remote_cleanup_receipt.json` and `drive_version_updated.jpg` retain evidence. No
unreadable handwriting is excluded merely because a detector returns no boxes.

See `report/DRIVE_REMAINING_LOCAL_20261004.md` for complete scope, local results,
known defects, curation evidence and completed remote-update verification.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: small resumable data workflow and meaningful regression checks.
  - Applied to: batch CLI, stdlib SQLite/JSON/CSV, detector reuse and label validation.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: discover and fetch the owner's Drive photographs.
  - Applied to: paginated discovery, metadata provenance and preservation of originals.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.930.31730/skills/computer-use/SKILL.md`
  - Why selected: inspect the public folder when the Drive connector was unavailable
    during the 500-file follow-up.
  - Applied to: public browser folder discovery and metadata capture for that batch.
