# Nguồn quy trình và skill

Tham chiếu theo yêu cầu owner: `DTU-TEAM-2/smart-cafe-management`, các file governance ở revision `667b580f89d63c7caf176d26869a2b2dbb5e25c8`. `scripts/skills.mjs` điều chỉnh từ script registry bên đó. Các ý tưởng working agreement, naming, PR checklist, CI tách module và dọn nhánh được viết lại theo hợp đồng MathVisionKid.

Bốn skill `mathvision-workflow`, `mathvision-review`, `mathvision-quality`, `mathvision-backend` bao phủ các trách nhiệm workflow/requirements/release, correctness review, verification và API/database trong bộ `cafe-*`; không chép nghiệp vụ bàn, đơn hàng, hóa đơn hoặc mã task CF/QA. Không tạo bảy wrapper trùng tài liệu.

Giữ nguyên các skill UI/React/brand đang có, metadata và giấy phép gốc; một phần vốn là nguồn CODEGYM đã tham khảo ngược từ MathVisionKid. Không nhập lại duplicate hoặc gói prototype/slide không liên quan. Các bộ TDD/diagnosis bên ngoài không được sao chép toàn bộ chỉ vì nằm trong CODEGYM; kỹ năng test/diagnosis phù hợp đã ghi trong quy trình quality/review hiện tại.

Registry JSON là nguồn máy đọc, SKILLS_INSTALLED.md là mục lục. Không tự gán tác giả hoặc giấy phép cho nội dung bên thứ ba; attribution commit tuân CONTRIBUTING.md. Quy trình không cấp quyền deploy, training, gửi tin hay đổi quyền ngoài yêu cầu owner.
