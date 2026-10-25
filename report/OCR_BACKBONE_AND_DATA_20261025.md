# OCR chữ và toán — kết quả kiểm chứng ngày 25/10/2026

**Chưa đủ điều kiện thay model trong app.** Đã hoàn tất 12 lượt train có cập nhật trọng số, tổng cộng 116 lượt đi hết corpus TRAIN và 80 lượt đi hết tập token nguyên âm đã căn chỉnh. Không ứng viên nào vượt toàn bộ guard giữ những dòng/số/dấu/đơn vị đang đúng. Tất cả checkpoint được chọn ở epoch0, giữ trọng số parent; không gọi chúng là model đã cải thiện.

21 kiểm thử kỹ thuật đã qua. Đây là kiểm thử mã/pipeline và tính toàn vẹn, không phải 21 bằng chứng đạt chất lượng OCR.

## Dữ liệu mới và cách bảo vệ phép đo

- Dành riêng bốn nguồn mới cho TRAIN bằng thứ tự SHA trước khi mở ảnh. Đọc nguồn và từng crop trực tiếp; tạo 49 nhãn nháp, sửa khung cắt/nhãn theo pixel, loại bốn vùng bị cắt hoặc còn mơ hồ. Chốt **45 vùng:12prose,28số,5biểu thức có đơn vị** trước khi đọc dự đoán của model trên những vùng này.
- Bổ sung vào replay: **722 TRAIN fulltext** và **1.487 TRAIN numeric**. Không chuyển VAL/DEV/chẩn đoán vào TRAIN. Nhãn ghi chữ thực tế, không sửa phép tính của học sinh bằng suy luận số học.
- Hai lượt nhìn/crop do cùng Codex thực hiện; **không phải kiểm định giáo viên hoặc hai người rà độc lập**. Không biết ID người viết. SHA nguồn khác nhau không chứng minh khác người viết hoặc khác trang được chụp lại.
- Các loader xác minh byte/pixel/crop SHA trước tiền xử lý. Ảnh nguồn/crop chỉ ở RAM; hình phục vụ rà nhãn truyền bằng JPEG trong RAM. Không lưu ảnh/ZIP/Parquet vào thư mục thử nghiệm mới.
- Old22 là tập đối chiếu bị loại khỏi TRAIN của các thử nghiệm fulltext hiện tại, nhưng vẫn giữ metadata TRAIN lịch sử. Một nguồn trong TRAIN của numeric trùng nguồn old22 của fulltext; các lượt tiền huấn luyện cũng chưa xác minh độc lập. **Không dùng các điểm này làm bằng chứng acceptance độc lập toàn pipeline.**

## Các hướng đã thực hiện

| Hướng | Khối lượng train thực tế | Quyết định |
|---|---:|---|
| VietOCR native32: output head và toàn decoder |2×8 full passes,677TRAIN|Cả hai bị loại|
| VietOCR64: CNN,encoder,decoder; BN statistics cố định |8 full passes,677TRAIN|Bị loại|
| CRNN chuyên chữ: CNN cố định,RNN/head cập nhật |2×16 full passes,173TRAINprose|Bị loại; dù chỉ chấm vai trò chữ cũng có hồi quy|
| CRNN replay có45vùng mới, hai mức retention mỗi vai trò |4×12 full passes;722text/1.487numeric|Cả bốn bị loại|
| Classifier nguyên âm: GT căn theo vị trí token TRAIN |2×40 token passes|Bị loại; bộ giải mã giữ nguyên ranh giới token/số/dấu nhưng vẫn có hồi quy chữ|
| VietOCR native32: CNN,encoder,decoder cùng cập nhật, thêm45vùng mới |12 full passes,722TRAIN|Bị loại|

Lượt VietOCR native32 toàn mạng giảm lỗi new39 từ **451 xuống83** và prose10 từ366 xuống48, nhưng vẫn kém đối chứng CRNN; old22 còn55lỗi. Đây là thay đổi của checkpoint cuối **bị loại**, không phải điểm của ứng viên được chấp nhận. Checkpoint được chọn giữ parent ở epoch0. Các lượt hiện tại chỉ lưu checkpoint được chọn; trạng thái cuối của checkpoint bị loại không được giữ riêng, nên không dùng chúng để tuyên bố có model mới có thể triển khai.

Đã tải và kiểm SHA weights từ nguồn chính thức của [VietOCR](https://github.com/pbcquoc/vietocr) và model [TrOCR tiếng Việt của tác giả](https://huggingface.co/duyle2408/trocr-vietnamese-handwriting). TrOCR nạp đủ weights bằng thư viện cài cục bộ, tắt remote code, chạy GPU và benchmark thực tế; kết quả **0/22 old và0/39 new**. Không fine-tune hoặc chọn TrOCR làm thay thế. Điểm/model card của tác giả không được coi là điểm trên dữ liệu dự án.

## Tiền xử lý cũng được đo riêng

Chọn xử lý màu mực trên TRAIN trước rồi cố định để đo VAL:

- Fulltext: old22 lỗi **13→14**, new39 **42→39**.
- Numeric: old65 lỗi **8→9**, new22 **3→2**.

Cả hai bị loại vì làm sai thêm dữ liệu cũ. Thử thêm sáu cách thêm lề/kéo ngang bên cạnh identity trên173prose và280vùng số TRAIN; CPU/GPU đối chứng khớp. Không cách nào vượt identity mà giữ được các dòng đang đúng, nên không thử chọn lại bằng VAL.

## Tình trạng có thể dùng để đánh giá dự án

Các mốc CRNN tốt nhất đã kiểm chứng ở vòng trước vẫn giữ nguyên; vòng này không đọc lại DEV/chẩn đoán để chọn các ứng viên đã thất bại ở VAL:

| Phép đo phát triển | Kết quả giữ lại |
|---|---:|
| Numeric oldVAL65 |58/65 đúng nguyên dòng,8lỗi/187ký tự|
| Numeric newVAL22 |19/22,3lỗi/63ký tự|
| Prose old22 subset14 |10/14,7lỗi/187ký tự|
| Prose new39 subset10 |3/10,20lỗi/197ký tự|
| Phân số với cặp crop thủ công,31cặp đã xem |26/31|
| Phân số từ57đề xuất hình học cố định |22/31đúng;26/31được phát hiện; nhãn trang chưa đầy đủ|

Không suy ra precision hay độ chính xác toàn trang từ các vùng đã chú thích một phần. Các tập VAL/DEV đã dùng nhiều vòng là dữ liệu phát triển, không phải kết quả nghiên cứu độc lập.

## Tính toàn vẹn và giới hạn còn lại

- Audit đầu kiểm223đầu vào hash,11lượt train; audit nối tiếp xác minh thêm lượt native32 thứ12 và liên kết SHA với audit trước.
- Checkpoint epoch0 bằng tensor với parent thật; kiểm shape/finite và nạp lại. Các lượt CRNN kiểm lại full forward CPU; các lượt VietOCR kiểm lại native full forward GPU. Classifier nguyên âm cần parent và bộ giải mã riêng, không phải checkpoint CRNN có thể thay trực tiếp.
- Model production vẫn SHA`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`. Năm file UI được bảo vệ và33trạng thái file đã sửa trước đó đều giữ nguyên. Không commit/push, không đổi runtime/provider/Student, không có bằng chứng thiết bị thật được tạo ra.
- Các lỗi runner/phương án nháp được giữ lại trong`recovery_notes.json`; hai lần chạy photometric lỗi được tách khỏi lầnv2 hoàn tất. Source plan có chỉ số trang sai không được dùng để mở ảnh/tạo nhãn; bảnv2 được chốt trước khi rà ảnh.
- **Mục tiêu chưa đạt:** ≥95%exact,≤2%CER, không mất literal đang đúng; acceptance theo nguồn/người viết độc lập và nhãn toàn trang đầy đủ; kiểm chứng ghép recognizer chữ/toán với detector trong luồng Student. Hiện chưa có dữ liệu đủ chứng nhận những điều kiện này.

Hướng nghiên cứu tiếp theo cần ưu tiên transcript và nguồn/người viết độc lập, thống nhất sổ nguồn giữa recognizer chữ/toán, và đo khả năng autoregressive đọc đúng TRAIN để phân biệt chưa học được với thiếu khả năng tổng quát. Những lượt fine-tune tiếp theo cần giữ thêm checkpoint cuối/optimizer và điểm TRAIN, kể cả khi bị guard loại. Tăng epoch trên các tập đã xem không tự chứng minh model hoàn thiện.

## Bằng chứng

- [Kết quả11lượt đầu và các phép đo](ocr-backbone-and-data-20261025/results.json)
- [Audit11lượt đầu](ocr-backbone-and-data-20261025/integrity.json)
- [Lượt native32 thứ12 và audit nối tiếp](ocr-backbone-and-data-20261025/native32-extension.json)
- Mã,policy,log epoch,nhãn và checkpoint:`ai-training/datasets/drive_math/math_vietocr_adaptation_20261025/`.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Controlled OCR training, literal annotation, regression evaluation and reproducibility in the existing Python pipeline.
  - Applied to: Reused CRNN/source loaders/native model APIs; isolated frozen experiments; rejected regressions; preserved runtime/UI/Git without adding a training framework.
