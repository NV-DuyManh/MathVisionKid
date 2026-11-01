# Kiểm tra phát hành, giọng nói, chuẩn bị bài và nhánh Hieu — 31/10/2026

## Kết luận

Chấp nhận tích hợp **bản Hieu đã được rà soát và sửa**, không lấy nguyên trạng toàn bộ thay đổi của nhánh. Điểm kiểm tra là `origin/Hieu` tại `03bbbef1f6916e15a3366b27f9ff1689dd17a466`; `origin/main` trước tích hợp là `20d6780f3a77b0ac2db96edc575e62481788ccad`. Lịch sử ba commit của Hieu được giữ bằng merge, không viết lại tác giả.

Các lượt kiểm thử cuối dưới đây không còn ca thất bại. Backend chạy với PostgreSQL thật và đã nâng schema từ V23 lên V26; Redis, MinIO, AI, worker, ba cổng web và Student đều báo sẵn sàng. Kiểm tra LAN cuối cùng đạt. Đây là kết quả trên máy phát triển này, không phải chứng nhận không thể lỗi hoặc phép thử trên điện thoại thật.

**Không có cơ sở để hứa mọi bài/giọng mới đều hoàn thành trong 1–3 giây.** Đọc đề có thể mở ngay và giọng được chuẩn bị trước khi bấm Phát. Tạo giọng mới vẫn chịu thời gian của dịch vụ bên ngoài; tính toán mới vẫn phải qua kiểm tra độc lập. Âm thanh đã lưu nhanh hơn rõ rệt, nhưng không được lấy số đo cache để đại diện cho lần tạo mới.

## Những phần lấy từ Hieu

| Phần | Quyết định và chỉnh sửa |
|---|---|
| Đăng ký Student/Teacher | Giữ. Backend kiểm tra vai trò, lớp học và mã hóa mật khẩu; không cho yêu cầu quyền Admin. |
| Quên mật khẩu bằng mã email | Giữ. Giới hạn yêu cầu/thử mã, mã dùng một lần, thu hồi refresh token sau đổi mật khẩu; lỗi chuyển thư không làm lộ tài khoản. |
| Đăng nhập Google | Giữ xác minh bằng SDK phía máy chủ: chữ ký, audience, hạn token và email có thẩm quyền. Vai trò tài khoản hiện có lấy từ DB. |
| Facebook qua Firebase | Giữ xác minh token/provider và kiểm tra thu hồi; email trùng không tự chứng minh quyền sở hữu tài khoản cũ. |
| Giao diện đăng nhập/đăng ký/khôi phục | Giữ các chức năng mới; khôi phục cơ chế chống gửi lặp, phản hồi đăng nhập cũ ghi đè phiên mới, và thông báo vai trò trên Student. |
| Migration | Đổi ba migration mới từ V17/V18/V19 thành V24/V25/V26 để không đụng phiên bản Quiz đã có. Kiểm tra trùng phiên bản tự động. |
| Cấu hình native | Giữ định danh ứng dụng; loại cây Android sinh tự động. Không đổi cách chạy Expo Go hiện có. |

Không lấy các thay đổi làm yếu cấu hình HTTPS production, thay image/volume MinIO theo máy cá nhân, ép bật nhà cung cấp OAuth, hoặc ghi đè cơ chế phiên web đang có. `demoUI` vẫn nằm trên máy và được Git bỏ qua. Không đưa khóa, dữ liệu riêng, trọng số model, thư mục môi trường hoặc bản export vào Git.

## Lỗi thực sự đã phát hiện và sửa

### Chuẩn bị bài và tiếng nói

1. Khi chuyển từ phần đọc đề sang kế hoạch toán đã kiểm tra, hàng đợi trước đây hủy cả đoạn đọc còn nguyên nội dung. Nay giữ tác vụ có nội dung trùng chính xác ở cả hai giọng; chỉ hủy phần đã đổi. Ngân sách ký tự vẫn tính cả phần đã đặt chỗ.
2. Câu hỏi rõ ràng dạng **“Cần bao nhiêu …?”** trước đây không được nhận là ranh giới câu hỏi. Một phép thử qua backend phải chờ khoảng **12,116 giây** để vào bài. Đã bổ sung ranh giới trích nguyên văn này; hai lượt đo sau sửa mở phần đọc trong **38,25 ms** và **21,18 ms**. Không suy diễn câu thiếu dấu hỏi hoặc gộp nhiều câu hỏi thành một.
3. Chữ số thập phân Unicode toàn chiều rộng trong mục tiêu do model trả về gây từ chối nhầm dù cùng số với đề. Nay chuẩn hóa khi đối chiếu giá trị; không sửa nguyên văn OCR, không biến số mũ đơn vị thành số thường, không cho số chưa được chứng minh xuất hiện sớm.
4. Chuẩn bị toán chạy nền có tối đa hai lượt phục hồi cho lỗi kiểm tra/bận/timeout trong **một cửa sổ tổng 60 giây**. Không lặp lại lỗi khóa/cấu hình/quota; không bỏ kiểm tra toán để trả lời nhanh.
5. Có ghi nhận `ClientConnectorDNSError` và `NoAudioReceived` trong lượt tạo giọng thật. Đã bổ sung phục hồi kết nối tạm thời trong giới hạn ba lần của một đoạn; dữ liệu âm thanh dở bị loại bỏ, không đổi âm sắc, không trả file rỗng. HTTP 401/403/429 không bị lặp vô ích. Chỉ lỗi DNS không đủ để kết luận hết khóa hoặc nhà cung cấp đã ngừng dịch vụ.

Hai giọng nội bộ vẫn là `vi-VN-NamMinhNeural` và `vi-VN-HoaiMyNeural`; giao diện dùng **Giọng nam/Giọng nữ**. Không thêm video. Không nâng thời gian chờ lên 150 giây.

### Xác thực và vận hành

- Khóa yêu cầu đặt lại mật khẩu trên hàng gốc `users`, tránh khóa outer join của kế thừa JOINED trên PostgreSQL. Truy vấn chỉ lấy hằng số để không phụ thuộc cách JDBC/H2 ánh xạ UUID. Kiểm tra dùng đồng thời cùng mã xác nhận chỉ thành công đúng một lần.
- Chặn mật khẩu vượt **72 byte UTF-8** trước BCrypt. Tài khoản bị khóa không đổi mật khẩu được. Mã không chuyển thư thành công bị vô hiệu hóa và vẫn được tính vào giới hạn yêu cầu.
- Giới hạn kết nối/đọc/ghi SMTP; dịch vụ chưa được cấu hình không bị giả vờ là đang hoạt động.
- Firebase ban đầu tạo hai bản app container, gây lỗi thật `Component auth has not been registered yet`. Chuyển sang đúng hai SDK modular cần dùng và khử bản trùng; kiểm tra `initializeApp/getAuth/signOut` thực tế đã qua.
- Gradle rút classpath thành JAR tạm trên Windows khiến bộ khởi động nhận nhầm backend của chính dự án. Nay đọc manifest, kiểm tra chính xác hai thư mục classes/resources của checkout. Thư mục dự án khác, trùng tiền tố, classpath tương đối/thiếu hoặc JAR không tồn tại đều bị từ chối. Không dừng tiến trình ngoài dự án.
- Một số test cũ dùng mật khẩu demo trước khi chủ dự án đổi thành `123`. Đã cập nhật tài khoản test mặc định, hỗ trợ biến môi trường khi cần, và chạy lại; không sửa backend để chấp nhận mật khẩu sai.

## Kết quả kiểm thử cuối

| Nhóm | Kết quả | Giới hạn bằng chứng |
|---|---:|---|
| AI/runtime, toàn bộ thư mục `tests` sau sửa | **2.154 đạt, 7 bỏ qua, 0 lỗi**, 175,18 giây | 3 ca thiếu catalog Gemini lịch sử; 4 ca thiếu ảnh riêng. Không chế dữ liệu để cho qua. |
| Student Jest | **110 bộ / 1.263 ca đạt**, 56,413 giây | Môi trường kiểm thử React Native, không phải Android/iPhone thật. |
| Backend đầy đủ trên H2 | **478 đạt, 1 bỏ qua, 0 lỗi** | Ca MinIO yêu cầu bật riêng; đã chạy ở nhóm tiếp theo. |
| Hieu/auth/migration trên PostgreSQL + đọc MinIO thật | **17/17 đạt** | Dùng database kiểm thử riêng; SMTP và token OAuth được mô phỏng có kiểm soát. Không gửi email thật. |
| Script dữ liệu/triển khai/launcher/diagnostics | **177 đạt, 1 bỏ qua, 15 subtest đạt**, 20,33 giây | Ca symlink thiếu quyền Windows. Không huấn luyện model. |
| Web config/session | **Teacher 21, Admin 34, Portal 21 đạt** | Bao gồm phản hồi OAuth cũ không ghi đè lần đăng nhập mới. |
| Kiểm tra bundle production | **Teacher 2, Admin 5, Portal 2 đạt** | Kiểm tra sản phẩm build; không phải đã deploy production. |
| Student Node contract | **19 đạt** | Metro/domain/QR, không thay thế kiểm thử thiết bị. |
| Runtime identity | **8 ca lệnh + 7 classpath JAR + 8 Python parent đạt**, thêm listener ngoài thật bị từ chối và giữ nguyên | Có kiểm tra trên PowerShell Windows. |
| MinIO guard | **7 ca đạt** | Bảo toàn image và volume, không thay ảnh/volume để né lỗi. |
| Catalog store | **2 ca đạt**; inventory **20 nguồn, 0 trùng** | Chỉ kiểm tra lưu trữ/cách ly/cấu trúc; không phải điểm chính xác OCR/toán. |

TypeScript Student, lint ba cổng web, build web toàn workspace và `bootJar` thành công. Expo export **web + Android + iOS JavaScript** thành công, web có 40 route. Export JavaScript không đồng nghĩa đã build/cài IPA/APK hoặc nghe thử trên máy thật. Đã cài sạch dependency một lượt, kiểm tra lockfile và `npm ls --depth=0`; cây dependency hợp lệ.

Đã sửa việc unmount thiếu trong test Gallery gây timer chạy sau khi test kết thúc; kiểm thử dữ liệu ảnh xác nhận đúng byte của fixture tạm; các cầu nối Node dùng đúng file TypeScript hiện có. Không bỏ assertion nghiệp vụ để làm xanh bộ kiểm thử.

## Đo luồng thật và hiệu năng

Các số sau là HTTP trên máy phát triển, không phải thời gian chạm nút tới âm thanh trên điện thoại. Mẫu nhỏ, không phải kiểm tra sức chịu tải production.

| Tình huống | Số đo |
|---|---:|
| Bắt đầu đọc đề qua AI trực tiếp | 15–32 ms ở hai bài đo |
| Bài mới: kế hoạch toán vượt kiểm tra độc lập, chạy nền | **26,204 giây**, 8 mục trong outline |
| Hai giọng tự tạo khi chưa bấm Phát, lượt đầu qua AI | Nam **8,766 s**, nữ **10,328 s** |
| Hai giọng qua backend, sau sửa câu “Cần bao nhiêu…”, trước khi có cache phù hợp | Nam **10,375 s**, nữ **16,594 s** |
| Lượt cuối cùng qua backend, cache đã có | Cả hai sẵn sàng sau **16 ms** quan sát; lấy WAV **6,59 / 6,34 ms** |
| `/me`, 20 yêu cầu, đồng thời 4, lượt cuối | Trung vị **5,18 ms**, lớn nhất **22,77 ms** |

WAV nhận về được đọc và kiểm tra có mẫu PCM khác 0. Lời nói chưa được công bố trong bài bị từ chối HTTP 400; Student vào phần Admin và Teacher vào phần học Student bị từ chối 403; Student khác không đọc được phiên bài học, trả 410 `LESSON_EXPIRED` theo hợp đồng hiện có.

Phải giữ lại cả kết quả không đạt: trước sửa có lượt kế hoạch chưa sẵn sàng sau 60 giây, bị từ chối nhầm chữ số Unicode; lượt HTTP đầu tiên của bài dạng “Cần bao nhiêu…” chậm và thiếu giọng nữ sau cửa sổ quan sát khi có lỗi kết nối. Không coi các lượt đó là thành công. Các bản sửa và kiểm thử phục hồi làm giảm các trường hợp này, không chứng minh xác suất lỗi bằng 0.

## Những điều chưa được xác nhận

- Chưa thử âm thanh, micro, tua lại và luồng học trên Android/iPhone thật trong lượt này. Không có ảnh chụp UI mới do quyền điều khiển trình duyệt đang tắt.
- Chưa đăng nhập OAuth hoặc gửi thư phục hồi qua nhà cung cấp thật vì chưa có cấu hình dịch vụ đó trên máy. Endpoint chưa cấu hình trả lỗi có kiểm soát; không tạo khóa hay tài nguyên trả phí thay chủ dự án.
- Dịch vụ giọng bên ngoài không có bằng chứng bảo đảm vô hạn hoặc không bao giờ ngừng; cache, tạo sớm và retry có giới hạn không loại được mất mạng hoặc lỗi nhà cung cấp. Không tự đổi sang giọng khác để làm đẹp số đo.
- `npm audit` còn **48 mục**: 1 low, 44 moderate, 2 high, 1 critical theo máy quét. Mục critical `portal-web` trùng tên gói npm độc hại, nhưng lockfile của dự án trỏ **workspace riêng `apps/portal-web`, `link: true`**, không phải tarball công khai. Hai mục high liên quan Zod 3 và chuỗi Expo CLI; không ép Zod 4 vào công cụ đang yêu cầu API Zod 3. Vite đã nâng bản vá 8.3.5 và các bản vá tương thích khác đã kiểm tra. Đây không phải kết luận “không có lỗ hổng”.
- Build còn cảnh báo chunk web lớn và deprecation FastAPI/Gradle. Không tắt cảnh báo để gọi dự án hoàn hảo.

Nguồn đối chiếu: [xác minh Google ID token](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token), [advisory portal-web](https://github.com/advisories/GHSA-25f9-p47j-2rc5), [advisory Zod](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5), [tài liệu Expo v57 theo quy tắc dự án](https://docs.expo.dev/versions/v57.0.0/). Dự án hiện dùng SDK 58, không hạ phiên bản theo trang tài liệu này.

Docker ban đầu không khởi động được Inference manager. Thao tác xóa socket tạm đã bị bộ kiểm duyệt tự động từ chối với lý do duy nhất `blocked by policy`; không thử xóa bằng cách khác. Chủ dự án sau đó khởi động lại Docker, các phép kiểm tra thật và migration PostgreSQL mới được chạy thành công. Không reset hoặc xóa volume dữ liệu.

## Tái chạy và bằng chứng

Chạy từ `E:/MathVisionKid`:

```powershell
npm test --workspace=student-mobile -- --runInBand
npm run typecheck --workspace=student-mobile
npm run build:web
npm run test:config --workspaces --if-present
npm run test:production --workspaces --if-present
Push-Location ai/runtime
.venv/Scripts/python.exe -m pytest -q tests
Pop-Location
ai/runtime/.venv/Scripts/python.exe -m pytest -q scripts/data scripts/deploy scripts/test/test_run_launcher.py tools/diagnostics/test_check_runtime.py
backend/business-api/gradlew.bat -p backend/business-api test bootJar
powershell -NoProfile -File scripts/test/test_service_runtime_identity.ps1
ai/runtime/.venv/Scripts/python.exe tools/diagnostics/check_runtime.py
```

Chạy test PostgreSQL trong database riêng, **không dùng `create-drop` trên database của ứng dụng**. Nhóm 17 ca đã dùng PostgreSQL dialect, Flyway thật và `ddl-auto=validate`; đọc MinIO bật bằng `MATHVISION_MINIO_SMOKE=true`. Nhật ký, XML, script đo và dữ liệu xuất thô giữ ở `.local-artifacts/release-audit-20261031/` trên máy, không đưa Git vì có thông tin môi trường/phiên kiểm tra. Bản tổng hợp không chứa token được lưu cùng báo cáo này.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa backend, pipeline và khởi động bằng thay đổi nhỏ, giữ giới hạn và ranh giới an toàn.
  - Applied to: phục hồi bài/giọng, khóa OTP, migration và nhận dạng tiến trình Gradle.
- `ponytail-review`
  - SKILL.md: `.agents/skills/ponytail-review/SKILL.md`
  - Why selected: chọn lọc nhánh Hieu, loại mã sinh và cấu hình riêng không cần đưa vào main.
  - Applied to: generated native code, SDK Firebase dư và thay đổi triển khai không phù hợp.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: bảo toàn luồng React đăng nhập và hiệu năng dependency web.
  - Applied to: chống phản hồi cũ ghi đè phiên mới, callback sau unmount, SDK modular và kiểm thử build.
