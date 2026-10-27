# OCR số riêng — tiếp tục cải thiện ngày 24/10/2026

Đã chạy thêm **hai lượt train, 12 epoch/lượt**, với model số riêng 13 lớp. Bản dùng 885 mẫu đạt **55/65 đúng toàn vùng bằng greedy**, **56/65 bằng CTC beam cố định**, cao hơn các đối chứng cùng vocab/decoder. Model chữ và model production được giữ nguyên byte. **Chưa đưa ứng viên vào app** vì vẫn nhầm một crop `22 → 21` vốn parent đọc đúng, và chưa có bằng chứng kiểm thử độc lập cho toàn pipeline.

## So sánh đúng phần cải thiện

Mỗi hàng dưới dùng cùng 65 crop VAL số, 187 ký tự, resize giữ tỷ lệ và cùng CNN. Không đổi ảnh, không tính đáp án toán để sửa kết quả. Beam dùng implementation sẵn trong runtime, width15/top5, chọn chuỗi có sequence log probability cao nhất, không chọn theo nhãn đúng.

| Model số trên VAL | Greedy đúng /65 | Greedy lỗi ký tự | Beam đúng /65 | Beam lỗi ký tự |
|---|---:|---:|---:|---:|
| Parent, chỉ giới hạn 13 lớp, **chưa train thêm** |44|26|45|24|
| Recurrent của lượt trước, giới hạn 13 lớp |50|18|50|18|
| Train mới: 885 mẫu sau cách ly |**55**|**11**|**56**|**10**|
| Train mới: 487 mẫu lọc bảo thủ |55|12|55|12|

Bản 885 mẫu có CER greedy **5,88%**, beam **5,35%**, so với parent giới hạn vocab **13,90%** / **12,83%**. Bản 487 mẫu có CER **6,42%** ở cả hai decoder. Phép thử beam được đề xuất trong giai đoạn phát triển sau khi đã thấy kết quả greedy, không phải kiểm thử mù trên dữ liệu mới.

Đối chứng full-vocab parent ban đầu chỉ 19/65, full-vocab recurrent lượt trước 44/65. Riêng thao tác giới hạn vocab đã đưa parent lên 44/65 mà không cập nhật trọng số. **Không gọi phần 19→44 này là thành quả huấn luyện của lượt hiện tại.** Lợi ích train hiện tại phải so với đối chứng 13 lớp: greedy44→55 hoặc beam45→56. VAL đã dùng chọn checkpoint và nhiều lượt phát triển, không phải test cuối độc lập hay độ chính xác toàn app.

## Kiểm tra crop số cũ

16 crop DEV cũ có nhãn phù hợp `[+-]?[0-9]+`, gồm 11 crop tử/mẫu. Chỉ mở pixel sau khi cả hai checkpoint đã chốt; không dùng để chọn epoch.

| Model / decoder | Đúng /16 | Lỗi ký tự /26 | Tử/mẫu đúng /11 |
|---|---:|---:|---:|
| Parent giới hạn vocab / greedy |12|4|7|
| Parent giới hạn vocab / beam |13|3|8|
| Train885 / greedy |13|3|8|
| Train885 / beam |13|3|8|
| Train487 / greedy |12|4|7|
| Train487 / beam |13|3|8|

**Cả hai ứng viên nhầm `22 → 21`**, ID `1-bFkCGeM1qu1TFLPZlhv31AyAy0fsXJS:math-review-20261013-extra-fraction-3`; parent đọc đúng. Vì vậy điểm tổng tăng không đủ để vượt kiểm tra hồi quy. Beam vẫn giữ lỗi này; không lấy phương án `22` trong top5 chỉ vì biết đáp án tham chiếu.

Nhóm nhiều số0 ở VAL mới có 2 crop và DEV số cũ chỉ có 1 crop; chúng được giữ đúng nhưng quá ít để kết luận về số0 nói chung. Model này đọc crop số/tử/mẫu; chưa đo ghép phân số2D hoặc tự phát hiện vùng từ ảnh trang. Phạm vi numeric được xác định trong benchmark, không phải một bộ định tuyến tự động đã triển khai. Có một output không khớp đầy đủ grammar số trong mỗi bản trên VAL, dù mọi ký tự đều thuộc vocab13; không được tự cắt/bỏ dấu để coi là đúng.

## Dữ liệu, cách ly và huấn luyện

- Đã áp dụng thật danh sách 17 crop cần rà của lượt trước: **749−17=732 HUMAN TRAIN mới**, nhãn giữ nguyên provenance được cung cấp. Không coi mọi nhãn `HUMAN_VERIFIED` là giáo viên xác nhận độc lập.
- Thêm **153 TRAIN cũ** có nhãn số ASCII hợp lệ, trong đó 58 crop tử/mẫu. Không đưa prose vào model số; **không tuyên bố đã train thêm chữ tiếng Việt trong lượt này**. Model chữ cũ không bị cập nhật cùng trọng số số.
- Hai tập: 732+153=885 mẫu; hoặc 334+153=487 mẫu. Bộ334 chỉ lọc theo heuristic TRAIN-only đã chốt: dải biên mực ≥2%, nhiều dải mực ngang, gần rỗng hoặc tương phản thấp. Đây là lọc bảo thủ, không chứng minh mọi mẫu còn lại sạch hoặc mẫu bị loại sai nhãn.
- Cùng12epoch nhưng số bước tối ưu khác nhau: 1.332 bước cho885 và732 bước cho487. Không quy chênh lệch điểm hoàn toàn cho chất lượng dữ liệu.
- Vocab13: blank, `+`, `-`, `0..9`. Copy chính xác từng hàng FC từ parent theo token; kiểm tra **950/950 mẫu TRAIN/VAL** cho đầu ra reduced-head chưa train giống restricted-logit greedy của parent. Leading zeros giữ dạng chuỗi, không chuyển sang số nguyên.
- CNN giữ nguyên. Train BiLSTM LR`2e-6` và head LR`5e-5`, batch8, seed`2026102403`; CTC supervised, KL2 trên141TRAIN numeric parent đọc đúng. Trọng số dữ liệu cũ3, tử/mẫu4, chuỗi nhiều số0 có trọng số4 theo thứ tự điều kiện trong code. Không dùng pseudo label, không dùng synthetic.
- Mỗi checkpoint chọn epoch12 theo ít lỗi ký tự rồi số vùng đúng trên65VAL. Chốt hai file và hash trước16DEV. Thời gian train thực tế **161,56 giây CPU**; phép thử beam thêm9,61giây, không có training trong bước beam.

## Tìm lại ảnh gốc để sửa crop

Đã tra 256source SHA HUMAN TRAIN với83.733mapping hiện có: không trùng. ZIP arithmetic có crop và metadata trang gốc nhưng thiếu ảnh gốc/bbox của các crop được chấp nhận. Thư mục nguồn ghi trong handoff `D:\nhom6\train thử\combined_dataset_fixed_v1.0\` hiện không có; các đường dẫn D:/E: tương ứng đã kiểm tra cũng không có.

Kiểm tra central directory của hai ZIP Drive `dataset_clean_full.zip` / `dataset_clean_filtered_20261004.zip` (3.188/3.184entry) cũng không có tên `hme_*`/`combined_dataset`. Phạm vi tìm kiếm này gồm các inventory và thư mục liên quan đã biết, không phải khẳng định đã duyệt mọi nơi trên Drive.

Chưa thể phục hồi nét bị cắt. Đã cách ly thay vì tạo nét mới hoặc thêm viền rồi coi là sửa. Nguồn cần đối chiếu là `combined_dataset_fixed_v1.0/images/train/hme_*.png` cùng nhãn nguồn; ví dụ `hme_117` cần khớp SHA `07f36c61eea40ef8352e4aeb0276beb21ca4aebde35bd8fb4fb2e96187b734fc`, kích thước1301×1161. Không gửi tin nhắn cho teammate hay thay file Drive.

## Kiểm chứng và trạng thái

- Self-check CTC/packed lengths/split/quarantine và leading zeros đạt. Loss/gradient hữu hạn. Hai checkpoint nạp lại đúng, mọi tensor hữu hạn, CNN không đổi.
- Tiến trình Python mới đọc lại65VAL, xác minh byte SHA/kích thước và tái lập chính xác bốn baseline cùng cả hai ứng viên; tính lại16DEV từ dự đoán đã lưu.
- Kiểm tra riêng decoder với các đường CTC `22` có blank phân cách, ký tự lặp liền nhau và `001`; dùng decoder có sẵn, không thêm thư viện hoặc luật sửa theo đáp án.
- 56 hash input train và 61 hash của phép thử decoder không đổi; các màn hình được bảo vệ không đổi. Trọng số OCR production vẫn SHA `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.
- Tiến trình riêng tái lập mọi chuỗi greedy/beam và cả top5 giả thuyết của parent + bản885 trên65VAL. Năm kiểm tra ký tự lặp/số0/dấu và vét cạn27đườngCTC nhỏ xác nhận phép cộng xác suất prefix. Bằng chứng ở `decoder_verification.json`.
- Không đọc pixel TEST/HOLDOUT, không ghi ảnh nguồn ra đĩa, không thay runtime, không commit/push.

`release_gate.json` tiếp tục chặn cả hai ứng viên. Tất cả split nguồn số được đánh dấu YOLO-seen, thiếu writer identity và chưa rõ trùng tiền huấn luyện; chưa có kiểm thử độc lập theo người viết. Vocab13 không thể thay trực tiếp file model chữ đầy đủ. Các checkpoint hiện dùng cho nghiên cứu và đánh giá riêng vùng số.

## Tệp tái lập

Trong `ai-training/datasets/drive_math/math_numeric_specialist_20261024/`:

- `train_numeric.py`, `policy.json`, `vocab.json`, `train.log`, `frozen_candidates.json`.
- `all_quarantined.pth` (tên nội bộ chỉ **tập đã loại17mẫu**, không có nghĩa train trên mẫu cách ly), `conservative_quality.pth`.
- `result.json`, `verification.json`, `release_gate.json`, `final_integrity.json`.
- `evaluate_decoder.py`, `decoder_policy.json`, `frozen_val_decoder_outputs.json`, `decoder_result.json`, `decoder_verification.json`.
- `source_recovery_audit.json`: bằng chứng tìm nguồn, không chứa ảnh.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Công cụ Python huấn luyện/đánh giá OCR; không có skill OCR chuyên biệt trong registry.
  - Applied to: Tái sử dụng reader RAM-only, CRNN/CTC, metrics, beam decoder có sẵn; giữ thử nghiệm riêng, không thêm dependency hoặc sửa kiến trúc app.
