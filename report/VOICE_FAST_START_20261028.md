# Giảm độ trễ giọng và khôi phục giới hạn 45 giây

Ngày 28/10/2026. Phạm vi: chuẩn bị tiếng bài học, tái sử dụng âm thanh, mở trình phát Student và giới hạn chờ. Giữ nguyên Nam Minh và Hoài My. Không commit/push; không huấn luyện hoặc thay model.

## Kết luận có bằng chứng

Cơ chế chuẩn bị nền có hoạt động, nhưng bản cũ còn các khâu chờ nối tiếp và làm lại việc đã có. Đã sửa để ưu tiên tiếng, ghép tổng kết từ kết quả đã tạo và lưu tệp trên máy học sinh trong lúc đọc bài. **Giới hạn chờ ở ứng dụng và mỗi tác vụ tạo tiếng hiện là 45 giây; đã bỏ mức 150/120 giây của đợt trước.**

Chưa có bằng chứng đủ để tuyên bố mọi lần tạo mới từ dịch vụ đều đạt 1–3 giây. Lượt kiểm tra mới có bước tạo trong khoảng 2,8 giây, nhưng một kịch bản dài khác vẫn mất khoảng 13 giây. Tiếng đã chuẩn bị được dùng lại nhanh; đó là luồng tối ưu chính. Không đánh đồng thời gian đọc bộ nhớ hoặc HTTP với thời gian phát trên Android.

## Các điểm gây chờ đã sửa

### Sửa thêm sau lượt thử Android chưa đạt

Người dùng đã thử bản đầu trong đợt này và trả lời **“Vẫn hơn 3 giây hoặc lỗi”**. Nhật ký trình phát Android ghi ba thời gian sẵn sàng: **663 ms, 14.055 ms và 2.924 ms**. Vì có một lượt chậm rõ rệt, không đánh giá bản đó đã đạt mục tiêu. Chứng cứ: [android-retest-round1.json](voice-fast-start-20261028/android-retest-round1.json).

Nhật ký máy chủ cùng giai đoạn có các lần tạo tiếng xong nhưng bị `StaleTurn` khi học sinh đã chuyển bước. Đã sửa tác vụ tạo nền: quyền/revision được kiểm tra lúc xếp hàng; khi hoàn tất, tệp được giữ riêng theo chủ sở hữu/phiên dù học sinh đã sang bước khác. Mọi lần đọc công khai vẫn kiểm tra revision hiện tại, quyền và chữ đã công bố. Kiểm thử xác nhận tệp không bị tạo lần thứ hai, trong khi yêu cầu đọc với revision cũ vẫn bị từ chối.

Ứng dụng cũng ngừng tự tạo thêm công việc công khai cho **giọng chưa chọn**: máy chủ đã có hàng đợi chuẩn bị cả hai, nên lượt trùng trên ứng dụng có thể tranh tài nguyên với bước tiếp theo. Ứng dụng chỉ tải/lưu trước giọng đang chọn, rồi thay ưu tiên khi học sinh đổi giọng. Hai lựa chọn vẫn giữ nguyên. Câu trả lời hỏi đáp cũng chuẩn bị giọng đang chọn khi học sinh đọc câu trả lời.

### Không dựng video xen giữa các lượt tạo tiếng

Hàng đợi trước đây tạo tiếng cho một bước rồi chờ dựng video bước đó trước khi tiếp tục tiếng của bước khác. Hiện tại âm thanh của các bài đang xếp hàng được ưu tiên hoàn tất trước video tùy chọn. Khi học sinh chủ động mở video một bước đã có tiếng, đường dựng video hiện có vẫn dùng lại WAV đó.

Các bước sắp đọc được ưu tiên trước các bản đọc kết quả ở xa. Khi học sinh đã sang bước sau, lượt chuẩn bị lời trước bước cũ chưa được dùng có thể nhường việc; lượt nghe đang được sử dụng vẫn được bảo vệ.

### Tổng kết dùng lại tiếng đúng nội dung, đúng thứ tự

Máy chủ tìm các phần WAV đã có trong cùng tài khoản, phiên học, giọng và chế độ dự phòng. Nếu các phần phủ kín chính xác toàn bộ danh sách đoạn cần đọc, ghép chúng theo đúng thứ tự rồi kiểm tra WAV và thời lượng. Không gọi TTS lại cho bản tổng kết đó.

Không lấy một phần câu từ âm thanh chưa biết điểm cắt, không bỏ nội dung, không dùng tiếng của tài khoản/phiên/giọng khác. Nếu thiếu một phần hoặc vượt giới hạn tệp thì không ghép giả thành bản hoàn chỉnh. Kiểm tra quyền, revision và chữ đã được công bố vẫn chạy trước khi trả kết quả; đáp án tương lai không được mở khóa bởi bộ nhớ.

### Lưu tệp sẵn trong lúc học sinh đọc

Bản cũ giữ mảng byte đã tải nhưng chỉ tạo tệp khi bảng nghe mở. Hiện tại phần chuẩn bị nền tạo tệp một lần và giữ URI của tệp trong bộ nhớ riêng màn bài học. Mở/đóng/mở lại bảng nghe dùng cùng tệp; không tải hoặc ghi lại chỉ vì mở bảng.

Việc giải phóng có theo dõi người dùng tệp: đóng bảng nghe không xóa tệp còn dùng để chuẩn bị; dọn bộ nhớ không xóa tệp của trình phát đang dùng. Khi rời bài/tài khoản, các tệp không còn được sử dụng được giải phóng. Ghi tệp thất bại dọn tệp dang dở và giữ lỗi gốc.

### Bỏ một lượt kiểm tra trạng thái không cần thiết

Nếu yêu cầu bắt đầu chuẩn bị đã trả `ready`, ứng dụng tải kết quả ngay thay vì hỏi trạng thái một lượt nữa. Khi chưa sẵn sàng, vẫn theo dõi trạng thái thật và các đoạn tạo xong; không lấy thời gian chờ chia cho 45 giây làm phần trăm.

### Giới hạn 45 giây

- `NARRATION_WAIT_SECONDS = 45` trên Student.
- `PREPARATION_TIMEOUT_SECONDS = 45` cho tác vụ tạo tiếng nền trên máy chủ.
- Các lần hỏi tiến độ và khoảng nghỉ được giới hạn bởi thời gian còn lại của lượt chờ.
- Đồng hồ ở bảng nghe được giữ cho đến khi trình phát báo đã mở tệp; nhận xong byte chưa được coi là trình phát sẵn sàng. Lỗi mở tệp dừng đồng hồ đó.
- Đến hạn thì báo lỗi/thử lại, không chuyển sang chờ 150 giây. Những đoạn hợp lệ đã tạo vẫn có thể dùng cho một lượt thử lại riêng.

## Kiểm tra với hệ thống thật

### Qua API đang chạy

Đề tổng hợp vườn cây, bài 5 bước, đăng nhập tài khoản kiểm tra qua API nghiệp vụ, dùng dịch vụ sinh bài và giọng thật:

| Phép đo | Kết quả một lượt kiểm tra |
|---|---:|
| Tạo kịch bản bài học | 7.687 giây |
| Tiếng bước đầu: thời gian render ghi trong máy chủ | 2.765 giây |
| Tiếng bước tiếp: thời gian render ghi trong máy chủ | 3.187 giây |
| Kiểm tra thấy hai bước đã có tiếng sau khi tạo bài trả về | 6.141 giây |
| Mở chuẩn bị cho bước tiếp đã có tiếng | 31 ms, `ready` |
| Tải WAV bước tiếp | 32 ms, HTTP 200, 467.022 byte |
| Yêu cầu không đăng nhập | HTTP 401 |
| Revision video chưa được mở | HTTP 409 |

Video mở chủ động ở lượt này trả `RENDERING`; không ghi thành video đã sẵn sàng. Chứng cứ: [http-smoke.json](voice-fast-start-20261028/http-smoke.json). Các thời gian HTTP là tại máy phát triển, không phải số đo bấm đến tiếng phát trên điện thoại.

### Chuẩn bị toàn bộ biến thể tiếng trước khi mở

Bài phân số tổng hợp hai bước, Edge TTS và ffmpeg thật:

- Đủ 10 biến thể tiếng trước/sau bước và tổng kết cho hai giọng; hai video có tiếng hoàn tất.
- Tổng thời gian hàng đợi: **34,297 giây**, không có mục thất bại ở lượt này.
- Giọng đang ưu tiên: bước đầu sẵn ở **12,953 giây**, bước kế tiếp ở 16,687 giây, tổng kết ở 19,500 giây. Số này cho thấy tạo mới còn dao động và chưa đạt 1–3 giây trong mọi trường hợp.
- Tổng kết ghép từ kết quả từng bước; số lượt render tiếng thực sự trong kiểm thử giảm từ 10 xuống 8 để tạo 10 biến thể. Bản tổng kết không cần hai lượt render riêng cho hai giọng.
- Đã ghi nhận 18 yêu cầu đoạn tới dịch vụ trong lượt kiểm tra thật; mở bản sau bước/tổng kết không phát sinh yêu cầu nhà cung cấp thêm.
- Lấy lại tài nguyên trong bộ nhớ máy chủ khoảng 0,070–1,284 ms. Đây không phải thời gian phát của Android.

Bằng chứng: [real-fast-start-benchmark.json](voice-fast-start-20261028/real-fast-start-benchmark.json). Không dùng tỉ lệ thời gian của hai ngày khác nhau làm kết luận hiệu năng cố định, vì độ trễ nhà cung cấp đã thay đổi giữa các lượt.

### Thử cách chia đoạn khác và quyết định không áp dụng

Đã thử độ rộng 400/720 ký tự và so sánh 220/720 với văn bản tổng hợp. Các lượt thử này bị timeout ở mốc bảo vệ 25 giây; một câu ngắn kiểm tra riêng có trả tiếng sau khoảng 3,7 giây. Do chưa có kết quả tốt hơn đáng tin cậy, **không đổi sang cách chia đoạn lớn hơn**. Giữ cơ chế chia đoạn đang có và giới hạn đồng thời; không tăng hàng loạt kết nối để ép tốc độ.

Chứng cứ: [chunk-comparison.json](voice-fast-start-20261028/chunk-comparison.json), [chunk-followup.json](voice-fast-start-20261028/chunk-followup.json). Đây không phải bằng chứng quota mới hoặc dịch vụ bị chặn; chỉ là kết quả các lần đo hiện tại.

## Kiểm thử

- Python: **269 qua**, gồm ghép đúng thứ tự khung âm thanh, chặn chủ sở hữu/giọng/chữ chưa công bố, nhường bước cũ, giữ tệp khi chuyển bước, ưu tiên tiếng trước video và dừng ngân sách 45 giây bằng đồng hồ mô phỏng.
- Student: **179 qua / 17 bộ**. Kiểm tra tệp được tạo trước khi bấm, mở lại không tải/ghi thêm, không xóa tệp đang dùng, dừng chờ 45 giây, đổi giọng, nghe/ghi câu hỏi, tua và video.
- TypeScript: qua. Lint: 0 lỗi, 2 cảnh báo cũ trong `cropRotation.web.ts`.
- Export web/Android: qua. Web dùng địa chỉ HTTPS mẫu chỉ để kiểm tra build; không triển khai địa chỉ mẫu. Android là xuất bundle, không phải kiểm tra cài APK.
- Một lượt Jest chạy cùng lúc với export bị timeout 5 giây ở kiểm thử giao diện phân số. Chạy lại sau khi export xong với nguyên giới hạn kiểm thử đã qua. Không tăng timeout kiểm thử để che lỗi. Mô phỏng hệ thống tệp của kiểm thử ghi âm cũng đã được bổ sung cho hành vi chuẩn bị tệp mới.

Tổng hợp nguồn, log và dấu kiểm: [verification.json](voice-fast-start-20261028/verification.json).

## Trạng thái và điều kiện còn lại

Đã nạp dịch vụ giọng và phục vụ lại Student trên máy hiện tại. Sau khi nạp lại dịch vụ, cần bài mới vì phiên bài học lưu trong bộ nhớ. Lượt thử đầu chưa đạt như ghi ở trên; sau đó đã nạp thêm hai sửa đổi về giữ kết quả qua chuyển bước và bỏ tạo trùng giọng chưa chọn. Đã gửi yêu cầu thử vòng hai để phân biệt cùng giọng mở lại với đổi giọng; tại thời điểm cập nhật báo cáo chưa nhận kết quả vòng hai. Xác nhận “ít phải chờ hơn” ngày trước không được dùng để chứng minh mục tiêu 1–3 giây của bản này.

Mục tiêu mở tiếng đã chuẩn bị trong 1–3 giây cần được đối chiếu trên thiết bị. **Không cam kết tạo mới bằng hai giọng dịch vụ trong 1–3 giây khi nhà cung cấp chậm hoặc mất kết nối.** Tạo trước vẫn tiêu thụ lượt TTS, kể cả phần học sinh không nghe; ghép và dùng lại tệp giảm việc tạo lặp. Không thêm model sinh lời giải để thực hiện việc chuẩn bị tiếng.

Không tự chuyển sang giọng khác để lấy tốc độ. Mã hiện tại chưa có cấu hình khóa dịch vụ Azure Speech để kiểm tra một tuyến dịch vụ chính thức khác; không tự nhận đã triển khai tuyến dự phòng cùng hai giọng này. Câu hỏi tự do và phần gợi ý mới chưa có kịch bản cũng không thể bảo đảm đã chuẩn bị trước.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa khâu chờ và làm lặp bằng hàng đợi, WAV và bộ nhớ đã có, không thêm dependency hay hệ thống mới.
  - Applied to: ưu tiên hàng đợi, ghép tiếng, hạn 45 giây, vòng đời tệp và kiểm chứng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: bỏ yêu cầu nối tiếp và công việc lặp khi mở bảng nghe trên React Native.
  - Applied to: tái sử dụng tệp chuẩn bị, quản lý lease, bỏ polling thừa, thời gian mở trình phát và kiểm thử Student.
