# Student Profile, gamification và giao diện điện thoại

## Đọc nhanh

- Student Mobile và Student Web dùng chung hồ sơ từ Spring Boot. Có sửa tên, avatar, danh hiệu đã mở khóa, quyền xuất hiện trên bảng xếp hạng và đăng xuất có xác nhận.
- Sao đến từ Tutor hoàn thành có bước toán được kiểm tra, Quiz hoàn thành đúng trước khi xem lời giải và chế độ Đường đua sao do máy chủ chấm. Flyway V32 thêm bảng hồ sơ, ledger chống cấp trùng và lượt game.
- Cao Thủ bắt đầu tại 112 sao tổng. Thách Đấu yêu cầu ít nhất 162 sao tổng và nằm trong Top 200 toàn hệ thống. Vị trí theo lớp cần quyền thành viên. Bảng công khai dùng bí danh do hệ thống tạo và mặc định tắt.
- Trên Chrome điện thoại, nút Đăng nhập ở đầu Portal nằm trọn một dòng. Nút Lưu hồ sơ có vị trí cố định dưới form cuộn. Hộp thoại Đăng xuất thu gọn và xác nhận bằng nút riêng.
- Bước che tên hỗ trợ dải ngang thấp. Student Web tô trực tiếp lên ảnh JPEG ở kích thước gốc, giữ nhiều vùng che qua bước cắt, và chặn chuyển tiếp nếu xuất ảnh thất bại. Thay đổi vùng che yêu cầu xác nhận lại.

## Ảnh trên Chrome Android 360 px

Các ảnh dùng tài khoản và đề toán tổng hợp, được chụp từ bản cục bộ trên điện thoại thật.

| Portal và hồ sơ | Sau khi chụp hoặc chọn ảnh |
| --- | --- |
| [Nút Đăng nhập](../media/screenshots/portal-header-android.png) | [Vẽ hai vùng che](../media/screenshots/privacy-mask-android.png) |
| [Form sửa hồ sơ](../media/screenshots/student-edit-android.png) | [Hai vùng còn nguyên trong bước cắt](../media/screenshots/privacy-crop-android.png) |
| [Xác nhận đăng xuất](../media/screenshots/student-logout-android.png) | |

## Rank, thành tích và Đường đua sao

Các ảnh dưới đây được chụp bằng Chromium ở 390 px và 1440 px với Spring Boot và PostgreSQL 16 cục bộ. Ảnh Đồng III dùng một sao nhận từ lượt chơi đã được máy chủ chấm. Ảnh Thách Đấu, danh hiệu và hai bảng xếp hạng dùng tài khoản, lớp và ledger tổng hợp được nạp riêng cho nghiệm thu.

| Màn hình | Ảnh bấm để xem đầy đủ |
| --- | --- |
| Hồ sơ và tiến độ lên hạng | [Đồng III, 1/3 sao](../media/screenshots/pr60-profile-rank-mobile.png) |
| Hồ sơ trên màn nhỏ | [Chỉnh sửa](../media/screenshots/pr60-profile-edit-mobile.png) · [Quyền riêng tư](../media/screenshots/pr60-profile-privacy-mobile.png) · [Xác nhận đăng xuất](../media/screenshots/pr60-profile-logout-mobile.png) |
| Rank cao và thống kê | [Thách Đấu trên màn nhỏ](../media/screenshots/pr60-challenger-mobile.png) · [Thách Đấu trên desktop](../media/screenshots/pr60-rank-desktop.png) |
| Nhiệm vụ, danh hiệu và lịch sử | [Nhiệm vụ và đường dẫn vào hoạt động](../media/screenshots/pr60-missions-mobile.png) · [Danh hiệu](../media/screenshots/pr60-titles-mobile.png) · [Lịch sử nhận sao](../media/screenshots/pr60-star-history.png) |
| Xếp hạng theo bí danh | [Toàn hệ thống](../media/screenshots/pr60-leaderboard-global.png) · [Lớp 3A](../media/screenshots/pr60-leaderboard-class.png) |
| Trò chơi | [Câu hỏi do máy chủ tạo](../media/screenshots/pr60-game-question.png) · [Thắng lượt chơi và nhận 1 sao](../media/screenshots/pr60-game-reward.png) |

## Sửa theo review PR #60

- Mũi tên bên cạnh Đăng nhập là trang trí. Playwright dùng tên truy cập `Đăng nhập` trên cả desktop và mobile. Các kiểm tra phiên, đăng xuất, điều hướng lại và hết hạn vẫn được giữ.
- Thanh tiến độ rank công bố giá trị hiện tại và tối đa cho trình đọc màn hình trên web.
- Huy hiệu thay đổi theo bậc ở hồ sơ, thành tích và bảng xếp hạng. Nút Quyền riêng tư mở hộp thoại về quyền xuất hiện trên bảng, có đường dẫn tới cài đặt.
- Student Profile chuyển migration chưa phát hành sang V32. Flyway trên PostgreSQL 16 đã kiểm tra hai đường nâng cấp từ V28 và từ V31 của PR #59, bao gồm bảo toàn dữ liệu, kiểm tra checksum và backup/restore. Tích hợp #59 trước rồi đồng bộ #60 theo [thứ tự migration](student-profile-rewards.md#integration).

Skills applied: mathvision-workflow, mathvision-quality, mathvision-review, mathvision-backend, fixing-accessibility.

## Kiểm thử và giới hạn

- PostgreSQL 16/Flyway và Gradle backend đạt 572 test, 1 skip. Bao gồm khôi phục bản sao, idempotency, cạnh tranh đồng thời, rollback, quyền lớp, đồng điểm và rời Top 200.
- Student Mobile typecheck, lint, 1.468 test Jest và 15 test hợp đồng đạt. Lint có cảnh báo đã có từ trước trong QuizInvitation. Portal build production và 16 test governance đạt.
- Chromium ở 320, 390 và 1440 px với API thật. Kiểm tra lưu tên/avatar, nhận sao từ game và thu hồi phiên. Chrome Android 360 px kiểm tra mở form, lưu và đăng xuất. Kiểm tra điểm ảnh của JPEG 720×780 sau khi kéo bằng touch để xác nhận hai vùng đen và phần đề ngoài vùng che.
- Chưa nghiệm thu Camera/Expo native trên Android. Kiểm tra ảnh che trên Chrome Android dùng ảnh tổng hợp qua luồng chọn ảnh, cùng màn hình che với ảnh chụp; chưa gọi OCR live.
- Năm game vendor hiện lưu kết quả cục bộ và chưa có cơ chế máy chủ xác minh. Các game đó tiếp tục hoạt động, còn Đường đua sao là game được tính sao. Ledger bắt đầu từ V32. Phản hồi nhận sao bằng thông báo đọc được, chưa có hiệu ứng riêng khi lên rank hoặc mở danh hiệu.
- Nếu Spring không ghi được lesson reward sau khi Tutor hoàn thành, Tutor vẫn trả lời thành công theo hợp đồng hiện có. Luồng này chưa có cơ chế tự đối soát lượt thưởng sau khi dịch vụ khôi phục.
- Dùng luồng đăng xuất có sẵn của backend, thu hồi phiên tài khoản khi có mạng. Khi mất mạng, ứng dụng xóa phiên cục bộ.
- Skill đã dùng gồm mathvision-workflow, mathvision-backend, mathvision-quality, mathvision-review, ui-ux-pro-max, react-best-practices, design-system, fixing-accessibility, Computer Use và last30days. Kết quả 30 ngày có tín hiệu hạn chế, nguồn đối chiếu và công thức nằm trong tài liệu rank/reward.

## Nơi review source

- [Spring profile, game và rewards](../../backend/business-api/src/main/java/com/mathvisionkids/api/studentprofile/)
- [Flyway V32](../../backend/business-api/src/main/resources/db/migration/V32__student_profile_rewards.sql)
- [Hồ sơ và API phía Student](../../apps/student-mobile/src/features/student-profile/)
- [Che thông tin riêng tư](../../apps/student-mobile/src/app/privacy.tsx)
- [Header Portal](../../apps/portal-web/src/components/layout/PortalLayout.tsx)
- [Công thức và vận hành](student-profile-rewards.md)

Triển khai cần chạy Flyway V32 trước bản ứng dụng mới. Rollback ứng dụng bằng bản trước, giữ các bảng V32 để bảo toàn dữ liệu.
