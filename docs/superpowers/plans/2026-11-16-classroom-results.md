# Phase 4 Results & Teacher Productivity Implementation Plan

> Execute vertical slices with Superpowers TDD and EGM review. Owner's full Phase 4 directive is the approved scope; this plan makes implementation choices within it.

**Goal:** Give teachers an actionable inbox and accurate publication results, and students their own progress and released feedback.

**Architecture:** Query the existing canonical V41 schema directly. A reusable assigned-recipient projection provides one row per publication recipient. Scope each SQL statement to the authenticated role and current ownership/membership. Use existing Phase 3 writes, private image reads and review dialog.

**Tech stack:** Spring JDBC, PostgreSQL, Teacher React/MUI, Student Expo Web. No schema or dependencies added.

**Baseline:** `22e8f505` contains the verified class-route isolation fix, separately from Phase 4. `406aaf8d` contains the accepted audit. Preserve the unrelated Portal LoginPage and untracked artifacts. Local only.

## Design choices

- Alternatives: combining roster and queue data in the browser loses authoritative consistency across reads; precomputed stats need invalidation on membership, handover, uploads and grades. Use statements derived from the immutable snapshot, with no materialized data or cache service.
- Snapshot rows survive removal; current membership is a separate boolean. Historical status and official grade remain visible to the current Teacher. Student access continues to require active account, recipient and roster. Class/Teacher metadata is current. Admin does not inherit access.
- Classify GRADE_RELEASED before UPLOADING, then map an eligible OPEN attempt (including prepared after expiry) to UPLOADING. Remaining supported states are AWAITING_IMAGE, AWAITING_REVIEW and RETAKE_REQUESTED. A missing submission maps to AWAITING_IMAGE. Use statement time for stable classification. Score comes only from ASSIGNED_RELEASE with released state. Zero is a value and absence is null. The Phase 3 release transaction writes the official decision and released state together. A manually corrupted release can fail its Results read. The Action Center classifies persisted status, while History reads a nullable official score. Teacher summaries omit feedback, image paths, email and image bytes. The authorized review detail provides released score and feedback. Student reads feedback via existing submission detail.
- Counts and rows of one results response agree. Separate endpoints are independent snapshots; invalidate after successful review, and refetch on entry/focus or explicit refresh. No promise of atomicity across tabs or requests.
- Existing ownership and permissions on review, upload and image stay unchanged. No changes to publication, roster, Phase 3 state transitions or grade writes.

## Slices and gates

- [x] Gate 0: verify commits and current diffs; repeat Teacher suite; local commit 22e8f505.
- [x] 4A: add GET /api/v1/teacher/assignments/{id}/results. In one SQL statement return authorized publication header even with no recipients, rows (studentId, studentName, member, status, submissionId, score), total and five counts derived from those rows. 50 maximum by existing publish policy; filter/search client side. Add PostgreSQL MockMvc tests: all five states, zero score, preview privacy, empty publication, roster removal, handover and wrong role. Real Teacher Results page deep links to existing review dialog; invalidate results on save, preserve requested filter on return. Browser verify real data and measure 30–50 row load.
- [x] 4B: add GET /api/v1/teacher/assignments/action-center, organized by current classes and published assignments. Aggregate from the same projection with one bounded SQL read per request. Provide counts by unit and filters with drill-down to existing Results route; deterministic paging if needed. Test zero and multi-class data, handover, legacy exclusion and post-review movement. Integrate with existing dashboard without replacing legacy batch workflows.
- [x] 4C: add GET /api/v1/student/assignments/history for current authorized recipients with metadata, state and official score. Reuse existing assignment/detail and AssignedSubmission for feedback/image and polling. List refresh on focus with cancellation and account isolation. Test another student, removed membership, zero/null, late response and real mobile browser.
- [x] 4D: test filter, search, result context and Next; loading/empty/error and recovery; keyboard/focus and 320/390/768/1280 widths. Retrieve relevant Modern Web Guidance first and adapt to existing libraries.
- [x] 4E: run focused then final PostgreSQL/MinIO, app, governance and build gates. Run browser A–E with synthetic data; measure clicks, response times and synthetic completion. EGM follow-up on authorization, projection parity and state isolation, fix confirmed blockers. Commit local only after verification and write owner report.

## Review focus

Scope ownership in the data-returning statement; empty vs forbidden; historical snapshot denominator after roster removal; expired prepared attempt and released priority; grade0 versus null; no duplicate joins or MinIO reads in summaries; same-session cross-route navigation and old-session late completions; actionable drill-down counts; keep existing Flyway lineage risks explicit.

## Contract decisions after independent EGM design review

- Results header: `assignmentId,classId,className,teacherName,title,publishedAt,maxScore,recipientCount,counts,recipients`. Each row: `studentId,studentName,member,activeMember,status,submissionId,score`. A missing, unpublished or unauthorized publication returns 404. A valid empty publication returns 200 with zero counts and an empty array. The publication snapshot is immutable. Each private endpoint returns no-store.
- Results URL `/assignments/:id/results` accepts an optional exact status filter. Student-name search stays in component state. Header counts cover all recipients. Open an authorized image/review using the existing dialog. Next fetches current results before selecting a waiting recipient and excludes the just-completed ID. A transient summary failure preserves an open review draft. A confirmed access failure closes it.
- Action Center: pending submissions, retake recipient tasks, distinct publications with missing active-member work and released submissions are separately labeled. Current active roster is required for missing/retake actions; historical review and released actions follow current Teacher review rights. Matching drill-down carries the same member predicate. Global counts cover the Teacher's current classes; assignment drill-down list is bounded and ordered by publishedAt descending then assignmentId descending, and filter predicates execute before paging. Test with multiple classes and measure query plan on synthetic data.
- Student history: dedicated minimal read projection avoids changing the existing assignment list/detail contract. One current user/role/active/membership/recipient scope in each data-returning SQL statement; no feedback or storage references in list. Key visible state by active session, abort previous reads, and use a navigation/request generation for same-session races.
- 4A files: add `submission/AssignedResults.java`, `submission/AssignedResultsController.java` and `submission/PostgresAssignedResultsTest.java` in the Business API; extend `submission/AssignedTeacherReview.java` for read-only released metadata. Add Teacher `pages/AssignmentResultsPage.tsx`, wire `App.tsx` and `pages/ClassAssignmentsPanel.tsx`, and reuse `pages/AssignedReviewDialog.tsx`. Document API in `docs/engineering/classroom-foundation-api.md`.
- 4B extends the same API and test classes and adds `TeacherActionCenterPage.tsx` to `DashboardPage.tsx`. The 20-row cap applies to the returned page. Totals scan eligible published work across current classes. Verify filter and member predicate parity before paging.
- 4C updates `assignments.web.tsx` and `studentAssignmentsRoutes.test.tsx`. Use Expo Router focus refresh on the list. Preserve the mounted detail and its Phase 3.1 observation lifecycle when a student switches tabs.
- 4D verifies keyboard entry to the new headings, row actions, Next across fresh reads, network recovery and the 320/390/768/1280 px widths. 4E runs the five named scenarios against canonical V41 and MinIO with the privacy fixture, captures evidence in `.local-artifacts/phase4/`, then records gates and EGM outcomes in the owner report.
