# Meeting action items implementation plan

**Goal:** Complete the four software action items in the owner's C1SE.01 meeting minutes dated 20 October 2026.

**Architecture:** Extend the existing account-owned guided lesson with prepared comprehension choices before calculation, preserving private answer keys and optimistic revisions. Add lightweight student hint responses and equal-part fraction interaction. Improve one reproducible photo/OCR defect through existing normalization/recognition paths and controls.

**Tech stack:** Expo SDK 57 React Native, TypeScript, Spring business API, Python FastAPI runtime.

**Spec source:** `D:/Capstone/Biên bản họp/C1SE.01_Meeting_Minutes_20-10-2026.docx`, Action Items section. Owner explicitly requested implementation. Original document remains unchanged.

## Constraints

- No commits, pushes, deployment, model training, or model replacement in this task.
- No rewriting original meeting records or marking institutional tasks complete without evidence.
- Keep source confirmation, privacy masking, account ownership, source-only numeric facts and no premature solution disclosure.
- Voice remains a feasibility proposal, not an agreed deliverable. Do not add games.
- No source corpus downloads/copies or new external account/service.
- SDK 57 documentation read before code. Student text excludes developer/debug information.

## Work and checks

- [x] Server and service contracts: optional guided-understanding path with source-specific facts/question/true-false choices, privately evaluated before calculation. Test variations, invalid input, source ambiguity, ownership and revisions; simplify language while retaining why/how. Unsupported extractive forms retain the existing independently reviewed math lesson.
- [x] Fraction explorer: equal parts can be selected, checked and reset for fractions present in the confirmed source. Test selection, accessibility, invalid/proper/improper fractions, signed literals and dates.
- [x] Student integration: comprehension framing, fraction exploration, small learner response in hint flow, full reset on source/session/account changes and no repeated API request on local exploration.
- [x] OCR: diagnose and fix a concrete photographed-math recognition defect with regressions and existing controls. Report measured limits; do not invent global accuracy.
- [x] Verify combined TypeScript, Student tests (640), tutor/OCR tests (345), Spring tests (86), web/Android/iOS bundles; inspect rendered browser UI at four widths with isolated HTTP fixtures.
- [x] Record four-item status and evidence in `report/MEETING_ACTIONS_20261021.md`, including Skills Applied and limits. No commit/push/deployment.

Parallel boundaries: OCR worker owns OCR runtime files/tests; fraction worker owns the new FractionExplorer component/tests; lesson worker owns Python lesson, Spring DTO/service and TypeScript TutorService contracts/tests. Parent owns math-guide integration, screen tests and final verification/report. No worker changes branch or shares an implementation file.
