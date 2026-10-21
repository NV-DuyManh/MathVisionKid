# Student — cập nhật 7 giao diện đã chọn

Ngày: 21/10/2026. Phạm vi: mã giao diện Student dùng chung cho web và ứng dụng. Đã sửa trong working tree; chưa commit, push hay triển khai môi trường dùng chung.

## Xem giao diện

- [Bảng đối chiếu 7 mẫu và ảnh chụp app](student-selected-ui-20261021/index.html)
- Chọn Điện thoại / Tablet / Laptop trong bảng. Bấm từng ảnh để xem ảnh chụp ở độ phân giải đầy đủ.
- Ảnh chụp sử dụng giao diện thật đã export từ dự án. Tài khoản, lịch sử, phản hồi API và sự kiện kết thúc giọng đọc là dữ liệu kiểm thử cô lập; không phải bằng chứng chấm AI trực tiếp hay thử trên thiết bị vật lý.

## Các phần đã thay

| Mẫu được chọn | Thay đổi trong mã thật |
|---|---|
| Bài học | Header nhỏ, các nút chọn lớp, danh sách chủ đề có minh họa và nền pastel. Mở từng bài để đọc đề, xem gợi ý, học từng bước hoặc chụp bài làm. Giữ các bài hiện có trong giáo trình. |
| Thành tích | Cúp vàng trên bục tím, lời động viên ngắn, hai số liệu nổi bật, thẻ tiến bộ và nút mở lịch sử tuần. Số bài, số bước và chuỗi ngày lấy từ lịch sử đang lưu, không tạo XP hoặc huy hiệu đã đạt giả. Laptop có cột thông tin tuần bên cạnh. |
| Của em / Bài đã lưu | Danh sách thu gọn với bản xem trước bằng chữ, ngày lưu, số bước; tab Bài đã lưu / Bài làm / Ghi chú lọc dữ liệu thật. Menu mở đúng bài và ghi chú tương ứng. |
| Một bước học tập | Thanh tiến trình xanh nhạt, một câu hỏi chính, giấy ô ly khi mở phép tính gợi ý, ô nhập kết quả và lựa chọn a/b nhỏ. Phép cộng/trừ số nguyên không âm được trình bày theo cột; biểu thức khác giữ nguyên cách viết toán. Không tự tính hay tiết lộ đáp số. |
| Nghe giảng | Minh họa Sao Nhỏ đeo tai nghe, cụm phát âm thanh tím, tiến độ theo ý đọc thực tế, nút xanh Em đã hiểu và nút viền Em chưa hiểu. Giọng/tốc độ và lời giảng dài được thu gọn. |
| Chọn chỗ còn vướng | Danh sách chọn một ý, trạng thái được chọn rõ, một nút Xem giải thích nhé!. Chọn dòng không gọi AI; chỉ gửi khi bấm nút. Câu trả lời ngắn và lời đọc dài bám bước học, phiên và lựa chọn. |
| Bài làm của em | Sau khi nhận xét xong, tập trung vào ảnh và kết quả thay vì giữ các thẻ xác nhận ở phía trên. Bài cần sửa có vùng bôi vàng ở ngay đầu; các dòng và gợi ý nằm trong phần chi tiết. Bài được xác nhận đúng có ảnh, lời khen ngắn và nút mở nhận xét chi tiết. |

## Những chức năng được giữ

- Kiểm tra đáp án, xác nhận nguồn và kết luận đúng/sai vẫn theo dịch vụ hiện có; không thay model hay logic chấm điểm.
- Hủy yêu cầu, bỏ kết quả cũ khi đổi tài khoản/ảnh/nội dung/phiên; giọng đọc dừng khi rời màn hoặc ứng dụng chuyển nền.
- Nhập phân số chính xác vẫn có ở mọi phép tính. Nút a/b chỉ thu gọn trình bày, không loại bỏ khả năng nhập tử/mẫu hoặc số âm.
- Video có lời đọc riêng cho bài học từ đợt trước vẫn hoạt động qua Xem thêm → Xem video bài này.
- Không lưu ảnh riêng tư vào lịch sử bài học. Hình thu nhỏ ở Của em được dựng từ chữ đã lưu; tab Bài làm dùng nội dung bài đã lưu bằng chữ.
- `privacy.tsx`, `crop.tsx`, `AppHeader.tsx`, `AppButton.tsx`, `theme.ts` có SHA-256 giữ nguyên so với baseline: [protected-after.json](student-selected-ui-20261021/protected-after.json).

## Kiểm tra đã thực hiện

| Kiểm tra | Kết quả |
|---|---|
| Toàn bộ Jest Student | **869/869 tests, 67/67 suites đạt** — [kết quả máy đọc](student-selected-ui-20261021/jest-results.json) |
| TypeScript | `npx tsc --noEmit` đạt |
| ESLint các file sản phẩm đã sửa | Đạt, không lỗi/cảnh báo |
| Web export | 32 route, kiểm tra địa chỉ dịch vụ đạt |
| Android và iOS export | Hai bundle Hermes xuất thành công, 77 asset |
| Browser responsive | **82 trạng thái**, rộng 320 / 390 / 768 / 1024 / 1440 px; không tràn ngang, không ảnh hỏng, không nút ngoài chiều ngang, không page error — [visual-qa.json](student-selected-ui-20261021/visual-qa.json) |
| Luồng ảnh | Dùng ảnh mẫu chủ sở hữu, đi qua chọn ảnh → xác nhận riêng tư → cắt ảnh → nhận diện/nhận xét bằng phản hồi kiểm thử cô lập |
| Review độc lập | Không còn phát hiện Critical/Important trong phạm vi thay đổi; đã rà cả phần tập trung kết quả bài làm và trình bày ảnh/dòng tách riêng |

Kiểm thử thêm cho việc chọn chỗ chưa hiểu rồi xác nhận, lọc tab theo nội dung lưu, chuyển tài khoản khi lịch sử chưa tải xong, biểu thức theo cột không sinh đáp số, ảnh bôi vàng và hàng chữ tách riêng, và quay lại đề từ màn nhận xét.

Giới hạn bằng chứng: chưa kiểm tra trên điện thoại/iPad vật lý, chưa nghe để xếp hạng chất âm trên từng máy, chưa chạy chấm ảnh bằng AI trực tiếp trong vòng kiểm tra UI này. Giọng tiếng Việt thực tế phụ thuộc giọng được cài trên thiết bị. Nút Dừng nghe dừng lời đọc; đây không phải chức năng tua âm thanh hoặc tạm dừng tiếp tục ở vị trí chính xác.

## Minh họa mới

- `apps/student-mobile/assets/illustrations/star-listening.png`
- `apps/student-mobile/assets/illustrations/achievement-trophy.png`
- Sinh bằng công cụ image_gen tích hợp với nền trong suốt; prompt và nguồn gốc: [SELECTED_UI_ASSETS.md](../apps/student-mobile/assets/illustrations/SELECTED_UI_ASSETS.md).

Đã đọc [tài liệu Expo phiên bản v57.0.0](https://docs.expo.dev/versions/v57.0.0/) trước khi sửa mã theo AGENTS.md. Không thêm dependency, không train model, không thay luồng che tên/cắt ảnh.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: triển khai 7 mẫu giao diện đã được chủ sở hữu chọn.
  - Applied to: bố cục điện thoại trước, mật độ, typography, nút và responsive; tìm hướng dẫn React Native về touch targets và Pressable.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: các màn và tương tác dùng React/React Native.
  - Applied to: tái sử dụng luồng tải dữ liệu, vòng đời giọng đọc/yêu cầu, tránh bổ sung tải nối tiếp và thư viện mới.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: cần thay bố cục mà giữ logic hiện có và diff có thể kiểm tra.
  - Applied to: dùng giáo trình/lịch sử hiện có, một chế độ trình bày nhỏ cho ảnh và dòng, không tạo cơ chế điểm thưởng hoặc kho ảnh mới.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md` (không có bản canonical trong dự án).
  - Why selected: miền minh họa raster riêng, cần hai tài sản hình ảnh cụ thể giống hướng mẫu; đây là skill bổ sung thứ tư cho miền độc lập.
  - Applied to: tạo Sao Nhỏ nghe giảng và cúp thành tích, lưu tài sản vào dự án và ghi prompt.
