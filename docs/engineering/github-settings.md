# GitHub settings và kiểm chứng

Repo: `NV-DuyManh/MathVisionKid`; nhánh mặc định `main`. Thiết lập server phải được đọc lại qua API, không coi file trong Git là đã bật bảo vệ.

## Chính sách đích

1. **Owner merge:** một ruleset riêng hạn chế update `main`; chỉ tài khoản owner đã xác minh `NV-DuyManh` có bypass ở chế độ **pull_request**, không bypass push trực tiếp.
2. **PR và lịch sử:** ruleset không bypass yêu cầu PR, một approval khác tác giả, bỏ approval cũ khi có commit mới, giải quyết discussion, chặn force-push/xóa main.
3. **Required check:** `Quality gate` của GitHub Actions (app ID 15368), branch up-to-date. Chỉ đăng ký tên sau khi check thực tế xuất hiện và chạy đạt; không dùng workflow Catalog có paths filter làm required check chung.
4. **Dọn nhánh:** `delete_branch_on_merge=true`; không bật auto-merge. PR head `Manh` cũng có thể bị GitHub xóa sau merge; bản local và lịch sử vẫn còn.
5. **Reviewers:** CODEOWNERS dùng maintainer đã xác minh. Không bắt owner-review riêng cho mọi PR vì owner không thể tự approve PR của chính mình; vẫn cần một teammate khác tác giả. Không tạo danh tính/bot approval giả.

## CI và bot

`.github/workflows/ci.yml` chạy trên PR vào main, push main và workflow_dispatch. Governance xác minh registry, tên PR mới, action SHA và đường dẫn private/artifact mới; sau đó chọn các module bị ảnh hưởng. Config/workspace chung chạy tất cả; docs/report-only chỉ chạy governance. Merge vào main chạy lại đầy đủ. Check tổng hợp thất bại nếu module bắt buộc lỗi, bị hủy hoặc bị skip bất ngờ.

**MathVision Review Bot** là tên phần tóm tắt phạm vi/checks trong GitHub Actions Job Summary, không phải AI review ngữ nghĩa. Không cần API key, không gửi code/hình học sinh sang nhà cung cấp thứ ba, không tự comment/approve/merge. Bộ `mathvision-review` hỗ trợ người review; không thay teammate approval. Catalog Bot vẫn làm kiểm tra catalog độc lập.

CI PR không dùng secrets/production DB, không chạy `pull_request_target`, action được pin commit SHA và checkout không giữ credential. Dependency bot chỉ đề xuất PR hàng tuần, giới hạn số lượng; Expo/React không gom cập nhật tự động và ML cần campaign riêng.

## Kiểm tra và rollback

Đọc `gh api repos/NV-DuyManh/MathVisionKid/rulesets` và từng ID; `branches/main.protected` phải true. Đối chiếu `delete_branch_on_merge` và check-run thực tế. Bản cấu hình trước khi đổi được lưu ngoài checkout; báo cáo phase ghi trạng thái thật, ID và giới hạn. Thay đổi server không tự xuất hiện trong git diff.

Nếu một check hỏng, sửa workflow/test và chạy lại PR. Không vô hiệu hóa bảo vệ để ép merge. Khôi phục cấu hình cũ cần owner cho phép và bản snapshot chính xác; không dùng token admin để tự approve/bypass.

Nguồn: [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets), [secure Actions](https://docs.github.com/en/actions/reference/security/secure-use).
