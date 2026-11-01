# Kế hoạch cải thiện và thay OCR chữ/toán — 24/10/2026

Mục tiêu là có ứng viên đủ bằng chứng để thay model đang dùng, không phải đạt100% trên dữ liệu đã train. Tình trạng đầu vào: best numeric VAL59/65 nhưng bốn trang vở chỉ65/86; lỗi `22→21` và mất số0 còn tồn tại. Các lượt trước chưa được phát hành.

## Thứ tự thực hiện

| Giai đoạn | Việc làm cụ thể | Bằng chứng cần có |
|---|---|---|
|1. Chốt đối chứng|Pin hash code, ảnh nguồn, nhãn, checkpoint và split hiện có; lưu toàn bộ kết quả cũ|Không ghi đè thử nghiệm hoặc thay nhãn sau khi xem dự đoán|
|2. Thống nhất ảnh vào|Train và suy luận đều giữ tỷ lệ, min-width32 cho số hẹp; tái trích đặc trưng từ ảnh thật khi kích thước thay đổi|CTC đủ timestep, không feed padding vào GroupNorm/BiLSTM; so sánh checkpoint cũ với cùng input|
|3. Train có kiểm soát|Thử giữ KL trên mọi TRAIN cũ, so với KL trên vùng cũ đã đúng; không chọn checkpoint theo bốn trang chẩn đoán|Chọn bằng VAL đã khai báo; mỗi thay đổi có đối chứng, loss/gradient hữu hạn|
|4. Bổ sung chữ/vở|Ưu tiên dòng chữ tiếng Việt và số0/số lặp/dấu trên trang chưa dùng; xem ảnh và crop trước khi train|Nhãn literal, nguồn/hash, split theo trang; chưa rõ thì cách ly; không suy nhãn bằng phép tính|
|5. Phân số|Giữ tọa độ tử/gạch/mẫu, đo cả mất cặp và đọc sai; cần trang có nhãn đầy đủ để đo false positive|Không gọi điểm crop là độ chính xác cả trang; không chọn cặp bằng đáp án|
|6. Kiểm chứng|Nạp checkpoint trong tiến trình mới; kiểm tra chữ, số, dấu, zero, phân số và vùng bản cũ đã đúng|So decoder/preprocessing công bằng; báo cả hồi quy và coverage/abstention|
|7. Phát hành|Chốt ứng viên trước, mở bộ đánh giá độc lập cuối cùng, kiểm tra route app và fallback/rollback|Không thay nếu bất kỳ điều kiện bắt buộc nào chưa đạt|

## Điều kiện thay model

- Crop số đúng toàn bộ≥95%, CER≤2%, không làm sai thêm vùng số/dấu quan trọng mà parent đọc đúng.
- Chữ tiếng Việt phải được đo riêng; không đánh đổi giảm chất lượng chữ để tăng điểm số.
- Tử/mẫu/gạch và liên kết phân số được đo trên ảnh trang, có nhãn toàn bộ để kiểm false positive.
- Bộ chấp nhận cuối cần tách theo người viết/nguồn và có nhãn được xác nhận độc lập. Không gọi old DEV, VAL đã dùng nhiều lần hay bốn trang đã xem là test mù.
- Head13 lớp không thể thay trực tiếp OCR chữ/full-page. Luồng Student hiện dùng dịch vụ đọc vở Gemini; checkpoint nghiên cứu không tự làm app thay model.

## Quy tắc vòng lặp

Khi sai: phân loại lỗi dữ liệu/crop/ảnh vào/model/layout, sửa nguyên nhân bằng TRAIN mới hoặc cấu hình đã đóng băng, chạy lại đối chứng và kiểm hồi quy. Không thêm các trang chẩn đoán vào train rồi báo điểm đó như test độc lập; không mở TEST lặp lại để chọn epoch. Nếu tăng epoch không cải thiện thì đổi giả thuyết hoặc bổ sung dữ liệu, không kéo dài cùng một run để làm đẹp con số.

Vòng triển khai tiếp theo dùng thư mục `ai-training/datasets/drive_math/math_release_campaign_20261024/`. Lịch sử `math_robust_numeric_20261024/` được giữ bất biến. Dữ liệu ảnh tiếp tục ở nguồn/Drive hoặc RAM; chỉ lưu đặc trưng, nhãn, weights và log. Không commit/push trong yêu cầu này.

Không có bằng chứng để bảo đảm một model đúng mọi ảnh. Mỗi báo cáo phải ghi rõ phần đã đạt và điều kiện còn thiếu; không tự gọi một ứng viên chưa đạt là “hoàn hảo”.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Kế hoạch và công cụ Python huấn luyện/kiểm chứng OCR; không có skill OCR chuyên biệt trong registry.
  - Applied to: Tái sử dụng model, loader RAM-only, CTC/decoder/metrics và hash đã có; không thêm framework, không thay runtime khi chưa qua kiểm chứng.
