# Kế hoạch kiểm thử và cải tiến nhận diện từ ảnh Drive

## Yêu cầu và thời điểm bắt đầu

Chủ dự án muốn kiểm thử bộ ảnh toán theo đợt 10 hoặc 100 ảnh, cải tiến nhận diện dòng và huấn luyện thêm model từ dữ liệu phù hợp. Chủ dự án chọn bắt đầu khi nhắn **“bắt đầu test”**, không đặt lịch chạy ngày mai hoặc tự chạy hằng ngày. Lượt hiện tại chỉ lưu kế hoạch, không chạy kiểm thử hàng loạt hay huấn luyện.

Nguồn ảnh: [thư mục Drive được chủ dự án cung cấp](https://drive.google.com/drive/folders/1hw9icN3tsAkhghODoA_6WZt7Jg44NSFX?usp=sharing).

## Luồng thực hiện sau khi được gọi bắt đầu

1. Kiểm tra quyền truy cập, kiểm kê ảnh và nhãn sẵn có; ghi ID, checksum và trạng thái từng mẫu. Loại ảnh trùng, nhóm ảnh cùng trang/bài/người viết để tránh rò rỉ giữa các tập.
2. Chọn 10 ảnh đa dạng cho đợt đầu: đề bài, bài giải, chữ viết tay, phép tính, hình học và ảnh vở có đường kẻ. Kiểm tra nội dung và khung dòng tham chiếu; đánh dấu rõ nhãn chưa được xác minh.
3. Chạy pipeline hiện tại, lưu ảnh có khung dòng và nội dung đọc được. Đo bỏ sót dòng, gộp/tách nhầm dòng, thứ tự đọc, vị trí khung, lỗi chữ/số/ký hiệu và thời gian xử lý. Không công bố tỷ lệ chính xác nếu chưa có nhãn tham chiếu đủ tin cậy.
4. Sửa nguyên nhân theo nhóm lỗi, kiểm thử lại cả các mẫu lỗi và tập hồi quy. Giữ lịch sử trước/sau, không viết quy tắc riêng chỉ để khớp một ảnh mẫu.
5. Khi luồng và dữ liệu ổn định, tăng lên 100 ảnh mỗi đợt, tiếp tục từ danh sách ảnh chưa xử lý thay vì lặp lại nhóm đầu. Định lượng trên tập đánh giá cố định, tách biệt với tập dùng để phát triển hoặc huấn luyện.
6. Từ các dòng đã được gán nhãn và kiểm tra, chuẩn bị dữ liệu cho đúng thành phần: phát hiện dòng và đọc chữ/ký hiệu là hai vấn đề khác nhau. Tận dụng harness và cấu hình huấn luyện hiện có khi phù hợp; harness hiện tại cho phép tính đặt dọc chưa bao phủ đầy đủ ảnh đề/bài giải viết tay.
7. Huấn luyện một phiên bản ứng viên với giới hạn tài nguyên phù hợp máy và giữ checkpoint hiện hành. Chỉ thay model đang phục vụ sau khi phiên bản mới cải thiện trên tập độc lập và vượt qua kiểm thử hồi quy; nếu không thì giữ bản đang dùng ổn.

Mỗi đợt có báo cáo số ảnh đã kiểm tra, mẫu lỗi, số liệu trước/sau, thay đổi đã áp dụng, phiên bản model và phần việc tiếp theo. Không coi đầu ra OCR hoặc nhãn AI chưa kiểm tra là sự thật tham chiếu. Không suy luận rằng nhận diện đúng đồng nghĩa phản hồi hướng dẫn giải đã đúng; cần kiểm tra luồng ứng dụng riêng.

## Điều kiện và giới hạn

- Máy bật, workspace và dữ liệu truy cập được khi chủ dự án yêu cầu bắt đầu.
- Chủ dự án đã đề nghị huấn luyện thêm; không chạy huấn luyện trong lượt lưu kế hoạch này.
- Không tự đặt lịch, không tự thuê tài nguyên trả phí, không commit/push nếu chưa có yêu cầu tương ứng.
- Không cam kết nhận diện toàn bộ bộ ảnh chính xác trước khi đo kết quả thật.

## Skills Applied

Skills Applied: None — no installed skill matched the task. Đây là kế hoạch kiểm thử/huấn luyện AI, chưa thực hiện thay đổi mã hoặc thao tác Drive trong lượt này.
