# Tiếp tục nhận diện và huấn luyện OCR toán ngày 17/10/2026

## Kết quả và quyết định

Đã huấn luyện thật hai ứng viên OCR, mỗi ứng viên bốn epoch, và nhận diện mới
toàn bộ 557 vùng của nhóm dữ liệu đã có nhãn. Nhóm này bao gồm cả 122 vùng
còn lỗi ở đợt trước. Một tiến trình khác đã đọc lại ảnh gốc từ Drive và tái
lập toàn bộ dự đoán của cả hai ứng viên.

**Cả hai ứng viên bị loại. Không thay model đang sử dụng.** Trên cùng 95 vùng
DEV, lỗi ký tự tăng từ 105 lên 109 và lỗi chuỗi chữ số/dấu tăng từ 30 lên 32.
Một vài mẫu TRAIN đọc tốt hơn không bù được những phép tính đang đúng bị đọc sai.

Đợt này cải thiện việc kiểm soát nhãn: sửa một dấu câu nhìn thấy trên ảnh,
cách ly hai vùng số chưa chắc chắn và bổ sung kiểm tra chặn hồi quy ở những
biểu thức có nhiều chữ số 0. Không tuyên bố OCR đã hoàn hảo.

## Phạm vi dữ liệu

- Đọc mới 68 trang gốc trên Drive, tạo 557 vùng trong RAM để nhận diện.
- Trong 462 vùng TRAIN trước đây, dùng 460 vùng đủ điều kiện để tối ưu trọng số.
  Hai vùng được cách ly không tham gia tính loss hoặc chọn trọng số huấn luyện.
- Giữ nguyên 95 vùng DEV, gồm cả nhãn, nguồn và hộp tọa độ. DEV không nhận gradient.
- Loại nguồn HOLDOUT trước khi đọc ảnh; không chạy suy luận trên HOLDOUT.
- Giữ phân chia theo nhóm nguồn và hash trang; không chuyển DEV sang TRAIN.

Hồ sơ nhận diện trước đây ghi 6.850 nguồn đã được đọc, cùng một nguồn dành riêng
cho đánh giá. Đó là tiến độ của đợt trước, không phải số ảnh được nhận diện mới
ngày 17/10. Lượt hiện tại xử lý nhóm 557 vùng nói trên; không chạy lại toàn bộ
42.679 dòng nháp của kho lớn và không coi những dòng nháp đó là nhãn đúng để train.

## Rà nhãn trên ảnh gốc

Đã đối chiếu trong RAM cả ngữ cảnh ảnh và hộp cắt của 37 vùng TRAIN bị gắn cờ
sai chuỗi ký tự quan trọng ở lần trước. Cờ này bao gồm chữ số, toán tử và một số
dấu câu; không đồng nghĩa cả 37 vùng đều là lỗi tính toán.

| Xử lý | Số vùng | Chi tiết |
|---|---:|---|
| Giữ nhãn cũ | 34 | Đọc lại nét gốc, không đổi nhãn theo dự đoán OCR. |
| Sửa dấu câu thấy rõ | 1 | `962.jpeg`: `2 Tính nhẩm` thành `2. Tính nhẩm`. |
| Tạm cách ly | 2 | `271.jpeg` và `158.jpg`: cần xác nhận chắc hơn dấu phân cách/nét cuối và ranh giới ký tự. |

Hai vùng cách ly còn được xem lại ở mức phóng lớn 5 lần bằng nearest-neighbor
và có ngữ cảnh xung quanh. Quyết định cách ly trong tập train đã đóng băng được
giữ nguyên, không đổi nhãn sau khi xem điểm model. Nhãn trước đó vẫn được lưu
để truy nguyên, không được trình bày như nhãn mới đã xác nhận.

Những dòng học sinh viết sai về toán, chẳng hạn `4×1=4+2=6`, vẫn được giữ đúng
như nét viết. Không lấy kết quả phép tính để sửa chữ số, không điền đáp án thiếu.
Ô bảng ghi `5` cũng giữ nhãn `5`, dù model còn đọc thành `3`.

## Cách huấn luyện

Đối chứng là checkpoint riêng của nhóm thí nghiệm `math_focus/run_control`,
không phải phép đo trực tiếp chất lượng model production trên toàn kho ảnh.
So sánh dùng cùng checkpoint đầu vào, từ vựng, ảnh và cách tiền xử lý.

- Đổi phạm vi thích nghi: huấn luyện BiLSTM và lớp linear CTC; giữ nguyên CNN.
  Hai lần trước chỉ huấn luyện linear CTC.
- Hai lượt có cùng seed `20261017`, bốn epoch, batch 8, bốn luồng CPU.
- Adam: learning rate BiLSTM `1e-6`, linear CTC `5e-6`.
- Tăng trọng số loss cho các vai trò toán; 27 vùng TRAIN có chuỗi toán sai
  được tăng trọng số thêm. Không dùng DEV để quyết định mẫu train khó.
- Đối chứng không regularization; bản thứ hai có KL weight 2 nhằm giữ phân bố
  đầu ra của 426 mẫu TRAIN mà đối chứng đang đọc đúng toàn dòng hoặc đúng chuỗi
  ký tự quan trọng. Phân bố này là regularization, không phải nhãn mới.
- Dùng độ dài thật khi đóng gói chuỗi cho BiLSTM, tránh coi padding là ngữ cảnh
  của hướng đọc ngược. Không augmentation, sửa từ bằng ngôn ngữ hay sửa số bằng toán.

Tổng thời gian tiến trình train và nhận diện trong lượt chính: 69,67 giây.
Con số này không gồm rà ảnh, tiến trình kiểm tra độc lập và viết báo cáo, cũng
không phải độ trễ OCR trên thiết bị thật hay khi phục vụ nhiều học sinh.

## Điểm trên 95 vùng DEV không đổi

| Chỉ số | Đối chứng riêng | Recurrent control | Recurrent anchored |
|---|---:|---:|---:|
| Epoch được chọn | — | 2 | 1 |
| Lỗi ký tự / 1.097 ký tự tham chiếu | 105 | 109 | 109 |
| CER | 9,57% | 9,94% | 9,94% |
| Lỗi chuỗi chữ số/dấu / 432 ký tự | 30 | 32 | 32 |
| Vùng khớp toàn bộ / 95 | 53 | 52 | 52 |
| Vùng khớp chuỗi quan trọng / 87 | 64 | 63 | 63 |
| Qua điều kiện chấp nhận | Mốc đối chiếu | Không | Không |

Điều kiện đóng băng yêu cầu tối đa 105 lỗi ký tự, tối đa 29 lỗi chuỗi quan trọng,
ít nhất 53 vùng khớp toàn bộ và 64 vùng khớp chuỗi quan trọng, không giảm chất lượng
theo vai trò. Bổ sung kiểm tra cả năm biểu thức DEV có `00` mà đối chứng đã đọc
đúng chuỗi quan trọng. Cả hai ứng viên đều làm sai hai biểu thức trong nhóm này.

| Nhãn gốc | Đối chứng | Recurrent control | Recurrent anchored |
|---|---|---|---|
| `300 cm² = 3 dm²` | `300 cm² = 3 dm²` | `30 cm² = 3 d²` | `30 cm² = 3 dm²` |
| `650-150=500` | `650 - 150 =500` | `650 - 150 =00` | `650 - 150 =00` |

Không epoch nào của hai lượt vượt điều kiện chấp nhận. Không giảm ngưỡng hoặc
đổi nhãn DEV để cho ứng viên qua.

## Điểm trên cùng 460 vùng TRAIN đủ điều kiện

| Chỉ số | Đối chứng riêng | Recurrent control | Recurrent anchored |
|---|---:|---:|---:|
| Vùng khớp toàn bộ | 383 | 386 | 385 |
| Lỗi ký tự | 149 | 145 | 147 |
| Lỗi chuỗi chữ số/dấu | 44 | 44 | 44 |

Một số cải thiện là khoảng trắng trong số, như `5 8` thành `58` và `3 84` thành
`384`; chuỗi chữ số vốn đã đúng. Không diễn giải chúng thành cải thiện số học.
Ô `5` trong bảng `960.jpeg` vẫn đọc thành `3` ở cả hai bản.

Đây là điểm trên dữ liệu vừa được dùng để train. Không dùng nó làm bằng chứng
khả năng tổng quát hóa. Số TRAIN cũng không so trực tiếp với đợt trước vì đã sửa
một nhãn và cách ly hai mẫu.

## Kiểm tra độc lập và bảo toàn hệ thống

Tiến trình kiểm tra riêng đã đọc lại 68 trang từ Drive, kiểm tra ảnh/hộp cắt
bằng hash và chạy suy luận cho cả 557 vùng với đối chứng và hai checkpoint mới.
Kết quả tái lập đúng toàn bộ dự đoán đã lưu, điểm DEV, điểm TRAIN và quyết định loại.

- Chỉ 10 tensor thuộc `rnn.*` và `fc.*` thay đổi. CNN giữ nguyên, tất cả tensor hữu hạn.
- Các hash đầu vào đã đóng băng còn khớp; hash checkpoint và vocabulary production không đổi.
- Không ghi ảnh gốc, crop, ZIP hoặc Parquet xuống thư mục cục bộ của dự án.
  Thư mục ảnh gốc/cache mà chủ dự án đã xóa không được tạo lại.
- Không gọi API AI, không dùng dịch vụ trả phí, không thay UI, không deploy hoặc commit/push.
- Kiểm tra chạy được: tự kiểm tra độ dài chuỗi/loại DEV-HOLDOUT-mẫu mơ hồ,
  toàn bộ train, kiểm tra suy luận riêng và `git diff --check` đều hoàn tất.

## Tài liệu và trọng số riêng

Thư mục thí nghiệm nằm ngoài nội dung Git:
`ai-training/datasets/drive_math/math_recurrent_20261017/`.

- Rà nguồn: `review_queue.py`, `source_review.json`, `inspect_quarantine.py`.
- Điều kiện và dữ liệu đóng băng: `policy.json`.
- Huấn luyện/tự kiểm tra: `experiment.py`; kết quả: `result.json` và tám file epoch.
- Trọng số riêng: `recurrent_control.pth`, `recurrent_anchored.pth`.
- Kiểm tra mới: `audit.py`, `audit.json`.
- Hàng chờ: `remaining_review_queue.json`. Có 117 vùng chưa khớp đã chấm cộng hai
  vùng cách ly ở bản control; bản anchored có 118 vùng chưa khớp cộng hai vùng cách ly.
  Các số này không phải mức cải thiện của production và không so trực tiếp với hàng
  chờ 122 vùng cũ vì nhãn/điều kiện tính hàng chờ đã thay đổi.

SHA-256:

| Artifact | Hash |
|---|---|
| Control riêng | `c8e8ddabe78a585c9c10be4f19adc85843410f0b94b7d6efd3cf6217b463df4e` |
| Anchored riêng | `6406d6416fe336d374f71dedcc85fe1e78b90b9210af3d38bb1c426882c790d8` |
| Model production giữ nguyên | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` |
| Vocabulary production giữ nguyên | `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` |

## Giới hạn và phần còn cần làm

DEV đã được dùng nhiều lần nên là phép so sánh trong phát triển, không phải độ
chính xác độc lập. Chưa biết mức độc lập người viết hoặc trùng với dữ liệu pretrain.
Các nhóm kiểm soát nguồn lưu trữ từng bị loại chưa được khôi phục trong lượt này;
đây vẫn là điều kiện cản phát hành. Nhận diện tự động mọi bố cục toán hai chiều,
ô bảng và nét bút đỏ chưa được chứng minh.

Việc cần làm tiếp là rà nhãn và ranh giới vùng còn mơ hồ, bổ sung dữ liệu TRAIN
đã kiểm tra về những dạng chữ số/dấu đang thiếu và có tập đánh giá độc lập trước
khi thử thay production. Kết quả hiện tại không ủng hộ chỉ tăng thêm epoch với
cùng dữ liệu và coi loss giảm là đủ điều kiện phát hành.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng bộ đọc Drive, kiểm tra pixel, giải mã CTC và bộ chấm hiện có.
  - Applied to: thí nghiệm riêng, kiểm tra nhãn và tiến trình tái lập suy luận.
- `verification-before-completion`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/verification-before-completion/SKILL.md`
  - Why selected: phân biệt train đã chạy với model thực sự cải thiện và giữ bằng chứng mới.
  - Applied to: tự kiểm tra, audit mới, đối chiếu hash và quyết định không thay production.
