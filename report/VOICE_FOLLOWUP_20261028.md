# Tiếp tục tối ưu giọng khi chưa kiểm tra lại điện thoại

Ngày 28/10/2026. Người dùng đã thông báo chưa thử bản sửa thứ hai và muốn tiếp tục làm, sẽ thử sau. Đợt này sửa hàng đợi và phục hồi tiếng ở máy chủ; không đổi hai giọng Nam Minh/Hoài My, không tăng giới hạn chờ, không huấn luyện model, không commit/push.

## Các sửa đổi mới

### Chuẩn bị giọng còn lại cho nội dung hiện tại sớm hơn

Trước đây hàng đợi hoàn thành toàn bộ giọng đang chọn rồi mới chuẩn bị giọng còn lại. Như vậy đổi giọng ngay ở bước đầu có thể phải đợi cả các bước ở xa.

Thứ tự mới ưu tiên hai nội dung gần nhất bằng giọng đang chọn, rồi giọng còn lại cho nội dung hiện tại, sau đó tiếp tục các phần xa hơn. Không tạo thêm loại kịch bản hoặc tăng số tài nguyên tiếng đã lên kế hoạch. Khi đang xem lại kết quả một bước, nội dung xem lại cũng được dùng để xác định ưu tiên.

Ứng dụng tiếp tục tải/lưu trước giọng đang chọn, dùng chung hàng đợi máy chủ và tệp đã có. Không khôi phục lượt tạo trùng cho giọng chưa chọn trên ứng dụng.

### Một cơ hội phục hồi cho lỗi không có âm thanh

Lỗi `NoAudioReceived` được phân loại riêng. Sau các lần thử truyền của thư viện, nếu vẫn không có tiếng, phần chuẩn bị có thể tạo lại thêm một lần trong **cùng hạn chót 45 giây**, giữ nguyên giọng và nội dung. Nếu vẫn không có kết quả hoặc không đủ thời gian thì dừng; không lặp vô hạn.

Việc tiếp tục dựa trên các đoạn đã hoàn thành vẫn được giữ. Trường hợp không có tiếng ở lượt đầu không còn buộc phần chuẩn bị ngừng ngay chỉ vì chưa có đoạn nào để phục hồi. Đường lấy tiếng trực tiếp dùng cho video cũng nhận một lần thử lại có giới hạn, trong hạn chót 39 giây vốn có để phù hợp đường HTTP nghiệp vụ.

Không thử lại lỗi chữ chưa công bố, sai quyền, sai revision, tệp không hợp lệ hoặc giọng dự phòng theo quy tắc này. Không tự đổi sang giọng khác. Lượt thử lại có thể phát sinh thêm yêu cầu TTS; không coi là miễn lượt hoặc miễn quota.

### Không để lỗi cũ che mất tác vụ mới

Đã xử lý trường hợp một công việc công khai cũ thất bại, trong khi tác vụ nền đang thực sự tạo lại cùng nội dung. Trạng thái mới theo dõi cả lượt render đang chạy; không trả `failed` chỉ vì công việc cũ có cờ lỗi. Chỉ trả `ready` khi WAV hợp lệ thực sự có trong bộ nhớ.

Kiểm tra quyền tài khoản, phiên, revision, chữ đã công bố và tách hai giọng vẫn giữ nguyên. Không mở khóa đáp án tương lai để đạt tốc độ.

## Kiểm thử đã chạy

**277 kiểm thử Python qua**, bao gồm:

- Cả hai lựa chọn giọng đều có thứ tự ưu tiên mới đúng.
- Lỗi không có tiếng chỉ được phục hồi thêm một lần khi không có tiến bộ; cùng giọng, cùng hạn chót.
- Lỗi kéo dài dừng đúng giới hạn; không tự bật giọng dự phòng.
- Công việc lỗi cũ không che tác vụ tạo mới đang chạy.
- Kiểm tra quyền, chữ tương lai, ghép tiếng đúng thứ tự, giữ kết quả qua chuyển bước, video và các hồi quy bài học/hội thoại.

Frontend không đổi trong đợt này. Bộ Student hiện tại đã qua 179 kiểm thử/17 bộ và xuất web/Android ở đợt trước; không cộng lại các kết quả đó thành lượt chạy mới. `git diff --check` qua.

Các đầu ra và dấu kiểm nguồn: [verification.json](voice-followup-20261028/verification.json). Log: `runtime/voice-followup-python-20261028.log`.

## Đo bằng giọng thật

Một bài phân số tổng hợp hai bước, dùng Edge TTS và ffmpeg thật, không phải thao tác trên Android:

| Phép đo trong một lượt | Kết quả |
|---|---:|
| Đủ 10 biến thể tiếng và 2 video | 27,922 giây |
| Bước đầu, Nam Minh sẵn sàng | 5,828 giây |
| Bước kế tiếp, Nam Minh sẵn sàng | 11,047 giây kể từ đầu hàng đợi |
| Bước đầu, Hoài My sẵn sàng | 15,063 giây kể từ đầu hàng đợi |
| Các mục thất bại trong lượt này | 0 |
| Yêu cầu đoạn tới dịch vụ | 18 |
| Yêu cầu nhà cung cấp thêm khi mở lại bản đã chuẩn bị | 0 |

Tổng kết ghép từ tiếng từng bước; âm thanh được kiểm tra định dạng và thời lượng. Đây là số đo một lượt, không phải cam kết tốc độ cố định. Thứ tự ưu tiên mới không làm phát sinh thêm các bản tiếng trong bài kiểm tra này. Không dùng chênh lệch thời gian giữa các lượt có điều kiện mạng khác nhau làm tỉ lệ cải thiện chắc chắn.

Chứng cứ: [real-followup-benchmark.json](voice-followup-20261028/real-followup-benchmark.json). Mẫu tổng kết: [Nam Minh](voice-followup-20261028/final-summary-Nam-Minh.wav), [Hoài My](voice-followup-20261028/final-summary-Hoai-My.wav).

**Lần tạo mới vẫn chưa đạt 1–3 giây đều đặn.** Việc phát gần ngay khi mở chủ yếu dựa vào chuẩn bị trước và dùng lại tệp; không thể coi phép đọc bộ nhớ máy chủ là độ trễ phát của điện thoại.

## Kiểm tra toàn luồng qua API: hai lượt không thành công

Hai lượt kiểm tra đăng nhập → tạo bài → chuẩn bị tiếng đều dừng ở bước tạo bài với HTTP 503, trước khi tới giọng:

1. Bộ kiểm tra độc lập từ chối lời hướng dẫn sinh ra vì nêu đáp án trước khi học sinh làm.
2. Nhật ký có phản hồi 429 từ nhà cung cấp model rồi dùng đường dự phòng; bản sinh tiếp tục bị từ chối vì vấn đề đơn vị/nguồn.

Không gọi đây là kiểm tra toàn ứng dụng đã qua, cũng không kết luận đó là lỗi TTS. Không nới kiểm tra chất lượng toán để lấy kết quả thành công. Sau hai lượt này không gửi thêm yêu cầu tạo bài để thử cho đến khi có kết quả đẹp.

Chứng cứ: [lượt đầu](voice-followup-20261028/http-first-attempt.json), [lượt sau](voice-followup-20261028/http-smoke.json), [ghi chú đối chiếu nhật ký](voice-followup-20261028/http-smoke-notes.json). Vấn đề tạo bài còn là giới hạn khi đánh giá toàn bộ trải nghiệm; các thay đổi đợt này không sửa prompt hoặc model tạo bài.

## Bàn giao

Đã nạp các sửa đổi mới vào dịch vụ đang chạy. Giới hạn chuẩn bị vẫn 45 giây; đường tải tiếng trực tiếp vẫn giữ 39 giây bên trong timeout nghiệp vụ. Không có lượt kiểm tra điện thoại mới sau khi người dùng thông báo sẽ thử sau. Kết quả Android 663 ms / 14.055 ms / 2.924 ms thuộc bản trước các sửa đổi sau cùng, không được dùng để chứng minh bản này đã đạt yêu cầu.

Khi kiểm tra lại sau, cần tải lại ứng dụng và mở bài mới vì máy chủ đã được nạp lại, phiên bài cũ lưu trong bộ nhớ có thể hết hiệu lực. Không ghi nhận thay cho người dùng rằng đã đạt 1–3 giây trên thiết bị.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa đúng các khâu ưu tiên/trạng thái/thử lại bằng cơ chế hiện có, không thêm dependency hay dịch vụ mới.
  - Applied to: hàng đợi hai giọng, phân loại lỗi không có tiếng, phục hồi trong hạn chót, kiểm thử và bằng chứng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: tiếp tục mục tiêu chuẩn bị sớm và dùng chung tài nguyên cho luồng React Native.
  - Applied to: đối chiếu luồng chuẩn bị trên ứng dụng với máy chủ; giữ việc tái sử dụng tệp và tránh công việc trùng. Frontend không thay đổi thêm trong đợt này.
