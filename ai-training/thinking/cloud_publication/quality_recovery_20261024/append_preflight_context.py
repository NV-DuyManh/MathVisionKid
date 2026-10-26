from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
base=Path(__file__).resolve().parents[3]
p=base/'MATH_TRAINING_CONTEXT.md'
marker='### Nhật ký 24/10/2026 — quality recovery trên Chrome Duy Mạnh 6'
raw=p.read_bytes()
assert marker.encode() not in raw,'Do not duplicate context entry'
text='''

### Nhật ký 24/10/2026 — quality recovery trên Chrome Duy Mạnh 6
MCP đã kết nối đúng notebook1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l bằng Chrome Duy Manh6, tài khoản giao diện duymanh2k5proo@gmail.com. Nhãn server browser chrome-namnam-default là nhãn hardcoded cũ, không dùng làm bằng chứng tài khoản. Runtime mới TeslaT4 miễn phí; Drive đã xác thực và kiểm folder19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n. Môi trường riêng đã cài Torch2.11.0+cu130/Unsloth2026.10.7/Transformers5.16.1/PEFT0.21.2/Bitsandbytes0.50.2, chưa train trong bước cài. Ngân sách wallclock gồm setup/train/review/eval/export:2026-10-24T09:45:58Z–12:45:58Z, train cutoff12:15:58Z; không paid resources.
Chủ yêu cầu so sánh đề xuất QLoRA rồi chạy lại. Nhánh corrective5h trước REGRESSION_DO_NOT_PROMOTE cùng toàn bộ corpus/checkpoint/history giữ nguyên. Đợt mới bắt đầu từ Qwen/Qwen3-1.7B revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e; NF4 doublequant/FP16, r16alpha16, micro2/effective16, LR1e-5 warmup10; gradientcheckpointingOFF theo benchmark trước, no packing/paddingfree/FA2. Đây là cấu hình thận trọng để thử, không có bằng chứng tối ưu toàn cục. enable_thinking=False đúng target hội thoại gia sư hiện có; không chèn thought/thinking giả.
Nguồn 16kchat/4000case SHA14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331 được khôi phục cloud-only và xác minh; không tải corpus/model về PC. Source audit:16000mask/EOT và maxseq1329<2048 PASS;6373assistanttarget khác nhau,9627repeatrows.34actualrow đọc đủ nội dung qua semanticQA, chưa phát hiện sai toán trong mẫu này; limitedoracle unmatched không được tự coi sai. Derivedview giữ đủ4000worked_solution, cap identical hint target theo grade/topic/mode và xen grade; chỉ thay sampling, không xóa/đổi nhãn nguồn. Tối đa300updates và một pass của derivedview; chất lượng được so ở50/100/200/300/final, không lặp nhiều epoch để lấp thời gian. Base là ứng viên best; checkpoint giảm chất lượng không được tự promote. Step50 an toàn nhưng chưa tăng chỉ được chạy hết pilot100; sau100 phải có gain thực theo gate mới được tiếp tục.
Dev30 bài mới (SHA75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed) đã đọc đủ và kiểm Fraction/Decimal; lockedtest20 SHA41413ac3e61e7180cee53d06ccec6186256f1cfdf845557a6a598822f6ca22d0 giữ riêng tới sau model selection. Screening exact/number-masked sẽ chạy trên actual16k, không tuyên bố độc lập toàn6.5M hoặc toàn chương trình. Không truy cập concept_challenge_v4; không thêm human signoff/credential. Mọi quyết định semantic là đánh giá có evidence, không phải chứng nhận con người. Tại entry preflight này optimizer mới chưa chạy; chỉ được ghi training_started=true sau quan sát cập nhật thực. Skills applied: google-drive, computer-use.
'''
with p.open('ab') as f:f.write(text.encode('utf8'))
print(json.dumps({'context':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'previous_prefix_sha256':hashlib.sha256(raw).hexdigest()}))
