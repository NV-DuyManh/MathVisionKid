# Sửa chuẩn bị giọng toàn bài và lời giảng dài

Ngày 27/10/2026. Phạm vi: giọng nghe bài học trên Student, hàng đợi chuẩn bị tiếng, API theo dõi và kiểm thử. Không huấn luyện hoặc thay model OCR; không commit/push trong đợt này.

## Kết quả trên thiết bị của người dùng

Sau khi nạp đồng bộ bản sửa, người dùng được yêu cầu tải lại app, mở bài mới, làm/đọc bước đầu rồi thử nghe và nghe tổng kết. Câu trả lời nhận được trong cuộc trò chuyện: **“Nghe được, ít phải chờ hơn”**.

Đây là xác nhận do chủ dự án thử trên Android Expo Go, không phải phép đo điện thoại do agent thực hiện. Chưa đo thời gian từ bấm đến tiếng phát trên Android; chưa có xác nhận riêng mọi độ dài bài, từng giọng, mọi thao tác tua và mọi điều kiện mạng. Bằng chứng: [android-owner-confirmation.json](voice-full-prefetch-20261027/android-owner-confirmation.json).

## Nguyên nhân xác định từ mã và ảnh

1. Hàng đợi trước đó chuẩn bị lời hướng dẫn **trước khi trả lời** mỗi bước. Khi học sinh mở bản đọc **sau khi trả lời** hoặc bản tổng kết, nội dung khác nên không trúng bộ nhớ tiếng đã tạo. Việc đã chuẩn bị một kịch bản không đồng nghĩa đã có mọi phiên bản sẽ phát.
2. Bản tổng kết cũ gom cả lời giải, hướng dẫn chọn đáp án, ví dụ và chi tiết tính của nhiều bước. Ảnh người dùng gửi có nội dung lặp lại và đang tạo 9/12 đoạn. Càng nhiều đoạn càng nhiều lượt dịch vụ cần hoàn thành.
3. Đường nghe trực tiếp cũ vẫn phụ thuộc yêu cầu HTTP chờ tạo tiếng: giới hạn upstream 40 giây, ứng dụng 45 giây. Khôi phục một số đoạn không giải quyết được trường hợp toàn bộ công việc vượt cửa sổ này. **45 giây là hạn chờ chuẩn bị/tải, không phải thời lượng tiếng được phát.**

Không có bằng chứng đủ để kết luận nhà cung cấp đã áp dụng quota mới cho các lần chậm. Thời gian dịch vụ có dao động thật trong kiểm tra ở dưới; không coi ảnh chậm là bằng chứng bị khóa giọng.

## Thay đổi đã thực hiện

### Chuẩn bị đúng các bản tiếng từ đầu bài

Ngay sau khi tạo được kịch bản bài học đã kiểm tra, máy chủ lên hàng đợi cho:

- Lời hướng dẫn trước từng bước như trước.
- Lời đọc kết quả sau mỗi bước toán đã làm đúng.
- Lời tổng kết các bước toán khi hoàn thành.

Ưu tiên giọng đang chọn và bước gần vị trí đang học, sau đó chuẩn bị giọng còn lại. Giữ nguyên **Nam Minh (`vi-VN-NamMinhNeural`) và Hoài My (`vi-VN-HoaiMyNeural`)**, không tự chuyển sang giọng chất lượng khác. Không tự phát âm thanh. Bản video đã dựng cho bước tiếp tục dùng tiếng chuẩn bị sẵn; các bản đọc kết quả/tổng kết mới là **âm thanh**, không tuyên bố đã dựng thêm video tổng kết.

Máy chủ mô phỏng đường giải trên một bản sao phiên học để lấy đúng biểu thức và kết quả. Phiên học thật không bị tăng bước, ghi đáp án hoặc công bố lời giải trước. Mọi lần tải tiếng vẫn kiểm tra tài khoản sở hữu, phiên, revision và đoạn chữ đã được công bố. Kiểm thử chặn cả việc biết nội dung tổng kết rồi cố yêu cầu đọc trước khi mở khóa.

Trên ứng dụng, phần chuẩn bị tiếng cho nội dung hiện tại vẫn chạy khi màn bài học được mở để học sinh đọc. Nó sử dụng chung kết quả với nút nghe và tải tiếng hiện tại xuống bộ nhớ ứng dụng; không chờ mở bảng nghe mới khởi động. Chuẩn bị tương lai ở máy chủ không cần gửi đáp án tương lai xuống máy học sinh.

### Rút gọn bản đọc kết quả cho đúng mục đích

Mỗi bước đã hoàn thành đọc: câu lời giải/tên bước, phép tính với kết quả và đơn vị, phần giải thích. Không đọc lại hướng dẫn chọn đáp án và toàn bộ ví dụ gợi mở trước đó. Không cắt ngang câu hoặc đổi kết quả toán. Các chi tiết đặt tính vẫn có trong phần lời giải bằng chữ của bài học.

Kịch bản chuẩn bị trên máy chủ và kịch bản ứng dụng yêu cầu dùng cùng ba trường này, cùng thứ tự và chuẩn hóa khoảng trắng, để thực sự trúng bộ nhớ tiếng.

### Tách tạo tiếng dài khỏi yêu cầu HTTP chờ lâu

Ứng dụng gọi `POST /lesson/narration/prepare` để bắt đầu tác vụ có kiểm tra quyền; máy chủ trả trạng thái ngắn. Sau đó ứng dụng hỏi trạng thái và chỉ tải WAV khi tệp đã hợp lệ, sẵn sàng.

- Yêu cầu bắt đầu có hạn 5 giây; yêu cầu trạng thái có hạn 3 giây.
- Tác vụ tạo tiếng có ngân sách tổng 120 giây. Ứng dụng theo dõi tối đa 150 giây để còn thời gian lấy trạng thái/tải tệp. Không giữ một yêu cầu tạo tiếng xuyên suốt 150 giây.
- Khi nhà cung cấp thất bại sau khi đã tạo được các đoạn hợp lệ, giữ và dùng lại các đoạn đó. Chỉ tự tiếp tục khi số đoạn hoàn thành thực sự tăng; tối đa bốn lần gọi render trong ngân sách. Không tiếp tục vô hạn khi nhà cung cấp không tạo được gì.
- Tác vụ trùng cùng tài khoản/phiên/nội dung/giọng dùng chung công việc. Khi bận trả mã có thể thử lại, không nhân thêm lượt tạo tiếng cho mỗi lần hỏi tiến độ.
- Có trạng thái thất bại cuối cùng, giới hạn đồng thời và bộ nhớ. Không giữ thêm bản WAV hoặc traceback lớn trong kết quả Future của hàng đợi đã xong.
- Tiến độ vẫn dựa vào đoạn tạo xong và giai đoạn thật. 150 giây là hạn bảo vệ, **không phải mẫu số tính phần trăm**. Không báo 100% chỉ vì đã chờ đủ lâu.

Đường trả WAV đồng bộ cũ được giữ để tương thích. Luồng nghe mới dùng tác vụ nền rồi tải kết quả; không chỉ tăng con số timeout trên luồng cũ.

## Kiểm chứng bằng dịch vụ thật

### Qua API nghiệp vụ đang chạy

Đề tổng hợp vườn cây, bài gồm 5 bước; dùng dịch vụ sinh bài, Edge TTS và bộ dựng video thật trên máy hiện tại:

| Phép đo trong một lượt kiểm tra | Kết quả |
|---|---:|
| Tạo bài | 7.703 giây |
| Sau khi bài trả về: 2 bước có tiếng và video chuẩn bị sẵn | 4.141 giây |
| Gọi đường bắt đầu chuẩn bị cho bước tiếp theo đã có tiếng | 47 ms, trạng thái `ready` |
| Tải WAV bước tiếp theo | 16 ms, HTTP 200, 467.022 byte |
| Kiểm tra video bước tiếp theo | 31 ms, `READY`, có tiếng |
| Yêu cầu không đăng nhập | HTTP 401 |
| Yêu cầu video revision tương lai | HTTP 409 |

Đây là thời gian HTTP trên máy phát triển, không phải thời gian bấm-phát trên điện thoại. Bằng chứng: [http-smoke.json](voice-full-prefetch-20261027/http-smoke.json). Video tải được: [http-later-step.mp4](voice-full-prefetch-20261027/http-later-step.mp4).

### Bao phủ bản đọc kết quả và tổng kết trước khi mở

Một chương trình kiểm tra riêng dùng bài phân số tổng hợp hai bước, giọng Edge và ffmpeg thật. Hàng đợi tạo xong **10 biến thể tiếng** — trước bước, sau bước và tổng kết cho hai giọng — cùng 2 video trước khi chương trình trả lời bước đầu. Mở bản sau bước và tổng kết sau đó **không gọi nhà cung cấp thêm lần nào**. Lấy lại tệp trong bộ nhớ máy chủ mất khoảng 0,097–0,173 ms; tệp WAV được kiểm tra định dạng và có dữ liệu âm thanh khác im lặng.

**Giới hạn quan trọng của phép đo này:** hoàn thành toàn bộ 10 biến thể và video mất **83,406 giây**, có một lần lỗi được thử lại. Tổng cộng 22 yêu cầu tạo đoạn tiếng, 3.651 ký tự sau chuyển cách đọc toán/kể cả lần thử. Đây là bằng chứng hàng đợi chuẩn bị trước hoạt động và dịch vụ vẫn có lúc chậm, không phải bằng chứng mọi bài đều sẵn trong vài giây. Kết quả mở lại nhanh chỉ áp dụng khi tệp đã chuẩn bị còn trong bộ nhớ.

Bằng chứng và mẫu hai giọng: [real-prefetch-benchmark.json](voice-full-prefetch-20261027/real-prefetch-benchmark.json), [tổng kết Nam Minh](voice-full-prefetch-20261027/final-summary-Nam-Minh.wav), [tổng kết Hoài My](voice-full-prefetch-20261027/final-summary-Hoai-My.wav).

## Kiểm thử hồi quy

- Python: **265 qua** — bài học, nhận định nguồn, giọng, video, hàng đợi, quyền truy cập và hội thoại.
- Student: **178 qua / 17 bộ** — nghe, bộ nhớ, chuẩn bị nền, API, ghi âm/câu hỏi, thanh tua, tiến độ và video.
- Java: **134 qua** — controller 48, service 86. Đường bắt đầu tạo tiếng lấy chủ sở hữu từ xác thực máy chủ.
- TypeScript: qua. Lint: 0 lỗi, còn 2 cảnh báo cũ trong `cropRotation.web.ts`.
- Export web và Android: qua. Lần export web đầu thiếu địa chỉ dịch vụ cấu hình nên dừng đúng kiểm tra; chạy lại với địa chỉ HTTPS mẫu chỉ để kiểm tra build đã qua. Không triển khai địa chỉ mẫu, không thay cấu hình máy đang chạy. Android ở đây là xuất bundle, không phải cài APK.
- Có kiểm thử đồng hồ giả: tác vụ nền tiếp tục các đoạn còn thiếu và hoàn thành ở giây mô phỏng 55; client vẫn chờ sau giây 46 bằng các yêu cầu ngắn. Đây là kiểm thử mô phỏng thời gian, không ghi thành số đo nhà cung cấp thật.
- Tệp không hợp lệ không được đưa vào bộ nhớ; tác vụ lỗi có trạng thái cuối; gọi lặp không tạo thêm việc; tiếng tương lai vẫn bị từ chối; giọng dự phòng chỉ bật theo lựa chọn rõ ràng.

Tổng hợp và dấu kiểm nguồn: [verification.json](voice-full-prefetch-20261027/verification.json). Nhật ký kiểm thử nằm trong `runtime/voice-full-prefetch-*-20261027.log`.

## Giới hạn và chi phí phải biết

- Không thể cam kết phản hồi bằng 0 khi chưa tạo xong, đổi mạng, nhà cung cấp lỗi hoặc tệp đã bị loại khỏi bộ nhớ. Lỗi mạng vẫn có thể cần thử lại.
- Chạy nền vẫn sử dụng dịch vụ TTS cho những phần học sinh có thể không nghe; không đồng nghĩa miễn quota hoặc dùng vô hạn. Việc bổ sung các biến thể tạo thêm nhu cầu TTS. Không gọi thêm model sinh lời giải chỉ để chuẩn bị các kịch bản này.
- Hàng đợi giữ nguyên ngân sách **72.000 ký tự văn bản gốc cho cả hai giọng trong một bài**, tối đa 4 bài đang giữ; có giới hạn lỗi từng giọng và bỏ hàng đợi bài cũ cùng học sinh. Ký tự sau chuyển phát âm và lượt thử lại không nên nhầm với số ký tự gốc của ngân sách này.
- Kho WAV 32 MiB, tối đa 64 mục, mỗi WAV tối đa 8 MiB/4 phút; đầu vào một bản nghe tối đa 4.000 ký tự. Tệp cũ có thể bị loại để giữ bộ nhớ ổn định. Không tuyên bố hỗ trợ bản đọc dài vô hạn.
- Câu hỏi tự do chưa được học sinh hỏi không thể chuẩn bị câu trả lời từ trước. Khi câu trả lời đã có, sử dụng cùng luồng chuẩn bị tiếng/bộ nhớ; không đoán trước câu hỏi.
- Tác vụ nền bắt đầu sau khi đã có kịch bản bài học hợp lệ. Không thể tạo chính xác tiếng cho các bước chưa có kịch bản khi còn chụp/cắt/nhận diện ảnh.

## Trạng thái bàn giao

Đã nạp bản sửa vào dịch vụ giọng, API nghiệp vụ và trình phục vụ Student tại máy phát triển. Phiên bài học nằm trong bộ nhớ nên sau khi nạp lại cần mở bài mới; người dùng đã thử và xác nhận ít chờ hơn. Không thay hoặc huấn luyện model, không commit/push, không sửa các tệp OCR hay `demoUI/` ngoài phạm vi.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa luồng nền và timeout bằng cơ chế công việc, bộ nhớ và kiểm tra quyền đã có; hạn chế thêm hệ thống hoặc dependency.
  - Applied to: hàng đợi chuẩn bị, API bắt đầu/theo dõi/tải, giới hạn tác vụ, phục hồi đoạn, kiểm thử và báo cáo.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: luồng React/React Native lấy tiếng sẵn, dùng chung công việc và kiểm soát vòng đời yêu cầu.
  - Applied to: nội dung đọc kết quả, client polling ngắn, tải tiếng và trạng thái chờ ở màn nghe.
