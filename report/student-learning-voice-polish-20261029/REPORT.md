# Hoàn thiện bài học và giọng đọc — 29/10/2026

Đã tích hợp vào mã nguồn `E:/MathVisionKid`, nhánh `codex/student-learning-voice-polish-20261029`. Đã nạp lại dịch vụ tại máy và Student để thử. Chưa commit/push thay đổi lần này.

## Kết quả theo 9 yêu cầu

| Yêu cầu | Đã thay đổi | Kiểm chứng |
|---|---|---|
| 1. Phân số xếp đứng | `MathText` nhận thêm `(3)/(5)`, LaTeX, dấu phân số Unicode và phân số âm. Chỉ đổi trình bày, giữ nguyên dữ liệu gốc gửi API. | Ca OCR, ngày tháng, mẫu số 0; ảnh `lesson-390.png`. |
| 2. Đề vừa nội dung | Trần nội dung tăng từ tối đa 104 lên 124 điểm, còn phụ thuộc chiều cao màn hình. Đề ngắn thu vừa chiều cao đo được; đề dài cuộn. Ảnh đề mở riêng, không ép chiều cao đề ngắn. | Phần nội dung đo trên web: điện thoại 124, tablet 82, laptop 71 điểm. Ca nội dung ngắn 38 điểm và nội dung dài qua. |
| 3. Nhãn giọng | Chỉ **Giọng nam / Giọng nữ**, bỏ tên và chữ viết tắt nhà cung cấp khỏi lựa chọn. Giữ chính hai giọng hiện có. | UI chỉ có hai lựa chọn, không hiện tên nhà cung cấp. |
| 4. Giảng đúng bài | Trích dữ kiện/câu hỏi của chính đề đang học. Bước nhận biết câu hỏi có hướng dẫn riêng. Model được yêu cầu mỗi ý khác nhau, đúng đại lượng của bài. | Hai đề khác nhau có kịch bản khác nhau; không tự thêm đáp số chưa tính. Giữ các kiểm tra tính đúng và chống lộ đáp án. |
| 5. Giảm chờ, giới hạn 60 giây | Chuẩn bị đồng thời cả hai giọng của đoạn đang học. Bỏ phần giảng lặp; tổng kết nhiều bước giữ câu lời giải/phép tính, giải thích chi tiết giữ tại từng bước. Giới hạn chờ client và chuẩn bị server là 60 giây. | Ca deadline tổng, không tự gia hạn, dùng chung request/cache và hủy tác vụ qua. Tổng kết ngắn được chuẩn bị riêng trước khi mở. |
| 6. Đọc đơn vị và ghi điểm | Bỏ phần ghi điểm; dấu nối trong tên đơn vị được đọc tự nhiên. Giữ ngoặc và dấu trừ trong phép tính. | `Bài 3: (2 điểm), 2 đề-xi-mét` → `Bài 3. 2 đề xi mét`; `(12+8)×2` vẫn đọc ngoặc. Kiểm thử cả client/server. |
| 7. Dừng sau câu đúng | Giữ nguyên câu hỏi và tất cả lựa chọn sau khi đúng; đánh dấu xanh đáp án đã chọn và khóa đến khi tiếp tục. Sai thì đánh dấu lựa chọn vừa chọn, giữ các lựa chọn để chọn lại. Giữ cả giá trị gõ vào với câu tự tính; chỉ xóa khi sang bước mới. Câu cuối phải bấm **Xem bài giải**. Số bước không nhảy sang bước mới trong lúc xem lại. | Ca bước giữa/bước cuối và thao tác web qua. Confetti 18 mảnh, 900 ms, màu chọn từ demoUI; tôn trọng giảm chuyển động và dừng khi ra nền. |
| 8. Giữ và đổi giọng | Lưu lựa chọn trong bộ nhớ và bộ lưu trữ bền vững. Đổi giọng không hủy phần chuẩn bị giọng còn lại của cùng kịch bản. Nội dung cũ vẫn nhường tài nguyên khi cần. | Ca ghi liên tiếp, lỗi lưu, chờ lưu và đổi giọng qua. Web xác nhận giọng nữ còn được chọn sau khi sang bước. |
| 9. Demo ngắn gọn | Chỉ `student`, `teacher`, `admin` ánh xạ tới ba tài khoản demo có sẵn. Seeder dev đặt mật khẩu đúng ba tài khoản thành `123`. Backend vẫn kiểm tra mật khẩu DB, trạng thái và vai trò. | HTTP thật: cả ba đăng nhập 200 và đúng vai trò; sai mật khẩu 401. Ca khóa tài khoản, giả vai trò, tên khác và truy cập chéo qua. |

## Kiểm tra đã chạy

- Student: **207/207** ca liên quan.
- AI/bài học/giọng: **184/184** ca liên quan. Lượt tự động này tắt gọi model bên ngoài để không phụ thuộc mạng/quota.
- Backend: **398/398**, toàn bộ bộ kiểm thử sau bổ sung.
- Hợp đồng/cấu hình web: **54/54**.
- TypeScript qua; lint không lỗi, còn 2 cảnh báo có từ trước ở `cropRotation.web.ts`.
- Build production Portal/Teacher/Admin qua với HTTPS ví dụ chỉ đặt trong tiến trình kiểm tra; không thay cấu hình triển khai.
- Xuất bundle Android qua, chưa tương đương kiểm tra trên máy thật.
- Web 320/390/768/1440 px: không tràn ngang; WAV tải được, phát/tạm dừng được; giữ giọng và tiếp tục thủ công qua.
- Đăng nhập web dùng backend thật. Player trong lượt kiểm tra bố cục dùng tệp giọng mẫu TTS thật để kiểm tra tải/phát, không coi đó là lời giảng của bài toán fixture. Dữ liệu bài học trong kiểm tra bố cục là fixture cố định, không coi ảnh là kết quả model mới.

Bằng chứng: [checks.json](checks.json), [visual-qa.json](visual-qa.json), [live-auth.json](live-auth.json), [live-voice.json](live-voice.json), [python-tests.xml](python-tests.xml), [student-tests.json](student-tests.json). Xem [ảnh giao diện](index.html).

## Hiệu năng và giới hạn thực tế

TTS online mới hoàn toàn, đoạn 111 ký tự: lượt đầu nam **11,631 giây**, nữ **10,774 giây**; lượt sau với chuẩn hóa phát âm cuối cùng nam **15,595 giây**, nữ **5,637 giây**. Cả hai lượt đo được giữ lại trong JSON, không chọn riêng lượt nhanh để báo cáo. Cả hai trả WAV 16 kHz, có tín hiệu khác 0, thời lượng khoảng 10 giây. Đây là đo trên máy chạy dịch vụ, không phải thời gian bấm đến phát trên điện thoại, không thay cho đánh giá nghe bằng tai. **Chưa bảo đảm 1–3 giây cho mọi lần tạo mới.** Chuẩn bị ngầm/cache giảm việc tạo lại khi đến bước. Người học đi nhanh hơn tốc độ nhà cung cấp vẫn có thể phải chờ; không thể cam kết dịch vụ ngoài luôn thành công hoặc không bao giờ hết quota.

Giữ đúng hai giọng hiện tại, không tự đổi sang giọng khác để báo nhanh hơn. Chuẩn bị cả hai có thể phát sinh lượng tổng hợp cho cả hai, đổi lại giảm chờ lúc đổi lựa chọn. Tác vụ vẫn được giới hạn số lượng/bộ nhớ/thời gian và dùng lại kết quả, không retry vô hạn. Không thêm video hay gọi model tạo lời giải mới chỉ để đọc kịch bản đã có. Lời đọc nhận biết dữ kiện được rút tiếp xuống một hướng dẫn gắn đúng dữ kiện, tránh đọc trước cả câu hỏi của bước kế tiếp.

Chưa thử trực tiếp Expo Go Android cho thay đổi lần này. Mã và dịch vụ tại máy đã cập nhật; máy chủ khác cần triển khai và khởi động lại tương ứng. Mật khẩu demo `123` được cập nhật bởi seeder **dev**, không tạo tài khoản/mật khẩu yếu qua seeder trong cấu hình production. Hai file OCR đang sửa từ trước được giữ nguyên, không đưa vào phạm vi thay đổi này.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Giữ thay đổi gọn, tránh thêm framework hay lớp cache mới.
  - Applied to: Dùng lại cache/giọng, đúng ba demo, chọn lọc hiệu ứng demoUI.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React/React Native và hiệu năng tác vụ bất đồng bộ.
  - Applied to: Chuẩn bị hai giọng, giữ request, chia sẻ lựa chọn và dọn tác vụ theo vòng đời.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Bố cục học tập và phản hồi câu đúng.
  - Applied to: Panel đề, nhãn giọng, đáp án có phân số và nút tiếp tục.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: Điều khiển mở/thu, chọn giọng và thông báo phản hồi.
  - Applied to: Nhãn phân số, trạng thái chọn/mở rộng, giảm chuyển động.
- `fixing-motion-performance`
  - SKILL.md: `.agents/skills/fixing-motion-performance/SKILL.md`
  - Why selected: Hiệu ứng chúc mừng cần nhẹ, có giới hạn.
  - Applied to: Một Animated.Value, transform/opacity, native driver khi phù hợp, hủy khi ra nền/unmount.

## Đo luồng giọng qua máy chủ thật

Một lượt có xác thực Student: mở phần đọc đề **0,310 giây**; chuẩn bị giọng chưa có cache **21,883 giây**; tải WAV đã chuẩn bị **0,032 giây**, HTTP 200, âm thanh dài 21,84 giây. Xem `live-pipeline.json`. Lượt này đo trước lần rút ngắn thêm hướng dẫn nhận biết dữ kiện; không dùng số đo đó để khẳng định tốc độ của kịch bản mới. Trường `backgroundPlanPhase` là phản hồi của một lệnh chuẩn bị được gửi riêng cuối phép đo, không phải chứng cứ phần toán đã tạo thành công.

## Lượt hoàn thiện tiếp

Xem [FOLLOWUP.md](FOLLOWUP.md): dùng lại tệp đã tải xong khi cùng lời đọc được cấp lại ở lượt xử lý mới; kiểm tra giữ tệp đúng vòng đời và hết hạn ban đầu. Đã kiểm tra thêm luồng API thật với kịch bản đọc đề rút gọn.
