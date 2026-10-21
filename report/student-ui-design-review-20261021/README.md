# Bộ 5 bảng thiết kế Student web — 21/10/2026

Phạm vi đã được chủ dự án xác nhận: **chỉ toàn bộ web app học sinh (Student)**. Bộ này dùng để chọn hướng giao diện, chưa thay giao diện ứng dụng.

Mở `index.html` bằng trình duyệt để xem cả 5 bảng. Chọn một bảng, bấm vào bất kỳ thẻ màn hình nào để phóng to. Trong bản đề xuất, chuyển giữa điện thoại, tablet/iPad và laptop; có thể bấm các nút để thử đường đi của bản thiết kế. Các ảnh bảng đầy đủ nằm trong `boards/`.

| Bảng | Nội dung | Tệp ảnh đầy đủ |
|---|---|---|
| 1 | Giao diện hiện tại | `boards/board-0-full.png` |
| 2 | Tím tinh gọn | `boards/board-1-full.png` |
| 3 | Vở học ấm áp | `boards/board-2-full.png` |
| 4 | Không gian học xanh | `boards/board-3-full.png` |
| 5 | Hành trình Sao nhỏ | `boards/board-4-full.png` |

## Phạm vi giao diện

`catalog.json` liệt kê 46 khung màn hình/trạng thái chính, bao phủ các trang Student và hộp thoại liên quan:

- Đăng nhập, trang chủ, kho bài lớp 1–5, bài luyện tập, thành tích, góc học tập và bài đã lưu.
- Chụp/chọn ảnh, mẹo chụp, che thông tin, cắt/căn thẳng, xem lại và xử lý ảnh.
- Chọn dòng, chỉnh vùng nhiều dòng, kết quả đọc chữ và xác nhận ký hiệu.
- Xác nhận/chỉnh đề, chuẩn bị riêng, hiểu đề, tóm tắt, giải từng bước và gợi ý.
- Hình phân số, lời giảng, hai lựa chọn giọng, hỏi bằng chữ/giọng, trả lời theo bước, công cụ và máy tính.
- Nhận xét bài làm, vùng cần sửa, động viên bài đúng, bài giải hoàn chỉnh và lưu để học tiếp.
- Ảnh chưa rõ, dạng bài chưa hỗ trợ, chưa đủ cơ sở kết luận, kết nối gián đoạn, quyền riêng tư, đăng xuất và lịch sử nhận dạng.

Các tệp điều hướng, bố cục kỹ thuật và công cụ nội bộ không được trình bày như một trang học sinh độc lập. Danh mục bao phủ trang và trạng thái chính, không liệt kê mọi tổ hợp dữ liệu/lỗi có thể xảy ra.

## Cách đọc bảng hiện tại

- Bảng 1 sử dụng ảnh chụp frontend đang deploy, không dùng AI vẽ lại giao diện hiện trạng.
- Trang chủ được chụp ở ba kích thước trình duyệt. Các khung hiện trạng còn lại chủ yếu là ảnh ở kích thước điện thoại; nơi có ảnh laptop thì có thể mở ở bộ chọn thiết bị. Không kéo giãn ảnh điện thoại để giả làm ảnh tablet/laptop.
- Một số trạng thái bài học, phản hồi toán và lỗi mạng được mở bằng phản hồi mẫu trong trình duyệt. Đây là **giao diện thật với dữ liệu mẫu**, không chứng minh AI đã suy luận/chấm đúng hoặc đã thử trên điện thoại thật.
- Khi mở trực tiếp một trang mà chưa có ảnh/bài làm, frontend có thể hiển thị trạng thái thiếu đầu vào. Những ảnh đó được giữ đúng hiện trạng; không dùng chúng để kết luận tính năng bị lỗi.
- `current-captures.json` ghi nguồn và điều kiện chụp; `current-data.js` cung cấp nhãn nguồn trong bảng xem.

## Điểm chung của bốn đề xuất

1. Giữ bộ minh họa tiện ích, biểu tượng điều hướng và linh vật đã được chọn.
2. Điện thoại dùng điều hướng dưới; tablet/laptop dùng thanh dọc gọn, có trạng thái thu gọn trên laptop.
3. Khung nội dung có chiều rộng giới hạn. Tablet đổi bố cục theo không gian, không kéo giãn bố cục điện thoại.
4. Khi học, ưu tiên một việc chính. Nghe giảng, hỏi bài, hình phân số và công cụ được mở riêng khi cần.
5. Phần chữ ngắn, rõ; phần nghe có thể giải thích dài hơn. Giọng thực tế phụ thuộc thiết bị, tối đa hai lựa chọn phù hợp.
6. Luồng hỏi giọng nói giữ nguyên yêu cầu xin phép, kiểm tra chữ sau nhận dạng và tự bấm gửi khi triển khai thật.
7. Dữ liệu tiến bộ, bài đã lưu, bài viết và phản hồi trong đề xuất đều là minh họa. Bản thiết kế không gọi backend, không chấm bài thật và không thu âm thật.

Các ảnh AI được dùng ở giai đoạn khám phá phong cách. Bộ bảng chi tiết và mẫu tương tác được dựng bằng HTML/CSS với chữ tiếng Việt và nội dung toán xác định, là bản dùng để so sánh/chọn. Không lấy nội dung nhỏ trong ảnh khám phá AI làm đặc tả chức năng.

## Kiểm tra

- `visual-qa.json`: 4 phương án × 46 khung × 3 kích thước = **552 lượt kiểm tra bố cục**, tại 390, 768 và 1440 px.
- Kiểm tra tràn ngang, ảnh tải được và lỗi JavaScript.
- `gallery-qa.json`: 5 bảng × 46 thẻ, tệp ảnh, mở khung xem, đổi thiết bị, điều hướng thu gọn, tương tác phân số, trạng thái câu trả lời mẫu và giới hạn hai giọng.
- Đây là kiểm tra trình duyệt của bộ thiết kế. Không phải kiểm thử ứng dụng native, chất lượng giọng thật hoặc độ chính xác mô hình.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: thiết kế toàn bộ trải nghiệm Student web trên nhiều kích thước.
  - Applied to: phân cấp thông tin, một việc chính mỗi màn hình, bố cục responsive và kiểm tra hiển thị.
- `design`
  - SKILL.md: `.agents/skills/design/SKILL.md`
  - Why selected: trình bày bộ phương án thống nhất để so sánh.
  - Applied to: bốn hướng mỹ thuật, bố cục bảng, giữ bộ tài sản nhận diện đã duyệt.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: khám phá hình ảnh của bốn hướng thiết kế.
  - Applied to: ảnh định hướng phong cách, sử dụng công cụ image generation tích hợp; không dùng CLI/API trả phí.

Chưa thay mã sản phẩm, chưa deploy giao diện mới, chưa commit/push và chưa huấn luyện mô hình.
