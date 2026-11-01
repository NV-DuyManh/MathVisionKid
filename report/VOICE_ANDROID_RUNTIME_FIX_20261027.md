# Sửa lỗi giọng thực tế trên Android

Ngày 27/10/2026. Phạm vi: nghe giảng, gửi câu hỏi ghi âm, phục hồi lỗi và kiểm tra đúng hệ thống đang chạy.

## Kết quả đã được xác nhận

Sau khi nạp bản sửa và yêu cầu tải lại ứng dụng/mở bài mới, người dùng đã trả lời trong cuộc trò chuyện: **“Nghe được và câu hỏi ra chữ”** trên Expo Go Android. Đây là xác nhận từ người dùng; không trình bày thành phép đo âm thanh hoặc thao tác điện thoại do agent trực tiếp thực hiện. Chưa có xác nhận riêng từng giọng, thao tác tua hoặc mọi loại mạng.

Bằng chứng: [xác nhận Android](voice-device-fix-20261027/android-owner-confirmation.json).

## Lỗi tìm thấy trong lần chạy thật

Nhật ký của máy chủ được khởi động lúc 21:57–21:58 ghi nhận yêu cầu nghe thực tế lúc 22:04 thất bại:

- TTS timeout khoảng 25 giây và trả 503. Những tác vụ tiếp theo có tạo được âm thanh, nhưng màn hình đã nhận thất bại từ yêu cầu đầu. Trước bản sửa, việc giữ đoạn đã tạo chưa đồng nghĩa với tự phục hồi ngay trong yêu cầu nghe của học sinh.
- Client gửi `Accept: audio/wav`; khi cần trả lỗi JSON, bộ xử lý ngoại lệ gặp `HttpMediaTypeNotAcceptableException: No acceptable representation`. Vì vậy đường báo lỗi có thể che mất mã lỗi gốc.
- Giao diện ghi âm gom các lỗi gửi tệp, timeout, dịch vụ không sẵn sàng và không nhận ra lời nói vào một thông báo chung. Bản ghi còn được giữ nhưng chỉ có lựa chọn nói lại, thiếu nút gửi lại chính bản ghi đó.

Không đủ bằng chứng để khẳng định duy nhất một nguyên nhân của lần nhận giọng thất bại trên điện thoại trước đó. Khi kiểm tra riêng qua hệ thống đang chạy, cả WAV và M4A/AAC tổng hợp đều được chuyển thành chữ đúng nội dung. Không thay suy đoán về mic, mạng hay quota bằng kết luận chắc chắn.

## Đã sửa

### Giữ yêu cầu nghe để tự phục hồi phần còn thiếu

Nếu tạo tiếng bị lỗi tạm thời nhưng có đoạn hoàn chỉnh được lưu tạm, yêu cầu nghe trực tiếp được tiếp tục một lần bằng những đoạn còn thiếu. Không chờ học sinh tự phát hiện rồi bấm lại sau lỗi đầu.

Hai lần dùng chung một hạn chót tổng 39 giây, nằm trong timeout đọc 40 giây của máy chủ nghiệp vụ và timeout 45 giây ở ứng dụng. Không kéo dài vô hạn. Không thử lại tự động khi chưa có đoạn hợp lệ để tiếp tục hoặc khi đã hết ngân sách thời gian; không đổi giọng và không trả bản tiếng bị thiếu.

Đã xử lý trường hợp người nghe đang chờ tác vụ nền vừa thất bại nhưng tác vụ đó chưa kịp nhả chỗ: phản hồi lúc này là trạng thái bận có thể thử lại, tránh nối lại ngay vào cùng kết quả lỗi đã hoàn tất.

### Trả và hiển thị đúng loại lỗi

- Client chấp nhận WAV thành công và JSON khi có lỗi. Máy chủ đặt rõ kiểu JSON cho lỗi nghiệp vụ và lỗi kiểm tra dữ liệu, kể cả client cũ chỉ yêu cầu WAV.
- Phân biệt phiên học thay đổi, nội dung không hợp lệ, đang bận và dịch vụ giọng chưa sẵn sàng; không trả thông báo tạo “gợi ý” cho lỗi giọng.
- Theo dõi tiến độ nhận trạng thái mới của lần tiếp tục, không giữ mãi số đo thời gian của lượt đã lỗi.
- Hỏi bằng giọng phân biệt mất kết nối, quá thời gian, gửi quá nhiều và dịch vụ chưa sẵn sàng. Thông tin kỹ thuật không được đưa vào giao diện học sinh.

### Gửi lại bản ghi mà không phải nói lại

Thêm nút **“Thử lại bản ghi này”** sau khi chuyển thành chữ thất bại. Nút dùng lại tệp đang giữ, không bật mic, không dừng/ghi lại hoặc xóa bản ghi. Câu hỏi vẫn cần được học sinh kiểm tra và chủ động bấm gửi; bản ghi và kết quả tới muộn vẫn tuân theo vòng đời màn hình/chủ phiên.

Đồng hồ của bước chuyển giọng có thời hạn 45 giây. Nhật ký chẩn đoán chỉ ghi loại lỗi, trạng thái và kích thước tệp; không ghi âm thanh, câu hỏi, khóa hay token.

## Kiểm tra trên hệ thống đang chạy

Đã nạp lại đúng hai máy chủ trong workspace sau khi kiểm thử qua. Giữ cấu hình và biến môi trường của các tiến trình đang chạy. Việc này làm hết phiên bài cũ nên người dùng đã được yêu cầu mở bài mới, sau đó xác nhận thành công trên Android.

Lượt HTTP sau bản sửa, dùng đề tổng hợp và xác thực qua máy chủ nghiệp vụ:

| Kiểm tra | Ghi nhận |
|---|---:|
| Hai bước đầu có tiếng và video chuẩn bị trước | 4.234 ms sau phản hồi tạo bài |
| Tải tiếng đã chuẩn bị của bước sau | 110 ms, HTTP 200 |
| Mở video đã chuẩn bị | 62 ms, READY và có tiếng |
| Xin revision tương lai | HTTP 409, bị chặn đúng |

[Kết quả HTTP sau sửa](voice-device-fix-20261027/http-smoke.json). Các con số này không phải thời gian bấm-phát trên điện thoại.

Phép thử nhận giọng trước khi nạp lại bản sửa, dùng tiếng tổng hợp rõ chữ:

- WAV: HTTP 200, khoảng 2,78 giây.
- M4A/AAC theo định dạng Android HIGH_QUALITY: HTTP 200, khoảng 0,87 giây.
- Cả hai trả đúng câu hỏi tổng hợp về chia các phần bằng nhau trước khi cộng phân số.

[Bằng chứng nhận giọng HTTP](voice-device-fix-20261027/transcription-before.json). Đây không phải bản ghi lấy từ mic điện thoại của người dùng. Trong lần người dùng thử lại, nhật ký ghi nhận hai lần gửi bản ghi và hai phản hồi 200 từ dịch vụ chuyển giọng; không lưu nội dung các bản ghi thật vào báo cáo.

## Kiểm thử và giới hạn

- 261 kiểm thử Python qua.
- 157 kiểm thử Student trong 16 nhóm qua.
- 133 kiểm thử Java qua, gồm kiểm thử client chỉ chấp nhận âm thanh vẫn nhận đúng JSON và HTTP 503.
- TypeScript qua; lint không lỗi, còn hai cảnh báo cũ ở `cropRotation.web.ts`.
- Bằng chứng bản dựng và mã băm được ghi trong [verification.json](voice-device-fix-20261027/verification.json).

Kênh quan sát từ xa của runtime Android có yêu cầu xác thực và trả 401, nên không có dữ liệu gỡ lỗi native trực tiếp từ kênh đó. Xác nhận nghe được/ra chữ là phản hồi của người dùng, cùng với bằng chứng API và nhật ký máy chủ; không chế thêm bằng chứng thiết bị.

TTS vẫn phụ thuộc nhà cung cấp và có thể chậm. Chạy nền và thử lại vẫn sử dụng yêu cầu dịch vụ; lần này không chuyển nhà cung cấp, không gọi mô hình khác để bù hoặc giảm chất lượng giọng. Nam Minh và Hoài My được giữ nguyên. Không commit/push, không huấn luyện hoặc đổi OCR.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa nguyên nhân ở đường gọi chung và xử lý lỗi, dùng lại đoạn âm thanh và bản ghi hiện có.
  - Applied to: phục hồi có hạn chót, tránh chờ tác vụ đã lỗi, kiểu nội dung lỗi JSON, mã lỗi nghiệp vụ, gửi lại tệp ghi âm.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: xử lý vòng đời yêu cầu và cập nhật trạng thái đúng khi nghe/ghi âm bất đồng bộ.
  - Applied to: trạng thái tiến độ, hủy theo màn hình, không áp dụng kết quả cũ và dùng lại bản ghi mà không mở mic lần nữa.
