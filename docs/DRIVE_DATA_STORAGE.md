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
