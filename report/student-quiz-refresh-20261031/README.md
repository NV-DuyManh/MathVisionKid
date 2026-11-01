# Student: Quiz, giọng có sẵn và màn hình hoàn thành

Ngày kiểm tra: 31/10/2026. Thay đổi đã nằm trong mã nguồn và bản chạy local tại `E:/MathVisionKid`. Chưa commit/push trong lượt sửa này.

## Đã sửa theo yêu cầu

1. **Đồng hồ Quiz chỉ tính thời gian đang làm.** Bấm Bắt đầu mới mở lượt tính giờ; rời màn hình hoặc đưa app xuống nền sẽ gửi tạm dừng. Quay lại tiếp tục cộng thời gian đã làm, không cộng thời gian vắng mặt. Hoàn thành sẽ đóng băng đồng hồ. Máy chủ quản lý thời gian và chấm sao; máy khách không được gửi thời gian tùy ý.
2. **Tiêu đề đề bài ngắn gọn:** dùng “Đề bài”, bỏ nhãn “Đã xác nhận”. Giữ khả năng mở/thu gọn và xem ảnh đề gốc.
3. **Bỏ hình phân số khỏi Xem thêm:** bỏ nút và màn hình phụ tương ứng trong luồng bài học. Không thay cách hiển thị phân số đứng trong đề/lời giải.
4. **Quiz dùng một vùng làm bài thống nhất:** đề, đồng hồ nhỏ, câu trả lời và kết quả nằm trong cùng thẻ. Nghe giảng và Hỏi bài mở bằng cùng bộ khung, bộ phát và phần ghi âm/hỏi đáp của bài học. Lịch sử và cách giải chỉ mở khi cần. Quyền nghe lời giải vẫn do máy chủ kiểm tra; nghe đề không tự mở khóa lời giải. Nhờ hướng dẫn được ghi nhận là lượt có hỗ trợ, tối đa 1 sao theo chính sách hiện có.
5. **Có lựa chọn “Giọng có sẵn”** ở bài học, câu trả lời hỏi bài và Quiz, bên cạnh Giọng nam/Giọng nữ. Lựa chọn được lưu cho các đoạn sau. Khi chọn giọng này, bộ phát dùng giọng Việt của thiết bị, không gửi yêu cầu tạo âm thanh lên API giọng của dự án. Không tự phát khi mở. Dừng khi đóng/rời màn hình; bỏ qua callback cũ để không ảnh hưởng lượt đọc mới. Khi đổi từ giọng có sẵn về giọng trực tuyến, chuẩn bị ngầm hoạt động lại.
6. **Hoàn thành bài:** chỉ hiển thị lời mời Quiz sau khi có đề xuất đã được xác minh; không dựng thẻ trống hoặc thẻ lỗi khi không có bài phù hợp. Áp dụng cho bài học và nhận xét bài làm. Bài học hoàn tất luôn có nút Về trang chủ/Làm bài khác, độc lập với lời mời Quiz. Quiz hoàn tất có Về trang chủ/Chọn câu đố khác.

## Cách xử lý đồng hồ và dữ liệu cũ

- Máy đang mở Quiz gửi tín hiệu hoạt động mỗi 4 giây. Mỗi tín hiệu có hiệu lực tối đa 12 giây, gắn với đúng lượt bắt đầu và đúng chủ sở hữu.
- Rời màn hình bình thường gửi tạm dừng ngay. Nếu app bị tắt đột ngột hoặc mạng mất trước khi gửi được tạm dừng, máy chủ có thể tính thêm phần còn lại của khoảng 12 giây đó; không chạy tiếp nhiều giờ/ngày. Không khẳng định sai rằng máy chủ biết chính xác thời điểm app bị ngắt mạng.
- Migration V28 thêm bộ đếm thời gian hoạt động. Lịch sử lần thử và số sao không bị viết lại. Bài đã hoàn tất giữ thời lượng cũ. Với bài đang dở từ phiên bản cũ, không thể suy ra thời gian học thực từ giờ bắt đầu: bộ đếm mới khởi tạo ở trạng thái tạm dừng, từ 0.
- Đã sao lưu cơ sở dữ liệu local trước khi cập nhật. Bản sao lưu và dữ liệu QA nằm trong `.local-artifacts/`, được Git bỏ qua.

## Kiểm chứng

- Student: toàn bộ 113 bộ kiểm thử, **1.282 kiểm thử qua**. Sau đó thêm hai trường hợp về lựa chọn giọng có sẵn và ẩn đề xuất nhận xét bài làm; bộ chạy tập trung tương ứng **36 kiểm thử qua**. Luồng hoàn thành/nhận xét/bài học cũng đã chạy tập trung **89 kiểm thử qua**.
- TypeScript: `npm run typecheck --workspace=student-mobile` qua.
- Backend: `gradlew test bootJar` qua; **486 trường hợp, 0 lỗi, 1 bỏ qua**. Trường hợp bỏ qua là `MinioLocalStorageIntegrationTest.springStorageBeanAuthenticatesAndReadsTheExistingBucket`; không coi đó là kết quả đạt.
- PostgreSQL/Flyway và HTTP thật trên bản sao cơ sở dữ liệu: **17 kiểm tra qua**, gồm bảo toàn lịch sử, tạm dừng/tiếp tục, timestamp qua PostgreSQL, từ chối tín hiệu lượt cũ, từ chối sửa thời gian từ máy khách, giới hạn phiên mất kết nối, kiểm tra xác thực, hoàn thành có hỗ trợ và dừng đồng hồ. QA không thay dữ liệu ứng dụng gốc.
- Local đang dùng Flyway V28. Kiểm tra sức khỏe máy chủ nghiệp vụ, AI, Student và ba web portal đều trả HTTP 200 sau khi nạp lại dịch vụ.
- Đã xuất bundle web và Android. Bản xuất kiểm tra dùng địa chỉ cấu hình riêng trong tiến trình build; không đổi cấu hình dịch vụ đang sử dụng của dự án.
- `git diff --check` qua. Không đổi dependency/lockfile; không đưa khóa dịch vụ, bản sao dữ liệu hay demoUI vào Git.

## Giới hạn cần nói rõ

- Chưa có bằng chứng kiểm thử âm thanh trên điện thoại thật trong lượt này. Các test của giọng thiết bị giả lập callback của bộ đọc để kiểm tra trạng thái, hủy, lỗi và không gọi API đám mây; không thay thế việc nghe thử chất giọng thực tế.
- Đã mở LDPlayer/Expo Go qua Computer Use, nhưng việc nhập địa chỉ dự án bị lỗi đồng bộ nhập liệu của trình giả lập, nên chưa vào được màn hình Quiz để xác nhận hình ảnh thực tế. Không ghi nhận lượt này là QA Expo thành công. Đã đóng trình giả lập sau lượt thử.
- Giọng có sẵn phụ thuộc máy có cài giọng tiếng Việt. Âm sắc và khả năng hoạt động khi mất mạng tùy bộ đọc của máy. Khi không tìm được giọng Việt, hiển thị thông báo gọn và cho chọn lại giọng nam/nữ; không thay bằng giọng ngôn ngữ khác.
- Giọng thiết bị có phát/dừng/nghe lại từ đầu; không giả lập thanh tua theo giây khi bộ đọc không cung cấp dữ liệu tua đáng tin cậy. Hai giọng âm thanh của máy chủ giữ thanh tua hiện có.
- Các dịch vụ bên ngoài vẫn có thể lỗi hoặc chậm; không cam kết mọi thiết bị/mọi mạng đều phản hồi trong 1–3 giây hoặc không bao giờ lỗi.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: bố cục và tương tác Student/Quiz trên điện thoại.
  - Applied to: vùng làm bài thống nhất, đồng hồ gọn, bộ chọn ba giọng, điều hướng hoàn tất.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: vòng đời React, bất đồng bộ và hủy tác vụ.
  - Applied to: timer theo focus/AppState, bỏ kết quả cũ, dùng chung bộ phát/khung hỏi bài.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa tối thiểu và dùng lại thành phần có sẵn.
  - Applied to: thay bộ phát riêng của Quiz, bỏ giao diện phụ không cần thiết, không thêm thư viện.
- `computer-use`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/computer-use/26.1027.30824/skills/computer-use/SKILL.md`
  - Why selected: thử xác nhận giao diện trong Expo Go trên trình giả lập có sẵn.
  - Applied to: mở LDPlayer/Expo Go, thử kết nối, ghi nhận giới hạn nhập liệu và kết thúc lượt thử; không dùng làm bằng chứng kiểm thử thành công.
