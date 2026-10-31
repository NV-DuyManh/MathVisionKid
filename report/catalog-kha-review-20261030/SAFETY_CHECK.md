# Kiểm tra bổ sung và sửa lỗi — 30/10/2026

**Đã tích hợp vào app local sau báo cáo này:** xem [báo cáo runtime hiện tại](../local-app-integration-20261030/REPORT.md). Nội dung bên dưới giữ nguyên trạng thái và bằng chứng của lượt kiểm tra trước tích hợp.

## Kết luận cập nhật

Đã sửa các lỗi tái hiện được và kiểm tra bản kết hợp **Kha + catalog** trong worktree riêng:

- Nhánh kiểm tra: `codex/kha-safety-fixes-20261030`.
- Thư mục: `C:/Users/Admin/.codex/worktrees/kha-catalog-review/MathVisionKid`.
- Nền Kha: `bf29939b4c47be180581f951c1e7483011227b17`.
- Main/origin/main vẫn là `20d6780f3a77b0ac2db96edc575e62481788ccad`.

**Nhánh Kha gốc/PR #7 chưa nhận các bản sửa này. Không merge trực tiếp PR gốc rồi cho rằng lỗi đã hết.** Bản đã sửa đang nằm local, chưa commit/push/merge. Các lỗi chặn merge đã được sửa trong bản local và vượt qua kiểm tra dưới đây; bước tích hợp cần mang theo toàn bộ các bản sửa cùng catalog.

## Lỗi đã sửa

### 1. Viết thêm chữ số: hiểu toàn bộ đề trước khi giải nhanh

Bộ nhận dạng cũ tìm riêng chữ số, hiệu và từ “tìm số”, nên trả 59 ngay cả khi đề còn yêu cầu số chẵn hoặc nhỏ hơn 50. Bản sửa nhận toàn bộ hai cấu trúc câu được hỗ trợ. Điều kiện/câu hỏi khác chưa hiểu, số thập phân, số âm, phân số trong vị trí hiệu, chữ số viết thêm không hợp lệ hoặc số chữ số mâu thuẫn đều bỏ đường giải nhanh và chuyển sang đường kiểm tra đầy đủ.

Kiểm tra cả giới hạn độ dài/số lượng và điều kiện số chữ số. Có thêm kiểm tra 80 tổ hợp số gốc/chữ số viết thêm, dùng phép ghép chuỗi thập phân để tính hiệu đối chứng; không cố định đáp án 59.

### 2. Phân số phần còn lại: không bỏ qua điều kiện trong lời văn

Đã tái hiện lỗi với “Tổng số cây là số lẻ” đặt trước đề có đáp số 60. Trước đây cả tiền tố tự do của AI và luồng quiz Java có thể nhận phần đề phía sau rồi bỏ điều kiện này.

Đã giới hạn cấu trúc mở đầu/câu hỏi được hiểu ở cả hai luồng. Các đề hợp lệ về vườn cây, sách, kẹo, bi, hoa và bóng vẫn được kiểm tra bằng số hữu tỉ chính xác, bảo toàn số lượng và yêu cầu số lượng nguyên.

### 3. Đúng đối tượng được hỏi và nơi chứa dữ kiện

Đã tái hiện đề cho vườn bác Nam nhưng hỏi vườn bác Tư vẫn bị chấp nhận. Nay kiểm tra ngữ cảnh được nêu rõ trong câu hỏi và phần cho số lượng: chủ thể/chủ sở hữu/nơi chứa phải khớp với phần mở đầu. Vườn và vườn cây được nhận là cùng loại địa điểm; địa điểm hoặc tên chủ khác phải qua đường kiểm tra đầy đủ.

Kiểm tra trường hợp số cây cam cho ở vườn bác Tư hoặc ở lớp trong khi đề đang xét vườn bác Nam. Áp dụng cho cả hai đường kiểm chứng quiz Java để không vượt guard qua một parser khác.

Đổi phiên bản xác minh quiz sang `confirmed-problem-v5` để phần chuẩn bị quiz nhận biết chính sách mới.

### 4. Catalog: dữ liệu hỏng phải được loại bỏ an toàn

Đã thêm kiểm tra kiểu dữ liệu BLOB và hạn dùng trước khi tính hash/so sánh. Một cột payload hỏng thành TEXT được phát hiện, loại bỏ và tạo lại qua đường kiểm tra hiện có. Kiểm kê có thể phát hiện payload sai kiểu mà không sập. Bổ sung test tái hiện bằng database tạm.

Đã kết hợp catalog với Kha trong worktree kiểm tra, giữ nguyên các thay đổi Kha có sẵn. Cả kế hoạch từ model đã kiểm tra và bộ giải chính xác đều dùng cùng cơ chế lưu. Hai test tích hợp xác nhận đề hợp lệ dùng lại được và đề thêm điều kiện không hit catalog, không lưu kế hoạch thất bại.

Tại `E:/MathVisionKid`, phần catalog cũng đã nhận bản sửa dữ liệu hỏng và được kiểm tra riêng trên nền main. Các bản sửa bộ giải/quiz của Kha nằm ở worktree riêng, chưa đưa vào ứng dụng đang chạy ở thư mục E.

## Kết quả kiểm tra cuối

| Phạm vi | Kết quả thực tế |
|---|---|
| Student Kha, toàn bộ Jest | **108/108 suite; 1.239/1.239 test qua**, 65,067 giây |
| AI Kha + catalog + các bản sửa | **276 test qua**, 2 cảnh báo deprecation, 16,82 giây |
| Java toàn bộ và bootJar sau bản sửa cuối | **463 test: 0 failure/error, 1 skip**; build thành công, 2 phút 4 giây |
| Catalog trên nền main riêng tại E | **152 test qua**, 9,34 giây |
| Catalog store độc lập, thư viện chuẩn | **2 test qua** |
| Corpus công khai hiện có | 20 đề phân biệt; 0 trùng nguồn chính xác |
| Docker Compose cấu hình bản kết hợp | `config --quiet` thành công |
| Git whitespace bản kết hợp | `diff --check` thành công |

Ca Student từng timeout nằm trong bộ 1.239 test chạy lại đã qua. Chưa có bằng chứng xác định nguyên nhân timeout lần trước; không báo đã sửa một lỗi React runtime khi chưa tìm thấy nó. Các thay đổi lần này tập trung vào backend, bộ giải và catalog, không thay giao diện Student.

Java chạy trên môi trường test của dự án, chưa xác nhận migration trên dữ liệu production. Cảnh báo còn lại: FastAPI `on_event` deprecation và Gradle có tính năng sẽ không tương thích Gradle 10. Chúng chưa gây thất bại trong các lượt chạy trên.

Chưa có kiểm tra Android/iOS thật trong lượt này. Các test dùng dữ liệu/đáp ứng kiểm soát và không chứng minh mọi đề tự do, mọi mạng hoặc mọi dịch vụ bên ngoài sẽ luôn thành công. Kết quả đủ xác nhận các lỗi tái hiện ở trên đã được sửa trong bản local; không gọi đó là bảo đảm “hoàn hảo 100%”. Không huấn luyện/chuyển model, không thay hai giọng, không thay timeout giọng 60 giây, không tác động demoUI.

## Bằng chứng và vị trí

- Trước sửa: `kha-parser-reproduction.json` và `REPORT.md`.
- Sau sửa: `safety-after-fixes.json`, `safety-check-results.json`.
- Log trên máy: `E:/MathVisionKid/runtime/kha-catalog-safety-python-20261030.log`, `kha-safety-java-20261030.log`, `kha-safety-student-20261030.log/json`, `catalog-safety-main-20261030.log`.
- Đường dẫn các bản sửa: `ai/runtime/app/tutoring/digit_append.py`, `fraction_remainder.py`, `lesson.py`, `catalog_store.py`; `backend/business-api/src/main/java/com/mathvisionkids/api/quiz/QuizMath.java` và các regression tương ứng.
- Catalog/bot và giới hạn dữ liệu: `catalog/README.md`. Workflow chỉ chạy trên GitHub sau khi được push; chưa tuyên bố có lượt chạy cloud.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Sửa đúng điểm dùng chung của bộ giải và lưu trữ, giữ giải pháp nhỏ và không thêm thư viện.
  - Applied to: Nhận dạng toàn bộ câu, kiểm tra ngữ cảnh, SQLite hỏng, tích hợp catalog và test chống tái phát.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Kiểm tra lại tính ổn định của bộ Student React sau timeout trong lượt review trước.
  - Applied to: Kiểm tra hook/trạng thái bất đồng bộ đã review và chạy đầy đủ 108 suite; không có thay đổi UI React trong lượt này.
