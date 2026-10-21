# Tutoring and geometry polish

Owner request: make hints, solving guidance and student geometry interactions substantially clearer and robust. This is a bounded refinement of the current lesson flow, not an assertion of universal perfection.

- [x] Inspect and reproduce educational/interaction defects in hints, part selection and phase transitions.
- [x] Give specific count-based add/remove feedback for source fractions, explain equal parts progressively and preserve valid geometry/accessibility.
- [x] Make local hint checks match reading/calculation context; retain opened hints after wrong attempts, cap duplicate deep-help requests and return focus to the relevant answer control. Keep server grading authoritative.
- [x] Fix concrete backend hint/teaching defects with offline regressions while preserving exact arithmetic, source facts, current/future answer guards, ownership and revisions.
- [x] Run relevant Student/Python checks, TypeScript/lint and bundles; independently review integrated diff. Inspect browser interactions at phone/tablet/laptop sizes and both choice/numeric answer paths.
- [x] Report actual outcomes and limits with Skills Applied; no commits, pushes, deploys, training, corpus copying or live credentialed AI requests.

Parallel ownership: parent HintCheckIn/math-guide/screen tests/report; fraction worker FractionExplorer/tests; backend worker lesson.py/related tests. Preserve all earlier uncommitted work and unrelated reports.

Verification: 743 Student tests (53 suites), 393 offline Python tests, TypeScript, focused ESLint, Android/iOS/web export (32 web routes), and browser replay at 320/390/820/1440 widths passed. Integrated read-only review found no actionable regression. Details and limits: `report/TUTORING_INTERACTION_POLISH_20261021.md`.
