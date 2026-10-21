# Giao diện học từng bước và hỏi bài bằng giọng nói — 21/10/2026

## Kết quả

Đã thay cách ghép nhiều bảng liên tiếp bằng một bước học chính. Giữ màu tím, chữ dễ đọc, nút chạm lớn và giới hạn chiều rộng nội dung 640 px; phần đầu trang cũng đi cùng khung nội dung trên laptop.

Luồng chính: kiểm tra đề → chuẩn bị riêng → hiểu đề → xem tóm tắt → giải từng bước → xem bài giải đầy đủ. Chỉ kết quả được máy chủ kiểm tra mới chuyển bước. Khi chuyển bước, đưa nội dung về đầu màn hình.

- Màn học không tự hiện đồng thời đề gốc, tóm tắt, danh sách lời giảng và mọi hình phân số.
- Thanh hỗ trợ có ba mục: **Nghe giảng**, **Hỏi bài**, **Xem thêm**.
- Đề, bài đã viết, tóm tắt, cài đặt giọng và hình phân số mở riêng. Hình phân số chuyển từng hình; không xếp tất cả xuống dưới bài.
- Phần kiểm tra nhỏ để hiểu gợi ý cũng mở riêng khi học sinh yêu cầu; không đặt thêm câu hỏi cạnh câu đang làm.
- Sau bước đúng, học sinh xem câu lời giải/phép tính rồi chủ động tiếp tục. Bài giải cuối giữ câu lời giải, phép tính, đơn vị, kết luận và các dòng tính chi tiết đã kiểm tra.

## Giọng đọc

Chỉ giữ tối đa hai giọng tiếng Việt thực sự được thiết bị cung cấp, xếp ưu tiên theo chất lượng Enhanced, tên Natural/Hoài My/Nam Minh và ngôn ngữ vi-VN. Lưu giọng/tốc độ đã chọn. Không giả lập giọng vắng mặt hoặc tự đọc bằng giọng tiếng Anh.

Chữ trong bước học ngắn hơn phần giảng có thể nghe hoặc mở đọc riêng. Không tự phát âm thanh. Dừng khi đóng bảng, rời bài, đổi ngữ cảnh hoặc ứng dụng chuyển nền. Trả lời hỏi–đáp dùng nút nghe gọn, không lặp lại cả bảng cài đặt.

**Chưa đánh giá độ hay/tự nhiên bằng tai trên điện thoại/iPad vật lý.** Việc ưu tiên dựa trên thông tin nền tảng, không phải một thử nghiệm nghe để khẳng định hai giọng hay nhất trên mọi thiết bị. Chưa đăng ký Azure hoặc nâng cấp dịch vụ trả phí.

## Hỏi bài bằng mic hoặc chữ

1. Học sinh mở Hỏi bài, đọc thông báo gửi bản ghi và đồng ý ghi âm.
2. Ghi tối đa 30 giây; bấm Nói xong hoặc tự kết thúc theo giới hạn.
3. Chuyển lời nói thành chữ. Học sinh đọc lại, sửa được và bấm Gửi câu hỏi; không tự gửi bản chép thành câu hỏi cho gia sư.
4. Máy chủ giải thích đúng bước đang mở, có phần chữ ngắn, phần nói dài hơn và một câu gợi mở. Khi trả lời xong, bảng chỉ hiện câu hỏi/câu trả lời và các nút cần dùng.
5. Hỏi thêm chỗ này giữ tối đa hai lượt gần nhất cùng bước làm ngữ cảnh phía máy chủ; không tạo một lịch sử trò chuyện dài trong giao diện.

Dùng Whisper tiếng Việt qua cấu hình Groq hiện có để chuyển lời nói, và bộ sinh lời giảng hiện có để giải thích. Không huấn luyện hoặc thay model giải toán trong đợt này. Khi mic hoặc dịch vụ chưa dùng được, vẫn gõ câu hỏi và giữ phần chữ đã nhập.

Web dùng MediaRecorder với quản lý track rõ ràng, kể cả khi quyền mic trả về sau lúc đã đóng bảng; native dùng expo-audio tương ứng SDK 57. Dừng, hủy yêu cầu cũ và dọn bản ghi tạm; không sửa ảnh bài toán của người dùng. Khi nhận giọng sai, học sinh có cơ hội sửa trước khi gửi.

## Kiểm soát phía máy chủ

- Tài khoản lấy từ phiên đăng nhập; không nhận owner do trình duyệt tự khai làm căn cứ quyền.
- Kiểm tra chủ sở hữu, hạn phiên, revision và bước đã mở; kiểm tra lại sau khi chờ model để bỏ phản hồi đã cũ.
- Không gửi đáp án riêng của bước hoặc các bước tương lai vào ngữ cảnh hỏi–đáp. Câu trả lời hỏi bài không chấm điểm hoặc tự chuyển bước.
- Kiểm tra cấu trúc, độ dài, nội dung kỹ thuật không phù hợp và các số chưa có trong dữ kiện/kết quả đã kiểm tra. Phản hồi không đạt chuyển sang yêu cầu làm rõ; không khẳng định bộ lọc này chứng minh được mọi câu giải thích là đúng.
- Bản ghi tối đa 3 MB; kiểm tra dấu định dạng thực, giới hạn nhận giọng đồng thời, bốn yêu cầu ghi âm/phút/tài khoản và 20 câu hỏi/phiên học. Không quét qua các khóa khác để né quota.
- Chặn PCM/WAV quá ngắn, quá dài hoặc gần như im lặng trước khi gọi nhận giọng; với định dạng nén vẫn kiểm tra thông tin tiếng nói từ dịch vụ và bắt buộc học sinh xác nhận bản chép. Không coi bộ nhận giọng luôn chính xác.

## Kiểm chứng

| Phạm vi | Kết quả |
| --- | --- |
| Toàn bộ Student | 847 kiểm thử, 61 bộ, đạt |
| Nhóm Python gia sư/OCR liên quan | 465 kiểm thử, đạt |
| Java tutoring service/controller | 114 kiểm thử, đạt; gồm quyền student, chủ phiên và đầu vào ghi âm |
| TypeScript / ESLint các phần thay đổi | Đạt |
| Export web SDK 57 | Đạt |
| Kiểm tra cấu hình portal / bản production / ghép Student | 16 + 2 + 4 kiểm thử, đạt |
| Giao diện web thực đã export | 360×740, 390×844, 768×1024, 1024×768, 1440×900; không tràn ngang |
| Luồng trình duyệt | Kiểm tra mic giả lập Chromium, đồng ý → ghi/dừng → xác nhận bản chép → hỏi; kiểm tra cả tự kết thúc với đồng hồ tăng tốc |
| Dịch vụ thật | Đăng nhập 200, tạo bài vườn cây 200, hỏi theo bước 200; bản WAV im lặng bị từ chối 400 |
| Giao diện production | Đăng nhập thật, hỏi–đáp thật 200, bảng trả lời gọn, xem đề và lời giảng; endpoint không đăng nhập trả 401 |

Các bài kiểm tra responsive dùng câu trả lời dịch vụ và danh sách giọng được kiểm soát để kiểm tra bố cục, không phải bằng chứng về chất lượng giọng thật. Lần smoke trên production tái sử dụng phiên học thật đã được tạo cho đúng tài khoản để tránh gọi sinh kế hoạch nhiều lần; phần trả lời câu hỏi vẫn gọi dịch vụ thật.

Bằng chứng cục bộ nằm tại `scratch/focused-lesson-qa/`: ảnh từng kích thước, `results.json`, `live-api-result.json`, `public-result.json` và kiểm tra bundle native. Các tệp này không chứa mật khẩu hoặc token đăng nhập; không phải bằng chứng chạy trên máy vật lý.

## Triển khai và dùng thử

- Đã cập nhật backend/AI trong bộ chạy PC và xuất bản Student tại https://mathvisionkid-portal.vercel.app/study/.
- Deployment cuối: `dpl_HVubbQD87tgsULvKcCFdKbE5xHim`, trạng thái READY; bản phát hành `mathvisionkid-portal-m611bx8zu-manh15.vercel.app`.
- Giữ cấu hình teacher/admin; không commit/push Git trong đợt này.
- Mở bài mới sau khi tải lại trang hoặc Reload trong Expo Go. Các phiên học trong bộ nhớ trước lúc khởi động lại máy chủ có thể cần mở lại.
- Backend hiện vẫn chạy trên PC; đợt này không hoàn tất một máy chủ cloud chạy độc lập khi PC tắt.
- Bản dựng native và các kiểm thử tự động không thay cho việc thử mic, quyền ghi âm và nghe giọng trên điện thoại/iPad thật.

Tài liệu phiên bản đã đối chiếu: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), [expo-audio SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/audio/), [Groq Speech to Text](https://console.groq.com/docs/speech-to-text).

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: giảm tải nhận thức và sửa bố cục học trên điện thoại/tablet/laptop.
  - Applied to: một bước chính, bảng hỗ trợ riêng, chiều rộng đọc, thứ tự thao tác và nút chạm.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: thay đổi React Native/web và các tác vụ bất đồng bộ.
  - Applied to: chỉ gắn bảng khi cần, hủy phản hồi cũ, quản lý recorder và lời giảng theo ngữ cảnh.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tránh tăng độ phức tạp khi bổ sung hỏi–đáp và thu gọn giao diện.
  - Applied to: dùng bộ gia sư hiện có, API trình duyệt chuẩn và thư viện audio đúng SDK; không thêm framework chat hoặc dịch vụ giọng mới.
