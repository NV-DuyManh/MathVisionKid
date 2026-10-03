# Nhận diện và kiểm tra toán — 03/10/2026

Đã nối luồng ảnh phép tính tới mô hình thật, kết quả backend và giao diện học sinh; đồng thời bổ sung kiểm tra phép tính, đáp số, đơn vị và tính nhất quán giữa các bước trong lời giải đã được xác nhận. Các thay đổi giao diện theo mẫu ở lượt trước được giữ nguyên; chi tiết ở [UI_REFERENCE_REWORK_20261003.md](UI_REFERENCE_REWORK_20261003.md).

## Ảnh phép tính

- Kết quả chứa phép tính thực, mã lượt xử lý, từng ký hiệu và vị trí trên ảnh. Hoàn thành xử lý không tự động có nghĩa là bài đúng: kết quả thiếu bằng chứng vẫn yêu cầu kiểm tra.
- Màn hình xác nhận khoanh đúng ký hiệu trên ảnh của chính lượt gửi. Sửa một chữ số hoặc dấu cộng/trừ gửi đúng mã ký hiệu và lượt xử lý; backend kiểm tra lại, giữ nguyên OCR gốc và lưu lịch sử sửa.
- Chụp lại dùng ảnh mới, tạo lượt xử lý mới và từ chối xác nhận của lượt cũ. Phản hồi trễ không ghi đè kết quả mới. Yêu cầu chạy tuần tự, có giới hạn và được hủy khi rời màn hình.
- Sửa việc thiếu worker trong kiểm tra sẵn sàng và nhận diện worker của dự án khi khởi động. Kết quả bây giờ đi đủ qua hàng đợi, mô hình, callback được xác thực và API học sinh.
- Giữ một thanh hoạt động ngang với giai đoạn thực và nút quay lại; không hiển thị đồng hồ chờ hay phần trăm hoàn thành giả.

## Lời giải viết tay

- Kiểm tra biểu thức đầy đủ với cộng, trừ, nhân, chia, số thập phân, dấu âm và ngoặc; từ chối biểu thức thiếu hoặc có phần thừa.
- Dùng đúng nội dung học sinh đang xem và đã xác nhận. Chữ chưa xác nhận không được kết luận đúng; dòng bỏ qua và ranh giới bài không bị ghép thành một phép tính khác.
- Đối chiếu đáp số với phép tính cuối của cùng bài, kiểm tra đơn vị và cảnh báo khi bước sau dùng kết quả sai ở bước trước. Phép tính đúng nhưng đáp số sai vẫn được báo cần sửa.
- Kết luận nói rõ về các phép tính đã kiểm tra. Việc một số xuất hiện lại ở bước sau chỉ là gợi ý đối chiếu, không chứng minh cách giải phù hợp với đề bài.

## Lỗi giao diện tìm thấy khi thử luồng thật

- Thư viện web dùng bộ chọn ảnh thiết bị ngay, tránh chờ quyền thư viện native vô hạn. Bỏ thông tin môi trường phát triển khỏi lời hướng dẫn học sinh.
- Màn hình máy ảnh vẫn cho chọn ảnh khi yêu cầu quyền máy ảnh chưa trả kết quả, thay cho màn hình trắng.
- Ổn định callback tải ảnh ở bước riêng tư: các callback mới mỗi lần render từng khiến bộ tải ảnh web khởi động lại liên tục. Bước này nay tải ổn định và cho tiếp tục sau xác nhận.
- Đường dẫn kết quả chỉ mang mã bài làm, không chép toàn bộ kết quả/chẩn đoán vào URL. Backend vẫn là nguồn kết quả và quyền truy cập.

## Bằng chứng và kiểm thử

| Kiểm tra | Kết quả cuối |
|---|---|
| Toàn bộ kiểm thử mobile | 344/344, 32 bộ |
| TypeScript | Đạt |
| Toàn bộ kiểm thử backend | 175/175, không lỗi |
| 15 module AI liên quan đến arithmetic | 88/88, 7,22 giây |
| Xuất Android | Đạt, 60 assets |
| Xuất web | Đạt, 31 routes |
| `git diff --check` | Đạt |

[verification.json](math_recognition_20261003/verification.json) ghi phạm vi kiểm tra; kết quả chi tiết nằm trong [mobile-tests.json](math_recognition_20261003/mobile-tests.json), [backend-tests.json](math_recognition_20261003/backend-tests.json) và [ai-current-tests.xml](math_recognition_20261003/ai-current-tests.xml).

[arithmetic-flow.json](math_recognition_20261003/arithmetic-flow.json) ghi kiểm thử API học sinh → worker thật → YOLO thật → callback → kết quả. Mẫu cộng `45 + 27 = 72` và trừ `52 - 18 = 34` hợp lệ; mẫu `52 - 18 = 44` bị phát hiện sai ở hàng chục. Sửa đúng ký hiệu trả kết quả hợp lệ và giữ OCR gốc. Chụp lại với ảnh cộng trả bài mới; xác nhận của lượt cũ nhận 409. Truy cập trái quyền bị từ chối. Thời gian các mẫu là khoảng 0,32–3,04 giây từ tải ảnh tới đọc kết quả trong môi trường cục bộ; đây không phải cam kết thời gian cho mọi ảnh hay điện thoại.

[word-flow.json](math_recognition_20261003/word-flow.json) ghi mẫu trang tiếng Việt gồm 6 dòng được đọc bằng CRNN thật, sau đó xác nhận nội dung và kiểm tra bằng evaluator dùng trong app. `18 - 6 = 12 (cm)` → `18 x 12 = 216 (cm2)` → `Đáp số: 216 cm2` khớp. Đổi đáp số sang `216 kg` phát hiện sai đơn vị; đổi bước đầu thành `18 - 6 = 10` phát hiện lỗi tính và cảnh báo chuỗi bước. Nội dung đã phục hồi, OCR gốc được giữ. Đây là ảnh chữ in tổng hợp với khung dòng chỉ định thủ công; không phải bằng chứng độ chính xác trên chữ viết tay thực tế.

Trình duyệt trong ứng dụng đã thực hiện chọn ảnh, bước riêng tư, dùng toàn ảnh, gửi bài, thanh tiến trình, xác nhận ký hiệu có khoanh vị trí và đọc kết quả thật `45 + 27 = 72`. [browser-checks.json](math_recognition_20261003/browser-checks.json) và [ảnh kết quả](math_recognition_20261003/browser/arithmetic-confirmed-real.png) ghi bằng chứng ở 375 × 812, không tràn ngang. Đây là giao diện web với viewport điện thoại, không phải thử trên thiết bị vật lý. Sau luồng hoàn chỉnh này, kết nối điều khiển trình duyệt bị timeout ở các lần mở trang bổ sung; bài sai, liên kết thiếu dữ liệu và lời giải vẫn được kiểm tra ở mức API/evaluator/component, không báo là đã hoàn tất toàn bộ ma trận trình duyệt.

Lượt thử toàn bộ AI trước đó không xanh: bộ chặn socket thử nghiệm làm lỗi cả giao tiếp nội bộ của TestClient (100 lỗi setup và 59 failure), nhiều kiểm thử cũ còn tham chiếu các đường dẫn `ocr-pilot`/`OcrPilotService` đã đổi, và còn các failure khác ngoài phạm vi. Không tính lượt đó là kiểm thử hồi quy hợp lệ đã đạt, cũng không sửa hàng loạt kiểm thử cũ để che lỗi. File thô: `scratch/math_ai_full_20261003/full-ai-raw.xml`. Con số 88 chỉ áp dụng cho 15 module liên quan được chạy lại với cách cô lập hàng đợi đúng.

## Phạm vi hiện có

Mô hình nhận diện ký hiệu từ ảnh hiện hỗ trợ **một phép cộng/trừ số tự nhiên đặt dọc**, tối đa 6 chữ số mỗi toán hạng; phép cộng có thể có thêm một chữ số kết quả. Nhân/chia được kiểm tra từ nội dung OCR đã xác nhận ở luồng lời giải, chưa có mô hình ảnh chuyên nhận diện đầy đủ nhân/chia, phân số hoặc nhiều bài trên một trang. Hai checkpoint detector có tên khác nhau nhưng cùng checksum; không coi chúng là hai mô hình mạnh khác nhau.

Lời giải hiện được kiểm tra về phép tính và tính nhất quán của đáp số/đơn vị. **Chưa chấm ngữ nghĩa toàn bộ cách giải theo đề bài hoặc tự quyết định điểm chính thức.** Các giá trị confidence không phải phần trăm độ chính xác đã hiệu chuẩn.

Không huấn luyện/tải model mới, không sửa dự án HandAI riêng, không reset dữ liệu, không commit hoặc push. Các dịch vụ cục bộ của MathVision vẫn đang chạy. Các bản ghi thử nghiệm dùng ảnh tổng hợp; feedback OCR của trang lời giải được đánh dấu test, không đủ điều kiện training.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa luồng hiện có với ít lớp trung gian và không thêm dependency.
  - Applied to: parser/evaluator, API callback, xác nhận ký hiệu, worker và kiểm thử.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native, dữ liệu bất đồng bộ và render kết quả.
  - Applied to: hủy request, bỏ phản hồi cũ, memo evaluator và callback tải ảnh ổn định.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: phản hồi nhận diện rõ ràng, thao tác sửa trên ảnh và giao diện học sinh.
  - Applied to: thanh tiến trình, nhãn phạm vi, trạng thái chưa đủ dữ liệu và xác nhận ký hiệu.
- `control-in-app-browser`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-bundled/browser/26.928.21956/skills/control-in-app-browser/SKILL.md`
  - Why selected: kiểm thử giao diện web thực tế trong trình duyệt của ứng dụng.
  - Applied to: chọn ảnh, riêng tư, crop, gửi bài, xác nhận và ảnh bằng chứng.

Đã đọc tài liệu [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) trước khi sửa mã.
