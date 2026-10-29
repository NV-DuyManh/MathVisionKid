# Ghi chú bằng chứng HTTP

Trong lần kiểm tra lại sau đó, kịch bản smoke cũ đã ghi đè tệp `http-later-step.mp4`. JSON của lần đo 156 ms/47 ms được khôi phục từ nhật ký gốc; tệp MP4 hiện có thuộc lần kiểm tra sau, không phải tệp có mã băm cũ trong verification.json. Tệp của lần kiểm tra sau cũng được giữ tại `../voice-device-fix-20261027/http-before-later-step.mp4`. Không diễn giải tệp được thay thế thành bằng chứng nguyên vẹn của lần đo cũ.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bảo toàn và làm rõ nguồn bằng chứng của phép thử.
  - Applied to: ghi nhận việc script cũ ghi đè tệp trong lần kiểm tra lại.
