# Khôi phục tải ứng dụng trên Expo Go — 03/10/2026

## Hiện tượng và kiểm tra

Điện thoại báo `java.io.IOException: Failed to download remote update` trước khi vào ứng dụng. Đây là màn hình của Expo Go; ảnh lỗi chưa cho biết ngoại lệ mạng chi tiết.

- Chủ dự án xác nhận điện thoại và máy tính cùng Wi-Fi, và trình duyệt điện thoại mở được `/status`, hiện `packager-status:running`.
- Địa chỉ Wi-Fi máy tính là `192.168.1.11`; mạng Windows đang ở profile Private. Các rule cho cổng 8081 và 8080 đã bật Allow trên Private. Không đổi hoặc tắt tường lửa.
- Backend và AI vẫn hoạt động. Manifest cung cấp đúng host LAN và SDK `57.0.0`.
- Gói Android tải được trên máy tính. Kiểm tra đầu tiên bằng PowerShell mất 31,04 giây; lượt tiếp theo 25,44 giây. Các số này gồm công việc ở máy tính, không phải thời gian tải trên điện thoại.

## Xử lý đã thực hiện

- Xác minh tiến trình giữ 8081 thuộc checkout này rồi dừng đúng tiến trình đó.
- Khởi động lại bằng Expo CLI cài trong dự án, với `start --go --lan --clear --port 8081`.
- Làm nóng gói Android trước khi yêu cầu chủ dự án mở lại. Không cài/nâng dependency, không sửa mã ứng dụng, không đổi API, không dùng public tunnel.
- Lấy deep link từ `/_expo/open?platform=android&runtime=expo`, tạo QR bằng chính implementation `toqr` của Expo CLI, rồi giải mã bằng OpenCV để kiểm tra khớp `exp://192.168.1.11:8081`.
- Cập nhật PID tracker của Metro. Tiến trình đang chạy trong phiên terminal do công cụ quản lý; để nguyên khi kết thúc lượt hỗ trợ.

Lần kiểm tra cuối mô phỏng header tải của Expo Go (`multipart/mixed`, Android, protocol và yêu cầu signature): manifest HTTP 200; launch asset Android HTTP 200, 10.895.275 byte, tải 12,922 giây trên máy tính. Đây là bằng chứng máy chủ phục vụ được gói native, không phải chứng minh đã mở ứng dụng trên điện thoại.

Tài nguyên kiểm tra local nằm trong `scratch/product_20261003/`: `expo-download-check.py`, `expo-download-check.json`, `expo-qr.cjs`, `render-expo-qr.py`, `expo-go-current.png`. QR đã được cung cấp cho chủ dự án để thoát màn hình lỗi và mở lại bằng mã hiện tại.

Sau khi khởi động lại, phiên Metro mới đã nhận log thực thi từ client Android, gồm chọn ảnh, che thông tin và cắt ảnh. Đây là bằng chứng gói mới đã tải và chạy trên client Android, vượt qua giai đoạn bị lỗi trong ảnh ban đầu. Không coi đó là kiểm thử tự động đầy đủ trên thiết bị hoặc chứng minh mọi chức năng đã đúng.

Chủ dự án xác nhận **“Đã vào được”** sau khi mở bằng mã mới. Lỗi tải ban đầu đã được khôi phục trong phiên chạy này. Kiểm tra cuối: Metro `packager-status:running`, backend `UP`, AI `/health` HTTP 200.

Chưa kết luận nguyên nhân chắc chắn là cache hoặc timeout. Nếu lỗi tải tái diễn, cần thông tin trong `View error log` để xác định request/ngoại lệ thực sự thay vì sửa UI hoặc thay cấu hình mạng theo suy đoán. Bằng chứng mở ứng dụng trên điện thoại là phản hồi của chủ dự án và log client, không phải tuyên bố tự kiểm thử thiết bị.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Khắc phục lỗi chạy thử bằng đường sẵn có, tránh thêm dependency hoặc thay mã khi chưa có bằng chứng.
  - Applied to: Xác minh kết nối, khởi động đúng Expo CLI, xóa cache bundler, kiểm tra manifest/gói Android và dùng implementation QR hiện có.

Tài liệu đã đọc: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) và [Expo CLI](https://docs.expo.dev/more/expo-cli/). Không commit/push, không huấn luyện model, không có kiểm thử thiết bị tự động.
