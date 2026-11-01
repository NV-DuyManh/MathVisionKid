# Trình phát theo thời gian thật

Yêu cầu: thay tua theo ý bằng thanh trượt đến thời điểm bất kỳ, áp dụng cho lời giảng, câu trả lời, bản ghi câu hỏi và video. Thiết kế lại trình phát thành thẻ sáng gọn, nút phát trung tâm, thời gian thật, lùi/tiến và thiết lập phụ thu gọn.

1. Tạo WAV riêng tư từ những đoạn hướng dẫn đã được backend công bố, dùng giọng offline có sẵn. Ràng buộc tài khoản/phiên/bản sửa, giới hạn nội dung, thời gian, dung lượng và số tác vụ; cache có giới hạn. Không gọi model mới để dựng âm thanh.
2. Thêm route xác thực trên business-api và client tải binary an toàn. File/blob cục bộ được dọn khi đóng hoặc đổi nguồn.
3. Một bộ điều khiển thời gian chung dùng slider chuẩn, gắn vào audio/video thật. Giữ trạng thái phát khi tua, hỗ trợ kéo/chạm/bàn phím và phát lại khi đã hết.
4. Thay trình phát lời giảng cũ, đồng bộ bản ghi và video; giữ chữ và xác nhận hiểu bài. Không tự phát khi mở màn hình.
5. Kiểm tra quyền truy cập, hủy/phản hồi muộn, cache, seek thật, trình bày nhiều kích thước, TypeScript/lint và xuất web/native. Chỉ báo cáo bằng chứng đã chạy.

Phạm vi: thay trình phát và các màn liên quan; giữ nguyên phần che thông tin/cắt ảnh, không train, không commit/push/deploy nếu không được yêu cầu mới.
