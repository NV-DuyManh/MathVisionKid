# Safe local disk cleanup — 2026-10-07

## Scope and status

The owner requested safe cleanup of drives C and E and explicitly approved compacting the Docker virtual disk with a short Docker restart. No application code was changed by this cleanup. Existing OCR and tutoring changes were preserved. No model training, Git commit, or push was performed.

Cleanup and Docker restoration completed successfully. Approximately **47.86 GiB of actual disk space** was recovered across C and E, after retaining the draft backup and cleanup evidence.

| Drive | Free before | Free after | Net recovered |
| --- | ---: | ---: | ---: |
| C | 15.62 GiB | 62.35 GiB | 46.74 GiB |
| E | 0.23 GiB (237 MiB) | 1.35 GiB | 1.12 GiB |

Exact final free bytes: C **66,948,710,400**; E **1,453,809,664**. Measurements are a snapshot; background activity can change free space. GiB means 1,073,741,824 bytes.

The Docker data VHDX was successfully compacted from **89,935,314,944 bytes (83.76 GiB)** to **45,747,273,728 bytes (42.61 GiB)**. DiskPart reported successful compaction with exit code 0. Docker Desktop then restarted successfully.

## Why space had run out

- C held an 83.76 GiB Docker virtual disk, substantial Docker build cache, Python/Node package caches, and old temporary installer/bundler files. Removing Docker cache alone does not make the host virtual-disk file shrink automatically; Windows provides detached virtual-disk compaction for that purpose. [Microsoft documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/compact-vdisk).
- E is a small volume: 22.20 GiB total. The Drive dataset, original dataset archives, audit outputs, cached image responses, and many small draft-label files left only 237 MiB free at the initial measurement.
- Several dataset directories share images through hardlinks. Their directory byte totals can count the same underlying image repeatedly. Volume free-space snapshots are used for actual savings; directory totals are not reported as physical disk usage.

## Cleanup performed

| Area | Action and safeguards |
| --- | --- |
| Package caches on C | Used `pip cache purge`, `uv cache prune`, and `npm cache clean`. Preserved project virtual environments, installed dependencies, managed Python runtimes, and the trained models. |
| Temporary files on C | Removed 21,138 individually checked cache/installer files from six identified cache folders. No general Temp-folder wipe. User clipboard images were excluded. |
| Duplicate image-response caches on E | Removed 20 download-response JSON files only after decoding and comparing their image bytes against 200 retained original images. |
| Large audit JSON files on E | Applied lossless NTFS compression to 25 JSON/JSONL files. All before/after SHA-256 checks matched; paths and content remained unchanged. |
| Empty draft labels on E | Archived 123,214 empty, unreviewed, training-ineligible machine drafts. Verified every archived entry against its original SHA-256 before deleting the loose copies individually. |
| Docker build cache | Reduced build cache from 23.9 GB to approximately 4.65 GB. Pruned build cache only; no image, container, or volume pruning. This is internal cache reclamation, distinct from Windows disk free space. |
| Docker virtual disk | Trimmed free blocks inside the Docker filesystem, stopped Docker, and used Windows DiskPart to compact only the detached Docker data VHDX after administrator approval. |

Machine drafts with content, notes, extra review metadata, or non-empty annotations were excluded from draft cleanup. The 280 existing labels with `verified`, `geometry_verified`, or `count_verified` status were preserved. Empty machine drafts are not verified ground truth and were not used to train a model.

## Preserved data and checks

- 23,046 protected source/model/configuration/label files were checked against their pre-cleanup SHA-256 values: **zero mismatches**.
- The recognition ledger retained **83,733 rows**, with SQLite `quick_check` returning **`ok`**.
- All 200 original images corresponding to the removed response caches passed byte/hash comparisons.
- The project Python package list remained identical.
- After Docker compaction and restart, all **23 container identities** and **36 Docker volume names** matched the initial snapshots. The original three running containers were restored: PostgreSQL, Redis, and MinIO all reported **healthy**.
- Original images, original dataset archives, reviewed/non-empty labels, model files, secrets, unrelated projects/documents, and application source were excluded from deletion.
- The pre-existing Git working-tree status remained unchanged before adding this report.

No physical-device or application-UI test is claimed. Validation covers cleanup scope, file preservation, ledger integrity, installed dependencies, and local infrastructure restoration.

## Recovering archived empty drafts

Local backup, excluded from Git:

```text
E:\MathVisionKid\ai-training\datasets\drive_math\archives\empty_machine_drafts_cleanup_20261007.zip
```

Archive size: **102,324,925 bytes**. Archive SHA-256:

```text
a71f5b953b1f5b4da530f1234cb390e2fb654ebb42cf213aff733586a471f8b5
```

To recover a draft, verify the archive hash and extract into an **empty directory**. `_cleanup_manifest.json` records the original relative paths and hashes. Restore only needed missing files under the Drive dataset root. Do not overwrite newer reviewed labels. Restoring all loose drafts would consume disk space again.

## Operational notes

E still has limited capacity after safe cleanup. Retain original images and annotations, avoid duplicating dataset downloads or emitting unused empty drafts, and plan larger storage for continued dataset growth. Owner documents, VM files, browser profiles, chat-app data, and unrelated installations were left alone.

Cleanup inventories, exact plans, hashes, command logs, and verification outputs are retained locally under the ignored `infra/local-runtime/logs/safe-cleanup-20261007/` directory. `evidence.zip` contains 52 files, all verified entry by entry, with archive SHA-256 `a35caf9680477813980e341b663c02e95fd34d85ffb25e839a5d15977a6f9253`. `final-volumes.json` records the final measurements after creating this evidence archive.

## Skills Applied

Skills Applied: None — no installed skill matched the task.
