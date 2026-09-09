# MathVision Kids — Admin Web Application Guide (Track A1.2)

---

## 1. Overview & Architecture

The **Admin Web Portal** (`admin-web/`) is an isolated, dedicated frontend web application designed exclusively for MathVision Kids system administrators. It operates independently on port **5174**, connecting to the Spring Boot Business API on port **8080** and operating alongside the Teacher Web Portal (port **5173**) and Student Mobile Client (port **8081**).

### Key Architectural Invariants
- **Port Allocation:** `5174` (strict non-conflict with Teacher Web on `5173` or Expo Metro on `8081`).
- **Project Structure:** Fully standalone directory at repository root (`admin-web/`), with its own `package.json`, TypeScript configuration, Vite build pipeline, and styling assets.
- **Strict Role Isolation:** Only accounts with role `ADMIN` can access the portal. Attempts to authenticate with `STUDENT` or `TEACHER` credentials are automatically rejected.
- **Non-Grading Invariant:** Administrators have zero access to student submissions, grading queues, or AI evaluation overrides. Administrative privileges are strictly bounded to provisioning, roster management, and system auditing.

---

## 2. Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Runtime & Bundler** | Vite | `^8.2.2` | Fast HMR dev server & production bundling |
| **Framework** | React | `^19.2.8` | Declarative UI component tree |
| **Language** | TypeScript | `~6.0.2` | Static type safety and contract enforcement |
| **UI Component System** | Material UI (MUI) | `^9.4.0` | Executive Slate & Cobalt theme system |
| **Icons** | MUI Icons | `^9.4.0` | SVG iconography |
| **Data Fetching** | TanStack Query | `^5.102.8` | Query caching, mutation lifecycles, cache invalidation |
| **HTTP Client** | Axios | `^1.20.0` | Bearer auth interceptors & refresh rotation |
| **Routing** | React Router | `^7.18.3` | Client-side routing with protected route guards |
| **Linter** | Oxlint | `^1.79.0` | Fast, zero-config linting (0 errors, 0 warnings) |

---

## 3. Authentication & RBAC Boundary

### Authentication Flow
1. **Login (`/login`):** Admin submits email and password.
2. **Backend Authentication:** Spring Boot issues standard JWT token pair (`accessToken` and `refreshToken`).
3. **Role Verification:** The client immediately calls `/api/v1/me` to inspect the authenticated principal's role.
   - If `role === 'ADMIN'`: Tokens are retained in memory and local storage, user state is initialized, and user is redirected to `/dashboard`.
   - If `role !== 'ADMIN'` (e.g. `TEACHER` or `STUDENT`): Tokens are immediately discarded, local state is purged, and the UI displays:
     > *"Chỉ tài khoản Quản trị viên (ADMIN) mới có quyền truy cập cổng quản trị."*
4. **Token Refresh Rotation:** If an API request encounters HTTP `401 Unauthorized`, Axios interceptor automatically requests a refreshed access token using `/api/v1/auth/refresh`. If refresh fails or account is disabled, session is terminated and user is redirected to `/login`.

### Dev Seed Account
In development (`@Profile("dev")`), a pre-configured administrator account is seeded:
- **Email:** `admin.demo@mathvision.local`
- **Password:** `MathVision123!`
- **Helper:** The login screen provides a quick-fill button ("Điền tài khoản Admin mẫu") for instant testing.

---

## 4. Administrative Features & User Workflows

### 4.1. Operational Dashboard (`/dashboard`)
Displays real-time system metrics using lightweight SQL count queries:
- **Students:** Total registered, active accounts, disabled accounts.
- **Teachers:** Total registered, active accounts, disabled accounts.
- **Classrooms:** Total managed classrooms.
- **Quick Links:** Shortcuts to immediately provision users or classrooms.
- **Recent Audit Trail:** Live table of the 6 most recent administrative actions with timestamps and actor emails.

### 4.2. User Management (`/users`, `/users/:userId`)
- **Role Tabs:** Segment accounts into `Tất cả` (All), `Học sinh` (Students), and `Giáo viên` (Teachers).
- **Search & Filters:** Real-time search by full name or email, filter by active or disabled status.
- **Account Provisioning:**
  - Create Student: Requires Name, Email, Password (min 6 characters), and Grade Level (1..5).
  - Create Teacher: Requires Name, Email, and Password.
  - Normalizes email to lowercase; passwords hashed via BCrypt on backend; raw password hash is never exposed.
- **Profile Updates:** Safe modification of display names and student grade levels. Roles remain strictly immutable.
- **Account Lifecycle (Disable / Enable):**
  - Disable: Sets `active = false`, invalidates active refresh tokens, and immediately blocks further login attempts.
  - Enable: Restores account status to `active = true`, permitting logins.
  - Self-Protection: Administrators are blocked by the backend from disabling their own account.
- **Temporary Password Reset:**
  - Generates a cryptographically random temporary password and revokes existing refresh tokens.
  - Displays the generated temporary password in a secure modal with a one-click copy button.
  - *Notice:* The UI clearly notifies administrators that forced password reset on first login is deferred to Track A1.3.

### 4.3. Classroom & Roster Administration (`/classes`, `/classes/:classId`)
- **Class Creation:** Specify Class Name (e.g. "Lớp 3A"), Grade Level (1..5), Academic Year (e.g. "2025-2026"), and assign an active Teacher.
- **Teacher Assignment:** Reassign any active teacher to lead the classroom.
- **Student Roster Management:**
  - Add active students to the class roster (idempotent, prevents duplicates).
  - Remove students from the class roster.
- **Single Source of Truth Invariant:**
  - The student roster table directly maps to the `classroom_students` database join table.
  - This join table is the **exact authoritative source** read by the Teacher Web Portal during batch submission processing (`/api/v1/teacher/batches`).
  - An informational banner is prominently displayed on the class detail page to reinforce this architectural invariant.

### 4.4. System Audit Trail (`/audit`)
- **Full Historical Log:** Displays all recorded `AuditEvent` records in reverse chronological order.
- **Action Filters:** Filter by event type (`ADMIN_USER_CREATED`, `ADMIN_USER_UPDATED`, `ADMIN_USER_DISABLED`, `ADMIN_USER_ENABLED`, `ADMIN_USER_PASSWORD_RESET`, `ADMIN_CLASS_CREATED`, `ADMIN_CLASS_UPDATED`, `ADMIN_CLASS_TEACHER_ASSIGNED`, `ADMIN_STUDENT_ADDED_TO_CLASS`, `ADMIN_STUDENT_REMOVED_FROM_CLASS`).
- **Metadata Viewer:** Modal inspection of detailed structured JSON metadata (actor email, target IDs, affected fields) for compliance auditing.

---

## 5. Local Runtime Integration

### Starting the Unified Stack
Run the standard unified launcher:
```cmd
scripts\start-all.bat
```
or from PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1
```

**Services Started (Hidden Windows / 0 Popups):**
1. Docker Compose: PostgreSQL (5432), MinIO (9000), Redis (6379)
2. Spring Boot Business API: `http://127.0.0.1:8080` (PID in `runtime/pids/spring.pid`)
3. FastAPI AI Runtime: `http://127.0.0.1:8000` (PID in `runtime/pids/fastapi.pid`)
4. Celery Worker: Worker pool running background AI tasks
5. Teacher Web Portal: `http://localhost:5173` (PID in `runtime/pids/teacher-web.pid`)
6. **Admin Web Portal:** `http://localhost:5174` (PID in `runtime/pids/admin-web.pid`)

### Stopping the Stack
```cmd
scripts\stop-all.bat
```
Safely terminates all background processes (including port 5174) and stops infrastructure containers.

### Diagnostic Verification
Run the diagnostic tool to verify all components:
```cmd
python tools\diagnostics\check_runtime.py
```
Output:
```text
Docker ................. PASS
PostgreSQL ............. PASS
MinIO .................. PASS
Redis .................. PASS
Spring Boot ............ PASS
FastAPI ................ PASS
Celery Worker .......... PASS
Teacher Web ............ PASS
Admin Web .............. PASS
Student Mobile ......... CONFIGURED (or RUNNING)

Overall ............... READY_FOR_DEMO
```

---

## 6. Scope Boundaries & Deferred Features (Track A1.3)

The following features were intentionally excluded from Track A1.2 and are reserved for Track A1.3:
1. **Bulk CSV / Excel User Import:** All account provisioning in A1.2 is performed via individual interactive forms.
2. **Mandatory Password Reset on First Login:** Temporary passwords allow immediate login; `passwordResetRequired` state enforcement will be introduced in A1.3.
3. **Parent Account Linkage:** Only `STUDENT`, `TEACHER`, and `ADMIN` accounts exist in the database.
4. **Multi-Tenant / District Hierarchy:** MathVision Kids operates as a single-school deployment model.
