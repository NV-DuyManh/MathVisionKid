# Báo cáo xử lý lỗi 1–8 trên Student Web

Ngày đối chiếu 20/11/2026. Dự án MathVisionKid, nhánh `bugfix/reported-student-web-bugs`, commit nền `5ab0124d`. Các thay đổi hiện ở thư mục chính. Nguồn đối chiếu gồm báo cáo Word ngày 18/11/2026, video, mã nguồn và các ca kiểm thử local.

## Bảng theo dõi

| # | Lỗi và mức ưu tiên | Nguyên nhân hoặc bằng chứng | Cách sửa, hướng xử lý và trạng thái |
|---|---|---|---|
| 1 | F5 làm mất ảnh và vùng che · P1 | Ảnh nguồn và vùng che đang vẽ chỉ có trong bộ nhớ của màn hình. F5 tạo lại màn hình. | **Đã sửa và xác minh.** Lưu tạm ảnh và vùng che theo phiên và tab tối đa 30 giây. Khôi phục trong hạn luôn yêu cầu xác nhận riêng tư lại. Sau hạn, F5 về Camera cùng chế độ. Chrome và Spring Boot local đã kiểm tra cả hai trường hợp. |
| 2 | Tab mới yêu cầu đăng nhập lại, đăng xuất không đồng bộ · P1 | Cơ chế cũ lưu phiên riêng theo tab. Tín hiệu đồng bộ trước đó không phục hồi đăng nhập cho tab mới. | **Đã sửa và xác minh.** Phiên Web do Spring Boot quản lý, dùng cookie HttpOnly và mã phiên dùng chung giữa các tab cùng origin. Chrome desktop và Pixel 7 giả lập đã mở đúng hồ sơ và kiểm tra đăng xuất đa tab. Mobile native giữ SecureStore, luân chuyển refresh token và có thể thu hồi refresh token khi access token hết hạn. |
| 3 | Chọn ảnh qua màn trung gian, F5 mất ảnh tại màn cắt · P1 | Luồng cũ đi qua gallery riêng và ảnh trên Web phụ thuộc vào dữ liệu tạm. | **Bản xử lý đã có trên develop và được kiểm tra lại.** Camera mở hộp thoại tệp trực tiếp. Ảnh đã che và vùng cắt, số lần xoay, góc căn thẳng được khôi phục từ bản lưu trình duyệt. Đã kiểm tra trên hai kích thước màn hình. |
| 4 | Giọng thiết bị lỗi, nút giọng Việt dự phòng cũng lỗi · P1 | Nút dự phòng gửi yêu cầu TTS offline tới FastAPI. Trên máy local, cả trình duyệt và backend đều dùng cùng Windows thiếu giọng vi-VN. | **Đã sửa và xác minh nút chuyển giọng.** Nút dự phòng chuyển sang Nam hoặc Nữ trực tuyến đã chọn gần nhất, mặc định Nam. Chrome desktop và Pixel 7 giả lập đã phát được qua backend và bộ đếm chạy. Giọng thiết bị cần Windows có giọng Việt; hạng mục cài giọng được tạm gác theo yêu cầu. |
| 5 | F5 khi nộp ảnh bị lặp lỗi trong báo cáo gốc. F5 sau khi đọc ảnh hoặc trong Math Guide làm mất bước đang học · P1, báo cáo gốc xếp nghiêm trọng | Ở màn nộp bài, ảnh trong bộ nhớ mất sau F5. Thử lại với cùng tham chiếu trống gây lặp lỗi. Ở Math Guide, kết quả đọc chỉ nằm trong state và bản nháp bị xóa khi đọc xong. Cơ chế tải tiến độ cũ bỏ qua bài từ ảnh vì đề ban đầu trống. | **Đã sửa và xác minh trên Student Web local.** Luồng nộp bài đã có lối chọn ảnh khi thiếu dữ liệu, và truy vấn lại kết quả bằng mã bài nộp đã nhận. Lần này bổ sung khôi phục Math Guide theo tài khoản, phiên, tab và nguồn bài. Khi còn phiên học, lấy bước chính thức từ backend và khôi phục dữ liệu đang nhập. Khi đọc ảnh bị gián đoạn, học sinh chủ động chọn đọc tiếp hoặc nhập chữ. |
| 6 | Lỗi cái chó gì | Chế độ giọng Việt dự phòng khóa bộ chọn giọng. | **Người dùng đã xác nhận OK.** Bài học có sẵn trên Student Web mở với Giọng thiết bị. Giọng nam và Giọng nữ luôn có thể chọn trực tiếp. |
| 7 | Lỗi cái chó gì | — | **Người dùng đã xác nhận OK.** |
| 8 | Lỗi cái chó gì | — | **Người dùng đã xác nhận OK.** |

## Ghi chú nghiệm thu

- Với lỗi 5, người dùng đã duyệt khôi phục đúng màn từ lúc đọc ảnh thành công đến xem kết quả. Các hộp thoại máy tính, nghe giảng và vị trí cuộn có thể đặt lại.
- Ảnh chưa xác nhận vẫn theo giới hạn 30 giây của lỗi 1. Bản khôi phục Math Guide không chứa ảnh gốc hay URL Blob. Ảnh đã che giữ trong kho ảnh trình duyệt, với hạn thông thường 30 phút. Nếu ảnh hết hạn, phần chữ vẫn có thể khôi phục trong cùng phiên và tab. Nếu phiên học backend hết hạn, đề và bài làm dạng chữ được giữ để bắt đầu lại.
- Nếu dịch vụ đọc ảnh trả 503 TUTOR_CONFIGURATION, kiểm tra cấu hình Groq/Gemini của FastAPI. Đó là tình trạng runtime từng được xác nhận riêng trên localhost.
- Kết quả Chrome giả lập mobile không chứng minh hành vi của một thiết bị vật lý. Hiện trạng và kết quả kiểm thử tại đây là local.

## Kiểm thử bổ sung cho lỗi 5

- Trước khi sửa, Chrome với phản hồi inspect thành công đã tái hiện dữ liệu biến mất sau F5, với đúng một yêu cầu inspect.
- Chrome DevTools MCP trên `localhost:5172`, đăng nhập bằng tài khoản thử local, mở bài tam giác, xác nhận đề, bắt đầu và tải lại. Desktop và mobile web giả lập đều hiển thị đúng bước “Nhận biết dữ kiện”. Kiểm tra Network trên mobile web cho thấy API tải lại phiên học trả HTTP 200. Spring Boot và FastAPI local hoạt động, với OCR chạy ở chế độ fixture.
- Playwright + Chrome đạt 12/12 lượt trên desktop và mobile web giả lập, dùng dữ liệu kiểm thử. Các ca gồm ảnh đã đọc và bản xem trước, đọc dở có thể tiếp tục hoặc nhập chữ, bước đã xem, màn tóm tắt, phân số đang nhập, gợi ý đang mở, đáp số cuối, kết quả “Bài đã làm” và bài nộp khôi phục bằng GET. Các ca ảnh đối chiếu số yêu cầu để phát hiện đọc, chấm hoặc tải ảnh lên lặp lại.
- `npx tsc --noEmit -p apps/student-mobile/tsconfig.json` và ESLint trên các tệp TypeScript sửa cho lỗi 5 đã qua. Thêm 129 kiểm thử Jest trong hai bộ liên quan và 17 kiểm thử hợp đồng bằng `npm run test:contracts`, tất cả qua.
- `scripts/start-all.bat` xác nhận `READY_FOR_FULL_DEMO`; Portal đã xuất lại Student Web. `git diff --check` qua. Báo cáo Markdown là tệp local dưới `report/` và thuộc đường dẫn Git bỏ qua.
- Thay đổi tập trung ở `crop.tsx`, `math-guide.tsx`, `mathGuideCheckpoint.ts`, `StudentWorkReview.tsx`, phần dọn bản nháp của xác thực Web, và hai bộ hồi quy ảnh và bài học. Lần kiểm tra này chưa đánh giá độ chính xác đọc ảnh của nhà cung cấp, thời gian tải trên thiết bị thật hoặc xác minh hành vi trên production.

## Skills Applied

- `systematic-debugging`, `brainstorming`, `writing-plans`, `test-driven-development`, `verification-before-completion`
  - SKILL.md: từng thư mục cùng tên dưới `C:/Users/LOC/.codex/plugins/cache/openai-curated-remote/superpowers/7.0.1/skills`.
  - Lý do và áp dụng: tái hiện lỗi, lập phạm vi lưu/khôi phục, thêm ca hồi quy và kiểm tra kết quả.
- `mathvision-quality`, `mathvision-review`, `ponytail`
  - SKILL.md: từng thư mục cùng tên dưới `E:/DuyTan/C1SE/Project/MathVisionKid/.agents/skills`.
  - Lý do và áp dụng: kiểm thử theo từng bước, bảo vệ bản nháp/phiên và tái sử dụng bộ lưu ảnh cùng API khôi phục hiện có.

- `vercel-react-best-practices`
  - SKILL.md: `E:/DuyTan/C1SE/Project/MathVisionKid/.agents/skills/react-best-practices/SKILL.md`.
  - Lý do và áp dụng: rà soát vòng đời đọc ảnh và khôi phục trạng thái của màn Math Guide.
- `docx`
  - SKILL.md: `E:/DuyTan/C1SE/Project/MathVisionKid/.agents/skills/docx/SKILL.md`.
  - Lý do và áp dụng: đối chiếu tám lỗi với nội dung báo cáo Word gốc.
