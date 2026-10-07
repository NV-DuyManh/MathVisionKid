# Final original-image migration to Drive — 2026-10-07

Dataset originals do not need a copy inside the repository. The private source
index now resolves **83,733 source identities** to verified mounted Drive files,
ZIP members, or Parquet rows. App images, tiny runtime fixtures, models,
dependencies, reviewed labels, SQLite, results, and review previews remain local.

## Changes

- Copied both different dataset ZIP versions and three reference photos into
  `G:/My Drive/Dự án/MathVisionKid/Dữ liệu OCR/Nguồn`.
- Independently verified all five files on the correct owner's Drive web,
  including the expected displayed sizes, before removing local copies.
- Fully compared SHA-256 for both ZIPs through the native G mount. Verified
  all **2,978 remaining original identities** against their frozen image hashes:
  2,975 crops inside the full ZIP and three mounted photos. The filtered ZIP
  excludes four preserved crops, so both ZIP versions remain on Drive.
- Added 2,978 mappings to the existing 80,755 mappings. Installed the compressed
  private index atomically; verified **28 samples** through both the direct
  mounted reader and nested audit reader before deletion.
- Removed **20,893 local original image paths** and **two local ZIP copies**.
  These image paths represented 2,978 distinct NTFS files, so their logical
  combined size was not used as reclaimed-space evidence.
- `prepare_archive_batch.py` now falls back to the mounted ZIP when the local
  ZIP is absent. Its acquisition inventory stays local, and it still hashes
  the entire selected ZIP before writing a batch.

Supported audits read mapped bytes without batch image copies. The archive
preparation helper retains its extraction behavior for new crops. Old private
one-off scripts must use the common reader before rerunning on migrated images.
See [storage workflow](../docs/DRIVE_DATA_STORAGE.md).

## Safety and validation

Local removals used native PowerShell exact paths. Each image target was
checked against the verified plan for size, timestamp, and native NTFS file
identity. Every target had to stay inside the private dataset; directories and
reparse points, including reparse ancestors, were rejected. Local ZIP hashes
were checked again immediately before removal.

- **300,801 protected metadata files** retained their sizes and modification
  times; **20,388 selected protected files** also retained their SHA-256 hashes.
- **41 frozen source selections** retained their hashes.
- SQLite retained **83,733 rows**, and `PRAGMA quick_check` returned **`ok`**.
- Source/batch/archive tests: **23 passed**, including available, missing, and
  changed mounted-archive fallback cases. Scoped diff whitespace checks passed.
- After deletion, the actual local detector processed **6/6 newly mapped G
  samples** with zero execution failures, no image/overlay/draft-label copies,
  no cloud AI calls, and no writes to the dataset ledger.

These checks validate storage and execution. They do not establish recognition
accuracy, convert predictions into reviewed labels, or train a model.

## Space and retained evidence

Free E immediately before this migration was **5,120,278,528 bytes (4.77 GiB)**.
Immediately after local removal it was **9,978,314,752 bytes (9.29 GiB)**:
**4,858,036,224 bytes (4.52 GiB)** reclaimed before retaining evidence and the
report. Final retained-evidence measurements are saved privately in
`infra/local-runtime/logs/drive-originals-final-20261007/final-volumes.json`.
Volume snapshots include background activity.

After retaining verified evidence, E has **9,954,660,352 bytes (9.27 GiB) free**:
**4,834,381,824 bytes (4.50 GiB) net recovered** in this final migration.

Private evidence retains the verified plan, before/after source indexes,
metadata and selection hashes, deletion receipt, detector outputs, and Drive
web screenshot. The evidence archive is excluded from Git and verified after
creation. Originals remain on Drive; no cloud file was deleted or had its
sharing changed. No model training, Git commit, or Git push was performed.

The evidence ZIP contains **28 verified entries**, is **23,609,577 bytes**, and
has SHA-256 `7647d58e2f2e3c499b22ccf05eb3e65b1501987c151582cb5ce511113b85a33e`.

Duplicate temporary evidence on C (**171,728,382 bytes, about 164 MiB**) was
retained at `C:/Users/Admin/AppData/Local/Temp/mathvision-drive-final-20261007`.
Automatic command review rejected both directory cleanup and individually
hash-verified file cleanup with the stated reason `blocked by policy` before
execution. No temporary evidence was removed. This does not affect the
completed original-image cleanup on E.

Drive streaming still uses local cache when opening files; G is not a physical
extra disk. A first read can wait for download. Keep the dataset streamed rather
than marking everything available offline. The app's own assets and runtime
fixtures remain local, so ordinary app use does not depend on G.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal adaptation of the existing dataset storage reader.
  - Applied to: ZIP fallback, focused tests, reuse of existing source mappings.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: preserve source versions and verify the correct Drive.
  - Applied to: native mounted storage and independent cloud availability.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.1002.51308/skills/computer-use/SKILL.md`
  - Why selected: verify completed synchronization through the Drive web UI.
  - Applied to: source-folder verification and screenshot evidence.
