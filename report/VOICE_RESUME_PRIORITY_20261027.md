# Cải thiện phục hồi và ưu tiên giọng đọc

Ngày: 27/10/2026. Giữ Nam Minh và Hoài My; không đổi mô hình, giọng, tốc độ tổng hợp hoặc cách mã hóa âm thanh để lấy tốc độ.

## Những điểm đã sửa

### 1. Không tạo lại các đoạn giọng đã hoàn tất khi một đoạn khác lỗi

Trước đây, lời giảng dài được chia thành nhiều lượt gửi dịch vụ. Nếu một lượt lỗi, các lượt đã thành công cũng bị bỏ theo cả yêu cầu; lần thử lại gửi lại toàn bộ.

Đã thêm bộ lưu tạm các đoạn hoàn tất. Khi thử lại đúng nội dung và giọng, hệ thống chỉ gọi dịch vụ cho phần còn thiếu, sau đó ghép đúng thứ tự và kiểm tra toàn bộ WAV trước khi trả về. Không trả tiếng bị thiếu đoạn để giả vờ hoàn tất.

Bộ lưu tạm gắn với chủ sở hữu, phiên học, giọng và toàn bộ nội dung yêu cầu. Giới hạn 8 mục/8 MiB, thời hạn tối đa 5 phút và không vượt phiên học. Khi âm thanh hoàn chỉnh đã được kiểm tra, phần lưu tạm được bỏ; lỗi giải mã hoặc kết quả không hợp lệ cũng làm bỏ phần tạm để tránh dùng lại dữ liệu hỏng. Bộ đệm WAV hoàn chỉnh vẫn giữ giới hạn riêng hiện có.

Việc nhường tác vụ nền cho yêu cầu trực tiếp vẫn giữ các đoạn đã hoàn tất để có thể tiếp tục sau đó. Mọi kiểm tra chủ phiên, revision và nội dung đã mở vẫn diễn ra trước khi dùng dữ liệu.

### 2. Đổi giọng cập nhật ngay hàng đợi toàn bài

Trước đây, hook chuẩn bị chỉ đọc lựa chọn đã lưu khi bắt đầu. Đổi giọng trong bảng nghe có thể chưa đổi thứ tự hàng đợi của các bước sau cho tới khi mở lại màn hình.

Đã nối sự kiện thay đổi giọng tới phần chuẩn bị. Chọn giọng mới cập nhật ngay yêu cầu ưu tiên gửi máy chủ và việc tải trước ở ứng dụng. Tác vụ nền chưa có người nghe trực tiếp chờ ở giọng cũ được nhường lại; các đoạn đã xong vẫn được giữ. Không hủy một tác vụ đang có yêu cầu nghe trực tiếp dùng chung.

Khi ứng dụng ra nền, thay đổi lựa chọn được ghi nhận nhưng không khởi động tải mới ở điện thoại; quay lại mới tiếp tục theo giọng mới. Hàng đợi máy chủ giữ hành vi chuẩn bị nền đã có. Rời màn hình hủy đăng ký theo dõi để tránh công việc thừa.

### 3. Tránh lưu nhầm lựa chọn khi đổi giọng nhanh

Các lần lưu lựa chọn được xếp theo thứ tự. Phần khác của ứng dụng đọc được giọng vừa chọn trong lúc lưu còn đang chạy, giúp tránh mở video bằng lựa chọn cũ. Nếu lưu trữ cục bộ lỗi, lựa chọn mới vẫn dùng được trong tiến trình và lần lưu tiếp theo có thể phục hồi.

## Thử với dịch vụ giọng thật

Dùng lời giảng phân số tổng hợp dài 3 đoạn, gọi đúng hai giọng thật. Phép thử **chủ động chèn một lần ngắt sau khi một đoạn thật đã hoàn tất** để kiểm tra phục hồi; không báo lần ngắt giả lập này như một sự cố mạng quan sát được. Không gọi LLM để tạo kế hoạch trong phép đo này.

| Kết quả | Nam Minh | Hoài My |
|---|---:|---:|
| Phần còn thiếu tạo xong ở lần thử lại | 1.431 ms | 1.269 ms |
| Thời lượng bản tiếng hoàn chỉnh | 51,504 giây | 50,544 giây |
| Số lần yêu cầu lại đoạn đầu đã thành công | 0 | 0 |
| Lấy lại WAV đã có trong tiến trình | 0,070 ms | 0,055 ms |
| Yêu cầu nhà cung cấp phát sinh khi lấy lại WAV | 0 | 0 |

Toàn phép thử ghi nhận 8 yêu cầu thực tới nhà cung cấp. Các yêu cầu đã khởi động rồi bị ngắt vẫn có thể tiêu thụ tài nguyên; lưu tạm không biến việc thử lại thành miễn quota. Số đo lấy WAV trong tiến trình không bao gồm truyền mạng, lưu tệp, mở trình phát hoặc bấm-phát trên điện thoại. Không suy ra phần trăm tăng tốc chung từ một lượt thử.

Bằng chứng:

- [Kết quả phục hồi thật](voice-resume-20261027/real-resume.json).
- [Mẫu Nam Minh](voice-resume-20261027/Nam-Minh.wav).
- [Mẫu Hoài My](voice-resume-20261027/Hoai-My.wav).
- [Kiểm tra và mã băm nguồn](voice-resume-20261027/verification.json).

## Kiểm thử và phạm vi xác nhận

- 259 kiểm thử Python liên quan giọng, video, hàng đợi, hỏi đáp và bài học qua.
- 156 kiểm thử phía học sinh trong 16 nhóm qua.
- TypeScript qua. Lint không lỗi; còn hai cảnh báo cũ ở `cropRotation.web.ts`.
- Xuất web và Android thành công, dùng cấu hình địa chỉ HTTPS cho kiểm tra bản dựng. Không triển khai lên môi trường công khai.
- Bao gồm kiểm thử tiếp tục đúng đoạn còn thiếu, đúng thứ tự, tách giọng/nội dung/chủ phiên, giới hạn bộ nhớ/thời hạn, đổi ưu tiên, bảo vệ người nghe trực tiếp, đổi giọng khi ứng dụng ra nền, bỏ đăng ký khi rời màn hình và thứ tự lưu lựa chọn.

Không có xác nhận phát/tua trên Android thật hoặc kiểm tra trực quan bằng trình duyệt trong lượt này. Các máy chủ nội bộ không chạy khi kiểm tra cuối, nên không nhận đây là một lượt đo HTTP mới qua toàn bộ hệ thống. Phép đo HTTP 156 ms/47 ms ở báo cáo trước là bằng chứng của lượt trước; phép đo ở đây chạy trực tiếp các hàm sản phẩm với dịch vụ TTS thật và ngắt có kiểm soát.

## Phần còn phụ thuộc bên ngoài

Các thay đổi này giảm công việc phải làm lại và tránh chuẩn bị sai ưu tiên; không bảo đảm mọi lần tạo mới đều nhanh. Nếu nhà cung cấp không trả âm thanh, hệ thống vẫn áp dụng timeout và số lần thử hữu hạn, giữ phần chữ để học sinh dùng và cho phép thử lại. Không tự đổi sang giọng khác để che lỗi.

Đường Edge TTS hiện tại không có hạn mức tài khoản công bố trong README đã kiểm tra để khẳng định dùng vô hạn. Muốn vận hành với quota được công bố rõ ràng cần đánh giá dịch vụ chính thức và cấu hình tài khoản riêng; chưa chuyển nhà cung cấp trong lượt này. [edge-tts](https://github.com/rany2/edge-tts), [quota Azure Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits).

Không commit/push; không huấn luyện hay thay mô hình OCR. Các thay đổi OCR và tệp khác sẵn có được giữ nguyên.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: xử lý nguyên nhân tạo lại dữ liệu bằng bộ lưu tạm nhỏ và dùng lại giới hạn/render hiện có.
  - Applied to: khôi phục đoạn TTS đã hoàn tất, giới hạn bộ nhớ và thời hạn, nhường tác vụ nền đúng giọng; không thêm thư viện hoặc dịch vụ.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: cập nhật chuẩn bị theo lựa chọn người dùng mà không chặn giao diện hoặc giữ tác vụ thừa.
  - Applied to: đăng ký/hủy sự kiện đổi giọng, vòng đời hook theo ứng dụng, bỏ kết quả cũ, tuần tự hóa lưu lựa chọn.
