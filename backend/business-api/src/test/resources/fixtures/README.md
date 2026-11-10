# Ảnh phục vụ kiểm thử offline

`worksheet-addition.jpg` là ảnh phép cộng được dựng bằng chữ in, có kích thước 640×640. Ảnh này dùng để kiểm tra giải mã, ghi file, lấy ảnh có xác thực và lưu quyết định giáo viên trong `TeacherReviewWorkflowIntegrationTest`.

Test này cung cấp kết quả AI giả lập để kiểm tra riêng nghiệp vụ backend. Kết quả của nó không chứng minh OCR, chất lượng bài viết tay hoặc giọng đọc.

Nghiệm thu bằng ảnh chụp và dịch vụ thật dùng `scripts/test/live_teacher_review.mjs` và `scripts/test/live_student_lesson.py`. Ảnh nghiệm thu được truyền qua biến môi trường và lưu ngoài Git.
