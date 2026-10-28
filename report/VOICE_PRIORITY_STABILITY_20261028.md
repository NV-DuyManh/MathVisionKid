# Sửa ưu tiên giọng, chuẩn bị nền và lỗi tạo bài

Ngày 28/10/2026. Tiếp tục theo yêu cầu của chủ dự án; chủ dự án thông báo chưa thử bản mới trên điện thoại và sẽ kiểm tra sau. Giữ nguyên Nam Minh, Hoài My và hạn chờ 45 giây. Không commit/push, không huấn luyện hoặc thay model OCR, không thay nhà cung cấp hay tự chuyển sang giọng chất lượng khác.

## Kết luận hiện tại

Đã sửa các lỗi có thể xác định trong mã và kiểm tra liên tầng: ranh giới hướng dẫn ban đầu/trợ giúp sâu, mã báo bận, hủy tác vụ nền cũ, nâng ưu tiên cùng tác vụ khi bấm nghe, giữ bộ nhớ tiếng và phục hồi lỗi đọc tiến độ. Đã nạp thay đổi vào hệ thống phát triển.

**Chưa đạt mục tiêu tiếng mới luôn sẵn sàng trong 1–3 giây.** Kiểm tra toàn luồng lần này tạo bài được, chuyển được đến bước toán, nhưng tiếng của cả hai giọng cuối cùng thất bại. Một phép thử riêng với câu ngắn, gọi lần lượt từng giọng, cũng không nhận được tiếng hợp lệ. Không ghi các kiểm thử mô phỏng hoặc thời gian đọc bộ nhớ thành kết quả phát thành công trên Android.

## Lỗi tạo bài: giữ đúng ranh giới riêng tư

Kịch bản model đã có `initialGuidance` và phần hướng dẫn giải sâu riêng. Mã chuyển đổi trước đây gộp chúng rồi chọn lại nội dung tự động bằng cách lọc chữ số. Một đoạn có đáp án viết bằng chữ như “bốn phần mười lăm”, hoặc hướng dẫn phép nghịch đảo với các số đã biết, có thể lọt vào hướng dẫn ban đầu. Bộ kiểm tra độc lập sau đó từ chối bài, tạo lỗi 503. Bộ kiểm tra đã làm đúng; không nới nó để làm bài vượt kiểm tra.

Đã giữ trường ranh giới ban đầu riêng trong kế hoạch máy chủ. Hiển thị trước khi làm chỉ lấy các đoạn đó, rồi vẫn kiểm tra nguồn/số liệu và thẩm định độc lập. Trường ranh giới không được xuất thành trường mới trong phản hồi học sinh hoặc lặp trong dữ liệu gửi thẩm định. Các hướng dẫn giải sâu vẫn xuất hiện đúng khi xin trợ giúp sâu hoặc làm xong. Danh sách ban đầu rỗng không được lấy lời giải riêng tư thay vào; payload kế hoạch kiểu cũ vẫn tương thích.

Khi thêm ba bước đọc hiểu, tham chiếu trong ranh giới này cũng được chuyển đúng chỉ số. Prompt được làm rõ: tham chiếu kết quả bước trước chỉ dùng trong các trường hướng dẫn/hints và công thức được phép; các trường tiêu đề/câu hỏi/giải thích tự động không dùng ngoặc nhọn chưa được xử lý. Không chuẩn hóa tùy tiện đơn vị sai, không bỏ kiểm tra bài thiếu dữ kiện và không bảo đảm model sẽ không bao giờ tạo bài bị từ chối.

## Giọng: phân biệt đang đọc với đã bấm nghe

### Cờ chuẩn bị nền xuyên suốt ứng dụng và máy chủ

Thêm `prefetch` dạng boolean, mặc định `false`, qua Student → API nghiệp vụ → dịch vụ giọng. Chủ sở hữu vẫn lấy từ xác thực máy chủ; cờ này chỉ điều khiển ưu tiên, không cấp quyền đọc chữ hoặc đáp án. Chữ, phiên, revision, giọng và chế độ dự phòng vẫn được kiểm tra như trước.

Lượt tải trong khi đọc bài mang `prefetch:true`. Khi học sinh thực sự bấm nghe một lượt đang chuẩn bị, ứng dụng gửi yêu cầu nâng ưu tiên cho **cùng nội dung và tác vụ**, giữ lại tệp/tải đang chờ. Không tạo một lượt tải TTS thứ hai chỉ vì mở bảng nghe. Cờ ưu tiên không tạo ra một khóa âm thanh khác.

Việc nâng ưu tiên không cấp thêm 45 giây. Client giữ hạn chót ban đầu, chỉ gửi yêu cầu nâng ưu tiên trong thời gian còn lại và dùng cùng tín hiệu hủy. Nếu yêu cầu nâng ưu tiên tức thời gặp lỗi, lượt tải đang hợp lệ không bị hủy; các lần thử bắt đầu lại trong lượt tải đó cũng mang ưu tiên đã đổi.

### Bước cũ nhường chỗ, lượt nghe đang dùng được bảo vệ

Máy chủ giữ tín hiệu hủy cho tác vụ nền từ khi xếp hàng. Chuyển bước sẽ hủy các lượt `prefetch` của revision cũ; đổi giọng hoặc bỏ bài cũ cũng hủy phần nền tương ứng. Việc đang nối vào một tác vụ chia sẻ được kiểm tra hủy thường xuyên, không giữ chỗ thêm hàng chục giây chỉ vì đợi tác vụ khác.

Khi đã bấm nghe, tác vụ được nâng ưu tiên và bảo vệ bằng cơ chế người nghe đang chờ. Nó dùng cùng hạn chót và không tạo lại phần đã xong. Tệp của lượt nghe công khai đã được phép vẫn có thể được lưu riêng khi học sinh chuyển bước; mọi lần đọc công khai tiếp theo tiếp tục kiểm tra revision hiện tại. Tác vụ nền đã bị bỏ ở revision cũ không được coi là lỗi cuối cùng của một yêu cầu mới ở revision mới có cùng lời đọc.

Đã kiểm thử cả trường hợp yêu cầu nâng ưu tiên đến đúng lúc việc nền đang nhường chỗ: lượt nghe tiếp tục trong tác vụ và hạn chót cũ, không dùng kết quả bị hủy làm lỗi giả của lượt nghe mới.

Trong kiểm tra qua dịch vụ thật, các lượt nền cũ bị hủy ghi nhận thời gian render khoảng **30–155 ms** ở những lần chuyển nhanh đầu bài. Đây là thời gian các lượt cụ thể trong nhật ký, không phải cam kết mọi hủy tác vụ luôn mất từng đó thời gian.

## Các lỗi phụ gây chờ hoặc thất bại giả

- API giọng nội bộ báo bận bằng 429 nhưng đường prepare/status ở API nghiệp vụ từng đổi thành 503. Đã giữ **429 / NARRATION_BUSY** cho đúng hai đường này, để ứng dụng thử lại trong cùng hạn 45 giây. Các đường model khác không bị đổi chính sách lỗi. Payload WAV không cần mang cờ ưu tiên mới.
- Một lần đọc tiến độ gặp timeout/mất mạng/5xx tạm thời không còn làm hủy ngay việc tạo tiếng đang chạy. Chỉ thử lại đọc trạng thái, giữ tác vụ và hạn chót. Lỗi quyền, revision, đầu vào và cấu trúc trạng thái không hợp lệ vẫn dừng.
- Nếu WAV đã hết hạn hoặc bị dọn và trạng thái thật là `waiting`, client có thể gọi chuẩn bị lại theo cách idempotent thay vì chỉ hỏi mãi tới hết 45 giây. Không tạo lại mỗi lần gặp lỗi mạng.
- Dọn lịch sử tiến độ không còn xóa WAV đang được dùng gần đây. WAV tiếp tục có giới hạn riêng về số tệp, dung lượng và thời gian sống.
- Các timeout HTTP được chặn dưới ít nhất 1 ms, tránh giá trị 0 vô tình làm Axios mất hạn chờ ở sát hạn chót.
- Kiểm thử điều hướng màn bài học được cô lập khỏi đường HTTP giọng đang chạy thật; kiểm thử giọng chuyên biệt vẫn kiểm tra quá trình tải/chuẩn bị đầy đủ. Không tăng timeout Jest để che một lần kiểm tra giao diện bị quá hạn.

## Kiểm thử và rà soát

| Nhóm kiểm tra | Kết quả |
|---|---:|
| Python: bài học, lời hướng dẫn, giọng, video, hàng đợi và quyền | 293 qua |
| Student: nghe, bộ nhớ, chuẩn bị, API, ghi âm, tua và màn bài học | 209 qua / 17 bộ |
| Java: service và controller | 141 qua (91 + 50) |
| Tổng | **643 qua** |

TypeScript qua; lint 0 lỗi, còn 2 cảnh báo cũ trong `cropRotation.web.ts`. Xuất web và Android qua. Web dùng địa chỉ HTTPS mẫu chỉ cho kiểm tra build, không triển khai địa chỉ đó. Android ở đây là xuất bundle, không phải thử cài APK trên điện thoại.

Có các kiểm thử chặn đọc lời tương lai, khác tài khoản/giọng/revision, hủy hai lượt nền để giải phóng chỗ, nâng ưu tiên cùng tác vụ một lần, bảo vệ người đang nghe, phục hồi lỗi tiến độ và giữ cùng hạn 45 giây. Đã chặn thêm trường hợp nâng ưu tiên đến ngay sau khi worker đã dọn xong nhưng Future chưa kịp báo hoàn tất, tránh giữ nhầm bộ đếm người nghe. Đã rà soát độc lập các thay đổi về ranh giới hướng dẫn, quyền và timeout; sau đó tích hợp thêm phần ưu tiên/hủy và chạy lại toàn bộ nhóm kiểm tra ở trên.

Tổng hợp log và dấu kiểm nguồn: [verification.json](voice-priority-20261028/verification.json). Log Java: `runtime/voice-priority-contract-java-20261028.log`; Python/Student/typecheck/lint/export: `runtime/voice-priority-*-20261028.log`.

## Kiểm tra toàn luồng thật — tiếng chưa đạt

Đề tổng hợp vườn cây, đăng nhập qua API nghiệp vụ, sử dụng model tạo bài và dịch vụ giọng đang chạy thật:

- Không đăng nhập: HTTP 401.
- Tạo bài: HTTP 200, **7,614 giây** trong lượt này. Phản hồi không chứa `correctChoice` hoặc trường riêng `initialGuidance`.
- Ba yêu cầu chuẩn bị nền tại các bước đọc hiểu đều HTTP 200. Chuyển tới bước toán chỉ số 3 thành công; ba đoạn hướng dẫn ban đầu, tổng nội dung nghe 830 ký tự trước đổi cách đọc toán.
- Có gửi chuẩn bị nền tại bước toán trước cửa sổ đọc mô phỏng **15 giây**. Khoảng đọc này được ghi riêng, không giấu trong phép đo mở tiếng.
- Nam Minh vẫn đang tạo sau cửa sổ đọc; sau khi mô phỏng bấm nghe, chờ thêm **39,161 giây** rồi báo `failed`.
- Hoài My chưa có tệp khi kiểm tra; lượt nghe trực tiếp tiếp theo chờ **34,159 giây** rồi báo `failed`.
- Không có tệp WAV hoàn chỉnh để tải trong hai lượt này. Nhật ký cho thấy `NoAudioReceived` và timeout, không phải đã tải tệp nhưng loa im lặng.

Chứng cứ: [http-smoke.json](voice-priority-20261028/http-smoke.json). Trường `probeCompleted` chỉ có nghĩa chương trình đo chạy xong các bước; `success:false` và `allVoicesUltimatelyReady:false` ghi rõ tiếng không đạt. [Bản quan sát ban đầu](voice-priority-20261028/http-observations-original.json) được giữ để không che cách chương trình đo ban đầu đặt cờ hoàn thành.

Lượt kiểm tra trước khi hoàn thiện hợp đồng ưu tiên cũng được giữ riêng: [http-before-priority-fix.json](voice-stability-20261028/http-before-priority-fix.json). Bài đã tạo được nhưng tiếng chưa sẵn sau cửa sổ đọc; không ghi thành thành công giọng.

### Kiểm tra cô lập bằng câu ngắn

Gọi lần lượt, không gọi song song, cùng một câu tiếng Việt tổng hợp **189 ký tự**:

- Nam Minh: không có tiếng hợp lệ trong giới hạn thử **12,004 giây**; lỗi timeout.
- Hoài My: lỗi `NoAudioReceived` sau **8,954 giây**.

Chứng cứ: [provider-isolation.json](voice-priority-20261028/provider-isolation.json). Kết quả cho thấy lần lỗi này không chỉ xuất hiện vì bài toán dài hoặc do mở bảng nghe. Tuy nhiên, chưa đủ bằng chứng để kết luận quota bị khóa, IP bị giới hạn hoặc nhà cung cấp đã ngừng dịch vụ. Không thay suy đoán đó thành kết luận chắc chắn, không tiếp tục gọi lặp đến khi có một kết quả đẹp để báo cáo.

## Trạng thái bàn giao và giới hạn

Đã nạp các sửa đổi máy chủ và hợp đồng API mới; Student đã được sửa, kiểm tra kiểu và xuất bundle. Người dùng chưa thử bản sau cùng trên điện thoại và đã nói sẽ thử sau. Lần kiểm tra tiếp theo cần tải lại app và mở bài mới vì dịch vụ vừa được nạp lại, phiên bài cũ nằm trong bộ nhớ có thể hết hiệu lực.

Không tự đổi sang giọng thiết bị hoặc giọng khác để làm đẹp số đo. Nút dự phòng thủ công hiện có vẫn là lựa chọn khi tiếng chính không khả dụng. Chưa có tuyến dịch vụ chính thức khác với thông tin truy cập sẵn sàng đã được kiểm chứng cho đúng hai giọng này. Vì vậy **chưa thể bảo đảm mục tiêu 1–3 giây khi phải tạo mới**, nhất là khi dịch vụ đang trả lỗi; không tuyên bố đã hoàn hảo. Những lỗi của hàng đợi và báo tiến độ đã sửa được không thay thế được việc dịch vụ thật cần trả về âm thanh.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa ranh giới dữ liệu, ưu tiên công việc và ánh xạ lỗi bằng cơ chế hiện có; không thêm dependency hoặc tăng đồng thời để ép tốc độ.
  - Applied to: kế hoạch bài học, hàng đợi giọng, API Python/Java, giới hạn tài nguyên, kiểm thử và bằng chứng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: dùng chung lượt tải/chuẩn bị trong React Native, tránh bắt đầu lại và xử lý vòng đời yêu cầu.
  - Applied to: cờ prefetch, nâng ưu tiên khi bấm nghe, bộ nhớ tiếng, phục hồi polling trong hạn chót, kiểm thử Student.
