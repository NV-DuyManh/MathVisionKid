# Drive cold storage and project handover — 2026-10-07

**292,250 verified local artifact files were archived on the owner's private Google Drive and removed from E.** Application source, runtime assets/models/dependencies, reviewed labels, frozen selections, cloud outputs/queues, the source index, and the current ledger remain local. Nine temporary ZIP copies remain local because automatic approval review rejected their deletion.

Start with [the root handover guide](../DU_LIEU_GOOGLE_DRIVE.md). The archive catalog and restore helper are linked from it and from the repository README.

## Storage destinations

- Private archive folder: `G:\My Drive\Dự án\MathVisionKid\Lưu trữ` — [open Drive](https://drive.google.com/drive/folders/1oOenOCeNdsHRprk3c8yNNmdp9ZYRE2Lh).
- Source originals remain in the previously verified Drive mappings, including `Dữ liệu OCR\Nguồn` and the actual C1SE.01 shared-folder mount. No original source mapping was changed in this operation.
- [Catalog](../docs/drive-archives.json): exact filenames, SHA-256, bytes, file counts, and backup-only flags.
- Private local evidence: `infra/local-runtime/storage-offload-20261007`; its 29 completed inspection/verification files were also saved in `storage-evidence-20261007.zip` on Drive.

| Archive ID | Files | Purpose |
| :--- | ---: | :--- |
| `audit-results-20261007` | 276,648 | Cold local/baseline results and result manifests |
| `review-images-20261007` | 11,830 | Overlays, sheets, crops, acquisition duplicates and visual review images |
| `history-20261007` | 8 | Large historical inventories and old dataset archives |
| `evidence-20261007` | 1,369 | Dated diagnostics and previous verification evidence |
| `scratch-20261007` | 1,628 | Old experiments and app exports |
| `parquet-tools-20261007` | 763 | Complete redundant standalone Parquet package copy |
| `handoff-20261007` | 4 | Incoming ZIPs and duplicate model artifacts |
| `private-metadata-20261007` | 24,219 | Backup only: labels, selections, cloud records, helpers and source mappings |
| `ledger-backup-20261007` | 1 | Backup only: consistent snapshot at canonical `ledger.sqlite3` path |
| `storage-evidence-20261007` | 29 | Backup only: this operation's file plans, receipts and verification results |

The seven offloaded artifact groups contain **2,865,613,167 logical bytes**. The first nine ZIPs occupy **2,182,052,202 bytes**; the additional operation-evidence ZIP occupies **22,568,486 bytes**. Backup-only files were not removed from their working locations.

## Verification and deletion boundary

1. Independently classified every eligible file, checked Git tracking/ignore boundaries, and recorded exact relative path, byte count, timestamp, volume and native file identity. Tracked quarantine data was retained. Runtime forensics under `scratch/runtime6_live_input`, root test fixtures, staged OCR parity samples/weight, current models, and active service logs were excluded.
2. Every archive member passed CRC and SHA-256 verification against the inspected source. Every initial mounted Drive copy matched its verified ZIP SHA-256. The authenticated Drive web listing independently showed all nine archives with completed sizes before any original removal. The operation-evidence ZIP was then created and fully verified directly on the mounted Drive.
3. A read-only credential review covered all 292,250 candidates, 530,559 text streams and 11 ZIP containers, including nested ZIP text. It reported zero real credentials and zero read errors. A separate binary-inclusive scratch pass cleared nine Hermes icon-string false positives. No secret values were printed or intentionally backed up.
4. Native PowerShell checked all removal paths, reparse ancestors, byte counts, timestamps and NTFS identities, then removed only those exact archived files. No parent directory was recursively removed. `removed-files.jsonl` records all 292,250 removals.
5. Real archive restoration verified a JPEG, a local-result JSON and a consistent ledger snapshot, including bytes, original timestamps, repeat-restore skipping and SQLite integrity. Automated unsafe-path/conflict checks passed.

## Preserved state and runtime checks

- **27,787 protected file hashes matched** after removal; 78 actively changing outputs were excluded from strict content comparison.
- The source-index SHA-256 remained `5a4b6aa049cd7198eb820a9ea46b0ba219780c2e79be193bc876e433f27a744a`, resolving **83,733** source identities.
- The current ledger retained **83,733** image rows; SQLite `quick_check` returned `ok`.
- Protected content includes 65 frozen `source_selection.json` files, 23,581 label/imported-label files and 12 runtime model/config files. These counts include duplicate snapshots; they are not counts of independently reviewed images.
- Two real mapped Drive images decoded and ran through the unchanged pinned local line detector, returning 18 and 10 regions. This checks execution/storage compatibility, not line precision or OCR accuracy.
- Storage/restore/archive/batch tests: **34 passed, 1 skipped**. The skip requires Windows symlink-creation privilege; a separate deterministic reparse-point rejection check passed. Cloud-resume tests ran with `ai/runtime` on the Python import path.
- No model training, Git commit/push, application source edits or physical-device testing was performed in this task.

## Space measurements and remaining local copies

The recorded E free space immediately before the removal phase was **12,232,417,280 bytes**. After the 292,250 removals it was **15,417,221,120 bytes**, about **14.36 GiB free**. That phase's observed increase was about **2.97 GiB**. Earlier volumes changed during the long archive/upload operation, so the broader task-start difference is not attributed entirely to this cleanup. Drive streaming can still use the local cache.

**Automatic approval review rejected deletion of the nine verified ZIP copies in `infra/local-runtime/storage-offload-20261007/staging`, reporting only `blocked by policy`.** The command did not execute. Those copies, about **2.03 GiB**, remain on E, as do small inspection records and restore-smoke files. They are recoverable from the verified Drive archives and are not required to run the app. The rejected deletion was not retried through another mechanism.

The previous operation's C temporary evidence was outside this removal plan and was not modified. Dependencies, current models, SQLite, secrets and tracked files remain on a normal local filesystem.

## Continuing work

Read [DU_LIEU_GOOGLE_DRIVE.md](../DU_LIEU_GOOGLE_DRIVE.md). `--list` works without Drive mounted. Restore only the required archive ID and batch prefix before historical comparison, preview inspection or resuming a previous local audit. Missing cached local results can otherwise trigger recomputation. Keep existing cloud outputs and queues to avoid repeated provider requests.

For a new empty dataset, the private metadata and consistent ledger backups support continuation after obtaining the owner's private Drive access. Never overwrite a newer ledger or reviewed label with an older snapshot. Changing the mount letter or source layout requires hash-based source-mapping revalidation; `--drive-root` changes only the archive location.

Folder-level `ARCHIVED.md` pointers were left in the dataset, scratch, incoming handoff and dated evidence folders. The handover guide, catalog and restore helper also have companion copies in the Drive archive folder.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal Python/PowerShell storage tooling and restoration logic.
  - Applied to: standard-library archive/restore helper, scoped file operations and checks.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: organize and verify private Drive storage.
  - Applied to: account/destination verification and mounted-Drive workflow; the mismatched connector account was not used for mutations.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.1002.51308/skills/computer-use/SKILL.md`
  - Why selected: independent authenticated cloud completion verification.
  - Applied to: background Drive browser listing and screenshot evidence.
