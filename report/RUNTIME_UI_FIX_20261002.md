# Sửa lỗi nhận dạng và cập nhật Student Mobile — 02/10/2026

Luồng gửi bài nhiều dòng đã hoạt động qua backend MathVision đang chạy. Trang chủ được cập nhật theo ảnh mẫu, dùng đủ bảy PNG chủ dự án cung cấp. Các màn chờ nhận dạng dài dùng thanh ngang, thời gian đã chờ và nút quay lại.

## Nguyên nhân và sửa lỗi

Cổng 8080 trước đó thuộc tiến trình backend từ `E:/HandAI/backend`, trong khi bộ khởi động MathVision coi bất kỳ cổng đang mở nào là dịch vụ đúng. PostgreSQL vẫn ở Flyway V15, thiếu cột `gemini_confidence_source`; ba lỗi database khớp thời điểm HTTP 500 trong log chủ dự án gửi.

Đã xác minh tiến trình, dừng đúng backend cũ và khởi động backend từ `E:/MathVisionKid/backend/business-api`. Flyway tự áp dụng migration V16 có sẵn, không sửa migration hoặc checksum. FastAPI của MathVision được giữ chạy. Không chỉnh sửa mã nguồn dự án HandAI riêng.

- Bộ khởi động kiểm tra đường dẫn dự án và entry point trước khi sử dụng Spring/FastAPI đang chạy. Tiến trình không thuộc dự án bị báo xung đột, không bị tự động dừng.
- Công cụ chẩn đoán từ chối backend khỏe nhưng thuộc checkout khác.
- JSON phản hồi nhiều dòng thống nhất tên `isTestData` với hợp đồng mobile và luồng một dòng.
- Hủy nhận dạng gửi tín hiệu abort; kết quả của yêu cầu cũ không ghi đè trạng thái mới. Hủy gửi hoặc thử lại sau lỗi giữ nguyên ảnh và khung đã chỉnh.
- Lỗi HTTP dự kiến có thông báo dễ hiểu, không đưa lỗi kỹ thuật vào LogBox trên màn học sinh.
- Tách ba hàm tính khoảng cách văn bản thuần túy để bỏ vòng import analytics store → metrics → store; công thức và API export cũ được giữ nguyên.

Chi tiết và bằng chứng backend: [BACKEND_RUNTIME_REPAIR.md](E:/MathVisionKid/report/runtime_ui_fix_20261002/BACKEND_RUNTIME_REPAIR.md).

## Giao diện và phản hồi khi chờ

- Trang chủ dùng nền tím nhạt, tiêu đề xanh đậm, linh vật ngôi sao, nút chụp màu tím, ba thẻ tiện ích, chuỗi học tập và bài học gợi ý theo ảnh mẫu.
- Bảy PNG được sao chép nguyên bản, giữ nền trong suốt; SHA-256 khớp tệp đính kèm. Không tạo ảnh thay thế hoặc thêm thư viện.
- Các lối vào nhận dạng chữ viết, phép tính, chọn ảnh, lịch sử, tiến bộ, bài học theo lớp, mẹo, quyền riêng tư và hồ sơ vẫn hoạt động. Thanh điều hướng dùng ba màn hiện có.
- Chuỗi học tập tính từ bài nhận dạng đã xác nhận lưu trên thiết bị, loại trừ dữ liệu mẫu/benchmark/ngày tương lai. Tài khoản chưa học hiển thị trạng thái trống, không dùng con số năm ngày từ ảnh mẫu.
- Màn phát hiện dòng, gửi nhiều dòng, tải kết quả và xử lý phép tính dùng thanh ngang. Thời gian chờ là thời gian thực; không hiển thị phần trăm hoặc thời gian hoàn thành ước lượng khi backend không cung cấp tiến độ.
- Tôn trọng reduced motion; nút quay lại có thể cuộn tới trên màn ngang thấp. Khung ảnh dùng kích thước màn hiện tại và vùng an toàn khi xoay.

Ảnh kiểm tra: [trang chủ](E:/MathVisionKid/report/runtime_ui_fix_20261002/ui/home-375x812.png), [thanh nhận dạng](E:/MathVisionKid/report/runtime_ui_fix_20261002/ui/recognition-detection-bar-375.png), [màn gửi bài](E:/MathVisionKid/report/runtime_ui_fix_20261002/ui/recognition-submit-bar-375.png).

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Mobile Jest | 27 suite, 262 test đạt |
| Backend, profile test/H2 riêng | 22 suite, 154 test đạt; không lỗi hoặc bỏ qua |
| TypeScript `--noEmit` | Đạt |
| Expo web export | Đạt, 27 route |
| Expo Android export | Đạt; Hermes bundle và cả bảy ảnh được đóng gói |
| Nhận diện đúng tiến trình runtime | 8 trường hợp đạt; listener lạ được giữ chạy |
| Chẩn đoán danh tính backend | 3 trường hợp đạt |
| HTTP thực: phát hiện → tạo bài → đọc → phản hồi | 200 → 201 → 200 → 200, ảnh chủ dự án có 9 dòng |
| Kiểm tra quyền và đồng ý riêng tư | Chưa đăng nhập 401; học sinh khác 404; không đồng ý 400 |
| Chromium, 375×812 / 430×932 / 844×390 | Không tràn ngang; ảnh tải đủ, điều hướng và modal hoạt động |
| Hủy và ba lần thử gửi lỗi 500 trên trình duyệt | Giữ khung đã chỉnh; không page error hoặc LogBox lỗi debug |

Kiểm chứng HTTP thực đi qua business API, AI runtime, PostgreSQL và MinIO. Ảnh lưu có SHA-256 khớp ảnh tải lên. Bài kiểm thử đánh dấu `isTestData=true`, phản hồi `SKIPPED`, không dòng nào đủ điều kiện huấn luyện. Lần cuối mất 3,72 giây với cache đã nóng; đây không phải cam kết tốc độ với ảnh mới.

Kiểm chứng giao diện dùng Chromium/Expo web, với fixture cho `/me`, phát hiện và gửi bài. Nó độc lập với bài kiểm chứng HTTP thực. Android export chứng minh đóng gói được mã và tài nguyên, chưa chứng minh hoạt động trên điện thoại thật. Stress CSS chữ 200% không mô phỏng native fontScale. Chín ca segmentation AI đã biết từ lần kiểm tra trước chưa được đánh giá lại trong lần sửa runtime/UI này; không thay model hoặc huấn luyện.

Bằng chứng có cấu trúc: [verification.json](E:/MathVisionKid/report/runtime_ui_fix_20261002/verification.json), [HTTP thực](E:/MathVisionKid/report/runtime_ui_fix_20261002/live-recognition-http.json), [QA trình duyệt](E:/MathVisionKid/report/runtime_ui_fix_20261002/ui/browser-checks.json), [đối chiếu ảnh](E:/MathVisionKid/report/runtime_ui_fix_20261002/asset-manifest.json).

## Trạng thái bàn giao

Kiểm tra cuối phát hiện và đã khôi phục một gián đoạn hạ tầng mới: Docker engine nhận yêu cầu dừng bình thường lúc 23:20:44, sau đó không còn chuyển tiếp kết nối database/cache/storage. Backend vẫn đúng checkout MathVision nhưng health database chuyển sang DOWN. Docker Desktop khởi động lại gặp endpoint tạm `Docker/run/dockerInference` bị kẹt.

Đã xác minh `C:/Users/Admin/AppData/Local/Docker/run` là thư mục runtime thường, chỉ có ba endpoint IPC rỗng; chuyển nguyên thư mục sang `run-stale-20261002`, không ghi đè, giữ các endpoint cũ và tạo thư mục runtime mới. Docker Desktop khởi động bình thường trở lại. Không xóa/reset volume, VHD hoặc settings. [Báo cáo tương tự trong repository Docker](https://github.com/docker/desktop-feedback/issues/527) là nguồn tham khảo; chẩn đoán trên máy này dựa vào log và kiểm chứng thực tế, không suy luận ai đã yêu cầu dừng hoặc nguyên nhân thiếu RAM.

Kiểm tra sau khôi phục: backend và database đều UP, bài kiểm thử 9 dòng vẫn đọc được qua HTTP 200, phản hồi SKIPPED giữ nguyên và SHA-256 ảnh lưu khớp bằng chứng trước gián đoạn. Không tạo bài mới trong lần kiểm tra bảo toàn dữ liệu. Bằng chứng: [thư mục runtime](E:/MathVisionKid/report/runtime_ui_fix_20261002/docker-run-quarantine.json), [bảo toàn dữ liệu](E:/MathVisionKid/report/runtime_ui_fix_20261002/data-preservation-after-recovery.json).

Backend MathVision, dịch vụ nhận dạng và bộ phục vụ ứng dụng điện thoại đang chạy từ checkout này. Chủ dự án mở lại hoặc tải lại ứng dụng để nhận bản mới. Chưa xác nhận trực tiếp trên điện thoại của chủ dự án sau sửa. Các kiểm chứng được chốt trước bước commit/push theo yêu cầu riêng của chủ dự án. Đây là khôi phục runtime hiện tại; không phải bản vá lỗi Docker/Windows được báo cáo bên ngoài dự án.

File PID và bản export là dữ liệu runtime của máy, không phải mã nguồn bàn giao. Ignore thư mục PID và web export; ngừng theo dõi file PID Celery trong Git nhưng giữ nguyên file trên máy cho tiến trình hiện chạy.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân runtime và hợp đồng dữ liệu với thay đổi nhỏ, dùng cơ chế sẵn có.
  - Applied to: kiểm tra tiến trình, chẩn đoán backend, Flyway, JSON, abort và bỏ vòng import.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai và kiểm tra component React/React Native, trạng thái bất đồng bộ.
  - Applied to: HomeDashboard, RecognitionProgress, trạng thái yêu cầu và tham chiếu tài nguyên tĩnh.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: chuyển ảnh tham chiếu thành giao diện di động và cải thiện phản hồi khi chờ.
  - Applied to: màu, bố cục, tài nguyên chủ dự án, vùng chạm, reduced motion và kiểm tra các kích thước màn.

Đã đọc tài liệu Expo đúng phiên bản trước khi sửa mã: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/).
