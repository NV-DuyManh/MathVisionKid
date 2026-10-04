# Kiểm tra trước khi đẩy Git — 2026-10-04

Cập nhật tiếp theo: `report/ANNOTATION_LINE_REFINEMENT_20261004.md` đã sửa ca
243, chạy mới 3.279 ảnh và 995 kiểm thử AI. Chủ dự án sau đó chấp nhận các lỗi
nhận nhầm ảnh nền/cắt dấu hai chấm và yêu cầu đẩy Git; xem
`report/GIT_PUBLISH_20261004.md`. Số liệu và quyết định bên dưới là bằng chứng
của lượt kiểm tra trước xác nhận đó.

## Quyết định

Chưa commit/push. Chủ dự án yêu cầu kiểm tra ổn mới đẩy Git. Kiểm thử mã nguồn
đạt, nhưng lỗi nhận diện đã biết vẫn tái hiện trên ảnh gốc: ảnh kiểm tra số 243
có ba dòng phương trình cùng hai nét mũi tên; bộ phát hiện trả năm vùng.
Không coi kết quả này là nhận diện chính xác chỉ vì các kiểm thử tự động đạt.

Lượt này chạy kiểm tra, xem ảnh gốc và tổng hợp báo cáo; không sửa thuật toán,
huấn luyện model, đổi nhãn, xóa dữ liệu hoặc khởi động lại dịch vụ.

## Kiểm tra mới thực hiện

| Kiểm tra | Kết quả |
| --- | --- |
| Student mobile Jest | 39 suites / **427 tests đạt** |
| Student mobile lint | Đạt, không có lỗi/cảnh báo |
| Student mobile TypeScript | Đạt |
| AI offline | **967 tests đạt**, 87 files; 4 cảnh báo deprecation |
| Dataset/archive workflow | **13 tests đạt** |
| Backend, chạy lại Gradle test | 26 suites / **234 tests đạt**, 0 lỗi, 0 bỏ qua |
| Teacher/admin/portal và shared packages | Build đạt |
| Git diff whitespace | Đạt |
| Quét mẫu credential trên 2.669 file nguồn/tài liệu có thể đưa lên Git | Không có mẫu khớp; không có đường dẫn dữ liệu riêng hoặc file >40 MB |
| Kiểm tra ignore | `.env`, ledger/dataset, log và model weights đều được ignore |
| Dịch vụ đang chạy | Backend health, AI health, mobile bundler status đều HTTP 200 |
| Git sau fetch | `main` và `origin/main` cùng commit `91bcba5`, ahead/behind 0/0 |

Build web có cảnh báo bundle vượt 500 kB. Gradle báo API sẽ bị loại bỏ ở phiên
bản tương lai. Đây là cảnh báo, không phải kiểm thử/build thất bại. Quét mẫu
credential không phải chứng nhận an toàn tuyệt đối.

AI offline chặn transport HTTPX thật. Chín suite phụ thuộc dịch vụ/model catalog
không được chạy: `test_groq_live_migration.py`, `test_groq_production_route.py`,
`test_gemini_live.py`, `test_submit_400_fix.py`, `test_minio_pipeline.py`,
`test_prod2b_trigger.py`, `test_prod2e_gemini_migration.py`,
`test_prod2f_release_gate.py`, `test_gemini_model_migration.py`. Không tính các
suite này là đạt. Health 200 không xác minh dịch vụ vision bên ngoài đã phục hồi.

Các lệnh chính:

```powershell
npm test --workspace=student-mobile -- --runInBand --silent
npm run lint --workspace=student-mobile
# Trong apps/student-mobile:
npx tsc --noEmit
# Trong ai/runtime:
.venv/Scripts/python.exe -m pytest ../../scripts/data/test_drive_line_batch.py ../../scripts/data/test_archive_audit.py -q --tb=short
# Trong backend/business-api:
.\gradlew.bat test --no-daemon --rerun-tasks
# Tại gốc repository:
npm run build:web
git -c core.safecrlf=false diff --check
```

Bằng chứng AI mới: `infra/local-runtime/logs/git-verification-ai-20261004.xml`.
Kết quả backend: `backend/business-api/build/test-results/test/TEST-*.xml`.
Các thư mục này được ignore, không chứa nội dung cần đẩy Git.

## Kiểm tra lại nhận diện

- Đã đối chiếu hash 604 kết quả của lần kiểm tra readiness với mã nguồn/model
  hiện tại và hash ảnh gốc: tất cả khớp. Đây là kiểm tra tính toàn vẹn bằng chứng,
  không phải chạy nhận diện mới trên cả 604 ảnh.
- 33 ảnh có số dòng được kiểm tra độc lập: **32/33** đúng số lượng.
- 22 ảnh có nhãn hình học: đúng số lượng 22/22; khớp một-một tại IoU >= 0.5 là
  **146/148 vùng**, chỉ **20/22 ảnh** khớp toàn bộ vùng ở ngưỡng đó.
- Đọc ảnh gốc số 243 và chạy lại hàm production: vẫn **5 vùng thay vì 3**;
  `needs_review=true`. Bằng chứng mới nằm ở
  `infra/local-runtime/logs/git-verification-line243-20261004.json`.
- Trong tập 604 ảnh có **571 ảnh chưa được xác minh độc lập**. Chưa đo độ chính
  xác toàn bộ bản chép chữ. Không đổi nhãn dự đoán thành nhãn chuẩn.

## Tổng hợp các yêu cầu trước

- **Drive:** lịch sử kiểm tra đã xử lý 3.279 ảnh nguồn duy nhất, bao gồm ảnh đầy
  trang và ảnh cắt; 3.176 có vùng ứng viên, 103 không có. Đây là kết quả của
  phiên bản thuật toán ở thời điểm báo cáo dữ liệu, không phải kết quả chạy mới
  3.279 ảnh hôm nay. Không có exception/vùng vượt biên trong đợt đó.
  Ledger lưu danh tính/hash để tránh chọn lặp. NEW2 gồm 100 ảnh; tất cả có vùng
  ứng viên, vẫn chưa có nhãn hình học/nội dung hoàn chỉnh cho toàn bộ tập.
- **Ảnh không có chữ:** bốn ảnh vải/giấy trắng đã được xác minh và loại cùng bốn
  dòng CSV khỏi ZIP sạch. Bản ZIP sạch đã trở thành phiên bản hiện hành trên
  Drive, giữ ID/tên/link cũ; bản gốc vẫn được lưu. Không xóa ảnh chỉ vì detector
  trả rỗng. Chi tiết: `report/DRIVE_REMAINING_LOCAL_20261004.md`.
- **21 ảnh khó:** đã tìm được vùng ứng viên, nhưng vẫn có trường hợp gộp dòng,
  nhiều cột, chữ mờ và nền bị nhận nhầm. Chưa hoàn thành nhận diện/nhãn chính xác
  toàn bộ nhóm. Không tuyên bố chúng đã phục hồi hoàn toàn.
- **Huấn luyện:** chưa train model mới trên dữ liệu này. Đã tích hợp detector
  pretrained và cải thiện xử lý ảnh/phân vùng. Nhãn tự động chưa xác minh không
  được dùng như ground truth. 87 lượt đọc cloud NEW2 còn chờ trong bằng chứng
  lịch sử; lượt kiểm tra này không chạy lại chúng.
- **Hướng dẫn giải:** bộ hướng dẫn nội bộ có tám dạng thường gặp và kiểm tra
  từng bước. Bằng chứng trước đã hoàn thành bài thêm chữ số 6/hơn 537 với kết
  quả 59 và bài hình thang do chủ dự án cung cấp với chiều cao 12 cm, diện tích
  138 cm². Lỗi 503 của kế hoạch hướng dẫn không hợp lệ đã được phân biệt với
  lỗi kết nối; bỏ thẻ gợi ý chung không liên quan. Đây không phải bộ số hóa đầy
  đủ sách Kết nối tri thức. Các dạng khác/đọc ảnh còn phụ thuộc dịch vụ AI.
  Chi tiết: `report/CROP_TUTOR_REFINEMENT_20261004.md`.
- **Giao diện/crop:** đã sửa kích thước ảnh khi quay lại, nút thu gọn đề, cảnh
  báo đọc shared value khi render; thanh căn thẳng, một nút xoay và lớp tối ngoài
  khung; khung tối thiểu 8 logical pixels với tám tay kéo có thể vượt qua cạnh
  đối diện rồi kéo ngược trong cùng một thao tác. Có bằng chứng browser/compiler,
  chưa có kiểm thử vật lý trên điện thoại từ agent.
  Chi tiết: `report/IMAGE_BACK_NAVIGATION_UI_20261004.md` và
  `report/CONTINUOUS_CROP_RESIZE_20261004.md`.

## Phần còn thiếu trước điều kiện hoàn chỉnh

Lỗi phân vùng mũi tên, xác minh nhãn/nội dung còn lại, đọc cloud đang chờ và
đánh giá trên điện thoại thật vẫn chưa hoàn tất. Kết quả kiểm thử mã nguồn đạt
không thay thế các công việc này. Giữ nguyên các thay đổi tại máy, chưa đưa lên
remote theo điều kiện của chủ dự án.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: kiểm tra hồi quy và quyết định Git dựa trên bằng chứng hiện có.
  - Applied to: dùng bộ kiểm thử sẵn có, đối chiếu hash/reference, không thêm
    thuật toán phỏng đoán hay phụ thuộc mới, quét phạm vi Git và tổng hợp báo cáo.
