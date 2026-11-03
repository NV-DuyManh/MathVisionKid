# Hoàn thiện luồng đăng xuất và trạng thái học tập — 02/11/2026

## Phạm vi và bản chạy

Thực hiện trên `E:\MathVisionKid`, nhánh `main` với các thay đổi cục bộ có sẵn. Không commit, push, triển khai hoặc sửa dữ liệu huấn luyện. Giữ nguyên các thay đổi khác của chủ dự án và demoUI.

Theo ảnh xác nhận cuối cùng của chủ dự án, đích đăng xuất là **trang chủ Portal `/`**, không phải `/login`.

## Đã sửa

- Bỏ toàn bộ thẻ “Đăng xuất thành công”. Route `/logout`, kể cả nguồn Teacher/Admin, xóa thông tin phiên cục bộ rồi dùng điều hướng thay thế lịch sử để về `/` ngay. Thu hồi phiên ở máy chủ tiếp tục chạy với giới hạn 5 giây sẵn có; mạng chậm không giữ người dùng tại màn xác nhận. Không thay đổi quyền truy cập backend.
- QuizHelp khởi tạo lại theo câu hỏi/lượt làm, không giữ phiên hỏi bài cũ khi đổi câu hỏi. Thử lại xóa thông báo lỗi trong sự kiện bấm, tránh cập nhật trạng thái đồng bộ trong effect.
- Bộ đếm thời gian Quiz đồng bộ dữ liệu mới mà không tạo vòng render từ effect; giữ cơ chế tính thời gian hoạt động và heartbeat hiện có.
- NarrationPreparation đổi bộ nhớ âm thanh khi chủ tài khoản thay đổi, kể cả khi bên gọi không truyền React key. Hủy yêu cầu của tài khoản trước và giữ riêng bookmark.
- StudentWorkReview ổn định callback nhận xét và khai báo đầy đủ phụ thuộc effect. Hai biểu thức cropRotation được đổi thành if/else rõ ràng, không đổi thao tác cắt ảnh.
- Test thông báo lỗi 503 được đồng bộ với thông báo an toàn hiện tại; giữ các kiểm tra thử lại và quyền truy cập.

## Kết quả kiểm thử

| Kiểm tra | Kết quả |
|---|---|
| Student toàn bộ Jest sau sửa mã | 114/114 suite, 1.329/1.329 test qua; 70,611 giây |
| Hai test mới bổ sung sau lượt toàn bộ | Cả hai qua trong lượt chạy lại QuizHelp/NarrationPreparation: 17/17 test, 8,797 giây |
| Student lint và TypeScript sau bổ sung test | Qua, không có lỗi/cảnh báo lint |
| Portal config/auth/logout | 30/30 qua, bao gồm 9 tình huống đăng xuất mới |
| Portal lint và TypeScript | Qua |
| Portal production build | Qua; còn cảnh báo chunk chính 721,99 kB trước gzip |
| Portal production smoke | 2/2 qua |
| Module đang phục vụ trên máy | `/logout?source=teacher` HTTP 200; module LogoutPage phục vụ mã điều hướng mới và không còn thẻ xác nhận |

9 tình huống mới bao phủ Portal/Teacher/Admin với yêu cầu thu hồi phiên đang chờ, mất mạng hoặc hết access token. Mỗi tình huống kiểm tra xóa phiên trước khi gửi yêu cầu, về trang chủ ngay cả khi mạng chưa trả lời, không xóa tài khoản mới khi phản hồi cũ đến muộn và nút Back không quay lại route đăng xuất. Chạy trong React StrictMode.

Bản build dùng URL HTTPS mẫu trong biến môi trường riêng của tiến trình để kiểm tra chính sách build, không đổi `.env` và không công bố đó là cấu hình triển khai thật.

## Giọng nói: điều đã kiểm chứng và giới hạn còn lại

Đã đọc lại đường tạo/chia đoạn, giới hạn đồng thời, retry có chặn thời gian, checkpoint và catalog. Catalog đã tái dùng âm thanh theo đúng chủ tài khoản, văn bản, giọng và chế độ; không thêm một lớp cache trùng lặp khác.

Thử trực tiếp từng đoạn Edge TTS cho thấy các lượt có âm thanh và các lượt `NoAudioReceived` xen kẽ. Ví dụ ba đoạn nam 140/153/168 ký tự thành công khoảng 0,88/0,97/1,08 giây, đoạn 145 ký tự tiếp theo thất bại khoảng 9,46 giây. Việc đổi câu hoặc thử lại đôi lúc thành công, nhưng không chứng minh nội dung là nguyên nhân. Không thay lời giảng đã kiểm chứng chỉ để né lỗi nhà cung cấp.

Thư viện 7.3.1 đang có [báo cáo NoAudioReceived ngắt quãng](https://github.com/rany2/edge-tts/issues/512); đây là báo cáo trong kho thư viện, không phải kết luận chính thức về mọi lượt lỗi của ứng dụng. Máy hiện chưa có cấu hình Azure Speech hoạt động. Vì vậy chưa có căn cứ cam kết tạo mới luôn dưới 3 giây hoặc không bao giờ lỗi. Lượt này không thay mã TTS sau khi điều tra; các sửa Mobile ở trên chủ yếu xử lý vòng đời, render và cách ly tài khoản.

Không có thiết bị ADB để xác nhận phát âm thanh trên Android thật. Công cụ thao tác Cốc Cốc bị chặn bởi chính sách URL của công cụ; kiểm tra điều hướng dùng React/Router trong JSDOM và kiểm tra mã thực tế qua HTTP, không ghi nhận là đã bấm thử thành công trên Cốc Cốc.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Sửa lỗi theo nguyên nhân, tránh thêm cache hoặc màn hình không cần thiết.
  - Applied to: Đăng xuất tập trung, truy nguyên lỗi TTS, chọn kiểm thử hồi quy và giữ nguyên cấu hình bí mật.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Luồng điều hướng và trạng thái React/React Native cần tránh render thừa và dữ liệu phiên cũ.
  - Applied to: QuizHelp, useQuizActivity, NarrationPreparation, StudentWorkReview và LogoutPage.
