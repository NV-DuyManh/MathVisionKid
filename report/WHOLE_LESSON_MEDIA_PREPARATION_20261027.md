# Chuẩn bị trước giọng đọc và video cho toàn kịch bản bài học

Ngày kiểm tra: 27/10/2026. Phạm vi: các bước cố định của bài học đã tạo và kiểm tra hợp lệ, hai giọng Nam Minh và Hoài My, video minh họa có tiếng, quyền truy cập và chi phí yêu cầu nền.

## Kết quả triển khai

Đã chuyển từ tải trước riêng bước đang xem sang hàng đợi chuẩn bị các bước phía sau trên máy chủ. Ngay khi tạo bài học thành công, hàng đợi bắt đầu chạy; học sinh không phải mở mục Nghe giảng để kích hoạt.

Thời điểm bắt đầu là **sau khi xác nhận nội dung nhận diện và tạo được kế hoạch hợp lệ**. Chỉ chụp/cắt ảnh chưa đủ để tạo tiếng đúng bài, vì học sinh còn có thể sửa phần nhận diện.

Luồng hiện tại:

1. Máy chủ giữ kế hoạch riêng và tạo bản mô phỏng các bước để xác định đúng nội dung đọc của từng bước. Việc mô phỏng không thay đổi tiến độ thật, không mở đáp án hay phát tiếng.
2. Ưu tiên giọng đang chọn cho bước hiện tại và các bước còn lại; sau đó mới chuẩn bị giọng thứ hai. Khi đọc được tùy chọn đã lưu trên ứng dụng, ứng dụng gửi tùy chọn đó để cập nhật thứ tự hàng đợi.
3. Cùng một nội dung, giọng và phiên học dùng chung một tác vụ và bộ nhớ đệm. Bấm nghe trong lúc đang tạo sẽ dùng chung công việc đã bắt đầu.
4. Video từng bước dùng lại đúng âm thanh đã tạo, không gọi dịch vụ giọng thêm lần nữa. Video được dựng trước cho giọng ưu tiên. Nếu đổi sang giọng kia, tiếng có thể đã sẵn nhưng video tương ứng còn phải dựng khi mở.
5. Mỗi lần tải tiếng/video, máy chủ vẫn kiểm tra chủ phiên, thời hạn và bước hiện tại. Chỉ số tiến độ chuẩn bị trả về số lượng; không gửi nội dung, đáp án hoặc mã video tương lai xuống ứng dụng.

Câu hỏi học sinh chưa nói, câu trả lời hỏi đáp mới, gợi ý bổ sung sau khi chọn sai và bản nghe tổng hợp cuối bài không thuộc các kịch bản cố định được chuẩn bị ở hàng đợi này. Luồng tải trước nội dung hiện tại vẫn phục vụ các phần đó sau khi nội dung được tạo.

## Đo bằng dịch vụ thật

Kiểm tra HTTP đăng nhập thật qua máy chủ nghiệp vụ và máy chủ AI nội bộ, dùng đề vườn cây tổng hợp để thử. Không phải số đo phát tiếng trên điện thoại thật.

| Hạng mục | Kết quả ghi nhận |
|---|---:|
| Tạo bài học 5 bước | 8.297 ms |
| Hai bước có tiếng và video chuẩn bị sẵn, kể từ sau phản hồi tạo bài | 6.234 ms |
| Sang bước thứ hai, tải tiếng đã chuẩn bị qua HTTP | 156 ms |
| Mở video đã chuẩn bị của bước thứ hai | 47 ms, trạng thái READY |
| Tệp video tải được | 254.374 byte, H.264 960×540 và AAC, 14,592 giây |
| Chưa đăng nhập gọi chuẩn bị | HTTP 401 |
| Xin video của revision tương lai | HTTP 409 |

Bằng chứng: [HTTP smoke](whole-lesson-media-20261027/http-smoke.json), [video tải thật](whole-lesson-media-20261027/http-later-step.mp4), [kiểm tra định dạng và mã nguồn](whole-lesson-media-20261027/verification.json).

Sau khi bổ sung thử lại hữu hạn, lượt thử cuối với toàn bộ kế hoạch phân số hai bước đã hoàn tất đủ **bốn bản tiếng (hai bước × hai giọng) và hai video của giọng ưu tiên**, trước khi mở bước thứ hai. Tổng chuẩn bị nền 45,891 giây; khi mở bước sau có **0 yêu cầu TTS phát sinh thêm**, cả hai bản tiếng dài khoảng 50–51 giây hợp lệ, video có luồng AAC. Lượt này thực tế ghi nhận 16 yêu cầu tới dịch vụ, gồm các lần thử ở lớp chia đoạn. Số đo dùng lại WAV trong tiến trình ghi 0,0 ms do độ phân giải đồng hồ đo trên Windows; không diễn giải con số đó thành thời gian bấm-phát bằng không. [Bằng chứng toàn bài với dịch vụ thật](whole-lesson-media-20261027/real-media-benchmark.json), [video bước sau](whole-lesson-media-20261027/later-step.mp4).

**Đã có các lượt tạo giọng thật bị timeout khoảng 25 giây.** Ba lượt thử riêng kế hoạch phân số dài không hoàn tất toàn bộ trước khi bổ sung cơ chế thử lại có giới hạn. Các kết quả lỗi được giữ trong thư mục bằng chứng, không thay bằng kết quả giả thành công. Đo hai giọng với đoạn ngắn ghi nhận Nam Minh khoảng 5,7 giây, Hoài My khoảng 8,2 giây. Một lượt đo từng đoạn của phần phân số ghi nhận ba yêu cầu lần lượt khoảng 1,0; 1,3 và 8,9 giây. Những số này cho thấy thời gian đáp ứng dịch vụ ngoài biến động; chưa đủ bằng chứng kết luận lỗi do hết quota hay do một nguyên nhân mạng cụ thể.

Một lượt tạo bài thử với đề táo cũng bị từ chối an toàn sau hai lần mô hình đưa kết quả tính sẵn vào phần công khai. Đây là bước kiểm tra kế hoạch trước hàng đợi tiếng; không được coi là lỗi bộ đệm hoặc bỏ qua kiểm tra để làm phép thử thành công. Bằng chứng được lưu ở `http-first-validation-rejected.json`.

Không cam kết 0 ms: cần tệp đã tạo xong, còn trong bộ đệm, cùng nội dung và giọng; truyền tệp, giải mã và mở trình phát vẫn mất thời gian. Chưa xác nhận phát/tua trên Android thật hoặc duyệt giao diện bằng trình duyệt trong lượt này.

## Khi dịch vụ chậm hoặc lỗi

- Không đổi sang giọng chất lượng thấp hơn một cách tự động; vẫn giữ hai mã `vi-VN-NamMinhNeural` và `vi-VN-HoaiMyNeural`.
- Giữ các tệp đã tạo thành công; một đoạn lỗi không xóa cả bài. Đoạn chưa có được xếp thử lại sau các đoạn chưa xử lý và giọng còn lại.
- Giới hạn tối đa hai lần tạo thất bại cho mỗi giọng trong một đợt nền. Hết giới hạn thì dừng phần nền của giọng đó; mở nghe trực tiếp vẫn có thể yêu cầu lại. Đây là giới hạn số lượt dựng thất bại; mỗi lượt dựng còn có giới hạn thời gian và lần thử từng đoạn ở lớp dịch vụ.
- Tác vụ nền có thể nhường chỗ khi yêu cầu trực tiếp cần tài nguyên. Không hủy một tác vụ nền đang được yêu cầu trực tiếp chờ dùng chung.
- Một hàng đợi nền hoạt động tại một thời điểm, tối đa bốn bài giữ trong hàng đợi; mỗi học sinh giữ một bài nền. Mở bài khác hủy phần nền còn dư của bài cũ.
- Tiếng giữ tối đa 64 mục/32 MiB, hạn tối đa 15 phút và không vượt phiên; video chuẩn bị giữ tối đa 64 MiB. Có thể phải tạo/tải lại khi bị đẩy khỏi bộ đệm.
- Chạy nền diễn ra trên máy chủ, không phụ thuộc điện thoại còn bật màn hình. Hàng đợi và bộ đệm hiện ở trong tiến trình, không tồn tại qua lần khởi động lại máy chủ. Phiên học cũng giữ quy tắc hết hạn hiện có.

## Có tốn token hoặc quota không?

**Có sử dụng dịch vụ giọng. Chạy nền không làm các yêu cầu đó được miễn giới hạn.** Phần này lấy lại kế hoạch đã có và tính toán xác định, không gọi mô hình ngôn ngữ thêm để viết lại từng bước; vì vậy không phát sinh token LLM từ riêng việc chuẩn bị lại các bước cố định. Nhận diện, tạo kế hoạch ban đầu, nhận giọng hỏi và trả lời câu hỏi mới vẫn có chi phí/giới hạn riêng.

`edge-tts` hiện dùng dịch vụ đọc trực tuyến của Microsoft Edge. Trong README đã kiểm tra không có hạn mức tài khoản theo ngày/tháng hoặc cam kết SLA để có thể kết luận “dùng vô hạn”. Không lấy hạn mức Azure rồi gán cho đường Edge hiện tại. [Tài liệu dự án edge-tts](https://github.com/rany2/edge-tts).

Ví dụ minh họa, không phải lượng dùng thực tế của tài khoản: bài 5 bước, mỗi bước vừa một đoạn gửi dịch vụ, chuẩn bị đủ hai giọng cần 10 lượt tổng hợp. Nếu mỗi bước cần hai đoạn thì thành 20 lượt trước thử lại. Mã hiện chia văn bản nói thành đoạn khoảng 220 ký tự và có thể thử một đoạn tối đa ba lần trong giới hạn thời gian. Video từng bước dùng lại WAV nên không cộng thêm lượt TTS cho phần tiếng đã có. Bộ đệm trúng cũng không gọi TTS lại. `preparedCharacters` chỉ là số ký tự đầu vào đã chuẩn bị theo từng mục, **không phải** bộ đếm tính phí hoặc số yêu cầu thật của nhà cung cấp.

Nếu dùng Azure Speech chính thức, có quota được công bố: F0 20 giao dịch/60 giây; S0 mặc định 30 giao dịch/giây và có cơ chế xin điều chỉnh. Microsoft còn lưu ý 429 có thể liên quan năng lực phục vụ giọng ở vùng triển khai. Đây là lựa chọn để vận hành có tài khoản và quota rõ ràng, cần cấu hình tài khoản/khóa và kiểm thử riêng; **chưa chuyển ứng dụng sang Azure**. [Giới hạn Azure Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits).

Groq công bố các giới hạn yêu cầu, token và giây âm thanh ở cấp tổ chức. Không có bằng chứng về số dư tài khoản hiện tại trong phép thử này; không báo một con số còn lại suy đoán. [Giới hạn Groq](https://console.groq.com/docs/rate-limits).

## Kiểm thử

- 254 kiểm thử Python liên quan hàng đợi, tiếng, video, hỏi đáp và bài học qua.
- 151 kiểm thử trong 15 nhóm phía học sinh qua.
- 132 kiểm thử Java: 46 controller, 86 service, không lỗi.
- TypeScript qua; lint không lỗi, còn hai cảnh báo cũ ở `cropRotation.web.ts`.
- Xuất web và Android thành công với địa chỉ HTTPS cho kiểm tra bản dựng. Không có triển khai lên môi trường công khai. Hai lần thử xuất trước đó bị cấu hình thiếu địa chỉ/địa chỉ HTTP và đã bị chặn đúng; không sửa bỏ kiểm tra cấu hình.
- Có kiểm thử quyền sở hữu, revision tương lai, không công khai đoạn tương lai, không gọi mô hình khi mô phỏng, trùng yêu cầu không tạo lại, nhường chỗ cho yêu cầu trực tiếp, cạn ngân sách, thử lại hữu hạn và lỗi video không chặn phần tiếng còn lại.

Không commit/push trong lượt này. Không thay mô hình OCR hoặc tiến hành huấn luyện.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: hàng đợi và bộ đệm phải dùng lại hệ thống hiện có, tránh bổ sung dịch vụ hoặc thư viện không cần thiết.
  - Applied to: hàng đợi trong tiến trình, mô phỏng kế hoạch, dùng chung tác vụ tiếng và bộ dựng video hiện có, giới hạn tài nguyên và thử lại.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: chuẩn bị dữ liệu sớm trong React Native nhưng không chặn đọc bài hoặc phát âm thanh ngoài ý muốn.
  - Applied to: hook chuẩn bị theo phiên/revision, gửi tùy chọn giọng không chặn giao diện, hủy yêu cầu ứng dụng khi rời màn hình, tái sử dụng bộ đệm phía học sinh.
