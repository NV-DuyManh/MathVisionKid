# Candidate-band OCR review — 2026-10-09

## Outcome

Added bounded source-band rereading, explicit uncertainty for symbolic equations,
and protection against conflicting original questions. **328 selected regression
tests passed**. Saved **15 new source responses** and **four repeat comparison
readings**. The inventory now has **329/1,319 source IDs with saved responses and
990 pending**. These are prediction counts, not full-photo accuracy.

## Implementation

- Ordinary-row count disagreement can use full-width padded source bands in the
  existing second request. The full original page is retained at the top. The
  sheet is bounded to 35 candidates, a maximum source dimension of 1,400 pixels
  and a total band height of at most twice the source height; over-budget inputs
  are rejected rather than truncated. Fraction ink and grouped fraction/division
  paths keep their existing complete-layout review.
- The second reply can use positional candidate groups, each containing zero,
  one or several actual rows. IDs must appear exactly once in source order. Mixed
  flat/grouped content, missing IDs and duplicate IDs are rejected. A legacy flat
  reply still faces the existing identical-content guard. The internal groups
  never appear in the student API contract.
- New breaks can replace the first boundaries only when complete ordered text,
  word/numeric whitespace boundaries and roles agree. Original uncertainty
  propagates. Any non-singleton candidate grouping prevents automatic geometry;
  all rows remain uncertain with no boxes. Touching envelopes retain that same
  protection. Changed digits, operators or duplicated content cannot substitute
  for the first transcription.
- A selected question that differs between readings, including a number/operator
  disagreement, is cleared and requires the pupil to clarify the original task.
  First transcribed lines are preserved. EQUATION rows such as `a + b = c` receive
  independent review even when they contain no digits.

This adds no provider call beyond the existing bounded second request and uses
the existing Pillow/OpenCV renderer. It adds no dependency, calculated OCR repair,
known-image rule, model training or production checkpoint replacement.

## Actual evidence and limits

| Measure | Result |
|---|---:|
| Previous unique source responses | 314 |
| New source responses | 15 |
| Current unique source responses | 329 |
| Pending sources | 990 |
| New WORK / MULTIPLE / UNREADABLE | 2 / 10 / 3 |
| New responses containing rows / predicted rows | 2 / 24 |
| Repeat readings excluded from coverage | 4 |
| Promoted reference labels / training runs | 0 / 0 |

Flat-band version: four new responses, followed by a provider stop. After honoring
the saved deadline, the final grouped version saved eleven more and stopped on
another provider failure. Logs record a server error, timeout/malformed fallback
failure and disabled fallback credentials due to authentication errors. The final
stop record/deadline is saved; neither run reached its planned new-read budget.
No quota/key sweep or new queue name was used to bypass a live deadline.

Source-linked checks:

- **Lớp 5/IMG/20.jpg:** the flat panel reread still returned four rows for five
  visible baselines. The grouped experiment split the final wrapped prose into
  two rows, but repeated another explanatory row and changed notation. Its six
  rows therefore failed the content/count guard; the final response retains the
  first four uncertain rows without boxes. This is not a successful final row
  correction. No deduplication by guessing was applied.
- **NEW2/IMG/20.jpg:** the flat comparison still merged prose and retained the
  questionable first operand with uncertainty. No arithmetic replacement was
  inserted.
- **NEW2/IMG/208.jpeg:** the comparison still reads the vertical multiplication
  sign as `+ 8`, with incomplete table cells. All fourteen rows are uncertain;
  neither operator accuracy nor table completion is claimed.
- **NEW2/IMG/217.jpeg:** visibly contains multiple independent school division
  setups; MULTIPLE fits the one-exercise endpoint. This is classification, not
  transcription of every division field.
- **NEW2/IMG/218.jpeg:** contains Vietnamese-language work, so UNREADABLE is
  appropriate for this math endpoint. The source is retained.
- **Lớp 5/IMG/22.jpg:** contains several worked calculations. The source's written
  erroneous results are retained rather than repaired using arithmetic; a
  crossed-out value and its adjacent operator remain uncertain. The seven-row
  response is not approved as complete/correct geometry or training text.
- **NEW2/IMG/222.jpeg:** source-reviewed addend `3992` and final row `73992` are
  predicted as `3991` and `73991`. Two answer rows (`Mai: 9 tuổi`, `Mi: 6 tuổi`)
  collapse into one answer and lose information. Its three unfinished equals-sign
  rows remain unfinished. All seventeen rows remain uncertain with no boxes;
  this response is unapproved and its wrong digits are not source labels.

Earlier successful responses are compared byte-for-byte with the preceding Drive
archive. Originals are read through hash-verified mounted G mappings; no image
batch is copied into the repository. Source observations are separate from raw
predictions and never automatically promoted to labels.

## Validation and continuation

**328 tests passed** across notebook classification, symbolic/numeric review,
band rendering/group safety, fraction/division layout, capacity, handwriting
geometry, generalized segmentation, lessons, source storage, resumable queues
and training-gate safety. Two existing framework deprecation warnings remain.
The internal inspect API contract is covered. No runtime restart, physical-device
test, commit or push is claimed.

Final reader fingerprint:
`9816e1c4aba4936a77c08b1d87b65b0d75a3b9be088c5525a74f7583856470b7`.
Resume only `all_current_20261007/cloud_groupedsafe1001_20261009`, honoring its
saved backoff; see `docs/OCR_REVIEW_AND_TRAINING.md`. The old flat-band outputs
remain immutable. The intermediate `cloud_grouped1001_20261009` and
`grouped_compare1_20261009` plans were never invoked. The comparison batches are
historical evidence, not pending queues.

Local evidence is in `infra/local-runtime/logs/ocr-candidate-bands-20261009`,
including final regressions, provider logs, literal grouped comparison trace,
queue plans and source review. The private archive is
`ocr-candidate-bands-20261009.zip` under the existing G Drive archive directory.
Its receipt and `docs/drive-archives.json` record hashes/readback and a selected
fresh restore. A mounted readback does not independently prove Google's completed
background upload. Working evidence is retained.

Remaining work: pending photos, reviewed separation of multiple exercises,
literal ambiguous glyphs/operators, table cells and unresolved row duplication.
There is no model-accuracy percentage or claim of perfect recognition.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: minimal shared OCR/backend changes using existing tools.
  - Applied to: bounded panel reuse, positional response validation, disagreement
    guards, focused safety regressions and immutable resumable evidence.
