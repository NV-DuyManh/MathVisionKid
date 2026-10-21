# Căn giữa màn hình đọc bài — 21/10/2026

## Thay đổi

Màn “Mình đang đọc bài của em” dùng chung khung chờ toàn màn hình với “Chuẩn bị các bước học”. Toàn bộ ảnh, tiêu đề, mô tả, thanh tiến trình và nút dừng được căn giữa trong vùng an toàn. Không còn header và công cụ phía trên khiến nội dung dồn lên đầu màn hình.

Chỉ sửa điều kiện render trong `apps/student-mobile/src/app/learning/math-guide.tsx`, tái sử dụng thành phần `RecognitionProgress` và bố cục hiện có. Giữ cơ chế hủy, lưu ảnh và bỏ qua phản hồi muộn. Không thêm route, thư viện hoặc gọi model.

## Kiểm chứng

- 52/52 kiểm thử liên quan đạt trong `tutorScreen.test.tsx` và `RecognitionProgress.test.tsx`. Kiểm thử mới kiểm tra màn đọc riêng, hủy yêu cầu, giữ ảnh, bỏ qua kết quả đã hủy và đọc lại.
- TypeScript đạt; ESLint file giao diện đạt. File kiểm thử nằm trong cấu hình bỏ qua của ESLint; Jest đã chạy file này.
- Xuất web thành công, 32 route.
- Kiểm tra giao diện web thật tại 320×568, 390×844, 768×1024, 1440×1000, 844×390. Cả hai trạng thái có tâm nội dung trùng tâm khung chứa; không tràn ngang, nút dừng truy cập được.
- 10 ảnh chụp và số đo tại `report/student-reading-centered-20261021/visual-qa.json` và `screenshots/`. Đã xem trực tiếp ảnh điện thoại của cả hai trạng thái. API trì hoãn bằng dữ liệu kiểm thử để quan sát màn chờ; không phải bằng chứng chạy trên thiết bị vật lý.
- Hash của privacy, crop, AppHeader, AppButton và theme khớp nguyên bản đã bảo vệ. Chi tiết: `protected-after.json`.

Không commit, push hoặc triển khai lên máy chủ trong đợt sửa này.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: sửa căn chỉnh trạng thái chờ trên điện thoại và màn hình rộng.
  - Applied to: căn giữa trong vùng an toàn, giới hạn chiều rộng, giữ cuộn trên màn hình thấp.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: thay đổi điều kiện render React Native/web.
  - Applied to: dùng trạng thái yêu cầu hiện có, giữ cơ chế hủy và bảo vệ phản hồi muộn.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa lỗi bằng thay đổi nhỏ tại nguyên nhân bố cục.
  - Applied to: dùng chung khung chuẩn bị, không thêm thành phần hoặc phụ thuộc mới.
