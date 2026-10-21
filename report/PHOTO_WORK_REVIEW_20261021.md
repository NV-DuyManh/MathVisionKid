# Chụp bài làm, nhận xét và bôi vàng vùng cần sửa

Ngày kiểm tra: 21/10/2026. Nhánh: `codex/meeting-actions-20261021`.

Yêu cầu: học sinh chụp đề, chụp tiếp bài giải của mình; hệ thống nhận xét, hướng dẫn sửa và tuyên dương khi làm đúng. Chủ dự án làm rõ rằng highlight phải là **bôi vàng trực tiếp lên vùng cần sửa trên ảnh bài làm**, không chỉ khung viền hoặc tô chữ đã nhận diện.

## Luồng đã triển khai

1. Chụp/chọn ảnh đề, kiểm tra thông tin riêng tư và cắt vùng bài toán như luồng hiện có.
2. Chọn chụp thêm bài làm. Giữ nguyên đề đã xác nhận, ảnh đề và các dòng/vị trí của ảnh bài làm qua lần chụp bổ sung. Vẫn cho chụp bài làm khi đang học hoặc sau khi hoàn tất bài học.
3. Đối chiếu đề và bài làm đọc được với ảnh. Không tự gửi nhận xét khi chưa xác nhận; dấu `[?]` phải được làm rõ.
4. Chọn **Nhận xét bài em làm**. Trả về một trong ba trạng thái: phù hợp toàn bài, có dòng cần sửa, hoặc cần làm rõ trước khi kết luận.
5. Dòng được xác định cần sửa có **lớp bôi vàng bán trong suốt trên đúng ảnh nguồn**. Nét chữ vẫn nhìn thấy. Số dòng đặt phía trên vùng để hạn chế che chữ; các nút dòng tương đương dùng được bằng bàn phím và trình đọc màn hình.
6. Chọn dòng để đọc nhận xét, mở lần lượt gợi ý. Học sinh tự sửa trong vở rồi chụp lại, hoặc nhập riêng dòng vừa sửa. Không điền hộ đáp án, không sửa ảnh nguồn, không chấm đúng chỉ vì đã mở gợi ý.
7. Sau sửa bằng chữ, bỏ kết quả/vị trí cũ và yêu cầu xác nhận lại. Ảnh trước khi sửa được ghi rõ là ảnh cũ, không dùng làm ảnh minh chứng của nội dung mới. Chụp lại thì dùng ảnh và vị trí mới.
8. Với bài được đối chiếu phù hợp, hiển thị lời khen cụ thể về cách làm/đơn vị; cách nghĩ khác chỉ mở khi học sinh chọn, nếu có gợi ý phù hợp.

## Hình ảnh và vị trí bôi vàng

`WorkPhotoEvidence.tsx` vẽ lớp màu `rgba(255, 221, 0, 0.32)` trên ảnh gốc đang xem; chỉ dòng `FIX` có nền vàng. Dòng `OK` có viền xanh và nhãn đúng; dòng `UNSURE` dùng viền đứt, không bôi vàng như lỗi toán.

Tọa độ lấy từ dòng vật lý mà luồng đọc ảnh đã xác định, theo cạnh trái/trên/phải/dưới trên thang 0–1000. Không nhận tọa độ do AI nhận xét tự sinh. Liên kết nhận xét cần đúng cả chỉ số dòng và nguyên văn nguồn đã chuẩn hóa; không tìm gần giống bằng câu trích. Tỷ lệ canvas khớp ảnh tự nhiên, có giới hạn chiều cao; bỏ qua kết quả tải ảnh cũ/muộn, cho thử mở lại khi lỗi.

Không có vị trí đủ chắc thì vẫn nhận xét bằng nội dung dòng, không bịa vùng bôi vàng. Phạm vi đánh dấu là **vùng dòng**, chưa phải định vị riêng từng chữ số/nét bút. Các khối phân số/chia dọc mà luồng đọc hiện tại không trả vị trí tin cậy vẫn giữ `box=null`.

## Kiểm tra bài và bảo vệ dữ liệu

- Thêm `POST /api/v1/student/tutor/work-review` qua Spring, gọi nội bộ `POST /internal/v1/tutor/work-review`. Spring giữ xác thực và phân quyền học sinh; không mở đường gọi AI trực tiếp từ ứng dụng.
- Yêu cầu có xác nhận kiểu boolean thật cho cả đề và bài làm, nguồn có giới hạn, tối đa 35 dòng, mỗi dòng tối đa 500 ký tự, tổng bài làm tối đa 6000. Mỗi phản hồi gắn với `sourceId` đúng lượt yêu cầu và đủ các dòng theo thứ tự nguồn.
- Hai lượt nhận xét độc lập về ngữ cảnh, chỉ nhận đề và các dòng nguồn, không xem kết luận của nhau. Phải đồng thuận về dữ kiện, phương pháp, toán, đơn vị và độ đầy đủ trước khi khen đúng toàn bài. Chấp nhận phương pháp hợp lệ khác, không buộc giống bài giải mẫu duy nhất.
- Tái sử dụng kiểm tra đẳng thức chính xác cho số/phân số. Phép tính sai không được biến thành đúng vì AI khen. Khi hai lượt cùng chỉ ra lỗi và gợi ý an toàn, giữ gợi ý sát dòng đó; không thay bằng lời hướng dẫn chung không liên quan.
- Câu gợi ý không cung cấp đáp án đã tính hoặc toàn bộ lời giải để chép. Sửa bộ lọc tiếng Việt chặn nhầm “sau khi/sau đó”, vẫn chặn việc đưa số đáp án bằng chữ.
- Thiếu hình vẽ cần thiết, biểu thức chưa hỗ trợ, nguồn thay đổi, nhận xét bất đồng/sai cấu trúc: giữ trạng thái cần đối chiếu. Dịch vụ không phản hồi thì thông báo thử lại, không tự tạo lời khen.
- Đổi nguồn, tài khoản, chỉnh đề/bài làm hoặc rời màn hình hủy lượt đang chờ. Kết quả muộn không gắn sang nguồn mới. Mở gợi ý, đổi dòng và xem cách nghĩ khác không gọi chấm lại.
- Camera native chờ sẵn sàng, chống chụp lặp, dừng preview khi rời màn hình, bỏ ảnh hoặc kết quả thư viện trả muộn kể cả sau khi quay lại; giữ đề và ngữ cảnh lần chụp bổ sung. Không đổi luồng riêng tư/cắt ảnh.

Không thêm thư viện hoặc model trong đợt này. Đọc [SDK 57](https://docs.expo.dev/versions/v57.0.0/) và [camera SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/camera/) trước khi sửa mã.

## Kiểm chứng

- Python sau mẫu ảnh chủ dự án: **525 kiểm tra qua** trong 11 tệp liên quan hướng dẫn, nhận xét, notebook/layout và bảo vệ lỗi đầu tiên; hai cảnh báo deprecation Starlette/anyio hiện có. Riêng phần nhận xét mới: **92 kiểm tra qua**, gồm hồi quy ảnh vườn cây, lọc tiếng Việt và giữ gợi ý cụ thể.
- Java: **108 kiểm tra qua**, chạy `--rerun-tasks`: controller 32, service 76; không lỗi, không bỏ qua. Gồm xác thực/phân quyền, xác nhận nguồn, giới hạn và phản hồi nhận xét sai nguồn/sai cấu trúc.
- Student bản bôi vàng cuối: **811/811 kiểm tra qua / 57 suites**, `npm test -- --runInBand --silent`. Các kiểm tra nhận xét, ảnh bằng chứng và camera bổ sung đều có trong lượt này.
- TypeScript và ESLint các tệp triển khai sửa/thêm: qua.
- Export bản cuối web, Android, iOS: qua, 32 route web. Đây là export bundle, không phải bằng chứng cài/chạy trên máy thật.
- Trình duyệt bản bôi vàng: qua 390×844, 820×1180, 1440×1000, 320×740. Thử chọn ảnh qua bộ chọn thật của trình duyệt, xác nhận riêng tư, cắt toàn ảnh, nhận xét, mở gợi ý dần, sửa chữ, xác nhận lại, chụp lại và tuyên dương. Kiểm tra màu nền vàng trên vùng sai, nền trong suốt trên dòng khác, tỷ lệ ảnh, vị trí vùng, bàn phím và không tràn ngang/lỗi trang.
- Rà soát độc lập phát hiện và đã sửa: trạng thái bận sau quay lại màn hình, khác biệt trim Unicode, hiển thị chưa rõ trái với nguồn vừa xác nhận, lộ toàn bộ gợi ý sớm qua component ảnh, thông báo nội dung mới và nút cuối bị mất tiêu điểm.
- `git diff --check`: qua; thông báo LF/CRLF là cấu hình working copy.

Fixture trình duyệt ban đầu là ảnh mẫu được tạo cục bộ, dùng kết quả bộ nhận xét Python thật với toàn bộ lời gọi model được mock. Bằng chứng này không đo độ chính xác OCR/AI trực tuyến hay camera thiết bị vật lý. Mẫu ảnh chủ dự án bên dưới có thêm các lượt OCR và nhận xét AI trực tuyến có giới hạn; độ đúng ngữ nghĩa vẫn phụ thuộc dịch vụ AI đang cấu hình, hai lượt nhận xét không bảo đảm tuyệt đối.

Đầu ra kiểm tra được Git bỏ qua:

- `scratch/work-review-qa/make_fixture.py`, `fixture.json`, `check.cjs`, `results.json`.
- Ảnh đã xem: `revision-photo-390.png`, `revision-photo-820.png`, `correct-820.png`, `rewrite-320.png` trong cùng thư mục QA.
- Bundle: `scratch/work-review-web/`.

Lệnh Python:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_work_review.py tests/test_source_understanding.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py tests/test_primary_lessons.py tests/test_math_tutor.py tests/test_notebook_tutor.py tests/test_notebook_math_layout.py tests/test_notebook_row_panels.py tests/test_notebook_capacity.py tests/test_earliest_error.py -q
```

Lệnh Java:

```powershell
.\gradlew.bat test --tests com.mathvisionkids.api.tutoring.MathTutorServiceTest --tests com.mathvisionkids.api.tutoring.MathTutorControllerTest --rerun-tasks --console=plain
```

Các thay đổi chính: `work_review.py` và endpoint Python; DTO/service/controller Spring; `TutorService.ts`, `StudentWorkReview.tsx`, `WorkPhotoEvidence.tsx`; state ngữ cảnh ảnh; `math-guide.tsx`, camera native và các tệp kiểm tra tương ứng. Giữ toàn bộ thay đổi trước và báo cáo không liên quan.

## Mẫu ảnh vườn cây do chủ dự án cung cấp

Nguồn: `C:/Users/Admin/AppData/Local/Temp/codex-clipboard-2fd24bf3-ee8e-4d43-baa5-7c4f05a65275.png`, ảnh 960×540. Đọc trực tiếp tệp được cung cấp; không chỉnh ảnh hoặc sao chép vào corpus huấn luyện.

- Hai đẳng thức nhìn thấy đều đúng: `1/3 + 2/5 = 11/15` và `1 - 11/15 = 4/15`. Bài còn thiếu bước dùng số cây cam và phần tương ứng để tìm tổng số cây. Không bịa dòng sai hoặc bôi vàng hai phép tính đúng. Ký hiệu `(số cây)` cần đọc cùng câu lời giải nói về phần tổng số cây, không tự coi đây là số đếm cây lẻ.
- Lượt OCR thật đầu có lặp phần đề trong các dòng bài làm. Đã làm rõ prompt và chỉ loại phần đề lặp trước tiêu đề “Bài giải” khi nội dung khớp chính xác với đề vẫn được giữ. Nếu có số/chữ khác, giữ nguyên để đối chiếu. Lượt OCR sau tách được đề và năm dòng phần bài làm, gồm tiêu đề; các phân số đọc đúng.
- Hai lượt nhận xét thật đã nhận ra bài chưa hoàn thành. Sửa luồng để khi cả hai cùng xác nhận những dòng hiện có đúng, chỉ còn thiếu kết quả được hỏi, giữ hướng dẫn cụ thể cho bước làm tiếp; không khen hoàn tất hoặc sinh thêm dòng đã giải.
- Bộ lọc trước đó chặn nhầm các cụm sư phạm như “một phân số”, “hai tử số” và yêu cầu kết thúc câu “viết đáp số”. Chỉ cho phép các cụm hẹp, có kiểm tra biên câu; vẫn chặn số kết quả, số viết bằng chữ, đẳng thức và nhãn đáp án. Có kiểm tra đối kháng cho câu gần giống, dấu hai chấm, “là”, kết quả bằng chữ và nhãn ở câu tiếp theo.
- Nếu diễn đạt của một lượt bị chặn nhưng lượt còn lại an toàn hoàn toàn, chỉ dùng nguyên phần diễn đạt an toàn khi schema/nguồn của cả hai hợp lệ, năm boolean và mọi trạng thái dòng giống nhau. Không ghép câu từ hai bản, không sửa lời không an toàn để đưa ra giao diện. Sai nguồn hoặc có bất đồng thì giữ fallback thận trọng; phép tính chính xác vẫn có quyền ép `FIX`.
- Phát lại hai phản hồi AI thật đã ghi qua mã hiện tại cho kết quả `NEEDS_REVIEW`, bốn dòng viết tay `OK`, không praise/alternative, có việc cần làm tiếp. Đây là **replay phản hồi đã ghi**, không phải lượt gọi model mới hoặc bằng chứng đường API công khai đã chạy hoàn chỉnh.
- Kiểm tra giao diện với chính ảnh thật qua thư viện → riêng tư → cắt ảnh → xác nhận → nhận xét trên 390, 820 và 1440 px đều qua, không tràn ngang. Phần OCR dùng kết quả thật; phần nhận xét trong lượt kiểm tra giao diện dùng kết quả kỳ vọng với model mock. Không bịa tọa độ cho các khối phân số `box=null`.
- Lượt gọi trực tuyến cuối dừng sau một phản hồi thành công vì dịch vụ báo **`RATE_LIMIT`** ở lượt còn lại. Không tiếp tục gọi thử dồn hoặc kết luận hết quota tháng. **Chưa xác nhận toàn luồng trực tuyến sau sửa đạt**; đã xác nhận OCR trực tuyến, replay kết quả thật và hồi quy ngoại tuyến. Không có bằng chứng thử camera trên thiết bị vật lý.

Đầu ra QA được Git bỏ qua trong `scratch/owner-garden-review-qa/`: `live-reading.json`, các phản hồi trước sửa, `recorded-review-result.json`, `ui-fixture.json`, `ui-results.json`, ảnh `garden-390.png`, `garden-820.png`, `garden-1440.png`. Các tệp này không chứa khóa API; không đưa phản hồi nội bộ chưa lọc lên giao diện học sinh.

Chưa commit, push hoặc deploy. Không huấn luyện, thay model, tải/sao chép corpus Drive hoặc đăng ký dịch vụ trả phí.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: phản hồi học tập và tương tác trực tiếp trên ảnh.
  - Applied to: bôi vàng, số dòng, trạng thái, mở gợi ý dần, sửa và tuyên dương.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: luồng React Native dùng chung web/native.
  - Applied to: giữ/đặt lại state đúng nguồn, hủy tác vụ, ảnh đúng tỷ lệ và camera khi đổi màn hình.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: vùng ảnh, lựa chọn dòng, ô sửa và nội dung mở rộng.
  - Applied to: nút dòng 48, tiêu điểm, phím, nhãn/trạng thái, phản hồi đọc được và không chỉ dựa vào màu.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: API và kiểm tra toán tái sử dụng luồng có sẵn.
  - Applied to: endpoint stateless có giới hạn, kiểm tra đẳng thức hiện có, không thêm model/lớp lưu trữ hoặc thư viện.
