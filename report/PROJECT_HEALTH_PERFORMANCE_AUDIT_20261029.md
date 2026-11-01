# Kiểm tra trạng thái và hiệu năng — 29/10/2026

## Kết luận

**Chưa đủ cơ sở gọi toàn bộ dự án ổn định.** Docker đã được chủ dự án bật lại và ba dịch vụ hạ tầng đều khỏe. Tuy nhiên, phép thử thật vẫn có một bản soạn bài bị từ chối, một lượt nhận tiếng nói thất bại rồi thử lại mới thành công, và tạo giọng mới vẫn vượt mục tiêu 1–3 giây.

Đây là lượt **kiểm tra**, không sửa mã ứng dụng/cấu hình, không train model, không khởi động lại dịch vụ ứng dụng, không commit/push. Chỉ thêm bộ đo và bằng chứng. Các thay đổi ứng dụng có sẵn từ lượt trước được giữ nguyên.

## Trạng thái sau khi bật Docker

Kiểm tra lại lúc 08:29 ngày 29/10, múi giờ Việt Nam:

| Thành phần | Kết quả |
|---|---|
| PostgreSQL | Container healthy; phép đọc `SELECT 1` thành công |
| Redis | Container healthy; 30 lệnh PING qua TCP thành công |
| MinIO | Container healthy; 30 yêu cầu readiness HTTP thành công |
| AI, Business API, Student, Portal, Teacher, Admin | Chưa truy cập được tại các cổng cấu hình cục bộ |

Bật Docker khôi phục hạ tầng; không tự khởi động những tiến trình ứng dụng chạy ngoài container. Không coi trạng thái ứng dụng chưa bật là bằng chứng mã ứng dụng hỏng. Vì giữ phạm vi chỉ kiểm tra, tôi không tự chạy launcher.

Bằng chứng: `project-audit-20261029/docker-recheck.json`, `performance.json`. `/health` không thay thế một luồng nghiệp vụ đầy đủ.

## Số đo mới

### Hai giọng hiện tại

Dùng đúng hàm tạo lời giảng của dự án, nhà cung cấp đang cấu hình là Edge. Phiên cho phép đọc văn bản là fixture riêng trong tiến trình kiểm tra; âm thanh được tạo thật, không mock nhà cung cấp. Không gửi dữ liệu cá nhân học sinh.

| Nội dung | Nam Minh: tạo mới | Hoài My: tạo mới | Độ dài âm thanh |
|---|---:|---:|---:|
| Đoạn ngắn, 140 ký tự | 3,47 giây | 3,98 giây | Khoảng 10 giây |
| Đoạn dài, 606 ký tự | 10,06 giây | 13,53 giây | Khoảng 42,6 giây |

Cả bốn lượt trả WAV đầy đủ, đúng định dạng, có tín hiệu âm thanh khác không. Đây **không phải** đánh giá nghe bằng tai hoặc thử loa điện thoại. Mỗi ô tạo mới chỉ có một quan sát, không phải p95 hoặc cam kết độ trễ.

Sau khi có WAV, mỗi trường hợp đọc cache 30 lần: p95 từ **0,020 đến 0,072 ms**. Đây chỉ là trả byte trong bộ nhớ cùng tiến trình, **không bao gồm tải qua HTTP, mạng điện thoại, giải mã và bắt đầu phát**. Cache nhanh không chứng minh lần đầu luôn sẵn sàng trong ba giây.

Kết luận: tạo mới chưa đạt mục tiêu 1–3 giây trong bốn phép thử này; chuẩn bị trước và cache vẫn có giá trị khi thực sự hoàn thành trước lúc học sinh bấm nghe. Không từ bốn mẫu suy ra tỷ lệ thành công chung.

### Soạn bài và chuẩn bị nền

Hai bài được thử bằng model thật trong tiến trình kiểm tra riêng, không qua HTTP hay điện thoại. Mỗi bài dùng tài khoản kiểm tra riêng và cache trống; gọi chuẩn bị kín trước khi mở phần đọc hiểu.

| Bài | Mở đọc hiểu | Chuẩn bị phần toán | Mở từ cache đã kiểm tra | Kết quả |
|---|---:|---:|---:|---|
| Nền nhà dài 8 m, gạch 4 dm, giá 250 000 đồng/2 m² | 6,65 ms | 18,386 giây đến trạng thái unavailable | Không có | Không tạo được bản đạt kiểm tra trong lượt này |
| Biến thể dài 6 m, gạch 3 dm, giá 180 000 đồng/2 m² | 7,00 ms | 12,521 giây đến ready | 3,20 ms | Hoàn thành; 200 viên, 1.620.000 đồng |

**Chạy nền có hoạt động trong phép thử hàm:** phần đọc hiểu xuất hiện khi phần toán đang được chuẩn bị. Điều này chưa chứng minh bản trên điện thoại thực sự đã nạp hiệu ứng chuẩn bị nền, vì app chưa chạy và chưa thử điện thoại trong lượt này.

Lượt bài gốc thất bại do kiểm tra nội dung: lần đầu ghi nhận số `0` chưa được phép trong hướng dẫn ban đầu; lượt sửa bị bộ kiểm tra độc lập từ chối phần gợi ý có bước tính/thuật toán làm bài trước lúc học sinh tự làm. Đề không thiếu dữ kiện. Đây là lỗi đầu ra/kiểm tra bản soạn trong lượt đo, **không có bằng chứng để gọi là hết key hoặc hết timeout**. Không vô hiệu hóa bộ kiểm tra để ép thành công.

Trường `mathReadySeconds` trong JSON thu thập ban đầu là thời gian đến khi việc chuẩn bị kết thúc; phải đọc cùng `preparationPhase`. Trường hợp unavailable không phải thời gian tạo thành công. Bộ đo đã đặt tên rõ hơn `preparationElapsedSeconds` cho các lượt chạy sau, không thay đổi giá trị bằng chứng cũ.

### Hỏi đáp và chuyển tiếng nói thành chữ

- Lần đầu dùng file giọng tạo thật dài khoảng 10 giây: hàm nhận tiếng nói trả `TutorUnavailable`. Lượt này chưa ghi lại mã HTTP, nên **chưa xác định được nguyên nhân gốc**; không suy đoán là hết key.
- Thử lại cùng file, có đo trạng thái HTTP: nhận tiếng nói HTTP 200 trong **1,370 giây**. Chuỗi nhận được khớp văn bản nguồn sau khi bỏ khác biệt dấu câu/viết hoa.
- Câu hỏi khái niệm về phân biệt dữ kiện và điều cần tìm: phản hồi chữ trong **3,847 giây** ở lượt đầu và **0,710 giây** ở lượt thử lại; lượt sau HTTP 200, không dùng phản hồi guard.
- Ngữ cảnh hỏi đáp là ba bước đọc hiểu trích từ đề, trong phiên kiểm tra riêng. Không giả một lời giải toán đã được model kiểm tra. Phép thử không đại diện giọng trẻ em, phòng ồn, ghi âm Android hay chuỗi ghi âm → mạng → trả lời → phát trên thiết bị.

Bằng chứng: `voice-dialogue.json`, `voice-dialogue-recheck.json`, các file WAV và `performance.json`. Việc thành công khi thử lại không xóa lần thất bại trước.

### Hạ tầng và model số tại máy này

| Phép đo | Số mẫu | Trung vị | p95 |
|---|---:|---:|---:|
| Redis PING, TCP cục bộ | 30 | 1,48 ms | 20,52 ms |
| MinIO readiness HTTP | 30 | 8,49 ms | 31,52 ms |
| Bốn phép tính chính xác + đọc số/đơn vị đề trong một vòng | 200 | 1,21 ms | 3,93 ms |
| YOLO số + parser + validator, lặp ảnh tổng hợp 45 + 27 | 10 lượt sau lượt đầu | 114,63 ms | 120,18 ms |

Lượt model số đầu tiên: tải model khoảng **9,61 giây**, lần suy luận/kiểm tra đầu **6,72 giây**. Thiết bị suy luận được báo là CPU, CUDA không sẵn sàng. Đây là model nhận số trên **một ảnh tổng hợp lặp lại**, không phải độ chính xác chữ viết tay, OCR đề chụp thật hay thời gian toàn tuyến Student. Không lấy mẫu lặp để tuyên bố nhận diện hoàn hảo.

Máy có khoảng 15,62 GiB RAM. Trong lúc chạy hồi quy đồng thời, RAM khả dụng xuống khoảng 0,9–1,3 GiB. Các thời gian chạy toàn bộ test/build không phải độ trễ ứng dụng. Các phép đo provider/model chính được thực hiện sau khi ba lượt hồi quy lớn đã kết thúc; đây vẫn là máy phát triển dùng chung, không phải môi trường benchmark cách ly.

## Kiểm thử hồi quy và build

| Bộ kiểm tra | Kết quả lượt rộng | Kiểm tra lại / giải thích |
|---|---|---|
| Business API, toàn bộ Gradle test | **390 đạt, 0 lỗi** | 32 lớp test; không thay thế kiểm tra HTTP của dịch vụ đang chạy |
| Student, toàn bộ Jest | **1.083 đạt, 3 lỗi / 1.086** | Chạy lại ba suite: 61 đạt, 2 lỗi; ca màn học bị timeout 5 giây ở lượt đầu đã đạt khi chạy riêng |
| AI/OCR, pytest | **1.920 đạt, 9 lỗi, 25 bỏ qua** | Bốn lỗi phụ thuộc cờ/key được chạy lại với cấu hình đang có: 4/4 đạt; còn năm ca chưa đạt/chưa đáp ứng điều kiện kiểm thử |
| Auth/SSO/cấu hình web và Node contract | Lượt đầu 58 đạt, 1 bị hủy do timeout | Chạy tuần tự lại **59/59 đạt**, giữ nguyên timeout và mã |
| Smoke của ba bản web đã build | **9/9 đạt** | Dùng môi trường DOM và HTTP stub trong test, không phải đăng nhập thật với backend |
| TypeScript Student | Đạt | Không sửa mã để cho qua |
| Lint Student | 0 lỗi, 2 cảnh báo | Hai cảnh báo có sẵn tại `cropRotation.web.ts` |
| Xuất Student web | Đạt | Bundle tĩnh tạo tại `runtime/audit-student-web-20261029`; không phải đo trải nghiệm trình duyệt/điện thoại |
| Build Portal / Teacher / Admin | Đạt với URL HTTPS ví dụ cấp riêng cho tiến trình build | Build trần thiếu `VITE_API_BASE_URL` bị chặn đúng thiết kế; không sửa file .env, không triển khai bản build ví dụ |

Không cộng các lượt chạy lại thành số test mới. Lượt pytest rộng tắt key/cờ cloud **chỉ trong tiến trình test** để tránh vô tình gọi nhà cung cấp hàng loạt; điều này gây bốn lỗi kiểm tra vốn đòi key/cờ thực. Bốn ca đó đã đạt khi chạy riêng với cấu hình hiện có. Loại trừ ba file cần dịch vụ/nhà cung cấp thật khỏi lượt rộng: `test_minio_pipeline.py`, `test_groq_live_migration.py`, `test_gemini_live.py`. Ngoài ra có 25 skip ghi trong JUnit; không tính skip là đạt.

Các ca còn đỏ cần phân loại trước khi sửa:

1. Hai test loading (`RecognitionProgress`, `startupArt`) kỳ vọng progressbar là chỉ số bước `1`; thành phần hiện trả phần trăm khởi điểm `6` trên thang 0–100. Có dấu hiệu kỳ vọng test cũ; không đủ để nói UI thực tế bị lỗi. Chạy lại vẫn đỏ.
2. Hai test Python gọi tệp Node `suggestionDedupe.test.mjs` không còn tồn tại; hiện có `suggestionDedupe.test.ts` và được Jest thu thập. Đường dẫn test không đồng bộ.
3. Test UI Python dò chuỗi `borderRadius: 14` trong mã; chuỗi không tồn tại. Đây không phải kiểm tra hình ảnh trên màn hình thật.
4. Test capture byte ảnh đọc tệp scratch cũ khi chế độ lưu ảnh vật lý đang tắt. Mã hiện chỉ lưu ảnh khi opt-in; thất bại không chứng minh dữ liệu HTTP bị thay đổi.
5. Test hybrid OCR đòi ít nhất hai dòng gọi advisor trong môi trường tắt cloud của lượt rộng. Chưa kiểm chứng lại ca này với mô hình OCR thực/cấu hình launcher; không kết luận pipeline production hỏng từ điều kiện này.

Ba bản web có chunk JavaScript lớn hơn 500 kB sau minify: Portal khoảng **605 kB**, Teacher **763 kB**, Admin **748 kB** (gzip khoảng 193/235/231 kB). Đây là dấu hiệu nên xem lại chia tải trang; chưa đo thời gian tải trên mạng điện thoại nên không gán số giây chậm cho người dùng.

## Thứ tự việc nên xử lý sau kiểm tra

1. Độ ổn định bản soạn: giữ kiểm tra đúng/sai, làm rõ điều kiện từ chối và tăng tỷ lệ tạo bản đạt ngay; vẫn có lỗi thật ở một đề đủ dữ kiện.
2. Nhận tiếng nói: bổ sung bằng chứng lỗi có phân loại an toàn; lần đầu hiện chỉ thấy lỗi tổng quát, không đủ truy nguyên. Đo lại với bản ghi Android thật khi ứng dụng đang chạy.
3. Giọng mới: xác nhận warm-up của bản điện thoại và đo trọn luồng bấm → phát. Số đo hàm cache hiện tại không thay thế việc đó. Đo dài hơn/bộ mẫu lớn hơn trước khi cam kết 1–3 giây.
4. Đồng bộ các test cũ với hợp đồng UI/OCR hiện tại, không sửa mù để tăng số xanh.
5. Kiểm tra toàn tuyến với bộ ứng dụng được bật và đo web trên thiết bị; cân nhắc chia chunk web sau khi có số đo tải thật.

**Chưa thực hiện các sửa đổi trên**, đúng phạm vi yêu cầu kiểm tra.

## Bộ đo có thể chạy lại

Tệp mới: `scripts/test/project_performance_audit.py`.

```powershell
ai/runtime/.venv/Scripts/python.exe scripts/test/project_performance_audit.py --output report/performance-next
```

Thêm `--live` để thử hữu hạn hai đề, bốn lượt tạo giọng và hỏi đáp/nhận tiếng nói với nhà cung cấp thật. Có dùng hạn mức nhà cung cấp; không chạy stress vô hạn. Đọc trạng thái từng mục trong JSON, không coi việc tiến trình thu thập kết thúc là mọi nghiệp vụ đạt. p95 dùng nearest-rank trên đúng số mẫu ghi trong bảng; không có p95 tin cậy cho các ô tạo mới chỉ một mẫu.

Nhật ký và dữ liệu gốc nằm trong `report/project-audit-20261029/`. Không có bằng chứng điện thoại thật trong lượt kiểm tra này.

Đối chiếu SHA-256 trước/sau của **4.466 tệp đã có** không thấy tệp nào bị thay đổi nội dung. Tệp kiểm chứng: `source-integrity.json`. Mã ứng dụng và các thay đổi chưa commit từ trước được giữ nguyên; tệp mới ngoài báo cáo chỉ có bộ đo hiệu năng.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: kiểm tra và đo hiệu năng có giới hạn, tái sử dụng test/hàm hiện có, tránh thêm framework hoặc sửa sản phẩm ngoài yêu cầu.
  - Applied to: bộ đo riêng, phân tách tạo mới/cache, ghi nhận lỗi và phạm vi phép đo, bảo toàn mã ứng dụng.
