# Triển khai giao diện Student responsive — 20/10/2026

## Kết quả

Đã áp dụng bộ tiện ích giấy tím–kem và icon điều hướng duotone A mà chủ dự án chọn. Cập nhật trực tiếp ứng dụng Student dùng chung React Native/web; không chỉ dựng bản mô phỏng.

| Khu vực | Thay đổi |
| --- | --- |
| Điều hướng | Điện thoại giữ bốn tab dưới. Từ 768px chuyển menu dọc, mở/thu gọn được; mặc định mở từ 1200px. |
| Trang chủ | Bỏ giới hạn web 860px; bố cục dựa trên bề ngang nội dung thực tế. Từ 1000px nội dung hữu dụng chuyển thành hai cột, tiện ích nằm bên phải. |
| Minh họa | Bốn ảnh nền trong suốt riêng cho bài đã lưu, luyện tập, tiến bộ và máy tính; tổng 261.954 byte. Bốn icon điều hướng SVG dùng Expo Image, không thêm thư viện runtime. |
| Bài học | Hình mới, danh sách chia hai cột khi vùng màn hình đủ rộng; các lớp, gợi ý và đường dẫn bài học được giữ. |
| Thành tích | Hình mới, bố cục nhóm thống kê/tuần học và thẻ khuyến khích; số liệu tiếp tục lấy từ hoạt động thật. |
| Của em | Mở rộng khung đọc vừa phải, dùng hình bài đã lưu mới, giữ lịch sử theo tài khoản và đăng xuất. |
| Hướng thiết bị | Cho phép bố cục theo cả hướng ngang và dọc thay vì khóa dọc toàn ứng dụng. |

Các màn học từng bước đã có khung đọc tối đa 640px, tiếp tục giữ khung đó. Không thay đổi việc tiết lộ đáp án, logic giải toán, OCR, dữ liệu huấn luyện, API hoặc quyền truy cập.

## Kiểm chứng

- `npx tsc --noEmit -p apps/student-mobile/tsconfig.json`: đạt.
- `npm test --workspace=student-mobile -- --runInBand --silent`: **49 bộ, 579 kiểm tra đạt** trên bản cuối.
- `node --test scripts/deploy/test_student_web.mjs apps/student-mobile/src/context/__tests__/webAuthSession.test.mjs`: **11 kiểm tra đạt**, bao gồm kiểm tra quyền học sinh, không cho hồ sơ cache tự cấp quyền và đăng xuất chung.
- `expo export --platform all`: xuất thành công **web, Android, iOS**, 32 tuyến web; các SVG và WebP mới có trong gói native.
- Trình duyệt chạy bản web xuất thật ở **320×740, 390×844, 768×1024, 820×1180, 1024×768, 1440×1000, 1920×1080**. Không có lỗi JavaScript; không có nút/tab bị tràn ngang trong các kích thước kiểm tra.
- Kiểm tra chuyển đủ bốn trang, thu/mở menu, chọn lớp, mở bài đã lưu rỗng, điều hướng bằng phím mũi tên và Enter, mở máy tính, tính `12+3=15`, đóng máy tính.
- Các kiểm tra sẵn có tiếp tục xác nhận nút chụp vào camera trực tiếp, thư viện ảnh và các callback học tập.
- `git diff --check`: đạt.

Đã quan sát kiểm tra mới thất bại trước khi thêm menu responsive. Rà soát độc lập tìm thấy lỗi `tabIndex=-1` làm mục chưa chọn không nhận focus trên Android; thêm kiểm tra tái hiện, sửa chỉ áp dụng roving tabIndex trên web, rồi chạy lại đạt. Kiểm tra cache minh họa được đổi từ số lượng ảnh cố định sang xác nhận chỉ tải lại đúng một ảnh thất bại.

## Bằng chứng và giới hạn

Ảnh chụp thật và kết quả nằm tại `docs/design/student-responsive-20261020/implemented/`. Runner cục bộ và gói xuất nằm trong các thư mục `output/student-responsive-*`, được loại khỏi Git.

Phiên browser QA dùng HTTP fixture cho `/me` và lịch sử rỗng; không thêm đường tắt đăng nhập vào mã ứng dụng. Địa chỉ API thử nghiệm chỉ được truyền qua môi trường khi tạo gói kiểm chứng, không ghi vào cấu hình nguồn. Gói này không dùng để triển khai production.

Chưa kiểm thử trên điện thoại/iPad vật lý; xuất bundle native thành công không thay thế kiểm tra thiết bị. Chưa triển khai Vercel, commit hoặc push. Nhánh làm việc: `codex/student-responsive-approved`. Các báo cáo và tài liệu không liên quan được giữ nguyên.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Thiết kế giao diện theo không gian sử dụng trên nhiều thiết bị.
  - Applied to: Phân cấp trang chủ, bố cục thẻ, menu dọc và ngưỡng chia cột.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Thực thi các thành phần React/React Native.
  - Applied to: Giữ nguyên luồng callback/router, không thêm dependency, dùng ảnh tĩnh và khối giao diện dùng một lần.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Menu thu gọn và điều hướng có tương tác bàn phím.
  - Applied to: Tên truy cập, trạng thái được chọn/mở rộng, focus hiển thị, phím mũi tên/Home/End, giữ native focus.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: Tạo tài sản bitmap riêng từ bộ minh họa đã duyệt.
  - Applied to: Tách bốn minh họa nền trong suốt; giữ bản gốc và tối ưu bản phân phối WebP.

Quy trình bổ trợ: `superpowers:writing-plans`, `superpowers:executing-plans`, `superpowers:test-driven-development`, `superpowers:requesting-code-review`, `superpowers:verification-before-completion`. Quy tắc không commit của chủ dự án được ưu tiên.

Đã đọc tài liệu Expo theo đúng phiên bản trước khi sửa mã: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) và [Expo Image SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/image/).
