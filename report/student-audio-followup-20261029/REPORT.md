# Cải thiện giọng đọc và giao diện Student — 29/10/2026

Đã sửa trực tiếp tại `E:/MathVisionKid`, nhánh `codex/student-learning-voice-polish-20261029`. Chưa commit hoặc push.

## Những gì sửa trong vòng này

1. **Bỏ công việc chuẩn bị dư trong hỏi đáp.** Trước đây khi làm nóng hai giọng cho câu trả lời, hook còn gửi yêu cầu chuẩn bị cả bài học. Giờ câu trả lời chỉ làm nóng hai bản giọng của nội dung vừa được trả về. Luồng học chính vẫn chuẩn bị các phần tiếp theo như trước.
2. **Giảm khởi động lại công việc nền.** Thông báo foreground trùng lặp không còn hủy rồi tạo lại lượt tải đang chạy. Chỉ chuyển trạng thái thật sự mới dừng hoặc tiếp tục. Khi đổi giọng, giữ hai lượt tải hiện có và cập nhật ưu tiên của bài học.
3. **Giữ nguyên câu hỏi khi chỉ đang đọc/gõ.** Rời ứng dụng lúc không ghi âm hoặc gửi yêu cầu sẽ không gọi dừng máy ghi và không chèn thông báo “Đã dừng”. Việc ghi âm/yêu cầu đang hoạt động vẫn có quy tắc hủy và chặn phản hồi đến muộn.
4. **Bỏ nháy giao diện chờ.** Chỉ hiện phần chuẩn bị nếu việc mở âm thanh kéo dài hơn 180 ms. Tệp đã lưu sẵn mở thẳng bộ phát sau khi bộ giải mã xác nhận tải xong. Khi thật sự phải chờ, giao diện hoàn tất tiến độ trước khi chuyển sang bộ phát, tránh hiện hai khung cùng lúc.
5. **Thu gọn bộ phát trong hỏi đáp.** Chuyển tùy chọn gọn xuống đúng thành phần phát. Khung giảm từ 342 xuống 264 px trong các ảnh kiểm tra, khoảng 23%; vẫn giữ thanh tua tự do, lùi/tiến 10 giây, nghe lại và đổi tốc độ. Bản ghi câu hỏi vẫn giữ điều khiển riêng của nó.

Không đổi hai giọng hiện tại, không tự chuyển âm sắc và không thay timeout giọng 60 giây. Không bổ sung video hay thư viện. Các thông báo lỗi vẫn dùng khung gọn với “Thử lại” và “Giọng thiết bị”, có thể mở lời giảng dạng chữ.

## Kết quả kiểm chứng

- **1140 kiểm thử / 94 bộ kiểm thử Student đạt**, không có kiểm thử thất bại. Xem `all-student-tests.json`.
- TypeScript đạt. Lint không có lỗi; còn hai cảnh báo đã có từ trước trong `cropRotation.web.ts`.
- Xuất Android thành công; bằng chứng `android-export/metadata.json`. Đây là kiểm tra đóng gói, **không phải thử trên điện thoại thật**.
- Đăng nhập Student qua giao diện thật và backend thật đạt; tải lại trang vẫn giữ phiên và mở được trang chủ. Trang phát triển vẫn hoạt động sau khi xuất Android. Xem `gallery-qa.json`.
- Kiểm tra ảnh và thao tác trên 5 kích thước, gồm điện thoại dọc/ngang, tablet và desktop. Không tràn ngang. Các nút bộ phát cao ít nhất 44 px. Tab được giữ trong hộp thoại, Escape đóng và tiêu điểm trở lại nút mở.
- Mô phỏng dịch vụ báo thất bại rồi phục hồi: hiển thị hai thao tác gọn, tải lại phát được, giữ nội dung bài. Không lộ chi tiết nhà cung cấp.
- Kiểm tra âm thanh đã lưu sẵn: không gửi lại lượt tải tệp; không thấy khung chuẩn bị lóe lên; không chồng khung chuẩn bị và bộ phát.
- Kiểm tra hỏi đáp: không phát sinh thêm yêu cầu `/lesson/media/prepare` khi câu trả lời xuất hiện.

| Khung nhìn | Mở lại bộ phát đã lưu | Bộ phát hỏi đáp | Khung lỗi | Thao tác/bố cục |
|---|---:|---:|---:|---|
| 320 × 844 | 126 ms | 264 px | 141 px | Đạt |
| 390 × 844 | 106 ms | 264 px | 123 px | Đạt |
| 768 × 1024 | 107 ms | 264 px | 123 px | Đạt |
| 1440 × 900 | 129 ms | 264 px | 123 px | Đạt |
| 844 × 390 | 125 ms | 264 px | 123 px | Đạt |

Đơn vị px trong bảng là CSS pixel. Mỗi thời gian là một lượt đo, tính từ thao tác mở đến khi bộ phát thực sự sẵn sàng trong Chromium chạy ở máy này; chưa phải phân vị thống kê hay thời gian trên Android.

## Phạm vi bằng chứng và giới hạn

Ảnh chụp là **thành phần Student thực đang chạy**, không phải ảnh thiết kế dựng lại. Đăng nhập dùng máy chủ thật; phản hồi bài học và trạng thái giọng được chủ động mô phỏng để kiểm tra chờ/lỗi/phục hồi có thể lặp lại. Tệp WAV dùng cho kiểm tra bộ phát là âm thanh tiếng Việt đã tạo thật ở vòng trước. Vì vậy số 106–129 ms ở đây chỉ chứng minh đường mở tệp đã lưu và UI, **không chứng minh tốc độ tạo mới của dịch vụ bên ngoài**.

Vòng này không đo lại chất lượng bằng nghe trực tiếp và không có thử nghiệm Android vật lý. Kết quả cold synthesis ở vòng trước vẫn được ghi riêng tại `../student-audio-refinement-20261029/REPORT.md`; không gộp nó với thời gian cache. Chưa có cơ sở cam kết mọi lượt tạo giọng mới đều đạt 1–3 giây, hoặc dịch vụ bên ngoài không bao giờ lỗi. Chuẩn bị sớm và tái dùng tệp giúp giảm thời gian người học phải đợi, nhưng bài mới/nội dung mới vẫn cần tạo âm thanh.

## Tệp liên quan

- `apps/student-mobile/src/features/tutoring/NarrationPreparation.tsx`
- `apps/student-mobile/src/features/tutoring/LessonQuestion.tsx`
- `apps/student-mobile/src/features/tutoring/LessonNarration.tsx`
- `apps/student-mobile/src/features/tutoring/AudioPlayback.tsx`
- Các kiểm thử `narrationPreparation`, `lessonQuestion`, `lessonNarration`; kịch bản trình duyệt `capture.cjs`.

Không đụng vào các thay đổi OCR có sẵn của tác vụ khác. Không thay backend hoặc dữ liệu huấn luyện trong vòng này.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: giao diện chờ, phản hồi và bố cục trên màn hình nhỏ.
  - Applied to: trì hoãn khung chờ ngắn, chuyển sang bộ phát, khung hỏi đáp gọn.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: hook React và công việc mạng nền.
  - Applied to: bỏ yêu cầu chuẩn bị dư, xử lý foreground và giữ lượt tải đang có.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: bộ phát và hộp thoại tương tác.
  - Applied to: ẩn phần chưa sẵn sàng khỏi trình đọc màn hình; kiểm tra Tab/Escape/trả tiêu điểm, nhãn và kích thước nút.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa gọn theo nguyên nhân đã kiểm chứng.
  - Applied to: tái dùng cache, RecoveryNotice và MediaTimeline; không thêm dependency hoặc cơ chế focus tùy biến trùng nền tảng.
