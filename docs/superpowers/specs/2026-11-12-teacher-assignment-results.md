# Kết quả theo bài tập

Trạng thái: đề xuất chờ duyệt. Mốc nguồn: `Loc/Teacher-features`.

## Công việc của giáo viên

Từ lớp hoặc danh sách bài tập, mở kết quả của một bài, xem còn ai cần xử lý, mở bài làm và quay về đúng bộ lọc. Đầu trang có tên lớp, bài tập, thang điểm và số học sinh theo tiến độ. Tiếp theo là tìm tên, lọc và danh sách mở rộng từng học sinh. Màn hẹp dùng danh sách thẻ theo cùng thứ tự đọc. Điểm chính thức và điểm AI có nhãn và đơn vị rõ ràng.

## Chính sách dữ liệu đề xuất

- Spring kiểm tra chủ bài tập và phân công lớp hiện tại, đồng thời áp dụng quyền chủ đợt cho từng bài nộp. Không mở rộng quyền của Review Workspace. Một bài nộp thuộc đợt của bài tập được tính riêng. Chụp lại và retry trên cùng ID không sinh thêm lần nộp.
- Tập hiển thị là học sinh hiện thuộc lớp cộng với học sinh từng có bài nộp được phép xem trong bài tập. Đánh dấu nhóm sau là ngoài danh sách lớp hiện tại. “Chưa có bài” chỉ áp dụng cho danh sách hiện tại; dữ liệu hiện có không chứng minh danh sách lớp tại thời điểm giao.
- Bài không có học sinh được đưa vào nhóm riêng, vẫn có trạng thái và đường xử lý khi được phép. Không gán suy đoán. Không nhập các bài tự luyện không liên kết bài tập.
- Mỗi bài nộp hiển thị trạng thái xử lý riêng, điểm AI nếu có và điểm giáo viên đã chốt nếu hợp lệ. Không tự chọn một điểm đại diện. Không hiển thị số 0 cho trường hợp thiếu điểm. Bộ lọc học sinh có thể chồng lấn nếu một người có nhiều bài. Bộ đếm ghi rõ đơn vị và phạm vi.

## Giao diện và hợp đồng

- Đề xuất `GET /teacher/assignments/{assignmentId}/results` phân trang theo học sinh, tìm và lọc ở Spring, thứ tự ổn định theo tên và ID. Chi tiết bài nộp tải khi mở dòng, có phân trang riêng. Bài chưa gán có phân trang riêng. Dùng projection và truy vấn theo lô, không đọc chi tiết ảnh trong danh sách.
- Trang giữ bộ lọc, trang, dòng đang mở và focus quay lại từ review trong cùng phiên. Không ghi tên tìm kiếm vào URL. Có trạng thái tải, rỗng, lỗi, thử lại, mất quyền. Thao tác được bằng bàn phím, có nhãn accessible, trạng thái đọc được ngoài màu sắc.
- Phạm vi gồm đọc kết quả và điều hướng sang luồng xử lý hiện có. Gradebook nhiều bài, xuất điểm, sửa điểm và thay đổi quy tắc sở hữu nằm ngoài lát cắt.

## Nghiệm thu

Đối chiếu DB với lớp chuyển đi/chuyển đến, nhiều bài cùng học sinh, ảnh chụp lại, chưa gán, 0 hợp lệ, lỗi, đang xử lý, cần xác nhận, cần chụp lại, chờ duyệt, đã chốt, mất quyền và giới hạn trang. Kiểm tra số truy vấn hữu hạn khi tăng sĩ số, bộ đếm và lọc nhất quán. Chromium desktop và mobile kiểm tra tìm, mở, duyệt, quay lại, cập nhật kết quả và điều hướng bàn phím. API mock cho lỗi UI, PostgreSQL cách ly và AI FIXTURE cho luồng tích hợp.

## Quy tắc cụ thể sau phản biện dữ liệu

- Tập dữ liệu hợp lệ yêu cầu cả `submission.assignment_id` và `batch.assignment_id` bằng bài đang xem. Áp quyền bài tập và quyền đợt trước mọi phép đếm, tìm, phân trang và đọc chi tiết. Loại bản ghi khóa ngoại mâu thuẫn khỏi kết quả. Kiểm thử đọc trực tiếp ID học sinh và ID đợt ngoài phạm vi. Mất quyền làm màn hình xóa kết quả cũ và hiển thị trạng thái từ chối.
- Nhóm “Đang xử lý” gồm CREATED, IMAGE_UPLOADED và PROCESSING. Nhóm “Cần xử lý” gồm PROPOSED_GRADE, NEEDS_CONFIRMATION, NEEDS_RETAKE, CROP_REQUIRED, FEEDBACK_READY, REVIEW_REQUIRED, OUT_OF_SCOPE và FAILED, vẫn hiển thị trạng thái cụ thể và hành động có thật. TEACHER_APPROVED hoặc TEACHER_OVERRIDDEN kèm quyết định hợp lệ vào nhóm “Đã chốt”. Trạng thái lạ hoặc quyết định thiếu/sai thang điểm hiển thị “Cần kiểm tra dữ liệu”, không tính đã chốt.
- Điểm chính thức lấy từ quyết định duy nhất theo submission ID, trong khoảng 0 đến thang điểm. Điểm AI theo quy tắc hiển thị analysis của job hiện hành ở trang duyệt, với đơn vị gốc trên 100. Điểm chính thức dùng thang bài tập. Điểm 0 hợp lệ hiển thị bình thường, điểm thiếu để trống có nhãn.
- Mặc định 25 học sinh hoặc bài mỗi trang, tối đa 50. Sắp xếp học sinh theo tên rồi ID, bài nộp theo thời gian giảm dần rồi ID. Bộ đếm toàn bài độc lập với tìm/lọc, ghi rõ “học sinh” hay “bài nộp”. Bộ đếm theo trạng thái học sinh có thể chồng lấn. Cùng phản hồi dùng một snapshot PostgreSQL nhất quán; trang hoặc lượt tải tiếp có thể phản ánh cập nhật mới, giao diện làm mới sau quyết định.
- Màn hình mở đầu hiển thị toàn bộ lớp và đặt lối tắt đến nhóm cần xử lý ở đầu. Cột/thẻ chỉ hiển thị số bài và các trạng thái có ý nghĩa. Khi mở chi tiết mới hiển thị từng điểm, thời điểm nộp, nguồn đợt và liên kết. Nhóm chưa gán hiện ngay nếu có dữ liệu, độc lập với ô tìm tên.
- Bộ lọc gồm Tất cả, Chưa có bài, Đang xử lý, Cần xử lý và Có bài đã chốt. Nhóm dữ liệu bất thường cũng có đường vào từ Cần xử lý nhưng giữ nhãn riêng. Phân trang nhóm chưa gán chỉ hiện khi mở nhóm và có nhiều trang. Nút mở học sinh có `aria-expanded`, vùng thông báo đọc số kết quả sau lọc. Quay lại từ review khôi phục focus vào mục đã mở, hoặc tiêu đề danh sách nếu mục đã rời bộ lọc. Giữ hành vi “Duyệt bài tiếp theo” trong phạm vi hàng đợi hiện có.

## Lựa chọn và rủi ro

Hàng đợi theo đợt phục vụ quyết định trên từng bài. Trang theo bài tập phục vụ đối soát xuyên đợt. Tải toàn bộ phía client hoặc gọi theo từng học sinh làm chi phí tăng theo lịch sử và dễ làm số liệu thiếu nhất quán. Dùng truy vấn Spring giới hạn dữ liệu, kiểm tra EXPLAIN với lớp 50 học sinh và 2.000 bài nộp tổng hợp, đo số truy vấn cho trang 1 và 50 học sinh. Mục tiêu là không có truy vấn theo từng học sinh hoặc bài. Chỉ đề xuất migration index nếu EXPLAIN cho thấy cần, trình chủ dự án trước khi áp dụng.

## Bổ sung sau khi xem trực tiếp Teacher Web

Đề xuất mở mặc định ở “Tất cả” để lần đầu nhìn đủ danh sách lớp. Các lối tắt “Cần xử lý” và “Chưa có bài” đứng ngay sau phần tổng quan và áp dụng bộ lọc bằng một thao tác. Trên danh sách bài tập, “Xem kết quả” và “Tạo đợt” là hai hành động có nhãn riêng, kiểm tra cả ở màn 390 px. Mở bài từ Kết quả dùng cùng quyền và màn hình duyệt hiện có. Đề xuất này chờ duyệt cùng đặc tả.

Các bước mở rộng sau lát cắt đầu: bổ sung lối tắt đến bài tập đang làm từ Dashboard, rồi xuất kết quả theo bài có quyền kiểm soát. Gradebook đa bài và Class Progress cần chính sách điểm đại diện riêng.
