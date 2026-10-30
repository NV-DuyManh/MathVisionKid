# Sửa lỗi bài nhiều ý và giảm thời gian chờ — 28/10/2026

## Kết quả đã đo

Bản sửa nằm tại **E:/MathVisionKid** và đã được nạp lại vào bộ dịch vụ đang chạy. Không commit/push trong vòng sửa này.

Đã thử bằng API thật, dùng dịch vụ AI đang cấu hình và đi hết từng bước, không dùng lời giải giả hoặc mock cho phép thử này:

| Bài thử | Mở đọc hiểu khi phần toán chưa xong | Chuẩn bị toán ngầm | Mở lại từ bản đã chuẩn bị | Kết quả |
|---|---:|---:|---:|---|
| Đề trong ảnh: dài 8 m, rộng bằng 1/2 chiều dài, gạch cạnh 4 dm, 2 m² giá 250 000 đồng | 8,8 ms | 9,096 giây | 15,2 ms | 200 viên; 4.000.000 đồng; COMPLETE |
| Đổi dữ kiện: dài 6 m, gạch cạnh 3 dm, 2 m² giá 180 000 đồng | 5,6 ms | 10,6 giây | 14,6 ms | 200 viên; 1.620.000 đồng; COMPLETE |

Đây là **hai phép thử API cục bộ**, không phải số đo trên điện thoại, không phải p95/SLA. Thời gian mở phần đọc hiểu không đồng nghĩa AI đã giải xong trong từng ấy thời gian. Phần toán vẫn phải chờ kiểm tra hoàn tất trước khi học sinh được làm các bước giải. Không xác nhận mọi lần tạo mới đều dưới 3 giây.

Bằng chứng: `lesson-background-reliability-20261028/floor-http.json`, `variant-http.json`, `verification.json`. Mỗi tệp ghi cả thời gian mở, thời gian tạo toán và kết quả các bước; `physicalDeviceVerified=false`.

## Nguyên nhân đã xác định

Nhật ký lúc 22:32–22:33 ghi nhận các lượt soạn bài có HTTP 200 từ nhà cung cấp nhưng bị từ chối bởi kiểm tra nội bộ. Vì vậy lỗi trong lượt này không thể quy chung là hết thời gian hoặc hết khóa.

- `250 000` bị tách thành hai số `250` và `000`; phép tính dùng đúng giá `250000` bị xem là không có trong đề.
- Hệ số đổi m² sang dm² chưa được cấp cho bộ kiểm tra, khiến phép đổi đúng nhân `100` bị chặn.
- Quy tắc phân số áp dụng cho cả bài vì có `1/2` trong đề, rồi tự thêm lời dạy quy đồng vào phép tính diện tích/tiền. Kiểm tra độc lập đã đúng khi từ chối phần dạy sai ngữ cảnh này.
- Quy tắc kiểm tra kết quả cuối chưa nói rõ trường hợp hai ý a–b với `finalAnswerStep=null`. Một số bản do model tạo còn bỏ ý b, đưa đáp án ra tiêu đề/câu hỏi hoặc tính đơn giá ngay trong phần hướng dẫn ban đầu.
- Thông báo sửa bản nháp trước đây quá chung, không chỉ ra trường và số chưa được phép; model có thể sửa không đúng chỗ trong lượt sửa giới hạn.

Trong các phép thử trung gian còn có phản hồi HTTP 429 loại token/phút và lỗi/timeout của dịch vụ dự phòng. Đây là bằng chứng hạn mức/gián đoạn thực tế, không chứng minh mọi khóa đã hết hạn. Có lượt thử bản trung gian vẫn thất bại; báo cáo không coi những lượt đó là thành công. Nhật ký và bản chụp phản hồi trung gian được giữ trong `runtime/lesson-metric-*` và `runtime/floor-lesson-*`.

## Thay đổi

1. Đọc số phân nhóm bằng dấu cách thường, khoảng trắng không ngắt dòng và khoảng trắng hẹp thành một số. Không ghép các dòng hoặc các kết quả bước riêng thành một số mới; vẫn chặn đáp án tương lai viết bằng dấu cách.
2. Chỉ cấp quy ước đổi đơn vị từ các đơn vị xuất hiện trong đề. Phân biệt hệ số độ dài, diện tích và thể tích; gửi quy ước này cùng đề cho bộ soạn và kiểm tra. Không cấp toán hạng tùy ý từ model.
3. Chọn lời hướng dẫn quy đồng dựa trên phép cộng/trừ thực sự có phần phân số trong biểu thức. Không suy từ việc toàn bài có một phân số.
4. Ràng buộc cấu trúc tiêu đề/mục tiêu không chứa chữ số; phần dạy ban đầu có ba đoạn đủ độ dài. Khi có số chưa được phép, thông báo riêng cho model nêu rõ bước/trường/đoạn cần sửa. Không đổi số thành chữ để cho qua; kiểm tra độc lập vẫn kiểm tra cả ý nghĩa lời giảng.
5. Kiểm tra đủ mọi kết quả đề yêu cầu ở bài nhiều ý. Không bỏ phần kiểm tra độc lập, không bỏ kiểm tra số học/đơn vị và không tăng timeout 45 giây.
6. Với đúng hai ý **a), b)** và hai câu hỏi tường minh đủ ngắn, mở ba bước đọc hiểu bằng cách trích nguyên văn đề. Học sinh xác định dữ kiện, câu hỏi ý a và câu hỏi ý b trong khi toán được chuẩn bị. Không đoán câu hỏi ngầm, không tự ghép nhiều bài độc lập. Bản tóm tắt giữ cả hai câu hỏi đã chọn.
7. Student gọi chuẩn bị kín ngay khi bản nhận diện hiển thị cho tài khoản đang đăng nhập, trước khi đánh dấu xác nhận. API này chỉ trả trạng thái, không trả bài học/đáp án và không giả `problemConfirmed=true`. Lệnh bắt đầu bình thường vẫn bắt buộc xác nhận đề và phần bài làm sử dụng.
8. Bản soạn đã kiểm tra chỉ được dùng lại khi **cùng tài khoản, nguyên văn đề và nguyên văn phần bài làm được chọn**. Kết quả được sao chép riêng cho từng phiên. Đổi chữ/số/bài làm hoặc tài khoản không dùng nhầm bản cũ. Các yêu cầu đang đợi dùng chung tác vụ; hủy một yêu cầu không làm hỏng tác vụ của yêu cầu còn lại.

Chuẩn bị kín được giới hạn: tối đa hai tác vụ nền đồng thời, một tác vụ nền đang chạy cho mỗi tài khoản, tối đa 16 bản trong bộ nhớ, hết hạn sau năm phút. Không gọi lại vô hạn. Bản nền thất bại không được mở thành lời giải; thao tác bắt đầu/thử lại rõ ràng có thể tạo một lượt kiểm tra mới.

Chạy ngầm **vẫn sử dụng token và hạn mức dịch vụ**. Nếu dùng đúng bản đã chuẩn bị thì không soạn lại; nếu học sinh bỏ bài hoặc sửa đề, phần chuẩn bị trước có thể đã tiêu tốn yêu cầu. Không quảng bá cơ chế này là miễn phí hoặc vô hạn.

## Kiểm chứng và trạng thái triển khai

- **499 kiểm thử Python**: bộ soạn bài, bài nhiều ý, số tiền/đơn vị, đọc hiểu, phân số, giới hạn thời gian, âm thanh, hỏi đáp và chuẩn bị kín.
- **135 kiểm thử Student / hai suite**: xác nhận nguồn, bắt đầu ngầm trước xác nhận, lỗi nền không khóa bài, API và tóm tắt hai câu hỏi.
- **146 kiểm thử Java**: 95 service + 51 controller, gồm nguồn danh tính từ xác thực, không cho người chưa đăng nhập/role giáo viên dùng API Student, phản hồi kín và lỗi an toàn.
- Tổng **780 kiểm thử liên quan** đều đạt, không cộng các lượt chạy lặp. TypeScript đạt; lint không có lỗi, còn hai cảnh báo cũ ở `cropRotation.web.ts`. Xuất bundle Android đạt. `git diff --check` đạt.
- Đã nạp lại AI và Business API từ dự án gốc. Health/readiness/Student đều HTTP 200; tài liệu API của dịch vụ đang chạy có route mới. Không dùng bằng chứng export hoặc HTTP để khẳng định đã thử trên điện thoại thật.

Tệp kiểm chứng: `lesson-background-reliability-20261028/verification.json`; log: `runtime/lesson-background-*20261028.log`. Không sửa/merge nhánh Khả, không train model, không đổi hai giọng đã chọn và không phục hồi video.

Đề thiếu dữ kiện, ảnh không rõ, bài ngoài phạm vi hoặc nhà cung cấp lỗi vẫn phải được xử lý trung thực. Không thể cam kết mọi ảnh/mọi bài/mọi lần luôn có lời giải đúng và tức thì; không cho qua lời giải chưa đạt chỉ để giấu lỗi.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân dữ kiện/kiểm tra, giữ tái sử dụng có giới hạn và kiểm chứng rõ.
  - Applied to: số tiền, đổi đơn vị, kiểm tra hướng dẫn, bộ chuẩn bị nền, API Python/Java và kiểm thử.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: tránh chờ tuần tự và quản lý yêu cầu theo tài khoản/nguồn trong React.
  - Applied to: khởi động chuẩn bị kín khi hiển thị bản nhận diện, hủy yêu cầu giao diện cũ, giữ bước xác nhận và tóm tắt nhiều câu hỏi.
