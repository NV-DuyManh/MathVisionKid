# Remaining downloaded math images — local audit and curation

Date: 2026-10-04. Owner scope: continue other images while vision providers recover;
then remove clearly useless crops containing no writing from the Drive source.

## Outcome and limits

Processed **2,575 additional unique supplied crops**, then rechecked the previous
604 sources and all 100 NEW2 photographs with the final local production detector.
All **3,279** unique originals completed local segmentation without execution
exceptions or out-of-bounds regions. This does **not** establish correct line
grouping, transcription or end-to-end student feedback for every image.

The tight-strip fallback added candidates for **331** previously empty crops.
Existing nonempty arrays on the new crop batch were unchanged; no outputs were
lost. NEW2's 100 candidate arrays were also unchanged by this crop-only fix.
The final new batch still has **94** empty outputs and the old 400-crop set has
**9**. Some sources contain no writing; others contain clipped or faint ink.
Empty output alone is not sufficient evidence to remove an image.

Four fabric/blank-paper crops were visually confirmed and removed from the
filtered ZIP, including their four CSV rows. **The filtered ZIP is now the current
version on Google Drive**, retaining the source file ID, name, parent and share
URL. It contains 3,003 supplied crops and 3,003 matching CSV rows. Their originals
remain private negative evaluation cases. These crops are ZIP members, not four
independent Drive file IDs. The connector rejected the 1,524,091,115-byte upload
because of its 512 MiB limit; after the owner signed into the browser, upload
through Drive's Manage versions completed and was verified by metadata and
revision readback. The prior archive remains visible as the previous revision.

## Exact source scope

The downloaded archive is `dataset_clean_full.zip`, Drive ID
`17TN2eCey2tWE2qy6aEVPiJcbv-OaKwax`, 1,573,499,256 bytes, SHA-256
`8823cdcb70c9b82eab50bae863e5136b364fff5d013725f5348c532607466a54`.
Its 3,183 image entries comprise 3,007 original supplied crops and 176 derived
debug visualizations. All 3,007 crop entry paths have matching source CSV rows.

The remaining selection partitions those 3,007 entries into 2,575 newly selected
images, 400 previously tested identities and 32 duplicate-pixel exclusions.
No crop path is missing from that partition. Crops from the same source page
remain related; this is not 2,575 independent new full-page photographs. The
scope covers downloaded sources, not a fresh inventory of every Drive folder.

The 704 older unique sources comprise 204 original photographs, 400 supplied
crops and 100 NEW2 photographs. Rechecking these does not increase the new-image
count. The ledger now contains 3,279 distinct identities and pixel hashes;
marking excludes ordinary future selection, not remote deletion. Raw image
hashes for all 3,279 final inputs were checked against their persisted results.

## Final local measurements

| Selection | Tested | Nonempty candidate output | Empty output | Execution failures | Local p95 |
|---|---:|---:|---:|---:|---:|
| Remaining supplied crops | 2,575 | 2,481 | 94 | 0 | 139.99 ms |
| Previous 204 photographs | 204 | 204 | 0 | 0 | part of mixed recheck |
| Previous 400 supplied crops | 400 | 391 | 9 | 0 | part of mixed recheck |
| NEW2 photographs | 100 | 100 | 0 | 0 | 470.27 ms |
| Total distinct audited inputs | 3,279 | 3,176 | 103 | 0 | not aggregated |

The mixed 604-source recheck has p95 464.50 ms. Timings measure local geometry
only, on this computer with some audit runs overlapping. They exclude API calls,
transcription, mobile upload and feedback latency. The audit uses a 200-region
limit; the legacy HTTP OCR default remains 30. The live application route and a
physical phone were not tested in this task.

Baseline for the new crops was 2,150 nonempty / 425 empty. The final 2,481 / 94
comparison is candidate availability, not OCR accuracy. The baseline snapshot
contains 2,567 results from the first run plus eight remeasured using preserved
prior code: an overlapping copy captured eight newer results, which were
identified by code hashes and corrected. Original overlapping copies are retained
in private evidence. `before_crop_fallback/baseline_remeasure_provenance.json`
records this explicitly; baseline latency comes from the first-run summary.

## Implementation

- `scripts/data/prepare_archive_batch.py` validates the archive hash, enumerates
  crop entries including unlabelled ones, retains original bytes, separates
  unverified CSV labels and freezes a deduplicated selection.
- `scripts/data/audit_text_regions.py` runs the actual production segmentation
  function. Resume requires matching input/code/model hashes and region limit.
  Successful evidence is persisted before optional ledger marking; accepted
  labels and first-test provenance remain intact. Changed originals are rejected.
- `scripts/data/review_local_batch.py` records review priorities without approving
  predictions or deleting sources.
- `app/recognition/text_detector.py` adds 16 pixels of white context around tight
  strips, then removes that context and clips proposed coordinates to original
  pixels. It cannot reconstruct ink cut off by the original crop.
- `app/api/generalized_pipeline.py` tries that optional model fallback only when
  all existing paths are empty, the source is at least eight times wider than
  tall, and height is 8–128 pixels. Results explicitly remain unverified and
  potentially clipped. Every existing nonempty classical result is preserved.

All final records match these hashes:

| Source | SHA-256 |
|---|---|
| `app/api/generalized_pipeline.py` | `a01d2b57015b38b716e421f81a9ba8b59e95e1fd989c1853f68f58aea5816c8a` |
| `app/recognition/text_detector.py` | `af5652e74f8a001e7a69e2e4c975959e685a4e833693fea1860efbe025bcada4` |
| `app/tutoring/rows.py` | `d2fe54b3da3a1d19fd3fa3ceca797de609a036d549023b0fe185068dc80f0702` |
| Pinned local PP-OCRv3 artifact | `03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587` |

## Labels and visual review

All 2,575 imported CSV labels remain separate and unverified. Automated triage
flagged 1,817 sources before manual background annotation, including 1,087 crops
with multiple candidates, 448 sources under 32 pixels high, 331 fallback outputs,
110 blank labels and 400 labels containing refusal/no-content phrases. Flags
overlap and do not prove an incorrect label. A no-content label can be correct
for a blank/background source. No inferred box count is promoted to ground truth.

The existing 33 accepted count/geometry/text references were preserved byte for
byte. Their count comparison is unchanged: 21/23 original photographs and 7/10
supplied crops match reviewed counts. Matching counts alone do not validate boxes
or transcript text. Four new references verify **zero text regions** only; they
do not add any verified mathematics transcriptions and are not training eligible.
The final new-batch label stages are 2,571 `needs_review` and four
`geometry_verified` zero-text negatives. Rebuilding the review queue preserves
these reviewed references; its 1,817 flagged-source total is unchanged.

Full-resolution originals visually reviewed as containing no writing:

| New batch index | Archive crop | Action |
|---:|---|---|
| 1321 | `Lớp_5_10_line_000.png` | exclude floral fabric/blank-paper crop |
| 1334 | `Lớp_5_10_line_014.png` | exclude floral fabric crop |
| 1335 | `Lớp_5_11_line_000.png` | exclude fabric/blank-paper crop |
| 1348 | `Lớp_5_12_line_000.png` | exclude fabric/blank-paper crop |

Three of these negative cases have false-positive classical candidate boxes;
one correctly has none. This is direct evidence against interpreting nonempty
outputs as recognition success. The filtered ZIP retains 3,003 crops and 3,003
matching CSV rows; its full CRC validation passes, retained image bytes are
unchanged, and the original archive remains intact. The private exclusion manifest
includes every original/source hash and the cleaned ZIP hash.

The 21 previously troublesome photos now all produce candidates, but visual
contact-sheet review still finds merged prose rows, fractional/column grouping,
faint missing paragraphs, facing pages crossing columns and background false
positives (including a person). None of these 21 is declared fully recovered.
`prior_other_recheck_20261004/manual_previous_failure_review.json` records each
source and remaining concern. NEW2 remains 100 unverified geometry drafts despite
having no automatic flags in this particular triage pass.

## Validation and remaining work

Targeted suite: **102 passed**, four existing framework deprecation warnings:

```powershell
cd ai/runtime
.venv/Scripts/python.exe -m pytest tests/test_text_detector.py tests/test_handwriting_rows.py tests/test_notebook_tutor.py tests/test_live_path_contracts.py tests/test_generalized_segmentation.py tests/test_row_grouper.py ../../scripts/data/test_drive_line_batch.py ../../scripts/data/test_archive_audit.py -q
```

Checks cover original-coordinate restoration, fractions, preservation of existing
nonempty results, frozen selection, duplicate/unlabelled sources, resumability,
changed/corrupt originals, accepted-label preservation and provider-label triage.
This is a targeted suite, not a claim that all repository tests pass.

Private evidence is under `ai-training/datasets/drive_math/`:
`remaining_crops_20261004/`, `prior_other_recheck_20261004/`,
`new2_final_recheck_20261004/`, and
`archives/dataset_clean_filtered_20261004.zip`. Use `local_regions/`, overlays,
review queues, `fallback_comparison.json`, `final_integrity_check.json` and the
curation manifest to inspect exact cases. Raw images and artifacts remain ignored
by Git. Run commands are documented in `docs/DRIVE_BATCH_REVIEW.md`.

No external vision-provider requests were issued in this task. Historical NEW2 evidence remains
12 responses before the prior notebook change plus one afterwards, with 87
sources pending. Providers have not been rechecked or declared recovered.
Accurate transcript review and difficult-layout correction remain unfinished.
Remote archive replacement is complete. No training, commit, push, service restart
or physical-device evidence was produced.

### Remote update follow-up

Source metadata was read using the connected Google Drive plugin and matched
`dataset_clean_full.zip`, ID `17TN2eCey2tWE2qy6aEVPiJcbv-OaKwax`, MIME
`application/zip`, parent `1PbH8o2Bki71u7ZaYGwaBDYP-HNNM0FMK`, modified
`2026-09-19T05:18:44.808Z`. The completed local filtered archive SHA-256 is
`4e545cc537705b2da454405c7cfd8fe3e25ae1053d47650f2f276c2844b32148`
and MD5 is `a915ceeed8078a39af4db87d3f935067`. An in-place update preserving the
Drive ID was attempted once and rejected by the file-size limit. Do not retry
that same oversized connector upload, split the logical dataset into new remote
files without authorization, or delete the entire ZIP to remove four members.

After owner authentication, Drive's Manage versions accepted the filtered file
and displayed it as the completed current revision. Connector readback confirms
the unchanged file name `dataset_clean_full.zip`, same ID, same parent, current
size 1,524,091,115 bytes and modification time `2026-10-04T08:43:36.713Z`.
The browser identified the uploaded revision filename as
`dataset_clean_filtered_20261004.zip`; this does not rename the source Drive file.
Its current MIME type is `application/x-zip-compressed`.

Current revision: `0B8S-F-6bYfmJRHVjNnNGMFZjVjZZK0xHc2xWVkNwWkJnYWlVPQ`.
Previous revision: `0B8S-F-6bYfmJM1hUSTJiMGRPcmYzWlVoYisrM1dhU2pyYmlRPQ`.
The previous revision is subject to Drive's normal retention policy; the original
downloaded archive is also preserved locally. Historical audit hashes refer to
that original archive, not the new current remote revision. The readback did not
return a remote checksum; validation consists of the verified local ZIP, completed
browser upload, exact remote size and new revision identity. No remote full-file
checksum comparison is claimed.

Private evidence: `remaining_crops_20261004/remote_cleanup_receipt.json`, updated
`confirmed_background_exclusions.json` and screenshot `drive_version_updated.jpg`.
The verified file URL remains
`https://drive.google.com/file/d/17TN2eCey2tWE2qy6aEVPiJcbv-OaKwax/view?usp=drivesdk`.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded local OCR fix and reusable offline audit with existing dependencies.
  - Applied to: crop fallback, stdlib archive/ledger workflow, resume and regression tests.
- `plugin-management`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/plugin-management/0.1.0/skills/plugin-management/SKILL.md`
  - Why selected: owner requested removal from an external Drive source.
  - Applied to: discovery of available Google Drive integration and truthful remote-access status.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: connected Drive lifecycle action after installation.
  - Applied to: exact archive metadata, attempted connector update, completed-upload metadata and revision readback.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.930.31730/skills/computer-use/SKILL.md`
  - Why selected: inspect a browser upload alternative after the connector size rejection.
  - Applied to: browser authentication handoff, Manage versions upload, completion verification and screenshot evidence.
