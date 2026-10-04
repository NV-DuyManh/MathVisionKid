# Cải thiện phân vùng dòng và kiểm tra Git — 2026-10-04

## Quyết định Git

**Chủ dự án đã chấp nhận các lỗi còn lại và yêu cầu commit/push.** Quyết định
ban đầu giữ lại mã được thay thế bởi xác nhận này. Đã sửa lỗi tách mũi tên
thành dòng và chọn hướng dẫn thiếu yêu cầu; hai ảnh nền bị nhận nhầm cùng
một dòng ngắn cắt dấu hai chấm vẫn được ghi rõ bên dưới. Không tuyên bố
nhận diện đúng tất cả ảnh.

Phạm vi đồng bộ và kiểm tra trước khi đẩy nằm trong
`report/GIT_PUBLISH_20261004.md`. Giữ nguyên dữ liệu Drive, nhãn chuẩn và
trọng số model; không huấn luyện trong lượt xuất bản.

## Thay đổi mã

- Gắn một nét mũi tên/gạch dưới mảnh vào dòng chữ gần nó khi chỉ có một dòng
  phù hợp. Giữ nguyên nét ảnh trong vùng hợp nhất, không xóa nét để cải thiện
  số lượng vùng.
- Dùng thành phần thân chữ làm bằng chứng để bảo vệ chữ viết liền nét, dòng
  ngắn, chữ nhỏ và phân số. Nét xa hoặc nằm giữa hai dòng vẫn được giữ riêng.
- Dùng vị trí dòng ban đầu để xét khoảng cách; vùng đã mở rộng không được
  kéo tiếp một nét xa vào theo chuỗi.
- Tăng phiên bản detector và cache để kết quả cũ không che bản sửa.
- Hướng dẫn cục bộ phải khớp toàn bộ mục tiêu: hỏi tích hai số, hỏi cả diện
  tích và chu vi, hỏi số mới hoặc nhiều đại lượng sẽ chuyển sang bộ hướng dẫn
  chung. Khi chưa tạo được kế hoạch hợp lệ, không thay bằng bài học trả lời
  thiếu yêu cầu.
- Thêm 12 ca bảo vệ phân vùng và 16 ca kiểm tra mục tiêu hướng dẫn. Hai đề
  mẫu vẫn đạt: thêm chữ số 6/hơn 537 tìm được 59; hình thang AB = 8 cm,
  CD = 15 cm, diện tích tam giác ACD = 90 cm² có diện tích 138 cm².

Bản thử rộng ban đầu gộp nhầm các dòng “phương là:”, “Toán”, “2) Tính”. Đã
loại cách ghép đó trước lần kiểm tra cuối; không đưa bản thử này lên Git.

## Kiểm thử cuối

| Kiểm tra | Kết quả |
| --- | --- |
| AI offline sau lần sửa cuối | **995 tests đạt**, 87 files, 4 cảnh báo deprecation |
| Kiểm thử chuyên dụng mục tiêu bài học | **53 tests đạt** |
| Chạy mới bộ ảnh Drive đã tải về | **3.279/3.279 ảnh**, 0 lỗi thực thi, 0 khung vượt biên hoặc vượt giới hạn vùng |
| Ảnh có vùng ứng viên | **3.192**; 87 ảnh trả rỗng, chưa mặc định chúng đều là ảnh không có chữ |
| 31 ảnh có chữ có số dòng tham chiếu | **31/31** khớp số lượng |
| 6 ảnh tham chiếu không có chữ | **4/6** trả rỗng đúng |
| 22 ảnh tham chiếu hình học, IoU ≥ 0,5 | **146/148 vùng**, 20/22 ảnh khớp toàn bộ |
| API thật, ảnh số 243 | HTTP 200, **3 vùng thay vì 5**; 0 lượt gọi cloud để hỗ trợ/chỉnh dòng |
| AI health / ready sau nạp mã cuối | HTTP 200 / 200 |
| Git diff whitespace | Đạt |

Chín suite phụ thuộc dịch vụ ngoài vẫn được loại khỏi lượt offline, không
tính là đạt: `test_groq_live_migration.py`, `test_groq_production_route.py`,
`test_gemini_live.py`, `test_submit_400_fix.py`, `test_minio_pipeline.py`,
`test_prod2b_trigger.py`, `test_prod2e_gemini_migration.py`,
`test_prod2f_release_gate.py`, `test_gemini_model_migration.py`.

Kiểm tra trước đó trên phần mã không đổi vẫn có: mobile 427 tests, lint và
TypeScript đạt; backend 234 tests đạt; workflow dữ liệu 13 tests đạt; build
teacher/admin/portal và shared packages đạt. Lượt này chỉ sửa AI và chạy lại
toàn bộ kiểm thử AI liên quan, không tính lại các kết quả trước thành kiểm
tra mới. Chi tiết trong `report/GIT_VERIFICATION_20261004.md`.

## Tính toàn vẹn và cách đọc kết quả

- Ba nhóm chạy song song, cùng hash mã/model; không dùng lại kết quả cũ.
  Hash 3.279 ảnh nguồn, nhãn gốc và nhãn đã duyệt đều được giữ nguyên.
- **3.242 ảnh vẫn mang trạng thái cần duyệt.** Có khung ứng viên không có
  nghĩa là bản chép chữ đúng; chưa đo độ chính xác chữ trên toàn bộ bộ ảnh.
- Trong 604 ảnh có baseline gần nhất, chỉ ảnh 243 và 521 đổi hình học. Xem
  trực tiếp xác nhận chúng là mũi tên hoặc đường trang trí, không phải dòng
  chữ riêng. Không thấy hồi quy mới trong các tham chiếu đã duyệt.
- Tổng cộng 869 ảnh khác baseline lưu trước (2 readiness, 57 NEW2, 810 ảnh
  cắt còn lại). NEW2 và tập ảnh cắt dùng phiên bản cũ hơn; không quy toàn bộ
  thay đổi này cho bản sửa mũi tên hoặc coi mọi thay đổi là cải thiện.
- P95 phân vùng cục bộ trong đợt audit là 826,77 ms; ca chậm nhất 25.543,64 ms.
  Đây là số đo tại máy trong đợt chạy nhóm, không phải thời gian toàn luồng
  cloud hoặc bằng chứng độ mượt trên điện thoại.
- Kết quả mới nằm riêng trong `ai-training/datasets/drive_math/annotation_recheck_20261004/`.
  Giữ lịch sử chọn/đánh dấu ảnh đã test trong ledger cũ, không ghi đè lần
  kiểm tra đầu hay nâng dự đoán tự động thành nhãn chuẩn.

## Lỗi còn lại đã xem ảnh gốc

1. Ảnh kiểm tra 2038 là nền vải, không có chữ, nhưng trả 7 vùng; ảnh 2039 là
   mép trang/nền vải, trả 1 vùng. Detector học sẵn và bộ lọc hình dạng cũng
   có thể bị đánh lừa. Chưa chứng minh được một bộ lọc loại chúng mà giữ
   an toàn chữ thật bị cắt sát mép.
2. Dòng “là:” ở ảnh 59 đã khôi phục đủ dòng nhưng còn cắt mất dấu hai chấm
   bên phải. Khung tham chiếu của cả ảnh 11 và 59 cũng cắt nét chữ, nên cần
   duyệt lại hình học; không sửa nhãn để làm đẹp điểm số. Ảnh 11 hiện giữ
   đủ nét của dòng. Hai trường hợp này có từ bước khôi phục dòng ngắn,
   không phải hồi quy do bản ghép mũi tên.

Bốn ảnh nền/giấy trắng đã loại khỏi ZIP sạch trên Drive ở lượt trước vẫn
được giữ trong tập kiểm tra âm để không che hạn chế detector. Không xóa thêm
ảnh vì thuật toán trả rỗng; không dùng các ảnh nền này làm nhãn chữ để train.

## Báo cáo các yêu cầu trước

- Cắt/xoay: thanh căn thẳng, một nút xoay, lớp tối ngoài khung; khung tối thiểu
  8 logical pixels, tám tay kéo và đổi cạnh khi kéo vượt cạnh đối diện trong
  cùng thao tác. Xem trước không xuất lại bitmap mỗi lần kéo; xuất ảnh khi
  xác nhận. `report/CONTINUOUS_CROP_RESIZE_20261004.md`.
- Quay lại/thu gọn đề: sửa lấy kích thước ảnh thực, giữ ảnh che riêng tư,
  sửa cảnh báo shared value khi render và nút mở/đóng đề.
  `report/IMAGE_BACK_NAVIGATION_UI_20261004.md`.
- Hướng dẫn: tám dạng cục bộ, bước theo ý nghĩa toán thay vì từng dòng OCR;
  cần đề gốc để kiểm tra bài làm. Chưa phải bộ số hóa đầy đủ sách Kết nối
  tri thức. `report/CROP_TUTOR_REFINEMENT_20261004.md`.
- Drive/NEW2/ảnh khó: đã kiểm tra lại tất cả 3.279 nguồn duy nhất đã tải,
  nhưng chưa hoàn thành nhãn hình học và bản chép chữ chính xác của toàn bộ
  ảnh hoặc toàn bộ 21 ca khó. Các lượt đọc cloud chưa xong trong hồ sơ NEW2
  trước không được chạy lại ở đây. `report/DRIVE_REMAINING_LOCAL_20261004.md`.
- Chưa train model mới. Cải thiện hiện tại là detector pretrained và xử lý
  phân vùng; nhãn chưa duyệt không được dùng như ground truth. Chưa có bằng
  chứng kiểm thử vật lý trên điện thoại do agent thực hiện.
- Kiểm tra phạm vi Git không thấy khóa thật mới, dữ liệu riêng hay trọng số
  model trong các file thay đổi có thể publish. `.env`, dataset/ledger, log
  và weights tiếp tục được ignore. Quét mẫu không là chứng nhận tuyệt đối.

## Bằng chứng tại máy

- `infra/local-runtime/logs/annotation-ai-narrow-20261004.xml`: 995 tests.
- `infra/local-runtime/logs/annotation-live-final-20261004.json`: API mã cuối,
  3 dòng, 573,42 ms, không dùng cloud hỗ trợ/chỉnh dòng.
- `annotation_recheck_20261004/local_summary.json`, `reference_comparison.json`:
  kết quả, hash, đối chiếu số dòng và hình học, tất cả dưới dataset riêng.
- `infra/local-runtime/logs/annotation_visual_review.json` và ảnh zoom:
  bằng chứng trực tiếp về nét trang trí, ảnh nền và hai dòng ngắn.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân và kiểm tra hồi quy với thay đổi nhỏ, không
    thêm model/phụ thuộc hoặc bộ lọc riêng cho từng ảnh.
  - Applied to: liên kết nét mảnh, giữ thân chữ và vị trí gốc, điều kiện mục
    tiêu bài học, kiểm thử có ý nghĩa và quyết định Git theo bằng chứng.
