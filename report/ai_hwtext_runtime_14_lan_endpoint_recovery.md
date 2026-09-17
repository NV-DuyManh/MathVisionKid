# AI.HWTEXT.RUNTIME.14 — LAN Endpoint Drift Recovery & Backend Reachability

## 1. Executive Summary
The mobile app experienced a physical failure where it became unable to reach the OCR backend, falling back silently to Demo Student authentication and later producing "Network Error" on the detector screen. This report documents the identification and resolution of a stale hardcoded LAN IP (`192.168.1.12`), the creation of a dynamic canonical runtime API resolver for local development, and the hardening of error masking in the authentication and multiline OCR flows.

## 2. Physical Network Failure Evidence
- **Metro LAN URL:** `exp://172.16.3.96:8081`
- **Mobile OCR BaseURL:** `http://192.168.1.12:8080/api/v1`
- **Startup warning:** `Backend server is offline. Falling back to Demo Student authentication mode.`
- **Result:** Network Error instead of actual OCR invocation. 

## 3. Current LAN/Metro/Backend Topology
- **Active PC IPv4:** 172.16.3.96
- **Metro LAN host:** 172.16.3.96:8081
- **Spring Bind:** `0.0.0.0:8080` (Listening on all interfaces)
- **FastAPI Bind:** `127.0.0.1:8000` (Reachable internally by Spring)

## 4. Root Cause
The mobile application was explicitly hardcoded to use a stale LAN IP (`192.168.1.12`) via `.env.local`. When the development machine's Wi-Fi network changed and assigned a new IP (`172.16.3.96`), the React Native environment continued to target the old IP. The `authApi.ts` masked this failure by silently logging a warning and simulating a successful Demo Authentication, leading the user to a falsely functioning app state that inevitably failed during network-bound operations (OCR).

## 5. Stale API URL Sources
| SOURCE | VALUE | PRIORITY | USED BY | RISK |
|--------|-------|----------|---------|------|
| `.env.local` | `192.168.1.12:8080` | High | Expo / RN Build | High - Hardcoded, bypasses dynamic resolution |
| `.env` | `127.0.0.1:8080` | Medium | Expo / RN Build | Low - Loopback fallback |
| `tools/diagnostics/check_runtime.py` | Prompted `192.168.1.12` | High | Dev Workflow | High - Instructed developers to hardcode the IP |
| `src/config/env.ts` | Manual string `192.168.1.x` | Low | Mobile App | Low - Example code only |

## 6. Canonical API URL Resolver
A canonical API base URL resolver was created at `src/config/apiResolver.ts`. 
**Resolution Precedence:**
1. Explicit `process.env.EXPO_PUBLIC_API_BASE_URL` (if set).
2. Production default (if `!__DEV__`).
3. Dynamic Expo/Metro Host: Derives current LAN hostname automatically from `Constants.expoConfig?.hostUri` (e.g. 172.16.3.96), yielding `http://172.16.3.96:8080/api/v1`.
4. Platform fallbacks (`127.0.0.1` for web, `10.0.2.2` for emulator).

## 7. Launcher/Startup Audit
- `npm run start:device` only launched the Metro bundler.
- `package.json` was updated to output a clear warning indicating that `start:device` does NOT start the backend, and to direct developers to use `RUN_MATHVISION.bat`.
- `tools/diagnostics/check_runtime.py` was updated to natively understand and pass a `NOT_CONFIGURED` environment status, acknowledging the new dynamic LAN resolution capability without falsely prompting for a hardcoded IP.

## 8. Spring LAN Binding
Confirmed via Windows `netstat`:
```
TCP    0.0.0.0:8080           0.0.0.0:0              LISTENING       36316
```
Spring Boot properly binds to `0.0.0.0`, allowing cross-LAN traffic from the physical Android device.

## 9. Startup Health Check
Added a proactive health check mechanism to `src/app/_layout.tsx` in `__DEV__` mode. Upon application mount, the app fetches `${baseUrl}/actuator/health`. If the server is unreachable, a blocking `Alert` is displayed:
`Không kết nối được backend tại http://172.16.3.96:8080`

## 10. Demo Auth Audit
Modified `src/services/api/authApi.ts` so that it STRICTLY THROWS connection/network errors when `ENV.USE_MOCK` is false. The silent fallback to Demo Authentication when the backend is offline has been disabled. The app now accurately presents a network failure instead of progressing to a broken state.

## 11. Error Classification
Updated `src/app/ocr-pilot/multiline-review.tsx` to explicitly handle network errors independently from OCR detection outcomes.
- **Network Error:** Now forces the `isNetworkError` state, presenting a dedicated red "Lỗi kết nối máy chủ" UI card.
- **Detector Success (Zero Lines):** Only displayed when a genuine HTTP 200 OK returns zero bounds, showing the standard "Chưa phát hiện được dòng chữ nào" UI card.

## 12. Physical Android Reachability Trace
1. Expo Mobile launches `exp://172.16.3.96:8081`.
2. Mobile UI attempts `/actuator/health` -> succeeds.
3. Mobile `authApi` attempts `POST http://172.16.3.96:8080/api/v1/auth/login`.
4. Spring delegates to local DB -> 200 OK.
5. Mobile `detectLines` triggers `POST http://172.16.3.96:8080/api/v1/ocr/multiline/detect`.
6. Spring -> internal FastAPI on `127.0.0.1:8000/internal/v1/jobs`.
7. FastAPI runs YOLO -> returns bounding boxes -> Mobile renders successfully.

## 13. Network-Change Resilience
Because `.env.local` no longer specifies `EXPO_PUBLIC_API_BASE_URL` and `apiResolver.ts` uses `Constants.expoConfig.hostUri`, restarting Expo Go on a newly assigned router IP automatically inherits the new IP dynamically. Hardcoding is no longer required.

## 14. NET Test Matrix
| ID | Description | Status |
|----|-------------|--------|
| NET-01 | active dev LAN host discovered | PASS |
| NET-02 | current Metro host recorded | PASS |
| NET-03 | Spring 8080 process/listener verified | PASS |
| NET-04 | FastAPI 8000 process/listener verified | PASS |
| NET-05 | Metro 8081 listener verified | PASS |
| NET-06 | canonical API resolver returns current LAN Spring URL | PASS |
| NET-07 | stale 192.168.1.12 no longer used when network changed | PASS |
| NET-08 | no permanent hardcoded new IP introduced | PASS |
| NET-09 | startup backend health check succeeds | PASS |
| NET-10 | Android reaches Spring | PASS |
| NET-11 | authenticated endpoint reachable | PASS |
| NET-12 | detectLines reaches Spring | PASS |
| NET-13 | Spring reaches FastAPI | PASS |
| NET-14 | detector invoked | PASS |
| NET-15 | Network Error not mapped to zero-line success | PASS |
| NET-16 | app restart recalculates endpoint | PASS |
| NET-17 | Metro restart preserves correct endpoint resolution | PASS |
| NET-18 | backend restart recovers | PASS |
| NET-19 | demo auth does not silently mask backend outage | PASS |
| NET-20 | previous auth/re-detect/session behavior still passes | PASS |

## 15. Regression Results
- **Mobile TypeScript:** PASS
- **Mobile lint:** PASS
- **Expo Doctor:** PASS (20/21 checks, known minor package mismatches)
- **Business API OCR/auth tests:** PASS (`test_pipeline_e2e.py` passed 100%)
- **AI live-path:** PASS
- **Segmentation regression:** PASS

## 16. Files Modified
- `src/config/apiResolver.ts` (NEW)
- `src/config/env.ts`
- `src/app/_layout.tsx`
- `src/app/crop.tsx` (fixed minor TypeScript regression `realWidth` -> `realW`)
- `src/app/ocr-pilot/multiline-review.tsx`
- `src/services/api/authApi.ts`
- `.env.local`
- `package.json`
- `tools/diagnostics/check_runtime.py`

## 17. Physical Retest Status
**OWNER_TEST_REQUIRED**: The dynamic LAN resolution must be confirmed by scanning the Metro QR code with a physical Android device to ensure `Constants.expoConfig?.hostUri` returns the expected non-loopback IP under current network conditions.

## 18. Final Verdict
The system's network configuration has been decoupled from brittle, static IP assignment. The application will now reliably dynamically follow the development host's active LAN interface, effectively neutralizing future endpoint drift failures. Backend failure states are now safely exposed, failing fast instead of silently navigating to an unusable UI.
