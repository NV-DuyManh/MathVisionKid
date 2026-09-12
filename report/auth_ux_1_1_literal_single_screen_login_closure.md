# AUTH.UX.1.1 — Literal Single-Screen Login Closure & Hardening

**Task Reference:** AUTH.UX.1.1  
**Project:** MathVision Kids  
**Mode:** Micro UX Closure Only  
**Design Intelligence:** Applied `/ui-ux-pro-max` (consumer-app login simplicity, clean whitespace, accessible typography, zero technical jargon)  
**Timestamp:** 2026-09-12T21:07:00+07:00  
**Status:** PASS  

---

## 1. Before / After Comparison

| Area | Before AUTH.UX.1.1 | After AUTH.UX.1.1 (Current) |
|---|---|---|
| **Root Route (`/`)** | Rendered a marketing/feature landing page with educational highlights and an extra `[Đăng nhập]` CTA button. | **Direct Single Login Screen:** Navigating to `http://localhost:5172/` renders the login form directly. No intermediate landing page. |
| **Public Header** | Header included a second, redundant `[Đăng nhập]` button in the top-right corner. | Minimal header showing only the MathVision Kids logo and brand title. No duplicate login button. |
| **Student Product Bridge** | Claimed `"Ứng dụng Học sinh đang được chạy trên thiết bị di động"` and included an `"Mở ứng dụng Học sinh"` dialog button. | **Truthful Product Copy:** `"MathVision Kids dành cho học sinh được sử dụng trên điện thoại hoặc máy tính bảng."` Removed the unverified assertion and fake action dialog. |
| **Teacher/Admin Dev Fallback** | Fallback direct login form was accessible solely via `?fallback=true` or `?direct=true` query parameters. | **Hardened Dev Isolation:** Fallback direct login strictly requires `VITE_SHOW_DEV_TOOLS === 'true'`. In standard/production mode, `?fallback=true` immediately redirects to `http://localhost:5172/`. |
| **Pre-Auth Navigation** | Pre-auth tabs existed in previous iterations. | **Zero pre-auth role tabs, zero role pickers, zero marketing blocks.** |

---

## 2. Root Route Behavior

- The root path (`/`) in `portal-web/src/App.tsx` now directly maps to `<LoginPage />`:
  ```tsx
  <Route index element={<LoginPage />} />
  <Route path="login" element={<LoginPage />} />
  ```
- Unauthenticated users arriving at `http://localhost:5172/` immediately see the login card with zero friction.
- Authenticated users with active session tokens who visit `/` or `/login` are automatically dispatched to their designated workspace (`/student` for students, Teacher Dashboard via SSO for teachers, Admin Dashboard via SSO for admins).

---

## 3. Login Screen

The single login interface conforms strictly to consumer-grade simplicity:
- **Title:** "Đăng nhập MathVision Kids"
- **Subtitle:** "Nhập tài khoản của bạn để tiếp tục"
- **Form Fields:**
  - `Email` (autoFocus, clean placeholder)
  - `Mật khẩu` (with interactive show/hide visibility toggle)
- **Primary CTA:** Full-width `[Đăng nhập]` button with loading state indicator
- **Validation & Error Handling:** Clean Vietnamese alerts (`"Tài khoản hoặc mật khẩu chưa đúng."`, `"Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."`)
- **Developer Demo Tools:** Completely hidden behind an accordion that renders only when `VITE_SHOW_DEV_TOOLS === 'true'`.
- **Duplicate Buttons:** Zero duplicate login buttons in the navigation bar.

---

## 4. Automatic Role Dispatch

Role routing is strictly backend-authoritative:
1. User enters Email + Password and clicks `[Đăng nhập]`.
2. Spring Boot authenticates credentials and returns JWT session tokens.
3. Client verifies role from authenticated profile:
   - `ROLE_STUDENT` (`STUDENT`): Dispatches immediately to `/student`.
   - `ROLE_TEACHER` (`TEACHER`): Requests short-lived one-time SSO ticket and redirects via fragment transport to `http://localhost:5173/login#sso=${ticket.code}`.
   - `ROLE_ADMIN` (`ADMIN`): Requests short-lived one-time SSO ticket and redirects via fragment transport to `http://localhost:5174/login#sso=${ticket.code}`.
4. The user is never prompted to select or confirm a role.

---

## 5. Student Destination

- **Route:** `/student`
- **Truthful Tone:**
  - Headline: *"MathVision Kids dành cho học sinh được sử dụng trên điện thoại hoặc máy tính bảng."*
  - Body: *"Để chụp ảnh và chấm bài tập số học trực tiếp từ vở ô ly, em hãy mở ứng dụng MathVision Kids trên điện thoại hoặc máy tính bảng."*
- **Child-Friendly 3-Step Guide:**
  1. *Chụp ảnh bài toán*
  2. *Nhận hướng dẫn ngay*
  3. *Tự tin tiến bộ*
- **Technical Isolation:** Zero mentions of Expo, Metro, LAN, localhost, ports, or backend architecture.
- **Removed Artifacts:** The misleading assertion that the mobile app is currently running in the background and the fake "Mở ứng dụng Học sinh" dialog button have been removed.

---

## 6. Teacher / Admin Direct Access

Normal users who access Teacher Web or Admin Web without prior authentication are seamlessly bounced to the single portal login:
- Direct visit to `http://localhost:5173/` or `http://localhost:5173/login` → automatically redirects to `http://localhost:5172/`.
- Direct visit to `http://localhost:5174/` or `http://localhost:5174/login` → automatically redirects to `http://localhost:5172/`.
- Upon successful authentication on `http://localhost:5172/`, the verified Teacher or Admin is automatically returned to their dashboard via one-time SSO fragment exchange.

---

## 7. Dev Fallback Isolation Hardening

Direct login fallback forms in Teacher and Admin apps have been hardened against query-parameter leakage:
```typescript
// teacher-web & admin-web LoginPage.tsx
const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';
const hasFallbackParam = searchParams.get('fallback') === 'true' || searchParams.get('direct') === 'true';
const isAllowedFallback = showDevTools && hasFallbackParam;

if (!isAllowedFallback) {
  window.location.href = 'http://localhost:5172/';
  return;
}
```
- When `VITE_SHOW_DEV_TOOLS` is `false` (the default production mode), query parameters like `?fallback=true` or `?direct=true` are ignored, and the user is redirected to `http://localhost:5172/`.

---

## 8. Security Regression Verification

All security mechanisms remain fully intact:
- **Backend Role Authority:** Enforced by Spring Boot RBAC filters.
- **SSO Ticket Security:** 60-second time-to-live, single-use consumption, replay attacks rejected with HTTP 401.
- **Credential Transport:** URL fragment `#sso=` used exclusively; zero JWT/access tokens in URLs; URL bar immediately scrubbed.
- **Unified Logout:** Revokes server session tokens and clears all local storage.
- **Network Boundaries:** FastAPI internal service remains bound to loopback.

---

## 9. Visual Verification

Verified via `browser_subagent` across desktop and mobile viewports:

1. **Desktop Viewport (1440x900) — Root Login (`http://localhost:5172/`):**
   - Screenshot: `root_login_1440x900_1789221889524.png`
   - Directly renders the single login card. Minimal header with zero duplicate buttons.
2. **Mobile Viewport (375x812) — Root Login (`http://localhost:5172/`):**
   - Screenshot: `root_login_375x812_1789221936885.png`
   - Clean mobile fit, zero horizontal overflow, 48px+ touch targets.
3. **Mobile Viewport (375x812) — Student Bridge (`http://localhost:5172/student`):**
   - Screenshot: `student_truthful_375x812_1789221944382.png`
   - Truthful copy displayed. No fake modal trigger.
4. **Teacher Fallback Blocked (`http://localhost:5173/login?fallback=true`):**
   - Screenshot: `teacher_fallback_blocked_1789221960775.png`
   - Immediately redirected to `http://localhost:5172/`.
5. **Admin Fallback Blocked (`http://localhost:5174/login?fallback=true`):**
   - Screenshot: `admin_fallback_blocked_1789221969511.png`
   - Immediately redirected to `http://localhost:5172/`.

---

## 10. Test Results

| Test Suite | Scope | Result |
|---|---|---|
| **Portal Web Build & Lint** | `oxlint` & `tsc -b && vite build` | **PASS** (0 errors, 0 warnings) |
| **Teacher Web Build & Lint** | `oxlint` & `tsc -b && vite build` | **PASS** (0 errors, build OK) |
| **Admin Web Build & Lint** | `oxlint` & `tsc -b && vite build` | **PASS** (0 errors, 0 warnings) |
| **Student Mobile Lint & TSC** | `npx tsc --noEmit && expo lint` | **PASS** (0 errors, build OK) |
| **Spring Boot Unit & Integration** | `./gradlew.bat test` | **PASS** (119/119 tests passed) |
| **AUTH.UX.1.1 Targeted E2E** | `python scratch/test_auth_ux_1_e2e.py` | **PASS** (29/29 assertions passed) |
| **Ecosystem E2E Suite** | `python scratch/test_ecosystem_portal_1_1_e2e.py` | **PASS** (28/28 assertions passed) |
| **Dev Text Leak Scan** | `python scratch/test_dev_leak.py` | **PASS** (0 forbidden strings found) |

---

## 11. Files Modified

1. `portal-web/src/App.tsx`: Mapped root route (`/`) directly to `<LoginPage />`.
2. `portal-web/src/components/layout/PortalLayout.tsx`: Removed redundant top-right `[Đăng nhập]` button for unauthenticated users.
3. `portal-web/src/pages/LoginPage.tsx`: Added auto-dispatch on mount for users with existing active session tokens.
4. `portal-web/src/pages/StudentLandingPage.tsx`: Updated copy to truthful product wording; removed unverified "running" status and fake "open app" dialog.
5. `teacher-web/src/pages/LoginPage.tsx`: Hardened fallback login condition to require both `VITE_SHOW_DEV_TOOLS=true` and fallback query parameter.
6. `admin-web/src/pages/LoginPage.tsx`: Hardened fallback login condition to require both `VITE_SHOW_DEV_TOOLS=true` and fallback query parameter.

---

## 12. Final Verdict

**ECOSYSTEM AUTH.UX.1.1: PASS**  
The login flow is now literally a single-screen experience. The browser opens directly to the MathVision Kids login form; the backend verifies identity and role; and the system dispatches each role to their intended destination with zero intermediate marketing friction, zero pre-login role selection, and zero developer terminology.
