# Giao diện nghe giảng và hỏi đáp giọng nói

Ngày: 27/10/2026. Phạm vi: các thành phần nghe giảng, ghi câu hỏi, đọc lại bản ghi, nhận câu trả lời và trình phát dùng chung của Student. Không thay toàn bộ các trang không liên quan của ứng dụng.

## Thay đổi đã đưa vào mã

### Giao diện

- Thẻ ghi âm có màu tím nhạt, nút mic nổi bật, hướng dẫn ngắn và hình Sao nhỏ sẵn có trong dự án. Ô nhập chữ có trạng thái focus rõ và lời nhắc giải thích vì sao chưa gửi được khi câu hỏi còn trống.
- Khi ghi âm, hiển thị trạng thái thật và đồng hồ `0:00 / 0:30`; nút “Nói xong” và hủy ghi âm giữ rõ ràng. Không vẽ sóng âm ngẫu nhiên để giả làm tín hiệu mic.
- Bản ghi câu hỏi dùng trình phát gọn hơn, vẫn có thanh tua tới vị trí bất kỳ, lùi/tiến và nghe lại từ đầu.
- Sau khi nhận câu trả lời, câu hỏi của học sinh nằm trong thẻ riêng; nút “Nghe lại” mở bản ghi khi cần. Không bày đồng thời hai trình phát ngay từ đầu.
- Phần giải thích và câu gợi suy nghĩ có phân cấp chữ/màu riêng. Nút “Em đã hiểu” quay về đúng bài đang học. Hỏi câu mới sẽ dọn bản ghi cũ để không lẫn tiếng của câu trước.
- Hai giọng Nam Minh/Hoài My có tên, ký hiệu và dấu chọn rõ. Ẩn phần avatar trang trí khi màn hình nhỏ hoặc cỡ chữ hệ thống lớn để giữ chỗ cho tên giọng.
- Trình phát dùng nền trắng, nút phát tím chuyển sắc, thời gian thật, trạng thái tải/phát/sẵn sàng và thanh tua đồng bộ trên web/native. Bản ghi câu hỏi có bố cục gọn; lời giảng/video dùng bố cục đầy đủ.
- Giọng dự phòng/giọng thiết bị chỉ đưa ra khi có lỗi. Luồng bình thường tập trung vào đúng hai giọng mong muốn.

Các thay đổi được triển khai bằng component hiện có, không thêm thư viện UI hoặc tài nguyên ảnh mới.

### Tốc độ và chất lượng

- Dùng cơ chế chuẩn bị/cache đã có cho **câu trả lời hỏi đáp mới**: khi chữ xuất hiện và học sinh đọc, chuẩn bị giọng đang chọn trước rồi giọng còn lại. Chỉ dùng `spokenExplanation` và `followUp` mà backend vừa cấp.
- Mở nghe hoặc chuyển giọng sẽ tham gia yêu cầu đang tải hoặc dùng lại kết quả còn hiệu lực, thay vì tạo trùng. Quy tắc hủy, ưu tiên yêu cầu nghe thật và cách ly học sinh/phiên/revision giữ nguyên.
- Không cắt bớt lời giảng, tăng tốc độ đọc, tự đổi giọng hoặc hạ model nhận tiếng/trả lời để tạo cảm giác nhanh.
- Android giữ `RecordingPresets.HIGH_QUALITY`. Web giữ bitrate ghi âm 64 kbps; yêu cầu trình duyệt bật xử lý tiếng nói echo cancellation/noise suppression/auto gain. Trình duyệt có thể thực hiện khác nhau; chưa có điểm đo chất lượng âm thanh để khẳng định các tuỳ chọn này tốt hơn trên mọi máy.
- Sửa việc giải phóng mic web khi tạo MediaRecorder thất bại. Track từ yêu cầu cấp quyền trả về sau khi đóng vẫn được dọn.
- Học sinh vẫn kiểm tra và sửa chữ trước khi gửi. Không tự gửi bản nhận tiếng chưa xác nhận, vì số/phân số/đơn vị có thể được nhận sai.

## Kiểm tra luồng thật

Đã dùng business backend và các dịch vụ nhận tiếng, trả lời, tổng hợp tiếng đang chạy thật, với bài toán và âm thanh **nhân tạo phục vụ kiểm thử**. Không dùng giọng học sinh thật, không thay phản hồi HTTP bằng fixture trong phép đo này. Tài khoản kiểm thử đã đăng xuất khi kết thúc; không ghi token/mật khẩu vào báo cáo.

Âm thanh đầu vào được tạo từ câu: “Vì sao em phải chia thành các phần bằng nhau trước khi cộng hai phân số?”

| Công đoạn | Một lần đo |
| --- | ---: |
| Nhận tiếng thành chữ | 855,23 ms |
| Soạn câu trả lời | 883,41 ms |
| Tạo/tải Nam Minh cho toàn bộ lời giảng dài | 11.842,89 ms |
| Tạo/tải Hoài My cho toàn bộ lời giảng dài | 13.892,86 ms |

Bản nhận tiếng: “Vì sao em phải chia thành các phần bằng nhau trước khi cộng 2 phân số?” Phản hồi có phần giải thích bằng ví dụ bánh và câu gợi nghĩ tiếp; `guarded=false`. Hai tệp trả về đều là WAV có dữ liệu âm thanh. Không thay phản hồi đó bằng kết quả giả để báo đạt.

Đây là phép đo HTTP với âm thanh tổng hợp rõ tiếng, **không phải** đo mic điện thoại, tiếng trẻ em, môi trường ồn hoặc thời gian bấm đến lúc tai người nghe được tiếng. Một mẫu không chứng minh chất lượng nhận tiếng tổng quát hoặc tốc độ ổn định.

### Vì sao giọng dài vẫn có lúc chậm?

Log lần đo ghi `provider_ms=11703/decode_ms=77` cho giọng nam và `provider_ms=13750/decode_ms=93` cho giọng nữ. Trong lần đó, gần như toàn bộ thời gian nằm ở dịch vụ online; giải mã tệp chỉ chiếm phần nhỏ.

Đã thử nghiệm riêng cùng lời giảng đã chuẩn hóa với hai kích cỡ chia đoạn, cùng hai voice ID và giới hạn hai luồng. Kích cỡ hiện tại 220 ký tự có lượt hoàn tất khoảng 1,50/1,58 giây; kích cỡ 160 ký tự ở lượt sau mất khoảng 6,31/12,86 giây. Thử nghiệm này khác thời điểm và môi trường tiến trình của phép đo HTTP; **không đủ để kết luận kích cỡ gây ra toàn bộ khác biệt**, và không dùng các lượt nhanh làm bằng chứng tốc độ giao diện đã được cải thiện tương ứng.

Không áp dụng thay đổi chia đoạn hoặc deadline thiếu bằng chứng hiệu quả. Cách giảm thời gian học sinh phải chờ hiện đã áp dụng là chuẩn bị song song lúc đọc, dùng lại dữ liệu và không tạo trùng. Một yêu cầu giọng hoàn toàn mới vẫn có thể chậm khi nhà cung cấp chậm; chưa có cơ sở cam kết “ngay lập tức trong mọi trường hợp”.

Dữ liệu và mẫu:

- [Kết quả luồng thật](voice-ui-polish-20261027/live-qa.json)
- [Thử nghiệm chia đoạn, chưa áp dụng](voice-ui-polish-20261027/chunk-timing-experiment.json)
- [Câu hỏi nhân tạo](voice-ui-polish-20261027/samples/synthetic-question.wav)
- [Trả lời Nam Minh](voice-ui-polish-20261027/samples/answer-male.wav)
- [Trả lời Hoài My](voice-ui-polish-20261027/samples/answer-female.wav)

## Kiểm chứng mã và khả năng tiếp cận

- **150 kiểm thử qua, 0 lỗi, 14 bộ**. Bao phủ ghi âm một chạm, xem/sửa chữ trước gửi, hủy/đóng, lỗi mic/nhận chữ, bản ghi cũ, tải trước hai giọng, cache, đổi học sinh/bước, tua vị trí bất kỳ, video, giọng dự phòng và deadline.
- Các ca mới kiểm tra nghe lại câu hỏi sau khi nhận trả lời, dọn bản ghi trước câu mới, tải trước hai giọng đúng nội dung, quay về bài học, không đưa giọng dự phòng vào màn hình bình thường, giữ bitrate web và giải phóng mic khi constructor/cấp quyền muộn gặp lỗi.
- TypeScript, ESLint cho mã sửa và `git diff --check` qua.
- Xuất web và Android/Hermes thành công tại `runtime/voice-ui-export-final-20261027`; log tương ứng `runtime/voice-ui-export-final-20261027.log`.
- Nhãn cho mic, nút phát/dừng, tua, nghe lại, sửa và lựa chọn giọng được giữ. Nút mới có vùng chạm tối thiểu 44 px; slider dùng bàn phím trên web vẫn được giữ. Vùng mở bản ghi có `aria-expanded`/`aria-controls`; ô nhập liên kết với mô tả và thông báo.
- Đã tính tương phản các cặp màu mới đại diện: chữ đạt 4,72–7,20:1; biểu tượng play trên điểm sáng nhất của gradient đạt 3,80:1. [Dữ liệu màu](voice-ui-polish-20261027/contrast-check.json). Đây không phải audit WCAG toàn ứng dụng.
- Modal web hiện dùng focus trap/Escape/khôi phục focus của React Native Web; không tự viết lại cơ chế này. Đã đọc mã thư viện, chưa chạy lại kiểm tra tương tác bàn phím trong trình duyệt ở lượt này.

## Giới hạn kiểm tra giao diện

Công cụ trả thông báo **Local browser use is disabled in Work settings**. Vì vậy chưa chụp hoặc rà soát bằng mắt giao diện mới trong lượt này, chưa có kết quả kiểm chứng bố cục trên tablet/laptop/điện thoại thật và chưa đo FPS. Không dùng ảnh các bản trước làm ảnh của bản mới, không vượt cài đặt để điều khiển trình duyệt bằng cách khác.

Mã giao diện đã được tích hợp, kiểm thử hành vi và xuất bản thành công; không gọi kết quả đó là chứng minh giao diện đã “hoàn hảo” trên mọi thiết bị. Không commit/push, không train hoặc đổi model trong lượt này.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: bố cục và phản hồi trạng thái ghi âm/nghe trên màn hình nhỏ.
  - Applied to: thẻ mic, lựa chọn giọng, trình phát gọn, phân cấp câu hỏi/câu trả lời và trạng thái lỗi.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: chuẩn bị dữ liệu sớm và lifecycle React.
  - Applied to: tải trước giọng câu trả lời, dùng lại cache, hủy theo phiên và dọn bản ghi.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: các nút ghi/phát, form nhập câu hỏi và vùng mở bản ghi.
  - Applied to: tên truy cập, mô tả form, focus input, vùng chạm, toggle, trạng thái disabled và màu tương phản.
