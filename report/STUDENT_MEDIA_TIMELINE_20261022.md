# Trình phát kéo theo thời gian và giao diện mới — 22/10/2026

[Xem toàn bộ ảnh UI mới và nghe file giọng thật](student-media-timeline-20261022/index.html).

## Đã thay đổi

Theo phản hồi của chủ dự án, bỏ trình phát tua theo ý/câu. Cả bốn nơi **nghe giảng, câu trả lời AI, câu hỏi vừa ghi và video** dùng cùng cách điều khiển theo thời gian: thanh trượt đến vị trí bất kỳ, thời gian đã phát/tổng, phát/tạm dừng, lùi/tiến vài giây và về đầu. Lời giảng/video có tốc độ 0,8×, 1×, 1,2×.

Trình phát nền sáng, viền mảnh và nút phát tím ở giữa thay cho mảng tím lớn. Bỏ hình sóng và danh sách tua theo ý. Mục lời giảng chữ thu gọn; câu hỏi và trả lời được tách thành khối rõ ràng. Nút đã hiểu/chưa hiểu thu gọn thành một hàng. Phần video bỏ nhãn thông tin dài lặp lại thời lượng.

Giữ việc nhấn mic là ghi âm ngay, giới hạn 30 giây, xem/sửa chữ trước khi gửi. Không đưa lại hộp xác nhận lặp lại.

## Tua thật được thực hiện thế nào

Giọng TTS trực tiếp của thiết bị không cho truy cập file để tua theo giây trên mọi nền tảng. Lời giảng mới được dựng thành WAV PCM 16 kHz từ **nội dung backend đã công bố**, sau đó phát bằng expo-audio. Video dùng expo-video. Thanh kéo đặt thời gian thật trên trình phát, không ước lượng tiến độ bằng số chữ.

Khi kéo, phát tạm dừng; thả tay sẽ trở lại đúng trạng thái trước khi kéo. Âm thanh đang dừng không tự phát sau thao tác tua. Kiểm tra cả tình huống vừa dừng thì kéo ngay, khi trạng thái UI chưa kịp cập nhật. Web dùng input range chuẩn hỗ trợ chuột, chạm và bàn phím; native dùng slider hệ thống được Expo SDK 57 hỗ trợ.

Dựng WAV dùng lại giọng offline hiện có của dự án và FFmpeg. Không gọi thêm model hoặc dịch vụ trả phí để dựng/nghe lại. Câu hỏi mới và chuyển giọng nói thành chữ vẫn dùng dịch vụ hiện có như trước.

Đo mẫu trên máy hiện tại: lời giảng dài **10,95 giây**, câu trả lời **11,95 giây**; thời gian dựng ấm khoảng **0,6–2,3 giây** tùy lượt. Đây là số đo mẫu, không phải cam kết mọi bài/mọi máy chủ. Metadata lượt chạy gần nhất ở `samples/metadata.json`.

## Quyền truy cập và giới hạn

- Route business-api lấy tài khoản từ authentication; client không quyết định `owner`. AI runtime vẫn yêu cầu khóa nội bộ.
- Mỗi yêu cầu gắn phiên, revision và danh sách đoạn. Backend chỉ chấp nhận đoạn đã được công bố qua bài học/gợi ý/câu trả lời; không đọc kế hoạch/đáp án chưa mở.
- Nội dung tối đa 4.000 ký tự, 80 đoạn; WAV dưới 4 phút và 8 MiB. Một tiến trình dựng giọng đồng thời. Bộ nhớ đệm tối đa tám file, kiểm tra hết hạn không quá 15 phút và không vượt phiên.
- Trả binary qua route đã xác thực với `Cache-Control: no-store`, không tạo URL công khai. File tạm dựng được dọn ngay; file/blob phát trên client dọn khi đóng hoặc đổi nguồn.
- Đóng màn/đổi tài khoản hoặc phiên sẽ hủy yêu cầu và bỏ qua kết quả đến muộn. Chuyển nền dừng phát; tải âm thanh đang chờ sẽ bị hủy.
- Giọng mẫu trên Windows dùng giọng tiếng Việt đang cài. Linux dùng eSpeak NG như bộ dựng video sẵn có; âm sắc giữa các máy chủ có thể khác. Không khẳng định hai môi trường có cùng chất giọng hoặc đã được nghe thử trên điện thoại vật lý.

## Kiểm chứng

- Student: **875 kiểm thử / 71 bộ đạt**, chạy `npm test -- --runInBand --silent --json --outputFile=../../report/student-media-timeline-20261022/student-tests.json` trong `apps/student-mobile`; gồm tua chính xác, phát/dừng, phản hồi muộn, dọn file và trường hợp vừa dừng thì kéo ngay.
- Backend: **124 kiểm thử controller/service tutoring đạt**, gồm auth, vai trò, chủ tài khoản và binary WAV.
- AI: **309 kiểm thử đạt** cho narration, hội thoại, bước học, phân số, video, nhận xét bài làm và nhận diện nguồn/ký hiệu; có kiểm tra phiên thật chỉ công bố hướng dẫn đã mở. Không gọi model cho kiểm thử dựng audio. Chi tiết `student-media-timeline-20261022/python-tests.log`.
- TypeScript/ESLint đạt. File LessonClip ghi rõ ngoại lệ lint: VideoPlayer là đối tượng native có setter thời gian/tốc độ, không phải React state bất biến.
- Web export 32 route; Android/iOS Hermes export thành công. Đã kiểm tra tài liệu đúng Expo SDK 57 trước khi sửa.
- QA trình duyệt: **31 ảnh, 30 lần kéo audio/video**, tại 320×740, 390×844, 768×1024, 1440×1000 và 844×390. Kiểm tra tua khi phát/dừng, bàn phím, phát hết rồi nghe lại, không tải lại audio khi tua, không tràn ngang/ảnh hỏng/nút vượt khung/lỗi JavaScript.
- WAV và MP4 dùng để QA là file thật. Auth, nội dung bài/câu trả lời và chuyển chữ được cô lập; mic là thiết bị giả lập Chromium. Không dùng kết quả này để khẳng định chất lượng AI online, chất giọng trên thiết bị thật hoặc deployment production.
- Trang xem ảnh cũng đã được chạy trong trình duyệt: năm lựa chọn kích thước, 25 ảnh tải đúng và hai WAV phát được.
- Smoke ASGI với WAV thật: không có khóa → 401; đúng tài khoản → 200 audio/wav; khác chủ → 410; revision cũ → 409; `no-store`; không gọi model. Chi tiết `api-smoke.json`.
- Giữ nguyên SHA-256 của privacy, crop, AppHeader, AppButton và theme; xem `protected-after.json`.

## Trạng thái triển khai

Đã sửa mã nguồn Student, business-api và AI runtime trên nhánh `codex/student-voice-replay-20261022`. Chưa commit, push hoặc deploy trong đợt này. Tính năng WAV mới cần cập nhật cả hai backend cùng Student; frontend trỏ vào backend cũ sẽ báo chưa tải được âm thanh, phần chữ vẫn dùng được.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: thiết kế lại trình phát và phân bố nội dung trên màn hình nhỏ/rộng.
  - Applied to: thẻ sáng, một bộ điều khiển thống nhất, kéo/chạm/bàn phím và nút thay thế kéo, QA responsive.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: trạng thái phát/tua, tải binary và vòng đời React Native/web.
  - Applied to: hủy yêu cầu, bỏ phản hồi muộn, cleanup file/blob, không tự phát và giữ trạng thái khi tua.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: dùng lại bộ dựng giọng, quyền phiên và trình phát hiện có.
  - Applied to: WAV đồng bộ có giới hạn, cache nhỏ, công cụ offline hiện có và slider tiêu chuẩn.

Quy trình hỗ trợ được dùng: systematic-debugging, test-driven-development, verification-before-completion; nguồn `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/`. Kế hoạch: `docs/superpowers/plans/2026-10-22-media-timeline.md`.
