# Tăng độ ổn định giọng — 01/11/2026

Đã sửa trực tiếp tại `E:/MathVisionKid`. Phạm vi lần này là ổn định đường tạo/tải giọng và kiểm tra khả năng chạy local; không thay engine, giọng, nội dung bài học hoặc hạ chất lượng âm thanh. Chưa commit/push các sửa đổi này.

## Các lỗi đã xử lý

1. **Tạo giọng cùng lúc có thể mở quá nhiều kết nối.** Trước đây mỗi bản đọc giới hạn hai đoạn, nhưng nhiều worker bài chính, hỏi đáp và Quiz vẫn có thể cộng dồn kết nối. Thêm giới hạn chung bốn lượt gọi nhà cung cấp trong một tiến trình, dùng semaphore chuẩn của Python. Chờ slot nằm trong deadline có sẵn; hủy hoặc lỗi đều trả slot. Không khóa phần mã hóa, đọc cache hoặc toàn bộ lời giảng.
2. **Quiz chưa phục hồi tốt khi dịch vụ bận hoặc đường truyền chập chờn.** Tải lại đúng nội dung/giọng đã được cấp quyền khi gặp lỗi tạm thời; 429 chờ với backoff trong cùng ngân sách **60 giây**, các lỗi mạng/5xx khác tối đa hai lần thử lại. Mỗi HTTP request chỉ được dùng thời gian còn lại, không có vòng chờ 60 giây mới sau mỗi lỗi. Không thử lại lỗi quyền, nội dung cũ hay WAV hỏng; rời màn hình hủy backoff và không gửi yêu cầu muộn.
3. **Hai giọng tranh khởi tạo kho cache mới.** Đo với giọng thật phát hiện `OperationalError` trong catalog. Thử riêng bằng hai thread mở cùng SQLite mới: trước sửa có **5 lỗi `database is locked` trong 12 cặp**. Chỉ tuần tự hóa thiết lập WAL/schema, chờ tối đa 150 ms rồi dùng cơ chế bỏ qua kho sẵn có nếu kho thực sự bận. Chạy lại cùng thử nghiệm: **0 lỗi trong 12 cặp**. Test mới còn kiểm tra ghi/đọc riêng hai giọng và phục hồi sau tranh chấp.

Các sửa đổi chuẩn bị sớm, giữ tệp và thống nhất player Quiz/bài chính từ lượt trước vẫn được giữ. Xem [báo cáo parity](../voice-quiz-parity-20261101/README.md). Khi nội dung đã được chuẩn bị, mở sheet dùng chung tệp/yêu cầu thay vì tạo lại. Không tạo đáp án chưa được server cho phép, không trộn giọng và không bỏ kiểm tra WAV để làm nhanh.

## Đo dịch vụ giọng thật

Đo một văn bản toán tổng hợp ngắn qua cấu hình `edge` hiện có, hai giọng tạo song song. Kho thử riêng trong thư mục tạm; không dùng bài học cá nhân hoặc khóa trong báo cáo.

| Đường gọi trực tiếp AI engine | Giọng nam | Giọng nữ |
| :--- | ---: | ---: |
| Tạo mới qua mạng | 8.728 giây | 7.819 giây |
| Xóa RAM, đọc lại catalog | 7.394 ms | 7.127 ms |
| Đọc lại từ RAM | 0.020 ms | 0.007 ms |

Hai WAV hợp lệ, dài 8,64 và 8,40 giây. File đo: `.local-artifacts/voice-stability-20261101/real-voice-result.json`. Lượt này diễn ra trước bản sửa tranh khởi tạo SQLite; một lượt đọc kho mới đã bị bỏ qua an toàn rồi vẫn tạo âm thanh thành công. Thử nghiệm cache sau sửa nằm tại `catalog-concurrency.json` cùng thư mục.

Đây không phải thời gian bấm đến nghe trên điện thoại, không phải p95 và không phải đánh giá cảm nhận chất lượng giọng. Không so trực tiếp với số đo lượt trước vì văn bản và điều kiện nhà cung cấp khác nhau. Không có cơ sở khẳng định mọi văn bản mới sẽ tạo trong 1–3 giây. Lợi ích nhanh nhất vẫn đến từ chuẩn bị sớm và dùng lại âm thanh đúng nội dung; giới hạn kết nối nhằm tránh tự gây quá tải, chưa có phép đo tải nhiều học sinh thật để định lượng mức tăng thông lượng.

## Kiểm thử cuối

| Kiểm tra | Kết quả |
| :--- | :--- |
| Student TypeScript | Qua |
| Toàn bộ Student Jest | **114 suite / 1.303 test qua**, 40,702 giây |
| Python giọng, Azure, phát âm, chuẩn bị, catalog | **185 test qua**, 6,50 giây; hai cảnh báo FastAPI `on_event` có sẵn |
| Catalog stdlib, cùng lệnh workflow bot | **5 test qua** |
| Tạo hai giọng thật | Cả hai trả WAV hợp lệ |
| SQLite mới, hai giọng đồng thời sau sửa | 12 cặp, không lỗi |
| Xuất web, Android, iOS | Thành công; `.local-artifacts/voice-stability-20261101/export` |
| `git diff --check` | Qua; Git chỉ cảnh báo chuyển dòng LF/CRLF ở một số file sẵn có |

Lệnh Python: `python -m pytest tests/test_neural_speech.py tests/test_quiz_narration.py tests/test_lesson_narration.py tests/test_media_preparation.py tests/test_azure_speech.py tests/test_speech_pronunciation.py tests/test_lesson_catalog.py tests/test_catalog_solver_integration.py -q`, từ `ai/runtime` bằng `.venv` hiện có. Lệnh Student: `npm run typecheck` và `npm test -- --runInBand --silent`.

Export dùng địa chỉ HTTPS theo cấu hình xuất bản sẵn có của dự án, chỉ đặt trong tiến trình kiểm tra. Không sửa khóa hoặc cấu hình triển khai. Đã đọc tài liệu Expo v57 theo quy định; không thay phiên bản package. Không có kiểm thử trên Android/iOS vật lý trong lượt này.

## Local: còn vướng Docker Desktop

**Cập nhật ở lượt kiểm tra tiếp theo ngày 01/11:** Docker đã hoạt động trở lại; đã khởi động và kiểm tra stack local với kết quả `READY_FOR_FULL_DEMO`. Xem [báo cáo hoàn thiện tiếp](../voice-completion-20261101/README.md). Nội dung dưới đây giữ lại tình trạng đã quan sát ở lượt trước.

Không thể kết luận toàn bộ local đã chạy tốt. Lúc kiểm tra, các cổng ứng dụng và dịch vụ dữ liệu đều chưa lắng nghe. Docker Desktop **4.80.0** không khởi động engine được, nhật ký báo:

`starting services: initializing Inference manager ... dockerInference ... The file cannot be accessed by the system`

Sau một lượt phục hồi runtime, lỗi tiếp tục ở **Secrets Engine / engine.sock** với cùng loại lỗi truy cập. Không có PostgreSQL/Redis/MinIO nên chưa chạy lại được kiểm thử tích hợp toàn bộ qua Business API. Các test và mẫu giọng phía trên chạy độc lập được với Docker.

Đã kiểm tra và giữ lại nguyên hai thư mục socket runtime trước khi mở lại Docker, chỉ đổi tên thư mục chứa các endpoint rỗng đã xác minh; không đụng image, container, volume, cơ sở dữ liệu hoặc cấu hình. Ánh xạ đường dẫn được giữ tại `.local-artifacts/voice-stability-20261101/docker-recovery.json`. Việc này chưa chữa được crash. Không factory reset, không unregister WSL, không tự khởi động lại Windows hay thay phiên bản phần mềm hệ thống.

Lỗi tương tự đã được ghi nhận trong [Docker desktop-feedback #460](https://github.com/docker/desktop-feedback/issues/460). Đây là bằng chứng đối chiếu loại lỗi; không phải bảo đảm mọi cách xử lý trong thảo luận sẽ hoạt động trên máy này. Cần khôi phục Docker trước khi xác nhận luồng đăng nhập → mở bài → hỏi đáp bằng toàn bộ dịch vụ local.

## Giới hạn và bước tiếp theo

- Hai giọng mạng vẫn phụ thuộc nhà cung cấp/mạng; cache và retry có giới hạn không thể bảo đảm không bao giờ lỗi. Giọng có sẵn trên thiết bị vẫn là lựa chọn độc lập khi giọng mạng không dùng được.
- Giới hạn bốn kết nối và khóa schema chỉ áp dụng trong một tiến trình. Chạy nhiều replica cần kiểm tra quota và tải tổng thực tế.
- Azure cùng hai giọng đã có đường xử lý và test, nhưng chưa có cấu hình tài nguyên trên máy; không tự coi Azure là dự phòng đang hoạt động.
- Kiểm thử tiếp theo có giá trị nhất là đo chạm-nút-đến-nghe trên Expo Go thật, rồi thử nhiều tài khoản cùng lúc sau khi Docker hoạt động. Không lấy thời gian đọc cache vài ms làm thời gian phản hồi toàn ứng dụng.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân tranh tài nguyên bằng cơ chế chuẩn, không thêm nhà cung cấp hay thư viện.
  - Applied to: semaphore chung, khóa khởi tạo SQLite có giới hạn, dùng lại phân loại lỗi và deadline hiện có.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: bảo vệ quá trình chuẩn bị/tải dữ liệu cho React Native khi mạng chậm hoặc màn hình đổi trạng thái.
  - Applied to: retry Quiz giữ nguyên nguồn, không gia hạn timeout, hủy backoff và kiểm thử không phát sinh yêu cầu muộn.
