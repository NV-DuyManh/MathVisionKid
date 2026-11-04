# Evidence kept out of Git

Dated implementation reports, screenshots, probe output and large result JSON stay local. New one-off diagnostics belong in `.local-artifacts/`; reusable regression tests remain with the application and CI.

Only contributor receipts, model governance manifests and checklists consumed by retained tests are tracked here or under `reports/archive/`. Contributor identities and source hashes remain in [CONTRIBUTORS.md](../CONTRIBUTORS.md) and [the provenance inventory](../docs/contributions/provenance-20261031.json).

## Local archive

Historical reports and retired one-off verification scripts were copied byte-for-byte to `E:/MathVisionKid-cleanup-archive/2026-11-04/git-hygiene/files/` before removal from the working tree. `manifest.json` alongside `files/` records original paths, SHA-256 and byte counts. The previous cleanup archive remains at `E:/MathVisionKid-cleanup-archive/2026-11-04/`.

Later on 4 November, the owner requested cleanup of the drive root. `MathVisionKid-cleanup-archive` and the clean, integrated temporary review worktree were moved to Windows Recycle Bin. Restore `MathVisionKid-cleanup-archive` from Recycle Bin before using the archive paths above. The deletion record and copies of both file manifests are retained locally in `.local-artifacts/drive-root-cleanup-20261104/`.

Links in older documentation point to this index and name the archived file. Restore a selected path from the local archive when comparing old evidence; check for newer files before copying it back. Archived results describe the revision and environment recorded at the time.

The tracked originals also remain in Git history at commit `399a7b7f604b8057a2ecf24391f0309e5d490a77`, before cleanup. This recovery source is available to other clones without the owner's local archive. For example, `git show 399a7b7:report/VOICE_BACKGROUND_PREPARATION_20261027.md` reads an old report without changing current files. Restore individual files only after checking for newer replacements; reusable tests and contributor/model receipts remain in the current tree.

The current local cleanup report is `report/cleanup-20261104/git-hygiene.md` and is ignored by Git. Build and cache directories may be recreated by running applications; `.gitignore` keeps them out of new changes.
