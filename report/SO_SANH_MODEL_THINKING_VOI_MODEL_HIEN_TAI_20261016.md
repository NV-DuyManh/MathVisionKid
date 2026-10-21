# Báo cáo so sánh model thinking và model hiện tại của MathVisionKid

**Ngày kiểm tra:** 16/10/2026 — **Phạm vi:** giải toán và hướng dẫn học sinh.

## Kết luận để quyết định

**Chưa nên thay model hiện tại bằng TeacherMath v3 thinking trên Drive.**

TeacherMath v3 thinking cải thiện rõ việc trả đúng định dạng và đáp số kèm đơn
vị so với Qwen3-1.7B gốc trong gói. Tuy nhiên, chưa có bằng chứng đủ rộng cho
thấy nó tốt hơn Qwen3.8-27B/Gemini đang được cấu hình trong dự án. Gói này còn
các lỗi lời giải và gợi ý trực tiếp ảnh hưởng đến việc học của trẻ.

| Câu hỏi | Trả lời từ bằng chứng hiện có |
|---|---|
| Bản thinking trên Drive có điểm mạnh không? | Có: 167/173 đáp số đúng; 164/173 đúng số và đơn vị theo bộ chấm. |
| Nó có tốt hơn Qwen3-1.7B gốc trong gói không? | Tốt hơn về đáp số kèm đơn vị, định dạng và một số tiêu chí hướng dẫn; vẫn có hồi quy ở nhóm bài lớp 3–4. |
| Nó có tốt hơn model đang dùng trong dự án không? | Chưa chứng minh được. Lần thử mới chỉ so được 3 câu chung do giới hạn/lỗi dịch vụ. |
| Có thể thay ngay bằng cách đổi tên model trong cấu hình không? | Chưa: định dạng đầu ra, cách phục vụ LoRA và yêu cầu bài học hiện tại khác nhau. |
| Nên làm gì với bản Drive? | Giữ làm ứng viên nghiên cứu; chưa đưa vào luồng học sinh chính thức. |

Việc giữ cấu hình hiện tại là **quyết định vận hành**, không phải tuyên bố rằng
model hiện tại đã được chứng minh đứng đầu về độ chính xác.

## 1. Đang so sánh những model nào?

| Model | Vai trò | Trạng thái được kiểm tra |
|---|---|---|
| **TeacherMath v3 — Qwen3-1.7B + LoRA, bật thinking** | Ứng viên giải toán trên Drive | Kiểm tra lại adapter và đầu ra đánh giá được cung cấp. |
| **`qwen/qwen3.8-27b`** qua Groq | Model chính được cấu hình cho phần gia sư | Gọi trực tiếp API trên bộ câu hỏi chung trong lần đánh giá này. |
| **`gemini-3.6-flash`** | Model dự phòng được cấu hình cho phần gia sư | Gọi trực tiếp API; gặp HTTP 503 trước khi trả câu đầu tiên. |
| Qwen3-1.7B gốc, bật thinking | Mốc đối chứng trong gói Drive | Chấm lại đầu ra đã lưu để đo tác động của LoRA. |

**Model hiện tại cũng đã bật suy luận khi lập và kiểm duyệt bài học.** Mã gọi
Qwen dùng `reasoning_effort="low"`; Gemini dùng mức thinking thấp. Vì thế,
chữ “thinking” không tự làm cho bản Drive trở thành bản nâng cấp của dự án.

Cấu hình huấn luyện của gói Drive ghi `enable_thinking_training=false`.
Đánh giá thinking là bật chế độ suy luận khi sinh đầu ra; không phải một đợt
huấn luyện mới bằng toàn bộ nội dung suy nghĩ ẩn.

Gói này thuộc phần **giải toán từ văn bản**. Nó chưa có bằng chứng thay thế được
CRNN đọc chữ viết tay, YOLO phát hiện vùng bài hoặc quy trình xử lý ảnh.

**Giới hạn trạng thái chạy:** lúc kiểm tra, Docker chưa kết nối được và dịch vụ
local ở cổng 8000/8080 không nhận kết nối. Các tên trên được xác nhận từ cấu hình
và mã nguồn; phép thử mới gọi trực tiếp API của nhà cung cấp. Đây không phải
chứng nhận toàn bộ website đang hoạt động hoặc kết quả trên điện thoại thật.

## 2. Cách kiểm tra và độ tin cậy của dữ liệu

Đợt này đã thực hiện các bước sau:

1. Đọc lại cấu hình model, luồng lập bài học, bộ tính chính xác và kiểm duyệt
   trước khi xuất bản bài học trong dự án.
2. Kiểm tra lại **19 hash trong manifest gói Drive**, hash adapter, và **3 file
   quyết định đánh giá ngữ nghĩa** nằm trong gói đánh giá nén. Các hash đều khớp.
3. Chấm lại **5 bộ × 262 đầu ra đã lưu** bằng bộ chấm đã được kiểm tra trước đó.
   Không chạy trainer hay bộ giải theo mẫu tải từ Drive.
4. Giữ nguyên bộ 20 câu đã chọn trước đây: mỗi nhóm lớp 1–5 gồm 2 bài giải,
   1 yêu cầu gợi ý và 1 trường hợp cần hỏi lại/từ chối. Đầu vào cho model chỉ có
   lớp, đề và chế độ; không có đáp án chuẩn.
5. Gọi lại từng nhà cung cấp bằng một key cố định của nhà cung cấp đó; dừng ngay
   khi có lỗi. Tổng cộng **5 yêu cầu HTTP**, không retry hay đổi key vượt quota.
6. So sánh bản Drive trên **đúng các ID câu hỏi** mà model hiện tại đã trả lời.
   Đọc trực tiếp đầu ra dành cho học sinh để phân biệt lỗi thật và giới hạn bộ chấm.

### Các giới hạn cần giữ khi đọc số liệu

- Bộ 262 câu là dữ liệu văn bản tự soạn bằng mẫu: **173 bài giải, 59 yêu cầu
  gợi ý, 30 trường hợp hỏi lại/từ chối**. Chưa phải tập bài trường học được giáo
  viên độc lập xác nhận. Nhãn lớp là phân loại kỹ thuật, chưa chứng nhận đầy đủ
  độ phù hợp chương trình chính thức.
- Đầu ra TeacherMath được sinh trong đợt trước trên Tesla T4 và nay được chấm
  lại. **Chưa chạy lại mạng Qwen3-1.7B + LoRA trên máy này.** Môi trường hiện
  không có CUDA, Transformers/PEFT và bộ weights nền trong runtime được kiểm tra.
- Bài thử API dùng yêu cầu JSON chung của gói và giới hạn 2.048 token, nhiệt độ
  0,6. Đây là phép thử khả năng model với cùng đầu bài; chưa phải phép thử đầy
  đủ bằng prompt và quy trình bài học nhiều bước của ứng dụng.
- Bộ chấm chặt còn yêu cầu khớp đường giải tham chiếu và quy ước đơn vị. Cách
  giải tương đương hoặc cách ghi đơn vị hợp lý có thể bị trừ điểm. Vì vậy cần
  đọc lời giải thật, không chỉ nhìn một tỷ lệ tổng.
- Đánh giá ngữ nghĩa đi kèm do AI thực hiện; chưa có xác nhận giáo viên.
- Không cộng các lượt 13/10 và 16/10 thành mẫu độc lập vì có câu hỏi trùng nhau.

## 3. Bản thinking cải thiện gì so với các bản trong gói?

Các dòng dưới dùng cùng bộ 173 bài giải, 59 gợi ý và 30 trường hợp cần hỏi lại.

| Tiêu chí | Qwen3-1.7B gốc, thinking | TeacherMath LoRA, không thinking | **TeacherMath LoRA, thinking** |
|---|---:|---:|---:|
| Đúng đáp số | 165/173 — 95,4% | 113/173 — 65,3% | **167/173 — 96,5%** |
| Đúng số + đơn vị theo bộ chấm trực tiếp | 101/173 — 58,4% | 113/173 — 65,3% | **164/173 — 94,8%** |
| Qua kiểm tra đường giải/định dạng chặt | 1/173 | 96/173 | **134/173** |
| Gợi ý qua kiểm tra cấu trúc/an toàn bằng máy | 0/59 | 59/59 | **25/59** |
| Hỏi lại/từ chối đúng theo bộ chấm | 3/30 | 30/30 | **27/30** |

Diễn giải:

- Thinking giúp adapter giải đúng nhiều bài hơn so với chính adapter khi tắt
  thinking. Đây là điểm mạnh có số liệu rõ ràng.
- So với bản nền đã bật thinking, số đáp số đúng chỉ tăng **2 bài**. Phần tăng
  lớn nhất nằm ở đơn vị và khả năng tuân thủ định dạng yêu cầu.
- Bản không thinking có gợi ý đúng cấu trúc hơn, nhưng đáp số bài giải thấp hơn.
  Không có một chế độ thắng toàn bộ các tiêu chí.
- **94,8% đúng số và đơn vị không đồng nghĩa 94,8% bài học đủ tốt cho trẻ.**

### Hồi quy theo nhóm lớp

| Nhóm lớp trong bộ dữ liệu | Qwen3-1.7B gốc thinking: đúng số | TeacherMath thinking: đúng số |
|---|---:|---:|
| 1 | 15/15 | 15/15 |
| 2 | 15/15 | 15/15 |
| 3 | 38/38 | **36/38** |
| 4 | 35/36 | **32/36** |
| 5 | 62/69 | **69/69** |

Bản mới tăng mạnh ở nhóm lớp 5 nhưng giảm ở lớp 3–4. Tổng điểm cao hơn không
loại bỏ được các hồi quy này.

## 4. Chất lượng hướng dẫn học sinh

Theo hồ sơ đánh giá ngữ nghĩa bằng AI đi kèm:

| Tiêu chí của TeacherMath thinking | Kết quả | Ý nghĩa |
|---|---:|---|
| Bài giải có lỗi nghiêm trọng | **19/173 — 11,0%** | Có thể đúng đáp số nhưng sai khái niệm, quan hệ hoặc dòng phép tính. |
| Gợi ý làm lộ đáp án | **30/59 — 50,8%** | Không đáp ứng mục tiêu để học sinh tự làm khi mới xin gợi ý. |
| Bài giải được đánh giá phù hợp vai trò | 137/173 — 79,2% | Số liệu đánh giá AI, chưa có giáo viên xác nhận. |
| Gợi ý được đánh giá phù hợp vai trò | **15/59 — 25,4%** | Còn yếu ở chức năng gia sư từng bước. |
| Hướng dẫn từng bước được đánh giá hữu ích | 145/173 | Có tiến bộ so với 129/173 của bản nền, nhưng chưa bảo đảm mọi lời giải đúng. |

Đợt này đã đếm lại trực tiếp được **19 lỗi nghiêm trọng và 30 gợi ý lộ đáp án**
từ các file quyết định có hash khớp. Các nhận xét đó vẫn là đánh giá của AI;
việc khớp hash xác nhận nguồn bằng chứng, không biến chúng thành chứng nhận sư phạm.

### Những lỗi đã đọc lại trên đầu ra thật của bản Drive

| Đề bài | Đầu ra quan sát được | Vấn đề |
|---|---|---|
| Đóng nhiều hộp nhất từ 401 cái bánh, mỗi hộp 7 cái; hỏi số bánh dư. | Đáp số `2`, nhưng bước tính ghi expression `401/7`, result `2`. | Số dư đúng, phép chia được trình bày sai. Cần phân biệt thương và số dư, chẳng hạn `401 − 57 × 7 = 2`. |
| Ngoài 30 phút nghỉ còn 12 giờ hoạt động; hỏi cả hai khoảng là bao nhiêu phút. | Đổi được 720 phút rồi trừ 30, trả `690`. | Hiểu sai quan hệ cộng hai khoảng thời gian. Đúng phải là `12 × 60 + 30 = 750` phút. |
| Giá trị của chữ số hàng chục trong số 11. | Đáp số `10`, nhưng giải thích có “một nhóm gồm hai đơn vị chục”. | Đáp số đúng nhưng lời giảng sai cấu tạo số, có thể khiến trẻ hiểu nhầm hàng chục. |

Đây là lý do chính chưa nên dùng điểm đáp số để quyết định thay model gia sư.

## 5. So sánh mới với model hiện tại, ngày 16/10

### Tình trạng phép thử trực tiếp

| Model | Câu trả về / dự kiến | Kết quả trên bài giải đã trả | Lý do dừng |
|---|---:|---|---|
| Qwen3.8-27B đang được cấu hình | **3/20** | 2/2 đáp số đúng; 2/2 đúng đơn vị theo bộ chấm trực tiếp | HTTP **429** ở yêu cầu thứ tư |
| Gemini 3.6 Flash dự phòng | **0/20** | Chưa có câu trả lời để chấm | HTTP **503** ở yêu cầu đầu |

429 là lỗi giới hạn dịch vụ; 503 là lỗi dịch vụ không sẵn sàng. Chúng không
được tính thành bài toán giải sai. Riêng mã 429 chưa xác định được giới hạn
đang áp dụng là theo phút, ngày hay loại quota khác.

### Đúng ba câu chung giữa Qwen hiện tại và bản Drive

| Tiêu chí | TeacherMath thinking: đầu ra đã lưu | Qwen3.8-27B: đầu ra mới |
|---|---:|---:|
| Cùng câu hỏi so được | 3 | 3 |
| Đáp số đúng trên hai bài giải | 2/2 | 2/2 |
| Đúng số + đơn vị theo quy ước bộ chấm | 1/2 | 2/2 |
| Qua kiểm tra đường giải chặt | 1/2 | 1/2 |
| Gợi ý qua kiểm tra máy | 0/1 | 0/1 |

Các chi tiết làm thay đổi cách hiểu bảng:

- Với bài hỏi giá trị hàng chục của 51, bản Drive trả `50`, đơn vị “đơn vị”;
  tham chiếu để trống đơn vị nên bị bộ chấm trừ điểm. Cách ghi “50 đơn vị”
  có thể hiểu được về mặt toán học; không dùng chênh lệch này để kết luận Qwen
  hiện tại giải toán giỏi hơn.
- Qwen hiện tại cũng có lỗi đáng chú ý: một bước ghi expression `51`, result
  `5`, rồi mới tính `5 × 10 = 50`. Đáp số cuối đúng nhưng bước đầu không phải
  một đẳng thức tính toán đúng theo cấu trúc yêu cầu.
- Với yêu cầu gợi ý về hàng chục của 11, bản Drive điền sẵn answer `10` và unit
  “chục”, nên làm lộ đáp án. Qwen hiện tại không điền đáp án, nhưng hỏi hai câu
  trong khi bộ chấm yêu cầu đúng một dấu hỏi. Hai kết quả `0/1` do những nguyên
  nhân khác nhau, không thể diễn giải thành hai gợi ý có chất lượng như nhau.

**Ba câu đều thuộc nhóm lớp 1. Không đủ cơ sở xếp hạng toàn bộ hai model.**
Gemini không có đầu ra mới nên cũng không thể xếp trên hoặc dưới bản Drive.

## 6. Vì sao chưa thể thay trực tiếp trong dự án?

### Chất lượng sản phẩm cần rộng hơn đáp số

Yêu cầu của MathVisionKid là trẻ hiểu vì sao dùng phép tính, biết bắt đầu từ đâu,
nhận gợi ý sâu khi cần và ghi được bài giải trên lớp. Dữ liệu huấn luyện trong
gói yêu cầu explanation ngắn và một câu gợi ý; chưa chứng minh được khả năng
đáp ứng trọn bộ yêu cầu hướng dẫn dài, có phân tầng của ứng dụng hiện tại.

Hồ sơ gói ghi rõ:

- `production_approved=false`;
- `standalone_student_tutor_approved=false`;
- trạng thái `FULL_THINKING_EVALUATED_RESEARCH_ONLY_UNSUITABLE_FOR_STUDENT_TUTOR`;
- bước chọn model trong gói vẫn chọn bản nền, với adapter không qua kiểm tra
  không hồi quy theo lớp.

### Giao tiếp và kiểm tra đầu ra khác nhau

TeacherMath trả JSON gồm `status`, `steps`, `answer`, `unit`, `hint`.
Luồng hiện tại cần kế hoạch tương tác với `canSolve`, `finalAnswerStep`, câu
lời giải, câu hỏi, công thức có tham chiếu bước trước, `initialGuidance`, phần
hỗ trợ sâu và các gợi ý riêng. Đổi tên model trong biến môi trường không tự
chuyển đổi được hai định dạng này.

Ví dụ khác biệt phép tính: dữ liệu TeacherMath cho phép `%` để lấy số dư;
bộ tính chính xác hiện tại chỉ chấp nhận cộng, trừ, nhân và chia. Muốn dùng
đầu ra mới phải xử lý tương thích một cách có kiểm tra, không mở rộng tùy tiện
bộ thực thi công thức do model sinh.

Ứng dụng hiện có kiểm tra dữ kiện, tính toán chính xác, kiểm duyệt ý nghĩa và
chỉ mở phần hỗ trợ có kết quả ở thời điểm phù hợp. Các lớp này cần được giữ khi
đánh giá ứng viên mới. Chúng giảm rủi ro, không bảo đảm model luôn đúng hoặc
dịch vụ luôn sẵn sàng.

**231 kiểm thử mã nguồn gia sư đã chạy lại và qua** trong lần kiểm tra này.
Đây là kiểm thử logic ứng dụng, không phải 231 bài giải AI được chấm đúng.

### Chưa xác minh được việc phục vụ model mới

Adapter được kiểm tra có dung lượng **69.782.384 byte**, không phải toàn bộ
weights Qwen3-1.7B. Để chạy cần bản nền đúng revision, thư viện tương thích và
dịch vụ suy luận. Chưa đo tốc độ, RAM, độ trễ khi nhiều học sinh dùng hoặc
khả năng hoạt động liên tục của bản này trên máy chủ dự kiến.

Vì vậy chưa có cơ sở khẳng định chuyển sang bản Drive sẽ nhanh hơn, rẻ hơn
hoặc làm website hoạt động khi máy cá nhân tắt. Những lợi ích đó cần đo và
triển khai riêng.

## 7. Điều kiện để xem xét thay model

1. Hoàn thành bộ so sánh chung, có đủ bài nhiều bước, phân số, đơn vị, bài làm
   sai và câu thiếu dữ kiện ở các nhóm lớp. Báo cáo riêng lỗi dịch vụ và lỗi toán.
2. Có tập bài mới ngoài các mẫu đã dùng để phát triển; giáo viên kiểm tra phần
   diễn giải, câu lời giải và mức gợi ý. Không dùng lại tập đã xem nhiều lần
   như bằng chứng độ chính xác độc lập.
3. Sửa các lỗi nghiêm trọng đã nêu và kiểm tra hồi quy theo từng nhóm lớp.
   Bộ kiểm tra chặn phát hành phải không còn các lỗi nghiêm trọng đã biết hoặc
   gợi ý đầu làm lộ đáp án. Điều này không phải cam kết không thể sai trên bài mới.
4. Chứng minh đầu ra mới đáp ứng đúng giao tiếp bài học hiện tại, qua các lớp
   kiểm tra toán/dữ kiện và không làm lộ đáp án trong giao diện ban đầu.
5. Đo thực tế tốc độ, tài nguyên, lỗi và độ ổn định; thử song song trước khi
   chuyển luồng học sinh, có khả năng quay về cấu hình cũ.

**Khuyến nghị cuối:** tiếp tục dùng cấu hình hiện tại sau khi dịch vụ hoạt động
ổn định; giữ TeacherMath thinking ở nhánh thử nghiệm. Bản Drive có giá trị để
cải thiện tiếp, nhưng bằng chứng hiện tại chưa đủ cho quyết định thay chính thức.

## 8. Nguồn và khả năng kiểm tra lại

- [Gói TeacherMath v3 do chủ dự án cung cấp](https://drive.google.com/drive/folders/1cBCKxNB3CdOr6wL06xpNEYOxbLc4YiVi).
- [Bảng so sánh ngày 13/10](E:/MathVisionKid/report/MODEL_LEADERBOARD_20261013.md).
- [Luồng lập và kiểm tra bài học hiện tại](E:/MathVisionKid/ai/runtime/app/tutoring/lesson.py:692).
- [Cách gọi model và cấu hình reasoning](E:/MathVisionKid/ai/runtime/app/tutoring/service.py:201).
- Bằng chứng riêng của đợt này: `ai-training/datasets/drive_math/thinking_review_20261016/`:
  `teacher_audit.json`, `teacher_live_policy.json`, `teacher_live_results.json`,
  `review_evidence.json`, cùng các script tái kiểm tra.
- SHA-256 adapter:
  `20e99388093c5f7caa1aacaac2a6014cdc0bfd4b4b1bb6f25b5a593ea8beae8d`.
- Revision bản nền:
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`.

Đợt này không huấn luyện, thay model, đổi cấu hình, khởi động hệ thống, triển
khai, commit hoặc push. Không lưu ảnh gốc hay trích xuất ZIP ra thư mục; các
file quyết định được đọc trong RAM. Không công bố nội dung suy nghĩ ẩn của model.

## Skills Applied

- `using-superpowers`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/using-superpowers/SKILL.md`
  - Why selected: xác định hướng dẫn áp dụng trước khi đánh giá.
  - Applied to: lựa chọn quy trình và kỹ năng phù hợp với việc kiểm chứng model.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tận dụng bộ chấm đã kiểm tra và giao thức câu hỏi chung hiện có.
  - Applied to: script tái chấm, gọi API có giới hạn và tổng hợp bằng chứng.
- `verification-before-completion`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/verification-before-completion/SKILL.md`
  - Why selected: mọi kết luận cần số liệu và lệnh kiểm chứng mới.
  - Applied to: kiểm tra hash, chấm lại kết quả, thử API và kiểm thử mã nguồn.
