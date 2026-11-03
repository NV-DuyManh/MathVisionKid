# Khôi phục đường vào app Student trên web local — 02/11/2026

## Nguyên nhân

Các nút “Bài học của tôi”, “Chụp bài ngay” và đăng nhập Student dẫn tới `/student`. Trang này kiểm tra vai trò với backend rồi chuyển tới `/study/`. Tuy nhiên thư mục Student đã export không có trong bản chạy local; middleware trả lại HTML Portal tại đường dẫn học tập. Trang giới thiệu có phiên đăng nhập nhưng người dùng không vào được app Student.

Bộ smoke production trước đây xác nhận điều hướng tới `/study/`, chưa kiểm tra app thực sự được phục vụ tại đó trong môi trường local. Đã bổ sung kiểm tra trực tiếp để phát hiện trường hợp này.

## Đã sửa trên E:\MathVisionKid

- Khi Vite Portal khởi động, chuẩn bị app web từ chính mã Student hiện tại, gắn tại `/study/`. Chỉ chế độ preview local dùng một trang đầu vào, giảm công việc prerender các trang riêng.
- Portal và Student giữ cùng origin và cùng thông tin phiên trong sessionStorage; Student vẫn xác minh `/me` với backend. Không truyền access/refresh token qua URL, không giả quyền học sinh.
- API của Student đi qua proxy cùng origin về backend được cấu hình. Kiểm tra cả tiền tố tùy chỉnh của backend.
- Theo dõi dấu phiên bản nguồn/cấu hình để tái dùng bản export còn đúng; thay đổi mã Student và khởi động lại Portal sẽ tạo bản mới. Expo development app riêng vẫn hoạt động như trước. Không thay cấu hình Android/iOS hoặc đầu ra web triển khai khi không bật cờ preview local.
- Route học tập, Quiz và liên kết sâu trả app Student. File JavaScript bị thiếu trả 404; không trả HTML Portal thay cho JavaScript. Chặn đường dẫn ra ngoài thư mục export và tắt cache HTTP cho preview.
- File sinh tự động nằm ngoài Git. Launcher cho phép thêm thời gian chuẩn bị ở lần đầu chưa có preview; các lượt có cache giữ thời gian chờ cũ.

## Kiểm tra

| Kiểm tra | Kết quả |
|---|---|
| Portal config/auth/logout | 31/31 qua |
| Cấu hình export web và bảo toàn native/deployment | 5/5 qua |
| Khôi phục phiên Student web, phân quyền và đăng xuất | 14/14 qua |
| Live local Student entry/assets/API/cache restart | 3/3 qua |
| Portal production build/smoke | Build qua; 2/2 smoke qua |
| Launcher | 6/6 qua |
| Portal lint, TypeScript, diff whitespace | Qua |

Lượt live lấy `/study/`, `/study/learning/math-guide`, `/study/quiz`, các script được HTML tham chiếu và favicon. Xác nhận app đọc khóa phiên Portal; API proxy đăng nhập Student và `/me` trả 200, đúng vai trò và active; không có token bị 401. Phiên tạo để kiểm tra được đăng xuất trong finally.

Khởi tạo một Vite server mới trên cổng tạm với cùng nguồn giữ nguyên thời điểm ghi index, trả đúng app và đóng lại thành công; lượt kiểm tra này mất khoảng 202 ms. Đây là thời gian kiểm tra server/cache, không phải số đo từ bấm nút tới hiển thị UI trên máy người dùng. Một lượt export đã có Metro cache mất 7,3 giây; khởi tạo lạnh có thể lâu hơn.

URL để thử ngay: `http://localhost:5172/study/`. Người đã đăng nhập Portal có thể dùng nút “Bài học của tôi”; người chưa đăng nhập vẫn cần xác thực. Không công bố đã bấm thử bằng Cốc Cốc hoặc kiểm tra trên Android thật. Không commit/push/deploy.

## Hậu kiểm sau ảnh “Unmatched Route”

Kiểm tra HTTP trước đó chưa đủ: HTML và script có thể tải được nhưng router vẫn không nhận `/study/`. Đã tái hiện đúng lỗi từ mã export đang phục vụ bằng JSDOM, với `Unmatched Route` trong nội dung trang và không có lỗi JavaScript. Đây là thiếu sót của phạm vi kiểm tra trước.

Nguyên nhân: hàm `stripBaseUrl` của Expo Router đang cài chỉ bỏ base URL khi `NODE_ENV` khác `development`. Dùng `expo export --dev` để gắn dưới `/study` vì thế không phù hợp. Đã bỏ `--dev`; bản local vẫn dùng một entry web, API cùng origin `/api/v1` và đúng mã Student. Web API resolver chỉ thêm ngoại lệ cho đường dẫn cùng origin chính xác `/api/v1`; địa chỉ bên ngoài không an toàn và đường dẫn chứa query khác vẫn bị từ chối. Không thay cấu hình API native.

Sau khi đổi bản xuất, phát hiện thêm danh sách public asset của Vite có thể giữ tên file cũ khi không theo dõi thư mục sinh tự động. Đã đưa preview ra `infra/local-runtime/student-web-preview`, phục vụ file trực tiếp với đúng Content-Type và kiểm tra phạm vi đường dẫn. Bản này không bị chép vào đầu ra Portal production. Cache cũ được lưu tại `infra/local-runtime/legacy-student-web-preview`, không xóa mã nguồn hay demoUI. Dấu cache nay tính cả cấu hình Vite.

Kết quả mới:

- 4/4 test live local qua. Test bổ sung thực thi chính HTML, React, Expo Router và script export với backend thật; chỉ cung cấp readiness font/ảnh và các API trình duyệt mà JSDOM thiếu. Không mock router hay màn hình ứng dụng.
- Xác nhận root hiện “Tiện ích nhanh”, thao tác tab Bài học chuyển tới `/study/lessons` và hiện danh sách học; truy cập trực tiếp Bài học/Quiz đều hiện đúng màn hình, không có `Unmatched Route` hoặc exception JS.
- 31/31 test cấu hình/đăng nhập Portal, 5/5 cấu hình export/API, TypeScript Student và Portal, lint Portal qua. Build Portal và 2/2 smoke production qua; xác nhận `dist/study` không chứa preview local.
- Một lượt tạo bản preview mới đã có cache mất 8,6 giây; khởi động server mới dùng lại preview không export lại. Đây không phải thời gian mở app trên điện thoại.

Đây là kiểm thử render và điều hướng trong JSDOM, không phải bằng chứng đã bấm trên Cốc Cốc hay Android thật. Mã và bản local đã cập nhật, chưa commit/push/deploy.

## Skills Applied (toàn bộ lượt sửa và hậu kiểm)

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Sửa đường phục vụ bị thiếu tại nơi dùng chung thay vì nhân đôi giao diện hoặc thêm cơ chế xác thực riêng.
  - Applied to: Middleware local, export có cache, proxy API, launcher và kiểm thử live.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Giữ vòng đời/phiên của app React dùng chung, tránh tải một app khác tại route học tập.
  - Applied to: Tích hợp Portal với Student, cấu hình xuất web và kiểm tra khôi phục phiên/phân quyền.
