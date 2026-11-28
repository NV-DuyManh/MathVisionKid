# Bàn giao giao diện Portal Web và Student Mobile

## Thay đổi

- Portal Web và Student Mobile giới thiệu cách dẫn dắt học sinh từng bước qua câu hỏi gợi mở và các cam kết về quyền riêng tư.
- Mô phỏng vở ô ly có ví dụ tương tác cho năm khối lớp. Tên đã che và bài toán minh họa lấy từ fixture có sẵn trong ứng dụng.
- Hai đường dẫn khởi động `/` và `/portal` trên Student Mobile dùng chung màn chờ xác minh phiên. Học sinh có phiên hợp lệ mở trang học. Khách có thể xem demo rồi tiếp tục qua giới thiệu hoặc đăng nhập.

## Tích hợp và khôi phục

- [PR #196](https://github.com/NV-DuyManh/MathVisionKid/pull/196) đưa thay đổi vào `develop`. Phiên bản phát hành sẽ được chốt trên nhánh release theo [Git Flow](git-flow.md). Tag source release chỉ xác định mã nguồn đã phát hành. Trạng thái triển khai được xác minh riêng trên từng môi trường.
- Khi cần khôi phục sau tích hợp, mở PR revert phần thay đổi Portal trên nhánh bị ảnh hưởng và chạy lại các luồng kiểm thử. Nếu lỗi ảnh hưởng production, xác minh revision đang triển khai rồi tạo hotfix từ revision phát hành phù hợp theo Git Flow. Giữ nguyên các tag đã công bố.
- Thay đổi không cần migration. Backend tiếp tục xác minh phiên, vai trò và quyền truy cập.

## Kiểm thử

- Kết quả CI của `4f5abe29` phản ánh nền PR trước khi đồng bộ với `develop` (`eee59d0c`). Trên bản cập nhật, đã chạy governance, Student typecheck, 11 ca Jest liên quan, Portal lint và 29 ca cấu hình/phiên Portal.
- Chromium desktop và mobile đã kiểm tra thao tác bàn phím, độ tương phản, vùng phản hồi và hai toán hạng được tô sáng sau bước nhân lớp 4 trên bản build Portal. [Ảnh Portal lớp 4](../media/screenshots/pr196-portal-web-grade4-feedback.png)
- Bản export Student Web chạy trên Chromium desktop và mobile với API fixture. Khi mở trực tiếp `/study/portal`, phiên đang xác minh không hiển thị nút đăng nhập dành cho khách. Phiên hợp lệ mở trang học và khách đi đến trang đăng nhập chung. [Ảnh Student Web sau khi xác minh phiên](../media/screenshots/pr196-student-web-portal-session-restored.png)
- Jest xác nhận vùng live polite trên Android, lệnh xếp hàng thông báo trên iOS và hủy điều hướng khi màn Portal đóng. Chưa nghe thông báo thật trên TalkBack hoặc VoiceOver. Chưa kiểm thử backend production, OAuth thực tế hoặc thiết bị di động vật lý.
