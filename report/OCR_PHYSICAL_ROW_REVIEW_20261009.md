# Physical-row and task review — 2026-10-09

## Outcome

Improved ordinary handwriting row detection and conservative interpretation of
source text. Ran **331 passing regression tests**, **20 new source readings** and
**two independently requested repeat comparisons**. This is a bounded continuation,
not completion of the Drive inventory or a model-accuracy claim.

## Changes

- Tall connected letters can produce two projection peaks inside one physical
  row. The detector merges such peaks only when at least two substantial glyph
  bodies span both, and preserves their vertical ink support. It has no special
  source ID, expected arithmetic or fixed page-row count.
- A second ordinary-row transcription may supply corrected row breaks only when
  its ordered content, word/numeric whitespace boundaries and roles match the
  first reading, and its row count matches detected physical rows. Original
  uncertainty propagates to every affected child row. Changed digits, signs,
  missing text or roles cannot replace the first transcription. Fractions and
  school division blocks retain their grouped layout.
- Mismatched or touching physical envelopes remain uncertain and have no displayed
  boxes. Count agreement alone cannot certify complete strokes.
- Worked-material detection includes a division’s written quotient/working rows.
  Task validation examines the selected problem text, rather than unrelated
  question words elsewhere on the page. Genuine fill-in, comparison, conversion
  and symbolic/blank-box tasks survive when work is also present; phrases such as
  “Ta tính” and “Tính được” do not manufacture an original question.
- When the independent reading identifies only work and rejects the supposed
  original question, the app retains the first lines and requests the missing
  problem. No calculated correction is substituted into OCR output.

## Actual source evidence

| Measure | Result |
|---|---:|
| Full source inventory | 1,319 |
| Earlier unique sources with saved responses | 294 |
| New unique source responses | 20 |
| Current unique sources with responses | 314 |
| Pending sources | 1,005 |
| New responses with content / predicted rows | 2 / 17 |
| New MULTIPLE / UNREADABLE responses without rows | 8 / 10 |
| Repeated historical sources, excluded from coverage | 2 |
| Promoted reference labels / training runs | 0 / 0 |

The new queue ended with `batch_limit` and exit 2 because pages remain pending;
the invocation did not exhaust its queue. The log also records two disabled
fallback credentials due to authentication errors. This does not prove fallback
availability or complete image recognition.

Source-linked observations are recorded separately from predictions:

- **Lớp 5/IMG/20.jpg:** the detector now finds five rows instead of six; the
  previous implementation is reproduced from the committed detector for this
  comparison. The fresh provider response correctly stays WORK with empty
  original problem, but still merges the last two prose rows into one. All four
  predicted rows remain uncertain without boxes. Ascenders overlap between real
  rows, so five detected envelopes are not approved crop geometry.
- **NEW2/IMG/20.jpg:** the first operand and merged explanatory prose remain
  unresolved. The fresh response retains its predicted `68` with uncertainty;
  arithmetic is not used to manufacture a replacement.
- **NEW2/IMG/201.png:** contains language copying rather than a math exercise;
  UNREADABLE fits this math endpoint. The source is retained.
- **NEW2/IMG/208.jpeg:** table-cell transcription is incomplete and a vertical
  multiplication operator is predicted as `+ 8`. All 14 rows are uncertain. This
  prediction is not approved.
- **Lớp 5/IMG/21.jpg:** three visible rows and their written quantities match the
  inspected prediction at this spot check. WORK fits the crop; uncertainty is
  retained. This is not a dataset-wide accuracy measurement or training approval.

The two historical response files were checked byte-for-byte against the previous
Drive archive and remain unchanged. Original images were read through the
hash-verified mounted G mappings; no source-image batch was copied into the repo.

## Validation and continuation

**331 tests passed** across notebook task classification, numeric/fraction/division
reading, capacity, ordinary/short/tiny row geometry, generalized segmentation,
guided lessons, source storage, cloud queue and training-gate safety. Two existing
framework deprecation warnings remain. The internal inspect API contract is
covered by these tests. `git diff --check` passed with normal LF/CRLF notices.

The new reader fingerprint is
`92cf8073bf6d3dfa1e101564306fc5ee492887e89668ff8e0c4b4850aacc0556`.
Resume `all_current_20261007/cloud_rowreview1025_20261009` using the instructions in
`docs/OCR_REVIEW_AND_TRAINING.md`; completed reads are skipped. The earlier
`cloud_workguard1025_20261009` contains only an uninvoked historical plan.

Local evidence is under `infra/local-runtime/logs/ocr-row-review-20261009`:
`regression.txt`, `cloud-run.txt`, `comparison-run.txt`, `source-review.json`, and
`queue-plans.json`. The development services were not listening during this phase;
no runtime reload or physical-device test is claimed. Changes load on the next
normal app startup. No commit or push was performed.

Remaining work includes the 1,005 pending pages, table layout, literal ambiguous
glyph review and unresolved merged prose. No percentage, full-corpus success or
OCR weight improvement is claimed. Read the required
[versioned Expo reference](https://docs.expo.dev/versions/v57.0.0/) before editing.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: shared OCR/backend fixes using the existing bounded reader.
  - Applied to: task guard, row detector, identical-content boundary reconciliation,
    conservative geometry, focused regression checks and resumable evidence.

Google Drive file guidance was read to preserve the existing mounted organization.
No sharing, ownership, source deletion or automatic label promotion was performed.
