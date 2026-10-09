# Pocket calculator — 2026-10-09

> Historical first version. The owner requested a unified popup afterward; see `POCKET_CALCULATOR_POPUP_20261009.md` and the current `docs/POCKET_CALCULATOR.md` for the replacement.

## Outcome

Added a student pocket calculator accessible from the home quick tools and the math-guide header. It opens as a shared modal over the current screen, so closing it preserves the lesson and recognition inputs. Existing artwork and branding were preserved. No dependencies, backend endpoints, model training, commits or pushes were added in this phase.

Three modes support basic arithmetic, vertically displayed fractions and integer division with remainder. A custom keypad provides large controls, selected-input feedback and an input-next button. Results include expandable explanations using the actual entered operands. Addition/subtraction explain carrying/borrowing; division explains each partial dividend, multiplication, subtraction and next digit brought down. Recent history restores editable inputs and is limited to 10 in-memory entries per parent screen.

## Accuracy and boundaries

The pure calculation module uses rational integer arithmetic and validates safe intermediate results. Terminating decimals are rendered exactly; recurring decimals remain fractions. Invalid inputs, zero denominators, division by zero and unsafe intermediate arithmetic produce explicit errors. Editing operands or operators clears stale results. Inputs are bounded to 6 digits, with up to 4 decimal places in basic mode.

The calculator does not read or modify OCR, lesson answers, draft rows, or TutorService state, and it makes no AI request. It helps pupils check calculations without submitting answers for them.

## Validation

- Final complete mobile suite: **45 suites, 514 tests passed**, exit code 0.
- Final focused calculator suites: **2 suites, 45 tests passed**.
- TypeScript: `npx tsc --noEmit` passed, exit code 0.
- Browser checks on the running app: separate numerator/denominator inputs; stacked `1/3 + 2/5 = 11/15`; common-denominator explanations; `1005 ÷ 5` gives quotient 201 and remainder 0 with the internal zero retained; keypad entry `0,1 + 0,2 = 0,3`; history restore; close/reopen preserves calculator state and guide rows.
- Responsive checks at **375 × 812** and **812 × 375**: no horizontal document overflow. Temporary viewport override reset afterward.
- Guide retention test checks no additional tutoring calls when using and closing the calculator. Home test verifies the entry and existing capture action.

The browser division lesson used explicitly entered text as a fixture; it is not new OCR evidence. No physical-device evidence is claimed. Native Back behavior, font scaling, screen readers and rotation require a phone check using `docs/POCKET_CALCULATOR.md`.

## Changed areas

- `apps/student-mobile/src/features/calculator/calculate.ts`: validated exact calculations and explanations.
- `apps/student-mobile/src/features/calculator/PocketCalculator.tsx`: shared modal, keypad, fractions, result/steps and bounded history.
- `apps/student-mobile/src/components/home/HomeDashboard.tsx`: quick-tool entry.
- `apps/student-mobile/src/app/learning/math-guide.tsx`: header entry with lesson state preserved.
- Calculator, home and tutor screen tests; `docs/POCKET_CALCULATOR.md` usage and phone checklist.

## Evidence

Ignored local evidence is under `infra/local-runtime/logs/`:

- `calculator-20261009-mobile-full.txt`: final complete test output.
- `calculator-20261009-final-targeted.txt`: final focused calculator output.
- `calculator-20261009/typescript.txt`: TypeScript receipt.
- `calculator-20261009/calculator-controls.png`, `fraction-portrait.png`, `remainder-portrait.png`, `remainder-landscape.png`: actual app browser screenshots.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: student mobile UI, responsive layout and interaction design.
  - Applied to: existing theme reuse, large touch targets, 8px control gaps, input feedback and browser viewport checks. The unrelated calculator marketing pattern returned by the general design search was not adopted.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native implementation and state handling.
  - Applied to: derived display values without synchronizing effects, parent-preserving modal, bounded history and event-driven resets.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: keep implementation small and avoid unnecessary dependencies.
  - Applied to: one shared calculator component and one pure calculation module, existing MathText/AppButton/theme reuse, no route/API/dependency expansion.

Exact Expo SDK 57 versioned documentation was inspected before implementation: https://docs.expo.dev/versions/v57.0.0/ .
