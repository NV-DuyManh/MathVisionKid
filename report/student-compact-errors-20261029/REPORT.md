# Giao diện lỗi Student gọn hơn — 29/10/2026

Đã áp dụng trực tiếp vào mã nguồn tại `E:/MathVisionKid`, nhánh `codex/student-learning-voice-polish-20261029`. Chưa commit hoặc push trong lượt này.

## Thay đổi

- Lỗi giọng đọc: một thẻ nhỏ, tiêu đề và lời nhắc ngắn, hai nút **Thử lại** / **Giọng thiết bị**. Bỏ nút giọng dự phòng thứ ba khỏi giao diện này. Vẫn có thể mở lời giảng bằng chữ.
- Lỗi giọng trên thiết bị: cùng kiểu thẻ, cho thử lại hoặc quay về giọng chính. Không tự chuyển sang tiếng Anh, không tự phát tiếng. Giọng thiết bị cần máy có giọng Việt; âm sắc tùy thiết bị.
- Bản ghi lỗi mở tệp: thay bộ phát bị vô hiệu hóa bằng thông báo và nút tải lại. Nút này mở lại cùng tệp, không xóa bản ghi hoặc tự phát.
- Hỏi bài, chuyển lời nói thành chữ, mở mic: thông báo gần phần nhập; thử lại đúng bản ghi/câu hỏi, hoặc đưa con trỏ về phần gõ. Nội dung câu hỏi được giữ.
- Tạo hướng dẫn, nhận xét bài làm, nhận diện dòng chữ, xử lý ảnh, bài đã lưu và tải hình lúc mở ứng dụng: dùng cùng mẫu thông báo với hành động phù hợp. Nhận diện dòng chữ thử lại trên cùng ảnh đã cắt thay vì đưa về trang chủ như trước.
- Thông báo có vùng đọc cho trình đọc màn hình; nút cao tối thiểu 44, có viền khi tập trung bằng bàn phím. Chữ được phép xuống dòng thay vì bị cắt.
- Dọn các kiểu trang trí lỗi cũ không còn sử dụng. Không thêm thư viện.

Phần đáp án đúng/sai giữ nguyên hành vi đã sửa trước đó: giữ câu hỏi, các lựa chọn và đáp án đã chọn để đối chiếu; đúng thì chờ học sinh bấm tiếp tục.

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Toàn bộ kiểm thử Student | **94 bộ, 1.115 kiểm thử qua** — `all-student-tests.json` |
| TypeScript | Qua |
| Lint | 0 lỗi; còn 2 cảnh báo có sẵn tại `cropRotation.web.ts` |
| Xuất Android | Thành công — `android-export/metadata.json` |
| Giao diện thật trên web | Qua ở chiều rộng 320, 390, 768, 1440 — `visual-qa.json` |
| Thử lại giọng | Sau trạng thái lỗi có thể tải và phát/tạm dừng WAV |
| Thử lại hỏi bài | Gửi lại nguyên câu hỏi; nhập liệu vẫn giữ; nút sửa đưa con trỏ đúng ô |
| Trường hợp thiết bị thiếu giọng Việt | Có thông báo gọn, có đường quay lại giọng chính |
| Bàn phím và bố cục | Nút kích hoạt bằng Enter; viền tập trung 2 px; không tràn ngang |

Thẻ lỗi giọng trong bài kiểm tra bố cục cao 141 px ở màn hình 320 px; 123 px ở các màn hình còn lại. Hai nút đều cao 44 px. Đây là kích thước CSS, không phải pixel vật lý của ảnh chụp.

Ảnh tại `screenshots/` chụp **thành phần thật của dự án**, dùng phản hồi bài học/lỗi được kiểm soát để tái hiện nhất quán. Đăng nhập dùng máy chủ cục bộ thật; âm thanh phục hồi dùng WAV tiếng Việt đã tạo thật. Đây không phải bằng chứng chạy trên điện thoại Android thật. Xem ảnh trong `index.html`.

Hai kiểm thử cũ về tiến độ chờ từng cố định giá trị bằng 1 dù thanh hiện phần trăm; đã đổi sang kiểm tra đúng trạng thái: đang bận, chưa đạt 100%, đúng bước hiện tại. Mock font của kiểm thử khởi động được bổ sung cho biểu tượng mới.

## Giới hạn

Đây là cải thiện cách trình bày và thao tác phục hồi khi lỗi. Không tuyên bố dịch vụ giọng bên ngoài sẽ luôn thành công, nhanh hơn hoặc không còn lỗi. Hai giọng chính, chuẩn bị âm thanh nền, nội dung và giới hạn chờ 60 giây vẫn giữ như trước. Không thay thuật toán OCR, không huấn luyện, không đổi cấu hình nhà cung cấp trong lượt này.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Thiết kế phản hồi lỗi gọn, rõ hành động tiếp theo.
  - Applied to: RecoveryNotice và bố cục lỗi Student ở nhiều kích thước màn hình.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Thay đổi thành phần React/React Native và vòng đời yêu cầu thử lại.
  - Applied to: Giữ trạng thái dữ liệu, hủy phản hồi cũ, mở lại bộ phát đúng tệp.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Thông báo lỗi và nút tương tác cần hỗ trợ trình đọc màn hình, bàn phím.
  - Applied to: Vùng thông báo, nhãn nút, viền tập trung, kích thước nút và con trỏ ô câu hỏi.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Dùng lại một thành phần nhỏ thay vì thêm nhiều kiểu lỗi và thư viện.
  - Applied to: RecoveryNotice, bỏ nút dư và các kiểu trang trí cũ.
