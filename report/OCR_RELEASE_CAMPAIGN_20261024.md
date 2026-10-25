# OCR chữ, số và phân số — vòng huấn luyện 24/10/2026

**Đã thực hiện kế hoạch, bổ sung dữ liệu vở thật và chạy thêm 8 thử nghiệm neural, tổng 98 epoch. Chưa đạt điều kiện thay model trong ứng dụng.** Bản số cập nhật toàn bộ CNN cải thiện trên cùng bốn trang chẩn đoán: 70 → 74/86 vùng số và 21 → 26/31 cặp tử–mẫu đúng. Phần chữ chỉ cải thiện nhẹ trên VAL mới và vẫn có hồi quy mất số 0, nên bị loại khỏi phát hành.

Đây là kết quả offline của vòng mới `math_release_campaign_20261024`, tách khỏi 11 thử nghiệm/196 epoch đã báo cáo ở vòng trước. Không cộng hai nhóm thành một phép đo chất lượng; không ghi đè kết quả cũ. [Kế hoạch và điều kiện thay model](OCR_TRAINING_PLAN_20261024.md) đã được chốt trước triển khai.

## Kết quả số và phân số

Đối chứng trong bảng là `domain_numeric.pth` của vòng trước, **cùng preprocessing aspect_min32, cùng crop, cùng greedy CTC** với ứng viên `full_visual.pth`. Vì đổi preprocessing cũng ảnh hưởng điểm, không dùng 65/86 của cấu hình cũ min64 để quy toàn bộ cải thiện cho weights mới.

| Phạm vi | Đối chứng | Full CNN mới | Lỗi ký tự trước → sau |
|---|---:|---:|---:|
| VAL cũ, 65 crop | 58/65 | 58/65 | 8 → 9 / 187 |
| VAL vở mới, 22 vùng số nguyên | 17/22 | 18/22 | 6 → 4 / 63 |
| Bốn trang chẩn đoán, 86 vùng số | 70/86 | 74/86 | 16 → 12 / 130 |
| Cặp tử–mẫu từ crop thủ công | 21/31 | 26/31 | Chấm đúng cả hai tầng, giữ literal |

Với beam15/top5, VAL cũ giảm **59/65 → 58/65**, lỗi 7 → 8. VAL vở mới và chẩn đoán của full CNN vẫn lần lượt 18/22 và 74/86. Không chọn riêng decoder có điểm đẹp nhất trên chẩn đoán.

57 đề xuất phân số tự động được giữ nguyên tọa độ từ probe đã đóng băng. Với paired IoU ≥0,5 và ghép duy nhất chỉ bằng hình học, tìm được **26/31** cặp chú thích; đọc đúng **21/31**, so với 20/31 khi dùng numeric warm start min32. Đây là kết quả trên **chú thích một phần trang**: không biết toàn bộ phân số/negative trên ảnh nên chưa công bố precision hoặc độ chính xác đọc cả trang. Crop thủ công 26/31 cũng không chứng minh detector tự tìm được 26 cặp đúng nội dung.

Trên 16 DEV số cũ, ứng viên vẫn đúng 13/16. So với parent full321 được rút head13 ở cùng input, vẫn còn hồi quy **`22 → 21`**. Không gọi là “không hồi quy” chỉ vì đối chứng domain gần nhất đã mắc lỗi này hoặc tổng điểm 13/16 bằng nhau. Hai vùng `13` vẫn bị đọc thành `3`.

**Ứng viên số chưa đạt:** VAL vở mới 81,82% exact, CER 6,35%; chẩn đoán 86,05% exact, CER 9,23%. Ngưỡng trong kế hoạch là exact ≥95%, CER ≤2% và không hồi quy số/dấu quan trọng.

## Chữ tiếng Việt và giữ số trong biểu thức

| Phạm vi full321, greedy | Parent | Visual prose mới |
|---|---:|---:|
| VAL mới, 10 dòng prose / 197 ký tự | 2/10 đúng; 23 lỗi | 3/10 đúng; 20 lỗi |
| DEV cũ, 22 vùng prose / 494 ký tự | 9/22 đúng; 29 lỗi | 9/22 đúng; 29 lỗi |
| Chẩn đoán, 6 vùng prose / 122 ký tự | 2/6 đúng; 22 lỗi | 2/6 đúng; 23 lỗi |
| DEV cũ, toàn bộ 95 vùng / 1.097 ký tự | 53/95 đúng; 105 lỗi | 52/95 đúng; 109 lỗi |

CER trên prose VAL mới giảm 11,68% → 10,15%, nhưng chưa tổng quát tốt hơn trên các tập còn lại. Khi dùng full321 này thay recognizer tổng quát, ba vùng mà parent giữ đúng số/dấu bị làm sai:

- `9 × 0 = 0` → mất số 0 cuối.
- `300 cm² = 3 dm²` → `30 cm² = 3 dm²`.
- `650-150=500` → kết quả thành `00`.

Các head-only/recurrent prose cũng chọn được 20 lỗi trên cùng 10 dòng VAL mới nhưng làm DEV toàn bộ tăng lên 108/107 lỗi, và có hồi quy ở số 0. Vì vậy chưa có ứng viên chữ được phát hành. Metadata vai trò prose được hỗ trợ thủ công trong đánh giá; không giả định app tự phân loại vai trò đúng để né các hồi quy toán.

## Dữ liệu và ảnh vào đã làm

- Chốt 8 nguồn vở grade4/grade5 bằng metadata hash trước chú thích/dự đoán: **5 trang TRAIN, 3 trang VAL**. Loại nguồn thuộc tập đang dùng và bốn trang chẩn đoán trước khi chọn.
- Xem trực tiếp ảnh và crop trong RAM, sửa hình học crop/rectification trước suy luận. Từ 122 vùng nháp, loại 16 vùng viết đè, mất nét hoặc lẫn dòng; chốt **106 vùng: 67 TRAIN, 39 VAL**.
- 67 TRAIN mới gồm **23 prose, 2 expression, 12 numeric_field, 15 numerator, 15 denominator**. Chỉ 40 vùng đáp ứng head số nguyên. VAL có 10 prose, 3 expression và 26 numeric_field; chỉ 22 vùng số nguyên được đưa vào head13. Không cắt bỏ dấu phẩy để biến số thập phân thành nhãn số nguyên.
- Chốt **15 cặp phân số TRAIN**, giữ đúng từng tầng nhìn thấy; ví dụ `72 : 8/120 : 8` không được đổi thành `9/15` bằng suy luận đáp án.
- Giữ literal lỗi đơn vị học sinh viết ở VAL: `15 × 3 = 45 (dm)`, cùng số 0 đầu `07`. Đây là nhận diện chữ viết, không phải sửa bài toán trong nhãn OCR.
- Nguồn có các cờ triage lịch sử chưa xác minh; quyết định đủ điều kiện nằm ở **crop đã được Codex rà trực tiếp**, không nâng cờ lịch sử thành xác nhận độc lập của giáo viên. Các nhãn mới chưa được giáo viên xác nhận. Người viết và trùng tiền huấn luyện vẫn **UNKNOWN**; tách trang không đồng nghĩa tách người viết.

Tái kiểm SHA của **256 nguồn HME-VAS TRAIN gốc** đã khôi phục ở vòng trước, giữ nguyên 1.176 crop đủ điều kiện từ chú thích gốc. Không đọc ảnh gốc VAL/TEST của nguồn này. 1.361 TRAIN số hiện có cộng 40 vùng mới thành **1.401 mẫu TRAIN số**; prose có 122 dòng TRAIN cũ cộng 23 dòng mới thành **145 dòng**.

Để TRAIN và suy luận số đều dùng min32, tái trích **1.128 crop hẹp từ pixel thật**, giữ lại 298 feature crop rộng có input giống hệt. Kiểm tra toàn bộ 1.426 chuỗi hiện có đủ timestep cho CTC, kể cả chữ số lặp. CNN xử lý từng ảnh ở chiều rộng thật để GroupNorm không nhận padding của ảnh khác; BiLSTM dùng độ dài thật. Với full CNN mới, mọi tầng được tính lại từ ảnh, không tái dùng feature của encoder parent.

Ảnh nguồn, crop, ZIP và Parquet không được ghi vào thư mục thí nghiệm. Chỉ lưu metadata, weights, feature và log; pixel/tensor ảnh của các lượt full CNN chỉ ở RAM. Không tạo nhãn bằng đầu ra model hoặc dùng phép tính để sửa nhãn nguồn.

## Các lượt train thực sự

| Thử nghiệm | Epoch đã chạy | Epoch chọn bằng VAL | Kết luận |
|---|---:|---:|---|
| `all_old_retention` | 16 | 0 | Giữ KL mọi TRAIN số cũ, không vượt warm start |
| `correct_old_retention` | 16 | 0 | Chỉ KL vùng cũ parent đọc đúng, không vượt warm start |
| `notebook_numeric` | 12 | 0 | Thêm 40 TRAIN số vở mới; CNN cuối/RNN/head không vượt warm start |
| `notebook_text_head` | 12 | 7 | VAL prose 23 → 20 lỗi; hồi quy DEV tổng quát |
| `notebook_text_recurrent` | 12 | 10 | VAL prose 23 → 20 lỗi; hồi quy DEV tổng quát |
| `full_visual` | 8 | 8 | Cập nhật toàn bộ CNN; cải thiện vở/phân số, chưa qua gate |
| `visual_prose` | 10 | 4 | Toàn bộ CNN + width augmentation; 20 lỗi VAL, mất zero trên DEV |
| `visual_augmentation` | 12 | 0 | Width/margin augmentation trên ảnh TRAIN thật; không vượt full_visual warm start |

**Epoch0 là từ chối weights cập nhật và giữ parent**, không được gọi là model đã cải thiện. Có 8 trial thực sự chạy gradient nhưng chỉ 4 selected checkpoint có tensor khác parent. Thí nghiệm augmentation số đã chạy đủ 12 epoch, không bị dừng giữa chừng để giấu điểm xấu.

Augmentation chỉ đổi chiều rộng và thêm lề trắng, không tạo nét/chữ số mới; chỉ áp dụng TRAIN. Chiều dài ảnh luôn đủ đường đi CTC cho transcript gốc. Lượt prose giữ 479 teacher anchor cũ, mỗi anchor đều tham gia mỗi epoch, không dùng VAL/held làm teacher retention. Phân phối teacher là KL regularization, không trở thành nhãn xác thực mới.

Tổng thời gian mà năm tiến trình train báo là **2.607,40 giây**, gồm đọc nguồn/chuẩn bị trong tiến trình. Một số tiến trình chạy đồng thời nên đây không phải wall time toàn bộ tác vụ hoặc thời gian GPU. Tất cả chạy CPU; không cài CUDA hoặc train cloud.

## Thử độ tương phản và kiểm chứng

Probe riêng chốt ba chế độ trước đo: ảnh gốc, grayscale/autocontrast và RGB/autocontrast. Chọn bằng held14 + VAL prose10 trước khi đọc lại DEV/chẩn đoán:

| Chế độ | Lỗi held14 | Lỗi VAL10 |
|---|---:|---:|
| Gốc | 9 | 23 |
| Gray/autocontrast | 30 | 24 |
| RGB/autocontrast | 31 | 22 |

Hai chế độ tương phản đều không qua điều kiện giữ held; **chọn ảnh gốc**, không lấy 22 lỗi VAL để che việc held tăng 9 → 31. Không áp bộ lọc nền/grid lên ứng dụng.

- Tiến trình mới nạp checkpoint, đọc lại pixel/hash nguồn, tái lập selected VAL/held. Các full CNN được đo trực tiếp từ pixel, không dùng cache encoder cũ.
- **7 test mới + 15 test hồi quy cũ đạt**: tách nguồn, không đưa DEV/TEST vào TRAIN, crop/hash, timestep của số lặp, số 0 đầu, giữ literal đơn vị sai, augmentation không xóa nét biên và đủ CTC, ghép phân số một-một bằng hình học. Đây là kiểm thử phần mềm, không phải 22 ảnh nhận diện đúng.
- **104 input riêng biệt được pin hash** qua 9 policy thực thi giữ nguyên. Kiểm tra 8 checkpoint hữu hạn, đúng số lớp và tensor thay đổi/không đổi khớp selected epoch.
- Có một lỗi chuẩn bị prose do `math_role` không có ở một số record cũ, sửa trước đóng băng policy/gradient. Probe tương phản v1 hoàn tất lựa chọn nhưng lỗi import helper ở bước chẩn đoán; giữ v1/policy/selection, chạy bản v2 đã sửa và tái lập lại lựa chọn/đối chứng. Không tính hai lần lỗi công cụ này là neural training hoặc thay đổi chất lượng model.
- TEST68 chữ tay và nguồn HOLDOUT vẫn không đọc pixel. Không có bằng chứng kiểm thử trên điện thoại vật lý trong vòng này.

## Quyết định thay model và kế hoạch tiếp theo

[Release gate](ocr-release-campaign-20261024/release-gate.json) là **NOT_READY_FOR_PRODUCTION**. Không thay runtime, không commit/push/deploy. Model production giữ SHA256:

`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`

File che tên, cắt ảnh và các thành phần UI được bảo vệ vẫn khớp hash. Luồng Student `inspect_notebook` gọi `_generate` với ảnh và provider theo cấu hình hiện tại; weights CRNN offline không tự thay luồng này. Head13 chỉ có blank, `+`, `-`, `0..9`; không đọc chữ, dấu thập phân hoặc tự nhận cấu trúc phân số 2D. Không tuyên bố OCR trong app đã tốt hơn chỉ từ điểm thí nghiệm.

Các hướng đã thử thêm epoch, giữ KL, head/RNN, full CNN, width/margin augmentation và tương phản đã có đối chứng. Bằng chứng hiện tại không ủng hộ tiếp tục kéo dài cùng cấu hình rồi hứa đạt 100%. Việc tiếp theo phải bổ sung bằng chứng/dữ liệu đúng chỗ:

1. Bổ sung nhiều trang TRAIN đã rà literal từ nhiều người viết, đặc biệt chữ tím nét mảnh, multi-digit/zero/số lặp và dòng prose; ghi writer ID nếu có nguồn xác thực. Không chuyển 43 hồ sơ lỗi DEV/VAL/chẩn đoán sang TRAIN.
2. Có chú thích **đầy đủ toàn trang** cho vùng chữ, biểu thức, gạch/tử/mẫu và vùng không phải phân số, cùng ignore region cho phần không đọc được, để đo cả false positive. 15 cặp TRAIN và 31 cặp chẩn đoán hiện tại chưa đủ cho tiêu chí này.
3. Xác nhận nhãn độc lập và chốt bộ acceptance tách người viết/nguồn tiền huấn luyện. Không tự gắn nhãn “giáo viên xác nhận” hoặc “test mù” cho bộ đã xem.
4. Chốt ứng viên/decoder/preprocessing trước test cuối, kiểm critical regression, rồi mới tích hợp route chữ và route toán riêng với fallback/rollback. Không dùng một head số nguyên thay recognizer cả trang.

Không có model nào được chứng minh đúng mọi ảnh. Mục tiêu thay model vẫn chưa đạt; báo cáo này đánh dấu một vòng thử nghiệm đã kiểm chứng, không đánh dấu dự án OCR hoàn thành.

## Tệp tái lập

- [Chỉ số, cấu hình và checkpoint hash](ocr-release-campaign-20261024/summary.json)
- [Hash, checkpoint và kiểm chứng cuối](ocr-release-campaign-20261024/integrity.json)
- [Hồi quy số/dấu quan trọng](ocr-release-campaign-20261024/critical-regressions.json)
- [43 hồ sơ cần rà, không đủ điều kiện TRAIN](ocr-release-campaign-20261024/review-queue.json)

Code, policy, manifest, feature, checkpoint và từng epoch ở `ai-training/datasets/drive_math/math_release_campaign_20261024/` (Git ignored theo cấu hình hiện có). `numeric_vocab.json` ghi đúng mapping13 lớp. Kết quả gốc: `training_result.json`, `notebook_training_result.json`, `full_visual_result.json`, `visual_prose_result.json`, `visual_augmentation_result.json`; kiểm chứng ở `evaluation_result.json`, `full_visual_evaluation.json`, `latest_evaluation_result.json`, `text_photometric_result_v2.json`. Các báo cáo vòng trước giữ nguyên.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Công cụ Python huấn luyện/đánh giá OCR; registry chưa có skill OCR chuyên biệt, không dùng skill UI/design cho model.
  - Applied to: Tái sử dụng CRNN, bộ đọc nguồn/RAM và kiểm SHA, CTC/packed sequence, decoder và metrics đã có; không thêm dependency, không sửa ứng dụng khi ứng viên chưa qua gate.
