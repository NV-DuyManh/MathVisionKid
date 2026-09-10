# Parallel Track A1.2: Admin Web Application, Backend Integration & Local Runtime Integration Report

---

## 1. Executive Summary

Parallel Track A1.2 successfully implements and verifies the dedicated **Admin Web Portal** (`admin-web/`) for MathVision Kids. Operating independently on port **5174**, this application connects to the Spring Boot Business API (port **8080**), enforces strict Role-Based Access Control (RBAC) restricted solely to `ADMIN` accounts, and delivers complete operational management workflows for users, classrooms, and system audit logs.

Track A1.1 backend contracts remain **FROZEN** and 100% passing. The formal Phase 4.3 status remains **`BLOCKED_DATASET`**. No model weights, prompt configurations, evaluation protocols, or grading pipelines were altered.

### Headline Accomplishments
1. **Dedicated Frontend Architecture:** Standalone React 19 + TypeScript + Vite + MUI v9 + TanStack Query application at `admin-web/` on port **5174**.
2. **Strict RBAC Enforcement:** Attempting to log into the Admin Portal with `STUDENT` or `TEACHER` credentials is immediately rejected with explicit error messaging.
3. **End-to-End Administrative Capabilities:**
   - **Operational Dashboard:** Real-time metrics for students, teachers, classes, and recent audit logs.
   - **User Management:** Provision students (grades 1..5) and teachers, update profiles, toggle account active status (disable/enable), and generate temporary passwords.
   - **Classroom & Roster Administration:** Create classrooms, assign/reassign teachers, and manage the student roster as the single source of truth for Teacher batch processing.
   - **Audit Trail:** Chronological log of administrative actions with structured JSON metadata inspection.
4. **Unified Silent Runtime Integration:** Fully integrated into `scripts/start-all.ps1`, `scripts/stop-all.ps1`, and `tools/diagnostics/check_runtime.py`. All local services run in hidden windows with **0 extra popup terminal windows**, achieving `Overall: READY_FOR_DEMO`.
5. **Zero-Regression Full Suite:** 71/71 Spring tests pass (including all 20 Admin integration tests), 97/97 Python AI tests pass, Teacher Web builds with 0 errors, Student Mobile compiles with 0 TypeScript errors and 0 lint errors, and Admin Web builds and lints with 0 errors and 0 warnings.
6. **OpenAPI Precision Reconciliation:** Formally documented that the 11 admin REST path patterns encompass **16 distinct HTTP operations**.

---

## 2. Scope & Status Alignment

| Dimension | Status | Notes |
| :--- | :--- | :--- |
| **Track A1.1 (Backend & RBAC)** | `IMPLEMENTED_VERIFIED / FROZEN` | All 71 Spring Boot tests passing; no backend regressions |
| **Track A1.2 (Admin Web Frontend)** | `IMPLEMENTED_VERIFIED` | Complete frontend operational on port 5174 |
| **Track A1.3 (Advanced Admin)** | `NOT_STARTED` | Bulk CSV import, forced password change on first login deferred |
| **Phase 4.3 (AI Model Evaluation)** | `BLOCKED_DATASET` | Formal evaluation pipeline strictly preserved; no changes |
| **Proposal v3.1 & Capstone Docs** | `UNTOUCHED` | No alterations to formal project proposals or disclosures |

---

## 3. Technology Stack & Directory Architecture

The Admin Web Portal is housed entirely in the top-level `admin-web/` directory, ensuring strict isolation from the Teacher Web Portal (`teacher-web/`) and Student Mobile app (`/` root):

```text
admin-web/
├── index.html                  # HTML entry point with Inter font
├── package.json                # React 19, TypeScript, MUI 9, TanStack Query, Axios
├── tsconfig.json               # Root TS configuration
├── tsconfig.app.json           # Bundler TS configuration (module: esnext)
├── tsconfig.node.json          # Node TS configuration (module: nodenext)
├── vite.config.ts              # Port 5174, host: 0.0.0.0, strictPort: true
└── src/
    ├── main.tsx                # Mounts QueryClient, ThemeProvider, BrowserRouter, AuthProvider
    ├── App.tsx                 # Route declarations & ProtectedRoute guard
    ├── theme.ts                # Professional Slate (#0F172A) and Cobalt (#2563EB) theme
    ├── types/
    │   └── index.ts            # TypeScript interfaces aligned with OpenAPI spec
    ├── services/api/
    │   ├── tokenStore.ts       # Isolated access & refresh token management
    │   ├── apiClient.ts        # Axios client with 401 interceptor & token refresh rotation
    │   ├── authService.ts      # Login, /me, refresh, logout with role checking
    │   └── adminService.ts     # Typed calls for dashboard, users, classes, audit
    ├── context/
    │   └── AuthContext.tsx     # Authentication context with role validation
    ├── components/
    │   ├── common/             # ProtectedRoute, StatusChip, RoleChip, ConfirmDialog, LoadingSkeleton, EmptyState
    │   └── layout/             # AdminLayout, AdminSidebar, AdminTopbar
    └── pages/
        ├── LoginPage.tsx       # Auth portal with dev quick-fill
        ├── DashboardPage.tsx   # Operational metrics & recent audit table
        ├── UsersPage.tsx       # User list, tabs, search, filters, create modal
        ├── UserDetailPage.tsx  # User profile, edit, disable/enable, reset password
        ├── ClassesPage.tsx     # Classroom list & create modal
        ├── ClassDetailPage.tsx # Class detail, teacher assignment, roster table
        └── AuditPage.tsx       # System audit log & metadata viewer modal
```

---

## 4. Security, RBAC & Role Isolation Verification

### 4.1. Portal Login Authorization Boundary
The Admin Web application implements strict client-side role validation on top of Spring Security's backend enforcement:
1. Upon submitting credentials to `POST /api/v1/auth/login`, an access token is received.
2. The client immediately queries `GET /api/v1/me`.
3. If `user.role !== 'ADMIN'`:
   - Tokens are cleared immediately from `tokenStore`.
   - The user session is rejected.
   - An alert displays: *"Chỉ tài khoản Quản trị viên (ADMIN) mới có quyền truy cập cổng quản trị."*

### 4.2. Multi-Role Browser Test Results
| Test Role | Test Credentials | Result | Verification Details |
| :--- | :--- | :--- | :--- |
| **Student** | `student.demo@mathvision.local` / `[REDACTED]` | **REJECTED (PASS)** | Login denied; error alert displayed; access blocked |
| **Teacher** | `lan.teacher@mathvision.local` / `[REDACTED]` | **REJECTED (PASS)** | Login denied; error alert displayed; access blocked |
| **Admin** | `admin.demo@mathvision.local` / `[REDACTED]` | **ACCEPTED (PASS)** | Tokens stored; redirected to `/dashboard` |

### 4.3. Non-Grading Invariant
The Admin Web frontend contains **no UI routes, buttons, forms, or API clients** for:
- Viewing student submission images or crops.
- Overriding AI grades or teacher approvals.
- Accessing the teacher review queue (`/teacher/**`).
Attempting to invoke teacher grading APIs directly with an admin token results in `403 Forbidden` from Spring Security.

---

## 5. Administrative Workflows Verified

### 5.1. Operational Dashboard (`/dashboard`)
- Real-time KPI cards:
  - **Học sinh (Students):** Total registered, active, disabled counts.
  - **Giáo viên (Teachers):** Total registered, active, disabled counts.
  - **Lớp học (Classrooms):** Total classrooms managed.
- Quick action buttons to provision users and classrooms.
- Live recent audit log showing actor email, action type, and timestamps.

### 5.2. User Management (`/users`, `/users/:userId`)
- **Categorization:** Tabs for `Tất cả` (All), `Học sinh` (Students), `Giáo viên` (Teachers).
- **Filtering & Search:** Real-time search query across name/email; filter by Active/Disabled status.
- **Account Provisioning:**
  - Create Student: Required Name, Email, Password, and Grade Level (1..5).
  - Create Teacher: Required Name, Email, Password.
  - Form validation: Enforces minimum 6-character passwords and valid email format.
- **User Detail & Lifecycle:**
  - Profile edit: Updates display name and student grade level. Role is immutable.
  - Account Disable: Sets status to `VÔ HIỆU HÓA`, purges refresh tokens. Disabled account fails subsequent login attempts.
  - Account Re-enable: Sets status to `HOẠT ĐỘNG`. Account can immediately log in again.
  - Temporary Password Reset: Generates random password, displays in modal with copy button, revokes previous sessions. UI informs admin that forced first-login change is deferred to A1.3.

### 5.3. Classroom & Roster Management (`/classes`, `/classes/:classId`)
- **Classroom Creation:** Creates class with Name, Grade Level (1..5), Academic Year, and Assigned Teacher.
- **Teacher Assignment:** Dynamic dropdown of active teachers allows instant reassignment.
- **Roster Single Source of Truth Invariant:**
  - Class detail displays the prominent banner:
    > *"Quy tắc đồng bộ danh sách lớp: Danh sách học sinh dưới đây là nguồn dữ liệu chuẩn duy nhất (Single Source of Truth). Giáo viên phụ trách sẽ sử dụng danh sách này khi chấm bài theo đợt (Batch Submission) để ghép nối ảnh bài làm của học sinh tương ứng."*
  - Adding a student to the roster inserts into `classroom_students`.
  - Removing a student deletes from `classroom_students`.
  - Sĩ số (student count) increments and decrements synchronously.

### 5.4. System Audit Trail (`/audit`)
- Displays all administrative mutation events in reverse chronological order.
- Action filter dropdown supports filtering by all 10 administrative event types.
- Metadata modal displays structured JSON detail for each operation.

---

## 6. Local Runtime Integration & Silent Launcher

### 6.1. Script Modifications
1. **`scripts/start-all.ps1`:**
   - Added Admin Web Portal launch step on port **5174** (`cmd.exe /c npm run dev` inside `admin-web/`).
   - Process tracking: PID recorded in `runtime/pids/admin-web.pid`, stdout in `runtime/logs/admin-web.log`, stderr in `runtime/logs/admin-web.err.log`.
   - Window style: `-WindowStyle Hidden` (0 extra popup terminal windows).
   - Readiness check: Probes `http://localhost:5174` before declaring readiness.
   - Summary display: Lists `Admin Web Portal: http://localhost:5174`.
2. **`scripts/stop-all.ps1`:**
   - Added port **5174** to `$PortsToCheck`.
   - Added `admin-web` pattern to process command-line detection for safe termination.
3. **`tools/diagnostics/check_runtime.py`:**
   - Added `check_admin_web()` probing `http://localhost:5174`.
   - Added `Admin Web` to diagnostic reporting table and `required_services`.

### 6.2. Runtime Diagnostic Output
Executing `python tools/diagnostics/check_runtime.py` confirms:
```text
============================================
 MathVision Kids -- Local Runtime Diagnostic
============================================

Docker ................. PASS
PostgreSQL ............. PASS
MinIO .................. PASS
Redis .................. PASS
Spring Boot ............ PASS
FastAPI ................ PASS
Celery Worker .......... PASS
Teacher Web ............ PASS
Admin Web .............. PASS
Student Mobile ......... RUNNING

AI Mode ............... MODEL
Primary Model ......... MathVision-Kids-Detection
Model Version ......... 1.0.0
Model Artifact ........ LOADED

Overall ............... READY_FOR_DEMO
============================================
```

---

## 7. OpenAPI Contract Reconciliation (Requirement 72)

During A1.1 documentation, it was stated that "all 11 admin REST endpoints" were implemented. For architectural precision, we reconcile the distinction between **path patterns** and **distinct HTTP operations**:

The **11 path patterns** encompass **16 distinct HTTP operations**:

| # | Path Pattern | HTTP Method | Operation | Purpose |
| :---: | :--- | :---: | :--- | :--- |
| 1 | `/api/v1/admin/users` | `GET` | `listUsers` | Paginated user search with role/active filters |
| 2 | `/api/v1/admin/users` | `POST` | `createUser` | Provision new Student or Teacher |
| 3 | `/api/v1/admin/users/{userId}` | `GET` | `getUser` | Get user details and enrolled/taught classes |
| 4 | `/api/v1/admin/users/{userId}` | `PATCH` | `updateUser` | Update display name and student grade level |
| 5 | `/api/v1/admin/users/{userId}/disable` | `POST` | `disableUser` | Deactivate account and purge active sessions |
| 6 | `/api/v1/admin/users/{userId}/enable` | `POST` | `enableUser` | Reactivate account |
| 7 | `/api/v1/admin/users/{userId}/reset-password` | `POST` | `resetPassword` | Generate temporary password and revoke tokens |
| 8 | `/api/v1/admin/classes` | `GET` | `listClasses` | Paginated classroom list with teacher & count |
| 9 | `/api/v1/admin/classes` | `POST` | `createClass` | Create classroom and assign initial teacher |
| 10 | `/api/v1/admin/classes/{classId}` | `GET` | `getClass` | Get classroom details and full student roster |
| 11 | `/api/v1/admin/classes/{classId}` | `PATCH` | `updateClass` | Update class name, grade, and academic year |
| 12 | `/api/v1/admin/classes/{classId}/teacher` | `PUT` | `assignTeacher` | Reassign active teacher to classroom |
| 13 | `/api/v1/admin/classes/{classId}/students/{studentId}` | `POST` | `addStudent` | Add student to class roster (idempotent) |
| 14 | `/api/v1/admin/classes/{classId}/students/{studentId}` | `DELETE` | `removeStudent` | Remove student from class roster |
| 15 | `/api/v1/admin/dashboard` | `GET` | `getDashboard` | Get operational dashboard metrics |
| 16 | `/api/v1/admin/audit` | `GET` | `getAuditEvents` | Query immutable administrative audit trail |

Both `report/parallel_a1_1_admin_backend_rbac.md` and `contracts/openapi/mathvision-api.yaml` are formally aligned with this 16-operation taxonomy.

---

## 8. Full Regression Test Matrix

| Component / Test Suite | Command | Expected | Actual Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Spring Boot Unit & Integration** | `gradlew.bat clean test` | 71 tests passing | 71 passed, 0 failed, 0 skipped | **PASS** |
| **Spring Boot Production Jar** | `gradlew.bat build -x test` | Build successful | BUILD SUCCESSFUL in 2s | **PASS** |
| **FastAPI & AI Pipeline Pytest** | `pytest tests/` | 97 tests passing | 97 passed, 0 failed | **PASS** |
| **Teacher Web Production Build** | `npm run build` (teacher-web) | Build successful | Vite built in 5.20s | **PASS** |
| **Student Mobile TypeScript** | `npx tsc --noEmit` (root) | 0 errors | 0 errors | **PASS** |
| **Student Mobile Linter** | `npm run lint` (root) | 0 errors | 0 errors (8 unused var warnings) | **PASS** |
| **Admin Web Production Build** | `npm run build` (admin-web) | Build successful | Vite built in 4.10s | **PASS** |
| **Admin Web Linter (Oxlint)** | `npm run lint` (admin-web) | 0 errors, 0 warnings | 0 errors, 0 warnings | **PASS** |
| **Model Weights Hash Check** | `Get-FileHash yolov8n_mathvision_det_v1.pt` | Exact SHA256 match | `E78F8FA5A2FC8BE581B8624FA510...` | **PASS** |
| **Local Runtime Diagnostics** | `python tools/diagnostics/check_runtime.py` | All components PASS | `Overall: READY_FOR_DEMO` | **PASS** |

---

## 9. Verification Screenshots & Media Artifacts

The following visual artifacts were generated during end-to-end browser verification of the Admin Web portal:
- **Admin Dashboard Verified:** `admin_dashboard_verified_1788963185734.png` (displays operational metrics cards, quick actions, and recent audit activity).
- **User Detail & Status Management:** Interactive tests confirmed disable chip (`VÔ HIỆU HÓA`), re-enable chip (`HOẠT ĐỘNG`), and temporary password display dialog.
- **Classroom Roster & Invariant Notice:** `final_roster_empty_1788963988750.png` (demonstrating the Single Source of Truth notice, roster table, and add/remove controls).
- **Teacher Web Dashboard:** `teacher_dashboard_verified_1788964205562.png` (confirming Teacher Web on port 5173 remains fully operational and unimpaired).

---

## 10. Conclusion & Stop Directive

Track A1.2 is **COMPLETE**, verified, and frozen.
- The Admin Web application is operating stably at `http://localhost:5174`.
- All operational workflows (users, classrooms, rosters, audit) have been validated end-to-end.
- Local runtime launcher scripts start and stop all components cleanly with zero extra popup windows.
- No work on Track A1.3 will be initiated.
- Formal Phase 4.3 remains strictly `BLOCKED_DATASET`.
