# Kiểm thử trên điện thoại thật

Ngày 08/10/2026: chưa kiểm thử điện thoại thật. Bạn chưa thể kết nối thiết bị;
các kiểm tra trình duyệt và kiểm thử tự động không thay thế bước này.

Mở app bằng bộ khởi chạy hiện có, giữ cửa sổ có mã QR và mở app trên điện thoại.
Dùng ảnh không chứa thông tin riêng tư; thử cả ảnh chụp mới và ảnh từ thư viện.
Ghi phiên bản app, loại máy và kết quả từng dòng dưới đây.

| Luồng | Kết quả cần thấy | Kết quả thực tế |
| --- | --- | --- |
| Chụp/chọn ảnh → cắt | Ảnh đủ lớn, vùng ngoài khung tối, kéo bốn cạnh/góc được | Chưa test |
| Thu khung rất mỏng, kéo qua cạnh đối diện | Thao tác tiếp tục trong cùng lần giữ tay, không kẹt khung | Chưa test |
| Xoay bằng thanh kéo, xoay 90° | Preview theo tay; xác nhận tạo ảnh đúng vùng đã chọn | Chưa test |
| Nhận diện xong → quay lại che thông tin | Ảnh giữ đúng kích thước, không thu thành ảnh tí hon trên nền đen | Chưa test |
| Đang đọc → dừng chờ → quay lại | Giữ ảnh; kết quả đến muộn không tự đổi màn hình | Chưa test |
| Mở/đóng đề, chỉnh đề rồi quay lại | Nội dung và trạng thái đúng; chỉnh đề hủy bài hướng dẫn cũ | Chưa test |
| Đề chưa xác nhận | Không bắt đầu hướng dẫn trước khi xem/sửa và xác nhận | Chưa test |
| Bài làm chưa xác nhận | Không dùng bản đọc chưa xác nhận để kết luận học sinh sai | Chưa test |
| Chữ số có `[?]` | Yêu cầu sửa số chưa rõ trước khi giải | Chưa test |
| Phân số có tử/mẫu xếp tầng | Giữ đúng tử và mẫu; không ghép với hàng bên cạnh | Chưa test |
| Chia đặt tính có nhiều hàng dư | Giữ số bị chia, số chia, thương và từng hàng trong ảnh | Chưa test |
| Thương học sinh viết sai | Bản đọc giữ số sai trong ảnh; cho học sinh sửa hoặc kiểm tra | Chưa test |
| Trả lời sai một bước | Giữ bước hiện tại, phản hồi phù hợp; không tự tính thay toàn bộ | Chưa test |
| Mất mạng/dịch vụ đọc ảnh gián đoạn | Giữ ảnh và nội dung đã nhập, cho thử lại | Chưa test |
| Bàn phím, xoay màn hình, đưa app ra nền | Nút/input vẫn dùng được, không mất bản nháp hay che thao tác chính | Chưa test |

Với phép chia, đối chiếu **từng số trong ảnh** trước khi đánh giá phép tính.
Ảnh mờ, nét chồng và phần bị cắt phải được báo chưa rõ; không bổ sung số bằng
cách suy từ đáp án. Những ảnh bạn gửi trước đây vẫn là ảnh tham chiếu, không phải
bằng chứng rằng phiên bản hiện tại đã chạy trên điện thoại của bạn.

Nếu gặp lỗi, ghi thao tác từ lúc mở ảnh đến khi lỗi xuất hiện và chụp màn hình
trước/sau lỗi. Đánh dấu “Chưa test” cho bước chưa làm, không suy từ bước khác.
