# Sửa luồng bài mới, gợi ý, hai giọng và nhận xét bài làm

Ngày hoàn tất kiểm tra: 31/10/2026. Thay đổi đã nằm trong mã nguồn app local đang chạy. Chưa commit hoặc push trong lượt này.

## 1. Bài mới lỗi ở lượt đầu

Đã tái hiện lỗi tạo hướng dẫn cho bài căn phòng dài 45/4 m, rộng 6 m, gạch cạnh 30 cm. Một nguyên nhân cụ thể là bộ sinh trả chỉ số bước kết luận theo cách đếm từ một, còn bộ kiểm tra đếm từ không. Một số bản sinh còn đặt phần giải có kết quả vào phần hướng dẫn ban đầu. Đây là lỗi cấu trúc của bản hướng dẫn; không phải bằng chứng rằng OCR sai hoặc mọi lỗi đều do hết khóa.

Đã sửa chỉ số riêng tư trong trường hợp xác định được chính xác bước cuối; các chỉ số sai khác vẫn bị từ chối. Phần giải đặt nhầm được chuyển về phần riêng tư, chỉ khi còn đủ hướng dẫn ban đầu không tiết lộ đáp án. Sau đó vẫn phải qua kiểm tra toán và kiểm tra độc lập. Không bỏ bộ kiểm tra để làm cho yêu cầu trông như thành công.

Luồng thử lại cũng phân biệt đọc ảnh và tạo bài học; ảnh/nội dung vẫn được giữ, không yêu cầu tải lại toàn bộ app để gọi lại đúng nhiệm vụ.

## 2. Gợi ý và đáp án đã chọn

Trước đây, một dấu phân số trong phép chia có thể kích hoạt câu hỏi cố định về tử số. Hiện gợi ý xét cả nội dung đang giải thích, câu hỏi, tiêu đề bước và đơn vị: đổi diện tích, tính diện tích hình chữ nhật, số viên gạch, rút gọn thương… có câu kiểm tra phù hợp. Không đủ ngữ cảnh thì cho quay lại thử làm, không tự đặt một câu hỏi chung thiếu liên quan.

Đáp án chọn sai được giữ, có biểu tượng và nhãn chưa đúng, cho chọn lại. Chọn đúng giữ nguyên các lựa chọn, đánh dấu đúng và chờ học sinh chủ động tiếp tục. Không chỉ dùng màu để phân biệt.

## 3. Phát âm

Chuẩn hóa văn bản trước khi tạo tiếng, không sửa dữ kiện gốc: ngoặc trong lời văn trở thành ngắt nghỉ; tên đơn vị có gạch nối được đọc thành tên đơn vị tự nhiên. Xử lý cả các dấu gạch Unicode thường gặp trong OCR. Phép trừ thật và nhóm phép tính vẫn được giữ nghĩa.

Đã đổi phiên bản bộ nhớ đệm âm thanh để không dùng lại tệp phát âm theo quy tắc cũ. Hai giọng Nam Minh/Hoài My bên trong vẫn giữ nguyên; giao diện chỉ ghi Giọng nam/Giọng nữ. Thời gian chờ tối đa vẫn 60 giây.

## 4. Hai giọng chạy ngầm

Trước đây, hàng đợi toàn bài chỉ có một worker, có thể làm bước tiếp theo của giọng chính trước giọng còn lại của bước hiện tại; đổi giọng còn có thể hủy phần đang chuẩn bị. Hiện có hai worker có giới hạn, chuẩn bị cặp giọng của cùng kịch bản trước khi chuyển sang kịch bản tiếp theo. Giữ tác vụ giọng còn lại khi đổi lựa chọn; ưu tiên yêu cầu nghe trực tiếp trước phần chuẩn bị chưa cần tới. Hai worker dùng chung giới hạn render và ngân sách ký tự, không tăng song song vô hạn.

Giọng đã chọn vẫn được lưu và dùng ở các bước sau. Chuẩn bị thêm cả hai giọng cho câu trả lời giải thích phát sinh. Không tự phát tiếng khi chuẩn bị và không tái tạo video.

**Bằng chứng dịch vụ thật trước khi bấm nghe:** một bài mới trả HTTP 200 sau 8,505 giây; cả hai giọng tự chuyển sang sẵn sàng sau 23,8 giây. Lấy tệp đã chuẩn bị: nam 40,19 ms, nữ 49,24 ms. Đây là thời gian HTTP trên máy chủ local, không phải thời gian bấm đến lúc loa điện thoại phát. Tệp có âm thanh dài lần lượt 28,61 và 27,62 giây; con số này không phải thời gian tạo.

Chạy đồng thời không bảo đảm hai nhà cung cấp trả kết quả cùng một mili giây. Nếu học sinh bấm trước khi giọng tương ứng xong, vẫn có thể phải chờ. Không có bằng chứng để hứa mọi lần tạo lạnh đạt 1–3 giây.

## 5. Bài học sinh đã làm

Tách thành hai phần rõ ràng:

1. **Đọc nội dung ảnh:** xem đề hoặc bài đã viết, sửa chữ/số nếu đọc nhầm, một nút xác nhận nội dung để xem nhận xét. Dấu chưa đọc rõ phải được xử lý trước khi chấm. Đây là xác nhận bản đọc ảnh, không phải bài tập tóm tắt hay học lại đề.
2. **Nhận xét:** bắt đầu sau xác nhận. Bài đúng hiện lời khen và nút hoàn tất; chi tiết và câu tương tự là tùy chọn. Bài có lỗi tập trung vào dòng cần sửa, gợi ý và nhập lại một dòng hoặc chụp bài đã sửa. Quay về xem nguồn không tự gọi chấm lại.

Chỉ đánh dấu trên ảnh khi có vị trí OCR gắn đúng dòng nguồn đã xác nhận. Không có vị trí tin cậy thì chỉ rõ bằng nội dung dòng, không dựng khung hay khoanh tròn đoán mò. Sửa bản chữ làm mất hiệu lực vị trí của ảnh cũ, tránh đánh dấu nhầm sau khi sửa.

Đã tách phán quyết toán khỏi lời nhận xét trình bày: khi hai lần kiểm tra nguồn độc lập đồng ý hoàn toàn nhưng câu nhận xét chứa con số/đáp án không được phép, thay phần trình bày bằng mẫu an toàn, không gọi thêm lần thứ ba. Không thay phán quyết, số liệu, nguồn hay trạng thái từng dòng; bất đồng, lời chứa chỉ dẫn kỹ thuật, thiếu bằng chứng hoặc sai toán vẫn không được nâng thành đúng.

Khi dịch vụ nhận xét lỗi, kiểm tra cục bộ có thể chỉ ra một đẳng thức chắc chắn sai. Các dòng khác giữ trạng thái chưa đủ bằng chứng, không tự nhận là đúng.

**Lượt kiểm tra qua app local sau bản sửa cuối:** bài vườn cây đúng được nhận xét CORRECT, HTTP 200, 6,219 giây. Đổi riêng dòng `135 × 1/6 = 45 m²`: HTTP 200, 7,125 giây, NEEDS_REVISION, đánh dấu đúng dòng đó; các dòng chưa được kiểm chứng đầy đủ giữ UNSURE. Không có sửa đáp số âm thầm trong bài học sinh.

## Kiểm thử và giới hạn bằng chứng

- Student: **110 bộ / 1.263 kiểm thử qua**, 45,134 giây. Có kiểm thử đáp án giữ nguyên, ngữ cảnh gợi ý, xác nhận bản đọc ảnh, chấm một lần trong Strict Mode, quay về nguồn không chấm lại và vô hiệu hóa đánh dấu cũ sau sửa.
- AI: **486 kiểm thử qua**, 7,08 giây; hai cảnh báo deprecation FastAPI đã có. Phạm vi gồm bài mới, kiểm tra độc lập, phân số, catalog, bài viết, chuẩn bị cặp giọng, phát âm và quyền truy cập âm thanh.
- TypeScript noEmit qua; export web 40 route và Android qua. Export Android không chứng minh hoạt động trên thiết bị thật.
- `git diff --check` cho phần sửa qua; có thông báo đổi LF/CRLF, không có lỗi whitespace.
- Nhật ký thực tế có Groq 429, Gemini 503 và một số 403 ở các lượt chẩn đoán. Có lượt nhận xét trước bản sửa bị hạ xuống chưa đủ bằng chứng. Không coi các lỗi này là đã hết chỉ vì lượt cuối qua. Không thêm khóa, không quét khóa, không đổi model hoặc huấn luyện.
- Chưa xác minh bằng thao tác Android thật trong lượt này. Không có ảnh chụp UI mới vì điều khiển trình duyệt bị tắt trong phiên làm việc; kiểm thử component và export không thay thế kiểm tra hình ảnh trên máy người dùng.

Để thử bản local: tải lại app và mở một bài mới, vì máy chủ đã được khởi động lại trong quá trình kiểm tra. Thử đổi giọng sau khi đọc bước đầu; với bài đã viết, xác nhận bản đọc rồi xem nhận xét, không đi lại cả bài học.

Bằng chứng nhỏ kèm theo: [dịch vụ và cặp giọng](live-smoke.json), [nhận xét đúng/sai sau bản sửa cuối](review-smoke.json), [hai bài tạo mới bổ sung](fresh-lesson-results.json).

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: sửa tương tác và bố cục Student trên điện thoại.
  - Applied to: trạng thái đáp án, bước xác nhận nội dung ảnh và nhận xét bài viết.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native, vòng đời effect và tránh công việc lặp.
  - Applied to: giữ trạng thái nhận xét, khởi chạy một lần, bộ nhớ đệm và chuẩn bị giọng.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa đúng nguyên nhân với thay đổi có giới hạn.
  - Applied to: phục hồi metadata, kiểm tra phép tính cục bộ, hai worker có ngân sách chung và không thêm lần gọi AI cho lời trình bày.
