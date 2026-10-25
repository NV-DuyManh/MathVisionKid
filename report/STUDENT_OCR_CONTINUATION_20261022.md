# Tiếp tục UI Student và train OCR toán — 22/10/2026

[Xem giao diện mới](student-recording-20261022/index.html) · [Bằng chứng train](student-recording-20261022/ocr-training.json).

## Kết quả

Đã chỉnh màn ghi âm/chờ hỏi bài và huấn luyện thật bốn ứng viên CRNN OCR, mỗi ứng viên tám epoch. **Cả bốn chưa vượt đối chứng, không thay model đang chạy.** Đây là train nhận diện chữ/số toán từ ảnh, không phải fine-tune model Qwen giải toán.

## UI Student

- Khối đang ghi âm có biểu tượng mic, thời gian thực trên 30 giây và thanh tiến độ. Không tạo sóng âm giả hoặc hiệu ứng nhấp nháy.
- Nói xong là hành động chính; Hủy ghi âm là nút chữ nhẹ hơn.
- Chuyển giọng thành chữ, đọc câu hỏi và dừng mic có trạng thái chờ rõ ràng; nội dung chờ căn giữa vùng còn lại.
- Nhãn ô nhập gọn hơn, hiện số ký tự khi gần giới hạn 500. Giữ nội dung để học sinh sửa trước khi gửi; không gửi tự động.
- Không thêm popup xác nhận, không đổi che tên/cắt ảnh hoặc các thành phần được bảo vệ.

Lượt kiểm tra này có 14 kiểm thử trực tiếp của hỏi bài/bản ghi, TypeScript và ESLint. Bộ 880 kiểm thử toàn Student đã đạt ở lượt hoàn thiện trước; không trình bày đó là bộ chạy lại của lượt này. Có 30 ảnh mới tại năm kích thước, kiểm tra ghi âm thật trong trình duyệt bằng mic giả lập, chuyển chữ/chờ trả lời bằng phản hồi cô lập, không tràn ngang/ảnh hỏng/nút vượt mép ngang/lỗi JavaScript. Kết quả ở `student-recording-20261022/visual-qa.json`. Không có bằng chứng điện thoại vật lý.

Web export và Android/iOS Hermes export đã thành công sau lần chỉnh cuối; log trong `student-recording-20261022/export-web.log` và `export-native.log`. Cấu hình QA chỉ đặt trong tiến trình build, không đổi cấu hình deploy thật. Trang xem ảnh đã kiểm tra đủ 30 ảnh qua năm nút chọn kích thước. Hash của privacy, crop, AppHeader, AppButton và theme còn nguyên theo baseline; xem `protected-after.json`.

## Phạm vi train thật

- Đọc 72 nguồn gốc trên ổ Drive G:, nhận diện 598 vùng. Không sao chép ảnh gốc, crop, ZIP hay Parquet vào dự án.
- TRAIN đủ điều kiện: 501 vùng; hai vùng nhãn mơ hồ tiếp tục cách ly, không nhận gradient. DEV: giữ nguyên 95 vùng, nhãn, nguồn và hộp cắt. Nguồn HOLDOUT bị loại trước khi đọc ảnh.
- Giữ nguyên phân chia theo hash trang/nhóm nguồn, kiểm tra hash pixel theo các hồ sơ trước. Không lấy dự đoán làm nhãn hoặc tính đáp án để sửa nét học sinh.
- Đầu vào là checkpoint đối chứng riêng `math_focus/run_control/candidate.pth`, cùng vocabulary thí nghiệm. Các điểm dưới là so sánh trong thí nghiệm, không phải đo chính xác toàn bộ pipeline production.

Lần này thử tích lũy gradient của cả 501 mẫu TRAIN trước mỗi bước cập nhật để giảm ảnh hưởng thứ tự minibatch. CNN/BiLSTM giữ nguyên; chỉ linear CTC thay đổi. Batch 8, tám epoch, mỗi epoch một bước Adam, learning rate 1e-5 hoặc 3e-5, seed 20261022, bốn luồng CPU. Không augmentation hoặc gọi API AI.

Regularization KL có trọng số 2, chỉ dùng 409 mẫu TRAIN mà đối chứng khớp toàn dòng. Phân bố teacher là regularization, không phải nhãn mới. Nhân thêm trọng số cho các mẫu TRAIN có chuỗi quan trọng đọc sai; không dùng lỗi DEV để gán trọng số train.

Lượt đầu `math_batch_stability_20261022` có danh sách vai trò chưa khớp schema: thực tế chỉ 164 vùng `expression` được hưởng hệ số vai trò toán. Khi phát hiện, giữ nguyên hồ sơ và trọng số lượt đầu; tạo lượt thứ hai `math_batch_roles_20261022` dùng hằng `MATH_TRAIN_ROLES` hiện có, bao phủ 343 vùng TRAIN thuộc các vai trò toán. Không sửa lịch sử hoặc gọi lượt đầu là bao phủ mọi vai trò toán.

Hai tiến trình train hoàn tất lần lượt trong 33,02 và 32,28 giây, gồm đọc/trích đặc trưng/train/suy luận. Đây là số đo trên nhóm nhỏ và máy hiện tại; không gồm rà mã, audit riêng hay viết báo cáo. PyTorch cài hiện tại là CPU (`cuda=False`) dù máy có GPU; không cài lại runtime hoặc dùng GPU/Colab trong lượt này.

## DEV không đổi

| Chỉ số trên 95 vùng | Đối chứng riêng | Cả bốn ứng viên được chọn |
|---|---:|---:|
| Lỗi ký tự / 1.097 | 105 | 106 |
| CER | 9,57% | 9,66% |
| Lỗi chuỗi chữ số/dấu / 432 | 30 | 31 |
| Khớp toàn dòng | 53 | 52 |
| Khớp chuỗi quan trọng / 87 | 64 | 63 |
| Được chấp nhận | Mốc so sánh | Không |

Epoch được chọn đều là epoch 1. Các epoch sau không vượt gate; không hạ ngưỡng để lấy model. Gate yêu cầu tối đa 105 lỗi ký tự, tối đa 29 lỗi chuỗi quan trọng, ít nhất 53 dòng khớp toàn bộ và 64 dòng khớp chuỗi quan trọng, không hồi quy theo vai trò hoặc làm sai chuỗi nhiều số 0 vốn đúng.

Cả bốn đọc `300 cm² = 3 dm²` thành `30 cm² = 3 dm²`, làm sai một biểu thức số 0 vốn đúng. Hàng chờ mới của mỗi bản learning rate nhỏ có 134 vùng chưa khớp được chấm cộng hai vùng cách ly; bản learning rate vừa có 133 vùng chưa khớp cộng hai vùng cách ly. Toàn bộ vùng lỗi cũ trong nhóm 598 vẫn được nhận diện, không chỉ mẫu mới.

Trên TRAIN, khớp toàn dòng tăng từ 409 lên 410/411 tùy bản, lỗi chuỗi quan trọng vẫn 57. Đây là điểm trên dữ liệu vừa dùng huấn luyện, không chứng minh tổng quát hóa. DEV đã dùng nhiều lần; không phải kiểm định độc lập. Chưa biết mức độc lập người viết và trùng dữ liệu pretrain.

## Kiểm chứng trọng số và nguồn

Mỗi lượt có một tiến trình audit mới: đọc lại 72 nguồn Drive, dựng lại 598 crop trong RAM, tái lập đúng mọi dự đoán đối chứng/ứng viên, DEV/TRAIN và quyết định loại. Chỉ `fc.weight`, `fc.bias` thay đổi; trọng số hữu hạn; checkpoint/vocabulary production giữ nguyên hash. Không có ảnh gốc trong hai thư mục thí nghiệm mới.

Artifact riêng được Git bỏ qua:

- `ai-training/datasets/drive_math/math_batch_stability_20261022/`
- `ai-training/datasets/drive_math/math_batch_roles_20261022/`

Mỗi thư mục có `train.py`, `policy.json`, 16 bản ghi epoch, hai checkpoint, `result.json`, `audit.json`, `remaining_review_queue.json`. Bản tóm tắt công khai trong repo giữ metrics, hash và gate, không chứa ảnh nguồn. SHA-256 production: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.

## Dữ liệu Qwen trên Drive

Đã đọc metadata thư mục do chủ dự án đưa và `MathVisionKid_CLOUD_STATE.json`, cập nhật nguồn lúc 12:39:32 UTC ngày 22/10/2026. Đây là trạng thái được lưu trên Drive, **không phải lượt kiểm tra trực tiếp Colab**.

Snapshot ghi `TRAINING_DATASET_READY=false`, `training_started=false`; kiểm tra toàn kho token/liên kết/tách split chưa xong, còn một issue `SOURCE_SPLIT_MISSING_OR_UNKNOWN`. Quan sát Colab lưu gần nhất nói đang chạy data-only, chưa tải trọng số. Không sửa notebook, điều khiển phiên đó hay nhận công việc của phiên khác là kết quả của lượt này.

Không bắt đầu fine-tune Qwen trên kho lớn khi các điều kiện dữ liệu còn thiếu, không cắt cụt dữ liệu để ép train, không đọc/sửa checkpoint SQLite 3,4 GB hoặc tải cả kho. Snapshot rút gọn: `student-recording-20261022/drive-readiness.json`. Dữ liệu mới/đếm nhiều dòng không đồng nghĩa model đã được train hoặc tốt hơn.

## Trạng thái và việc tiếp theo

Đã hoàn tất lượt train OCR có đo trước/sau và giữ cả bốn ứng viên riêng. Không thay model production, không commit/push/deploy. Cần bổ sung nhãn TRAIN kiểm tra từ ảnh gốc cho các dạng còn sai và có bộ đánh giá độc lập trước khi thay production; kết quả hiện tại không ủng hộ tiếp tục tăng epoch trên cùng nhóm rồi coi loss giảm là cải thiện.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: hoàn thiện bố cục và phản hồi lúc ghi âm/chờ.
  - Applied to: phân cấp Nói xong/Hủy, thời gian/thanh tiến độ thật và ảnh responsive.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native/web ở màn hỏi bài.
  - Applied to: trạng thái chờ suy ra từ phase hiện có, giữ vòng đời ghi âm và API.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: dùng lại pipeline OCR và UI đang có.
  - Applied to: CTC head nhỏ, bộ chấm/đọc Drive/đối chứng hiện có, không thêm dependency.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.22/skills/google-drive/SKILL.md`
  - Why selected: xác định tình trạng nguồn dữ liệu model trên Drive.
  - Applied to: chỉ đọc danh sách file và snapshot readiness, không sửa/chia sẻ/xóa file Drive.

Chưa có skill chuyên OCR/training trong registry dự án; các kết quả train dựa trên pipeline có sẵn và kiểm tra mới ở trên.
