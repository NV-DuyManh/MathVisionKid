# Bài được giao · Kế hoạch triển khai

**Trạng thái** · Bản kế hoạch dự thảo theo [đặc tả Teacher–Student Integration](../specs/2026-11-13-teacher-student-integration-design.md), chỉ thực hiện sau duyệt.

**Mục tiêu** · Một lớp đã có giao được một bài, học sinh nộp ảnh, giáo viên trả điểm và hai bên thấy cùng kết quả theo quyền.

**Kiến trúc** · Spring xác thực quyền, lưu người nhận và kết quả trên PostgreSQL, giữ ảnh trong kho đối tượng riêng. Teacher React và Student Expo Web dùng hợp đồng API mới. Review ảnh và TeacherDecision tái sử dụng từ luồng hiện có.

| Việc | Mã nguồn phụ trách | Điểm kiểm chứng |
| --- | --- | --- |
| 1. Phát hành bài | Module `assignment`, `classroom`, Flyway | Viết test hai lần phát hành đồng thời và roster đổi lúc phát hành. Bổ sung publication, snapshot người nhận và API Student. Xác minh đúng số người nhận, truy vấn có giới hạn và học sinh ngoài lớp không thấy bài. |
| 2. Nhận bài nộp | Module `submission`, kho ảnh, adapter camera/privacy/crop của Student | Viết test timeout, replay cùng hoặc khác payload, restart sau ghi object, rời lớp giữa upload. Triển khai bản ghi nhận ảnh bền vững và kiểm tra quyền trước lưu và khi xác nhận nhận bài. Chạy lại test tự luyện và batch. |
| 3. Chấm và trả điểm | Review Workspace, module `submission`, `TeacherDecision` | Viết test sai đề, điểm 0, ngoài thang, gọi endpoint legacy, chốt đồng thời và đổi giáo viên. Thực hiện một giao dịch chấm và trả, tách lý do nội bộ khỏi phản hồi Student, giữ số điểm và snapshot thang điểm. |
| 4. Nghiệm thu người dùng | Teacher Web, Student Web và Playwright | Thêm Bài được giao, chi tiết nộp/kết quả và bảng tiến độ từng bài. Chạy kịch bản ở đặc tả trên hai viewport với Spring và PostgreSQL cách ly. Đối chiếu UI, DTO và dữ liệu lưu. |

- [ ] Xác nhận chính sách với owner và chọn revision đã merge từ `origin/develop`.
- [ ] Viết các ca thất bại trước từng việc, chạy lại ca mục tiêu và hồi quy liên quan sau từng thay đổi.
- [ ] Chạy `npm run check:governance`, build Teacher, typecheck Student, Playwright web/Student, test Gradle và ca nâng cấp PostgreSQL có dữ liệu. Ghi revision, kết quả và giới hạn bằng chứng.
- [ ] Kiểm tra bằng MCP qua tài khoản phát triển, chụp bằng chứng với dữ liệu tổng hợp. Điều kiện bàn giao gồm UI có dữ liệu thật từ backend local, điểm đồng nhất hai bên và các ca truy cập chéo bị từ chối.
- [ ] Rà PR nhỏ theo Git Flow, ghi migration cộng thêm, cách tắt đường vào nếu rollback và trạng thái kiểm soát ảnh trước pilot.
