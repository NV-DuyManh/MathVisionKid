# GitHub settings và kiểm chứng

Repo: `NV-DuyManh/MathVisionKid`; nhánh mặc định `main`. Thiết lập server phải được đọc lại qua API, không coi file trong Git là đã bật bảo vệ.

## Chính sách đích

1. **Owner merge:** một ruleset riêng hạn chế update `main`; chỉ tài khoản owner đã xác minh `NV-DuyManh` có bypass ở chế độ **pull_request**, không bypass push trực tiếp.
2. **PR và lịch sử:** ruleset không bypass yêu cầu PR, required Quality gate, giải quyết discussion, chặn force-push/xóa main. Số approval bắt buộc là 0 theo yêu cầu owner, giống CODEGYM; quyền merge cuối cùng chỉ thuộc owner qua ruleset riêng.
3. **Required check:** `Quality gate` của GitHub Actions (app ID 15368), branch up-to-date. Chỉ đăng ký tên sau khi check thực tế xuất hiện và chạy đạt; không dùng workflow Catalog có paths filter làm required check chung.
4. **Dọn nhánh:** `delete_branch_on_merge=true`; không bật auto-merge. PR head `Manh` cũng có thể bị GitHub xóa sau merge; bản local và lịch sử vẫn còn.
5. **Reviewers:** CODEOWNERS trỏ `@NV-DuyManh`. Thành viên/bot có thể góp ý nhưng approval của họ không cấp quyền merge. Owner xem và quyết định merge từng PR sau checks/discussions; với PR do owner tạo, quyết định merge của owner là bước duyệt cuối vì GitHub không cho tự approve PR. Agent không được suy diễn quyền merge từ việc checks xanh.

## CI và bot

`.github/workflows/ci.yml` chạy trên PR vào main, push main và workflow_dispatch. Governance xác minh registry, tên PR mới, action SHA và đường dẫn private/artifact mới; sau đó chọn các module bị ảnh hưởng. Config/workspace chung chạy tất cả; docs/report-only chỉ chạy governance. Merge vào main chạy lại đầy đủ. Check tổng hợp thất bại nếu module bắt buộc lỗi, bị hủy hoặc bị skip bất ngờ.

**MathVision Review Bot** là tên phần tóm tắt phạm vi/checks trong GitHub Actions Job Summary, không phải AI review ngữ nghĩa. Không cần API key, không gửi code/hình học sinh sang nhà cung cấp thứ ba, không tự comment/approve/merge. Bộ `mathvision-review` hỗ trợ review; không thay quyết định của owner. Catalog Bot vẫn làm kiểm tra catalog độc lập.

CI PR không dùng secrets/production DB, không chạy `pull_request_target`, action được pin commit SHA và checkout không giữ credential. Dependency bot chỉ đề xuất PR; không tự duyệt hoặc merge.

Dependency được kiểm hàng tuần, thứ Hai 08:00 giờ Việt Nam. PR phiên bản thường được gom theo nhóm, tối đa 5 PR mở (npm 2, Gradle/Python/Actions mỗi nhóm 1); chỉ đề xuất minor/patch. Expo/React và model có nhóm riêng, vẫn cần kiểm thử tương thích và owner duyệt. Major thường được nâng trong đợt riêng. Cooldown 7 ngày chỉ áp dụng cập nhật phiên bản, không trì hoãn bản vá bảo mật. Security có nhóm riêng và giới hạn riêng của GitHub; tổng PR không bị khóa cứng ở 5. Không ignore toàn bộ thư viện ML hoặc tắt cảnh báo để làm gọn số đếm.

Python dùng một updater `uv` cho `/ai/runtime` và `/scripts`, gồm requirements và uv.lock, tránh pip/uv cùng sửa một pin. Khi gom PR cũ vào PR thay thế, ghi rõ số PR/commit nguồn, giữ tác giả với `cherry-pick -x`, chỉ đóng nguồn sau khi phần thay thế được chấp nhận. PR nâng không tương thích được từ chối kèm lý do kiểm chứng. Không đóng bản vá chưa có giải pháp chỉ để giảm số PR.

Auto-delete chỉ dọn head của PR đã merge. Nhánh cũ chỉ xóa sau khi xác minh toàn bộ head đã nằm trên main và không còn PR mở dùng làm head/base; lưu ref trước xóa và dùng expected SHA để tránh xóa commit mới được đồng đội đẩy lên. Nhánh còn commit riêng phải được giữ. Không viết lại lịch sử đóng góp.

Nguồn cấu hình: [Dependabot options](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference). Alert trong manifest nghiên cứu/handoff cũ phải được phân loại riêng; không sửa số phiên bản của biên nhận lịch sử để giả vờ đã vá môi trường đó.

`Web checks` còn chạy Playwright Chromium trên production bundles với viewport desktop/mobile và API fixture offline. Lỗi luồng đăng nhập/SSO/đăng xuất/vai trò/form/filter làm Quality gate thất bại; report/trace/ảnh lỗi lưu artifact 7 ngày. Xem [phạm vi và cách chạy browser tests](browser-testing.md); không nhầm API fixture với bằng chứng backend RBAC hoặc test Android thật.

## Kiểm tra và rollback

Đọc `gh api repos/NV-DuyManh/MathVisionKid/rulesets` và từng ID; `branches/main.protected` phải true. Đối chiếu `delete_branch_on_merge` và check-run thực tế. Bản cấu hình trước khi đổi được lưu ngoài checkout; báo cáo phase ghi trạng thái thật, ID và giới hạn. Thay đổi server không tự xuất hiện trong git diff.

Nếu một check hỏng, sửa workflow/test và chạy lại PR. Không vô hiệu hóa bảo vệ để ép merge. Khôi phục cấu hình cũ cần owner cho phép và bản snapshot chính xác; không dùng token admin để tự approve/bypass.

Nguồn: [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), [secure Actions](https://docs.github.com/en/actions/reference/security/secure-use).
