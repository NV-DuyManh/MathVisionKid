# Giọng nói, tiến độ chờ và đăng nhập Student — 27/10/2026

Đã sửa code và nạp lại dịch vụ cục bộ. **Nam Minh và Hoài My vẫn là hai giọng chính. Không tự đổi sang giọng khác để đổi lấy tốc độ.** Giọng dự phòng trên máy chủ hoặc thiết bị chỉ dùng sau thao tác chọn của học sinh. Không commit/push trong lượt này.

[Xem ảnh giao diện và nghe mẫu](voice-reliability-20261027/index.html) · [Kết quả đo cuối](voice-reliability-20261027/quality-policy-final.json) · [Kiểm thử Student](voice-reliability-20261027/student-tests.json)

## 1. Nguyên nhân đã xác định

### Giọng trước đây nhanh hơn vì đường tạo tiếng đã thay đổi

Đã đối chiếu Git: ở `71ad997`, `narration.render_audio` gọi `synthesize`, tức bộ đọc cục bộ trên máy chủ rồi chuẩn hóa WAV. Bản `3b80e41` chuyển sang `synthesize_neural` qua Edge online để có hai giọng Nam Minh và Hoài My. Đường dự phòng cục bộ không còn trong luồng nghe giảng lúc đó.

Sự thay đổi này làm thời gian chờ phụ thuộc thêm vào mạng và dịch vụ online. Log thực tế có `TimeoutError`, `NoAudioReceived`, HTTP 503; có lượt hết 25 giây. Phiên bản đang cài là `edge-tts==7.3.1`. Không có bằng chứng để kết luận nhà cung cấp đã ngừng dịch vụ, hoặc lỗi hôm nay là do đang dùng lại phiên bản 7.2.8.

README của [edge-tts](https://github.com/rany2/edge-tts) xác nhận thư viện dùng dịch vụ đọc online của Edge. Các phép đo tại từng thời điểm khác nhau không đủ tách riêng ảnh hưởng của mạng, tải dịch vụ và nội dung; không quy hết lỗi cho một bên khi thiếu dữ liệu.

### Ảnh “Mở lời giảng” là một tình huống khác với chờ tạo tiếng

Ở bước đó, app đã nhận được tệp và giao cho trình phát. Code cũ không đặt hạn chờ giải mã; player chưa báo `isLoaded` và chưa báo lỗi thì giao diện có thể chờ mãi, thời lượng vẫn 0:00. Đã xác định lỗ hổng xử lý này trong code. Chưa có log ExoPlayer từ điện thoại trong ảnh, nên chưa kết luận nguyên nhân giải mã cụ thể trên máy Android đó.

Các yếu tố phụ đã được xử lý hoặc giữ lại từ bản sửa trước: khóa tạo tiếng chỉ cho một request chạy; request trùng bị tạo lại hoặc bị từ chối; cache tám mục dễ phải tổng hợp lại khi mở các bước cũ.

### Web có vòng tải lại trang đăng nhập

`AuthContext.web.tsx` trước đây gọi `window.location.replace('/login')` khi không có token, đồng thời chỉ render nội dung khi đã có user. Khi chạy Student độc lập ngay tại `/login`, trang có thể tải lại chính nó và form không được mở.

Ngoài ra, client dùng chung có thể làm mới token cả khi `/auth/login` trả 401; nhánh không có refresh token không giải phóng hết request đang chờ; lời gọi refresh không có timeout riêng. Các nhánh này làm lỗi xác thực khó phân biệt với giao diện đang tải.

## 2. Cơ chế giọng nói cuối cùng

1. Mặc định chỉ tổng hợp đúng `vi-VN-NamMinhNeural` hoặc `vi-VN-HoaiMyNeural` đã chọn. Giọng được lưu theo lựa chọn cũ. Lỗi online không tự chuyển giọng.
2. Lời giảng dài được chia ở khoảng trắng, khoảng 220 ký tự mỗi đoạn, tối đa hai đoạn tổng hợp cùng lúc. Ghép theo đúng thứ tự rồi giải mã WAV; không trả audio dở dang, không lặp lại phần nhận được từ một lần thử lỗi.
3. Thời gian tạo online tối đa 25 giây; tổng công việc server có hạn 32 giây. Client có ngân sách tải 45 giây, kể cả retry ngắn khi hết slot. Khi thất bại, hiển thị lỗi và thao tác thử lại; không để spinner vô hạn.
4. Học sinh có thể chọn **“Dùng giọng dự phòng (âm sắc khác)”** sau lỗi. Khi đó mới gửi `useFallback: true`; máy chủ dùng bộ đọc tiếng Việt đã cài. Trên Windows hiện tại, bộ đọc này đã tạo được audio thật. Docker hiện có `espeak-ng`; chưa chạy kiểm chứng âm sắc trong Linux/container ở lượt này.
5. Cache tách riêng lựa chọn dự phòng và hai giọng chính. Audio dự phòng không được dùng để trả cho request Nam Minh/Hoài My thông thường. Chọn lại một trong hai radio sẽ quay về giọng chính. Lựa chọn dự phòng không ghi đè giọng yêu thích.
6. Có thêm cách đọc bằng giọng Việt trên thiết bị, không phụ thuộc máy chủ tạo tiếng. Chỉ đọc khi bấm; chỉ chọn giọng Việt; có dừng và nghe lại từ đầu. Cách này không có thanh tua và tùy thuộc bộ TTS đã cài, được nói rõ trên giao diện. Không khẳng định mọi thiết bị đều có giọng Việt hoặc mọi engine thiết bị đều hoạt động offline.

Hai render server có thể chạy song song; request trùng chia sẻ cùng kết quả. Cache LRU giữ tối đa 64 mục, 32 MiB, tối đa 15 phút và không vượt tuổi phiên. Vẫn kiểm tra owner, session, revision và nội dung đã công bố trước khi dùng cache, sau khi tạo và sau khi chờ request trùng.

Giọng dự phòng cục bộ dựa vào [Windows SpeechSynthesizer](https://learn.microsoft.com/en-us/uwp/api/windows.media.speechsynthesis.speechsynthesizer?view=winrt-26100), vốn dùng engine đã cài. Âm sắc không được coi tương đương hai giọng neural. [Expo Speech](https://docs.expo.dev/versions/v58.0.0/sdk/speech/) cung cấp danh sách giọng trên thiết bị; khả năng đọc phụ thuộc giọng hiện có.

Nếu cần giữ đúng hai âm sắc này khi Edge không hoạt động lâu dài, có thể đánh giá API Speech chính thức: [danh sách giọng Azure](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) có Nam Minh và Hoài My. **Chưa cấu hình, mua dịch vụ hoặc tuyên bố đã kiểm chứng Azure trong dự án.** Hiện tại giải pháp đã chạy là hai giọng chính kèm lựa chọn dự phòng có thông báo.

## 3. Tiến độ và thời gian chờ

- `TaskProgress` có thanh tiến độ, spinner cho nhiệm vụ hiện tại, trạng thái từng bước, số giây đã chờ và giới hạn chờ. Không tự đánh dấu công việc xong vì đã trôi qua một khoảng thời gian.
- Tạo giọng có endpoint tiến độ riêng, vẫn đi qua xác thực Student ở backend. Client đọc khoảng mỗi 1,2 giây; mỗi lần đọc tiến độ có timeout 3 giây. Lỗi đọc tiến độ không hủy một lượt tải audio hợp lệ.
- Phần trăm là **tiến độ theo các phần chuẩn bị đã hoàn tất**, không phải phần trăm CPU hay dự đoán chính xác thời gian còn lại: 10% khi đã nhận công việc; các đoạn hoàn tất đưa mức này đến 80%; bắt đầu chuẩn hóa WAV là 90%; server kiểm tra xong tệp mới báo 100%. Client giữ dưới mức hoàn tất trong lúc tải/mở, và hiển thị 95% khi chờ player giải mã.
- Trình phát âm thanh có hạn mở tệp 12 giây, sau đó chuyển sang thông báo lỗi/thử lại hoặc lựa chọn dự phòng. Có kiểm tra trường hợp player báo sẵn sàng muộn để không khóa vĩnh viễn bản ghi đã mở được. Video cũng có hạn mở 12 giây.
- Màn đọc đề/chuẩn bị bài học hiển thị phần trăm theo các bước thực sự hoàn tất và đồng hồ chờ. **Dịch vụ soạn bài/OCR đang là lời gọi nguyên khối, chưa có số liệu phần trăm nội bộ của mô hình.** Vì vậy bước đang chờ có thể giữ ở 33%, kèm spinner và thời gian; không bịa số tăng lên 90–99% để tạo cảm giác đang tiến triển.
- Video dùng phần trăm dựng mà API đã báo, rồi chuyển sang tải/mở. Các màn khác dùng thành phần tiến độ chung đã có đồng hồ và trạng thái.
- Khởi động web không chặn đăng nhập vô hạn chỉ vì tải font hoặc hình trang trí: tối đa 12 giây chờ phần trang trí rồi tiếp tục; xác thực tài khoản vẫn phải qua backend.

## 4. Đăng nhập web

- Student chạy độc lập render được form `/login` khi chưa có token, không tải lại chính trang đó. Các đường dẫn bảo vệ vẫn chờ xác thực `/me`.
- Luồng nhúng dưới `/study` hoặc đường dẫn cũ `/learn` giữ điều hướng về cổng đăng nhập tương ứng.
- Hồ sơ lưu trong trình duyệt không được dùng làm bằng chứng đăng nhập. Vai trò khác Student hoặc tài khoản không hoạt động không vào phần học.
- Không đính kèm token cũ vào request đăng nhập mới; không tự refresh khi chính login/refresh/logout trả 401. Refresh có timeout 8 giây, request đã thử lại không lặp vô hạn, hàng đợi được giải phóng cả khi thiếu refresh token.
- Khôi phục phiên có hạn chờ; đăng nhập và đọc hồ sơ có timeout riêng. Đã thử đăng nhập, tải lại trang và đăng xuất bằng tài khoản mẫu cục bộ; cuối kiểm tra đã đăng xuất tài khoản đó.

## 5. Kết quả đo cuối cùng

Nguồn: [quality-policy-final.json](voice-reliability-20261027/quality-policy-final.json). Nội dung là câu mẫu tự tạo dài 322 ký tự, không gửi ảnh hoặc lời nói của học sinh thật.

| Phép kiểm tra | Kết quả quan sát |
| --- | --- |
| Nam Minh, provider online thật qua API ASGI | HTTP 200, 1,359 giây; audio dài 24,648 giây |
| Hoài My, provider online thật qua API ASGI | HTTP 200, 1,578 giây; audio dài 25,008 giây |
| Nghe lại từ cache, cùng request | Đúng byte cũ; thời gian dưới độ phân giải ghi nhận 0,1 ms ở lượt đo ASGI này |
| Tiến độ tạo giọng | Có quan sát 10%, 45%, 90%, 100%; một lần poll có thể bỏ qua bước nhanh giữa hai lượt đọc |
| Cố tình làm provider online lỗi | Request giọng chính trả 503, không tự thay giọng |
| Chủ động chọn giọng dự phòng sau lỗi | HTTP 200, 1,438 giây, WAV hợp lệ |
| Gọi lại giọng chính khi provider vẫn bị giả lập lỗi | Vẫn 503; cache dự phòng không lẫn vào giọng chính |

Các số ASGI bao gồm provider online thật và xử lý server, **không bao gồm truyền WAV tới điện thoại, giải mã/loa Android hoặc mạng của học sinh**. Đây là mẫu chẩn đoán nhỏ ở thời điểm đo, không phải p95, SLA hay bảo đảm mọi lượt đều dưới hai giây. Lượt trước trong cùng ngày từng có timeout 25 giây; không xóa hoặc phủ nhận bằng chứng đó.

Đã kiểm tra WAV không câm/cụt và nhận dạng lại mẫu dự phòng bằng máy: [offline-asr-final.json](voice-reliability-20261027/offline-asr-final.json) có SHA-256 của tệp cùng văn bản đọc lại. Kết quả máy đọc đúng nội dung mẫu; đây không phải đánh giá âm sắc của người nghe.

Thử nghiệm tự chuyển dự phòng 8 giây đã được thực hiện trước khi người dùng chốt ưu tiên âm sắc. **Cơ chế đó đã bỏ khỏi bản cuối**, không dùng số đo của nó làm cam kết hiệu năng hiện tại.

## 6. Kiểm thử và ảnh thực tế

- **58/58 Python:** tạo tiếng, chia đoạn, ghép đúng thứ tự, deadline/hủy stream, không nhận file câm/cụt, cache và request trùng, tiến độ riêng tư, lựa chọn dự phòng rõ ràng, cách ly cache giữa các chế độ, video và hội thoại.
- **112/112 Student, 9 suite:** chuyển giọng, hủy tải, phản hồi đến muộn, không retry lỗi provider/phiên, retry bận có giới hạn, watchdog giải mã, bản ghi sẵn sàng muộn, dừng/nghe lại, giọng thiết bị không bắt đầu, phần trăm/thời gian, playback/video và màn bài học.
- **8/8 kiểm tra Node cho phiên web:** bảo vệ deep link, backend từ chối token, vai trò không phù hợp, logout và `/login` độc lập không tự tải lại.
- **129/129 Java:** 85 service và 44 controller. Có kiểm tra owner từ xác thực, chế độ dự phòng được chuyển đúng, percent sai bị từ chối, header no-store và Teacher không được đọc tiến độ Student.
- TypeScript, ESLint các phần production sửa và `git diff --check` đạt. Export web và Android/Hermes từ code cuối đạt; xuất được không đồng nghĩa đã thử loa trên thiết bị thật.
- Trình duyệt thực tế, không mock API ở bước giao diện: đăng nhập → trang chủ; tải lại vẫn về trang chủ khi phiên hợp lệ; xác nhận đề → tạo bài học → mở Nghe giảng → phát → hoàn tất → tua bằng thanh trượt; đăng xuất → form đăng nhập. Có ảnh viewport 390×844 và desktop. Âm thanh chuyển trạng thái phát/hoàn tất trong trình duyệt; chưa khẳng định đã nghe bằng loa vật lý.

Ảnh: [đăng nhập desktop](voice-reliability-20261027/screenshots/student-login-desktop.jpg), [đăng nhập mobile](voice-reliability-20261027/screenshots/student-login-mobile.jpg), [tiến độ tạo bài học](voice-reliability-20261027/screenshots/lesson-loading-mobile.jpg), [giọng sẵn sàng/phát](voice-reliability-20261027/screenshots/voice-ready-mobile.jpg).

## 7. Giới hạn và phạm vi bảo toàn

Chưa kiểm thử loa/giải mã trên điện thoại Android trong ảnh, trình duyệt iOS, mọi engine TTS, máy không có giọng Việt hoặc tải đồng thời của nhiều lớp học. Dịch vụ online vẫn có thể lỗi; bản sửa đảm bảo đường xử lý lỗi có hạn chờ và lựa chọn phục hồi trong các tình huống đã kiểm tra, không thể hứa không có lỗi trong mọi môi trường.

Không thay OCR/model, không train, không đổi RBAC, không thêm thư viện, không thay tiếng video offline. Hai file `scripts/data/recognize_line_batch.py` và `scripts/data/test_recognize_line_batch.py` đã sửa từ công việc OCR trước, được giữ nguyên. Không merge, commit, push hay triển khai production trong lượt này.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa đường xử lý hiện có, dùng lại bộ đọc cục bộ và thư viện đã cài.
  - Applied to: giới hạn render/cache, chia sẻ request trùng, lựa chọn dự phòng tường minh và kiểm thử các nhánh lỗi.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: tải giọng, polling tiến độ và xác thực React/React Native.
  - Applied to: hủy request/timer, bỏ phản hồi trễ, tránh lặp refresh, tải song song có giới hạn và không autoplay.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: phản hồi chờ, trạng thái lỗi, tiến độ và tính dễ hiểu trên màn hình điện thoại.
  - Applied to: phần trăm có nguồn, đồng hồ, nhãn nhiệm vụ, thao tác thử lại/dự phòng và ảnh kiểm tra giao diện thực tế.
