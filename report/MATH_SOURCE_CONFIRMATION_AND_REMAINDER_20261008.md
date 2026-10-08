# Source confirmation, handwritten mathematics and remaining-image review

Date: 2026-10-08. Scope: finish the proposed source-safety, real-math,
remaining-crop, pending-15 and running-app checks.

The app now requires explicit confirmation of the source text before creating
a guided lesson. Long division uses the complete source image alongside its
position crops, and unknown written digits remain editable uncertainty. The
15 pending entries from the previous bounded cohort are complete. Recognition
is **not perfect**: unresolved crops and actual digit mistakes remain recorded.

## Implemented behavior

- The mobile screen, Java business API and Python lesson request enforce
  `problemConfirmed`. Nonblank `workText` also requires `workConfirmed`.
  Omitted or false confirmation and `[?]` markers cannot start a lesson.
- New photos and text edits invalidate the relevant confirmation. The student
  can inspect the image, edit the text and explicitly accept it. The checkboxes
  expose accessible labels, checked state and disabled state.
- An unconfirmed work transcript is excluded from lesson creation. A confirmed
  problem can still be used for guidance while its accompanying work awaits
  review. Restored drafts retain only their explicitly saved confirmation.
- Division bracket detection rejects numeral diagonals more strictly and joins
  short interruptions in an actual vertical bracket. Four labelled position
  panels now include a fifth, unchanged **full source** image. A working row
  crossing the bracket can therefore retain its complete last digit.
- An embedded unread letter in a provider's numeric working row becomes an
  explicit unknown: `0M5` becomes `0[?]5`, never a guessed `015`. The raw
  provider output remains preserved; invalid operands and commands remain
  invalid. This adapter does not calculate missing digits or repair pupil errors.
- Exactly one structured division can be reviewed even when a companion note
  is present. Editing it preserves the other transcribed lines and displays
  them separately. Multiple divisions retain the existing selection fallback.
- Authentication, student ownership and role checks remain authoritative in
  the business API. A teacher cannot invoke the student lesson route.

Main implementation: [mobile guide](../apps/student-mobile/src/app/learning/math-guide.tsx),
[mobile request](../apps/student-mobile/src/features/tutoring/api/TutorService.ts),
[business validation](../backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutorDtos.java),
[Python lesson contract](../ai/runtime/app/tutoring/lesson.py),
[layout](../ai/runtime/app/tutoring/math_layout.py) and
[source reader](../ai/runtime/app/tutoring/notebook.py).

The lesson request contract deliberately requires the new confirmation fields;
older clients must be updated. Student confirmation is a review step, not
independent proof that every symbol is correct.

## Actual mathematics images

The bounded development cohort contains **18 selections from five original
Drive photos**: nine individual long divisions, seven fraction selections and
two pages containing multiple exercises. Original and crop SHA-256 values,
crop coordinates, raw predictions and code hashes are preserved separately.
Original source bytes were read through the existing storage index; the whole
dataset was not restored into the project.

| Observation | Saved result |
| --- | --- |
| Division bracket candidates on nine individual crops | Improved from 7 to 9 after the geometry change |
| Structured division in the first saved final-cohort read | 8 / 9 |
| Remaining division crop | Its first read stays unstructured; a separately saved provider retry returned a reviewable division and companion note, with `0[?]5` |
| Seven fraction selections | Returned as complete expression groups or continuation groups, rather than isolated numerator/denominator rows |
| Two full pages | Both classified `MULTIPLE`; their empty transcripts are not full-page reading success |
| Clear `13/2` source | Provider predicted `13 1/2`; the incorrect prediction and uncertainty remain recorded |

Overwritten quotient and working-row digits also remain uncertain. Source
grouping and bracket detection do not establish character accuracy. These are
development selections, not a held-out benchmark; no aggregate transcription
accuracy or automatic label approval is claimed. The initial failed read was
not replaced by the successful retry to make the first-read result look better.

The configured provider encountered availability errors twice during the
bounded runs. Batches stopped and resumed after cooldown; no keys or provider
configuration were changed to bypass those failures.

## Remaining crops and pending page reads

All **13 previously unresolved writing crops** and **seven clipped fragments**
were revisited against hash-checked source bytes. The writing crops received
52 bounded experiments: original, background normalization, normalized CLAHE
and a small source median filter. Eight produced candidate boxes, but source
overlays showed missing word ends, overlapping rows or merged baselines.
**None was promoted into production geometry or verified training labels.**
The 13 remain unresolved. The seven clipped sources need larger originals;
missing strokes cannot be reconstructed reliably from these fragments.

The line detector and its learned weight did not change in this phase. The
previous [paper-texture phase](PAPER_TEXTURE_AND_TRANSCRIPT_REVIEW_20261008.md)
already checked 1,671 local sources and preserved 1,500 regression results.
Those historical counts are not presented as new full-corpus calls here.

The previous bounded 100-entry cloud cohort is now complete across its separate
85-read and 15-read folders. The earlier 85 output files were verified
byte-identical. The new 15 classifications are two `PROBLEM`, six `WORK`, four
`MULTIPLE` and three `UNREADABLE`. These remain provider predictions.

Across the original **1,319-page queue, 139 reads are saved and 1,180 remain
pending**. This phase did not complete all Drive page transcriptions. No source
was deleted on the basis of an empty detection or `UNREADABLE` classification.

## Verification

| Check | Result |
| --- | --- |
| Python regression and request tests | 428 passed; four existing deprecation warnings |
| Mobile screen, API and privacy tests | 53 passed in three Jest suites |
| TypeScript type check | Exit 0 |
| Java tutoring controller/service/checker tests | 80 passed in three suites |
| Authenticated local HTTP checks | 13 passed |
| Actual photo through business API → AI runtime | HTTP 200 with a structured division; transcript accuracy not certified |
| Running service application | Owned AI runtime restarted with final code; health and readiness HTTP 200 |

HTTP checks cover missing/false confirmation, unconfirmed work, unread digits,
anonymous access, teacher-role denial, confirmed lesson creation, incorrect
answers retaining the current step, and incorrect written quotient checking
without exposing the correct answer.

The actual browser app was checked at desktop size and a **390 × 844 browser
viewport**: initial start disabled, explicit confirmation enabling start,
five-step lesson creation, a wrong answer keeping step one, editing cancelling
the lesson, and an unread marker preventing start. Screenshots are preserved in
the private evidence archive. **No physical Android/iOS device was tested.**

Run the repeatable checks from the indicated project directories:

```powershell
# From ai/runtime
& .\.venv\Scripts\python.exe -X utf8 -m pytest `
  tests/test_text_detector.py tests/test_handwriting_rows.py `
  tests/test_short_row_recovery.py tests/test_short_row_marks.py `
  tests/test_tiny_row_ends.py tests/test_generalized_segmentation.py `
  tests/test_segmentation_contracts.py tests/test_notebook_math_layout.py `
  tests/test_notebook_tutor.py tests/test_notebook_capacity.py `
  tests/test_math_tutor.py tests/test_live_path_contracts.py `
  tests/test_guided_lesson.py tests/test_primary_lessons.py -q

# From apps/student-mobile
npm test -- --runInBand src/__tests__/tutorScreen.test.tsx `
  src/__tests__/tutorApi.test.ts src/__tests__/privacyScreen.test.tsx
npx tsc --noEmit --pretty false

# From backend/business-api
.\gradlew.bat test --tests 'com.mathvisionkids.api.tutoring.*' --console=plain
```

## Evidence and handoff

Archive `math-source-safety-20261008` is registered in
[the catalog](../docs/drive-archives.json), on the mounted private Drive under
`G:\My Drive\Dự án\MathVisionKid\Lưu trữ`.

- ZIP: 18,722,442 bytes; 189 files; 19,388,305 source bytes.
- SHA-256: `7e9fcdc03157fa74ce21a880fa863035418eae278c9cdd36d499af5c7f4d2097`.
- All archived entries were read back and hash-verified. A fresh selected
  restore reproduced `phase-verification.json` byte for byte.
- Includes source selections, previews, baseline/final predictions, the separate
  failed-read retry, remaining-crop experiments, cloud-15 results, code/test
  snapshots, Java XML results, HTTP receipts and browser screenshots.
- Launch logs, local authentication helpers and credentials were excluded.
- Drive background upload completion is not independently verified; small
  working evidence is retained locally. Original datasets remain on Drive.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id math-source-safety-20261008 `
  --prefix 'infra/local-runtime/logs/math-source-safety-20261008'
py -3 .\scripts\data\restore_drive_archive.py --id math-source-safety-20261008 `
  --prefix 'ai-training/datasets/drive_math/all_current_20261007/cloud_pending15_20261008'
```

Read [the storage guide](../docs/DRIVE_DATA_STORAGE.md) before restoring or
resuming. Preserve the older 85 outputs and the separate new 15; do not rerun
the old cohort blindly or merge unverified predictions into approved labels.
Historical comparisons require their saved code and source hashes.

Unchanged detector weight SHA-256:
`03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587`.
No model training, weight replacement, commit or push occurred in this phase.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: extend existing source, contract, review and archive paths
    with small bounded changes and no new dependencies.
  - Applied to: confirmation contracts, division panels, unknown-digit
    preservation, bounded source experiments and evidence verification.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: the task changes the existing React Native tutoring flow.
  - Applied to: explicit state, request cancellation, draft restoration,
    independent source confirmation and preserving companion lines.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: new interactive source-confirmation controls need meaningful
    labels and exposed state.
  - Applied to: confirmation checkbox roles, labels, checked/disabled state
    and visible correction guidance.

The exact [Expo v57 documentation](https://docs.expo.dev/versions/v57.0.0/)
was read before implementation.
