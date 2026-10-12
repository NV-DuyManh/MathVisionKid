# Rà lỗi OCR toàn kho và triển khai — 12/10/2026

Trạng thái: hoàn tất lượt rà toàn kho, thử lại các vùng cần xem và đối chiếu kết quả. Các sửa lỗi runtime đã triển khai và kiểm tra thành công; phần nhận dạng chữ chưa đạt để thay model đang dùng.

## Phạm vi và cách xử lý

Đã đối chiếu toàn bộ danh sách 64.803 nguồn riêng biệt và 101.797 vùng của đợt nhận diện trước với JSONL/SQLite. Không còn lỗi thực thi trong kết quả hợp lệ của đợt trước. Lần này xử lý những vùng rỗng, điểm thấp, bố cục đáng ngờ hoặc bị giới hạn chiều rộng, đồng thời phát hiện lại toàn bộ 1.581 trang chụp.

Kết quả cuối: đã thử lại **25.950 vùng trên 8.635 ảnh**, bao phủ đủ **25.156 vùng từng cần rà trên 8.380 ảnh cũ**, cộng các cảnh báo phát sinh sau đó. Phát hiện mới trên đủ 1.581 trang chỉ thay đổi hộp của `828.jpeg`; các trang khác giữ toạ độ cũ. **Không còn lỗi thực thi/đọc nguồn chưa được xử lý** trong các kết quả hợp lệ. Điều này không có nghĩa toàn bộ chữ đã đúng: 349 vùng trước đó rỗng có gợi ý đồng thuận, 5.783 vùng vẫn rỗng ở cả hai cách đọc, và 11.037 vùng của nhóm cảnh báo hiện tại có hai cách đọc khác nhau. Chúng vẫn cần rà nguồn; không tự đưa gợi ý đồng thuận vào ứng dụng hoặc dữ liệu train.

Các ảnh/ZIP/Parquet gốc chỉ được đọc từ Drive vào RAM. Không tạo ảnh nguồn, ảnh tổng hợp, ảnh cắt dòng hoặc archive trên ổ máy. Ảnh tổng hợp phục vụ kiểm tra trực quan được hiển thị từ RAM. Các thư mục nguồn tạm mà chủ dự án đã xoá không được tạo lại. Chỉ mã, thông tin nguồn, kết quả nháp và báo cáo được lưu trong thư mục riêng của lượt chạy.

12 ảnh trên Drive có tên được đổi thêm `(1)`. Đã tìm đúng tệp hiện tại bằng đối chiếu SHA-256 với nguyên bản và chạy lại; không đổi tên ảnh trên Drive, sửa manifest cũ hay sửa chỉ mục nguồn toàn cục. Các bản ghi lỗi ban đầu được giữ để truy vết. Lượt trang ban đầu được dừng sau khi ghi giao dịch SQLite hoàn chỉnh; danh sách phần còn lại được cố định thành hai lượt độc lập, không tính trùng kết quả đã có.

Mỗi vùng cần rà được thử hai đầu vào: tương phản màu với chiều rộng tối đa 2.048 và tương phản xám với chiều rộng tối đa 1.024. Model/từ điển thử nghiệm được giữ cố định, không train thêm. Kết quả từng cách đọc được lưu riêng, không tự sửa bản nháp gốc, tự tạo nhãn đúng hoặc cấp điều kiện train.

## Phát hiện về chất lượng

Đối chiếu 60.247 bản nháp với cột `text` có sẵn trong Parquet: model thử nghiệm hiện tại có 377.801 lỗi trên 2.742.261 ký tự tham chiếu, CER **13,78%**; bản thử nghiệm trước là 13,99%. Đây là đối chiếu với nhãn được cung cấp, không phải độ chính xác tổng quát của ứng dụng. Nguồn nhãn/chia người viết và mức lộ dữ liệu tiền huấn luyện chưa được xác minh. Nhóm `test` 1.000 ảnh còn một ảnh đã xuất hiện trong DEV, nên không được xem là tập kiểm tra hoàn toàn độc lập.

Trên 61 dòng DEV đã được rà trước đây, tương phản màu/xám làm CER tăng từ 5,60% lên 6,22%/6,48%, đồng thời tăng lỗi số/ký hiệu. Năm dòng HOLDOUT đã được xem trước đây chỉ được dùng làm chẩn đoán; không trở thành bằng chứng release mới. Hai cách tăng tương phản không được áp dụng làm mặc định.

Thử riêng đầu vào rộng 2.048 với **model production giữ nguyên**, trên 185 dòng dài của Parquet `test`, giảm CER từ 10,07% xuống 8,73% nhưng tăng số ký tự số/ký hiệu phát sinh trong dòng không có chúng từ 3 lên 7. Cách này chưa đưa vào runtime vì còn lỗi đã biết và chưa có kiểm định độc lập phù hợp.

Kiểm tra trực quan sáu vùng mà hai cách đọc cùng đồng ý cho thấy vẫn có chữ giả từ đường kẻ, dấu gạch, vùng trống và hộp cắt thiếu chữ. Một hộp chứa nhiều hàng chữ nằm nghiêng 90° nhưng trả một ký tự. Cả sáu không được duyệt thành nhãn. Đồng ý giữa hai cách xử lý của cùng model không chứng minh nhận đúng.

ZIP có `labels.csv` nhưng nhãn không luôn là bản chép chữ: ảnh nền không có chữ được gắn câu trả lời kiểu “không thể nhận dạng”; một dòng có chữ “Thử lại” bị gán thành một dòng `b)`. Đã đưa **374/2.844 nhãn có nội dung** vào hàng chờ vì có dấu hiệu câu trạng thái/từ chối, cần rà trực quan. Việc gắn cờ không tự chứng minh cả 374 nhãn sai. 131 ảnh không có nhãn nội dung khớp để chấm. CER đối chiếu ZIP không được coi là độ chính xác OCR đã xác minh; không train tự động từ bộ nhãn này.

## Thay đổi đã triển khai

Đã xây dựng lại và cập nhật hai dịch vụ `ai`/`worker`, giữ nguyên model production và từ điển. Bản sửa phát hiện chữ nhỏ trên trang ô ly thay sáu hộp lưới sai của `828.jpeg` bằng hộp bao chữ thực; model thử nghiệm vẫn đọc chữ `t` thành `1`, nên chưa chứng nhận nhận dạng ký tự này.

API trước đây lưu ảnh chẩn đoán dù cấu hình trace bị tắt. Đã sửa để chỉ lưu khi chủ động bật trace ở môi trường phát triển; production không lưu ảnh chẩn đoán kể cả trace bị bật nhầm. Đây là phần lưu ảnh chẩn đoán của endpoint, không phải thay đổi cơ chế lưu bài người dùng.

Đã cập nhật địa chỉ API cũ không còn hoạt động và xuất bản lại ba trang Vercel. Kiểm tra sau triển khai: nội dung mã trong cả hai container khớp mã đã thử; model/từ điển giữ nguyên; phát hiện ảnh thật từ Drive trong container trả đúng hộp `[324, 420, 363, 502]`; endpoint OCR HTTP trả thông tin model/điểm hữu hạn; ba trang web trả HTTP 200 và đăng nhập tài khoản học sinh qua backend thành công. Không có kiểm thử điện thoại thật trong lượt này.

Lưu image Docker cũ để rollback. Không mua dịch vụ, chuyển tài khoản Vercel, commit hay push. Web đã cập nhật nhưng backend/OCR vẫn chạy bằng máy hiện tại; tắt máy vẫn làm API/OCR ngừng.

## Kiểm tra và kết quả

Bộ hồi quy **275 kiểm tra đạt**; sau khi bổ sung trường hợp bật trace ở development, kiểm tra lưu ảnh đạt **4/4**. Kiểm tra riêng ba tỉ lệ ảnh xác nhận đầu vào bị giới hạn kích thước, giá trị hữu hạn và không thay đổi pixel nguồn. `git diff --check` đạt. Thay đổi còn được chụp mã/hash vào thư mục bằng chứng.

Bằng chứng riêng: `ai-training/datasets/drive_math/quality_recovery_20261012/`. Danh sách đối chiếu toàn kho, các lượt thử lại, nhãn cần rà, kết quả đo và kiểm tra triển khai đều ở đó. Kết quả OCR còn là bản nháp cần xem lại; không dùng số vùng có chữ hoặc điểm softmax để suy ra độ chính xác.

Đối chiếu cuối nằm trong `complete_reconciliation.json`; danh sách đủ các vùng cần rà là `complete_review_queue.jsonl`; chỉ mục toàn bộ nguồn là `complete_effective_corpus_index.jsonl`. Không tính trùng các lượt bị dừng hoặc các lần đọc lại. Một lượt bổ sung lỗi kiểm tra cuối do trùng tên biến đã được sửa trong bản mới và chạy lại thành công, giữ nguyên lượt cũ để truy vết. Kiểm tra cuối xác nhận không có job của đợt này còn chạy, chỉ mục Drive/model production không đổi và các thư mục nguồn tạm đã xoá vẫn không tồn tại.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Tái sử dụng trình nhận diện, OpenCV/Pillow, SQLite và quy trình triển khai hiện có; sửa điều kiện lưu ảnh ở đường dùng chung.
  - Applied to: Đối chiếu nguồn, thử lại trong RAM có giới hạn, bảo toàn kết quả cũ/nhãn, kiểm tra hồi quy và cập nhật dịch vụ OCR.
