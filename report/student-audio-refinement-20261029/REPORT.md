# Cải thiện nghe giảng và hỏi bài — 29/10/2026

Đã sửa trực tiếp tại `E:/MathVisionKid`, nhánh `codex/student-learning-voice-polish-20261029`. Chưa commit/push trong lượt này. Không đổi model OCR, không huấn luyện, không thêm thư viện và không đổi thông tin đăng nhập/nhà cung cấp.

## Kết quả

**Giao diện:** bộ phát có nền tím nhẹ, nhãn trạng thái, nút phát nổi bật, nút nghe lại và tốc độ rõ hơn. Bỏ lời nhắc tua bị lặp. Giữ thanh tua theo thời gian, lùi/tiến, nghe lại và hai lựa chọn Giọng nam/Giọng nữ. Viền điều khiển hỗ trợ bàn phím; thao tác trỏ không dùng viền đen tùy chỉnh.

Phần chuẩn bị âm thanh rút gọn còn bước hiện tại, thanh tiến độ, thời gian đã chờ, giới hạn và số đoạn thực tế khi có dữ liệu. Phần trăm vẫn ghi **Ước tính**; không dùng số giây chờ chia cho giới hạn và không coi 100% là đã phát được khi chưa mở xong tệp. Các màn chờ khác giữ kiểu đầy đủ. Nút mic ở phần hỏi bài chuyển thành hàng gọn, để ô nhập và nút gửi dễ thấy hơn.

**Phục hồi giọng:** tìm thấy hai đường chưa phục hồi lỗi mạng ngắn: gửi lệnh chuẩn bị và lấy WAV đã sẵn sàng. Đã thêm thử lại tối đa hai lần sau lượt đầu cho các lỗi mạng/HTTP tạm thời. Yêu cầu giữ nguyên bài, phiên, lần kiểm tra, nội dung và giọng; không tự đổi chất giọng. Lúc thử lại, giao diện báo rõ đang thử lại. Tất cả lượt dùng chung hạn chót **60 giây**, không cộng thêm 60 giây cho mỗi lần.

Không thử lại lỗi quyền truy cập, phiên hết hạn, đầu vào sai hoặc kết quả giọng đã bị máy chủ đánh dấu thất bại. Lỗi đọc tiến độ vẫn dùng một vòng theo dõi chung; không tạo thêm vòng polling cho mỗi nơi mở nghe. Kiểm thử xác nhận hủy chờ dừng ngay việc thử lại.

Khi học sinh rời app lúc đang tải rồi quay lại, màn nghe tiếp tục tải đúng giọng. Tệp đã sẵn sàng được giữ để dùng lại. **Không tự phát tiếng khi quay lại.** Cơ chế chuẩn bị cả hai giọng khi đọc bài và cache riêng theo màn bài học được giữ nguyên.

**Phát âm:** sửa cách đọc đơn vị dạng `m2`, `dm^2`, `cm^{3}`, phép nhân viết `8 x 4` và phân số thập phân. Cả giọng máy chủ và giọng thiết bị có quy tắc tương ứng. Chỉ đổi cách phát âm; không tính lại hoặc tự đổi đáp án, không thay chữ `x` đứng riêng thành phép nhân.

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Student | **94 bộ, 1.135 kiểm thử qua** — `all-student-tests.json` |
| Dịch vụ giọng và chuẩn bị bài | **125 kiểm thử qua** — `ai-tests.xml` |
| TypeScript | Qua |
| Lint | 0 lỗi; 2 cảnh báo cũ tại `cropRotation.web.ts` |
| Android export | Thành công — `android-export/metadata.json` |
| UI web | Qua ở 320, 390, 768, 1440 px — `visual-qa.json` |
| Lỗi mạng được kiểm soát | Gửi chuẩn bị lỗi 503 và tải WAV lỗi 502 rồi phục hồi thành công; không hiện thẻ thất bại |
| Đóng/mở lại cùng giọng | 120–135 ms đến bộ phát sẵn sàng trên web kiểm tra; không thêm lượt tải WAV |
| Điều khiển | Phát/tạm dừng qua bàn phím; tua tùy vị trí; nút cao tối thiểu 44; không tràn ngang |

Ảnh trong `screenshots/` là thành phần thật của dự án, với phản hồi bài học/lỗi được kiểm soát. Đăng nhập dùng dịch vụ thật; WAV là âm thanh tạo thật. Đây không phải đo độ trễ trên điện thoại Android thật và không phải bằng chứng nghe đánh giá bởi con người.

## Phép đo dịch vụ thật

`live-probe.cjs` chạy qua đăng nhập và API đang hoạt động, dùng bài học thuộc đúng tài khoản. Không lưu token hoặc khóa. Đo một đoạn đã được máy chủ mở, dài **113 ký tự**:

| Đường đo | Giọng nam | Giọng nữ |
|---|---:|---:|
| Máy chủ nhận lệnh chuẩn bị | 31 ms | 31 ms |
| Từ gửi lệnh tới báo WAV sẵn sàng | 17.586 ms | 17.262 ms |
| Lấy lại đúng WAV đã lưu qua HTTP cục bộ | 14 ms | 17 ms |
| Thời lượng lời đọc | 9,58 giây | 9,79 giây |

Mở bước đọc đề mất 79 ms trong phép đo này. Hai WAV có dữ liệu không im lặng, mono 16 kHz và nội dung byte không đổi khi tải lại. Xem `live-probe.json` và `audio-validation.json`.

**Lần tạo mới vẫn còn chậm.** Nhật ký có các lượt nhà cung cấp không trả âm thanh và phải thử lại. Các thay đổi lượt này không chứng minh thời gian tạo mới đã giảm; không thể dùng thời gian đọc cache để tuyên bố mọi lần tạo đều chỉ mất 1–3 giây. Tạo trước giúp che thời gian chờ khi học sinh đang đọc, nhưng lúc học sinh đi nhanh hơn việc chuẩn bị, vẫn có thể phải chờ. Hạn 60 giây và hai nút phục hồi vẫn cần thiết khi dịch vụ/mạng không hoàn tất.

Đã nạp lại dịch vụ giọng cục bộ để dùng quy tắc phát âm mới. Các phiên bài học trong bộ nhớ của tiến trình cũ cần mở lại bài mới. Chưa kiểm chứng lượt sửa này trên Expo Go Android thật.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Cải thiện bố cục nghe giảng, phản hồi đang chờ và thao tác hỏi bài.
  - Applied to: Bộ phát, trạng thái, nút mic gọn, tiến độ chỉ hiện thông tin cần thiết.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Hiệu năng luồng tải và vòng đời React Native.
  - Applied to: Dùng lại cache/yêu cầu hiện có, xử lý quay lại app và bỏ phản hồi đã hủy.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Điều khiển media và trạng thái cần dùng được bằng bàn phím/trình đọc màn hình.
  - Applied to: Nhãn trạng thái, nút có tên, viền tập trung, kích thước nút, giữ thanh tua và thông tin thời gian.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Sửa đúng hai đường lỗi mạng bằng cơ chế hiện có.
  - Applied to: Thử lại có giới hạn, giữ hạn chót, tái sử dụng TaskProgress và MediaTimeline, không thêm dịch vụ/thư viện.
