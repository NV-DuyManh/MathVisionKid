# Student — nghe giảng, kiểm tra mức hiểu, UI và video

Ngày: 21/10/2026. Phạm vi: ứng dụng học sinh MathVisionKid.

[Mở trang xem ảnh thật, ba bộ UI và video](student-voice-ui-20261021/index.html).

## Những phần đã triển khai

### Nghe xong, học sinh được chọn cách học tiếp

- Vào **Nghe giảng** ở bước đang học. Lời giảng chỉ phát khi học sinh bấm nghe.
- Khi đọc xong toàn bộ lời giảng, cửa sổ chuyển riêng sang **Em đã hiểu / Em chưa hiểu**. Không chồng phần kiểm tra mức hiểu xuống dưới một khối lời giảng dài.
- **Em đã hiểu** đưa học sinh trở lại bước đang làm; không tự chấm đúng, không tự chuyển bước, không tăng thành tích.
- **Em chưa hiểu** mở ba lựa chọn theo ngữ cảnh. Ví dụ cộng/trừ phân số: lý do quy đồng, bắt đầu từ đâu, ý nghĩa tử số và mẫu số. Bước đọc hiểu đề có các lựa chọn về dữ kiện, câu hỏi và từ chưa hiểu.
- Chọn một ý sẽ gửi câu hỏi cho dịch vụ hỏi bài hiện có, kèm đúng phiên, phiên bản và bước đã mở. Phản hồi có **chữ ngắn** và **lời giảng dài hơn**. Sau lần nghe mới, học sinh lại chọn mức hiểu.
- Có nút **Em đã đọc lời giảng** cho trường hợp học sinh muốn đọc hoặc thiết bị không có giọng Việt. Có nghe lại, dừng chờ và thử lại khi cần.
- Chặn bấm gửi trùng, hủy yêu cầu khi đóng/đổi phiên/chuyển nền, bỏ phản hồi đến muộn. Lỗi dịch vụ được diễn đạt bằng lời dễ hiểu cho học sinh.

Giữ tối đa hai giọng Việt từ danh sách thực sự có trên thiết bị, ưu tiên giọng Enhanced/Natural nếu có. Đây là xếp hạng theo thông tin hệ thống, không phải đánh giá nghe thử của con người. Không thêm Azure Speech hay dịch vụ TTS trả phí. Chất lượng âm sắc trên điện thoại thật chưa được xác nhận.

Các thành phần chính:

- `apps/student-mobile/src/features/tutoring/LessonListening.tsx`
- `apps/student-mobile/src/features/tutoring/LessonNarration.tsx`
- `apps/student-mobile/src/app/learning/math-guide.tsx`

### Chỉnh tiếp các màn Student còn lại

- Đồng bộ màn kết quả đúng, gợi ý sửa, ảnh chưa rõ, ngoài phạm vi và cần xem lại bằng khung kết quả chung. Điện thoại dùng bố cục dọc; màn lớn dùng minh họa và nội dung cạnh nhau, giới hạn chiều rộng để không kéo giãn.
- Chỉnh thư viện ảnh theo chiều rộng cửa sổ: ba cột điện thoại, bốn cột tablet và sáu cột màn lớn.
- Cải thiện màn xem lại ảnh: ảnh và thao tác xếp dọc trên điện thoại, hai cột khi màn hình đủ rộng; nội dung có thể cuộn khi máy nhỏ hoặc nằm ngang.
- Cân lại khung camera web, màn nhận diện, xem lại nhiều dòng và trạng thái lỗi xử lý.
- Kiểm tra mở rộng phát hiện nút hiện mật khẩu tràn tại 320 px. Nguyên nhân là ô nhập giữ chiều rộng tối thiểu theo nội dung; đã cho ô nhập co lại, kiểm tra lại cả thao tác hiện/ẩn mật khẩu tại năm chiều rộng.
- Không thay logic đăng nhập, phân quyền, chấm bài hoặc kết luận đúng/sai từ máy chủ.

Các file che tên/cắt ảnh và thành phần nền được giữ nguyên theo SHA-256: `privacy.tsx`, `crop.tsx`, `AppHeader.tsx`, `AppButton.tsx`, `theme.ts`. Xem [đối chiếu hash](student-voice-ui-20261021/protected-after.json).

Đợt này tập trung vào luồng học và các màn Student ở trên. Không tuyên bố đã thiết kế lại các công cụ phân tích/dev nội bộ; không sửa giao diện Teacher/Admin.

### Ba bộ ảnh UI mới để lựa chọn

| Bộ | Phong cách | Ảnh đầy đủ |
|---|---|---|
| 01 — Sao nhỏ tinh gọn | Lavender, tím, điểm vàng; gần nhận diện hiện tại nhất | [Mở ảnh](student-voice-ui-20261021/ui-a-sao-nho.png) |
| 02 — Vườn khám phá | Kem, mint, thiên nhiên và hành trình học | [Mở ảnh](student-voice-ui-20261021/ui-b-vuon-kham-pha.png) |
| 03 — Xưởng toán sáng tạo | Không gian học tập, giấy và khối hình | [Mở ảnh](student-voice-ui-20261021/ui-c-xuong-toan.png) |

Mỗi bảng có điện thoại, tablet, laptop và các màn học chính. Đây là **ảnh ý tưởng do AI tạo**, không phải ảnh chụp app; chữ/số liệu nhỏ trong ảnh mang tính minh họa. Ba hướng được lưu riêng cho chủ dự án chọn sau; chưa đổi app sang một trong ba bộ mới.

Dùng chế độ **built-in tool** của `image_gen.imagegen`, không dùng CLI/API riêng. [Toàn bộ prompt và ảnh tham chiếu](student-voice-ui-20261021/UI_CONCEPT_PROMPTS.md). Các file PNG đã lưu trong workspace.

### Ba video minh họa đã đưa vào app

Mở **Xem thêm → Xem video minh họa** trong bài học. Bước đọc hiểu mở ví dụ tóm tắt đề; bước có phân số mở ví dụ phân số. Video chỉ phát khi chọn, có tạm dừng và xem lại từ đầu. Chuyển nền/đổi màn hình sẽ dừng phát.

| Video | Nội dung | File |
|---|---|---|
| Một phần ba nghĩa là gì? | Chia hình thành ba phần bằng nhau rồi chọn một phần | [MP4](../apps/student-mobile/assets/videos/fraction-intro.mp4) |
| Vì sao phần phải cùng kích thước? | Chia lại một nửa và một phần ba thành phần sáu, giữ nguyên lượng tô | [MP4](../apps/student-mobile/assets/videos/common-parts.mp4) |
| Tóm tắt đề trước khi tính | Tách Đã biết / Cần tìm từ ví dụ riêng | [MP4](../apps/student-mobile/assets/videos/problem-summary.mp4) |

Mỗi clip dài 12 giây, 960×540, H.264, có chữ tiếng Việt. Tổng ba MP4 khoảng 192 KB. Video mẫu **chưa ghép âm thanh**; lời giảng bằng tiếng nằm trong cửa sổ Nghe giảng. Clip dùng ví dụ độc lập, không tự giải hộ bài đang học.

Video được dựng bằng canvas và FFmpeg cục bộ với hình minh họa của dự án, không thuê dịch vụ sinh video. Mã tạo clip: `student-voice-ui-20261021/make-learning-videos.cjs`. Trình phát dùng `expo-video ~57.0.5` theo Expo SDK 57; không bật phát nền hoặc PiP.

## Kiểm tra và giới hạn bằng chứng

- **856/856 kiểm tra Student, 63 suite** qua. Bao gồm hoàn tất narration, lựa chọn chưa hiểu, nội dung text/voice riêng, thử lại, hủy yêu cầu cũ và vòng đời video.
- **12 kiểm tra conversation Python** qua trong môi trường `.venv` của AI runtime. Phần dịch vụ hỏi bài sẵn có không bị đổi trong đợt này.
- TypeScript và ESLint các phần thay đổi qua.
- Export web thành công với 32 route; export Android/iOS Hermes thành công, gồm ba MP4. Đây là kiểm tra đóng gói, không phải đã cài và chạy trên máy thật.
- Bốn kiểm tra cấu hình export/deploy qua; địa chỉ dịch vụ trong bản web đã đối chiếu. Không thực hiện deploy.
- **127 trạng thái trình duyệt** được chụp và kiểm tra: không tràn ngang, không ảnh lỗi, không nút vượt khung và không lỗi console. Home ở chín chiều rộng từ 320 đến 1920; luồng học/nghe/chưa hiểu/video/kết quả ở 320, 390, 768, 1024 ngang và 1440 px. Camera → che tên → cắt ảnh → xem lại được chạy ở 390, 768 và 1440 px.
- Đã phát và tạm dừng MP4 thật trong Chromium. Chú thích và các khung hình mẫu được xem lại.
- Review độc lập phát hiện một lỗi pause trình phát sau khi Expo đã giải phóng tài nguyên native. Đã sửa thành pause khi mất focus, để SDK xử lý unmount; bốn kiểm tra vòng đời qua. Reviewer xác nhận P1 đã được giải quyết, không còn phát hiện quan trọng trong phạm vi đó.

Các ảnh chụp UI dùng phiên và phản hồi API cô lập để kiểm tra app thật từ bản export. Sự kiện đọc xong được mô phỏng để kiểm tra luồng; không dùng làm bằng chứng âm sắc hoặc chất lượng trả lời của AI thật. Chưa kiểm tra trên điện thoại/iPad vật lý; chưa xác nhận endpoint hỏi bài ở hệ thống đang deploy đã được cập nhật và hoạt động với phiên thật.

[Kết quả Jest](student-voice-ui-20261021/jest-results.json) · [QA giao diện](student-voice-ui-20261021/visual-qa.json) · [Thông số MP4](student-voice-ui-20261021/video-metadata.json).

Không commit, push hoặc deploy trong đợt này. Không train model; không thay model; không tải thêm dữ liệu Drive.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: bố cục Student và trải nghiệm theo từng bước trên nhiều kích thước.
  - Applied to: màn kết quả, thư viện, xem lại ảnh, trạng thái nghe và lựa chọn mức hiểu.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai React/React Native và vòng đời bất đồng bộ.
  - Applied to: request theo scope, bỏ kết quả cũ, callback narration, cleanup video.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng dịch vụ/thành phần sẵn có và giữ luồng đơn giản.
  - Applied to: dùng lại askLesson, giới hạn ba lựa chọn, khung kết quả dùng chung, MP4 cục bộ.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: người dùng yêu cầu thêm ba bảng ảnh UI.
  - Applied to: ba bộ ảnh ý tưởng, lưu kết quả và prompt, tách rõ mockup với ảnh app thật.

Workflow skills: `using-superpowers`, `brainstorming`, `test-driven-development`, `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, `systematic-debugging`, từ `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/<tên>/SKILL.md`. Áp dụng để xác định phạm vi, kiểm tra lỗi trước khi sửa, review độc lập và chỉ báo kết quả đã có bằng chứng.
