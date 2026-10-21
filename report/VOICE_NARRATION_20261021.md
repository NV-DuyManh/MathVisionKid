# Lời giảng bằng giọng nói — 21/10/2026

## Kết quả

Đã triển khai phần nghe giảng theo từng bước trong Student, xuất bản portal lên production và kiểm tra đăng nhập, danh tính học sinh cùng việc tạo bài học qua API thật.

- Trang dùng chung: https://mathvisionkid-portal.vercel.app/study/
- Deployment: `dpl_B1bjmQ7bvVPm7b7BakcFMVhFtxYL`, trạng thái `READY`, target `production`.
- Bản triển khai: https://mathvisionkid-portal-7mvydbgea-manh15.vercel.app
- Kiểm tra Vercel: https://vercel.com/manh15/mathvisionkid-portal/B1bjmQ7bvVPm7b7BakcFMVhFtxYL

## Hành vi cho học sinh

1. Giữ câu lời giải, phép tính và đơn vị của các bước đã hoàn thành. Phần giải thích chữ tiếp tục mở dần theo từng ý.
2. Thêm “Nghe giảng kỹ hơn”, “Dừng nghe”, chọn giọng tiếng Việt, ba mức tốc độ và nghe thử giọng.
3. Nội dung nói gồm giải thích, hướng dẫn đã được dịch vụ bài học cho phép, gợi ý hiện tại và câu hỏi của chính bước đang học. Các đoạn hướng dẫn dài hơn phần chữ đang thu gọn. Học sinh có thể mở “Đọc lời giảng chi tiết” để đọc lại.
4. Với bước đã làm đúng, có thể nghe câu lời giải, phép tính, đáp án, đơn vị và hướng dẫn tính chi tiết đã được kiểm tra.
5. Nội dung giảng lấy từ bài học được hệ thống tạo cho đề hiện tại; không dùng bản thu hoặc lời giải viết sẵn riêng cho bài vườn cây. Chỉ câu nghe thử là lời chào cố định.
6. Chuẩn hóa cách đọc phân số, phép nhân/chia/cộng/trừ, số âm, phần trăm, đơn vị diện tích và thể tích. Đây là xử lý phát âm, không thay thế bộ tính/chấm toán.

## Phạm vi giọng đọc

Chủ dự án chưa có Azure Speech. Bản này dùng giọng tiếng Việt do thiết bị hoặc trình duyệt cung cấp, ưu tiên giọng chất lượng cao khi nền tảng liệt kê được. Hoài My/Nam Minh chỉ xuất hiện nếu thiết bị thực sự cung cấp giọng tương ứng; không giả lập sự có mặt của các giọng này cho người dùng thật.

Nếu không tìm thấy giọng Việt, giữ toàn bộ bản chữ, thông báo dễ hiểu và cho tìm lại giọng. Không tự chuyển sang giọng tiếng Anh. Chưa đăng ký dịch vụ Azure, chưa thêm khóa dịch vụ hay kích hoạt dịch vụ giọng nói tính phí. Tính năng này là đọc lời giảng; nhận câu trả lời qua microphone chưa nằm trong đợt triển khai này.

Chất lượng và khả năng phát âm thực tế còn phụ thuộc giọng đã cài, trình duyệt, âm lượng và thiết bị. Chưa có bằng chứng nghe trên điện thoại/iPad vật lý; không khẳng định đã đánh giá độ tự nhiên của âm thanh bằng tai.

## Kiểm soát tương tác

- Chỉ phát khi học sinh chủ động bấm nút; không tự phát khi mở bài hoặc chuyển bước.
- Bấm nghe không gửi đáp án, xin thêm gợi ý, chấm bài hay chuyển bước.
- Không đọc nguyên đối tượng bước học: loại khỏi lời giảng hiện tại biểu thức chưa mở, câu lời giải chưa mở và bản chép bài làm thô. Phép tính/đáp án được đọc trong phần bước đã hoàn thành.
- Dừng và vô hiệu hóa callback cũ khi đổi chủ sở hữu/nguồn/bước/gợi ý, đổi giọng/tốc độ, mở máy tính, đang chờ phản hồi, bài hết hạn, rời trang hoặc ứng dụng chuyển nền.
- Chặn bấm lặp; native đợi hủy lần phát trước hoàn tất rồi mới phát tiếp. Callback cũ không thể nối lời giảng của bài khác.
- Web gọi phát trong thao tác bấm; đọc danh sách giọng rỗng trả kết quả ngay và cập nhật khi trình duyệt báo thay đổi giọng.
- Nút và vùng chọn có nhãn, trạng thái, điều khiển bàn phím, viền focus và vùng thông báo; có bản chữ thay thế âm thanh.

## Kiểm chứng

| Hạng mục | Kết quả |
|---|---|
| Toàn bộ Jest Student | **837/837**, 60 suites |
| TypeScript | `npx tsc --noEmit` đạt |
| ESLint các tệp sản phẩm liên quan | Đạt |
| Xuất web production dưới `/study` | Đạt; kiểm tra địa chỉ dịch vụ đạt |
| Xuất Android và iOS | Đạt, gồm `expo-speech ~57.0.3` |
| Portal configuration/auth tests | 16/16 đạt |
| Student web deployment configuration | 4/4 đạt |
| Portal production bundle smoke check | Đạt qua script xuất bản |
| Trình duyệt 320/390/820/1440 px | Đạt; không tràn ngang |
| Production đăng nhập + `/me` | HTTP 200, vai trò STUDENT |
| Production tạo bài học vườn cây | HTTP 200, giao diện bài học hiển thị |
| Production nghe/dừng + bản chữ | Luồng điều khiển đạt với thiết bị speech mô phỏng; không gửi yêu cầu chấm bài |

Kiểm thử trình duyệt kiểm tra gọi phát đúng giọng, tốc độ, chia đoạn, callback muộn, chuyển nền, hiển thị lời giải đã hoàn thành và trường hợp không có giọng Việt. Các bài học trong kiểm thử bốn kích thước dùng fixture để kiểm tra tương tác ổn định. Kiểm thử production dùng đăng nhập, danh tính và tạo bài học thật; riêng thiết bị speech được mô phỏng. Hai loại bằng chứng này không phải kiểm thử chất lượng âm thanh trên thiết bị vật lý.

Bằng chứng cục bộ, nằm trong thư mục scratch bị bỏ qua bởi Git:

- `scratch/voice-qa/results.json`
- `scratch/voice-qa/voice-320.png`, `voice-390.png`, `voice-820.png`, `voice-1440.png`
- `scratch/voice-qa/public-result.json`
- `scratch/voice-qa/public-voice-390.png`
- `scratch/voice-native/metadata.json`

## Triển khai và vận hành

Đã build và khởi động lại stack PC preview từ mã hiện tại; backend, AI, worker và các phụ thuộc đạt kiểm tra sức khỏe. Đã xử lý lỗi khởi động Docker do hai thư mục socket IPC cũ bằng cách đổi tên để giữ bản dự phòng, sau khi dừng Docker và kiểm tra đường dẫn; không xóa dữ liệu container hay volume.

Đã xuất bản riêng portal cùng Student web và cập nhật proxy đến tunnel vừa kiểm tra. Website vẫn dùng địa chỉ API ổn định cùng tên miền. Backend/OCR **vẫn chạy trên PC của chủ dự án**: phải giữ PC và Docker hoạt động để đăng nhập, tạo bài học và nhận diện. Đợt này không tạo máy chủ cloud độc lập, không hoàn tất mục tiêu dùng backend khi PC tắt.

Không commit/push, không huấn luyện model; giữ nguyên các thay đổi đang có của các phần trước. Các kiểm tra Python/Java của đợt nhận xét bài làm trước đây không được ghi lại thành kiểm tra mới của giọng đọc.

## Tệp triển khai chính

- `apps/student-mobile/src/features/tutoring/LessonNarration.tsx`
- `apps/student-mobile/src/features/tutoring/narration.ts`
- `apps/student-mobile/src/features/tutoring/speechOutput.ts`
- `apps/student-mobile/src/features/tutoring/speechOutput.web.ts`
- `apps/student-mobile/src/app/learning/math-guide.tsx`
- Các kiểm thử `narration`, `lessonNarration`, `speechOutputWeb`, `tutorScreen`.
- `apps/student-mobile/package.json`, `package-lock.json`.

Đã đối chiếu tài liệu đúng SDK trước khi sửa mã: https://docs.expo.dev/versions/v57.0.0/ và https://docs.expo.dev/versions/v57.0.0/sdk/speech/.

## Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: triển khai React/React Native và quản lý tác vụ bất đồng bộ.
  - Applied to: lifecycle trình đọc, callback theo nguồn, cập nhật danh sách giọng và tích hợp trang bài học.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: thêm điều khiển âm thanh cần dùng được bằng bàn phím và công nghệ hỗ trợ.
  - Applied to: nhãn nút, trạng thái chọn/mở, focus, vùng thông báo, kích thước thao tác và bản chữ thay thế.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: chọn cách triển khai gọn, phù hợp việc chủ dự án chưa có dịch vụ giọng nói.
  - Applied to: dùng speech có sẵn của nền tảng, tái sử dụng nội dung giảng đã được duyệt, không thêm hệ thống sinh lời giải/nhà cung cấp/khóa dịch vụ mới.
