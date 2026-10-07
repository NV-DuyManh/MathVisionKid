# Additional safe cleanup — 2026-10-07

## Result

The owner's additional cleanup request recovered another **1.84 GiB of measured free space**, after retaining private evidence. This is a new pass, separate from the previous 11.39 GiB cleanup.

| Drive | Free before this pass | Free after | Net change |
| --- | ---: | ---: | ---: |
| C | 59.28 GiB | 60.81 GiB | +1.53 GiB |
| D | 5.96 GiB | 5.96 GiB | Unchanged |
| E | 4.77 GiB | 4.77 GiB | Approximately -0.64 MiB for evidence |
| F | 7.36 GiB | 7.67 GiB | +0.30 GiB |

Measurements include background disk activity. Free space at the beginning differs from the earlier report because applications continued running. Logical file sizes are not treated as physical savings.

## Actions

- Removed **1,602 old generated files** from Next.js development output and Vite's dependency cache on F: 324,866,344 logical bytes. No Next/Vite process was using these locations. Application dependencies and production outputs were preserved.
- Removed **39,397 old npx cache files**: 708,925,312 logical bytes. All were at least seven days old; no running Node process referenced the npx cache. Future use of these temporary packages may download them again. Installed project dependencies and runtimes were retained.
- Removed **84 temporary evidence duplicates** from C: 93,807,243 logical bytes. Each file's SHA-256 matched a retained entry in a verified archive on E before deletion. Both original evidence archives remain intact.
- Applied native, lossless NTFS compression to **132 old text/log/history files**. Content was checked before, immediately after, and again at completion: zero SHA-256 mismatches. Approximately 0.30 GiB of file allocation was saved. Active/recent history and database files were excluded; no conversations were deleted.

Deletion used individual native PowerShell file operations with checked absolute roots, reparse-point exclusions and exclusive file-open checks. Temporary duplicates received another hash check immediately before deletion. All 41,083 planned deletions succeeded; none required stopping an application or forcing a locked file.

## Preservation and limits

- 24,412 protected source/model/configuration/label files remained unchanged.
- All 89 installed distributions in the AI project environment retained their names and versions.
- Five Git working-tree snapshots matched before adding this report.
- SQLite recognition ledger: 83,733 image records; `quick_check` returned `ok`.
- All 132 compressed files passed the final content recheck. Both earlier evidence archives passed SHA-256 and CRC verification.

Personal documents, original images, reviewed annotations, trained models, secrets, VM/emulator disks, chat histories, fresh installer payloads, DriveFS content cache and original dataset ZIPs were retained. G's streaming dataset mapping was preserved. No application code, Git commit/push, model training or physical-device test occurred. Further large reductions would involve retained user data or installations rather than the verified cleanup candidates identified here.

## Private evidence

```text
E:\MathVisionKid\infra\local-runtime\logs\extra-cleanup-20261007\evidence.zip
```

Size: 664,983 bytes. All 18 source entries passed SHA-256 comparison and archive CRC validation.

```text
SHA-256: 6e2ace7d7d08bc86e3c250ef5487b0b781d4dd3c5f48d6e96d5de436fe4b6cf3
```

Exact byte measurements are saved in the accompanying `final-volumes.json`. The ignored archive contains local path inventories and remains private.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse scoped native cleanup helpers and avoid additional dependencies.
  - Applied to: cache deletion, verified temporary-duplicate removal, lossless compression and preservation checks.
