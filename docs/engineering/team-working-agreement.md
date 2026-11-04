# Cách làm việc của nhóm

`main` là nhánh tích hợp luôn cần build được. Nhánh task tách từ main mới nhất, đi qua PR; follow-up cùng task tiếp tục trên PR đó. Không ép đổi tên nhánh thành viên đang dùng. Task mới sau merge tách nhánh mới, không tiếp tục đẩy vào nhánh đã merge.

Một task có owner, nguồn yêu cầu, tiêu chí nghiệm thu và reviewer. Khi chưa rõ một quy tắc sản phẩm, tách phần phụ thuộc và tiếp tục việc độc lập. Không bịa link issue, quyết định hoặc account reviewer. Không bắt buộc Jira/Trello nếu issue/PR đã đủ thông tin.

Definition of Ready: đủ scope, kết quả quan sát được, phụ thuộc và điều kiện lỗi/quyền liên quan. Definition of Done: hành vi đúng, checks phù hợp đạt, có bằng chứng/giới hạn, đã review chéo, tài liệu/hợp đồng cần thiết cập nhật. CI xanh không tự thay nghiệm thu.

Reviewer ưu tiên correctness, dữ liệu, quyền, hồi quy trước style. Tối thiểu một approval khác tác giả. Maintainer xác nhận merge sau required checks; không tự merge hoặc tự approve bằng bot. Giữ nguyên tác giả commit; cherry-pick chọn lọc dùng `-x`, adaptation ghi nguồn xác minh được. Xem [CONTRIBUTING](../../CONTRIBUTING.md).

Không force-push nhánh chung, không đổi lịch sử main, không xóa nhánh PR còn mở. GitHub auto-delete chỉ dọn head remote sau merge; local dọn bằng `branch -d` sau xác minh, không `-D` hàng loạt. Trạng thái GitHub server và tài liệu phải được báo riêng.
