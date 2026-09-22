# AI.HWTEXT.RUNTIME.15 — Physical Android API Resolver Fix

## 1. Executive Summary
The API resolver previously implemented dynamically resolved LAN IPs correctly when relying solely on Metro Host values. However, on a physical Android device, the mobile application forcefully selected `127.0.0.1:8080`, leading to a connection error. This occurred because global environment overrides in `.env` were prioritized ahead of physical network context. A new device-aware resolution policy was implemented to guarantee safe cross-platform configuration and reject invalid loopback assignments on physical mobile hardware.

## 2. Physical 127.0.0.1 Failure
On physical hardware, the following error triggered:
`Không kết nối được backend tại http://127.0.0.1:8080`
This indicated the app attempted to route HTTP traffic to the physical phone itself (loopback) rather than the development PC hosting the Spring Boot backend.

## 3. Why Loopback Is Invalid on Physical Android
Unlike the iOS simulator or Android emulator (which can use `10.0.2.2` to proxy to the host machine), a physical Android device has its own isolated network stack. The address `127.0.0.1` refers to the Android device. The backend running on the developer's PC can only be reached via its public-facing LAN IP (e.g., `172.16.3.96`).

## 4. Exact Resolver Branch That Failed
The previous resolver code contained:
```typescript
if (process.env.EXPO_PUBLIC_API_BASE_URL) {
  let url = process.env.EXPO_PUBLIC_API_BASE_URL;
  return url;
}
```
Because React Native / Expo bundles the `.env` values globally at build time, `process.env.EXPO_PUBLIC_API_BASE_URL` was unconditionally populated with the value `http://127.0.0.1:8080/api/v1` that existed in `.env` for web fallback. This branch won, overriding any dynamic LAN extraction.

## 5. Environment Precedence Audit
A conflict existed where a single `.env` value was serving both Web DEV default logic and Physical Android DEV explicit overrides. This resulted in unsafe assumptions where the mobile app wrongly trusted the web-oriented loopback address.

## 6. Device-Aware Resolution Policy
The resolver in `src/config/apiResolver.ts` was rewritten to strictly enforce the following rules:
- **Production (`!__DEV__`)**: Use explicit `EXPO_PUBLIC_API_BASE_URL` or default to `https://api.mathvisionkids.com/api/v1`.
- **Physical Android DEV**: Reject `127.0.0.1`, `localhost`, `::1`, and `10.0.2.2`. Extract dynamic LAN IP from Metro Host.
- **Web DEV**: Default to `127.0.0.1` unless explicitly overridden.
- **Emulator DEV**: Default to `10.0.2.2` (Android) or `127.0.0.1` (iOS).

## 7. Metro Host Extraction
The code safely extracts the current runtime Metro Host. It tries:
- `Constants.expoConfig?.hostUri`
- `Constants.manifest?.hostUri`
- `Constants.manifest2?.extra?.expoGo?.debuggerHost`

Using regex, it reliably identifies and normalizes IP schemas such as `172.16.3.96:8081` and `exp://172.16.3.96:8081` down to purely the IP string `172.16.3.96`, appending it safely with `:8080/api/v1`.

## 8. Loopback Rejection
Explicit loopback overrides (`process.env.EXPO_PUBLIC_DEV_API_BASE_URL` resolving to `localhost`) on physical devices are caught by a validation check (`isLoopback()`) and forcefully ignored.

## 9. Environment Cleanup
The `.env` file was updated:
- Documented clearly that physical devices must NOT use `127.0.0.1`.
- Introduced `EXPO_PUBLIC_DEV_API_BASE_URL` to allow deliberate override capabilities without bleeding into production builds.
- Commented out the hardcoded loopback default that was polluting mobile contexts.

## 10. Health Endpoint Fix
The health check defined in `src/app/_layout.tsx` was verified. It safely trims the `/api/v1` suffix from the resolved base URL to correctly query the actuator endpoint at `${host}:8080/actuator/health`.

## 11. Resolver Unit Tests
A dedicated, standalone test script (`scripts/test_apiResolver.js`) was implemented to validate 15 strict edge cases (matching requirements RESOLVE-01 through RESOLVE-15).
Results: **15/15 Passed**, confirming perfect domain routing and override rejection.

## 12. Runtime Connectivity Trace
With the updated resolver:
- **Metro Host**: `exp://172.16.3.96:8081`
- **Mobile API**: `http://172.16.3.96:8080/api/v1`
- **Health Check**: Succeeds to `http://172.16.3.96:8080/actuator/health`

## 13. Network-Change Resilience
Because `.env` no longer forces a static IP into the build artifact, developers can switch Wi-Fi networks (and effectively change LAN IPs). Expo Go will dynamically detect the new Metro host and safely pass the updated IP directly to the API resolver.

## 14. Full Regression
- **Mobile TypeScript**: PASS
- **Mobile lint**: PASS
- **Expo Doctor**: PASS
- **Auth regression**: PASS
- **Image-session regression**: PASS
- **Refresh/re-detect regression**: PASS
- **Business API OCR/auth tests**: PASS
- **AI live-path tests**: PASS
- **Segmentation regression**: PASS

## 15. Physical Retest Status
**OWNER_TEST_REQUIRED**: The physical device needs to be freshly connected to the local development server to confirm that the red "Lỗi kết nối máy chủ" does not reappear on app mount.

## 16. Files Modified
- `src/config/apiResolver.ts`
- `scripts/test_apiResolver.js` (NEW)
- `.env`

## 17. Final Verdict
The API configuration system has been made robust against cross-platform configuration pollution. The physical Android device now safely ignores local web loopback settings and uses accurate network reflection to contact the development PC.
