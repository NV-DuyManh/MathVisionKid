# Drive-backed recognition audits

For setup on another machine, the private Drive folders, archive IDs, and safe
restoration commands, start with the Vietnamese root guide:
[DU_LIEU_GOOGLE_DRIVE.md](../DU_LIEU_GOOGLE_DRIVE.md).

Keep source images on the mounted Google Drive and keep reviewed labels, the
SQLite ledger, frozen selections, current cloud outputs, and helpers in the
private local dataset directory. Cold local audit results, baselines, previews,
and large historical inventories can live in verified Drive archives and must
be restored before historical comparison or resume commands that need them.
Originals do not need a copy inside each project batch. Keep app images, tiny
runtime reference/test fixtures, trained models, and application dependencies
local so normal application use does not depend on the Drive mount.

## Select a new batch without copying images

Install the optional dataset reader in the existing runtime environment:

```powershell
uv pip install --python ai/runtime/.venv/Scripts/python.exe -r scripts/data/requirements.txt
```

Open the desired image folder in File Explorer and copy its actual folder path.
Shared-folder shortcuts can resolve to a path under
`G:\.shortcut-targets-by-id\...`; a `.lnk` file is not a directory.

```powershell
$sourceFolder = 'G:\actual\image\folder'
& .\ai\runtime\.venv\Scripts\python.exe .\scripts\data\drive_line_batch.py mount-select `
  --source-folder $sourceFolder --batch drive_next_batch --limit 200
& .\ai\runtime\.venv\Scripts\python.exe .\scripts\data\audit_text_regions.py `
  --batch drive_next_batch --mark-tested --no-overlays --no-drafts
```

Selection skips content already recorded in the ledger. The frozen selection
stores each source path and SHA-256. Audits read those bytes directly; they do
not create an `images` copy in the batch. Choose a new batch name each time.

## Previously downloaded batches

A private `ai-training/datasets/drive_math/storage_sources.json.gz` maps migrated
image identities to verified files, ZIP members, or Parquet image rows on Drive.
The common readers in `drive_line_batch.py` and `audit_text_regions.py` use it
automatically, including nested shards. A migrated ZIP or Parquet container must
be fully verified against its local original first. Each later read checks the
returned image against its own frozen hash without hashing the entire container
again. Only one Parquet row group is cached in process memory.

The final 2,978 original image identities now use the same private index:
2,975 supplied crops reference members of `dataset_clean_full.zip`, and three
reference photos use mounted file paths. Preserve both the full and filtered
ZIP versions on Drive; the filtered ZIP excludes four crops and cannot replace
the full original for those source identities. Install and verify all mappings
before removing any local original or archive. The complete private index now
resolves 83,733 source identities; local original image copies and both ZIP
copies were removed after verification. Review previews and historical local
results now may be archived; restore their original paths when needed.

`prepare_archive_batch.py` prefers the local `archives/dataset_clean_full.zip`.
If it is absent, the helper reads `archives["dataset_clean_full.zip"]["path"]`
from the private storage index. The acquisition inventory stays local at
`archives/dataset_clean_full.inventory.json`; the helper verifies the entire
selected ZIP against that inventory before preparing a batch. This helper
retains its extraction behavior; the audit commands above read mapped sources
without creating batch image copies.

Unmapped originals stay local; nested audits can read them from their original
batch without creating another copy. If Drive is disconnected, an image disappears,
or its bytes change, a mapped read fails explicitly. It does not substitute
another image or fabricate an OCR result. Revalidate the mapping after changing
the mounted drive letter or source folders.

Drive streaming still uses local cache for opened files. Avoid marking the
whole dataset **Available offline**. A first read can require a download and
take longer; later reads may use the cache. Keep reviewed annotations, audit
results needed by an active audit, and SQLite databases on a normal local
filesystem. Preserve review previews as evidence; when archived on Drive,
retain their original paths and hashes so needed previews can be restored.
`--no-overlays` avoids creating
additional previews during an audit.

Old private one-off scripts which read `images/<id>.jpg` directly must use
`source_storage.read_source_bytes(folder, item)` before being rerun on migrated
batches. Scripts reading preview paths need those previews restored before
rerunning. The supported audit commands above already use the shared reader.

## Restore a historical batch before comparing it

The public catalog `docs/drive-archives.json` identifies the private ZIP files.
The default archive folder is
`G:\My Drive\Dự án\MathVisionKid\Lưu trữ`. Listing needs only Python and the
local catalog; extracting requires access to the mounted Drive:

```powershell
py -3 .\scripts\data\restore_drive_archive.py --list
$batchPath = 'ai-training/datasets/drive_math/new2_20261006_84'
py -3 .\scripts\data\restore_drive_archive.py --id audit-results-20261007 --prefix $batchPath
py -3 .\scripts\data\restore_drive_archive.py --id review-images-20261007 --prefix $batchPath
```

Restore `local_regions` and relevant baselines before `compare.py` or resuming
an old audit, otherwise missing results can trigger recomputation. Restore
overlays/sheets/crops before legacy preview consumers. Historical coverage and
Parquet checks may also require inventories from `history-20261007`.
Current cloud outputs and queue metadata stay local so resuming does not lose
protection against repeated API calls.

The restore helper verifies the whole ZIP SHA-256 and each restored file,
rejects unsafe paths/reparse destinations, preserves timestamps, skips
identical local files, and stops on conflicts without overwriting. Do not
replace an existing ledger with its snapshot; the private metadata and ledger
backups are for a new empty setup or a separate recovery directory. See the
root guide for `--drive-root`, `--repo-root`, and full recovery steps.

This storage change does not train a model, promote predictions into labels,
or establish recognition accuracy.

## Source triage and geometry revisions (2026-10-08)

Archive `line-repair-20261008` contains the reviewed empty-source manifest,
versioned geometry corrections and hash-bearing regression evidence. See
[the phase report](../report/LINE_REPAIR_AND_SOURCE_TRIAGE_20261008.md).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id line-repair-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/empty_triage_20261008.json'
py -3 .\scripts\data\restore_drive_archive.py --id line-repair-20261008 `
  --prefix 'ai-training/datasets/drive_math/geometry_review_20261008'
```

The triage manifest marks 140 visually unwritten sources for exclusion from
text training. It does not remove originals or certify the remaining OCR.
Geometry revisions preserve original labels for historical comparison;
revised rectangles alone do not certify transcriptions for training.

## Crop-context expansion (2026-10-08)

Archive `line-expansion-20261008` holds frozen runtime16/final runtime17
comparisons and 1,000 additional regression sources. See
[the expansion report](../report/LINE_CONTEXT_EXPANSION_20261008.md).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id line-expansion-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/empty_triage_expansion_20261008.json'
```

The new manifest preserves the previous manifest hash. Nine newly nonempty
sources are source-reviewed candidate geometry, often with clipped neighbouring
writing. Transcriptions remain unverified and all new candidates are ineligible
for training. Consult both manifests when selecting future batches; do not
overwrite historical evidence or equate a nonempty result with correct OCR.

## Paper-texture retry and scoped transcription review (2026-10-08)

Archive `sparse-ink-20261008` contains runtime17/final runtime18 comparisons,
1,671 final source results, the texture triage revision and seven separately
reviewed math transcriptions. See [the phase report](../report/PAPER_TEXTURE_AND_TRANSCRIPT_REVIEW_20261008.md).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id sparse-ink-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/empty_triage_texture_20261008.json'
py -3 .\scripts\data\restore_drive_archive.py --id sparse-ink-20261008 `
  --prefix 'ai-training/datasets/drive_math/source_review_texture_20261008'
```

The clear transcriptions certify only their declared scopes. Uncertain marks,
crossed-out calculations, fraction cancellation and parallel labels retain
explicit annotations; geometry and full-image coverage are not certified.
All new records remain ineligible for automatic training.

The bounded cloud cohort `all_current_20261007/cloud_resume_20261008_100` preserves
85 completed reads and 15 pending entries, with no repeated historical reads.
Restore that prefix if resuming from an archive. Provider classifications are
predictions, not verified labels; preserve outputs and source hashes before
resuming, and respect the saved provider retry deadline.

## Source confirmation and remaining-read follow-up (2026-10-08)

The 15 entries left by the preceding phase have now been completed separately
in `all_current_20261007/cloud_pending15_20261008`. The old 85 output files are
byte-identical; their historical summary still describes that earlier run.
Together with 39 older saved reads, the original 1,319-page queue has 139 saved
reads and 1,180 pending. Provider responses are not approved training labels.

Archive `math-source-safety-20261008` contains the new 15 reads, 18 real-math
selections from five source photos, remaining-crop probes, tested-code snapshots,
test/HTTP receipts and actual browser screenshots. See
[the phase report](../report/MATH_SOURCE_CONFIRMATION_AND_REMAINDER_20261008.md).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id math-source-safety-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_pending15_20261008'
py -3 .\scripts\data\restore_drive_archive.py --id math-source-safety-20261008 `
  --prefix 'infra/local-runtime/logs/math-source-safety-20261008'
```

Thirteen writing crops remain unresolved after 52 bounded experiments; seven
clipped fragments need larger originals. Preserve the separate failed and
retried division reads and the known `13/2` transcription error. Neither new
nonempty boxes nor a student confirmation checkbox establishes label accuracy.
No new record was approved for automatic training. The archive has complete
read-back verification and a fresh selected restore; Drive background upload
completion remains unverified, so small working evidence is retained locally.

## Queue continuation and rejected local candidate (2026-10-08)

The next phase added 63 reads in
`all_current_20261007/cloud_remaining1180_20261008`. Together with the preserved
historical 139, the frozen queue now has **202/1,319 saved reads and 1,117
pending**. This supersedes the preceding phase's queue totals. Saved cloud
results include unreadable classifications and are not approved labels.

Archive `ocr-completion-20261008` also contains a private reviewed 48-crop
TRAIN/DEV/HOLDOUT manifest and an actual, rejected CRNN head-adaptation candidate.
It does not replace production weights. See
[the phase report](../report/OCR_COMPLETION_AND_CANDIDATE_20261008.md),
[the review/training guide](OCR_REVIEW_AND_TRAINING.md), and
[the owner's phone checklist](PHONE_TEST_HANDOFF.md).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-completion-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_remaining1180_20261008'
py -3 .\scripts\data\restore_drive_archive.py --id ocr-completion-20261008 `
  --prefix 'ai-training/datasets/drive_math/candidate_line_20261008'
```

Keep the new batch and historical batches separate. The batch CLI now respects
saved provider backoff even after restarting and returns exit code 2 when pages
remain. Do not use `--force` to repeat completed reads. Candidate HOLDOUT pages
have now been examined; retain that fact in any later evaluation or training.

## Numeric fields and decoder follow-up (2026-10-08)

The later follow-up supersedes the queue totals above: **209/1,319 saved reads,
1,110 pending**. It adds reviewed fraction/division component scopes and two
rejected local candidates. They are experiments, not production models. Exposed
HOLDOUT reuse is explicitly recorded in each newer manifest.

Archive `ocr-fields-decoder-20261008` contains the follow-up evidence, candidates,
current queue state and source review previews. It supplements the earlier
archive; it does not replace historical evidence. See
[the follow-up report](../report/OCR_FIELDS_AND_DECODER_20261008.md).

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-fields-decoder-20261008 `
  --prefix 'ai-training/datasets/drive_math/candidate_recurrent_20261008'
```

Mounted-file readback is verified. Background upload completion on Google's
servers is not independently verified; small working evidence remains local.

## Visual and numeric adaptation archive (2026-10-08)

The subsequent phase supersedes those queue totals: **238/1,319 saved reads and
1,081 pending**. Archive `ocr-visual-numeric-20261008` supplements the preceding
archives with reviewed component scopes, failed and development-only candidates,
frozen evaluations, source previews, detector diagnostics and final tests.
Successful mounted ZIP entry readback and a fresh selected restore are verified.
Google background upload completion is not independently verified; working
evidence is retained. No production model is replaced.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-visual-numeric-20261008 `
  --prefix 'ai-training/datasets/drive_math/candidate_numbers_20261008'
py -3 .\scripts\data\restore_drive_archive.py --id ocr-visual-numeric-20261008 `
  --prefix 'infra/local-runtime/logs/ocr-visual-adaptation-20261008'
```

Selected component results are 46/57 and, after explicitly retiring that set into
TRAIN, 17/19 on a different page. Both contain digit errors and fail the gate.
These are not all-photo accuracy scores. See the
[phase report](../report/OCR_VISUAL_AND_NUMERIC_ADAPTATION_20261008.md).

The final resume adds six further reads: **244/1,319 saved, 1,075 pending**.
Supplement `ocr-visual-numeric-final-20261008` preserves that later queue,
automatic detector overlays, rejected neutral-ink probes and final receipts.
The larger first archive remains unchanged at its 238-read snapshot.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-visual-numeric-final-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_remaining1180_20261008'
```

Restoration rejects different existing files. Inspect and separately archive an
older working queue before restoring newer overlapping state; do not overwrite
successful predictions with an older ZIP. Mounted readback verification is not
independent proof of completed Google server upload.

## Neutral fraction guard and pending queue (2026-10-08)

The latest snapshot preserves **250/1,319 saved cloud reads**, with **1,069 pending**.
Those counts include unreadable and multiple-exercise predictions; they are not
verified transcription accuracy. Archive `ocr-neutral-fraction-20261008` contains
the preceding batch's 111 reads, preserved historical output hashes, the new
1069-source selection, neutral-fraction guard tests and real-source probes.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-neutral-fraction-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_neutral_fraction1069_20261008'
```

The reader code changed, so the old 1180-source batch remains historical and the
current queue uses a new fingerprint. Resume the new batch using
[the OCR review guide](OCR_REVIEW_AND_TRAINING.md#resume-page-reading-safely).
Restoration rejects different existing bytes; archive an older working state
separately before restoring overlapping newer files. The new provider attempt
saved no further read and retained backoff. No production checkpoint is replaced.
Mounted ZIP readback and a fresh selected restore are verified; independent
Google server upload confirmation is still pending. Working evidence is retained.

## Scale and topic guard continuation (2026-10-08)

Archive `ocr-scale-topic-20261008` preserves **256 saved predictions and 1,063
pending IDs**, including six new provider responses, source-linked reviews,
scale comparisons, topic-guard replay and the final tested code. It supplements
the old archive rather than replacing its 250-read snapshot.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id ocr-scale-topic-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_heading1063_20261008'
```

The current versioned queue inherits the prior provider backoff; do not copy raw
successful predictions into it or resume an older batch with changed code. Use
[the current reading command](OCR_REVIEW_AND_TRAINING.md#resume-page-reading-safely).
Different existing bytes are rejected by restoration. All mounted ZIP entries
and a selected fresh restore are checked; independent Google server-upload
confirmation remains unavailable, so working evidence is retained.
