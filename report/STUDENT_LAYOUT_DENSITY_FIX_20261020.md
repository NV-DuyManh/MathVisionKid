# Chỉnh mật độ bố cục laptop và tablet — 20/10/2026

## Phản hồi và nguyên nhân

Chủ dự án nhận xét laptop trống và tablet bị giãn. Ảnh chạy thực tế cho thấy cột tiện ích hẹp ở bên phải laptop để lại vùng trống phía dưới, trong khi các nhóm nội dung bên trái trải rộng. Tablet vẫn dùng nhiều thẻ ngang rộng và hình/nút lớn của bố cục trước.

## Thay đổi

- Laptop: đặt khối chào cạnh chuỗi học tập; bốn tiện ích thành một hàng; bài học gợi ý và lối chọn lớp nằm ở hàng dưới. Giới hạn khung trang chủ thay vì kéo dài toàn màn hình.
- Tablet: bốn tiện ích thành lưới 2×2, hình 76px và thẻ có chiều cao tối thiểu 110px; nút chụp rộng 230px; khối chào giảm từ 300 xuống 248px. Hình linh vật có kích thước giới hạn, không phóng theo phần trăm bề ngang.
- Bố cục dựa vào vùng nội dung còn lại sau menu. Khi vùng này dưới 640px, nhóm thành tích và bài gợi ý chuyển về một cột; các nút lớp được phép xuống dòng trong khung.
- Đưa lối mở kho đề lớp 1–5 đang có ra màn hình rộng, gọi lại callback `onPractice(grade)` hiện hữu. Không thêm nguồn bài, dữ liệu giả hoặc dịch vụ mới.
- Giữ bộ icon đã duyệt, bố cục điện thoại dọc, menu, xác thực, OCR, máy tính và camera.

## Kiểm chứng

- Trong đợt sửa: toàn bộ Student **50 bộ / 580 kiểm tra đạt**. Kiểm tra chọn lớp sau resize được thêm cho callback thực tế; kiểm tra camera/máy tính sẵn có tiếp tục đạt.
- Sau chỉnh ngưỡng và cách xếp cột cuối: **9/9 kiểm tra trang chủ liên quan đạt**, TypeScript đạt.
- Xuất web, Android, iOS bằng SDK 57. Chỉ là gói kiểm chứng cục bộ, không triển khai production.
- Browser QA trên gói web thật: 320, 390, 768, 820, 1024, 1440, 1920px; kiểm tra không tràn nút/tab, số hàng tiện ích, nút chụp không bị kéo rộng, mở kho đề, máy tính, điều hướng và bàn phím.
- Kiểm tra thêm menu tablet mở rộng ở 768/820/1024px.
- Không có bằng chứng thiết bị vật lý; phiên browser dùng HTTP fixture tách khỏi mã xác thực.

Ảnh mới: `docs/design/student-responsive-20261020/density-refinement/`. Ảnh ở thư mục `implemented/` giữ lại để so trước/sau.

Chưa commit, push hoặc deploy. Không thay model hoặc huấn luyện.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Sửa mật độ và tỉ lệ giao diện theo phản hồi cụ thể.
  - Applied to: Khung nội dung, hàng/cột laptop, lưới tablet, ngưỡng theo bề ngang hữu dụng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Cập nhật React Native và giữ luồng tương tác.
  - Applied to: Dùng lại các khối JSX/callback hiện có, không thêm thư viện hoặc fetch.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Giữ bản sửa tập trung và nhỏ.
  - Applied to: Hai tệp giao diện trang chủ, một kiểm tra hành vi; giữ nguyên các màn khác.
