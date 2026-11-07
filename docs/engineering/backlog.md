# Theo dõi yêu cầu cải tiến

## Student — Quay lại bước hướng dẫn

- Ngày ghi nhận: 07/11/2026.
- Trạng thái: **Đã triển khai trong mã nguồn local**, theo yêu cầu “giờ làm đi”; chưa commit/push.
- [x] Thêm nút **Bước trước** phía trên khung bước học, từ bước thứ hai. Sau khi hoàn thành vẫn xem lại được.
- [x] Bước đã hoàn thành giữ câu hỏi, toàn bộ lựa chọn và đáp án đã được máy chủ kiểm tra đúng; chỉ xem, không chọn/chấm lại. Câu trả lời sai đang sửa và gợi ý đang mở được giữ khi trở về bước hiện tại.
- [x] Có **Bước tiếp theo** để đi qua lịch sử và **Về bước đang học / Về bài giải** để trở lại vị trí hiện tại; không tự chuyển bước.
- [x] Xem lại không gửi đáp án, không thay đổi tiến độ/revision, không phát lại hiệu ứng thưởng và không mở bước chưa học.
- [x] Nghe giảng và hỏi bài dùng ngữ cảnh bước đang xem; không ghi đè câu hỏi nháp ở bước hiện tại.
- [x] Máy chủ trả câu hỏi/lựa chọn của các bước đã hoàn thành để khôi phục sau khi tải lại. Cách nhập số gốc được giữ trong bộ nhớ theo tài khoản và chỉ dùng lại khi tương đương đáp án máy chủ.
- [x] Kiểm thử component React Native, API/Python/backend, bàn phím và trình duyệt ở 390×844 / 1280×900; xuất web và Android thành công.
- [x] Rà soát bổ sung: vẫn duyệt lịch sử chỉ đọc khi hết đăng nhập; focus đúng tiêu đề sau khi quay về bước hiện tại/bài giải; khôi phục phân số có khoảng trắng; lựa chọn trắc nghiệm luôn khớp nhãn đã được máy chủ kiểm tra; kiểm tra payload review trước khi hiển thị. Sau lượt này: 1.404 ca Student qua.
- [ ] Xác nhận thao tác và phát âm thanh trên điện thoại Android/iOS thật sau khi nạp bản mới.

Bằng chứng local: `.local-artifacts/lesson-history-20261107/README.md`. Trình duyệt dùng HTTP fixture từ kết quả engine Python; không thay thế kiểm thử dịch vụ thật hoặc thiết bị thật. Phiên cũ đã tạo trước bản cập nhật có thể thiếu câu hỏi/lựa chọn lịch sử; mở bài mới để kiểm tra đầy đủ.

## Hồi quy toàn dự án và giọng nói — 07/11/2026

- [x] Sửa retry giọng bị chính cooldown của giọng đó chặn; áp dụng cho tạo ngầm, lời giảng trực tiếp và Quiz, giữ deadline/quyền truy cập/giới hạn retry.
- [x] Bỏ khởi tạo WAL/schema catalog lặp khi đọc/ghi bình thường; kiểm tra hai giọng trên 100 database mới và 1.000 lượt ghi/đọc lại.
- [x] Kiểm thử Python cuối: 2.708 qua, 14 bỏ qua; backend 525 qua, 1 bỏ qua; Playwright 32 qua. Ba web build thành công; 28 migration SQL qua trên PostgreSQL cô lập.
- [x] Nạp lại dịch vụ local; lượt đo cuối hai giọng sẵn sàng 1,315 / 1,658 giây, nghe lại 10,4 / 21,6 ms. Có lượt nhà cung cấp trả rỗng cần 32,551 giây để tự phục hồi; chưa đạt cam kết mọi lượt dưới 3 giây.
- [ ] Đo bấm–phát trên Android/iOS thật, cold start, mạng chậm và nhiều người dùng; không suy ra từ latency HTTP local.
- [ ] Xử lý dependency Expo còn cảnh báo theo nâng cấp tương thích: Zod, glob, minimatch cần đánh giá major; deepmerge chưa có bản vá được advisory ghi nhận. Không ép override hoặc hạ version để làm mất cảnh báo. `portal-web` critical hiện là trùng tên workspace private với gói npm công cộng; đã kiểm tra nguồn liên kết.

Bằng chứng và phạm vi/giới hạn: `.local-artifacts/project-regression-20261107/README.md`. Không commit/push trong lượt này.

## Hoàn thiện các task sau audit — 07/11/2026

- [x] Quiz nhận đáp án văn bản/dãy số từ kế hoạch đã kiểm chứng; giữ lựa chọn, chấm tại backend. Nâng generation version lên v11 để thử lại draft cũ chưa hỗ trợ.
- [x] Tiến độ đợt chấm phản ánh trạng thái bài nộp thật; upload nguyên tử, không âm thầm bỏ ảnh, rollback dọn đối tượng đã lưu; xử lý lỗi điều phối AI và gửi trùng.
- [x] Rotation refresh token được khóa theo user; replay thu hồi phiên dù trả 401; reset/logout vô hiệu hóa JWT cũ qua sessionVersion và migration V29.
- [x] CI không bỏ sót script/Student browser, gate từ chối kế hoạch thiếu. Thêm browser test dùng export Student thật dưới /study/ và workflow cài mới Windows thủ công.
- [x] Flyway thật V28 → V29 với dữ liệu có sẵn, checksum, chạy lặp và backup/restore PostgreSQL qua; MinIO thật trên bucket cô lập qua. JVM dùng UTC để tránh tên timezone legacy bị PostgreSQL từ chối.
- [x] Cooldown lỗi giọng tạm thời phục hồi sớm và tăng dần khi sự cố kéo dài; giữ deadline 60 giây, checkpoint, giới hạn song song và giọng đã chọn.
- [x] Lượt hồi quy này: Python **2.703 qua, 22 bỏ qua**; Student **1.405 qua**; backend đầy đủ **534 qua, 2 opt-in bỏ qua** rồi chạy riêng hai opt-in PostgreSQL/MinIO đều qua; browser web **32 qua**, Student thật **4 qua**; typecheck/governance/launcher/installer contract/pip check qua.
- [ ] **Chưa đạt mọi lượt giọng 1–3 giây:** probe transport thật có 13,546–19,984 giây và một lượt SpeechNoAudio sau 7,438 giây. Lớp transport độc lập với retry toàn app; giải mã lượt đo chỉ 109 ms. Cần cấu hình dịch vụ chính thức/đo lại; không coi lỗi bên thứ ba đã biến mất.
- [ ] Thử Android/iOS thật, tải đồng thời và mạng chậm; chưa có thiết bị/adb trong lượt này.
- [ ] Chạy workflow cài mới trên máy Windows sạch sau khi phát hành mã; test contract local chưa thay thế bước này.
- [ ] Đánh giá nâng dependency Expo tương thích; audit vẫn còn cảnh báo, không ép override major để làm sạch số đếm.
- [ ] Đồng bộ và phát hành theo quyền chủ dự án: local đang 5 commit sau origin/main khi so sánh; còn thay đổi chưa commit. Chưa merge/push hay nạp lại dịch vụ trong lượt này.

Báo cáo mới: `.local-artifacts/task-improvements/README.md`. Các số đo giọng và kết quả cũ ở mục trước là lịch sử của lượt chạy trước, không thay thế kết quả mới này. Skills applied: mathvision-workflow, mathvision-backend, mathvision-quality, mathvision-review, vercel-react-best-practices.

## Kiểm tra Android, cài mới và máy tính — 07/11/2026

- [x] Android 14 / Expo Go 58 thật: đăng nhập, mở lại bài, chọn sai/chọn lại đúng, giữ lựa chọn, xem bài giải, quay lại bước đã học và mở Quiz riêng. Sửa nhận diện điện thoại thật bằng `expo-device.isDevice`, tránh chọn nhầm địa chỉ giả lập khi dùng USB.
- [x] Cài dependency trong thư mục Windows mới không có node_modules, venv hoặc cấu hình riêng: npm ci, môi trường Python mới, pip check/import, FFmpeg và Gradle bootJar/testClasses qua. Sửa tải dependency lớn bằng pip có hỗ trợ tiếp tục tải. Đây là thư mục sạch trên máy hiện tại, chưa phải máy Windows mới hoàn toàn.
- [x] Đồng bộ các bản vá tương thích SDK hiện tại, thêm kiểm tra `expo install --check` trong CI. Audit từ 37 còn 8 mục: 7 low thuộc cùng advisory deepmerge trong bộ test chưa có bản vá; 1 critical là trùng tên workspace private `portal-web`, đã xác minh là symlink local, không phải gói tải từ npm. Production audit chỉ còn mục trùng tên này; không che hoặc dismiss cảnh báo.
- [x] Máy tính có **Tính toán / Đổi đơn vị**: độ dài, diện tích, khối lượng, thể tích, số đo ghép hai phần; dùng phân số chính xác và hệ số nguyên, không làm tròn trung gian. Hỗn số có ba ô nhập riêng và kết quả tương đương dạng hỗn số. Phép tính nhẩm một chữ số có kết quả nguyên chỉ hiện kết quả.
- [x] Android thật xác nhận `2+3=5` không có bước giải; nhập hỗn số `2 1/4`; `1/3+2/5=11/15` có phân số đứng và cách quy đồng; `15 m 25 cm=15,25 m` kèm cách đổi.
- [x] Sau thay đổi máy tính: Student 118 suite / 1.459 test qua; 145 ca máy tính/đổi đơn vị qua; browser máy tính desktop/mobile qua, typecheck qua. Khởi động lại ba web local; launcher báo READY_FOR_FULL_DEMO.
- [ ] Chưa đo âm thanh bấm–phát trên thiết bị, chưa kiểm tra iOS thật, mạng chậm/đồng thời hoặc workflow trên Windows mới hoàn toàn. Không suy ra những phần này từ kiểm thử giao diện.
- [ ] Chưa commit/push hoặc đồng bộ 5 commit remote; cần thực hiện theo yêu cầu phát hành của chủ dự án.

Bằng chứng mới: `.local-artifacts/dependency-setup-20261107/README.md`. Các kết quả ở trên bổ sung cho lịch sử các lượt trước, không đổi dữ liệu nghiên cứu hay tắt bộ kiểm chứng toán.

## Lỗi OCR đề in Bài 3 — 07/11/2026

- [x] Tái hiện phản hồi đọc đủ đề nhưng bị loại vì nhà cung cấp lặp một đề trong cả `problemText` và `questions`. Chỉ loại metadata trùng đã xác thực và giống nguyên văn; giữ chặn mâu thuẫn, thiếu ý, thay số, bài làm và cờ chưa chắc chắn.
- [x] Đọc dự phòng phục hồi được một bài đơn; lỗi định dạng dịch vụ không còn bị trình bày như kết luận ảnh không rõ.
- [x] Hồi quy liên quan **212 ca qua**; hai lượt cloud thật qua API Student đọc đủ Bài 3 a/b trong **1,437 / 1,469 giây**. Đây là ảnh cắt từ đề gốc và biến thể có lề trắng, không phải kiểm tra trực tiếp tệp tải từ điện thoại lúc báo lỗi.
- [ ] Chưa xác minh lại trên Android thật trong lượt này vì không có thiết bị kết nối; không suy ra mọi ảnh hay nhà cung cấp đều không thể lỗi.

Bằng chứng: `.local-artifacts/ocr-clear-20261107/README.md`. Không đổi trọng số, không tắt bộ kiểm chứng toán, chưa commit/push.

## Đối chiếu và lưu bộ đề vào catalog — 07/11/2026

- [x] Đối chiếu lại 81 nhóm tương ứng 85 câu/ý/ô đủ dữ kiện với đáp án độc lập; lưu và đọc lại ở catalog hiện tại của tài khoản Student local. Không đưa dữ liệu riêng vào Git.
- [x] Phát hiện và sửa lỗi `1 1/3 + 5/8 : 7/2`: kết quả đúng `127/84`, không phải `463/336`. Giữ bộ kiểm chứng và cách ly các phiên bản cache.
- [x] 590 kiểm thử Python liên quan qua; 81 luồng trả lời từ catalog hoàn thành với đáp án tham chiếu; 4 lượt API Student thật xác nhận cache hit và đáp án đúng. Đã nạp lại dịch vụ local.
- [ ] Đề 3 Câu 4a/b thiếu đơn vị khối lượng; chủ dự án xác nhận đề gốc không rõ. Chưa lưu lời giải chuẩn.
- [ ] Đề 02 TN1e thiếu hàng làm tròn; `89,99` được chủ dự án đề xuất nhưng `90,1` lớn hơn và cũng làm tròn thành 90 ở hàng đơn vị. Chưa có đáp án chuẩn duy nhất theo đề hiện tại.
- [ ] Không suy ra nhận diện toàn bộ ảnh hoặc âm thanh/Android thật đã qua từ các phép thử văn bản/catalog này. Chưa commit/push.

Bằng chứng và Skills Applied: `.local-artifacts/exam-catalog-20261107/README.md` (`mathvision-quality`, `mathvision-review`, `ponytail`).

## Catalog dùng chung qua Git — 07/11/2026

- [x] Theo yêu cầu chủ dự án, đóng gói 81 nhóm/85 câu, ý đã kiểm chứng thành dữ liệu công khai kèm mã nguồn. Giữ riêng database, ảnh, âm thanh và trạng thái học của từng tài khoản.
- [x] Kiểm tra tài khoản mới với kho local trống đọc cùng catalog, không gọi model; kiểm tra phiên bản chính sách giống nhau trên Windows/Linux. CI kiểm tra toàn bộ đáp án độc lập, phiên bản và dữ liệu công khai.
- [x] Catalog Bot hiển thị số đề đã phát hành. Công cụ refresh chỉ cập nhật kế hoạch khi khớp các đáp án đã duyệt, không đọc database riêng.
- [ ] Ba câu/ý chưa đủ dữ kiện ở mục trước vẫn chờ làm rõ. Catalog không thay thế huấn luyện và không chứng minh mọi ảnh mới đều nhận diện thành công.

Skills applied: `mathvision-workflow`, `mathvision-review`, `mathvision-quality`, `mathvision-backend`, `ponytail`. Trạng thái commit/push/PR được báo riêng sau kiểm thử phát hành.
