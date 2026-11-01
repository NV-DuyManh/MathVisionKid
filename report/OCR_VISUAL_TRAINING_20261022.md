# Huấn luyện tiếp OCR chữ/toán — 22/10/2026

Đã huấn luyện thật **hai ứng viên, mỗi ứng viên sáu epoch**. Cả hai kém đối chứng trên DEV và **bị loại**, không thay model đang chạy. Phần tử–mẫu chưa được cải thiện, chưa thể gọi kết quả là hoàn hảo hoặc dữ liệu nhãn đạt chuẩn nghiên cứu.

## Phạm vi train

- 501 vùng TRAIN đủ điều kiện từ 57 trang Drive. Hai vùng TRAIN mơ hồ tiếp tục cách ly, không nhận gradient. 95 vùng DEV giữ nguyên nhãn và pixel. Tổng hồ sơ nhận diện/kiểm chứng: 598 vùng từ 72 trang.
- Dùng checkpoint OCR toán thí nghiệm đã có `math_all_20261013/math_focus/run_control/candidate.pth` làm đối chứng. Đây là train CRNN nhận diện ảnh chữ/số toán, không phải train Qwen giải toán và không phải cập nhật trọng số production.
- Fine-tune khối Conv/GroupNorm cuối của CNN, BiLSTM và lớp đầu ra CTC. Ba khối CNN đầu giữ nguyên. Giữ nguyên vocabulary và preprocessing giữ tỷ lệ của thí nghiệm.
- 62 vùng tử/mẫu TRAIN được nhân trọng số 4; vai trò toán còn lại nhân 2. Mẫu TRAIN mà đối chứng sai chuỗi số/dấu nhân thêm 2. Không dùng lỗi từng mẫu DEV để gán trọng số train.
- Regularization KL trọng số 2 từ đối chứng trên 409 vùng TRAIN đọc đúng toàn chuỗi. Xác suất teacher là ràng buộc giữ hành vi, không thay nhãn nguồn hoặc tạo nhãn mới.
- Ứng viên `original` học ảnh gốc. Ứng viên `contrast` dùng trung bình hai loss CTC từ ảnh gốc và biến thể grayscale/autocontrast, chỉ trong TRAIN. Biến thể là góc nhìn bổ sung của cùng 501 vùng, không phải 501 nhãn độc lập mới.

Seed 20261022, batch 8, bốn luồng CPU; learning rate CNN cuối 1e-6, BiLSTM 2e-6, CTC 5e-6. Số epoch và hai cấu hình được đóng băng trong policy trước khi chạy. Chỉ chấm DEV sau khi lưu checkpoint cuối epoch 6, không đo DEV mỗi epoch hoặc chọn vòng đẹp nhất theo DEV.

Thời gian tiến trình đọc nguồn/trích đặc trưng/train/chấm cuối: **430,14 giây**. Không tính kiểm chứng lại, đọc đối chứng bổ sung, rà mã và viết báo cáo. Không cài lại runtime, không dùng GPU hoặc gọi model cloud.

## Kết quả cuối

| Chỉ số trên cùng 95 vùng DEV | Đối chứng toán riêng | `original` | `contrast` |
|---|---:|---:|---:|
| Lỗi ký tự / 1.097 ký tự tham chiếu | 105 | 111 | 111 |
| CER | 9,57% | 10,12% | 10,12% |
| Đúng toàn vùng | 53/95 | 50/95 | 49/95 |
| Lỗi số/dấu quan trọng | 30 | 32 | 33 |
| Đúng từng vùng tử–mẫu | 7/11 | 7/11 | 7/11 |

Hai ứng viên đều vi phạm ngưỡng kỹ thuật và có hồi quy ở nhóm biểu thức, chữ và trường hợp số có nhiều chữ số 0. Mỗi ứng viên có 11 lý do loại được lưu trong JSON. Không gọi kết quả chấm trên crop thủ công này là độ chính xác toàn bộ ứng dụng hoặc nhận diện phân số 2D hoàn chỉnh.

Trên TRAIN, lỗi ký tự giảm 190→178 cho cả hai ứng viên; đúng toàn vùng 409→411 ở `original` và giữ 409 ở `contrast`. **Học khớp TRAIN hơn không đồng nghĩa đọc ảnh DEV tốt hơn.** Lượt này cho thấy tiếp tục cập nhật các khối này trên nhóm nhỏ với hai cấu hình đã thử chưa khắc phục được khả năng tổng quát hóa. Chưa đủ bằng chứng quy nguyên nhân duy nhất cho số epoch, kiến trúc hay kích thước dữ liệu.

## Kiểm chứng

- Có kiểm tra thực thi riêng cho bộ tính loss/độ dài chuỗi, loại DEV/nhãn mơ hồ khỏi TRAIN, bảo toàn chữ số 0, tương đương dự đoán khi cache đặc trưng và chỉ cập nhật các khối được phép. Có bước backward và Adam thật trên dữ liệu kiểm tra tổng hợp; đây là kiểm chứng cơ chế, không phải bằng chứng chất lượng OCR.
- Bộ kiểm thử chuẩn bị dữ liệu/train/hướng ảnh/nhãn nháp đạt **66/66**. Lần gọi đầu từ thư mục gốc thiếu `PYTHONPATH`, gây bảy lỗi import `app`; đã chẩn đoán từ traceback và chạy lại với `PYTHONPATH=E:/MathVisionKid/ai/runtime;E:/MathVisionKid/scripts/data`, không sửa mã ứng dụng để né kiểm thử.
- Một tiến trình mới đọc lại 72 ảnh Drive, xác minh hash nguồn/crop và tái lập toàn bộ 598 dự đoán của đối chứng cùng mỗi ứng viên. Điểm TRAIN/DEV, danh sách tham số thay đổi và lý do loại khớp kết quả train.
- Chỉ 14 tensor thuộc CNN cuối/BiLSTM/CTC thay đổi; các tensor ba khối CNN đầu giống hệt đối chứng. Hash checkpoint, vocabulary production và các file che tên/cắt ảnh/thành phần UI được bảo vệ giữ nguyên.
- Không lấy ảnh, crop, ZIP hoặc Parquet gốc lưu vào dự án. Không đọc HOLDOUT, không tạo nhãn huấn luyện từ dự đoán, không sửa nhãn DEV hoặc tính đáp án để chữa chữ học sinh. Không commit/push/deploy.

**Bộ 18 đối chứng lịch sử bổ sung chưa chấm được hợp lệ trong lượt này.** Lượt HTTP tải nguyên gói quá chậm đã được dừng và lưu log; trước khi dừng có log đã suy luận 2/18 nhưng chưa lưu giả thuyết/điểm nên không dùng để kết luận. Lượt sau đọc các hàng cần thiết từ Drive G:, giới hạn 15 giây mỗi yêu cầu, ghi nhận 0/18 ảnh suy luận và 18 lỗi nguồn qua 12 nhóm. Lỗi từng nguồn chưa được lưu trước khi bộ tổng hợp điểm gặp lỗi so sánh hai CER `None`; không suy đoán rằng cả 18 nguồn đều lỗi vì cùng nguyên nhân.

Đã sửa recipe đánh giá để tập không có ảnh chấm trả về “accuracy unavailable” và từ chối thông qua, đồng thời lưu tiến độ đọc nguồn trước phần tính điểm. Ba kiểm tra thực thi bổ sung đạt: thiếu nguồn không có accuracy, bản đọc không đổi không hồi quy và mất chữ số 0 bị loại. **Không chạy lại 18 nguồn sau sửa trong lượt này**, không coi kiểm tra tổng hợp dữ liệu giả là chấm được ảnh thật. `controls-summary.json` giữ nguyên trạng thái chưa hoàn tất và log thất bại; không dùng kết quả lịch sử làm số đo mới. Các lỗi này thuộc đường đánh giá bổ sung, không làm thay đổi hai checkpoint hay kết quả train/kiểm chứng 598 vùng đã có.

## Quyết định và giới hạn nghiên cứu

**Không phát hành hai ứng viên này.** Giữ checkpoint và lịch sử để tái lập thí nghiệm, không dùng chúng thay model hiện tại. Danh sách hồi quy được giữ để rà lỗi, không chuyển thành nhãn TRAIN.

Hướng tiếp theo cần dựa vào thêm mẫu nguồn đã được rà nhãn, đặc biệt chữ số nét mảnh/tím và phân số có nhiều chữ số, cùng một tập đánh giá độc lập chưa dùng chọn phương pháp. Không đưa 11 vùng tử–mẫu DEV hiện có sang TRAIN để làm điểm đẹp lên. Hai vùng mơ hồ cần người rà soát xác nhận trước khi dùng huấn luyện.

DEV đã được dùng trong các vòng nghiên cứu trước; chưa chứng minh độc lập người viết/nguồn tiền huấn luyện. Hộp cắt và vai trò vùng là metadata đã rà từ trước, không chứng minh hệ thống tự phát hiện đúng mọi phân số trên ảnh toàn trang. Chưa có xác nhận nhãn độc lập từ giáo viên trong lượt này.

[Điểm, lịch sử loss và hash tổng hợp](ocr-visual-training-20261022/training-summary.json) · [Các trường hợp DEV bị hồi quy](ocr-visual-training-20261022/dev-regressions.json) · [Kiểm tra cuối](ocr-visual-training-20261022/verification.json) · [Đối chứng bổ sung](ocr-visual-training-20261022/controls-summary.json).

Thư mục thí nghiệm ngoài Git: `ai-training/datasets/drive_math/math_visual_retention_20261022/`. Có `train.py`, `policy.json`, hai checkpoint, 12 log epoch, `result.json`, `audit.json`, log train/audit và hồ sơ kiểm tra đối chứng. `train.py check` kiểm tra cơ chế; `train.py audit` chạy lại kiểm chứng nguồn/model trong tiến trình mới. Công cụ từ chối ghi đè kết quả, cần thư mục thí nghiệm mới nếu chạy lại.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng bộ đọc Drive, CRNN, CTC và metric hiện có cho thao tác huấn luyện được yêu cầu.
  - Applied to: recipe thí nghiệm riêng; không xây thêm subsystem hoặc thay hành vi ứng dụng.
- `superpowers:using-superpowers`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/using-superpowers/SKILL.md`
  - Why selected: định tuyến quy trình và đọc skill áp dụng trước công việc.
  - Applied to: chọn quy trình huấn luyện/kiểm chứng, giữ giới hạn người dùng đã yêu cầu.
- `superpowers:verification-before-completion`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/verification-before-completion/SKILL.md`
  - Why selected: cần bằng chứng chạy thật trước khi nói train hoàn tất hay ứng viên tốt hơn.
  - Applied to: kiểm tra checkpoint, tái lập dự đoán trong tiến trình mới, báo cáo kết quả xấu và không phát hành.
- `superpowers:systematic-debugging`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/systematic-debugging/SKILL.md`
  - Why selected: lỗi import khi chạy bộ kiểm thử và lỗi đọc đối chứng bổ sung cần phân biệt với lỗi model.
  - Applied to: xác định đường dẫn import thiếu từ traceback; ghi nhận riêng nguồn dữ liệu chưa đọc đủ.
