# Cải thiện ghi âm và nghe lại — 22/10/2026

[Xem ảnh giao diện thật ở năm kích thước](student-voice-replay-20261022/index.html).

## Đã thay đổi

- Bỏ hộp “Đồng ý và ghi âm” lặp lại. Nhấn mic mở ghi âm ngay; vẫn dùng quyền mic của hệ điều hành/trình duyệt. Giữ giới hạn bản ghi 30 giây và lời nhắc ngắn, không bắt học sinh xác nhận lại.
- Sau “Nói xong”, giữ bản ghi cục bộ để nghe lại, tạm dừng, chạm thanh tua hoặc lùi/tiến 5 giây. Bản ghi chạy hết vẫn phát lại từ đầu được. Giữ ô chuyển chữ cho học sinh sửa rồi chủ động gửi câu hỏi.
- Lời giảng và câu trả lời đều có ý trước/sau, tạm dừng, nghe tiếp, nghe từ đầu và mục thu gọn “Các ý đã nghe” để chọn đoạn. Không cần gọi lại AI khi nghe lại.
- Thay hai bên hình sóng trang trí bằng nút điều khiển rõ ràng, giữ màu tím và minh họa đã duyệt. Các phần thiết lập và danh sách đoạn mặc định thu gọn.

## Phạm vi và vòng đời

Lời giảng đang dùng giọng TTS trên thiết bị. Tua theo các ý/câu đã chia, không giả lập thời lượng bằng số giây. Khi nghe tiếp, đọc lại từ đầu ý đang dở; giao diện ghi rõ. Các ý bỏ qua không được tính là đã nghe và không kích hoạt xác nhận nghe hết.

“Các ý đã nghe” thuộc lời giảng/câu trả lời đang mở. Đây chưa phải kho lưu hội thoại qua nhiều lần đóng màn hình hoặc nhiều ngày. Không lưu bản ghi của học sinh lên kho nghe lại lâu dài. Đóng câu hỏi, đổi tài khoản/bước học hoặc ghi lại sẽ dọn file/blob; chuyển nền dừng ghi/phát và bỏ qua phản hồi cũ. Giữ bản ghi nếu chuyển lời nói thành chữ thất bại để em vẫn nghe và tự gõ.

Backend nhận câu hỏi và xác định quyền truy cập như trước. Đợt này không sửa prompt, model, chất giọng, API hoặc giới hạn quota, không huấn luyện. Nghe lại dùng nội dung sẵn có; câu hỏi mới và chuyển lời nói thành chữ vẫn dùng dịch vụ hiện có.

## Kiểm tra

- Kiểm thử mới đã tái hiện lỗi trước khi sửa: bước xác nhận lặp lại, thiếu điều khiển nghe lại, và chạm thanh tua web dùng nhầm tọa độ native.
- Student: **881/881 kiểm thử, 68 suite đạt**. TypeScript và ESLint ba file giao diện đạt. Web export 32 route; Android/iOS Hermes export đạt, 77 tài nguyên.
- Giao diện chạy bằng bản web xuất thật, có dữ liệu bài học/câu trả lời cô lập. Chromium ghi âm thật từ thiết bị mic giả lập, phát/tạm dừng/tua và phát lại sau khi hết bản ghi. Không đánh giá chất lượng chuyển chữ hoặc chất giọng qua các dữ liệu cô lập này.
- Năm kích thước: 320×740, 390×844, 768×1024, 1440×1000 và 844×390. 25 ảnh chụp. Kiểm tra tràn ngang, ảnh hỏng, nút vượt khung và lỗi JavaScript.
- Chạy cuối `visual-qa.cjs`: **25 trạng thái đạt, 0 lỗi JavaScript**. Cả năm kích thước đều kiểm tra chạm thanh tua, lùi về đầu, phát bản ghi đến hết rồi nghe lại. Mỗi lượt chỉ có một yêu cầu chuyển chữ và một yêu cầu trả lời mới; các thao tác nghe lại không tăng số yêu cầu trả lời.
- Cơ chế speech completion mô phỏng để kiểm tra quay lại ý, nghe tiếp và chọn đoạn; không dùng làm bằng chứng âm thanh TTS nghe hay trên thiết bị thật.
- Giữ nguyên SHA-256 của privacy, crop, AppHeader, AppButton và theme; bằng chứng tại `student-voice-replay-20261022/protected-after.json`.

Không commit/push hoặc deploy trong đợt này. Nhánh làm việc: `codex/student-voice-replay-20261022`.

## Gợi ý ưu tiên tiếp theo

1. Nhật ký các chỗ em hay vướng, dẫn về đúng bước và lời giảng liên quan để ôn lại.
2. Bài kiểm tra rất ngắn sau lời giảng, giúp biết em đã hiểu trước khi chuyển bước.
3. Báo cáo tiến bộ theo kỹ năng cho phụ huynh/giáo viên, dựa trên kết quả đã kiểm tra thay vì số lần bấm.

Ba mục trên là đề xuất; chưa triển khai trong đợt sửa luồng giọng nói này.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: trình bày điều khiển giọng nói rõ và gọn trên nhiều màn hình.
  - Applied to: trình phát, danh sách thu gọn, nút tối thiểu 44–48 px và QA năm kích thước.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native/web và tài nguyên phát/ghi âm bất đồng bộ.
  - Applied to: trạng thái phát, guard phản hồi muộn, cleanup file/blob và không tự phát.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: mở rộng luồng có sẵn với ít thay đổi và không thêm thư viện.
  - Applied to: dùng expo-audio đã cài, dùng lại các đoạn TTS và giữ API hiện tại.

Quy trình hỗ trợ: `using-superpowers`, `brainstorming`, `systematic-debugging`, `test-driven-development`, `verification-before-completion`, được đọc từ `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/`. Áp dụng vào rà luồng, thiết kế ngắn theo yêu cầu đã được giao, kiểm thử đỏ/xanh và kiểm chứng thực tế. Đã đọc tài liệu [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), [expo-audio](https://docs.expo.dev/versions/v57.0.0/sdk/audio/), [expo-speech](https://docs.expo.dev/versions/v57.0.0/sdk/speech/) và mã thư viện đã cài trước khi sửa.
