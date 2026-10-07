# Long division: faithful reading and student repair

Date: 2026-10-07

The three owner-supplied photos now have a complete path from a structured reading to editable numbers, explicit pupil confirmation, deterministic arithmetic feedback, and rechecking after correction. A wrong handwritten answer stays wrong in the transcription; the reader does not substitute a calculated answer.

## Exact-photo evidence

The existing position-aware reader was run on the original bytes of all three new attachments, before and after exposing its structured fields to the app. Both runs preserved every visible field in these examples.

| Photo | Written operands | Written quotient | Written left rows, top to bottom | Final read |
| --- | --- | --- | --- | --- |
| 1 | 49572 : 6 | 8262 | 015; 037; 012; 00 | All fields match visual reference |
| 2 | 17843 : 3 | 59947 | 028; 014; 023; 02 | All fields match; reading flagged for review |
| 3 | 87268 : 3 | 2989 | 27; 0026; 008; 01 | All fields match visual reference |

This is **3/3 supplied examples**, not a claim of perfect recognition on unseen images. Recognition still uses the configured vision provider; arithmetic checking uses no provider call. No weights were trained or replaced in this phase.

Original-image SHA-256 values, exact outputs, timings, manually reviewed transcriptions and code hashes are recorded privately in `infra/local-runtime/logs/math-layout-20261006/user_examples_final/assessment.json`. Original photos and private evidence remain outside Git. The local `assess_user_examples.py` verifies that source bytes have not changed. These records are not promoted to training labels.

## Student flow

1. Show the masked source photo with editable dividend, divisor, quotient and each working row. Keep leading zeroes.
2. Let the pupil add a missing row in the middle or at the end, remove an extra row, and correct misread numbers.
3. Require explicit confirmation before grading. Empty or unresolved fields cannot be submitted.
4. Highlight the relevant quotient or row and give a short division-step hint. Do not fill in the correct answer automatically.
5. After any edit, invalidate the previous verdict and cancel any pending request. A late response cannot overwrite the new work. Retry retains input after connection errors.
6. Reopen saved canonical division text as editable fields; do not grade it automatically.

An isolated division no longer forces the pupil to photograph a word problem before checking its arithmetic. The UI explicitly distinguishes arithmetic checking from judging whether a step solves a word problem.

## Arithmetic behavior

- Photo 1 passes with its exact written rows.
- Photo 2 points to the third quotient digit (14 divided by 3). Correcting `59947` to `5947` passes with the original four rows and remainder 2.
- Photo 3 first points to the missing zero in the quotient (the partial dividend 2 is smaller than 3). Correcting the quotient to `29089` still requires reviewing the missing working row. The complete compact rows `27, 002, 0026, 028, 01` pass; `008` is reported at its exact row once the missing row is supplied.
- Verify every compact brought-down partial and the final remainder, including zero dividend, divisor larger than dividend, multi-digit divisors, inner/trailing zeroes, leading zeroes and numbers up to 12 digits.
- Unclear symbols, division by zero, larger numbers, different row counts or explicit subtraction layouts require review. They do not receive a blanket success verdict. This phase checks the compact school notation shown in the three examples; it does not certify every possible written-division layout.

## Implementation

- `ai/runtime/app/tutoring/notebook.py`: expose optional `division` transcription while keeping internal layout evidence private; retain legacy text and uncertainty fields.
- Business API: bounded structured DTOs, validated reader response, and authenticated `POST /api/v1/student/tutor/division/check`. Existing student-role enforcement remains authoritative. `DivisionChecker` is deterministic and requires no new service or dependency.
- Student Mobile: `DivisionReview` in the existing learning screen, existing typography/colors/buttons, labelled controls, 48 px row actions, inline feedback and announced status. Restore structured editing from saved canonical text.

## Validation

- Python: **141 passed** (`test_notebook_math_layout`, `test_notebook_tutor`, `test_notebook_capacity`, `test_math_tutor`). Existing Starlette/httpx and AnyIO deprecation warnings remain.
- Java: **78 passed** — 6 checker, 46 service, 26 controller tests. Includes real checker calls through authenticated controller requests, wrong-answer-to-correct-answer repair, anonymous/other-role denial, invalid inputs and explicit confirmation.
- Mobile: **45 passed** across `tutorScreen.test.tsx` and `tutorApi.test.ts`. Includes edit/confirm/recheck, unresolved fields, inserted/deleted rows, saved work, cancellation and stale response rejection.
- TypeScript: `npx tsc --noEmit` passed.
- Scoped ESLint: learning screen, `DivisionReview`, and `TutorService` passed after extracting a proper field component for React Compiler compatibility.
- Browser: inspected the actual mobile web UI at 375×812 and 812×375 using an isolated mock-login development instance; manually inserted/deleted a row, edited the quotient and enabled checking only after confirmation. The browser did not exercise a live grading backend; that boundary was verified through the controller/service tests. No physical Android/iOS device evidence is claimed. Native keyboard, large system text and screen-reader behavior still need device QA.
- Private screenshot: `infra/local-runtime/logs/math-layout-20261006/division-review-375.jpg`.

No commit, push, model training or production deployment was performed. Existing unrelated working-tree changes were preserved. Restart the normal local stack to load the new backend endpoint and app code together.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bounded implementation using existing tutor boundaries and native arithmetic.
  - Applied to: checker, API extension, reuse of existing saved-text format; no new dependencies.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native state, async request handling and rendering.
  - Applied to: controlled fields, event-driven validation, stale-request cancellation and stable field component.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: student correction flow and accessible inline validation.
  - Applied to: existing visual language, visible field labels, touch targets, error placement, confirmation and responsive browser review. Focused UX query: `error summary validation`.

Expo v57 documentation was read before implementation: https://docs.expo.dev/versions/v57.0.0/.
