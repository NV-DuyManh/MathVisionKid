# Parallel Track A1.1: Admin Backend, RBAC, User Provisioning & Classroom Administration Report

---

## 1. Executive Summary
Parallel Track A1.1 ("Admin Lite") establishes the backend infrastructure, role-based access control (RBAC), operational account provisioning, classroom administration, and audit event visibility for MathVision Kids. This is an intentional, approved product scope extension beyond the previously frozen Student and Teacher runtime.

The operational role **ADMIN** was introduced alongside **STUDENT** and **TEACHER** without introducing a role hierarchy. Admin authority is strictly isolated: Administrators can provision and manage teacher/student accounts and classroom rosters, but **cannot** grade, approve, override, or evaluate student work (`POST /api/v1/teacher/submissions/**` returns `403 Forbidden`). All 51 baseline Spring tests remain 100% passing, 20 new Admin integration tests were added (total: 71 tests passing), all 97 Python AI tests remain passing, Teacher and Student builds compile cleanly, and local runtime achieved `READY_FOR_DEMO` with 0 popup terminals.

---

## 2. Scope
Track A1.1 covers:
- Role extension: `STUDENT`, `TEACHER`, and `ADMIN`.
- Spring Security route isolation and exception handling (`/api/v1/admin/**` requires `ROLE_ADMIN`).
- User provisioning and lifecycle APIs (creation, filtering, profile updates, account disable/enable, password reset).
- Classroom and roster administration (creation, metadata updates, teacher assignment, student roster management).
- Single source of truth for rosters (`classroom_students` join table directly consumed by Teacher batch processing).
- Operational dashboard metrics and administrative audit logging.
- OpenAPI specification, Architecture Decision Records, Breaking Changes log, and Scope documentation.

Explicitly **out of scope**:
- No `admin-web/` frontend was built (reserved for Track A1.2).
- No self-registration (`/register` remains absent).
- No extra roles (`SUPER_ADMIN`, `PARENT`, `SCHOOL_MANAGER`, `DATA_SCIENTIST`).
- No modification of Phase 4.3 status (remains `BLOCKED_DATASET`).

---

## 3. Existing Domain Reuse
Rather than inventing duplicated schemas, A1.1 reused all existing core domain models:
- **`User.java`**: Base entity used for Admin accounts, preserving existing inheritance and timestamps.
- **`Student.java` & `Teacher.java`**: Subclasses instantiated during user creation based on role.
- **`Classroom.java`**: Preserved existing fields (`teacher`, `students`, `gradeLevel`, `academicYear`).
- **`classroom_students`**: Direct join table used for student membership, keeping teacher batch validation intact.
- **`AuditEvent.java`**: Reused for recording administrative lifecycle events with JSONB metadata.

---

## 4. ADMIN Role Design
The `role` field on `users` was extended from `{"STUDENT", "TEACHER"}` to `{"STUDENT", "TEACHER", "ADMIN"}`.
- Admin accounts are stored directly in `users` without requiring redundant child tables.
- Role is immutable after user creation: admins cannot convert a Student to Teacher or escalate accounts.
- Admin creation through the public API is forbidden: the API only allows provisioning `STUDENT` or `TEACHER`.

---

## 5. Security/RBAC Design
Spring Security configuration in `SecurityConfig.java` enforces strict route separation:
```java
.requestMatchers("/api/v1/student/**").hasRole("STUDENT")
.requestMatchers("/api/v1/teacher/**").hasRole("TEACHER")
.requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
.anyRequest().authenticated()
```
- **Unauthenticated requests** to protected routes receive `401 Unauthorized`.
- **Authenticated requests with the wrong role** (e.g. Student -> Admin, Teacher -> Admin, Admin -> Teacher) receive `403 Forbidden`.
- **Shared endpoints** (`/api/v1/me`, `/api/v1/auth/logout`) accept any authenticated role.
- Role hierarchy (`ADMIN > TEACHER > STUDENT`) was intentionally avoided.

---

## 6. User Account Status Design
The existing `User.active` boolean was integrated across the entire auth pipeline:
1. **Login Prevention:** `UserDetailsServiceImpl` passes `user.getActive()` to Spring Security's `UserDetails.isEnabled()`. Disabled accounts fail login with `401 Unauthorized`.
2. **Refresh Prevention:** `RefreshTokenService.verifyExpiration()` explicitly checks `user.getActive()`. If false, all refresh tokens for that user are revoked and the request fails with `401 Unauthorized`.
3. **Session Purging on Disable:** `POST /api/v1/admin/users/{userId}/disable` sets `active = false` and calls `refreshTokenService.deleteByUserId(userId)`.
4. **Stateless Access Token Boundary:** As per standard JWT stateless architecture, already-issued short-lived access tokens remain valid until expiration (24h dev default); refresh and new logins are immediately rejected upon disabling.
5. **Self-Disable Protection:** Administrators are strictly prohibited from disabling their own account (`400 Bad Request`).

---

## 7. Admin User Endpoints
All administrative user management endpoints were implemented under `/api/v1/admin/users`:
- `POST /api/v1/admin/users`: Creates Student (grade 1..5) or Teacher; rejects ADMIN role; normalizes email; hashes password via BCrypt; never returns password hash.
- `GET /api/v1/admin/users`: Paginated user list with `role`, `active`, and `query` (search by email or name) filtering.
- `GET /api/v1/admin/users/{userId}`: Safe user detail including enrolled/taught classes.
- `PATCH /api/v1/admin/users/{userId}`: Safe updates to `displayName` and student `gradeLevel`. Role remains immutable.
- `POST /api/v1/admin/users/{userId}/disable`: Disables account and revokes refresh tokens.
- `POST /api/v1/admin/users/{userId}/enable`: Re-enables user account.
- `POST /api/v1/admin/users/{userId}/reset-password`: Sets temporary password, revokes existing sessions, and returns the temporary password to the admin.

---

## 8. Admin Classroom Endpoints
Classroom management endpoints were implemented under `/api/v1/admin/classes`:
- `POST /api/v1/admin/classes`: Validates grade (1..5) and verifies assigned teacher exists, has role `TEACHER`, and is active.
- `GET /api/v1/admin/classes`: Paginated list of classrooms with teacher summary and student count.
- `GET /api/v1/admin/classes/{classId}`: Detailed classroom view including full student roster.
- `PATCH /api/v1/admin/classes/{classId}`: Updates class metadata (`name`, `gradeLevel`, `academicYear`).
- `PUT /api/v1/admin/classes/{classId}/teacher`: Reassigns active Teacher to classroom.
- `POST /api/v1/admin/classes/{classId}/students/{studentId}`: Adds active Student to classroom roster (idempotent).
- `DELETE /api/v1/admin/classes/{classId}/students/{studentId}`: Removes Student from classroom roster.

---

## 9. Admin Dashboard
Endpoint `GET /api/v1/admin/dashboard` provides lightweight operational metrics using optimized SQL count queries:
- `totalStudents`, `activeStudents`, `disabledStudents`
- `totalTeachers`, `activeTeachers`, `disabledTeachers`
- `totalClasses`

---

## 10. Admin Audit
- **Write Audit Logging:** Every administrative mutation automatically writes an `AuditEvent` record with the admin actor identity, action type, target ID, and timestamp. Passwords, secrets, and binary images are never included in metadata.
  - `ADMIN_USER_CREATED`, `ADMIN_USER_UPDATED`, `ADMIN_USER_DISABLED`, `ADMIN_USER_ENABLED`, `ADMIN_USER_PASSWORD_RESET`
  - `ADMIN_CLASS_CREATED`, `ADMIN_CLASS_UPDATED`, `ADMIN_CLASS_TEACHER_ASSIGNED`, `ADMIN_STUDENT_ADDED_TO_CLASS`, `ADMIN_STUDENT_REMOVED_FROM_CLASS`
- **Audit Log Inspection:** `GET /api/v1/admin/audit` returns paginated audit records with optional `eventType` filtering.

---

## 11. Database Migration
Created forward-only Flyway migration:
- File: `services/business-api/src/main/resources/db/migration/V5__add_admin_and_audit_indexes.sql`
- Adds performance indexes:
  - `idx_users_role` on `users(role)`
  - `idx_users_active` on `users(active)`
  - `idx_audit_events_created_at` on `audit_events(created_at DESC)`
  - `idx_audit_events_type` on `audit_events(event_type)`
- Preserves all historical student submissions, images, and teacher decisions.

---

## 12. OpenAPI Changes
Updated `contracts/openapi/mathvision-api.yaml`:
- Added `Admin` tag.
- Added 11 admin REST path patterns encompassing 16 distinct HTTP operations:
  - Users (7 operations): `GET /admin/users`, `POST /admin/users`, `GET /admin/users/{userId}`, `PATCH /admin/users/{userId}`, `POST /admin/users/{userId}/disable`, `POST /admin/users/{userId}/enable`, `POST /admin/users/{userId}/reset-password`
  - Classes (7 operations): `GET /admin/classes`, `POST /admin/classes`, `GET /admin/classes/{classId}`, `PATCH /admin/classes/{classId}`, `PUT /admin/classes/{classId}/teacher`, `POST /admin/classes/{classId}/students/{studentId}`, `DELETE /admin/classes/{classId}/students/{studentId}`
  - Dashboard (1 operation): `GET /admin/dashboard`
  - Audit (1 operation): `GET /admin/audit`
- Added DTO schemas: `CreateUserRequest`, `UpdateUserRequest`, `AdminUserSummary`, `AdminClassSummary`, `AdminUserResponse`, `ResetPasswordRequest`, `ResetPasswordResponse`, `CreateClassRequest`, `UpdateClassRequest`, `AssignTeacherRequest`, `AdminClassResponse`, `AdminDashboardResponse`, `AdminAuditEventResponse`.
- Preserved existing Student, Teacher, and Auth endpoint backward compatibility.

---

## 13. Dev Admin Seed
In `SeedDataInitializer.java` (`@Profile("dev")`):
- Account: `admin.demo@mathvision.local`
- Password: `MathVision123!`
- Role: `ADMIN`
- Display Name: `Demo Administrator`
- Seeded idempotently via `userRepository.findByEmail`. Does not run in production-like profiles.

---

## 14. Student/Teacher Compatibility
All existing Student Mobile and Teacher Web endpoints and behavior remain untouched:
- Student submission uploads and diagnostic polling: Unchanged.
- Teacher batch uploads, review queues, and grade decisions: Unchanged.
- Auth tokens: Canonical `accessToken` and `refreshToken` response maintained across all roles.

---

## 15. Admin Login Test
- **Test:** `POST /api/v1/auth/login` with `admin.demo@mathvision.local` / `MathVision123!`.
- **Result:** PASS. Returns valid `accessToken` and `refreshToken`.
- **`/me` Verification:** Returns `{ "role": "ADMIN", "email": "admin.demo@mathvision.local", "displayName": "Demo Administrator" }`.

---

## 16. RBAC Tests
- `Unauthenticated -> /api/v1/admin/**`: 401 Unauthorized (PASS).
- `Student -> /api/v1/admin/**`: 403 Forbidden (PASS).
- `Teacher -> /api/v1/admin/**`: 403 Forbidden (PASS).
- `Admin -> /api/v1/admin/**`: 200 OK (PASS).

---

## 17. User Provisioning Tests
- Admin creates valid Student: 201 Created (PASS).
- Admin creates valid Teacher: 201 Created (PASS).
- Admin creating ADMIN role: 400 Bad Request (PASS).
- Duplicate email creation: 409 Conflict (PASS).
- Student grade level < 1 or > 5: 400 Bad Request (PASS).
- Student grade levels 1 and 5: 201 Created (PASS).
- Teacher with student grade level: 400 Bad Request (PASS).
- Update Student profile (displayName, gradeLevel): 200 OK (PASS).
- Disable Student -> login fails (401), refresh fails (401): PASS.
- Enable Student -> login succeeds (200): PASS.
- Admin disables self: 400 Bad Request (PASS).
- Password hash never returned in JSON response: PASS.

---

## 18. Classroom Tests
- Admin creates class (grade 1..5): 201 Created (PASS).
- Class grade < 1 or > 5: 400 Bad Request (PASS).
- Assign Student as Teacher: 400 Bad Request (PASS).
- Assign disabled Teacher: 400 Bad Request (PASS).
- Assign active Teacher: 200 OK (PASS).
- Add Student as Teacher: 400 Bad Request (PASS).
- Add Teacher as Student: 400 Bad Request (PASS).
- Add active Student to class: 200 OK (PASS).
- Duplicate Student addition: Idempotent 200 OK (PASS).
- Remove Student from class: 200 OK (PASS).
- Nonexistent class/user: 404 Not Found (PASS).

---

## 19. Roster Integration Test
- **Verification:** Admin adds student to a classroom. The student is immediately present in `Classroom.getStudents()` mapped to `classroom_students`.
- **Invariant:** `BatchService.uploadImages` checks `classroom.getStudents().stream().anyMatch(s -> s.getId().equals(student.getId()))`. Roster integration verified with no duplicate roster tables.

---

## 20. Admin Cannot Grade Test
- `POST /api/v1/teacher/submissions/{id}/approve` with Admin JWT: **403 Forbidden** (PASS).
- `POST /api/v1/teacher/submissions/{id}/override` with Admin JWT: **403 Forbidden** (PASS).
- Direct HTTP E2E and MockMvc integration tests both confirmed 403.

---

## 21. Audit Tests
- Verified `ADMIN_USER_CREATED`, `ADMIN_USER_UPDATED`, `ADMIN_USER_DISABLED`, `ADMIN_USER_ENABLED`, `ADMIN_CLASS_CREATED`, `ADMIN_STUDENT_ADDED_TO_CLASS` are persisted in `audit_events`.
- Metadata includes target ID and action details; zero plaintext passwords, tokens, or image binaries.

---

## 22. Spring Test Discovery
JUnit XML test suite execution report (`services/business-api/build/test-results/test/TEST-*.xml`):

| Test Suite | Tests | Fail | Err | Skip |
|:---|:---:|:---:|:---:|:---:|
| `com.mathvisionkids.api.BusinessApiApplicationTests` | 1 | 0 | 0 | 0 |
| `com.mathvisionkids.api.admin.AdminControllerTest` | 20 | 0 | 0 | 0 |
| `com.mathvisionkids.api.analysis.HttpAiAnalysisGatewayTest` | 8 | 0 | 0 | 0 |
| `com.mathvisionkids.api.analysis.InternalAiCallbackControllerTest` | 6 | 0 | 0 | 0 |
| `com.mathvisionkids.api.auth.AuthControllerTest` | 4 | 0 | 0 | 0 |
| `com.mathvisionkids.api.batch.BatchControllerTest` | 7 | 0 | 0 | 0 |
| `com.mathvisionkids.api.dashboard.TeacherDashboardControllerTest` | 4 | 0 | 0 | 0 |
| `com.mathvisionkids.api.submission.StateTransitionTest` | 16 | 0 | 0 | 0 |
| `com.mathvisionkids.api.submission.SubmissionControllerTest` | 5 | 0 | 0 | 0 |
| **TOTAL** | **71** | **0** | **0** | **0** |

---

## 23. Original Tests Regression
- **Baseline before A1.1:** 51 passed, 0 failed, 0 skipped.
- **Current execution:** 51/51 original baseline tests continue to pass with 0 regressions.

---

## 24. New Admin Tests
- **Admin Tests Added:** 20 tests in `AdminControllerTest.java`.
- **Status:** 20 passed, 0 failed, 0 skipped.

---

## 25. Spring Build
- Command: `gradlew.bat build`
- Result: **BUILD SUCCESSFUL** (0 errors).

---

## 26. Python Regression
- Command: `services/ai-service/.venv/Scripts/python.exe -m pytest tests/`
- Result: **97 passed, 0 failed, 0 skipped** in 9.22s.

---

## 27. Student Regression
- Command: `npx tsc --noEmit` -> 0 errors.
- Command: `npm run lint` -> 0 errors (8 preexisting warnings).

---

## 28. Teacher Regression
- Command: `npm run build` in `teacher-web/` -> **built in 2.85s**, 0 errors.

---

## 29. Runtime Regression
- Executed: `scripts\restart-all.bat`
- Output:
  - Docker: PASS
  - PostgreSQL: PASS
  - MinIO: PASS
  - Redis: PASS
  - Spring Boot: PASS (PID: 30684)
  - FastAPI: PASS (PID: 19792)
  - Celery: PASS (PID: 1812)
  - Teacher Web: PASS (PID: 30992)
  - Diagnostic: **Overall READY_FOR_DEMO**
  - Extra popup terminals: **0**

---

## 30. Model SHA
- File: `services/ai-service/models/yolov8n_mathvision_det_v1.pt`
- Recomputed SHA-256: `E78F8FA5A2FC8BE581B8624FA510CD2C429C40CDBD0930DBB2F1C2D870338985`
- Status: **PASS** (Zero weight modification).

---

## 31. Files Created
1. `services/business-api/src/main/resources/db/migration/V5__add_admin_and_audit_indexes.sql`
2. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/CreateUserRequest.java`
3. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/UpdateUserRequest.java`
4. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AdminUserSummary.java`
5. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AdminClassSummary.java`
6. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AdminUserResponse.java`
7. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/ResetPasswordRequest.java`
8. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/ResetPasswordResponse.java`
9. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/CreateClassRequest.java`
10. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/UpdateClassRequest.java`
11. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AssignTeacherRequest.java`
12. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AdminClassResponse.java`
13. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AdminDashboardResponse.java`
14. `services/business-api/src/main/java/com/mathvisionkids/api/admin/dto/AdminAuditEventResponse.java`
15. `services/business-api/src/main/java/com/mathvisionkids/api/admin/AdminService.java`
16. `services/business-api/src/main/java/com/mathvisionkids/api/admin/AdminController.java`
17. `services/business-api/src/test/java/com/mathvisionkids/api/admin/AdminControllerTest.java`
18. `docs/admin/ADMIN_LITE_SCOPE.md`
19. `report/parallel_a1_1_admin_backend_rbac.md`

---

## 32. Files Modified
1. `services/business-api/src/main/java/com/mathvisionkids/api/user/UserRepository.java` (added counts and JpaSpecificationExecutor)
2. `services/business-api/src/main/java/com/mathvisionkids/api/classroom/ClassroomRepository.java` (added `findByStudents_Id`)
3. `services/business-api/src/main/java/com/mathvisionkids/api/audit/AuditEventRepository.java` (added paginated query methods)
4. `services/business-api/src/main/java/com/mathvisionkids/api/config/SecurityConfig.java` (added `/api/v1/admin/**` route protection and 401/403 entry points)
5. `services/business-api/src/main/java/com/mathvisionkids/api/config/SeedDataInitializer.java` (added dev admin seed)
6. `services/business-api/src/main/java/com/mathvisionkids/api/auth/RefreshTokenService.java` (added disabled account check in `verifyExpiration`)
7. `contracts/openapi/mathvision-api.yaml` (added Admin endpoints, tags, and schemas)
8. `contracts/ARCHITECTURE_DECISIONS.md` (added ADR-011)
9. `contracts/BREAKING_CHANGES.md` (documented additive ADMIN role extension)

---

## 33. Deferred Items
- `PASSWORD_RESET=DEFERRED_TO_A1_3`: The backend provides an administrative temporary password reset endpoint (`POST /api/v1/admin/users/{userId}/reset-password`), but full client-enforced forced password changes on first login are deferred to A1.3 to avoid modifying the frozen Student and Teacher frontends.
- `ADMIN_WEB=DEFERRED_TO_A1_2`: Admin web portal frontend implementation is deferred to Track A1.2.

---

## 34. Known Limitations
- Stateless JWT access tokens remain valid until expiration (up to 24h in dev); however, refresh-token rotation and future logins are blocked immediately upon account disablement.
- Admin cannot provision another Admin through the public API; dev seed or direct DB operations are required for bootstrapping new administrators.

---

## 35. Final Assessment
**Status: IMPLEMENTED_VERIFIED**
All requirements of Track A1.1 have been met with zero regressions on existing student, teacher, and AI components. RBAC boundaries and the "Admin Cannot Grade" invariant are proven both by automated integration tests and live HTTP E2E execution.

---

## 36. Recommended A1.2 Inputs
For Track A1.2 (Admin Web):
1. Use the canonical openapi contract in `contracts/openapi/mathvision-api.yaml` for generating TypeScript API clients.
2. Build an isolated `admin-web/` Vite React application (do not embed admin pages in `teacher-web/`).
3. Leverage `GET /api/v1/admin/dashboard` for the overview landing page.
4. Implement tabular views for User Management and Classroom Administration with active/disabled toggling and student roster assignment modals.
