# Nhận dạng trong MathVision Kids

Mô-đun nhận dạng dùng chung tài khoản, ảnh được bảo vệ và luồng bài làm của MathVision. Không có chế độ sản phẩm riêng hoặc API khách.

| Thư mục | Trách nhiệm |
| --- | --- |
| `api/` | Gửi ảnh thực, phát hiện dòng, nhận dạng, lấy kết quả và lưu phản hồi qua API `/ocr/**` |
| `image/` | Giữ ảnh gốc, xử lý ảnh đã che/cắt, URI ảnh trên web và thiết bị |
| `state/` | Bản nháp ảnh và miền nhận dạng chữ/phép tính |
| `utils/` | Gợi ý AI, cập nhật bất đồng bộ, bảo vệ lựa chọn của người dùng, nguồn độ tin cậy |
| `analytics/` | Lịch sử, đo lường với bản chuẩn độc lập, xuất JSON/CSV/báo cáo, dữ liệu nghiên cứu |
| `components/` | Thành phần kết quả dùng chung trong MathVision |

Màn hình tại `src/app/recognition/` chỉ điều phối thao tác. Chấm lời giải vẫn dùng `src/utils/mathSolutionEvaluator.ts`; nhận phép tính vẫn dùng luồng `ARITHMETIC` và AI runtime chung.

Lõi AI tại `ai/runtime/app/ocr` và `ai/runtime/app/api`; API nghiệp vụ tại `backend/business-api/.../ocr`. Checkpoint OCR và mô hình toán vẫn ở `ai/runtime/models`.

Khóa lưu trữ cũ chỉ nằm trong `analytics/legacyHistory.ts` để chuyển lịch sử sang `mathvision_recognition_history_v4`. Không đổi dữ liệu ảnh, đầu ra mô hình hay câu trả lời của học sinh khi chuyển. Bản cũ chỉ được xóa sau khi lưu bền vững thành công.

Lịch sử mới và chi tiết bài được lưu riêng theo tài khoản. Lịch sử cũ chưa có chủ sở hữu được giữ riêng trên thiết bị, không tự gán cho học sinh đăng nhập tiếp theo. Khi đổi tài khoản, cache kết quả và bản nháp được làm sạch; phản hồi đến trễ từ phiên cũ không được đưa vào cache phiên mới.

Dữ liệu mẫu/benchmark được giữ cho nghiên cứu và kiểm thử; giao diện học sinh chỉ hiển thị lịch sử thực. Các tỷ lệ không có bản chuẩn độc lập hiển thị chưa biết, không suy ra độ chính xác từ việc học sinh đồng ý hoặc tự sửa.
