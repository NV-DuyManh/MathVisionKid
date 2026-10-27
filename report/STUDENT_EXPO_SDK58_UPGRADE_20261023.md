# Nâng Student lên Expo SDK 58 — 23/10/2026

## Kết quả

Dự án Student đã nâng từ Expo 57.0.19 lên **58.0.17**, tương thích dòng SDK 58 mà Expo Go Android trong ảnh của chủ dự án yêu cầu. Máy chủ phát triển đang chạy tại cổng 8081; kiểm tra manifest qua LAN trả về `sdkVersion: 58.0.0`, đúng slug MathVisionKid. QR mới được tạo từ manifest đang chạy, không tự đoán địa chỉ; đã giải mã lại ảnh QR để đối chiếu URL.

## Thay đổi

- Đồng bộ thư viện native theo `expo install --fix`: React Native 0.88.0, React/React DOM 19.3.0, Expo Router 58.0.25, Audio 58.0.10, Video 58.0.12 và các gói camera, file, ảnh, gesture, worklets tương ứng. Bổ sung plugin mà SDK yêu cầu trong `app.json`.
- Ghim React/React DOM 19.3.0 cho Teacher, Admin, Portal để các thư viện dùng chung trong monorepo không nạp React 19.3.1 song song với bản Student. Không thay đổi màn hình của ba ứng dụng này; cả ba đã build lại thành công.
- Cài sạch và tạo lại lockfile, sau đó dedupe; không dùng `--force`, `--legacy-peer-deps`, hoặc tắt kiểm tra dependency. Bản sao manifests/lockfile trước nâng nằm trong thư mục báo cáo; thư viện cũ được chuyển vào `infra/local-runtime/sdk58-reinstall/` (đã được Git ignore).
- Sửa cache WAV/MP4 sang `File.writeSync()`. SDK 58 đổi `File.write()` thành bất đồng bộ; hợp đồng hiện tại cần ghi xong trước khi trả URI cho trình phát. Có kiểm thử cho cả hai định dạng.
- Chuyển tab bar sang `emitter`/`navigateToTab`, giữ quyền ngăn sự kiện đổi tab, điều khiển bàn phím và hiệu ứng hover. Bổ sung `useServerDocumentContext` cho HTML xuất tĩnh để giữ tài nguyên và script hydration.
- Chuyển refs sang instance types theo API TypeScript mới, giữ nguyên giá trị bố cục. Chuyển reset trạng thái thử lại hình vào thao tác bấm nút theo quy tắc React mới.
- Cập nhật Jest 30/jest-expo 58 và renderer khớp React. Mô phỏng I/O font native trong môi trường unit test; không mô phỏng thay cho phép thử âm thanh thật trên điện thoại. Hai bộ Node ESM chạy bằng `test:contracts`; ma trận gợi ý được chuyển sang test TypeScript của Jest, giữ nguyên các khẳng định.
- Launcher từ chối in QR nếu manifest là SDK cũ; cập nhật tài liệu cài đặt hiện hành và yêu cầu Node.
- Metro bỏ qua `infra/local-runtime`, tránh quét dữ liệu dịch vụ và các bản sao thư viện dự phòng khi khởi động. Kiểm thử cấu hình xác nhận mã Student và font vẫn được đưa vào.

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Expo Doctor | **20/20 đạt**, không duplicate native dependencies |
| Expo install --check | Phiên bản phù hợp SDK 58 |
| Jest toàn bộ Student | **74 suite, 893 test đạt** |
| Node web-auth/privacy contracts | **8 test đạt** |
| QR launcher regression | Đạt: đúng dự án/host/SDK; từ chối SDK cũ hoặc thiếu version |
| TypeScript | `tsc --noEmit` đạt |
| Student lint | 0 lỗi; 2 cảnh báo `no-unused-expressions` có sẵn trong `cropRotation.web.ts` |
| Expo export | Android + iOS + web tĩnh, **32 route** |
| Teacher/Admin/Portal + packages build | Đạt, dùng cấu hình URL production đã có trong script deploy; không deploy |
| Manifest máy chủ thật | Android/LAN, `58.0.0`, MathVisionKid |
| Ảnh QR | Đã tạo và giải mã lại đúng URL máy chủ |
| File cần giữ nguyên | privacy.tsx, crop.tsx, AppHeader.tsx, AppButton.tsx, theme.ts khớp SHA-256 baseline |
| Git | `diff --check` đạt; không commit/push |

Bằng chứng chi tiết trong `student-sdk58-upgrade-20261023/`: `doctor.log`, `expo-check.log`, `jest-results.json`, `node-contracts.log`, `qr-tests.log`, `types-final.log`, `lint.log`, `web-builds.log`, `export.log`, `manifest-smoke.json`, `protected-files.json`, `expo-go-sdk58-qr.png`.

## Giới hạn xác nhận

Đây là kiểm tra mã, dependency, đóng gói và máy chủ đang chạy. Không có điện thoại Android kết nối để thao tác trực tiếp: chưa chứng minh nghe được tiếng, quyền mic/camera hoặc cảm ứng trên thiết bị thật. Quét QR mới bằng Expo Go SDK 58, cùng Wi-Fi, rồi kiểm tra ghi câu hỏi → nghe lại → gửi → nghe lời giải thích. Backend và model không thay đổi trong lượt nâng SDK này.

Thao tác dọn thư viện dự phòng cuối lượt bị bộ duyệt tự động từ chối với thông báo `blocked by policy`, không nêu lý do chi tiết hơn. Không thực hiện lại bằng cách khác; thư mục dự phòng trong runtime vẫn giữ nguyên. Thao tác này không thay đổi kết quả kiểm thử hoặc mã đang chạy.

## Tài liệu đối chiếu

- [Hướng dẫn nâng Expo](https://docs.expo.dev/workflow/upgrading-expo-sdk-walkthrough/)
- [SDK 58 release notes](https://expo.dev/changelog/sdk-58)
- [Router 57 → 58](https://docs.expo.dev/router/migrate/sdk-57-to-58/)
- [Expo SDK 58 reference](https://docs.expo.dev/versions/v58.0.0/)

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa tương thích trên hệ thống hiện tại, tránh thêm thư viện hay đổi UI ngoài phạm vi nâng SDK.
  - Applied to: dependency alignment, cache media, launcher và kiểm tra hồi quy.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: chuyển API React/React Native và Router trong ứng dụng hiện có.
  - Applied to: refs, keyboard/hover, khởi động app, tab events và web hydration.
