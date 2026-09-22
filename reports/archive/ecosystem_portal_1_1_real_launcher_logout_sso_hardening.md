# ECOSYSTEM.PORTAL.1.1 — Real One-Click Student Launch, Unified Logout & SSO Credential Hardening

**Task Reference:** ECOSYSTEM.PORTAL.1.1  
**Project:** MathVision Kids  
**Mode:** Targeted Ecosystem Closure  
**Timestamp:** 2026-09-12T20:15:30+07:00  
**Status:** PASS  

---

## 1. Executive Summary

ECOSYSTEM.PORTAL.1 established the unified web portal, role-based routing, Teacher/Admin SSO handoff, and unified branding across MathVision Kids. Independent review identified four remaining product-truth and security gaps:
1. **Student Metro Cold-Start Absence:** `RUN_MATHVISION.bat` previously started core services and web frontends, but did not cold-start the Student Expo/Metro runtime, yet labeled the environment `READY_FOR_DEMO`.
2. **Student Portal Fake Localhost QR/Link:** The Portal Student landing page presented a static SVG QR code encoding `http://localhost:8081`, which is completely non-functional on physical mobile phones.
3. **SSO Code Transport Exposure:** The 60-second one-time SSO code was transferred in the URL query string (`/login?code=...`), creating bearer credential exposure in browser history and HTTP referrers.
4. **Unified Logout Deficit:** Logging out of Teacher Web or Admin Web left the Portal tab silently authenticated in `localStorage`, breaking the single-ecosystem mental model.

**ECOSYSTEM.PORTAL.1.1 has closed 100% of these gaps:**
- `RUN_MATHVISION.bat` now executes a true one-click owner cold start: starts the core stack in the background (0 service console windows), auto-launches Student Metro in LAN mode (`npm run start:device`) inside exactly 1 visible terminal titled `MathVision Kids - Student Mobile (Metro LAN)`, displays the real Expo LAN QR code, verifies full ecosystem diagnostics (`READY_FOR_FULL_DEMO`), and launches `http://localhost:5172` in the default browser.
- The fake localhost QR SVG and `http://localhost:8081` hyperlinks were completely removed from the Portal Student landing page. The page now directs mobile users to scan the real Expo LAN QR displayed in the visible Metro terminal over local Wi-Fi.
- SSO handoff transport was hardened to the URL fragment (`/login#sso=...`). Target apps (`teacher-web` and `admin-web`) immediately scrub the hash from the browser history entry via `window.history.replaceState` before exchanging the code via `POST /api/v1/auth/sso/exchange`. SSO ticket cache hygiene was implemented via `@Scheduled(fixedRate = 60000)` bounded pruning and eager eviction.
- Unified logout was implemented: target apps call backend `/auth/logout`, clear local tokens, and redirect to `http://localhost:5172/logout?source=teacher` or `?source=admin`. Portal `/logout` explicitly revokes backend sessions and clears Portal `localStorage`, preventing silent lingering authentication.

---

## 2. Repository State

```bash
git rev-parse --show-toplevel: E:/MathVisionKid
git branch --show-current:     main
git log -5 --oneline:
112bbb5 feat(ocr-pilot): complete multi-line handwriting OCR, privacy hardening, and notebook line robustness
712f806 feat(ocr-pilot): complete handwriting test mode, feedback loop, and mobile image pipeline
dc9a9de feat(ocr): integrate OCR bridge, arithmetic line dataset handoff, and test cleanup
f89c43f feat: complete OCR artifact provenance reconciliation and refreeze (INT.1.1, INT.1.1.1, INT.1.1.2)
b87a028 feat: complete Teacher UI refreeze, backend closure and handwritten OCR staging (UI.2, UI.2.2, INT.1)
```

- **Model Training Commands Executed:** 0
- **New Checkpoints Generated:** NONE
- **Git Commits Executed:** 0
- **Git Pushes Executed:** 0

---

## 3. Pre-Fix Cold-Start Truth

Before code changes, the local environment was stopped cleanly using `scripts\stop-all.bat` and all ports verified released. `RUN_MATHVISION.bat` was executed from a cold state.

**Pre-Fix Audit Results:**
- `CORE_STACK_STARTED`: **YES** (Postgres, MinIO, Redis, Spring 8080, FastAPI 8000, Celery, Portal 5172, Teacher 5173, Admin 5174 started)
- `PORTAL_STARTED`: **YES**
- `TEACHER_STARTED`: **YES**
- `ADMIN_STARTED`: **YES**
- `STUDENT_METRO_STARTED`: **NO** (Port 8081 was closed; no Metro process was spawned)
- `METRO_QR_AVAILABLE`: **NO** (No terminal window or QR code was produced)

**Conclusion:** The pre-fix launcher only started the core web stack and falsely claimed the complete ecosystem was ready for demo without student capabilities.

---

## 4. One-Click Launcher Architecture

The launcher architecture was separated into two clear tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RUN_MATHVISION.bat                              │
│                    (Owner One-Click Demo Entry)                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       ▼                                                         ▼
[1/3] Core Stack Launch                                [2/3] Student Metro
scripts\start-all.bat                                  scripts\start-student-metro.ps1
- Docker infrastructure (5432, 9000, 6379)             - Starts Metro in LAN mode
- Spring Boot (8080, hidden)                           - npm run start:device
- FastAPI (8000 on 127.0.0.1, hidden)                  - Dedicated visible window:
- Celery Worker (hidden)                                 "MathVision Kids - Student Mobile
- Portal Web (5172, hidden)                               (Metro LAN)"
- Teacher Web (5173, hidden)                           - Displays authentic Expo LAN QR
- Admin Web (5174, hidden)                             - Waits for port 8081 readiness
- Outputs READY_FOR_CORE_DEMO                          - Tracks PID in student-metro.pid
       │                                                         │
       └────────────────────────────┬────────────────────────────┘
                                    ▼
                       [3/3] Full Stack Diagnostics
                       tools\diagnostics\check_runtime.py
                       - Evaluates all 11 components
                       - Reports READY_FOR_FULL_DEMO
                       - Launches Portal (http://localhost:5172) in default browser
```

**Terminal Window Cleanliness:**
- Background services (Spring, FastAPI, Celery, Portal, Teacher, Admin): **0 console windows**.
- Student Metro Bundler: **Exactly 1 visible console window** containing the live Expo LAN QR.

---

## 5. Student Metro Auto-Start

- **Script:** [scripts/start-student-metro.ps1](file:///e:/MathVisionKid/scripts/start-student-metro.ps1)
- **Command:** `cmd.exe /c "title MathVision Kids - Student Mobile (Metro LAN) && npm run start:device"`
- **Native Project Script:** Calls root `package.json` script `"start:device": "expo start --lan"`.
- **PID Tracking:** Written to `runtime\pids\student-metro.pid` for safe, deterministic teardown.
- **Port Probe:** Polls TCP port 8081 up to 25s until accepted.
- **Stop Integration:** `scripts\stop-all.ps1` terminates the process tree (`taskkill /PID <pid> /T /F`) and matches console window title `MathVision Kids - Student Mobile` to guarantee no orphaned Node/Metro processes linger.

---

## 6. Student QR / LAN Truth

### Audit of Previous Code
In `portal-web/src/pages/StudentLandingPage.tsx`:
- Contained a hardcoded SVG rendering a static QR matrix.
- Encoded text was: `http://localhost:8081/`.
- Included direct hyperlinks to `http://localhost:8081`.

**Root Flaw:** On a physical smartphone scanning a QR code, `localhost` resolves to the phone's loopback interface, not the developer's laptop. Directing a physical phone to `http://localhost:8081` is completely inoperable.

### Fix Implemented
1. Removed the fake QR SVG component.
2. Removed all `localhost:8081` direct phone hyperlinks.
3. Rendered clear, honest guidance in Vietnamese matching product branding:
   - *"Ứng dụng học sinh đã được khởi động bằng Expo LAN."*
   - *"1. Kết nối điện thoại và laptop cùng mạng Wi-Fi."*
   - *"2. Mở ứng dụng Expo Go trên điện thoại."*
   - *"3. Quét mã QR hiển thị trong cửa sổ terminal 'MathVision Kids - Student Mobile (Metro LAN)' vừa được mở tự động bởi RUN_MATHVISION.bat."*
4. Maintained guidance regarding Spring Boot LAN accessibility for grading endpoints.

---

## 7. Runtime Diagnostics

[tools/diagnostics/check_runtime.py](file:///e:/MathVisionKid/tools/diagnostics/check_runtime.py) was enhanced to probe and distinguish Core Stack vs Full Demo status:

### Monitored Components (11 Total)
1. Docker Daemon (CLI/Socket)
2. PostgreSQL (5432 + `pg_isready`)
3. MinIO (`http://127.0.0.1:9000/minio/health/live`)
4. Redis (`127.0.0.1:6379` PING -> PONG)
5. Spring Boot (`http://127.0.0.1:8080/actuator/health` -> `status: "UP"`)
6. FastAPI AI Runtime (`http://127.0.0.1:8000/ready` -> `status: "ready"`)
7. Celery Worker (Celery control ping via venv python)
8. Unified Portal Web (`http://localhost:5172`)
9. Teacher Web (`http://localhost:5173`)
10. Admin Web (`http://localhost:5174`)
11. Student Metro Bundler (`http://localhost:8081/status` -> `"packager-status:running"`)

### Status Classification Rules
- If components 1–10 PASS and Student Metro is absent: **`READY_FOR_CORE_DEMO`**
- If components 1–10 PASS and Student Metro is running: **`READY_FOR_FULL_DEMO`**
- If any component 1–10 fails: **`NOT_READY`** (exit code 1)
- The ambiguous string `READY_FOR_DEMO` is **never produced**.

---

## 8. SSO Fragment Handoff

### Transport Security Hardening
Previously:
```
Portal -> http://localhost:5173/login?code=mvk_sso_...
```
Now:
```
Portal -> http://localhost:5173/login#sso=mvk_sso_...
Portal -> http://localhost:5174/login#sso=mvk_sso_...
```

### Technical Rationale
- **HTTP Transport:** URL fragments (`#...`) are never transmitted in HTTP request lines across the wire.
- **Referer Privacy:** Browsers strip fragments from the `Referer` header on outbound cross-origin navigation.
- **Client-Side Extraction:** The target Single Page Application reads `window.location.hash`, extracts the parameter `sso`, and immediately scrubs the URL.

### Target App Scrubbing Implementation
Both `teacher-web` ([LoginPage.tsx](file:///e:/MathVisionKid/teacher-web/src/pages/LoginPage.tsx)) and `admin-web` ([LoginPage.tsx](file:///e:/MathVisionKid/admin-web/src/pages/LoginPage.tsx)):
```typescript
const hash = window.location.hash;
if (hash.includes('sso=')) {
  const hashParams = new URLSearchParams(hash.replace(/^#/, ''));
  const ssoCode = hashParams.get('sso');
  if (ssoCode) {
    // 1. Immediately scrub URL from browser history
    window.history.replaceState(null, '', window.location.pathname);
    // 2. Exchange opaque one-time code via POST body
    exchangeSso(ssoCode);
  }
}
```

### Precise Credential Claim
- **Zero JWT, access tokens, or refresh tokens in URL.**
- An opaque, cryptographically random 32-byte (64 hex characters) code prefixed with `mvk_sso_` with 60-second TTL is transmitted solely in the client URL fragment and scrubbed before view render.

---

## 9. Ticket Cache Hygiene

- **Backend Component:** [SsoHandoffService.java](file:///e:/MathVisionKid/services/business-api/src/main/java/com/mathvisionkids/api/auth/sso/SsoHandoffService.java)
- **Bounded Cleanup:**
  1. `@EnableScheduling` activated on `BusinessApiApplication`.
  2. `@Scheduled(fixedRate = 60000)` invokes `cleanupExpiredTickets()`.
  3. Eager inline eviction: `exchangeHandoffTicket()` and `createHandoffTicket()` sweep expired tickets on demand.
  4. Exposed `getActiveTicketCount()` for health inspection.
- **Unit Test Coverage:** [SsoHandoffServiceTest.java](file:///e:/MathVisionKid/services/business-api/src/test/java/com/mathvisionkids/api/auth/sso/SsoHandoffServiceTest.java) executes 8 tests verifying ticket creation, successful exchange, single-use burn, target app mismatch rejection, expired ticket eviction, and role enforcement.

---

## 10. Unified Logout

### Ecosystem Flow
```
Teacher Web / Admin Web (User clicks "Đăng xuất")
   │
   ├─► 1. POST /api/v1/auth/logout (Revokes backend refresh tokens)
   ├─► 2. Clears localStorage auth tokens in target app
   └─► 3. Redirects to Portal: http://localhost:5172/logout?source=teacher
           │
           ▼
     Portal Web (/logout Route)
     [LogoutPage.tsx]
     ├─► 1. POST /api/v1/auth/logout (Revokes Portal backend session)
     ├─► 2. tokenStore.clear() (Destroys Portal localStorage token & user)
     └─► 3. Displays logout confirmation card with "Đăng nhập lại" action
```

### Audit Finding & Truth
The Portal no longer remains silently authenticated. If a user logs out in Teacher Web or Admin Web, navigating back to Portal shows the unauthenticated login screen. Tokens are never passed in the logout query string; only the harmless string `source=teacher` or `source=admin` is passed for contextual messaging.

---

## 11. Direct URL Behavior

| Scenario | Direct URL | Observed Behavior | Status |
| :--- | :--- | :--- | :--- |
| Teacher Web with no session | `http://localhost:5173/dashboard` | Redirects to `http://localhost:5173/login` | PASS |
| Admin Web with no session | `http://localhost:5174/dashboard` | Redirects to `http://localhost:5174/login` | PASS |
| Teacher Web with expired/used `#sso=` | `http://localhost:5173/login#sso=used_code` | Fragment scrubbed immediately; backend returns 401; user sees error card with link back to Portal | PASS |
| Admin Web with expired/used `#sso=` | `http://localhost:5174/login#sso=used_code` | Fragment scrubbed immediately; backend returns 401; user sees error card with link back to Portal | PASS |
| Portal Web unauthenticated | `http://localhost:5172/student` | Redirects to `http://localhost:5172/login` | PASS |

---

## 12. Role/RBAC Regression

Verified via automated E2E suite [scratch/test_ecosystem_portal_1_1_e2e.py](file:///e:/MathVisionKid/scratch/test_ecosystem_portal_1_1_e2e.py):

| Actor | Action | Endpoint | Expected | Actual |
| :--- | :--- | :--- | :--- | :--- |
| Student | Access Teacher Dashboard | `GET /api/v1/teacher/dashboard` | 403 Forbidden | 403 Forbidden |
| Student | Access Admin Dashboard | `GET /api/v1/admin/dashboard` | 403 Forbidden | 403 Forbidden |
| Student | Mint Teacher SSO Ticket | `POST /api/v1/auth/sso/ticket` (`TEACHER`) | 403 Forbidden | 403 Forbidden |
| Student | Mint Admin SSO Ticket | `POST /api/v1/auth/sso/ticket` (`ADMIN`) | 403 Forbidden | 403 Forbidden |
| Teacher | Access Admin Dashboard | `GET /api/v1/admin/dashboard` | 403 Forbidden | 403 Forbidden |
| Teacher | Mint Admin SSO Ticket | `POST /api/v1/auth/sso/ticket` (`ADMIN`) | 403 Forbidden | 403 Forbidden |
| Teacher | Mint Teacher SSO Ticket | `POST /api/v1/auth/sso/ticket` (`TEACHER`) | 200 OK | 200 OK |
| Admin | Mint Admin SSO Ticket | `POST /api/v1/auth/sso/ticket` (`ADMIN`) | 200 OK | 200 OK |

---

## 13. URL Credential Leak Test

- **JWT in URL:** **ABSENT** (0 occurrences in URL search or hash)
- **Refresh Token in URL:** **ABSENT**
- **Access Token in URL:** **ABSENT**
- **One-time SSO Code:** **FRAGMENT ONLY** (`#sso=mvk_sso_...`)
- **Browser History Entry Post-Exchange:**
  - `window.location.href`: `http://localhost:5173/login` (Fragment removed)
  - Current browser history state replaced via `history.replaceState` before rendering protected views.

---

## 14. Cold-Start Full Demo Test

Executed clean cold start:
1. `scripts\stop-all.bat` ran; ports 5172, 5173, 5174, 8080, 8000, 8081 verified closed.
2. Ran ONLY `RUN_MATHVISION.bat`. Zero additional manual commands.

**Observed Console Output:**
```
============================================================
 MathVision Kids -- Complete Local Ecosystem Launcher
============================================================
[1/3] Starting Core Stack Services...
...
[6/6] Running system diagnostics...
Overall ............... READY_FOR_CORE_DEMO

[2/3] Starting Student Mobile Metro Bundler (LAN Mode)...
  Launching Student Metro in visible LAN terminal...
  Student Metro launched (PID: 36584, title: 'MathVision Kids - Student Mobile (Metro LAN)')
  Waiting for Metro Bundler to accept connections on port 8081...
  Student Metro Bundler is READY on port 8081 (LAN mode).

[3/3] Verifying Complete Ecosystem Diagnostics...
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
Unified Portal Web ..... PASS
Teacher Web ............ PASS
Admin Web .............. PASS
Student Metro .......... PASS

AI Mode ............... OCR_COLLECTION
Primary Model ......... MathVision-Kids-Detection
Model Version ......... 1.0.0
Model Artifact ........ LOADED

Overall ............... READY_FOR_FULL_DEMO
============================================
Launching Unified Portal Web in default browser...
```

- Portal 5172: **UP**
- Teacher 5173: **UP**
- Admin 5174: **UP**
- Spring 8080: **UP**
- FastAPI 8000: **UP (Bound to 127.0.0.1 loopback only)**
- Postgres 5432: **UP**
- Redis 6379: **UP**
- MinIO 9000/9001: **UP**
- Celery Worker: **UP**
- Student Metro 8081: **UP**
- Real Expo LAN QR: **AVAILABLE IN DEDICATED METRO WINDOW**

---

## 15. Stop-All Safety Test

Executed `scripts\stop-all.bat`:
```
Stopping admin-web (PID: 26364)...
Stopping celery (PID: 32328)...
Stopping fastapi (PID: 31808)...
Stopping portal-web (PID: 36780)...
Stopping spring (PID: 31088)...
Stopping student-metro (PID: 36584)...
Stopping teacher-web (PID: 31740)...
Stopping Docker Compose infrastructure...
All MathVision Kids local services stopped.
```

- All 6 project ports (5172, 5173, 5174, 8080, 8000, 8081) released.
- Unrelated developer and browser processes remained untouched.

---

## 16. Portal Build/Lint

- `npm run lint` (`oxlint`): **0 warnings, 0 errors** (16 files scanned)
- `npm run build` (`tsc -b && vite build`): **PASS** (Generated `dist/` with 0 TypeScript/bundler errors)

---

## 17. Teacher Build/Lint

- `npm run lint` (`oxlint`): **0 errors** (5 warnings in pre-existing legacy modal canvas code, 0 blockers)
- `npm run build` (`tsc -b && vite build`): **PASS** (Generated `dist/` with 0 TypeScript/bundler errors)

---

## 18. Admin Build/Lint

- `npm run lint` (`oxlint`): **0 warnings, 0 errors** (26 files scanned)
- `npm run build` (`tsc -b && vite build`): **PASS** (Generated `dist/` with 0 TypeScript/bundler errors)

---

## 19. Student Regression

- `npx tsc --noEmit`: **PASS** (0 errors)
- `npm run lint` (`expo lint`): **PASS** (0 errors)
- `npx expo-doctor`: **WARN** (20/21 checks passed; 1 check noted 17 out-of-date patch dependencies, consistent with SDK 57 lock)

---

## 20. Spring Tests

- Command: `services/business-api/gradlew.bat test`
- **Result:** **119/119 passed** (0 failures, 0 skipped, 0 errors)
- Including 8 new/updated unit tests in `SsoHandoffServiceTest`.

---

## 21. Files Modified

| File | Type | Purpose |
| :--- | :--- | :--- |
| `RUN_MATHVISION.bat` | Modified | Added Student Metro auto-start, full diagnostics check, browser launch |
| `scripts/start-student-metro.ps1` | New | PowerShell helper to launch Metro LAN in visible window with PID tracking |
| `scripts/start-all.ps1` | Modified | Updated completion banner to `READY_FOR_CORE_DEMO` without ambiguity |
| `scripts/stop-all.ps1` | Modified | Added port 8081 check, Student Metro process title matching, safe termination |
| `tools/diagnostics/check_runtime.py` | Modified | Added Student Metro 8081 probe, reports `READY_FOR_FULL_DEMO` vs `CORE_DEMO` |
| `portal-web/src/pages/StudentLandingPage.tsx` | Modified | Removed fake localhost QR and links; added real Expo LAN instructions |
| `portal-web/src/pages/TeacherEntryPage.tsx` | Modified | Changed SSO handoff URL from query param to URL fragment `#sso=` |
| `portal-web/src/pages/AdminEntryPage.tsx` | Modified | Changed SSO handoff URL from query param to URL fragment `#sso=` |
| `portal-web/src/pages/LogoutPage.tsx` | New | Unified Portal `/logout` page: revokes session, clears `localStorage` |
| `portal-web/src/App.tsx` | Modified | Registered `/logout` route in React Router |
| `portal-web/src/components/layout/PortalLayout.tsx` | Modified | Updated navigation logout action to route to `/logout` |
| `teacher-web/src/pages/LoginPage.tsx` | Modified | Extracts `#sso=` from URL fragment, scrubs via `replaceState`, exchanges code |
| `teacher-web/src/components/layout/Topbar.tsx` | Modified | Logout redirects to `http://localhost:5172/logout?source=teacher` |
| `admin-web/src/pages/LoginPage.tsx` | Modified | Extracts `#sso=` from URL fragment, scrubs via `replaceState`, exchanges code |
| `admin-web/src/components/layout/AdminSidebar.tsx` | Modified | Logout redirects to `http://localhost:5172/logout?source=admin` |
| `services/business-api/.../BusinessApiApplication.java` | Modified | Added `@EnableScheduling` |
| `services/business-api/.../SsoHandoffService.java` | Modified | Added `@Scheduled` cleanup, eager cache eviction, active ticket count |
| `services/business-api/.../SsoHandoffServiceTest.java` | Modified | Extended unit tests for cache hygiene and expired ticket eviction |
| `scratch/test_ecosystem_portal_1_1_e2e.py` | New | Comprehensive automated verification suite (24 passing assertions) |

---

## 22. Manual/Physical Requirements

1. **Wi-Fi Connectivity:** The physical mobile device running Expo Go must be on the same Wi-Fi subnet as the laptop running `RUN_MATHVISION.bat`.
2. **Access Point Isolation:** The Wi-Fi router must not have client AP isolation enabled.
3. **Expo Go Application:** The physical device must have the Expo Go app installed from Google Play or App Store.
4. **Scanning:** The user scans the QR code directly from the `MathVision Kids - Student Mobile (Metro LAN)` terminal window.

---

## 23. Known Limitations

1. **Local Development Scope:** All configurations target local development environments (ports 5172, 5173, 5174, 8080, 8000, 8081). No cloud hosting or production ingress configurations are included in this phase.
2. **Physical Device Firewalls:** If Windows Defender Firewall blocks incoming connections to Node.js/Metro, the user must allow Node.js through private network firewall rules for Expo Go to fetch the JavaScript bundle.

---

## 24. Final Verdict

**ECOSYSTEM.PORTAL.1.1: PASS**

All four audit gaps have been definitively closed, verified by cold-start execution, unit testing, linting, production builds, and full automated regression suites.
