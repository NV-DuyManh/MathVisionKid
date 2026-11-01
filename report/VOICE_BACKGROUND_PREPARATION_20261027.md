# Chuẩn bị giọng đọc trong lúc học sinh đọc bài

Ngày: 27/10/2026. Đã triển khai vào mã Student dùng chung web/Android. Giữ nguyên Nam Minh và Hoài My; không tự chuyển sang giọng khác.

## Hành vi mới

Trước đây, mở sheet “Nghe giảng” mới bắt đầu tạo/tải tiếng. Nay, khi dịch vụ đã trả về bước học và học sinh đang đọc nội dung, ứng dụng tự chuẩn bị âm thanh của đúng bước đó.

1. Đọc lựa chọn giọng đang lưu và chuẩn bị giọng đó trước.
2. Khi giọng đang chọn đã tải xong, chuẩn bị giọng còn lại. Không để việc chuẩn bị giọng thứ hai cạnh tranh với giọng chính ngay từ đầu.
3. Bấm nghe khi đang tải sẽ tham gia cùng yêu cầu đang chạy, không tạo một yêu cầu trùng.
4. Bấm nghe khi đã tải xong sẽ lấy dữ liệu từ bộ nhớ; chỉ còn tạo tệp cục bộ và mở trình phát.
5. Đóng rồi mở lại sheet hoặc đổi sang giọng đã chuẩn bị sẽ dùng lại dữ liệu còn hiệu lực.

Phần tải trước không phát tiếng, không tạo player ẩn, không chiếm phiên ghi âm. Giọng chỉ phát sau thao tác của học sinh. Thay đổi không sửa âm sắc, tốc độ đọc, công thức phát âm toán hoặc chính sách chọn hai giọng.

## Phạm vi “chạy ngầm”

Đây là làm việc song song trong lúc **ứng dụng đang hoạt động và học sinh đang đọc bước học**, không phải dịch vụ chạy liên tục khi điện thoại khóa hoặc đã đóng app.

Chỉ chuẩn bị lời giảng đã được backend cấp cho bước hiện tại, gợi ý đã mở hoặc bước đã làm xong đang xem lại. Không gọi model để đoán trước đáp án bước chưa mở. Chưa thể tạo đúng lời giảng cá nhân hóa trước khi đề được xác nhận và dịch vụ trả về nội dung; cũng không thể biết sẵn câu hỏi mới mà học sinh chưa gửi.

Nếu bấm ngay khi bước vừa xuất hiện, yêu cầu vẫn có thể đang tạo giọng: tiếp tục chờ phần còn lại với thanh tải hiện có. Nếu đã tải xong, việc tạo/tải qua mạng không còn nằm trên đường bấm nghe. Không có cam kết 0 ms hoặc thành công với mọi tình trạng mạng/thiết bị/dịch vụ ngoài.

## Hủy, ưu tiên và dữ liệu riêng

- Cache nằm trong vòng đời màn hình bài học, không phải biến toàn cục dùng chung các tài khoản. Màn hình vốn được khóa theo học sinh và nguồn bài; thay học sinh hoặc nguồn bài sẽ tạo cache mới và hủy cache cũ.
- Khóa dữ liệu gồm phiên bài học, revision, nội dung đọc đã chuẩn hóa, voice ID và lựa chọn dự phòng. Không dùng âm thanh của giọng/phiên/nội dung khác để lấp chỗ trống.
- Mỗi nơi dùng dữ liệu giữ một lượt tham chiếu. Đóng sheet không hủy yêu cầu mà tác vụ chuẩn bị còn cần. Khi không còn nơi nào cần yêu cầu chưa xong, yêu cầu bị hủy; kết quả trả muộn không được đưa lại vào cache.
- Đổi bước, rời màn hình hoặc chuyển app vào nền sẽ ngừng phần chuẩn bị không còn cần. Trở về app đang hoạt động sẽ chuẩn bị lại hoặc dùng cache còn hợp lệ.
- Một yêu cầu nghe nội dung mới được ưu tiên: hủy phần tổng hợp suy đoán đang chờ mà không có người nghe sử dụng. Việc hủy phía ứng dụng không bảo đảm máy chủ bên ngoài ngừng xử lý ngay.
- Lỗi tải trước được giữ im lặng để không cản việc đọc bài. Kết quả lỗi không được cache; bấm nghe có thể thử lại bình thường. Trình phát báo lỗi thì bản cache tương ứng bị loại bỏ trước lần thử sau.
- Giới hạn cache: tối đa 4 kết quả đã tải, tổng tối đa 16 MiB; một kết quả không được tái sử dụng sau 5 phút. Việc loại dữ liệu hết hạn diễn ra khi cache được truy cập; đóng màn hình xóa toàn bộ tham chiếu cache. Các nơi đang nghe có thể còn giữ dữ liệu riêng cần thiết cho lần phát hiện tại.
- Không thêm thư viện, không sửa RBAC/backend, không lưu âm thanh tải trước vào kho lâu dài. Việc ghi tệp phát tạm vẫn dùng luồng đã có và xóa tệp khi đóng trình phát.

## Đo với máy chủ thật

Đã chạy chính mã TypeScript `narrationCache.ts`, `narrationApi.ts`, `narration.ts` bằng harness Node, gửi HTTP đăng nhập thật qua business backend, tạo một bài mẫu nhân tạo rồi gọi dịch vụ giọng thật. Không giả lập dữ liệu HTTP của lần đo này. Tài khoản kiểm thử đã đăng xuất sau phép đo; báo cáo không lưu token/mật khẩu.

Bài mẫu: 12 quả táo, cho đi 3 quả. Nội dung lời giảng được backend trả về dài 187 ký tự.

| Giọng | Tạo/tải trước | Lấy dữ liệu sau khi đã chuẩn bị | Yêu cầu mạng thêm khi lấy |
| --- | ---: | ---: | ---: |
| Nam Minh | 1.093,37 ms | 0,236 ms | 0 |
| Hoài My | 1.149,65 ms | 0,086 ms | 0 |

Hai lần lấy lại trả đúng cùng bộ đệm đã tải. Tổng có hai yêu cầu tải âm thanh, một cho mỗi giọng. Lần tạo bài học trong phép đo mất 6.504,86 ms, là thời gian chuẩn bị nội dung riêng với thời gian tạo giọng.

**Không lấy các số dưới 1 ms làm thời gian bấm-phát trên điện thoại.** Phép đo chỉ kết thúc khi bộ đệm âm thanh có sẵn; chưa tính tạo tệp, giải mã, thiết bị phát tiếng và thao tác giao diện. Đây là một mẫu đo, không phải trung vị, SLA hoặc chứng minh mọi bài đều mất khoảng một giây.

Dữ liệu gốc: [live-cache-benchmark.json](voice-prefetch-20261027/live-cache-benchmark.json). Harness: `runtime/voice-prefetch-benchmark-20261027.cjs`.

## Chi phí và giới hạn còn lại

Tải trước dùng văn bản đã có nên không gọi thêm model ngôn ngữ để tạo lời giải. Tuy nhiên, chuẩn bị cả hai giọng có thể tăng số lần tổng hợp và dữ liệu tải so với chỉ tải khi bấm nghe, đặc biệt khi học sinh không dùng âm thanh. Giọng còn lại chỉ bắt đầu sau giọng chính; dedup và cache hạn chế các lần lặp. Không thể gọi việc này là miễn phí/vô hạn hoặc không tốn tài nguyên.

Chất lượng hai giọng và các deadline 25/32/45 giây hiện có được giữ. Mạng mất, phiên hết hạn, dịch vụ ngoài chậm hoặc không phục vụ vẫn có thể làm lần tải trước thất bại. Các lựa chọn dự phòng vẫn phải do học sinh chủ động chọn. Nghiên cứu giới hạn nhà cung cấp ở [báo cáo trước](MFILM_LOADING_VOICE_LIMITS_20261027.md).

## Kiểm chứng

- **142 kiểm thử qua, 0 lỗi, 12 bộ**: cache/preparation, narration API/player, màn hình học, hỏi bài, nghe hiểu, tiến độ, video và giọng thiết bị.
- Kiểm thử mới bao phủ chia sẻ yêu cầu đang tải, dùng lại hai giọng, hủy một người dùng không làm hỏng lượt tải chung, loại kết quả muộn, lỗi rồi thử lại, TTL/LRU/dung lượng, ưu tiên yêu cầu thật, chuyển bước, đổi học sinh, nền/foreground và chỉ dùng nội dung đã mở.
- TypeScript và ESLint cho mã thay đổi đều qua; diff check qua.
- Export web và Android/Hermes thành công: `runtime/voice-prefetch-export-20261027`; log `runtime/voice-prefetch-export-20261027.log`.
- Chưa có đo bấm-phát trên điện thoại Android thật cho tính năng mới. Kiểm thử hook dùng môi trường React test renderer; phép đo HTTP dùng Node và backend thật, được phân biệt rõ ở trên.
- Không commit/push, không train model, không thay nhà cung cấp giọng đọc.

## Skills Applied

- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: tải dữ liệu sớm và chia sẻ yêu cầu giữa các component React.
  - Applied to: chuẩn bị khi đọc, loại chuỗi chờ khi bấm nghe, dependency theo nội dung/revision và lifecycle cleanup.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng luồng giọng hiện có, tránh thêm framework/cache toàn cục hoặc dịch vụ nền không cần thiết.
  - Applied to: cache bộ đệm giới hạn theo màn hình, giữ nguyên decoder/file/player và kiểm thử có thể chạy lại.
