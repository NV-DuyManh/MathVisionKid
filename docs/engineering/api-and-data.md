# Hợp đồng API và dữ liệu

Spring Boot là thẩm quyền xác thực/RBAC và quyền sở hữu tài nguyên. Student/Teacher/Admin không tự cấp role hoặc coi ẩn nút là bảo vệ API. Giữ namespace, DTO và cấu trúc lỗi đang phát hành; quy ước mới không cho phép thay hợp đồng hàng loạt.

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
