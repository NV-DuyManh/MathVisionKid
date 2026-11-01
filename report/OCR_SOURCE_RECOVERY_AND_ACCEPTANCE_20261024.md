# OCR chữ, số và phân số — khôi phục nguồn và kiểm chứng 24/10/2026

**Đã tìm được ảnh gốc, huấn luyện và kiểm chứng thêm; chưa có ứng viên đủ điều kiện thay model trong ứng dụng.** Bản số tốt nhất trên VAL đạt **59/65 vùng đúng toàn bộ, CER 3,74%** bằng beam. Cùng cấu hình đó trên bốn trang vở chẩn đoán chỉ đúng **65/86 vùng số**, vẫn có hồi quy `22 → 21`. Không lấy điểm VAL cao để gọi model đã hoàn thiện.

Đây là vòng nghiên cứu tiếp nối. Các thay đổi nằm trong `ai-training/datasets/drive_math/math_robust_numeric_20261024/`; runtime và trọng số production không đổi. Không commit/push.

## Khôi phục ảnh gốc: nút thắt trước đây đã được giải quyết

Đã xác định được nguồn chính thức [HME-VAS](https://github.com/Danielgol/HME-VAS/tree/bb610aa67e9c8fda71ce1416a0068521f8274bee), khóa commit `bb610aa67e9c8fda71ce1416a0068521f8274bee`. Ảnh `117.png` có SHA256 `07f36c61eea40ef8352e4aeb0276beb21ca4aebde35bd8fb4fb2e96187b734fc`, khớp byte với provenance `hme_117` của gói Drive. Vì vậy kết luận “chưa tìm được ảnh gốc” trong báo cáo trước đã được thay bằng bằng chứng khôi phục thực tế.

- Đọc **256/256 ảnh TRAIN gốc** vào RAM, kiểm tra SHA256 với metadata đã có. Không truy cập ảnh gốc VAL/TEST/HOLDOUT.
- Đọc chú thích ký tự gốc; lấy hợp đầy đủ bounding box ký tự, thêm lề hình học. Không phục hồi nét bằng ảnh sinh hoặc suy luận phép tính.
- 17 hàng từng bị cảnh báo cắt nét đã được đối chiếu với nguồn; các hàng khớp nhãn được cắt lại từ nét thật. Một số vùng vẫn lẫn dấu nhớ hoặc dấu phân cách nên tiếp tục bị loại khỏi train.
- Loại **44 trường hợp không khớp nhãn/nhóm hàng**. Trong 1.711 vùng khôi phục còn lại, loại **535 vùng có chú thích phụ giao vào crop** mà transcript không chứa chúng.
- Giữ **1.176 mẫu**: 170 hàng số và 1.006 ký tự đơn từ chú thích gốc. Cộng 153 TRAIN số cũ thành **1.329 mẫu**. Đây là số crop/annotation, không phải 1.329 người viết hoặc ảnh trang độc lập.
- Chỉ lưu cache đặc trưng CNN `original_prefixes.pt` khoảng 99,5 MB và metadata; không ghi ảnh nguồn/crop/ZIP/Parquet vào dự án.

Chú thích upstream và cờ `HUMAN_VERIFIED` do bên cung cấp khai báo không được nâng thành xác nhận độc lập của giáo viên. Writer identity và trùng tiền huấn luyện vẫn chưa rõ; nguồn HME đã được đánh dấu YOLO-seen trong gói.

## Dữ liệu vở thật bổ sung

Đã chọn sáu ảnh grade5 theo hash metadata, ngoài toàn bộ nguồn TRAIN/DEV đang dùng và bốn trang chẩn đoán. Xem trực tiếp ảnh gốc rồi từng crop trước khi chạy OCR trên các vùng đó.

- Một ảnh mờ/viết đè không được nhận vào train.
- Bản nháp có 53 vùng. Loại năm vùng khó xác nhận hoặc lẫn nét lân cận; chốt **48 crop từ năm ảnh**, gồm **5 vùng chữ** và 43 vùng số/đoạn chữ số.
- Giữ dấu phẩy thập phân, số 0 đầu và lỗi toán viết trong ảnh. Vùng số thập phân không được đưa vào head chỉ nhận số nguyên. Các đoạn chữ số cắt ra được ghi rõ `digit_fragment`, không gọi là toàn bộ giá trị thập phân.
- Nhãn do Codex rà trực tiếp trên ảnh; **chưa có giáo viên xác nhận độc lập**. Không lấy dự đoán model hoặc đáp án để tạo nhãn.
- `domain_training_manifest_v2.json` là manifest thực thi. Bản trước và log lỗi chuẩn bị được giữ nguyên, không hồi tố sửa dữ liệu của một lần chạy đã xong.

## Các lượt huấn luyện thực sự đã chạy

Tổng **11 lượt neural training, 196 epoch cộng gộp**, trong đó 60 epoch là head phân loại chữ số nhỏ; không so trực tiếp số epoch giữa các kiến trúc. Tổng thời gian các tiến trình train báo là **1.579,80 giây** trên CPU; không phải thời gian toàn bộ công việc. Không báo train GPU/cloud.

| Thử nghiệm | Dữ liệu/đích cập nhật | Kết quả chính |
|---|---|---|
| Retention control, 20 epoch | 885 TRAIN số; BiLSTM + head13 | Chọn epoch19; 57/65 greedy và beam |
| Retention composed, 20 epoch | 885 + 300 chuỗi ghép từ 21 glyph TRAIN đã xem | 56/65; không hơn control |
| Recovered recurrent, 8 epoch | 1.329 TRAIN; CNN cố định | 54/65 greedy, 55/65 beam |
| Recovered visual, 8 epoch | Thêm cập nhật block CNN cuối | 55/65 greedy, 56/65 beam |
| Text+math recurrent, 10 epoch | Full vocab321; chữ có trọng số cao | Chọn epoch5; old DEV 106 lỗi so với parent105 |
| Text+math visual, 10 epoch | Thêm CNN cuối | Chọn epoch8 nhưng không qua điều kiện giữ chất lượng prose; old DEV108 lỗi |
| Numeric continuation, 24 epoch | Tăng cập nhật thị giác và glyph thật | Không vượt warm start; chọn epoch0, không coi là cải thiện |
| Digit head, 60 epoch | CNN cố định; pooling + linear10 | 212/218 held-TRAIN; chỉ 29/47 trên tập con chữ số vở chẩn đoán |
| Domain numeric, 8 epoch | 1.361 TRAIN, gồm32 crop mới phù hợp số nguyên | Chọn epoch2; 58/65 greedy, 59/65 beam |
| Domain text, 8 epoch | 1.703 TRAIN, đầy đủ chữ/số/thập phân | Không vượt điều kiện prose; chọn parent epoch0 |
| Prose specialist, 20 epoch | CTC trên127 dòng chữ; giữ các vùng khác bằng KL | Held-TRAIN giảm9→8 lỗi; old DEV prose vẫn29 lỗi |

Các chuỗi ghép ở một thử nghiệm là augmentation có nhãn chương trình từ glyph TRAIN đã rà, không được gọi là 300 bài viết tay thực tế mới. Không dùng chúng làm nhãn đánh giá. Các thử nghiệm còn lại không dùng augmentation chuỗi này.

CTC dùng độ dài thật, packed BiLSTM; CNN tính từng crop ở chiều dài thật để GroupNorm không nhận padding của ảnh khác. KL dùng phân phối teacher để giữ hành vi, không biến đầu ra teacher thành nhãn xác nhận. Loss/gradient và checkpoint được kiểm tra hữu hạn.

## So sánh đúng cùng bộ và decoder

VAL gồm65 crop/187 ký tự đã dùng nhiều lần để chọn cấu hình, **không phải test độc lập**. Beam dùng prefix decoder hiện có, width15/top5; chọn chuỗi theo xác suất, không chọn theo đáp án.

| Cấu hình số | Greedy đúng /65 | Beam đúng /65 | Beam CER |
|---|---:|---:|---:|
| Parent giới hạn13 lớp, chưa train thêm |44|45|12,83%|
| Specialist885 của lượt trước |55|56|5,35%|
| Retention control |57|57|4,81%|
| Retention control + giữ tỷ lệ tối thiểu32px |—|58|4,28%|
| Domain numeric |58|59|3,74%|

Thử riêng bốn preprocessing: stretch tối thiểu64, giữ tỷ lệ tối thiểu32, letterbox64 và letterbox96. Chọn bằng VAL trước khi đọc lại chẩn đoán. Với retention control, min32 cải thiện bốn trang từ66/86 lên71/86. Khi so cả model và preprocessing, domain numeric có ít lỗi VAL hơn nên được chọn theo quy tắc đóng băng; trên bốn trang nó chỉ đúng65/86. **Không tự chọn lại cấu hình theo điểm chẩn đoán rồi gọi đó là kết quả độc lập.**

Trên16 DEV số cũ, domain numeric và parent cùng beam đạt13/16, nhưng tập lỗi khác nhau: domain numeric vẫn biến một vùng `22` mà parent đọc đúng thành `21`. Tổng điểm bằng nhau không có nghĩa không hồi quy.

## Chữ tiếng Việt

Parent ở đây là checkpoint nghiên cứu full vocab321 với preprocessing giữ tỷ lệ, không phải bản production320 resize64×1024. Không so điểm của hai preprocessing như thể chỉ thay trọng số.

| Full-vocab greedy trên95 DEV cũ | Đúng toàn vùng | Lỗi ký tự | Lỗi trên22 vùng prose |
|---|---:|---:|---:|
| Parent |53/95|105|29|
| Text+math recurrent |48/95|106|31|
| Text+math visual |47/95|108|30|
| Prose specialist |52/95|107|29|

Prose specialist giảm lỗi trên phần held-TRAIN đã tách trang cho lượt này nhưng chưa cải thiện DEV. Nó còn làm mất số0 ở `300 cm² = 3 dm²` và `650-150=500`. Trên sáu vùng chữ của bốn trang chẩn đoán, parent và prose specialist đều đúng2/6, 22 lỗi/122 ký tự. Vì vậy không thay model chữ.

14 prose held-TRAIN được tách theo source page khỏi gradient của các lượt continuation tương ứng; chúng vốn thuộc TRAIN lịch sử nên **không độc lập với mọi tiền huấn luyện/thử nghiệm trước**.

## Phân số và đánh giá cả vùng

Đã đóng băng bốn trang,92 vùng:86 số,6 prose,31 cặp tử/mẫu. Nhãn và hộp được rà trước dự đoán đầu tiên. Không dùng bốn trang để train hoặc chọn checkpoint; sau lần đánh giá đầu, đây là tập **chẩn đoán đã xem**, không gọi là test mù cho các lượt sau. Chưa có transcript đầy đủ toàn trang hoặc writer-disjoint certification.

- Crop thủ công: retention control đúng **22/31 cặp**; domain numeric đúng **21/31**. Kết quả11 tử/mẫu của bộ cũ không được gọi là11 phân số hoàn chỉnh.
- Probe tự tìm gạch, tách tầng rồi OCR có **57 đề xuất trên4 trang**. Theo paired IoU≥0,5 và ghép duy nhất chỉ theo hình học: tìm26/31 cặp được chú thích; retention control đọc đúng20/31, domain numeric19/31.
- Quy tắc đầu tiên yêu cầu chứa80% cả hộp thủ công, gồm lề trắng, chỉ tính2/31. Đã giữ nguyên kết quả đó và ghi phép sửa giao thức riêng trong `fraction_matching_audit.json`; không sửa nhãn, prediction hoặc hồi tố báo đó là tăng độ chính xác model.
- Chưa có ground truth toàn bộ trang nên **không công bố precision** của57 đề xuất. Các đoạn chữ/dấu gạch có thể tạo false positive. Probe này là công cụ offline, chưa thay route production.
- Thử điều kiện parent và candidate cùng đọc một chuỗi: chấp nhận80/86 vùng nhưng chỉ64 đúng. Đồng thuận vẫn có thể cùng sai, nên không dùng làm nhãn nghiên cứu tự động.

## Kiểm chứng và các lỗi công cụ đã sửa

- Tiến trình Python riêng nạp8 cấu hình số, đọc lại65 VAL đã kiểm SHA; tái lập đúng greedy/beam và cả top5. Các checkpoint domain, continuation và prose được nạp lại; điểm selected-VAL/held-TRAIN khớp.
- Digit head nạp lại tái lập212/218 held-TRAIN. Điểm97,25% đó chỉ là phân loại crop một chữ số cùng nguồn; độ chính xác vở29/47 cho thấy không được quảng cáo97% OCR thực tế.
- **15 unit test đạt**: cached CNN tương đương full forward, chặn split ngoài TRAIN trước network, từ chối hash sai trước decode, crop giữ nét cao, CTC `22`/`001`, IoU, ghép một-một, không dùng giá trị để chọn geometry, giữ tỷ lệ crop hẹp, cách ly vùng mơ hồ, thập phân không lọt head số nguyên, trang mới không trùng DEV/chẩn đoán.
- **104 input được pin hash không đổi** qua13 policy thực thi;10 CRNN có tensor hữu hạn/nạp được, digit head kiểm riêng. Các màn hình được bảo vệ vẫn khớp hash.
- Một lần chuẩn bị retention bị collision tên module `prepare`; sửa bằng import tuyệt đối trước khi train. `training_policy_v2.json`/`training_v2.log` mới là bản chạy; log thất bại cũ được giữ.
- Một lần chuẩn bị domain gặp tên trường `decoded_source_size`; sửa adapter metadata, chốt manifest/policy v2 trước gradient. Bản thất bại không được tính là training.
- TEST68 crop chữ tay và nguồn HOLDOUT vẫn không đọc pixel. Metadata split có được kiểm để phát hiện trùng. Không ghi ảnh nguồn/crop, không gọi cloud model, không có kiểm thử thiết bị vật lý.

## Quyết định thay model và phần còn thiếu

`release_gate.json` là **NOT_READY_FOR_PRODUCTION**. Ngưỡng đã khai báo gồm exact≥95%, CER≤2%, không hồi quy vùng quan trọng cũ, kiểm thử trang đầy đủ và người viết độc lập. Hiện vẫn không đạt.

Model production vẫn SHA256:

`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`

Luồng đọc vở Student hiện đi qua `app/tutoring/notebook.py::inspect_notebook` và dịch vụ sinh kết quả Gemini. Các CRNN/công cụ trong báo cáo là nhánh nghiên cứu riêng; không tuyên bố đã nâng chất lượng OCR của app chỉ vì train checkpoint offline. Head13 chỉ đọc vùng số phù hợp, không thay trực tiếp recognizer chữ hoặc luồng ảnh cả trang. Qwen sinh chữ không trở thành model nhận ảnh khi đổi tên.

Các việc còn cần cho một lần thay có cơ sở:

1. Bổ sung nhiều ảnh vở cùng miền sử dụng, đủ kiểu viết, nét mờ, số lặp, dấu và phân số; quản lý theo người viết/trang, tránh thêm nhiều crop của cùng ảnh rồi gọi là đa dạng dữ liệu.
2. Xác nhận nhãn literal chữ/dấu/zero bằng người có trách nhiệm; ghi mơ hồ là mơ hồ. 48 crop mới và các hàng khôi phục chưa thay cho một tập nhãn lớn đã kiểm độc lập.
3. Có nhãn phát hiện vùng chữ/số/gạch phân số và liên kết tử–mẫu, đo cả false positive trên transcript toàn trang. Điểm crop riêng không đủ để thay cả pipeline.
4. Chốt ứng viên và preprocessing, kiểm hồi quy trước, rồi mới mở test độc lập sau cùng. Không train vào `diagnostic_failures.json`, không mở TEST nhiều lần để chọn model.

Đây là giới hạn đo được của vòng này; không có bằng chứng rằng tăng tiếp epoch trên cùng dữ liệu sẽ đưa tới “hoàn hảo”.

## Tệp tái lập

Thư mục `ai-training/datasets/drive_math/math_robust_numeric_20261024/` chứa code, manifest, policy, checkpoint, log và kết quả từng lượt. Các tệp chính:

- Nguồn: `recover_hmevas.py`, `recover_features.py`, `recovered_source_audit.json`, `recovered_training_manifest.json`.
- Dữ liệu mới: `domain_data.py`, `domain_source_plan_v2.json`, `domain_training_manifest_v2.json`, `domain_feature_manifest.json`.
- Train: `train_robust.py`, `train_recovered.py`, `train_text_math.py`, `continue_numeric.py`, `train_digit_head.py`, `train_domain.py`, `train_prose.py` và policy/log cùng tên.
- Đánh giá: `evaluation_result.json`, `fraction_matching_audit.json`, `text_math_evaluation.json`, `numeric_continue_evaluation.json`, `digit_head_result.json`, `domain_evaluation.json`, `preprocessing_result.json`, `combined_evaluation.json`, `prose_evaluation.json`.
- Kiểm chứng: `numeric_verification.json`, `final_integrity.json` là snapshot trước phần domain; **`round_integrity.json` là snapshot tổng kết đầy đủ**. `release_gate.json`, `diagnostic_failures.json` giữ quyết định và lỗi còn lại.

Các thư mục thí nghiệm/weights lớn hiện được Git ignore theo cấu hình dự án. Báo cáo không đồng nghĩa checkpoint đã upload Git hoặc Drive.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Công cụ Python cho OCR/training; registry chưa có skill chuyên OCR. Không áp dụng skill UI cho phần AI.
  - Applied to: Tái sử dụng CRNN, loader Drive RAM-only, source hash/orientation, CTC/beam và metric hiện có; dùng PyTorch/stdlib đã cài, giữ nghiên cứu riêng, không thêm dependency hoặc đổi runtime/app.
