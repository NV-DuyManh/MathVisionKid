# Kết quả triển khai các việc trong biên bản ngày 20/10/2026

Ngày kiểm tra: 21/10/2026. Nhánh: `codex/meeting-actions-20261021`.

Cập nhật tiếp theo: [sửa nhận nhầm tiêu đề và cải thiện câu Đúng/Sai](MEETING_READING_FOLLOWUP_20261021.md), kèm kết quả kiểm tra riêng của lượt tiếp tục.

Nguồn yêu cầu: `D:/Capstone/Biên bản họp/C1SE.01_Meeting_Minutes_20-10-2026.docx`, mục **4. Action Items**, đối chiếu với phần thảo luận. Tài liệu gốc chỉ được đọc; báo cáo này không thay chữ ký hay xác nhận nghiệm thu của nhóm/giảng viên.

## Bốn hạng mục đã triển khai

| Hạng mục | Thay đổi và kết quả |
|---|---|
| Lời hướng dẫn phù hợp học sinh, có phản hồi trong gợi ý | Điều chỉnh yêu cầu sinh và duyệt bài học: câu ngắn, một ý mỗi câu, vẫn phải nêu dữ kiện, vì sao chọn phép tính/thứ tự và cách bắt đầu. Hiện từng ý; trong gợi ý có câu chọn nhỏ về phép tính/phân số và phản hồi đúng/sai. Không tự điền đáp án hoặc mở khóa bước học. |
| Hiểu đề trước khi giải | Với đề trích xuất được rõ ràng: ba bước chọn dữ kiện, chọn câu hỏi và Đúng/Sai về câu trích thực tế trong đề. Không yêu cầu học sinh viết tóm tắt tự do. Máy chủ giữ đáp án, kiểm tra tài khoản và phiên bản lượt trả lời; chọn sai không tiến bước. |
| Mô hình phân số tương tác | Dùng các phần bằng nhau cho phân số có trong đề đã xác nhận; chọn/bỏ chọn, kiểm tra và làm lại. Có nhãn trợ năng, dấu chọn, tiêu điểm bàn phím và Space. Thao tác này độc lập với việc chấm bài trên máy chủ. |
| OCR chữ viết tay và ký hiệu toán | Sửa lỗi vùng dấu trừ/dấu bằng thấp hơn chữ số bị tách thành dòng OCR riêng. Chỉ ghép dấu nhỏ, gần và cùng vùng chiều cao; giữ các chặn với cột xa, thanh dài, tầng phân số và phép tính dọc. Không thay nội dung ký tự hoặc làm tăng độ tin cậy giả. |

## Phạm vi và giới hạn

- Bước hiểu đề trích một mệnh đề có số và một câu hỏi bắt đầu rõ bằng Hỏi/Tính/Tìm/Đếm, mỗi đoạn tối đa 100 ký tự. Đây là kiểm tra một dữ kiện, không phải xác nhận học sinh đã hiểu tất cả dữ kiện. Đề dạng khác vẫn đi qua luồng sinh và duyệt toán hiện có với `understandingSteps=0`; không tự bịa câu đọc hiểu hoặc chặn các bài toán vốn được hỗ trợ.
- Bài tính vẫn được lập theo đề đã xác nhận và qua bộ duyệt hiện có. Không thêm lời giải cố định cho riêng một bài mẫu. Số bước tối đa là ba bước hiểu đề cộng hai đến sáu bước toán. Các câu hiểu đề không bị chép thành phép tính trong bài giải trên lớp.
- Mô hình hỗ trợ tối đa hai phân số viết rõ `tử/mẫu` trong đề; mẫu 1–20, tử không âm và tối đa ba hình nguyên. Bỏ qua ngày tháng và ký hiệu có dấu chưa hỗ trợ, gồm dấu cách sau dấu âm. Trường hợp ngoài phạm vi hiển thị thông báo phù hợp thay vì vẽ sai.
- Đã sửa và kiểm tra lỗi nhầm dấu âm đơn ngôi với phép trừ. Đổi đề/tài khoản sẽ hủy yêu cầu cũ và đặt lại bài học; bản nháp ảnh của tài khoản trước bị xóa, phản hồi OCR đến muộn không áp dụng cho học sinh sau.
- OCR được chứng minh bằng kiểm tra hình học và ảnh tổng hợp có kiểm soát. Chưa đo mức tăng độ chính xác trên tập ảnh thật có nhãn; không tuyên bố mọi ảnh đã nhận diện đúng. Xem [báo cáo OCR](MEETING_OCR_20261021.md).
- Chưa đánh giá chất lượng giải thích của mô hình đang chạy thật với học sinh hoặc thiết bị vật lý. Bundle native thành công không tương đương kiểm thử điện thoại/iPad thật.
- Giọng nói là đề xuất nghiên cứu khả thi trong biên bản, chưa phải đầu việc cam kết kỳ này. Biên bản không yêu cầu sửa trò chơi.

## Kiểm tra bản cuối

| Kiểm tra | Kết quả |
|---|---|
| Toàn bộ Student: `npm test -- --runInBand --silent` | **640 passed**, 52 test suites |
| TypeScript: `npx tsc --noEmit` | Qua |
| ESLint bốn tệp triển khai tutoring bên Student | Qua, không lỗi/cảnh báo |
| Python: các suite đọc hiểu, bài học, phân số, tutor, vùng ký hiệu và pipeline OCR | **345 passed**; hai cảnh báo thư viện Starlette đã có |
| Gradle: `MathTutorServiceTest`, `MathTutorControllerTest`, có `--rerun-tasks` | **86 passed** (59 service + 27 controller), không lỗi |
| `expo export --platform all` | Web, Android, iOS thành công; 32 route web |
| Playwright trên bản web vừa xuất | Qua 320×740, 390×844, 820×1180, 1440×1000; không tràn ngang, không lỗi trang |
| `git diff --check` | Qua |

Các lệnh tái lập chính:

```powershell
# E:/MathVisionKid/apps/student-mobile
npm test -- --runInBand --silent
npx tsc --noEmit
npx eslint src/app/learning/math-guide.tsx src/features/tutoring/FractionExplorer.tsx src/features/tutoring/HintCheckIn.tsx src/features/tutoring/api/TutorService.ts
$env:EXPO_PUBLIC_API_BASE_URL='https://ui-preview.mathvision.example/api/v1'
npx expo export --platform all --output-dir ../../scratch/meeting-actions-web

# E:/MathVisionKid/ai/runtime
.\.venv\Scripts\python.exe -m pytest tests/test_source_understanding.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py tests/test_math_tutor.py tests/test_math_symbol_regions.py tests/test_text_detector.py tests/test_generalized_segmentation.py tests/test_column_regions.py tests/test_sparse_ruled_recovery.py tests/test_ocr_bridge.py tests/test_line_cap.py -q

# E:/MathVisionKid/backend/business-api
.\gradlew.bat test --tests com.mathvisionkids.api.tutoring.MathTutorServiceTest --tests com.mathvisionkids.api.tutoring.MathTutorControllerTest --rerun-tasks
```

Kiểm tra trình duyệt dùng HTTP fixture cục bộ, lấy chuyển trạng thái từ phiên Python thật với bộ sinh kế hoạch thay bằng fixture kiểm thử. Có kiểm tra sai đáp án không tiến bước, phân số bằng Space/reset không gọi chấm bài, Đúng/Sai, gợi ý không điền đáp án, tiêu điểm trở về ô trả lời và bài giải cuối. Đây không phải bằng chứng AI online, đăng nhập production hoặc thiết bị thật.

Runner, fixture, ảnh và JSON kết quả cục bộ: `E:/MathVisionKid/scratch/meeting-actions-qa/`. Bundle kiểm tra: `E:/MathVisionKid/scratch/meeting-actions-web/`. Thư mục scratch được Git bỏ qua. Ảnh đã được xem trực tiếp để kiểm tra bố cục.

## Tệp triển khai chính

- `apps/student-mobile/src/app/learning/math-guide.tsx`
- `apps/student-mobile/src/features/tutoring/HintCheckIn.tsx`
- `apps/student-mobile/src/features/tutoring/FractionExplorer.tsx`
- `apps/student-mobile/src/features/tutoring/api/TutorService.ts`
- `ai/runtime/app/tutoring/lesson.py`
- `ai/runtime/app/recognition/text_detector.py`
- `backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutorDtos.java`
- `backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutorService.java`

Có kiểm tra hồi quy tương ứng ở ba tầng. Giữ quyền xác thực/RBAC tại backend. Không huấn luyện, đổi model, tải/sao chép tập ảnh Drive, sửa tài khoản cloud, commit, push hoặc deploy trong đợt này. Các báo cáo không liên quan đã có trong workspace được giữ nguyên.

## Skills Applied

- `docx`
  - SKILL.md: `.agents/skills/docx/SKILL.md`
  - Why selected: đọc yêu cầu từ biên bản Word.
  - Applied to: trích nội dung, tách action items với đề xuất giọng nói; giữ nguyên bản gốc.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai React Native/React web.
  - Applied to: tương tác gợi ý, phân số, reset state theo nguồn/tài khoản, hủy yêu cầu và hợp đồng API.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: thêm lựa chọn và phần tử tương tác.
  - Applied to: nhãn, checkbox, trạng thái chọn, phản hồi, tiêu điểm, bàn phím và kích thước vùng bấm.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: thiết kế tương tác mô hình phân số cho học sinh.
  - Applied to: các phần bằng nhau, chọn/kiểm tra/làm lại và chữ hướng dẫn.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: thay đổi backend/OCR tối thiểu trên luồng sẵn có.
  - Applied to: trích nguồn đọc hiểu, tái sử dụng chấm bài theo phiên và sửa nhóm vùng OCR; không thêm phụ thuộc hay thay model.
