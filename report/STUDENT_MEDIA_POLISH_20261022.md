# Hoàn thiện UI nghe, hỏi bài và video — 22/10/2026

[Xem ảnh trước/sau và các màn thật](student-media-polish-20261022/index.html).

## Những điểm tìm thấy và đã sửa

| Điểm chưa ổn | Thay đổi |
|---|---|
| Nút tốc độ chiếm chỗ tiêu đề, hướng dẫn xuống ba dòng trên màn 320 px | Chuyển tốc độ xuống hàng phụ cạnh nút Từ đầu, rút gọn câu hướng dẫn |
| Điều khiển phụ mờ, khó phân biệt tiến/lùi | Tăng tương phản thanh chưa phát và chữ phụ; ghi rõ −10s/+10s, bản ghi dùng −5s/+5s |
| Trạng thái tải trông giống các nút hỏng | Có chỉ báo đang tải và ngữ nghĩa busy; mọi nút phụ cũng thể hiện disabled |
| Âm thanh tải thành công nhưng không giải mã được thì không có cách tải lại | Đưa lỗi về thẻ thử lại, dọn file cũ và tải file mới; phần chữ tiếp tục dùng được |
| Thẻ lỗi chiếm chỗ với cả bộ điều khiển mờ | Thay bằng thẻ thông báo ngắn và một nút thử lại |
| Đổi tốc độ bị thiết bị từ chối có thể ném lỗi ra UI | Giữ tốc độ cũ và báo dễ hiểu |
| Đang kéo video rồi chuyển nền/đổi màn có thể tự phát khi thả | Xóa trạng thái phát trước thao tác kéo khi ứng dụng mất hoạt động |
| Hai nút Đã hiểu / Chưa hiểu lệch kích thước | Hai nút cân nhau, nút đã hiểu màu xanh nhẹ, có dấu và chữ rõ |
| Lựa chọn chỗ chưa hiểu dùng vai trò radio nhưng chưa có đầy đủ hành vi bàn phím của radio | Dùng nút lựa chọn có trạng thái pressed/selected và dấu chọn; Tab, Enter/Space sử dụng được |
| Hộp thoại chưa có tên cho trình đọc màn hình | Đặt tên theo tiêu đề; dùng cơ chế giữ/phục hồi tiêu điểm và Escape sẵn có của Modal |
| Lề và chiều cao tối thiểu dư trên màn nhỏ | Lề 16 px ở màn dưới 360 px; giảm chiều cao tối thiểu, giữ chiều rộng tối đa 640 px trên màn lớn |

Giữ kiểu màu tím sáng của dự án, không thêm mục điều khiển hoặc tính năng mới vào luồng học. Giữ việc bấm mic ghi ngay, sửa chữ trước khi gửi, không tự phát audio khi mở. Màn che tên/cắt ảnh và các thành phần được bảo vệ giữ nguyên.

## Kiểm chứng

- Student: **880 kiểm thử / 71 bộ đạt**. Năm trường hợp mới đã chạy thất bại trước khi sửa: chuyển nền/blur trong lúc tua video, lỗi giải mã audio, thử lại file lỗi và từ chối đổi tốc độ. Nhật ký: `student-media-polish-20261022/student-tests.log`.
- TypeScript và ESLint cho bảy file sản phẩm thay đổi đạt.
- Web export 32 route và Android/iOS Hermes export thành công. Cấu hình QA chỉ đặt trong tiến trình build, không sửa cấu hình sản phẩm hoặc triển khai lên môi trường thật. Lượt build đầu thiếu cấu hình dịch vụ và đã được chạy lại với cấu hình QA hợp lệ; không nới kiểm tra cấu hình sản phẩm.
- Trình duyệt: **37 ảnh**, **30 lần kéo thời gian thật**, năm kích thước 320×740, 390×844, 768×1024, 1440×1000, 844×390. Không tràn ngang, ảnh hỏng, nút vượt mép ngang hoặc lỗi JavaScript. Có trạng thái tải chậm, tải lỗi, thử lại và đọc lời giảng chữ.
- Stress chữ lớn 1,6× trong trình duyệt: không tràn ngang. Đây không phải bằng chứng Dynamic Type trên thiết bị native.
- Bàn phím: hộp thoại có tên; 16 lượt Tab giữ trong hộp thoại và có viền focus; Home/End tua thật, Enter đổi tốc độ, Space chọn chỗ vướng; Escape đóng và phục hồi tiêu điểm về nút mở. Không có `aria-controls` trỏ đến phần tử không tồn tại.
- Tương phản các cặp đã sửa: chữ phụ 5,53:1, đường thanh tua 3,05:1, chữ Đã hiểu 6,06:1, chữ Chưa hiểu 6,20:1 và nội dung thẻ lỗi 7,18:1; xem `student-media-polish-20261022/contrast.json`. Đây là kiểm tra các cặp cụ thể, không phải chứng nhận toàn ứng dụng.
- Audio/video dùng file thật từ lượt kiểm tra trước. Auth, nội dung bài học/câu trả lời/chuyển chữ là fixture, mic giả lập Chromium. Không tuyên bố đã kiểm thử trên điện thoại vật lý hay xác nhận chất lượng AI online.
- SHA-256 của năm file bảo vệ tiếp tục không đổi; xem `student-media-polish-20261022/protected-after.json`.

Lệnh chính: `npm test -- --runInBand --silent --json --outputFile=../../report/student-media-polish-20261022/student-tests.json`, `npx tsc --noEmit`, `npx eslint ...`, `npx expo export --platform web`, `npx expo export --platform android --platform ios`, `node report/student-media-polish-20261022/visual-qa.cjs`, `node report/student-media-polish-20261022/keyboard-qa.cjs`.

Đã đọc tài liệu đúng [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/), [audio](https://docs.expo.dev/versions/v57.0.0/sdk/audio/) và [slider](https://docs.expo.dev/versions/v57.0.0/sdk/slider/) trước khi sửa. Không thêm dependency trong lượt hoàn thiện này.

## Trạng thái

Đã sửa trên nhánh `codex/student-voice-replay-20261022`. Không commit, push, deploy hoặc train trong lượt này. Các thay đổi backend WAV của lượt trước vẫn cần phát hành cùng Student để phần tua giọng hoạt động trên môi trường thật. Giọng offline có thể khác nhau giữa máy Windows và máy chủ Linux, như báo cáo trước đã ghi.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: rà soát bố cục và tương tác trình phát trên điện thoại nhỏ, tablet và laptop.
  - Applied to: tách hàng tốc độ, khoảng cách thao tác, thẻ tải/lỗi và kiểm tra ảnh trước/sau.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: trạng thái phát, callback lỗi, vòng đời file và render React Native/web.
  - Applied to: callback ổn định, dọn file khi thử lại, giữ trạng thái phát/dừng và xử lý đổi tốc độ lỗi.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: điều khiển media, lựa chọn và hộp thoại phải dùng được bằng bàn phím/trình đọc màn hình.
  - Applied to: tên dialog, trạng thái disabled/busy/pressed, dấu chọn, tương phản, focus và quan hệ phần chữ mở rộng.

Đã dùng systematic-debugging, test-driven-development và verification-before-completion làm quy trình hỗ trợ. Tìm kiếm skill cho `font scaling` không trả kết quả phù hợp sau một lần thu hẹp; kiểm tra chữ lớn dùng phép stress trình duyệt và không được coi là xác nhận native.
