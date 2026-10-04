# Cắt / căn thẳng ảnh và hướng dẫn toán — 2026-10-04

Yêu cầu: thao tác cắt/xoay giống trình sửa ảnh điện thoại, bỏ chờ xử lý ảnh mỗi lần chỉnh; hướng dẫn thật theo đề của học sinh thay cho phản hồi chung chung.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: tương tác cắt, căn thẳng và luồng học trên điện thoại.
  - Applied to: thanh căn thẳng, lớp phủ tối, một nút xoay, giảm nội dung phụ, bước học đang làm.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai React Native, kiểm soát render và cập nhật bất đồng bộ.
  - Applied to: shared values, gesture trên UI thread, trạng thái bài học, hủy yêu cầu và bảo toàn ảnh.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân lỗi bằng các API sẵn có, giữ thay đổi gọn.
  - Applied to: chỉ xuất ảnh khi xác nhận, bỏ gợi ý dự phòng chung chung; bộ hướng dẫn có dữ kiện rõ và bộ kiểm tra phép tính hiện có.

## Nguyên nhân đã xác minh

1. Bản cũ render và lưu ảnh trung gian mỗi lần đổi góc. Người dùng phải chờ xử lý bitmap dù chỉ muốn xem trước.
2. AI đọc được đề “viết thêm chữ số 6 ... hơn 537 đơn vị”, nhưng kế hoạch học do AI sinh dùng phương trình, các giá trị đã tính và tham chiếu bước trong nội dung công khai. Bộ kiểm tra từ chối kế hoạch, trả 503; giao diện lại mô tả như lỗi kết nối và đưa một gợi ý chung không phù hợp đề.
3. Một dòng nhận diện không tương đương một bước suy luận. Luồng học nay theo ý nghĩa bài toán, không bắt học sinh duyệt từng dòng OCR.

## Thay đổi

### Cắt và căn thẳng

- Thanh kéo căn thẳng từ −45° đến +45°, có thước chia và giá trị độ.
- Một nút xoay 90°; phối hợp với thanh kéo để điều chỉnh hướng ảnh.
- Làm tối bên ngoài vùng cắt, khung trắng và lưới một phần ba. Kéo khung để di chuyển, kéo góc để đổi kích thước.
- Xem trước bằng transform và shared values; không render/lưu ảnh trung gian khi kéo hoặc bấm xoay.
- Chỉ render và lưu JPEG khi bấm “Dùng ảnh này”. Dùng kích thước ảnh thực sau xoay để xác định vùng cắt.
- Không chuyển từ ảnh đã che thông tin riêng tư sang ảnh gốc nếu ảnh đã che gặp lỗi. Chặn xuất trùng và kết quả của ảnh cũ.
- Đã kiểm tra bố cục dọc 390 × 844 và ngang 844 × 390.
- Thời gian xuất tệp khi xác nhận vẫn phụ thuộc độ lớn ảnh và thiết bị; chưa đo độ mượt trên điện thoại thật.

### Học cách giải

- Các trường hợp rõ ràng có bộ hướng dẫn xác định từ dữ kiện: viết thêm chữ số bên phải; tổng–hiệu; tổng–tỉ số; diện tích hình chữ nhật; chu vi hình chữ nhật; diện tích tam giác; giá trị biểu thức; hình thang từ diện tích tam giác cùng chiều cao.
- Giải thích giá trị hàng, sơ đồ các phần bằng nhau, đại lượng và đơn vị; không dùng phương trình chứa x/y để dạy học sinh tiểu học.
- AI tiếp tục xử lý các dạng bài khác. Prompt có mẫu hợp lệ, giữ nguyên số cho sẵn trong phép tính, không tách chữ số hay đưa kết quả đã tính vào lời gợi ý.
- Bộ kiểm tra vẫn từ chối dữ kiện tự bịa, tham chiếu bước tương lai, phép tính không hỗ trợ, đáp án tính sẵn hoặc thông tin kỹ thuật trong trường công khai (kể cả tên bài, mục tiêu và đơn vị).
- Học sinh chọn cách làm và tự tính; sai thì ở nguyên bước. Chỉ sau khi hoàn thành mới ghép các bước thành lời giải đầy đủ.
- Giải thích luôn hiện trước câu hỏi. Đề gốc thu gọn khi học, tiến trình gọn hơn; màn hình tự đưa bước mới vào tầm nhìn.
- Có thể xem lại bài đã viết; vẫn phải bổ sung đề gốc nếu ảnh chỉ có lời giải. Không khẳng định toàn bộ bài viết đúng khi thiếu đề hoặc nét chữ chưa rõ.
- 503 được mô tả là chưa chuẩn bị được hướng dẫn, không gắn nhầm mọi lỗi thành mất kết nối. Bỏ thẻ gợi ý chung không liên quan bài đang học.

## Kiểm chứng

- Mobile: 37 suites / 400 tests đạt; lint và TypeScript đạt. Sau chỉnh thêm tiến trình và tự cuộn: 25 tests của hai nhóm liên quan đạt, lint và TypeScript vẫn đạt.
- AI: 131 tests của guided lesson, primary lessons, notebook tutor và math tutor đạt.
- Android development bundle biên dịch và trả HTTP 200. Đây không phải bằng chứng chạy trên điện thoại thật.
- Trình duyệt Chromium, kích thước điện thoại: kéo thanh và bấm xoay giữ nguyên URI nguồn; không có page error; nút xác nhận nằm trong màn hình ở cả dọc/ngang.
- Luồng thật chọn ảnh tổng hợp → kiểm tra riêng tư → xoay đủ bốn lần → căn thẳng → xuất cắt → đọc ảnh → bắt đầu hướng dẫn: inspect và lesson đều HTTP 200, không mock dịch vụ.
- Qua gateway xác thực thật: bài viết thêm chữ số 6/hơn 537 hoàn thành năm bước (9 phần → 531 → 59 → kiểm tra hiệu 537); đáp án 59 không có trong nội dung trước bước học sinh tính. Chọn sai không tiến bước.
- Ảnh đề hình thang viết tay do chủ dự án cung cấp: đọc đúng AB = 8 cm, CD = 15 cm, diện tích tam giác ACD = 90 cm²; bài học ba bước hoàn thành với chiều cao 12 cm và diện tích 138 cm².
- Ba bài ngoài bộ hướng dẫn xác định (24 + 18 bút, 45 − 17 kg gạo, chia 36 học sinh vào 4 nhóm) tạo kế hoạch hợp lệ qua dịch vụ AI thật; luồng trình duyệt bài bút cũng hoàn thành.
- Bằng chứng và ảnh QA nằm trong `infra/local-runtime/logs/crop-guide-20261004/` (thư mục runtime riêng, không đưa vào Git). Các JSON không ghi token đăng nhập.

## Phạm vi và giới hạn

- Hướng dẫn tự viết theo cách học tiểu học, phù hợp định hướng Kết nối tri thức; không sao chép sách hoặc tuyên bố đã số hóa toàn bộ chương trình/các trang sách. Nguồn sách của nhà xuất bản: https://truonghocsoquocgia.nxbgd.vn/.
- Nhận diện ảnh và hướng dẫn các dạng ngoài bộ xác định còn phụ thuộc dịch vụ AI. Ảnh thiếu đề, nhiều bài, mờ hoặc không phải toán vẫn cần chọn lại vùng/ảnh; không đoán dữ kiện.
- Không huấn luyện model, không thay đổi dữ liệu Drive ở lượt này. Không phát sinh commit/push.
- Các thay đổi đang có từ các lượt kiểm thử Drive và sửa lỗi trước được giữ nguyên.
