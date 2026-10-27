# Rà soát và lấy chọn lọc nhánh Nam — 26/10/2026

> Cập nhật sau yêu cầu tiếp theo của chủ dự án: đã kiểm tra live và tích hợp chọn lọc provider cùng hai giọng vào narration hiện tại. Xem [báo cáo tích hợp giọng](NAM_VOICE_INTEGRATION_20261026.md). Nội dung dưới đây giữ kết quả của lượt lọc ban đầu, khi provider chưa được nhập.

**Kết luận: không merge nguyên nhánh `Nam`.** Đã lấy và chỉnh các hunk phát âm toán/đơn vị cần thiết vào mã hiện tại, đồng thời chuyển cùng cải tiến vào bộ tổng hợp âm thanh Python thực tế đang dùng. Giữ trình phát có thanh tua, luồng xác thực phiên học và các chỉnh giao diện đang có. Chưa commit, push, sửa lịch sử hoặc xóa nhánh từ xa.

## Mốc kiểm tra

- Nhánh được kiểm tra: **`origin/Nam`**, không phải `origin/Namm`.
- Candidate: `ec6d633f5491d398fc7f743e9c88f28060094f5d`.
- Main hiện tại: `71ad997ad55301dd6a869baed34c0d13fbd8246e`; merge base: `10582a6facede82394794b975a4501a98303903c`.
- Candidate có 6 commit riêng; commit `705faab` mang tên `fix tts` chứa 4.600 file. Tổng diff candidate kể từ merge base là **4.614 file, 592.769.394 byte nội dung blob** (~593 MB thập phân, không phải kích thước clone nén).
- `git merge-tree --write-tree` chạy trên hai commit, không sửa checkout: **5 xung đột nội dung**. Không bắt đầu merge thật.
- [Tóm tắt kiểm chứng và hash file bảo toàn](nam-selective-review-20261026/summary.json). Inventory/selection theo từng đường dẫn và patch nhỏ được giữ cục bộ tại `runtime/nam-review-20261026/`.

## Phát hiện cần chặn trước khi merge

| Mức | Vị trí ở candidate | Vấn đề và quyết định |
|---|---|---|
| P1 | `ai/runtime/app/tutoring/speech.py:16`, `backend/business-api/.../MathTutorController.java:64` | Route `/speech` mới chỉ nhận text/voice/rate, không nhận owner/session/revision và không đối chiếu lời giảng đã được công bố trong phiên. Backend vẫn có bảo vệ vai trò Student, **không phải API công khai cho người chưa đăng nhập**; nhưng một tài khoản Student có thể gửi văn bản tùy ý để tổng hợp, khác với hàng rào nội dung/phiên của `/lesson/narration` hiện tại. Không nhập route/provider này. |
| P1 | `apps/student-mobile/src/features/tutoring/LessonNarration.tsx:112,119,133` | Trình phát candidate chỉ báo số đoạn đã nghe và có nút dừng/phát lại, không có thanh seek theo thời gian. Nhánh `compact` chỉ còn nút nghe giải thích. Nếu chọn implementation này để giải quyết conflict sẽ làm mất yêu cầu tua trực tiếp và trình phát đã sửa. Giữ `AudioPlayback`/`MediaTimeline` hiện có. |
| P2 | `apps/student-mobile/src/app/learning/math-guide.tsx:222,231` | Prefetch lời mở đầu viết cứng trước phản hồi bài học rồi chờ thêm tối đa khoảng 4 giây cho audio. Có fallback nếu provider chậm, nhưng phát sinh công việc đoán trước và trạng thái chuẩn bị mới cho một khả năng hiện không cần nhập. Không lấy cache/prefetch/stage UI này. |
| P2 | `ai-training/thinking/cloud_publication/owner_resume_20261023/install_status_report_cache_failed_syntax.py:4` | Static parse phát hiện `SyntaxError` trong script chụp trạng thái cũ. Đây là artifact được đặt tên là failed, **không phải bằng chứng worker train chính bị lỗi cú pháp**. Tuy nhiên nó cho thấy commit chứa cả đầu ra tạm/lần thất bại, cần tách khỏi mã ứng dụng. |
| P2 | `ai-training/thinking/cloud_publication/recovery_20261026/gate_closure_v2_receipt.json:12` | Receipt được lưu trong nhánh báo `decision=STOP`, `candidate_eligible=false`; snapshot trạng thái báo `QUALITY_GATE_STOP`. Đây là thông tin lịch sử do nhánh lưu, chưa đối chiếu lại Colab/Drive trực tiếp. Không dùng nó làm bằng chứng model đã đạt yêu cầu triển khai. |

Các file conflict: `ai/runtime/app/api/tutor.py`, `apps/student-mobile/src/__tests__/lessonNarration.test.tsx`, `apps/student-mobile/src/features/tutoring/LessonNarration.tsx`, `backend/business-api/src/main/java/com/mathvisionkids/api/tutoring/MathTutorService.java`, `backend/business-api/src/test/java/com/mathvisionkids/api/tutoring/MathTutorServiceTest.java`.

## Phần lấy và phần loại khỏi tích hợp

| Nhóm | Quyết định |
|---|---|
| Hunk `spokenMath` và các ca phát âm trong `narration.test.ts` | **Lấy chọn lọc, có chỉnh:** đọc số âm sau toán tử, đơn vị độ dài/khối lượng/dung tích, giữ ngoặc nhóm toán học. Không lấy hàm chia audio `narrationSegments` hoặc phụ thuộc mới. |
| Cải tiến tương ứng cho `ai/runtime/app/tutoring/video_render.py` | **Áp dụng vào đường phát thực tế:** cả lời giảng WAV và video hiện gọi `spoken_math` Python này. Chỉ sửa helper TypeScript sẽ không đủ để cải thiện audio đang dùng. |
| Giọng online Nam Minh/Hoài My, `microsoftSpeech`, `speechCache`, `speechPreferences`, file audio và endpoint mới | **Chưa lấy.** Ý tưởng giọng dễ nghe có ích, giới hạn request/cache cũng có chủ đích; nhưng triển khai cần đi qua owner/session/revision và trình phát có tua hiện tại. Không thêm hai tầng phát/cache song song hoặc dịch vụ mạng tự động trong lần lọc này. |
| `RecognitionProgress` và trạng thái chuẩn bị mới | **Không lấy.** Nó phục vụ prefetch audio mới; màn chuẩn bị hiện tại đã độc lập và báo hoạt động chưa có tỷ lệ hoàn tất. Tránh thêm danh sách bước/logic chỉ để phục vụ stack đã loại. |
| `ai-training/**` (4.538 file) | **Không nhập vào main.** Có ý tưởng nghiên cứu đáng giữ như hash/model revision cố định, baseline cache bất biến, đối chiếu gate trước/sau. Nhưng phần này là tập dữ liệu, code thí nghiệm, notebook và snapshot theo run; không phải một gói runtime ổn định hoặc bằng chứng đủ để thay OCR/model toán. Bằng chứng vẫn còn ở nhánh nguồn. |
| `.agent/skills-dox/**`, thay đổi `AGENTS.md` | **Không lấy.** Skill trùng với thư mục canonical; quy tắc báo cáo/context mới của candidate không cần thiết cho việc tích hợp này. |
| `HAND_AI_*`, `assets/presentation/**`, `expo_qr_code.png`, report pilot | **Không lấy vào app.** Tài liệu/ảnh trình bày và mã QR cục bộ không phải thành phần tính năng cần thiết. Không xóa lịch sử nghiên cứu hoặc file cá nhân. |
| `package-lock.json` | **Không lấy.** Không có thay đổi version package giữa base và candidate; phần lớn thay đổi metadata `peer` và bốn entry bị bỏ, không cần cho phần đã chọn. Python dependency/lock mới cũng không được nhập. |

Trong diff 4.614 đường dẫn, chỉ **2 đường dẫn lấy hunk chọn lọc**, **4.612 đường dẫn còn lại loại khỏi phần nhập**; thêm 2 file Python hiện có được sửa/test để tích hợp vào luồng đang chạy. Đây là lọc phần tích hợp, không phải xóa nhánh Nam hoặc xóa dữ liệu nghiên cứu trên Drive.

## Rà độ dư thừa

- Quét object của toàn bộ 4.614 file thay đổi, không checkout hoặc chạy các script của candidate.
- **283 nhóm blob trùng byte**, tương ứng **383 bản sao ngoài bản đầu, 27.885.555 byte**. Bản chụp bằng chứng có thể cố ý trùng để lưu lịch sử; không tự xóa chúng, chỉ không nhập hàng loạt vào main.
- 4.458 file nằm trong `ai-training/thinking`, riêng `cloud_publication` có 3.185 file. Một nguồn JSONL gần 95,8 MB; một số snapshot notebook hơn 10 MB.
- Static parse **1.059 file Python**: 1 file lỗi cú pháp cũ như đã nêu. Không khẳng định đã chạy hay xác nhận tính đúng của toàn bộ code train.
- Quét 4.155 object văn bản với các mẫu key có độ tin cậy cao không thấy khớp; đây không phải chứng nhận không có mọi loại bí mật hoặc quyền chia sẻ dữ liệu.
- Các lớp phát/prefetch/session/cache mới bị loại nguyên nhóm, không mang module chỉ có một đường gọi hoặc file lock mới vào cho một helper đọc toán.

## Xác minh phần đã chọn

- Trước khi sửa: tái hiện **9 ca lỗi phát âm trong Python**, 10 assertion mới/được cập nhật không đạt trong suite TypeScript. Sau sửa, các ca và suite liên quan đều qua.
- Python runtime: **79/79 test qua**, gồm lời giảng private, phiên cũ/chủ sở hữu sai, video, hội thoại, hướng dẫn và YOLO adapter.
- Student: **102/102 test, 7 suite qua**, gồm phát âm, lời giảng, narration API, timeline, phát lại ghi âm, màn học và video. Lượt chạy đồng thời đầu tiên timeout ở một bài tutor-screen rồi kéo theo một assertion khác; chạy lại cả 7 suite không tăng timeout và không sửa các bài đó thì qua.
- TypeScript qua; ESLint helper TypeScript qua; whitespace diff qua.
- Hash **6 file giao diện đang sửa từ trước** (gồm khung đề mới) giữ nguyên so với đầu lượt. Không thay backend auth, dependency/lock, provider âm thanh, model weights hay dữ liệu train.
- Không train, gọi Colab/Drive, tổng hợp giọng qua mạng, commit hoặc push trong lượt review này. Không kiểm tra trực tiếp thiết bị Android và không tuyên bố chất lượng giọng mới qua nghe thực tế.

## Đánh giá cuối

**Chỉ nên đưa patch nhỏ đã lọc vào main sau bước commit theo yêu cầu chủ dự án. Không merge toàn bộ `Nam` tại commit đang rà.** Nếu tiếp tục nhánh nghiên cứu, nên tách gói train riêng với entrypoint/test/dependency rõ ràng, giữ dữ liệu/snapshot ngoài source runtime, rồi kiểm chứng quality gate độc lập. Nếu muốn lấy giọng online, tích hợp provider vào endpoint narration có xác thực hiện tại và giữ file audio hoàn chỉnh để tua; không thay UI phát lại bằng trình phát theo đoạn của candidate.

## Skills Applied

- `ponytail-review`
  - SKILL.md: `.agents/skills/ponytail-review/SKILL.md`
  - Why selected: chủ dự án yêu cầu lọc phần dư thừa trong nhánh.
  - Applied to: nhận diện stack phát/cache trùng, snapshot/lần chạy tạm, dependency churn; không dùng skill này thay cho rà tính đúng/bảo mật.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tích hợp tối thiểu vào luồng hiện có.
  - Applied to: helper phát âm và test hồi quy; không nhập module/provider/phụ thuộc không cần thiết.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: rà thay đổi React Native và các lifecycle/cache của trình phát.
  - Applied to: đánh giá stack phát mới, prefetch, tác động đến UI/lifecycle, bảo toàn player và phạm vi source hiện tại.
