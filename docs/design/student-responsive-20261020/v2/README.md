# Student — phương án hình ảnh 02

Trạng thái: chờ góp ý của chủ dự án. Bộ ảnh 01 đã bị chủ dự án từ chối về
minh họa tiện ích và bố cục tablet/laptop. Ảnh dưới là phương án sửa, không
phải giao diện đã triển khai hay bằng chứng thiết bị thật. Chưa sửa mã app,
chưa thay tài sản runtime, chưa commit/push.

## Ảnh để duyệt

- `utility-illustrations-v2.png`: bảng bốn minh họa giấy/vở màu tím–kem.
  Đây là bảng phong cách, chưa phải bốn asset nền trong suốt để đưa vào app.
- `phone-home-v2.png`: giữ kiến trúc trang chủ mobile, làm lại chất liệu minh
  họa, nền thẻ, chữ và nhịp khoảng cách.
- `tablet-home-v2.png`: điều hướng ngang, hero cạnh chuỗi học tập, bốn tiện
  ích chạm rộng, ba thẻ bài học bên dưới.
- `laptop-home-v2.png`: điều hướng ngang, phần chính dành cho mở bài và bài
  học; chuỗi học tập thành dải thấp; tiện ích xếp thành hàng trong cột phụ.

Phong cách đề xuất do phản hồi của chủ dự án và nhận định thiết kế: minh họa
giấy có lớp, vở ô ly, nét chi tiết vừa phải, tím #7055F6, chữ xanh đậm, nền
trắng ấm. Giữ nhận diện mascot ngôi sao. Hai truy vấn style trong skill chưa
trả về hướng khớp hoàn toàn nên không dùng kết quả đó làm tiêu chuẩn thiết kế.

Không mặc định bốn ảnh này đã được chủ dự án duyệt. Bản 02 trong lượt này
tập trung trang chủ và minh họa tiện ích; màn học ở bản 01 chưa được làm lại
theo ngôn ngữ điều hướng ngang của bản 02. Các màn khác, dọc/ngang, chữ lớn,
chuyển kích thước và tương tác vẫn cần thiết kế/kiểm tra sau khi chốt hướng.

Không dùng số liệu thành tích giả. Chữ và chi tiết phím trong minh họa do AI
sinh cần vẽ/chuẩn hóa chính xác khi tách thành asset hoặc điều khiển thật.
Ảnh máy tính trang trí không thay thế bàn phím chức năng của máy tính hiện có.

## Prompt set và cách tạo

Công cụ: image_gen tích hợp, không dùng CLI/API riêng.

1. Bảng bốn tiện ích: thiết kế mới hồ sơ bài đã lưu, sổ luyện tập, đường tiến
   bộ và máy tính; chất liệu giấy mờ, màu tím–kem, nét xanh đậm; tránh bộ hình
   nhựa phồng, emoji và biểu đồ cột chứng khoán; nhãn tiếng Việt.
2. Mobile: lấy home hiện có làm cấu trúc, bảng tiện ích mới làm tham chiếu
   chất liệu và mascot thật làm tham chiếu nhân vật; giữ tab dưới, hero,
   ba tiện ích, máy tính, chuỗi học tập và bài gợi ý.
3. Tablet: dùng mobile mới và bảng minh họa làm tham chiếu; khung ngang 4:3,
   menu ngang, hero 2/3 và chuỗi học 1/3, bốn tiện ích và ba bài học.
4. Laptop: cùng nhận diện, menu ngang; bố cục bất đối xứng 8/4, hero chính,
   chuỗi học tập thành dải thấp, hai bài gợi ý, tiện ích thành bốn hàng ở cột
   phụ, không dùng sidebar điều hướng hoặc cột điện thoại kéo rộng.

Tham chiếu gốc: `docs/media/screenshots/home-web.jpg` và
`apps/student-mobile/assets/illustrations/mathvision-star.png`.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: chỉnh phân cấp và bố cục Student theo kích thước màn hình.
  - Applied to: hướng menu ngang, cột phụ chức năng, khả năng đọc và mục tiêu chạm.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: chủ dự án yêu cầu minh họa và ảnh thiết kế mới.
  - Applied to: bốn ảnh phác thảo, giữ ảnh cũ và tài sản runtime nguyên trạng.
- `brainstorming`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/brainstorming/SKILL.md`
  - Why selected: sửa hướng thiết kế theo phản hồi trước khi triển khai.
  - Applied to: phản ánh yêu cầu, đề xuất ngôn ngữ hình ảnh mới, chờ góp ý.
