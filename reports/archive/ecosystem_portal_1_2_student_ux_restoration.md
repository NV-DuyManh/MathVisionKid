# ECOSYSTEM.PORTAL.1.2 — Student UX Restoration, Dev-Tool Isolation & Product-Facing Portal Cleanup

**Task Reference:** ECOSYSTEM.PORTAL.1.2  
**Project:** MathVision Kids  
**Mode:** Targeted UX Correction  
**Timestamp:** 2026-09-12T20:37:00+07:00  
**Status:** PASS  

---

## 1. Executive Summary

In ECOSYSTEM.PORTAL.1 and 1.1, technical instructions and developer concepts (Expo, Metro Bundler, LAN QR codes, localhost ports, Spring Boot, FastAPI, MinIO, demo credentials) inadvertently leaked into the student-facing and public web portal pages. 

Because **MathVision Kids is designed for primary-school elementary students (grades 1–5)**, exposing developer testing mechanisms to young learners and parents was fundamentally incorrect for the product.

**ECOSYSTEM.PORTAL.1.2 has restored complete product boundaries and child-friendly UX:**
1. **Original Student Mobile Preservation:** Verified that the native Student Mobile app source (`src/`, `app.json`, `package.json`) was 100% UNCHANGED and preserved by all portal integration phases.
2. **Product vs. Developer UX Isolation:** Completely segregated the ecosystem into three distinct audiences:
   - **Student:** Native child-friendly mobile app (Expo/React Native) with camera and arithmetic grading.
   - **Public/Web Portal:** Warm, accessible educational portal for students, teachers, and administrators.
   - **Developer/Owner:** `RUN_MATHVISION.bat`, visible Metro terminal, health checks, ports, and dev tools.
3. **Student Portal Page Rebuild (`/student`):** Replaced technical QR/LAN/terminal instructions with a gentle, primary-school-appropriate product bridge featuring a 3-step guide (*"Chụp ảnh bài toán"*, *"Nhận hướng dẫn ngay"*, *"Tự tin tiến bộ"*) and a clear status indicator (*"Ứng dụng Học sinh đang được chạy trên thiết bị di động"*).
4. **Dev-Only Tooling Isolation (`/dev/mobile`):** Relocated all Expo/Metro LAN instructions, architecture diagrams, port matrices, and demo quick-fill credentials to a dedicated developer route gated by `VITE_SHOW_DEV_TOOLS=true`. When this flag is unset or false, normal users cannot view or access dev tools.
5. **Portal Home & Footer Sanitization:** Stripped all infrastructure terms (ports 8080, 8000, 5172, 5173, 5174, Spring Boot, FastAPI, PostgreSQL, MinIO, Redis) from the public homepage, login page, and footer.
6. **Zero Credential / Token Leaks:** Hardened all login redirects to use `#sso=` fragment transport and removed plain-text demo credentials from the public login screen.

---

## 2. Repository State

```bash
git rev-parse --show-toplevel: E:/MathVisionKid
git branch --show-current:     main
git status --short: (Only portal-web, scripts, and business-api SSO touched)
git diff -- src app.json package.json: (EMPTY — ZERO DIFF)
```

- **Model Training Executed:** 0
- **New Checkpoints Generated:** NONE
- **Git Commits Executed:** 0
- **Git Pushes Executed:** 0

---

## 3. Original Student Mobile Preservation Audit

A strict diff check against baseline HEAD (`112bbb5`) confirmed:
```bash
git diff -- src app.json package.json
# Output: (empty)
```

**Classification:**
`STUDENT_MOBILE_ORIGINAL_UI: UNCHANGED`

The native Student Mobile flow remains intact:
- Login screen
- Home screen with recent assignments
- Camera/Gallery capture with document bounds
- Privacy consent & masking
- OCR / arithmetic recognition pipeline
- Step-by-step Socratic hints & results feedback

---

## 4. Product vs Developer UX Boundary

| Dimension | Student Audience | Public Web Portal | Developer / Owner Tooling |
| :--- | :--- | :--- | :--- |
| **Primary Target** | Elementary students (grades 1–5) | Students, teachers, parents, admins | Project developer & evaluators |
| **Medium** | Mobile / Tablet (camera-enabled) | Web browser (`http://localhost:5172`) | Terminal / PowerShell / Batch |
| **Tone** | Friendly, large text, colorful, simple | Professional yet accessible educational platform | Diagnostics, ports, metrics |
| **Visible Elements** | Math problems, score stars, hints | Login, role routing, class management | Metro LAN QR, PID tables, logs |
| **Forbidden Items** | Ports, Expo, Metro, LAN, APIs, terminals | Internal ports, debug chips, demo passwords | N/A |

---

## 5. Portal Home Before/After

| Element | Pre-Fix (Portal 1.1) | Post-Fix (Portal 1.2) |
| :--- | :--- | :--- |
| **Hero Chip** | `Nền tảng Hệ sinh thái Thống nhất` | `Cổng Giáo dục Tiểu học — MathVision Kids` |
| **Secondary Button** | `Hướng dẫn Học sinh (Expo)` (Leak) | `Dành cho Học sinh` (Clean link to `/student`) |
| **Student Card Chip** | `Mobile First` (Tech jargon) | `Học sinh` (Primary school focus) |
| **Student Features** | Listed *"Ứng dụng Expo di động cho trẻ"* | *"Làm bài tập số học trên điện thoại hoặc máy tính bảng"* |
| **Architecture Section**| `<Paper>` listing ports 8080, Postgres, MinIO, RBAC | Warm school mission banner: *"Đồng hành cùng giáo dục tiểu học"* |

---

## 6. Student Page Before/After

| Element | Pre-Fix (Portal 1.1) | Post-Fix (Portal 1.2) |
| :--- | :--- | :--- |
| **Heading** | `Cổng Học sinh — MathVision Kids` | `MathVision Kids dành cho Học sinh` |
| **Subtitle** | Tech explanation of mobile-first Expo | *"Chụp bài viết tay, xem kết quả và nhận hướng dẫn từng bước."* |
| **Main Card** | "Mã QR Expo LAN Thực Tế" with terminal instructions | Green status card: *"Ứng dụng Học sinh đang được chạy trên thiết bị di động"* |
| **Connection Guide** | 4 steps referencing Expo Go, Wi-Fi, RUN_MATHVISION | 3 friendly steps for kids: Chụp ảnh bài toán, Nhận hướng dẫn ngay, Tự tin tiến bộ |
| **Primary Action** | Directs phone to scan console QR | Friendly [Mở ứng dụng Học sinh] button with guidance dialog |
| **Backend Line** | Listed Spring Boot (8080), FastAPI (8000), MinIO | Completely removed |

---

## 7. Login Cleanup

- **Pre-Fix:** Displayed 3 quick-fill demo chips directly in the public login card with plain-text demo email addresses and passwords.
- **Post-Fix:**
  - Standard product login form contains ONLY: Email, Password, [Đăng nhập] button, and standard error feedback.
  - Demo quick-fill chips are wrapped in an Accordion (*"Công cụ Developer Demo (Dev Only)"*) and **only rendered when `VITE_SHOW_DEV_TOOLS=true`**.
  - Passwords are never displayed in the UI.
  - Redirect URLs for Teacher and Admin in `LoginPage.tsx` use the hardened `#sso=` fragment transport.

---

## 8. Dev-Only Mobile Tooling

- Created [portal-web/src/pages/DevRuntimePage.tsx](file:///e:/MathVisionKid/portal-web/src/pages/DevRuntimePage.tsx) mapped to routes `/dev/mobile` and `/dev/runtime`.
- Protected by runtime guard:
  ```typescript
  const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';
  if (!showDevTools) {
    return <Navigate to="/" replace />;
  }
  ```
- Houses all developer testing documentation:
  - Expo CLI & Metro LAN bundler port (`8081`)
  - Running instructions via `RUN_MATHVISION.bat`
  - Local service port mapping (5172, 5173, 5174, 8080, 8000, 5432, 6379, 9000/9001)
  - Quick-copy demo credentials for test automation
- Tested in browser: attempting to access `/dev/mobile` when `VITE_SHOW_DEV_TOOLS=false` immediately redirects to `/`.

---

## 9. Footer/Technical Leak Cleanup

- **Pre-Fix Footer:**
  `Spring Business API: 8080 · AI Runtime: 8000 · Portal: 5172 · Teacher: 5173 · Admin: 5174`
- **Post-Fix Footer:**
  `© 2026 MathVision Kids — Trợ lý học tập và chấm bài viết tay cho giáo dục tiểu học`  
  `Phiên bản thử nghiệm (v1.0)`
- **Logout Page Cleaned:** Removed `(Port 5173)` and `(Port 5174)` from `LogoutPage.tsx` message strings.

---

## 10. Role Routing Regression

| Role | Authenticated Landing | Experience Delivered | Status |
| :--- | :--- | :--- | :--- |
| **STUDENT** | `/student` | Child-friendly product bridge with 3-step guide | PASS |
| **TEACHER** | `http://localhost:5173/login#sso=...` | Seamless SSO handoff to Teacher Web | PASS |
| **ADMIN** | `http://localhost:5174/login#sso=...` | Seamless SSO handoff to Admin Web | PASS |

Students never land on `/dev/mobile` or see terminal instructions upon login.

---

## 11. SSO/Logout Regression

- SSO ticket exchange: PASS (`200 OK`, returns valid JWTs)
- URL fragment handoff: PASS (`#sso=mvk_sso_...`)
- URL immediate scrubbing: PASS (`replaceState` removes code before render)
- Single-use replay protection: PASS (`401 Unauthorized`)
- Target app mismatch rejection: PASS (`401 Unauthorized`)
- Unified logout: PASS (Teacher/Admin logout calls backend `/auth/logout`, clears local session, and redirects to Portal `/logout`, which destroys Portal `localStorage`)

---

## 12. Teacher/Admin Regression

- `teacher-web`: `npm run lint` PASS (0 errors), `npm run build` PASS (0 errors)
- `admin-web`: `npm run lint` PASS (0 errors), `npm run build` PASS (0 errors)
- Workspaces and capabilities (Classroom management, Batch submission review, Privacy masking, Audit logs) remain completely intact.

---

## 13. Student Mobile Regression

- `npx tsc --noEmit`: **PASS** (0 errors)
- `npm run lint` (`expo lint`): **PASS** (0 errors)
- Screen hierarchy and native Expo components preserved.

---

## 14. Developer String Leak Search

Executed automated text search across all public/student portal files:
- `portal-web/src/pages/LandingPage.tsx`
- `portal-web/src/pages/StudentLandingPage.tsx`
- `portal-web/src/pages/LoginPage.tsx`
- `portal-web/src/pages/LogoutPage.tsx`
- `portal-web/src/pages/AccessDeniedPage.tsx`
- `portal-web/src/pages/SessionExpiredPage.tsx`
- `portal-web/src/components/layout/PortalLayout.tsx`

**Results for forbidden search terms:**
- `Expo`: **0 occurrences** in public UI
- `Expo Go`: **0 occurrences** in public UI
- `Metro`: **0 occurrences** in public UI
- `LAN`: **0 occurrences** in public UI (only matched Vietnamese name "Lan" in test comments)
- `localhost`: **0 visible occurrences** (only used in code redirect strings)
- `127.0.0.1`: **0 occurrences**
- `8080`, `8000`, `8081`, `5172`, `5173`, `5174`: **0 occurrences** in public UI
- `Spring Boot`, `FastAPI`, `MinIO`, `Redis`, `PostgreSQL`: **0 occurrences** in public UI
- `RUN_MATHVISION`: **0 occurrences** in public UI

---

## 15. Visual Verification

Verified using real browser screenshots at required dimensions:
1. **Portal Home (1440x900):**
   - Clean, rounded design with calm Indigo and Slate tones.
   - Header with Logo and navigation: Trang chủ, Học sinh, Giáo viên, Quản trị.
   - No clipped cards, no developer badges.
2. **Portal Login (1440x900):**
   - Clean authentication card.
   - Zero demo account chips shown in standard product mode.
3. **Student Portal Page (1440x900):**
   - Warm, friendly elementary school aesthetic.
   - Clear [Mở ứng dụng Học sinh] button and 3-step learning guide.
4. **Student Portal Page (375x812 Mobile Viewport):**
   - Fully responsive, vertical card stacking, legible typography, no horizontal overflow.

---

## 16. Files Modified

| File | Status | Purpose |
| :--- | :--- | :--- |
| `portal-web/src/pages/DevRuntimePage.tsx` | New | Isolated developer/testing documentation behind `VITE_SHOW_DEV_TOOLS` |
| `portal-web/src/pages/StudentLandingPage.tsx` | Rebuilt | Child-friendly Student bridge; removed all Expo/Metro/port leaks |
| `portal-web/src/pages/LandingPage.tsx` | Cleaned | Removed architecture Paper and tech jargon; educational focus |
| `portal-web/src/pages/LoginPage.tsx` | Cleaned | Gated demo accounts behind dev flag; hardened SSO redirect to `#sso=` |
| `portal-web/src/pages/LogoutPage.tsx` | Cleaned | Removed `(Port 5173)` and `(Port 5174)` strings from messages |
| `portal-web/src/components/layout/PortalLayout.tsx` | Cleaned | Removed technical ports from footer; added conditional dev link |
| `portal-web/src/App.tsx` | Modified | Registered `/dev/mobile` and `/dev/runtime` routes |

---

## 17. Remaining Manual Tests

1. **Owner Physical Android Test:**
   - Run `RUN_MATHVISION.bat` on laptop.
   - Scan authentic Expo LAN QR displayed in the visible terminal window using Expo Go on Android phone.
   - Submit handwriting arithmetic test sheet to verify end-to-end mobile grading.

---

## 18. Final Verdict

**ECOSYSTEM.PORTAL.1.2: PASS**

The product boundaries have been restored. Elementary school students are presented with an encouraging, age-appropriate educational interface, while developer and owner tooling remains safely isolated in dedicated workflows.
