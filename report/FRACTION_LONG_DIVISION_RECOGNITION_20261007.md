# Nhận diện phân số và phép chia đặt tính — 2026-10-07

Đã bổ sung đọc theo cấu trúc cho luồng **ảnh → nội dung bài toán/bài làm**:
phân số giữ tử và mẫu trong cùng biểu thức; phép chia đặt tính giữ số bị chia,
số chia, thương và các hàng tính trong một khối. Không tính lại để thay nội dung
học sinh đã viết. Các kết quả không thống nhất được giữ ở trạng thái cần xác nhận.

Đây là cải thiện luồng đọc notebook đang dùng cloud vision và bằng chứng mực
local. **Không huấn luyện, không đổi trọng số CRNN/YOLO/PP-OCR** trong lượt này.
Không thể suy ra độ chính xác của model OCR riêng từ các kết quả cloud dưới đây.

## Những lỗi đã sửa

1. Phân số xếp chồng bị coi là các dòng độc lập: thêm cấu trúc `FRACTION`, giữ
   đầy đủ tử, mẫu, phép toán, dấu ngoặc và các bước bằng nhau đã viết. Chấp nhận
   cả `3/2` và `(3)/(2)`; không từ chối một bản đọc đúng chỉ vì thiếu ngoặc ngoài.
2. Phân số đơn lẻ không có lời văn bị báo không đọc được hoặc nhiều bài: một
   khung mực nhỏ có đúng một gạch phân số được đọc lại có giới hạn. Tử và mẫu
   không phải hai bài riêng. Nếu lượt kiểm tra thứ hai không thống nhất, giữ
   bản đọc đầu và đánh dấu cần xác nhận.
3. Phép chia đặt tính bị đảo vị trí hoặc chia vụn thành các bước vô nghĩa:
   `LONG_DIVISION` có các trường chuỗi `dividend`, `divisor`, `quotient`, `rows`.
   Nhận một dấu chia đặt tính được mực hỗ trợ thì tách ảnh theo vị trí thành
   vùng trái trên, phải trên, phải dưới và các hàng bên trái để đọc lại.
4. Số `0` đầu hàng và thương viết sai bị mất hoặc tự sửa: giữ nguyên chuỗi,
   ví dụ `067`, `032`, `0025`, `01`, và thương học sinh thực sự viết `88403`.
   Không chèn dấu bằng để khẳng định phép chia đúng; không tự thêm bước hạ số,
   tích, phép trừ hay số dư chưa viết.
5. Kết quả bị gạch sửa làm mất cả biểu thức: có mực hỗ trợ nhiều phân số thì
   đọc lại phần nhìn rõ, giữ trạng thái không chắc chắn. Một bản đọc toán hợp lệ
   không bị xóa chỉ vì lượt kiểm tra thứ hai không hoàn thành.
6. Bài làm phân số bị đưa vào đề bài: biểu thức có kết quả đã viết không trở
   thành đề bài tự suy đoán. Đề được nhận riêng với từ yêu cầu như “Tính” vẫn giữ.
7. Khung dòng bị gán theo số lượng: các khối toán nhiều tầng không nhận geometry
   từ việc số dòng tình cờ bằng nhau. `box=null` cho các khối này; không bịa khung.

Giữ giới hạn độ dài, số trường, số hàng con và tổng nội dung. Nhiều phép chia
độc lập trên cùng trang vẫn trả `MULTIPLE` để chọn từng bài. Vùng ảnh không có
mực hỗ trợ hoặc có nhiều dấu chia không được tự tách thành một phép chia.
Các heuristic mực chỉ hỗ trợ bút màu; mực trung tính giữ luồng đọc ảnh thường.

## Đối chiếu ảnh thật

Bộ development gồm **18 ca từ 5 ảnh nguồn**, không phải 18 ảnh độc lập:
9 vùng phép chia, 7 vùng phân số và 2 trang đầy đủ có nhiều phép chia. Ảnh từ
NEW2 723/731 và các trang phân số trong batch kiểm tra cũ được cắt riêng để
đối chiếu. Các vùng này đã dùng khi điều chỉnh code, **không phải tập held-out**.

| Đối chiếu | Kết quả |
| --- | --- |
| Phép chia được giữ thành một khối | 9/9 vùng; ghi chú giáo viên riêng vẫn giữ |
| Cặp số bị chia/số chia đúng theo ảnh đã xem | 9/9 vùng |
| Phân số trả nội dung để xem lại | 7/7 vùng trong lượt kiểm tra cuối |
| Hai trang có nhiều phép chia | `MULTIPLE`, không chọn tùy ý một bài |
| SHA-256 ảnh nguồn và crop | Giữ nguyên; không sửa nguồn hoặc nhãn tham chiếu |

Ví dụ đối chiếu rõ:

- `70725 : 8`: bản cũ trả 6 dòng rời; bản mới giữ một khối với thương đã viết
  `88403` và các hàng `067`, `032`, `0025`, `01`. Thương là bản chép từ ảnh,
  **không phải đáp án do ứng dụng xác nhận**.
- `17843 : 3`: cách đọc toàn ảnh từng đảo thành `59947 : 17843`, thương `3`.
  Vùng vị trí giữ đúng `17843 : 3`, thương học sinh viết `59947` và các hàng
  `028`, `014`, `023`, `02`; khác biệt giữa hai lượt vẫn được đánh dấu.
- Crop `13/2`: trước đây `UNREADABLE`, nay `PROBLEM` với `13/2` nguyên dạng.
- Biểu thức cộng phân số giữ `(7)/(24) + (11)/(6)` và các phân số trung gian;
  biểu thức trừ giữ `(19)/(28) - (3)/(7)`, tử ghép `(19-12)` và mẫu `28`.

Hai fixture tạo bằng OpenCV kiểm tra thêm **đúng yêu cầu `3/2`** và phép chia
`87 : 4`, thương viết `21`, các hàng `07`, `3`. Lượt cloud cuối trả đúng các
giá trị này. Đây là ảnh tổng hợp, không phải bằng chứng viết tay hoặc điện thoại.

## Những trường hợp chưa hoàn hảo

- Phân số hỗn hợp trong ảnh thật còn thiếu mẫu `1` của một bước `3/1`; khối này
  được đánh dấu không chắc chắn. Giữ được biểu thức không có nghĩa mọi ký tự đúng.
- Dòng bị giáo viên khoanh/gạch/viết đè còn mất hoặc nhầm chữ số; vùng `68721 : 9`
  có phần cuối viết đè mà model chưa giữ đầy đủ các ký tự đọc rõ cạnh đó.
- Phân số tích có kết quả bị gạch sửa được giữ để xem lại, nhưng vẫn có thể chọn
  nhầm bản sửa hoặc bỏ dấu gạch. Không dùng làm nhãn training đã xác minh.
- Hai lượt đọc có thể dùng cùng provider và cùng mắc một lỗi. “Đồng ý” chỉ là
  tín hiệu nội bộ, không phải bằng chứng độ chính xác ký tự hoặc lời giải đúng.
- Chưa có bộ kiểm chứng từng bước chia → nhân → trừ → hạ số, hay nhãn geometry
  đầy đủ cho từng tầng phép chia. Lượt này nhận cấu trúc và chép nội dung.
- Khung mực dựa trên màu chưa bao phủ tất cả bút đen, ảnh cong/xiên mạnh và nền
  bất thường. Không tuyên bố tất cả ảnh trên Drive đều nhận đúng.

Các lỗi dịch vụ 5xx/timeout xảy ra trong audit được dừng rồi tiếp tục các ca
chưa làm; không quay vòng thêm khóa để vượt quota. Đọc lại có giới hạn thời gian
và trả bản đọc đầu ở trạng thái không chắc chắn khi kiểm chứng không khả dụng.

## Kiểm thử

| Kiểm tra | Kết quả |
| --- | --- |
| OCR geometry, rows, notebook, capacity, math tutor và kiểm thử mới | **294 passed** |
| Backend `MathTutorServiceTest` | **44 tests**, 0 failure/error/skipped |
| API `/inspect` | Giữ wire shape cũ; trường cấu trúc nội bộ không lộ ra response |
| Chuỗi nhiều dòng/số 0 đầu hàng | Giữ qua serialization API |
| Dữ liệu không hợp lệ/quá giới hạn, ảnh trống/nhiều dấu chia | Kiểm thử qua |
| `git diff --check` | Qua; chỉ cảnh báo LF/CRLF từ cấu hình Git |

Hai cảnh báo deprecation Starlette/httpx và AnyIO tồn tại trong môi trường kiểm
thử; không đổi dependency để xử lý ngoài phạm vi. Không kiểm thử điện thoại thật,
không cam kết độ trễ thiết bị hay CER/WER trên tập đánh giá độc lập.

```powershell
cd E:\MathVisionKid\ai\runtime
& .venv\Scripts\python.exe -m pytest tests/test_notebook_math_layout.py tests/test_notebook_tutor.py tests/test_notebook_capacity.py tests/test_text_detector.py tests/test_handwriting_rows.py tests/test_short_row_recovery.py tests/test_tiny_row_ends.py tests/test_coloured_strips.py tests/test_generalized_segmentation.py tests/test_math_tutor.py -q
```

## Bằng chứng và phạm vi file

- `ai/runtime/app/tutoring/notebook.py`: cấu trúc, validation, prompt, đọc lại
  có giới hạn, phân loại và trạng thái cần xác nhận.
- `ai/runtime/app/tutoring/math_layout.py`: bằng chứng mực phân số và vùng ảnh
  cho một phép chia, dùng OpenCV/Pillow đã có.
- `ai/runtime/tests/test_notebook_math_layout.py`: hồi quy thực sự cho các lỗi trên.
- `scripts/data/drive_line_batch.py`: thêm helper mới vào chữ ký cache để không
  dùng bản đọc của phiên bản cũ.

Bằng chứng riêng tư nằm trong `infra/local-runtime/logs/math-layout-20261006/`:
`selection.json`, ảnh crop, `before/`, các lượt development, `verified_20261007/`,
assessment và `synthetic_verified/`. Mỗi ca ghi hash nguồn/crop/code và cấu trúc
nội bộ. `audit.py`, `assess.py`, `fixtures.py` chạy lại bằng nguồn local.
Các ảnh và dự đoán nằm ngoài Git, không tự nâng thành nhãn đã xác minh.

Lượt cuối `verified_20261007-assessment.json` đủ 18 ca, không còn ca chưa chạy.
16 vùng bài đơn trả nội dung; hai trang đầy đủ được phân loại nhiều bài. Tất cả
ca kiểm tra cuối khớp hash code hiện tại và giữ byte nguồn/crop:

- `notebook.py`: `379efbd7f36cde00c987125e1e7d16fc50949b8e710d6a5c1dc7f07cd5fd46f5`
- `math_layout.py`: `41f93e9d491423e592417e8afac720410d25eadc18868f2fedf727ce84c90377`

Các thay đổi detector/runtime15 đã có từ phase trước được giữ và kiểm tra hồi
quy, không tính lại thành cải thiện phân số ở phase này. Không sửa Student Mobile
hoặc backend auth/RBAC; không thêm dependency, không commit/push, không training.
Code cần được nạp lại bằng lần khởi chạy dịch vụ bình thường trước khi test app.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa luồng Python hiện có với helper giới hạn, tái dùng OpenCV,
    Pillow, Pydantic và provider sẵn có, không tạo thêm dịch vụ/model phụ.
  - Applied to: đọc notebook, validation khối toán, crop vị trí phép chia, chữ ký
    cache và các kiểm thử hồi quy.

Đã đọc tài liệu Expo v57 theo AGENTS.md trước khi sửa code; không sửa Expo.
Skills applied: ponytail.
