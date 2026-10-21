# Nhận xét gói Primary Math Teacher và so sánh các model MathVisionKid

Ngày kiểm tra: **17/10/2026**. Nguồn: [thư mục Drive chủ dự án gửi](https://drive.google.com/drive/folders/19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n).

## Kết luận

**Gói mới có thiết kế dữ liệu hướng dẫn học sinh đáng phát triển, nhưng chưa
phải model đã huấn luyện. Chưa có căn cứ kết luận nó giải tốt hơn TeacherMath
v3 Thinking hoặc các model đang cấu hình trong dự án, và chưa thể dùng để thay
model hiện tại.**

Đã kiểm tra cả ba tệp công khai trong thư mục. `data_build_state.json` và
manifest cùng ghi `training_started=false`; ZIP không có checkpoint hay
adapter dưới dạng `.safetensors`, `.pth`, `.bin`, `.gguf`, `.onnx` hoặc `.pt`.
Giai đoạn được khai báo là `DATA_AUTHORING_AND_REVIEW`, chưa phê duyệt production.
Kết luận này áp dụng cho gói được cung cấp, không khẳng định bên ngoài thư mục
không có một lần huấn luyện khác.

## 1. Gói mới thực sự có gì?

| Nội dung kiểm tra | Kết quả |
|---|---:|
| Bài gốc có ID riêng | 286 |
| Lượt hội thoại huấn luyện | 1.144 |
| Biến thể mỗi bài | Một lời giải và ba mức gợi ý |
| Nhóm chuẩn hóa theo `case_group_id` | 274 |
| Bài cốt lõi / bài xử lý hiểu sai / bài hỏi lại / bài bổ sung | 180 / 57 / 40 / 9 |
| Hội thoại thuộc TRAIN | 1.144/1.144 |
| Biểu thức số được tính lại bằng bộ tính chính xác hiện tại | 374/374 khớp kết quả ghi sẵn |
| Mục trong manifest được kiểm tra hash | 242/242 |
| Batch đầu vào được kiểm tra hash | 44/44 |

**1.144 lượt không phải 1.144 bài độc lập.** Bốn lượt cùng một bài vẫn giữ
chung nhóm; một số bài khác nhau cũng có chung nhóm chuẩn hóa. Khi chia dữ
liệu về sau phải giữ cả nhóm trong cùng một tập để tránh lộ bài giữa TRAIN và
kiểm định. Gói chat này chưa cung cấp một tập kiểm định độc lập cho model mới.

374 phép tính đúng chỉ xác nhận sự nhất quán giữa biểu thức và kết quả số.
Phép thử không chứng minh mọi bài đều hiểu đúng đề, đúng đơn vị, gợi ý an toàn
hoặc đủ dễ hiểu với học sinh. Không chạy trainer hay mã Python tải từ Drive.

## 2. Điểm tốt của hướng dữ liệu mới

Các bài tách riêng dữ kiện, đại lượng cần tìm, hướng dẫn đầu, lý do chọn phép
tính, từng bước giải, đáp số và ba mức gợi ý. Thiết kế này phù hợp yêu cầu
chủ dự án đã nêu: giải thích vì sao làm, làm theo thứ tự nào và giúp trẻ tự
bắt đầu, thay vì chỉ trả đáp án cuối.

Ví dụ đã đọc trực tiếp trong dữ liệu lớp 4: tổng hai ngăn có 156 quyển sách,
ngăn trên hơn ngăn dưới 28 quyển. Dữ liệu hướng dẫn bỏ phần hơn để còn hai
phần bằng nhau, tính `156 − 28 = 128`, chia `128 : 2 = 64` để tìm ngăn dưới,
rồi cộng lại phần hơn để có 92 quyển ở ngăn trên. Nó giải thích ý nghĩa của
mỗi phép tính và kiểm lại tổng, hiệu. Ba mức gợi ý được tách khỏi bài giải đầy đủ.

Bài lớp 5 về thêm rồi bán dầu còn hướng dẫn đặt dấu phẩy thẳng cột, viết
`2,8 = 2,80` và giải thích vì sao cộng trước, trừ sau. Đây là ví dụ nội dung
đích tốt hơn việc chỉ ghi công thức. Tuy nhiên, **nội dung đích viết tốt không
chứng minh model sau huấn luyện sẽ tự sinh được lời giảng tốt trên bài mới**.

Đã parse toàn bộ 858 hội thoại gợi ý: không thấy điền phần `answer` hoặc
`steps` có nội dung. Chưa có đánh giá ngữ nghĩa đầy đủ để khẳng định cả 858
gợi ý không làm lộ đáp án qua câu chữ.

## 3. Những phần chưa ổn

### Độ phủ lệch nhiều về lớp 1–3

| Lớp | Bài gốc |
|---|---:|
| 1 | 70 |
| 2 | 105 |
| 3 | 98 |
| 4 | 5 |
| 5 | 8 |

Lớp 4–5 chỉ có **13/286 bài, khoảng 4,5%**. Chưa đủ đại diện cho phân số,
tỉ số, phần trăm, chuyển động và bài nhiều bước ở hai lớp này. Theo kế hoạch
nội bộ, mới điền 180/495 vị trí bài cốt lõi, còn 315; hoàn tất định mức ở
56/165 chủ đề đăng ký. Đây là tiến độ soạn dữ liệu theo định mức, không phải
tỷ lệ bao phủ toàn bộ chương trình hay tỷ lệ model làm đúng.

### Nội dung vẫn còn việc cần chỉnh

`pre_sft_polish_queue.json` liệt kê **47 bài** cần chỉnh hoặc kiểm tra trước
huấn luyện. Hồ sơ nêu các vấn đề như thiếu khoảng trắng, lặp bước và một số
gợi ý nhắc chữ số nên chưa phù hợp trực tiếp với quy tắc `/guide`. Đây là hàng
chờ do gói cung cấp, không phải kết quả kiểm duyệt độc lập toàn bộ nội dung
trong lần nhận xét này.

Các tệp khai báo `human_verified=false`, `teacher_certified=false`. Những bài
về đồng hồ, hình, đo đạc hoặc thao tác chủ yếu mô tả bằng chữ; không chứng minh
model đọc được ảnh đồng hồ, bản vẽ hay bài viết tay thật.

### Chưa khớp giao tiếp ứng dụng hiện tại

Chat dùng schema trung gian `neutral_teacher_chat.v1_not_live_PlanDraft`.
Thử đưa trực tiếp 286 đầu ra lời giải vào `PlanDraft` hiện tại: **0/286 hợp
lệ**. Đây là khác biệt định dạng được thiết kế sẵn, không phải 286 bài toán
giải sai. Cần bước chuyển đổi và kiểm tra trước khi tích hợp.

Sáu bài có hơn sáu bước, trong khi bản kế hoạch của ứng dụng giới hạn sáu
bước. Ví dụ bài chia thập phân có tám bước cần được tổ chức lại khi ánh xạ,
giữ phần giảng chi tiết nhưng tránh bỏ mất phép tính hoặc quan hệ phụ thuộc.

Đặc biệt, `tutor_contract.json` trong gói không mô tả đúng checkout hiện tại:
cả năm hash nguồn đều khác. Tệp ghi không có trường `initialGuidance`, trong
khi `DraftStep` hiện tại có trường này. Phải đồng bộ lại hợp đồng theo mã
nguồn đang dùng; không triển khai dựa trên khẳng định cũ trong gói.

## 4. So sánh với những model trước

Các số liệu dưới được đọc lại từ bằng chứng đánh giá **ngày 16/10/2026**,
không phải lượt chạy suy luận mới ngày 17/10. Cùng 173 bài giải văn bản trong
gói cũ, sắp theo số đáp số đúng:

| Model/chế độ trong gói cũ | Đúng đáp số | Đúng số và đơn vị theo bộ chấm |
|---|---:|---:|
| TeacherMath v3 LoRA, Thinking | 167/173 — 96,5% | 164/173 — 94,8% |
| Qwen3-1.7B nền, Thinking | 165/173 — 95,4% | 101/173 — 58,4% |
| Qwen3-1.7B nền, không Thinking | 138/173 — 79,8% | 91/173 — 52,6% |
| TeacherMath v3 LoRA, không Thinking | 113/173 — 65,3% | 113/173 — 65,3% |
| Qwen3-0.6B nền, không Thinking | 76/173 — 43,9% | 52/173 — 30,1% |
| Primary Math Teacher trong link mới | Chưa có model/đầu ra đánh giá để chấm | Chưa đo |

Thứ tự này chỉ phản ánh tiêu chí đáp số trên bộ phát triển cũ. Nó không phải
bảng xếp hạng gia sư cho trẻ. Chẳng hạn, bản v3 không Thinking có số và đơn
vị tốt hơn bản nền Thinking nhưng đáp số thấp hơn. Bộ bài được soạn tổng hợp,
đã dùng nhiều lần; chưa có xác nhận độc lập của giáo viên.

Bản v3 Thinking vẫn có **19/173 bài bị đánh giá AI là lỗi nghiêm trọng** và
**30/59 gợi ý bị đánh giá AI là lộ đáp án** trong hồ sơ trước. Đáp số cao không
đủ để thay model gia sư. Gói mới đang sửa hướng soạn dữ liệu, chưa có kết quả
chứng minh đã khắc phục các lỗi đó sau huấn luyện.

## 5. So với các model đang cấu hình trong dự án

Đã đọc cấu hình hiệu lực hiện tại, chỉ lấy tên model và trạng thái bật/tắt,
không xuất key:

| Thành phần | Trạng thái/bằng chứng | Kết luận so với gói mới |
|---|---|---|
| `qwen/qwen3.8-27b` qua Groq | Model chính cấu hình cho gia sư; phép thử 16/10 trả ba câu, sau đó HTTP 429. Hai bài giải trả về đúng đáp số. | Chưa đủ câu chung để xếp hạng; gói mới còn chưa có checkpoint. |
| `qwen/qwen3.6-27b` | Model dự phòng Groq trong cấu hình. | Không có kết quả đối chứng chung trong lượt này. |
| `gemini-3.6-flash` | Model Gemini trong cấu hình; lượt 16/10 gặp HTTP 503 trước khi có đầu ra. | Chưa có kết quả để xếp trên/dưới. |
| CRNN OCR và các ứng viên OCR đã train | Đọc chữ/số từ ảnh, khác nhiệm vụ giải toán văn bản. | Gói chat mới không thay thế được OCR; không đặt chung bảng điểm. |

Tên cấu hình không chứng nhận dịch vụ đang hoạt động hoặc model đã được
kiểm tra chất lượng rộng. Không tính 429/503 thành bài toán giải sai, và không
xếp Qwen/Gemini trên hay dưới v3 từ vài câu không đủ độ phủ.

## 6. Khuyến nghị

**Nên tiếp tục phát triển bộ dữ liệu mới; chưa nên thay model bằng gói này.**
Ưu tiên hoàn thiện lớp 4–5, xử lý 47 mục chỉnh sửa, đồng bộ hợp đồng ứng dụng
và rà lời giảng bằng giáo viên. Sau đó mới huấn luyện một ứng viên có version
trọng số rõ ràng, so cùng bộ bài mới với bản v3 Thinking và model hiện tại.
Chấm riêng đáp số, từng phép tính, hiểu đề, đơn vị, giải thích, gợi ý lộ đáp án,
tốc độ và tài nguyên. Giữ cả bốn biến thể cùng nhóm trong một tập dữ liệu.

Nếu chỉ đánh giá **hướng thiết kế tài liệu huấn luyện**, gói mới đáng đầu tư
hơn cho mục tiêu hướng dẫn chi tiết của dự án. Nếu hỏi **model nào giải tốt
nhất và có thể thay ngay**, bằng chứng hiện có chưa cho phép kết luận như vậy.

## Nguồn và kiểm chứng

- Gói mới: [Primary Math Teacher trên Drive](https://drive.google.com/drive/folders/19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n).
- [Báo cáo model Thinking ngày 16/10](E:/MathVisionKid/report/SO_SANH_MODEL_THINKING_VOI_MODEL_HIEN_TAI_20261016.md).
- [Khai báo kế hoạch/bước học hiện tại](E:/MathVisionKid/ai/runtime/app/tutoring/lesson.py:44).
- [Cấu hình model của dự án](E:/MathVisionKid/ai/runtime/app/config.py:56).
- Bằng chứng riêng: `ai-training/datasets/drive_math/primary_teacher_review_20261017/package_audit.json`,
  `comparison_evidence.json`, cùng script `inspect_package.py`.
- SHA-256 ZIP: `1ae63343c5f1b3c138a91a96b1ceac1fbbd3aeff32ff57994da0da5ffc390a3a`.
- SHA-256 chat: `52aa592b71e7a3908fca388a83d90ff2ce67334484ff2eabaa5b8467b2fa9bff`.

Chỉ đọc nội dung gói trong RAM, lưu kết quả kiểm tra và vài ví dụ văn bản.
Không giải nén ZIP ra đĩa, không lưu ảnh, không huấn luyện hoặc gọi API model,
không thay cấu hình/model, không deploy, commit hay push trong lượt này.

## Skills Applied

- `using-superpowers`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/using-superpowers/SKILL.md`
  - Why selected: xác định kỹ năng và giới hạn công việc trước khi đánh giá.
  - Applied to: chọn quy trình đọc và kiểm chứng model.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng bộ tính chính xác và schema của ứng dụng, dùng thư viện sẵn có.
  - Applied to: script kiểm tra gói, hash, thống kê và phép tính; không chạy mã tải từ Drive.
- `verification-before-completion`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/verification-before-completion/SKILL.md`
  - Why selected: chỉ kết luận từ kết quả được kiểm tra.
  - Applied to: kiểm tra 242 hash, 44 batch, số bài, phép tính, hợp đồng và bằng chứng so sánh cũ.
