# OCR chữ và toán — kết quả cải thiện 25/10/2026

**Đã chạy thêm 5 thử nghiệm neural, tổng 68 epoch theo lịch cập nhật cố định. Có cải thiện đo được; chưa đạt điều kiện thay model trong app.** Bản số được chọn bằng VAL tăng từ 18 lên 19/22 vùng vở mới và từ 74 lên 76/86 vùng số trên cùng bốn trang chẩn đoán. Bản chữ giảm lỗi trên VAL mà không làm tăng lỗi số/dấu toán trong các tập vừa kiểm tra, nhưng vẫn có một hồi quy chữ cần giải quyết.

Vòng này nằm tại `ai-training/datasets/drive_math/math_refinement_20261024`, bắt đầu ngày 24 và hoàn tất ngày 25/10. Không ghi đè kết quả các vòng trước. [Kế hoạch và ngưỡng thay model](OCR_TRAINING_PLAN_20261024.md) được giữ nguyên.

## Số và phân số

Đối chứng là `full_visual.pth` của vòng trước. Cùng crop, min32, CNN tính lại từ pixel và greedy CTC; beam15/top5 được báo riêng, không chọn lại decoder theo trang chẩn đoán.

| Phạm vi | Đối chứng | `base_balanced_all`, epoch 8 | Lỗi ký tự trước → sau |
|---|---:|---:|---:|
| VAL cũ, 65 vùng | 58/65 | 58/65 | 9 → 8 / 187 |
| VAL vở mới, 22 vùng số nguyên | 18/22 | **19/22** | 4 → 3 / 63 |
| DEV số cũ, 16 vùng | 13/16 | 13/16 | 3 → 3 / 26 |
| Bốn trang chẩn đoán, 86 vùng số | 74/86 | **76/86** | 12 → 10 / 130 |
| Cặp tử–mẫu từ crop thủ công | 26/31 | 26/31 | Đúng cả hai tầng |
| Đúng nội dung phân số từ 57 đề xuất tự động cố định | 21/31 | **22/31** | Hình học detector giữ nguyên |

Một lỗi VAL được sửa đúng là `37872`, trước bị đọc thành `32872`. Không mất thêm vùng đúng so với warm start trên old65, new22, DEV16 và diagnostic86; kiểm riêng từng transcript, không chỉ tổng điểm.

**Vẫn còn hồi quy `22 → 21` so với parent full321 rút head13 ban đầu**; warm start gần nhất vốn đã sai vùng này. Hai vùng `13` ở DEV vẫn bị đọc thành `3`. Không dùng tổng điểm bằng nhau để tuyên bố đã hết hồi quy.

Ứng viên `expanded_balanced_correct` có 58 số nguyên TRAIN mới đạt **28/31 cặp crop thủ công**, nhưng VAL chỉ 18/22. Đây là kết quả chẩn đoán của một ứng viên khác; không thay lựa chọn `base_balanced_all` để lấy điểm phân số đẹp hơn. Bản `base_balanced_correct` đạt 19/22 VAL, 75/86 chẩn đoán, 26/31 crop thủ công, 21/31 phân số tự động.

Tất cả dùng cùng 57 đề xuất và ghép duy nhất theo hình học với IoU tối thiểu 0,5 cho cả tử và mẫu. Tìm được 26/31 cặp chú thích; chỉ nội dung recognizer thay đổi. Chú thích trang còn một phần, nên **precision chưa xác định**, không phải phép đo đọc đúng toàn trang hoặc phát hiện mọi phân số.

## Chữ tiếng Việt và giữ nội dung toán

`letter_head`, epoch 8, chỉ cập nhật 207 hàng ký tự chữ của lớp cuối; giữ nguyên CNN, RNN và 114 hàng còn lại, gồm blank/số/dấu toán và x/X. Giữ logits số không bảo đảm giữ bản đọc vì logits chữ vẫn cạnh tranh; do đó vẫn chạy hồi quy trên ảnh thật.

| Phạm vi full321, greedy | Parent | `letter_head` |
|---|---:|---:|
| VAL mới, 39 vùng | 16/39 đúng; 45/328 lỗi | **17/39 đúng; 42/328 lỗi** |
| Trong đó 10 dòng prose | 2/10 đúng; 23/197 lỗi | **3/10 đúng; 20/197 lỗi** |
| Tập giữ chất lượng cũ, 22 vùng | 13/22 đúng; 15/255 lỗi | 13/22 đúng; 14/255 lỗi |
| Trong đó 14 dòng prose | 9/14 đúng; 9/187 lỗi | 9/14 đúng; 8/187 lỗi |
| DEV cũ, toàn bộ 95 vùng | 53/95 đúng; 105/1.097 lỗi | 53/95 đúng; 105/1.097 lỗi |
| DEV cũ, 22 dòng prose | 9/22 đúng; 29/494 lỗi | 9/22 đúng; 29/494 lỗi |
| Bốn trang chẩn đoán, toàn bộ 92 vùng | 59/92 đúng; 52/252 lỗi | 59/92 đúng; 52/252 lỗi |
| Chẩn đoán, 6 dòng prose | 2/6 đúng; 22/122 lỗi | 2/6 đúng; 22/122 lỗi |

Không phát sinh thêm hồi quy **chữ số/dấu toán** so với parent trên oldheld22, new39, DEV95 và diagnostic92. Các lỗi mất số 0 từng xuất hiện ở lượt prose trước không xuất hiện thêm trong ứng viên này.

Tuy nhiên, kiểm từng dòng cho thấy **một dòng cũ đang đúng bị làm sai**: `che ô, cá dữ, lá khô.` → `che ô, cá cữ, lá khô.`. Đồng thời sửa được `bé có có` → `bé có cỏ`, nên tổng exact vẫn bằng 13/22. Guard hiện tại giữ critical signature và tổng điểm; nó không bảo vệ mọi chữ trong từng dòng. Vì vậy không gọi bản này là “không hồi quy”. Các transcript thay đổi, cả tốt và xấu, đều có trong [regression-review.json](ocr-refinement-20261025/regression-review.json).

Nhãn lỗi đơn vị của học sinh `15 × 3 = 45 (dm)` được giữ nguyên; model vẫn đọc sai thành `(cm)`. Không đổi ground truth theo đáp án toán để làm đẹp điểm OCR. Độ chính xác chữ hiện vẫn thấp, nhất là dấu và nét mảnh.

## Dữ liệu và cách train đã thực hiện

- Chốt metadata/hash 6 trang TRAIN mới trước khi xem ảnh hoặc dự đoán; nguồn không trùng SHA trang TRAIN/DEV/VAL/TEST/HOLDOUT và các trang chẩn đoán đã biết.
- Từ 96 vùng nháp, loại 13 vùng mơ hồ/lẫn nét; rà trực tiếp ảnh và crop hai lượt, chốt **83 vùng: 23 prose, 58 số nguyên, 2 số thập phân**. Không bỏ dấu phẩy để ép số thập phân vào head13. Giữ số 0 đầu và lỗi học sinh viết; không tạo nhãn từ model hay phép tính.
- Các cờ triage lịch sử trong metadata nguồn vẫn giữ nguyên. Quyết định đủ điều kiện nằm ở chú thích crop đã rà bởi Codex; **chưa có xác nhận nhãn độc lập của giáo viên**. Tách trang không chứng minh tách người viết hoặc tách dữ liệu tiền huấn luyện; cả hai vẫn UNKNOWN.
- Batch số cân bằng nguồn/vai trò: 4 vùng vở, 2 dòng HME, 1 glyph và 1 mẫu khó TRAIN. Hard pool dựa trên lỗi TRAIN, số 0 và chữ số lặp, không lấy lỗi DEV/VAL làm dữ liệu train.
- So sánh giữ KL trên mọi teacher và chỉ teacher đọc đúng, chuẩn hóa KL theo cả batch. Teacher sai không trở thành nhãn thật; CTC luôn dùng transcript gốc.
- CNN chỉ batch ảnh cùng kích thước; packed RNN và decoder dùng độ dài thật, tránh padding thành chữ số. Khi cập nhật CNN, tính lại mọi tầng từ pixel. Lượt chỉ cập nhật head dùng feature RNN đóng băng trong RAM, có kiểm logit/CTC path trùng forward gốc.

| Thử nghiệm | Epoch × updates | TRAIN đủ điều kiện | Số vùng đã tham gia cuối lượt | Epoch chọn |
|---|---:|---:|---:|---:|
| `base_balanced_all` | 12 × 176 | 1.401 | 1.261, từ 280 nguồn | 8 |
| `base_balanced_correct` | 12 × 176 | 1.401 | 1.261, từ 280 nguồn | 2 |
| `expanded_balanced_correct` | 12 × 176 | 1.459 | 1.315, từ 286 nguồn | 1 |
| `joint_text_gpu` | 12 × 100 | 677 | 671, từ 68 nguồn; replay cũ 475/479 | **0 — từ chối cập nhật** |
| `letter_head` | 20 × 100 | 677 | 677, từ 68 nguồn; replay cũ 479/479 | 8 |

**68 epoch ở đây là lịch số bước cố định, không phải 68 lượt đi qua toàn bộ corpus.** Các vùng chưa tham gia được log rõ; không tuyên bố full replay cho lượt joint. Joint full321 cải thiện một số điểm VAL nhưng không qua guard cũ, nên checkpoint chọn epoch0 giống parent từng tensor. Numeric expanded chạy đủ 12 epoch; các epoch sau có VAL mới tốt hơn nhưng làm hỏng guard cũ đã bị loại.

Hai trial số đầu chạy CPU. Ba trial tiếp chạy RTX 4060 Laptop trong môi trường CUDA tách riêng, có smoke test CRNN/CTC backward thật; runtime app vẫn `torch 2.14.0+cpu`. cuDNN yêu cầu RNN của learner ở train mode để backward; bản GPU ghi rõ và kiểm RNN một tầng/dropout0, các tầng còn lại giữ cùng chế độ. Lần dispatch hỏng trước train được giữ log, không tính là trial/epoch.

Tổng thời gian bốn tiến trình train báo là **1.816,06 giây**, gồm đọc nguồn/chuẩn bị; tiến trình đầu chứa hai recipe. Đây không phải wall time toàn bộ công việc, thời gian cài môi trường hoặc benchmark CPU/GPU tương đương.

## Kiểm chứng và tính toàn vẹn

- **19/19 unit test đạt**: độ dài CNN/RNN/CTC, số lặp, teacher sai, source/split boundary, sampling, guard, coverage, mask hàng head và feature replay. Test tổng hợp không phải bằng chứng chất lượng OCR ảnh học sinh.
- Evaluator self-check đạt, gồm phát hiện hash gốc sai và hash trùng nhưng mâu thuẫn. Kiểm từng policy riêng trước khi gộp để không che một file đã đổi.
- Đóng băng model, decoder và thứ tự chọn bằng VAL **trước khi đọc trang chẩn đoán**. Cùng điểm số ưu tiên base-all rồi base-correct rồi expanded; không chọn theo 28/31 crop phân số.
- **7/7 cấu hình checkpoint/đối chứng** được nạp lại và tái lập điểm VAL trên CPU từ pixel đã kiểm SHA; fulltext phải trùng cả transcript đã chọn. Đối chứng DEV105 lỗi và chẩn đoán số74/86, phân số26/31 +21/31 đều tái lập.
- Kiểm cuối đạt: 5 policy, checkpoint hash/shape/finite, epoch0 tensor-identical, 83 nhãn đóng băng, 5 file UI được bảo vệ và SHA model production giữ nguyên. [final-integrity.json](ocr-refinement-20261025/final-integrity.json)
- Không lưu ảnh nguồn/crop/ZIP/Parquet vào thí nghiệm; không mở pixel TEST/HOLDOUT; không đổi runtime hoặc giao diện, không commit/push. Model production vẫn SHA `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.

## Điều kiện còn thiếu để thay model

Kết luận phát hành: **NOT_READY_FOR_PRODUCTION**. Numeric VAL mới đạt 86,36% exact, CER4,76%; chẩn đoán 88,37%, CER7,69%. Prose VAL đạt 30% exact, CER10,15%. Chưa đạt ngưỡng ≥95% exact, CER≤2%, đồng thời còn lỗi `22 → 21`, đơn vị và một dòng prose cũ bị thay chữ.

Các tập này đã được dùng nhiều vòng để phát triển, không phải acceptance độc lập. Chưa có tập xác nhận tách người viết/nguồn tiền huấn luyện và chưa có nhãn toàn trang đầy đủ để chấm precision/layout. Head13 cũng không nhận chữ, dấu phẩy hay tự phân tích bố cục phân số 2D; không thể thay nguyên tuyến OCR Student chỉ bằng checkpoint số.

Bước tiếp theo cần đo riêng: giữ từng dòng cũ đang đúng, thay vì chỉ tổng điểm; bổ sung TRAIN đã rà cho chữ có dấu/nét mảnh, số lặp/số 0 và đơn vị; hoàn thiện nhãn toàn trang và tập acceptance độc lập. Không dùng những lỗi DEV/chẩn đoán hiện tại làm nhãn TRAIN hoặc chọn lại checkpoint dựa trên chúng.

## Bằng chứng

- [Kết quả gọn của 7 cấu hình, dữ liệu và 5 trial](ocr-refinement-20261025/results.json)
- [Lựa chọn VAL đã đóng băng](ocr-refinement-20261025/frozen-choice.json)
- [So từng transcript, hồi quy chữ và số](ocr-refinement-20261025/regression-review.json)
- [Release gate](ocr-refinement-20261025/release-gate.json), [kiểm tra kỹ thuật](ocr-refinement-20261025/checks.json), [môi trường GPU](ocr-refinement-20261025/gpu-environment.json)
- Checkpoint số: `ai-training/datasets/drive_math/math_refinement_20261024/numeric_base/balanced_all.pth`.
- Checkpoint chữ: `ai-training/datasets/drive_math/math_refinement_20261024/letter_head/candidate.pth`.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Python OCR training, loss/sampling audit, checkpoint validation and minimal reuse of the existing CRNN pipeline.
  - Applied to: Source-balanced batches, true-width forward/CTC, selective KL, constrained head updates and independent evaluation without changing the app or adding a new training framework.
