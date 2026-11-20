# Thiết kế Hồ sơ và Góc phụ huynh

Của em dành cho học sinh: giữ tiến độ, thành tích, bài đã lưu và thêm lối vào Góc phụ huynh gần thông tin học sinh. Chỉnh sửa hồ sơ tập trung vào thông tin, quyền riêng tư, an toàn tài khoản và đăng xuất; giữ lối vào phụ huynh tại đây cho phép tìm lại.

Góc phụ huynh dùng màu, font, icon và điều khiển Student. Cổng PIN một cột, biểu mẫu trước nội dung phụ. Sau mở khóa, tổng quan cân bằng Tiến độ học tập và Sử dụng an toàn. Tiến độ hiển thị kỳ đo và gợi ý đồng hành chung, không chẩn đoán từ số 0. Sử dụng an toàn hiển thị số phút hôm nay, mức đang áp dụng và biểu đồ tuần có dữ liệu dạng chữ. Dùng bố cục hai cột nếu đủ rộng, xếp dọc trên mobile. Mức áp dụng lấy từ kết quả mở khóa, thiết lập hoặc lưu; thời gian lấy từ API tuần. Giới hạn có hai lựa chọn tường minh, đơn vị và PIN xác nhận khi lưu.

Tách trạng thái đang tải, dữ liệu trống, mất kết nối, tải lại và lỗi PIN. Khi hết giờ giữa bài, giữ nội dung đang mở bên dưới lớp chặn, không cho tiếp tục thao tác và không tuyên bố đã lưu. Phân biệt hết giờ với trò chơi chờ xác minh kết nối. Giữ phân quyền, khóa PIN, API và cơ chế kiểm soát của backend.

Dùng tài khoản dev dành riêng cho thay đổi thiết lập trong nghiệm thu. Mock có nhãn để kiểm tra trạng thái lỗi và thời điểm hết giờ. Kiểm chứng app native riêng với web responsive.

Khi xác nhận hết giờ, hiển thị hộp thông báo nổi trên nền tím khói bán trong suốt. Ở web có thể làm mờ nhẹ phần nền, với lớp phủ màu làm dự phòng. Vẫn nhận ra màn hình đang học, nhưng màn hình bên dưới không nhận focus hoặc thao tác. Hộp thông báo giữ nền đặc, có thể cuộn khi màn hình thấp, và không đóng bằng cách nhấn bên ngoài.
