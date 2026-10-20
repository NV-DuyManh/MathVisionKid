# Student — menu dọc thu gọn và icon, phương án 03

Chờ chủ dự án góp ý. Người dùng yêu cầu menu chuyển sang dọc, có thể thu
nhỏ và tiếp tục tìm bộ icon đẹp hơn. Yêu cầu này thay hướng menu ngang của
bản 02; không thay đổi mã sản phẩm trong lượt xem trước.

## Ảnh

- `icon-directions-v3.png`: A duotone tím bo tròn, B nét mảnh xanh đậm.
  Đây là bảng hướng mỹ thuật, chưa phải bộ SVG/asset sản phẩm sẵn dùng.
- `laptop-sidebar-expanded-v3.png`: menu dọc có icon và tên, nút Thu gọn.
- `laptop-sidebar-collapsed-v3.png`: cùng trang khi thanh bên chỉ có icon,
  nút mũi tên mở rộng, nội dung dùng thêm chiều ngang.
- `tablet-sidebar-collapsed-v3.png`: bố cục tablet ngang với menu icon dọc.

Ba ảnh giao diện dùng hướng A để minh họa. Chưa được chủ dự án chọn icon.
Giữ mobile theo bản trước với điều hướng dưới, chưa vẽ lại mobile lượt này.

## Hành vi dự kiến để duyệt

Menu gồm Trang chủ / Bài học / Thành tích / Của em. Độ rộng mục tiêu khi
triển khai khoảng 200 px mở rộng và 64–72 px thu gọn, cần hiệu chỉnh theo chữ,
không suy ra số đo CSS chính xác từ ảnh raster. Trạng thái đang chọn phân
biệt bằng cả nền, hình và tên/nhãn truy cập.

Nút mở/thu luôn có sẵn; bàn phím sử dụng được, không làm mất focus khi đổi
trạng thái. Khi thu, giữ nhãn cho trình đọc màn hình, tên mục khi hover/focus
trên máy tính; trên cảm ứng có thể mở menu để thấy nhãn, không dựa vào hover.
Mục tiêu chạm vẫn tối thiểu 48 px dù hình icon chỉ khoảng 22–24 px. Đây là
yêu cầu dự kiến, chưa được triển khai hoặc kiểm thử tương tác.

Vùng tiện ích dùng glyph gọn hơn thay các minh họa giấy lớn ở bản 02. Giữ
mascot, màu tím và nội dung học sinh; không thêm số liệu thành tích giả.

Tất cả là ảnh AI phác thảo, không phải screenshot app chạy thật, bằng chứng
responsive tự động hay bộ vector đã được chuẩn hóa. Các màn học khác chưa
được vẽ lại trong lượt này. Chưa deploy, train, commit hoặc push.

## Prompt set

Công cụ image_gen tích hợp, không dùng CLI/API riêng:

1. Bảng hai hệ icon: cùng tám nghĩa điều hướng/tiện ích; A duotone tím–lilac,
   B outline xanh đậm; cùng độ dày nét và tỷ lệ, không dùng hình lá/vật liệu
   giấy hoặc stock nhựa phồng. Có mẫu menu nhỏ để xem tỷ lệ dùng trong UI.
2. Laptop mở: sửa bản 02 theo menu trái gọn có bốn nhãn, nút Thu gọn bên
   dưới; dùng icon A; giữ hero, bài gợi ý và góc học tập.
3. Laptop thu: sửa đúng ảnh mở, giữ nội dung và typography, thanh trái chỉ
   còn icon, mũi tên mở rộng, nội dung dịch/reflow vào khoảng trống.
4. Tablet thu: tham chiếu laptop mới và bộ A, khung 4:3, rail hẹp, hero ngang,
   bốn tiện ích gọn, bài gợi ý cạnh chuỗi học tập.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: menu Student thích ứng với không gian màn hình.
  - Applied to: menu dọc hai trạng thái, phân cấp và kích thước mục chạm.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: chủ dự án muốn xem ảnh thiết kế và icon mới trước.
  - Applied to: bảng icon và ba ảnh giao diện, giữ các bản cũ nguyên trạng.
- `brainstorming`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/brainstorming/SKILL.md`
  - Why selected: chỉnh hướng thiết kế theo phản hồi của chủ dự án.
  - Applied to: phản ánh yêu cầu, trình bày hai kiểu icon, dừng ở ảnh đề xuất.
