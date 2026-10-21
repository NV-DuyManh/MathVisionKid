# OCR toán với huấn luyện riêng các dấu ngày 17/10/2026

## Kết quả chính

Đã huấn luyện thật một ứng viên chỉ cập nhật bốn lớp dấu `×`, `<`, `>` và `=`.
Lượt này chạy tám epoch trên cùng 501 vùng TRAIN đủ điều kiện, nhận diện lại
598 vùng và được kiểm tra lại bằng một tiến trình đọc Drive riêng.

**Ứng viên vượt điều kiện DEV nhưng bị loại ở kiểm tra đối chứng bổ sung.**
Trên cùng 95 vùng DEV, lỗi chuỗi
chữ số/dấu giảm từ 30 xuống 27, lỗi ký tự giảm từ 105 xuống 104; số vùng khớp
toàn bộ giữ ở 53. Đây là tiến bộ nhỏ trong so sánh phát triển, chưa phải bằng
chứng độ chính xác độc lập hoặc quyết định thay model production.

Đã đọc và nhận diện được đủ 18 vùng đối chứng từng bị gián đoạn truy cập
Parquet. Hai dòng văn bản phát sinh lỗi chữ `x` thành dấu `×`; nhóm 12 mẫu
TRAIN lịch sử tăng lỗi ký tự từ 31 lên 33. Vì vậy quyết định cuối là giữ
checkpoint để nghiên cứu, **không thay model production**. Không train hoặc
điều chỉnh model sau khi xem kết quả 18 vùng này.

Trọng số nhận biết các chữ số 0–9, CTC blank, CNN, BiLSTM và các lớp khác giữ
nguyên. Việc khóa trọng số chữ số không bảo đảm mọi ảnh mới đều không mất số:
các lớp dấu vẫn cạnh tranh với lớp chữ số khi giải mã. Cần tiếp tục kiểm tra
thực tế và giữ các điều kiện chặn hồi quy.

## Chẩn đoán lỗi mất số 0 ở lượt trước

Đã đọc lại đặc trưng và đầu ra theo từng timestep của năm biểu thức DEV có
`00` mà checkpoint đối chứng đọc đúng. Với dòng `300 cm² = 3 dm²`, ở timestep
6, chênh lệch logit giữa `0` và blank của đối chứng chỉ khoảng `0,000583`.
Ở bản expanded control trước đó, chênh lệch thành `-0,002134`; blank thắng và
kết quả mất một số 0 thành `30 cm² = 3 dm²`.

Đây là bằng chứng về cơ chế xảy ra trên một mẫu cụ thể, không phải lời giải
thích đầy đủ cho mọi lỗi mất số trong kho dữ liệu. Nó cho thấy cập nhật đồng
thời các lớp chữ số/blank có thể làm đổi một quyết định rất sát nhau.

Vì vậy lượt mới giới hạn cập nhật ở bốn lớp dấu. Không thêm hay sửa số bằng
phép tính, không dùng đáp án toán học để vá đầu ra OCR.

## Dữ liệu và quy trình

Giữ nguyên nhóm dữ liệu từ lượt mở rộng trước:

- 501 vùng TRAIN được xác nhận đủ điều kiện.
- Hai vùng TRAIN còn mơ hồ được nhận diện để truy nguyên, không nhận gradient
  và không chấm như nhãn chắc chắn.
- 95 vùng DEV với nguyên nguồn, tọa độ và nội dung nhãn.
- Tổng 598 vùng từ 72 nguồn gốc trên Drive, gồm cả các vùng lỗi cũ và 41 mẫu
  mới của lượt trước. Lượt này không bổ sung thêm 41 nhãn lần thứ hai.
- Nguồn HOLDOUT bị loại trước khi đọc pixel; không chạy suy luận HOLDOUT.

Những điều kiện sau được lưu trước khi chạy: tám epoch, seed `20261017`, Adam
learning rate `1e-4`, batch 8, bốn luồng CPU, tăng trọng số loss theo vai trò toán
và theo lỗi TRAIN của đối chứng. Chỉ 1.028 tham số thuộc bốn hàng của lớp
linear CTC được phép đổi. Các vùng DEV không dùng để gán trọng số mẫu hoặc nhận
gradient; DEV được dùng để chọn epoch như trong các lượt trước.

Tự kiểm tra đã chạy optimizer trên fixture và xác nhận chỉ hàng được phép
thay đổi, còn DEV và mẫu mơ hồ bị loại. Kiểm tra checkpoint thật xác nhận
chỉ `fc.weight` và `fc.bias` khác, và trong hai tensor này chỉ bốn hàng `<`,
`=`, `>` và `×` khác đối chứng. Mọi tensor hữu hạn.

Lượt chính gồm đọc nguồn, trích đặc trưng, train và suy luận hoàn tất trong
26,83 giây. Không gồm rà ảnh, audit mới hoặc đọc các gói đối chứng bổ sung;
không dùng thời gian này làm số liệu độ trễ website hay thiết bị thật.

## Kết quả trên bộ DEV giữ nguyên

| Chỉ số | Đối chứng riêng | Ứng viên dấu |
|---|---:|---:|
| Epoch được chọn | — | 8 |
| Lỗi ký tự / 1.097 | 105 | 104 |
| CER | 9,57% | 9,48% |
| Lỗi chuỗi chữ số/dấu / 432 | 30 | 27 |
| CER chuỗi chữ số/dấu | 6,94% | 6,25% |
| Vùng khớp toàn bộ / 95 | 53 | 53 |
| Vùng khớp chuỗi quan trọng / 87 | 64 | 66 |
| Giữ đúng chuỗi quan trọng trên năm mẫu `00` đối chứng đang đúng | 5/5 | 5/5 |
| Qua điều kiện DEV đóng băng | Mốc đối chiếu | Có |

Điều kiện yêu cầu ít hơn 30 lỗi chuỗi quan trọng, không tăng lỗi ký tự, không
giảm số vùng khớp toàn bộ hoặc khớp chuỗi quan trọng, không hồi quy theo vai
trò và không làm hỏng các mẫu số 0 đang đúng. Những epoch đầu chưa vượt toàn
bộ điều kiện; epoch 8 vượt các điều kiện này.

Các vai trò phân số, trường số và văn xuôi không giảm điểm trong bộ DEV này.
Tuy nhiên, bản mới vẫn còn 27 lỗi chuỗi quan trọng và chưa tăng số dòng khớp
hoàn toàn, nên không được mô tả như một model hoàn hảo.

## Thay đổi đã đối chiếu ảnh gốc

Tiến trình audit phát hiện 10 vùng có đầu ra thay đổi: bảy TRAIN và ba DEV.
Cả 10 vùng được xem lại trực tiếp trên ngữ cảnh ảnh gốc và hộp cắt trong RAM.
Không sửa nhãn tham chiếu sau khi xem điểm model.

| Nhãn từ ảnh | Trước | Sau | Diễn giải |
|---|---|---|---|
| `25+12=37` | `25 + 12 - 37` | `25 + 12 = 37` | Sửa được dấu bằng, vẫn có khác biệt khoảng trắng. |
| `65+8=73` | `65 +8  73` | `65 +8 = 73` | Bổ sung đúng dấu bằng; điểm ký tự toàn dòng riêng mẫu này vẫn tăng lỗi khoảng trắng. |
| `85,70 < 85,8` | `85, 70 858` | `85, 70 <858` | Đọc được dấu nhỏ hơn, nhưng vẫn thiếu dấu phẩy ở vế phải. |
| `7>1` | `7 ) 1` | `7 > 1` | Mẫu TRAIN sửa được dấu lớn hơn. |
| `9>7` | `9 5 7` | `9 > 7` | Mẫu TRAIN sửa được ký hiệu từng bị đọc như chữ số. |
| `=4×8` | `- 4×8` | `= 4×8` | Mẫu TRAIN mới sửa được dấu bằng. |

Không dùng bảng này để khẳng định mọi dòng đã đúng toàn bộ hoặc như bằng
chứng của giáo viên. Nó chỉ mô tả thay đổi cục bộ đã quan sát.

Trên cùng 501 TRAIN, lỗi chuỗi quan trọng giảm 57 → 49 và số vùng khớp chuỗi
quan trọng tăng 375 → 381. Điểm TRAIN là kết quả trên dữ liệu dùng huấn luyện,
không phải bằng chứng tổng quát hóa. Số vùng khớp toàn bộ TRAIN giữ ở 409.

## Đối chứng bổ sung: phát hiện hồi quy và loại ứng viên

Sau khi cố định checkpoint và kết quả chính, đã đọc lại tám gói Parquet trên
Drive bằng bộ đọc RAM có giới hạn 256 MiB mỗi gói. Kiểm tra SHA-256 của gói,
ảnh nhúng và pixel vùng cắt; nhận diện đủ 18/18 vùng, không có lỗi đọc nguồn.
Tổng dữ liệu truyền là 1.271.129.936 byte, xử lý tuần tự trong 308,61 giây;
không ghi ảnh hay Parquet xuống đĩa.

Đây là 12 vùng TRAIN và sáu vùng DEV theo phân chia lịch sử, không nằm trong
501 mẫu nhận gradient của lượt này. Chúng từng được dùng trong các lượt phát
triển trước, nên không phải bộ kiểm định chưa từng thấy hay xác nhận độc lập
của giáo viên. Giữ nguyên nhãn tham chiếu, không xem lại ảnh bằng mắt trong
lượt kiểm tra bổ sung này.

| Chỉ số | Đối chứng riêng | Ứng viên dấu |
|---|---:|---:|
| Lỗi ký tự trên 12 TRAIN lịch sử / 575 ký tự | 31 | 33 |
| Lỗi chuỗi quan trọng trên nhóm này / 18 ký tự | 3 | 4 |
| Vùng khớp toàn bộ trên nhóm này | 3/12 | 3/12 |
| Vùng khớp chuỗi quan trọng trên nhóm này | 7/9 | 6/9 |
| Lỗi ký tự trên sáu DEV bổ sung / 307 ký tự | 30 | 30 |
| Lỗi chuỗi quan trọng trên sáu DEV bổ sung / 11 ký tự | 4 | 4 |
| Vùng khớp toàn bộ trên sáu DEV bổ sung | 1/6 | 1/6 |

Hai thay đổi làm sai thêm văn bản là `xen kẽ` → `×en kẽ` và `nhận xét` →
`nhận ×ét`. Các lỗi khác vốn có trong hai dòng cũng chưa được sửa. Điểm này
cho thấy tăng khả năng chọn dấu nhân có thể lấn át chữ `x`, dù trọng số của
chữ `x` được giữ nguyên.

Ứng viên không vượt điều kiện không hồi quy của nhóm bổ sung. Kết quả DEV
chính không đủ để cho phép phát hành. Không sửa chuỗi bằng quy tắc `x`/`×`
để che lỗi, không đổi nhãn và không train thêm sau kiểm tra này. Bộ 598 vùng
đã được audit ở tiến trình riêng; 18 vùng bổ sung mới chạy một lần so sánh,
chưa có lượt đọc/suy luận thứ hai để tái lập toàn bộ nhóm đó.

## Audit mới và các artifact riêng

Audit mới đã đọc lại 72 nguồn, kiểm tra hash trang/pixel và chạy lại đối chứng
cùng ứng viên cho cả 598 vùng. Mọi dự đoán và điểm số đã lưu được tái lập đúng.
Trọng số chữ số/blank được so trực tiếp với đối chứng và khớp chính xác.

Thư mục riêng được Git bỏ qua:
`ai-training/datasets/drive_math/math_symbol_isolation_20261017/`.

- `train_symbols.py`, `policy.json` và tám file kết quả epoch.
- `previous_zero_margin_diagnosis.json`: bằng chứng theo timestep của lỗi số 0 cũ.
- `result.json`, `symbol_candidate.pth`: kết quả và trọng số riêng.
- `audit_symbols.py`, `audit.json`: đọc lại nguồn và kiểm tra checkpoint.
- `review_changes.py`, `changed_source_review.json`: rà lại 10 vùng thay đổi.
- `evaluate_storage_controls.py`, `storage_control_policy.json`,
  `storage_control_result.json`: chính sách đóng băng và kết quả 18 vùng bổ sung.
- `candidate_decision.json`: ghi nhận DEV đạt nhưng đối chứng bổ sung không
  đạt, không phê duyệt production.
- `remaining_review_queue.json`: 134 vùng có nhãn chưa khớp toàn dòng, cộng hai
  vùng cách ly. Không dùng độ dài hàng chờ để thay cho điểm lỗi chữ số/dấu.

Candidate SHA-256:
`9d5fb86b893be38d5c84ab8025eaa7ff087766804d4182808a5c7a0ef4d5a29e`.

Model production giữ nguyên SHA-256:
`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.

Vocabulary production giữ nguyên SHA-256:
`6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.

## Giới hạn phát hành

Đối chứng ở đây là checkpoint nghiên cứu riêng với vocabulary và cách resize
của thí nghiệm. Không suy ra model mới đã vượt toàn bộ pipeline production,
và không chép trực tiếp checkpoint này đè model đang phục vụ.

DEV đã được dùng nhiều lần nên vẫn là so sánh phát triển. Chưa có tập mới do
giáo viên xác nhận độc lập; mức độc lập người viết/pretraining chưa rõ. Những
nhãn hiện có cũng chưa phải chứng nhận chương trình học chính thức.

Lượt sau cần bổ sung đối chứng phân biệt chữ `x`, biến số `x` và dấu nhân `×`
trong nhiều ngữ cảnh, đồng thời bảo vệ các trường hợp số 0 đang đúng. Phải
công khai việc 18 vùng trên đã được xem kết quả; không coi chúng là kiểm định
mới chưa từng dùng ở những lượt tiếp theo.

Ảnh gốc, crop và Parquet chỉ được đọc trong RAM. Không phục hồi các thư mục
cache ảnh mà chủ dự án đã xóa, không gọi API AI hoặc dùng dịch vụ trả phí.
Không thay UI, cấu hình production, deploy, commit hoặc push trong lượt này.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng bộ đọc Drive, đặc trưng CRNN, bộ chấm và điều kiện cũ; giới hạn thay đổi đúng các lớp dấu cần học.
  - Applied to: chẩn đoán margin, huấn luyện hàng trọng số riêng, audit đọc nguồn và đánh giá đối chứng bổ sung.
