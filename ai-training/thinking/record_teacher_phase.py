"""Update the one existing context document, preserving all prior evidence."""
from pathlib import Path

path=Path(__file__).resolve().parent.parent/'MATH_TRAINING_CONTEXT.md'
text=path.read_text(encoding='utf-8')
start=text.index('**TRAINING_RUNNING:**')
end=text.index('\n\nChủ dự án đã yêu cầu',start)
text=text[:start]+'''**V3_TRAIN_COMPLETE_VALIDATION_REJECTED — đang đánh giá cuối.** Run `qwen3_17b_teacher_math_v3_epoch1_seed20261013` đã train đủ 4.170 mẫu / 1.043 optimizer steps, một epoch trên T4, 1.739 giây, peak allocation 6,006 GiB, 0 retry overflow. Fresh reload và validation đã thực chạy. Adapter sinh đáp số và đơn vị đúng 113/173; baseline 91/173 theo diagnostic đọc trực tiếp answer/unit. Tuy nhiên nếu chỉ xét số tính đúng, adapter 113/173 thấp hơn baseline 138/173, nhất là lớp 3–5. Theo gate đã đặt trước, selection chọn model nền; không dùng adapter này làm solver độc lập.

Strict rubric: adapter 96/173 lời giải có đáp số, đơn vị và đường tính khớp tham chiếu, 59/59 hint qua gate hình thức, 30/30 guard, 0 truncated. Đây không chứng nhận ý nghĩa của mọi câu giải thích/gợi ý. Baseline strict solution_verified=0 vì không theo đủ cấu trúc đường giải; không phải baseline không biết tính toán. Challenge đang chạy trên model nền; controller PID24611; posthoc PID27618 vẫn đợi controller/audit hoàn tất. Không khởi động GPU job khác khi hai tiến trình này còn hoạt động.

**V4_PREPARATION_ONLY:** Đã review 330 chat khái niệm (212 hiện hành / 118 lịch sử, 165 lời giải / 165 gợi ý), 188 phép tính tham chiếu và 30 câu validation mới, 32 phép tính. Numeric V3 không đổi. Tệp train khái niệm SHA `50b57a8d72e9c95b29fd435481604e7af20d84e24069fb40059d1777cc26f983`; val SHA `65826b8a18e78a7c6f823b712e88ed81850890f66906a1be00189c4b9d0726f2`. Không coi nội dung đã vào weights. Scorer tự động chỉ là screening: đã sửa parse ngoặc, ranh giới chữ số, role binding thương/dư; 30/30 reference pass. Các mâu thuẫn prose vẫn cần đọc output thực tế. Trainer V4 tách stage candidate → AI review hash-bound đủ baseline/candidate → selection → challenge; không dùng lexical screening để chứng nhận ngữ nghĩa. 34 local tests hiện đã pass; peer review integrity còn đang bổ sung.

Kế hoạch V4 đang review: fresh pinned Qwen3-1.7B, learning rate 2e-5 (thấp hơn V3 1e-4), một epoch, replay 4.170 mẫu số học và 330 mẫu khái niệm lặp 4 lần (5.490 training instances / 4.500 source examples riêng biệt). Đây là cấu hình dự kiến, chưa launch. Giữ numeric eval batch4/max512 giống V3 và bắt buộc raw numeric/unit overall/per-grade không giảm so với model nền được chọn. File ngữ cảnh này là báo cáo `.md` duy nhất.''' + text[end:]
text+='''

## Nhật ký 13/10/2026 — tiếp tục sau lượt số học V3

Đã đo đủ validation 262 câu sau fresh reload, giữ số LLM tự sinh riêng với bộ kiểm toán học. Chưa promote adapter V3 dù lời giải có cấu trúc tốt hơn. Challenge/auditor và 30 anchor + 8 thinking probe riêng còn chạy/đợi; kiểm `training_runner_state.json`, `posthoc_runner_state.json` và cell compact monitor `UReBBrRINja4` trước khởi chạy lại. Notebook đã thêm read-only diagnostic cell `qKWQyTmeVeyW` ở index69; snapshot Drive cần save/readback sau các cell mới.

Review khái niệm: `concept_v4_peer_review.json` giữ các reproduction của scorer cũ, không sửa thành pass giả. Local `teacher_multitask_v4.py` mới dùng review AI trực tiếp từng output, hash bound vào predictions/reference; review không phải human_verified hoặc teacher certification. Lượt V4 chỉ được chạy sau audit V3 thành công và GPU rảnh. Mọi tệp V3 freeze, checkpoint OCR và 8 OCR cell đầu giữ nguyên. Không commit/push, không gọi API trả phí, không deploy cho học sinh.
'''
path.write_text(text,encoding='utf-8',newline='\n')
print({'context_bytes':path.stat().st_size})
