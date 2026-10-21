# Hình phân số tương tác và hướng dẫn tóm tắt đề

Ngày hoàn thành kiểm tra: 21/10/2026. Nhánh `codex/meeting-actions-20261021`. Phạm vi theo yêu cầu bổ sung của chủ dự án: thêm hình học để học sinh hiểu phân số và hướng dẫn tóm tắt đề trong luồng học hiện có.

## Học sinh dùng như thế nào

### 1. Hiểu phân số bằng hình

- Chọn **Hình tròn**, **Hình vuông** hoặc **Thanh phân số**.
- Chạm trực tiếp từng vùng để chọn/bỏ chọn. Hình tròn chia thành các quạt bằng nhau; hình vuông chia các ô hoặc dải bằng nhau; thanh chia các dải bằng nhau.
- Đổi loại hình vẫn giữ số phần đã chọn để thấy cùng một phân số có nhiều cách biểu diễn. Dấu chọn và màu phân biệt vùng đã chọn.
- Có nút phần đánh số, kích thước tối thiểu 48, làm cách tương đương cho vùng hình nhỏ và trình đọc màn hình. Kiểm tra thực tế bằng Space/Enter trên web; có tiêu điểm nhìn thấy được.
- Nút kiểm tra chỉ kiểm tra biểu diễn phân số đã cho. Không điền đáp án hoặc mở khóa bài toán. Nút chọn lại xóa lựa chọn.
- Có thể dùng hình cả lúc hiểu đề và khi đang tính. Bài đã hoàn tất không giữ các bộ chọn hình đang hoạt động.

### 2. Tập tóm tắt đề

Khung **Em tập tóm tắt đề** hướng dẫn ba việc: tìm số/đơn vị/mối liên hệ, tìm điều cần hỏi, rồi đối chiếu lại với đề.

Trước khi trả lời, khung chỉ có hướng dẫn và chỗ **Đã biết / Cần tìm**. Sau một lựa chọn đúng, dữ kiện được ghi rõ là **một dữ kiện em vừa chọn**, không tuyên bố đã hiểu toàn bộ đề. Sau khi học sinh chọn đúng cả dữ kiện và câu hỏi, máy chủ mới gửi bản nhóm các mệnh đề nguồn vào hai phần. Giữ cả quan hệ không có số như “phần còn lại để dành”.

Bản tóm tắt không thêm phép tính/đáp số. Khi chuyển sang tính, khung thu gọn và có thể mở lại. Chỉnh đề, đổi nguồn, đổi phiên hoặc tài khoản đặt lại trạng thái theo các bảo vệ hiện có.

## Giới hạn và tính đúng

- Hình tương tác dùng tối đa hai phân số viết rõ trong đề; mẫu 1–20, tử không âm và tối đa ba hình nguyên. Đã kiểm tra hình học cho mọi mẫu 1–20 ở ba dạng, gồm mẫu 1, tử 0 và phân số lớn hơn 1. Giữ nguyên bộ lọc ngày tháng và dấu âm chưa hỗ trợ.
- Các quạt có cùng góc/bán kính; các ô/dải có cùng diện tích. Với mẫu nguyên tố, hình vuông dùng các dải bằng nhau thay vì vẽ ô không bằng nhau. Nút số cung cấp cách chọn tương đương khi mảnh hình nhỏ.
- Tóm tắt dùng cùng bộ trích nguồn của bước hiểu đề hiện có: một câu hỏi rõ theo dạng được hỗ trợ. Nguồn không trích được an toàn vẫn dùng bài học toán đã duyệt hiện có, không đoán thêm dữ kiện.
- Hợp đồng bổ sung tùy chọn: `summary: {givens: string[], question: string} | null`. Từ 1–12 mệnh đề, mỗi mệnh đề không rỗng và tối đa 200 ký tự; câu hỏi tối đa 100. Vượt giới hạn thì bỏ toàn bộ bản tóm tắt; không âm thầm ghi một phần thành bản đầy đủ. Nguồn được trích nguyên văn, chỉ tách/trim mệnh đề và bỏ nhãn tiêu đề.
- Chỉ công khai summary sau hai câu đọc hiểu được máy chủ chấm đúng; giữ kiểm tra quyền sở hữu, số phiên bản lượt trả lời và thời hạn. Java và mobile kiểm tra giới hạn/pha, vẫn nhận được phản hồi cũ không có summary.
- Không có bằng chứng thiết bị vật lý hoặc chất lượng AI trực tuyến trong đợt này. Kiểm tra web dùng HTTP fixture với chuyển trạng thái Python thật và bộ lập kế hoạch toán được thay bằng dữ liệu kiểm thử. Không huấn luyện, đổi model hoặc đánh giá mới độ chính xác OCR.

## Thay đổi chính

- `apps/student-mobile/src/features/tutoring/FractionExplorer.tsx` — đổi hình, trạng thái và cách chọn tương đương.
- `apps/student-mobile/src/features/tutoring/FractionShape.tsx` — hình và các vùng bằng nhau.
- `apps/student-mobile/src/features/tutoring/ProblemSummary.tsx` — hướng dẫn/hiện tóm tắt theo tiến độ.
- `apps/student-mobile/src/app/learning/math-guide.tsx` — ghép vào luồng học, giữ mô hình nguồn khi tính.
- Python `lesson.py`, Spring tutoring DTO/service và mobile `TutorService.ts` — metadata nguồn có giới hạn và kiểm tra trước khi hiển thị.
- Các bộ kiểm tra tương ứng và `apps/student-mobile/package.json`, `package-lock.json`.

Đã cài `react-native-svg` 15.15.4 qua `npx expo install react-native-svg` theo [tài liệu đúng phiên bản SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/svg/), sau khi đọc [tham chiếu SDK 57](https://docs.expo.dev/versions/v57.0.0/).

## Kết quả kiểm tra

| Phạm vi | Bằng chứng |
|---|---|
| Toàn bộ Student | **732/732**, 53 suites, `npm test -- --runInBand --silent` |
| Sau chỉnh bố cục cuối | **44/44** trong `problemSummary.test.tsx` và `tutorScreen.test.tsx` |
| TypeScript + ESLint các tệp triển khai mới/sửa | Qua, không lỗi/cảnh báo |
| Python bài học/tutor/notebook | **387/387**, hai cảnh báo thư viện Starlette/anyio |
| Java service/controller, chạy `--rerun-tasks` | **98/98** (71+27), build thành công |
| Export bản cuối web/Android/iOS | Thành công, 32 route web |
| Trình duyệt bản cuối | Qua 320×740, 390×844, 820×1180, 1440×1000; không tràn ngang/lỗi trang |
| Rà soát độc lập phạm vi tính đúng/trợ năng/nguồn | Không có phát hiện cần sửa; lỗi chữ dồn cạnh phân số được phát hiện khi xem ảnh và sửa trước lượt web cuối |
| `git diff --check` | Qua |

Lệnh Python từ `ai/runtime`:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_source_understanding.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py tests/test_primary_lessons.py tests/test_math_tutor.py tests/test_notebook_tutor.py tests/test_notebook_math_layout.py -q
```

Lệnh Java từ `backend/business-api`:

```powershell
.\gradlew.bat test --tests com.mathvisionkids.api.tutoring.MathTutorServiceTest --tests com.mathvisionkids.api.tutoring.MathTutorControllerTest --rerun-tasks --console=plain
```

Web kiểm tra trực tiếp vùng hình, ba dạng, giữ lựa chọn qua bước học, Space/Enter, không gọi chấm bài khi thao tác cục bộ, chưa công khai summary sớm, giữ mệnh đề định tính, mở/thu gọn tóm tắt và hoàn tất bài giải. Fixture cuối dùng đáp án **Sai** ở câu kiểm tra đọc hiểu để bảo đảm không phụ thuộc luôn chọn Đúng.

Runner và kết quả: `E:/MathVisionKid/scratch/fraction-shapes-qa/check.cjs`, `results.json`. Ảnh tiêu biểu: `shape-Hình tròn-390.png`, `shape-Hình vuông-820.png`, `shape-Thanh phân số-820.png`, `summary-820.png`. Bundle cuối: `scratch/fraction-shapes-web`. Các đường dẫn scratch là đầu ra kiểm tra cục bộ được Git bỏ qua, chưa phát hành.

Chưa commit, push hoặc deploy. Giữ nguyên các thay đổi trước, tài liệu gốc, dữ liệu Drive và báo cáo không liên quan.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: hình học và hướng dẫn tương tác cho học sinh.
  - Applied to: đổi biểu diễn, cách chọn phần, kích thước thao tác và phản hồi rõ ràng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native và web dùng chung.
  - Applied to: component hình/tóm tắt, state giữ/đặt lại đúng phạm vi, hợp đồng dữ liệu tùy chọn.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: phần tử tương tác, mở/thu gọn và nội dung phản hồi.
  - Applied to: nhãn, phím Space/Enter, checkbox tương đương, dấu chọn/tiêu điểm và trạng thái mở rộng.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bổ sung nhỏ vào hợp đồng backend hiện có.
  - Applied to: tái sử dụng bộ trích nguồn/chấm phiên, giới hạn metadata, không thêm bộ sinh hoặc model.
