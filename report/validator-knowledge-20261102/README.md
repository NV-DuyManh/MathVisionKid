# Giảm từ chối nhầm bằng kiến thức có căn cứ

Thực hiện đêm 01/11 → 02/11/2026, checkout `E:/MathVisionKid`. Bản cuối đã nạp vào dịch vụ AI local. Chưa commit/push.

## Đã triển khai

Đây là bổ sung kiến thức và kiểm tra hồi quy tại runtime, **không phải đã huấn luyện trọng số Groq/Gemini**. Không train OCR, không dùng câu trả lời của model làm nhãn đúng tự động và không bỏ bộ kiểm chứng.

### Kho quy ước dùng chung

`ai/runtime/app/tutoring/math_knowledge.py` thay thế phần đơn vị/hằng số rải trong `lesson.py`:

- 39 đơn vị chuẩn hóa: 7 độ dài, 8 diện tích, 11 thể tích/dung tích, 8 khối lượng và 5 thời gian.
- Đổi trực tiếp và đổi ngược bằng phép chia trên hệ số chính xác; dùng `Fraction`, không làm tròn hệ số.
- Hỗ trợ héc-ta, lít với dm³/cm³, giờ với giây, ngày với giờ, tuần với ngày; giữ tấn/tạ/yến và các tiền tố thường gặp.
- Nhận tên đơn vị tiếng Việt viết đầy đủ, nhiều dấu nối Unicode, số mũ `²`/`³`, `^2`/`^{2}`/`m2`, chữ số Unicode và dấu cách tách số mũ. Chỉ chuẩn hóa bản dùng để đọc quy tắc; không viết lại văn bản đề gốc.
- Cấp quy tắc theo ngữ cảnh cho phần trăm, giá trị hàng thập phân, hình chữ nhật, hình vuông, tam giác, hình thang, hình lập phương và hình hộp chữ nhật.
- Tên người Tân/Tạ/Hà không tự trở thành đơn vị. Không đổi khác thứ nguyên như kg sang lít, diện tích sang độ dài; không đặt cố định một tháng bằng 30 ngày hoặc một năm bằng 365 ngày.

Mô hình soạn bài và mô hình phản biện nhận cùng phiên bản kiến thức, các quy ước liên quan và hệ số đổi đơn vị. Prompt nêu rõ không được báo thiếu dữ kiện chỉ vì đề không in lại một quy ước đã được máy chủ cấp. Số liệu/kết quả do model tự thêm vẫn phải bị chặn.

Các quan hệ SI, tấn, héc-ta, lít và thời gian tham khảo [NIST SP 330, mục 4](https://www.nist.gov/pml/special-publication-330/sp-330-section-4) và [BIPM SI Brochure](https://www.bipm.org/en/publications/si-brochure). Cách gọi tạ/yến là quy ước toán phổ thông tiếng Việt được khai báo riêng.

### Giảm chặn nhầm cách viết tương đương

- `10000.0` được đối chiếu chính xác với hệ số `10000` đã có căn cứ. Số gần bằng như `10000.00001` vẫn không được nhận thay thế.
- Đổi m² → cm² bằng `3 × 100 × 100` được chuẩn hóa về `3 × 10000` nếu đúng quan hệ đơn vị của nguồn.
- Đổi m³ → dm³ bằng ba lần nhân 10 và đổi giờ → giây bằng hai lần nhân 60 cũng được kiểm tra tương đương như vậy.
- Chỉ gộp các thừa số chưa được cấp khi tích chính xác của chúng là hệ số chuyển đổi đã được xác minh. Không gộp một kết quả cuối tự tính thành dữ kiện; không cho phép các tổng số tự bịa hoặc tùy ý làm tròn.
- Tham chiếu kết quả bước trước vẫn được bảo toàn. Chuỗi tên giả giống biến nội bộ không được biến thành tham chiếu hợp lệ.

Đã cập nhật dấu vân tay chính sách catalog với file kiến thức mới; kế hoạch lưu bằng chính sách cũ không được tái dùng mà bỏ qua thay đổi kiểm tra.

### Lý do từ chối có thể truy vết

`validation_audit.py` ghi mã ổn định: `SCHEMA`, `UNGROUNDED_OPERAND`, `SOURCE_UNRESOLVED`, `SEMANTIC_REVIEW`, `RESULT_SCOPE`, `PREMATURE_RESULT`, `UNIT`, `OTHER_VALIDATION`; lượt sửa thành công có `RECOVERED`.

Nhật ký phân biệt giai đoạn soạn/phản biện, nguồn model thực sự kiểm tra và các cờ bị đánh giá sai: dữ kiện, toán học, trả lời câu hỏi, chất lượng giảng. Không lưu văn bản học sinh, tài khoản, bản nháp bị từ chối hay nội dung lỗi tự do vào các dòng audit mới. Chỉ có dấu vân tay nguồn để ghép các lần xử lý.

`RECOVERED` không tự động trở thành “chặn nhầm” hay nhãn train: bản nháp trước có thể sai thật và đã được sửa đúng. Quy tắc/nhãn mới vẫn cần được kiểm tra trước khi đưa vào kho.

## Dữ liệu và công cụ đánh giá

- `ai/runtime/tests/fixtures/validator_knowledge_cases.json`: **56 ca** có phép tính/đáp số được khai báo rõ; 39 ca được phép, 17 ca phải chặn theo chính sách căn cứ.
- Ca âm gồm cả kết quả số đúng nhưng dùng đáp án chưa được chứng minh hoặc số phụ tự thêm. Không coi toàn bộ ca âm là sai kết quả số.
- `ai/runtime/scripts/benchmark_lesson_validator.py`: chạy bộ ca, báo riêng tỷ lệ chặn nhầm/duyệt nhầm tại lớp căn cứ cục bộ, độ trễ và tổng hợp mã audit từ nhật ký.
- `ai/runtime/evaluation/validator_knowledge.md`: cách chạy, quy tắc gán nhãn, cách ly dữ liệu riêng và giới hạn diễn giải kết quả.

Đây là dữ liệu hồi quy tổng hợp đã dùng trong phát triển, không phải tập nghiên cứu độc lập chưa từng xem. Không có dữ liệu dự đoán OCR/model độc lập để công bố độ chính xác tổng quát hoặc thành tích fine-tuning.

## Kết quả kiểm thử

**649 passed, 6,97 giây** cho các suite bài học, đọc hiểu, nguồn dự phòng, chuẩn bị nền, phân số, catalog, tương tác và kiến thức mới. JUnit: `.local-artifacts/validator-knowledge-20261101/pytest.xml`.

Trong đó có kiểm tra nhiều dấu nối/cách viết/số mũ, tên người, thứ nguyên, lịch, tính bất biến giữa yêu cầu, hệ số phân tích thành nhiều thừa số, số thập phân gần đúng, metadata giả và việc audit không ghi dữ liệu thô.

Benchmark cục bộ: **56/56 qua**, không ghi nhận chặn nhầm trên 39 ca hợp lệ hoặc duyệt nhầm trên 17 ca cần chặn của bộ này. Lượt cuối: trung vị khoảng **0,53 ms/ca**, cao nhất khoảng **8,31 ms**. Đây là microbenchmark gồm cả tạo đối tượng test và kiểm tra, không phải thời gian model/HTTP/điện thoại. 56 ca đã được bao trong kiểm thử, không cộng chúng vào 649 để tăng tổng.

### Model thật trên bốn bài mới

| Dữ kiện và yêu cầu | Kết quả đã đối chiếu | Thời gian tạo/kiểm chứng toàn bộ |
|---|---|---:|
| 3 lít, rót 750 ml, hỏi phần còn lại theo ml | 2250 ml | 16,94 s; cần một lần sửa sau phản biện |
| 1 giờ 15 phút đổi ra giây | 4500 giây | 8,07 s |
| 2,5 ha, dùng 3500 m², hỏi phần còn lại | 21500 m² | 6,73 s |
| Lập phương cạnh 5 cm, diện tích toàn phần và thể tích | 150 cm², 125 cm³ | 7,19 s |

Các lượt này thực sự gọi Groq/Gemini. Không gọi lần phản biện đầu của bài lít là “chặn nhầm” khi chưa có nhãn xác minh bản nháp trước sửa. Kết quả cho thấy chuyển nguồn/sửa nội dung hoạt động; vẫn có chi phí độ trễ, không phải mọi bài mới đều xong trong 1–3 giây.

### Bài tấn–kg qua API local sau nạp bản cuối

Đúng văn bản 250 ký tự trong ảnh của người dùng: 2 tấn 35 kg, hạnh nhân chiếm 2/5, bốn phương án A–D.

- Mở phần đọc đề: **66,57 ms**.
- Toán sẵn sàng: **146,68 ms** tính từ đầu lượt thử, có gọi chuẩn bị trước mở bài.
- Trả lời sai thử nghiệm vẫn ở đúng revision; trả lời đúng hoàn tất `2035 kg → 814 kg`, đáp án A.
- Đo qua HTTP trên máy local; không phải bằng chứng thao tác trên điện thoại thật hoặc số đo OCR.

Đã nạp lại đúng tiến trình AI; chẩn đoán launcher `READY_FOR_FULL_DEMO`. Không xóa dữ liệu hay khởi động lại các dịch vụ đang khỏe khác.

## Giới hạn và trạng thái bàn giao

- Bộ luật mới không tự chứng minh mọi quan hệ ngữ nghĩa hoặc mọi đơn vị của một lời giải tùy ý. Phản biện độc lập và các bộ giải chính xác vẫn bắt buộc theo luồng hiện có.
- Bài thiếu dữ kiện, ảnh mơ hồ hoặc nguồn dịch vụ lỗi vẫn có thể chưa giải được; không hứa “không bao giờ từ chối”.
- Giữ nguyên giọng nam/nữ và lịch giọng nền; lượt này không thay dịch vụ TTS hoặc chứng minh hết các lỗi giọng bên ngoài.
- Chưa huấn luyện trọng số model. Muốn tinh chỉnh model riêng cần nhãn chuẩn và tập đánh giá riêng theo nguồn/dạng bài; không dùng log retry như nhãn đúng tự động.
- Không sửa frontend, Expo dependency, tài khoản, `.env.local` hay `demoUI`. Giữ các thay đổi chưa commit từ những lượt trước. Chưa commit/push.
- Tải lại app và mở phiên bài mới để thử bản vừa nạp.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: gom quy tắc về một nguồn, dùng thư viện chuẩn cho số học/chuẩn hóa/audit, không thêm hạ tầng huấn luyện giả hoặc dependency.
  - Applied to: kho kiến thức, bộ kiểm chứng, chuẩn hóa tương đương, audit và benchmark.
