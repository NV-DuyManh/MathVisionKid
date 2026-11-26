# Hợp đồng API và dữ liệu

Spring Boot là thẩm quyền xác thực/RBAC và quyền sở hữu tài nguyên. Student/Teacher/Admin không tự cấp role hoặc coi ẩn nút là bảo vệ API. Giữ namespace, DTO và cấu trúc lỗi đang phát hành; quy ước mới không cho phép thay hợp đồng hàng loạt.

## Phiên đăng nhập

- Portal và Student Web dùng chung client `portal`. Teacher và Admin lần lượt dùng `teacher` và `admin`. Mỗi cổng chuyển tiếp `/api/v1` cùng origin tới Spring Boot. Yêu cầu Web gửi `X-MathVision-Web`, cookie `HttpOnly` và `X-MathVision-Session` khi đã đăng nhập. Dùng HTTPS ngoài môi trường phát triển nội bộ.
- Đăng nhập, đổi vé SSO và đổi mật khẩu trên Web trả về `{ sessionId }`. Các tab trong cùng hồ sơ trình duyệt và cùng origin chia sẻ mã phiên qua `localStorage`. Cookie `HttpOnly` và mã phiên phải khớp với bản ghi Spring Boot. Các tab đang mở tải lại khi phiên đổi để khôi phục đúng tài khoản. Bản nháp ảnh của Student Web vẫn gắn với mã tab trong `sessionStorage`. Phiên hết hạn sau tối đa 7 ngày tính từ lần cấp, với mã mới khi cấp lại. Đăng xuất Web thu hồi các phiên Web của tài khoản đó. Đổi mật khẩu và phát hiện refresh token bị dùng lại thu hồi các phiên theo chính sách tài khoản hiện có.
- Mobile dùng Bearer access token và refresh token luân chuyển trên `/api/v1/auth/refresh`. Ứng dụng native giữ token trong `expo-secure-store`. Khi access token đã hết hạn, `/api/v1/auth/logout` dùng refresh token còn hiệu lực để thu hồi chính refresh token đó. Spring Boot kiểm tra role và trạng thái tài khoản ở cả hai luồng.

## PIN Góc phụ huynh

- Hai API học sinh đã đăng nhập `POST /api/v1/student/parent-control/pin-code/request` và `POST /api/v1/student/parent-control/pin-code/confirm` hỗ trợ mục đích `SETUP` hoặc `RESET`. Request chỉ nhận `purpose` và trả `maskedEmail`. Confirm nhận `purpose`, `code`, `pin` và trả 204 khi thành công. Backend lấy địa chỉ từ tài khoản, dùng chung cấu hình SMTP của khôi phục mật khẩu.
- Mã email có sáu chữ số, hết hạn sau 10 phút, chỉ dùng một lần và chỉ có hiệu lực cho học sinh cùng mục đích. Mỗi tài khoản có tối đa ba lần gửi trong cửa sổ một giờ, cách nhau ít nhất 60 giây, và tối đa năm lần thử cho mỗi mã.
- Ai có quyền vào hộp thư tài khoản đều có thể đặt và khôi phục PIN. PIN bảo vệ Góc phụ huynh khi người sử dụng app không đồng thời kiểm soát hộp thư. Đổi PIN giữ giới hạn, thời gian sử dụng và phiên đăng nhập học sinh. Phiên bản PIN thay đổi khiến quyền đọc cài đặt đã cấp bị từ chối ngay ở backend.

## Quy ước API

- Hồ sơ riêng của học sinh trả `googleLinked` để Student Web mở luồng đặt lại mật khẩu qua email hiện có. `avatarPhoto` ưu tiên ảnh học sinh tải lên. Khi dùng ảnh Google, trường này chứa URL HTTPS lấy từ thông tin đăng nhập Google đã xác thực. Bảng xếp hạng dùng hình đại diện mặc định của hồ sơ.
- `POST /api/v1/auth/google` có thể nhận thêm `profileAccessToken`. Khi ID token đã xác thực thiếu URL ảnh hợp lệ, API dùng token bổ sung để đọc ảnh từ Google UserInfo và chỉ nhận ảnh nếu `sub` trùng với ID token.

- API nghiệp vụ dưới `/api/v1`, JSON camelCase. Dùng DTO và allowlist đầu vào, không bind entity hoặc nhận điểm/quyền đã duyệt từ client làm sự thật.
- HTTP: 200 đọc/cập nhật, 201 tạo, 204 không body; 400 validation, 401 chưa xác thực, 403 thiếu quyền, 404 không tồn tại/không được tiết lộ, 409 xung đột, 429 giới hạn. Không trả stack trace, SQL, secret hoặc thông tin môi trường trong lỗi người dùng.
- Phân trang/sort theo hợp đồng backend hiện có; endpoint mới chốt rõ giới hạn và trường sort. Timestamp ISO 8601; lưu instant, hiển thị theo múi giờ đã chọn.
- Thao tác có thể gửi lại cần quyết định idempotency ở backend, uniqueness/transaction khi có cạnh tranh; disable nút chỉ là lớp UX. Retry chỉ cho lỗi có thể phục hồi, có giới hạn và không nhân bản upload/đợt chấm.
- Flyway là nguồn schema PostgreSQL. Không sửa hoặc đánh lại số migration đã phát hành; không dùng `ddl-auto=update` trên môi trường dùng chung. Seed demo tách khỏi dữ liệu thật.
- File upload kiểm tra quyền, MIME, nội dung, dung lượng; tên và MIME của ảnh đã che phải khớp bytes xuất ra. Vùng không đọc rõ phải yêu cầu xác nhận, không bịa nét chữ hoặc tọa độ lỗi.
- OCR, dựng bài, kiểm chứng toán, tạo giọng và phát giọng là các giai đoạn riêng. Phân số/đơn vị phải giữ nghĩa. Không tắt bộ kiểm chứng để che lỗi từ chối; sửa với ca hồi quy có đáp án độc lập.
- Cache/catalog phân tách tài khoản, nội dung, version chính sách và giọng đọc; không trộn nam/nữ hoặc trả dữ liệu từ phiên cũ. Prefetch bị giới hạn, nhường foreground; không tự phát hoặc tạo video ngoài phạm vi.
- Ngoại lệ dùng chung là catalog đề công khai đã duyệt tại `ai/runtime/app/tutoring/data/verified_exercises.json`: không chứa dữ liệu tài khoản/bài làm/ảnh/âm thanh, khớp chính xác đề và được kiểm chứng lại. Đẩy bản cập nhật đã duyệt cùng mã nguồn qua PR; không tự xuất database học sinh lên Git. Máy khác cần pull và nạp lại dịch vụ để nhận bản mới.
- Tiến độ có nguồn đo thì dùng nguồn đo; ước tính phải ghi ước tính. Thành công chỉ khi có kết quả hợp lệ, không vì hết animation. Phân biệt timeout, auth, quota, mạng và kết quả không đạt kiểm chứng trong log đã lọc.
- H2 test không chứng minh migration PostgreSQL. CI và báo cáo phải phân biệt kiểm thử logic, migration thật, provider mock và thiết bị thật.
