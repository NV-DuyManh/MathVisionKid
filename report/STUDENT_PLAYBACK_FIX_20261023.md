# Sửa Play im tiếng — 23/10/2026

## Phạm vi và bằng chứng

Chủ dự án xác nhận lỗi trên Expo Go Android. Hai ảnh là trình nghe **Lời giải thích** và **Câu hỏi vừa ghi** trong Hỏi bài. Cả hai đi qua `AudioPlayback.tsx`; đây là lỗi phát âm thanh, chưa có bằng chứng video MP4 bị lỗi cùng nguyên nhân.

Trước sửa, Play gọi trực tiếp `player.play()`; không khôi phục audio session, không bật lại audio hoặc kiểm tra tiến độ khi lời gọi trả về nhưng trình phát không chạy. Sau ghi âm, cấu hình trả về chế độ nghe chỉ đặt `allowsRecording: false` và bỏ qua lỗi. Những thiếu sót này đã được sửa; chưa có log từ điện thoại để kết luận một nguyên nhân duy nhất của lần lỗi hôm qua.

## Thay đổi

- Dùng `playbackSession.ts` để cấu hình chế độ nghe đầy đủ: kết thúc chế độ ghi, cho phát khi máy để im lặng, dùng đường phát media thay cho ép qua loa thoại, quản lý audio focus và bật audio trước Play trên native.
- Bỏ mute và phục hồi gain của riêng player; không thay đổi âm lượng hệ thống của học sinh.
- Cả Play, nghe lại từ đầu và tiếp tục sau tua đều qua cùng luồng. Lệnh đang chờ không được phát sau khi đóng màn hình hoặc đưa ứng dụng xuống nền.
- Nếu sau 6 giây vị trí phát không tiến lên và chưa kết thúc, dừng yêu cầu phát và hiện thông báo thử lại. Tạm dừng, tua, đóng màn hình và xuống nền hủy kiểm tra cũ. Kiểm tra này phát hiện không khởi chạy; không thể đo người dùng có nghe thấy loa hay không.
- Sau dừng mic, khôi phục đầy đủ session. Nếu khôi phục thất bại, lần Play tiếp theo thử lại và hiện lỗi dễ hiểu nếu vẫn thất bại.
- Giữ giao diện và điều khiển tua hiện tại, không thêm bảng cài đặt.

Tham chiếu API: [Expo SDK 57 Audio](https://docs.expo.dev/versions/v57.0.0/sdk/audio/), đối chiếu mã `expo-audio` 57.0.5 đang cài trong dự án.

## Kiểm thử

- **46/46 test, 10 suite đạt**: bản ghi, trả lời, lời giảng, video hồi quy, thanh tua native/web, tải âm thanh. Test trình phát đặt `Platform.OS = android` và giả lập SDK: thứ tự thiết lập session → kích hoạt → Play, lỗi và thử lại, đóng/nền khi chờ, không khởi chạy, hủy timer, tua và nghe lại.
- TypeScript `tsc --noEmit`: đạt.
- ESLint ba file production thay đổi: đạt, không cảnh báo.
- `expo export --platform android`: đạt, 2.063 module, Hermes bundle tạo thành công. Đây là kiểm tra đóng gói, không phải chạy native trên máy thật.
- Dựng WAV thật qua bộ tổng hợp tiếng Việt hiện tại: 191.934 byte, mono PCM 16 kHz, 6 giây, peak 28.821, RMS 3.531,15. File có tín hiệu tiếng; không phải phép đo âm thanh từ loa Android.
- Năm file giao diện được yêu cầu giữ nguyên khớp SHA-256 với baseline, gồm che thông tin và cắt ảnh.
- `git diff --check`: đạt. Không commit/push.

Bằng chứng: `student-playback-fix-20261023/jest-results.json`, `student-playback-fix-20261023/narration-smoke.json`, `student-playback-fix-20261023/narration-smoke.wav`, `student-playback-fix-20261023/android-export/metadata.json`.

## Xác nhận trên thiết bị còn thiếu

Không có Android/ADB kết nối trong phiên này; chưa xác nhận nghe thấy tiếng trên điện thoại của chủ dự án. Cần reload bản mới trong Expo Go, ghi một câu rồi nghe lại; gửi câu hỏi và phát Lời giải thích; tua, tạm dừng và nghe lại sau khi hết. Nếu vẫn lỗi, phân biệt thanh thời gian đứng yên (trình phát chưa chạy) với thời gian tăng mà loa im (cần log/kiểm tra đường âm thanh trên thiết bị).

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa lỗi ở điểm dùng chung, không thêm thư viện hoặc cơ chế phát riêng cho mỗi màn.
  - Applied to: khôi phục audio session, Play/tua và kiểm tra không khởi chạy.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: xử lý component React Native và tác vụ bất đồng bộ theo vòng đời.
  - Applied to: loại bỏ lệnh phát cũ sau unmount/background, cleanup timer và kiểm thử hồi quy.
