# Detailed teaching inside each solution step

Date: 2026-10-10. Owner request: a short written solution must still teach the pupil how and why to do each smaller calculation. The previous explanation and two hints were too brief to provide that teaching reliably.

## Result

Each solution step now includes **Cùng làm từng ý**, with numbered teaching paragraphs opened using **Xem ý tiếp theo**. Earlier paragraphs remain visible. Opening a paragraph is a local UI action: it neither submits an answer nor clears the pupil's input. The pupil still calculates and submits the result; a wrong answer stays on the current step.

The confirmed garden problem has three classroom solution steps, containing **6 / 4 / 5 teaching actions**:

1. Understand the meaning of both source fractions, why the groups are added, why their parts need equal sizes, how to subdivide each fraction, how to add equal-sized parts, and how to write the solution sentence and calculation.
2. Reuse the previously checked combined fraction, explain the whole as one and as an equal-numerator-and-denominator fraction, subtract equal-sized parts, and write the sentence describing the remaining fraction.
3. Connect the given tree count to the previously checked remaining fraction, divide to find one equal part, multiply to find the whole, explain the order of those operations, and write the sentence, calculation and tree unit.

These are teaching actions **inside** the written solution steps. Selecting a denominator is not presented as a separate classroom solution line. Fractions reuse the existing stacked numerator/bar/denominator renderer. After a correct submission, the existing pause shows the classroom line and calculation details. Once all steps pass, **Bài giải** contains the checked solution and **Đáp số**.

The lesson-generation prompt now requests 3–6 ordered teaching paragraphs per solution step, including prerequisite meaning, reasons, smaller calculations and classroom writing. Existing plans without the new field receive a compatible fallback assembled from their question, progressive hints and solution sentence. The garden family has explicit detailed teaching; this report does not claim that every generated explanation is equally good without further pupil review.

## Implementation and answer safety

- `ai/runtime/app/tutoring/lesson.py`: bounded guidance fields; detailed garden-family guidance derived from confirmed problem text; generation instructions; public presentation and completed-step retention.
- Guidance references can only address an **earlier calculation**. Current, future and concept-step references are rejected. References are resolved from the actual checked session answers, not private dry-run answers.
- Public content checks still reject unsupported computed numbers, malformed references, service addresses and developer details. Guidance never computes the current answer for the pupil. No answer is auto-filled.
- `backend/business-api/.../tutoring/MathTutorDtos.java` and `MathTutorService.java`: forward and validate at most six nonblank paragraphs of at most 500 characters each. Backend ownership and private-answer stripping remain in force.
- `apps/student-mobile/src/features/tutoring/api/TutorService.ts`: optional field for compatibility, with validation on current and completed steps.
- `apps/student-mobile/src/app/learning/math-guide.tsx`: local progressive disclosure, reset on a new step, retained input on reveal/wrong answer, checked-step reflection and final review.
- No image-ID lookup, fabricated OCR transcription, model training, new dependency or database reset was introduced. The browser validation deliberately used the owner's source problem as manually confirmed text; it was not an OCR accuracy test.

## Validation

| Check | Result |
| --- | --- |
| AI fraction support, guided lessons and primary lessons | 95 passed |
| Student tutor screen and API boundary tests | 69 passed |
| Backend tutor service and controller tests | 80 passed, zero failures/errors |
| Student TypeScript check | Passed |
| Scoped whitespace validation | Passed; existing Windows line-ending warnings only |
| Portal configuration, artifact and student deployment gates | 17 passed |

The 244 related tests include three different garden data variants, malformed/unsafe provider guidance, earlier-answer-only references, local reveal without API calls, retained pupil input, wrong-answer behavior and new-step reset.

An actual request through the public API logged in with the existing authorized student demo account, created a real lesson from confirmed text, verified 6/4/5 teaching paragraphs, submitted an intentionally wrong answer, then checked `11/15`, `4/15` and `60`. It verified completed-step retention and **Đáp số: 60 cây.** Credentials and tokens were not printed. The diagnostic script is in ignored private runtime storage, `infra/local-runtime/pc-preview/check_detailed_teaching.py`.

The deployed browser UI was then exercised independently: enter confirmed text, confirm the problem, start the lesson, reveal all paragraphs, preserve the draft `10/15` while revealing, reject it without moving forward, correct it, complete all three steps and inspect the written solution. The browser reported no captured console errors during this flow.

Actual browser screenshots, kept outside tracked source:

- `infra/local-runtime/pc-preview/detailed-teaching-actions.png`: step three's reasons and smaller teaching actions.
- `infra/local-runtime/pc-preview/detailed-teaching-complete.png`: checked written solution and final answer.

Browser evidence used the actual 1280×720 viewport. The attempted 375×812 viewport override did not change the existing tab; it was reset. No phone, small-viewport or physical-device evidence is claimed.

## Published state

- Production site: https://mathvisionkid-portal.vercel.app
- Unique deployment: https://mathvisionkid-portal-3v2mztsct-manh15.vercel.app
- Deployment ID: `dpl_EWqhZjQVNB3UWAvZ7buvhG4RYowb`
- Vercel inspection: **Ready**, target **production**, stable alias attached.
- New student entry bundle: `entry-55116a348215df794c90be52388b7125.js`.
- Vercel error-log query returned no logs. This static deployment's empty log result is not proof that the separate API has no errors; the public integration and browser flow provide the direct evidence for this change.
- The isolated existing `mathvision-pc-preview` AI and backend services were rebuilt and became healthy before publishing. The first publish attempt stopped at the health gate while those services were starting; the later successful attempt ran after health checks passed.

The backend still uses the existing PC-hosted preview setup. This task does **not** make API/OCR available when the owner's PC is off. That earlier hosting requirement remains separate.

Git base is `0e40db7`; pre-existing workspace changes were preserved. No commit or push was performed in this task.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: child-facing learning interaction and progressive disclosure.
  - Applied to: numbered paragraphs, explicit reveal action, persistent prior content and visible opened count. The initial UX search was poorly matched; a narrower `step by step disclosure` search returned progress-indicator guidance used for this interaction.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: shared React Native/React tutoring screen.
  - Applied to: event-driven local reveal state, keyed step reset, no extra fetch/effect for paragraph disclosure; the `rerender-move-effect-to-event` rule was read.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: focused API/UI change with compatible existing plans.
  - Applied to: a small optional array field, existing math renderer and buttons, a single presentation helper and no new package or generic lesson engine.
- `deployments-cicd`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated/vercel/0722921d/skills/deployments-cicd/SKILL.md`
  - Why selected: owner-authorized update to the existing production website.
  - Applied to: health-gated build/publish, fresh student export, deployment inspection and one bounded error-log check.

Exact Expo v57 documentation was read before code changes: https://docs.expo.dev/versions/v57.0.0/.

## Practical review limit

The owner's specific example and adjacent lesson/checking paths are verified. Automated tests and one browser lesson do not establish that every possible pupil understands every generated explanation. A pupil/teacher review of varied problems remains the appropriate next evidence for teaching quality.
