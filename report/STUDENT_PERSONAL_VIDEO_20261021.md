# Video theo từng bài học, có lời giảng tiếng Việt

Ngày: 21/10/2026. Phạm vi: Student, business-api và AI runtime phục vụ bài học hiện có.

[Mở trang xem video có tiếng và ảnh app thật](student-personal-video-20261021/index.html).

## Đã triển khai

Trong bài học, mở **Xem thêm → Xem video bài này**. Ứng dụng tự yêu cầu dựng video cho đúng phiên bản bài đang xem; không còn chọn một clip mẫu cố định làm video chính.

Luồng tạo: bài học đã được máy chủ lập và kiểm tra → lấy các bước được phép công bố → tách thành cảnh → vẽ tiêu đề, lời giải thích, phép tính và minh họa phân số phù hợp → tổng hợp giọng Việt cục bộ → ghép H.264/AAC thành MP4. Âm thanh nằm trong file video, nên tải file về vẫn có tiếng. Có chữ hướng dẫn trong khung hình, phát chủ động, tạm dừng và xem lại từ đầu.

- Khi đang học, video gồm những phần đã mở và gợi ý của bước hiện tại; không tự lấy đáp án bước sau từ kế hoạch riêng tư.
- Khi hoàn thành, video xem lại các bước đã được kiểm tra đúng, theo đúng thứ tự và số liệu của bài đó.
- Hai bài có các bước khác nhau sẽ tạo các cảnh, phép tính và lời giảng khác nhau. Khung hình dùng một hệ thống trình bày chung để nhất quán.
- Bài chưa tạo được hướng dẫn hợp lệ không có video giải hộ dự phòng. Không bịa thêm một hướng giải để lấp lỗi.
- Nếu chưa có sơ đồ hình học thích hợp, giữ nguyên phần chữ và phép tính đã công bố; không tự đoán hình vẽ.

Đây là video minh họa theo cảnh được dựng bằng code. Không dùng dịch vụ AI sinh phim hoạt hình hay avatar nói chuyện.

## Token, chi phí và giới hạn

**Dựng video từ bài học hiện có và ghép giọng cục bộ không gọi thêm model, không tiêu thụ thêm token AI.** Phần AI tạo và xem xét hướng dẫn ban đầu, hoặc trả lời câu hỏi mới của học sinh, vẫn dùng quota của dịch vụ hiện có.

Không thêm dịch vụ TTS/video trả phí. Trên máy Windows này, bộ dựng dùng **Windows WinRT Speech / Microsoft An tiếng Việt**. Linux được cấu hình **eSpeak NG tiếng Việt**; chất giọng này khác Microsoft An và chưa được nghe thử trong container. Nếu thiếu giọng Việt hoặc công cụ dựng, trả trạng thái lỗi và cho thử lại; không báo video có tiếng khi chỉ tạo được file im lặng.

Dựng video vẫn tiêu thụ CPU, RAM, ổ đĩa và băng thông. Đã giới hạn:

- Một tác vụ dựng chạy đồng thời trong mỗi tiến trình.
- Video khoảng tối đa bốn phút, MP4 tối đa 16 MiB.
- Tối đa tám tác vụ/video được giữ trong bộ đệm; cùng tài khoản/phiên/bản sửa dùng lại video đã tạo.
- File riêng tư hết hạn sau tối đa 15 phút hoặc khi phiên hết hạn sớm hơn. Bộ hẹn giờ tự dọn, không cần đợi một yêu cầu tiếp theo.
- Xóa WAV, PNG và MP4 từng cảnh sau khi ghép xong file cuối. Tác vụ thất bại hoặc không đưa được vào worker cũng dọn tài nguyên.
- Không tự dựng cho mọi ảnh vừa tải lên. Chỉ dựng khi mở chức năng video trong bài đã xác nhận, để tránh dùng CPU cho video không được xem.

## Video và thời gian đo thật

Các mẫu sau dùng dữ liệu xác định để kiểm tra bộ dựng, không gọi AI. Các bước hoàn thành được gửi qua bộ kiểm tra toán thật của dự án trước khi xuất video.

| Mẫu | Thời lượng video | Thời gian dựng đo trên máy này |
|---|---:|---:|
| Gợi ý bước đầu bài vườn cây, chưa có kết quả | 20,65 giây | 2,73 giây |
| Xem lại ba bước bài vườn cây | 53,52 giây | 5,04 giây |
| Bài bút: được cho thêm rồi cho bớt | 37,71 giây | 3,91 giây |

Đây là số đo của các bài mẫu trên máy hiện tại, không phải cam kết thời gian cho mọi bài hoặc mọi máy chủ.

Các MP4 có video H.264 960×540 và âm thanh AAC 24 kHz. Đã giải mã track âm thanh và kiểm tra RMS khác im lặng; khung hình mở đầu không bị đen. Các dấu ngoặc, phân số, số âm và đơn vị vuông/khối được giữ nghĩa khi chuyển sang lời đọc.

[Nội dung từng cảnh và thời gian dựng](student-personal-video-20261021/samples.json) · [Thông số video và mức âm thanh](student-personal-video-20261021/video-metadata.json).

## API và quyền truy cập

Ba route Student: tạo tác vụ, lấy trạng thái và lấy nội dung video. `owner` luôn lấy từ xác thực của business-api; dữ liệu `owner` do client gửi không quyết định quyền truy cập. Phía AI runtime vẫn yêu cầu khóa nội bộ và đối chiếu tài khoản, phiên và phiên bản bài.

Không trả URL công khai tới video. Client tải nhị phân qua route đã xác thực, kiểm tra MP4 rồi tạo URL blob trên web hoặc file cache riêng trên thiết bị. Đóng/đổi bài hoặc tài khoản sẽ hủy yêu cầu, bỏ phản hồi đến muộn và giải phóng file/URL của client. Trình phát do Expo giải phóng khi unmount; chỉ gọi pause khi đổi màn hình hoặc chuyển nền để tránh lỗi pause sau khi đã release.

API video đặt `Cache-Control: no-store`. File giới hạn kích thước và kiểm tra định dạng; không đưa tên file/đường dẫn hoặc lỗi provider vào giao diện học sinh. Tham số giọng đọc và đường dẫn tạm được truyền bằng dữ liệu JSON, không ghép nội dung bài học vào lệnh shell.

## Kết quả kiểm tra

- Student: **860 kiểm tra / 65 suite** qua.
- Python: **123 kiểm tra** video, hội thoại, bước học, phân số và đọc hiểu nguồn qua; riêng video có bảy kiểm tra với nhiều nhánh quyền truy cập/vòng đời.
- Business-api: **120 kiểm tra** controller/service tutoring qua, gồm route video, lấy chủ tài khoản từ authentication, từ chối vai trò khác, phản hồi có tiếng và tải MP4 riêng tư.
- TypeScript và ESLint các phần thay đổi qua.
- Web export 32 route, Android/iOS Hermes export thành công. Các clip mẫu không tiếng cũ không nằm trên đường import của tính năng video chính mới.
- QA UI: **16 trạng thái** gồm đang dựng/sẵn sàng/tạm dừng tại 320, 390, 768, 1024 ngang và 1440 px, cùng trạng thái lỗi và thử lại. Đã kiểm tra không tràn ngang, không nút vượt khung, không ảnh lỗi và không lỗi JavaScript; MP4 phát và tạm dừng thật, âm lượng bật.
- Smoke test thực tế qua HTTP ASGI nội bộ: tạo job → dùng lại cùng job → poll READY → tải MP4 có tiếng; người khác bị từ chối, bản sửa cũ bị từ chối, `no-store`, **0 lượt gọi model thêm**. Mẫu video 17 giây hoàn tất toàn chu trình khoảng 2,67 giây.
- Review độc lập tìm và đã xác nhận sửa ba vấn đề: đường dẫn font trong container nông, đọc mất ngoặc làm đổi nghĩa toán, và dọn file hết hạn. Thêm kiểm tra tình huống worker không nhận tác vụ.
- Giữ nguyên SHA-256 của `privacy.tsx`, `crop.tsx`, `AppHeader.tsx`, `AppButton.tsx`, `theme.ts`.

Ảnh UI dùng phản hồi đăng nhập/trạng thái tác vụ cô lập và MP4 thật do bộ dựng tạo ra. Không dùng làm bằng chứng hệ thống online đang chạy hoặc chất lượng AI trả lời một bài mới. Chưa chạy container Linux hoặc phát trên điện thoại/iPad vật lý. Chưa có đánh giá nghe của con người để kết luận giọng nào hay nhất.

[QA UI](student-personal-video-20261021/visual-qa.json) · [Smoke API](student-personal-video-20261021/api-smoke.json) · [Jest](student-personal-video-20261021/jest-results.json) · [File được giữ nguyên](student-personal-video-20261021/protected-after.json).

**Chưa commit, push hoặc deploy bản online. Không train hoặc đổi model.**

## Các file chính

- `ai/runtime/app/tutoring/video.py`: tác vụ riêng tư, cache, giới hạn và hết hạn.
- `ai/runtime/app/tutoring/video_render.py`: cảnh, lời đọc toán, TTS, hình và xuất MP4.
- `ai/runtime/app/api/tutor.py`: route nội bộ video.
- `ai/runtime/Dockerfile`: công cụ dựng/giọng/font cho Linux.
- `backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutor{Dtos,Controller,Service}.java`: proxy đã xác thực và kiểm tra response.
- `apps/student-mobile/src/features/tutoring/{PersonalLessonVideo,LessonClip,lessonVideoApi,lessonVideoFile}.tsx/ts`: chuẩn bị, tải và phát riêng tư.
- `apps/student-mobile/src/app/learning/math-guide.tsx`: điểm vào chức năng mới.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: renderer backend và giới hạn tài nguyên, tránh dịch vụ/model không cần thiết.
  - Applied to: tái sử dụng `lesson.present`, thư viện sẵn có, worker đơn, cache giới hạn, TTS hệ thống.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native, async và tài nguyên phát video.
  - Applied to: tải theo nhu cầu, hủy theo scope, bỏ response cũ, cleanup file/URL/player, tách player khỏi thư viện clip tĩnh cũ.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: trạng thái chờ, lỗi, phát chủ động và phụ đề cho Student.
  - Applied to: một cửa sổ video, progress có trạng thái thật, nút thử lại, kiểm tra responsive năm chiều rộng. Tra cứu UX `video playback loading captions` đã được đối chiếu đúng lĩnh vực.

Workflow: `using-superpowers`, `brainstorming`, `writing-plans`, `executing-plans`, `test-driven-development`, `requesting-code-review`, `receiving-code-review`, `verification-before-completion`. Nguồn: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/<tên>/SKILL.md`. Áp dụng vào kế hoạch, red/green, review và chứng cứ hoàn tất. Kế hoạch: `docs/superpowers/plans/2026-10-21-personal-lesson-video.md`.

Đã đọc [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) và [expo-video SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/video/), đồng thời kiểm tra khai báo `File.create/write/delete` của đúng package đã cài trước khi sử dụng API cache native.
