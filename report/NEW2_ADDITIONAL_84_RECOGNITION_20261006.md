# Nhận diện 84 ảnh mới NEW2 — 2026-10-06

Đã xử lý **84/84 ảnh mới 648.jpeg–731.jpeg** bằng bộ phân vùng hiện có và model
CRNN tại máy. Không có lỗi thực thi; mọi ảnh đều có vùng ứng viên. Kết quả này
**không chứng minh khung hoặc bản chép chữ đều đúng**. Rà soát trực quan vẫn thấy
sót chữ đơn lẻ, khung phân mảnh/gộp dòng, chữ trang bên cạnh và logo nền.

Lượt này là kiểm thử và curation dữ liệu. Trọng số và code ứng dụng giữ nguyên;
không huấn luyện, không suy ra kết quả trên điện thoại từ chạy hàm Python.

## Phạm vi và nguồn

- 84 ID mới đã đổi tên trong NEW2/IMG, tiếp nối ảnh 647.
- 84 ảnh RGB khác nội dung, không trùng pixel với ledger cũ; tổng 17.560.427 byte.
- Metadata lấy bằng Google Drive connector. Liên kết raw-file của connector
  trả HTTP 403 ở máy; tải byte gốc qua đường public của đúng các ID đã xác nhận.
  Kích thước byte khớp metadata, lưu SHA-256 từng nguồn.
- Đã xem 14 contact sheet, phủ toàn bộ 84 ảnh, và xem trực tiếp ảnh/crop tham chiếu.
  Phân loại chủ đề bằng rà soát: **70 ảnh luyện chữ/nét/Tiếng Việt, 14 ảnh toán**.
  Đây không phải 84 đề toán độc lập.
- Hai ảnh 724/725 là hai góc chụp cùng trang viết; đã ghi chung family để sau này
  không chia sang hai tập training/evaluation khác nhau.
- Batch riêng: `ai-training/datasets/drive_math/new2_20261006_84/`.
  Ảnh, bản chép và nhãn riêng tư nằm trong thư mục đã được Git ignore.

## Kết quả thực thi

| Kiểm tra | Kết quả |
| --- | ---: |
| Tải/giải mã nguồn | 84/84 |
| Phân vùng dòng, tối đa 200 vùng/ảnh | 84/84, 0 lỗi |
| Ảnh có vùng ứng viên | 84 |
| Tổng vùng ứng viên | 3.447 |
| Số vùng lớn nhất trong một ảnh | 170 |
| Ảnh vượt giới hạn hoặc khung ngoài ảnh | 0 |
| Phân vùng p95 trên máy này | 539,38 ms |
| CRNN chạy trên toàn bộ khung ứng viên | 84/84, 0 lỗi |
| Khung có bản chép khác rỗng sau trim | 2.200/3.447 |
| Khung cho bản chép rỗng/whitespace | 1.247 |
| Nguồn mới ghi trạng thái đã kiểm thử | 84 |

p95 chỉ đo hàm phân vùng, không gồm tải ảnh, CRNN, HTTP hoặc cloud.
Khung khác rỗng và điểm softmax không phải độ chính xác.
CRNN được gọi trực tiếp bằng `CrnnOcrProvider` để kiểm thử trọng số của chủ dự án,
CPU, micro-batch 4. Không coi việc gọi trực tiếp này là bằng chứng luồng đọc đề
trong app đã chuyển sang CRNN; luồng notebook vẫn dùng provider cloud.

Trọng số CRNN SHA-256:
`a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`.
Vocabulary SHA-256:
`6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`.
Text detector SHA-256:
`03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587`.
Hash code và từng ảnh được lưu trong các kết quả riêng.

## Nhãn và kiểm tra chất lượng

- 84 nhãn toàn ảnh giữ `needs_review`, `training_eligible: false`.
  Thêm ghi chú rà soát và nhóm chủ đề, không biến khung dự đoán thành ground truth.
- Đã chép tham chiếu thủ công **16 dòng được chọn ở 2 ảnh** để đối chiếu.
  NFC + trim, giữ dấu/case/dấu câu: 31 chỉnh sửa trên 271 ký tự, CER **11,44%**;
  5/16 dòng khớp chính xác. Đây là kiểm tra nhỏ, có chủ đích, gồm lỗi crop của
  pipeline; **không phải CER toàn bộ 84 ảnh, kết quả held-out hoặc CER model thuần**.
  Không nâng hai ảnh này thành nhãn toàn ảnh đã duyệt.
- Đếm tham chiếu cho bốn crop đã xem độc lập, chỉ áp dụng đúng SHA và phạm vi crop:

| Ảnh | Dòng chữ học sinh trong crop | Vùng tìm được |
| --- | ---: | ---: |
| 648 | 16 | 16 |
| 651 | 11 | 12 |
| 652 | 14 | 14 |
| 655 | 14 | 17 |

Crop 648/652 tránh được chữ nền và đúng số dòng; 651 còn khung dấu tách riêng,
655 còn khung mảnh/đường kẻ và chồng lấn. Đúng số dòng ở hai crop không chứng minh
hình học hoặc bản chép đúng. Crop tham chiếu chỉ được duyệt đếm; chưa duyệt geometry.
Đây là bằng chứng cho lợi ích và giới hạn của chọn vùng bài, không phải thay đổi
bộ dò của ứng dụng.

Nhóm ca khó tiêu biểu được giữ:

- 675, 677, 687–691, 701–702, 707: chữ/nét đơn lẻ bị sót hoặc chỉ lấy một phần.
  702 vẫn có chữ rõ nhưng chỉ trả 2 vùng, nên không được tính là nhận đúng.
- 660–674: nhiều cột ký tự rời; cần phân biệt dòng vật lý với ô chữ trước khi
  dùng số vùng làm mục tiêu.
- 648, 655, 659 và một số ảnh toán: chồng khung/gộp lời văn, chữ ở trang bên,
  đường kẻ hoặc logo.
- 720, 721, 728–730: gạch xóa, ghi đè và sửa bằng mực khác; giữ đúng lỗi học sinh,
  không suy ra ký hiệu chuẩn bằng cách tự giải.

Danh sách này là rà soát ưu tiên, không phải tỷ lệ lỗi đã đo trên cả tập.
Không ảnh nào bị xóa khỏi Drive hoặc loại chỉ vì model chưa đọc được.

## Luồng đọc bài toán cloud

Lượt đầu trả 18 ảnh ngoài toán là `UNREADABLE`, sau đó dừng vì primary rate limit
và fallback gián đoạn. Sau thời điểm retry đã ghi, kiểm thử riêng 14 ảnh toán;
lượt này cũng từng dừng, sau cooldown tiếp tục và hoàn thành **14/14**.

- 7 `WORK`, tổng 102 dòng chép; các kết quả WORK có `needsProblem: true`.
- 7 `MULTIPLE`, nội dung rỗng theo hợp đồng chọn một bài.
- Tổng 32 ID có response cloud thành công: 18 ngoài toán và 14 toán.
  52 ảnh ngoài toán còn lại đã chạy local/CRNN và được rà soát chủ đề, chưa gọi
  tiếp cloud. Không mô tả chúng như 84 lần đọc cloud thành công.
- Response thành công hoặc MULTIPLE không phải nhãn OCR được xác minh.
  Chưa đo CER cho bản chép cloud.
- Rà soát phân loại xác nhận ba ca cần sửa: **723** có ba phép chia độc lập,
  **726** có năm phép chia độc lập, **729** có ít nhất ba nhóm bài đánh số;
  cloud lại trả `WORK`. Theo hợp đồng hiện tại các ảnh này cần `MULTIPLE`.
  Lưu `math_cloud/manual_outcome_review.json` để kiểm thử regression sau này.
  Chưa triển khai một heuristic phân loại rộng chỉ dựa trên các ảnh này.

## Bằng chứng và kiểm tra cuối

- `source_selection.json`, `downloads.json`: danh tính, hash, kích thước và nguồn.
- `local_regions/`, `local_overlays/`, `local_summary.json`: phân vùng production.
- `crnn_results/`, `crnn_summary.json`: bản chép thực của trọng số CRNN.
- `visual_review_notes.json`, `review_manifest.csv`, `review_sheets/`: rà soát 84 ảnh.
- `ocr_spot_checks.json`, `crop_checks/comparison.json`: tham chiếu giới hạn theo scope.
- `cloud_results/`, `math_cloud/cloud_results/`: kết quả đọc app riêng.
- Ledger có **83.733 nguồn**, thêm đúng 84 ID; kiểm tra hash nguồn và ledger khớp.
  84 overlay giải mã được; file tạm chứa liên kết tải đã được gỡ.
- **14 test công cụ dữ liệu đạt**:
  `scripts/data/test_drive_line_batch.py`, `scripts/data/test_archive_audit.py`.
  Hash/tọa độ/đếm nguồn kiểm tra bằng assert.
- Không chạy lại regression toàn ứng dụng vì code ứng dụng không đổi.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse the existing OCR and resumable audit tools.
  - Applied to: local batch, bounded CRNN inference, private review helpers and focused checks.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: acquire the owner's new Drive sources with file identity provenance.
  - Applied to: metadata, original acquisition and preservation of source organization.
