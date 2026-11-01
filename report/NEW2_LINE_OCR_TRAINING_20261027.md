# NEW2: nhận diện dòng và thử huấn luyện ngày 27/10/2026

> Cập nhật cùng ngày: đợt mở rộng tiếp theo đã tạo được ứng viên chữ và số cải thiện trong phạm vi đo, chưa phát hành. Đối chiếu policy trực tiếp cũng tìm thấy nguồn trùng mà `ledger.sqlite3` không bao phủ đầy đủ. Xem [báo cáo mở rộng](NEW2_OCR_EXPANSION_20261027.md); số liệu và quyết định của đợt đầu bên dưới được giữ nguyên.

Đã chạy nhận diện đủ **136 ảnh mới** và hoàn thành **4 cấu hình huấn luyện thực**, tổng cộng **9.120 bước cập nhật**. Chưa có trọng số mới vượt điều kiện giữ chất lượng cũ, vì vậy **không thay model trong app**. Không commit/push trong tác vụ này.

## Dữ liệu và nhận diện

| Hạng mục | Kết quả |
|---|---:|
| Ảnh đã đọc, kiểm tra SHA-256, tách vùng và chạy OCR | 136/136 |
| Ảnh khác nhau theo byte/pixel | 127 |
| Bản trùng hoàn toàn, giữ tên để truy vết | 9 |
| Lỗi thực thi tách vùng / nhận diện | 0 / 0 |
| Vùng đã chạy nhận diện, có tính các bản trùng | 2.821 |
| Vùng trên các nguồn khác nhau theo byte | 2.592 |
| Bản nháp có chữ / bản nháp rỗng | 2.404 / 417 |
| Vùng trong hàng đợi ưu tiên kiểm tra | 1.215 |

**2.821 là số vùng đã xử lý, không phải số dòng được xác nhận đọc đúng.** Bộ tách có thể trả cả vùng nhỏ, vùng không phải chữ hoặc vùng thiếu nét. Chưa có nhãn đầy đủ cho toàn bộ các trang nên chưa thể tính độ chính xác hay recall tách dòng của cả lô. Điểm thô của CRNN không được coi là xác suất đọc đúng.

Nhận diện dùng CRNN hiện có, chạy GPU trong môi trường riêng. Đã thêm tùy chọn `--device cpu/cuda` cho công cụ batch; CPU vẫn là mặc định. Cache được phân biệt theo thiết bị để không báo nhầm kết quả CPU thành lần chạy GPU. Không sửa cấu hình OCR của app, không gọi dịch vụ OCR đám mây.

## Nhãn được dùng để train

Chỉ nhận nhãn sau khi đối chiếu trang nguồn và ảnh cắt cụ thể. Codex thực hiện hai lượt nhìn; **chưa có giáo viên hoặc người duyệt độc lập xác nhận**. Không lấy bản nháp OCR làm đáp án, không sửa bài học sinh theo kết quả phép tính.

| Phần mới | Ô chữ/số | Trang nguồn được chọn | Vai trò |
|---|---:|---:|---|
| TRAIN | 42 | 6 | Chịu gradient |
| DEV | 7 | 2 | Chọn cấu hình/epoch |
| HOLDOUT chẩn đoán | 4 | 2 | Đánh giá sau khi khóa lựa chọn |

49 ô TRAIN/DEV gồm 12 ô số nguyên, 6 biểu thức, 3 biểu thức có đơn vị và 28 ô chữ. Bốn ô giữ riêng là văn bản. 25 ô nháp TRAIN/DEV và 4 ô nháp giữ riêng bị loại vì nét cắt sát, chữ/dấu chưa rõ hoặc lẫn dòng bên cạnh. Nhãn nháp ô `1046:11` được sửa từ `56` thành `36` sau khi nhìn lại nét chữ, không suy ra từ phép nhân.

**Không phải toàn bộ 136 ảnh đã được nhận vào tập train có giám sát.** Phần còn lại vẫn là dữ liệu chờ duyệt. Những bản nháp không nằm trong hàng đợi ưu tiên cũng chưa được tự động chấp thuận.

Chính sách chia v1 theo hash đã được giữ làm lịch sử và thay bằng v2 **trước khi chạy nhận diện thần kinh hoặc train**, vì nhìn ảnh thấy nhiều trang được chụp lại. V2 gộp theo họ trang/quyển, chia 121 ảnh TRAIN, 8 DEV, 7 HOLDOUT. Bản trùng byte/pixel luôn cùng phần. Không thấy trùng SHA với sổ dữ liệu đã kiểm tra; chưa chứng minh được độc lập người viết hay độc lập nội dung với toàn bộ dữ liệu cũ/pretraining.

## Huấn luyện và kết quả

Mỗi cấu hình học **741 ô TRAIN cũ + 42 ô mới**. Mỗi epoch đi qua đủ 741 ô cũ một lần, mỗi ô mới bốn lần; tổng 909 lượt mẫu/epoch. Giữ 61 ô cũ khỏi gradient để kiểm tra hồi quy; đây là tập phát triển đã dùng nhiều lần, không phải kiểm định nghiên cứu độc lập.

Model khởi tạo là ứng viên CRNN đủ 321 lớp đã có từ trước, kèm đúng vocabulary của nó. Đây **không phải** model production. Hai cấu hình đầu giữ CNN/BiLSTM cố định và học head; hai cấu hình sau học BiLSTM + head, giữ CNN cố định. CTC dùng chiều dài thực, không giải mã phần padding; KL chỉ giữ các dự đoán TRAIN khởi tạo đúng nhãn. Cache được đối chiếu đường giải mã với model đầy đủ.

| Cấu hình | Epoch / bước cập nhật | CER thấp nhất trên DEV mới | Số ô DEV đúng toàn bộ tại điểm đó | Kiểm tra dữ liệu cũ |
|---|---:|---:|---:|---|
| Khởi tạo trước đợt này | 0 | 8/120 ký tự = 6,67% | 2/7 | Mốc đối chiếu |
| Head, mức học thấp | 24 / 2.736 | 6,67% | 2/7 | Không đạt |
| Head, mức học vừa | 24 / 2.736 | 6,67% | 2/7 | Không đạt |
| BiLSTM + head, mức thấp | 16 / 1.824 | 6,67% | 2/7 | Không đạt |
| BiLSTM + head, mức vừa | 16 / 1.824 | 7/120 ký tự = 5,83% | 3/7 | Không đạt |

Nhật ký tốt nhất của cấu hình cuối có giảm lỗi DEV, nhưng làm sai thêm một dòng cũ trước đó đúng toàn bộ. Không epoch nào trong bốn cấu hình vượt kiểm tra hồi quy. Điểm trên 42 ô **đã train** tăng từ 23/42 lên 31/42 ở trọng số cuối cấu hình BiLSTM mức vừa; con số này thể hiện khả năng học tập train, **không chứng minh tổng quát hóa**.

Đã lưu bốn bộ trọng số thực sự đã học, optimizer, nhật ký từng epoch, hash dữ liệu/chính sách và số lượt đi qua mẫu. Các tệp `candidate.pth` được chọn cuối cùng quay về **epoch 0, giống hệt ứng viên khởi tạo**; không gọi việc quay về này là cải thiện do train mới.

Sau khi khóa lựa chọn mới mở phần giữ riêng cho suy luận: trên **4 ô/89 ký tự**, ứng viên được giữ có 6 lỗi ký tự (CER 6,74%), đúng toàn bộ 0/4 ô. Model production với cách resize gốc cũng có 6 lỗi ký tự nhưng khác kiểu lỗi. Đây là kiểm tra trên crop thủ công, không phải kết quả toàn bộ luồng app. Mẫu quá nhỏ và chỉ có văn bản; **không đủ kết luận về phân số, trang đầy đủ hay độ sẵn sàng thay model**. Phần giữ riêng này nay đã được xem kết quả, phải coi là chẩn đoán trong các đợt sau.

## Kiểm tra và bảo toàn

- **81 test passed**: nguồn ảnh, hướng ảnh, nhận diện batch, dữ liệu huấn luyện; có kiểm tra cache đổi thiết bị.
- **10 kiểm tra bổ sung passed**: tách TRAIN/DEV/guard, nhãn đủ điều kiện, nhóm trang/bản trùng, mất số 0, số bịa trong văn bản, dấu tiếng Việt và đơn vị.
- Đã đối chiếu lại 136 SHA ảnh nguồn sau khi chạy: không đổi.
- Checkpoint được chọn tải lại trên CPU cho cùng kết quả đã đo; không có gradient từ DEV/HOLDOUT.
- Production checkpoint vẫn là SHA-256 `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`; vocabulary production không đổi. Không sửa mô hình detector, giao diện, backend hoặc gói phụ thuộc ứng dụng.
- `git diff --check` qua. Thay đổi mã dùng chung chỉ ở công cụ batch và test tương ứng. Dữ liệu gốc, transcript và checkpoint ở vùng riêng bị Git bỏ qua; báo cáo này chỉ có số liệu tổng hợp.

## Tệp kết quả trên máy

Thư mục riêng: `E:/MathVisionKid/ai-training/datasets/drive_math/new2_20261027_136/`

- `line_predictions_all_136.csv`: vị trí vùng và bản nháp OCR đủ 136 ảnh, luôn đánh dấu chưa xác minh/không đủ điều kiện train.
- `review_queue.csv`: vùng rỗng, nhỏ hoặc điểm thô thấp để ưu tiên nhìn lại, không tự cấp nhãn.
- `annotations_reviewed.json`, `holdout_reviewed.json`: 53 nhãn crop và nguồn gốc đối chiếu.
- `training/`, `recurrent/`: chính sách cố định, trọng số đã train, optimizer, baseline và nhật ký.
- `final_selection.json`, `final_diagnostic.json`, `completed_summary.json`, `safety_checks.json`: lựa chọn, kết quả kiểm tra và bằng chứng bảo toàn.

## Phần cần làm tiếp để tiến tới thay model

Mở rộng nhãn trực tiếp trên các crop còn lại, ưu tiên chữ hoa cách điệu, dấu tiếng Việt, dòng nghiêng/cong và các số/toán tử dễ nhầm. Cần thêm nhãn toán/phân số đầy đủ và tập kiểm định có người duyệt độc lập, tách người viết/trang nguồn. Huấn luyện tiếp phải giữ các kiểm tra cũ và dùng phần kiểm định mới chưa xem để quyết định phát hành. **Trạng thái đợt này: `NOT_READY_FOR_PRODUCTION`.**

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng công cụ nguồn ảnh, detector, CRNN, CTC và kiểm tra sẵn có; tránh tạo hệ OCR mới hoặc đổi app khi chỉ cần thử train.
  - Applied to: thêm thiết bị cho batch với thay đổi nhỏ, tái dùng replay/cache, bốn thử nghiệm giới hạn và giữ nguyên model production khi không đạt.
