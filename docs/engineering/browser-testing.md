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
- Admin: lọc vai trò/trạng thái/tìm kiếm và bỏ bộ lọc không gửi sai tham số.
- Student: chỉ kiểm tra yêu cầu điều hướng sang `/study/`, không thay trang đó bằng app giả hoặc tuyên bố đã test toàn bộ Student web.

## Cách ly và bằng chứng

Build cấu hình các origin HTTPS `.test`; Playwright chuyển nội dung tĩnh tới ba preview server loopback cổng 43170–43172. Không dùng lại server đã chạy sẵn: nếu cổng bị chiếm, test dừng và không tắt tiến trình đó. Build nằm ngoài thư mục dist của app, không ghi đè web đang phục vụ local.

API trả fixture tổng hợp qua browser routing, gồm 401/403/503, tài khoản/vé dùng một lần và các lớp/bài tập giả. Không gọi API thật, social login, cloud OCR, LLM hay TTS; đường mạng không khai báo làm test thất bại. State và browser context được tách từng ca. Không nạp storageState/tài khoản học sinh hoặc secret thật.

Đây là kiểm thử hành vi frontend đối với hợp đồng API giả lập. Nó **không chứng minh** backend thực thi RBAC, OAuth, thu hồi token thật, accuracy OCR, phát âm hoặc latency nhà cung cấp. Backend tests và smoke môi trường thật vẫn cần riêng. Bộ hiện tại không chụp so sánh pixel hoặc tuyên bố phủ hết mọi màn hình.

CI chạy trong job `Web checks`; bất kỳ ca lỗi khiến job và `Quality gate` thất bại. Không retry để che lỗi chập chờn. Lỗi giữ HTML report, ảnh và trace dữ liệu tổng hợp trong artifact GitHub tối đa 7 ngày; local lưu `.local-artifacts/browser/` được ignore. Không upload build hoặc dữ liệu dự án thật.

Nguồn hướng dẫn: [Playwright webServer](https://playwright.dev/docs/test-webserver), [Playwright CI](https://playwright.dev/docs/ci-intro).
