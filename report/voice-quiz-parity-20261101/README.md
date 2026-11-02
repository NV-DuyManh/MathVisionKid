# Giọng Quiz và bài chính — 01/11/2026

## Kết quả và nguyên nhân

Quiz ở bản local trước tác vụ đã dùng giao diện `LessonNarration`, nhưng vẫn gọi tải âm thanh riêng qua `audioLoader` mỗi lần mở sheet. Không có provider giữ tệp hay hook chuẩn bị hai giọng ở màn hình Quiz; bởi vậy giao diện giống nhưng thời gian chờ khác bài chính.

Đã sửa trực tiếp tại `E:/MathVisionKid`:

- Màn hình Quiz giữ cache và chuẩn bị đồng thời hai giọng của nội dung **đã được server công bố**. Không tạo âm thanh placeholder khi chưa bấm bắt đầu, không tải lời giải chưa được mở quyền.
- `QuizVoice` dùng đúng `LessonNarration`, `VoicePicker`, `AudioPlayback`, thanh tua, tua ±10 giây, nghe từ đầu, tốc độ và lỗi gọn của bài chính. Giọng có sẵn vẫn phát trên thiết bị; khi lựa chọn này được lưu, không chạy chuẩn bị hai giọng mạng.
- Bấm nghe lúc đang chuẩn bị dùng chung yêu cầu đang chạy. Đóng sheet không hủy công việc mà màn hình còn cần. Mở lại hoặc đổi sang giọng đã sẵn sàng dùng lại tệp, không ghi WAV/tạo URL lại.
- Bộ cache chung nhận hàm tải được cấp riêng cho Quiz; không gọi nhầm endpoint Tutor để ưu tiên Quiz. Cache được tách theo tài khoản, câu chữ và nội dung QUESTION/SOLUTION; đổi tài khoản xóa các tệp giữ của tài khoản trước.
- Hỏi đáp Quiz có provider Tutor riêng. Không đưa phần trả lời của Tutor vào hàm tải câu hỏi/lời giải Quiz.
- Cả bài chính và Quiz hiện nút Phát ngay khi bộ giải mã sẵn sàng, bỏ thời gian chờ hiệu ứng thanh tiến độ kết thúc.
- Máy chủ Quiz dùng thêm catalog âm thanh riêng theo tài khoản, văn bản chính xác, giọng và chính sách xử lý như bài chính. Cache RAM bị xóa/khởi động lại không buộc gọi nhà cung cấp nếu tệp catalog còn hợp lệ. Kho không dùng được vẫn về đường tạo giọng cũ; WAV không hợp lệ không được lưu.

Giữ đúng hai giọng neural hiện tại; không đổi giọng để lấy số đo nhanh, không cắt bớt lời giải hay hạ chất lượng âm thanh. Giới hạn chờ giao diện vẫn **60 giây**. Quyền đọc câu hỏi/lời giải vẫn do Spring kiểm tra trước khi gọi máy chủ AI; cache không mở quyền xem đáp án.

## Đo dịch vụ thật

Đo trực tiếp engine trên máy này, provider `edge`, một văn bản toán tổng hợp ngắn, hai giọng tạo song song. Dữ liệu thử và SQLite nằm trong thư mục tạm, không dùng bài riêng của học sinh. Không có mock provider trong phép đo này.

| Đường đọc | Giọng nam | Giọng nữ |
| :--- | ---: | ---: |
| Tạo lần đầu, qua mạng | 22.763 giây | 7.757 giây |
| Xóa cache RAM, đọc lại catalog | 7.780 ms | 7.230 ms |
| Đọc cache RAM tiếp theo | 0.022 ms | 0.009 ms |

Cả hai lượt tạo trả WAV hợp lệ, dài lần lượt 7,44 và 7,37 giây. Nhật ký trong lượt đo có `NoAudioReceived` trước khi thử lại thành công; log cảnh báo này không đủ để gán chắc chắn cho một giọng cụ thể. Lần đầu còn phụ thuộc nhà cung cấp; không có cơ sở khẳng định mọi văn bản mới đều tạo trong 1–3 giây.

Số trên **không phải** thời gian chạm nút đến lúc nghe trên Android/iOS/web: chưa bao gồm HTTP Business API, truyền tệp tới điện thoại hoặc khởi động bộ giải mã tại thiết bị. Mẫu nhỏ này không phải p95, không phải nghiên cứu chất lượng giọng. Số đo: `.local-artifacts/quiz-voice-latency-20261101/result.json`.

## Kiểm thử

| Phạm vi | Bằng chứng |
| :--- | :--- |
| TypeScript | Qua |
| Toàn bộ Student sau thay đổi cache/player | 113 suite / 1.289 test qua, 45,517 giây |
| Bảo vệ chưa mở đề, sau lượt toàn bộ | 3 suite Quiz / 29 test qua |
| Python: Quiz narration + lesson catalog + solver/catalog | 24 test qua; 2 cảnh báo FastAPI deprecation có sẵn |
| Bot/storage stdlib | 5 + 8 test qua |
| Xuất Expo web/Android/iOS | Thành công; output `.local-artifacts/voice-parity-20261101/export` |
| Whitespace diff | Qua |

Kiểm thử mới xác nhận hai giọng được gọi **trước** khi mở sheet; mở, đổi giọng, đóng/mở lại chỉ có tổng cộng hai yêu cầu và hai lần lưu tệp. Có ca bấm khi job chưa xong, lựa chọn giọng thiết bị, đổi tài khoản, tách QUESTION/SOLUTION, không chuẩn bị đề chưa bắt đầu, không đợi animation sau khi decoder ready, và đọc catalog sau khi xóa RAM.

Lượt export đầu thiếu biến cấu hình địa chỉ dịch vụ cho bản web production nên dừng ở static render; chạy lại với địa chỉ HTTPS theo script xuất bản sẵn có của dự án đã qua. Biến chỉ đặt trong tiến trình kiểm tra, không sửa cấu hình triển khai hay khóa. Lượt typecheck đầu phát hiện tham số voice có thể undefined; đã thêm giọng mặc định hiện có rồi chạy lại thành công. Các test cũ yêu cầu đợi animation được cập nhật theo hành vi mới hiện player ngay khi ready.

Đã đọc tài liệu Expo phiên bản 57 theo quy định repo; dự án hiện cài 58, không nâng/hạ package. Chưa thử âm thanh trên điện thoại thật trong tác vụ này. Không khởi động lại dịch vụ đang dùng hoặc tự deploy. Không commit/push tác vụ giọng này; commit `b040c54` vừa đẩy trước đó chỉ dành cho bot.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa đường gây chờ thay vì thêm dịch vụ/engine mới.
  - Applied to: dùng lại cache/player/catalog hiện có; thêm điểm nối downloader nhỏ, giữ kiểm tra quyền và WAV.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: chuẩn bị dữ liệu sớm, tránh tải trùng và quản lý vòng đời React.
  - Applied to: prefetch hai giọng, chia sẻ promise/file, memo hóa cache theo downloader/tài khoản, cleanup khi rời màn hình.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: giữ cùng tương tác nghe giảng giữa Quiz và bài chính.
  - Applied to: tái sử dụng bộ chọn giọng, player và lỗi hiện có; bỏ trì hoãn trang trí khi player thực sự ready.
