# MathVision Kids — ECOSYSTEM.PORTAL.1 Authority Report
## Unified Entry, Role-Based Routing & Shared Product Experience

**Document Status:** AUTHORITATIVE REFROZEN  
**Project:** MathVision Kids  
**Milestone:** ECOSYSTEM.PORTAL.1  
**Mode:** Frontend / Auth Integration, Zero Model Training, No Large Backend Rewrite  
**Target Environment:** Local-First Hybrid Architecture (Spring Boot 8080, FastAPI 8000, MinIO 9000/9001, Redis 6379, PostgreSQL 5432, Portal Web 5172, Teacher Web 5173, Admin Web 5174, Student Mobile 8081)  
**Execution Timestamp:** 2026-09-12T19:50:00+07:00  

---

## 1. Executive Summary

Prior to milestone **ECOSYSTEM.PORTAL.1**, the MathVision Kids platform existed as separate client silos:
1. **Student Mobile** (Expo 57 / React Native) for handwriting capture and arithmetic feedback.
2. **Teacher Web** (Vite + React 19 + MUI 9 on port 5173) for classroom assignments and AI batch grading oversight.
3. **Admin Web** (Vite + React 19 + MUI 9 on port 5174) for user administration and system audit logs.

While all clients shared the same Spring Boot backend, database, and RBAC authentication system, users lacked a single product entry point, consistent design language, and unified role-based navigation. 

**ECOSYSTEM.PORTAL.1** establishes:
- **One Unified Entry (`http://localhost:5172`)**: The `portal-web` application welcomes all visitors, communicates the product identity, and serves as the single login gateway.
- **Server-Verified Role-Based Automatic Dispatch**: When an authenticated user logs in, the portal inspects the cryptographically signed role from Spring Boot and routes them:
  - `STUDENT` $\rightarrow$ Dedicated Student Landing & Mobile Connection Guide.
  - `TEACHER` $\rightarrow$ Cryptographically verified handoff to Teacher Web (`http://localhost:5173`).
  - `ADMIN` $\rightarrow$ Cryptographically verified handoff to Admin Web (`http://localhost:5174`).
- **Secure One-Time SSO Handoff**: A ticket-based handoff mechanism (`POST /api/v1/auth/sso/ticket` and `POST /api/v1/auth/sso/exchange`) that guarantees:
  - **Zero JWT/tokens in URL query parameters**.
  - **Single-use consumption with atomic cache removal** (immune to replay attacks).
  - **60-second time-to-live (TTL)**.
  - **Strict role-to-target RBAC validation**.
- **Shared Design Tokens (`packages/ui-brand`)**: Cohesive typography, harmonious color palette, role-specific badge styling, and shared navigation back to the unified ecosystem.
- **Integrated Tooling & Readiness Diagnostic**: One-click startup via `RUN_MATHVISION.bat` / `scripts/start-all.ps1`, zero-orphan shutdown via `scripts/stop-all.ps1`, and diagnostic verification via `tools/diagnostics/check_runtime.py` reporting `READY_FOR_DEMO`.

All 26 automated E2E integration tests and 117 Spring Boot backend unit/integration tests pass with 0 failures.

---

## 2. Product & Architecture Vision

MathVision Kids is designed as an AI-assisted handwritten arithmetic grading and tutoring platform for elementary schools. The ecosystem architecture unites three specialized experiences:

```
                              MathVision Kids Ecosystem
                                          │
                        ┌─────────────────┴─────────────────┐
                        │   Unified Portal (Port 5172)      │
                        │   Branding • Gateway • Login      │
                        └─────────────────┬─────────────────┘
                                          │
                         [Backend Authenticated Role Dispatch]
                                          │
           ┌──────────────────────────────┼──────────────────────────────┐
           ▼                              ▼                              ▼
     [ROLE: STUDENT]               [ROLE: TEACHER]                [ROLE: ADMIN]
  Student Landing & Mobile       SSO Handoff Ticket             SSO Handoff Ticket
   Connection (Port 5172)        (60s Single-Use)               (60s Single-Use)
           │                              │                              │
           ▼                              ▼                              ▼
  Student Mobile App             Teacher Web Portal             Admin Web Portal
 (Expo 57 / Metro 8081)             (Port 5173)                    (Port 5174)
  Camera • OCR • AI Check       Classes • Batches • Review     Users • Audit • Security
```

### Architectural Principles Preserved:
1. **Separation of Concerns**: Student Mobile remains a mobile-first Expo app tailored for camera hardware and touch interaction; Teacher Web remains a rich desktop workspace; Admin Web remains a hardened administrative console.
2. **Local-First & Offline Resilience**: Frontends communicate with local Spring Boot (8080) and local FastAPI AI (8000).
3. **Defense-in-Depth**: Frontends guide users, but the backend strictly enforces authorization boundaries regardless of client-side routing.

---

## 3. Single Entry vs Multi-App Boundary Analysis

During the design phase, two candidate integration models were evaluated:

| Criterion | Option A: Single-Origin Proxy (Vite Dev Proxy) | Option B: Secure One-Time SSO Handoff (Selected) |
|---|---|---|
| **Architectural Complexity** | High: Multi-SPA reverse proxy in Vite dev mode causes asset root collision (`/@vite/client`, `/src/main.tsx`). | Minimal: Independent Vite dev servers running on designated ports (5172, 5173, 5174). |
| **HMR Reliability** | Fragile: WebSocket and HMR connections drop across nested subpaths. | Rock-Solid: Native HMR on each development server. |
| **Token Security** | Vulnerable if tokens leaked across origins. | Maximum: 60s single-use cryptographically random ticket exchanged via HTTP POST; zero JWT in URL query strings. |
| **Physical Phone Access** | Confusing path rewrites. | Clear: Direct connection to Expo Metro or Spring Boot LAN IP. |
| **Decision** | Rejected due to development fragility. | **ADOPTED & IMPLEMENTED**. |

---

## 4. Authentication & RBAC Alignment

MathVision Kids enforces three core roles defined in PostgreSQL and Spring Security:

| Role | Target Client Experience | Permitted API Endpoints | Forbidden API Endpoints |
|---|---|---|---|
| `ROLE_STUDENT` | Student Mobile (8081) & Portal Student Page (5172) | `/api/v1/ocr/**`, `/api/v1/students/**` | `/api/v1/teacher/**` (403), `/api/v1/admin/**` (403) |
| `ROLE_TEACHER` | Teacher Web Portal (5173) | `/api/v1/teacher/**`, `/api/v1/auth/sso/ticket` (TEACHER) | `/api/v1/admin/**` (403) |
| `ROLE_ADMIN` | Admin Web Portal (5174) | `/api/v1/admin/**`, `/api/v1/teacher/**`, `/api/v1/auth/sso/ticket` (ADMIN) | Student-only endpoints (403) |

---

## 5. SSO / Authenticated Handoff Mechanism

### 5.1 Protocol Flow
1. **User Login**: User submits credentials to `POST /api/v1/auth/login` on `portal-web`.
2. **Ticket Request**: Upon receiving user profile with role `TEACHER` or `ADMIN`, `portal-web` calls:
   ```http
   POST /api/v1/auth/sso/ticket
   Authorization: Bearer <Portal_Access_Token>
   Content-Type: application/json

   {
     "targetApp": "TEACHER"
   }
   ```
3. **Backend Ticket Generation**:
   - Validates that user's role matches `targetApp`.
   - Generates 32 cryptographically secure random bytes formatted as `mvk_sso_<64_hex_chars>`.
   - Stores ticket in thread-safe memory cache with 60s expiration.
   - Returns `{ "code": "mvk_sso_...", "expiresIn": 60, "targetApp": "TEACHER" }`.
4. **Browser Redirect**:
   `portal-web` navigates the browser to `http://localhost:5173/login?code=mvk_sso_...`.
5. **Target App Ticket Exchange**:
   - Target app reads `code` from query string.
   - Immediately executes POST exchange:
     ```http
     POST /api/v1/auth/sso/exchange
     Content-Type: application/json

     {
       "code": "mvk_sso_...",
       "targetApp": "TEACHER"
     }
     ```
   - **Single-Use Enforcement**: Backend atomically removes ticket (`ticketStore.remove(code)`).
   - Validates expiration and target app binding.
   - Issues fresh, independent JWT accessToken and refreshToken.
6. **URL Scrubbing**:
   Target app calls `window.history.replaceState({}, document.title, window.location.pathname)`, scrubbing the code from browser history and URL bar before routing to `/dashboard`.

---

## 6. URL / Route Map & Port Matrix

| Service | Port | Base URL | Primary Role / Purpose |
|---|---|---|---|
| **Spring Boot Business API** | `8080` | `http://127.0.0.1:8080` | Core backend REST API, JWT auth, RBAC, SSO service |
| **FastAPI AI Runtime** | `8000` | `http://127.0.0.1:8000` | YOLOv8 inference, stroke analysis, arithmetic check |
| **PostgreSQL** | `5432` | `127.0.0.1:5432` | Primary relational database |
| **Redis** | `6379` | `127.0.0.1:6379` | Celery broker, token caching, session storage |
| **MinIO Storage** | `9000/9001` | `http://127.0.0.1:9000` | S3 object storage for raw and cropped exercise images |
| **Unified Portal Web** | `5172` | `http://localhost:5172` | Unified public landing, shared login, role router |
| **Teacher Web Portal** | `5173` | `http://localhost:5173` | Classroom management, batch creation, grading review |
| **Admin Web Portal** | `5174` | `http://localhost:5174` | User administration, audit trail, system configuration |
| **Student Mobile / Metro** | `8081` | `http://localhost:8081` | Expo Metro bundler, student mobile app runtime |

---

## 7. Unified Portal Web Implementation (`portal-web/`)

- **Root Location**: `portal-web/`
- **Framework**: React 19, TypeScript 5.9, Vite 8.3, MUI 9.4, React Router 7.
- **Port**: Fixed on `5172` with `strictPort: true`.
- **Key Routes**:
  - `/`: Public landing page with product overview, role cards, and ecosystem links.
  - `/login`: Universal login form with role-based auto-dispatch and dev quick-fill buttons.
  - `/student`: Student landing page explaining mobile-first architecture with QR connection guide.
  - `/teacher`: Teacher handoff dispatch page (requests SSO ticket $\rightarrow$ redirects to 5173).
  - `/admin`: Admin handoff dispatch page (requests SSO ticket $\rightarrow$ redirects to 5174).
  - `/access-denied`: Explains role boundaries when unauthorized cross-access occurs.
  - `/session-expired`: Guidance when auth token expires.
- **Build & Quality**: `npm run build` succeeds cleanly; `npm run lint` yields 0 warnings and 0 errors.

---

## 8. Teacher Web Portal Integration (`teacher-web/`)

- **SSO Exchange Integration**: In `teacher-web/src/pages/LoginPage.tsx`, added `useEffect` monitoring `?code=...`. Calls `POST /api/v1/auth/sso/exchange` with `targetApp: "TEACHER"`, stores tokens in `AuthTokenStore`, scrubs the query param with `window.history.replaceState`, and navigates to `/dashboard`.
- **Fallback Direct Login**: Preserved direct email/password login for offline/direct usage.
- **Ecosystem Navigation**:
  - Topbar user menu includes "Về Cổng chung (Portal)" linking to `http://localhost:5172`.
  - Sidebar drawer includes persistent "Cổng chung (Portal)" button at the bottom.
  - Login page includes "Đăng nhập qua MathVision Kids Portal" button and return link.
- **Build & Quality**: `npm run build` succeeds cleanly; `npm run lint` yields 0 errors.

---

## 9. Admin Web Portal Integration (`admin-web/`)

- **SSO Exchange Integration**: Added `exchangeSsoTicket` in `authService.ts` and `loginWithSsoTicket` in `AuthContext.tsx`. In `admin-web/src/pages/LoginPage.tsx`, automatically detects `?code=...`, executes exchange with `targetApp: "ADMIN"`, scrubs browser URL, and directs to `/dashboard`.
- **Ecosystem Navigation**:
  - Sidebar drawer includes persistent "Cổng chung (Portal)" link at the bottom.
  - Login page includes "Đăng nhập qua MathVision Kids Portal" button and return link.
- **Build & Quality**: `npm run build` succeeds cleanly; `npm run lint` yields 0 warnings and 0 errors.

---

## 10. Student Experience & Mobile Integration

- **Why Mobile-First**: MathVision Kids requires high-resolution camera capture of handwriting on 5mm grid notebooks (vở ô ly), local perspective crop assist, and touch interaction.
- **Student Portal Landing (`http://localhost:5172/student`)**:
  - Clarifies why the official student experience is mobile-first.
  - Displays step-by-step connection guide for Expo Go.
  - Displays QR code and direct links to Metro bundler (`http://localhost:8081`).
  - Confirms backend Spring Boot (8080) and MinIO storage readiness.
- **Mobile App Verification**: Root Expo project passes `npx tsc --noEmit` and `npm run lint` with 0 errors.

---

## 11. Shared Design System & Branding Tokens (`packages/ui-brand/`)

A dedicated shared package was constructed at `packages/ui-brand/`:
- **Tokens Exported**:
  - `BRAND_NAME`: `"MathVision Kids"`
  - `BRAND_TAGLINE_VI`: `"Nền tảng chấm điểm số học và nhận diện chữ viết tay ứng dụng AI"`
  - `BRAND_COLORS`: Curated Indigo (`#4F46E5`), Sky (`#0284C7`), Emerald (`#10B981`), Amber (`#F59E0B`), Slate (`#0F172A`).
  - `ROLE_CONFIGS`: Visual configuration (colors, labels, borders) for `STUDENT`, `TEACHER`, and `ADMIN`.
  - `ECOSYSTEM_URLS`: Authoritative port mapping (5172, 5173, 5174, 8081, 8080).
- **Compilation**: Compiled cleanly with `npx tsc` producing type declarations and ESM bundles.

---

## 12. Shared Components & Visual Consistency

- **`RoleBadge` Component**: Standardized chip displaying Vietnamese role labels (`Học sinh`, `Giáo viên`, `Quản trị viên`), with role-specific color accents and icons.
- **`PortalLayout` Component**: Responsive navigation bar with consistent brand mark, role indicator, and quick links to all ecosystem applications.
- **Consistent Visual Hierarchy**: Consistent typography (Inter/system sans-serif), elevation shadows, border radii (12px-16px), and card styling across all three web frontends.

---

## 13. Access Denied & Edge Cases Handling

- **Access Denied Page (`/access-denied`)**:
  - Triggered when a user logs in with one role (e.g. `STUDENT`) but attempts to navigate to a restricted portal (e.g. `http://localhost:5172/teacher`).
  - Clear Vietnamese explanatory alert explaining role boundaries and data privacy.
  - Direct action buttons to "Về Trang chủ" or "Đăng nhập lại".
- **Target Mismatch Prevention**:
  - If a Teacher SSO ticket is intercepted or replayed to Admin Web, backend rejects exchange with 401 Unauthorized and burns the ticket immediately.
- **Replay Attack Prevention**:
  - Attempting to exchange a ticket twice returns 401 Unauthorized.

---

## 14. Session Management & Token Expiration

- **Token Storage**:
  - `portal-web`: `localStorage` for portal-level authentication and routing.
  - `teacher-web`: `sessionStorage` (tab-scoped) via `AuthTokenStore`.
  - `admin-web`: `localStorage` via `tokenStore`.
- **Session Expiration**:
  - Interceptors in `portal-web`, `teacher-web`, and `admin-web` monitor HTTP 401 responses.
  - If refresh token fails, tokens are cleared and user is redirected to `/session-expired` or `/login`.

---

## 15. Launcher & Developer Experience

Three core operational tools were enhanced:
1. **`scripts/start-all.ps1`**:
   - Starts PostgreSQL, MinIO, Redis in Docker.
   - Starts Spring Boot (8080), FastAPI (8000), Celery Worker.
   - Starts Unified Portal Web (`portal-web` on 5172).
   - Starts Teacher Web (5173) and Admin Web (5174).
   - Probes port 5172 during startup readiness loop.
   - Displays unified banner highlighting `http://localhost:5172` as the main entry.
2. **`scripts/stop-all.ps1`**:
   - Tracks port 5172 in `$PortsToCheck`.
   - Safely cleans up all MathVision node/vite child processes.
3. **`RUN_MATHVISION.bat`**:
   - Added to repository root for one-click startup from Windows Explorer or CMD.
4. **`tools/diagnostics/check_runtime.py`**:
   - Added `check_portal_web()` probing `http://localhost:5172`.
   - Verified that all 10 core components PASS and output is `READY_FOR_DEMO`.

---

## 16. Backend SSO Support & API Endpoints

### 16.1 New Classes Added in `com.mathvisionkids.api.auth.sso`
- `SsoTicket`: Immutable record storing `code`, `userId`, `email`, `role`, `targetApp`, `expiresAt`.
- `SsoTicketRequest`: DTO with `@NotBlank targetApp`.
- `SsoTicketResponse`: DTO with `code`, `expiresIn`, `targetApp`.
- `SsoExchangeRequest`: DTO with `code` and `targetApp`.
- `SsoHandoffService`: Thread-safe in-memory cache, 60s TTL, atomic removal, strict role check.
- `SsoController`: Exposes `POST /api/v1/auth/sso/ticket` and `POST /api/v1/auth/sso/exchange`.

### 16.2 Security & CORS Configuration
- In `SecurityConfig.java`: Allowed `/api/v1/auth/sso/exchange` under `permitAll()`.
- In `application.yml` and `.env`: Added `http://localhost:5172`, `http://127.0.0.1:5172`, `http://localhost:5174`, `http://127.0.0.1:5174` to `CORS_ALLOWED_ORIGINS`.

---

## 17. Security Analysis & Threat Model

| Threat Vector | Mitigation Implemented | Validation Result |
|---|---|---|
| **JWT in URL Query Parameter** | Eliminated completely. Only opaque, random 32-byte ticket codes (`mvk_sso_...`) are passed in URLs. | **PASS** |
| **Ticket Replay / Interception** | Single-use atomic removal from cache (`ticketStore.remove(code)`). | **PASS** (Replay returns 401) |
| **Ticket Expiration** | 60-second TTL enforced by `ticket.isExpired()`. | **PASS** |
| **Target App Spoofing** | Target app must match ticket metadata on exchange (`ticket.targetApp() == targetApp`). | **PASS** (Mismatch returns 401) |
| **Role Escalation via Ticket** | Ticket creation strictly requires authenticated user role to equal target role. Student cannot create Teacher or Admin tickets. | **PASS** (Student request returns 403) |
| **Cross-Origin Leakage** | CORS origins locked to explicit localhost/127.0.0.1 ports; credential sharing restricted. | **PASS** |

---

## 18. End-to-End User Journeys

### 18.1 Anonymous Visitor Journey
1. Navigates to `http://localhost:5172`.
2. Views product branding, feature overview, and ecosystem architecture diagram.
3. Clicks "Đăng nhập ngay" $\rightarrow$ redirected to `/login`.

### 18.2 Student Journey
1. Logs into `http://localhost:5172/login` with `an.student@mathvision.local`.
2. Backend authenticates role `STUDENT`.
3. Portal automatically routes student to `http://localhost:5172/student`.
4. Student scans QR code with Expo Go to launch mobile camera experience.

### 18.3 Teacher Journey
1. Logs into `http://localhost:5172/login` with `lan.teacher@mathvision.local`.
2. Backend authenticates role `TEACHER`.
3. Portal requests SSO ticket for `TEACHER` $\rightarrow$ receives code `mvk_sso_...`.
4. Browser redirects to `http://localhost:5173/login?code=mvk_sso_...`.
5. Teacher Web exchanges ticket for local session tokens, scrubs URL, and displays Dashboard (`/dashboard`).

### 18.4 Admin Journey
1. Logs into `http://localhost:5172/login` with `admin.demo@mathvision.local`.
2. Backend authenticates role `ADMIN`.
3. Portal requests SSO ticket for `ADMIN` $\rightarrow$ receives code `mvk_sso_...`.
4. Browser redirects to `http://localhost:5174/login?code=mvk_sso_...`.
5. Admin Web exchanges ticket for local session tokens, scrubs URL, and displays Dashboard (`/dashboard`).

### 18.5 Unauthorized Cross-Access Journey
1. Authenticated Student attempts to navigate to `http://localhost:5172/teacher`.
2. Portal detects role mismatch $\rightarrow$ redirects to `/access-denied?target=Cổng Giáo viên&current=STUDENT`.
3. Student sees clear denial message and cannot proceed.

---

## 19. Test Strategy & Execution Results

### 19.1 Automated Test Execution Summary
1. **Spring Boot Backend Test Suite**:
   - Test Command: `./gradlew.bat test`
   - Result: **117/117 PASSED** (including 6 dedicated `SsoHandoffServiceTest` cases).
2. **Ecosystem Portal E2E Regression Suite** (`scratch/test_portal_ecosystem_e2e.py`):
   - Frontend availability (5172, 5173, 5174): **3/3 PASS**
   - Unauthenticated 401 protection: **3/3 PASS**
   - Student authentication & 403 boundaries: **5/5 PASS**
   - Teacher authentication & SSO handoff & exchange: **8/8 PASS**
   - Admin authentication & SSO handoff & exchange: **7/7 PASS**
   - **Total: 26/26 PASSED (100%)**.
3. **Core Regression Suite** (`scratch/test_system_audit_auth_and_boundaries.py`):
   - Full-stack authorization, batch upload boundaries, and arithmetic pipeline terminal verification: **ALL PASSED**.
4. **TypeScript & Static Analysis**:
   - `portal-web`: `tsc -b && vite build` (0 errors), `oxlint` (0 warnings, 0 errors).
   - `teacher-web`: `tsc -b && vite build` (0 errors), `oxlint` (0 errors).
   - `admin-web`: `tsc -b && vite build` (0 errors), `oxlint` (0 warnings, 0 errors).
   - `mathvisionkid` (mobile): `npx tsc --noEmit` (0 errors), `expo lint` (0 errors).

---

## 20. Cross-Browser & Responsiveness Audit

- **Desktop (1920x1080 & 1440x900)**: Clean responsive layouts on Portal, Teacher Web, and Admin Web with sidebars and fixed topbars.
- **Tablet / Mobile (768px & 375px)**:
  - Portal adapts gracefully: cards stack vertically, navigation bar collapses cleanly.
  - Student landing page prominently shows QR code and step-by-step instructions.

---

## 21. Performance & Bundle Size Impact

- `portal-web`: Total production bundle size is 618.8 kB (gzip 195.9 kB), build time 1.52s.
- `teacher-web`: Production bundle size 726 kB (gzip 224.6 kB), build time 3.82s.
- `admin-web`: Production bundle size 712 kB (gzip 218.8 kB), build time 3.33s.
- Total static asset overhead added to ecosystem: < 2.5 MB.

---

## 22. Physical Device & Network Considerations

- In local testing, clients access frontends via `localhost` or `127.0.0.1`.
- For physical mobile devices running Expo Go, Spring Boot must be accessed via LAN IP (e.g. `192.168.1.x:8080`).
- The `portal-web` Student page guides users to connect their mobile device to the same Wi-Fi network as the developer workstation.

---

## 23. Known Limitations & Technical Debt

1. **In-Memory SSO Ticket Cache**:
   - SSO tickets are stored in-memory within Spring Boot (`ConcurrentHashMap`). In a clustered multi-instance production deployment, this should be backed by Redis (`StringRedisTemplate`) with native TTL. For local single-node development, the in-memory cache is thread-safe, ultra-low latency, and fully adequate.
2. **Target Ports in Local Dev**:
   - The SSO redirection URLs (`http://localhost:5173`, `http://localhost:5174`) are hardcoded to standard Vite local development ports in the frontend pages. In production, these should be configurable via environment variables (`VITE_TEACHER_PORTAL_URL`, `VITE_ADMIN_PORTAL_URL`).

---

## 24. Operational & Demo Playbook

### Step 1: Start the Entire Ecosystem
Double click `RUN_MATHVISION.bat` at the repository root, or run:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1
```

### Step 2: Open Unified Portal
Open a browser and navigate to:
```
http://localhost:5172
```

### Step 3: Test Role-Based Flows
1. Click **Đăng nhập**.
2. Click **Điền tài khoản Giáo viên** (or use `lan.teacher@mathvision.local` / `MathVision123!`) $\rightarrow$ Observe automatic handoff to Teacher Web (`http://localhost:5173/dashboard`).
3. Return to Portal (`http://localhost:5172/login`), click **Điền tài khoản Admin** $\rightarrow$ Observe automatic handoff to Admin Web (`http://localhost:5174/dashboard`).
4. Log in as Student (`an.student@mathvision.local` / `MathVision123!`) $\rightarrow$ Observe routing to Student Connection Guide (`http://localhost:5172/student`).

### Step 4: Stop the Ecosystem
```powershell
scripts\stop-all.bat
```

---

## 25. Files Created, Modified & Deleted

### Files Created:
1. `services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoTicket.java`
2. `services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoTicketRequest.java`
3. `services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoTicketResponse.java`
4. `services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoExchangeRequest.java`
5. `services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoHandoffService.java`
6. `services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoController.java`
7. `services/business-api/src/test/java/com/mathvisionkids/api/auth/sso/SsoHandoffServiceTest.java`
8. `packages/ui-brand/package.json`
9. `packages/ui-brand/tsconfig.json`
10. `packages/ui-brand/src/index.ts`
11. `portal-web/package.json`
12. `portal-web/tsconfig.json`
13. `portal-web/tsconfig.app.json`
14. `portal-web/tsconfig.node.json`
15. `portal-web/vite.config.ts`
16. `portal-web/index.html`
17. `portal-web/public/logo.svg`
18. `portal-web/src/main.tsx`
19. `portal-web/src/App.tsx`
20. `portal-web/src/theme.ts`
21. `portal-web/src/services/apiClient.ts`
22. `portal-web/src/services/authService.ts`
23. `portal-web/src/components/common/RoleBadge.tsx`
24. `portal-web/src/components/layout/PortalLayout.tsx`
25. `portal-web/src/pages/LandingPage.tsx`
26. `portal-web/src/pages/LoginPage.tsx`
27. `portal-web/src/pages/StudentLandingPage.tsx`
28. `portal-web/src/pages/TeacherEntryPage.tsx`
29. `portal-web/src/pages/AdminEntryPage.tsx`
30. `portal-web/src/pages/AccessDeniedPage.tsx`
31. `portal-web/src/pages/SessionExpiredPage.tsx`
32. `RUN_MATHVISION.bat`
33. `scratch/test_portal_ecosystem_e2e.py`
34. `report/ecosystem_portal_1_unified_entry_role_routing.md`

### Files Modified:
1. `services/business-api/src/main/java/com/mathvisionkids/api/config/SecurityConfig.java` (allowed `/api/v1/auth/sso/exchange`)
2. `services/business-api/src/main/resources/application.yml` (added 5172, 5174 to CORS)
3. `.env` (added 5172, 5174 to CORS_ALLOWED_ORIGINS)
4. `teacher-web/src/pages/LoginPage.tsx` (added SSO ticket exchange and portal link)
5. `teacher-web/src/components/layout/Topbar.tsx` (added Portal menu item)
6. `teacher-web/src/components/layout/Sidebar.tsx` (added Portal navigation link)
7. `admin-web/src/services/api/authService.ts` (added exchangeSsoTicket)
8. `admin-web/src/context/AuthContext.tsx` (added loginWithSsoTicket)
9. `admin-web/src/pages/LoginPage.tsx` (added SSO exchange and portal link)
10. `admin-web/src/components/layout/AdminSidebar.tsx` (added Portal navigation link)
11. `scripts/start-all.ps1` (added portal-web launch, 5172 probe, and summary banner)
12. `scripts/stop-all.ps1` (added port 5172 and portal-web to termination filter)
13. `tools/diagnostics/check_runtime.py` (added check_portal_web and READY_FOR_DEMO verification)

### Files Deleted:
None.

---

## 26. Traceability Matrix against Owner Goals

| Owner Requirement | Implementation Component | Verification Evidence | Status |
|---|---|---|---|
| One unified entry point for MathVision Kids | `portal-web` running on port 5172 | `http://localhost:5172` returns 200; diagnostic PASS | **SATISFIED** |
| Server-verified role-based routing | `portal-web` login dispatch + Spring Boot JWT validation | Student $\rightarrow$ `/student`, Teacher $\rightarrow$ 5173, Admin $\rightarrow$ 5174 | **SATISFIED** |
| Secure handoff without tokens in URLs | Backend SSO Ticket subsystem (`POST /api/v1/auth/sso/ticket`, `/exchange`) | E2E test verified opaque random code; zero JWT in URL | **SATISFIED** |
| Preserve Student Mobile as mobile-first Expo app | Mobile codebase untouched, clear guide on Portal | `npx tsc --noEmit` and `expo lint` PASS (0 errors) | **SATISFIED** |
| Preserve Teacher Web workspace | `teacher-web` on 5173 receives SSO ticket exchange | `npm run build` PASS, SSO exchange 200, dashboard load | **SATISFIED** |
| Preserve Admin Web console | `admin-web` on 5174 receives SSO ticket exchange | `npm run build` PASS, SSO exchange 200, dashboard load | **SATISFIED** |
| Consistent branding and return links | `packages/ui-brand`, Topbar/Sidebar portal links | Unified colors, typography, RoleBadge, Portal return button | **SATISFIED** |
| Unified startup, shutdown, and diagnostic | `start-all.ps1`, `stop-all.ps1`, `RUN_MATHVISION.bat`, `check_runtime.py` | `check_runtime.py` outputs `READY_FOR_DEMO` (exit code 0) | **SATISFIED** |

---

## 27. Final Sign-Off & Capability Certification

### 27.1 Authority Certification
This document certifies that milestone **ECOSYSTEM.PORTAL.1** has achieved complete integration across all MathVision Kids frontends and backends:
- Unified entry point established at `http://localhost:5172`.
- Server-verified role routing active.
- Secure, single-use SSO handoff functioning with zero JWT exposure in URLs.
- All 117 backend unit tests, 26 E2E integration tests, and full runtime regression suites pass.
- The platform is certified **READY_FOR_DEMO**.

---
*Report generated and approved autonomously by pair programming agent under strict verification gate.*
