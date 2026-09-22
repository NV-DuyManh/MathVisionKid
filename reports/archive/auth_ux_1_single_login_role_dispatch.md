# AUTH.UX.1 — Single Login, Automatic Role Dispatch & Portal UX Simplification

**Task Reference:** AUTH.UX.1  
**Project:** MathVision Kids  
**Mode:** Targeted UX Correction  
**Design Intelligence:** Applied `/ui-ux-pro-max` design system (soft educational style, high-contrast accessible typography, zero technical jargon)  
**Timestamp:** 2026-09-12T20:57:00+07:00  
**Status:** PASS  

---

## 1. Executive Summary

In previous iterations, the unified web portal presented multiple role-picker cards, role navigation tabs ("Học sinh", "Giáo viên", "Quản trị"), and separate login buttons. For elementary school users, teachers, and parents, requiring the user to choose their portal before authentication was an overdesigned, non-intuitive interaction.

**AUTH.UX.1 has simplified the entire ecosystem login to a consumer-grade experience:**
1. **Single Unified Login Form:** One clean login form with Email, Password (with interactive show/hide toggle), and a single [Đăng nhập] button. Zero role selectors, zero tabs, zero pre-auth role questions.
2. **Automatic Role Dispatch by Backend Authority:** The Spring Boot backend authenticates credentials and returns the verified role (`STUDENT`, `TEACHER`, `ADMIN`). The frontend immediately and seamlessly dispatches the user to their designated workspace without asking further questions.
3. **Public Landing Simplification:** Stripped all 3 role portal cards, "Vào cổng", and "Vào khu vực" buttons from the public homepage. Replaced with an elegant educational hero and prominent [Đăng nhập] primary CTA.
4. **Header Navigation Cleanup:** Removed pre-login role navigation tabs ("Học sinh | Giáo viên | Quản trị") from the public header.
5. **Teacher & Admin Direct Login Isolation:** Unauthenticated direct visits to `http://localhost:5173/login` or `http://localhost:5174/login` automatically bounce to `http://localhost:5172/login`. Internal fallback login is strictly reserved for developer/emergency modes (`?fallback=true`).
6. **Student Mobile Untouched:** Verified `git diff -- src app.json package.json` remains exactly 0. The native React Native/Expo app remains 100% preserved.
7. **Zero Developer Term Leaks:** Verified 0 occurrences of Expo, Metro, LAN, localhost, ports, or backend tech terms across normal product pages.

---

## 2. Before / After UX Comparison

| Area | Before AUTH.UX.1 | After AUTH.UX.1 (Current) |
|---|---|---|
| **Public Landing (`/`)** | 3 separate role cards ("Dành cho Học sinh", "Cổng Giáo viên", "Cổng Quản trị viên") with 3 separate entry buttons ("Vào khu vực", "Vào cổng"). | One clean educational hero with prominent [Đăng nhập] CTA and 3 educational feature highlights. Zero role cards. |
| **Public Header** | Displayed pre-login navigation tabs: "Học sinh", "Giáo viên", "Quản trị". | Clean brand logo + title on left, single [Đăng nhập] button on right. |
| **Login Screen (`/login`)** | Displayed role-targeted text ("Dành cho Học sinh, Giáo viên và Quản trị viên") and multi-role messaging. | Single clean form: Title "Đăng nhập MathVision Kids", Subtitle "Nhập tài khoản của bạn để tiếp tục", Email + Password + [Đăng nhập]. |
| **Role Selection** | Implicit role choice via cards/buttons. | **ABSENT.** Zero role selectors or tabs. Backend determines user role. |
| **Post-Auth Dispatch** | Intermediary status texts ("Đang mở Cổng Học sinh...", "Đang kết nối Cổng Giáo viên..."). | **Immediate automatic dispatch:** Student → `/student`, Teacher → Teacher Dashboard via SSO, Admin → Admin Dashboard via SSO. |
| **Teacher Web (`5173`) Direct Login** | Rendered separate direct login card with ecosystem link. | Automatically redirects unauthenticated traffic to `http://localhost:5172/login`. |
| **Admin Web (`5174`) Direct Login** | Rendered separate direct login card with quick-fill demo buttons. | Automatically redirects unauthenticated traffic to `http://localhost:5172/login`. |

---

## 3. One Login Architecture

```
                      [ User Enters Credentials ]
                                  │
                       Email + Password Form
                                  │
                                  ▼
               POST /api/v1/auth/login (Spring Boot)
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              [ 401 Invalid ]             [ 200 Valid ]
                    │                           │
          "Tài khoản hoặc mật khẩu        Extract verified role
             chưa đúng."                   from Backend Authority
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │                              │                              │
                 ▼                              ▼                              ▼
             [ STUDENT ]                   [ TEACHER ]                     [ ADMIN ]
                 │                              │                              │
         navigate('/student')         POST /auth/sso/ticket          POST /auth/sso/ticket
                 │                              │                              │
          Friendly Product            Redirect to Teacher App       Redirect to Admin App
               Bridge                 :5173/login#sso=<code             :5174/login#sso=<code
                                                │                              │
                                      Exchange ticket (POST)         Exchange ticket (POST)
                                                │                              │
                                        Teacher Dashboard              Admin Dashboard
```

---

## 4. Backend Role Dispatch

Role resolution is strictly backend-authoritative:
- The frontend client never infers roles from email names, requested URLs, or client-side toggles.
- Spring Boot generates signed JWT tokens encoding the user's authoritative role.
- Upon successful authentication, `authService.login()` validates the profile role via `/api/v1/me`.
- Switch dispatcher routes:
  ```typescript
  switch (role) {
    case 'STUDENT':
      navigate('/student');
      break;
    case 'TEACHER': {
      const ticket = await authService.requestSsoTicket('TEACHER');
      window.location.href = `http://localhost:5173/login#sso=${encodeURIComponent(ticket.code)}`;
      break;
    }
    case 'ADMIN': {
      const ticket = await authService.requestSsoTicket('ADMIN');
      window.location.href = `http://localhost:5174/login#sso=${encodeURIComponent(ticket.code)}`;
      break;
    }
    default:
      tokenStore.clearTokens();
      setError('Tài khoản không có quyền truy cập hệ thống.');
      break;
  }
  ```

---

## 5. Student Flow

1. **Authentication:** Student enters credentials (`an.student@mathvision.local` / `MathVision123!`) on `http://localhost:5172/login`.
2. **Dispatch:** Verified role `STUDENT` automatically dispatches to `/student`.
3. **Product Bridge:** Displays warm, child-friendly product guidance:
   - *"MathVision Kids dành cho Học sinh"*
   - *"Ứng dụng Học sinh đang được chạy trên thiết bị di động"*
   - 3-step learning guide (*"Chụp ảnh bài toán"*, *"Hướng dẫn từng bước"*, *"Tự tin tiến bộ"*).
   - Large buttons, accessible typography, zero developer or Expo jargon.
4. **Native Mobile Preservation:** Native Student Mobile Expo/React Native app remains completely independent and untouched.

---

## 6. Teacher Flow

1. **Authentication:** Teacher enters credentials (`lan.teacher@mathvision.local` / `MathVision123!`) on `http://localhost:5172/login`.
2. **Dispatch:** Verified role `TEACHER` triggers secure SSO ticket minting:
   - `POST /api/v1/auth/sso/ticket` with `{ "targetApp": "TEACHER" }`.
   - Backend issues short-lived (60s), single-use ticket code `mvk_sso_<64 hex chars>`.
3. **Handoff:** Portal redirects to `http://localhost:5173/login#sso=${ticket.code}` using URL Fragment (never in query parameters, never in access tokens).
4. **Exchange:** Teacher Web extracts fragment, scrubs the URL bar immediately, exchanges the ticket via `/api/v1/auth/sso/exchange`, stores session tokens, and navigates to the Teacher Dashboard.
5. **Direct Navigation Protection:** If an unauthenticated user navigates directly to `http://localhost:5173/` or `http://localhost:5173/login`, Teacher Web automatically redirects them to `http://localhost:5172/login`.

---

## 7. Admin Flow

1. **Authentication:** Admin enters credentials (`admin.demo@mathvision.local` / `MathVision123!`) on `http://localhost:5172/login`.
2. **Dispatch:** Verified role `ADMIN` triggers secure SSO ticket minting:
   - `POST /api/v1/auth/sso/ticket` with `{ "targetApp": "ADMIN" }`.
   - Backend issues short-lived (60s), single-use ticket code `mvk_sso_<64 hex chars>`.
3. **Handoff:** Portal redirects to `http://localhost:5174/login#sso=${ticket.code}` using URL Fragment.
4. **Exchange:** Admin Web extracts fragment, scrubs the URL bar, exchanges ticket via `/api/v1/auth/sso/exchange`, and navigates to the Admin Dashboard.
5. **Direct Navigation Protection:** If an unauthenticated user navigates directly to `http://localhost:5174/` or `http://localhost:5174/login`, Admin Web automatically redirects them to `http://localhost:5172/login`.

---

## 8. Public Navigation Simplification

- **Unauthenticated Header:**
  - Left: Brand Logo + `MathVision Kids` + `Trợ lý học tập và chấm bài viết tay`.
  - Center: Clean (no role links).
  - Right: Single `[Đăng nhập]` primary button.
  - (If `VITE_SHOW_DEV_TOOLS === 'true'`, renders discreet `Dev Tools` link).
- **Authenticated Header (Student on Web):**
  - Displays user avatar, display name, `Học sinh` role badge, and `[Đăng xuất]` button.
- **Removed from Navigation:**
  - Removed pre-login tabs: "Học sinh", "Giáo viên", "Quản trị".
  - Removed "Cổng Học sinh", "Cổng Giáo viên", "Cổng Quản trị".

---

## 9. Teacher/Admin Direct Login Handling

Normal users must never encounter multiple disparate login pages.
- **Teacher Web (`teacher-web/src/pages/LoginPage.tsx`):**
  - Unauthenticated access without `#sso=` code automatically redirects:
    `window.location.href = 'http://localhost:5172/login';`
  - Fallback direct login form is rendered **only** when `?fallback=true` or `?direct=true` is explicitly provided.
  - Removed all mentions of `(Port 5172)` from fallback UI.
- **Admin Web (`admin-web/src/pages/LoginPage.tsx`):**
  - Unauthenticated access without `#sso=` code automatically redirects:
    `window.location.href = 'http://localhost:5172/login';`
  - Fallback direct login form is rendered **only** when `?fallback=true` or `?direct=true` is explicitly provided.
  - Removed all mentions of `(Port 5172)` and developer quick-fill chips from normal product UI.

---

## 10. Dev Tool Isolation

All developer-oriented features remain strictly quarantined:
- **Flag Gating:** `import.meta.env.VITE_SHOW_DEV_TOOLS === 'true'`.
- **Default Production Mode:** `VITE_SHOW_DEV_TOOLS=false`.
- **Developer Demo Tools Accordion:** Quick-fill chips for test credentials in `LoginPage.tsx` render **only** when `VITE_SHOW_DEV_TOOLS=true`.
- **Dev Runtime Route:** `/dev/mobile` and `/dev/runtime` immediately redirect to `/` when dev flag is unset or false.

---

## 11. Security Preservation

All security closures established in earlier phases are fully maintained:
1. **Spring Boot Authority:** Spring Boot remains the single source of truth for authentication and authorization.
2. **Strict RBAC:** Role boundaries enforced at API layer (Student denied `/teacher/*` and `/admin/*`; Teacher denied `/admin/*`).
3. **SSO Ticket Security:**
   - 60-second TTL.
   - Single-use consumption (replay attacks rejected with HTTP 401).
   - Target app binding (Teacher cannot mint Admin tickets; tickets cannot be exchanged by unauthorized applications).
4. **URL Fragment Transport:** `#sso=` fragment transport ensures credentials and tickets never hit server access logs or browser history. URL is immediately scrubbed upon load.
5. **Unified Logout:** `POST /api/v1/auth/logout` revokes backend sessions and clears all tokens across frontends.

---

## 12. Role & RBAC Regression Verification

| Test Case | Actor | Target Resource | Expected | Actual Result | Status |
|---|---|---|---|---|---|
| Student Access Teacher API | Student (`ROLE_STUDENT`) | `/api/v1/teacher/dashboard` | 403 Forbidden | HTTP 403 | **PASS** |
| Student Access Admin API | Student (`ROLE_STUDENT`) | `/api/v1/admin/dashboard` | 403 Forbidden | HTTP 403 | **PASS** |
| Student Mint Teacher SSO | Student (`ROLE_STUDENT`) | `/api/v1/auth/sso/ticket` (TEACHER) | 403 Forbidden | HTTP 403 | **PASS** |
| Student Mint Admin SSO | Student (`ROLE_STUDENT`) | `/api/v1/auth/sso/ticket` (ADMIN) | 403 Forbidden | HTTP 403 | **PASS** |
| Teacher Access Admin API | Teacher (`ROLE_TEACHER`) | `/api/v1/admin/dashboard` | 403 Forbidden | HTTP 403 | **PASS** |
| Teacher Mint Admin SSO | Teacher (`ROLE_TEACHER`) | `/api/v1/auth/sso/ticket` (ADMIN) | 403 Forbidden | HTTP 403 | **PASS** |
| SSO Ticket Replay Attack | Any | `/api/v1/auth/sso/exchange` | 401 Unauthorized | HTTP 401 | **PASS** |
| SSO Target App Mismatch | Teacher Ticket | `/api/v1/auth/sso/exchange` (ADMIN) | 401 Unauthorized | HTTP 401 | **PASS** |

---

## 13. Visual Verification

Captured and audited via `browser_subagent`:

1. **Portal Landing Page (`1440x900`):**
   - File: `portal_landing_1440x900_1789221343472.png`
   - Zero role cards. Clean, prominent, centered `[Đăng nhập]` CTA button. Educational feature highlights.
2. **Portal Login Page (`1440x900`):**
   - File: `portal_login_1440x900_1789221350565.png`
   - Single clean login card. Title: "Đăng nhập MathVision Kids". Subtitle: "Nhập tài khoản của bạn để tiếp tục".
   - Email, Password with interactive show/hide toggle. Zero demo chips.
3. **Portal Login Page Mobile (`375x812`):**
   - File: `portal_login_375x812_1789221361982.png`
   - Fits cleanly without horizontal overflow. Generous touch targets (48px+).
4. **Student Product Bridge Mobile (`375x812`):**
   - File: `portal_student_375x812_1789221368318.png`
   - Warm primary school aesthetic. Clear educational guidance. Zero developer jargon.
5. **Teacher & Admin Unauthenticated Redirects:**
   - `http://localhost:5173/login` → automatically redirected to `http://localhost:5172/login`.
   - `http://localhost:5174/login` → automatically redirected to `http://localhost:5172/login`.

---

## 14. Student Mobile Preservation

Strict diff check against baseline HEAD:
```bash
git diff -- src app.json package.json
# Output: (empty — 0 lines changed)
```

- **Student Mobile Source Changed:** NO (0 diff).
- **Student Mobile UI:** 100% PRESERVED.
- **Typecheck & Lint:** `npx tsc --noEmit` and `expo lint` both passed with 0 errors.

---

## 15. Files Modified

| File | Nature of Change |
|---|---|
| `portal-web/index.html` | Updated title from "Cổng Hệ sinh thái" to "Trợ lý học tập và chấm bài viết tay". |
| `portal-web/src/pages/LandingPage.tsx` | Removed 3 role cards, feature matrices, and "Vào cổng" buttons. Created clean educational hero with single [Đăng nhập] CTA. |
| `portal-web/src/pages/LoginPage.tsx` | Rebuilt into single clean login form with show/hide password toggle, automatic role dispatch, and dev tools gated behind dev flag. |
| `portal-web/src/components/layout/PortalLayout.tsx` | Removed pre-login role navigation tabs ("Học sinh", "Giáo viên", "Quản trị") from public header. |
| `portal-web/src/pages/TeacherEntryPage.tsx` | Cleaned terminology; redirects unauthenticated visitors to `/login`. |
| `portal-web/src/pages/AdminEntryPage.tsx` | Cleaned terminology; redirects unauthenticated visitors to `/login`. |
| `portal-web/src/pages/AccessDeniedPage.tsx` | Refined phrasing to remove overdesign terms. |
| `portal-web/src/pages/LogoutPage.tsx` | Cleaned source title strings to remove overdesign terms. |
| `teacher-web/src/pages/LoginPage.tsx` | Automatically redirects unauthenticated traffic to portal login; cleaned fallback links. |
| `teacher-web/src/components/layout/Sidebar.tsx` | Updated home link label from "Cổng chung (Portal)" to "Trang chủ MathVision Kids". |
| `teacher-web/src/components/layout/Topbar.tsx` | Updated home link label from "Về Cổng chung (Portal)" to "Về MathVision Kids". |
| `admin-web/src/pages/LoginPage.tsx` | Automatically redirects unauthenticated traffic to portal login; cleaned fallback links. |
| `admin-web/src/components/layout/AdminSidebar.tsx` | Updated home link label from "Cổng chung (Portal)" to "Trang chủ MathVision Kids". |

---

## 16. Test Results

| Test Suite | Commands | Results |
|---|---|---|
| **Portal Web Build & Lint** | `npm run lint && npm run build` in `portal-web/` | **PASS** (0 errors, 0 warnings) |
| **Teacher Web Build & Lint** | `npm run lint && npm run build` in `teacher-web/` | **PASS** (0 errors, build OK) |
| **Admin Web Build & Lint** | `npm run lint && npm run build` in `admin-web/` | **PASS** (0 errors, 0 warnings) |
| **Student Mobile Typecheck & Lint** | `npx tsc --noEmit && npm run lint` in root | **PASS** (0 errors, build OK) |
| **Spring Boot Tests** | `./gradlew.bat test --rerun` in `services/business-api/` | **PASS** (119/119 tests passed, 0 failures) |
| **Dev Text Leak Scan** | `python scratch/test_dev_leak.py` | **PASS** (0 forbidden strings found) |
| **AUTH.UX.1 E2E Suite** | `python scratch/test_auth_ux_1_e2e.py` | **PASS** (24/24 assertions passed) |
| **Ecosystem E2E Suite** | `python scratch/test_ecosystem_portal_1_1_e2e.py` | **PASS** (28/28 assertions passed) |

---

## 17. Final Verdict

**ECOSYSTEM AUTH.UX.1: PASS**  
The login and web portal experience of MathVision Kids has been restored to clean, consumer-grade simplicity. Users interact with a single, elegant login form; the backend verifies identity and role; and the system automatically dispatches each user to their corresponding workspace with zero unnecessary friction or technical jargon.
