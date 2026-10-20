# Student responsive — ảnh đề xuất ngày 20/10/2026

Trạng thái: **đang chờ chủ dự án xem và góp ý**. Đây là ảnh thiết kế tạo bằng
image_gen tích hợp, chưa phải giao diện được triển khai hoặc bằng chứng chạy
trên điện thoại/iPad/laptop thật. Không sửa mã sản phẩm trong lượt này.

## Ảnh xem trước

- `home-responsive-concept.png`: trang chủ điện thoại, tablet/iPad, laptop.
- `learning-responsive-concept.png`: màn học từng bước, đề và hướng dẫn cạnh
  nhau trên màn lớn; máy tính nhỏ mở cạnh vùng làm bài.
- Ảnh đối chiếu giao diện hiện có: `../../media/screenshots/home-web.jpg`.
  Theo `docs/media/README.md`, ảnh này là bản chụp web 390 × 844 ngày 5/10/2026,
  không phải ảnh chụp điện thoại mới ngày 20/10. Trang đăng nhập đang phát hành
  báo lỗi máy chủ khi thử mở tài khoản mẫu nên không lấy được ảnh mới.

## Hướng bố cục để duyệt

Giữ màu tím #7055F6, nền #F8F7FE, chữ xanh đậm #18164C, font Nunito, mascot
ngôi sao và các mục Trang chủ / Bài học / Thành tích / Của em.

- Điện thoại: một cột, điều hướng dưới, hành động Chụp bài toán nổi bật.
- Tablet/iPad: thanh điều hướng gọn; chia cột khi bề rộng nội dung cho phép.
  Khi xoay dọc hoặc chữ lớn thì ưu tiên khả năng đọc thay vì cố giữ hai cột.
- Laptop: sidebar có nhãn; nội dung có giới hạn chiều rộng, hero và chuỗi học
  tập cạnh nhau; tiện ích, bài học được sắp thành hàng.
- Học từng bước: điện thoại thu gọn đề; màn lớn giữ đề bên trái, bước đang
  học bên phải. Chỉ mở bước hiện tại và giữ phần giải thích vì sao.
- Máy tính: một công cụ thống nhất dạng pop-up có nút đóng, ưu tiên vị trí
  không che ô nhập/nút kiểm tra; trên điện thoại dùng hộp phù hợp vùng nhìn.

Các mốc dự kiến để khảo sát khi triển khai: 390, 600, 834, 1024, 1440 pixel.
Chọn ngưỡng theo độ rộng nội dung thực tế và cỡ chữ, không suy ra chỉ từ tên
thiết bị. Cần kiểm tra dọc/ngang, bàn phím, chữ lớn, chuột và cảm ứng sau này.
Ảnh minh họa chưa xác minh các tương tác hoặc mọi cỡ màn hình này.

Không thêm bảng xếp hạng, thành tích giả, chức năng quản trị hoặc thông tin
kỹ thuật vào màn học sinh. Chữ nhỏ/biểu tượng trong ảnh sinh có thể cần chỉnh
chính xác khi triển khai theo thiết kế được duyệt.

## Prompt dùng để tạo ảnh

Công cụ: built-in `image_gen`, không dùng CLI/API riêng.

- Trang chủ: tạo bảng UI ba thiết bị cùng nội dung, dựa trên ảnh home hiện có
  và mascot thật; giữ màu và font; điện thoại điều hướng dưới, tablet rail,
  laptop sidebar; bố trí hero, ba tiện ích, máy tính, chuỗi học tập trạng thái
  ban đầu và bài gợi ý; không chỉ phóng to màn điện thoại.
- Học từng bước: dùng bảng trang chủ làm tham chiếu phong cách; bài vườn cây
  có 1/3 táo, 2/5 xoài, 16 cây cam; chỉ hiển thị bước cộng hai phân số đang
  chờ trả lời, lời giải thích và nút gợi ý; tablet/laptop có đề cạnh hướng dẫn.
- Chỉnh ảnh học: chỉ chuyển máy tính ở laptop sang phần trống dưới đề,
  thay mascot lớn tại đó, để toàn bộ ô nhập và nút kiểm tra không bị che.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: bố cục Student thích ứng theo không gian và cách dùng.
  - Applied to: phân chia cột, điều hướng, khả năng đọc và mục tiêu cảm ứng.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: chủ dự án yêu cầu ảnh phác thảo trước khi triển khai.
  - Applied to: tạo hai bảng UI và chỉnh vị trí pop-up; giữ tài sản tham chiếu.
- `brainstorming`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/brainstorming/SKILL.md`
  - Why selected: trình bày hướng thiết kế để chủ dự án xem trước.
  - Applied to: làm rõ mục tiêu, khám phá UI hiện có, dừng ở ảnh đề xuất.
