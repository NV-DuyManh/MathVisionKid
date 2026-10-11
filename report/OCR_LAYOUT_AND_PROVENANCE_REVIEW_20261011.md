# OCR layout and reproducible batch recognition — 2026-10-11

The batch recognizer now rejects stale detector geometry and validates oriented image dimensions before inference or cache reuse. A newly reviewed three-page cohort confirms that the improved private model still fails the release gate. The most significant layout failure is a two-column page whose printed exercises and pencil handwriting are grouped into broad horizontal bands. **Production weights, vocabulary, provider and segmentation remain unchanged.**

## Implemented change

`scripts/data/recognize_line_batch.py` now requires the detector dependency hashes recorded by `audit_text_regions.py`: the five segmentation/API source files and the optional pinned detector artifact. Resolve dependency paths within the runtime directory, reject missing/incomplete provenance and changed dependencies, and pin absence of the optional model so installing it invalidates earlier geometry. Verify exact EXIF-oriented image dimensions in addition to source SHA-256 and integer crop bounds. Include a deterministic detector-provenance digest in resumable recognition signatures; identical rectangles do not make a changed detector version reusable. Malformed metadata fails the individual image before recognizer calls. Recognition drafts still cannot become verified references or training labels.

An old batch should be regenerated into a **new evidence batch/snapshot** using the original source paths. Preserve previously frozen region files and evaluations. This change does not automatically rerun, overwrite or approve the original 266-image evidence.

## Inspected punctuation prototype — rejected

Reused the existing detached-mark helper to attempt narrowly bounded suffix recovery from blue ink, at working resolution no larger than 1280 pixels. Synthetic checks covered period/colon preservation, immutable vertical bands/source pixels, neighboring regions, fractions, rulings, unsupported texture and inference count. The prototype passed its focused tests, but later visual inspection of TRAIN-page suffixes showed that a small connected fragment of a neighboring letter could also qualify as punctuation. This is unacceptable for a default OCR crop policy.

Archived the exact prototype and tests privately, then restored the two production segmentation files byte-for-byte. A successful unit suite is insufficient evidence of recognition quality. The prototype is **not enabled**, and no punctuation-improvement claim is made. Initial frozen geometry measurements describe that inspected prototype; the compared reference boxes were unchanged by it. No thresholds were tuned on the newly scored references.

## New reviewed references and independence

Reviewed full sources and individual crops before scoring. Final fresh cohort: **16 lines / 237 characters**, comprising **5 expressions and 11 prose lines**, from pages 960, 961 and 776. Excluded ambiguous pencil spelling, crossed-out arithmetic, and three candidate crops containing neighboring-row ink. Corrected crop envelopes to include visible colons/periods before freezing. Labels retain visible spelling and numbers; arithmetic is not used to supply an OCR answer.

Rejected page 958 as fresh evidence because its byte hash is identical to previously reviewed TRAIN page 938. Excluded alternate capture 969 of page 960. Existing source-hash/pixel/crop split checks pass. Reclassified the preceding phase's already scored 16 HOLDOUT records as development TRAIN only in this new manifest, with explicit exposure notes; prior evidence is untouched. No training occurred in this phase. The new pages had earlier unverified production drafts, but no reviewed score or fitting/checkpoint-selection use. Writer independence is unknown; these notebook exercises may share writers and book styles.

## Frozen comparison

Kept the previous DEV-selected candidate, checkpoint `c903700319799628c62d322045382b464dc0df83a052e1f04c045635848b40f4`, unchanged. Frozen manifest SHA-256: `6efa8b8a9292713f8d7ede960e0ef5da4a0908602e1069a1033a37c070eb69ad`. Compare literal greedy CTC decoding with the candidate's aspect preprocessing and production's original fixed preprocessing; no answer correction or model fitting.

| Selected manual crops | Production baseline | Private candidate |
|---|---:|---:|
| CER, 16 lines | 28.27% | 7.17% |
| Exact lines | 2/16 | 4/16 |
| Critical digit/operator/punctuation edits | 11 | 2 |
| Expression CER, 5 lines | 51.43% | 10.00% |
| Prose CER, 11 lines | 18.56% | 5.99% |

The candidate confuses `28 : 4 = 7` with `28 : 4 = 1` and drops a sentence-ending period. Other literal errors include accents, word spacing and parentheses. CER includes literal spaces and punctuation; it is not an overall OCR accuracy percentage. The release gate still fails: CER exceeds 5% and critical errors remain.

For the detector-to-recognizer diagnostic, match selected references one-to-one by descending IoU at threshold 0.5. Unmatched references emit empty text and count as deletions. Twelve references match on the two blue-ink pages; **0/4 pencil references match individually** on page 776. That page's detector output contains wide bands spanning both printed and handwritten columns; the failure is separation of individual lines, not proof that no pencil pixels were detected. Do not count these oversized mixed-column bands as correct line crops.

On all 16 references using detected crops, baseline CER is **56.54%**, candidate CER **36.71%**; exact lines 0/16 → 2/16, critical edits 18 → 9. Cached original and prototype geometries yield the same reference crops and scores. This identifies an important layout weakness despite the better manually cropped recognizer. Partial annotation cannot establish whole-page precision/recall. The crop-policy comparisons share the same references and are not additional independent trials or physical-device/API-flow evidence.

## Verification and outcome

**174 tests passed on the final retained implementation** across detector geometry, short-row recovery, tiny-row endpoints, batch recognition, source storage, bounded training and archive audit. New provenance cases check changed code/model, missing dependencies, wrong oriented shape, escaping paths, malformed boxes, same-box detector-version invalidation and pinned model absence. The rejected prototype had its separate passing synthetic suite, which is not counted as a retained production improvement.

Verified all 266 original SHA-256 hashes (238 unique), and checked that the three evaluation PNGs match the corresponding EXIF-oriented source pixels exactly. Verified frozen candidate/model/provider pins; production segmentation was restored to its original hashes. Earlier frozen measurements and private references remain preserved. New images, labels, checkpoints and prototype snapshots remain Git-ignored. Unrelated cloud/deployment work is unchanged. No model promotion, paid service, deployment, student UI/mobile change, commit or push occurred.

Private evidence: `ai-training/datasets/drive_math/new2_20261011_266/crop_development/`. Frozen evaluation SHA-256: `d9cc51b9f3f5eec06a0aa04f1d558fb452268fae499d5fddd00b3c05fc07957f`. This evidence remains diagnostic; the 16 references are now exposed and must not be presented as a fresh test in future work.

Remaining work: separate columns without flattening tables/fractions, preserve low-contrast pencil lines, distinguish digit/operator shapes, and validate complete page geometry and recognition on a larger newly reviewed cohort. The improved weights remain private until those release checks pass.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: repair an existing evidence-reuse bug and test concrete OCR limitations without introducing another pipeline or dependency.
  - Applied to: source/provenance validation, existing draft resume signature, reused geometry helpers and validation tools, focused tests, and removal of an unsafe prototype from production.
