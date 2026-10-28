# Tối ưu thời gian chờ và hiệu suất giọng — 28/10/2026

## Kết quả

Đã sửa hàng đợi tạo ngầm, phục hồi âm thanh gần bước hiện tại sau khi bị đẩy khỏi cache, và loại bỏ việc đọc tiến độ trùng phía Student. Giữ nguyên Nam Minh, Hoài My, quyền xem theo bước và thời hạn 45 giây. Không tăng số vị trí tổng hợp hoặc đổi chất lượng giọng để chạy nhanh hơn.

**578 kiểm thử qua trong vòng này:** 345 Python, 217 Student và 16 kiểm thử cấu hình/cache Metro. TypeScript, lint và xuất web/Android thành công. Lint còn hai cảnh báo sẵn có trong `cropRotation.web.ts`, không có lỗi. Chưa đo lại trên Android vật lý; không coi xuất bundle là thử trên điện thoại.

**Chưa đạt độ trễ 1–3 giây ổn định khi phải tổng hợp mới:** phép thử thật với đoạn công khai 64 ký tự ghi nhận Nam Minh lỗi sau 9.219 ms, Hoài My tạo WAV hoàn chỉnh sau 12.453 ms. Tối ưu hàng đợi/cache không bảo đảm được thời gian phản hồi của kết nối tổng hợp bên ngoài.

## Những chỗ chờ thừa đã loại bỏ

### Hàng đợi ngầm tiếp tục dùng vị trí trống

Trước đây, worker chuẩn bị cả bài có thể chờ `Future` của đoạn hiện tại đang được tác vụ khác tạo. Đường chờ này có thể kéo dài tới 34 giây theo giới hạn mã, dù còn vị trí để tạo bước khác. Đây là giới hạn lý thuyết của đường mã cũ, không phải số giây tiết kiệm đã đo trên điện thoại.

Hiện tác vụ tạo ngầm nhường ngay khi gặp đoạn đang được xử lý. Scheduler chọn đoạn đủ điều kiện khác trong cùng bài hoặc bài của học sinh khác. Nếu tất cả đoạn đều đang được tạo, hàng đợi vẫn giữ lịch chờ có giới hạn, tránh tạo trùng và tránh bỏ quên công việc. Yêu cầu nghe chủ động tiếp tục dùng chung kết quả đang tạo và deadline gốc.

Các kiểm thử dùng `Future` chưa hoàn tất và vị trí xử lý bị giữ để xác nhận bước kế tiếp/học sinh khác được xử lý **trước khi** đoạn đang chờ hoàn tất; đoạn hiện tại không bị tổng hợp lần nữa. Không giả lập thành phép đo tốc độ dịch vụ thật.

### Chuẩn bị nhận xét gần thời điểm sử dụng

Sau bước hiện tại, bước tiếp theo của giọng chọn và giọng còn lại cho nội dung hiện tại, scheduler ưu tiên lời nhận xét của câu hỏi sắp trả lời trước các bước ở xa. Nhận xét vẫn là nội dung riêng cho tới khi câu trả lời hợp lệ mở nó; không đưa kịch bản tương lai xuống client.

### Phục hồi có chọn lọc sau khi cache bị đẩy bớt

Trước đây, một mục đã được đánh dấu chuẩn bị xong vẫn nằm trong danh sách hoàn tất sau khi WAV hết hạn hoặc bị loại khỏi cache. Gọi chuẩn bị lại chỉ trả số lượng bị giảm, không tự đưa mục đó trở lại hàng đợi.

Hiện lần lập lịch tiếp theo kiểm tra các mục **đã từng sẵn sàng** ở gần bước hiện tại của giọng đang chọn. Mục thiếu được chuẩn bị lại; không dựng lại toàn bộ bài hoặc cả hai giọng chỉ vì một tệp hết hạn. Giới hạn 72.000 ký tự nguồn và cơ chế dừng sau hai lỗi liên tiếp vẫn áp dụng. Nếu đã hết ngân sách hoặc giọng đang bị dừng vì lỗi liên tiếp, cơ chế này không vượt giới hạn để gọi lại vô hạn.

### Một nguồn tiến độ cho một lượt tải

`LessonNarration` trước đây hỏi `/status` riêng trong khi `downloadNarration` cũng đã hỏi tiến độ. Hiện các màn hình quan sát tiến độ đã được kiểm tra từ cùng lượt tải, qua listener gắn theo từng lượt sử dụng cache. Đóng màn hình bỏ listener tương ứng; lỗi của listener không làm hỏng âm thanh hợp lệ.

Không còn lượt hỏi tiến độ cuối chỉ để mở lại tệp đã có. Chế độ giọng dự phòng được xác định từ lựa chọn chủ động của người dùng, không cần gọi mạng riêng để suy ra nhãn.

### Cùng lời giảng dùng cùng tệp

Khóa cache và nội dung gửi đi đã gộp xuống dòng, tab và khoảng trắng liên tiếp theo cùng quy tắc chuẩn hóa ở backend. Hai bản cùng lời giảng nhưng khác cách xuống dòng dùng chung lượt tải và tệp đã ghi. Phiên, revision, nội dung, giọng và lựa chọn fallback vẫn được phân tách; không bỏ kiểm tra revision để tăng tỷ lệ hit.

Kiểm thử xác nhận:

- Hai cách xuống dòng của cùng lời giảng: một lượt tải, một lượt ghi tệp.
- Mở lại tệp còn trong cache: không thêm tải, ghi tệp hoặc RPC tiến độ.
- Nhiều màn hình theo dõi cùng tác vụ: một downloader/vòng tiến độ, gỡ listener riêng từng màn hình.
- Mục đang tải được ưu tiên vẫn dùng deadline gốc; không khởi động lại mốc 45 giây.

Các con số về số lượt ở trên là kết quả kiểm thử tự động, không phải số đo trên Android thật. Độ trễ giải mã và mở trình phát trên thiết bị vẫn cần được đo riêng.

## Máy chủ phát mã Student

Lúc kiểm tra lại, tiến trình Metro còn lắng nghe nhưng endpoint trạng thái hết thời gian sau 4 giây và 10 giây. Lấy mẫu một giây cho thấy tiến trình dùng khoảng 96,9% của một lõi CPU. Nhật ký có các lượt bundle Android 676.291 ms, web 1.159.847 ms và SSR 1.307.466 ms. Các dòng này là quan sát trong môi trường phát triển, không phải độ trễ giọng hoặc thời gian tải app trên điện thoại.

Đã giới hạn file map ở các đường dẫn gốc không phải mã Student: báo cáo, kết quả runtime, AI/backend, dữ liệu/model và thư mục tạm. Vẫn theo dõi mã app, assets, packages, vendor và phụ thuộc hoisted. Bộ lọc được neo đúng thư mục gốc để không chặn nhầm package bên trong `node_modules` có tên tương tự.

Đã đổi hàng đợi I/O cache từ `Array.shift()` sang chỉ số đầu hàng đợi, giải phóng phần tử đã xử lý và gom gọn định kỳ. Giữ giới hạn 32 thao tác, thứ tự FIFO và cách trả lỗi. Đây là giới hạn **số thao tác I/O**, không phải giới hạn 32 MB.

Benchmark riêng bộ điều phối, cùng tiến trình Node 22, ba cặp chạy 50.000 thao tác trong bộ nhớ: trung vị từ 3.323,91 ms xuống 82,53 ms. Dữ liệu đầy đủ ở `metro-cache-benchmark.json`; tái hiện bằng `node runtime/metro-cache-benchmark-20261028.cjs`. Không được dùng số này làm tốc độ tăng của ổ đĩa, bundle hay Android.

Lượt xuất web đầu với bộ lọc mới bắt được lỗi do tôi thêm cờ `i` riêng cho Windows, trong khi Expo yêu cầu các mẫu ghép có cùng cờ. Đã bỏ cờ không tương thích và thêm kiểm thử dùng hàm `composeMetroIgnorePatterns` thực tế từ Expo đã cài; lỗi cũ bị kiểm thử này bắt lại. Giữ nguyên nhật ký lỗi `runtime/voice-throughput-watchfix-web-export-20261028.log`.

Sau khi sửa và khởi động lại, endpoint trạng thái trả 200; ba mẫu sau khởi động lần lượt 15 ms, dưới 1 ms, dưới 1 ms. Lượt khởi động đầu cần khoảng 10 giây trước khi endpoint sẵn sàng, các lần kết nối chưa được được giữ trong JSON. Lấy mẫu CPU một giây sau khởi động là 6,2%. Đây là quan sát trước/sau **cả sửa mã và restart**, không tách riêng được mức đóng góp của từng thay đổi.

Tuyến `/login` trả HTTP 200, 101.559 byte, sau 7.172 ms trong lượt gọi kiểm tra; không kiểm tra hiển thị, đăng nhập tài khoản hoặc thời gian tương tác trên trình duyệt/điện thoại. Chứng cứ: `metro-status-probe.json` và `student-route-probe.json` trong thư mục báo cáo của vòng này. Xuất web/Android sau sửa cấu hình cũng thành công.

## Phép thử dịch vụ thật

Chạy đúng hai lượt nối tiếp bằng production renderer với một câu tiếng Việt công khai 64 ký tự; không tạo bài học, không gọi mô hình, không gửi nội dung học sinh. Mỗi lượt bị giới hạn 25 giây, có retry ngắn sẵn có của renderer. Không lặp lại tới khi kết quả thành công.

| Giọng | Kết quả | Thời gian |
|---|---|---:|
| Nam Minh | Không nhận được audio hoàn chỉnh, `SpeechNoAudio` | 9.219 ms |
| Hoài My | WAV hoàn chỉnh, 181.326 byte, dài 5,664 giây | 12.453 ms |

Đây không phải phép so sánh trước/sau cùng điều kiện mạng và không chứng minh nguyên nhân là quota hoặc dịch vụ ngừng hoạt động. Nó xác nhận vẫn còn vấn đề ngoài phần chờ thừa vừa sửa. Đường Azure dùng đúng hai giọng đã có từ vòng trước, nhưng chưa có cấu hình xác thực để bật hoặc đo thật. Không tự dùng giọng khác hay tuyên bố đã đạt mục tiêu 1–3 giây.

Chứng cứ: `report/voice-throughput-20261028/provider-probe.json`, nhật ký `runtime/voice-throughput-provider-20261028.log`, WAV công khai `report/voice-throughput-20261028/public-voice-2.wav`. Nhãn mô tả của JSON ban đầu ghi nhầm 61 ký tự, đã sửa thành 64 theo trường `characters` đo được; kết quả/thời gian không đổi và bản gốc được giữ ở `provider-probe.original.json`.

## Xác minh và phạm vi

- Python: 345 passed, nhật ký `runtime/voice-throughput-python-20261028.log`.
- Student: 17 suites / 217 passed, `runtime/voice-throughput-student-corrected-20261028.json` và `.log`.
- Cấu hình/cache Metro: 2 suites / 16 passed, `runtime/voice-throughput-metro-corrected-tests-20261028.json` và `.log`; đây là các test khác với 217 test Student ở lệnh trên.
- Lần gọi bộ kiểm thử Student đầu tiên nhập nhầm đuôi `.ts` cho `lessonListening.test.tsx`, làm một suite không mở được; 213 test thực sự chạy đều qua. Đã sửa lệnh và chạy lại đủ 17 suite thành công; giữ nguyên nhật ký thất bại ban đầu, không tính nó là một lần qua.
- TypeScript: `runtime/voice-throughput-typecheck-20261028.log`.
- Lint cuối: `runtime/voice-throughput-final-lint-20261028.log`; 0 lỗi, 2 cảnh báo cũ.
- Xuất web/Android cuối, sau sửa cấu hình Metro: `runtime/voice-throughput-watchfix-corrected-web-export-20261028.log`, `runtime/voice-throughput-watchfix-android-export-20261028.log`. Dùng URL minh họa khi kiểm tra bundle, không đổi cấu hình dịch vụ thật hoặc triển khai lên mạng.
- `git diff --check` qua, có cảnh báo chuyển LF/CRLF sẵn có.

Đã nạp lại AI runtime với bản sửa và khởi động lại Metro thành công sau sửa cấu hình. Chưa xác nhận điện thoại đã tải lại bundle. Không commit/push, không train model, không sửa phần OCR hoặc các thay đổi ngoài phạm vi đang có trong workspace.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa hiệu năng ở đường dùng chung và giữ giải pháp nhỏ trong các giới hạn hiện có.
  - Applied to: nhường tác vụ đang chạy, ưu tiên hàng đợi, phục hồi cache có giới hạn, tối ưu FIFO và vùng theo dõi tệp; không tăng concurrency hoặc thêm dependency.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: tránh yêu cầu dữ liệu trùng và dùng lại dữ liệu sẵn có trong React.
  - Applied to: tiến độ dùng chung, khóa cache chuẩn hóa, listener theo vòng đời, mở lại tệp không cần RPC.
