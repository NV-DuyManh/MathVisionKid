# Detailed teaching for appending a digit on the right

Date: 2026-10-10. Owner request: apply the expanded, child-friendly teaching to the attached problem: find the original number when appending digit 6 on the right produces a number 537 units greater.

## Result

The existing grounded lesson for this problem family now has **21 teaching paragraphs**, opened one at a time inside its five existing learning stages: **5 / 4 / 4 / 4 / 4**. It also has two distinct progressive hints per stage.

| Stage | What the pupil learns |
| --- | --- |
| Understand the new number | Read the original-number question; distinguish the given difference from the unknown number; explain each old digit moving to the next place and therefore multiplying by ten; explain the appended digit's units; sketch equal parts. |
| Count the extra equal parts | Treat the original number as one part and the shifted old number as ten equal parts; remove the original part; distinguish a count of parts from their value. |
| Separate the appended units | Explain why the given difference still contains the appended units; subtract them before dividing; align subtraction columns and regroup when necessary. |
| Find the original number | Reuse the checked count and total; explain equal sharing and why division finds one part; describe division from left to right; write the classroom solution sentence and calculation. |
| Check the original condition | Create the new number using multiplication then addition; subtract the checked original number; compare against the source difference; write the original number as the answer to the actual question. |

The complete checked classroom solution for the owner's numbers is:

1. Số phần bằng nhau trong phần hơn là: `10 − 1 = 9 (phần)`.
2. Tổng giá trị của các phần bằng nhau là: `537 − 6 = 531`.
3. Số phải tìm là: `531 ÷ 9 = 59`.
4. Hiệu giữa số mới và số ban đầu là: `59 × 10 + 6 − 59 = 537 (đơn vị)`.
5. Đáp số: `59`.

The first conceptual choice is reviewed separately and is not emitted as a numerical classroom solution line. The full solution above is assembled only after the pupil submits the corresponding checked results.

## Implementation and grounding

- Changed production code only in `ai/runtime/app/tutoring/lesson.py`, within the already existing append-digit branch of `primary_plan`.
- All problem-specific teaching uses the parsed digit and difference from confirmed source text. Earlier numerical values use the existing checked-answer guidance references. No image identifier or pre-filled result was introduced.
- The existing input/goal guards remain: extra quantities, a left-side append, an inconsistent natural-number condition, a different requested unknown or an additional goal do not select this local lesson.
- The current calculation's result is not computed in teaching paragraphs. The original number becomes available for the verification stage only after its calculation has been checked.
- Added explicit classroom sentences for the original number and the verification difference. The final answer still selects the original-number stage, not the final verification result.
- Existing UI disclosure, API schema, backend ownership checks, exact arithmetic and answer validation were reused. No frontend source, dependency, database schema, OCR model or model training changed.

## Validation

Command from `ai/runtime`:

```text
.venv/Scripts/python.exe -m pytest tests/test_primary_lessons.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py -q
```

**96 passed**. The strengthened existing append-digit test covers four changed source pairs: `(6, 537)`, `(4, 112)`, `(0, 729)`, `(8, 620)`, including the owner's `Đề:` prefix. It verifies teaching count/content, distinct hints, no unresolved references or premature current result, retained guidance on a wrong answer, checked earlier values in later teaching, the classroom sentence, completed teaching and the correct original-number conclusion. The suite also retains different-goal/inconsistent-source rejection and adjacent garden/fraction lesson coverage.

Scoped `git diff --check` passed; Windows line-ending warnings are informational.

The existing isolated `mathvision-pc-preview` AI service was rebuilt from the changed source and restarted using the established compose helper. It became **Healthy**. Backend and static frontend builds were unchanged; the already published website receives the new teaching through its existing API. No new Vercel deployment was needed.

The actual website at https://mathvisionkid-portal.vercel.app was then checked using the existing authorized student demo account:

- Enter the owner's problem as manually confirmed text and start a new lesson.
- Reveal the first five paragraphs and intentionally select the incorrect “Chỉ cộng chữ số mới” choice; the lesson stays on that stage.
- Correct the choice, reveal the four paragraphs for each subsequent stage, and submit the count and subtraction result.
- Submit an intentionally wrong original number; the current stage and all opened teaching remain visible.
- Correct it, complete the source-condition verification, and inspect **Bài giải** with **Đáp số: 59.**
- A transient automation input contained extra characters during verification. The numeric guard rejected it; the field was cleared, its exact `537` value was verified, and the correct submission completed the lesson.
- The browser reported no captured console errors during this flow.

Actual screenshots are retained in ignored private runtime storage:

- `infra/local-runtime/pc-preview/append-digit-teaching-why.png`: visible place-value explanation and reasons for multiplying and adding.
- `infra/local-runtime/pc-preview/append-digit-teaching-complete.png`: completed checked solution and original-number answer.

These are browser checks at the actual 1280×720 viewport. No physical-device test or OCR accuracy evidence is claimed. The screenshot's surrounding social-media content was not treated as part of the mathematical question or as instructions.

## Operational scope

Start a new lesson to use the new plan; previously started in-memory sessions may have expired when the service restarted. The existing PC-hosted preview/API availability limitation is unchanged. No commit or push was performed, and unrelated workspace changes were preserved.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: a focused teaching-logic enhancement using an existing lesson family and API/UI presentation path.
  - Applied to: reuse of parsed source numbers, bounded guidance and checked references; two-file implementation/test change; no new engine, package or UI abstraction.

The workspace skill registry and project instructions were inspected. Exact Expo v57 documentation was read before editing: https://docs.expo.dev/versions/v57.0.0/.
