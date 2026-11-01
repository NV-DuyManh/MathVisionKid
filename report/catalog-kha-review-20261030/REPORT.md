# Catalog và review nhánh Kha — 30/10/2026

Cập nhật sau kiểm tra bổ sung: xem [SAFETY_CHECK.md](SAFETY_CHECK.md). Báo cáo dưới đây giữ nguyên bằng chứng review ban đầu; các lỗi được sửa ở worktree local riêng, chưa đẩy lên nhánh Kha gốc.

## Kết luận

Đã thêm catalog vào mã nguồn đang làm việc tại `E:/MathVisionKid`, nhánh `codex/verified-catalog-20261030`. Chưa commit/push phần mới. **Chưa merge Kha vào main** vì tái hiện được lỗi bộ giải bỏ qua điều kiện phụ và trả đáp án trái đề. Main và origin/main vẫn cùng commit `20d6780f3a77b0ac2db96edc575e62481788ccad`.

## Catalog đã triển khai

1. Máy chủ tự lưu kế hoạch toán đã qua luồng tạo/kiểm tra hiện có, sau khi học sinh xác nhận đề. Kế hoạch chuẩn bị ngầm cũng được thu vào catalog khi phiên học đã xác nhận sử dụng nó. Không tự thu bản OCR chưa xác nhận hoặc bài có phần làm riêng của học sinh thành kế hoạch dùng lại.
2. Lần gặp lại đúng đề, cùng tài khoản, máy chủ đọc bản lưu và kiểm tra lại schema, dữ kiện, phép toán. Phiên học vẫn tạo ID mới, revision 0 và chưa có đáp án đã hoàn thành. Các ý hướng dẫn ban đầu và ý riêng của bước được giữ đúng ranh giới; đáp án/bước sau không được phát hành trước.
3. So khớp chỉ chuẩn hóa Unicode NFC và khoảng trắng. Đổi số, đơn vị, quan hệ, dấu hoặc tài khoản không dùng chung. Bản đầu chưa tái sử dụng dữ liệu riêng chéo tài khoản; muốn chia sẻ toàn hệ thống cần một bộ công khai được tuyển chọn, khử thông tin riêng và duyệt riêng.
4. Âm thanh TTS đã hợp lệ được lưu bền vững theo tài khoản, nguyên văn các đoạn theo thứ tự, giọng, chế độ dự phòng và phiên bản xử lý giọng. Có thể dùng lại qua phiên mới hoặc lần khởi động sau. Quyền sở hữu phiên, revision và quyền nghe nội dung vẫn được kiểm tra trước khi đọc cache. Không lưu bản ghi câu hỏi của học sinh vào catalog này.
5. SQLite dùng thư viện chuẩn, không thêm dependency. Mặc định lưu 30 ngày, tối đa 500 mục mỗi loại, 128 MiB payload âm thanh. Docker có volume riêng. Tệp trạng thái không vào Git hoặc image build. Hash tài khoản là định danh giả, không phải mã hóa/ẩn danh; volume phải được bảo vệ như dữ liệu ứng dụng.
6. Hết hạn, thay đổi chính sách kiểm tra, kế hoạch/WAV hỏng hoặc SQLite không truy cập được thì quay về luồng xử lý hiện có. Không trả bản hỏng để cố báo thành công. Giới hạn payload không đồng nghĩa SQLite thu nhỏ tệp vật lý ngay lập tức.

Không có thay đổi giọng, giao diện Student, timeout giọng 60 giây, mô hình OCR hay huấn luyện model trong công việc này. Không động vào demoUI.

## Vai trò bot GitHub

Workflow `.github/workflows/lesson-catalog.yml` đã được viết: chạy khi PR/push main có thay đổi liên quan, chạy thủ công hoặc mỗi ngày 02:17 UTC. Nó kiểm tra lưu trữ/cách ly/toàn vẹn và kiểm kê bộ regression công khai để phát hiện bản ghi sai cấu trúc, trùng ID hoặc trùng đề chính xác. Actions được ghim SHA đã đối chiếu với tag của kho chính thức; token chỉ đọc, không giữ credential checkout, không cần khóa API.

**Ứng dụng thu dữ liệu riêng ngay trên máy chủ; bot kiểm tra phần được phép đặt trong kho.** Workflow không tự kết nối máy cá nhân để lấy SQLite, không đưa dữ liệu học sinh lên GitHub, không tự xác nhận lời giải đúng về ngữ nghĩa và không tự merge. Sau khi được push, GitHub mới có thể chạy workflow; chưa có bằng chứng một lượt chạy trên GitHub trong báo cáo này.

Xem `catalog/README.md` để cấu hình, chạy tương đương tại máy và kiểm kê/dọn bản hết hạn bằng lệnh quản trị. Kiểm kê mặc định dùng kết nối chỉ đọc và không tạo database rỗng. Thêm `--prune` mới xóa mục hết hạn/hỏng.

## Kiểm chứng catalog

| Kiểm tra | Kết quả |
|---|---|
| Python bài học, giọng, chuẩn bị ngầm, regression, catalog | 151 pass; gồm 11 test catalog mới |
| Hai test lưu trữ độc lập, chỉ thư viện chuẩn | 2 pass |
| Kiểm kê corpus hiện có | 20 đề, 20 nguồn phân biệt, 0 trùng |
| Docker Compose cấu hình | `config --quiet` thành công; không khởi động/rebuild container |
| Git whitespace | `diff --check` thành công |

Các test mới kiểm tra phiên mới không gọi lại model khi trùng đề; thay số/đơn vị/quan hệ/tài khoản thì không hit; không thu bản nháp/bài làm; thất bại không được lưu; bản sai/hỏng/hết hạn bị loại; giới hạn dung lượng/LRU; giữ ý hướng dẫn riêng; âm thanh không vượt quyền nghe; bản chuẩn bị ngầm chỉ được thu sau xác nhận; thay chính sách thì miss; lưu trữ lỗi vẫn giải theo đường cũ.

40 lượt đọc fixture đã được kiểm tra: trung vị **12,187 ms**, p95 **14,928 ms**, lớn nhất **15,276 ms**. Phép đo bao gồm đọc SQLite, parse và kiểm tra lại kế hoạch trên máy này, không gọi cloud/TTS và không đo trên điện thoại. Không thể suy ra mọi bài mới hoặc mọi lần bấm nghe đều dưới 1–3 giây. Chi tiết: `catalog-local-read.json`. Audio test là WAV fixture, không phải bằng chứng đã nghe giọng thật trên thiết bị.

## Kha thêm gì

Đối chiếu lại sau fetch: head Kha `bf29939b4c47be180581f951c1e7483011227b17`, PR #7: https://github.com/NV-DuyManh/MathVisionKid/pull/7. Main là tổ tiên của Kha: 0 commit chỉ main, 5 commit chỉ Kha; khoảng 256 tệp, +12.398/-4.092 dòng. Không có xung đột lịch sử với main hiện tại; điều đó không bảo đảm hành vi đúng.

- Quiz thông minh sau bài học/nhận xét: chuẩn bị đề, xác minh phép toán, lưu nguồn và lịch sử, luyện lại bài gốc hoặc bài biến thể, chấm sao theo thời gian và không thưởng sao khi xem lời giải/luyện lại. Có snapshot lần làm, khóa/idempotency và phần giọng quiz.
- Nâng giao diện Admin, quản lý người dùng/lớp/nhật ký và thống kê nhận diện; thay đổi cách ly phiên đăng nhập và SSO, kiểm tra lại quyền khi đổi vé SSO.
- Giữ ba bước đọc hiểu đã làm khi chuẩn bị toán lỗi, có trạng thái chờ/thử lại/polling thay vì làm mất tiến độ.
- Bộ giải cục bộ cho một số bài viết thêm chữ số và phân số phần còn lại; thay đổi ảnh Student/iOS và script/runtime phục vụ kiểm tra.
- Thêm migrations V17–V23 cho quiz. Đây là thay đổi xuyên Student, AI, Java, database, Admin, Teacher và launcher, không nên coi là một PR giao diện nhỏ.

## Phát hiện chặn merge

**[P1] Bộ giải viết thêm chữ số bỏ qua phần đề chưa hiểu.**

`ai/runtime/app/tutoring/digit_append.py:33–80` dùng các `re.search` riêng để lấy chữ số, hiệu và yêu cầu tìm số, nhưng không xác nhận toàn bộ đề đã được hiểu. `lesson.py:1113–1124` ưu tiên kết quả này khi không có bài làm, không qua kiểm tra ngữ nghĩa độc lập của cloud. Kiểm tra phép tính chỉ chứng minh `596 - 59 = 537`, không chứng minh đáp ứng mọi điều kiện của đề.

Đã chạy trực tiếp `checked_plan` tại đúng head Kha:

| Đề | Kết quả thực tế | Vấn đề |
|---|---|---|
| Viết thêm 6 bên phải, số mới hơn số cũ 537, tìm số cũ | 531 rồi 59 | Đúng cho đề cơ bản |
| Cùng đề, thêm “Số đó là số chẵn” | Vẫn 531 rồi 59 | 59 là số lẻ; đề mâu thuẫn phải được nhận ra |
| Cùng đề, thêm “Biết số đó nhỏ hơn 50” | Vẫn 531 rồi 59 | 59 không nhỏ hơn 50 |

Bằng chứng: `kha-parser-reproduction.json`. Đây là lỗi tái hiện thực tế, không phải suy đoán từ tên hàm. Cần nhận diện toàn bộ mẫu đề được hỗ trợ; từ chối đường giải cục bộ nếu còn điều kiện/câu hỏi chưa hiểu, hoặc kiểm tra mọi ràng buộc trước khi trả kế hoạch. Không nên chỉ thêm một danh sách từ cấm ngắn vì vẫn lọt các điều kiện khác.

**Độ ổn định kiểm thử cần xem lại:** full Student có 1 test timeout 5 giây tại `tutorScreen.test.tsx:70` (thu gọn đề sau xác nhận). Cùng test chạy riêng đã pass. Vì vậy chưa xác định là lỗi runtime; cũng không được báo full suite đã pass.

## Kiểm chứng Kha trong worktree riêng

| Kiểm tra | Kết quả |
|---|---|
| Java `test bootJar`, JDK 21 | Build thành công; 462 test, 0 fail/error, 1 skip |
| Python reliability/reading/recovery/digit/fraction/quiz/regression | 150 pass |
| Student Jest toàn bộ | 107/108 suite pass; 1.238 pass, 1 timeout; 250,946 giây |
| Ca timeout chạy riêng | 1 pass, 65 ca khác không chạy |
| Student typecheck | Pass |
| Student auth/privacy contracts | 10 pass |
| Admin config/auth/session | 34 pass |
| Teacher config/contracts | 21 pass |
| Portal config | 19 pass |
| Admin và Teacher production build | Đều thành công với địa chỉ HTTPS giả phục vụ build; đều cảnh báo chunk lớn hơn 500 kB |

Không có bằng chứng kiểm tra thiết bị Android/iOS thật, migration trên dữ liệu production hoặc toàn bộ hành trình trình duyệt của Kha trong lượt này. Review đọc trọng tâm solver, luồng chuẩn bị bài/quiz, phân quyền/phiên và các thay đổi liên quan; không tuyên bố đã kiểm toán từng dòng của 256 tệp.

**Đề xuất:** giữ main hiện tại. Yêu cầu sửa lỗi P1 và có regression chống bỏ sót điều kiện trước; làm ổn định full Student. Nên tách thay đổi Admin/auth và quiz/recovery để dễ kiểm tra, rollback và tránh kéo cả script/debug/UI vào cùng một lần. Chưa lấy riêng commit lớn vì các phần đang gộp và phụ thuộc migrations/contract; không cherry-pick theo tên commit để làm sai lệch dự án.

Log đầy đủ giữ tại `runtime/catalog-regression-20261030.log`, `runtime/kha-review-*.log`, `runtime/kha-student-tests-20261030.json` trên máy; các file này không tự đưa lên Git. Không sửa/push nhánh Kha của cộng tác viên, không gửi review/comment ra ngoài.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Backend/catalog cần cách triển khai ít phụ thuộc và dễ kiểm chứng.
  - Applied to: SQLite chuẩn, giới hạn dữ liệu, exact matching, fail-open, CLI và workflow nhỏ.
- `ponytail-review`
  - SKILL.md: `.agents/skills/ponytail-review/SKILL.md`
  - Why selected: Đánh giá độ rộng, phần trùng và chi phí ghép nhánh Kha.
  - Applied to: Phân tách Admin/auth khỏi quiz/recovery; tránh cherry-pick commit gộp hoặc thêm hệ thống mới không cần thiết. Review đúng/sai tách riêng khỏi review độ phức tạp.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Nhánh Kha có hook React bất đồng bộ và thay đổi nhiều ứng dụng React.
  - Applied to: Review useQuizPreparation, trạng thái cũ/polling, kiểm tra Student và build các portal.
