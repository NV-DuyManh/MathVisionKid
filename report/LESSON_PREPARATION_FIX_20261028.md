# Sửa lỗi chuẩn bị hướng dẫn — 28/10/2026

Cập nhật tiếp tối 28/10: lỗi bài lát nền có hai ý và thời gian chờ được xử lý trong `LESSON_BACKGROUND_RELIABILITY_FIX_20261028.md`. Bản mới có chuẩn bị kín trước xác nhận và đọc hiểu hai ý; các số liệu bên dưới là bằng chứng của vòng sửa trước.

## Kết luận từ bằng chứng

Thông báo trong ảnh là nhánh xử lý chung HTTP 503 của Student. Ảnh không kèm mã yêu cầu, nên chưa thể gắn chính xác ảnh lúc 18:09 với một request cụ thể. Nhật ký cục bộ gần đó ghi nhận nhiều nguyên nhân khác nhau, không phải chỉ hết thời gian hoặc hết khóa:

- 17:52:15 và 17:52:34: nội dung sinh ra bị kiểm tra từ chối (hằng số không dựa vào dữ kiện/kết quả trước; lời hướng dẫn ban đầu chưa đủ). Giữ việc từ chối các hướng dẫn chưa đạt.
- 17:53:56: lỗi `steps.3.guidance` có 7 mục, vượt giới hạn 6. Code đã nối `initialGuidance` vào `guidance` trước khi kiểm tra, dù hai mảng riêng đều có thể hợp lệ.
- 17:52–17:53: dịch vụ chính có HTTP 429; dịch vụ dự phòng có 503 và một số 403. 429 chứng minh bị giới hạn yêu cầu ở thời điểm đó; 403 được phân loại lỗi xác thực/quyền. Các mã này không chứng minh mọi khóa hết hạn, hết tiền hoặc hết tổng hạn mức.
- Các timeout tổng hợp giọng cũng có trong log, nhưng thuộc tác vụ âm thanh riêng; không dùng chúng để kết luận nguyên nhân lỗi soạn bài trong ảnh.

Nguồn: `infra/local-runtime/logs/fastapi.err.log`, `fastapi.log`, `spring.log`. Không sao chép khóa, token hoặc danh tính học sinh vào báo cáo.

## Sửa tại dự án gốc E:/MathVisionKid

1. Khi OCR mất dấu chấm trước từ **Hỏi**, nhận ra ranh giới câu hỏi tường minh để mở các bước đọc đề ngay. Chỉ trích nguyên văn, không tự suy ra câu hỏi ngầm; đề nhiều câu hỏi hoặc chưa rõ vẫn bị chặn theo quy tắc hiện có.
2. Giữ riêng hướng dẫn trước khi trả lời và trợ giúp sâu. Hai mảng được kiểm tra theo giới hạn riêng, tránh lỗi do nối thành 7–9 đoạn. Không cắt bỏ nội dung để làm vừa và không bỏ kiểm chứng toán/đáp án độc lập.
3. Truyền nhóm lỗi an toàn từ Python qua Java tới Student: giới hạn yêu cầu, timeout, cấu hình, nội dung chưa đạt kiểm tra hoặc đang bận. Java chỉ nhận các giá trị nằm trong danh sách cho phép; không chuyển lỗi thô hoặc tên nhà cung cấp cho học sinh. Khi soạn toán ngầm thất bại, giữ nhóm lỗi đó khi học sinh thử bước tiếp theo.
4. Thông báo lỗi của Student giải thích tình trạng và giữ đề/bài làm; không đồng loạt yêu cầu kiểm tra đề khi dịch vụ lỗi. Giữ giới hạn chờ 45 giây, phép kiểm soạn toán 38 giây; không tăng lên 150 giây. Không quét khóa để vượt giới hạn hoặc tự gọi lại vô hạn.
5. Nhật ký mới ghi cách mở bài (đọc trước/đợi bản đã kiểm duyệt) và nhóm lỗi; không ghi nguyên đề trong dòng chẩn đoán mới.

Các thay đổi thử của PR Khả ở worktree review và hai script OCR sửa riêng được giữ nguyên. Không merge, train, commit hoặc push trong vòng sửa lỗi này.

## Xác minh

- **415 kiểm thử Python**, gồm soạn bài, đọc đề, kiểm tra toán, chuẩn bị tiếng, phân loại lỗi và an toàn nội dung: đạt.
- **140 kiểm thử Student / 3 suite**: đạt, gồm giữ nguyên đề, giải thích lỗi an toàn và chuẩn bị giọng.
- **142 kiểm thử Java** (94 service, 48 controller): đạt, gồm danh sách nhóm lỗi an toàn và không chuyển lỗi thô.
- Tổng **697 kiểm thử**, không cộng lặp các lượt chạy lại. TypeScript đạt; lint 0 lỗi, 2 cảnh báo cũ ở cropRotation.web.ts. Xuất bundle Android đạt. `git diff --check` đạt.
- Phép thử với **dịch vụ AI thật**, một đề vườn cây tổng hợp giống dữ kiện ảnh và cố ý bỏ dấu chấm trước Hỏi: mở phần đọc trước trong **6,3 ms tại runtime Python**, phần toán đã kiểm duyệt hoàn tất sau **15.300,1 ms**, kết quả **60 cây**. Có một lượt sửa do model đưa kết quả ra phần ban đầu. Đây không phải thời gian truyền mạng/mở tiếng trên điện thoại, không phải p95 và không chứng minh hết lỗi trong mọi trường hợp.
- Tại thời điểm kết thúc vòng sửa mã, chưa kiểm chứng trên điện thoại thật và chưa nạp lại dịch vụ (8000/8080/8081 chưa kết nối được). Trạng thái này đã được cập nhật ở mục khởi động bên dưới; `verification.json` giữ nguyên bằng chứng của vòng kiểm thử trước.

Bằng chứng: `lesson-preparation-fix-20261028/verification.json`, `live-probe.json`; log chi tiết ở `runtime/lesson-reliability-*20261028.log`.

## Đã nạp bản sửa để chủ dự án thử — tối 28/10/2026

- Khởi động bộ dịch vụ bằng launcher hiện có tại `E:/MathVisionKid`, cùng máy chủ Student ở đúng thư mục dự án. Sao lưu nhật ký trước khi launcher mở lại các tệp log. Không sửa mã ứng dụng, cấu hình model, khóa dịch vụ hoặc dữ liệu học sinh trong bước khởi động.
- Kiểm tra HTTP: Business API báo `UP`; AI báo `ok`; kiểm tra sẵn sàng báo `ready` với worker hoạt động; máy chủ Student trả `packager-status:running`. Các tiến trình phục vụ đều chạy trong dự án gốc.
- Hash của cả tám tệp sửa/kiểm thử khớp bản đã kiểm chứng. Tải bundle màn bài học Android từ máy chủ đang chạy thành công HTTP 200, có xử lý mới cho `TUTOR_TIMEOUT` và `LESSON_VALIDATION_FAILED`.
- Manifest Android và iOS đều trả HTTP 200, đúng MathVisionKid, SDK 58 và địa chỉ mạng hiện tại. Business API truy cập được qua địa chỉ mạng của máy. Chẩn đoán launcher kết luận `READY_FOR_FULL_DEMO`.
- Tạo mã QR từ thư viện QR đã cài cùng Expo; giải mã lại ảnh để xác minh đúng kết nối hiện tại. Ảnh: `lesson-preparation-fix-20261028/test-on-phone-20261028.png`.
- Chủ dự án có thể mở lại app và tạo bài mới để thử. Phiên học cũ có thể không còn tồn tại sau lần khởi động lại. Chưa có kết quả thử trên điện thoại thật sau lần nạp này; không coi kiểm tra HTTP/bundle là bằng chứng thiết bị.
- Bằng chứng cập nhật: `lesson-preparation-fix-20261028/runtime-applied.json`. Không commit/push.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân ở luồng soạn bài và giữ giải pháp nhỏ, có kiểm chứng.
  - Applied to: ranh giới trích câu hỏi, mảng hướng dẫn riêng, phân loại lỗi Python/Java, giới hạn thời gian và kiểm thử; tái sử dụng launcher để nạp bản sửa, xác minh dịch vụ/bundle và kết nối điện thoại.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: xử lý kết quả API và trạng thái lỗi màn học React Native.
  - Applied to: thông báo an toàn theo nhóm lỗi, giữ dữ liệu và kiểm thử hành vi thử lại.
