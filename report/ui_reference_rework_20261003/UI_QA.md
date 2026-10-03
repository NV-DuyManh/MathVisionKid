# Kiểm tra giao diện Student Mobile — 2026-10-03

## Phạm vi bằng chứng

Chromium headless chạy Expo web development preview tại `http://localhost:8087`, ở các khung 375×812, 430×932 và 844×390; bật reduced motion. Đây là kiểm tra trình duyệt, không phải bằng chứng trên điện thoại vật lý.

Fixture người dùng không chứa email và chỉ giả lập HTTP `/me`, phát hiện dòng, gửi nhận dạng. Ảnh vở SVG và kết quả lỗi HTTP 500 là dữ liệu kiểm tra. Một lượt riêng đưa lịch sử giả lập vào store thật để kiểm tra bộ đếm; không dùng các bộ đếm này làm kết quả học sinh hoặc độ chính xác OCR thật.

Kịch bản kiểm tra: `scratch/ui-reference-browser-qa.cjs`. Kết quả máy đọc: [ui/browser-checks.json](ui/browser-checks.json).

## Kết quả

- Ba kích thước Trang chủ không tràn ngang; toàn bộ 8 hình minh họa tải thành công. Bốn tab và trạng thái `aria-selected` đúng khi chuyển giữa Trang chủ, Bài học, Thành tích, Của em.
- Sáu font Nunito được đăng ký. Trình duyệt tải font theo nhu cầu: Medium/Bold chưa dùng trên Trang chủ ở thời điểm đầu; kiểm tra gọi `document.fonts.load` để fetch cả sáu file thật và xác nhận trạng thái loaded. Chữ “Chào em!” có computed font `NunitoBlack`.
- Nút chính mở ba lựa chọn bài viết tay/thư viện/phép tính. Bài học chọn Lớp 2, mở bài giải tham khảo và chuyển sang chụp lời giải đúng chế độ.
- Thành tích với lịch sử trống hiển thị hai bộ đếm 0. Lịch sử tổng hợp riêng cho kết quả 2 bài, 5 dòng, chuỗi 2 ngày; loại bài mẫu và timestamp tương lai.
- Nút đóng và “Đã hiểu rồi” của hộp mẹo đều nằm trong màn hình, kể cả ngang 844×390. Nội dung dài cuộn bên trong; footer cố định.
- Thanh nhận dạng ngang có `aria-busy=true`, không có phần trăm, đồng hồ, thời lượng hay ETA giả. Ảnh đang nhận dạng vẫn hiện. Nút hủy nằm trong màn hình sau cuộn ở chế độ ngang.
- Sửa khung đầu từ y=100 thành y=116; hủy gửi, lỗi 500 và thử lại giữ nguyên cả 3 khung và tọa độ. Không có page error hay LogBox lỗi gửi nhận dạng xuất hiện. Hai console error HTTP 500 là phản hồi kiểm tra cố ý.

Development preview có thể hiện nút tia sét của công cụ phát triển ở góc dưới một số ảnh; đây là lớp UI của preview, không phải nội dung do các màn Student Mobile tạo. Không che hay chỉnh sửa screenshot để bỏ lớp này.

## Bằng chứng chính

- [Trang chủ 375×812](ui/home-375x812.png), [430×932](ui/home-430x932.png), [ngang 844×390](ui/home-844x390.png).
- [Thanh nhận dạng 375](ui/recognition-detection-bar-375.png), [430](ui/recognition-detection-bar-430x932.png), [ngang](ui/recognition-detection-bar-844x390.png).
- [Kiểm tra khung](ui/recognition-review-375.png), [giữ khung sau lỗi](ui/recognition-error-retry-375.png).
- [Mẹo ở màn ngang](ui/tips-844x390.png), [Bài học](ui/lessons-375x812.png), [Thành tích trống](ui/achievements-375x812.png), [Hồ sơ](ui/profile-375x812.png).
- [Bộ đếm từ lịch sử tổng hợp có kiểm soát](ui/achievements-synthetic-history-counters-375.png).

## Kiểm tra hồi quy có ý nghĩa

`RecognitionProgress.test.tsx` và `multilineResultPolling.test.tsx`: 2 suite, 8 test PASS. Kiểm tra reduced motion, giữ ảnh và hủy, không đếm giây; polling dừng sau 24 lượt dù payload/edit state đổi; không gửi GET chồng; gợi ý về muộn vẫn giữ nội dung người dùng đang sửa; đổi bài/unmount bỏ phản hồi cũ. Xác nhận gửi đúng snapshot đang hiển thị dù finalText cũ khác; chữ khác prediction được gửi dưới dạng sửa. Phản hồi lưu về chậm không xóa advisor đã hoàn tất; lỗi 400 phục hồi verdict chưa xác nhận nhưng giữ gợi ý mới; nội dung trống yêu cầu tự sửa.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Thiết kế và kiểm tra giao diện chờ nhận dạng phù hợp trẻ em.
  - Applied to: Lavender surface, hình bài đang xử lý, mascot, thanh ngang, bố cục portrait/landscape.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Component React Native, vòng đời effect và cập nhật bất đồng bộ.
  - Applied to: Cleanup animation, polling tuần tự có giới hạn, bảo toàn chỉnh sửa khi response về muộn.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Giữ thay đổi gọn và dùng cơ chế có sẵn.
  - Applied to: Một shared progress component, bỏ timer/stepper dư thừa, setTimeout tuần tự, không thêm thư viện ngoài package Expo đã được root chủ động chọn.
