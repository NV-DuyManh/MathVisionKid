# Fraction shapes and guided summary implementation plan

**Goal:** Let pupils explore the same source fraction through circle, square and bar models, and learn to separate givens from the question before calculation.

**Architecture:** Extend the existing fraction explorer with SVG drawing primitives and equivalent accessible part controls. Reuse server-checked UNDERSTAND progress; publish an optional source-only summary after both reading choices are checked, then render it as a guided two-part summary. No student-written free-form summary, new model, or new auth path.

**Tech stack:** Expo SDK 57, React Native, react-native-svg (SDK-compatible install), TypeScript, Python tutoring runtime, Spring API.

**Spec:** Owner's current request, plus the previously implemented guided-reading flow. Preserve the approved mobile theme and source confirmation/privacy boundaries.

## Work and validation

- [x] Geometry: equal-area sectors/grid/strips for supported fractions, direct tap and equivalent 48px checkboxes. Source/session changes reset; changing representation preserves selection. Check denominator1, zero/improper fractions, keyboard, labels and geometry.
- [x] Server summary: optional `{givens:string[],question:string}` after two checked reading choices, never before. Exact source clauses, no computed answers; all-or-nothing bounded extraction. Preserve legacy callers, auth/revision and unsupported-source fallback. Validate Python, Spring and mobile boundaries with tests.
- [x] Guided summary UI: explain how to find known facts and the question, show selected progress, then the server's grouped source summary. Label partial selections clearly and omit the panel for legacy/nonreading lessons. Source/account/edit resets clear it. Test normal/error/reset paths and no extra API grading.
- [x] Integration: Student 732 tests, TypeScript/lint, Python 387/Java 98, web/Android/iOS bundles; browser interactions and visual inspection at phone/tablet/laptop widths. Final layout patch rechecked with44focusedtests and fresh three-platformexport/browser.
- [x] Report results, supported limits and evidence in report/FRACTION_SHAPES_SUMMARY_20261021.md with Skills Applied. No commit/push/deploy/training.

Parallel file ownership: geometry worker owns FractionExplorer/FractionShape/tests; summary worker owns lesson.py + source tests, Java tutoring DTO/service/tests and mobile TutorService/API tests; parent owns ProblemSummary, math-guide integration, screen tests and final verification/report. Only parent modifies package files.
