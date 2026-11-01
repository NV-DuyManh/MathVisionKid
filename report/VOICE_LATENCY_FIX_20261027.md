# Kiểm tra và sửa luồng giọng nói — 27/10/2026

> Báo cáo lượt trước. Cơ chế cuối theo yêu cầu giữ chất lượng hai giọng được mô tả tại [Giọng nói, tiến độ và đăng nhập](VOICE_QUALITY_LOADING_AUTH_20261027.md).

Đã sửa code tải/tạo lời giảng và nạp lại AI runtime cục bộ. Giữ hai giọng Nam Minh và Hoài My, trình phát có tua, transcript và xác thực hiện có. Chưa commit/push. Không thay model OCR hoặc huấn luyện trong công việc giọng nói này.

## Nguyên nhân có bằng chứng

- Log runtime thực tế có nhiều `Vietnamese narration unavailable category=TimeoutError`, một số `NoAudioReceived`, và các phản hồi narration HTTP 503. Gói đang cài đúng `edge-tts==7.3.1`; không phải máy này đang dùng lại 7.2.8.
- Nghe giảng/Hỏi bài hiện tạo tiếng online rồi chờ nhận đủ file WAV mới mở player. Vì vậy độ trễ tạo tiếng và các lần thử lại đều xuất hiện trước khi học sinh nghe được. Đây không phải đường đọc văn bản trực tiếp trên thiết bị.
- Một khóa render chung chỉ cho một request chạy. Đổi giọng hoặc mở lại khi request trước còn chạy bị 503 ngay; client hủy tải không tự hủy công việc đang chạy ở server.
- Cache cũ chỉ có tám mục, dùng thứ tự thêm thay vì cập nhật theo lần sử dụng; các lời giảng cũ dễ bị tạo lại khi mở lại.
- Câu ngắn tổng hợp thành công, còn lời giảng 322 ký tự từng chạm giới hạn 25 giây. Một probe raw nhận được những frame đầu sau 7,625 giây nhưng chưa xong khi bị dừng ở 15 giây: không thể coi nhận một phần stream là đã có audio đầy đủ.

## Thay đổi

- Tối đa hai render độc lập; các request trùng owner/session/revision/voice/nội dung cùng chờ một `Future`, không tạo tiếng lặp. Vẫn kiểm tra phiên/quyền trước khi dùng cache và sau khi tạo/chờ kết quả.
- Khi hết hai slot, API trả 429 thay vì giả thành lỗi nhà cung cấp 503. Student thử lại tối đa hai lần, chờ 0,5 và 1 giây, trong cùng ngân sách 45 giây. Không tự lặp lỗi 503, 409 hoặc 410; hủy chờ ngay khi đóng/chuyển giọng.
- Cache LRU tối đa 64 mục và 32 MiB, TTL tối đa 15 phút và không vượt tuổi phiên. Cache vẫn tách theo chủ sở hữu, phiên, revision và giọng; không tạo URL công khai hoặc lưu lời giảng lâu dài.
- Chia văn bản đã chuyển cách đọc toán thành đoạn tối đa khoảng 220 ký tự tại khoảng trắng, không cắt từ. Tạo tối đa hai đoạn cùng lúc trong mỗi render, ghép frame MP3 theo đúng thứ tự rồi giải mã WAV. Không bỏ nội dung, không đổi giọng, không trả/cache audio dở dang. Token dài không có khoảng trắng được giữ nguyên.
- Mỗi đoạn chỉ thử lại các turn rỗng hoặc timeout tạm thời trong deadline tổng hiện có. Tổng dữ liệu MP3 vẫn giới hạn 2 MiB; hủy và thu hồi các tác vụ còn lại khi một đoạn lỗi hoặc quá hạn. Video offline vẫn dùng bộ tổng hợp cũ.
- Bổ sung log thời gian provider, giải mã, cache hit và loại lỗi; không ghi lời học sinh, nội dung giảng, URL provider hay thông tin xác thực.

## Đo online bằng nội dung tự tạo

Các lượt dưới đây là mẫu chẩn đoán nhỏ, chạy tuần tự tại những thời điểm khác nhau; không phải benchmark kiểm soát mạng hoặc cam kết tốc độ production.

| Phép thử | Kết quả |
| --- | --- |
| Trước sửa: câu phân số ngắn, Nam Minh hai lượt | Thành công: 7,719 và 5,656 giây |
| Trước sửa: cùng câu ngắn, Hoài My hai lượt | Thành công: 8,375 và 4,031 giây |
| Trước sửa: câu 29 ký tự | Thành công: 6,281 giây |
| Trước sửa: lời giảng 322 ký tự, Nam Minh | Thất bại sau 25,110 giây |
| Sau chia đoạn: cùng lời giảng 322 ký tự, Nam Minh | Thành công: 12,765 giây, WAV 788.814 byte |
| Mở lại kết quả Nam Minh trong cache | Dưới 0,1 ms tại hàm server, đúng byte cũ; chưa bao gồm truyền mạng/giải mã trên điện thoại |
| Sau chia đoạn: lời giảng 322 ký tự, Hoài My lượt đầu | Vẫn thất bại sau 25,282 giây |
| Hoài My thử tiếp sau lượt lỗi | Thành công: 17,515 giây, WAV 800.334 byte; đây là tạo lại, không phải cache hit |

Kết luận: đã khắc phục các lỗi tranh chấp/tạo lại trong dự án, có một phép thử dài chuyển từ timeout sang thành công. **Dịch vụ online vẫn có lượt timeout; chưa đủ bằng chứng để gọi ổn định hoàn toàn.** Lời giảng rất dài hoặc kết nối chậm vẫn có thể vượt deadline vì hiện vẫn nhận đủ WAV trước khi phát. Muốn bảo đảm tốt hơn cần đánh giá một dịch vụ TTS có hợp đồng/API hỗ trợ chính thức; thay nhà cung cấp chưa nằm trong bản sửa này.

## Kiểm thử

- Python: **55/55** — narration, neural speech, video, hội thoại. Gồm request trùng thật bằng thread, đổi giọng đồng thời, giới hạn slot/cache, slot được trả sau lỗi, 429, auth/phiên, thứ tự đoạn, giữ từ/giọng, retry không nối audio cũ, hủy tác vụ và không trả file thiếu/câm.
- Student: **32/32**, ba suite `narrationApi`, `lessonNarration`, `questionRecording` — retry có giới hạn, không retry lỗi provider/phiên, abort, đổi giọng, bỏ phản hồi trễ, playback/tua, phục hồi chế độ âm thanh native.
- Spring: **126/126** — 84 service và 42 controller. Có kiểm tra mới giữ nguyên 429 và owner xác thực qua proxy; RBAC hiện có vẫn đạt.
- TypeScript và ESLint phần production sửa đạt. File Jest bị ESLint registry bỏ qua, được kiểm tra bằng Jest/TypeScript.
- AI runtime cục bộ đã khởi động lại riêng, giữ log cũ. HTTP thật: health 200, narration không có internal key 401, phiên không tồn tại 410. Session đang mở trước restart cần mở lại. Không restart backend hoặc sửa dữ liệu bài đã lưu.
- Không tuyên bố đã nghe loa hoặc kiểm tra Expo Go Android vật lý. Các phép thử audio online chạy tại server; test native player dùng mock.

## Phạm vi bảo toàn

Không sửa giao diện ngoài luồng tải audio, không thêm thư viện, không đổi SDK, không thay tiếng video offline. Hai file `scripts/data/recognize_line_batch.py` và `scripts/data/test_recognize_line_batch.py` đã thay đổi từ công việc OCR trước đó, được giữ nguyên trong lượt này.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân trong luồng hiện có, tránh thêm stack hoặc provider khi chưa có bằng chứng.
  - Applied to: giới hạn render, Future dùng chung, LRU có trần bộ nhớ, tạo đoạn bằng stdlib và kiểm thử hồi quy.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: xử lý request giọng nói bất đồng bộ của React Native.
  - Applied to: retry đúng loại lỗi trong deadline chung, hủy timer/listener khi đổi giọng hoặc đóng màn hình; giữ lifecycle/player hiện có.
