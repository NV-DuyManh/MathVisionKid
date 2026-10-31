# Câu đố: lối vào và thư viện gọn hơn

Ngày: 30/10/2026. Áp dụng trực tiếp tại `E:/MathVisionKid`, bản local đang chạy. Chưa commit/push.

## Cách hoạt động đã đối chiếu với mã nguồn

- Khi hoàn tất bài học hoặc phần nhận xét, `QuizInvitation` gọi luồng tạo/mở lại câu đố của nguồn đó. Chỉ dạng toán được bộ kiểm chứng hỗ trợ mới có câu đố; không phải mọi đề đều sinh được câu luyện.
- Câu luyện cùng dạng, dùng dữ kiện mới. Học sinh có thể làm ngay hoặc để sau; câu đang làm và kết quả gắn với tài khoản.
- Danh sách không khởi động câu đố. Trong màn câu đố, yêu cầu `start` mới đặt `startedAt`; phía máy chủ quản lý thời gian, đáp án và chấm điểm.
- `QuizService.counts` đếm READY, DEFERRED và IN_PROGRESS. Mục PENDING của thư viện chỉ trả READY/DEFERRED. Đây là lý do có thể có số trên thẻ nhưng mục Chờ làm lại trống.

## Đã thay đổi

- Bỏ thẻ Quiz riêng khỏi trang chủ. Lối vào đặt trong **Bài học → Câu đố của em**, ngay dưới chọn lớp; nút Luyện tập trên trang chủ vẫn dẫn đến Bài học.
- Thẻ vào nhỏ hơn, thông tin một dòng ngắn, số câu chưa hoàn thành nhẹ hơn; không có khối lỗi phụ chỉ vì không tải được số đếm.
- Thư viện dùng phần giới thiệu nhỏ, ba bộ lọc Chờ làm / Đang làm / Đã xong, thẻ câu đố gọn và trạng thái trống theo từng mục. Hướng dẫn chi tiết chỉ mở khi bấm nút dấu hỏi.
- Khi vào lần đầu, nếu không có câu chờ và số đếm báo còn câu chưa hoàn thành, tự mở Đang làm. Thao tác tự chọn mục luôn được ưu tiên. Hai yêu cầu danh sách/số đếm chạy độc lập; danh sách có dữ liệu không phải chờ số đếm.
- Giữ khóa theo tài khoản và hủy yêu cầu cũ để không hiện câu của tài khoản trước. Danh sách dùng MathText để trình bày phân số thẳng đứng.
- Các nút lọc cao tối thiểu 44, trạng thái chọn và nút trợ giúp có thông tin tiếp cận. Không thêm thư viện hay ảnh mới.
- Không sửa backend, bộ giải, quyền truy cập, âm thanh, cách chấm hoặc thời gian làm câu đố.

## Kiểm chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Kiểm thử tập trung Quiz library, Student Quiz, Home, Quiz layout | 4 bộ / 20 kiểm thử qua |
| Toàn bộ Jest Student | 109 bộ / 1.246 kiểm thử qua, 52,011 giây |
| TypeScript `npx tsc --noEmit` | Qua |
| Xuất web bằng Expo | Qua; 40 route tĩnh, gồm home, lessons, quiz và quiz/[quizId] |
| Rà soát độc lập các thay đổi UI/async | Không phát hiện lỗi chặn; xác nhận hai thứ tự phản hồi bằng kiểm thử |

Các ca mới kiểm tra: vào từ Bài học, trạng thái trống dẫn về Bài học, phản hồi count trước/list trước, giữ mục được chọn khi count đến muộn, hiện câu làm dở/phân số khi count chưa trả, điều hướng đúng ID, hủy phản hồi của tài khoản cũ, thử lại khi mất kết nối và mở trợ giúp.

Lần xuất web đầu thiếu biến cấu hình dịch vụ nên dừng theo kiểm tra sẵn có. Lần sau cung cấp `EXPO_PUBLIC_API_BASE_URL=https://student-build.example.test/api/v1` chỉ cho tiến trình kiểm tra build và xuất thành công. Tên miền `.test` là cấu hình giả dành cho kiểm tra biên dịch; thư mục `.local-artifacts/quiz-ui-qa-20261030/web` **không phải bản để triển khai**, không dùng làm bằng chứng API thực tế. Không thay tệp môi trường hoặc cấu hình của tiến trình local đang chạy.

## Giới hạn bằng chứng

- Công cụ trình duyệt báo “Local browser use is disabled in Work settings”; chưa chụp ảnh mới, chưa kiểm tra trực quan các kích thước màn hình hoặc bàn phím trong lượt này.
- Chưa xác nhận trên Android/iOS thật. Kiểm thử tự động và build không thay cho kiểm tra hình ảnh/thiết bị.
- Trong trường hợp số đếm trả chậm, trạng thái PENDING trống có thể xuất hiện ngắn trước khi app tự chuyển sang Đang làm. Không khóa danh sách để chờ số đếm và không ghi đè lựa chọn của người học.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: bố cục di động và mật độ thông tin của thẻ/thư viện.
  - Applied to: lối vào trong Bài học, giới thiệu gọn, bộ lọc và trạng thái trống.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native, yêu cầu dữ liệu độc lập và vòng đời khi đổi tài khoản/mục.
  - Applied to: tải song song, bảo vệ phản hồi cũ, kiểm thử các thứ tự phản hồi.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: nút lọc, nút trợ giúp và trạng thái tải/lỗi.
  - Applied to: nhãn nút, selected/expanded/busy, vùng chạm và biểu tượng trang trí.
