"""Prompt tiếng Việt cho 4 subagent. Đề toán GSM8K-level, đáp án SỐ để verify bằng code."""

# Luân phiên bối cảnh để chống mode-collapse (đề bị dồn về 1 chủ đề như quán phở).
CONTEXTS = [
    "nông nghiệp (ruộng lúa, thu hoạch, gia súc)",
    "giao thông (xe máy, quãng đường, xăng dầu)",
    "trường học (học sinh, lớp, điểm số, sách vở)",
    "mua sắm siêu thị (giảm giá, khuyến mãi)",
    "thể thao (bóng đá, chạy bộ, số liệu)",
    "nhà máy sản xuất (sản phẩm, công nhân, năng suất)",
    "tiền lương và tiết kiệm (lương, chi tiêu, ngân hàng)",
    "thời gian và lịch trình (giờ làm, ngày)",
    "đo lường (mét vải, lít nước, ki-lô-gam)",
    "du lịch (vé, khách sạn, nhóm khách)",
    "xây dựng (gạch, xi măng, công thợ)",
    "vườn cây ăn quả (cây, trái, thu hoạch)",
    "bể nước (chứa, chảy vào/ra)",
    "tuổi tác trong gia đình",
    "điện nước sinh hoạt (số điện, hóa đơn)",
    "may mặc (vải, áo, công may)",
    "chăn nuôi (gà, vịt, trứng, cám)",
    "thư viện và đọc sách (trang, ngày, số sách)",
    "công nghệ (điện thoại, pin, dung lượng)",
    "quyên góp từ thiện (phần quà, số người)",
]

CHALLENGER_PROMPT = """Bạn là người RA ĐỀ toán tiếng Việt cho học sinh.
Dựa trên bài mẫu (seed) dưới đây, hãy SÁNG TẠO MỘT BÀI TOÁN MỚI bằng tiếng Việt:
- Đặt bài toán trong bối cảnh: **{context}**. TUYỆT ĐỐI tránh chủ đề ăn uống/quán phở trừ khi bối cảnh nêu rõ là ẩm thực.
- Tăng độ khó: bài toán cần 3–4 BƯỚC tính toán (nhiều bước hơn bài mẫu), kết hợp 2–3 phép tính khác nhau.
- ĐỀ PHẢI RÕ RÀNG, ĐƠN NGHĨA: nêu đủ MỌI dữ kiện cần thiết, chỉ có MỘT cách hiểu và dẫn tới ĐÚNG MỘT đáp án số. KHÔNG dùng câu chữ mơ hồ, KHÔNG trộn nhiều tình huống rời rạc, KHÔNG bắt người đọc tự suy đoán dữ kiện còn thiếu.
- Đáp án BẮT BUỘC là MỘT SỐ, tính được chính xác từ dữ kiện. Không để lộ đáp án trong đề.

BẮT BUỘC: trước khi chốt, hãy TỰ GIẢI bài toán từng bước (ghi vào "solution") để bảo đảm đề đủ dữ kiện và "final_answer" KHỚP với lời giải. Nếu thấy đề mơ hồ hoặc thiếu dữ kiện, hãy SỬA lại đề cho rõ rồi mới trả về.

Bài mẫu:
- Đề: {seed_q}
- Đáp án: {seed_a}

Trả về DUY NHẤT một JSON (không kèm giải thích):
{{"question": "<đề toán tiếng Việt, rõ ràng đơn nghĩa>", "solution": "<lời giải từng bước>", "final_answer": "<đáp án dạng số>", "topic": "<chủ đề ngắn>"}}"""

STRONG_SOLVER_PROMPT = """Giải bài toán sau bằng tiếng Việt, trình bày TỪNG BƯỚC rõ ràng.
Kết thúc bằng ĐÚNG một dòng cuối: "ĐÁP ÁN CUỐI: <số>"

Bài toán: {question}"""

# Weak solver: cố tình YẾU — ép nhẩm nhanh, không trình bày -> dễ sai trên đề nhiều bước.
WEAK_SOLVER_PROMPT = """Trả lời NHANH bài toán sau bằng cách nhẩm trong đầu.
KHÔNG trình bày các bước, KHÔNG dùng giấy nháp — ghi ngay con số bạn nghĩ ra.
Kết thúc bằng đúng một dòng: "ĐÁP ÁN CUỐI: <số>"

Bài toán: {question}"""

VERIFIER_PROMPT = """Bạn là giám khảo toán. Kiểm tra lời giải dưới đây có HỢP LỆ không:
các bước logic liền mạch, không nhảy cóc, và dẫn tới đáp án đã cho.

Đề: {question}
Lời giải: {cot}
Đáp án: {answer}

Trả về DUY NHẤT một JSON: {{"valid": true/false, "reason": "<ngắn gọn>"}}"""
