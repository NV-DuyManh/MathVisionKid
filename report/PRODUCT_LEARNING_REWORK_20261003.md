# Luồng học toán từ ảnh và giao diện đồng bộ — 03/10/2026

Đã chuyển đường vào công khai của Student Mobile sang **chụp/chọn ảnh → che thông tin → cắt một bài → cùng học từng bước**. Học sinh nhận một gợi ý và một câu hỏi, tự viết bước làm, rồi tiếp tục; không phải xác nhận toàn bộ các dòng OCR trước khi học. Giao diện dùng lại bộ màu tím nhạt, Nunito và linh vật ngôi sao của trang chủ đã được chủ dự án chấp nhận.

Báo cáo này cập nhật hành vi sản phẩm so với [MVP_MATH_TUTOR_20261003.md](MVP_MATH_TUTOR_20261003.md). Màn hình và API nghiên cứu cũ vẫn được giữ cho đường vào riêng; chúng không còn là đường chụp mặc định của học sinh. Chưa có bằng chứng đủ để gọi độ chính xác nhận diện là hoàn thiện trên mọi ảnh.

## Sản phẩm sau khi chụp

1. **Ảnh đề chưa làm:** cho chọn “Em chưa hiểu đề”, “Bắt đầu từ đâu?” hoặc “Gợi ý bước tiếp”. Mỗi lượt chỉ có một gợi ý ngắn và một câu hỏi.
2. **Ảnh bài học sinh đã làm:** mở một bước đang chọn, ưu tiên phép tính đầu tiên. Có thể chuyển bước, xem lại ảnh hoặc sửa nội dung của bước này. Không hiển thị độ tin cậy, gợi ý OCR cạnh nhau hoặc danh sách xác nhận bắt buộc.
3. **Chỉ có bài làm, thiếu đề:** nhắc bổ sung đề gốc trước khi đánh giá cách làm có phù hợp hay không. Hiện bổ sung bằng ô nhập; chưa có luồng ghép thêm ảnh đề thứ hai. Vẫn có thể học cách kiểm tra phép tính đang chọn.
4. **Chỗ chưa rõ:** nếu dịch vụ đánh dấu không chắc hoặc có `[?]`, chỉ hỏi lại bước đang chọn trước khi đưa gợi ý. Dấu hiệu không chắc chưa phát hiện được mọi chữ gạch sửa, vì vậy học sinh vẫn có nút sửa và ảnh để đối chiếu.
5. **Nhiều bài trong một ảnh:** yêu cầu cắt một bài; không tự chọn hoặc giải tất cả.
6. **Lưu và học tiếp:** lưu tối đa 30 bài dạng văn bản theo tài khoản trên thiết bị/trình duyệt hiện tại, gồm đề, bài làm và suy nghĩ của học sinh. Không lưu ảnh gốc vào lịch sử; chưa đồng bộ lịch sử giữa thiết bị. Mở lại giữ mã bài để tránh tăng số bài giả.

Gợi ý nhiều hơn giới hạn hai mức bổ sung. Bộ lọc chặn phương trình đã hoàn tất, đáp số, kết quả số mới và lời chứng nhận toàn bài đúng/sai. Phản hồi bị chặn chuyển sang câu hỏi khái niệm phù hợp; dịch vụ không sẵn sàng trả lỗi để thử lại, không giả kết quả cloud thành công. Đây là biện pháp giảm việc đưa lời giải sẵn, không phải chứng minh model không bao giờ sai.

## Giao diện và thương hiệu

- Trang chủ giữ hướng thiết kế đã được chấp nhận. Các đường chụp/chọn ảnh, quyền riêng tư, cắt ảnh, màn hình học, đăng nhập, khởi động trong ứng dụng, bài đã lưu và thành tích dùng chung màu, chữ, nút và header.
- Dùng linh vật ngôi sao thay biểu tượng máy tính ở đăng nhập; chữ MathVision và Kid dùng hai màu đồng bộ trang chủ.
- Tạo icon MathVisionKid mới từ chính linh vật hiện có; cập nhật icon, adaptive icon và splash trong `apps/student-mobile/app.json`.
- Thay spinner trong các điểm chờ của luồng công khai bằng thanh ngang. Không thêm đồng hồ chờ hoặc phần trăm tiến độ tự đặt. Thanh chờ không biểu thị phần trăm công việc đã hoàn thành.
- Hủy yêu cầu khi rời màn hình/dừng chờ, bỏ phản hồi cũ; lỗi kết nối giữ nội dung học sinh đang làm. Phiên hết hạn có đường đăng nhập lại.
- Học sinh không nhìn thấy tên nhà cung cấp, địa chỉ API, khóa, cấu trúc máy chủ hoặc chỉ dẫn terminal.

**Icon/splash native cần bản cài mới.** Đổi cấu hình không thay được màn hình tải do Expo Go cung cấp. Lượt này xuất thành công bundle và assets Android/iOS/web; chưa tạo APK/IPA, chưa kiểm chứng splash trên điện thoại. Tham chiếu: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) và [SplashScreen SDK 57](https://docs.expo.dev/versions/v57.0.0/sdk/splash-screen/).

## Nhận diện dòng và API

### Hình học dòng

`ai/runtime/app/tutoring/rows.py` tìm hàng mực viết trên ảnh đã xử lý chiều EXIF, bỏ đường kẻ dài, hạn chế tách dấu tiếng Việt thành hàng riêng và chia vùng theo khoảng trống giữa hàng. Không huấn luyện model, không cố định số hàng theo ảnh bò khoang.

API đọc cả trang bằng model vision, phân biệt văn bản/phép tính với nhãn sơ đồ. Tọa độ do model tự đưa không được dùng trực tiếp. Chỉ gắn khung khi số dòng vật lý và số dòng phiên âm phù hợp; nhãn sơ đồ ở đầu trang được xử lý riêng trong trường hợp đủ điều kiện. Nếu chưa phù hợp, giữ văn bản nhưng không vẽ khung suy đoán. Kiểm tra lại bằng một lượt đọc độc lập có giới hạn thời gian khi hai số dòng không khớp; bất đồng có thể đánh dấu cần hỏi lại.

Đường nhận diện dòng cũ cũng dùng bộ tìm hàng mực này và bỏ phép xoay chỉ áp dụng lên ảnh detector vốn làm tọa độ lệch ảnh dùng để cắt. Bỏ ưu tiên “nhiều khung hơn là tốt hơn” và không tăng điểm tin cậy giả.

Phần tìm hàng mực ưu tiên mực xanh/tím/hồng. Chưa có bằng chứng đủ với mực đen, ảnh nghiêng mạnh, mờ, nhiều cột, phân số xếp chồng hoặc tất cả kiểu chữ gạch sửa. Khung đúng số lượng cũng không chứng minh phiên âm đúng từng ký tự.

### Ranh giới dịch vụ

- Spring giữ quyền quyết định đăng nhập/vai trò cho `POST /api/v1/student/tutor/inspect` và `/coach`; không chuyển quyền đó sang mobile hoặc AI.
- Đọc ảnh yêu cầu đồng ý sử dụng ảnh, giới hạn 8 MiB và kiểm tra chữ ký định dạng. Mobile gửi ảnh đã qua bước che thông tin/cắt ảnh hiện có.
- Chuẩn hóa ảnh trong bộ nhớ, xử lý EXIF, bỏ metadata trước khi gửi model. Khóa nhà cung cấp và khóa nội bộ ở máy chủ; không sửa `.env` hoặc đưa khóa vào báo cáo.
- Schema và độ dài đề/bài làm/câu trả lời được kiểm tra ở backend và AI. Bước đang chọn phải thuộc bài làm; gợi ý không được lấy đáp số từ bước khác để đưa cho học sinh.
- Dùng cấu hình Groq hiện có, Gemini dự phòng. **Lượt kiểm tra trực tiếp Gemini trên ba ảnh Drive lần này chưa đạt** do lỗi dịch vụ/xác thực/phản hồi, nên không coi dự phòng đã được xác minh với các ảnh đó. Bằng chứng Gemini trong báo cáo MVP trước là lượt kiểm tra khác.

## Kiểm thử tự động

| Phần | Kết quả trong lượt triển khai |
| --- | --- |
| Student Mobile, toàn bộ | 35 bộ, 374 test đạt |
| Business API, toàn bộ | 229 test đạt, không lỗi hoặc bỏ qua |
| AI, 6 module liên quan tutoring/hình học dòng | 126 test đạt; không tuyên bố toàn bộ AI legacy đạt |
| Kiểm tra cuối sau sửa prompt/đánh dấu chưa rõ | 92 test tutoring đạt; các test hình học đã đạt trước đó |
| Kiểm tra màn hình học sau chỉnh nội dung cuối | 7 test đạt |
| TypeScript | `tsc --noEmit` đạt |
| Expo export | Android, iOS, web đạt; 60 assets, 32 route web |
| Git whitespace | `git diff --check` đạt |

126 test AI gồm cả 92 test tutoring và các test hình học liên quan; không cộng lại thành 218. Bộ xuất cuối nằm ở `scratch/product_20261003/final-export`. Export kiểm tra khả năng đóng gói JavaScript/assets, không thay thế native build hoặc kiểm thử thiết bị.

Các kiểm thử mới tập trung giới hạn đầu vào/phản hồi, ảnh nhiều bài, tọa độ không có bằng chứng, không đưa kết quả sẵn, ký hiệu chưa rõ, hủy yêu cầu/phản hồi cũ, lưu lịch sử theo tài khoản và mở lại bài. Kiểm thử controller dùng cấu hình bảo mật của dự án, gồm thiếu đăng nhập và vai trò không phù hợp.

## Ảnh thật và kết quả cuối

Đã lấy bốn ảnh từ [thư mục Drive chủ dự án cung cấp](https://drive.google.com/drive/folders/1hw9icN3tsAkhghODoA_6WZt7Jg44NSFX?usp=sharing), cộng ảnh đính kèm bài bò khoang. Không tải toàn bộ kho dữ liệu hoặc file model lớn. Ảnh `grade5-1` là cùng bài bò khoang có thêm sơ đồ, **không phải mẫu độc lập** để tính tỷ lệ chính xác.

| Ảnh | Kết quả HTTP cuối | Phiên âm/khung | Thời gian |
| --- | --- | --- | --- |
| Bài bò khoang đính kèm | WORK, cần đề gốc | 9 dòng / 9 khung | 3,593 giây |
| Trang 79 lớp 4, nhiều bài | MULTIPLE, cần cắt một bài | Không trả phiên âm riêng từng bài | 1,812 giây |
| Lớp 5, ảnh 1, bò khoang kèm sơ đồ | WORK, cần đề gốc | 9 dòng bài làm / 9 khung | 4,578 giây |
| Lớp 5, ảnh 2, bài tiền có gạch sửa | WORK, cần đề gốc | 7 dòng / 7 khung trong lượt cuối | 3,469 giây |
| Lớp 5, ảnh 3, bài đường dốc có viết đè | WORK, cần đề gốc | 5 dòng bài làm / 5 khung | 5,875 giây |

**Sai sót đã quan sát:**

- Lượt cuối hai ảnh bò khoang đọc “bò vàng” thành “bò vằn”, chưa tự đánh dấu không chắc. Các phép tính 2 + 5 = 7, 49 : 7 × 2 = 14, 49 − 14 = 35 và hai hàng đáp số được giữ.
- Ảnh tiền có số bị gạch và giá trị sửa trên hàng riêng. Lượt trước trả 8 dòng nhưng không gắn khung; lượt cuối trả 7 dòng, gộp đáp số buổi sáng thành 10 800 000 đồng và không đánh dấu chữ gạch. Không chứng nhận hình học hoặc cách gộp này chính xác cho mọi hàng sửa.
- Ảnh đường dốc vẫn phiên âm “đoạn đường dốc” và bỏ từ “lên” viết thay “xuống”; chưa đánh dấu không chắc. Phần phép tính nhìn thấy được đọc 1400 : 7 × 3 = 600 (m).

Vì vậy đây là bằng chứng cải thiện việc tìm dòng trên ảnh thật, **không phải CER/WER benchmark hoặc độ chính xác 100%**. Kết quả model thay đổi giữa các lượt. Việc cho sửa ngay bước đang chọn vẫn cần thiết; không buộc học sinh duyệt cả trang OCR.

11 trường hợp HTTP thật qua Spring đều trả trạng thái mong đợi: thiếu đăng nhập 401, thiếu đồng ý ảnh 400, năm ảnh thật 200, gợi ý bước đang chọn 200, bước không thuộc bài 400, ký hiệu chưa rõ 200 và yêu cầu giải toàn bộ 200 nhưng chỉ nhận gợi ý/câu hỏi. Bản tóm tắt không chứa token: [live-summary.json](product_learning_rework_20261003/live-summary.json).

Gợi ý thực tế cho bước 49 : 7 × 2: “Em hãy kiểm tra lại phép tính 49 : 7 × 2. Trước tiên, em thử tính 49 chia cho 7 xem ra bao nhiêu, rồi mới nhân với 2 nhé.” Câu hỏi: “Em tính 49 : 7 ra bao nhiêu?” Không trả đáp số. Thời gian 0,532 giây cho lượt này; không bảo đảm mọi lượt đều có cùng tốc độ.

## Kiểm tra giao diện và giới hạn bằng chứng

Đã kiểm tra code, test component, TypeScript và export. Computer Use bị công cụ dừng vì không xác định chắc URL hiện tại trên Windows để thực thi chính sách; không thử công cụ điều khiển khác để vượt giới hạn đó. Do vậy **chưa có bằng chứng kiểm tra trực quan tương tác trên browser/điện thoại cho bản cuối**, không có ảnh chụp màn hình thiết bị được coi là kết quả mới. Bản icon sinh được xem trực tiếp; ảnh overlay thuật toán chỉ kiểm tra dữ liệu hình học.

## Cách thử bản hiện tại

1. Chạy hệ thống bằng launcher hiện có của dự án, mở Student Mobile và đăng nhập học sinh. Đăng nhập seed chỉ dùng trong kiểm thử local, không đưa email/mật khẩu vào UI.
2. Trang chủ → **Chụp bài toán** → chụp hoặc chọn ảnh, che thông tin riêng tư, cắt phần có một bài, xác nhận.
3. Với ảnh bò khoang, kiểm tra màn hình **Cùng em tìm cách giải** mở trực tiếp, có ảnh và bước đang chọn; không chuyển qua màn hình xác nhận tám/chín dòng OCR cũ.
4. Chọn một bước, đọc gợi ý và câu hỏi, nhập suy nghĩ của mình. Thử hỏi “cho toàn bộ đáp số” để kiểm tra hành vi vẫn chỉ hướng dẫn bước tiếp.
5. Thử thiếu đề gốc, ảnh nhiều bài, ký hiệu chưa rõ và dừng chờ. Đối chiếu lại chữ gạch sửa; sửa nội dung khi đọc sai.
6. Lưu bài, vào **Của em**, mở lại bài; kiểm tra nội dung và số bài không tăng giả khi lưu lại cùng bài. Thử đăng nhập tài khoản khác để kiểm tra lịch sử tách theo tài khoản.
7. Muốn đánh giá icon/splash native mới, cần tạo và cài bản native mới; bundle export trong lượt này chưa là APK/IPA.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Đồng bộ UI/UX mobile với trang chủ đã được chủ dự án chấp nhận.
  - Applied to: Luồng chụp ảnh, màn hình học, lịch sử, header, nút, nhận biết trạng thái và cách trình bày gợi ý.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Triển khai và chỉnh component React/React Native, xử lý tác vụ bất đồng bộ.
  - Applied to: Màn hình học, hủy yêu cầu, bỏ phản hồi cũ, trạng thái lưu/mở lại bài và các component dùng chung.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Giữ thay đổi trực tiếp, dùng lại thư viện và cơ chế hiện có.
  - Applied to: Lịch sử bằng expo-file-system/localStorage sẵn có, bộ tìm dòng dùng OpenCV, dùng lại gateway và cấu hình provider; không thêm dependency hoặc training.

Skill bổ sung ngoài workspace đã dùng: `imagegen` để tạo icon từ linh vật hiện có; `computer-use:computer-use` để thử kiểm tra trực quan, nhưng công cụ đã dừng như ghi trên; Google Drive để truy cập dữ liệu ảnh chủ dự án cung cấp. Không coi lần thử Computer Use là kiểm tra UI thành công.

## Nguồn icon sinh

- Mode: chỉnh từ ảnh tham chiếu linh vật, nền opaque.
- Tài nguyên dự án: `apps/student-mobile/assets/images/mathvision-icon.png`.
- Nguồn sinh: `C:/Users/Admin/.codex/generated_images/01a0fc52-cdd5-7b42-9da4-a52951ff8018/exec-1191a27e-8b86-48c5-ba5d-0e8bf65429bc.png`.
- Prompt:

> Create a polished square mobile app icon for MathVisionKid using the EXACT supplied yellow five-point star student mascot as the central subject. Preserve the mascot's recognizable face, blue graduation cap, purple book, waving pose, glossy 3D style, and child-friendly proportions. Place it centered and large inside a soft rounded-square background with a very light lavender-to-white gradient (#F6F2FF to #EDE7FF), subtle depth, tiny tasteful yellow and lavender sparkles, generous safe margins for iOS and Android masking. No text, no letters, no symbols, no border, no watermark. Premium cohesive educational kids app branding, crisp at small sizes, 1024x1024, fully opaque background.

Không commit/push trong lượt triển khai này. Không huấn luyện model. Các thay đổi MVP và báo cáo cũ trong working tree được giữ.
