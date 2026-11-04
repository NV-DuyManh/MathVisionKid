# Quy trình GitHub/CI và luật dự án — 04/11/2026

## Phạm vi

Triển khai ở nhánh `Manh`, nền `ac7aa8e`. Không đổi mã nghiệp vụ Student/web/backend/AI hoặc huấn luyện model. Dọn báo cáo/tệp được giao cho chat riêng; commit governance không gộp thay đổi cleanup.

## Đã triển khai

- Quy ước naming, workflow nhóm, API/database, chất lượng/bảo mật, bảo trì và bàn giao trong `docs/engineering/` và `docs/templates/`.
- `.editorconfig`, Node 22.19.0, CODEOWNERS, mẫu PR/issue, Dependabot có giới hạn; không đổi tên/reformat hàng loạt code cũ hoặc biên nhận nghiên cứu.
- Registry 23 skill và 20 route; bốn skill riêng MathVision bao phủ workflow/requirements/release, review correctness, quality và backend/database. Giữ skill hiện có, không nhập duplicate hay nghiệp vụ café.
- CI PR có quyền đọc, action SHA cố định, không giữ credential checkout, không dùng pull_request_target hoặc live TTS/model. Bot tổng hợp phạm vi/kết quả trong Job Summary; không giả làm AI semantic review và không auto-approve/merge/comment.
- Các nhóm Web, Student, Backend/migration PostgreSQL, AI offline, Windows launcher. `Quality gate` là check tổng hợp ổn định; lỗi/cancel hoặc skip bất ngờ không được tính là đạt.
- JSON chính sách ở `.github/rulesets/`: chỉ owner merge qua PR; một review khác tác giả, hủy approval cũ khi có push, resolve discussions, chống force-push/xóa main, required Quality gate gắn app GitHub Actions.

## Kiểm chứng local

| Kiểm tra | Kết quả |
| --- | --- |
| Governance policy/routing tests | 7/7 đạt; registry 23 skill, 20 route |
| Skill Creator quick_validate | 4/4 skill mới hợp lệ |
| actionlint 1.7.12 | Hai workflow hợp lệ; binary kiểm tra checksum theo release chính thức |
| Portal / Teacher / Admin config tests | 33/31/34 đạt |
| Production build + bundle tests ba web | Build đạt; 2/2/5 kiểm thử bundle đạt |
| Lint web | Không lỗi; Teacher còn một cảnh báo Fast Refresh đã có |
| Student | Typecheck và 15 contracts đạt; không đổi source Student |
| Backend Gradle | 487 ca được liệt kê, 0 lỗi; 1 MinIO opt-in skip; H2 profile test |
| SQL PostgreSQL 16 | 28 migration chạy trong container dùng một lần, không cổng/volume dự án; container đã dừng |
| Migration runner guards | 3/3 đạt; từ chối DB không phải test, ngoài CI hoặc DB không rỗng |
| AI môi trường Python 3.12 sạch | 123/123 toán/phát âm đạt; dependencies riêng, không torch/trọng số |
| Catalog | Store và bot checks đạt, không đọc DB học sinh thật |
| Windows launcher | Environment/identity regressions đạt; 6 batch launcher tests đạt |

AI lần đầu thiếu Celery do fixture chung import worker, sau đó thiếu plugin pytest-asyncio; đã bổ sung dependencies vào manifest CI và chạy lại môi trường sạch đạt 123/123. Không bỏ fixture hoặc assertion để làm xanh. Không bật/dừng SmartCafe hay chiếm cổng 8080.

Các build vẫn cảnh báo bundle lớn; task này không đổi bundling hoặc tuyên bố tối ưu runtime mới. Migration check kiểm SQL PostgreSQL fresh DB, không chứng minh Flyway history/checksum hoặc upgrade từ DB production. Không tạo bằng chứng thiết bị thật/latency live.

Log local: `C:\Users\Admin\.codex\tmp\web-audit-20261103\governance-*.log`. Snapshot cấu hình GitHub trước thay đổi: `C:\Users\Admin\.codex\tmp\mathvision-governance-20261104\`.

## GitHub — trạng thái rollout

Đã đọc lại qua API: auto-delete head sau merge bật; auto-merge vẫn tắt. Dependabot security updates, secret scanning và secret push protection đã bật. Các cấu hình này không nằm trong git diff.

CI và required status check cần chạy thật trên PR trước khi kích hoạt toàn bộ điều kiện merge. Trạng thái PR/check-run/ruleset cuối cùng được bổ sung sau khi GitHub thực thi, không suy diễn từ kết quả local. File CI/Dependabot trong nhánh chưa merge không đồng nghĩa đã áp dụng làm cấu hình mặc định của main.

Không self-approve hoặc bỏ điều kiện review để đưa bộ luật vào main. Người khác tác giả phải review PR; owner thực hiện merge sau khi checks đạt. Auto-delete không xóa lịch sử đóng góp, nhánh local hoặc nhánh còn PR mở.

## Nguồn và phần không lấy

Tham chiếu governance CODEGYM ở revision `667b580f89d63c7caf176d26869a2b2dbb5e25c8`; chi tiết trong `docs/engineering/skill-provenance.md`. Không nhập Maven/MySQL, mã CF/QA, luật hóa đơn/đơn hàng, skill trùng, prototype daemon, bot AI trả phí hoặc auto-merge. Giữ Catalog Bot hiện có.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Quy trình tập trung, không thêm framework/SDK hoặc wrapper trùng.
  - Applied to: Registry, bot Job Summary, CI dùng công cụ và kiểm thử sẵn có.
- `skill-creator`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/skill-creator/SKILL.md`
  - Why selected: Tạo skill dự án phù hợp và không mở rộng quyền ngoài yêu cầu.
  - Applied to: Bốn SKILL.md ngắn, mô tả chọn đúng phase, quick_validate.
- `mathvision-review`
  - SKILL.md: `.agents/skills/mathvision-review/SKILL.md`
  - Why selected: Review chính sách, an toàn dữ liệu và tính đúng của bằng chứng trước tích hợp.
  - Applied to: Quyền workflow, ruleset không bypass chất lượng, phân biệt local/CI và mock/live.
