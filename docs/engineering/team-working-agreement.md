# Cách làm việc của nhóm

Áp dụng [Git Flow](git-flow.md) cho mọi task: `develop` là nhánh tích hợp; `main` lưu các bản sẵn sàng phát hành. Task mới tách `feature/*` hoặc `bugfix/*` từ develop mới nhất, mở PR về develop. Chốt phiên bản qua `release/*`; vá production qua `hotfix/*`. Cả hai phải vào main và đồng bộ lại develop. Không phát triển trực tiếp trên nhánh chung. Follow-up tiếp tục trên PR đang mở, không dùng lại nhánh task đã merge.

Một task có owner, nguồn yêu cầu, tiêu chí nghiệm thu và reviewer. Khi chưa rõ một quy tắc sản phẩm, tách phần phụ thuộc và tiếp tục việc độc lập. Không bịa link issue, quyết định hoặc account reviewer. Không bắt buộc Jira/Trello nếu issue/PR đã đủ thông tin.

Definition of Ready: đủ scope, kết quả quan sát được, phụ thuộc và điều kiện lỗi/quyền liên quan. Definition of Done: hành vi đúng, checks phù hợp đạt, có bằng chứng/giới hạn, owner đã xem xét, tài liệu/hợp đồng cần thiết cập nhật. CI xanh không tự thay nghiệm thu.

Reviewer ưu tiên correctness, dữ liệu, quyền, hồi quy trước style. Bot kiểm tra chính sách/phạm vi/CI; AI review ghi revision và kết quả trong PR. Mọi người cần ít nhất một người khác Approve; riêng owner đã xác minh `NV-DuyManh` được miễn approval qua ruleset riêng ở chế độ pull_request. CI, PR và chặn force-push vẫn bắt buộc với owner. Không tự resolve discussion của người khác. Agent chỉ merge khi owner đã cho phép. Giữ nguyên tác giả commit; cherry-pick chọn lọc dùng `-x`, adaptation ghi nguồn xác minh được. Xem [CONTRIBUTING](../../CONTRIBUTING.md).

Không force-push nhánh chung, không đổi lịch sử main, không xóa nhánh PR còn mở. Tắt xóa head tự động để giữ release/hotfix tới khi backmerge xong; local dọn bằng `branch -d` sau xác minh, không `-D` hàng loạt. PR #51 có ngoại lệ chuyển tiếp giới hạn ở develop và có hạn trong `.github/git-flow.json`; task mới không được dùng ngoại lệ. Trạng thái GitHub server và tài liệu phải được báo riêng.
