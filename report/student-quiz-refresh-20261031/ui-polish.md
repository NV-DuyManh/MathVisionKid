# Làm mới nhẹ UI Quiz và nghe giảng

Đã áp dụng vào bản local. Phạm vi: màn hình làm Quiz, bộ chọn giọng, trình phát dùng chung và thẻ giọng có sẵn.

## Thay đổi

- Quiz có nhãn thử thách nhỏ và đồng hồ ở hàng đầu; đề được đặt trong khung màu nhạt riêng, với tên dạng toán ngắn hơn. Phần trả lời/kết quả vẫn nằm trong cùng một vùng làm bài.
- Kết quả dùng ba huy hiệu sao và khung xanh dịu. Nút hành động cùng bán kính bo góc, phần công cụ phụ giảm độ nổi để nút chính rõ hơn.
- Bộ chọn giọng có biểu tượng, trạng thái chọn rõ và màu nền nhẹ. Giọng có sẵn có màu xanh dịu riêng. Màn hình hẹp dưới 350 hoặc cỡ chữ hệ thống lớn chuyển các lựa chọn thành từng hàng để giữ khả năng đọc.
- Trình phát có nền trắng, biểu tượng tai nghe gọn, trạng thái phát tách biệt bằng chữ và màu, thanh tua tím và các nút lùi/tiến có vùng bấm rõ. Trạng thái chuyển xuống dưới tiêu đề trên màn hình hẹp hoặc khi tăng cỡ chữ.
- Thẻ giọng có sẵn dùng cùng ngôn ngữ hình ảnh; thông báo trạng thái gọn, nút phát/dừng rõ.

Không thêm thư viện, ảnh tải từ mạng hoặc hiệu ứng chạy liên tục.

## Kiểm tra

- TypeScript qua.
- 8 bộ kiểm thử liên quan Quiz, giọng đọc, tua, phát lại và ghi âm: **72 kiểm thử qua**.
- Xuất web, Android và iOS thành công.
- `git diff --check` qua.
- Kiểm tra số học 8 cặp màu chính: chữ đạt tối thiểu 4,5:1; biểu tượng phát và đường viền nhập đáp án đạt tối thiểu 3:1. Đây không phải kết luận toàn bộ ứng dụng đã đạt mọi tiêu chí accessibility.
- Chưa có ảnh chụp hoặc kiểm chứng giao diện trên điện thoại thật cho lượt làm mới này. Kiểm tra bố cục hẹp dựa trên cách xuống hàng, giới hạn chiều rộng, khả năng tăng chiều cao theo chữ và kết quả build; chưa thay thế QA hình ảnh trên thiết bị.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: cải thiện phân cấp nội dung và bố cục UI điện thoại.
  - Applied to: khung đề Quiz, huy hiệu kết quả, bộ chọn giọng, khoảng cách và độ tương phản.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai trong các thành phần React Native/web dùng chung.
  - Applied to: điều chỉnh hiển thị theo kích thước/cỡ chữ, không thêm tác vụ nền hoặc listener riêng.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: đổi vừa đủ, tái sử dụng giao diện và tài nguyên hiện có.
  - Applied to: thay đổi trong 5 file UI, dùng biểu tượng và gradient đã cài sẵn.
