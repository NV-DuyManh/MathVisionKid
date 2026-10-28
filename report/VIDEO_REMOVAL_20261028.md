# Gỡ hẳn video hướng dẫn — 28/10/2026

Đã xóa các thành phần phát/chọn/tải/lưu video của Student, ba clip MP4 minh họa, API tạo/trạng thái/tải video ở Java và Python, DTO, hàng đợi và bộ xuất video. Đã gỡ `expo-video` khỏi dependency, lockfile, plugin và thư mục thư viện đã cài.

Phần tổng hợp tiếng trước đây dùng chung tệp với bộ dựng video được chuyển sang `ai/runtime/app/tutoring/speech_render.py`. Hàng đợi chuẩn bị ngầm nay chỉ chứa các đoạn lời đọc, không còn metadata cảnh hoặc bộ đếm video. Giữ Nam Minh, Hoài My, giới hạn 45 giây, tua/phát lại, ghi âm và hỏi đáp. Các định dạng M4A/`audio/mp4` và ffmpeg vẫn phục vụ âm thanh.

Các kiểm thử phát âm toán, dấu âm, phân số và đơn vị được chuyển sang `test_speech_pronunciation.py`; kiểm thử ghi tệp WAV được giữ khi loại kiểm thử MP4. Bộ kiểm thử mới xác nhận các endpoint video không còn trong schema/handler. Việc này phát hiện xử lý chung đang biến đường dẫn không tồn tại thành 500; đã sửa trả 404 JSON với thông báo phù hợp.

## Xác minh

- Python: **357 passed**, `runtime/video-removal-python-20261028.log`.
- Student: **259 passed / 14 suites**, `runtime/video-removal-student-20261028.json`.
- Java: **140 passed** (92 service, 48 controller), `runtime/video-removal-corrected-java-20261028.log` và XML trong `backend/business-api/build/test-results/test/`.
- Tổng: **756 kiểm thử**, không cộng các lượt chạy lại.
- TypeScript qua; lint 0 lỗi, hai cảnh báo cũ ở `cropRotation.web.ts`.
- Xuất web và bundle Android thành công: `runtime/video-removed-web-export-20261028.log`, `runtime/video-removed-android-export-20261028.log`. Chưa kiểm chứng trên Android vật lý.
- `git diff --check` qua; có cảnh báo chuyển LF/CRLF sẵn có.

AI runtime, business API và máy chủ Student đã được nạp lại. Kết quả kiểm tra HTTP sau nạp được lưu cùng `verification.json`. Các báo cáo và mẫu lịch sử được giữ làm chứng cứ của những vòng trước. Không commit/push hoặc train model.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: gỡ trọn tính năng và các phụ thuộc không còn dùng.
  - Applied to: API/DTO/bộ xuất, thư viện video và việc giữ riêng phần tổng hợp tiếng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: loại module và tài nguyên video khỏi Student.
  - Applied to: component/player/API client, tài nguyên MP4 và cấu hình đóng gói.
