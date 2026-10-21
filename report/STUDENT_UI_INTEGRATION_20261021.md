# Student — tích hợp giao diện Hành trình Sao nhỏ

Ngày: 21/10/2026. Phạm vi: mã ứng dụng Student dùng chung React Native và web; ưu tiên điện thoại.

## Kết quả đã tích hợp

- Trang chủ dùng hình minh họa đã được chọn, màu tím/lavender, chữ Nunito và kích thước hình phù hợp màn hình. Hình lớn dùng nguồn đầy đủ độ phân giải; biểu tượng điều hướng điện thoại tiếp tục dùng SVG.
- Điện thoại: nút chụp nổi bật, ba thẻ tiện ích, máy tính dạng hàng ngang, các khu vực học tiếp và lịch học phân bổ theo chiều dọc. Nội dung cuộn được; thao tác cuối không bị thanh điều hướng che.
- Tablet: menu dọc thu gọn, hành trình học dạng ngang và lưới tiện ích. Không kéo bố cục điện thoại thành một cột quá rộng.
- Laptop: menu dọc có thể thu gọn, khối chào và chuỗi học đặt cạnh nhau, hành trình học có đường nối và đảo cây, bốn tiện ích và khu vực chọn lớp. Chiều rộng nội dung dùng theo không gian thực còn lại sau menu.
- Bài học mở từng bài khi chọn; đổi lớp đóng nội dung trước. Nội dung chương trình, gợi ý và hành động học/chụp bài vẫn dùng dữ liệu thật sẵn có.
- Thành tích và Của em trình bày lại theo không gian màn hình; không thêm thành tích hoặc lịch sử giả vào app.
- Học từng bước chỉ hiển thị bước hiện tại. Laptop có tiến trình và đề bài cạnh nội dung chính. Nghe giảng, Hỏi bài và Hình phân số mở trong cửa sổ riêng; vẫn giữ các kiểm tra, quyền ghi âm và xử lý phiên học hiện có.
- Hình phân số dùng phông Nunito và viền/nút đồng bộ với giao diện. Không sửa cách chia hình hoặc tính đúng/sai.
- Màn đăng nhập native có hình Sao nhỏ và bố cục hai phần khi đủ rộng. Web tiếp tục sử dụng cơ chế xác thực của hệ thống hiện có.

## Che tên và cắt ảnh được giữ nguyên

Đối chiếu SHA-256 đầu/cuối lượt làm: cả 5 tệp sau không thay đổi:

- `apps/student-mobile/src/app/privacy.tsx`
- `apps/student-mobile/src/app/crop.tsx`
- `apps/student-mobile/src/components/ui/AppHeader.tsx`
- `apps/student-mobile/src/components/ui/AppButton.tsx`
- `apps/student-mobile/src/constants/theme.ts`

Bằng chứng: [trước](student-ui-integration-20261021/protected-before.json), [sau](student-ui-integration-20261021/protected-after.json). Kiểm tra chọn ảnh từ thư viện → xác nhận thông tin → mở màn cắt ảnh cũng đã chạy trên bản production tại 390, 768 và 1440 px. Đây là nhánh không vẽ vùng che; kiểm tra hồi quy của thao tác che và xuất ảnh nằm trong bộ test Student.

## Kiểm tra

| Hạng mục | Kết quả |
|---|---|
| TypeScript | `npx tsc --noEmit` qua |
| Toàn bộ test Student | 61 suites, 847 tests qua |
| Hồi quy sau tinh chỉnh header/bố cục | 5 suites, 59 tests qua |
| Hồi quy sau tinh chỉnh hình phân số | 107 tests qua |
| ESLint các thành phần/bố cục đã sửa | Qua |
| Cấu hình web và kiểm tra địa chỉ dịch vụ trong export | 4 tests qua; export hợp lệ |
| Expo production web | Xuất thành công 32 routes, mount `/study` |
| Expo Android và iOS | Xuất bundle Hermes thành công |
| Kiểm tra trình duyệt | 49 ảnh, 9 kích thước 320–1920 px; không tràn ngang, không điều khiển tràn khỏi màn hình, không ảnh lỗi sau khi tải xong, không JavaScript page error |

Các kích thước: 320×740, 360×800, 390×844, 414×896, 768×1024, 1024×768, 1280×800, 1440×1000, 1920×1080. Trang chủ kiểm tra cả 9; các trang và công cụ chính kiểm tra 390/768/1440.

## Xem giao diện thực tế

- [Thư viện ảnh theo màn hình và thiết bị](student-ui-integration-20261021/index.html)
- [Kết quả kiểm tra trình duyệt](student-ui-integration-20261021/visual-qa.json)
- [Script tái kiểm tra](student-ui-integration-20261021/visual-qa.cjs)

Ảnh được chụp từ bản production của mã app đã tích hợp, với phiên đăng nhập và phản hồi API cô lập trong trình duyệt để kiểm tra bố cục. Ảnh đăng nhập là kiểm tra thành phần đăng nhập của app; xác thực web thực tế vẫn đi qua cổng tài khoản chung. Không thêm chế độ mẫu hay bỏ qua xác thực vào ứng dụng. Các ảnh này không chứng minh chất lượng model, giọng đọc hoặc hoạt động camera trên thiết bị vật lý. Chưa kiểm tra trực tiếp bằng điện thoại/iPad thật trong lượt này.

Không train, không đổi model, không commit/push/deploy trong lượt này. Các thay đổi backend/OCR và luồng gia sư đã tồn tại trong working tree được giữ lại; phạm vi mới tập trung vào trình bày Student.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: giao diện Student thích ứng trên điện thoại, tablet và laptop.
  - Applied to: phân cấp nội dung, bố cục theo chiều rộng thực, hình ảnh, chữ, khoảng cách và rà soát đa kích thước.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai các thành phần React/React Native đang dùng trong dự án.
  - Applied to: tái sử dụng dữ liệu và callback thật, useWindowDimensions/onLayout, kích thước hình và hành vi điều hướng.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: giữ thay đổi tập trung, tránh thêm tầng giao diện hoặc phụ thuộc không cần thiết.
  - Applied to: dùng thư viện, hình và luồng học sẵn có; không tạo framework, cơ chế xác thực hoặc dữ liệu giả mới.
