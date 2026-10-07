# Ưu tiên sửa nhận diện dòng — 2026-10-06

Đã sửa lỗi khung dừng sớm ở đầu/cuối các dòng luyện chữ cách đều trên trang
chụp cong hoặc nghiêng. Chạy lại 84 ảnh NEW2 bằng byte nguồn đã lưu; 5 ảnh có
geometry thay đổi được rà trực quan. Không có lỗi thực thi hoặc khung vượt biên.

Đây là cải thiện phân vùng dòng, chưa phải kết luận mọi ảnh hoặc mọi ký tự OCR
đều đúng. Trọng số OCR và model dò chữ không thay đổi; không huấn luyện trong lượt này.

## Nguyên nhân và thay đổi

`recover_glyph_rows` dùng các dòng mực làm điểm tựa. Trên trang cong, phép chiếu
ngang có thể chia một dòng thành nhiều dải, chỉ để lại một phần chữ trong điểm
tựa. Nhánh mở rộng trước đây chỉ xét thêm một vị trí chữ ở mỗi đầu, nên vẫn bỏ
chữ khi phần bị cắt dài hơn một vị trí.

Phiên bản `runtime15-consecutive-glyph-ends-20261006` nối tiếp các vị trí có
thành phần mực thật. Mỗi lần nối điều chỉnh đường tâm theo các chữ đã hỗ trợ,
giúp theo được độ cong nhẹ. Dừng ngay tại vị trí rỗng, kích thước không phù hợp
hoặc lệch đường tâm; không nhảy qua khoảng trống để nối sang cột khác.

Giữ hỗ trợ mảnh chữ đầu tiên của phiên bản cũ. Điều kiện chặt hơn dùng cho việc
nối tiếp không làm mất mảnh chữ vốn đã được nhận. Các chặn phân số, dòng chồng
và dải chứa nhiều dòng vẫn được giữ. Xử lý ảnh vẫn giới hạn cạnh dài 1.280 pixel
trong nhánh này, trả tọa độ theo ảnh gốc. Đổi phiên bản cache để tránh dùng khung cũ.

## Đối chiếu trên ảnh thật

| Ảnh NEW2 | Vùng ứng viên trước → sau | Quan sát trực quan |
| --- | ---: | --- |
| 669 | 79 → 77 | Hai chữ mép dòng được nối vào hai dòng gần cuối thay vì để riêng. |
| 675 | 16 → 15 | Dòng luyện chữ bị cắt trước đây chỉ chứa 5/7 chữ trong khung; nay chứa đủ 7/7. |
| 682 | 27 → 27 | Mở rộng một khung dòng đến chữ ở mép còn thiếu. |
| 697 | 38 → 37 | Chữ đầu của dòng cuối được nối vào cùng dòng. |
| 716 | 12 → 11 | Dòng cuối có một khung thay vì hai khung chồng nhau. Logo in gần đó vẫn chưa được loại ngữ nghĩa. |

Số vùng ứng viên không đồng nhất với số dòng viết tay. Các quan sát trên là
kiểm tra development trên ảnh đã dùng để điều chỉnh, không phải điểm chính xác
trên tập đánh giá độc lập. Không nâng dự đoán thành nhãn training đã xác minh.

## Kiểm thử cuối cùng

| Kiểm tra | Kết quả |
| --- | ---: |
| NEW2 648–731, không tính theo cache cũ | 84/84 ảnh được chạy lại |
| Lỗi thực thi / khung vượt biên / vượt giới hạn 200 vùng | 0 / 0 / 0 |
| SHA-256 nguồn giữ nguyên | 84/84 |
| Geometry thay đổi | 5/84 ảnh |
| Tổng vùng ứng viên | 3.118 → 3.113 |
| Geometry giữ nguyên trên ảnh toán trong batch | 14/14 |
| Kiểm thử detector, notebook và capacity | 69 passed |
| Hồi quy số lượng trên tham chiếu có nhãn | 175/178, giữ nguyên baseline |
| Ghép geometry một-một, IoU ≥ 0,5 | 146/148 dòng, giữ nguyên baseline |
| Ảnh tham chiếu geometry khớp đủ | 20/22, giữ nguyên baseline |
| Nhãn tham chiếu hoặc byte nguồn bị sửa | 0 |

Kiểm thử mới bao gồm nối nhiều vị trí ở cả hai đầu, hai mức kích thước ảnh,
dừng tại vị trí rỗng và bảo toàn mảnh chữ nhỏ đầu tiên. Các kiểm thử phân số,
trang trống, nền bão hòa, xoay ảnh, dấu tiếng Việt, footer và giới hạn dòng cũng qua.

Không gọi cloud để đọc lại nội dung trong lượt này; kết quả trên đo phân vùng
local. Không có bằng chứng kiểm thử trên điện thoại. p95 của lượt audit là
1.085,38 ms khi các lượt kiểm tra khác chạy đồng thời trên máy này, không dùng
để so sánh tốc độ điện thoại hay tuyên bố nhanh hơn phiên bản cũ.

## Giới hạn còn lại

- Các trang nhiều chữ cao hoặc đuôi chữ gần nhau như 677, 687–691 còn phân mảnh.
- Một số dòng cong mạnh hoặc chữ quá nhạt vẫn không đủ bằng chứng để nối hết.
- Logo in, chữ trang bên cạnh và dấu gạch sửa vẫn cần rà soát.
- Ba tham chiếu số lượng và hai dòng tham chiếu geometry còn chưa khớp; lượt
  này không sửa nhãn để làm đẹp điểm số.
- Chưa đánh giá lại độ chính xác ký tự của CRNN hay bản đọc cloud trên toàn bộ corpus.

## Tái kiểm tra

```powershell
cd E:\MathVisionKid\ai\runtime
& .venv\Scripts\python.exe -m pytest tests/test_text_detector.py tests/test_notebook_tutor.py tests/test_notebook_capacity.py -q
```

Bằng chứng ảnh riêng tư được giữ tại
`ai-training/datasets/drive_math/new2_20261006_84/refine_next_20261006/`:

- `runtime14_baseline.zip`: code, geometry và tham chiếu trước sửa.
- `final/local_summary.json`, `final/local_regions/`, `final/local_overlays/`:
  kết quả bằng code cuối cùng.
- `comparison.json`: so sánh từng nguồn/khung và xác nhận hash code/model hiện tại.
- `regression.json`: kết quả 178 tham chiếu; nhãn và nguồn giữ nguyên.
- `audit.py`, `regression.py`: lệnh chạy lại bằng nguồn local, không thao tác Drive.

Các thử nghiệm và ảnh nguồn nằm ngoài Git. Không sửa Student Mobile, không thêm
dependency, không commit/push trong lượt này.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa logic Python hiện có với thay đổi nhỏ, tái dùng thành phần mực và các chặn an toàn sẵn có.
  - Applied to: mở rộng đầu/cuối dòng trong `text_detector.py`, phiên bản cache và kiểm thử hồi quy.

Đã đọc tài liệu Expo v57 theo AGENTS.md trước khi sửa code; lượt này không sửa Expo.
Skills applied: ponytail.
