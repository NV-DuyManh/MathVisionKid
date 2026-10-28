# Thanh tải theo MFILM và giới hạn hai giọng đọc

Ngày kiểm tra: 27/10/2026. Phạm vi: giao diện tiến độ Student, chuyển tiếp sang trình phát và nghiên cứu giới hạn giọng đọc. Không commit/push, không huấn luyện model, không sửa dự án FILM_MANAGEMENT.

## Kết quả đã triển khai

- Giữ nguyên **Nam Minh** (`vi-VN-NamMinhNeural`) và **Hoài My** (`vi-VN-HoaiMyNeural`). Không tự đổi sang giọng dự phòng để chạy nhanh hơn.
- Thay thanh đứng cứng bằng chuyển động chậm dần, sau đó đầy nhanh khi có kết quả thực sự. Có nhãn **Ước tính** để không đánh đồng hiệu ứng với phần trăm máy chủ đã làm xong.
- Thời gian đã chờ và thời gian chờ tối đa hiển thị riêng. Không tính phần trăm bằng số giây chia 45.
- Thu gọn các hàng trạng thái thành ba mốc nhỏ, giữ tên nhiệm vụ hiện tại, thanh tím chuyển sắc và số phần trăm. Tên trạng thái đầy đủ vẫn có cho trình đọc màn hình.
- Giọng đọc dùng một thanh xuyên suốt tạo giọng → nhận tệp → mở âm thanh. Máy chủ báo tạo xong chưa đủ để hiện 100%; phải chờ trình phát báo đã mở được tệp.
- Có bước đầy cuối khoảng 180 ms, chuyển màn hình sau tối đa khoảng 220 ms; người bật giảm chuyển động được bỏ hiệu ứng. Không trì hoãn tải mạng để tạo cảm giác chờ.
- Tiến độ không lùi khi máy chủ gửi lại mốc cũ. Thời gian trôi không tự đánh dấu nhiệm vụ tiếp theo đã hoàn tất. Hết hạn có thông báo; lỗi mạng/âm thanh vẫn đi vào nhánh thử lại hiện có.

## Đã tham khảo gì ở FILM_MANAGEMENT?

Đã đọc trực tiếp:

- `F:/FILM_MANAGEMENT/src/components/client/loadingScreen/LoadingScreen.jsx`
- `F:/FILM_MANAGEMENT/src/components/client/loadingScreen/LoadingScreen.css`

MFILM tăng tiến độ ước tính bằng số ngẫu nhiên mỗi 350 ms, dừng quanh 85%; khi dữ liệu phim và danh mục sẵn sàng thì đặt 100% và ẩn màn hình. CSS làm mượt thanh bằng chuyển tiếp 400 ms.

MathVisionKid áp dụng nguyên tắc chờ có chuyển động, hoàn tất nhanh khi có dữ liệu. Không sao chép phần tăng ngẫu nhiên vì có thể vượt mốc rồi lùi lại. Thay bằng đường cong cố định `6 + 79 × (1 − exp(−elapsed/8))`, cập nhật đích mỗi 250 ms và làm mượt bằng Animated. Đường cong chậm dần dưới 85%; mốc xử lý thật có thể đưa thanh lên cao hơn, nhưng luôn dưới 100% khi chưa sẵn sàng. Hạn chờ chỉ dùng báo hết hạn, không phải mẫu số của đường cong.

**Đây là ước tính thị giác, không phải phép đo công việc còn lại.** Khi xử lý lâu, thanh sẽ tiến chậm rõ rệt. Không có cơ sở tính thời gian hoàn thành chính xác từ một yêu cầu chưa có dữ liệu đo. Tên bước và số đoạn giọng đọc đã tạo vẫn phản ánh dữ liệu thật.

Animation chỉ đổi transform của thanh trong khung cắt; không thay width theo từng khung hình. Dừng cập nhật thị giác khi ứng dụng vào nền, đọc lại thời gian thật khi trở về và dọn timer/listener khi đóng.

## Hai giọng có được dùng vô hạn không?

**Không thể cam kết vô hạn.** Luồng hiện tại dùng `edge-tts==7.3.1` để truy cập dịch vụ đọc online của Microsoft Edge. Nó không phải tài khoản Azure Speech có hạn mức tài nguyên được cấu hình trong dự án. [README của edge-tts](https://github.com/rany2/edge-tts) mô tả đây là mô-đun truy cập dịch vụ online của Edge.

Trong tài liệu thư viện và trang Microsoft đã kiểm tra, không tìm thấy hạn mức số lượt/ngày hoặc ký tự/tháng được công bố cho cách truy cập Edge này, cũng không thấy cam kết SLA dành cho ứng dụng gọi qua thư viện đó. **Không có hạn mức công bố không có nghĩa là không bị giới hạn.** Mạng, năng lực phía cung cấp hoặc thay đổi dịch vụ vẫn có thể làm yêu cầu chậm hay thất bại. Chưa có dữ kiện để quy một lỗi cụ thể trên điện thoại của người dùng thành “hết quota”.

Mã hiện tại không có bộ đếm quota TTS theo ngày/tháng. Tuy nhiên, mỗi lượt vẫn có giới hạn nội bộ:

| Giới hạn trong dự án | Giá trị đã đọc từ mã |
| --- | --- |
| Văn bản một yêu cầu đọc | Tối đa 4.000 ký tự; tối đa 80 đoạn, mỗi đoạn tối đa 1.600 ký tự |
| Số tác vụ tổng hợp đồng thời trên một tiến trình | 2; yêu cầu trùng dùng chung kết quả đang tạo |
| Chia nhỏ gọi dịch vụ online | Khoảng 220 ký tự/đoạn, tối đa 2 đoạn đồng thời mỗi tác vụ |
| Thời gian chờ online | Tối đa 25 giây trong ngân sách dựng 32 giây |
| Chờ tạo và tải ở ứng dụng | 45 giây; mở tệp âm thanh có watchdog riêng 12 giây |
| Âm thanh trả về | WAV tối đa 8 MiB, thời lượng dưới 240 giây |
| Cache trong tiến trình | Tối đa 64 kết quả / 32 MiB; tối đa 15 phút và không vượt phiên học |

Đọc lại kết quả còn trong cache không cần tổng hợp lại. Phần chuyển văn bản đã có sang tiếng nói này không gọi model ngôn ngữ nên không tiêu token LLM; chi phí sinh lời giải là phần khác.

## Nếu cần dịch vụ có hạn mức rõ ràng

Azure Speech chính thức cũng có đúng hai voice ID trên trong [danh sách giọng Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts). Đây là lựa chọn phù hợp để đánh giá khi đưa vào vận hành có nhiều học sinh, vì có tài khoản dịch vụ và cơ chế quota rõ hơn. Chưa cấu hình hoặc chuyển sang Azure trong lần sửa này.

Theo [quota TTS của Azure](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits), F0 cho 20 giao dịch/60 giây, S0 mặc định 30 giao dịch/giây và có thể xin điều chỉnh. Microsoft cũng nói lỗi 429 có thể do năng lực phục vụ một giọng trong vùng. **Các con số này chỉ thuộc Azure chính thức; không phải quota của luồng Edge hiện tại.** Không có kết luận rằng đổi sang Azure sẽ loại bỏ mọi lỗi hoặc đảm bảo tốc độ cố định.

## Kiểm chứng lần sửa này

- **112 kiểm thử qua, 0 thất bại, 7 bộ**: TaskProgress, LessonNarration, QuestionRecording/AudioPlayback, TutorScreen, LessonVideo, PersonalLessonVideo, LessonQuestion.
- Có kiểm thử đường cong độc lập hạn chờ 45/150 giây; tăng đơn điệu; không tự hoàn tất; tôn trọng mốc máy chủ; hết hạn gọi một lần; nền/foreground; giảm chuyển động; hủy callback lúc đóng; hoàn tất chỉ sau decoder; không giữ tệp cũ khi chọn dự phòng.
- TypeScript, ESLint cho mã thay đổi và `git diff --check` đều qua.
- Expo export web và Android/Hermes thành công tại `runtime/mfilm-loading-export-final-20261027`; log `runtime/mfilm-loading-export-final-20261027.log`.
- Kiểm tra Student web thật với backend đang chạy, viewport 390×844, không giả lập phản hồi API: đăng nhập tài khoản kiểm thử có sẵn, tạo bài học mẫu, thấy thanh tải mới rồi mở bài học; mở Nam Minh và phát được; đổi Hoài My, phát tới 0:15/0:15 và hiện nghe lại.
- **Chưa kiểm thử trên điện thoại Android thật.** Không đo hoặc cam kết FPS, độ trễ mạng hay chất lượng nghe bằng tai từ ảnh chụp.
- Sau kiểm tra, công cụ báo thao tác trình duyệt cục bộ đã bị tắt trong Work settings, nên không thể đóng sheet/đăng xuất tài khoản kiểm thử hoặc đặt lại viewport qua công cụ. Không thử vượt cài đặt này.

Ảnh chụp từ ứng dụng đang chạy:

- [Tạo bài học](mfilm-loading-20261027/lesson-loading-mobile.jpg)
- [Tạo giọng đọc](mfilm-loading-20261027/voice-loading-mobile.jpg)
- [Trình phát Nam Minh](mfilm-loading-20261027/voice-ready-mobile.jpg)
- [Trình phát Hoài My](mfilm-loading-20261027/female-ready-mobile.jpg)
- [Dữ liệu kiểm chứng và hash mã](mfilm-loading-20261027/verification.json)

Các ảnh thể hiện trạng thái tại thời điểm chụp, không chứng minh độ mượt animation. Đường đi hoàn tất/hủy và chính sách chỉ dùng đúng giọng đã chọn được kiểm tra bằng test; thao tác phát trên web được kiểm tra thêm bằng giao diện thật.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: bố cục và phản hồi trạng thái tải trên màn hình nhỏ.
  - Applied to: thanh tiến độ, nhãn ước tính, thời gian chờ và các mốc gọn.
- `fixing-motion-performance`
  - SKILL.md: `.agents/skills/fixing-motion-performance/SKILL.md`
  - Why selected: chuyển động mượt trong React Native/web.
  - Applied to: Animated transform, giảm chuyển động, dừng nền và dọn tài nguyên.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: thay đổi lifecycle React và chuyển tiếp bất đồng bộ.
  - Applied to: completion callback, tiến độ xuyên suốt decoder, hủy và kiểm thử hồi quy.
