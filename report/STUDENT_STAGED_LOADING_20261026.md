# Student — tiến độ chờ theo từng bước

Ngày: 2026-10-26. Phạm vi: Student React Native / Expo web và Android. Đã tích hợp vào mã giao diện hiện tại, theo hướng loading trong nhánh `Nam`; không merge toàn nhánh.

## Kết quả

- Dùng chung `src/components/ui/TaskProgress.tsx`: thanh chia đoạn, số thứ tự, dấu hoàn tất và nhãn **Đã xong / Đang làm / Sắp tới**. Hỗ trợ thông báo tiến độ cho trình đọc màn hình. Component không dùng timer tăng tiến độ hoặc tính phần trăm theo thời gian.
- Màn đọc ảnh / chuẩn bị bài giữ mascot, hình ảnh và nút dừng, căn giữa. Thu nhỏ minh họa khi chiều cao dưới 700 px để dành chỗ cho tiến độ và nút dừng.
- Phần giảng âm thanh, hỏi bài, giải thích chỗ chưa hiểu, chuyển lời nói thành chữ, nhận xét bài và video dùng cùng kiểu tiến độ gọn.
- Sửa cách xác định hoàn tất so với bản Nam đã xem: đến bước cuối vẫn đang xử lý; chỉ rời loading khi có kết quả hoặc khi trình phát thực sự mở được tệp. Không báo sẵn sàng chỉ vì đã đến mục cuối.
- Khi tiếp tục xem một bài đã gửi, bắt đầu ở bước kiểm tra thay vì giả vờ đang tải ảnh lên lại.

## Các trạng thái đã áp dụng

| Khu vực | Các mốc hiển thị |
| --- | --- |
| Đọc ảnh trong bài học | Ảnh đã chọn → Đọc đề và bài làm → Mở phần kiểm tra |
| Chuẩn bị bài học | Đề đã xác nhận → Chuẩn bị các bước học → Mở bài học |
| Bài toán đặt dọc | Gửi ảnh bài làm → Đọc và kiểm tra bài → Mở kết quả |
| Nhận dạng nhiều dòng | Ảnh đã chọn → Tìm các dòng chữ → Mở khung kiểm tra; khi đã chọn dòng: đọc chữ → mở kết quả |
| Nhận dạng một dòng | Ảnh đã chọn → Đọc dòng chữ → Mở kết quả |
| Lấy lại kết quả / nhận xét / gợi ý / xác nhận ký hiệu | Tải kết quả hoặc kiểm tra lại → Mở nội dung tương ứng |
| Nghe giảng | Giọng đọc đã chọn → Chuẩn bị âm thanh → Mở lời giảng; bước cuối chờ decoder tải tệp |
| Ghi câu hỏi | Lưu câu hỏi vừa nói → Chuyển lời nói thành chữ → Mở phần kiểm tra; vẫn yêu cầu học sinh bấm gửi |
| Hỏi bài / giải thích chỗ còn vướng | Câu hỏi hoặc lựa chọn đã có → Soạn lời giải thích → Mở câu trả lời |
| Nhận xét bài đã viết | Bài làm đã xác nhận → Đối chiếu từng dòng → Mở nhận xét |
| Video bài học | Dựng hình và lời giảng → Tải video về → Mở trình phát |
| Mở ứng dụng / phần học / thư viện ảnh | Hiển thị bước tải tài nguyên tương ứng trước khi mở nội dung |

Các yêu cầu OCR và soạn bài hiện trả kết quả cuối, không cung cấp tiến độ nội bộ model. Vì vậy giao diện thể hiện đúng giai đoạn yêu cầu đang diễn ra, không đoán phần trăm OCR, số dòng đã nhận dạng hay thời gian còn lại. Riêng video giữ phần trăm do máy chủ cung cấp, ghi rõ **Phần dựng video**, không coi đó là phần trăm của cả quá trình tải và mở.

Các thao tác ngắn như mở/dừng mic, lưu và nút gửi vẫn dùng trạng thái chờ gọn tại chỗ; không thêm danh sách ba bước vào mọi nút. Luồng che thông tin riêng tư, cắt ảnh, camera, backend và model không thay đổi trong tác vụ này.

## Kiểm chứng

- **87 bộ, 984 kiểm thử Student đạt.** Kiểm tra không tự nhảy bước theo đồng hồ; bước cuối chưa hoàn tất; upload chỉ xong khi được chấp nhận; tiếp tục bài cũ không upload lại; chuyển pha ghi âm/soạn trả lời; chờ tải âm thanh/video; hủy và bỏ qua phản hồi muộn. Các kiểm thử bảo vệ luồng hiện có cũng đạt.
- **TypeScript và ESLint:** đạt. **Web export và Android export:** đạt. Android export là kiểm tra bundle, không phải bằng chứng chạy trên điện thoại thật.
- **Giao diện thực đã xuất:** 6 viewport (320×568, 360×800, 390×844, 768×1024, 844×390, 1440×900); 25 ảnh chụp trạng thái chuẩn bị bài, âm thanh, hỏi bài, dựng và tải video; không tràn ngang, không có lỗi JavaScript được ghi nhận. Chờ không tự tăng bước. Hủy ở 390 px rồi nhận phản hồi muộn không tự mở lại bài.
- **Luồng ảnh thực trong trình duyệt:** chọn ảnh từ thư viện → xác nhận riêng tư → cắt ảnh → yêu cầu đọc ảnh; kiểm tra ở 320 và 390 px, giữ ảnh và dừng được; thêm 2 ảnh chụp. Phản hồi OCR được giữ chờ bằng fixture, không dùng lượt này để đánh giá độ chính xác OCR.
- Âm thanh WAV và video MP4 dùng tệp thật để kiểm tra browser decoder; tài khoản, bài học và mạng dùng fixture. Không có kết luận về tiếng phát ra loa Android thật hoặc tốc độ dịch vụ production từ kiểm tra này.
- Dữ liệu kiểm tra: [summary.json](student-staged-loading-20261026/summary.json), [visual-qa.json](student-staged-loading-20261026/visual-qa.json), [photo-qa.json](student-staged-loading-20261026/photo-qa.json). [Xem 27 ảnh chụp](student-staged-loading-20261026/index.html).

## Giữ gìn thay đổi trước đó

Đã chụp SHA-256 của các tệp đang sửa trước khi bắt đầu tại `runtime/student-staged-loading-20261026/before.json`. Các thay đổi voice/Nam, bố cục đề bài và các tệp đang sửa từ lượt trước được giữ; những tệp cùng phạm vi được mở rộng thêm phần loading. Kiểm tra chi tiết trong `summary.json`. HEAD vẫn là `71ad997ad55301dd6a869baed34c0d13fbd8246e`; không commit/push trong tác vụ này. Không cài thêm dependency, không huấn luyện hoặc thay model.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: thiết kế bố cục tiến độ và phản hồi khi chờ.
  - Applied to: mascot, màu trạng thái, mật độ chữ, màn hình nhỏ và bố cục hộp thoại.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: tích hợp trạng thái tiến độ trong React Native và bản web.
  - Applied to: vòng đời yêu cầu, readiness của player, giữ cơ chế hủy, bỏ phản hồi cũ và component dùng chung.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: triển khai tối thiểu trên luồng hiện có.
  - Applied to: một component tiến độ nhỏ, tái sử dụng loader và giới hạn thay đổi trong Student; không thêm timer hay dependency.
