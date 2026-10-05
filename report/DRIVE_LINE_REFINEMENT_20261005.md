# Kiểm kê Drive và cải thiện nhận diện dòng — 2026-10-05

Báo cáo này ghi kết quả của runtime12. Bằng chứng đầy đủ trước lượt cải
thiện tiếp theo đã được đóng băng trong
`infra/local-runtime/logs/line-refine-round2-20261005/runtime12-baseline.zip`
(129.086 tệp, SHA256 `bc76b58ff8f1398b6fbf93e546daed3454503c84d8ba6407a245c927d95113bd`).
Các thư mục kết quả chuẩn tại máy có thể được cập nhật bởi lượt tiếp theo;
số liệu lịch sử bên dưới đối chiếu với bản đóng băng này.

## Phạm vi

Kiểm kê mới thư mục Drive C1SE.01 do chủ dự án cung cấp, tải ảnh nguồn,
loại bản trùng theo nội dung pixel và chạy đường phân vùng cục bộ thật.
Giữ nguyên ảnh, nhãn đã duyệt và trọng số model. Thư mục mã Skill, model và
tài liệu không được coi là tập ảnh học sinh để huấn luyện.

| Nguồn | Đã lấy đủ |
| --- | ---: |
| Ảnh | 279 ảnh |
| Toán lớp 4 | 86 ảnh |
| Toán lớp 5 / IMG | 173 ảnh |
| NEW2 / IMG | 647 ảnh |
| Bộ ảnh toán hỗn hợp | 93 ảnh |
| datatrain / train | 19.144 ảnh |
| 8 tệp Parquet | 60.247 ảnh nhúng |
| ẢnhQuanTrọng | 5 ảnh tham chiếu |

Các ảnh cắt trong ZIP sạch được đối chiếu với bộ nguồn đã giữ tại máy;
giữ riêng ảnh kiểm tra âm từ lần trước. 1.278 ID ảnh trang vở hiện trên Drive
hợp với 3.279 nguồn kiểm tra trước thành 4.205 ảnh pixel khác nhau; có 48
ID trùng nội dung trong tập hợp 4.253 danh tính nguồn này. NEW2 có 647 ID,
614 nội dung ảnh khác nhau và 33 bản trùng. Không loại ảnh chỉ vì detector
trả rỗng.

Kiểm kê chéo có **83.649 danh tính nguồn, tương ứng 64.457 nội dung ảnh
khác nhau**: 20.427 ID ảnh độc lập trên Drive, 2.975 mục ảnh trong ZIP và
60.247 hàng ảnh nhúng trong Parquet. Toàn bộ 19.144 ảnh trong `train`
trùng byte với ảnh Parquet, nên không chạy lại cùng một ảnh để tăng số liệu.
Danh sách alias giữ từng nguồn và ánh xạ tới kết quả kiểm tra ảnh chuẩn.

## Thay đổi đã triển khai

- Giữ dấu rời ở cuối dòng ngắn khi thân chữ và vị trí dòng có bằng chứng
  độc lập; không dùng dấu yếu để tạo ra một dòng mới. Ca “là:” đã giữ dấu
  hai chấm bị cắt mất ở bản trước.
- Với nền màu đặc, chỉ chặn khung giả khi bộ phát hiện chữ cục bộ cũng
  không tìm thấy chữ. Khi model chưa sẵn sàng hoặc có vùng chữ, giữ đường
  xử lý hiện có. Các ảnh cắt sát và ảnh nhỏ không bị chặn theo quy tắc này.
- Khôi phục dải chữ màu bị bỏ sót bằng thành phần thân chữ, giữ dấu và
  biểu thức; loại đường kẻ, chấm rời và họa tiết đặc khỏi bằng chứng.
- Với một dòng cắt rất thấp (8–31 pixel), chỉ mở đầu/cuối khung khi thân
  chữ độc lập và model cùng xác nhận. Giữ nguyên số dòng và biên dọc;
  tám ca đã xem trực tiếp được khôi phục đúng trong đường xử lý bản cuối.
  Khi bóng giấy đặc đi cùng nhiều đường kẻ đứng, từ chối mở khung để
  tránh kéo vào giấy trống. Đã xem 463 ca ứng viên trong lượt cuối: 457 ca
  có phần chữ/dấu được khôi phục, 5 ca còn mơ hồ về hoa trang trí/chữ ô
  bên cạnh/chữ nền/cách nhóm tiêu đề, 1 ca mở vào giấy trống đã bị chặn.
  Bản cuối giữ 462 ca sửa đầu/cuối khung, tất cả vẫn cần duyệt hình học
  toàn bộ khung; kiểm tra trực quan không thay thế nhãn chuẩn.
- Dải chữ sáng trên bảng tối được thử bằng ảnh đảo độ sáng cục bộ, nhưng
  chỉ nhận khung khi phủ đủ thân chữ độc lập. Khôi phục 3/26 ảnh Parquet
  từng trả rỗng; không tạo khung giả trên 139 ảnh âm đã duyệt.
- Chặn lỗi resize về chiều cao 0 với dải ảnh cực dài. Hai kiểm thử đi qua
  helper và điểm vào thật dùng ảnh 16 × 50.000 pixel; khung vẫn quy về
  tọa độ ảnh gốc.
- Nối phần khôi phục dòng ngắn vào luồng đối chiếu bài làm của ứng dụng.
  Vẫn yêu cầu số dòng vật lý phù hợp bản đọc; không gắn tọa độ đoán vào
  bản chép chữ chỉ để đủ số dòng.
- Cho lượt audit lớn bỏ ảnh preview trùng lặp nhưng vẫn lưu toàn bộ khung
  tọa độ nguồn, hash ảnh, hash mã/model và trạng thái cần duyệt.

## Kết quả lượt chạy cuối

| Bộ ảnh khác nội dung | Đã kiểm tra | Có vùng chữ | Trả rỗng | Lỗi thực thi |
| --- | ---: | ---: | ---: | ---: |
| Trang vở và ảnh cắt | 4.205 | 4.056 | 149 | 0 |
| Parquet | 60.247 | 60.224 | 23 | 0 |
| Ảnh tham chiếu quan trọng | 5 | 5 | 0 | 0 |
| **Tổng** | **64.457** | **64.285** | **172** | **0** |

Đã chạy lại đủ bằng mã/model đóng băng của `runtime12`, giới hạn audit
200 vùng/ảnh. Không có ảnh vượt giới hạn vùng; tọa độ được kiểm tra theo
kích thước ảnh gốc. Đây là kiểm tra khả năng xử lý và tính hợp lệ tọa độ,
không phải xác nhận 64.285 ảnh được phân vùng hoàn toàn đúng.
API ứng dụng hiện có giới hạn 30 dòng/ảnh; audit 200 vùng không xác nhận
API sẽ trả đủ tất cả vùng của một trang dài hoặc bị chia thành nhiều mảnh.
Lượt này không thay đổi giới hạn API hay giao diện ứng dụng.

31/31 ảnh tham chiếu dương có đúng số dòng. 22 ảnh có nhãn hình học gồm
148 dòng: khớp một-một 146 dòng ở IoU ≥ 0,5, 20/22 ảnh khớp đủ. Điểm
hình học này giữ nguyên so với bản v5; hai biên dòng chưa khớp đủ vẫn
được ghi rõ. Bộ tham chiếu đã dùng trong phát triển, không phải tập
held-out để suy ra độ chính xác trên toàn bộ Drive.
Đối chiếu tổng hợp cuối khớp 6/6 tham chiếu âm và 144/147 nhãn đếm riêng;
139 ảnh nền đã duyệt đều không tạo vùng chữ. Ba nhãn đếm còn lệch là ảnh
luyện số bị sót và hai ảnh đếm theo phạm vi chữ học sinh có 7/18 vùng
dự đoán so với 10/12 dòng chuẩn. Gộp bỏ bản trùng trong bộ tham chiếu
cho 175/178 ảnh đúng số vùng; số này không xác nhận hình học hoặc bản chép chữ.

## Tính toàn vẹn và nhãn

Kết quả từng ảnh, bản trùng, ảnh chưa đủ bằng chứng và ID đã kiểm tra nằm
trong `ai-training/datasets/drive_math/`, tiếp tục được Git ignore. Ledger
giữ lịch sử kiểm tra đầu tiên; chạy tiếp được sau gián đoạn. Không ghi đè
nhãn chuẩn bằng dự đoán. Bản chép chữ có sẵn trong Parquet/ZIP là nhãn được
cung cấp, chưa được mặc định là nhãn chữ hoặc hình học đã kiểm chứng.

87 ảnh từng trả rỗng được xem trực tiếp: 70 ảnh không có dòng chữ rõ,
11 ảnh chỉ có mảnh chữ cắt mất phần nội dung, 6 ảnh có dòng chữ thật bị
bỏ sót. Nhận định trực quan được lưu riêng cùng hash/provenance; nhãn chưa
duyệt không có quyền đi vào tập huấn luyện.

69 ảnh trả rỗng còn lại ngoài nhóm cũ cũng được xem trực tiếp, kiểm tra
SHA-256 và lưu nhãn đếm riêng: toàn bộ là nền vải, bàn tay hoặc mép giấy
không có chữ. Như vậy 149 ảnh trả rỗng của bộ 4.205 ảnh ở bản v5 đã được
phân loại: 139 ảnh âm hợp lệ, 9 mảnh chữ cắt dở và 1 ảnh luyện số thật
bị sót. Nhãn đếm không thay thế nhãn hình học/transcription đã duyệt.

Thư mục nhãn đếm riêng `reviewed_counts_20261005/` có **147 sidecar**:
139 ảnh đếm 0 dòng, 6 ảnh đếm 1 dòng và 2 ảnh đếm lần lượt 10/12 dòng.
Hai ảnh mới ghi rõ chỉ đếm chữ trong bài học sinh, loại chữ in ở nền,
logo, bàn phím và watermark. 76 sidecar cũ giữ nguyên từng byte; cả 147
nhãn không xác nhận hình học/transcription và không được phép huấn luyện.

Xác minh cuối đã kiểm tra đủ **83.649/83.649 danh tính nguồn**, tương ứng
**64.457 ảnh**, không có lỗi hash/phiên bản/tọa độ. Ledger tăng từ 64.457
lên 83.649 dòng nguồn: thêm 19.192 alias đã kiểm tra, giữ nguyên từng dòng
của lịch sử kiểm tra cũ. 178 tệp nhãn tham chiếu giữ nguyên hash trong
lượt đối chiếu. Mỗi nguồn có đường dẫn bằng chứng và chữ ký phiên bản;
không đánh dấu dự đoán thành nhãn hình học chuẩn.

Chữ ký mã/model của toàn bộ bằng chứng cuối:
`bd8c6c77215b71af618eddc19f9eb8247d387e43b9a6abef72151f3455fd7764`.

## Kiểm thử mã

- Phiên bản cuối: `runtime12-guarded-crops-20261005`; cache hình học:
  `text-regions-v7`.
- **1.078 kiểm thử AI offline đạt**, 4 cảnh báo thư viện hiện có. Chặn
  transport HTTP bên ngoài trong lượt này; 9 bộ kiểm thử cần dịch vụ sống
  không được tính là đã đạt.
- **14 kiểm thử công cụ dữ liệu đạt**, gồm tiếp tục lượt chạy, giữ nhãn
  đã duyệt và bỏ preview mà vẫn giữ tọa độ/hash/ledger.
- **12 kiểm thử công cụ tổng hợp coverage đạt**, gồm alias trùng byte/pixel,
  ảnh gốc khác hash, mã/model cũ, tọa độ ngoài biên, giới hạn vùng, giữ lịch
  sử kiểm tra đầu tiên và phạm vi 147 nhãn đếm đã duyệt.
- Trọng số detector giữ nguyên, SHA-256:
  `03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587`.
- Kiểm tra API chạy thật trả HTTP 200 cho health, readiness và detect-lines;
  bản `runtime12` trả đúng 3 dòng của một ảnh tham chiếu, Groq/Gemini OCR
  calls bằng 0 và không dùng cloud line assistance. Đây là một kiểm tra
  đường tích hợp cục bộ, không phải kiểm thử toàn bộ ảnh qua UI điện thoại.

## Bằng chứng có thể kiểm tra lại

- Kết quả từng ảnh và danh tính nguồn: `ai-training/datasets/drive_math/`.
- Kiểm kê nội dung và nguồn trùng:
  `ai-training/datasets/drive_math/inventory/crossdataset_census_20261005.json`.
- Danh sách đánh dấu từng nguồn, kiểm chứng nhãn và tổng hợp xác minh cuối:
  `ai-training/datasets/drive_math/inventory/final_tested_sources_20261005.jsonl`,
  `ai-training/datasets/drive_math/inventory/final_reference_comparison_20261005.json`,
  `ai-training/datasets/drive_math/inventory/final_coverage_summary_20261005.json`.
- Kiểm thử offline và công cụ dữ liệu:
  `infra/local-runtime/logs/line-refine-20261005/ai-offline.xml`,
  `infra/local-runtime/logs/line-refine-20261005/data-workflow.xml`.
- Kiểm tra API: `infra/local-runtime/logs/line-refine-20261005/api-live-final.json`.
- Bằng chứng chặn mở khung vào giấy trống:
  `infra/local-runtime/logs/line-refine-20261005/short-line/final-comparison/production_guard_validation.json`.
- Đối chiếu đủ 463 ca ứng viên với mã cuối, ảnh gốc và baseline; không có
  ca sửa đầu/cuối dòng chưa được xem:
  `infra/local-runtime/logs/line-refine-20261005/corpus-review/endpoint_review_final.json`.
- Điểm tham chiếu và trạng thái các ca khó của bản cuối:
  `infra/local-runtime/logs/line-refine-20261005/corpus-review/quality_comparison_final.json`,
  `infra/local-runtime/logs/line-refine-20261005/corpus-review/hard_case_status_final.json`.
- Các ca khó còn lại và phân loại ảnh trả rỗng:
  `infra/local-runtime/logs/line-refine-20261005/corpus-review/hard_case_catalog.json`,
  `infra/local-runtime/logs/line-refine-20261005/corpus-review/parquet_empty_writing_catalog.json`.

## Giới hạn

Không có nhãn hình học chuẩn cho toàn bộ tập nên số ảnh chạy được và số
khung trong biên không phải độ chính xác nhận diện dòng. Phân số, bố cục
nhiều cột, chữ quá mờ và mảnh chữ đã bị cắt khỏi ảnh nguồn vẫn cần duyệt.
Tập Drive còn có ghi chép văn/tiếng Anh, vật lý và luyện chữ; không mặc
định toàn bộ tập là toán tiểu học. Kiểm tra trực quan mới xác nhận còn ca
sót chữ luyện đơn lẻ, gộp qua gáy vở và lấy nhầm logo/bàn phím ở nền ảnh.
Cách gộp phân số thử nghiệm còn nối nhầm lời văn nên chưa đưa vào bản chính.
23 ảnh Parquet có chữ còn trả rỗng và một ảnh luyện số vẫn bị bỏ sót;
9 ảnh cắt dở còn lại không có đủ phần chữ để xác nhận một dòng hoàn chỉnh.
Mười ca bố cục khó đã ghi trong catalog chưa thay đổi hình học so với v5.
Lượt này không huấn luyện model mới, không gọi dịch vụ OCR cloud và không
xóa/sửa ảnh trên Drive. Không có bằng chứng kiểm thử trên điện thoại thật
do agent thực hiện.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân và kiểm tra hồi quy bằng đường xử lý hiện có.
  - Applied to: khôi phục dấu/dòng, chặn nền giả có bằng chứng, kết nối luồng
    bài làm và audit tiếp tục được, không thêm model/phụ thuộc ứng dụng.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.16/skills/google-drive/SKILL.md`
  - Why selected: chủ dự án yêu cầu dùng toàn bộ tập ảnh trên Drive đã cung cấp.
  - Applied to: kiểm kê phân trang theo thư mục, đối chiếu ID/metadata,
    tải bản gốc và giữ provenance nguồn; không đột biến dữ liệu Drive.
