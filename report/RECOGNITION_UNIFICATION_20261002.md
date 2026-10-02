# Tái cấu trúc nhận dạng thành mô-đun MathVision Kids

Ngày: 02/10/2026. Phạm vi: cấu trúc và tích hợp nhận dạng đang có trong MathVision; không huấn luyện mô hình, không sửa repository riêng, không commit/push.

## Kết quả

Nhận dạng chữ viết tay được tổ chức thành mô-đun của MathVision, dùng chung tài khoản, giao diện, quy trình bảo vệ ảnh và backend. Chế độ sản phẩm riêng, thương hiệu riêng, icon riêng và API khách của bản tách trước đây đã được gỡ. Khả năng OCR đã tích hợp được giữ lại; đây không phải bằng chứng rằng mọi tính năng của repository riêng đều giống hệt hoặc chất lượng mô hình đã tăng sau khi đổi cấu trúc.

| Vị trí hiện tại | Trách nhiệm |
| --- | --- |
| `apps/student-mobile/src/features/recognition/api/RecognitionService.ts` | API nhận dạng, phân dòng, phản hồi và cache kết quả |
| `apps/student-mobile/src/features/recognition/image/` | Ảnh gốc/ảnh đã che, cắt ảnh, URI web và thiết bị |
| `apps/student-mobile/src/features/recognition/state/` | Bản nháp dùng chung cho chữ viết và phép tính |
| `apps/student-mobile/src/features/recognition/utils/` | Gợi ý AI, cập nhật bất đồng bộ, độ tin cậy và lựa chọn người dùng |
| `apps/student-mobile/src/features/recognition/analytics/` | Lịch sử theo tài khoản, CER/WER với bản chuẩn độc lập, xuất dữ liệu |
| `apps/student-mobile/src/app/recognition/` | Các màn nhận dạng, kiểm tra từng dòng và lịch sử |
| `backend/business-api/src/main/java/com/mathvisionkids/api/ocr/` | API nghiệp vụ `/api/v1/ocr/**`, quyền truy cập và chủ sở hữu |
| `ai/runtime/app/ocr/`, `ai/runtime/app/api/`, `ai/runtime/app/schemas/ocr.py` | Lõi OCR và hợp đồng nhận dạng nội bộ |
| `apps/admin-web/src/pages/RecognitionAnalyticsPage.tsx` | Trang phân tích trong khu vực quản trị có bảo vệ đăng nhập |

Chi tiết: [mô-đun nhận dạng](../apps/student-mobile/src/features/recognition/README.md), [cấu trúc dự án](../README.md).

## Các khả năng được giữ

- Checkpoint OCR, vocab, xử lý ảnh/phân dòng, phục hồi nét mực màu và cấu trúc đầu ra hiện có.
- Nhận chữ viết trong lời giải và luồng nhận phép tính `ARITHMETIC`; bộ đánh giá lời giải toán vẫn được giữ.
- Gợi ý Groq/Gemini từ ảnh thật, nguồn độ tin cậy, trạng thái nhà cung cấp và cơ chế bảo vệ chữ/số/phép tính của học sinh.
- Đầu ra OCR gốc, lựa chọn nguồn, sửa tay và bảo vệ sửa tay khi gợi ý đến trễ.
- Phản hồi, điều kiện thu thập dữ liệu, đo lường với bản chuẩn độc lập, xuất JSON/CSV và các công thức nghiên cứu.

Giao diện học sinh không dùng số benchmark mẫu làm chất lượng thực tế. Trang phân tích quản trị hiện vẫn là dữ liệu minh họa và đã có nhãn rõ ràng; chưa được nối thành dashboard số liệu backend thật.

## Tài khoản, lịch sử và tương thích dữ liệu

Backend yêu cầu đăng nhập và vai trò phù hợp, đồng thời kiểm tra chủ sở hữu khi đọc bài hoặc gửi phản hồi. API khách cũ và ngoại lệ xác thực riêng đã bị gỡ. Mobile đợi phục hồi phiên đăng nhập trước khi mở nhận dạng.

Lịch sử mới được lưu theo tài khoản. Cache và bản nháp được làm sạch khi đổi phiên; phản hồi lấy kết quả đến trễ từ phiên cũ không được lưu vào cache phiên mới. Lịch sử cũ chưa xác định chủ sở hữu được bảo toàn riêng, không tự gán cho học sinh đăng nhập tiếp theo. Ảnh đã che không tự chuyển về ảnh gốc nếu ảnh bảo vệ gặp lỗi.

Một khóa lưu trữ cũ nằm trong `features/recognition/analytics/legacyHistory.ts` để chuyển dữ liệu; bản cũ chỉ được xóa sau khi lưu mới thành công. Hai migration V14/V15 giữ nguyên tên và nội dung đã áp dụng để bảo toàn checksum. Tài liệu và bằng chứng cấu trúc cũ được chuyển nguyên trạng vào `report/archive/recognition/`, có [manifest](recognition_unification_20261002/archive-manifest.json) gồm 85 mục. Các dấu vết lịch sử này không bật lại thương hiệu hoặc API riêng.

Ảnh cache được xử lý theo đường dẫn ứng dụng tổng quát, không gắn với tên sản phẩm cũ. Bản sao nguồn trước khi chỉnh sửa và các công cụ bảo trì tạm được giữ ngoài dự án tại `E:/MathVisionKidBackups/recognition-unification-20261002`.

## Kiểm chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Mobile Jest | 25 suites, 253/253 tests đạt |
| Mobile TypeScript | `tsc --noEmit` đạt |
| Backend test profile với H2 | 153/153 tests đạt; có kiểm tra xác thực và chủ sở hữu |
| Admin web production build | Đạt; còn cảnh báo bundle lớn sẵn có |
| Mobile web export | Đạt, 27 routes; có `/recognition/**`, không còn route sản phẩm riêng |
| Bộ hồi quy OCR được chọn | 224 tests: 215 đạt, 9 lỗi phân đoạn giống hệt danh sách lỗi trước tái cấu trúc |
| Ảnh chữ viết người dùng gửi | Phát hiện 9 dòng; tọa độ, văn bản OCR gốc, độ tin cậy và nguồn độ tin cậy giống trước tái cấu trúc |
| Checkpoint OCR | SHA256 giữ nguyên: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` |
| Kiểm tra diff | Không có lỗi whitespace |

Ảnh được kiểm tra bằng inference thật trong AI runtime, tắt nhà cung cấp tư vấn bên ngoài trong lần đối chiếu này. SHA256 ảnh: `56e218a182ff1bcd111b8a9a0615288dcb85439585844d1f3852fd610b8ca285`.

Bằng chứng: [tổng hợp kiểm chứng](recognition_unification_20261002/verification.json), [Jest](recognition_unification_20261002/mobile-tests.json), [pytest](recognition_unification_20261002/ai-tests.xml), [đối chiếu ảnh](recognition_unification_20261002/image-regression.json). Công cụ đối chiếu giữ tại `tools/verification/verify_recognition.py`.

Giới hạn: chưa kiểm tra lại toàn bộ luồng trên thiết bị vật lý, chưa chạy lại toàn bộ hệ thống với cơ sở dữ liệu production hoặc nhà cung cấp AI trực tiếp. Chín lỗi phân đoạn AI có từ trước vẫn cần xử lý ở công việc chất lượng nhận dạng riêng. Tái cấu trúc không chứng minh mô hình nhận dạng tốt hơn.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Tái cấu trúc tối thiểu và loại bỏ nhánh sản phẩm trùng lặp.
  - Applied to: Cấu trúc nhận dạng, API/backend, cấu hình, loại bỏ chế độ và code trùng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Thay đổi React/React Native, trạng thái và lưu trữ phía client.
  - Applied to: Routes, đồng bộ kết quả, bảo vệ chỉnh sửa, phiên đăng nhập và schema lưu trữ.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: Đưa màn hình lịch sử/phân tích vào giao diện MathVision cho học sinh.
  - Applied to: Thành phần tóm tắt, trạng thái tải/rỗng, nội dung dễ hiểu và nút thao tác.
