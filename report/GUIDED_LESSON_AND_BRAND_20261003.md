# MathVisionKid — học theo bước suy luận và thương hiệu mới

Ngày: 03/10/2026. Phạm vi: triển khai yêu cầu đã được chủ dự án đồng ý về camera, ghép đề với bài làm, thay màn duyệt từng dòng OCR và cải tiến logo. Không huấn luyện mô hình, không commit hoặc push. Giữ các thay đổi có sẵn trong workspace.

## Hành vi đã triển khai

- **Chụp bài toán** trên trang chủ đi thẳng đến camera. Thư viện ảnh nằm trong camera; hộp chọn nguồn ảnh ở trang chủ đã được bỏ. Nếu chưa cấp quyền máy ảnh, ứng dụng vẫn cần xin quyền của thiết bị.
- Ảnh chỉ có bài làm: giữ nguyên nội dung và ảnh đã xử lý riêng tư, yêu cầu **Chụp thêm đề bài** hoặc nhập đề. Không suy đoán đề từ đáp số để kết luận cách làm đúng.
- Đề có sẵn: có thể bắt đầu học hoặc chụp thêm bài làm. Ảnh thứ hai mang theo ngữ cảnh của ảnh thứ nhất qua camera, bước riêng tư và cắt ảnh.
- Màn học dùng các **bước suy luận có ý nghĩa**, gồm câu hỏi lựa chọn hoặc ô nhập số kèm đơn vị. Không còn nút trước/sau để duyệt từng dòng vật lý như bước giải.
- Trả lời sai giữ nguyên bước. Phần “Vì sao làm như vậy?” giải thích mục đích và cách làm. Bước tính tiếp theo dùng kết quả học sinh vừa tìm được. Bảng tổng kết hiện sau khi hoàn thành các bước.
- Với bài làm có sẵn, trích đoạn liên quan đi cùng bước học. Sau khi học sinh trả lời, kiểm tra phép tính trong trích đoạn nếu đọc được biểu thức. Phản hồi khớp giá trị không có nghĩa là đã chứng nhận toàn bộ lời giải, hình vẽ hoặc đơn vị.
- Màn học giữ màu tím, thẻ pastel, font Nunito và linh vật của trang chủ. Lựa chọn dài xuống dòng trên màn hình nhỏ. Sửa cảnh báo chuỗi rỗng nằm trực tiếp trong View ở bản web. Nút quay lại có đường về trang chủ khi bài được mở trực tiếp.
- Các tuyến nghiên cứu nhận diện và lịch sử cũ được giữ lại. Lưu bài học dùng kho lịch sử theo tài khoản hiện có; ảnh không được thêm vào dữ liệu lưu lịch sử.

## Bài hình thang của chủ dự án

Đọc ảnh đề: AB = 8 cm, CD = 15 cm, diện tích tam giác ACD = 90 cm², tìm diện tích hình thang ABCD.

1. **Tìm điều còn thiếu:** học sinh chọn chiều cao.
2. **Tìm chiều cao chung:** giải thích AH vuông góc CD và là chiều cao chung vì AB song song CD. Học sinh tự tính `90 × 2 ÷ 15` và nhập số, đơn vị cm.
3. **Tính diện tích hình thang:** dùng chiều cao học sinh vừa tìm, tự tính diện tích và nhập số, đơn vị cm².

Kết quả 12 và 138 không được gửi trước bước học sinh cần trả lời trong luồng chỉ có đề. Trích đoạn từ bài làm của học sinh có thể chứa chính đáp số họ đã viết; đó là nội dung do học sinh cung cấp. Quy tắc hình thang nhận dữ kiện từ đề, có kiểm thử với dữ kiện thay đổi, không gắn cứng đáp số của ảnh mẫu.

## AI và quyền truy cập

- Các đề khác dùng bộ tích hợp AI hiện có để tạo kế hoạch 2–6 bước. Kiểm tra cấu trúc, dữ kiện số, trích đoạn có nguồn, biểu thức tính hợp lệ và nội dung công khai trước khi nhận kế hoạch.
- Máy chủ giữ đáp án của bước, chỉ trả bước hiện tại và các bước đã hoàn thành. Biểu thức tính dùng AST giới hạn và Decimal, không dùng eval hoặc chạy mã do AI tạo.
- Spring lấy chủ phiên từ tài khoản đã xác thực; không tin trường owner do máy khách gửi. Các tuyến student vẫn chịu RBAC. Dịch vụ nội bộ cần khóa gateway.
- Phiên có revision để chặn gửi lại bước cũ, thời hạn một giờ và giới hạn 128 phiên trong bộ nhớ. Phiên hiện tại chưa có lưu trữ bền vững hay chia sẻ giữa nhiều tiến trình. Khởi động lại dịch vụ cần bắt đầu lại bài học; nội dung đề/bài làm trong màn đang mở vẫn được giữ.
- Bộ lọc và phép tính không chứng minh được mọi suy luận do mô hình tạo. Đây là luồng hướng dẫn toán tiểu học với phép tính cơ bản; chưa phải bộ kiểm chứng tổng quát cho mọi dạng toán hoặc chứng minh hình học.

## Logo và màn mở đầu

Asset mới: `apps/student-mobile/assets/images/mathvision-icon-v2.png`, PNG RGB 1254 × 1254, 1.45 MB. Tạo bằng công cụ imagegen tích hợp, chế độ chỉnh từ hai ảnh tham chiếu: linh vật hiện có và icon trước đó. Giữ ngôi sao vàng, mũ xanh, sách tím; nền tím đậm và bố cục gần, giảm chi tiết trang trí. Không thêm chữ vào icon.

`BrandLockup` dùng chung ở màn vào ứng dụng và đăng nhập: icon mới, chữ MathVisionKid hai màu, điểm nhấn vàng, font và khẩu hiệu đồng bộ. Cập nhật icon, favicon, cấu hình splash; Android adaptive icon tiếp tục dùng linh vật nền trong suốt để tránh cắt mất nhân vật trong mặt nạ hệ thống. Không thêm thời gian chờ giả.

Prompt đã dùng:

> Use case: logo-brand. Asset type: premium square mobile app icon for MathVisionKid. Image 1 is the exact brand mascot reference, image 2 is the previous icon to improve. Reimagine this as a beautifully art-directed polished app icon, keeping the recognisable cheerful golden five-point star, expressive dark eyes, royal blue graduation cap and purple learning book. Simplify into a closer, bold character composition with fewer distracting little stars; sculpted satin toy materials, tasteful highlights, gentle studio lighting, friendly and premium rather than excessively shiny. Edge-to-edge rich violet to periwinkle backdrop with a subtle soft luminous halo, strong contrast against the golden character. Essential face, cap and book centered in the inner 70 percent safe area for a circular Android icon crop. No white border, no pre-rounded square mask, no letters or words, no watermark. Crisp silhouette, beautifully controlled depth and soft shadows, not a busy illustration. Produce one finished square icon.

Đã đọc tài liệu [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) trước khi viết mã. [Tài liệu splash SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/splash-screen/) nêu Expo Go hiển thị icon thay cho trải nghiệm splash hoàn chỉnh; phải kiểm tra splash trên bản release. Chữ tên ứng dụng màu đen do Expo Go hiển thị trước khi JavaScript chạy không được thay thế bằng BrandLockup. Chưa tạo hoặc kiểm tra APK/release splash trong lượt này.

## Kiểm tra đã thực hiện

| Kiểm tra | Kết quả |
|---|---|
| Mobile Jest, toàn bộ | 35 suites, **381 passed** |
| TypeScript `tsc --noEmit` | Thành công |
| Spring Gradle test, toàn bộ | 26 suites, **234 tests**, 0 failures, 0 skipped |
| AI tutoring pytest | **110 passed** |
| Export web | Thành công, 32 tuyến |
| Export Android Hermes | Thành công, 1 bundle; đây không phải APK |
| `git diff --check` | Không có lỗi whitespace; cảnh báo chuyển LF/CRLF của môi trường Windows |

Kiểm thử mới tập trung vào camera trực tiếp, bảo toàn ảnh/ngữ cảnh thứ hai, yêu cầu đề gốc, không lộ đáp án, đáp án sai không chuyển bước, hết phiên, quyền sở hữu phiên, replay, tính toán an toàn và từ chối kế hoạch bịa dữ kiện. Các trường hợp hồi quy OCR, riêng tư, upload và lịch sử hiện có vẫn qua.

### Dịch vụ thực tế

Bằng chứng: `report/guided_lesson_20261003/live.json`. 12 trường hợp đã qua trên Spring → AI đang chạy: khách chưa đăng nhập 401, thiếu đề 400, đọc ảnh đề hình thang, tạo bài học, chọn sai/đúng, replay 409, nhập chiều cao sai, yêu cầu gợi ý, nhập chiều cao/diện tích đúng và tạo bài cộng bằng AI. Không lưu token đăng nhập hoặc mã phiên vào bằng chứng.

Ảnh **đề hình thang** thật do chủ dự án cung cấp được gửi qua tuyến nhận diện và đọc đúng các dữ kiện. Ở lần kiểm tra cuối, nhận diện mất **6.875 giây**; lần trước là 2.235 giây, thể hiện độ trễ dịch vụ có thể thay đổi. Tạo luồng hình thang mất 0.016 giây; tạo kế hoạch bài cộng bằng AI mất 1.094 giây. Các số này là từng phép đo tại máy, không phải cam kết độ trễ.

Phần bài làm hình thang trong bài kiểm tra ghép đề dùng **bản chép bằng chữ từ ảnh mẫu**, không phải kết quả OCR của ảnh lời giải có số điện thoại. Không dùng bằng chứng này để tuyên bố đã nhận diện chính xác toàn bộ ảnh lời giải đó.

### Kiểm tra trực tiếp giao diện

Trình duyệt ở kích thước mô phỏng 390 × 844, kết nối dịch vụ thực:

- Trang chủ → nút Chụp bài toán → camera, hiển thị xin quyền máy ảnh do trình duyệt chưa cấp quyền; không xuất hiện hộp chọn nguồn ở trang chủ.
- Bài hình thang: chọn chu vi sai, chọn chiều cao đúng, nhập 11 sai, mở giải thích, nhập 12 đúng, nhập 138 đúng → tổng kết.
- Bài cộng AI: lựa chọn dài xuống dòng, chọn cộng, nhập 17 → tổng kết và lời nhắc hoàn thành.
- Màn thương hiệu mới được kiểm tra bằng ảnh chụp trình duyệt.

Bằng chứng giao diện: `height-ui.jpg`, `choices-ui.jpg`, `brand-ui.jpg` trong `report/guided_lesson_20261003/`. Đây là **bằng chứng trình duyệt**, không phải kiểm tra camera, bàn phím hoặc splash trên điện thoại thật.

## Cách chủ dự án test tiếp

Reload dự án đang mở trên điện thoại. Bấm Chụp bài toán để kiểm tra camera trực tiếp. Thử ảnh chỉ có bài làm: ứng dụng phải yêu cầu thêm đề và giữ ảnh đầu. Thử ảnh đề hình thang: học sinh chọn đại lượng còn thiếu, tự nhập chiều cao và diện tích; câu trả lời sai phải ở lại bước hiện tại. Thử chụp thêm bài làm sau khi đã có đề để đối chiếu phép tính.

Các dịch vụ local đã được khởi động và kiểm tra hoạt động; cập nhật tệp PID theo tiến trình của lượt này. Đã dừng máy chủ preview tạm thời không còn dùng. Chưa commit/push.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Thiết kế lại trải nghiệm camera và học toán trên điện thoại.
  - Applied to: Thẻ bước suy luận, câu hỏi, nhập số, phản hồi, bố cục nhỏ và kiểm tra trực quan.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Thay đổi màn React/React Native, trạng thái và yêu cầu bất đồng bộ.
  - Applied to: Hủy yêu cầu, chặn phản hồi cũ, bảo toàn ngữ cảnh, component thương hiệu dùng chung.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Giữ triển khai gọn và dùng hạ tầng hiện có.
  - Applied to: Không thêm dependency, dùng AST/Decimal chuẩn, kho lịch sử hiện có, phiên giới hạn trong bộ nhớ.
- `brand`
  - SKILL.md: `.agents/skills/brand/SKILL.md`
  - Why selected: Chủ dự án yêu cầu cải tiến logo và tính đồng bộ thương hiệu.
  - Applied to: Bố cục icon, màu, chữ thương hiệu và BrandLockup.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: Tạo lại asset raster dựa trên linh vật tham chiếu.
  - Applied to: `mathvision-icon-v2.png` bằng công cụ imagegen tích hợp.

Nhiều hơn ba skill vì công việc gồm các miền độc lập: UX, React, hướng dẫn phía máy chủ và thương hiệu/raster. Không mở skill không liên quan.
