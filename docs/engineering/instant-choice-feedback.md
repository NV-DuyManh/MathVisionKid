# Phản hồi lựa chọn tức thì

`LessonStep.choiceChecks` là mảng boolean cùng thứ tự với `choices`, đúng một phần tử `true`. Dữ liệu được tạo từ bước hiện tại trong kế hoạch đã kiểm chứng. App chỉ hiện màu/ký hiệu sau khi học sinh chọn. Đây là phản hồi luyện tập đã gửi sẵn tới máy, có thể đọc được trong dữ liệu mạng; không dùng cơ chế này để giữ bí mật đáp án của bài thi.

- Không gửi khóa của bước tương lai hoặc đáp án số chưa mở. Bước nhập số dùng `[]`.
- Lựa chọn sai có phản hồi ngay và chọn lại được, không cần gọi máy chủ: thao tác sai vốn không thay đổi tiến độ phiên học.
- Lựa chọn đúng hiện ngay, đồng thời gửi chính câu trả lời tới endpoint `lesson/answer`. Chỉ kết quả máy chủ mới mở nút Tiếp tục và cập nhật bước/tiến độ.
- Client không gửi `choiceChecks`, điểm hoặc cờ đúng/sai làm bằng chứng. Máy chủ vẫn tự kiểm tra câu trả lời, tài khoản, session và revision như trước.
- Lỗi lưu giữ lựa chọn, hiển thị thử lại; không tự công nhận bước hoàn thành. Dữ liệu phản hồi trên client gắn session/revision, không dùng lại cho bước khác.
- API cũ không có trường này hoặc gửi `[]` vẫn chạy bằng kiểm tra máy chủ. Spring và Student từ chối mảng lệch chiều dài, sai kiểu hoặc có nhiều/không có đáp án đúng.
- Quiz có chấm điểm/sao vẫn do máy chủ quyết định; thay đổi này áp dụng các lựa chọn trong bài học, không đưa đáp án Quiz ra client.
