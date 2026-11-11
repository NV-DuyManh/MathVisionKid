# Kiểm thử web bằng trình duyệt

Chạy từ root với Node theo `.nvmrc`:

```sh
npm ci
npx playwright install chromium
npm run test:browser
```

Linux cần thư viện hệ thống: `npx playwright install --with-deps chromium`. Xem báo cáo bằng `npm run test:browser:report`. Bộ test được khóa Playwright trong package-lock; không cần cấu hình tài khoản thật hay khởi động Docker/backend/Expo.

## Phạm vi

Playwright build và chạy Portal, Teacher, Admin thật ở chế độ production trong `.local-artifacts/browser/build/`. Browser thao tác bằng nhãn/role của giao diện; không chỉ tìm chuỗi trong source. Hai project Chromium dùng viewport desktop và mobile có touch, không phải kiểm thử thiết bị Android/iOS thật.

- Đăng nhập sai rồi nhập lại bằng bàn phím.
- Teacher/Admin: khách không vào được trang bảo vệ; SSO đổi ticket đúng một lần, xóa fragment và reload giữ phiên; đăng xuất xóa cả phiên app và Portal; phiên hết hạn không lặp refresh/chuyển trang.
- Vai trò Student bị chặn ở Admin; Teacher không được chuyển tiếp vào Admin qua Portal.
- Teacher: tạo bài tập theo lớp và phép toán đã chọn, xác minh payload và trang thu thập ảnh; danh sách lớp lỗi có thể thử lại.
- Teacher: mở danh sách học sinh theo lớp, lọc bài tập theo phân công lớp học.
- Admin: lọc vai trò/trạng thái/tìm kiếm và bỏ bộ lọc không gửi sai tham số.
- Student: chỉ kiểm tra yêu cầu điều hướng sang `/study/`, không thay trang đó bằng app giả hoặc tuyên bố đã test toàn bộ Student web.

`npx playwright test --config=playwright.student.config.mjs` export Expo Web thật và kiểm tra đăng nhập, tải lại deep link, máy tính bỏ túi và đổi đơn vị toán học bằng hợp đồng API giả lập. Nghiệm thu ảnh, xử lý bài và âm thanh thật dùng các lệnh opt-in bên dưới.

## Cách ly và bằng chứng

Build cấu hình các origin HTTPS `.test`; Playwright chuyển nội dung tĩnh tới ba preview server loopback cổng 43170–43172. Không dùng lại server đã chạy sẵn: nếu cổng bị chiếm, test dừng và không tắt tiến trình đó. Build nằm ngoài thư mục dist của app, không ghi đè web đang phục vụ local.

API trả fixture tổng hợp qua browser routing, gồm 401/403/503, tài khoản/vé dùng một lần và các lớp/bài tập giả. Không gọi API thật, social login, cloud OCR, LLM hay TTS; đường mạng không khai báo làm test thất bại. State và browser context được tách từng ca. Không nạp storageState/tài khoản học sinh hoặc secret thật.

Đây là kiểm thử hành vi frontend đối với hợp đồng API giả lập. Nó **không chứng minh** backend thực thi RBAC, OAuth, thu hồi token thật, accuracy OCR, phát âm hoặc latency nhà cung cấp. Backend tests và smoke môi trường thật vẫn cần riêng. Bộ hiện tại không chụp so sánh pixel hoặc tuyên bố phủ hết mọi màn hình.

CI chạy trong job `Web checks`; bất kỳ ca lỗi khiến job và `Quality gate` thất bại. Không retry để che lỗi chập chờn. Lỗi giữ HTML report, ảnh và trace dữ liệu tổng hợp trong artifact GitHub tối đa 7 ngày; local lưu `.local-artifacts/browser/` được ignore. Không upload build hoặc dữ liệu dự án thật.

Nguồn hướng dẫn: [Playwright webServer](https://playwright.dev/docs/test-webserver), [Playwright CI](https://playwright.dev/docs/ci-intro).

## Nghiệm thu bằng dịch vụ thật

Hai lệnh sau dùng backend và dịch vụ đang chạy, có thể tạo bản ghi và sử dụng quota OCR, tạo bài, giọng đọc. Chuẩn bị PostgreSQL, Redis và MinIO riêng cho kiểm thử, Spring chạy gateway FASTAPI và AI chạy `RUNTIME_MODE=MODEL` với model/provider được cấu hình. Portal và Teacher phải trỏ tới backend này. Lệnh yêu cầu `MATHVISION_LIVE_DISPOSABLE=true` và các URL localhost/127.0.0.1.

Đặt `MATHVISION_LIVE_API` tới backend có hậu tố `/api/v1`, `MATHVISION_LIVE_PORTAL` và `MATHVISION_LIVE_TEACHER` tới hai web đang chạy. Dùng `MATHVISION_LIVE_IMAGE` cho đường dẫn ảnh JPEG đã loại thông tin cá nhân và `MATHVISION_LIVE_OUTPUT` cho thư mục bằng chứng trong `.local-artifacts/`.

Teacher cần các biến `MATHVISION_LIVE_TEACHER_EMAIL`, `MATHVISION_LIVE_TEACHER_PASSWORD`, `MATHVISION_LIVE_ADMIN_EMAIL`, `MATHVISION_LIVE_ADMIN_PASSWORD`. Tài khoản Teacher phải có lớp và học sinh. Đặt `MATHVISION_LIVE_SCORE` trong khoảng 0–100 và `MATHVISION_LIVE_REASON` theo quyết định đã đối chiếu với ảnh. Lệnh đăng nhập qua Portal/SSO, tạo bài tập, xác nhận ảnh, upload bằng giao diện, so SHA-256 của JPEG thực gửi với ảnh backend trả, chờ callback AI, kiểm tra xoay ảnh, lưu điểm và thử tài khoản khác lớp. Ảnh chỉ có đề bài có thể nhận `OUT_OF_SCOPE` ở bộ chấm đặt tính dọc và được giáo viên quyết định điểm thủ công.

```sh
node scripts/test/live_teacher_review.mjs
```

Để kiểm tra đợt đầy đủ, đặt `MATHVISION_LIVE_BATCH_SIZE=30` và `MATHVISION_LIVE_BATCH_IMAGES` tới thư mục chứa 30 ảnh JPEG tổng hợp khác nhau, tên từ `worksheet-1.jpg` đến `worksheet-30.jpg`. Kịch bản bổ sung tài khoản tổng hợp qua Admin nếu danh sách lớp có dưới 30 học sinh, sau đó gán từng ảnh trên giao diện và đối chiếu SHA-256 theo học sinh. Chạy ở chế độ `FIXTURE` khi kiểm tra năng lực luồng xử lý cách ly. Số đo của chế độ này không dùng để nghiệm thu độ chính xác hoặc p95 OCR.

Student cần `MATHVISION_LIVE_STUDENT_EMAIL`, `MATHVISION_LIVE_STUDENT_PASSWORD` và `MATHVISION_LIVE_TRUTH` trỏ tới JSON do người kiểm tra đối chiếu với ảnh, gồm `problemText` và `answer`. Lệnh giữ nguyên các số và phân số khi so bản đọc, kiểm tra bắt buộc xác nhận đề, chuẩn bị bài, tải giọng nam/nữ/dự phòng qua API thật, giải các biểu thức bằng phép tính phân số độc lập và đối chiếu đáp số cuối. WAV được kiểm tra định dạng, thời lượng, âm lượng và hash riêng từng chế độ.

```sh
ai/runtime/.venv/Scripts/python.exe scripts/test/live_student_lesson.py
```

Các lệnh này không chạy mặc định trong PR CI. Bằng chứng lưu ảnh, WAV và kết quả kiểm tra, cần giữ ngoài Git. Kiểm tra WAV không tự chứng minh phát âm chính xác hoặc playback trên thiết bị. Báo cáo nghiệm thu cần ghi riêng quan sát trình duyệt, đối chiếu lời đọc và kết quả nhà cung cấp.
