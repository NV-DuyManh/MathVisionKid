# Bản cải tiến học tập và giọng nói — 29/10/2026

Phạm vi: đưa lên `main` bản đang chạy tại `E:/MathVisionKid` sau khi chủ dự án xác nhận hoạt động tốt. Điểm gốc trước phát hành: `b0a49bb`.

## Nội dung đưa lên

- Phân số đứng, khung đề gọn theo nội dung, giữ đáp án đúng/sai để xem lại và chỉ chuyển khi học sinh bấm tiếp tục; hiệu ứng phản hồi đúng và giao diện lỗi gọn.
- Giữ hai giọng hiện tại, UI chỉ ghi Giọng nam/Giọng nữ; ghi nhớ lựa chọn, cải thiện đọc đơn vị, rút nội dung lặp và chuẩn bị âm thanh nền. Giới hạn chờ tạo giọng 60 giây.
- Bộ phát có thanh tua, nghe lại, điều khiển bàn phím; WAV mới có mốc đoạn từ số frame PCM thật để tô sáng và bấm nghe đúng đoạn. Tệp cũ thiếu mốc/giọng thiết bị không dùng mốc đoán.
- Lưu cục bộ bước học, câu trả lời đang nhập, câu hỏi đang gõ và vị trí nghe; khôi phục bước bằng xác nhận của máy chủ, có thẻ học tiếp trên trang chủ.
- Câu luyện đổi số tùy chọn, chấm bằng số hữu tỉ trên máy chủ; tách riêng khỏi dữ kiện đề gốc, không tự chuyển bước.
- Đo hiệu năng giọng và web bằng số liệu cục bộ có giới hạn; không gửi nội dung học sinh đến hệ thống theo dõi bên ngoài.
- Bộ hồi quy 20 bài và công cụ chấm dự đoán OCR/đáp án; không huấn luyện mô hình trong đợt này.
- Đăng nhập ba bí danh demo theo yêu cầu trước đó vẫn đi qua kiểm tra mật khẩu/vai trò phía máy chủ. Khởi tạo mật khẩu demo chỉ chạy với profile `dev & !prod`.

Theo yêu cầu đồng bộ toàn bộ mới nhất, đưa kèm thay đổi công cụ OCR `--device cpu/cuda`, kiểm thử cache theo thiết bị và các tài liệu/bằng chứng hiện có. Giữ rõ các kết quả nghiên cứu cũ là kết quả của đợt trước; không train thêm hoặc thay model trong lần đồng bộ này.

`demoUI` được giữ nguyên trên máy và bỏ qua trong Git theo yêu cầu riêng. Không đưa bản dựng có thể tạo lại, cache, môi trường riêng, khóa bí mật, thư viện cài đặt, checkpoint hoặc dữ liệu huấn luyện vào Git. Các bản sao trước merge được giữ cục bộ để phục hồi; tài liệu, ảnh giao diện và mẫu kiểm chứng nhẹ được lưu cùng dự án.

## Kiểm chứng trước phát hành

| Kiểm tra | Kết quả |
|---|---|
| Student Jest | 97 bộ, 1.150 kiểm thử đạt |
| Python — các bộ liên quan | 134 kiểm thử đạt |
| Java | 401 kiểm thử, 0 lỗi/thất bại; bootJar thành công |
| TypeScript | Đạt |
| Lint Student | 0 lỗi; còn hai cảnh báo có sẵn trong `cropRotation.web.ts` |
| Xuất web/Android | Thành công |
| Build Teacher/Admin/Portal | Thành công với URL HTTPS mẫu chỉ truyền trong tiến trình build; không sửa cấu hình chạy hoặc triển khai |
| Công cụ nhận diện batch | 10 kiểm thử đạt; không chạy huấn luyện hay thay model |
| Metro sau dọn dẹp | 16 kiểm thử và 1 kiểm tra hợp đồng đạt, gồm loại `demoUI`/bản dựng lưu cục bộ khỏi chỉ mục |
| UI web | 5 kích thước; không tràn ngang; kiểm tra giữ câu hỏi/đáp án, giọng/vị trí nghe và focus |
| Quyền resume/checkpoint | Student được phép; khách 401, Teacher 403, đổi nguồn đề 400 |
| Web đang chạy sau xuất | Trang chủ, xác nhận đề và lưu số đo web hoạt động; không có lỗi console/page trong lượt kiểm tra |

Bằng chứng chi tiết trong `report/student-six-upgrades-20261029/`. Bản dựng lớn có thể tạo lại được dọn sau khi lưu metadata; không đưa payload biên dịch vào Git.

Đã chuyển 59 mục bản dựng, tổng cộng 373.549.194 byte, vào `.local-artifacts/review-builds-20261029/` và giữ manifest phục hồi. Đây là sắp xếp cục bộ có thể đảo ngược, **không xóa vĩnh viễn và không giải phóng dung lượng ổ đĩa**. Metadata vẫn nằm tại đường dẫn báo cáo cũ. Lệnh xóa đệ quy ban đầu bị kiểm duyệt tự động chặn với thông báo `blocked by policy`; phương án lưu cục bộ an toàn đã thực hiện thành công.

`demoUI` và `.local-artifacts` cũng được loại khỏi phạm vi Metro lập chỉ mục, tránh kéo tài sản demo/bản dựng cũ vào quá trình theo dõi mã ứng dụng.

## Giới hạn được ghi nhận

- Chưa có kiểm chứng Android vật lý trong vòng này. Xuất gói thành công không đồng nghĩa đã thử điện thoại thật.
- Một lượt đo mới mỗi giọng, kịch bản 113 ký tự/hai đoạn: nam sẵn sàng sau 19.774 ms, nữ 6.000 ms; đọc lại tệp lưu lần lượt 13 ms và 17 ms. Đây là số đo HTTP cục bộ, không phải thời gian bấm-phát trên điện thoại hay p95 dịch vụ. Chưa thể cam kết tạo mọi nội dung mới trong 1–3 giây.
- Cấu hình thực tế vẫn dùng Edge. Azure Speech chưa có khóa/vùng tài nguyên để kiểm chứng. Chuẩn bị nền vẫn dùng hạn mức dịch vụ; không cam kết sử dụng vô hạn.
- Phiên học máy chủ có thời hạn một giờ và nằm trong bộ nhớ. Khi hết hạn/khởi động lại máy chủ, giữ văn bản để bắt đầu lại; không phục hồi giả tiến độ. Không lưu ảnh hoặc bản ghi chưa gửi qua lần khởi động lại bằng tính năng mới này.
- Bộ hồi quy 20/20 là kiểm tra đáp án chuẩn; chưa cấp dự đoán nên không có điểm chính xác OCR/model. Chưa xác minh độc lập với toàn bộ dữ liệu huấn luyện trước đây.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: phát hành gọn bản đã được kiểm thử, không mở rộng code hoặc phụ thuộc.
  - Applied to: kiểm tra phạm vi staged, kiểm thử bổ sung công cụ OCR theo yêu cầu mở rộng, giữ riêng `demoUI`/bí mật và dữ liệu nặng, dọn bản dựng có thể tạo lại, cập nhật `main` theo fast-forward, xác minh commit từ remote.

Các cải tiến chức năng trước khi phát hành đã áp dụng `ui-ux-pro-max`, `vercel-react-best-practices`, `fixing-accessibility` và `ponytail`, được ghi chi tiết trong báo cáo cục bộ của từng vòng.
