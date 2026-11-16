# Classroom Foundation API

Classroom Foundation started from develop 64d03ced. The merged migration sequence keeps develop's verified training at V34, Classroom at V35, shared quota at V36, and Assignment publication at V37. Databases already carrying the pre-merge Classroom V34–V36 history require a data-preserving cutover to the merged history before running this build.

Under /api/v1/teacher/classes, keep the existing list and detail. POST creates with name, gradeLevel and requestId (201, 200 for identical replay). PATCH /{classId} updates name, gradeLevel or joinMode. GET/POST/DELETE /{classId}/invitation read, replace or disable a shared code and link token. GET /{classId}/join-requests lists pending requests. PUT /{classId}/join-requests/{studentId} accepts requestId and approve, returns 204 for a matching decision/replay and 409 for a stale or conflicting decision. DELETE /{classId}/students/{studentId} removes a member.

Under /api/v1/student/classes, GET lists memberships and the Student's own PENDING, DECLINED or REMOVED statuses. POST /invitation-preview accepts credential (code or token) and returns minimal class metadata and an invitation generation ID. POST /join checks credential, classId and generation again and returns JOINED or PENDING. Disabled or replaced credentials return a generic 404. The preview and join endpoints share a limit of 20 validly formed requests per authenticated Student account per fixed one-minute window. Six-digit credentials also share a database-wide quota of 300 requests per fixed one-minute window across accounts and instances. Token links and QR links use the account quota alone. The shared quota does not use client IP or forwarding headers, so changing addresses or proxy headers does not change it. High parallel use of six-digit codes can exhaust the shared quota for all classrooms for the remainder of a window. Excess requests return 429 with Retry-After: 60 and Cache-Control: no-store. Never include invitation secrets in logs, roster in previews or another student's data in Student responses.

Classroom and classroom_students remain authoritative. Use a single join record per class and Student for PENDING, APPROVED, DECLINED or REMOVED. The persistent join record itself requires manual review on a new attempt when the Student is no longer a member. The roster remains authoritative for current membership. Retry can recreate PENDING, never auto-admit a previously declined or removed Student. Admin direct addition resolves pending membership and Admin removal marks manual review in the same transaction. All roster, invitation, mode and handover writers acquire the same class row lock before mutation. QR encodes the same URL as the copied link. Legacy classes default to approval and invitations disabled.

The account and shared quotas commit before invitation lookup. Invalid or expired credentials consume quota. A shared-quota rejection rolls back the account increment so the Student can still use the invitation link. Apply V36 before routing traffic to updated instances. Older instances enforce only the account quota, so complete the rollout before relying on the shared cap.

## Assignment Phase 2

Teacher assignment workflow uses `/api/v1/teacher/classes/{classId}/assignments` to list this teacher's class assignments, `POST /teacher/assignments/drafts` to create a private draft, `PUT /teacher/assignments/{id}/draft` to edit a draft, and `POST /teacher/assignments/{id}/publish` to publish once. Only the teacher currently assigned to the class can manage its workflow. Drafts remain invisible to students. Publication snapshots the active class roster in `assignment_recipients`; a published assignment and its snapshot are immutable. Classes above the 50-student workflow cap cannot be published through this path.

Student Web reads `/api/v1/student/assignments` and `/api/v1/student/assignments/{id}`. A student can read a published assignment only while active, currently enrolled in that class, and present in the publication snapshot. Responses use `Cache-Control: no-store`. Assignment publication is separate from the legacy Batch/Image workflow: existing ACTIVE assignments and batch grading remain available, and this phase does not create submissions, grades, or AI results. V37 adds nullable `prompt` and `instructions` to legacy assignments plus one publication row and a recipient snapshot per new published assignment.

Creation request IDs are scoped to their teacher. Keyed classroom, draft, legacy assignment and batch creation serialize on the teacher's `users` row, separate from the `teachers` row referenced by review foreign keys. Identical assignment replays must also match the workflow (legacy ACTIVE versus online DRAFT/PUBLISHED); a conflicting reuse returns 409. A new legacy Batch requires an ACTIVE assignment. Existing Batch reads and replays remain available.

## Assigned submissions — Phase 3

All routes below are under `/api/v1`. Student assignment access requires an active account, current class membership and inclusion in the immutable publication snapshot. Admin does not acquire Teacher image/review authority through these routes. Handover immediately changes the Teacher authorized to review; it does not replace recipients, images or decisions.

| Student route | Request and response |
|---|---|
| `GET /student/assignments/{assignmentId}/submission` | Private status, current image version and released result/retake instructions when applicable. |
| `GET /student/assignments/{assignmentId}/submission/image` | Current private image bytes; rechecks access/version after storage read. |
| `POST /student/assignments/{assignmentId}/submission/privacy-check` | Multipart `image`; validates eligibility and image, then requires a CLEAR privacy verdict; 204 on success. |
| `POST /student/assignments/{assignmentId}/submission` | UUID `Idempotency-Key` header; multipart `image`, integer `expectedImageVersion`, boolean `privacyConfirmed`. Returns 200 `{submissionId, imageVersion}`. |

The web editor crops/masks locally and requires explicit user confirmation. Final upload independently validates the bytes, confirmation and privacy verdict before reserving/writing an image. Detector transport errors or unknown verdicts fail closed. Local acceptance uses a synthetic HTTP fixture; it does not establish real detector accuracy. Sanitized input and stored image digests bind an attempt to its content. Confirmed identical retries return the prior receipt, while conflicting or expired attempts require recovery/new confirmation as indicated by the error. There is one official ASSIGNED_WEB submission per recipient, with immutable incrementing image versions. Storage keys remain private; these APIs return bytes rather than public URLs.

| Teacher route | Request and response |
|---|---|
| `GET /teacher/assigned-submissions/queue/{assignmentId}` | Recipient status and submission IDs for the currently owned class. |
| `GET /teacher/assigned-submissions/{id}` | Review metadata, current image version and max score. Includes official score and feedback after grade release. |
| `GET /teacher/assigned-submissions/{id}/image?imageVersion=N` | Private bytes for the authorized current version; generic 404 for unavailable/version-mismatched references. Client retry first reloads metadata. |
| `POST /teacher/assigned-submissions/{id}/return-image` | `{imageVersion, reason, instruction}`; reason UNREADABLE or WRONG_ASSIGNMENT, nonblank instruction at most 500 characters; 204. Does not create a grade. |
| `POST /teacher/assigned-submissions/{id}/release-grade` | `{imageVersion, requestId, readable, matchesAssignment, score, feedback}`; UUID request ID, both confirmations true, integer score 0..maxScore, feedback at most 2000 characters; 204. |

Review mutations lock class, assignment and submission, reject obsolete versions/states with 409 REVIEW_CONFLICT, and create at most one official TeacherDecision. An identical released-grade replay matches request ID, image version, score and trimmed feedback; other writes cannot change a released grade. Legacy Batch/AI paths cannot mutate ASSIGNED_WEB work. Image/status reads use `Cache-Control: no-store`, image bytes also use `X-Content-Type-Options: nosniff`.

## Recovery and observation — Phase 3.1

Student-visible states include AWAITING_IMAGE, UPLOADING, AWAITING_REVIEW, RETAKE_REQUESTED and GRADE_RELEASED. An OPEN prepared attempt with a recorded stored digest remains UPLOADING even after its reservation deadline: recovery may still confirm its object, so expiry alone is not evidence that no image was received. Recovery rechecks eligibility, content and current version before confirmation. Released grades and current/released images remain protected.

Cleanup uses persisted recovery/deletion claims and retained attempt records to reconcile interrupted work and late PUTs, including objects that appear after an earlier deletion sweep. An unrecognized object without an owned attempt record is not automatically deleted. V38 adds assigned uploads and integrity constraints, V39 image returns, V40 prepared-upload recovery and V41 durable cleanup/reconciliation. Never renumber or repair an already-applied divergent Flyway history to make validation pass.

Student Web observes pending work with bounded 5/10/20/40/60-second backoff and at most 20 background polls per observation window, pauses hidden tabs, and resumes on focus/pageshow/online or explicit refresh. At the cap it offers manual refresh. Definitive 403/404 clears loaded assignment/photo/result state and pending image operations; a transient transport error retains work for retry. Logout/unmount aborts observers and image work. Teacher stale-image retry reloads metadata and clears confirmations/score before assessment. These client controls complement backend authorization and do not replace it.

Implementation and acceptance details: [Phase 3 plan](../superpowers/plans/2026-11-14-submission-phase3.md), [Phase 3.1 plan](../superpowers/plans/2026-11-15-phase31-hardening.md). Historical local reports under `report/` are verification receipts, not a promise that every database history or physical device has been tested.

## Assignment results and Teacher Action Center — Phase 4

| Teacher route | Response |
|---|---|
| `GET /teacher/assignments/{assignmentId}/results` | Published assignment and current class/teacher metadata, recipient snapshot size, counts by status and recipient rows. Each row includes membership flags and a nullable official score. |
| `GET /teacher/assignments/action-center?filter=ALL&page=0` | Class count, pending and released submission counts, retake recipient-task count, count of assignments with missing work, and the matching assignment page. Filters are ALL, PENDING, RETAKE, MISSING and RELEASED. Pages are zero-based and contain at most 20 assignments, ordered by publication time and assignment ID descending. |

Both responses use `Cache-Control: no-store` and scope reads to the current active Teacher who owns each class. The Results endpoint returns 404 for an unavailable publication. Its denominator stays tied to publication even when membership changes. A score of 0 requires an official release. The Action Center includes missing and retake tasks only for active current members. Pending review and released counts include historical recipients under the current Teacher's review rights. Neither endpoint returns images or private feedback.

`GET /student/assignments/history` returns the active Student's assignments in current classes where the Student belongs to the publication snapshot. Each row includes the assignment and current class/teacher labels, publication date, status, max score and nullable official score. Responses use `Cache-Control: no-store`. Feedback and image viewing use the existing authorized submission-detail routes.
