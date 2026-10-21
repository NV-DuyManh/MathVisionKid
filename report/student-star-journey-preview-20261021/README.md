# Mẫu Student theo ảnh số 5 — Hành trình Sao nhỏ

Ngày: 21/10/2026. Phạm vi: toàn bộ Student web, xem thiết kế trước khi tích hợp. Chưa thay giao diện sản phẩm, chưa deploy, chưa commit/push. Các thay đổi sản phẩm tồn tại từ trước được giữ nguyên.

## Bản chỉnh v2 theo phản hồi về độ giống

- Giữ lại ảnh trước trong `comparison/before-*.png`; thêm phần đối chiếu ảnh gốc / trước / sau cho cả ba thiết bị trong thư viện.
- Hiệu chỉnh tỷ lệ theo phần màn hình bên trong khung tham chiếu: thanh bên laptop từ 195 lên 265 px, thẻ chào 323 px, tỷ lệ hero/chuỗi học 1,87:1, lề và khoảng cách các hàng.
- Lấy màu từ các vùng thẻ trong ảnh tham chiếu để chỉnh tím, kem, xanh mint và nền. Không công bố phần trăm tương đồng dựa trên các mẫu màu.
- Laptop dùng đường cong với cây, đảo nhỏ, cờ và bệ đích. Tablet dùng đường ngang, viên nối và huy hiệu riêng. Điện thoại dùng minh họa đảo cho Tiến bộ, thẻ máy tính ngang; bỏ gợi ý dư so với tham chiếu.
- Dựng riêng cây 3D nền trong suốt ở `assets/cactus-island-v2.png` bằng built-in image_gen. Prompt đầy đủ và nguồn ở `asset-prompt.txt`. Chỉ phụ kiện được tạo bằng AI; toàn bộ ảnh giao diện mới vẫn chụp từ mã chạy trong trình duyệt.
- Thu gọn Bài học, Thành tích, Của em; bố trí lại Kiểm tra đề, Học từng bước, Hỏi bài, Nghe giảng, Hình phân số, Nhận xét bài làm, Bài giải và Thử lại.
- Hình phân số có thanh 15 phần để thể hiện 5/15 + 6/15 = 11/15; đây là cùng một toàn thể, không ghép hai mẫu số thành số phần bằng cách cộng mẫu.

`calibration.json` ghi các mốc hình học ước lượng từ phần màn hình tham chiếu và số đo DOM. Ảnh tham chiếu có phối cảnh, chữ mờ và một số chi tiết minh họa; các mốc này phục vụ điều chỉnh, không chứng minh khớp từng điểm ảnh. Nét minh họa, huy hiệu và tư thế linh vật vẫn chưa thể gọi là giống tuyệt đối. Giữ nội dung toán đúng thay vì sao chép các chữ/ký hiệu nhỏ không rõ trong bảng ý tưởng.

## Mở bản duyệt

Mở `index.html` trong trình duyệt. Không cần cài thêm thư viện, đăng nhập hay chạy máy chủ. Bản duyệt có:

- Trang chủ tại 1440 px, 768 px và 390 px.
- 18 ảnh thành phần riêng, chụp ở mật độ điểm ảnh 2×; bấm để xem rõ.
- 46 màn hình và trạng thái theo danh mục Student đã rà soát ở đợt trước; từng màn có thể mở ở ba kích thước.
- `prototype.html?theme=4&screen=home`: bản mẫu tương tác bằng HTML/CSS/JavaScript.
- `reference.png`: ảnh chủ dự án chọn để đối chiếu.

## Ảnh xem nhanh

- `boards/01-responsive.png`: ba thiết bị.
- `boards/02-components.png`: thẻ chào, chuỗi học, đường hành trình, bốn tiện ích phóng lớn.
- `boards/03-all-screens.png`: toàn bộ 46 màn hình / trạng thái.
- `boards/04-learning.png`: xác nhận đề, hiểu đề, cùng tính, hình phân số.
- `boards/05-learning-tools.png`: hỏi bài, nghe giảng, hai lựa chọn giọng, nhận xét bài làm.
- `components/`: 18 ảnh riêng. `screens/`: ảnh màn hình riêng.

## Đối chiếu ảnh đã chọn

Bám theo: thanh bên tím đậm, nút đang chọn chuyển sắc, đầu trang có avatar, thẻ chào với linh vật phải và nút chụp bài trái, thẻ chuỗi học tập, đường cong với bốn mốc nổi, đảo đá và cờ, bốn tiện ích pastel. Tablet thu thanh bên vào menu; điện thoại dùng ba tiện ích với thẻ máy tính ngang và điều hướng dưới như ảnh gốc.

Dùng font Nunito, linh vật, avatar, các SVG điều hướng và minh họa của dự án. Đường cong, bệ mốc, huy hiệu và biểu tượng cột được dựng bằng CSS/SVG; cây 3D là phụ kiện raster tạo riêng ở v2. Không dùng ảnh gốc làm ảnh nền giả giao diện. Các mảnh ảnh tham chiếu chỉ nằm trong phần đối chiếu của thư viện duyệt.

Không tuyên bố khớp từng điểm ảnh 100%: ảnh gốc là bảng ý tưởng nhiều giao diện, chữ nhỏ và chi tiết mờ; kích thước, nội dung và tài nguyên khi chạy thật khác ảnh gốc. Đây là các mẫu có thể xem, chỉ ra phần cần chỉnh rồi mới tích hợp.

## Tình trạng chức năng

Đây là bản mẫu giao diện độc lập, không phải bản Expo / React Native / backend vừa được tích hợp. Đã nối thao tác mở màn, thu gọn menu, chọn dữ kiện, kiểm tra đáp án mẫu 4/15, chọn phần hình, chọn một trong hai giọng và mở chi tiết trong thư viện.

Giới hạn cần biết khi duyệt:

- Nội dung, thành tích, ngày học, bài đã lưu và nhận xét là dữ liệu mẫu, không phải thông tin thật của học sinh.
- Thu âm và phát giọng chỉ thể hiện bố cục; khi bấm có ghi rõ là minh họa. Chưa đánh giá chất lượng giọng thực tế hoặc nhận diện tiếng nói.
- Câu trả lời hỏi bài được dựng sẵn cho mẫu quy đồng, không gọi AI. Chưa kiểm thử câu hỏi bất kỳ.
- Khung chụp, che và cắt ảnh thể hiện thiết kế, chưa mở camera hay chỉnh ảnh thật.
- Vùng tô vàng nằm trên bài mẫu dựng bằng HTML. Không phải bằng chứng hệ thống đã định vị lỗi trên một ảnh học sinh thật.
- Tạo tài khoản chỉ mở giải thích về tài khoản được cấp; chưa nối tự đăng ký. Không thay đổi quyền đăng nhập hoặc RBAC.
- Chưa kiểm thử trên thiết bị vật lý; kích thước bên dưới là viewport trình duyệt.

## Kiểm tra

`visual-qa.json`: 46 màn hình × 9 viewport 320, 360, 375, 390, 414, 768, 1024, 1440, 1920 px = 414 lượt. Kiểm tra tràn ngang, ảnh hỏng và lỗi JavaScript. Các ảnh chính, hình phân số, hỏi bài, chọn giọng và bài mẫu tô vàng được xem trực quan.

`interaction-qa.json`: thao tác menu, chọn sai/đúng dữ kiện và phân số, chỉ hai giọng, câu hỏi gợi ý, minh bạch thu/phát mẫu, mở ảnh thành phần và màn theo thiết bị. Không dùng kết quả này để khẳng định camera, auth, AI hay giọng thật đã hoạt động.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: thiết kế Student web theo tham chiếu và bố cục thích ứng.
  - Applied to: giới hạn mật độ nội dung, một bước học đang mở, phân biệt chức năng chính và công cụ phụ, kiểm tra sáu viewport.
- `design`
  - SKILL.md: `.agents/skills/design/SKILL.md`
  - Why selected: dựng bảng duyệt nhiều màn và thành phần theo ảnh đã chọn.
  - Applied to: tái sử dụng bộ tài nguyên dự án; bảng màu tím, kem, vàng; ảnh chụp thành phần và bảng tổng quan.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bản mẫu kiểm chứng được, không mở rộng sản phẩm trước khi duyệt.
  - Applied to: HTML/CSS/SVG và JavaScript thuần, không thêm dependency, tái sử dụng danh mục 46 màn và mã bản mẫu trước.
- `imagegen`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/imagegen/SKILL.md`
  - Why selected: riêng lĩnh vực phụ kiện minh họa raster 3D; cây dựng bằng SVG ban đầu còn phẳng so với tham chiếu.
  - Applied to: `assets/cactus-island-v2.png`, tạo bằng công cụ built-in, giữ alpha và lưu trong workspace; không sinh ảnh giao diện thay cho bản chạy bằng mã.

Tra cứu UX cho học tuần tự trong skill không tìm được kết quả đủ sát sau hai truy vấn; cách chỉ mở một bước được áp dụng theo yêu cầu trực tiếp của chủ dự án và phán đoán thiết kế, không gán nhầm cho kết quả tra cứu.
