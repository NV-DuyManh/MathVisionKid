# Drive-backed dataset storage — 2026-10-07

## Scope

Recover space on E by removing only dataset originals and duplicate image paths
whose bytes have been verified against sources on the mounted Google Drive G.
Keep application dependencies, model weights, annotations, the SQLite ledger,
and audit results on a normal local filesystem.

## Verification and safeguards

- All eight supplied Parquet files were fully SHA-256 compared through the
  native G mount against the local originals. Their size and modification time
  were checked again before cleanup.
- Source photo candidates were compared by content hash, never filename alone.
- Each removed image path must resolve inside the private dataset, match its
  recorded NTFS identity and size, and match the source image SHA-256.
- The compressed source index is installed and tested before originals are
  removed. Every later mounted read checks the returned image bytes.
- Missing, changed, or disconnected Drive sources fail explicitly. Predictions
  do not become reference labels, and this operation does not train models.
- Metadata sizes and modification times are checked before and after removal;
  selected reviewed labels, helper scripts, and the ledger also have hash checks.
  Frozen batch selections have separate content hash checks.

## Storage workflow

The common local and cloud audit readers now resolve migrated identities to
files or Parquet rows on G. `mount-select` creates a frozen selection from a
mounted image folder without copying images into each batch. It skips byte
hashes already recorded in the ledger. Optional flags suppress duplicate
overlays and unverified draft labels.

See [Drive storage instructions](../docs/DRIVE_DATA_STORAGE.md).

G is cloud-backed streaming storage. Opened files can still occupy the local
Drive cache; do not mark the whole dataset available offline. The ordinary
content cache cap is configured at 2 GiB, with offline and pending-upload
exceptions. G is intended for dataset sources, not active databases or runtimes.

## Exceptions retained on E

This records the first migration's retained files. The subsequent
[final original migration](DRIVE_ORIGINALS_FINAL_MIGRATION_20261007.md) verified
and migrated these ZIPs and remaining source images; previews remain local.

Both the original and filtered dataset ZIPs are retained because a full cloud
byte comparison was not completed. They are different versions; the original
contains four crops absent from the filtered archive. Unmapped source images
also remain local. Review previews, annotations, and results are preserved.

## Results

Cleanup completed. After installing the optional Parquet reader and retaining
the source index and verified evidence archive, E has **4.77 GiB free**, up from
**1.35 GiB** at task start: **3.41 GiB net recovered**. The unlink operation itself
reclaimed 3.52 GiB; dependency and evidence storage are included in the net result.

| Measurement | Bytes | GiB |
| --- | ---: | ---: |
| Free E at task start | 1,453,793,280 | 1.35 |
| Free E immediately before removal | 1,360,711,680 | 1.27 |
| Free E after removal | 5,144,788,992 | 4.79 |
| Free E after retaining evidence | 5,117,186,048 | 4.77 |
| Net recovered versus task start | 3,663,392,768 | 3.41 |

These are volume free-space snapshots; background activity can change them.
Logical file sizes are not used as reclaimed-space figures because many paths
are hard links. E is a 22.20 GiB volume.

- Removed **210,420 verified image paths** and **8 verified Parquet containers**.
  The index resolves **80,755 source identities** to G: 1,364 file identities and
  79,391 Parquet identities, including aliases of the same image bytes.
- Retained **20,893 image paths**, representing **2,978 unique unmapped images**,
  plus both dataset ZIP versions. The original ZIP is 1,573,499,256 bytes and
  the filtered ZIP is 1,524,091,115 bytes. Neither was deleted.
- All **300,801 protected metadata files** passed size/modification-time checks
  before and after cleanup. **20,388 selected protected files** also passed
  SHA-256 checks. **41 frozen selections** passed separate hash checks.
- SQLite retained **83,733 rows** and `PRAGMA quick_check` returned **`ok`**.
- The mounted reader passed **16 exact-byte sample checks** before deletion.
  The real local detector then processed **12/12 G-backed samples**, with
  **zero execution failures**, zero cloud AI calls, and no image, overlay, or
  draft-label copies. This checks storage integration, not recognition accuracy.
- Five retained originals were also read successfully through the nested audit
  reader and matched their frozen hashes.
- Focused source/batch/archive regression tests: **20 passed**. Compilation of
  the two private resume helpers passed; frozen inventory reuse passed.

After preservation checks completed, the private `audit.py` and
`recheck_numeric_guard.py` helpers were intentionally adapted to resume through
the common reader without creating image hard links. Their before versions are
included in the evidence. Frozen selections remained unchanged after these edits.

Verified private evidence is retained under
`infra/local-runtime/logs/drive-storage-20261007/`, excluded from Git. The archive
contains 30 entries, each verified against its source, and is 27,584,482 bytes.
SHA-256: `a1922d07488382d433039e5730cc18238a4909418f4f50cd9ab22935bfb1f658`.
`final-volumes.json` records the final measurements. No cloud file was deleted
or changed, no model training was performed, and no Git commit or push was made.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal changes to existing Python dataset audit readers.
  - Applied to: one common source reader, mounted batch selection, focused tests.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: verify connected Drive source versions and ownership.
  - Applied to: read-only metadata, revision and source availability checks.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.930.41038/skills/computer-use/SKILL.md`
  - Why selected: inspect the native mounted Drive and streaming state.
  - Applied to: native Drive availability and download progress checks.
