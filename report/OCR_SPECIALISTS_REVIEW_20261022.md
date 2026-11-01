# Rà soát OCR chữ, toán và phân số — 22/10/2026

Đã sửa lỗi tọa độ vùng nhận diện và chạy đánh giá thật trên ảnh Drive. **Chưa có bằng chứng đạt mức đủ tin cậy để tự tạo nhãn nghiên cứu; chưa thay bất kỳ trọng số model production nào.**

## Thay đổi đã hoàn thành

- Sửa `xyxy_to_normalized_xywh` trong `ai/runtime/app/recognition/yolo_adapter.py`: cắt cả hai đầu hộp theo biên ảnh trước khi tính chiều rộng/cao. Ví dụ `[90,70,120,120]` trên ảnh 100×100 phải thành `[.9,.7,.1,.3]`; trước đó trả về `[.9,.7,.3,.5]`, vượt khỏi ảnh.
- Từ chối tọa độ hoặc kích thước ảnh NaN/Infinity, tránh ghi hình học không có thật. Có kiểm thử thất bại trước khi sửa và kiểm thử hồi quy cho cạnh trái, trên, phải, dưới.
- Thêm công cụ offline `scripts/data/compare_specialist_ocr.py`, giữ riêng các giả thuyết chữ/toán, hash checkpoint, vocabulary, ảnh nguồn và crop. Chọn nhánh theo vai trò vùng đã được rà trước, không dùng đáp án để chọn model.
- Thêm `scripts/data/inspect_fraction_ocr.py` chạy detector toán thật trên 73 vùng tử/mẫu. Không gộp tầng phân số, không giải phép tính để sửa chữ, không tạo mẫu ảnh hoặc ghi đè trọng số.
- Tạo hàng chờ rà nguồn cho đủ 598 vùng. Mọi nhãn máy đều là `MODEL_DRAFT`, `training_eligible=false`; đồng thuận của model không biến thành xác nhận của con người.

Đây là thay đổi tọa độ và công cụ đánh giá. Không có bằng chứng trong lượt này rằng độ chính xác OCR toàn ứng dụng đã tăng theo một tỷ lệ cụ thể.

## Dữ liệu và nguồn

Đọc lại 72 ảnh gốc trên ổ Drive G:, suy luận trên 598 vùng cắt cố định. Mỗi lần đọc kiểm tra SHA-256 ảnh gốc, hướng ảnh và pixel crop với hồ sơ đã đóng băng. Không ghi ảnh gốc, crop, ZIP hoặc Parquet vào dự án. Không đọc nguồn HOLDOUT.

501 vùng TRAIN có nhãn đủ điều kiện và 95 vùng DEV được dùng để tính điểm của lần chạy cuối. Hai vùng TRAIN mơ hồ vẫn được nhận diện để phục vụ rà soát nhưng **bị loại khỏi mọi điểm TRAIN cuối**, không huấn luyện. 22 vùng TRAIN chưa có vai trò phù hợp được nhánh ghép từ chối; coverage của nhánh ghép được ghi riêng trong JSON, không tính phần bỏ qua là đúng.

Lượt này không huấn luyện thêm. Các checkpoint thí nghiệm được tải chỉ để suy luận, không nhận gradient. Chưa coi nhãn cũ là dữ liệu đã có giáo viên xác nhận độc lập.

## Model Drive thực tế

| Thành phần | Khả năng xác nhận được | Giới hạn |
|---|---|---|
| `ocr_engine_handoff_final.zip` | CRNN dòng chữ tiếng Việt, 320 lớp; hash trọng số và vocabulary trùng bản trong dự án | Không phải model hiểu cả trang hoặc cấu trúc phân số 2D |
| `arithmetic_ocr_line_full_v1_2.zip` | 5.503 mục trong gói dữ liệu | Không có `.pth`, `.pt`, `.onnx`, `.safetensors`; không phải một model mới |
| CRNN legacy 237 lớp | Model dòng chữ cũ | Tên có “mathvision” không chứng minh là model chuyên toán |
| CRNN đối chứng toán riêng | Checkpoint thí nghiệm toán đã có, không phải trọng số production mới | Phụ thuộc crop và preprocessing của thí nghiệm |
| CRNN ứng viên dấu toán | Checkpoint thí nghiệm đã có cho dấu toán | Đã có hồi quy chữ trên bộ đối chứng bổ sung ở lượt trước |
| YOLO detector toán | 14 lớp: chữ số, `+`, `-`, `=`, dấu nhớ | Không có lớp riêng cho gạch phân số, nhân, chia hay hình học |
| Qwen giải toán trên Drive | Model sinh văn bản | Không nhận ảnh trực tiếp; không thể thay OCR chỉ bằng đổi tên model |

Đã dùng connector Drive xác định thư mục/gói model; đọc gói và ảnh từ mount G: vào RAM. Không tải thêm ảnh vào thư mục người dùng đã xóa.

## Điểm thực nghiệm trên cùng 95 vùng DEV

CER là số lỗi chỉnh sửa ký tự chia số ký tự tham chiếu; càng thấp càng tốt. “Đúng toàn vùng” đòi hỏi chuỗi khớp toàn bộ sau chuẩn hóa khoảng trắng/NFC. Mọi hàng đều dùng greedy CTC; không đồng nhất các số này với beam search hoặc pipeline production.

| Cấu hình | Đúng toàn vùng | CER | Lỗi chuỗi số/dấu quan trọng |
|---|---:|---:|---:|
| CRNN chữ 320, input cố định 64×1024 | 3/95 | 40,11% | 242 |
| CRNN legacy 237, input cố định 64×1024 | 0/95 | 66,73% | 394 |
| CRNN đối chứng toán riêng, giữ tỷ lệ | 53/95 | 9,57% | 30 |
| CRNN ứng viên dấu toán, giữ tỷ lệ | 53/95 | 9,48% | 27 |
| Ghép theo vai trò: prose→chữ 320, toán→đối chứng toán | 47/95 | 12,12% | 31 |

Kết luận trong phạm vi thử nghiệm: **ghép theo tên/chức năng dự kiến đang kém hơn đối chứng toán riêng**, nên không kích hoạt nhánh ghép trong ứng dụng. Bài test so sánh cả checkpoint và preprocessing đi kèm; không tách được tác động riêng của kiến trúc/trọng số/preprocessing.

Ở 22 vùng prose, model chữ đúng toàn vùng 3/22, đối chứng toán 9/22. Ở 73 vùng toán, hai model toán cùng đúng toàn vùng 44/73; ứng viên dấu giảm lỗi số/dấu từ 25 xuống 22. Không suy rộng rằng model toán tốt nhất cho mọi chữ viết tay tiếng Việt: tập này nhỏ và thiên về trang toán.

Ứng viên dấu vẫn chưa được chấp nhận. Hồ sơ **lượt trước**, không phải phép đo lại ở lượt này, trên 18 đối chứng bổ sung có 12 mẫu TRAIN lịch sử/6 DEV: số lỗi ký tự trên 12 mẫu tăng 31→33, lỗi số/dấu tăng 3→4, gồm nhầm `x` thành `×` trong chữ. Không lấy mức cải thiện nhỏ trên DEV hiện tại để bỏ qua hồi quy đó.

## Phân số: lỗi còn thật

Hai CRNN toán đều đọc đúng 7/11 vùng tử/mẫu DEV; detector YOLO đọc đúng toàn vùng 0/11 và không đưa ra chuỗi chỉ gồm chữ số ở 5/11 vùng. Đây là chẩn đoán trên **từng thành phần được cắt sẵn**, chưa phải độ chính xác đọc phân số hoàn chỉnh.

Đã xem trực tiếp trong RAM cả crop và ngữ cảnh của bốn lỗi DEV:

| ID hậu tố trên nguồn `1-bFkCGeM1qu1TFLPZlhv31AyAy0fsXJS` | Nhãn tham chiếu | Đối chứng toán đọc | Quan sát ảnh |
|---|---|---|---|
| `fraction-dev-1` | 5 | rỗng | Nét 5 còn thấy trong crop |
| `fraction-dev-5` | 7 | rỗng | Nét 7 còn thấy trong crop |
| `extra-fraction-0` | 13 | 3 | Cả nét 1 và 3 còn thấy trong crop |
| `extra-fraction-1` | 13 | 3 | Cả nét 1 và 3 còn thấy trong crop |

Không sửa nhãn/hộp cắt DEV sau khi xem lỗi, không thêm số 1 dựa vào đáp án. Quan sát này chưa đủ kết luận nguyên nhân sâu nằm riêng ở preprocessing hay trọng số, nhưng chưa có căn cứ nói nét bị cắt mất để nới crop theo đáp án.

Hai vùng TRAIN mơ hồ cũng được xem lại. Giữ nguyên cách ly để người có trách nhiệm xác nhận; không tự sửa nhãn bằng dự đoán của model hoặc suy luận phép tính.

## Hàng chờ nghiên cứu

- Ưu tiên 0: hai vùng nguồn mơ hồ, tiếp tục cách ly.
- Ưu tiên 1: 73 vùng tử/mẫu cần kiểm tra quan hệ trên–dưới và gạch phân số cùng ảnh nguồn.
- Ưu tiên 2: 523 vùng còn lại có bất đồng giữa ít nhất hai trong bốn checkpoint. Cả 598 vùng có bất đồng trong tập bốn model; cờ này là yêu cầu rà soát, không phải bằng chứng rằng 598 nhãn tham chiếu đều sai.
- 22 vùng thiếu vai trò được nhánh ghép từ chối; 39 vùng có bản đọc được chọn rỗng hoặc chưa chọn được nhánh. Các nhóm này có thể chồng lấp.

Không đưa bất kỳ bản dự đoán nào của lượt này vào manifest huấn luyện. Muốn dùng cho nghiên cứu cần đối chiếu nguồn, xác nhận nhãn bởi người rà soát, giữ đúng phân chia theo trang/người viết và một tập đánh giá độc lập chưa dùng chọn model/preprocessing.

## Kiểm chứng và bằng chứng

- 106 kiểm thử nhận diện/adapter/bố cục phân số/nguồn/dấu toán đạt; 119 kiểm thử CRNN, segmentation và đường OCR/API đạt.
- Sau khi bổ sung hai trường hợp kích thước ảnh không hữu hạn: chạy lại adapter đạt 17/17. Công cụ chọn nhánh/nhãn nháp đạt 3/3. Tổng 230 trường hợp khác nhau qua các lượt, không cộng trùng 15 adapter đã chạy trước.
- Hai lượt so sánh cho 598×4 giả thuyết giống hệt nhau. Lượt đầu chỉ dùng chẩn đoán; bảng cuối và summary dùng **v2**, đã loại hai nhãn cách ly khỏi điểm TRAIN và thêm hàng chờ rà nguồn. Không thay thế hồ sơ cũ.
- Hash trọng số/vocabulary giữ nguyên trước–sau suy luận. Các file privacy, crop, AppHeader, AppButton và theme khớp baseline được bảo vệ. Không đổi màn che tên/cắt ảnh, không sửa UI trong lượt này.
- Không commit, push, deploy, thay route model hay chỉnh notebook train Drive.

[Điểm và hash tổng hợp](ocr-specialists-20261022/summary.json) · [Kiểm tra gói Drive và file bảo vệ](ocr-specialists-20261022/inventory-checks.json) · [Kiểm tra cuối](ocr-specialists-20261022/verification.json).

Bằng chứng đầy đủ ngoài Git:

- `ai-training/datasets/drive_math/specialist_comparison_v2_20261022/comparison.json`
- `ai-training/datasets/drive_math/specialist_comparison_v2_20261022/review-queue.json`
- `ai-training/datasets/drive_math/specialist_comparison_v2_20261022/yolo-fraction-diagnostic.json`

Lệnh lặp lại: dùng Python trong `ai/runtime/.venv`, chạy `scripts/data/compare_specialist_ocr.py --output <thư-mục-mới>`; sau đó chạy `scripts/data/inspect_fraction_ocr.py --output <file-mới>`. Công cụ cố ý từ chối ghi đè bằng chứng. Detector chẩn đoán tham chiếu kết quả v2 được đóng băng.

Giới hạn: DEV đã dùng ở các vòng trước, chưa chứng minh độc lập người viết/nguồn tiền huấn luyện; vai trò/hộp cắt là metadata đã rà, không phải kết quả tự động. Kiểm thử phần mềm đạt không tương đương OCR đạt độ chính xác nghiên cứu hoặc mọi ảnh ngoài thực tế.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa lỗi Python và công cụ đánh giá với thay đổi nhỏ, tái sử dụng bộ đọc nguồn/model/metric đã có.
  - Applied to: tọa độ YOLO, kiểm thử hồi quy, so sánh offline và không xây thêm bộ định tuyến production.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.22/skills/google-drive/SKILL.md`
  - Why selected: xác định đúng gói model và dữ liệu trên Drive người dùng cung cấp.
  - Applied to: tra metadata/thư mục, phân biệt gói trọng số với dataset, đọc nguồn gốc vào RAM.
