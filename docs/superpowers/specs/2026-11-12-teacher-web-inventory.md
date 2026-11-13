# Teacher Web · Chức năng và luồng hiện tại

Môi trường: Teacher `http://127.0.0.1:15173`, Portal `http://127.0.0.1:15172`. Thay các tham số trong ngoặc nhọn bằng ID mà hệ thống cấp. Bảng gồm các route của Teacher Web và biến thể URL nghiệp vụ tìm được trong source.

| URL | Chức năng |
| --- | --- |
| `/` · `/dashboard` | Tổng quan, bộ đếm, lớp phụ trách, đợt gần đây, tạo bài/đợt, mở ngay hàng đợi chờ. Root chuyển về Dashboard. |
| `/login` · `/login#sso={ticket}` · `/login?code={ticket}` | Nhận SSO từ Portal. Form trực tiếp chỉ khi bật cấu hình dev và có `?fallback=true` hoặc `?direct=true`. |
| `/classes` | Danh sách lớp được phân công, sĩ số, vào danh sách học sinh, giao bài, xem bài của lớp. |
| `/classes/{classId}` | Danh sách và tìm học sinh, mở bài tập đã lọc theo lớp hoặc tạo bài cho lớp. |
| `/assignments` · `/assignments?classId={classId}` | Xem bài tập và lọc theo lớp, tạo bài, tạo đợt từ từng bài. |
| `/assignments/create` · `/assignments/create?classId={classId}` | Chọn lớp, nhập tiêu đề, chọn cộng/trừ đặt tính, đặt thang điểm, tạo bài rồi mở chuẩn bị ảnh. |
| `/batches` · `/batches?filter=pending` · `/batches?filter=failed` | Xem lịch sử đợt, tiến độ, đợt còn bài chờ hoặc có lỗi, mở chi tiết/hàng đợi. |
| `/batches/create` · `/batches/create?assignmentId={assignmentId}` · `/batches/create?batchId={batchId}` | Tạo đợt hoặc tiếp tục đợt còn mở. Chọn 1–30 ảnh, gán học sinh, thay/xóa ảnh, che hoặc xác nhận ảnh riêng từng tệp, xem tiến độ upload. Có cảnh báo khi rời trang có ảnh nháp. |
| `/batches/{batchId}` · `/batches/{batchId}?status=failed` | Xem số đã xử lý, chờ duyệt, đã chốt, lỗi, danh sách bài; làm mới hoặc tiếp tục đợt trống. |
| `/batches/{batchId}/review` | Tìm và lọc hàng đợi, theo dõi bài cần xử lý, mở bài nộp. |
| `/submissions/{submissionId}` · `?from=review` · `?from=failed` | Xem ảnh riêng tư, xoay/phóng to/toàn màn hình, xem đề xuất và bằng chứng, duyệt hoặc nhập điểm cùng lý do theo trạng thái, tải lại ảnh chụp và thử xử lý lại khi được phép, duyệt bài tiếp theo. |
| `/settings` | Xem hồ sơ giáo viên và thông tin hệ thống. |
| Portal `/`, `/login?role=TEACHER`, `/logout?source=teacher` | Trang chủ, đăng nhập và kết thúc phiên. |
| `#workspace-main` | Liên kết bỏ qua điều hướng, chuyển focus đến nội dung chính. |

Luồng chính: Portal → Tổng quan → Lớp → Bài tập → Chuẩn bị ảnh → Tiến độ đợt → Hàng đợi → Bài nộp → Chốt điểm hoặc xử lý ngoại lệ → Bài tiếp theo. Giáo viên cũng có thể mở trực tiếp hàng đợi từ Tổng quan và mở bài lỗi từ chi tiết đợt.

## Bằng chứng và giới hạn

Chrome DevTools MCP đã đăng nhập qua Portal trên stack cách ly, mở Dashboard, lớp, danh sách học sinh, bài tập, lịch sử đợt, cài đặt, hàng đợi và chi tiết một bài. Lượt khảo sát đọc dữ liệu, không gửi ảnh hay thay đổi điểm. Các thao tác upload, retry và duyệt điểm còn được đối chiếu với biên nhận vòng Reliability.

Lỗi SSO được tái hiện bằng test giữ request đổi ticket ở trạng thái chờ. Form Teacher hiện trước khi Dashboard sẵn sàng. Bản sửa thống nhất màn hình trạng thái khi đổi ticket và xác minh hồ sơ, giữ form trực tiếp cho chế độ dev, giữ thao tác xóa ticket và cung cấp đường đăng nhập lại nếu đổi ticket thất bại.
