# Sửa nhận diện NEW2 — 2026-10-06

Đã sửa code phân vùng chữ rời và luồng đọc bài của ứng dụng, rồi chạy lại
84 ảnh mới. Không có lỗi thực thi hoặc khung vượt biên. Bốn trường hợp phân loại
sai đã được kiểm tra lại bằng luồng đọc thật: 723, 724, 726 và 729 đều trả về
`MULTIPLE`, yêu cầu chọn một bài để học.

**Chưa đạt “mọi dòng và mọi ký tự đều đúng”.** Phân vùng có tiến bộ rõ ở một số
ảnh luyện chữ, nhưng vẫn có chữ bị bỏ sót, khung phân mảnh và logo in cuối trang.
Không dùng việc chạy thành công hoặc giảm số khung để gọi đó là độ chính xác.

## Thay đổi trong ứng dụng

- Bộ dò dòng `runtime14-spaced-glyph-rows-20261006` bổ sung các dòng chứa nhiều
  chữ rời, cách đều, dựa trên thành phần mực và dòng viết thật. Giữ dấu nhỏ gần
  dòng, mở rộng đến chữ mờ có bằng chứng pixel, giữ vùng chữ khác do model tìm được.
- Nhánh này chỉ chạy trên trang dọc có bằng chứng luyện chữ. Giới hạn xử lý ở
  cạnh dài 1.280 pixel, trả tọa độ theo ảnh nguồn. Không đoán nội dung hoặc tạo
  khung phủ cả trang khi thiếu bằng chứng.
- Chặn phân số, các dải chồng nhau và dải có bằng chứng chứa nhiều dòng.
  Không đưa thử nghiệm gom thành phần theo tâm chữ vào production: thử nghiệm đó
  không cải thiện ổn định trên các ảnh khó.
- Prompt phân biệt các phép tính đặt dọc độc lập với các bước giải của một bài.
  Kết quả kiểm tra độc lập `MULTIPLE` được ưu tiên thay cho bản đọc `WORK` ban đầu.
- Sửa lỗi `MULTIPLE + needsCrop=true` bị đổi thành `UNREADABLE`. Backend giữ
  loại “nhiều bài” và chuẩn hóa nội dung rỗng theo hợp đồng API hiện có.
- Đổi phiên bản cache phân vùng. Chữ ký audit cloud bao gồm cả code bộ dò vùng,
  để không tái dùng kết quả cũ sau khi sửa thành phần có ảnh hưởng đến việc đọc.

Không thay trọng số, không huấn luyện, không thêm thư viện, không sửa giao diện
hoặc hợp đồng API của Student Mobile. Không commit/push trong lượt này.

## Kiểm tra có bằng chứng

| Kiểm tra | Kết quả |
| --- | ---: |
| Phân vùng lại byte gốc 648–731 | 84/84, 0 lỗi |
| Khung vượt biên / vượt 200 vùng | 0 / 0 |
| Nguồn có SHA-256 giữ nguyên so với baseline | 84/84 |
| Ảnh có geometry ứng viên thay đổi | 33 |
| Tổng vùng ứng viên trước → sau | 3.447 → 3.118 |
| Geometry của 14 ảnh toán thay đổi | 0 |
| Đọc lại 14 ảnh toán qua `inspect_notebook` cuối cùng | 14/14, 0 pending |
| Kết quả phân loại cuối cùng | 4 WORK, 10 MULTIPLE, 0 UNREADABLE |
| Tổng dòng trong 4 bản đọc WORK | 55 |
| Dòng WORK đang yêu cầu xác nhận/không chắc chắn | 34/55 |
| Kiểm thử detector/notebook/capacity | 63 passed |
| Kiểm thử ledger/archive/cloud audit | 14 passed |
| Hồi quy số lượng trên 178 tham chiếu có nhãn | 175/178, giữ nguyên baseline |
| Hồi quy geometry, ghép một-một IoU ≥ 0,5 | 146/148 dòng, giữ nguyên baseline |
| Ảnh geometry khớp đầy đủ | 20/22, giữ nguyên baseline |
| Ca hồi quy số lượng bị giảm | 0 |

Các tham chiếu cũ được đọc lại từ nhãn và byte ảnh thật, không sửa nhãn để khớp
dự đoán. Chúng là tham chiếu development, không phải bộ đánh giá độc lập.
Kết quả cloud cuối cùng có chữ ký code hiện tại và SHA-256 khớp nguồn.

Ảnh **702** trước chỉ có 2 vùng; sau có 12 vùng: 11 dòng luyện chữ và một vùng
logo in riêng. Ảnh **707** sau có 12 vùng: tiêu đề ngày, 10 dòng luyện chữ và logo
in riêng. Rà soát trên ảnh nguồn xác nhận số dòng viết tay; đây chưa phải nhãn
geometry hoặc bản chép ký tự được xác minh đầy đủ. Hai sidecar mới được ghi
`count_verified`, `geometry_verified=false`, `training_eligible=false`, với phạm vi
loại logo và chữ trang bên cạnh.

p95 phân vùng của lượt 84 ảnh là 705,02 ms trên máy này, trong lúc có kiểm tra khác
chạy đồng thời; không dùng số này để kết luận tốc độ trên điện thoại. Lượt cloud
trung gian có timeout/5xx và được lưu riêng; lượt cuối hoàn tất đủ 14 ảnh.
Không có bằng chứng thử trên thiết bị vật lý trong lượt này.

## Phần chưa hoàn tất

- Một số trang lưới luyện chữ 660–674 vẫn còn vùng từng ký tự thay vì dòng hoàn chỉnh.
- Các dòng chữ cao/đuôi chữ chạm gần nhau như 677, 687–691 vẫn cần rà geometry.
  Nhánh khôi phục giữ kết quả cũ khi bằng chứng gộp dòng không đủ chắc chắn.
- Chữ mờ ở mép dòng trên một số trang như 675, 696, 697, 701 vẫn có thể thiếu.
- Logo, chữ trang bên cạnh và nội dung in nền chưa được loại ngữ nghĩa trên toàn bộ
  bộ dữ liệu. Số vùng thô không đồng nhất với số dòng viết tay trong nhãn.
- Chữ/số bị gạch hoặc sửa trong bài toán vẫn cần xác nhận của học sinh. Phân loại
  được ảnh không chứng minh mọi con số chép lại đều chính xác.
- Model CRNN của chủ dự án chưa được thay đổi. Geometry của 648 và 652 giữ nguyên;
  điểm spot-check cũ 16 dòng vẫn là CER 31/271 ≈ 11,44%, 5/16 dòng khớp hoàn toàn.
  Không đo lại CER cho mọi dòng mới và không công bố “100% OCR”.

Các nguồn, kết quả trước/sau, nhãn tham chiếu và ca còn lỗi được giữ trong batch
riêng, nằm ngoài Git. Không tự nâng nhãn dự đoán lên thành nhãn training.

## Tái kiểm tra và bằng chứng riêng tư

Thư mục: `ai-training/datasets/drive_math/new2_20261006_84/refine/`.

- `baseline.zip`: kết quả/code trước sửa, giữ nguyên để đối chiếu.
- `final/local_summary.json`, `final/local_regions/`: phân vùng bằng code cuối.
- `comparison.json`: so sánh 84 geometry, kiểm tra nguồn giữ nguyên.
- `regression.json`: kiểm tra lại 178 tham chiếu và 22 ảnh geometry.
- `cloud_release/cloud_summary.json`, `cloud_release/cloud_results/`: 14 bản đọc cuối.
- `validation.json`: đối chiếu chữ ký code và nguồn của kết quả cuối.
- `reviewed_counts/`: hai nhãn đếm dòng theo phạm vi viết tay, chưa dùng để training.

Lệnh kiểm thử code:

```powershell
cd E:\MathVisionKid\ai\runtime
& .venv\Scripts\python.exe -m pytest tests/test_text_detector.py tests/test_notebook_tutor.py tests/test_notebook_capacity.py -q
cd E:\MathVisionKid
& ai\runtime\.venv\Scripts\python.exe -m pytest scripts/data/test_drive_line_batch.py scripts/data/test_archive_audit.py -q
```

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa pipeline Python hiện có, ưu tiên tái dùng xử lý mực/dòng và tránh thêm dependency.
  - Applied to: `text_detector.py`, `notebook.py`, chữ ký audit và các kiểm thử hồi quy.

Đã đọc tài liệu Expo v57 trước khi sửa code theo AGENTS.md; lượt này không sửa Expo.
Skills applied: ponytail.
