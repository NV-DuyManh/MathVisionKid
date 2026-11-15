# Phase 3.1 reliability, UX and security hardening

Owner scope: `C:/Users/LOC/.codex/attachments/c2415e63-681e-4113-a5cb-4518a8b608f2/goal-objective.md`.
Baseline: `a9a8159df003214b63755308e267297a4f3adf27`. Local only; preserve the separate LoginPage change. No Phase 4, migration history rewrite, model execution or production data.

## Implementation decisions

- Recovery: stream MinIO's private assigned-work namespace and re-arm only an actually present object associated with a terminal EXPIRED attempt, with no submission-image reference. Reuse durable V41 lease/deletion state. Missing objects remain terminal; OPEN, CONFIRMED, referenced and untracked objects are preserved. Client timeouts alone cannot establish server-side absence after a late PUT. No new migration/service.
- Student Web: serial status fetches, abort/ignore on route blur/unmount, visible-tab polling for UPLOADING/AWAITING_REVIEW with 5/10/20/40/60-second backoff (60-second cap), at most 20 background polls per observation window. Route focus, browser focus/pageshow/online and explicit refresh restart observation; hidden tabs pause it. Released results stop polling. Preserve edited drafts on transient failure, clear on account exit through the existing AuthProvider unmount boundary. Native Student screens are unchanged.
- Teacher: identity/version/status keyed review state, reload current metadata and bytes on image or grade conflict, discard prior confirmations/assessment, abort/ignore closed-review mutation callbacks. Saved review supports the next waiting recipient within the existing queue filter; Back retains the filter.
- Privacy: keep server recheck and immutable digest/version binding. Browser acceptance uses synthetic images and a clearly labelled HTTP fixture. No real detector accuracy or physical-phone claim.

## Verification and acceptance

Implementation file/action allowlist: extend `backend/business-api/src/main/java/com/mathvisionkids/api/storage/{ObjectStorageService,MinioObjectStorageService}.java` with streaming assigned-key enumeration; update `submission/AssignedUploadCleanup.java` and `src/test/java/com/mathvisionkids/api/submission/AssignedUploadRecoveryIntegrationTest.java` for rediscovery and verification. Update `apps/student-mobile/src/features/recognition/AssignedSubmission.web.tsx` and its new `__tests__/assignedSubmissionRefresh.test.tsx`; update Teacher `src/pages/{AssignedReviewDialog,ClassAssignmentsPanel}.tsx`, new `tests/assigned-review-recovery.test.mjs` and `package.json` test routing. Maintain this plan and local acceptance report. Runtime evidence/scripts stay under ignored `.local-artifacts/phase31/`. No API route/schema change is planned. Changes outside this list require a demonstrated in-scope defect and explicit report entry.

Verification-driven addition: repair the existing `apps/student-mobile/src/utils/__tests__/cropRotationWeb.test.ts` canvas double to implement standard `resetTransform`, missing in four failed cases of the full Student suite. Keep production crop logic and all existing assertions unchanged. The corrected full suite must rerun; a focused pass alone is insufficient.

1. Reproduce terminal late-PUT leak before fix; real PostgreSQL/MinIO tests for outages, two workers, restart, current/graded/retained object preservation and stable completion.
2. Rendered Student tests for retake/result without reload, deduplication, bounded/hidden polling, cancellation and late responses. Browser login, account switch, 390px/smaller/desktop and keyboard acceptance.
3. Rendered Teacher tests for GET/grade conflicts, fresh-image confirmation, isolated callbacks and next/back flow; exercise actual browser controls with real backend.
4. Verify crop/mask, preflight/confirmation, final upload/private read, digest/version and retry failures with real storage; distinguish fault-injection fixtures.
5. Synthetic 30-student pilot smoke through real API/storage, report observed latency, query/work counts, success/failure and recovery/cleanup backlog; no production SLA inference.
6. Independent EGM codebase-details review plus mathvision-review; fix confirmed in-scope P0/P1 and document limits.
7. Final unified backend opt-in regression, web/student suites, builds/typechecks/lint/governance and browser evidence. Commit only verified Phase 3.1 files locally, then stop for owner acceptance.

## Web guidance compatibility

Use Chrome Modern Web Guidance as a reference, not as a replacement for Superpowers/EGM. Page Visibility/focus/AbortController and existing native controls require no new dependency. Preserve MUI Dialog's existing focus/keyboard behavior rather than migrate the UI library to native dialog or require newer invoker/closedby APIs. Check real browser semantics, focus and narrow layouts.
