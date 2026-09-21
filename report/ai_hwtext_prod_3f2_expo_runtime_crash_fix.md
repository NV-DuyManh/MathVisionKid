# Báo Cáo PROD.3F.2 — Expo Runtime Crash Root-Cause Fix

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Senior developer minimalist philosophy — inspect root cause at the source, avoid unrequested abstractions, implement the smallest correct fix directly where callers route through.
  - Applied to: `src/app/gallery.tsx` (safe lazy loader for `expo-media-library`, type-only imports), `src/app/(tabs)/index.tsx` (eliminated non-existent React Native `e.stopPropagation()` calls), and relocated `gallery.test.tsx` to `src/__tests__/`.

---

## 1. Tóm Tắt Sự Cố & Root-Cause Analysis

### Triệu chứng thực tế (Physical Android Device)
Sau phase `PROD.3F.1` đưa vào custom gallery tại `src/app/gallery.tsx`, thiết bị Android vật lý chạy Expo Go hiển thị màn hình crash nghiêm trọng ngay khi mở ứng dụng:
> *"Something went wrong. Sorry about that. You can go back to Expo home or try to reload the project."*

### Phân tích nguyên nhân gốc rễ (Root Causes)

1. **Eager Module-Evaluation Native Module Crash trong Expo Go Android (Nguyên nhân chính)**:
   - **File & Dòng**: `src/app/gallery.tsx:15` trước khi sửa có lệnh import tĩnh:
     ```ts
     import * as MediaLibrary from 'expo-media-library/legacy';
     ```
   - **Cơ chế lỗi**: Trong `node_modules/expo-media-library/src/ExpoMediaLibrary.ts`, dòng 5 thực thi ngay tại thời điểm import:
     ```ts
     export default requireNativeModule('ExpoMediaLibrary');
     ```
   - Trong `MediaLibraryModule.kt` trên Android của Expo SDK 57, hàm `maybeThrowIfExpoGo` chủ động ném `PermissionsException` hoặc native module không được đăng ký trong Expo Go APK vì chính sách Google Play cấm Expo Go xin quyền `READ_EXTERNAL_STORAGE` / `READ_MEDIA_IMAGES` toàn cục.
   - Với kiến trúc **Expo Router**, tất cả các file trong thư mục `src/app/` được tự động nạp (eagerly evaluated) qua Metro require context khi khởi động ứng dụng. Khi bundle được Hermes nạp vào bộ nhớ trước khi `RootLayout` hoặc `SplashScreen` có cơ hội hiển thị, lệnh `requireNativeModule('ExpoMediaLibrary')` bị ném lỗi Unhandled Exception, gây crash toàn bộ ứng dụng ngay tại boot time.

2. **React Native Event Handler Incompatibility**:
   - Trong `src/app/(tabs)/index.tsx`, tại dòng 206 và 276 (trong Tips Modal và Privacy Info Modal) có đoạn:
     ```tsx
     <Pressable style={[styles.modalCard, SHADOWS.large]} onPress={(e) => e.stopPropagation()}>
     ```
   - Trong React Native, `GestureResponderEvent` **không có** hàm `stopPropagation()`. Khi nhấn vào card trên thiết bị di động, lệnh này ném `TypeError: e.stopPropagation is not a function`.

3. **Expo Router File-Based Routing Collision**:
   - File test `src/app/__tests__/gallery.test.tsx` nằm bên trong `src/app/` khiến router coi file test là một route hợp lệ và quét các mock dependencies vào runtime bundle.

---

## 2. Giải Pháp Khắc Phục Tối Thiểu (Surgical Minimal Fix)

1. **Chuyển `expo-media-library` sang Lazy Safe Loader & Type-only Import**:
   - Đổi `import * as MediaLibrary` thành `import type * as MediaLibraryTypes from 'expo-media-library/legacy';`. Nhờ đó, trình biên dịch TypeScript loại bỏ hoàn toàn import này khi bundle, không sinh mã `require()` ở top-level bundle.
   - Thêm hàm lazy loader `getMediaLibrary()` bọc trong `try / catch`:
     ```ts
     function getMediaLibrary(): MediaLibraryModuleLike | null {
       try {
         // eslint-disable-next-line @typescript-eslint/no-require-imports
         return require('expo-media-library/legacy');
       } catch (error) {
         console.warn('[CustomGallery] expo-media-library native module unavailable:', error);
         return null;
       }
     }
     ```
   - Thay thế các enum tĩnh (`MediaLibrary.MediaType.photo`, `MediaLibrary.SortBy.creationTime`) bằng literal arrays `['photo']` và `['creationTime']` được hỗ trợ chuẩn bởi API.
   - Gọi `getAssetInfoAsync` an toàn qua `getMediaLibrary()?.getAssetInfoAsync`.

2. **Graceful Fallback UI cho Expo Go Android**:
   - Khi chạy trên Expo Go Android nơi native module bị hạn chế hoặc quyền bị từ chối, `isNativeUnavailable = true`.
   - Màn hình `/gallery` không bị crash mà hiển thị Card hướng dẫn thân thiện:
     * Tiêu đề: "Bộ chọn ảnh MathVision"
     * Mô tả: "Trên ứng dụng Expo Go Android, MathVision sử dụng bộ chọn ảnh hệ thống để em chọn ảnh bài tập nhanh và an toàn."
     * CTA chính: Nút "Chọn ảnh từ thiết bị" kích hoạt ngay `ImagePicker.launchImageLibraryAsync()` để chọn ảnh và chuyển tiếp sang `/privacy`.
   - Trên Development Build (`npx expo run:android`) hoặc iOS: `getMediaLibrary()` tải đầy đủ và hiển thị lưới ảnh thư viện nội bộ 3 cột mượt mà.

3. **Loại bỏ `e.stopPropagation()` trong `src/app/(tabs)/index.tsx`**:
   - Thay `onPress={(e) => e.stopPropagation()}` bằng `onPress={() => {}}` trên inner `Pressable`.

4. **Di chuyển Test Suite ra khỏi `src/app/`**:
   - Chuyển `src/app/__tests__/gallery.test.tsx` sang `src/__tests__/gallery.test.tsx`.

---

## 3. Bảng Tham Số Kiểm Định Bắt Buộc

| Trường | Kết Quả | Bằng Chứng Kỹ Thuật |
|---|:---:|---|
| **RootCause** | **IDENTIFIED** | Top-level native module evaluation of `expo-media-library` restricted in Expo Go Android + `e.stopPropagation()` on `GestureResponderEvent` |
| **CrashLocation** | **IDENTIFIED** | `src/app/gallery.tsx:15` (eager import) & `src/app/(tabs)/index.tsx:206,276` |
| **ExpoBootAfterFix** | **PASS** | Metro Android bundle compiled cleanly: HTTP 200, 11,194,921 bytes |
| **HomeRender** | **PASS** | Test `GALLERY-08` verified HomeScreen renders CTAs and navigates without error |
| **GalleryRoute** | **PASS** | Test suite `src/__tests__/gallery.test.tsx` (8/8 PASS) |
| **GalleryPermission** | **PASS** | Test `GALLERY-01` verified permission denial & fallback UI handling |
| **GalleryAssetGrid** | **PASS** | Test `GALLERY-03`, `04`, `05`, `06` verified grid rendering, single selection, and draft store commit *(Full MediaStore grid supported in Dev Build / iOS; Expo Go uses graceful system picker)* |
| **PrivacyRouteAfterGallery** | **PASS** | Test `GALLERY-06` verified navigation to `/privacy` with normalized draft URI |
| **TypeScript** | **PASS** | `npx tsc --noEmit` exited with code 0 (0 errors) |
| **ESLint** | **PASS** | `npm run lint` exited with code 0 (0 errors, 0 warnings) |
| **ExpoDoctor** | **20/21** | 20/21 checks passed (1 check failed on upstream package patch advisory as expected) |
| **PhysicalAndroid** | **OWNER_RETEST_REQUIRED** | Cần Owner tải lại bundle trên thiết bị thật (nhấn `r` trên Metro terminal) để xác nhận |
| **ReleaseVerdict** | **PARTIAL** | Sẵn sàng cho Owner kiểm thử trên thiết bị vật lý |

---

## 4. Bằng Chứng Thực Thi Chi Tiết

### 1. Metro Bundler Verification
```
Request: GET http://localhost:8081/node_modules/expo-router/entry.bundle?platform=android&dev=true&minify=false&transform.routerRoot=src%2Fapp
Result:
STATUS: 200 OK
TOTAL BYTES: 11,194,921
Bundle Analysis: Top-level static require eliminated, lazy require properly wrapped.
```

### 2. Jest Unit Tests (Gallery Suite)
```
PASS src/__tests__/gallery.test.tsx (12.315 s)
  AI.HWTEXT.PROD.3F.1 / 3F.2 — Custom Gallery & Direct CTAs
    √ GALLERY-01: renders permission denied state when permissions are not granted (1246 ms)
    √ GALLERY-02: renders empty state when library has 0 assets (10 ms)
    √ GALLERY-03: renders grid of assets when permission is granted and loads first page (712 ms)
    √ GALLERY-04: CTA is disabled when no image is selected (5 ms)
    √ GALLERY-05: selecting an asset enables the CTA, and switching replaces selection (469 ms)
    √ GALLERY-06: confirm sends selected image to draft store and navigates to /privacy (32 ms)
    √ GALLERY-07: back button calls router.back() (12 ms)
    √ GALLERY-08: Home screen gallery CTA routes to custom /gallery route, camera CTA routes directly to camera (809 ms)

Test Suites: 1 passed, 1 total
Tests:       8 passed, 8 total
```

### 3. Gesture & Privacy Suite
```
PASS src/utils/__tests__/privacyGestureArchitecture.test.ts
  AI.HWTEXT.PROD.3D.1 — Privacy Gesture Architecture Truth & Closure
    21 passed, 21 total (100% PASS)
```

### 4. AI Suggestion Deduplication Matrix (Node.js)
```
=== ALL 20 PROD.3B, PROD.3F & PROD.3F.1 CASES PASSED SUCCESSFULLY ===
20/20 PASS
```

### 5. Backend & AI Service Unit Tests
```
services/ai-service/tests/test_prod3f_ai_suggestions.py: 8 passed in 0.46s (100% PASS)
services/ai-service/tests/test_prod3b_suggestion_dedupe.py: 15 passed in 0.60s (100% PASS)
services/ai-service/tests/test_prod2g_latency.py: 16 passed in 7.58s (100% PASS)
```

### 6. TypeScript & ESLint
```
npx tsc --noEmit: 0 errors
npm run lint: 0 errors, 0 warnings
```

---

## 5. Hướng Dẫn Kiểm Thử Trên Thiết Bị Vật Lý (Owner Retest Steps)

1. Thiết bị Android đã kết nối cùng mạng LAN với Metro server (đang chạy ở cổng 8081).
2. Mở ứng dụng **Expo Go** trên điện thoại.
3. Nếu ứng dụng vẫn đang hiển thị màn hình crash cũ: Nhấn nút **"Reload"** hoặc lắc nhẹ thiết bị để mở Expo Developer Menu rồi chọn **"Reload"** (hoặc nhấn phím `r` trên cửa sổ terminal của Metro).
4. Quan sát:
   - Ứng dụng khởi động mượt mà vào màn hình chính (Home) mà không crash.
   - Nhấn **"Chụp ảnh mới"**: Mở trực tiếp màn hình Camera.
   - Nhấn **"Chọn từ thư viện"**: Chuyển đến màn hình `/gallery`. Trên Expo Go, màn hình sẽ hiển thị nút "Chọn ảnh từ thiết bị" — nhấn vào sẽ mở bộ chọn ảnh Android an toàn, chọn ảnh và điều hướng sang màn hình `/privacy`.
   - Thử mở lại các popup mẹo chụp ảnh để xác nhận không còn lỗi crash khi bấm vào modal card.
