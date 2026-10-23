# Rà soát Loc/Web và sửa lỗi tương tác — 23/10/2026

## Phạm vi tích hợp

Rà soát `origin/Loc/Web` tại `0a9e578fc32e02d6169978c15aa8d08f5ae17d77` trên nền `origin/main` tại `24221919608d398ee30c9fffa19b52171627df0b`. Chủ dự án đã yêu cầu sửa lỗi bấm trong video, kiểm tra nhánh và merge vào dự án. Không push hoặc deploy trong lượt này.

Nhánh thay đổi giao diện Admin và Teacher: theme tím/lavender, font Nunito, sidebar/drawer, topbar, bảng, form, dialog và trạng thái tải/rỗng/lỗi. Không thay đổi quyền truy cập backend. Biểu đồ Analytics bị bỏ trước đây chỉ là số liệu viết sẵn; bản mới hiển thị trạng thái chưa có dữ liệu thật.

## Các lỗi đã sửa trước khi merge

1. **Bấm Chụp bài toán quay về trang chủ.** Trong dự án tồn tại cả `app/camera.tsx` và alias `app/(tabs)/camera.tsx`. Router ưu tiên đường dẫn cùng nhóm tab; SDK 58 chuyển `href: null` thành tab ẩn và tự chuyển tab ẩn về trang chủ. Handler vẫn chạy — log máy chủ có các sự kiện `ACQUIRE`. Đã bỏ alias cùng khai báo tab ẩn và điều kiện tab bar không còn dùng. Giữ nguyên camera gốc, luồng che tên và cắt ảnh.
2. **Menu Admin mất khi tải hoặc lỗi trang chi tiết.** Sidebar mới thu vào drawer trên màn hình nhỏ, nhưng các nhánh loading/error của trang chi tiết lớp/người dùng chưa có topbar mở drawer. Đã giữ topbar trong các trạng thái này. Kiểm thử production thực sự mở drawer lúc request đang chờ, trả 404, mở lại drawer và chuyển về Tổng quan. Hai kiểm thử thất bại trên bundle cũ và đạt sau sửa.
3. **Thống kê Teacher đọc sai DTO backend, lỗi có sẵn.** Service chờ `metrics.*`, trong khi `DashboardResponse` trả `todayTotal`, `processedCount`, `reviewRequiredCount`, `recentBatches`. Đã ánh xạ đúng ba trường, giữ số 0 thật, từ chối dữ liệu sai thay vì đổi thành số 0 giả. Không đổi API hoặc backend. Fixture kiểm thử bundle cũng sử dụng DTO thật và kiểm tra trang không báo lỗi thống kê.

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Student, toàn bộ Jest trong workspace hiện hành SDK 58 | 75 suite, 896 test đạt |
| Định tuyến camera bằng Router thật, không mock `push()` | 3 platform × 4 tab nguồn đều vào camera gốc, giữ tham số bài học |
| Student TypeScript | Đạt |
| Student export Android | Đạt, tạo bundle Hermes |
| Admin typecheck và production build | Đạt |
| Teacher typecheck và production build | Đạt |
| Admin kiểm thử cấu hình/auth | 13/13 đạt |
| Admin production bundle, SSO/logout/menu loading/error | 5/5 đạt |
| Teacher kiểm thử cấu hình/API/auth | 21/21 đạt |
| Teacher production bundle và DTO thống kê thật | 2/2 đạt |
| Lint Admin/Teacher | 0 lỗi; Teacher còn cảnh báo Fast Refresh có sẵn ở AuthContext |
| Các file Student được yêu cầu giữ nguyên | privacy.tsx, crop.tsx, AppHeader.tsx, AppButton.tsx, theme.ts khớp SHA-256 baseline |

Kiểm tra web sử dụng cấu hình URL production mẫu trong tiến trình, không lưu env hoặc deploy. Worktree kiểm tra dùng junction tới dependency đã cài trong workspace chính; không cài lại hoặc thay lockfile. Còn cảnh báo bundle JS lớn hơn 500kB.

## Git và giới hạn xác nhận

Merge cục bộ gồm nhánh Loc/Web cùng các bản sửa trên. Các thay đổi SDK 58, media, backend/OCR và tài liệu đang làm dở trong workspace chính được giữ lại riêng, không tự gộp toàn bộ chúng vào commit merge. Vì vậy kiểm chứng Student SDK 58 phản ánh workspace đang chạy, không phải lời khẳng định một checkout sạch của commit merge đã được nâng SDK.

Bằng chứng tại `report/student-click-merge-20261023/` ở workspace chính: video overview, log Jest, kết quả JSON, so sánh định tuyến trước/sau, TypeScript, Android export, kiểm tra file bảo vệ và kiểm tra bảo toàn thay đổi đang dở. Log web tại `report/loc-web-integration-20261023/`.

Video chủ dự án là bằng chứng lỗi trên điện thoại. Kiểm chứng bổ sung trong lượt này là tự động bằng Router thật và bundle web chạy trong jsdom; không phải thao tác trên điện thoại Android. Cần mở lại ứng dụng để xác nhận camera/quyền camera trên máy thật. Không huấn luyện hoặc thay model; không push/deploy.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân lỗi điều hướng và ánh xạ dữ liệu với thay đổi nhỏ trên hệ thống hiện có.
  - Applied to: bỏ route trùng, giữ menu trong trạng thái lỗi/tải, tái sử dụng kiểm thử production và bảo toàn working tree.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: kiểm tra và sửa tương tác trong React Native/React.
  - Applied to: định tuyến Expo Router, UI loading/error và kiểm chứng bundle React thật sau merge.
