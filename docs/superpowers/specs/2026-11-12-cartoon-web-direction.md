# Định hướng remake giao diện web MathVision Kids

Phần sáng tạo được phát triển tiếp trong [Creative Direction và Design System v2](./2026-11-12-cartoon-web-creative-v2.md). Tài liệu này tiếp tục là nguồn phạm vi, các ràng buộc và baseline.

Đã duyệt hướng dùng một Design System với mức cartoon theo vai trò. Các quyết định sáng tạo, token và prototype v2 có mốc duyệt riêng. Phạm vi gồm Portal, Student Web, Teacher Web và Admin Web. Working tree có bản sửa đăng nhập Teacher và tài liệu Kết quả theo bài tập đang chờ duyệt. Đợt thiết kế giữ nguyên các thay đổi đó.

Bốn ảnh concept đã tạo được loại khỏi tài liệu tham chiếu. Bản thiết kế dùng linh vật ngôi sao hiện có của dự án. Tệp `mathvision-star.png` hiện có cùng SHA-256 ở cả bốn ứng dụng. Giữ hình dáng nhân vật và dùng chính tài sản này khi dựng mẫu trong trình duyệt.

## Giả thuyết thiết kế

Dùng hình minh họa toán học nguyên bản, chữ tiếng Việt dễ đọc, hình khối mềm và thao tác rõ. Portal và Student thể hiện cartoon mạnh nhất. Teacher và Admin dùng chung nhận diện, với minh họa tập trung ở điểm đón và trạng thái trống để danh sách, ảnh bài làm, điểm số và quyền thao tác luôn dễ đọc. Giữ quy trình học, chấm và quản trị hiện có trong lần remake giao diện.

| Khu vực | Mẫu giao diện thử trước | Trọng tâm |
| --- | --- | --- |
| Portal | Trang chủ → đăng nhập | Giúp phụ huynh, học sinh và giáo viên nhận đúng lối vào. |
| Student Web | Trang học → một bài luyện | Mỗi bước có một hành động chính, phản hồi dễ hiểu, vùng bấm rộng. |
| Teacher | Tổng quan → hàng đợi → xem bài | Ưu tiên tiến độ, ngoại lệ, bằng chứng và thao tác bàn phím. |
| Admin | Danh sách tài khoản → xác nhận thao tác | Bảng dễ quét, lọc rõ, cảnh báo và xác nhận dễ phân biệt. |

## Mẫu dùng chung

Mục tiêu là nhận diện rõ cùng một sản phẩm và hoàn thành các luồng hiện có ở cả bốn web. Phạm vi chỉ bao gồm thiết kế và trình bày frontend. Giữ nguyên nghiệp vụ, hợp đồng API, đăng nhập, quyền, chuyển trạng thái và dữ liệu. Nếu có phụ thuộc ngoài UI, tách đề xuất để duyệt riêng.

- Chia token nền tảng và token theo vai trò. Dùng chung quy ước chữ, khoảng cách, focus và trạng thái. Ánh xạ chúng vào theme MUI của ba web và theme Student Web theo nền tảng.
- Đề xuất một bảng token chuẩn trong tài liệu thiết kế, gồm màu bề mặt/chữ/viền, trạng thái, type scale, spacing, radius, elevation và motion. Giai đoạn mẫu kiểm tra bảng này qua adapter theme MUI và Expo Web, mỗi app vẫn sở hữu thành phần và hành vi theo nền tảng. Giữ fallback font hiện có cho đến khi kiểm tra đầy đủ dấu tiếng Việt. Motion ưu tiên opacity/transform và tắt chuyển động trang trí khi reduced motion được bật.
- Dùng bộ mẫu cho điều hướng, nút, thẻ, biểu mẫu, bảng hoặc danh sách hẹp, hộp thoại, loading, empty, error và success. Minh họa hỗ trợ ngữ cảnh, trạng thái vẫn có chữ. Hỗ trợ giảm chuyển động.
- Student Web ở `/study/` được Portal phục vụ từ ứng dụng Expo `apps/student-mobile`. Ưu tiên biến thể web và kiểm tra hồi quy native nếu cần chạm thành phần dùng chung.

## Phương án đã cân nhắc

| Phương án | Đánh đổi |
| --- | --- |
| Một hệ thống với mức biểu cảm theo vai trò, đề xuất chọn | Portal và Student có nhịp kể chuyện qua ngôi sao. Teacher và Admin vẫn chia sẻ nhận diện qua kiểu chữ, màu, viền và hình khối. Chi phí là kiểm chứng cả hai mức mật độ. |
| Cartoon đậm xuyên suốt | Nhận diện mạnh trong mọi màn. Minh họa và khoảng trống làm giảm diện tích ảnh bài làm, hàng bảng và thao tác lặp. |
| Hệ thống riêng cho nhóm học và nhóm vận hành | Dễ tối ưu từng vai trò. Tăng chi phí duy trì font, trạng thái và điều hướng qua SSO. |

Duolingo dùng mascot biểu cảm và phân cấp typography rõ. LingoDeer chia khái niệm phức tạp thành bài nhỏ trong một lộ trình có cấu trúc. Áp dụng nguyên tắc dùng ngôi sao MathVision để chỉ dẫn theo ngữ cảnh, và giúp trẻ nhận ra bước học tiếp theo từ trạng thái đã có. [Duolingo Illustration](https://design.duolingo.com/illustration/duo) · [Duolingo Typography](https://design.duolingo.com/identity/typography) · [LingoDeer Help Center](https://support.lingodeer.com/en/support/solutions/articles/61000306561-what-s-the-difference-between-lingodeer-and-lingodeer-plus-)

## Phạm vi màn hình theo source hiện tại

| Khu vực | Màn hình và luồng cần phủ | Trạng thái cần đối chiếu |
| --- | --- | --- |
| Portal | Trang chủ, đăng nhập, chuyển vào Student/Teacher/Admin, đăng xuất, từ chối truy cập, hết phiên. Các route dev được kiểm tra riêng. | Đang chuyển vai trò, lỗi đăng nhập, phiên hết hạn, trở về trang chủ. |
| Student Web | Trang vào, đăng nhập, Trang học, Bài học, hồ sơ, thành tích, hướng dẫn toán, quiz và trò chơi. Luồng ảnh gồm camera hoặc thư viện, xem trước, màn riêng tư, cắt ảnh, xử lý, kết quả và các nhánh nhận dạng. | Kiểm tra deep link, chuyển hướng khi chưa đăng nhập, quyền camera, tải ảnh, ảnh lỗi, xác nhận ký tự, cần chụp lại, ngoài phạm vi, phản hồi đúng và gợi ý. Kiểm tra route nhận dạng theo cấu hình truy cập hiện hành. |
| Teacher | Đăng nhập, Tổng quan, danh sách và chi tiết lớp, danh sách và tạo bài tập, danh sách và tạo đợt, chi tiết đợt, hàng đợi, chi tiết bài nộp, cài đặt. | Đợt trống, ảnh nháp, che thông tin, upload, lỗi AI, ảnh riêng tư, chốt điểm, tiếp tục duyệt. |
| Admin | Đăng nhập, Tổng quan, tài khoản và chi tiết, lớp và chi tiết, nhật ký, phân tích nhận dạng, 403, hết phiên và route lỗi. | Bảng rỗng hoặc tải lỗi, tìm/lọc, thao tác cần xác nhận, thiếu quyền, kết quả cập nhật. |

Nguồn kiểm kê là `apps/portal-web/src/App.tsx`, `apps/teacher-web/src/App.tsx`, `apps/admin-web/src/App.tsx` và `apps/student-mobile/src/app/`. Đây là danh mục từ mã nguồn, cần đối chiếu route thực tế và cấu hình ở vòng chụp baseline.

## Kế hoạch triển khai đề xuất

1. Sau khi duyệt hướng, chụp baseline Portal, Student Web, Teacher và Admin trên môi trường cách ly. Với mỗi route ghi viewport, vai trò, hành động chính, trạng thái và nguồn dữ liệu. Những trạng thái cần dữ liệu kiểm thử được ghi rõ là fixture.
2. Dựng bốn màn đại diện với token dùng chung và linh vật hiện có. Ưu tiên Portal trang chủ, Student trang học, Teacher hàng đợi duyệt và Admin danh sách tài khoản. Nghiệm thu tương tác thực tế trước khi áp pattern sang các route còn lại.
3. Hoàn thiện mỗi khu vực theo nhóm luồng. Portal gồm đăng nhập và chuyển vai trò. Student gồm học, quiz và toàn bộ luồng ảnh. Teacher gồm lớp, bài tập, upload, tiến độ và duyệt. Admin gồm tài khoản, lớp, nhật ký và phân tích. Giữ nguyên các URL và hợp đồng backend.
4. Kiểm tra từng nhóm theo route và trạng thái ở mobile 390 px và desktop. So sánh với baseline về thao tác bàn phím, cuộn, focus, trạng thái tải/lỗi và khả năng hoàn thành luồng. Chạy riêng kiểm thử Student Web nếu thay đổi mã Expo dùng chung.

## Kết quả EGM Review Loop

Đã chạy một vòng review độc lập trên bản thảo với Design Critic (Luna) và Structural (Terra), cùng chuẩn Feature Spec. Đã áp dụng các phát hiện về lựa chọn thay thế, phạm vi route Student, token MUI/Expo, tiêu chí tiếp cận, rủi ro native và bằng chứng nghiệm thu. Phần kiểm tra giao diện mới và đo trước/sau thuộc giai đoạn triển khai.

## Baseline đã kiểm tra

- Ảnh Chromium từ lượt Teacher Reliability, viewport 390 px, cho thấy ảnh gốc, thanh công cụ ảnh, nhận định AI, điểm đề xuất và quyết định giáo viên xếp dọc. Khi dựng mẫu, giữ ảnh và nút phóng to dễ tiếp cận, giữ ranh giới giữa điểm đề xuất và hành động chốt, thử lại với tên học sinh dài. Ảnh bài làm và kết quả OCR trong biên nhận dùng dữ liệu fixture. [Ảnh biên nhận](../../../.local-artifacts/teacher-round1/e2e-teacher-web-final-rerun-30/teacher-image-390.png)
- Đã mở trực tiếp Portal build production ở preview Chromium. Trang hiện có lời giới thiệu về vở ô ly, minh họa các bước chụp và gợi mở, khu vực ba vai trò và phần cam kết sư phạm. Bản remake cần giữ đường vào đăng nhập và thông tin theo vai trò. Có thể gom phần giải thích dài để người dùng tìm đúng cổng nhanh hơn, sau khi kiểm tra điều hướng ở mobile.
- Bộ Playwright web chạy ba web MUI với API mô phỏng. Student dùng cấu hình Expo Web riêng. Đường bàn giao `/study/` trong bộ web chung chỉ chứng minh chuyển URL. [Hướng dẫn chạy](../../engineering/browser-testing.md)
- Baseline Portal, Teacher và Admin đạt 32/32 ca Chromium desktop/mobile với API mô phỏng, gồm SSO, quyền, danh sách lớp và lọc tài khoản. Source cho thấy bảng bài tập Teacher có minWidth 700 px và bảng tài khoản Admin 760 px. Đây là rủi ro cuộn vùng bảng trên màn hẹp, chưa phải kết luận cả trang tràn ngang. Student Web có layout và tài sản khởi động riêng.
- Student Web hiện có và đã chạy được từ bản export Expo qua `/study/`. Sáu ca Chromium desktop/mobile với API mô phỏng đạt, bao gồm Portal vào Student, tải lại deep link, chuyển khách về đăng nhập và các thao tác máy tính/đổi đơn vị. Luồng camera, âm thanh, kiểm thử thiết bị native và phép đo trước/sau thiết kế thuộc nghiệm thu triển khai.

## Rủi ro, tiêu chí và cách kiểm chứng

| Rủi ro | Điều kiện nghiệm thu |
| --- | --- |
| Đổi UI làm mất đường đi, thao tác hoặc quyền | Với mỗi route ghi vai trò, trạng thái, hành động, viewport và bằng chứng. So sánh URL, payload, điều hướng, SSO và các trạng thái lỗi trước/sau. Tách ca UI dùng fixture khỏi ca tích hợp backend và AI. |
| Thiếu thao tác khi màn hẹp hoặc đổi mật độ bảng | Kiểm tra 390 × 844 và 1280 × 900. Với đợt 30 bài, tìm, lọc, mở bài và quay lại được, không cuộn ngang cả trang. Bảng có vùng cuộn riêng khi cần. |
| Tương phản, focus và chuyển động | Mục tiêu WCAG 2.2 AA. Chữ thường đạt 4.5:1, chữ lớn 3:1, trạng thái đọc được ngoài màu. Focus nhìn thấy, không bị thanh cố định che. Thử Tab, Escape, zoom 200%, reflow 320 CSS px và trình đọc màn hình với form, trạng thái và dialog mẫu. Mục tiêu riêng của Student là vùng bấm chính 44 px. [WCAG 2.2](https://www.w3.org/TR/WCAG22/) |
| UI chậm do font, ảnh và chuyển động | Ghi baseline kích thước bundle, tải lạnh và bố cục nhảy ở Portal và Student. Đo lại cùng viewport và cấu hình mạng. Minh họa trang trí không giữ màn hình ở trạng thái tải. |
| Student Web dùng chung mã với native | Ưu tiên entry và adapter dành cho web. Nếu chạm thành phần hoặc token dùng chung, chạy test/typecheck Student Mobile và smoke trên Android/iOS có sẵn. Ghi riêng nếu chưa có thiết bị. |
| Dữ liệu cá nhân lọt vào baseline | Chỉ dùng tài khoản, tên và ảnh tổng hợp trong môi trường cách ly. Biên nhận ghi rõ nguồn dữ liệu. Kiểm thử luồng ảnh và âm thanh bằng các kịch bản opt-in tương ứng. |

## Pattern và tiêu chí duyệt mẫu

| Pattern | Quy tắc dùng chung | Ca đại diện để duyệt |
| --- | --- | --- |
| Điều hướng và tiêu đề | Tên khu vực, tiêu đề trang và hành động chính nhìn thấy ngay. Màn hẹp giữ cùng đích và thứ tự ưu tiên. | Portal chuyển vai trò, Student chuyển bài, Teacher từ đợt đến bài nộp, Admin từ danh sách đến chi tiết. |
| Chữ và màu | Kiểm tra đầy đủ dấu tiếng Việt, chữ số và nội dung dài. Màu thương hiệu phục vụ nhận diện. Màu trạng thái đi kèm chữ và biểu tượng. | Tên học sinh dài, điểm 0, bài chờ duyệt, tài khoản bị khóa. |
| Nút và biểu mẫu | Trạng thái focus, disabled, đang gửi và lỗi có cách nhận biết rõ. Lỗi nằm cạnh trường liên quan, nội dung người dùng đã nhập được giữ theo luồng hiện tại. | Đăng nhập thất bại, tạo bài, bộ lọc Admin, tiếp tục sau lỗi. |
| Mật độ thông tin | Student ưu tiên một thao tác nổi bật. Teacher và Admin giữ tiêu đề cột, số liệu và thao tác gắn với đúng bản ghi. | Danh sách 30 bài, bảng tài khoản dài, bài tập ở màn hẹp. |
| Ảnh và phản hồi | Chừa đủ diện tích cho ảnh và bài toán. Minh họa hỗ trợ ngữ cảnh, chuyển động ngắn và có chế độ giảm chuyển động. | Che ảnh Student, ảnh bài nộp Teacher, xác nhận thao tác Admin. |

Hiện Portal dùng Nunito và Plus Jakarta Sans, Teacher và Admin dùng Plus Jakarta Sans và Inter trong theme MUI. Đây là điểm xuất phát để kiểm tra chữ tiếng Việt và mức chia sẻ nhận diện. Student Web dùng theme Expo riêng. Khi duyệt mẫu, đối chiếu ở 390 px và desktop, thử bàn phím và kiểm tra các trạng thái tải, rỗng, lỗi và thành công. Khi triển khai, dùng bộ Playwright web và cấu hình Student riêng hiện có để bảo vệ luồng qua các cổng.
