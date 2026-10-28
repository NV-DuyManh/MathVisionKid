# Mở bài nhanh, ưu tiên tiếng và bỏ video tự động — 28/10/2026

## Thay đổi chính

Đã thay cơ chế chờ ở màn hình “Chuẩn bị các bước học”. Với đề có thể dựng phần Hiểu đề an toàn từ nguồn, học sinh vào ba câu hỏi đọc đề trước. Trong thời gian đó, mô hình dựng và kiểm tra phần toán ở tác vụ ngầm. Đây là phần Hiểu đề thực tế của bài, không phải nội dung minh họa hoặc màn hình chờ được đổi tên.

Chỉ bật luồng mới sau khi học sinh xác nhận đề; ảnh hoặc văn bản chưa xác nhận không bị tự đánh dấu đã xác nhận. Đề không hỗ trợ ba câu hỏi đọc đề vẫn đi qua luồng dựng bài đầy đủ trước khi mở, không đoán thêm dữ kiện.

Đã bỏ nút video khỏi luồng học Student và tắt toàn bộ tự tạo video trong hàng đợi. Không còn bước xuất MP4 hoặc cache video ngầm tranh tài nguyên với tiếng. API video cũ được giữ tương thích cho yêu cầu trực tiếp từ client cũ; luồng Student mới không gọi nó.

## Cơ chế chạy ngầm hiện tại

1. Máy chủ nhận đề và bài làm đã xác nhận, kiểm tra chủ tài khoản.
2. Trả phần đọc đề lấy trực tiếp từ nguồn; đồng thời bắt đầu tác vụ dựng toán.
3. Giọng cho các bước đọc đề được chuẩn bị ngầm trước khi học sinh mở Nghe giảng.
4. Phần toán vẫn dùng planner, kiểm tra số học/dạy học tại chỗ và mô hình kiểm tra ngữ nghĩa độc lập như trước.
5. Khi toán được duyệt, làm mới hàng đợi giọng cho các bước tiếp theo; giữ giọng đang chọn và ngân sách đã dùng. Các đoạn đã có trong cache được dùng lại.
6. Nếu học sinh tới câu đọc đề cuối khi toán chưa xong, yêu cầu chuyển bước phải chờ kết quả duyệt. Không trả bước toán chưa kiểm tra hoặc báo hoàn thành giả.

Vẫn giữ Nam Minh và Hoài My. Không đổi giọng âm sắc khác để lấy tốc độ, không bỏ bước duyệt, không giảm nội dung giảng để làm đẹp số đo. Giới hạn dựng toán vẫn là 38 giây cho tác vụ; giới hạn chuẩn bị tiếng công khai vẫn là 45 giây, không đổi thành 150 giây.

## Chống dùng nhầm và lãng phí

- Phiên và revision được kiểm tra trước/sau khi chờ phần toán; người khác không được đọc hoặc kích hoạt phiên này.
- Hai yêu cầu trả lời cuối cùng cùng lúc dùng chung tác vụ dựng toán; chỉ một yêu cầu được chuyển revision.
- Đóng một lượt chờ không làm hủy tác vụ chung đang phục vụ phiên hợp lệ.
- Bắt đầu bài mới hủy tác vụ dựng toán chưa xong của bài cũ cùng học sinh.
- Tác vụ cũ hoàn tất muộn không được tạo lại hàng đợi đã bỏ và giành chỗ của bài mới.
- Làm mới phần toán không cắt tiếng của lượt đang nghe; các tác vụ tiếng chưa dùng có thể nhường chỗ.
- Nếu dựng/duyệt toán thất bại, học sinh vẫn giữ đề và bước đang đọc; không tự mở toán. Một lần thử lại chủ động mới có thể tạo lại tác vụ.
- Màn hình mở bài không đợi thêm hoạt ảnh hoàn thành sau khi dữ liệu đã về.

## Phép thử máy chủ thật

Dùng một đề vườn cây công khai tự tạo, đăng nhập vào tài khoản kiểm thử ở backend, gọi qua business API với mô hình và dịch vụ giọng thật. Không ghi token, mật khẩu hay thông tin tài khoản vào báo cáo. Không mô phỏng model/TTS trong phép thử này.

| Quan sát | Kết quả |
|---|---:|
| Mở phần Hiểu đề | HTTP 200, **315 ms** |
| Phần toán còn chuẩn bị khi phần đọc đã mở | Có, chỉ ba bước Hiểu đề được trả |
| Hỏi trạng thái tiếng trước mọi yêu cầu phát | HTTP 200, đang giải mã; 1/1 đoạn tổng hợp xong, elapsed 1.125 ms |
| Trả lời câu đọc đề thứ nhất | HTTP 200, 60 ms |
| Trả lời câu đọc đề thứ hai | HTTP 200, 37 ms |
| Trả lời câu cuối và chờ toán được duyệt | HTTP 200, **5.914 ms** |
| Mở bước toán sau duyệt | Thành công, `preparingMath=false` |

Giữa các câu trả lời, script chờ chủ động hai giây để mô phỏng một khoảng đọc ngắn. Khoảng chờ đó không được cộng vào độ trễ endpoint trong bảng. Trạng thái tiếng được đọc sau khoảng một giây, trước khi gửi bất cứ yêu cầu chuẩn bị/phát tiếng chủ động nào; vì vậy nó xác nhận công việc tạo tiếng đã được chạy ngầm.

**Giới hạn diễn giải:** một mẫu máy chủ không phải số đo trên Expo Go/Android vật lý, không phải trung vị nhiều lượt và không chứng minh mọi đề mở trong 315 ms. Trạng thái giải mã cũng chưa phải thời điểm loa điện thoại phát tiếng. Lượt chuyển cuối còn gần 5,9 giây; không tuyên bố toàn bộ quá trình đã đạt 1–3 giây. Đường dịch vụ giọng vẫn có thể gián đoạn như các vòng trước.

Chứng cứ gốc: `report/student-audio-first-20261028/http-probe.json`; script tái hiện: `runtime/reading-first-http-probe-20261028.py`. Không thay kết quả thất bại trước đây bằng mẫu này; đây là phép thử luồng mới, không phải so sánh trước/sau trong cùng điều kiện.

## Kiểm thử

- Python: **361 passed**, gồm kiểm tra mở đọc khi model đang bị giữ, không lộ toán, chặn bước cuối, sai đáp án/gợi ý không phải chờ, ownership/revision, hai lượt chờ, hủy tác vụ cũ, lỗi duyệt, làm mới cache giọng và không tự xuất video. Nhật ký `runtime/reading-first-final-python-20261028.log`.
- Student: **251 passed / 10 suites**, gồm hợp đồng `preparingMath`, yêu cầu mở đọc, vào bài không đợi hoạt ảnh cuối và chuẩn bị tiếng trước khi mở sheet Nghe giảng. JSON `runtime/reading-first-corrected-student-20261028.json`.
- Java: **145 passed** (95 service, 50 controller), gồm chuyển cờ mở đọc từ tài khoản hiện tại, nhận đúng ba bước khi đang dựng toán và từ chối cờ trạng thái sai kiểu. Nhật ký `runtime/reading-first-final-java-20261028.log`; XML trong `backend/business-api/build/test-results/test/`.
- Tổng ba nhóm trên: **757 kiểm thử**, không cộng các lượt chạy lặp lại.
- TypeScript qua; lint 0 lỗi, còn hai cảnh báo cũ trong `cropRotation.web.ts`.
- Xuất web và bundle Android thành công. Đây không phải cài/chạy trên điện thoại thật.
- `git diff --check` qua; có cảnh báo chuyển LF/CRLF sẵn có.

Lần chạy test Student mới đầu có một lỗi setup: test màn hình chưa cung cấp tài khoản nên cơ chế tạo tiếng ngầm đúng quy tắc đã không chạy. Đã bổ sung AuthContext trong test, giữ nguyên điều kiện phải có chủ tài khoản trong mã; chạy lại đủ 251 test qua. Nhật ký/JSON của lần lỗi vẫn được giữ, không tính thành một lần qua.

Đã nạp AI runtime và business API mới. Client cần tải bundle mới để gửi tùy chọn mở đọc; client cũ giữ luồng dựng bài đầy đủ. Không commit/push, không train model, không sửa các thay đổi OCR hoặc tệp ngoài phạm vi đang có trong workspace.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: giảm phần chờ ở đường xử lý chung và bỏ công việc video không cần thiết.
  - Applied to: tác vụ dựng toán có giới hạn, bảo vệ chuyển bước, vòng đời hàng đợi giọng, bỏ tự xuất/cache video.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: mở phần dữ liệu có thể dùng ngay trong khi công việc độc lập tiếp tục chạy.
  - Applied to: hợp đồng mở đọc của Student, bỏ hoạt ảnh chặn mở bài, bỏ import/entry video và kiểm tra chuẩn bị tiếng trước khi mở trình phát.
