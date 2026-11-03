# Kiểm tra hiện trạng MathVisionKid — 02/11/2026

## Phạm vi và kết luận

Kiểm tra bản local `E:\MathVisionKid`, nhánh `main`, HEAD `1f5543b`, bao gồm các thay đổi chưa commit đang có trên máy. Đây không phải xác nhận rằng remote main chứa toàn bộ các thay đổi đó. Không sửa mã nguồn, không commit/push trong lượt kiểm tra này.

**Chưa đủ điều kiện kết luận dự án ổn hoàn toàn.** Phần lớn kiểm thử qua; lỗi thực tế còn nằm ở độ ổn định của tạo giọng và chuẩn bị hướng dẫn. Student Mobile cũng còn một test thất bại và hai lỗi lint.

## Các vấn đề đã quan sát

1. **Giọng dài có thể thất bại.** Qua hàm narration thật và Edge TTS thật, đoạn công khai 606 ký tự/4 đoạn không tạo được âm thanh ở cả hai giọng. Giọng nam thất bại sau 37,04 giây; giọng nữ sau 19,38 giây. Nhật ký ghi `NoAudioReceived`, được ánh xạ thành `SpeechNoAudio`. Các lượt này chưa vượt giới hạn UI 60 giây; không phải bằng chứng lỗi timeout 60 giây. Đường Azure hiện chưa được cấu hình. Việc lấy dữ liệu từ cache rất nhanh không chứng minh dịch vụ luôn tạo mới thành công.
2. **Chuẩn bị hướng dẫn vẫn gián đoạn.** Hai đề lát nền thử với nhà cung cấp thật trả `unavailable` sau 15,00 giây và 1,99 giây. Thử lại đề thứ nhất bằng cùng đường chuẩn bị sau đó tạo được 6 bước trong 11,66 giây. Nhật ký cùng đợt ghi nhận hai khóa Gemini bị vô hiệu hóa do `AUTH_ERROR` và một phản hồi 429/backoff. Đây là vấn đề cấu hình/quota được quan sát, chưa đủ bằng chứng để quy mọi lần thất bại của kế hoạch cho cùng một nguyên nhân. Mẫu thử ít, không suy ra tỷ lệ lỗi toàn hệ thống.
3. **Test Student Mobile chưa xanh hoàn toàn.** Test `distinguishes lesson generation failure from a network error and offers a concrete retry` tại `apps/student-mobile/src/__tests__/tutorScreen.test.tsx:914` chờ chuỗi “Phần hướng dẫn đang tạm bận”; UI hiện hiển thị “Mình chưa chuẩn bị được hướng dẫn lúc này…”. Đây là sai lệch kỳ vọng thông báo trong test; không có bằng chứng từ lỗi này rằng app bị crash.
4. **Lint Student Mobile thất bại.** `QuizHelp.tsx:14` và `useQuizActivity.ts:12` bị quy tắc `react-hooks/set-state-in-effect` do gọi setState đồng bộ trong effect. Có thêm 4 cảnh báo tại NarrationPreparation, StudentWorkReview và cropRotation.web. Chưa đo được tác động của các lỗi lint này lên thiết bị thật.
5. **Cần chú ý cấu hình build và tải web.** Build mặc định với cấu hình local bị chặn vì URL API không phải HTTPS public. Build bằng các URL HTTPS ví dụ trong process kiểm thử thì cả ba web qua; không thay dotenv và không xác nhận các URL ví dụ là hệ thống đã triển khai. Bundle chính khoảng 724–780 kB trước gzip, có cảnh báo chunk lớn. Chưa đo thời gian tải trên mạng di động thật.

## Kết quả kiểm thử hiện tại

| Phần | Kết quả |
|---|---|
| Student Mobile Jest | 1.328 qua, 1 lỗi; 114 suite, trong đó 113 suite qua |
| Student Mobile TypeScript | Qua |
| Student Mobile lint | 2 lỗi, 4 cảnh báo |
| Metro config test | 1 qua |
| AI runtime pytest | 2.376 qua, 21 bỏ qua; 223,22 giây |
| Backend Gradle | 486 qua, 1 bỏ qua; 41 suite, 0 lỗi |
| Teacher/Admin/Portal config/auth tests | 76 qua |
| Teacher/Admin/Portal build và production smoke | Cả 3 build qua; 9 test bản build qua |
| Teacher/Admin/Portal lint | Không lỗi; Teacher có 1 cảnh báo Fast Refresh |
| git diff --check | Qua |
| Expo Android bundle từ bản E | HTTP 200, 13.706.259 byte |

## Kiểm tra dịch vụ và chức năng thật

- Ban đầu backend và API AI chưa chạy. Sau khi khởi động phục vụ kiểm thử, `/actuator/health`, `/health`, `/ready` trả HTTP 200. Docker PostgreSQL, Redis, MinIO đều healthy; SELECT 1, Redis PING và MinIO readiness qua.
- Alias demo student/teacher/admin đăng nhập và `/api/v1/me` đều HTTP 200, đúng vai trò. Student gọi Admin bị 403; gọi lesson khi chưa đăng nhập bị 401.
- Qua HTTP backend thật, ba bài `1 + 1 = ?`, `17/25 + 32/15 = ?`, `1,7 km² = ? ha` mở bài, nhận đáp án và hoàn thành chính xác: 2, 211/75, 170. Thời gian mở lần lượt 1.570,3 ms, 107,0 ms, 105,0 ms. Đây là ba mẫu, không phải SLA.
- Đoạn giọng ngắn 140 ký tự tạo mới thành công: nam 2,75 giây, nữ 1,30 giây. WAV không rỗng và qua kiểm tra âm thanh. Các số đo loại trừ HTTP, tải xuống và phát trên điện thoại.
- Một mẫu ASR từ âm thanh tổng hợp nhận đúng văn bản sau 2,61 giây; một câu trả lời thật mất 0,73 giây. Chưa phải kiểm tra bản ghi giọng người qua micro.
- YOLO local chạy CPU, thử một fixture tổng hợp 45+27: tải model 3,68 giây, lần suy luận đầu 3,10 giây, 10 lượt đã nạp có median 62,58 ms. Không suy ra độ chính xác OCR chữ viết tay từ mẫu này.
- Bộ chuẩn hóa phát âm biến “Bài 3: (2 điểm), 2 đề-xi-mét” thành “Bài 3. 2 đề xi mét”; đây là kiểm tra chuỗi đầu vào TTS, chưa phải đánh giá cảm nhận giọng trên điện thoại.

## Khởi động và giới hạn bằng chứng

Worktree `C:\Users\Admin\.codex\worktrees\kha-catalog-review\MathVisionKid` là nhánh cũ hơn, dùng junction node_modules sang ổ E. Trong worktree đó, bundle không resolve được expo-router/entry. Khi chạy đúng bản E, bundle Android trả 200. Đã tắt Metro của worktree cũ và để Expo của bản E chạy trên cổng 8081. Backend 8080 và AI 8000 cũng đang chạy sau kiểm tra.

ADB không liệt kê thiết bị. Chưa xác nhận UI, micro, phát âm thanh hay độ mượt thanh tua trên Android thật. Không cam kết không bao giờ lỗi dựa trên các bộ test tự động.

## Việc cần ưu tiên

1. Xử lý cấu hình khóa bị AUTH_ERROR/429 và xác nhận lại đường dự phòng tạo kế hoạch.
2. Điều tra các lượt Edge TTS trả không có âm thanh, kiểm thử lại đoạn dài và hai giọng trước khi công bố ổn định.
3. Đồng bộ test thông báo lỗi với hành vi mong muốn và xử lý hai lỗi lint Quiz.
4. Kiểm tra thực tế trên Expo Go Android: bài mới, thao tác nhanh, đổi giọng, đoạn dài và mất mạng.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Rà soát code và xác minh bằng các kiểm thử có sẵn, giữ phạm vi kiểm tra gọn.
  - Applied to: Chọn bộ kiểm thử, truy nguyên lỗi khởi động theo checkout, phân biệt lỗi runtime với test/cấu hình; không thêm mã ứng dụng.

Bằng chứng số đo nhà cung cấp và hạ tầng: [performance.json](performance.json). Nội dung thử là đề công khai và âm thanh tổng hợp, không chứa token đăng nhập hoặc khóa API.
