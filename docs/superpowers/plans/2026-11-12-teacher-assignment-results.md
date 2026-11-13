# Teacher Assignment Results Implementation Plan

**Goal:** Giáo viên đối soát và xử lý kết quả của một bài tập theo học sinh.

**Architecture:** Spring cung cấp projection theo phạm vi bài tập và đợt được phép. Teacher Web dùng React Query và Review Workspace hiện tại.

**Tech Stack:** Spring Boot, PostgreSQL, React, MUI, React Router, Playwright.

**Spec:** [Kết quả theo bài tập](../specs/2026-11-12-teacher-assignment-results.md)

## Điều kiện chung

Chờ chủ dự án duyệt đặc tả và kế hoạch. Khi bắt đầu ghi nhận branch/HEAD và bảo vệ working tree. Áp dụng kiểm thử đỏ/xanh từng lát cắt. Chỉ dùng dữ liệu tổng hợp ở môi trường cách ly. Không commit, push, merge hoặc deploy khi chưa được phép.

## Slice 1 · Mở kết quả và đối soát học sinh

- [ ] Thêm test trong package `backend/business-api/src/test/java/com/mathvisionkids/api/assignment/` cho API kết quả. Fixture gồm học sinh hiện tại chưa có bài, học sinh chuyển đến, học sinh chuyển đi có bài, hai bài cùng học sinh, bài mâu thuẫn ID và đợt ngoài quyền. Assert tập dòng, bộ đếm và từ chối khi mất quyền.
- [ ] Thêm `AssignmentResultsController`, `AssignmentResultsService` và projection trong package `assignment`. `GET /api/v1/teacher/assignments/{assignmentId}/results?page=0&size=25&filter=ALL&q=` trả metadata, counts, rows, page. Mỗi row gồm studentId, displayName, currentMember và các số bài theo nhóm trạng thái. Kiểm tra đầu vào size tối đa 50. Dùng cùng điều kiện phạm vi cho mọi projection và một snapshot mỗi phản hồi.
- [ ] Thêm phương thức `getAssignmentResults` vào TeacherService và SpringTeacherService, kiểu response trong `apps/teacher-web/src/types/index.ts`. Thêm `AssignmentResultsPage.tsx`, route `assignments/:id/results` trong App.tsx, hành động “Xem kết quả” ở AssignmentsPage và đường vào qua “Bài tập của lớp” trong ClassDetailPage. Hiện rõ tìm, lọc, đếm, tải, lỗi, rỗng và mất quyền.
- [ ] Chạy Spring test theo lớp test mới và Playwright spec `tests/browser/teacher-assignment-results.spec.mjs` trên desktop/mobile. Ca đầu đi từ lớp tới kết quả, kiểm tra điều hướng, lọc chồng lấn và bố cục thẻ.

## Slice 2 · Mở từng bài và xử lý tiếp

- [ ] Thêm test cho `GET /api/v1/teacher/assignments/{assignmentId}/results/submissions?studentId={uuid}&page=0&size=25`. Tham số `unassigned=true` thay studentId cho nhóm chưa gán. Assert các tham số loại trừ nhau, chống ID ngoài phạm vi, nhiều bài cùng học sinh, retake cùng ID, 0 hợp lệ, AI stale, trạng thái lạ và quyết định sai/thiếu.
- [ ] Thêm projection trả submissionId, batchId, createdAt, status, statusGroup, aiScorePercent nullable, officialScore nullable và maxScore. Tái sử dụng điều kiện hiển thị proposal và quy tắc quyết định của SubmissionService, không gọi service chi tiết theo từng bản ghi.
- [ ] Nối mở dòng, nhóm chưa gán, phân trang chi tiết và các liên kết review. Điều chỉnh SubmissionReviewPage.tsx để nhận ngữ cảnh quay lại từ kết quả, khôi phục filter/page/dòng/focus trong cùng phiên, làm mới dữ liệu sau quyết định và xóa cache riêng tư khi mất quyền.
- [ ] Bổ sung Playwright cho mở rộng bằng bàn phím, nhãn điểm khác thang, bài chưa gán, lỗi/403, quay lại sau duyệt và mục rời bộ lọc. Kiểm tra hai viewport và giữ các ca hàng đợi hiện tại.

## Slice 3 · Nghiệm thu xuyên lớp và nhiều đợt

- [ ] Đo truy vấn với PostgreSQL cách ly ở 1 và 50 học sinh, 2.000 bài tổng hợp. Đối chiếu count/filter/page, kiểm tra EXPLAIN, xác nhận số truy vấn không tăng theo số dòng. Nếu cần index mới, trình SQL và bằng chứng trước khi áp migration.
- [ ] Chạy kiểm thử tích hợp một bài qua API AI FIXTURE, sau đó duyệt và kiểm tra điểm chính thức xuất hiện ở trang kết quả. Kiểm tra lịch sử chuyển lớp, lô chưa gán, quyền bị thu hồi và đường quay lại. Dùng Chrome DevTools MCP hoặc Playwright kiểm tra thao tác thật và focus trên màn hẹp.
- [ ] Chạy `npm run test:config --workspace=teacher-web`, typecheck/build, bộ Playwright desktop/mobile và Gradle test. Cập nhật báo cáo với nguồn dữ liệu, quyền, kết quả truy vấn, API mock và stack FIXTURE. Rà soát độc lập đặc tả, diff và bằng chứng trước khi báo hoàn tất.

## Điều chỉnh sau khảo sát Chromium

- [ ] Slice 1: xác nhận mặc định “Tất cả”, các lối tắt “Cần xử lý”/“Chưa có bài” lọc bằng một thao tác. Ở 390 px, kiểm tra nút “Xem kết quả” và “Tạo đợt” đều nhìn thấy và bấm được, không tràn trang.
- [ ] Slice 2: đi từ một bài qua Kết quả → Duyệt → quay lại. Giữ đúng ngữ cảnh kể cả khi bài vừa chốt đã rời bộ lọc.
- [ ] Sau khi lát cắt này được nghiệm thu, lập đặc tả riêng cho lối tắt Dashboard và xuất kết quả. Tiêu chí đề xuất cho xuất gồm cùng tập kết quả với giao diện, đúng quyền và thể hiện rõ nhiều bài nộp. Gradebook và Class Progress chờ quyết định về điểm đại diện và so sánh thang điểm.
