# Tăng khả năng phục hồi khi chuẩn bị lời giải

Ngày: 01/11/2026. Checkout: `E:/MathVisionKid`. Đã nạp bản sửa vào runtime local; chưa commit/push.

## Quyết định: giữ bộ kiểm chứng

Không bỏ kiểm chứng chỉ để mọi yêu cầu trả thành công. Model có thể tính một biểu thức đúng nhưng chọn sai quan hệ, sai đơn vị hoặc trả lời nhầm đại lượng. Lời giải chỉ được mở khi qua kiểm tra cục bộ và kiểm tra độc lập, hoặc qua bộ giải chính xác có phạm vi nguồn được chứng minh.

Không thể cam kết mọi ảnh, mọi dạng toán và mọi tình trạng dịch vụ đều thành công. Thiếu dữ kiện thật sự vẫn phải giữ lại phần đã làm và yêu cầu làm rõ thay vì bịa đáp án.

## Điểm yếu tìm thấy

Hệ thống đã có Groq và Gemini được bật, có cấu hình khóa. Trước sửa, chuyển nguồn chủ yếu xảy ra khi lỗi truyền tải, timeout hoặc giới hạn yêu cầu. Nếu nhận JSON thành công nhưng kế hoạch không đạt kiểm tra, lần sửa nội dung có thể quay lại cùng nguồn. Ngoài ra, một nguồn có thể chiếm gần hết thời gian chung, khiến nguồn dự phòng không còn cửa sổ thực tế để hoàn tất.

`unavailable=true` còn có một đường thoát ngay trước vòng sửa nội dung, trong khi `lesson=null`/`canSolve=false` đã được xem xét lại có giới hạn. Đã thống nhất việc xem xét lại một lần; điều này không cho phép thông qua nguồn thiếu dữ kiện.

## Thay đổi trong lượt này

- Kết quả nội bộ của `_generate` lưu tên nguồn thực sự phản hồi bằng thuộc tính Python riêng; không thêm metadata này vào JSON/schema của học sinh.
- Khi kế hoạch không đạt kiểm tra hoặc từ chối ban đầu, lần sửa ưu tiên nguồn còn lại. Lựa chọn dựa trên nguồn thực sự trả kết quả, kể cả khi lần đầu đã chuyển nguồn vì lỗi mạng/quota.
- Kiểm tra ngữ nghĩa độc lập ưu tiên nguồn khác với nguồn soạn kế hoạch. Nếu nguồn đó không khả dụng, vẫn áp dụng luồng dự phòng hiện có; không khẳng định mọi lượt đều dùng được hai nhà cung cấp khác nhau.
- Khi có hai nguồn được cấu hình, mỗi lượt gọi nguồn bị giới hạn thời gian thực 14 giây, nằm trong hạn chung 30 giây của `_generate`. Tác vụ chậm bị hủy trước khi chuyển nguồn; không kéo dài hạn chuẩn bị của bài.
- Giữ nguyên hạn tối đa 38 giây cho một lần lập kế hoạch được kiểm chứng và 60 giây của tác vụ chuẩn bị nền. Một nguồn duy nhất vẫn giữ ngân sách gọi theo cấu hình cũ, tối đa 24 giây cho lời giải dài.
- Không gọi đồng loạt tất cả nguồn ở mỗi bài, không thêm dịch vụ/tài khoản trả phí, không quét khóa khác sau lỗi quota và không đổi model đã được cấu hình. Chỉ khóa bị xác thực không hợp lệ mới được vô hiệu hóa và bỏ qua theo cơ chế giới hạn đã có.

Các lớp dùng lại được giữ nguyên: catalog khớp đúng nguồn/tài khoản/chính sách → bộ giải số học chính xác phù hợp → model có dự phòng và sửa nội dung có giới hạn → kiểm tra ngữ nghĩa/đáp số độc lập. Không tính catalog hoặc bộ giải cục bộ là các nhà cung cấp model mới.

## Mở bài nhanh trong lúc chuẩn bị nền

Phần đọc hiểu tiếp tục được trích trực tiếp từ đề gốc; chưa cần đợi toàn bộ kế hoạch toán. Câu trả lời đọc hiểu được giữ lại trong khi chuẩn bị toán. Đáp số tương lai chưa được công bố. Giọng nền tiếp tục dùng lịch chuẩn bị hiện có và không chặn phản hồi mở bài.

Lượt này sửa đường tạo lời giải, không thay nhà cung cấp giọng. Edge TTS vẫn có lượt chậm/trả rỗng như đã ghi nhận trong báo cáo trước; không có căn cứ nói thay đổi nguồn model sẽ loại bỏ lỗi TTS.

## Kiểm thử tự động

- **547 passed**, 6,71 giây: các suite bài học, tách nguồn, đọc hiểu, chuẩn bị nền, catalog, bộ giải chính xác, tương tác và truyền tải tutor. JUnit tại `.local-artifacts/lesson-multisource-20261101/pytest.xml`.
- **36 passed**, 30,20 giây: hợp đồng model, key pool và bảo mật Gemini/Groq. Có bốn cảnh báo deprecation của thư viện. JUnit tại `.local-artifacts/lesson-multisource-20261101/provider-contracts.xml`.
- Tổng hai tập không trùng: **583 kiểm thử qua**. Không chạy lại toàn bộ frontend/Java vì lượt này không sửa các phần đó.
- Bộ mới kiểm tra ưu tiên nguồn, nguồn dự phòng bị tắt, hủy nguồn treo, hủy yêu cầu không để tác vụ thừa, cách ly lựa chọn giữa hai yêu cầu đồng thời, metadata giả trong JSON không thay được nguồn thực, từ chối nhầm ban đầu, lỗi tính toán cục bộ, phản biện ngữ nghĩa, và cả hai nguồn cùng đề xuất lời giải sai vẫn không được mở phiên.
- Cập nhật hai kỳ vọng cũ từ một sang hai lượt cho `unavailable=true`: vẫn xác nhận không mở phiên khi thiếu dữ kiện; thay đổi này phản ánh đúng việc xem xét lại có giới hạn.

## Đo nhà cung cấp thật

Chỉ dùng dữ liệu toán tổng hợp, khóa giữ trong bộ nhớ/cấu hình local; không lưu khóa vào artifact.

| Kiểm tra kết nối JSON | Thời gian | Kết quả |
|---|---:|---|
| Groq | 437,15 ms | Trả JSON đúng |
| Gemini | 1357,01 ms | Trả JSON đúng |

Có khóa Gemini không hợp lệ bị cơ chế có sẵn vô hiệu hóa trong lượt thử; sau đó vẫn có phản hồi từ nguồn. Không suy ra toàn bộ khóa đều khỏe hoặc nguồn dùng vô hạn.

| Bài mới qua luồng tạo và kiểm chứng thật | Kết quả đã đối chiếu | Toàn bộ kế hoạch sẵn sàng |
|---|---|---:|
| 8 túi × 7 viên, cho 9 viên | 47 viên | 8888,20 ms |
| 18 quyển, thêm 7, tặng 5 | 20 quyển | 6983,33 ms |
| Hình chữ nhật 13 cm × 7 cm, hỏi diện tích và chu vi | 91 cm² và 40 cm | 6243,93 ms |
| Chỉ cho tổng hai số bằng 70, hỏi hai số | Không bịa hai số | Từ chối sau 3904,87 ms |

Đây là mẫu nhỏ, không phải p95/p99 hay cam kết tốc độ cho mọi bài. Test chuyển nguồn do hỏng mạng/nội dung được thực hiện bằng giả lập có kiểm soát; kiểm tra nguồn thật xác nhận khả dụng và đáp án những bài trên, không cố gây lỗi nhà cung cấp thật để lấy số đo.

## Kiểm tra qua API local sau nạp bản sửa

Đề chưa dùng ở các lượt kiểm tra trên: “Có 9 hộp, mỗi hộp 8 viên bi. Cho đi 13 viên bi. Hỏi còn bao nhiêu viên bi?”

- Gọi chuẩn bị nguồn rồi mở bài: **50,43 ms** để nhận phần đọc hiểu.
- Ba câu trả lời đọc hiểu được nhận và lưu sau **84,13 ms** tính từ đầu lượt thử tự động.
- Toán sẵn sàng sau **6894,14 ms**; còn nguyên ba câu trả lời và revision tương ứng. Bước đầu là `9 × 8`, chưa lộ kết luận cuối.
- Nhật ký xác nhận `mode=reading-first` và toán hoàn tất ở revision 3 sau 6657 ms xử lý nền.
- Số đo qua HTTP local, không phải thao tác học sinh trên điện thoại; lượt trả lời tự động nhanh hơn thời gian đọc của người thật.

Đã nạp lại đúng dịch vụ AI sau khi xác minh tiến trình. Chẩn đoán runtime báo `READY_FOR_FULL_DEMO`; không khởi động lại các dịch vụ khác hoặc xóa dữ liệu. Tải lại app và mở phiên bài mới để thử.

## Giới hạn và phạm vi

- Không hứa 0 lỗi hoặc 1–3 giây cho toàn bộ lời giải mới. Phản hồi đọc đề mở sớm, còn toán cần được xác minh ở nền.
- Nhiều nguồn giúp phục hồi, nhưng vẫn chịu quota, mạng và khả năng suy luận của các nguồn được cấu hình. Retry/fallback có thể phát sinh thêm lượt API so với một lần thành công ngay.
- Giữ các thay đổi chưa commit khác, không sửa `.env.local`, không thay OCR model, không train và không động vào `demoUI`.
- Chưa kiểm chứng bằng điện thoại vật lý trong lượt này. Không commit/push.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa chuyển nguồn tại đường tạo dùng chung, tận dụng hai nguồn đã cấu hình, không thêm hạ tầng hoặc dependency.
  - Applied to: `service.py`, `generate_plan` trong `lesson.py`, kiểm thử phục hồi và phép đo thực.
