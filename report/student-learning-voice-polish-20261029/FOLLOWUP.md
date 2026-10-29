# Dùng lại giọng khi xử lý lại câu trả lời — 29/10/2026

Đã sửa việc tải lại tệp khi backend cấp một lượt xử lý mới nhưng lời đọc, giọng và phiên học không đổi. App chuyển tệp đã tải xong sang lượt mới, giữ nguyên thời hạn lưu và vòng đời tệp. Bản giọng nam/nữ hiện tại và chất lượng tổng hợp được giữ nguyên.

## Ranh giới dùng lại

- Chỉ dùng tệp hoàn chỉnh, còn hạn, trong cùng phiên học, cùng giọng, cùng chế độ đọc và nội dung đã chuẩn hóa giống hệt.
- Yêu cầu đang chạy ở lượt cũ vẫn bị tách riêng; không chuyển lời đọc chưa hoàn thành sang lượt mới.
- Tệp còn được player cũ hoặc player mới giữ sẽ chưa bị xóa. Sau khi mọi player nhả tệp, việc thu hồi diễn ra đúng một lần.
- Bộ lưu trữ vẫn tách theo vòng đời màn hình/tài khoản, tối đa 4 mục và 16 MiB. Dùng lại tệp không gia hạn thêm 5 phút lưu.

Đây là tối ưu tệp âm thanh đã được cấp cho học sinh. Backend tiếp tục xác thực mọi yêu cầu mới; client không tải sẵn hay mở lời giải chưa được cấp.

## Kiểm chứng

- **207/207** kiểm thử Student liên quan qua, gồm 4 ca mới về chuyển tệp, player còn giữ tệp, không chuyển request đang chạy, và không kéo dài hạn lưu.
- Kiểm tra web thật tại 320/390/768/1440 px qua. Với dữ liệu bài học cố định, sau một câu sai làm đổi revision nhưng giữ nguyên lời đọc, mở nghe lại không phát sinh lần tải WAV nữa. Xem `noDuplicateDownloadForSameRetrySpeech` trong `visual-qa.json`.
- Câu đúng vẫn giữ mọi lựa chọn, câu sai vẫn cho chọn lại, giọng đã chọn vẫn được giữ. Player tải/phát/tạm dừng được tệp giọng mẫu thật.
- TypeScript qua. Bundle Android xuất thành công; lint không có lỗi, còn hai cảnh báo cũ ở `cropRotation.web.ts`.
- Chưa có kiểm chứng trên điện thoại Android thật cho lượt sửa này.

## Số đo giọng qua dịch vụ thật

Một phiên đọc đề mới có xác thực Student, kịch bản rút gọn 139 ký tự, hai đoạn:

| Phép đo | Nam | Nữ |
|---|---:|---:|
| Chuẩn bị âm thanh chưa có cache | 10.318 ms | 12.905 ms |
| Tải WAV đã chuẩn bị | 14 ms | 14 ms |
| Độ dài âm thanh | 10,42 giây | 10,66 giây |
| HTTP chuẩn bị/tải âm thanh | 200 / 200 | 200 / 200 |

Mở phần **đọc đề** mất 47 ms trong lượt đo này. Không dùng con số đó để mô tả thời gian hoàn tất toàn bộ kế hoạch toán. Xem `live-reading-followup.json`.

Nhật ký truyền giọng ghi nhận có lượt âm thanh đầu tới khoảng 0,5 giây, có lượt hơn 11 giây; xử lý/đổi định dạng sau khi nhận dữ liệu trong các dòng kiểm tra khoảng 60–80 ms. Có lượt dịch vụ không trả âm thanh và lần thử tiếp theo mới thành công. Bằng chứng lọc bỏ văn bản học sinh/định danh tại `provider-timings.json`.

Vì vậy việc dùng lại tệp và chuẩn bị ngầm giúp tránh gọi lại nhà cung cấp, nhưng **chưa bảo đảm 1–3 giây cho mọi lần tổng hợp mới**. Đo tải WAV 14 ms là qua API ở máy kiểm tra, không phải thời gian bấm đến phát trên điện thoại. Không coi kiểm tra dữ liệu bài học cố định là kết quả model mới.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Loại bỏ việc tải trùng bằng cache hiện có, tránh thêm lớp lưu trữ.
  - Applied to: Chuyển mục đã hoàn thành, giữ giới hạn bộ nhớ/hạn lưu và thu hồi tệp.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Quản lý dữ liệu bất đồng bộ và vòng đời player React Native.
  - Applied to: Dùng lại tệp giữa hai lượt đã được backend xử lý, bảo vệ player còn giữ tệp.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Kiểm tra trải nghiệm nghe lại và trạng thái lựa chọn.
  - Applied to: Luồng sai/chọn lại/nghe lại, giữ lựa chọn giọng và kiểm tra 4 kích thước web.
