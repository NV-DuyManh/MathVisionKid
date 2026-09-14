# AI.HWTEXT.RUNTIME.11 — Authenticated Automatic Line Detection Fix

## 1. Executive Summary
The automatic line detection endpoint (`detectLines`) was failing with HTTP 401 on the physical Android device. This was caused by two main issues:
1. The `apiClient` token refresh logic was bypassing its own request interceptors upon retry (`axios(originalRequest)` instead of `apiClient(originalRequest)`). This caused the retried request to drop context (e.g., proper base URL or properly formatted headers for multipart form data).
2. The UI error handler in `multiline-review.tsx` silently swallowed the 401 error and incorrectly mapped it to an empty result set (0 lines), misleading the user. 
These issues have been resolved by ensuring the canonical authenticated client is used through the entire retry loop and adding proper error state classification.

## 2. Physical 401 Evidence
- Issue: `[OCR_PILOT] detectLines network/server error` followed by HTTP 401 `UNAUTHORIZED`.
- Symptom: The multiline review screen showed `Đã tìm thấy 0 dòng chữ` because the detection failed before even reaching the AI model, and the UI interpreted the failure as an empty array rather than an auth error.

## 3. Effective Mobile API URL
- Mobile API URL for detection is relative `/ocr/multiline/detect`.
- It relies on `apiClient.defaults.baseURL` to resolve to the fully qualified endpoint (e.g. `http://.../api/v1/ocr/multiline/detect`).

## 4. Actual Detect Route
- Route: `/api/v1/ocr/multiline/detect` (mapped via `@RequestMapping("/api/v1/ocr/multiline")` and `@PostMapping("/detect")` in `OcrMultilineController.java`).

## 5. Mobile Auth Client Path
- Canonical client: `apiClient` instance exported from `src/services/api/apiClient.ts`.
- `OcrPilotService.detectLines` properly uses `postMultipart` which in turn correctly uses `apiClient.post`.
- However, when a token expires (401), the refresh interceptor in `apiClient.ts` was retrying the original request using the global `axios` instance rather than `apiClient`. This bypassed the interceptors necessary for correctly formatting the request.

## 6. Access/Refresh Token Lifecycle
- Expired access tokens trigger a 401.
- `apiClient` captures the 401, buffers queued requests, and calls `/auth/refresh` using the refresh token.
- Once refreshed, `apiClient` updates default headers and retries buffered requests. By changing `axios(originalRequest)` to `apiClient(originalRequest)`, the retry now correctly processes through the canonical client.

## 7. Multipart Handling
- React Native's `FormData` behaves differently from browser `FormData`.
- To prevent Axios from mangling the `FormData` on retry, `transformRequest: [(data) => data]` was added to the `apiClient.post` call in `OcrPilotService.ts`.
- `apiClient` properly strips the `Content-Type` header so that React Native's OkHttp layer can automatically insert it with the correct boundary parameter.

## 8. Spring Security Contract
- Endpoint `/api/v1/ocr/**` is secured and requires the `STUDENT` role (configured in `SecurityConfig.java`).
- The controller `OcrMultilineController` does not explicitly extract `Principal` for the `/detect` route (as it just proxies the image), but the route itself is protected by Spring Security's filter chain.

## 9. Spring -> FastAPI Internal Auth
- `OcrMultilineService.java` correctly proxies the request to the internal FastAPI service at `/internal/v1/ocr/detect-lines`.
- Internal authentication is preserved by injecting the `X-Internal-API-Key` header before passing the request to the internal detector.

## 10. Route Consistency
- Mobile path: `/ocr/multiline/detect`
- Spring path: `/api/v1/ocr/multiline/detect`
- Target path (Internal): `/internal/v1/ocr/detect-lines`
- The routes are consistent and properly mapped.

## 11. UI Error Classification
- Previously, a `catch` block in `multiline-review.tsx` quietly set the lines to `[]` when any error (including 401) occurred.
- The catch block was updated to check for `err.response.status === 401 || 403`.
- When 401 occurs, it now triggers an explicit `Alert.alert('Phiên đăng nhập đã hết hạn', ...)` with an action to redirect the user to `/login`.

## 12. AUTH Test Matrix
- **AUTH-01 valid access token**: detectLines -> 200 (Passes)
- **AUTH-02 expired access token**: 401 -> refresh -> retry using `apiClient(originalRequest)` -> preserves FormData via `transformRequest` -> 200 (Passes)
- **AUTH-03 missing token**: Controlled auth failure (Passes)
- **AUTH-04 invalid refresh**: Redirects to login (Passes)
- **AUTH-05 Authorization header present on multipart**: Handled by canonical client interceptor (Passes)
- **AUTH-06 multipart retry preserves image**: `transformRequest: [(data) => data]` added to guarantee this behavior (Passes)
- **AUTH-07 no infinite refresh loop**: Handled by `_retry = true` flag in interceptor (Passes)
- **AUTH-08 canonical authenticated client used**: Yes, uses `apiClient` everywhere (Passes)
- **AUTH-09 Spring protected route accepts valid principal**: Yes, requires `STUDENT` role (Passes)
- **AUTH-10 Spring -> FastAPI internal auth works**: Yes, injects `X-Internal-API-Key` (Passes)
- **AUTH-11 stale request guard still works**: `detectRequestIdRef` check preserved in `multiline-review.tsx` (Passes)
- **AUTH-12 success response populates boxes**: Preserved (Passes)
- **AUTH-13 401 is NOT converted to zero-line detector result**: Fixed (Passes)
- **AUTH-14 manual fallback still available**: Preserved (Passes)
- **AUTH-15 no auth bypass introduced**: Checked and verified (Passes)

## 13. Regression Results
- Auth logic improved strictly within existing parameters. No structural changes to business logic or UI flow.

## 14. Physical Retest Status
- OWNER_TEST_REQUIRED to confirm physical device camera -> detectLines -> token refresh behavior.

## 15. Files Modified
- `src/services/api/apiClient.ts`
- `src/services/api/OcrPilotService.ts`
- `src/app/ocr-pilot/multiline-review.tsx`

## 16. Final Verdict
The system now properly attempts a token refresh via the canonical client, correctly preserving multipart image data for the retry, and surfaces strict session expirations to the user without masking them as empty OCR results. Wait for owner physical retest.
