# Tích hợp giọng Việt chọn lọc từ Nam — 26/10/2026

**Đã tích hợp hai giọng Nam Minh (nam) và Hoài My (nữ) vào Nghe giảng và lời giải thích trong Hỏi bài. Không merge nguyên nhánh Nam.** Giữ thanh tua theo thời gian, tốc độ phát, nghe lại, transcript và kiểm tra chủ sở hữu/phiên/revision. Chưa commit, push hoặc triển khai production.

**Giới hạn thực tế:** đã tạo và giải mã được âm thanh của cả hai giọng, nhưng thử nghiệm online vẫn có lượt `NoAudioReceived`/HTTP 503 sau thử lại. Không kết luận nhà cung cấp đã ổn định hoàn toàn hoặc hai giọng là tốt nhất trong mọi dịch vụ. Không có bằng chứng nghe bằng loa trên điện thoại Android thật.

[Xem giao diện chạy thật và nghe hai mẫu](nam-voice-integration-20261026/index.html) · [Kiểm tra giao diện](nam-voice-integration-20261026/visual-qa.json) · [Kết quả và hash](nam-voice-integration-20261026/summary.json)

## Nguồn và phạm vi chọn lọc

- Đã fetch lại `origin/Nam`; commit vẫn là `ec6d633f5491d398fc7f743e9c88f28060094f5d`. Main vẫn ở `71ad997ad55301dd6a869baed34c0d13fbd8246e`.
- Dùng kết quả rà toàn nhánh tại [báo cáo trước](NAM_SELECTIVE_REVIEW_20261026.md): 4.614 file, khoảng 593 MB nội dung, 5 conflict. Không checkout/merge hàng loạt, không chạy script train từ nhánh.
- Lấy ý tưởng và cách gọi `edge-tts==7.3.1` trong `ai/runtime/app/tutoring/speech.py`, giới hạn 2 MiB MP3, timeout kết nối, chỉ ghi loại lỗi; dùng đúng hai giọng Việt từ danh sách dịch vụ. Đồng bộ requirements, pyproject và uv.lock; không nâng SDK hay dependency JavaScript.
- Đối chiếu phiên bản và giao thức với [gói PyPI 7.3.1](https://pypi.org/project/edge-tts/7.3.1/) và [release upstream](https://github.com/rany2/edge-tts/releases). Không suy từ thông báo release rằng mọi lỗi audio đã được giải quyết.
- Tái sử dụng `voicePreferences` hiện có, với kiểm tra dữ liệu lưu cũ/hỏng; hai lựa chọn nằm trên trình phát. Mặc định Nam Minh. Việc chọn được giữ cho lần mở tiếp theo; tốc độ vẫn chỉnh trực tiếp trên player.
- Giữ cải tiến số âm/đơn vị đã chọn ở lượt trước. Không đổi công thức, kết quả toán, OCR hoặc model.
- Không lấy endpoint text-to-speech chung, trình phát từng đoạn, prefetch nội dung đoán trước, cache client mới hoặc kho dữ liệu/snapshot train. Endpoint hiện tại chỉ đọc nội dung đã công bố cho đúng phiên học.

## Tích hợp và bảo vệ

- Client gửi lựa chọn giọng qua endpoint `/student/tutor/lesson/narration`; Spring vẫn tự lấy owner từ tài khoản đăng nhập, kiểm tra vai trò Student và chỉ nhận đúng hai voice ID.
- Runtime kiểm tra owner/session/revision và danh sách lời giảng trước khi gọi giọng online; kiểm tra lại sau khi tạo âm thanh. Cache tách theo cả voice, không lẫn bản nam/nữ hoặc các tài khoản.
- Tối đa ba lượt gọi cho lỗi turn rỗng, trong **một** deadline tổng hợp 25 giây; deadline toàn quá trình lời giảng 32 giây. Mỗi lần thử dùng buffer mới, không nối lặp phần âm thanh dở dang.
- MP3 được giải mã thành WAV PCM mono 16 kHz. Kiểm tra độ dài, dung lượng, định dạng, số frame đầy đủ và mẫu không toàn số 0. Không cache file sai hoặc phiên đã đổi. File MP3 tạm được xóa cả khi lỗi; thư mục WAV server tự dọn sau request.
- Đổi giọng hủy tải cũ, dừng player cũ, dọn file/Blob URL cũ; phản hồi trễ không được đưa trở lại. Không tự phát khi đổi giọng hoặc mở lại. Khi lỗi vẫn đọc được transcript và bấm tải lại.
- Native giữ trạng thái checked/disabled; web thêm ARIA checked, phím mũi tên/Home/End và focus đúng lựa chọn. Hai nút cao 52 px, không tạo danh sách dài.
- **Giữ nguyên đường tổng hợp offline của video.** Không cho các lượt lỗi online đã quan sát làm gián đoạn bộ dựng phim hiện có. Hai giọng online trong thay đổi này áp dụng cho nghe giảng/Hỏi bài, chưa thay tiếng của video đóng gói sẵn hoặc video dựng theo bài.

## Bằng chứng chạy thực tế

Các phép thử chỉ gửi câu mẫu tự tạo, không dùng dữ liệu học sinh thật.

1. Danh sách giọng online trả về đúng `vi-VN-NamMinhNeural` (Male) và `vi-VN-HoaiMyNeural` (Female).
2. Probe đầu ở tốc độ -10%: cả hai lượt lỗi `NoAudioReceived`. Ma trận 8 lượt không retry: 4 thành công / 4 lỗi; không coi việc nâng phiên bản là bảo đảm hết lỗi.
3. Lượt API đầu với tối đa hai lần gọi: **1/4 thành công**. Sau chuyển sang tốc độ tự nhiên và tối đa ba lần gọi trong deadline: **3/4 thành công**. Các số này là mẫu chẩn đoán nhỏ, không phải benchmark SLA hoặc tỷ lệ tin cậy production.
4. Hai file câu mẫu phân số của phiên bản sau tạo thành công: Nam Minh 189.774 byte / 5,928 s / RMS 0,08749; Hoài My 198.222 byte / 6,192 s / RMS 0,11248. Cache phát lại trả đúng byte cũ. Có lưu hash trong summary.
5. Nhận dạng lại hai file bằng Whisper qua luồng hiện có đều trả: “Em gộp 1 phần 3 với 2 phần 5. Các phần phải có cùng kích thước trước khi cộng.” Đây là kiểm tra khả năng hiểu lời bằng máy, **không thay cho đánh giá âm sắc của người nghe**.
6. API runtime thực tế dùng ASGI transport với provider online thật: kiểm tra có/không có internal key, owner khác và revision cũ. Spring được kiểm tra riêng bằng MockMvc/MockRestServiceServer; không gọi đây là phép thử JWT toàn hệ thống hoặc thiết bị thật.
7. Giao diện từ bản Student web export thật: 6 viewport (320×568, 360×800, 390×844, 768×1024, 844×390, 1440×900), 12 ảnh. API đăng nhập/bài học được fixture; âm thanh dùng hai WAV online thật. Không tràn ngang; chọn giọng, lưu lựa chọn và mở lại đúng giọng. Ở 390 px đã kiểm tra phát với đồng hồ audio tăng, giọng cũ dừng khi đổi, tua bằng slider, nghe lại và tạm dừng. Đây là bằng chứng trình duyệt headless, không khẳng định đã nghe loa.

## Kiểm thử mã và build

- **92/92 Python test**: giọng online, retry/deadline/dọn file, lời giảng riêng tư, cache theo giọng, file câm/cụt, video, hội thoại, hướng dẫn và YOLO adapter.
- **107/107 Student test, 7 suite**: player, chuyển giọng, lưu giọng, phản hồi trễ, retry, timeline, ghi âm, màn học và video.
- **125/125 Java test**: 42 controller + 83 service, gồm hai giọng, giọng ngoài danh sách, RBAC và owner xác thực. Gradle 9.3.1 cục bộ được dùng để tránh sửa wrapper của dự án.
- TypeScript, ESLint cho phần thay đổi, `uv lock --check`, `git diff --check` đạt.
- Student web export và Android/Hermes export đạt. Lượt web đầu thiếu cấu hình địa chỉ dịch vụ đã bị production guard chặn; lượt sau cung cấp địa chỉ HTTPS hợp lệ để build, không nới guard. Browser QA chặn API bằng fixtures.
- Hai lỗi setup ban đầu trong test Python là tên tham số bytes quá dài với đường dẫn tạm Windows; đã đặt ID test ngắn và chạy lại. Các lỗi kiểu ref/key event ở React Native mới đã sửa; kiểm tra ARIA bằng DOM phát hiện trạng thái checked chưa xuất hiện, đã bổ sung và chạy lại cả browser QA.
- Khi kiểm tra tua bằng phím, chờ đồng hồ player đồng bộ vị trí End trước khi phát lệnh kế tiếp; không sửa hoặc tuyên bố tối ưu thêm độ trễ seek của player cũ.

## Đánh giá đưa vào sử dụng

Phần giao diện hai giọng, quyền truy cập, chuyển giọng và phát lại đã nối vào code hiện tại. Các file WAV mẫu đều có tiếng Việt và trình phát giải mã/phát được trong trình duyệt. **Chưa đủ bằng chứng để gọi dịch vụ online ổn định hoàn toàn hoặc thay toàn bộ hệ thống tiếng/video bằng nó.** Giữ retry và transcript khi gặp lỗi; cần kiểm tra thêm trên Android thật và theo dõi nhà cung cấp trước khi coi đây là thay thế production đã nghiệm thu.

Không train model, đổi corpus, promote OCR, merge nhánh nghiên cứu, commit hoặc push trong lượt này. Những thay đổi giao diện có từ trước được bảo toàn ngoài phần nghe giảng cần bổ sung hai giọng.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tích hợp chọn lọc, giữ luồng và giới hạn hiện có.
  - Applied to: provider có giới hạn, endpoint narration đang dùng, cache và kiểm tra phiên; không thêm stack player/cache mới.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native và tải âm thanh bất đồng bộ.
  - Applied to: hủy request, bỏ phản hồi trễ, dọn tài nguyên khi chuyển giọng và tránh tạo lại audio khi chỉ mở transcript.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: hai lựa chọn giọng cần dễ hiểu trên điện thoại.
  - Applied to: nút chạm 52 px, khoảng cách 10 px, tên/giới tính rõ ràng, ARIA và keyboard; kiểm tra 6 viewport.
