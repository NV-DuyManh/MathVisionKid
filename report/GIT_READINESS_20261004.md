# Readiness fixes — 2026-10-04

## Decision

The original two segmentation test failures and all 13 mobile lint errors / 26
warnings are resolved. Final offline checks pass. Keep the owner's conditional
Git push on hold: one reviewed image still produces extra annotation regions,
and the unverified dataset cannot be described as completely accurate.
No commit or push was performed; changes remain in the working tree.

## Changes verified

- Notebook-rule suppression now requires original ink support, preserving small
  letters while removing solid and dashed ruling lines.
- Learned fragments merge across gaps only when source pixels contain continuing
  writing. Contained duplicates are removed. Gap preprocessing is bounded to
  1280 pixels while output coordinates remain in the original image. The
  measured 4032×3024 example dropped from about 11.1 seconds to 0.9 seconds.
- Short rows such as `là:` recover only with learned and physical letter-body
  agreement. Existing envelopes remain intact; expressions, fractions, isolated
  accents and noise are protected. Recovered geometry is marked for review.
- Empty landscape results can use the optional detector, including readable
  narrow strips and column layouts. Student requests never download weights;
  missing/invalid optional weights retain the existing path.
- Very tight strips retain the established detector rather than treating parts
  of a letter as page-level rows. Isolated sparse paper-edge regions now receive
  the existing density check while valid boundary words are preserved.
- Cache identity includes image shape and region limit. Disagreement between
  chromatic and classical counts is flagged for review.
- Mobile request state resets on image/submission changes. A → pending B → A
  waits for a fresh A response; late B cannot show stale grading or analytics.
  Hook dependencies, render-time refs, confirmation, progress state and unused
  imports were corrected without disabling lint rules.
- Legacy tests exercise current routes and the actual `lineReview.ts` helper.
  Immutable OCR, arithmetic, confidence provenance and explicit selection
  assertions remain. Error-path fixtures explicitly supply uncertainty instead
  of depending on a model making a particular spelling error. The lesson
  answer-withholding assertion excludes only its opaque random session ID.

## Final verification

| Check | Result |
| --- | --- |
| Student mobile Jest | **37 suites, 390 tests passed** |
| Student mobile lint | **0 errors / 0 warnings** |
| Student mobile TypeScript | Passed |
| AI offline suite | **948 tests passed**, 86 test files |
| Dataset/archive workflow tests | **13 tests passed** |
| `git diff --check` | Passed |
| Fresh local image audit | **604/604 processed**, no execution failures, out-of-bounds boxes or region-limit overflow |

The final AI run blocked real HTTPX transports. It selected `tests/test_*.py`
except nine live-service/model-catalog suites: `test_groq_live_migration.py`,
`test_groq_production_route.py`, `test_gemini_live.py`, `test_submit_400_fix.py`,
`test_minio_pipeline.py`, `test_prod2b_trigger.py`,
`test_prod2e_gemini_migration.py`, `test_prod2f_release_gate.py`, and
`test_gemini_model_migration.py`. Exclusions are not passes or disabled tests.
Evidence: `infra/local-runtime/logs/ai-readiness-postfix.xml`.

Commands from the repository root:

```powershell
npm test --workspace=student-mobile -- --runInBand --silent
npm run lint --workspace=student-mobile
```

Run `npx tsc --noEmit` in `apps/student-mobile`. In `ai/runtime`:

```powershell
.venv/Scripts/python.exe -m pytest ../../scripts/data/test_drive_line_batch.py ../../scripts/data/test_archive_audit.py -q --tb=short
```

## Image evidence and limits

Private batch: `ai-training/datasets/drive_math/readiness_recheck_20261004/`.
Every image was rerun. All 604 source SHA-256 values match the frozen selection
and baseline; all result code/model hashes match final source files. Reviewed
labels were preserved. No model training was performed.

| Development-set measure | Before | Final |
| --- | --- | --- |
| Correct counts, 33 previously reviewed images | 28/33 | **32/33** |
| Correct counts, 22 geometry-reference images | 20/22 | **22/22** |
| One-to-one region matches at IoU ≥ 0.5 | 146/148 | **146/148** |
| Geometry-reference images matching every region at that threshold | 20/22 | **20/22** |

The two recovered short rows have pixel-supported envelopes but do not reach
IoU 0.5 against the existing manual rectangles. Count recovery does not prove
perfect geometric overlap or recognized text.

596 images have candidate regions. The eight empty results are seven visually
inspected paper/fabric/background crops and one severely clipped strip of stroke
fragments. Earlier readable misses at indices 249 and 573 now each have one
region. The multi-column crop at index 239 has 32 candidate regions and still
needs layout review. Index 499 contains a small visible date; this is not a math
exercise. Local detection p95 is **727.05 ms**, excluding OCR transcription,
tutoring, network and phone end-to-end latency.

**Remaining known error:** index 243 contains three equations plus curved arrows
and produces five regions. It is now flagged `needs_review=true`. A simple
component-size rule was rejected because arrow/parenthesis pieces resemble real
characters; it could remove valid writing. Annotation association is unfinished.

Reference statuses: 14 fully reviewed, 8 geometry-only, 11 count-only and
**571 not independently verified**. These are development references, not a
held-out accuracy estimate. OCR transcription accuracy was not measured.
`local_summary.json` and `reference_comparison.json` preserve detailed evidence.

## Release scope

Live-provider recovery, full backend/web readiness and physical-device behavior
were not established by these checks. Historical pending cloud readings remain
pending. Private images, labels, ledgers, logs, environment files and weights
remain ignored by Git. No new binary or credential payload was found in the
source diff. Expo v57 documentation was read; dependencies were not upgraded.
Backend and teacher/admin/portal source files were not changed.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: root-cause fixes using existing helpers and dependencies.
  - Applied to: segmentation, bounded preprocessing, cache correctness,
    regression fixtures, dataset verification and conditional Git decision.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native request lifecycle and rendering corrections.
  - Applied to: effect dependencies, derived state, cancellation, identity
    changes and stale-result regression tests.
