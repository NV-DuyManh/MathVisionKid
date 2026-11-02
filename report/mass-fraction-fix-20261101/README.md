# Sửa lỗi chuẩn bị bài: tấn, kg và phân số trong câu trắc nghiệm

Ngày kiểm tra: 01/11/2026. Bản sửa nằm trong checkout `E:/MathVisionKid`, đã nạp lại dịch vụ AI local. Chưa commit/push trong lượt này.

## Kết luận

Ảnh đã được đọc thành văn bản có đủ dữ kiện. Lỗi được báo nằm ở bước tạo/kiểm chứng hướng dẫn, không phải không đọc được ảnh.

Bài người dùng gửi:

> Tổng thu hoạch 2 tấn 35 kg; hạnh nhân chiếm 2/5 tổng khối lượng. Hỏi khối lượng hạnh nhân theo kg, các lựa chọn 814, 914, 1 221, 1 231 kg.

Phép tính đúng: `2 × 1000 + 35 = 2035 kg`; `2035 × 2/5 = 814 kg`. Đáp án **A**.

## Nguyên nhân và bằng chứng

Nhật ký trước sửa lúc 22:23–22:24 có nhiều lượt `requested_reading=True`, `source_chars=250` nhưng vào `mode=reviewed-plan`, sau đó bị từ chối với `Step 0: Derived literal operand`. Có cả lượt yêu cầu kiểm tra lại quan hệ của đề. Một số lần nhà cung cấp model báo `rate_limit` và chuyển sang cấu hình dự phòng; không có căn cứ kết luận mọi lần lỗi đều do hết key hoặc timeout.

Tái hiện trực tiếp với văn bản 250 ký tự trong ảnh, trước sửa:

- `unit_conversions(...)` trả danh sách rỗng, `formula_constants(...)` thiếu `1000`.
- `source_understanding(...)` từ chối tách câu hỏi; phương án tách câu có nhãn cũng không phù hợp.
- Bộ nhận diện câu hỏi trước đây chủ yếu tìm “Hỏi/Tính/Tìm…”. Bài này kết thúc bằng “Vậy, … là:” rồi có bốn đáp án A–D, nên không mở được phần đọc đề trước.
- Quy ước đổi đơn vị chỉ có chiều dài/diện tích/thể tích. Hệ số hợp lệ `1 tấn = 1000 kg` chưa được ghi nhận; bước đổi đơn vị vì thế có thể bị xem là thêm toán hạng không có căn cứ.

Các kiểm thử tái hiện phần tách đề và hệ số đổi đơn vị đã thất bại trước khi sửa, rồi qua sau sửa.

## Thay đổi

1. Tách một câu trắc nghiệm có đầy đủ A–D; giữ nguyên câu hỏi và dữ kiện gốc, không đưa đáp án nhiễu thành dữ kiện cho phần đọc đề.
2. Nhận câu hỏi tường minh “Vậy, … là:” khi đi kèm bộ lựa chọn đầy đủ. Phần đọc đề mở trước, phần toán tiếp tục chuẩn bị nền bằng cơ chế hiện có.
3. Bổ sung quy ước đổi khối lượng theo từng đơn vị xuất hiện có căn cứ trong đề; tách riêng với đơn vị chiều dài. Không hiểu tên người “Tân” thành đơn vị “tấn”.
4. Thêm bộ giải số học chính xác cho dạng giới hạn: tổng thu hoạch gồm tấn và kg, hai loại nông sản, một loại chiếm phân số tổng, hỏi đúng loại đó theo kg và có bốn lựa chọn số. Bộ giải kiểm tra toàn bộ quan hệ, đơn vị, phân số và đúng một phương án khớp kết quả trước khi dùng. Không cố định đáp số 814.
5. Bài ngoài phạm vi hoặc có mâu thuẫn tiếp tục qua luồng model và kiểm chứng hiện có. Không bỏ kiểm tra để ép mọi yêu cầu thành công; không cho phép dùng trực tiếp một tổng đã tính nhưng chưa có bước chứng minh.
6. Cập nhật dấu vân tay chính sách catalog để bản kế hoạch cũ không được tái dùng qua thay đổi bộ giải.

Không thay OCR model, không train, không sửa dependency Expo và không sửa UI trong lượt này. Đã kiểm tra tài liệu Expo v57 theo AGENTS; phiên bản dependency hiện tại được giữ nguyên.

## Luồng nền và tính đúng đắn

`startWithReading` đã có ở màn học chính. Sau sửa, bài này thực sự vào được luồng đó: trả ba câu đọc hiểu dựa trên đề gốc trước, chuẩn bị hai bước toán phía sau, không công bố đáp số tương lai khi chưa làm bài.

Endpoint mở bài tự lên lịch giọng đọc nền. Khi kế hoạch toán hoàn tất, hàng đợi giọng được cập nhật; không cần mở hộp “Nghe giảng” mới bắt đầu lịch nền. Tạo âm thanh là tác vụ tùy chọn, thất bại âm thanh không làm hỏng yêu cầu mở bài hợp lệ. Hai giọng hiện có được giữ nguyên.

Kiểm thử mô phỏng nhà cung cấp model luôn báo `rate_limit` vẫn hoàn thành bài này bằng bộ giải chính xác, không gọi model. Câu trả lời sai được giữ tại cùng bước/revision; trả lời đúng mới tiến tiếp. Phép tính dùng `Fraction`, không dùng số thực để đoán đáp án.

## Kết quả kiểm thử trong lượt này

| Kiểm tra | Kết quả |
|---|---|
| Python: các suite bài học, đọc hiểu, chuẩn bị nền, catalog, phân số, giọng và Quiz narration | **524 passed**, 16,88 s; hai cảnh báo deprecation FastAPI đã có |
| Student: tutorScreen + narrationPreparation | **78 passed**, 2 suites |
| Student: tutorApi | **80 passed**, 1 suite |
| Student TypeScript | Qua |
| `git diff --check` | Qua; cảnh báo chuyển LF/CRLF ở các file đã sửa trước đó |

Các ca mới gồm: đổi số liệu, đổi loại nông sản được hỏi, đổi vị trí đáp án đúng, phân số `(2)/(5)`, khoảng trắng Unicode trong số; từ chối thiếu dữ kiện, sai đơn vị, phân số không hợp lệ, đáp án trùng/không khớp, thêm điều kiện hoặc lẫn câu hỏi khác.

### Đo qua Business API local thực

Đăng nhập qua backend, gọi chuẩn bị đề, mở bài, chờ toán nền, trả lời cả sai và đúng tới khi hoàn tất. Không mock API ở các lượt đo sau.

| Trường hợp | Mở phần đọc đề | Toán sẵn sàng từ đầu lượt đo | Kết quả |
|---|---:|---:|---|
| Bài gốc, lần đo đầu sau nạp sửa | 88,69 ms | 1017,95 ms | 814 kg |
| Đổi thành 3 tấn 20 kg, lấy 3/4 | 45,08 ms | 162,55 ms | 2265 kg |
| Bài gốc với `(2)/(5)` | 32,69 ms | 143,59 ms | 814 kg |
| Mở lại bài gốc | 28,30 ms | 137,67 ms | 814 kg |

Đây là mẫu đo local nhỏ, bao gồm lời gọi chuẩn bị trước mở bài và polling; không phải p95/p99, không phải thời gian OCR, không phải số đo bấm trên điện thoại. Catalog/cache và trạng thái tiến trình ảnh hưởng các lượt sau.

### Giọng đọc: ghi nhận cả thành công và hạn chế

Lượt kiểm tra đầu chưa hoàn tất được phép đo cả hai giọng. Nhật ký có nhiều `NoAudioReceived`, một số đoạn được dịch vụ trả âm thanh sau retry, một số tác vụ nền thất bại. Không dùng lượt này để tuyên bố giọng luôn thành công hoặc luôn dưới ba giây.

Lượt kiểm tra lại trên lời giảng đã có trong catalog/cache:

| Giọng | Chuẩn bị/truy xuất sẵn sàng | Tải WAV | Nghe lại cùng dữ liệu | Độ dài âm thanh |
|---|---:|---:|---:|---:|
| Nam | 443,90 ms | 9,39 ms | 11,46 ms | 15,38 s |
| Nữ | 443,20 ms | 9,51 ms | 11,32 ms | 15,14 s |

Hai phản hồi là WAV có dữ liệu khung âm thanh hợp lệ, nghe lại trả cùng bytes. Không coi đây là đo tốc độ tạo mới; không coi kiểm tra bytes là bằng chứng đã nghe trên thiết bị thật. Dịch vụ giọng bên ngoài vẫn có thể trả rỗng hoặc chậm; bản sửa bài toán không thể bảo đảm dịch vụ đó không bao giờ lỗi.

## Trạng thái local và cách thử

- Đã sao lưu nhật ký trước sửa trong `.local-artifacts/mass-fraction-fix-20261101/`.
- Nạp lại đúng tiến trình AI của checkout hiện tại; giữ các dịch vụ khác và dữ liệu local. Chẩn đoán launcher báo `READY_FOR_FULL_DEMO`.
- Tải lại app, mở lại chính bài này thành phiên mới để dùng bản sửa. Phiên AI đang mở trước lần nạp lại cần mở lại.
- Chưa xác nhận bằng điện thoại vật lý trong lượt này. Không hứa mọi dạng bài, mọi điều kiện mạng đều thành công hoặc không có độ trễ.
- Giữ nguyên các thay đổi chưa commit từ những lượt trước; không động vào `demoUI`, không commit/push.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân tại các hàm dùng chung, dùng số học và regex có giới hạn, không thêm dịch vụ hay dependency.
  - Applied to: tách nguồn trắc nghiệm, quy ước khối lượng, bộ giải chính xác, kiểm thử hồi quy.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: rà soát đường mở bài và chuẩn bị nền từ React Native, tránh tạo chuỗi chờ model rồi mới chuẩn bị giọng.
  - Applied to: kiểm tra `math-guide.tsx`, TutorService, luồng narration; giữ nguyên cơ chế client đã có, xác minh bằng kiểm thử Student và TypeScript.
