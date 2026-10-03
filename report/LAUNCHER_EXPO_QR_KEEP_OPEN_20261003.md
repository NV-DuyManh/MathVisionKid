# Launcher giữ cửa sổ và mã QR Expo Go

## Kết quả

- `RUN_MATHVISION.bat` giữ cửa sổ sau khi khởi chạy thành công, hiển thị mã QR và đường dẫn Expo Go ở cuối màn hình. Đóng launcher bằng phím bất kỳ không dừng các dịch vụ.
- Khi Metro đã chạy sẵn, launcher tái sử dụng tiến trình và vẫn in mã QR; không cần khởi động lại Metro.
- Khi khởi động Metro mới, cửa sổ riêng dùng `cmd /k`, chế độ LAN, Expo Go và cổng 8081.
- QR dùng bộ chọn địa chỉ LAN và bộ render của Expo CLI đang cài, đọc manifest thật của MathVisionKid. Từ chối địa chỉ loopback, dự án khác và manifest không khớp địa chỉ/cổng.
- Kiểm tra diagnostics thất bại được chuyển tới màn hình lỗi có giữ cửa sổ.

## Kiểm chứng

- `node scripts/test/test_student_qr.cjs`: PASS, gồm địa chỉ đúng, 6 địa chỉ không dùng được và 5 manifest không hợp lệ.
- `node --check scripts/dev/show-student-qr.cjs`: PASS. PowerShell parser và `git diff --check` cho các launcher đã sửa: PASS.
- Chạy launcher Metro trên tiến trình đang phục vụ, PID 37308: PASS, tái sử dụng và in `exp://192.168.1.11:8081`.
- Đọc output QR thực tế, dựng lại các ô từ ký tự terminal và giải mã bằng OpenCV: PASS, nội dung chính xác `exp://192.168.1.11:8081`.
- Kiểm tra helper với `REACT_NATIVE_PACKAGER_HOSTNAME=127.0.0.1`: exit 1, thông báo lỗi kết nối, không xuất QR để quét.
- Chạy toàn bộ `RUN_MATHVISION.bat` qua terminal tương tác: diagnostics `READY_FOR_FULL_DEMO`, LAN `REACHABLE`; mã QR xuất hiện cuối; tiến trình tiếp tục chờ tại `pause`. Gửi một phím, launcher thoát với mã 0.
- `scripts/test/test_service_runtime_identity.ps1`: PASS, 8 trường hợp command, 8 trường hợp Python redirector và một TCP listener của tiến trình khác được giữ nguyên.
- Mở launcher bằng Windows Terminal để người dùng quét: `cmd` PID 18204 còn chạy sau khi hoàn tất, không còn tiến trình con khởi động dịch vụ. Việc quét và mở ứng dụng trên điện thoại trong lượt này chưa được kiểm chứng trực tiếp.

Không commit/push, không đổi giao diện ứng dụng hoặc huấn luyện mô hình trong nhiệm vụ này.

## Tài liệu đã đọc

[Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) và mã nguồn Expo CLI 57.0.21 đã cài trong workspace, đặc biệt LAN discovery, manifest và terminal QR renderer.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa luồng launcher bằng thay đổi nhỏ, dùng tiện ích đã cài và giữ các guard đang có.
  - Applied to: batch giữ terminal, tái sử dụng Metro, helper QR và kiểm tra hồi quy.
