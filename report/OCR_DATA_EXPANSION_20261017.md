# Mở rộng dữ liệu và tiếp tục huấn luyện OCR toán ngày 17/10/2026

## Kết quả

Đã bổ sung **41 nhãn TRAIN** từ bốn nguồn Drive chưa có trong nhóm nhãn của
thí nghiệm, sau khi xem cả ảnh gốc và từng hộp cắt. Bốn đề xuất khác bị loại
vì hộp còn lẫn nét bên cạnh hoặc cắt một phần ký hiệu.

Đã huấn luyện hai ứng viên, mỗi ứng viên sáu epoch, rồi nhận diện mới toàn bộ
598 vùng của nhóm mở rộng. Một tiến trình kiểm tra riêng đọc lại 72 nguồn gốc
và tái lập đúng mọi dự đoán. Nhóm này bao gồm tất cả 557 vùng của đợt trước,
nên không bỏ qua các vùng lỗi cũ khi thêm dữ liệu mới.

**Hai ứng viên đều bị loại; model và vocabulary production không đổi.**
Trên cùng 95 vùng DEV, lỗi chuỗi chữ số/dấu tăng từ 30 lên 31 và 32. Dữ liệu
mới là kết quả bổ sung có thể tiếp tục sử dụng, nhưng lượt này chưa tạo được
model tốt hơn để thay bản đang sử dụng.

## Chọn nguồn và kiểm tra nhãn

Bốn nguồn được chọn bằng thứ tự hash có seed cố định từ danh sách ảnh lớp 4
và lớp 5 chưa có trong nhóm tham chiếu. Việc chọn nguồn được lưu trước khi
chạy suy luận mới; không dùng điểm model để chọn các trang dễ. Nguồn đã được
gán toàn bộ vào TRAIN, không dùng để tuyên bố độ chính xác độc lập.

| Nguồn | Kích thước ảnh | Nhãn được chấp nhận | Nội dung |
|---|---|---:|---|
| `Trang_07.jpg` | 3024 × 4032 | 11 | Biểu thức một dòng, dấu bằng, cộng và nhân. |
| `Trang_67.jpg` | 3024 × 4032 | 26 | Tử số và mẫu số được cắt thành từng vùng riêng. |
| `124.jpg` | 1300 × 612 | 1 | Chuỗi `10 000 000.` với dấu chấm cuối nhìn thấy trên ảnh. |
| `70.jpg` | 1356 × 198 | 3 | Các trường số `240`, `180`, `60`. |

Tổng cộng 45 đề xuất được xem riêng. Các biên cắt sát nét chữ được sửa rồi
xem lại trước khi đóng băng nhãn. Không xóa đường kẻ, vẽ lại nét, tính ra đáp
án rồi điền vào nhãn hoặc dùng dự đoán OCR làm tham chiếu.

Bốn đề xuất bị loại vẫn nằm trong hồ sơ rà nguồn, không nằm trong tập train:
một biểu thức còn lẫn nét mở ngoặc của đơn vị phía sau và ba thành phần phân
số còn lẫn nét màu từ vùng lân cận. Hai vùng TRAIN mơ hồ đã cách ly ở lượt
trước cũng tiếp tục bị loại khỏi tối ưu và chấm điểm.

Các phân số hai chiều không được ghép thẳng thành nhãn của một dòng CRNN.
Lượt này có nhãn tử số/mẫu số riêng; chưa chứng minh được việc tự động phát
hiện và ghép đúng mọi phân số từ một trang ảnh mới.

## Tập dữ liệu sau khi mở rộng

- Tổng vùng nhận diện: 598 từ 72 nguồn ảnh, gồm 557 vùng cũ và 41 vùng mới.
- TRAIN đủ điều kiện: 501, gồm 460 vùng cũ và 41 vùng mới.
- TRAIN còn cách ly: hai vùng cũ, chỉ nhận diện để truy nguyên, không dùng loss
  hoặc chấm như nhãn chắc chắn.
- DEV: giữ nguyên 95 vùng, tọa độ, nguồn và nội dung nhãn so với đợt trước.
- HOLDOUT: nguồn bị loại trước khi đọc pixel; không được suy luận hoặc huấn luyện.

Kiểm tra ID, hộp cắt và hash trang để tránh lặp chính xác vùng dữ liệu và
trộn một trang giữa TRAIN và DEV. Chưa biết mức độc lập người viết hoặc trùng
với dữ liệu pretrain. Việc các trang mới chưa có trong nhóm nhãn không đồng
nghĩa chúng chưa từng có dự đoán nháp trong đợt nhận diện toàn kho trước đây.

## Huấn luyện và tự kiểm tra

Tái sử dụng checkpoint đối chứng riêng `math_focus/run_control/candidate.pth`
và vocabulary của nhóm thí nghiệm. So sánh dưới đây là ảnh hưởng của thích
nghi từ checkpoint riêng này, không phải bảng xếp hạng so với toàn bộ pipeline
OCR production trên website.

Hai lượt được xác định trước khi chạy: một lượt CTC đối chứng và một lượt
CTC có thêm cross entropy nhằm giữ đường đọc đúng của dữ liệu TRAIN cũ.

- Sáu epoch mỗi lượt, seed `20261017`, batch 8, bốn luồng CPU.
- Chỉ linear CTC head được tối ưu, Adam learning rate `1e-6`; CNN và BiLSTM giữ nguyên.
- Vai trò toán có trọng số loss gấp hai; 39 vùng TRAIN có chuỗi quan trọng sai
  ở checkpoint đối chứng được tăng trọng số thêm. Không dùng lỗi DEV để gán
  trọng số mẫu huấn luyện.
- Lượt retention dùng trọng số 1 và 409 đường đọc mà đối chứng khớp toàn bộ
  nhãn TRAIN sau chuẩn hóa NFC/khoảng trắng. Đây là regularization trên mẫu đã
  xác nhận, không tạo nhãn mới từ model.
- Tính loss theo độ dài thực; không truyền gradient qua phần padding. Tự kiểm
  tra đã xác nhận trường hợp không có mục tiêu retention và các timestep ngoài
  độ dài không bị tính vào loss retention.
- Không augmentation, ngôn ngữ sửa từ, phép toán sửa số hoặc gọi API AI.

Lượt chính hoàn tất trong 30,48 giây, bao gồm đọc nguồn, trích đặc trưng, train
và suy luận. Không gồm rà nhãn, kiểm tra riêng và viết báo cáo; đây không phải
độ trễ phục vụ người dùng thật.

## Kết quả trên bộ DEV giữ nguyên

| Chỉ số | Đối chứng riêng | Expanded control | Expanded retention |
|---|---:|---:|---:|
| Epoch được chọn | — | 1 | 1 |
| Lỗi ký tự / 1.097 | 105 | 106 | 107 |
| CER | 9,57% | 9,66% | 9,75% |
| Lỗi chuỗi chữ số/dấu / 432 | 30 | 31 | 32 |
| Vùng khớp toàn bộ / 95 | 53 | 52 | 52 |
| Vùng khớp chuỗi quan trọng / 87 | 64 | 63 | 62 |
| Được chấp nhận | Mốc so sánh | Không | Không |

Các epoch sau cũng không vượt điều kiện đóng băng. Không hạ điều kiện, đổi
nhãn DEV hoặc chuyển DEV sang TRAIN để làm đẹp kết quả.

Ví dụ hồi quy quan sát trực tiếp:

| Nhãn | Đối chứng | Control | Retention |
|---|---|---|---|
| `300 cm² = 3 dm²` | `300 cm² = 3 dm²` | `30 cm² = 3 dm²` | `30 cm² = 3 dm²` |
| `650-150=500` | `650 - 150 =500` | `650 - 150 =500` | `650 - 150 =00` |

Những lỗi này làm thay đổi số học học sinh nhìn thấy. Việc loss train giảm
hoặc một vài chuỗi TRAIN tốt hơn không đủ điều kiện thay model.

## Kết quả trên TRAIN và các mẫu mới

| Chỉ số | Đối chứng riêng | Control | Retention |
|---|---:|---:|---:|
| Khớp toàn bộ trên cùng 501 TRAIN | 409 | 411 | 411 |
| Lỗi ký tự trên 501 TRAIN | 190 | 188 | 188 |
| Lỗi chuỗi quan trọng trên 501 TRAIN | 57 | 57 | 57 |
| Khớp toàn bộ trên 41 mẫu mới | 26 | 26 | 26 |
| Khớp chuỗi quan trọng trên 41 mẫu mới | 29 | 29 | 29 |
| Lỗi chuỗi quan trọng trên 41 mẫu mới | 13 | 13 | 13 |

Tăng hai mẫu TRAIN khớp toàn bộ đến từ một từ tiếng Việt và khoảng trắng trong
`3 84` → `384`, không phải giảm lỗi chữ số. Các mẫu mới còn bộc lộ những lỗi
cụ thể: `35` đọc thành `3`, một chữ số `8` đọc thành `9`, và `240` đọc thành
`24ố`. Nhãn được giữ theo nét gốc, không thay theo kết quả model.

Điểm trên mẫu vừa dùng train không chứng minh khả năng tổng quát hóa. Các số
501 mẫu cũng không được so trực tiếp với tổng 460/462 mẫu ở báo cáo cũ như
một mức tăng hay giảm chất lượng, vì tập dữ liệu đã mở rộng.

## Kiểm tra riêng và dữ liệu giữ lại

Tiến trình audit mới đọc lại 72 nguồn gốc, kiểm tra hash trang và pixel từng
hộp rồi chạy suy luận cho cả đối chứng và hai ứng viên trên 598 vùng. Mọi
dự đoán và điểm số được tái lập đúng. Chỉ `fc.weight` và `fc.bias` thay đổi;
tất cả tensor hữu hạn, CNN/BiLSTM giữ nguyên và các hash đầu vào còn khớp.

Hàng chờ của mỗi ứng viên có 133 vùng chưa khớp có nhãn được chấm, cộng hai
vùng cách ly cũ. Danh sách chứa nguồn, hash, hộp, nhãn và dự đoán để tiếp tục
rà. Không so tổng hàng chờ này trực tiếp với 122 vùng của báo cáo trước vì
lượt này bổ sung 41 vùng mới và giữ nguyên quyết định cách ly.

Thư mục riêng, được Git bỏ qua:
`ai-training/datasets/drive_math/math_data_expansion_20261017/`.

- Nguồn và đề xuất: `source_plan.json`, `proposals.json`, `proposals_v2.json`,
  `proposals_v3.json`, `source_review.json` cùng script rà ảnh.
- Điều kiện đóng băng: `policy.json`.
- Train và tự kiểm tra: `train_expanded.py`.
- Kết quả: `result.json`, 12 file kết quả epoch và hai checkpoint riêng.
- Kiểm tra: `audit_expanded.py`, `audit.json`.
- Công việc còn lại: `remaining_review_queue.json`.

| Artifact | SHA-256 |
|---|---|
| Expanded control | `c9465f9b2ab55ed7959f12a36f17cb98824bfb2a2b32882765f0d34966bf6530` |
| Expanded retention | `22e5a2682a749b6e5b8a14016fe7cd28a598db5c742fda631a1b6f54b5a405a2` |
| Production weights giữ nguyên | `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` |
| Production vocabulary giữ nguyên | `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` |

## Giới hạn và phần còn cần làm

Ảnh gốc và crop chỉ được đọc trong RAM; không lưu ảnh, ZIP hoặc Parquet vào
thư mục dự án. Các thư mục cache mà chủ dự án đã xóa không được tạo lại.
Không sử dụng dịch vụ trả phí, gọi API AI, deploy, sửa UI hoặc commit/push.

DEV đã được dùng nhiều lần nên là phép so sánh trong phát triển. Các điều kiện
về tập đánh giá độc lập và các nhóm kiểm soát nguồn lưu trữ từng bị loại vẫn
chưa hoàn tất. Lượt này cũng chưa chạy lại toàn bộ 6.850 nguồn/42.679 dòng
nháp của kho lớn; phạm vi nhận diện mới là 598 vùng được nêu trong báo cáo.

Cần tiếp tục tăng dữ liệu chữ số và ký hiệu đã rà, phân tích các trường hợp
mất chữ số và kiểm tra trên dữ liệu độc lập trước khi xem xét thay model.
Việc bổ sung dữ liệu ở lượt này đã hoàn tất, nhưng chưa có bằng chứng model
OCR tốt hơn hoặc khả năng nhận diện mọi bố cục toán hai chiều.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng bộ đọc Drive, trích đặc trưng, giải mã CTC, bộ chấm và điều kiện chấp nhận hiện có.
  - Applied to: rà nhãn, chỉnh biên hộp, thí nghiệm head riêng và tiến trình tái lập suy luận.
