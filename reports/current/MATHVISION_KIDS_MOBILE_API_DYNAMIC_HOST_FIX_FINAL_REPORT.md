# MathVision Kids — Mobile API Dynamic Host Resolution Fix (Round 1) Final Report

**Run Identifier:** `MATHVISION.KIDS.MOBILE-API-DYNAMIC-HOST-FIX-R1`  
**Execution Timestamp:** 2026-09-22T14:05:00+07:00  
**Target Scope:** Student Mobile (`apps/student-mobile`), Metro Bundler Dynamic LAN Discovery, Safe Fallbacks  
**Review Target:** Single Comprehensive Verification Document

---

## Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native performance, dynamic URL evaluation per request without stale state freeze, and elimination of synchronous blocking alerts.
  - Applied to: `apps/student-mobile/src/config/apiResolver.ts`, `apps/student-mobile/src/config/env.ts`, `apps/student-mobile/src/services/api/apiClient.ts`.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal diffs, root cause resolution, standard library and native platform prioritization, and removal of dead hardcoded LAN IPs.
  - Applied to: `apps/student-mobile/src/config/apiResolver.ts`, `apps/student-mobile/src/app/_layout.tsx`.

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 The Incident
Following a local Wi-Fi router network migration, the development workstation's active IPv4 address changed from `192.168.1.10` to `192.168.1.14`.
When Student Mobile was opened via Expo Go (connecting to Metro at `192.168.1.14:8081`), network requests to the Spring Boot backend failed with:
```
java.net.ConnectException: Failed to connect to /192.168.1.10:8080
```
Furthermore, a blocking alert dialog was displayed on the mobile interface showing technical URLs (`Không kết nối được backend tại http://192.168.1.10:8080`).

### 1.2 Root Cause Identification
1. **Inverted Evaluation Order in `apiResolver.ts`:**
   In the legacy implementation of `apps/student-mobile/src/config/apiResolver.ts`, the developer environment override was evaluated **before** dynamic Metro LAN host discovery:
   ```typescript
   // LEGACY CODE (VULNERABLE ORDER):
   const overrideUrl = process.env.EXPO_PUBLIC_DEV_API_BASE_URL || process.env.EXPO_PUBLIC_API_BASE_URL;
   if (overrideUrl) {
     if (isPhysicalDevice && isLoopback(overrideUrl)) { ... }
     else {
       resolvedUrl = overrideUrl;
       selectedSource = 'ENV_OVERRIDE'; // <--- ALWAYS WON!
     }
   }
   // Step 3 (Metro Host Detection) was NEVER REACHED!
   ```
2. **Stale Hardcoded Variable in `.env.local`:**
   `apps/student-mobile/.env.local` and `.env.local` contained `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.10:8080/api/v1`. Because Expo automatically injects `.env.local` into `process.env`, `overrideUrl` was always defined with the stale IP, permanently masking Metro LAN detection.
3. **Hardcoded Fallback Anti-pattern:**
   Line 80 of legacy `apiResolver.ts` contained `resolvedUrl = 'http://192.168.1.10:8080/api/v1'`, hardcoding a temporary local IP directly into source code.
4. **Disruptive Blocking Alert in `_layout.tsx`:**
   `apps/student-mobile/src/app/_layout.tsx` invoked `Alert.alert('Lỗi kết nối máy chủ', ...)` when the backend health check failed, creating an intrusive popup and violating the project rule forbidding the display of internal URLs, ports, and infrastructure details to students.

---

## 2. Before / After Resolver Behavior

| Scenario | Legacy Behavior | Corrected Behavior (R1) |
|---|---|---|
| **Metro LAN Mode (Expo Go on physical phone)** | Used stale `192.168.1.10` from `.env.local` (`selectedSource = 'ENV_OVERRIDE'`) | Dynamically detects Metro host `192.168.1.14` (`selectedSource = 'METRO_LAN'`) -> resolves to `http://192.168.1.14:8080/api/v1` |
| **Old `.env.local` exists with old IP** | Permanently failed to connect (`ConnectException`) | Metro LAN host (Priority 1) wins; no permanent failure |
| **Workstation Wi-Fi IP Changes** | Stuck on old IP in `.env.local` until manually re-edited | Automatically tracks new Metro host IP immediately upon reload |
| **Manual Override explicitly set** | Only supported generic `EXPO_PUBLIC_API_BASE_URL` | Explicit override (`EXPO_PUBLIC_API_OVERRIDE` or `EXPO_PUBLIC_DEV_API_BASE_URL` or function argument) is honored cleanly |
| **No Metro Host Detected (Offline/Web/Sim)** | Fell back to hardcoded `192.168.1.10` | Falls back cleanly to localhost (`127.0.0.1:8080` / `10.0.2.2:8080`) without any hardcoded LAN IPs |
| **Backend Unreachable on Startup** | App raised disruptive `Alert.alert` with internal port/IP | Logs non-crashing warning (`console.warn`); Home screen loads cleanly; no popup |

---

## 3. Implemented Resolution Hierarchy

The new resolver in `apps/student-mobile/src/config/apiResolver.ts` enforces the strict 3-tier precedence hierarchy:

```
[resolveApiBaseUrl()]
       │
       ├─► 0. Production (!__DEV__)?
       │      └─► Return production URL (or EXPO_PUBLIC_API_BASE_URL)
       │
       ├─► [Explicit Manual Override]?
       │      (EXPO_PUBLIC_API_OVERRIDE / EXPO_PUBLIC_DEV_API_BASE_URL / custom argument)
       │      └─► YES: Validate non-loopback if physical device -> return user value (MANUAL_OVERRIDE)
       │
       ├─► Priority 1: Expo Metro LAN Host Detection
       │      Inspects Constants.expoGoConfig.debuggerHost, Constants.expoConfig.hostUri,
       │      NativeModules.SourceCode.scriptURL, linkingUri, experienceUrl
       │      └─► Non-loopback host detected? -> return http://${host}:8080/api/v1 (METRO_LAN)
       │
       ├─► Priority 2: General Environment Fallback
       │      (Used only when Metro LAN host is absent/unresolved)
       │      └─► Return EXPO_PUBLIC_API_BASE_URL if non-loopback (ENV_FALLBACK)
       │
       └─► Priority 3: Localhost / Emulator Fallbacks
              ├─► Android Emulator: http://10.0.2.2:8080/api/v1 (EMULATOR_LOCALHOST)
              ├─► Web / iOS Simulator: http://127.0.0.1:8080/api/v1 (WEB_LOCALHOST)
              └─► Physical Device Fallback: http://127.0.0.1:8080/api/v1 (LOCALHOST_FALLBACK)
                     (NO hardcoded LAN IPs anywhere in codebase!)
```

---

## 4. Files Changed

### 4.1 `apps/student-mobile/src/config/apiResolver.ts`
- Implemented Priority 1 Metro LAN host detection before fallback environment reads.
- Added support for explicit manual override variables (`EXPO_PUBLIC_API_OVERRIDE`, `EXPO_PUBLIC_DEV_API_BASE_URL`, and function arguments).
- Eliminated hardcoded LAN IP fallback (`192.168.1.10`), replacing it with standard localhost fallback.
- Used dynamic property lookups to prevent Babel from statically inlining empty strings during tests.

### 4.2 `apps/student-mobile/src/config/env.ts`
- Converted `ENV.API_BASE_URL` to a dynamic getter property (`get API_BASE_URL()`), guaranteeing that runtime changes to packager host reflect across all consumers without requiring full application restart.

### 4.3 `apps/student-mobile/src/services/api/apiClient.ts`
- Injected `config.baseURL = ENV.API_BASE_URL;` inside the Axios request interceptor to ensure every outgoing HTTP call targets the dynamically resolved endpoint.

### 4.4 `apps/student-mobile/src/app/_layout.tsx`
- Removed blocking `Alert.alert('Lỗi kết nối máy chủ', ...)` call.
- Kept graceful, non-crashing `console.warn` diagnostics for developers while ensuring the student-facing UI mounts without popups or leaked debug metadata.

### 4.5 `apps/student-mobile/.env.local` & Root `.env.local`
- Removed stale `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.10:8080/api/v1`.
- Added clear documentation instructing developers that dynamic Metro LAN detection is active by default, and how to specify `EXPO_PUBLIC_API_OVERRIDE` if explicitly needed.

### 4.6 `apps/student-mobile/src/config/__tests__/apiResolver.test.ts` (NEW)
- Implemented automated Jest test suite testing Scenarios A through G directly.

### 4.7 `scripts/test/test_apiResolver.js` & `scripts/test/test_apiResolver.ts`
- Updated legacy validation scripts to point to `apps/student-mobile/src/config/apiResolver.ts` and validate 20/20 test cases under the new priority model.

---

## 5. Verification & Test Results

### 5.1 Automated Unit Tests (`npm run test:mobile`)
Command: `npm run test:mobile -- src/config/__tests__/apiResolver.test.ts`
```
PASS src/config/__tests__/apiResolver.test.ts
  apiResolver - Dynamic Mobile API Host Resolution
    √ Test A: Old .env.local IP exists -> no permanent failure, follows Metro LAN host (29 ms)
    √ Test B: Metro host changes -> API dynamically follows new Metro host (4 ms)
    √ Test C1: Manual override via parameter -> override works (2 ms)
    √ Test C2: Manual override via EXPO_PUBLIC_API_OVERRIDE -> override works (1 ms)
    √ Test C3: Manual override via EXPO_PUBLIC_DEV_API_BASE_URL -> override works (1 ms)
    √ Test D: Backend unavailable / Metro host not detected -> Safe localhost fallback, no hardcoded LAN IP (6 ms)
    √ Test E: Physical device rejects loopback override, uses Metro LAN instead (3 ms)
    √ Test F: Trailing slash is properly normalized (1 ms)
    √ Test G: Production mode uses production URL (1 ms)

Test Suites: 1 passed, 1 total
Tests:       9 passed, 9 total
```

### 5.2 Full Mobile Regression Test Suite
Command: `npm run test:mobile`
```
Test Suites: 11 passed, 11 total
Tests:       88 passed, 88 total
Snapshots:   0 total
Time:        3.784 s
Result:      100% PASS
```

### 5.3 Legacy Script Test Suite (`node scripts/test/test_apiResolver.js`)
```
Tests: 20/20 passed (100% PASS)
```

### 5.4 Live Ecosystem Diagnostic (`check_runtime.py`)
Command: `.\ai\runtime\.venv\Scripts\python.exe tools\diagnostics\check_runtime.py`
```
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

--------------------------------------------
 Network & Mobile LAN Diagnostics
--------------------------------------------
Host LAN IPv4 ......... 192.168.1.14
Metro State ........... LAN_READY (bind=::, port=8081)
Metro Bind Address .... ::
Metro LAN Reach ....... REACHABLE
Spring (localhost:8080) REACHABLE
Spring (LAN IPv4:8080)  REACHABLE
Configured API Host ... NOT_CONFIGURED (from environment)
LAN Verdict ........... PASS
--------------------------------------------
Overall ............... READY_FOR_FULL_DEMO
============================================
```

---

## 6. Physical Device & Live Verification

1. **Metro Bundler Status on LAN (`http://192.168.1.14:8081/status`):**
   - Output: `packager-status:running`
   - Verified Metro is accepting connections over the local area network.
2. **Spring Boot Backend Health on LAN (`http://192.168.1.14:8080/actuator/health`):**
   - Output: `{"status":"UP","components":{"db":{"status":"UP"},"diskSpace":{"status":"UP"},"ping":{"status":"UP"}}}`
   - HTTP 200 OK verified.
3. **Application Bundle Serving on LAN:**
   - Queried bundle root: verified HTML title `MathVision Kids` and tagline `Chụp bài • Hiểu lỗi • Tự sửa` served correctly.
4. **Health Check on Mobile App Startup:**
   - With dynamic resolution active, the mobile app connects to `http://192.168.1.14:8080/actuator/health` instead of `192.168.1.10:8080`.
   - Health check logs: `[HEALTH_CHECK] Backend is UP at http://192.168.1.14:8080`.
   - Zero intrusive alert popups appear.
   - Splash and Login / Home screens mount smoothly.

---

## 7. Compliance Checklist

- [x] Scope only: mobile API host resolution.
- [x] Did NOT modify OCR.
- [x] Did NOT modify segmentation.
- [x] Did NOT train models.
- [x] Did NOT modify backend code.
- [x] Did NOT redesign UI.
- [x] Did NOT reorganize repository.
- [x] Did NOT commit or push.
- [x] Student-facing UI does NOT show debug/network metadata or raw URLs.
- [x] No hardcoded LAN IPs in codebase.
- [x] All 88 mobile unit tests pass.
- [x] Ecosystem runtime diagnostic passes with `READY_FOR_FULL_DEMO`.

---
