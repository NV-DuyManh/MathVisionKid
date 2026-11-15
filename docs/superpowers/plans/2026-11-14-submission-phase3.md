# Phase 3 Submission and Review implementation plan

**Goal:** Deliver the assigned-work loop from a private Student image upload through Teacher retake/release-grade and Student feedback.

**Spec:** Owner directive at C:/Users/LOC/.codex/attachments/c024d095-3c2e-43ae-b74b-5053c61e76b5/goal-objective.md.

**Architecture:** Extend the existing Submission and TeacherDecision models with an ASSIGNED_WEB boundary. Add durable upload-attempt/image-version persistence and private object operations. Keep external storage calls outside transactions holding Classroom/Assignment/Recipient/Submission locks. Reuse the existing Teacher image viewer and Student crop/privacy UI after verifying their contracts.

**Tech stack:** Spring/JPA, PostgreSQL/Flyway, MinIO, Teacher React/Vite and Student Expo Web.

## Gate 0

- [x] Verified local Phase1 ancestors64816562 and503007cc and Phase2 commitb62f30f6.
- [x] Preserved separate LoginPage.tsx modification and local artifacts.
- [x] Merge develop `0cbbd267` locally after owner approval. Merge commit `71ef6d84`.
- [x] Verify canonical migrations through V37 on isolated PostgreSQL with backup and restore. See `docs/engineering/phase3-gate0.md`.
- [x] Allocate V38 and V39 for Phase 3. Databases with the earlier local Classroom V34 need a separate cutover.

The three historical Classroom design/plan paths named in the directive are absent from this checkout. Use the complete current owner directive and actual source contracts, and check whether remote contains those documents before assuming their details.

### Implemented API contract

- Student `GET /api/v1/student/assignments/{id}/submission` returns the current version, status, released score and feedback, or the retake reason and instruction. The authenticated recipient must still belong to the class.
- Student `GET /api/v1/student/assignments/{id}/submission/image` returns only that student's current confirmed image. The backend verifies membership and current image identity before and after loading private bytes. Responses use `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. Missing access returns 404, a changed image returns 409, and unavailable storage returns 503.
- Student `POST` to the same route takes multipart fields `image`, `expectedImageVersion` and `privacyConfirmed`, with a UUID `Idempotency-Key` header. A successful confirmation or replay returns the submission ID and image version. Conflicts return 409, validation 400/413/415 as applicable, and transient object storage failure 503.
- Privacy inspection returns 422 `IMAGE_PRIVACY_REVIEW` when the image is rejected. Missing configuration, an inconclusive response or a failed inspection returns 503 `IMAGE_PRIVACY_UNAVAILABLE`. These outcomes happen before reservation or object storage writes. Storage failure uses the distinct 503 `UPLOAD_UNAVAILABLE`. The existing image remains current. A confirmed replay is authorized before returning its earlier receipt.
- Student `POST /api/v1/student/assignments/{id}/submission/privacy-check` accepts an image for an authorized recipient, validates and sanitizes it and inspects privacy without reserving a submission or writing an object. A clear result returns 204 with `Cache-Control: no-store`. The UI then requires the student to review the normalized preview and explicitly confirm sending. An edited or newly selected image must be checked again. Final upload performs its own server inspection and authorization, so an earlier successful preview cannot bypass validation.
- Teacher `GET /api/v1/teacher/assigned-submissions/queue/{assignmentId}` adds review states while preserving the Phase 2 recipient contract. Detail and versioned image reads require current classroom ownership and send `Cache-Control: no-store`. Teacher mutations accept `imageVersion` with a reason and instruction for retake, or a request UUID, both confirmations, an integer score and optional feedback for grade release.
- Reservation checks the immutable publication snapshot while holding Classroom and Assignment locks, then locks the Submission and UploadAttempt. Handover and roster writes contend on the Classroom lock. V40 persists the sanitized object digest, content type and length before PUT. A scheduled worker claims due attempts with a leased row update, verifies the stored bytes outside the transaction, and calls the same authorized confirmation as the upload request. Attempts without a matching object expire. An upload retry from the original browser keeps its key and expected version.

Prepared attempts require reconciliation before expiry. The recovery worker can confirm a matching object after the reservation deadline while repeating permission, digest and current-version checks. Explicit object absence, mismatched bytes or rejected confirmation permit expiry after the reservation deadline. A storage transport failure leaves the prepared attempt available for retry. Ordinary client confirmation still requires an unexpired reservation. This correction awaits execution of its extended regression test. Successful object deletions still retry daily to handle late PUTs, with the unbounded retry history recorded as an open EGM finding.

Student retry retains the edited image. Temporary 409 responses refresh status and require confirmation again. `UPLOAD_EXPIRED` creates a new request key. A refreshed current image version creates a new key with that version. Network failures retain the same image, key and version.

## 3A — Submission data and private upload

- [ ] Inventory every existing Submission mutation/callback and storage entry point. Specify ASSIGNED_WEB rejection guards before exposing new writes.
- [ ] Define DTOs for assignment submission status, upload reservation, image PUT/confirmation and authorized image read. Freeze idempotency identity, SHA256 and expected imageVersion together.
- [ ] Write meaningful failing tests for recipient authorization, one official Submission per recipient, image validation and reservation retry.
- [ ] Extend Submission and add focused assigned-work persistence under the submission package. Use unique DB constraints for recipient mapping and active image/upload invariants.
- [ ] Implement upload reservation, private immutable object write and confirmation with no MinIO call under PostgreSQL locks.
- [ ] Verify PostgreSQL and private MinIO behavior using isolated schema/bucket and synthetic images.

## 3B — Recovery and replacement

- [ ] Add TTL, restart recovery, single in-flight reservation and persistent cleanup retries.
- [ ] Test failures before PUT, after PUT, lost confirmation response, duplicate/changed request, two recovery workers, late PUT, failed DELETE and withdrawn membership.
- [ ] Preserve current confirmed image until replacement confirmation succeeds. Refuse replacement after grade release.

## 3C — Teacher review and grade

- [ ] Add assigned-submission detail/image/return-image/release-grade endpoints under the existing role namespaces.
- [ ] Require current teacher ownership and current imageVersion for retake and grading. Record retake history separately from the unique final TeacherDecision.
- [ ] Require readable-image and correct-prompt confirmations, integer0..maxScore, same-key/content replay and atomic grade publication.
- [ ] Test image replacement versus grading, competing grades, handover, roster removal, ID guessing and all legacy mutation/AI callback boundaries.

## 3D — Integrated web

- [ ] Student assigned detail gains camera/file picker, crop/privacy preview, explicit send confirmation, current upload state, replacement/retake and released feedback.
- [ ] Teacher class assignment gains recipient status list and review workspace with current image/version, zoom, retake, grade and next/back preserving filter.
- [ ] Exercise actual Teacher→Student→Teacher→Student flow with Spring/PostgreSQL/MinIO and synthetic accounts, including0 and8/10, retake, network error, refresh, account switch,390px and keyboard.

## 3E — Final verification and local commit

### Current implementation locations

- `backend/business-api/src/main/java/com/mathvisionkids/api/submission/AssignedStudentUploadController.java` owns Student upload, status and current-image routes.
- `backend/business-api/src/main/java/com/mathvisionkids/api/submission/AssignedUploadReservation.java` owns authorization, reservation, immutable image versions and confirmation.
- `backend/business-api/src/main/java/com/mathvisionkids/api/submission/AssignedUploadCleanup.java` owns recovery and orphan cleanup.
- `backend/business-api/src/main/java/com/mathvisionkids/api/submission/AssignedWebImage.java` owns byte and pixel validation and metadata stripping.
- `backend/business-api/src/main/java/com/mathvisionkids/api/submission/AssignedImagePrivacy.java` calls the internal image privacy gate before reservation.
- `backend/business-api/src/main/java/com/mathvisionkids/api/submission/AssignedTeacherReviewController.java` and `AssignedTeacherReview.java` own the review queue, private Teacher image reads, retake history and grade release.
- `backend/business-api/src/main/java/com/mathvisionkids/api/storage/MinioObjectStorageService.java` implements private digest-bound assigned image writes.
- `backend/business-api/src/main/resources/db/migration/V38__assigned_web_submission_uploads.sql`, `V39__assigned_image_returns.sql` and `V40__assigned_upload_recovery.sql` persist assigned-work boundaries and upload recovery metadata.
- `apps/student-mobile/src/app/(tabs)/assignments.web.tsx` connects `apps/student-mobile/src/features/recognition/AssignedSubmission.web.tsx` to assigned work. `apps/student-mobile/src/utils/cropRotation.web.ts` exports edited image bytes.
- `apps/teacher-web/src/pages/ClassAssignmentsPanel.tsx` connects the queue to `apps/teacher-web/src/pages/AssignedReviewDialog.tsx`.
- `ai/runtime/app/api/assigned_image_privacy.py`, `ai/runtime/Dockerfile.assigned-privacy`, `ai/runtime/scripts/verify_assigned_image_ocr.py` and `ai/runtime/scripts/verify_assigned_image_privacy_http.py` contain the candidate internal detector and its verification entry points. Local model execution is restricted by the owner's fixture-only instruction.
- `backend/business-api/src/test/java/com/mathvisionkids/api/submission/AssignedStudentUploadControllerTest.java`, `AssignedImagePrivacyTest.java` and `AssignedUploadRecoveryIntegrationTest.java` contain the focused regression cases. `backend/business-api/src/test/java/com/mathvisionkids/api/PostgresUpgradeTest.java` contains migration upgrade coverage.

This list locates implementation responsibilities. The final commit allowlist also requires inspection of the legacy submission, callback and batch guards in the complete working diff. Portal LoginPage edits, browser artifacts and local Gradle caches remain outside the Phase 3 commit scope.

### Image-content privacy gate

Owner clarification on 14 November 2026 restricts verification to fixtures. Detector accuracy on real handwriting remains unverified. The owner additionally requested user confirmation after detection. The implemented flow checks the image before enabling confirmation. The previously approved rejection policy still applies: a flagged image requires editing and another check. The pending question about allowing an override has not authorized such a change.

Recovery only leases reservations after their client deadline, so object inspection cannot establish a stale pre-deadline absence used later to expire a valid upload. The revised integration helper checks that live attempts remain unconfirmed by the worker before testing expired recovery.

The current server checks attestation, decodes the file, enforces size limits, and strips metadata. Browser testing verified that manual masks are baked into the stored pixels. Automatic rejection of prohibited content in unmasked pixels remains a release gate.

Evaluate an offline OCR candidate on Vietnamese printed and handwritten names and contact fields, and a separate offline face detector on synthetic photos. Test normal arithmetic alongside prohibited samples. Report missed detections and false rejections by category. Run the check on the final sanitized bytes before reserving storage or sending a PUT. An unavailable or inconclusive check must leave existing submissions intact and return an actionable response. Avoid storing source images, OCR text, or detected face crops in logs or diagnostics.

The candidate runs as the separate ASGI app `app.api.assigned_image_privacy:app`. Provision both Paddle model directories and the YuNet ONNX file beneath `ASSIGNED_PRIVACY_MODEL_DIR` before starting it. Mount the models read-only and restrict the process to internal networking. Configure the same dedicated key in `ASSIGNED_PRIVACY_KEY` on the service and `APP_ASSIGNED_UPLOAD_PRIVACY_KEY` on Spring, with `APP_ASSIGNED_UPLOAD_PRIVACY_URL` set to the internal endpoint. Keep the key out of the repository. The service returns a single decision. Runtime failures, an unknown verdict and an absent configuration all prevent the storage write.

Build the separate local image from the repository root with `docker build -f ai/runtime/Dockerfile.assigned-privacy -t mathvision-assigned-privacy:local ai/runtime`. The runtime performs a synthetic inference at startup and requires readable local model files. The image can run with networking disabled for the HTTP contract test using FastAPI TestClient. For Spring integration, use an internal network or a loopback port binding.

The text rule accepts arithmetic, selected units, and some complete counting clauses. Other legitimate wording can still be rejected, and the detector can miss writing not found by OCR. The HTTP smoke cases establish behavior for their own fixtures. Acceptance still requires representative photos of Vietnamese handwriting, including complete word problems and mixed-content images, followed by a final review.

- [ ] Run relevant backend, PostgreSQL/MinIO fault/concurrency, legacy Batch/selfpractice, frontend build/typecheck/lint/tests and governance on final source.
- [ ] Fresh EGM review of authorization, privacy, transaction order, storage recovery, immutable grades and rendered UX. Resolve P0/P1.
- [ ] Review final diff, preserve unrelated changes, commit only Phase3 files locally, verify SHA and write owner acceptance report.

No Phase4 work is authorized. Public deployment and external Git operations remain subject to the owner's explicit current restrictions.
