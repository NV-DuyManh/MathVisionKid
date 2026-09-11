# MOBILE.PHYSICAL.1 — Student Mobile Real Android Device Setup & Testing Audit Report

**Task:** `MOBILE.PHYSICAL.1 — Setup Student Mobile for Real Android Phone Testing + Owner Phone Guide`  
**Date:** 2026-09-11  
**Repository:** `E:\MathVisionKid`  
**Branch:** `main`  
**Mode:** Local Physical Device Testing / Zero Cloud Deployment / No Feature Scope Expansion  
**Final Status:** `LAPTOP_SETUP_READY` (Phone connectivity awaiting owner on-device test: `PHONE_TEST_REQUIRED`)  

---

## 1. Executive Summary

This phase configures the MathVision Kids Student Mobile application and the local backend runtime running on the Windows development laptop so that the product owner can connect and test the mobile application directly on a physical Android smartphone over the local Wi-Fi network.

The owner's physical device was confirmed to already have **Expo Go** active, with the "Scan QR" and "Enter URL exp://" interface ready for connection. The mobile app architecture was verified to be fully compatible with Expo Go (Expo SDK 57), requiring no native custom compilation or development build.

The laptop's active Wi-Fi LAN IPv4 address was dynamically detected as `192.168.1.12`. The Student Mobile API base URL configuration was safely updated using a gitignored `.env.local` file pointing to `http://192.168.1.12:8080/api/v1`. The Spring Boot backend was verified to bind to `0.0.0.0:8080` (dual-stack `:::8080`), and both localhost and LAN IP health checks passed (`{"status":"UP"}`). A dedicated in-app Developer Diagnostic card was added to the dev-demo screen and linked from the login screen in development mode (`__DEV__`).

All tests (TypeScript typecheck, ESLint, expo-doctor, stack health) passed without regressions. A simple, numbered Vietnamese guide was created at `report/evidence/mobile_physical_1/PHONE_TEST_QUICK_GUIDE_VI.md`.

---

## 2. Repository State

At task start:
```text
Repository Root: E:\MathVisionKid
Current Branch:  main
Working Tree:    clean (0 uncommitted changes prior to task execution)
```

At task completion:
Tracked changes are strictly limited to non-invasive configuration and developer diagnostic integration:
- `package.json` (`"start:device": "expo start --lan"`)
- `services/business-api/src/main/resources/application.yml` (`address: ${SERVER_ADDRESS:0.0.0.0}`)
- `src/app/dev-demo.tsx` (developer connection diagnostic box)
- `src/app/login.tsx` (development link to diagnostic screen)
- `.env.local` (untracked, gitignored local machine IP configuration)

No models, model weights, parsers, validators, or production settings were modified.

---

## 3. Student Mobile Location

The Student Mobile application is located at the workspace root of `E:\MathVisionKid`:
- Entry point: `expo-router/entry`
- Route hierarchy: `src/app/`
- Core domain components: `src/components/`
- Configuration & services: `src/config/`, `src/services/`
- Assets & icons: `assets/`

Directory verification:
- `package.json`: present at `E:\MathVisionKid\package.json`
- `app.json`: present at `E:\MathVisionKid\app.json`
- Expo config: Expo Router v57 file-based routing in `src/app/`

---

## 4. Expo / React Native Architecture

The mobile app is built upon the modern Expo SDK 57 ecosystem:
- **Expo SDK:** `~57.0.19`
- **React Native:** `0.86.3`
- **React:** `19.2.3`
- **Expo Router:** `~57.0.18` (file-based navigation with `src/app/` directory)
- **State Management & Context:** React Context (`AuthContext` with secure persistent storage)
- **Token Storage:** `expo-secure-store` on native devices; fallback to `localStorage` on web
- **Image Capture & Media:** `expo-camera` (`CameraView`), `expo-image-picker`, `expo-image-manipulator`
- **Privacy & Snapshot:** `react-native-view-shot` for manual on-device PII bounding box masking
- **HTTP Client:** `axios` with automatic token injection and 401 refresh queuing in `src/services/api/apiClient.ts`

---

## 5. Expo Go Compatibility

- **Status:** Fully compatible (`TEST METHOD = EXPO GO`)
- **Evidence:**
  1. All declared dependencies in `package.json` (`expo-camera`, `expo-image-picker`, `expo-image-manipulator`, `expo-secure-store`, `react-native-reanimated`, `react-native-gesture-handler`, `react-native-view-shot`) are standard Expo SDK 57 libraries bundled directly in Expo Go.
  2. No custom unlinked native C++/Java Android modules or custom native dependencies are present.
  3. The owner's uploaded screenshot (`media_1789133582804.png`) shows Expo Go actively open on the Android smartphone, currently supporting SDK 57 and ready to scan QR codes or accept `exp://` connection URLs.

No development build (`npx expo run:android`) is necessary for physical device testing.

---

## 6. Current API Base URL Architecture

Centralized configuration in `src/config/env.ts`:
```typescript
export const ENV = {
  API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL || (Platform.OS === 'web' ? 'http://127.0.0.1:8080/api/v1' : 'http://10.0.2.2:8080/api/v1'),
  USE_MOCK: process.env.EXPO_PUBLIC_USE_MOCK === 'true' || false,
};
```
- No hardcoded `localhost` or machine-specific IP addresses are scattered across application logic.
- Services (`apiClient`, `SpringSubmissionService`, `authApi`) import `ENV.API_BASE_URL` exclusively.
- `SubmissionServiceFactory.ts` delegates to `SpringSubmissionService` when `ENV.USE_MOCK` is `false` (the default).

---

## 7. Changes Made

1. **Local Device Environment (`.env.local`):**
   - Created at `E:\MathVisionKid\.env.local` (already gitignored by existing `.gitignore` patterns `*.env.local` and `.env*.local`).
   - Contains: `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.12:8080/api/v1`.
2. **Spring Boot LAN Binding (`application.yml`):**
   - Set `server.address: ${SERVER_ADDRESS:0.0.0.0}` to ensure Tomcat explicitly binds to all network interfaces on port 8080.
3. **Convenience Start Script (`package.json`):**
   - Added `"start:device": "expo start --lan"` for straightforward physical device launching.
4. **Developer Diagnostic Integration (`src/app/dev-demo.tsx` & `src/app/login.tsx`):**
   - Implemented an interactive diagnostic card showing resolved API URL, OS platform, and a live "Kiểm tra kết nối Backend" ping button targeting `/actuator/health`.
   - Exposed via a development-only (`__DEV__`) link on the login screen.

---

## 8. LAN Adapter / IPv4

Inspected Windows network adapters via `Get-NetIPAddress`:
- Active Adapter: **`Wi-Fi`** (SSID: `Kim Chung 4`)
- Interface Index: `23`
- IPv4 Address: **`192.168.1.12`**
- Prefix Length: `24` (Subnet mask `255.255.255.0`)
- Address State: `Preferred / Unicast`

Ignored adapters:
- `172.26.144.1`: Virtual WSL adapter
- `192.168.56.1`: VirtualBox host-only adapter
- `26.205.69.217`: Radmin VPN adapter
- `169.254.x.x`: APIPA unconfigured adapters
- `127.0.0.1`: Loopback

---

## 9. Spring Binding

- **Configuration:** `services/business-api/src/main/resources/application.yml`
- **Configured Address:** `server.address: ${SERVER_ADDRESS:0.0.0.0}`
- **Active Listener:** Port `8080` bound to `::` (dual-stack all-interfaces, accepting both IPv4 `0.0.0.0` and IPv6 `::`).

---

## 10. Spring Port

- **Port:** `8080`
- **Protocol:** HTTP (unencrypted local LAN transport suitable for physical testing)
- **Process:** Java PID `28656` (`com.mathvisionkids.api.BusinessApiApplication`)

---

## 11. LAN Health Check

Verified from the host laptop via PowerShell `Invoke-RestMethod`:
1. **Localhost:**
   - URL: `http://localhost:8080/actuator/health`
   - Result: `{"status":"UP","components":{...}}` (PASS)
2. **LAN IPv4:**
   - URL: `http://192.168.1.12:8080/actuator/health`
   - Result: `{"status":"UP","components":{...}}` (PASS)
3. **Student Auth API over LAN:**
   - URL: `http://192.168.1.12:8080/api/v1/auth/login`
   - Payload: `{"email":"minh.student@mathvision.local","password":"MathVision123!"}`
   - Result: HTTP 200 OK with valid JWT `accessToken` for student "Nguyễn Bình Minh" (PASS).

---

## 12. Windows Firewall Status

- **Detection:**
  - Wi-Fi Connection Profile: `Kim Chung 4`
  - Current Profile Category: `Public`
- **Implication:**
  - On Windows, a network profile set to `Public` causes Windows Firewall to block unsolicited incoming TCP connections from other LAN devices by default.
- **Action Taken (Strict Adherence to Safety Rules):**
  - Antigravity did NOT modify firewall settings silently as Administrator.
  - Provided two clear options for the owner:
    1. *(Recommended)* Set Wi-Fi network profile to **Private** in Windows Settings (`Settings → Network & internet → Wi-Fi → Kim Chung 4 → Private network`).
    2. *(Optional Manual Command)* Run in an elevated Administrator PowerShell prompt:
       ```powershell
       New-NetFirewallRule -DisplayName "MathVision Spring Boot (8080)" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
       New-NetFirewallRule -DisplayName "MathVision Expo Metro (8081)" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow
       ```

---

## 13. Expo Start Command

Recommended repeatable launch command:
```bash
npm run start:device
```
or
```bash
npx expo start --lan
```

---

## 14. QR / Metro Status

- **Status:** PASS
- **Host Mode:** `lan` (`192.168.1.12`)
- **Port:** `8081` (Listening on `:::8081`)
- **Packager Status Endpoint:**
  - `http://localhost:8081/status` -> `packager-status:running`
  - `http://192.168.1.12:8081/status` -> `packager-status:running`
- **Android Manifest Endpoint:**
  - `http://192.168.1.12:8081` with header `expo-platform: android` returned HTTP `200 OK`.
- **Expo URL:** `exp://192.168.1.12:8081`

---

## 15. Developer Diagnostic Status

Integrated directly into `src/app/dev-demo.tsx`:
- Displays:
  - Runtime Environment (`ANDROID Development`)
  - Resolved `API_BASE_URL` (`http://192.168.1.12:8080/api/v1`)
  - Mock Mode Toggle status
  - Dynamic "Kiểm tra kết nối Backend" button that tests `/actuator/health` and provides immediate feedback.
- Accessible via development link `🛠️ Chẩn đoán kết nối API (Dev)` on the login screen.
- Excluded from production builds by `__DEV__` guard.

---

## 16. Physical Phone Test Procedure

Full procedure documented in Vietnamese in `report/evidence/mobile_physical_1/PHONE_TEST_QUICK_GUIDE_VI.md`:
1. Connect phone and laptop to same Wi-Fi (`Kim Chung 4`).
2. Run `scripts\start-all.ps1` to ensure backend is ready.
3. Run `npm run start:device` to show Metro QR in terminal.
4. In Expo Go on phone: tap `Scan QR` or type `192.168.1.12:8081` into `Enter URL`.
5. Verify app loads and presents Login screen.
6. Verify connectivity using Chrome on phone: `http://192.168.1.12:8080/actuator/health`.
7. Login with demo student credentials: `minh.student@mathvision.local` / `MathVision123!`.

---

## 17. Camera/Photo Permission Procedure

- Upon tapping **`CHỤP BÀI CỦA EM`**, `useCameraPermissions()` checks Android camera authorization.
- If not granted, the app displays the dedicated `permissionContainer` explanation screen with a child-friendly prompt.
- Tapping **`Cho phép mở máy ảnh`** triggers the native Android OS permission dialog (`android.permission.CAMERA`).
- Selecting *"While using the app"* grants permission and opens the live camera view.
- Photo library selection uses `expo-image-picker`, which invokes the native Android photo picker.

---

## 18. Supported First Test Exercise

Recommended baseline test case:
```text
    45
  + 27
  ----
    72
```
- **Structure:** 2-operand vertical addition, natural numbers, 2 digits each.
- **Constraints:** One exercise per image, clear lighting, no finger shadows.
- **Scope limitation:** No fractions, word problems, horizontal expressions, or geometry (unsupported by MVP).

---

## 19. Expected E2E Flow

```text
Phone Camera Capture
  ↓
Privacy Gate (Interactive PII masking box if child face/name visible)
  ↓
Preview Screen (Image orientation check, rotation, optional crop)
  ↓
Processing Screen (POST /api/v1/student/submissions, multipart/form-data)
  ↓
Spring Boot (Stores raw image in MinIO, creates DB record, dispatches to AI)
  ↓
Celery Worker & FastAPI AI Runtime (YOLO token detection, Row grouping)
  ↓
StructuredParser & ArithmeticValidator (Calculates column sums, verifies carries)
  ↓
Spring Callback (/internal/v1/ai/jobs/{id}/complete)
  ↓
Student Mobile Polling (Receives FEEDBACK_READY, navigates to Correct or Error Hint screen)
```

---

## 20. Privacy Limitation

> ⚠️ **CRITICAL PRIVACY NOTICE:**  
> Automatic on-device PII detection is not yet trained or automated. MathVision Kids currently provides a manual client-side interactive PII masking canvas (`src/app/privacy.tsx`).  
> Therefore, physical device testing must be conducted with **controlled test sheets only**.  
> Do **NOT** photograph or upload real child faces, real student names, or school identifiers until automated PII masking has completed formal independent verification.

---

## 21. ADB USB Fallback

- **ADB Status:** `NO` (Android SDK platform-tools / `adb` not in system PATH or local AppData; Wi-Fi LAN is the active primary transport).
- **Fallback Procedure if ADB is installed in the future:**
  1. Enable Developer Options & USB Debugging on the Android phone.
  2. Connect phone to laptop via USB cable and accept RSA fingerprint prompt.
  3. Verify device is recognized: `adb devices`.
  4. Reverse ports:
     ```bash
     adb reverse tcp:8080 tcp:8080
     adb reverse tcp:8081 tcp:8081
     ```
  5. Under this fallback, the app can access `http://127.0.0.1:8080/api/v1` directly through the USB tunnel.

---

## 22. Student Mobile Tests

- **TypeScript Typecheck (`npx tsc --noEmit`):** PASS (0 errors)
- **ESLint (`npm run lint`):** PASS (0 errors, 1 pre-existing warning in `apiClient.ts`)
- **Expo Doctor (`npx expo-doctor`):** 20/21 checks passed (1 expected patch advisory for minor SDK 57 point releases)
- **Local Dev Server Smoke:** PASS (Metro listening on `0.0.0.0:8081`, manifest reachable via LAN IP)
- **API Environment Loading:** PASS (Verified Expo CLI loads `.env.local` before `.env`)

---

## 23. Backend / Stack Status

Verified via `scripts\start-all.ps1`:
- **Docker Infrastructure:**
  - `mathvision-postgres`: Healthy, accepting connections on `127.0.0.1:5432`
  - `mathvision-minio`: Healthy, S3 endpoint `127.0.0.1:9000`, console `9001`
  - `mathvision-redis`: Healthy, port `127.0.0.1:6379`
- **Application Services:**
  - Spring Boot Business API: Running on port `8080` (PID `28656`), `/actuator/health` reports `UP`
  - FastAPI AI Runtime: Running on port `8000` (PID `18392`), `/ready` reports `ready`
  - Celery Worker: Active (PID `27636`), worker pool initialized
  - Teacher Web: Running on port `5173` (PID `18336`)
  - Admin Web: Running on port `5174` (PID `3456`)
- **Overall System Status:** `READY_FOR_DEMO`

---

## 24. Files Modified

| File | Change Description |
|---|---|
| `services/business-api/src/main/resources/application.yml` | Added `address: ${SERVER_ADDRESS:0.0.0.0}` to explicitly bind Tomcat to all network interfaces |
| `package.json` | Added `"start:device": "expo start --lan"` npm script |
| `.env.local` | Created gitignored local environment file specifying `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.12:8080/api/v1` |
| `src/app/dev-demo.tsx` | Added interactive backend connection and environment diagnostic card |
| `src/app/login.tsx` | Added development-only navigation link to diagnostic screen |
| `report/evidence/mobile_physical_1/PHONE_TEST_QUICK_GUIDE_VI.md` | Created concise, numbered Vietnamese guide for the product owner |
| `report/mobile_physical_1_android_setup_and_test_guide.md` | Created this comprehensive audit report |

---

## 25. Owner Actions Required

1. **Verify Windows Wi-Fi Network Profile:**
   - In Windows Settings, ensure connection `Kim Chung 4` is set to **Private network** (or run the optional firewall commands if inbound connections are blocked).
2. **Launch Metro Server:**
   - Run `npm run start:device` in a terminal at `E:\MathVisionKid`.
3. **Connect on Android Phone:**
   - Open Expo Go, tap **Scan QR** (or enter `192.168.1.12:8081` in URL field).
4. **Conduct Test Submission:**
   - Log in with `minh.student@mathvision.local` / `MathVision123!`.
   - Take a clear photo of vertical addition `45 + 27 = 72`.
   - Complete privacy confirmation and submit.
   - Verify terminal feedback screen appears.

---

## 26. Final Assessment

The laptop and mobile codebase are fully prepared and verified up to the network boundary. All local backend services are active, healthy, and accessible via the detected LAN IP `192.168.1.12`. The Student Mobile app is verified for Expo Go on Expo SDK 57, and runtime diagnostic tools are in place.

**Status:** `LAPTOP_SETUP_READY`  
*(Phone on-device testing marked as `PHONE_TEST_REQUIRED` pending owner physical execution)*.
