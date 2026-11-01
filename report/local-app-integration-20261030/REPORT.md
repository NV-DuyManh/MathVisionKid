# Bản local đã tích hợp và dọn dẹp — 30/10/2026

## Kết quả

**Bản Kha đã sửa lỗi cùng catalog đã nằm trong ứng dụng chạy tại `E:/MathVisionKid`.** Không cần chạy thư mục worktree kiểm tra để thấy tính năng. Đã khởi động lại backend, AI và Student từ thư mục E, đăng nhập qua trình duyệt và xác nhận nút **Quiz của em** trên trang chủ, mở được danh sách và có một câu đố chờ làm trên tài khoản demo Student.

Đã tích hợp/đối chiếu hash 218 file nguồn từ bản đã kiểm thử. Giữ image MinIO chính thức đã có trên máy thay cho tên image riêng không tồn tại trong nhánh Kha; giữ nguyên các volume dữ liệu. Database đã đi từ v16 tới **v23**, áp dụng đủ 7 migration mới. Có bản dump trước migration và bản sao nguồn trước tích hợp tại `C:/Users/Admin/.codex/backups/mathvision-local-integration-20261030-204502` — dữ liệu riêng này không đưa vào Git.

Đây là tích hợp mã vào working tree và runtime local. **Chưa commit, tạo merge commit hay push lên GitHub.** HEAD của kho vẫn là commit nền cũ; trạng thái Git có thay đổi nguồn mới và các báo cáo cũ bị loại bỏ. Nhánh remote Kha cũng chưa nhận các bản sửa local.

## Cách test

1. Tải lại app trong Expo Go hoặc mở `http://127.0.0.1:8081` trên máy tính.
2. Trên trang chủ, ngay dưới khung Chào em, chọn **Quiz của em**.
3. Tài khoản demo Student có một câu đố thử đang chờ; bấm **Bắt đầu** khi muốn làm. Chưa tự bắt đầu đồng hồ/chấm sao cho câu đố này.
4. Với bài mới thuộc dạng được hỗ trợ, hoàn thành bài học hoặc xem nhận xét bài làm để nhận lời mời luyện Quiz.

Catalog hoạt động ngầm ở máy chủ; không có màn hình catalog dành cho học sinh. Hai lần mở lại cùng một đề qua HTTP thực tế đã hit catalog, tạo phiên mới và giữ tiến độ trống; thời gian đo là **78 ms và 62 ms**. Đây là thời gian mở bài của một đề hỗ trợ tại máy local, không phải độ trễ giọng hoặc số đo trên điện thoại.

## Lỗi khởi động đã phát hiện khi tích hợp

Launcher Kha nạp `PORT` từ dotenv vào Spring; cấu hình đó đang dành cho AI nên Spring đã cố dùng cổng 8000. Đã cố định cổng API local bằng đối số Spring `--server.port=8080`, giữ AI trên 8000. Thêm regression chạy chính câu lệnh khởi động qua stub khi `PORT=8000`; không khởi động dịch vụ thật trong test. Backend hiện nghe đúng 8080; kiểm tra truy cập từ LAN thành công.

## Kiểm chứng trên thư mục E

| Kiểm tra | Kết quả |
|---|---|
| Student Jest đầy đủ | 108 suite, **1.239 test qua**, 70,454 giây |
| AI lesson/reading/quiz/voice/catalog/reliability | **276 test qua**, 2 cảnh báo deprecation, 10,07 giây |
| HTTP thực tế qua Spring và AI | 8 kiểm tra qua: đăng nhập demo, backend quiz v5, chặn chưa đăng nhập, mở bài, kiểm tra hai bước, tạo lời mời quiz, thấy quiz trong danh sách |
| Catalog HTTP thực tế | 2 hit, hai session khác nhau, không có đáp án/tiến độ cũ |
| Alias Admin/Teacher | Đăng nhập 200 và `/me` trả đúng role |
| Launcher batch cách ly | 6 test qua |
| Dotenv/port/identity | Precedence, literal values, allowlist, dọn env; cổng Spring không nhận nhầm 8000; 8 identity case + 8 redirector case + listener lạ được giữ nguyên |
| Runtime diagnostics | **READY_FOR_FULL_DEMO**, LAN pass |
| Migrations trên database local | Phiên bản thành công mới nhất là 23 |
| Git whitespace | `diff --check` qua |

Java toàn bộ của bản nguồn tương ứng đã được kiểm tra ở lượt trước: 463 test, không failure/error, 1 skip; lần này đã compile và boot thật với PostgreSQL local, rồi kiểm tra HTTP. Không báo đã chạy lại toàn bộ Java tại E khi chỉ khởi động runtime ở E.

Đã xác nhận `ffmpeg` đang có trên PATH hệ thống và nhật ký máy chủ tạo được WAV của cả hai giọng Nam Minh/Hoài My trong nền sau khi khởi động. Có một lượt bận được retry rồi thành công; không báo mọi lượt tổng hợp đều lập tức hoặc không thể lỗi. Chưa nghe/kiểm chứng trên Android/iOS thật trong lượt này.

Ảnh giao diện là ảnh thực của trình duyệt chạy app local: `home-quiz.png`, `quiz-library.png`. Bằng chứng máy đọc được: `live-api.json`, `live-catalog.json`, `portal-login.json`, `student-tests.json`, `runtime-diagnostics.log`, `integrated-source-hashes.json`.

## Dọn dẹp

Đã chuyển **153 mục / 16.458 file / 3.639.780.229 byte (~3,64 GB)** vào **Thùng rác Windows**, loại khỏi cây dự án:

- Các web/native export thử nghiệm và bản build lặp lại trong `runtime`, `output`, `scratch`, `.local-artifacts`.
- Các bộ preview, ảnh/bundle UI cũ, ZIP giao diện cũ và báo cáo giai đoạn UI/voice/merge không còn cần cho bản app hiện tại.

Lệnh xóa vĩnh viễn bị cơ chế xét duyệt tự động chặn. Đã dùng phương án có thể khôi phục qua Thùng rác; không đổi phương pháp để xóa vĩnh viễn. Các byte trên là dung lượng logic của file đã chuyển, **không phải dung lượng ổ đĩa đã giải phóng**. Dung lượng chỉ được trả lại khi Thùng rác được làm trống.

Danh sách từng đường dẫn ở `cleanup-candidates.json` và `cleanup-results.json`. Mỗi đường dẫn được xác nhận nằm trong dự án; không xử lý symlink/junction. Không có file mã chạy nào bị xóa; các file tracked bị loại bỏ đều thuộc `report/`.

Giữ lại `demoUI` ở máy và tiếp tục loại khỏi Git; giữ model, dataset, ảnh/fixture/checklist OCR còn được test sử dụng, bằng chứng nghiên cứu, `.env` và khóa riêng, virtualenv, dependency, Git history, database, MinIO/Redis volumes, FFmpeg và các công cụ đang dùng. Giữ báo cáo hiện tại và bằng chứng kiểm chứng/corpus cần thiết; không xóa chỉ vì tên file có ngày cũ.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Tích hợp ít thay đổi, sửa đúng lỗi launcher, phân loại hiện vật có thể tái tạo.
  - Applied to: Đối chiếu nguồn, sửa cổng, dọn có manifest và giữ dữ liệu/công cụ đang dùng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Kiểm chứng Student React chạy từ thư mục chính sau tích hợp.
  - Applied to: Toàn bộ Student suite, khởi động Metro mới, xác nhận tuyến trang chủ/thư viện Quiz.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.1027.30824/skills/computer-use/SKILL.md`
  - Why selected: Cần xác nhận nút mới và luồng đăng nhập trên giao diện thật.
  - Applied to: Browser CUA, đăng nhập, mở Quiz, chụp bằng chứng và giữ trang để chủ dự án test. Không có thao tác kiểm thử thiết bị vật lý.
