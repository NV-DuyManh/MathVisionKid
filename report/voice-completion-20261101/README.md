# Hoàn thiện tiếp luồng giọng và kiểm tra local — 01/11/2026

Đã sửa tại `E:/MathVisionKid`, nạp lại dịch vụ AI của lượt kiểm tra và giữ Student đang chạy để chủ dự án thử. Không commit/push, không huấn luyện model, không thay hai giọng, không thêm video và không thay nội dung giao diện đã chọn.

## Hai lỗi tìm được và đã sửa

### Lựa chọn giọng mới có thể bị kết quả đọc cũ ghi đè

Trong hook chuẩn bị âm thanh, việc đọc lựa chọn đã lưu là bất đồng bộ. Nếu có thay đổi lựa chọn trong lúc chờ, giá trị đọc cũ có thể được dùng làm ưu tiên chuẩn bị. Test mới tái hiện được trước sửa. Hook hiện lấy lựa chọn mới nhất sau khi lượt đọc hoàn thành; vẫn chuẩn bị cả hai giọng, không khởi động lại hai bản đọc chỉ vì đổi ưu tiên.

File: `apps/student-mobile/src/features/tutoring/NarrationPreparation.tsx`; kiểm thử trong `narrationPreparation.test.tsx`.

### Giọng cho câu trả lời có thể chờ sau các bước tương lai

Phép thử HTTP thật đã tạo được bản chép lời và câu trả lời nhưng có một lượt chờ âm thanh hết **55 giây của harness**. Đây không phải bằng chứng hết key hoặc giới hạn 60 giây của app bị thay đổi.

Kiểm tra hàng đợi cho thấy yêu cầu chuẩn bị **nội dung đã công bố** mang cờ prefetch bị xếp chung ưu tiên với phần **bước tương lai chưa mở**. Khi các slot bận, nó không yêu cầu những đoạn không liên quan nhường chỗ; khoảng tạm ngừng dành cho việc nhường chỗ cũng chặn chính công việc chuẩn bị đoạn đang cần.

Đã sửa trong `ai/runtime/app/tutoring/narration.py`:

- Yêu cầu chuẩn bị đoạn đang dùng có thể nhường các job dự đoán không liên quan khi hết chỗ.
- Giữ nguyên hai giọng của cùng đoạn và các job có người đang nghe.
- Khoảng tạm ngừng chỉ chặn worker chuẩn bị bước tương lai, không chặn job chuẩn bị đoạn đã được cấp quyền.
- Giữ nguyên kiểm tra tài khoản, phiên, revision và danh sách văn bản đã công bố **trước** khi tác động hàng đợi. Không cho yêu cầu giả tạo giành ưu tiên.

Ba ca liên quan ưu tiên đã thất bại trước sửa và qua sau sửa; có thêm ba ca kiểm tra tài khoản khác, revision cũ, nội dung chưa công bố không được hủy hay đổi ưu tiên công việc nào. Không tăng số slot, deadline, tốc độ đọc hay nới kiểm tra WAV.

## Kiểm tra dịch vụ thật trên local

Docker engine đã phản hồi khi bắt đầu lượt này. Không có bằng chứng xác định vì sao nó hồi phục, nên không quy kết cho cách phục hồi của lượt trước. Đã dùng launcher hiện có để mở các dịch vụ; chỉ khởi động lại tiến trình AI do lượt này mở sau khi xác minh PID, đường dẫn và cây tiến trình. Không dừng dịch vụ khác hoặc đụng volume/cơ sở dữ liệu.

Kết quả cuối từ `tools/diagnostics/check_runtime.py`: **READY_FOR_FULL_DEMO**. Docker, PostgreSQL, Redis, MinIO, Spring, FastAPI, Celery, ba portal và Student đều qua; kiểm tra truy cập mạng nội bộ qua. Trang Student, health API và health AI trả HTTP 200. Đây là kiểm tra trạng thái và HTTP trên máy phát triển; không phải chứng nhận mọi chức năng hoặc điện thoại vật lý.

### Bài thử và chuẩn bị trước khi bấm nghe

Dùng đề tổng hợp mới: một vườn có 1/4 số cây là táo, 2/5 là xoài, còn lại cam, biết có 21 cây cam. Đăng nhập qua Business API và mở bài bằng đúng đường Student, không giả owner/token hoặc gọi trực tiếp engine thay cho API.

| Quan sát trước sửa ưu tiên hỏi đáp | Kết quả |
| :--- | ---: |
| Mở bước đọc đề | 132,94 ms |
| Giọng nữ sẵn sàng trước Play | 12,052 giây |
| Giọng nam sẵn sàng trước Play | 18,272 giây |
| Tải WAV đã sẵn sàng | Nam 17,48 ms; nữ 8,98 ms |
| Phát lại/đổi giọng, ba HTTP lượt mỗi giọng | Trung vị nam 21,24 ms; nữ 28,62 ms; tối đa 34,99 ms |

Các WAV đúng định dạng, có tín hiệu khác không, không thấy sample bị clipping trong mẫu. Ba lượt phát lại mỗi giọng trả cùng bytes. Đây xác nhận **có chuẩn bị trước Play**, không có nghĩa lần tạo mới dưới ba giây. Số liệu: `.local-artifacts/voice-completion-20261101/results.json`.

### Bản chép lời, hỏi đáp và giọng trả lời

- Upload WAV tổng hợp khoảng mười giây qua endpoint chép lời: trả HTTP 200, ra 124 ký tự trong **942,67 ms**. Không phải bản ghi micro hoặc đo chất lượng nhận dạng giọng trẻ em trên thiết bị thật.
- Câu hỏi “Em cần tìm điều gì trong bài này?” trả lời phù hợp: “Em cần tìm tổng số cây trong vườn.” Lượt trước sửa hàng đợi mất 598,48 ms; lượt sau sửa mất 625,69 ms. Mẫu nhỏ này không phải p95 hay cam kết cho câu hỏi bất kỳ.
- Sau sửa ưu tiên, chuẩn bị hai giọng trả lời song song khi phần tương lai của bài vẫn đang chuẩn bị: **nam 18.227,36 ms; nữ 1.667,76 ms**. Cả hai WAV hợp lệ, dài 25,75 và 26,28 giây. Trạng thái cuối ready, hoàn thành 3/3 đoạn ở mỗi giọng.
- Tải tệp sau chuẩn bị: **16,29 ms / 7,58 ms**; tải lại đúng tệp: **7,41 ms / 8,68 ms** (nam/nữ). Không gọi đây là thời gian chạm nút đến nghe.
- Yêu cầu âm thanh không đăng nhập bị chặn HTTP 401. Nội dung chưa được công bố bị chặn HTTP 400 trong phép thử bài đọc.

Hai lượt trước/sau không phải thí nghiệm hiệu năng đối chứng: cache, trạng thái nhà cung cấp và số công việc đang chạy có thể khác. Dùng test tái hiện để xác nhận lỗi ưu tiên; dùng HTTP thật để kiểm tra luồng sau sửa thành công. Không lấy chênh lệch 55 giây/18 giây làm mức tăng tốc bảo đảm.

Bằng chứng ở `.local-artifacts/voice-completion-20261101/`: `qa-flow-before-fix.json`, `qa-flow-after-fix.json`, `reply-final-progress.json`, `runtime-final.txt`, `http-health.json`. Lượt chạy harness đầu sau sửa vấp mã hóa console Windows khi in tiếng Việt, đã sửa stdout UTF-8 rồi chạy lại; lỗi harness này không tính là lỗi ứng dụng. Không lưu token/khóa vào các file kết quả.

## Kiểm thử và xuất bản kiểm tra

| Phạm vi | Kết quả |
| :--- | :--- |
| TypeScript Student | Qua |
| Toàn bộ Jest Student sau sửa lựa chọn giọng | 114 suite, **1.304 test qua**, 50,172 giây |
| Backend Tutor service/controller, Quiz integration/timer, Auth controller | **195 test qua**, Gradle thành công 35 giây; dùng profile kiểm thử, không ghi dữ liệu học sinh thật |
| Python giọng, chuẩn bị, phát âm, Azure, catalog | **188 test qua**, 7,84 giây sau sửa ưu tiên; hai cảnh báo FastAPI `on_event` có sẵn |
| Ba ca bảo vệ quyền của prefetch thêm sau lượt Python trên | **3 test qua** |
| Catalog stdlib, cùng lệnh workflow bot | **5 test qua** |
| Xuất web, Android, iOS | Thành công; output `voice-completion-20261101/export` trong `.local-artifacts` |
| Whitespace diff | Qua |

Đã đọc tài liệu Expo v57 theo yêu cầu repo. Không thay dependency; biến địa chỉ HTTPS khi export chỉ tồn tại trong tiến trình kiểm tra, không thay cấu hình chạy local hay khóa.

## Tình trạng còn lại

App local hiện đã mở để thử tại [Student](http://127.0.0.1:8081/login). Giọng mới qua mạng vẫn có độ trễ và rủi ro dịch vụ bên ngoài; mẫu nam sau sửa còn mất khoảng 18 giây. Không có cơ sở nói “hoàn hảo”, “không bao giờ lỗi” hoặc mọi nội dung mới dưới 1–3 giây. Không giảm chất lượng hay lén đổi sang giọng thiết bị để đạt số đo nhanh. Khi đã chuẩn bị và tải sẵn tệp, đường phát lại dùng cache như mong muốn.

Chưa đo chạm-nút-đến-nghe trên điện thoại thật hoặc tải đồng thời nhiều học sinh. Azure vẫn chưa có cấu hình tài nguyên nên không được coi là dự phòng đang hoạt động. Các việc này phải có bằng chứng riêng trước khi cam kết chất lượng phát hành.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa trực tiếp quy tắc ưu tiên hiện có và dùng lại launcher/test, tránh thêm scheduler hoặc dịch vụ mới.
  - Applied to: phân biệt đoạn đã công bố với bước tương lai, bảo toàn slot/deadline/quyền; kiểm thử tái hiện và chẩn đoán local.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: trạng thái lựa chọn và công việc bất đồng bộ của React Native.
  - Applied to: lấy lựa chọn mới nhất sau await, giữ hai bản âm thanh đang chuẩn bị, test kết quả lưu trữ trả về muộn.
