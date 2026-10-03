# MVP hướng dẫn học sinh giải toán — 03/10/2026

Đã bổ sung luồng cốt lõi mà chủ dự án yêu cầu: học sinh đưa ảnh đề toán vào, kiểm tra lại nội dung đã đọc, nhận gợi ý và câu hỏi từng bước, rồi viết suy nghĩ hoặc bước làm của mình để được góp ý. Trước lượt này, nhận diện và kiểm tra phép tính đã có, nhưng chưa có luồng hướng dẫn học độc lập này.

Đây là MVP cho luồng ảnh → hướng dẫn tự giải. Chưa phải xác nhận toàn bộ chức năng và độ chính xác của đề tài capstone đã hoàn tất.

## Cách sử dụng

1. Đăng nhập tài khoản học sinh. Tại Trang chủ, chọn **Chụp bài toán → Chụp đề, học cách giải**, hoặc **Chọn ảnh có sẵn**.
2. Kiểm tra và che thông tin riêng tư, xác nhận ảnh, rồi cắt phần chứa một đề bài.
3. Ứng dụng đọc ảnh và mở **Cùng em tìm cách giải**. Học sinh sửa chữ, số và dấu toán nếu cần; bấm **Đề đã đúng, cùng tìm cách giải**.
4. Chọn **Hiểu đề**, **Chọn cách làm**, **Bước tiếp theo**. Mỗi yêu cầu trả về một gợi ý ngắn và một câu hỏi, thay vì bài giải hoàn chỉnh.
5. Nhập vào **Bước làm của em**, chọn **Góp ý bước em đã làm**. **Em cần gợi ý rõ hơn** tăng mức gợi ý tối đa hai lần, không mở đáp án.

Cũng có thể nhập đề bằng tay hoặc mở từ bài học gợi ý. Khi đọc ảnh lỗi, học sinh vẫn có thể nhập đề để tiếp tục. Sửa đề buộc xác nhận lại và xóa gợi ý của đề cũ. Các nút và nội dung trên màn hình học sinh không chứa tên nhà cung cấp, khóa, địa chỉ API hoặc chỉ dẫn dành cho lập trình viên.

## Những phần đã triển khai

### Student Mobile

- Thêm chế độ `MATH_TUTOR` vào luồng ảnh hiện có, dùng lại chụp/chọn ảnh → che thông tin → cắt ảnh. Các chế độ đọc chữ viết tay và nhận diện phép tính cũ vẫn hoạt động riêng.
- Thêm `/learning/math-guide` và layout yêu cầu đăng nhập. Dùng bộ màu, Nunito và linh vật sẵn có; không thêm thư viện hoặc tài nguyên giao diện mới.
- Bắt buộc xác nhận đề trước khi gọi hướng dẫn. Khi đã xác nhận, ảnh và vùng nhập thu gọn để dành chỗ cho gợi ý.
- Giữ thanh tiến trình ngang và nút dừng chờ. Không hiển thị đồng hồ chờ hoặc phần trăm tự đặt.
- Hủy yêu cầu khi rời màn hình, sửa đề hoặc chọn ảnh khác; bỏ phản hồi đến muộn, tránh gửi trùng. Đề và bước làm được giữ khi dịch vụ lỗi. Phiên hết hạn hiển thị nút đăng nhập lại.
- Bỏ phần trình bày toàn bộ `sampleSolution.lines` ngay trong bài học và bài gợi ý; thay bằng đường vào hướng dẫn tự giải. Dữ liệu bài mẫu vẫn được giữ.

### Business API

- `POST /api/v1/student/tutor/read`: ảnh multipart `file` và `privacyConfirmed=true`.
- `POST /api/v1/student/tutor/guide`: đề đã xác nhận, giai đoạn học, bước học sinh viết, mức gợi ý và gợi ý trước.
- Spring vẫn là nơi quyết định đăng nhập và vai trò: không đăng nhập nhận 401; vai trò giáo viên/quản trị không được dùng API học sinh này. Kiểm thử controller dùng cấu hình bảo mật của dự án.
- Kiểm tra xác nhận ảnh, giới hạn 8 MiB, loại ảnh và dữ liệu đầu vào. Phản hồi AI phải đúng cấu trúc, độ dài và giai đoạn yêu cầu.
- Dịch vụ không sẵn sàng trả lỗi rõ ràng; không giả phản hồi AI thành công. Không trả thông tin nhà cung cấp hoặc khóa nội bộ cho học sinh.

### AI runtime

- Thêm module `app/tutoring`, dùng REST và các pool khóa có sẵn: **Groq ưu tiên, Gemini dự phòng**. Dùng model vision hiện đang được cấu hình; không đổi `.env`, không huấn luyện hoặc đổi trọng số OCR.
- Hai API nội bộ `/internal/v1/tutor/read` và `/internal/v1/tutor/guide` yêu cầu khóa nội bộ. Chuẩn hóa ảnh trong bộ nhớ, xử lý chiều EXIF và bỏ metadata trước khi gửi; chấp nhận JPEG/PNG/WebP tĩnh, tối đa 20 triệu pixel, thu cạnh dài về tối đa 2200 pixel.
- Đọc đề và hướng dẫn là hai yêu cầu riêng. Đọc ảnh không tự gọi giải toán. Đề và bước học sinh viết được đưa vào dưới dạng dữ liệu, không được dùng để thay chỉ dẫn của hệ thống.
- Hướng dẫn có bốn giai đoạn: `UNDERSTAND`, `PLAN`, `NEXT_STEP`, `CHECK_WORK`. Giai đoạn góp ý yêu cầu bước làm không trống, tập trung phương pháp và điểm cần xem lại, không chấm điểm hoặc chứng nhận đáp án đúng/sai.
- Lọc phản hồi chứa chữ số, lượng số bằng chữ, phân số thông dụng, phương trình, nhãn đáp án, lời giải nhiều bước và các khẳng định đúng/sai. Phản hồi không đạt chuyển sang gợi ý khái niệm an toàn theo giai đoạn. Nhận diện các phép nhân/chia để gợi ý dự phòng phù hợp hơn.
- Nếu ảnh có phép tính đã hoàn tất, phần phiên âm phép tính thuần số không mang theo kết quả; vẫn giữ phương trình cho trước có biến như `x + 2 = 5`. Ảnh nhiều đề hoặc không đọc được cần chọn/cắt lại, không tự đoán số.
- Giới hạn ba yêu cầu cloud đồng thời và 30 giây tổng thời gian AI; backend chờ tối đa 40 giây, mobile 45 giây và có thể hủy. Gemini bỏ qua tối đa ba khóa lỗi xác thực trong một yêu cầu; lỗi quota, timeout hoặc lỗi dịch vụ dừng ngay, không quét tiếp các khóa.

## Kiểm thử và bằng chứng

| Phần | Kết quả | Bằng chứng |
| --- | --- | --- |
| Mobile đầy đủ | 374 bài kiểm thử, 34 bộ, không lỗi | [mobile-tests.json](mvp_math_tutor_20261003/mobile-tests.json) |
| Backend đầy đủ | 222 bài kiểm thử, 26 bộ, không lỗi | [backend-tests.json](mvp_math_tutor_20261003/backend-tests.json) |
| AI liên quan | 168 bài kiểm thử trong 16 module, không lỗi; gồm 80 bài tutoring | [ai-focused-tests.xml](mvp_math_tutor_20261003/ai-focused-tests.xml) |
| TypeScript | `npx tsc --noEmit` đạt | Lệnh đã chạy thành công trong lượt này |
| Android export | Đạt, 60 assets | `scratch/mvp_math_tutor_20261003/android-export` |
| Web export | Đạt, 32 routes, có trang math-guide | `scratch/mvp_math_tutor_20261003/web-export` |
| Public API thật | 11 trường hợp đạt | [public-live-flow.json](mvp_math_tutor_20261003/public-live-flow.json) |
| Gemini thật | Đọc ảnh và tạo gợi ý đạt | [gemini-live.json](mvp_math_tutor_20261003/gemini-live.json) |

Tổng 764 bài kiểm thử tự động đạt, không cộng trùng 80 bài tutoring đã nằm trong 168 bài AI. Không chạy lại hoặc tuyên bố toàn bộ bộ kiểm thử AI legacy đạt; phạm vi AI lần này là 16 module liên quan.

Luồng HTTP thật dùng tài khoản seed tại hệ thống local và [ảnh đề tổng hợp](mvp_math_tutor_20261003/synthetic-problem.png), không tải ảnh cá nhân của học sinh. Đề “Lan có 24 viên bi, được cho thêm 18 viên bi” được đọc đúng; các gợi ý không trả 42 hoặc bài giải đầy đủ. Các trường hợp gồm thiếu đăng nhập, thiếu xác nhận ảnh/đề, hiểu đề, chọn cách, bước tiếp theo, phương pháp sai, yêu cầu bỏ qua chỉ dẫn để giải hết, phép nhân và phép chia.

Ví dụ gợi ý thật ở bước chọn cách: “Khi có lượng đồ vật ban đầu và lượng được thêm vào, phép cộng giúp gộp lại để tìm tổng lượng.” Câu hỏi tiếp theo yêu cầu học sinh tự chọn thông tin trong đề, không điền phép tính giúp em.

Lần public kiểm tra cuối ghi nhận 0,468–0,693 giây cho mỗi yêu cầu có suy luận AI. Một lần kiểm tra trước đó có bước tiếp theo mất 8,870 giây; thời gian phụ thuộc dịch vụ và mạng, không bảo đảm mọi ảnh có cùng tốc độ. Gemini đọc ảnh và tạo gợi ý trong tổng 8,792 giây ở tiến trình kiểm tra riêng, chỉ tắt Groq trong bộ nhớ của tiến trình đó, không đổi cấu hình runtime. Lần Gemini trước đã đọc ảnh được nhưng tạo gợi ý gặp lỗi dịch vụ; lần xác minh riêng tiếp theo đạt cả hai thao tác. Không coi lỗi đó là thành công.

Kiểm thử bao gồm biên ảnh, xác thực nội bộ, RBAC, đề chưa xác nhận, phản hồi sai kiểu/giai đoạn, lỗi nhà cung cấp, quota không quét khóa, khóa xác thực lỗi được bỏ qua, prompt injection, đáp án bằng chữ/phân số, khẳng định đúng/sai, hủy và phản hồi đến muộn. Reviewer độc lập kiểm tra lại hai lỗi đáp án phân số và khẳng định đúng/sai đã sửa; không còn phát hiện chặn nghiệm thu.

Tóm tắt máy đọc được: [verification.json](mvp_math_tutor_20261003/verification.json). Tái chạy kiểm tra thật bằng `.venv/Scripts/python.exe -m scripts.verify_math_tutor_mvp --check-gemini` từ thư mục `ai/runtime`, khi stack local đang chạy. Lệnh này dùng dịch vụ cloud thực tế và có thể tiêu thụ quota; báo cáo không chứa token hoặc khóa.

Đã khởi động lại AI với mã cuối cùng và giữ các dịch vụ core đang chạy; preview Student Mobile cũng đã khởi động, endpoint trạng thái trả `packager-status:running`. Việc này xác nhận runtime sẵn sàng, không thay thế kiểm thử tương tác trên thiết bị.

## Giới hạn của MVP

- Mục tiêu là một đề toán tiểu học mỗi lần. Chưa đánh giá trên bộ ảnh học sinh đại diện, trang nhiều câu, hình học phức tạp hoặc mọi dạng chữ viết tay; học sinh luôn phải xác nhận đề.
- Bộ lọc và prompt là biện pháp hạn chế lộ đáp án theo các trường hợp đã kiểm thử, không phải bằng chứng toán học rằng mọi cách diễn đạt của model đều bị chặn. Bộ lọc bảo thủ có thể thay phản hồi bằng gợi ý chung; lần public cuối có ba trong bảy gợi ý dùng đường dự phòng này.
- Góp ý phương pháp chưa phải bộ chấm đúng/sai chính xác bằng symbolic math. Không trả điểm và không kết luận học sinh giải đúng hoàn toàn.
- Phiên hướng dẫn hiện giữ đề và bước làm trên màn hình, chưa lưu lịch sử hội thoại tutor hoặc đánh giá hiệu quả học tập. Lịch sử nhận diện cũ không bị thay đổi.
- Các model OCR chữ viết tay và phép tính hiện có vẫn được giữ. Không có huấn luyện mới hoặc thay model YOLO bằng bộ giải toán tổng quát.
- Chưa xác minh luồng tutor trọn vẹn trong trình duyệt hoặc trên thiết bị Android/iPhone thật. QA trình duyệt ở lượt này đọc được trang chủ/hồ sơ, nhưng tab điều khiển gặp timeout trước khi hoàn tất luồng tutor; không dùng việc đó làm bằng chứng nghiệm thu. Kiểm thử component/API và export là bằng chứng đã hoàn tất.
- Thay đổi ở workspace chưa được commit/push cho lượt MVP này. Không đổi cấu hình, reset dữ liệu hoặc thực hiện migration.

## Tài liệu chính thức đã đối chiếu

- [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), đọc trước khi sửa code mobile.
- [Groq Vision](https://console.groq.com/docs/vision) và [Structured Outputs](https://console.groq.com/docs/structured-outputs).
- [Gemini Image Understanding](https://ai.google.dev/gemini-api/docs/image-understanding) và [Structured Output](https://ai.google.dev/gemini-api/docs/structured-output).

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Triển khai backend/AI tối thiểu bằng cơ chế hiện có, không thêm SDK hoặc hệ thống xử lý mới.
  - Applied to: REST stateless, pool khóa và timeout hiện có, lớp API nhỏ, kiểm thử biên và review độc lập.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native screen và vòng đời yêu cầu bất đồng bộ.
  - Applied to: TutorService, hủy/loại phản hồi muộn, chống gửi trùng, tái sử dụng luồng ảnh.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Trải nghiệm hướng dẫn học sinh trên mobile.
  - Applied to: Xác nhận đề, gợi ý theo giai đoạn, vùng viết bước làm, tiến trình ngang và giao diện theo bộ màu/font sẵn có.
- `control-in-app-browser`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/browser/26.928.21956/skills/control-in-app-browser/SKILL.md` (đã đọc ở phần QA của lượt này trước khi cache plugin thay đổi).
  - Why selected: Miền QA trình duyệt độc lập, ngoài ba skill triển khai.
  - Applied to: Quan sát trang chủ/hồ sơ và thử điều hướng tutor trong trình duyệt của app; không tuyên bố luồng tutor hoàn tất qua browser.

Skills applied: ponytail, vercel-react-best-practices, ui-ux-pro-max, control-in-app-browser.
