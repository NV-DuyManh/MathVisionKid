# Giọng đọc: sửa phần tạo ngầm và kiểm tra đường dịch vụ — 28/10/2026

## Kết luận

Đã sửa thêm hai nguyên nhân làm mất hiệu quả tạo ngầm: thiếu kịch bản nhận xét sau bước “Hiểu đề”, và bộ đếm lỗi cộng dồn khiến hai lỗi rời rạc có thể dừng phần chuẩn bị của cả giọng. Đã bổ sung đường Azure Speech chính thức dùng cùng hai mã giọng. Bản sửa đã được nạp vào máy chủ cục bộ; `/health` và `/ready` đều trả 200.

**Chưa đạt điều kiện nghiệm thu “mọi lượt đều sẵn sàng trong 1–3 giây”.** Đường Edge trực tiếp vẫn có lượt mất kết nối hoặc hết thời gian; đây không chỉ là trạng thái hiển thị trong app. Azure chưa được bật do chưa tìm thấy cấu hình tài nguyên/khóa trên máy. Không có phép thử Azure thật hoặc phép đo Android thật mới trong vòng này.

## Thay đổi đã làm

### 1. Chuẩn bị nhận xét của bước Hiểu đề

`ai/runtime/app/tutoring/media_preparation.py` trước đây bỏ qua nhận xét sau các bước `UNDERSTAND`, trong khi màn hình học vẫn dùng lời đọc của nhận xét đó. Vì thế phần này không thể có âm thanh từ giai đoạn dựng kịch bản trước câu trả lời.

Hiện phần dựng trước bao gồm cả nhận xét của các bước Hiểu đề cho Nam Minh và Hoài My. Bản tổng kết cuối vẫn chỉ gom các bước toán. Âm thanh dự kiến được giữ riêng: trước khi học sinh trả lời đúng, đọc công khai nội dung nhận xét vẫn bị từ chối; người dùng khác cũng không được lấy. Sau câu trả lời đúng, kiểm thử đối chiếu đúng lời nhận xét thực tế và lấy âm thanh đã lưu mà không tạo lại.

### 2. Lỗi gián đoạn không cộng dồn thành dừng cả bài

Trước đây bộ đếm lỗi của mỗi giọng chỉ tăng suốt bài. Chuỗi lỗi → thành công → lỗi vẫn đủ để dừng các tác vụ còn lại của giọng đó.

Hiện một lần tạo thành công xóa chuỗi lỗi liên tiếp của riêng giọng tương ứng. Tổng lỗi vẫn được thống kê. Hai lỗi **liên tiếp** vẫn dừng phần thử ngầm còn lại để không gọi dịch vụ liên tục trong sự cố. Đây là giới hạn chủ động: không có cơ chế tự thử vô hạn hoặc cam kết mọi bài sẽ luôn tạo ngầm đủ khi dịch vụ mất kết nối; yêu cầu nghe chủ động vẫn giữ đường thử riêng.

### 3. Đường chính thức giữ nguyên giọng

Đã thêm `ai/runtime/app/tutoring/azure_speech.py`, tích hợp vào `synthesize_neural` chung cho lời giảng và lời trả lời bằng giọng. Các thành phần tạo ngầm, cache, kiểm tra quyền, phát lại và tua tiếp tục dùng WAV như trước.

- Chỉ nhận `vi-VN-NamMinhNeural` và `vi-VN-HoaiMyNeural`.
- Chuyển phép toán thành lời đọc trước khi gửi; giới hạn SSML tính sau khi chuyển và escape XML.
- Dùng `httpx` đã cài; không thêm SDK/phụ thuộc mới.
- Nhận PCM 16 kHz / 16-bit / mono và bọc WAV bằng thư viện chuẩn; không dùng checkpoint MP3 hoặc ffmpeg của đường Edge.
- Giữ deadline tổng bên gọi, giới hạn một lượt tổng hợp tối đa 25 giây và thời hạn chuẩn bị công khai tối đa 45 giây; không đổi thành 150 giây.
- Hủy tác vụ đang chạy được truyền xuống kết nối. Không trả dữ liệu dở dang, rỗng, im lặng, quá kích thước hoặc sai định dạng đã kiểm tra.
- Khóa ở phía máy chủ; hostname HTTPS cố định theo region hợp lệ; không theo redirect, không ghi khóa, nội dung học sinh hay thông báo lỗi thô.
- Phân loại lỗi cấu hình, xác thực, hạn mức, mạng, timeout và dữ liệu âm thanh; không tự xoay khóa, không tự đổi giọng.

Microsoft liệt kê đúng hai mã giọng này trong [danh sách hỗ trợ](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=text-to-speech). Định dạng, xác thực và endpoint theo [REST reference](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech). Cùng mã giọng chưa chứng minh dạng sóng giống tuyệt đối hoặc độ trễ tốt hơn: cần kiểm tra bằng tài nguyên thật.

### 4. Đo thời gian ở từng lần thử Edge

Đã thêm nhật ký thời điểm nhận byte âm thanh đầu tiên, tổng thời gian, số byte, số lần thử và loại kết quả. Không ghi văn bản học sinh, URL, token hoặc nội dung exception. Nhận được một phần audio chưa được xem là hoàn tất.

## Kết quả gọi dịch vụ thật

Các phép thử dùng câu công khai tự tạo, không dùng bài học sinh và không lặp lại tới khi có kết quả đẹp. Các nhóm có giới hạn thời gian khác nhau, **không thể lấy tổng số thành công làm tỷ lệ khả dụng đại diện**.

| Phép thử | Nam Minh | Hoài My |
|---|---|---|
| Câu chào ngắn, một lượt/giọng, tối đa 12 giây | Hoàn tất 742 ms, 11.520 byte MP3 | Hoàn tất 586 ms, 11.232 byte MP3 |
| Đoạn 189 ký tự, một lượt/giọng, tối đa 12 giây | Không có audio; đóng bất thường, 3.121 ms | Có dữ liệu âm thanh nhưng chưa hoàn tất trước timeout, 12.014 ms |
| Câu 34 ký tự, tối đa 8 giây | Không có audio, 2.832 ms | Hoàn tất 4.834 ms |
| Câu 68 ký tự, tối đa 8 giây | Nhận byte đầu sau 7.479 ms; hết thời gian 8.009 ms trước khi hoàn tất | Không có audio, 2.715 ms |
| Câu 96 ký tự, tối đa 8 giây | Không có audio, 2.932 ms | Không có audio, 3.509 ms |

Hai lượt đoạn dài đã bắt tay WebSocket thành công. Dữ kiện cho thấy lỗi nằm trên đường tổng hợp/kết nối trực tiếp, nhưng **chưa xác định nguyên nhân phía nhà cung cấp hoặc mạng**, không chứng minh hết quota, bị khóa IP hay dịch vụ đã ngừng. Thư viện cài là `edge-tts==7.3.1`, nguyên vẹn theo checksum và là bản được PyPI công bố mới nhất khi kiểm tra. Không tự sửa header, giả danh phiên bản khác hoặc đổi dependency khi chưa có bằng chứng.

Chỉ 1/6 lượt của nhóm so sánh độ dài hoàn tất, nên không đổi sang chia câu 34 ký tự: chưa chứng minh ổn định hơn và sẽ tăng số yêu cầu. Timeout thử riêng 8/12 giây không phải thời hạn 45 giây trong ứng dụng.

Dữ liệu gốc:

- `report/voice-provider-recovery-20261028/protocol-probe.json`
- `report/voice-provider-recovery-20261028/paragraph-protocol-probe.json`
- `report/voice-provider-recovery-20261028/size-probe.json`

## Cấu hình thực tế

Sau yêu cầu tự cấu hình của chủ dự án, đã kiểm tra công cụ kết nối có sẵn, tên biến cấu hình trong dự án và cấu hình đăng nhập Azure cục bộ. Không có connector Azure được cung cấp, không có Azure CLI/thư mục hồ sơ Azure, không tìm thấy tên biến khóa/tài nguyên Azure Speech trong các cấu hình đã kiểm tra. Điều này không khẳng định chủ dự án không có tài khoản ở nơi khác.

Đã đặt rõ `SPEECH_PROVIDER=edge` trong `ai/runtime/.env.local` được Git bỏ qua và giữ các thông tin bí mật khác. Azure adapter mặc định không chạy; không có yêu cầu Azure trả phí được tạo trong vòng này. Không thể tự sinh khóa hợp lệ khi chưa có tài nguyên và thông tin xác thực. Hướng dẫn cấu hình đầy đủ nằm trong `ai/runtime/README.md`; mẫu biến nằm trong `.env.example`.

Khi có tài nguyên Speech, máy chủ cần `SPEECH_PROVIDER=azure`, `AZURE_SPEECH_REGION` và `AZURE_SPEECH_KEY` rồi khởi động lại. Tác vụ tạo ngầm cũng sẽ dùng đường đó. Cần đo lại audio thật, độ trễ và chi phí trước khi kết luận có thể thay đường hiện tại.

## Hạn mức, token và tạo ngầm

Đọc kịch bản bài học đã tạo không thêm prompt mô hình ngôn ngữ. Tuy nhiên, tạo ngầm **vẫn gửi yêu cầu tổng hợp giọng thật**, có thể tiêu thụ số lượt/ký tự và chi phí của dịch vụ. Chuẩn bị hai giọng và nhiều biến thể nhận xét tăng lượng sử dụng; phát lại dữ liệu đã lưu không cần gọi tổng hợp mới. Giới hạn 72.000 ký tự trong hàng đợi là ngân sách nội bộ của văn bản nguồn, không phải hạn mức miễn phí và không đồng nhất với đơn vị tính phí sau chuyển phép toán/SSML.

Azure có mô hình tính phí dịch vụ; không được xem là dùng vô hạn. Xem [giá chính thức](https://azure.microsoft.com/en-us/pricing/details/speech/). Edge qua thư viện cộng đồng không cung cấp cho dự án một quota/SLA được bảo đảm trong các tài liệu đã kiểm tra. Không thể hứa chất lượng dịch vụ ngoài ứng dụng bằng bộ đếm phần trăm hoặc cache.

## Kiểm thử và phạm vi xác minh

Lệnh kiểm thử mới nhất chạy 10 tệp Python liên quan giọng, video, bài học, nguồn đề và quyền truy cập: **336 passed**, 5,38 giây. Trong số này có 36 kiểm thử Azure giả lập, 18 kiểm thử neural speech/tích hợp và 24 kiểm thử chuẩn bị media. Các số này nằm trong tổng 336, không cộng thêm lần nữa.

Những tình huống mới được kiểm tra gồm: đúng hai giọng; escape XML; giới hạn sau chuyển toán; cấu hình thiếu không gọi mạng; 401/403/429; không theo redirect; audio sai/rỗng/im lặng/quá lớn/dở dang; hủy kết nối; deadline gốc; không trộn PCM với MP3; log không chứa nội dung riêng; nhận xét Hiểu đề riêng tư trước câu trả lời; hit cache sau câu trả lời; lỗi–thành công–lỗi không làm mất cả hàng đợi; cả hai giọng cùng lỗi vẫn dừng sau tối đa bốn lượt render nền.

Nhật ký: `runtime/voice-provider-recovery-python-20261028.log`. `git diff --check` qua (có cảnh báo chuyển LF/CRLF sẵn có). Máy chủ đã nạp bản sửa và trả 200 cho cả health/ready. Không chỉnh UI/Java trong vòng này nên không xuất lại bundle hay cộng kết quả cũ vào số kiểm thử mới. Không commit/push, không train model. Không có bằng chứng Android vật lý mới; chủ dự án đã hẹn thử sau.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa lỗi chung của pipeline giọng và bổ sung đường thay thế tối thiểu theo yêu cầu có sẵn.
  - Applied to: bộ đếm lỗi, kịch bản tạo trước, dùng httpx/stdlib hiện có, giới hạn transport và kiểm thử lỗi thực tế.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: đối chiếu đường chuẩn bị dữ liệu React với lời giảng và nhận xét ở máy chủ.
  - Applied to: rà soát `NarrationPreparation`, `narrationCache`, và hợp đồng `completedNarration` để tìm biến thể thiếu; không sửa React trong vòng này.
