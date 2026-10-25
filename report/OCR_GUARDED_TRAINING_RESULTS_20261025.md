# OCR chữ và toán — thực hiện kế hoạch giữ từng dòng đúng, 25/10/2026

**Đã lập kế hoạch và thực hiện thêm 6 thử nghiệm neural, tổng 160 epoch theo lịch cập nhật cố định.** Có ứng viên chữ ổn định hơn: giữ được dòng `cá dữ` mà vòng trước làm sai, tăng old-held từ 13 lên14/22 dòng đúng và giảm DEV105→104 lỗi. Hai thử nghiệm số chưa qua guard chặt hơn, nên không nhận weights cập nhật của chúng. **Chưa đạt điều kiện thay model trong app.**

Vòng mới: `ai-training/datasets/drive_math/math_guarded_training_20261025`. [Kế hoạch đã triển khai](OCR_NEXT_TRAINING_PLAN_20261025.md); [kết quả vòng trước](OCR_REFINEMENT_20261025.md). Không gộp số epoch giữa các vòng để suy ra chất lượng và không sửa bằng chứng vòng trước.

## Kết quả bản chữ được chọn

Lựa chọn đã đóng băng trước DEV/chẩn đoán là `text_accent_low`, epoch27. `accent_high` epoch10 có cùng key VAL nhưng không được đổi lên chỉ vì xem chẩn đoán; thứ tự ưu tiên đã chốt trước. Cả hai dùng head321, chỉ cập nhật **163 hàng nguyên âm/chữ hoa** theo quy tắc bảng chữ cái và giữ **158 hàng còn lại** cùng toàn bộ CNN/RNN giống parent từng tensor.

| Tập đánh giá, greedy | Parent gốc | Bản chữ vòng trước | Bản nguyên âm/chữ hoa mới |
|---|---:|---:|---:|
| Old-held22, toàn bộ | 13/22 đúng;15/255 lỗi | 13/22;14/255 | **14/22;13/255** |
| Trong đó14 dòng prose | 9/14;9/187 | 9/14;8/187 | **10/14;7/187** |
| VAL mới39 vùng | 16/39;45/328 | 17/39;42/328 | 17/39;42/328 |
| Trong đó10 dòng prose | 2/10;23/197 | 3/10;20/197 | 3/10;20/197 |
| DEV cũ95 vùng | 53/95;105/1.097 | 53/95;105/1.097 | **53/95;104/1.097** |
| Trong đó22 dòng prose | 9/22;29/494 | 9/22;29/494 | **9/22;28/494** |
| Bốn trang chẩn đoán92 vùng | 59/92;52/252 | 59/92;52/252 | 59/92;52/252 |
| Trong đó6 dòng prose | 2/6;22/122 | 2/6;22/122 | 2/6;22/122 |

Điểm cải thiện là **giữ chất lượng từng dòng**, không phải tăng mạnh khả năng đọc chữ. Bản mới vừa giữ `che ô, cá dữ, lá khô.` đúng, vừa sửa được `bé có có` thành `bé có cỏ`; bản trước làm sai dòng thứ nhất để sửa dòng thứ hai. Một cải thiện VAL khác là `Boán:`→`Toán:`.

Trên old22, new39, DEV95 và diagnostic92, không mất thêm **dòng đang đọc đúng hoàn toàn**, chuỗi số/dấu toán đang đúng hoặc chữ ký đơn vị đang đúng so với cả parent gốc lẫn bản chữ trước. Đây là quan sát trên những tập này; đóng băng hàng số không bảo đảm mọi ảnh tương lai được đọc đúng vì logits chữ vẫn cạnh tranh.

Các dòng vốn sai vẫn còn sai, và có chỗ đổi sai khác. Ví dụ `Lời giải bài toán` được đọc từ `Lời giải bài toăn` thành `Lơi giải bài toăn`; lỗi đơn vị học sinh viết `15 ×3=45(dm)` vẫn bị đọc thành `(cm)`. Vì vậy không gọi bản mới là “không có hồi quy ở mọi ký tự” hay “đọc hoàn hảo”. Không sửa nhãn OCR theo đáp án toán. [Toàn bộ thay đổi và mất dòng/số/đơn vị](ocr-guarded-training-20261025/literal-regressions.json).

## Phần số: hai thử nghiệm cập nhật bị loại

TRAIN-only audit cho thấy bản số trước đọc đúng225/225 vùng vở cũ; còn11 lỗi trong58 vùng mới. Ví dụ TRAIN `200`→`00`, `000`→`100/006`, `2026`→`20216`. Chúng đủ chiều dài CTC; không phải lỗi “target không có đường đi CTC”. Chỉ các dữ kiện TRAIN này tham gia hard pool/teacher, không đưa DEV hay trang chẩn đoán vào train.

Thử nghiệm `numeric_replay` giữ CNN, cập nhật RNN/head từ bản số tốt nhất. `original_replay` bắt đầu từ original full321 rút head13. Hai teacher chỉ dùng KL khi bản đọc TRAIN trùng ground truth; trường hợp teacher sai không được giữ như nhãn thật. Guard bảo vệ **59/65 vùng oldVAL trong hợp các đối chứng** và **19/22 vùng newVAL hiện đúng**, đồng thời giữ giới hạn lỗi tổng.

- `numeric_replay`: chạy đủ20×240 updates; newVAL giữ19/22, nhưng không giữ được một vùng oldVAL mà original đọc đúng. Chọn epoch0, guard=false; không nhận weights cập nhật.
- `original_replay`: chạy đủ20×240 updates; epoch cuối newVAL18/22 và còn mất các vùng đối chứng đúng. Chọn epoch0, guard=false; không gọi việc giữ original là cải thiện.

Không chọn lại epoch bằng DEV hoặc chẩn đoán để né guard. Bản số tốt nhất vòng trước vẫn là bằng chứng phát triển tốt hơn: **19/22 newVAL,76/86 vùng số chẩn đoán,26/31 cặp phân số crop thủ công và22/31 cặp đọc đúng từ57 đề xuất tự động cố định**. Nó vẫn có lỗi `22`→`21` so với original và chưa đạt ngưỡng phát hành.

## Các lượt train thực sự và dữ liệu

| Thử nghiệm | Epoch×updates | TRAIN | Coverage cuối lượt | Epoch chọn | Guard |
|---|---:|---:|---:|---:|---|
| Numeric replay, CNN cố định | 20×240 | 1.459 | 1.459/1.459 | 0 | Không đạt |
| Original numeric replay, cập nhật CNN/RNN/head | 20×240 | 1.459 | 1.459/1.459 | 0 | Không đạt |
| Head chữ, LR1e-5/KL2 | 30×100 | 677 | 677/677 | 0 | Không đạt |
| Head chữ, LR1e-5/KL8 | 30×100 | 677 | 677/677 | 0 | Không đạt |
| Nguyên âm/chữ hoa, LR1e-5/KL2 | 30×100 | 677 | 677/677 | **27** | Đạt guard VAL |
| Nguyên âm/chữ hoa, LR3e-5/KL2 | 30×100 | 677 | 677/677 | **10** | Đạt guard VAL |

Hai lượt head chữ đầu tiếp tục làm sai `cá dữ`; retention mạnh hơn không tự giải quyết được. Sau đó thử mask theo ngôn ngữ: với một ký tự alphabetic, chỉ cập nhật chữ hoa hoặc ký tự có gốc NFD trong `aeiouy`, loại x/X. Quy tắc bao phủ nguyên âm tiếng Việt có/không dấu; không lập danh sách ký tự riêng từ lỗi của một ảnh VAL.

**160 epoch là số lịch cập nhật cố định, không phải160 lượt đi qua toàn bộ corpus.** Numeric dùng hàng đợi nguồn xuyên epoch, cuối lượt thăm đủ283 vùng số vở,170 dòng HME và1.006 glyph. Mỗi lượt chữ cuối cùng thăm đủ677 TRAIN từ68 nguồn, bao gồm479/479 replay cũ. Coverage cuối lượt không đồng nghĩa coverage tại epoch chọn; chi tiết được giữ trong log.

Dùng lại dữ liệu đã chốt: không tạo thêm nhãn bằng dự đoán hoặc phép tính. 1.459 số TRAIN gồm283 vùng vở đã rà và1.176 vùng HME/glyph có provenance/exclusion từ ảnh TRAIN gốc. 677 fulltext TRAIN giữ cùng source/split/vocab. SourceSHA TRAIN không trùng các tập giữ lại đã biết; người viết và trùng dữ liệu tiền huấn luyện vẫn UNKNOWN. Nhãn mới của các vòng trước chưa có giáo viên xác nhận độc lập.

Ba tiến trình GPU báo thời gian lần lượt794,26s,156,97s và159,95s, tổng **1.111,18s**, gồm tải/kiểm nguồn và chuẩn bị trong từng tiến trình. Đây không phải wall time toàn bộ công việc hoặc benchmark tốc độ thuần GPU. Môi trường thử nghiệm CUDA tách riêng; runtime app vẫn dùngtorch2.14.0+cpu.

## Kiểm tra, lỗi báo cáo và khôi phục bằng chứng

- Numeric3 test, evaluator5 test, text/v2 gồm8 test, accent/case gồm10 test và completion2 test đều đạt: **28 lượt thực thi test**, có test kế thừa lặp giữa hai suite chữ; không tuyên bố28 ca độc lập. Kiểm thử tổng hợp không thay thế đo OCR trên ảnh thật.
- Đã nạp lại **12 cấu hình:6 trial và6 đối chứng**, tính toàn bộ CNN từ pixel đã kiểm SHA trên CPU. Metric dictionary và transcript được tái lập; cả6 đối chứng tái lập điểm chất lượng đã ghi ở vòng trước. Thứ tự/recipe được đóng băng bằng VAL trước khi đọc DEV/chẩn đoán.
- Có lỗi thật ở bước tổng hợp: engine đã lưu `result.json`, sau đó adapter cố lưu đè bằng helper chỉ cho phép tạo mới. Suy luận đã hoàn tất, nhưng tiến trình kết thúc lỗi `Preserve frozen evidence`; log lỗi, rawresult, gate và policy được giữ nguyên. Không báo tiến trình gốc đã thành công.
- Tạo bước completion riêng với policy/hash riêng, chỉ đọc JSON transcript đã lưu, tái tính và đối chiếu đúng audit literal cũ, giữ nguyên lựa chọn checkpoint. Ghi **audited_result.json/audited_release_gate.json** sang đường dẫn mới; không mở lại ảnh, không train lại và không sửa rawfailure. [Lỗi gốc](ocr-guarded-training-20261025/original-finalization-failure.json), [policy completion](ocr-guarded-training-20261025/completion-policy.json).
- Verifier cuối kiểm **5 policy hash riêng trước khi gộp**,6 checkpoint/shape/finite/epoch0/mask, lịch160epoch, các file history,12 roundtrip và6 control. Kiểm cả trạng thái33 file tracked vốn đã thay đổi trong workspace,5 file UI được bảo vệ và model production: tất cả giữ nguyên. [Final integrity](ocr-guarded-training-20261025/final-integrity.json).
- Không ghi ảnh/crop/ZIP/Parquet vào thí nghiệm, không đọc pixel TEST/HOLDOUT, không commit/push hoặc thay model app. Policy chữ đầu tiên chưa dispatch được giữ và không tính là trial. Model production vẫn SHA`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.

## Hướng model khác đã kiểm tra

Đã rà metadata các gói thực tế trong Drive. Gói handoff chứa cùng checkpoint production; gói arithmetic là dataset, không có một model toán mới ẩn trong đó. Đánh giá này không phải tìm toàn bộ Drive hoặc chứng minh nhãn mọi file đều đúng.

Chuẩn bị đối chứng VietOCR seq2seq trong môi trường riêng, pin config/commit upstream và xác minh đúngtorchCUDA hiện có. Server chính thức trảHEAD200, nhưng GET weights bị timeout sau **1.048.576/89.575.371byte**. Giữ partialfile và lỗi; chưa có checkpoint đầy đủ, chưa chạy inference, smoke test, benchmark hay train VietOCR. Không lấy việc cài package làm bằng chứng chất lượng. [Trạng thái chuẩn bị](../ai-training/datasets/drive_math/math_guarded_training_20261025/shadow_vietocr/PREPARATION_STATUS.md).

## Trạng thái và phần cần làm tiếp

**NOT_READY_FOR_PRODUCTION.** Ứng viên chữ mới cải thiện độ ổn định, nhưng prose VAL vẫn **3/10 dòng đúng, CER10,15%**, cách xa ngưỡng ≥95% exact/CER≤2%. Numeric chưa có ứng viên cập nhật qua guard; head13 cũng không thay được toàn tuyến chữ và bố cục phân số2D.

Hướng tiếp theo theo kế hoạch là baseline pretrained khác trong môi trường tách riêng sau khi lấy đủ weights, rồi fine-tune có kiểm soát trên nhãn chữ có dấu/nét mảnh và dữ liệu số dài/số lặp thật. Cần nhãn toàn trang đầy đủ để chấm detector/fractionlayout và acceptance tách người viết có xác nhận nhãn; các trang đã dùng nhiều vòng hiện chỉ là development. Tăng epoch lặp lại trên cùng dữ liệu không đủ cơ sở để cam kết đạt95% hoặc “hoàn hảo”.

Ứng viên chữ được lưu để tiếp tục đánh giá: `ai-training/datasets/drive_math/math_guarded_training_20261025/text/accent_case/accent_low/candidate.pth`. Nó chưa được tích hợp vào app.

## Bằng chứng gọn

- [Kết quả12 cấu hình và6 trial](ocr-guarded-training-20261025/results.json)
- [Lựa chọn VAL đóng băng](ocr-guarded-training-20261025/frozen-choice.json)
- [Transcript/số/dấu/đơn vị thay đổi](ocr-guarded-training-20261025/literal-regressions.json)
- [Release gate](ocr-guarded-training-20261025/release-gate.json), [integrity](ocr-guarded-training-20261025/final-integrity.json), [lỗi tải weights](ocr-guarded-training-20261025/vietocr-download-failure.json)

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Minimal controlled Python OCR experiments, source/held boundaries and checkpoint validation.
  - Applied to: Reuse existing verified loaders/CRNN, test bounded hypotheses, keep frozen evidence, independently audit literal regressions and avoid runtime/UI changes.
