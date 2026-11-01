# Sáu cải tiến Student — 29/10/2026

Đã sửa trực tiếp dự án đang chạy tại `E:/MathVisionKid`, nhánh `codex/student-learning-voice-polish-20261029`. Không commit, push, huấn luyện mô hình hoặc thêm thư viện trong vòng này. Các thay đổi chưa commit từ những vòng trước và công việc OCR khác được giữ nguyên.

## Kết quả theo từng yêu cầu

| Phần | Đã triển khai | Giới hạn thực tế |
|---|---|---|
| Đo hiệu năng | Ghi thời gian chuẩn bị, tải WAV và mở bộ phát; tách cache sẵn/đang chạy/lượt mới, foreground/background, nền tảng; đếm lỗi/hủy và p50/p95. Web có LCP, CLS và thời lượng tương tác lớn nhất. | Thời gian `prepare` là toàn bộ lượt lấy âm thanh sẵn sàng, gồm chờ/tải; không phải thời gian riêng nhà cung cấp. Thời lượng tương tác lớn nhất không được gọi là INP. Chưa có dữ liệu sản xuất trên số lượng lớn thiết bị. |
| Đọc đồng bộ | WAV mới chứa mốc từng đoạn dựa vào số frame PCM đã giải mã thật. Đoạn đang phát được tô sáng; bấm đoạn để nghe lại từ đúng mốc. | Đây là đồng bộ theo **đoạn**, không phải tô từng từ. Tệp cũ thiếu mốc và giọng thiết bị vẫn hiển thị lời giảng thông thường; không đoán thời gian bằng độ dài chữ. |
| Kiểm tra hiểu | Sau mỗi hai bước tính đúng, có câu thử nhỏ tùy chọn: đổi một số trong phép tính vừa học và chấm bằng phân số chính xác trên máy chủ. Giữ câu trả lời sai để sửa. | Là luyện chuyển cách tính sang số khác, chưa đủ để kết luận học sinh hiểu toàn bộ khái niệm. Không thay dữ kiện/đáp số đề gốc, không tự chuyển bước học. |
| Học tiếp | Lưu bước, câu trả lời đang nhập, câu hỏi đang gõ, giọng và vị trí nghe. Trang chủ có thẻ mở lại bài gần nhất. Tải lại ở màn đáp án đúng vẫn giữ màn xem lại cho đến khi bấm Tiếp tục. | Máy chủ xác nhận lại chủ sở hữu và trạng thái; không tin đáp án lưu ở trình duyệt. Phiên máy chủ hiện có TTL một giờ và nằm trong bộ nhớ; hết hạn/khởi động lại máy chủ thì giữ văn bản để bắt đầu lại, không khôi phục giả tiến độ. |
| Bộ hồi quy | 20 bài cố định, phép tính kiểm chứng bằng số hữu tỉ; công cụ nhận kết quả OCR/đáp án để chấm CER và đáp án. Có bài vườn cây, lát nền, trồng hoa và phòng học trong ví dụ người dùng. | 20/20 là kiểm tra **đáp án chuẩn của bộ dữ liệu**, không phải độ chính xác OCR/model. Chưa cấp dự đoán nên điểm OCR/model để `null`. Chưa xác minh độc lập với toàn bộ dữ liệu huấn luyện trước đây, không gọi đây là tập holdout nghiên cứu độc lập. |
| UI và khả năng sử dụng | Giữ thiết kế hiện có; thêm bài gần nhất, thẻ thử nhanh, lời giảng tương tác; gọn thẻ tiện ích ở màn hẹp, đổi sang hàng khi chữ hệ thống lớn; có chỉ báo focus bàn phím cho thành phần mới. | Kiểm tra trực quan và thao tác trên web. Xuất Android thành công không thay thế thử trên điện thoại thật. |

## Giọng nói: số đo thật và điều chưa đạt

Đo qua dịch vụ HTTP đang chạy và nhà cung cấp thực tế, cùng kịch bản 113 ký tự/hai đoạn. Mỗi giọng đo một lượt, không đủ để suy ra p95 của dịch vụ. Tệp trả về có hai mốc đoạn hợp lệ và lần đọc lại trùng nội dung âm thanh.

| Giọng | Từ gửi chuẩn bị đến sẵn sàng | Toàn lượt đến nhận tệp | Đọc lại tệp đã lưu trên máy chủ |
|---|---:|---:|---:|
| Nam | 19.774 ms | 19.803 ms | 13 ms |
| Nữ | 6.000 ms | 6.043 ms | 17 ms |

Nguồn: [live-probe.json](live-probe.json), [mẫu nam](male.wav), [mẫu nữ](female.wav). Đây **không phải** thời gian bấm-phát trên Android và không phải đánh giá nghe bằng người. Hai giọng vẫn giữ đúng âm sắc hiện tại; UI chỉ ghi Giọng nam/Giọng nữ. Không tự đổi sang giọng khác khi có lỗi.

Chuẩn bị nền và dùng chung công việc/tệp đã lưu vẫn hoạt động như trước. Bổ sung mốc đoạn không tạo cuộc gọi mô hình ngôn ngữ mới, nhưng việc tổng hợp theo đoạn có thể tăng số lượt gọi TTS so với ghép toàn văn bản; số ký tự tương ứng vẫn phải được xử lý bởi dịch vụ. Không thể coi chuẩn bị nền là miễn hạn mức. Giữ giới hạn chờ tạo giọng **60 giây**, bộ phát có giới hạn mở tệp riêng 12 giây.

**Chưa đạt cam kết 1–3 giây cho mọi nội dung mới.** Khi tệp đã chuẩn bị xong, có thể lấy lại nhanh; khi dịch vụ bên ngoài chậm hoặc mất kết nối, vẫn cần chờ/thử lại. Các lỗi tiếp tục dùng UI gọn với Thử lại và Giọng thiết bị, không tự hạ chất lượng âm sắc.

Kiểm tra cấu hình thực tế hiện dùng Edge; Azure Speech chưa có khóa/vùng trên máy này. Đường Azure có sẵn trong code nhưng chưa hoạt động để kiểm chứng. Không tự đăng ký tài khoản, mua tài nguyên hay bịa thông tin cấu hình. Xem [provider-readiness.json](provider-readiness.json). Hạn mức dịch vụ chính thức phụ thuộc tài nguyên/gói: [tài liệu Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits). Không có bằng chứng để hứa sử dụng vô hạn.

## Lưu dữ liệu và quyền truy cập

- Tiến độ lưu cục bộ theo tài khoản, một bài gần nhất, chỉ dùng để khôi phục trong bảy ngày; vị trí nghe chỉ dùng 20 nội dung gần nhất trong 24 giờ. Dữ liệu quá hạn không được dùng để khôi phục; bản lưu cũ được thay thế khi có lượt lưu mới, không có cam kết xóa vật lý đúng thời điểm hết hạn. Giọng đã chọn tiếp tục dùng cơ chế lưu hiện có.
- Lưu văn bản đề/bài làm/câu hỏi/đáp án; **không** lưu ảnh hoặc bản ghi giọng nói qua lần khởi động lại trong tính năng mới này. Không tuyên bố phục hồi được bản ghi chưa gửi.
- Thống kê giọng giữ tối đa 200 mẫu/bảy ngày, chỉ chứa số đo và loại giọng/nền tảng; không chứa nội dung học sinh, âm thanh, token, URL hay mã phiên. Bỏ trường lạ khi đọc dữ liệu cũ. Thống kê web chỉ giữ bản số đo mới nhất.
- Không gửi thống kê đến hệ thống theo dõi bên ngoài. Nếu bộ nhớ trình duyệt đầy/bị chặn, không làm bộ phát sập; việc lưu/khôi phục có thể không thực hiện được.
- Resume/checkpoint công khai đi qua Spring, lấy chủ sở hữu từ phiên đăng nhập; đường nội bộ yêu cầu khóa nội bộ. Không mở thêm quyền Teacher/khách cho Student.

## Kiểm chứng đã chạy

- **Student: 97 bộ / 1.150 kiểm thử đạt**, gồm kiểm thử mới cho việc gắn/tháo bộ đo vào đúng bố cục web. [Kết quả toàn bộ](student-tests.json).
- **Python: 134 kiểm thử đạt**, gồm lời giảng, chuẩn bị âm thanh, đơn vị, mốc WAV, resume, checkpoint và bộ hồi quy. [JUnit](python-tests.xml).
- **Java: 401 kiểm thử, 0 lỗi/thất bại; bootJar thành công.** Bao gồm ba kiểm tra RBAC mới cho resume/checkpoint. Kết quả gốc trong `backend/business-api/build/test-results/test/`.
- TypeScript đạt. Lint: 0 lỗi, hai cảnh báo có sẵn tại `cropRotation.web.ts`. Không sửa lan sang phần cắt ảnh vì không thuộc vấn đề mới này.
- Xuất Android và web thành công: [metadata Android](android-export/metadata.json), [kiểm tra chạy web sau xuất](final-smoke.json). Payload bản dựng được dọn theo yêu cầu đồng bộ cuối, có thể tạo lại từ code. Cấu hình URL giả dùng riêng lúc kiểm tra đóng gói, không sửa cấu hình chạy hiện tại. Không có bằng chứng điện thoại thật trong vòng này.
- HTTP thật với phiên Student/Teacher: resume 39 ms, phục hồi màn xem lại đúng; khách 401, Teacher 403, nguồn đề bị thay đổi 400; `no-store`, không lộ khóa đáp án bước tiếp. [backend-flow.json](backend-flow.json).
- UI thật ở 320×844, 390×844, 768×1024, 1440×900 và 844×390; dữ liệu lesson/resume/checkpoint được kiểm soát để tái hiện ổn định, âm thanh dùng WAV tạo thật ở trên. Bấm đoạn phát được; tải lại ngay sau gõ vẫn giữ câu hỏi; giữ giọng/vị trí nghe và không tự phát khi khôi phục; giữ đáp án đúng; câu thử sai rồi đúng không đổi bước gốc; không tràn ngang. [visual-qa.json](visual-qa.json).
- Kiểm tra focus bàn phím trên lời giảng và thẻ học tiếp; đối chiếu ảnh thực tế, sửa một lỗi trùng React key có thể làm mất trạng thái câu thử nhanh. Không ghi nhận lỗi console/page trong lượt QA cuối.
- Kiểm tra định dạng `git diff --check` đạt. Các file OCR ở `scripts/data/` không được sửa trong vòng này.

Trong quá trình xuất Android, cache phát triển web có lúc dùng nhầm bảng module và lỗi render; đã khởi động lại đúng dịch vụ của dự án rồi kiểm tra UI lại. Đây là kiểm tra môi trường phát triển, không phải kết luận lỗi ứng dụng trên điện thoại.

Kiểm tra web thật cuối vòng còn phát hiện bộ đo ban đầu được gắn ở bố cục chung trong khi web dùng bố cục riêng. Đã chuyển bộ đo sang `_layout.web.tsx`, thêm kiểm thử gắn/tháo bộ đo và xác nhận số đo được lưu trong trang thật. Xem [final-smoke.json](final-smoke.json).

## Phần nên làm tiếp khi có dữ liệu thực tế

1. Thu thập đủ các mẫu giọng trên điện thoại/mạng thật bằng bộ đo mới để tìm p50/p95 và tỷ lệ lỗi; chưa thể dùng vài lượt localhost để kết luận đạt toàn bộ mục tiêu.
2. Nếu cần bảo đảm vận hành lâu dài cho đúng hai giọng, cấu hình tài nguyên Speech chính thức bằng tài khoản của chủ dự án rồi đo/kiểm thử thực tế; hiện chưa có thông tin để kích hoạt tài nguyên đó.
3. Nếu cần tiếp tục bài sau khi máy chủ khởi động lại, chuyển lưu phiên học sang kho bền vững; hiện chưa thay kiến trúc phiên đang có.
4. Cấp dự đoán OCR/model thực tế cho bộ hồi quy và xây tập ảnh có nguồn gốc/nhãn xác minh riêng trước khi công bố chỉ số nghiên cứu.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: UI học tập trên điện thoại, tablet và desktop.
  - Applied to: thẻ học tiếp, thử nhanh, transcript đồng bộ, bố trí thẻ màn hẹp/chữ lớn.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native, vòng đời yêu cầu và trạng thái phát.
  - Applied to: khôi phục có kiểm chứng, hủy phản hồi muộn, callback bộ phát, key riêng cho các thành phần cùng cấp.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: thêm nút/ô nhập và lời giảng có thể tương tác.
  - Applied to: nhãn, trạng thái chọn, thông báo kiểm tra, focus bàn phím, thao tác không bắt buộc kéo thanh tua.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: giữ giải pháp ít phụ thuộc, tránh thêm hạ tầng không cần thiết.
  - Applied to: cue chuẩn WAV, số hữu tỉ của Python, kho cục bộ có sẵn, endpoint trong luồng auth hiện tại; không thêm thư viện/video/training.
