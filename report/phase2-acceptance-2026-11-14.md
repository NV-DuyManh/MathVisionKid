# Phase 2 — Local acceptance report

14/11/2026. Branch feature/classroom-foundation. Baseline503007cc includes Phase1 commits64816562 and503007cc. Local functional verification is complete. Integration with current develop requires the migration-history decision described below.

## Delivered workflow

Teacher can create, edit and preview a draft in the class Assignment tab, confirm the current roster count, and publish. Published content is frozen and the class list shows recipient count. The current class owner controls list/detail/mutations, including after Admin handover.

Student Web has assigned-work navigation, list, detail, teacher/class context, instructions, loading/error/empty states and back recovery. Access requires active account, current class membership and historical recipient membership. Entry after publication does not grant historical work. Removal revokes reads while retaining the recipient snapshot.

## API and data

All routes below are under /api/v1 and return private no-store responses.

| Method | Path | Capability |
|---|---|---|
| POST | /teacher/assignments/drafts | Create draft,201 new and200 idempotent replay |
| PUT | /teacher/assignments/{id}/draft | Edit private draft |
| GET | /teacher/classes/{classId}/assignments | Class workflow list |
| GET | /teacher/assignments/{id}/workflow | Teacher detail |
| POST | /teacher/assignments/{id}/publish | Idempotent publication |
| GET | /teacher/assignments/{id}/recipients | Historical recipient roster |
| GET | /student/assignments | Current authorized work |
| GET | /student/assignments/{id} | Authorized detail,404 otherwise |

V36 adds nullable prompt/instructions to Assignment and publication/recipient tables. Database uniqueness enforces one publication per assignment and one recipient per publication/student. Publish locks Classroom before loading Assignment for update and caps active recipients at50. Legacy ACTIVE assignments retain their Batch workflow. This phase creates no submissions, grading decisions or AI jobs.

## Changed areas

- Backend assignment package adds workflow controller/service, publication/recipient entities/repositories, extends Assignment/Repository, and adds V36.
- Backend tests add PostgreSQL concurrency, extend Assignment controller coverage and upgrade legacy fixtures in PostgresUpgradeTest.
- Teacher ClassDetailPage/ClassAssignmentsPanel and TeacherService/SpringTeacherService/MockTeacherService implement the class workflow. Production/runtime acceptance used SpringTeacherService.
- Student web assignments list/detail routes, native redirect placeholders and tab configuration add assigned work. Focused route tests cover delayed responses. A small classes.web change initializes invitation token from the hash lazily to satisfy the existing lint rule.
- classroom-foundation-api.md and the Phase2 plan record the contract. Detailed execution receipts and compatibility assessment accompany this report.

## Executed verification

| Command/check | Final result |
|---|---|
| Gradle TeacherAssignmentControllerTest |19 passed |
| Gradle batch package |18 passed |
| Enabled PostgresAssignmentConcurrencyTest |3 passed,0 skipped |
| Enabled PostgresUpgradeTest |7 passed,0 skipped |
| Teacher test:config |49 passed |
| Portal test:config |35 passed |
| Admin test:config outside network sandbox |42 passed |
| Student test:contracts |15 passed |
| Student Jest studentAssignmentsRoutes.test.tsx |2 passed |
| Student typecheck |Passed |
| Student lint |0 errors,1 existing QuizInvitation warning |
| Teacher lint |0 errors,4 existing warnings |
| Teacher production build with public placeholder URLs |Passed,924kB chunk warning |
| Governance |16 passed |
| git diff --check |Passed |

PostgreSQL tests use random schemas in mathvision_classroom_final_test, PostgreSQL16 in mathvision-audit-classroom-final. Upgrade tests seed and preserve Classroom roster, ACTIVE Assignment, COMPLETED Batch and linked Submission/image/quiz records through migration and matching pg_dump/pg_restore tools. Concurrent publishing returns one consistent PUBLISHED snapshot, serializes behind roster removal/handover and creates no downstream grading records. The concurrency test first reproduced a stale DRAFT response, then passed after changing the pre-lock read to scalar class ID.

Earlier failures were resolved explicitly. Draft replay status/metadata and Student recipient aggregate failed new tests before fixes. Admin logout tests failed from sandbox loopback EACCES and passed unchanged outside it. Initial multi-server Playwright regression startup failed, so controlled delayed-response React tests verify the races while real Playwright MCP verifies the integrated workflow. React test harness timeout was resolved with real timers and explicitly controlled deferred promises.

## Browser acceptance

Playwright MCP exercised actual Portal, Teacher, Student and Admin with Spring/PostgreSQL in the isolated phase2_browser_20261114 schema. Teacher created a draft, edited256+127 to256+128, saved and previewed it, then published to11 recipients. Student Minh and An read the expected prompt/instructions. Direct detail reload succeeded. Logout confirmation cleared access, protected navigation returned to login, and another student signed in using the same browser. Synthetic C saw an empty list and direct404, including after SQL fixture membership added after publication. Teacher removed Hà through UI, after which Hà received404; SQL retained11 recipients with10 current members.

Admin used its handover dialog to assign Teacher B. Old teacher's class read returned403. New teacher logged in through Portal SSO, viewed existing assignments and created a new draft. Published cards expose preview without edit controls. API tests reject published edits. Teacher confirmation displays the current11-student roster and explains snapshot timing.

Desktop and390px checks exercised Teacher/Student without horizontal overflow. Student Tab then Enter focused and activated back recovery on the error view. Final re-export smoke signed An in, opened the actual assigned card and rendered the expected detail after the request-lifecycle fixes. Chrome DevTools inspected mobile login/focus, but its login attempt did not establish a Student session; integrated role acceptance evidence comes from Playwright. These are desktop-browser viewport checks rather than physical-phone evidence.

## EGM findings

Fresh EGM implementation-readiness reviewer inspected workflow, authorization callers, database constraints, UI and tests. The two Student P2 findings were fixed with effect cleanup/abort and current-route result/status gating. Focused tests verify a late detail after back navigation and a valid-detail to denied-detail transition. Final source re-review found neither original finding remaining and no local P0/P1 blocker. The reviewer did not independently run the tests. Parent execution receipts provide runtime evidence.

## Integration compatibility

Fetched develop0cbbd267 adds V34 verified_training_runs, while local V34 is Classroom. Local V35 quota and V36 publication are already applied in test schemas. Seven upgrade tests include a temporary combined mapping fromV33 through developV34, ClassroomV35, quotaV36 and publicationV37. Existing migration sources/history were not rewritten.

That mapping is valid for databases not yet on the local Classroom history. Databases already on ClassroomV34–V36 require a reviewed data-preserving cutover/history reconciliation before integration. Public deployment histories have not been inspected. This remains an integration blocker. The owner explicitly permitted completing isolated local Phase2 verification independently of that decision. Details and checksums are in phase2-migration-compatibility.md.

## Owner acceptance

Portal login http://localhost:5192/login, Student http://localhost:5192/study/assignments, Teacher http://localhost:5173, Admin http://localhost:5194. Runtime uses the isolated test schema.

| Synthetic account | Password | State |
|---|---|---|
| an.student@mathvision.local | MathVision123! | Recipient, current class member |
| minh.student@mathvision.local |123 | Recipient, current class member |
| phase2.c@acceptance.local | MathVision123! | Entered after publication, cannot read old work |
| ha.student@mathvision.local | MathVision123! | Removed recipient |
| phase2.teacherb@acceptance.local | MathVision123! | Current class owner after handover |
| lan.teacher@mathvision.local |123 | Former owner |
| admin.demo@mathvision.local |123 | Admin |

1. Sign Teacher B in through Portal, open Lớp3A → Bài tập and inspect published work and “Bản nháp sau bàn giao”.
2. Edit the draft, preview it and verify the publish confirmation count before confirming.
3. Sign An in and open an assigned item, refresh detail and return by keyboard.
4. Sign C or Hà in and verify that the pre-existing acceptance item is unavailable.
5. As Admin, inspect class owner and perform another handover if desired. Verify the previous teacher loses access.

The test roster has changed during acceptance. Use a newly created class/assignment for a fresh end-to-end acceptance. Submission, review and grading are later phases.

## Git and readiness

Phase2 is ready for a local commit after final staged-content validation. The exact resulting SHA is supplied in the handoff. LoginPage.tsx is an earlier separate modification. Browser artifacts and .gradle-agent receipts stay local. Phase1 history remains intact. Integration readiness remains conditional on the documented Flyway cutover decision.

## Skills Applied

- mathvision-backend — .agents/skills/mathvision-backend/SKILL.md in the current worktree, applied to Spring authorization, locking and migrations.
- mathvision-quality — .agents/skills/mathvision-quality/SKILL.md in the current worktree, applied to regression and browser/PostgreSQL evidence.
- mathvision-review — .agents/skills/mathvision-review/SKILL.md in the current worktree, applied to final correctness review.
- vercel-react-best-practices — .agents/skills/react-best-practices/SKILL.md in the current worktree, applied to request cleanup and state derivation.
- egm-review-loop — C:/Users/LOC/.codex/plugins/cache/openai-curated-remote/egm/0.1.1/skills/egm-review-loop/SKILL.md, applied through a fresh implementation-readiness reviewer and finding resolution.
- Superpowers receiving-code-review/test-driven-development/verification-before-completion were applied to reproductions and verification. Impeccable was unavailable at its advertised local path during finalization, so existing design patterns and browser checks guided this hardening pass.
