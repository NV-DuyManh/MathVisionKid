# Phản biện độc lập · Kết quả theo bài tập

Hai reviewer EGM được cấp ngữ cảnh mới và đọc cùng bản đặc tả. Terra dùng Design Critic và chuẩn Feature Spec. Luna dùng Zoom Out và chuẩn tương ứng, kèm diễn giải lại luồng để kiểm tra khả năng hiểu. Phạm vi review là đặc tả và bằng chứng mã nguồn, chưa chạy đầy đủ chuỗi năm stage EGM. Cổng Teacher Web cục bộ không phản hồi trong lượt này, nên nhận định UI dựa trên mã và biên nhận Chromium vòng Reliability.

| Phát hiện | Xử lý trong đặc tả và kế hoạch |
| --- | --- |
| Major · Hai quan hệ bài tập độc lập trên bài nộp và đợt. Lọc quyền sau phép đếm có thể lộ dữ liệu. | Ràng buộc cả hai ID, quyền trước mọi phép đọc, kiểm thử cả số tổng và truy cập trực tiếp. |
| Major · Chưa định nghĩa điểm stale, điểm thiếu và trạng thái đã chốt thiếu quyết định. | Dùng quyết định duy nhất theo submission, kiểm tra thang, tái sử dụng điều kiện hiển thị analysis hiện tại. |
| Major · Chưa giới hạn dữ liệu và làm rõ snapshot. | Giới hạn trang, thứ tự xác định, snapshot mỗi phản hồi, đo số truy vấn và EXPLAIN. |
| Major · Thiếu lựa chọn và rủi ro. | Bổ sung phạm vi của hàng đợi, trade-off tải toàn bộ và chi phí truy vấn. |
| UX · Bộ lọc có thể chồng lấn, nhóm ngoài lớp và chưa gán dễ nhầm. | Nhãn riêng, đơn vị bộ đếm, nhóm chưa gán độc lập với ô tìm. |
| UX · Đường về, focus và màn hẹp cần hành vi cụ thể. | Dùng mẫu React Router sẵn có, khôi phục focus hoặc về tiêu đề danh sách, dùng thẻ ở viewport hẹp. |

Các thay đổi trên là đề xuất đã đưa vào tài liệu. Chính sách đối với lịch sử học sinh chuyển lớp và quyền lớp vẫn cần chủ dự án duyệt trước khi triển khai.
