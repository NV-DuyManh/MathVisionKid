# Admin & Teacher UI redesign — 2026-10-22

## Kết quả

Triển khai giao diện Admin và Teacher theo phong cách Student Mobile trên nhánh `codex/admin-teacher-mobile-ui`. Có thư viện `design/admin-teacher-redesign/index.html`, danh mục `manifest.json` và 30 ảnh chụp giao diện chạy thật. Không commit/push.

Giữ palette lavender/tím, Nunito và mascot sẵn có. Đồng nhất theme, sidebar, topbar, card, bảng, form, dialog và thông báo. Thêm navigation thu gọn, skip link, focus rõ ràng, accessible name cho icon button, liên kết nhãn input/select và tên dialog. Các thay đổi trạng thái hiển thị dùng dữ liệu hiện có; không sửa API/auth/nghiệp vụ.

## Phạm vi tệp

- `apps/admin-web/src/{theme.ts,index.css,main.tsx}`, các component UI common/layout và các page JSX/style.
- `apps/teacher-web/src/{theme.ts,index.css}`, các component UI common/layout và các page JSX/style.
- `apps/{admin-web,teacher-web}/public/ui/`: mascot, ba font và giấy phép font lấy từ tài sản mobile có sẵn.
- `apps/admin-web/src/components/layout/NavigationContext.ts`: chỉ điều khiển trạng thái mở menu trên màn hình nhỏ.
- Không đổi service/API client, config, auth context, router hay backend. Student Mobile giữ nguyên trong đợt UI này.
- Working tree có các thay đổi AI/mobile/infrastructure và các file `.shared` bị xóa từ trước; chúng không thuộc redesign này và được giữ nguyên.

## Phủ màn hình

| Nhóm | Trang/trạng thái | Bằng chứng |
|---|---|---|
| Admin | dashboard, recognition/analytics, users, users/:userId, classes, classes/:classId, audit | 7 ảnh trang chính |
| Admin dialogs | tạo/sửa tài khoản, reset/disable confirmation, tạo/sửa lớp, phân công giáo viên, thêm học sinh | 8 ảnh; chỉ mở/đóng, không submit |
| Teacher | dashboard, classes, assignments, assignments/create, batches, batches/create, settings | 7 ảnh; tạo batch mở từ bài tập có thật |
| Teacher thiếu bản ghi | batches/:id, batches/:id/review, submissions/:id | 3 ảnh lỗi với UUID không tồn tại; không xem như đã kiểm thử UI có dữ liệu |
| Responsive | Admin dashboard/menu, Teacher classes/menu | 4 ảnh viewport 390px |
| Auth | đăng nhập Portal chung | 1 ảnh; Portal không chỉnh sửa |

Tổng 30 ảnh cuối và 6 ảnh xem trước Admin. Dữ liệu local: 11 học sinh, 1 giáo viên, 1 lớp, 2 bài tập; có nguồn seed phát triển. Không khẳng định đây là dữ liệu production.

## Lượt hoàn thiện theo design/redesign.md

- Thực hiện trong nhánh riêng, giữ màu chủ đạo và mascot; giới hạn thay đổi Admin/Teacher theo yêu cầu hiện tại.
- Giữ màn hình công việc gọn, mascot chỉ ở banner chào mừng; không thêm trang/chức năng/metric để trang trông đầy.
- Thống nhất typography, spacing, semantic color, active navigation, loading/empty/error, focus, dialog và responsive.
- Thay biểu đồ Analytics viết sẵn bằng empty state trung thực. Teacher Dashboard lỗi tải dữ liệu hiển thị `—` và cảnh báo thay vì các con số 0 có thể gây hiểu nhầm.
- Bỏ nhãn phiên bản phát hành chính thức và trạng thái sức khỏe hệ thống viết sẵn ở Teacher Settings. Giữ các tính năng và handler sẵn có.
- Dùng asset mobile có sẵn, không cần tạo ảnh AI hoặc thêm dependency.

## Kiểm chứng

Chạy sau các chỉnh sửa UI cuối:

| Kiểm tra | Admin | Teacher |
|---|---:|---:|
| `npm run test:config` | 13/13 | 17/17 |
| `npm run build` | Đạt | Đạt |
| `npm run test:production` | 3/3 | 2/2 |
| `npm run lint` | Không lỗi/cảnh báo | 0 lỗi, 1 cảnh báo có sẵn |

Tổng **35/35 test đạt**. Production build dùng `VITE_API_BASE_URL=https://api.mathvision.example/api/v1` và `VITE_PORTAL_URL=https://mathvision.example` tạm trong tiến trình kiểm tra; không lưu env hoặc triển khai các URL này. Hai build có cảnh báo JS chunk lớn hơn 500kB; không thay đổi cấu hình bundler hoặc dependency trong phạm vi UI.

Cảnh báo Teacher: `src/components/layout/AuthContext.tsx:92` (`react/only-export-components`), file này không bị chỉnh sửa. Console trên trang Users của Admin và Settings của Teacher không có error/warn sau navigation cuối.

Manual browser: login thật qua Portal, mở toàn bộ trang chính; kiểm tra dialog có tên, focus nằm trong modal và Escape trả focus về trigger. Drawer Admin/Teacher 390px có tên, giữ focus và đóng bằng Escape. `document.scrollWidth=innerWidth=390` ở Admin dashboard, Admin users và Teacher classes; bảng users cuộn trong container 356px (nội dung 864px). Đây là kiểm tra viewport, không phải thiết bị vật lý.

## Giới hạn và lỗi có sẵn

1. Teacher Dashboard: service `getDashboard()` đang chờ trường `metrics`, trong khi API trả các trường thống kê ở cấp khác. Giữ nguyên service theo phạm vi UI; không che lỗi bằng dữ liệu mẫu.
2. Admin Analytics chưa có API thống kê thật được kết nối. Không có biểu đồ số liệu cho đến khi nguồn dữ liệu được triển khai.
3. Chưa có batch/submission. Chưa thể kiểm tra đường đi đầy đủ upload → OCR → duyệt/điều chỉnh điểm trên dữ liệu thật trong đợt UI. Các component vẫn dùng handler và logic cũ.
4. Login tại Admin/Teacher chuyển về Portal dùng chung; Portal giữ nguyên. Không thay auth để ép hiển thị form dự phòng.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: thiết kế lại web theo ngôn ngữ thiết kế mobile.
  - Applied to: palette, typography, layout, navigation, spacing, responsive và trạng thái UI.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai giao diện trong hai ứng dụng React hiện có.
  - Applied to: tách context điều hướng UI, tái sử dụng MUI theme, giữ nguyên các data/auth boundary.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: thay đổi navigation, form và dialog.
  - Applied to: accessible names, label association, skip link, keyboard focus, dialog/drawer và reduced motion.

Workflow skills: `superpowers:brainstorming`, `superpowers:verification-before-completion` để bám phạm vi đã được owner duyệt và xác minh trước bàn giao.
