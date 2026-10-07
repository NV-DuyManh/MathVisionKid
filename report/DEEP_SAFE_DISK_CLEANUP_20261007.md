# Extended safe disk cleanup — 2026-10-07

## Result

Recovered an additional **11.39 GiB of actual free disk space** across C, E and F. This is separate from the earlier cleanup and Drive dataset migration. No application source was changed, no model was trained, and no commit or push was performed.

| Drive | Free before | Free after | Additional recovered |
| --- | ---: | ---: | ---: |
| C | 50.98 GiB | 60.66 GiB | 9.69 GiB |
| D | 5.96 GiB | 5.96 GiB | Unchanged |
| E | 4.77 GiB | 4.77 GiB | 3.68 MiB net |
| F | 5.67 GiB | 7.36 GiB | 1.70 GiB |

Measurements include the retained evidence archive. Exact before/after values are in the private evidence; background activity can subsequently change free space. Directory sizes are logical byte totals and can include hardlinks, so actual savings are measured using volume free space.

## Inspection and cleanup

Inspected accessible contents of the user profile, ProgramData, selected Windows cache/log locations, installer/emulator/VM directories, and drives D, E and F. Reparse points were skipped, and inaccessible directories were left alone. This was not a claim to inspect every protected Windows system directory.

Removed **49,416 individually verified cache files**, with 9,690,509,963 logical bytes:

| Category | Files removed | Logical GiB |
| --- | ---: | ---: |
| Browser caches | 18,111 | 2.54 |
| Gradle generated caches | 26,788 | 2.44 |
| Next.js development cache on F | 974 | 1.70 |
| Crash dumps | 32 | 0.84 |
| IDE browser caches | 689 | 0.54 |
| Graphics/shader caches | 956 | 0.43 |
| Old system and user temporary files | 162 | 0.36 |
| Unity compiled caches | 1,704 | 0.18 |

Also used native package-manager cleanup commands:

- `uv cache clean --no-progress`: reported 36,716 cache files removed, 1.4 GiB. Project environments and managed Python installations were retained.
- `pnpm cache delete '*'` and `pnpm cache delete '@*/*'`: cleared registry metadata, including scoped packages. The pnpm package store and installed dependencies were retained. Remaining metadata files: zero.
- `dotnet nuget locals http-cache --clear` and `dotnet nuget locals temp --clear`: both succeeded. Global installed package contents were retained.

Applied lossless NTFS compression to three eligible files on E. All three retained their SHA-256 values and paths. The final E gain is small because the earlier cleanup already removed most safe candidates and this task also retained a 2.30 MiB evidence archive.

## Safeguards and retained data

Deletion used native PowerShell on exact file paths. Before each deletion, the helper checked the approved root, parent reparse points, file size, modification time and minimum age, then attempted an exclusive open to reject files in use. No root directory was recursively wiped. No application or service was stopped.

Skipped 209 planned entries: 16 were in use and 193 were already absent, including overlapping browser-cache aliases. These were not forced open or treated as successful deletions.

Retained source code, model weights, original/reviewed labels, secrets, dependencies, personal documents, downloaded installation media, VM/emulator disks, Zalo/chat histories and Codex conversations. Fresh Visual Studio installer payloads were retained. The original dataset ZIP archives were also retained because complete verified replacement on Drive has not been established.

Docker was unavailable during this pass. Its virtual disk, images, containers and volumes were left alone; the earlier compaction was not repeated.

The dataset storage mapping to G remains intact. G is a Google Drive streaming mount, not additional physical local storage. DriveFS content cache was not manually deleted because it can contain pending uploads. [Google's configuration guidance](https://knowledge.workspace.google.com/admin/drive/advanced-drive-for-desktop-configuration).

## Verification

- **24,412 protected source/model/configuration/label files:** zero missing files or SHA-256 mismatches.
- **89 distributions in the project's AI Python environment:** names and versions identical to the pre-cleanup snapshot. Verification used the project virtual environment, not the separate system Python installation.
- **Five Git repositories:** working-tree status unchanged before adding this report.
- **Recognition ledger:** 83,733 image rows; SQLite `quick_check` returned `ok`.
- **20 focused storage/archive/batch tests passed**; installed `torch`, `pyarrow` and `cv2` imported successfully after package-cache cleanup.
- A separate Next.js dependency probe in `F:\9router` could not run because that checkout has no local `node_modules`. Cleanup targeted only its generated development cache. No dependency installation or application runtime test is claimed there.
- No physical-device, UI or recognition-accuracy evidence is claimed by this storage cleanup.

## Private evidence

Inventories, exact deletion plan and results, protected-file hashes, Git/package snapshots, native cleanup logs and verification helpers are archived under an ignored runtime directory:

```text
E:\MathVisionKid\infra\local-runtime\logs\deep-cleanup-20261007\evidence.zip
```

Archive size: **2,409,689 bytes**. All **32 original entries** passed SHA-256 comparison and the ZIP passed CRC validation.

```text
SHA-256: 734d77be4c8e0be353cd8e1d4d760edc37ec6aa0aa4c959847aa9f5ca73751d4
```

`archive-verification.json` and `final-volumes.json` accompany the archive. Evidence contains local path inventories and should remain private.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: keep cleanup automation small, scoped and based on native tools.
  - Applied to: fixed cache roots, individual-file deletion checks, native package cleanup, preservation verification and evidence archiving.
