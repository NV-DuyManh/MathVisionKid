# NEW2: mở rộng nhãn, train chữ và số — 27/10/2026

**Đã có hai checkpoint mới thực sự thay đổi trọng số và cải thiện trong phạm vi đã đo.** Model chữ giảm hai lỗi dấu trên tập DEV; model số sửa ba trường hợp nhầm 3 thành 5 mà không làm sai thêm các mẫu số cũ được kiểm tra. **Chưa thay model trong app**: kiểm định độc lập còn thiếu và vẫn có lỗi ở ảnh ngoài tập train.

## Kết quả chính

| Phép đo | Trước đợt mở rộng | Checkpoint được chọn | Phạm vi |
|---|---:|---:|---|
| Chữ: lỗi ký tự DEV | 17/227, CER 7,49% | 15/227, CER 6,61% | 12 ô DEV, đã dùng chọn epoch |
| Chữ: đúng toàn bộ ô DEV | 3/12 | 4/12 | Không phải kiểm định độc lập |
| Chữ: lỗi trên dữ liệu cũ + chẩn đoán cũ | 61/672 ký tự | 61/672 ký tự | 65 ô; không mất ô trước đó đúng |
| Số: ô mới đúng toàn bộ | 46/49 | 49/49 | **TRAIN**, không phải độ chính xác ngoài mẫu |
| Phân số ghép thủ công từ ô số | 11/13 | 13/13 | **TRAIN**, biết trước vị trí tử/mẫu |
| Số: tập cũ thứ nhất | 58/65 đúng; 8/187 lỗi ký tự | Giữ nguyên | VAL đã dùng nhiều lần |
| Số: tập cũ thứ hai | 19/22 đúng; 3/63 lỗi ký tự | Giữ nguyên | VAL đã dùng nhiều lần |
| Số: DEV bổ sung | 1/2 đúng; 1/5 lỗi ký tự | Giữ nguyên | Chỉ hai ô, chưa đủ đại diện |

Hai thay đổi chữ quan sát được là “củ bước” → “cứ bước” và “mữ” → “mỡ”. Một lỗi khác trong cùng dòng vẫn còn; không gọi đoạn đó là đã đọc hoàn toàn đúng. Model số cũng còn lỗi trên một ô DEV bổ sung. Tỷ lệ 49/49 và 13/13 ở trên **không được quảng bá thành khả năng đọc hoàn hảo ảnh mới**.

## Dữ liệu và phát hiện trùng nguồn

- Duyệt thêm 62 crop TRAIN và 5 crop DEV từ ảnh nguồn và ảnh cắt; không lấy dự đoán làm đáp án. Thêm hai crop số DEV sau lượt nhìn lại riêng. Cùng Codex duyệt; chưa có giáo viên/người duyệt độc lập xác nhận.
- Bộ kiểm tra chặn hai crop mới ở trang 1022 vì nguồn byte trùng với ảnh thuộc phần kiểm tra cũ. Chặn cả họ trang `chicks_story` khỏi phần TRAIN mở rộng; lần freeze thất bại được giữ làm bằng chứng và chưa chạy gradient.
- Sau khi loại hai crop đó: **102 crop NEW2 TRAIN trên 13 nguồn, 12 crop chữ DEV trên 3 nguồn**. Trong 102 crop có 49 crop số, gồm 26 tử/mẫu của 13 phân số; không đổi phân số xếp dọc thành một dòng nhãn giả.
- Đối chiếu trực tiếp hai policy chữ/số cũ tìm thấy **5 ảnh mới trùng với 4 nguồn byte cũ**: hai ảnh trùng với phần kiểm tra và ba ảnh trùng với TRAIN. Những nguồn đã ở TRAIN cũ không phải dữ liệu người viết mới độc lập.
- Kết quả “không trùng” ở lần dò `ledger.sqlite3` trước chỉ đúng trong phạm vi sổ đó. Sổ không đại diện đầy đủ cho các policy huấn luyện lịch sử. Kết quả đối chiếu trực tiếp được lưu riêng và là căn cứ chặn train đợt này.
- Bốn crop giữ riêng của đợt trước nay là **chẩn đoán đã lộ kết quả**, chỉ dùng làm guard bổ sung. Không đưa chúng vào TRAIN và không gọi là kiểm định mới.

Ảnh gốc và các báo cáo đã khóa trước đây được giữ nguyên. Nhãn, crop, transcript và checkpoint tiếp tục nằm ở vùng dữ liệu riêng bị Git bỏ qua.

## Huấn luyện thực và lựa chọn

Đợt này hoàn thành **7 cấu hình, 184 epoch, 29.024 bước cập nhật gradient**; số bước là khối lượng công việc, không phải thước đo chất lượng.

1. **Ba cấu hình chữ**: 843 crop TRAIN, gồm 741 crop cũ + 102 NEW2. Mỗi epoch đi đủ dữ liệu cũ một lần và crop NEW2 hai lần. Chỉ cập nhật các hàng head cho nguyên âm/dấu và chữ hoa hoặc chữ cái; CNN/BiLSTM, chữ số, dấu câu, blank và x/X cố định. Cấu hình được chọn `accent_low`, epoch 4, vượt guard và cải thiện DEV. Hai kiểu mask khác vẫn được chạy đủ và lưu kết quả.
2. **Hai cấu hình số không khóa lớp**: 1.450 crop TRAIN, gồm 1.401 crop cũ + 49 NEW2. Đọc đúng 49/49 crop mới nhưng làm mẫu cũ `+12` thành `712`; **loại cả hai**, lựa chọn của giai đoạn này quay về parent epoch 0.
3. **Hai cấu hình số chỉ cập nhật lớp 3/5**: giữ cố định CNN/BiLSTM và tất cả hàng head còn lại, gồm blank và toán tử. Chọn `digits_35_low`, epoch 21. Không phát sinh lỗi mới trên 65 + 22 mẫu số cũ hoặc hai ô DEV bổ sung; sửa được ba nhầm 3/5 trên TRAIN. Việc chọn giữa các trạng thái có xét mức khớp TRAIN khi VAL hòa nhau, nên đây là **ứng viên đã học tốt hơn**, chưa phải bằng chứng tổng quát hóa.

Teacher KL chỉ nhận những dự đoán TRAIN khởi tạo đúng toàn bộ nhãn; không giữ dự đoán sai làm mục tiêu và không có gradient từ DEV/VAL/guard. Cache dùng đúng đường CNN và BiLSTM có chiều dài thực, đối chiếu trước khi học. Hai checkpoint được chọn đã tải lại bằng CPU và tái tạo đúng các dự đoán được lưu; encoder và các hàng head bảo vệ giữ nguyên bit.

## Nguồn HME-VAS và kiểm tra hash

Nguồn số cũ được khôi phục bằng ảnh và nhãn gốc ở commit cố định `bb610aa67e9c8fda71ce1416a0068521f8274bee`. Một lần chạy dừng vì byte tải về không khớp SHA đã khóa, **trước khi có gradient**. Lần chạy lại dùng bộ tải có kiểm tra hash và thử lại giới hạn, không bỏ qua bất kỳ kiểm tra ảnh, nhãn hay crop nào. Lần chạy thành công không cần dùng nhánh retry cho ảnh sai hash; nguyên nhân đáp ứng sai ở lần trước chưa xác định chắc chắn.

Ảnh và crop khôi phục chỉ giữ trong RAM. Nhãn ký hiệu gốc có schema provenance riêng và được kiểm tra commit, hash nhãn, pixel/crop cùng việc không chứa ký hiệu bị loại; không giả định chúng có trường `review_status` của nhãn crop mới.

## Phân số tự tách: giữ đủ kết quả, không đổi chuẩn để làm đẹp điểm

Đo trên hai trang TRAIN có **13 cặp được đánh dấu một phần**, không đủ nhãn để tính precision toàn trang. Ghép vị trí bằng hình học/nét bút; giá trị dự đoán chỉ được dùng chấm đúng sau khi ghép.

| Giao thức | Hình học gốc + model số cũ | Chia tile thử nghiệm + model số cũ | Hình học gốc cố định + model số mới |
|---|---:|---:|---:|
| Min IoU tử/mẫu ≥ 0,5: ghép được / đúng toàn cặp | 4/13 / 3/13 | 0/13 / 0/13 | 4/13 / 4/13 |
| Chẩn đoán nét bút bổ sung: ghép được / đúng toàn cặp | 12/13 / 11/13 | 9/13 / 7/13 | 12/13 / 12/13 |

Ảnh overlay cho thấy crop tự tách số 1 hẹp hơn nhiều so với khung nhãn cắt tay, nên IoU bị ảnh hưởng bởi lề trống. Vì vậy thêm **một giao thức chẩn đoán sau khi xem kết quả**, yêu cầu bao phủ ≥90% nét bút tham chiếu và ≥80% nét trong khung dự đoán nằm trong vùng nhãn, ghép một-một. Mask màu và ngưỡng được khóa trước khi tính giao thức bổ sung. Giữ nguyên toàn bộ điểm IoU cũ; không thay nó bằng điểm nét bút để tuyên bố đạt kiểm định.

Phương pháp chia tile bị loại vì kém hơn cả theo IoU và giao thức nét bút. Lần chấm model số mới giữ đúng **50 proposal hình học gốc**, không sửa vị trí theo đáp án. Các kết quả này chỉ là chẩn đoán TRAIN và cơ sở thiết kế benchmark tiếp theo, chưa phải đánh giá end-to-end trên ảnh chưa thấy.

## Kiểm tra và tệp bàn giao

- **81 test passed** cho nguồn ảnh, hướng ảnh, batch OCR và dữ liệu train. `git diff --check` qua.
- Kiểm tra riêng qua: tách nguồn TRAIN/DEV, nhãn ký hiệu, mask optimizer 3/5, cập nhật chỉ hàng cho phép, chặn `+12` → `712`, không dùng DEV làm TRAIN.
- Model production và vocabulary vẫn đúng hash ban đầu; không đổi code app, detector, TTS hoặc phụ thuộc. Không commit/push.
- Trạng thái: **`CANDIDATES_IMPROVED_NOT_RELEASED`**. Không tuyên bố đã huấn luyện có giám sát toàn bộ 136 ảnh.

Thư mục riêng: `E:/MathVisionKid/ai-training/datasets/drive_math/new2_20261027_136/`

| Tệp/thư mục | Nội dung |
|---|---|
| `candidate_bundle_v2.json` | Hai checkpoint/vocabulary đúng cặp, hash, tiền xử lý, giới hạn sử dụng |
| `expansion_v2/result.json` | Ứng viên chữ, epoch chọn, số liệu và kiểm tra CPU |
| `numeric_masked_v3/result.json` | Ứng viên số 3/5, kết quả các scope và 13 cặp TRAIN |
| `numeric_expansion_v2/` | Hai thử nghiệm số bị loại, giữ trọng số cuối và optimizer |
| `expansion_v2/historical_overlap_audit.json` | Đối chiếu trùng nguồn với policy lịch sử |
| `expansion_v2/fraction_candidate_audit.json` | Model số mới trên proposal cố định |
| `numeric_masked_v3/recovery_retry_result.json` | Bằng chứng lần khôi phục nguồn thành công |

Model số 13 lớp chỉ dành cho **vùng số có căn cứ**, không thay model chữ trên văn bản hoặc tự hiểu toàn bộ phân số/trang. Muốn thay trong app cần tập kiểm định mới chưa xem kết quả, người duyệt độc lập, kiểm tra tách dòng/tử–mẫu và mẫu đa dạng người viết. Điểm yếu còn lại gồm chữ hoa uốn nét, dấu, số ngoài mẫu và sự khác nhau giữa khung nhãn có lề với nét thực. Không chuyển DEV đang sai sang TRAIN để làm đẹp báo cáo.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: dùng lại CRNN, CTC, bộ khôi phục ảnh, mask head và kiểm tra đã có; tránh đổi app hoặc dựng hệ OCR mới.
  - Applied to: mở rộng nhãn có truy vết, các thử nghiệm giới hạn, khóa lớp để xử lý hồi quy, bảo toàn checkpoint cũ và báo cáo phép đo riêng biệt.
